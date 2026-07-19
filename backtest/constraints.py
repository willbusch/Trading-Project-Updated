"""Entry constraint checks — pure functions over (state, candidate order,
config). Each returns (ok: bool, reason: str); check_all_entry_constraints
composes every applicable one and is the single gate the simulator calls
per candidate entry.

The checks THEMSELVES never mutate state. The simulator only mutates state
after check_all_entry_constraints passes.
"""
from dataclasses import dataclass

import pandas as pd

from backtest.portfolio_state import PortfolioState


@dataclass
class EntryOrder:
    date: pd.Timestamp
    ticker: str
    kind: str               # "equity" | "leap"
    dollars: float          # intended cost of this entry
    is_tranche_add: bool = False   # adding to an existing position (ablation only)
    delta: float | None = None     # LEAP only


def check_slots(state: PortfolioState, order: EntryOrder, cfg: dict):
    if order.is_tranche_add:
        return True, ""
    key = "equity_slots" if order.kind == "equity" else "leap_slots"
    limit = cfg["sizing"][key]
    used = state.slots_used(order.kind)
    if used >= limit:
        return False, f"slots: {used}/{limit} {order.kind} slots already used"
    return True, ""


def check_position_cap(state: PortfolioState, order: EntryOrder, cfg: dict):
    book = state.total_equity
    if book <= 0:
        return False, "position_cap: book value is zero"
    existing = state.positions.get(order.ticker)
    existing_value = existing.market_value if existing is not None else 0.0
    if order.kind == "leap":
        cap = cfg["leap"]["single_entry_pct_of_book"]
        label = "leap.single_entry_pct_of_book"
    else:
        cap = cfg["sizing"]["max_position_pct_of_book"]
        label = "sizing.max_position_pct_of_book"
    if (existing_value + order.dollars) / book > cap + 1e-9:
        return False, (
            f"position_cap: {order.ticker} would be "
            f"{(existing_value + order.dollars) / book:.1%} of book, cap {label}={cap:.0%}"
        )
    return True, ""


def check_leap_sleeve(state: PortfolioState, order: EntryOrder, cfg: dict):
    if order.kind != "leap":
        return True, ""
    book = state.total_equity
    sleeve = sum(
        p.market_value for p in state.positions.values() if p.kind == "leap"
    )
    cap = cfg["leap"]["sleeve_cap_pct_of_book"]
    if (sleeve + order.dollars) / book > cap + 1e-9:
        return False, (
            f"leap_sleeve: sleeve would be {(sleeve + order.dollars) / book:.1%}, "
            f"cap {cap:.0%}"
        )
    return True, ""


def check_cash_floor(state: PortfolioState, order: EntryOrder, cfg: dict):
    floor = cfg["sizing"]["min_cash_floor_pct"] * state.total_equity
    remaining = state.cash.balance - order.dollars
    if remaining < floor - 1e-9:
        return False, (
            f"cash_floor: entry leaves {remaining:.2f} cash, floor is {floor:.2f}"
        )
    return True, ""


def check_weekly_cap(state: PortfolioState, order: EntryOrder, cfg: dict):
    if order.is_tranche_add:
        return True, ""
    cap = cfg["circuit_breakers"]["max_new_positions_per_week"]
    wk = PortfolioState.week_key(order.date)
    opened = state.new_positions_by_week.get(wk, 0)
    if opened >= cap:
        return False, f"weekly_cap: {opened}/{cap} new positions already this week"
    return True, ""


def check_kill_switch(state: PortfolioState, order: EntryOrder, cfg: dict):
    if state.halted_until is not None and order.date < state.halted_until:
        return False, f"kill_switch: entries halted until {state.halted_until.date()}"
    return True, ""


def check_cash_rule(state: PortfolioState, order: EntryOrder, cfg: dict):
    """THE cash rule (STRATEGY.md): all sale proceeds go to cash, and are
    NEVER routed into an underwater position. Concretely: an entry that
    adds to a position currently marked below its cost basis may not be
    funded by same-bar sale proceeds — it must clear from the cash that
    existed before this bar's sales. Proceeds may fund anything else;
    pre-existing cash may fund anything the other checks allow."""
    existing = state.positions.get(order.ticker)
    if existing is None or not existing.is_underwater:
        return True, ""
    proceeds_today = state.cash.sale_proceeds_on(order.date)
    cash_excl_proceeds = state.cash.balance - proceeds_today
    if order.dollars > cash_excl_proceeds + 1e-9:
        return False, (
            f"cash_rule: {order.ticker} is underwater; entry of "
            f"{order.dollars:.2f} exceeds pre-sale cash {cash_excl_proceeds:.2f} "
            f"(same-bar sale proceeds {proceeds_today:.2f} may not fund it)"
        )
    return True, ""


ALL_CHECKS = [
    check_kill_switch,
    check_slots,
    check_weekly_cap,
    check_position_cap,
    check_leap_sleeve,
    check_cash_floor,
    check_cash_rule,
]


def check_all_entry_constraints(state: PortfolioState, order: EntryOrder, cfg: dict):
    """Run every check; returns (ok, [failure reasons]). Runs ALL checks
    rather than short-circuiting so rejection logs show every violated
    rule, not just the first."""
    reasons = [r for ok, r in (c(state, order, cfg) for c in ALL_CHECKS) if not ok]
    return len(reasons) == 0, reasons
