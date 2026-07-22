import pandas as pd

from backtest.constraints import EntryOrder, check_leap_reserve
from backtest.portfolio_state import PortfolioState

D0 = pd.Timestamp("2024-01-02")
CFG = {"leap": {"reserve_pct": 0.33}, "sizing": {"min_cash_floor_pct": 0.05}}


def _state(cash=100_000.0):
    return PortfolioState(cash, D0)


def test_equity_entry_blocked_below_reserve_plus_floor_when_no_leap_held():
    state = _state(cash=100_000.0)
    # No LEAP held. Reserve (33%) + floor (5%) = 38% must stay in cash.
    # An equity buy of 65k would leave 35k < 38k required -> blocked.
    order = EntryOrder(D0, "AAPL", "equity", 65_000.0)
    ok, reason = check_leap_reserve(state, order, CFG)
    assert not ok
    assert "leap_reserve" in reason


def test_equity_entry_allowed_within_reserve_plus_floor():
    state = _state(cash=100_000.0)
    order = EntryOrder(D0, "AAPL", "equity", 60_000.0)   # leaves 40k >= 38k
    ok, reason = check_leap_reserve(state, order, CFG)
    assert ok


def test_reserve_check_steps_aside_once_a_leap_is_held():
    state = _state(cash=100_000.0)
    state.open_or_add(D0, "MSFT", "leap", price=5000.0, shares=6,
                      delta=0.60, strike=400.0, expiry_date=D0 + pd.Timedelta(days=730),
                      sigma=0.35, underlying_price=450.0)
    # 30k spent on the LEAP entry -> 70k cash left. No reserve requirement
    # anymore (the LEAP already deployed the 33%) — only the normal 5%
    # floor (checked elsewhere) applies. An equity buy that would leave
    # well above the 5% floor should NOT be blocked by the reserve rule.
    order = EntryOrder(D0, "GOOG", "equity", 60_000.0)
    ok, reason = check_leap_reserve(state, order, CFG)
    assert ok


def test_reserve_check_is_a_noop_when_not_configured():
    """Backward compatibility: configs without leap.reserve_pct (e.g. the
    retired A/B/C/D strategies' minimal test cfg) must not be affected."""
    state = _state(cash=1_000.0)
    order = EntryOrder(D0, "AAPL", "equity", 999.0)   # would leave ~1 dollar
    ok, reason = check_leap_reserve(state, order, {"leap": {}, "sizing": {}})
    assert ok


def test_reserve_check_leap_orders_never_blocked_by_this_rule():
    state = _state(cash=100_000.0)
    order = EntryOrder(D0, "MSFT", "leap", 33_000.0)
    ok, reason = check_leap_reserve(state, order, CFG)
    assert ok


# ---- A3 (2026-07-22, "Beat-SPY Package"): reserve REVERSED to spendable ----

CFG_SPENDABLE = {**CFG, "leap": {**CFG["leap"], "reserve_spendable": True}}


def test_reserve_spendable_flag_lets_equities_draw_on_the_reserve():
    """The exact case that used to be BLOCKED (test above,
    test_equity_entry_blocked_below_reserve_plus_floor_when_no_leap_held)
    must now be ALLOWED once reserve_spendable is set — the owner's
    explicit reversal from 'wall' to 'working capital'."""
    state = _state(cash=100_000.0)
    order = EntryOrder(D0, "AAPL", "equity", 65_000.0)   # would have failed under CFG
    ok, _ = check_leap_reserve(state, order, CFG_SPENDABLE)
    assert ok


def test_reserve_spendable_flag_still_leaves_cash_floor_check_to_its_own_rule():
    """check_leap_reserve stepping aside doesn't mean unlimited spending —
    check_cash_floor (a separate check) still applies; this test only
    verifies check_leap_reserve itself no-ops, not the composed gate."""
    state = _state(cash=100_000.0)
    order = EntryOrder(D0, "AAPL", "equity", 99_999.0)
    ok, _ = check_leap_reserve(state, order, CFG_SPENDABLE)
    assert ok
