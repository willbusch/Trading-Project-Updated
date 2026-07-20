"""Daily-clock event-driven simulator for the latched-Fib strategy.

Reuses the risk framework UNCHANGED — PortfolioState, the constraint
checks (incl. the cash rule + its adversarial test), and leap_pricing —
but runs its own daily loop because Fib exits depend on each position's
entry anchors and so cannot be precomputed as a static exit column the
way A/B/C/D's could. The shared simulate() and its tests are untouched.

Execution: signals read on daily close, filled at next daily open with
slippage. Exits fill first (proceeds→cash), then entries through
check_all_entry_constraints. Slot-selection tiebreak when more names
qualify than free slots (documented owner-flagged rule): deepest drawdown
first, then earliest gate-clear date, then ticker alphabetical.
"""
from dataclasses import dataclass, field

import pandas as pd

from backtest.constraints import EntryOrder, check_all_entry_constraints
from backtest.fib_exit import EquityLatchExit, LeapSimpleExit
from backtest.leap_pricing import PRICING_LABEL, leap_delta
from backtest.portfolio_state import PortfolioState


@dataclass
class FibTrade:
    ticker: str
    kind: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: float
    two_yr_high: float
    dip_low: float
    entry_frac: float
    peak_price: float                    # max close while held — for The Gap
    exit_date: pd.Timestamp | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    priced_as: str = "shares"
    stale_at_entry: bool = False

    @property
    def is_open(self) -> bool:
        return self.exit_date is None


@dataclass
class FibRejected:
    date: pd.Timestamp
    ticker: str
    reasons: list


@dataclass
class FibResult:
    cell: str
    window_label: str
    seed_cash: float
    trades: list = field(default_factory=list)
    rejected_entries: list = field(default_factory=list)
    equity_curve: pd.Series | None = None
    cash_curve: pd.Series | None = None
    halts: list = field(default_factory=list)
    stale_excluded: list = field(default_factory=list)   # (date,ticker) skipped

    @property
    def closed_trades(self):
        return [t for t in self.trades if not t.is_open]

    @property
    def open_trades(self):
        return [t for t in self.trades if t.is_open]


def simulate_fib(
    frames: dict,
    cfg: dict,
    window=None,
    seed_cash: float | None = None,
    cell: str = "?",
    window_label: str = "combined",
    leap_tickers: frozenset = frozenset(),
    include_stale: bool = False,          # both-ways diagnostic sets this True
    simple_exit: bool = False,            # ablation: no latch, sell@1.618 or UT>0.5
) -> FibResult:
    slippage = cfg["backtest"]["slippage_pct"]
    seed_cash = cfg["backtest"]["seed_cash"] if seed_cash is None else seed_cash

    sliced = {}
    for t, f in frames.items():
        s = f.loc[window[0]:window[1]] if window is not None else f
        if len(s) > 0:
            sliced[t] = s
    all_dates = sorted(set().union(*[set(f.index) for f in sliced.values()]))
    if not all_dates:
        raise ValueError("simulate_fib: empty window")

    state = PortfolioState(seed_cash, all_dates[0])
    result = FibResult(cell, window_label, seed_cash)
    open_trades: dict[str, FibTrade] = {}
    exit_machines: dict = {}
    pending_exits: dict[str, str] = {}
    # ticker -> anchor snapshot FROZEN at the signal bar's close (date D),
    # so nothing read at the fill bar (D+1) can leak into the anchors.
    pending_entries: dict[str, dict] = {}
    equity_hist, cash_hist = [], []
    delta = leap_delta(cfg)

    for date in all_dates:
        todays = {t: f.loc[date] for t, f in sliced.items() if date in f.index}

        # 1. pending EXITS at open
        for tkr in sorted(pending_exits):
            if tkr in todays and tkr in state.positions:
                pos = state.positions[tkr]
                fill = todays[tkr]["Open"] * (1 - slippage)
                if pos.kind == "leap" and pos.delta is not None:
                    cost_b = pos.cost_basis
                    proceeds = cost_b + pos.delta * (pos.shares * fill - cost_b)
                    state.positions.pop(tkr)
                    state.cash.deposit(date, proceeds, "sale", tkr)
                else:
                    proceeds = state.close_position(date, tkr, fill)
                tr = open_trades.pop(tkr)
                exit_machines.pop(tkr, None)
                tr.exit_date, tr.exit_price = date, fill
                tr.exit_reason = pending_exits[tkr]
                cost = tr.shares * tr.entry_price
                tr.pnl = proceeds - cost
                tr.pnl_pct = tr.pnl / cost
                result.trades.append(tr)
                del pending_exits[tkr]

        # 2. pending ENTRIES at open (constraint-gated)
        for tkr in sorted(pending_entries):
            if tkr not in todays:
                continue
            _snap = pending_entries.pop(tkr)
            if tkr in state.positions:
                continue
            kind = "leap" if tkr in leap_tickers else "equity"
            cap = (cfg["leap"]["single_entry_pct_of_book"] if kind == "leap"
                   else cfg["sizing"]["max_position_pct_of_book"])
            dollars = cap * state.total_equity
            order = EntryOrder(date, tkr, kind, dollars,
                               delta=delta if kind == "leap" else None)
            ok, reasons = check_all_entry_constraints(state, order, cfg)
            if not ok:
                result.rejected_entries.append(FibRejected(date, tkr, reasons))
                continue
            fill = todays[tkr]["Open"] * (1 + slippage)
            shares = dollars / fill
            state.open_or_add(date, tkr, kind, fill, shares, order.delta)
            two_yr_high, dip_low = _snap["high_2yr"], _snap["dip_low"]
            from backtest.drawdown_gate import price_fraction
            machine = (LeapSimpleExit(dip_low, two_yr_high) if kind == "leap"
                       else EquityLatchExit(dip_low, two_yr_high))
            exit_machines[tkr] = machine
            open_trades[tkr] = FibTrade(
                tkr, kind, date, fill, shares, two_yr_high, dip_low,
                price_fraction(fill, dip_low, two_yr_high), peak_price=fill,
                priced_as=PRICING_LABEL if kind == "leap" else "shares",
                stale_at_entry=bool(_snap["stale"]),
            )

        # 3. read CLOSE signals -> schedule next-bar exits / collect entries
        entry_candidates = []
        for tkr, row in todays.items():
            price = row["Close"]
            if tkr in state.positions:
                open_trades[tkr].peak_price = max(open_trades[tkr].peak_price, price)
                if tkr in pending_exits:
                    continue
                # LEAP modeled expiry ("rides to Fib target OR expiry"):
                # force-exit at entry + fib_modeled_expiry_years. force-close
                # 6mo rule is suspended for this strategy.
                tr = open_trades[tkr]
                if tr.kind == "leap":
                    age_yrs = (date - tr.entry_date).days / 365.25
                    if age_yrs >= cfg["leap"]["fib_modeled_expiry_years"]:
                        pending_exits[tkr] = "leap_modeled_expiry"
                        continue
                do_exit, reason = _eval_exit(
                    exit_machines[tkr], price, bool(row["exit_ut_sell"]), simple_exit,
                )
                if do_exit:
                    pending_exits[tkr] = reason
            else:
                if (row["eligible"] and row["entry_ut_buy"]
                        and tkr not in pending_entries):
                    if row["stale"] and not include_stale:
                        result.stale_excluded.append((date, tkr))
                        continue
                    entry_candidates.append((tkr, row))

        # slot-selection tiebreak: deepest drawdown, then earliest gate-clear,
        # then alphabetical — deterministic, documented.
        entry_candidates.sort(
            key=lambda tr: (-tr[1]["dd_pct"], tr[1]["gate_clear_date"], tr[0])
        )
        for tkr, row in entry_candidates:
            # freeze anchors at THIS bar's close (all known now) so the
            # fill bar can't leak into them
            pending_entries[tkr] = {
                "high_2yr": row["high_2yr"],
                "dip_low": row["dip_low"],
                "stale": bool(row["stale"]),
            }

        # 4. mark-to-market + kill switch
        state.mark_to_market(date, {t: r["Close"] for t, r in todays.items()})
        cb = cfg["circuit_breakers"]
        if (state.drawdown_from_peak >= cb["account_drawdown_halt_pct"]
                and (state.halted_until is None or date >= state.halted_until)):
            state.halted_until = date + pd.Timedelta(days=cb["halt_duration_days"])
            result.halts.append(date)
        equity_hist.append(state.total_equity)
        cash_hist.append(state.cash.balance)

    result.trades.extend(open_trades.values())
    result.equity_curve = pd.Series(equity_hist, index=all_dates, name="equity")
    result.cash_curve = pd.Series(cash_hist, index=all_dates, name="cash")
    return result


def _eval_exit(machine, price, ut_sell, simple_exit):
    """Dispatch to the position's Fib machine, or the ablation's simple
    exit (sell at 1.618 OR any exit-TF UT sell while price fraction > 0.5;
    no zones, no latch)."""
    if not simple_exit:
        return machine.step(price, ut_sell)
    from backtest.drawdown_gate import price_fraction
    frac = price_fraction(price, machine.dip_low, machine.two_yr_high)
    if frac != frac:
        return False, None
    if frac >= 1.618:
        return True, "simple_1618_hard"
    if frac > 0.5 and ut_sell:
        return True, "simple_ut_sell"
    return False, None
