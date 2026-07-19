import pandas as pd
import pytest

from backtest.constraints import (
    EntryOrder,
    check_all_entry_constraints,
    check_cash_floor,
    check_cash_rule,
    check_kill_switch,
    check_position_cap,
    check_slots,
    check_weekly_cap,
)
from backtest.portfolio_state import LedgerError, PortfolioState

CFG = {
    "sizing": {
        "equity_slots": 5,
        "leap_slots": 1,
        "max_position_pct_of_book": 0.15,
        "min_cash_floor_pct": 0.05,
    },
    "leap": {"single_entry_pct_of_book": 0.20, "sleeve_cap_pct_of_book": 0.25},
    "circuit_breakers": {"max_new_positions_per_week": 2},
}

D0 = pd.Timestamp("2024-01-02")
D1 = pd.Timestamp("2024-01-05")


def _state(cash=100_000.0):
    return PortfolioState(cash, D0)


def test_cash_rule_adversarial_sale_proceeds_cannot_fund_underwater_add():
    """THE adversarial test: sell a winner, try to route the proceeds into
    an underwater name on the same bar. Must be rejected."""
    state = _state(cash=20_000.0)
    # Underwater position: bought LOSER at 100, now marked 60.
    state.open_or_add(D0, "LOSER", "equity", price=100.0, shares=150)  # 15k cost
    # Winner bought at 50, now 100.
    state.open_or_add(D0, "WINNER", "equity", price=50.0, shares=80)  # 4k cost
    state.mark_to_market(D1, {"LOSER": 60.0, "WINNER": 100.0})
    assert state.positions["LOSER"].is_underwater

    # Same-bar: sell the winner (8k proceeds -> cash = 1k pre-existing + 8k).
    state.close_position(D1, "WINNER", 100.0)
    assert state.cash.balance == pytest.approx(9_000.0)

    # Adversarial order: add 5k to the underwater LOSER. Cash balance
    # covers it — but only because of the same-bar sale. Must be REJECTED.
    order = EntryOrder(D1, "LOSER", "equity", dollars=5_000.0, is_tranche_add=True)
    ok, reason = check_cash_rule(_s := state, order, CFG)
    assert not ok
    assert "cash_rule" in reason and "underwater" in reason

    # And the composed gate rejects it too (not just the isolated check).
    ok_all, reasons = check_all_entry_constraints(state, order, CFG)
    assert not ok_all
    assert any("cash_rule" in r for r in reasons)

    # Control 1: the same 5k entry into a FRESH name (not underwater) is
    # allowed to use the proceeds — the rule bans routing into underwater
    # names, not spending proceeds at all.
    fresh = EntryOrder(D1, "FRESH", "equity", dollars=5_000.0)
    ok_fresh, _ = check_cash_rule(state, fresh, CFG)
    assert ok_fresh

    # Control 2: an add to LOSER small enough to clear PRE-sale cash
    # (1k existed before the sale) is not blocked by the cash rule.
    small = EntryOrder(D1, "LOSER", "equity", dollars=900.0, is_tranche_add=True)
    ok_small, _ = check_cash_rule(state, small, CFG)
    assert ok_small


def test_all_sale_proceeds_go_to_cash_structurally():
    state = _state(cash=10_000.0)
    state.open_or_add(D0, "AAA", "equity", price=100.0, shares=50)
    state.mark_to_market(D1, {"AAA": 120.0})
    proceeds = state.close_position(D1, "AAA", 120.0)
    assert proceeds == pytest.approx(6_000.0)
    assert state.cash.balance == pytest.approx(5_000.0 + 6_000.0)
    assert state.cash.sale_proceeds_on(D1) == pytest.approx(6_000.0)
    # ledger history shows the sale credited to cash, tagged to the ticker
    last = state.cash.history[-1]
    assert last.reason == "sale" and last.ticker == "AAA" and last.amount > 0


def test_slots_cap_equity_and_leap():
    state = _state()
    for i in range(5):
        state.open_or_add(D0, f"EQ{i}", "equity", price=10.0, shares=100)
    ok, reason = check_slots(state, EntryOrder(D1, "NEW", "equity", 1_000.0), CFG)
    assert not ok and "slots" in reason
    # LEAP slot independent of equity slots
    ok_leap, _ = check_slots(state, EntryOrder(D1, "MSFT", "leap", 1_000.0), CFG)
    assert ok_leap
    state.open_or_add(D0, "MSFT", "leap", price=10.0, shares=100, delta=0.55)
    ok_leap2, r = check_slots(state, EntryOrder(D1, "AAPL", "leap", 1_000.0), CFG)
    assert not ok_leap2 and "leap" in r


def test_position_cap_15_pct():
    state = _state(cash=100_000.0)
    ok, _ = check_position_cap(state, EntryOrder(D1, "AAA", "equity", 15_000.0), CFG)
    assert ok
    ok2, reason = check_position_cap(state, EntryOrder(D1, "AAA", "equity", 15_001.0), CFG)
    assert not ok2 and "position_cap" in reason


def test_cash_floor_5_pct():
    state = _state(cash=100_000.0)
    ok, _ = check_cash_floor(state, EntryOrder(D1, "AAA", "equity", 95_000.0), CFG)
    assert ok
    ok2, reason = check_cash_floor(state, EntryOrder(D1, "AAA", "equity", 95_001.0), CFG)
    assert not ok2 and "cash_floor" in reason


def test_weekly_cap_two_new_positions():
    state = _state()
    state.open_or_add(D1, "AAA", "equity", price=10.0, shares=10)
    state.open_or_add(D1, "BBB", "equity", price=10.0, shares=10)
    ok, reason = check_weekly_cap(state, EntryOrder(D1, "CCC", "equity", 100.0), CFG)
    assert not ok and "weekly_cap" in reason
    # next week resets
    next_week = D1 + pd.Timedelta(days=7)
    ok2, _ = check_weekly_cap(state, EntryOrder(next_week, "CCC", "equity", 100.0), CFG)
    assert ok2


def test_kill_switch_blocks_until_date():
    state = _state()
    state.halted_until = pd.Timestamp("2024-02-01")
    ok, reason = check_kill_switch(state, EntryOrder(D1, "AAA", "equity", 100.0), CFG)
    assert not ok and "kill_switch" in reason
    ok2, _ = check_kill_switch(
        state, EntryOrder(pd.Timestamp("2024-02-01"), "AAA", "equity", 100.0), CFG
    )
    assert ok2


def test_ledger_refuses_overdraw():
    state = _state(cash=100.0)
    with pytest.raises(LedgerError):
        state.cash.withdraw(D1, 200.0, "entry", "AAA")
