"""The ONE stateful event-driven backtest engine. Everything else —
windows, the UT/volume sweeps, ablations, all four strategies — composes
around simulate() with different inputs; no engine logic is duplicated
anywhere else.

Execution model (documented, applied uniformly):
  - Signals are computed on bar CLOSES (in backtest/signals.py). A signal
    on bar i executes at bar i+1's OPEN for that ticker — never same-bar,
    no lookahead. A signal on a ticker's final bar in the window never
    executes.
  - Fills pay slippage: buys at open*(1+slippage_pct), sells at
    open*(1-slippage_pct).
  - Each bar date: exits fill first (proceeds -> cash, structurally),
    then entries — every candidate passes through
    check_all_entry_constraints, which includes the cash rule (same-bar
    sale proceeds may not fund an add to an underwater name).
  - Same-date entry tie-break: alphabetical ticker order (locked plan
    decision #9).
  - Sizing: equities enter at sizing.max_position_pct_of_book x current
    book; LEAPs at leap.single_entry_pct_of_book x book. Single entry is
    PRIMARY; the 3-tranche ladder exists only behind
    AblationConfig.ladder_enabled.
  - Mark-to-market on every bar close; kill switch: drawdown from peak
    >= circuit_breakers.account_drawdown_halt_pct halts new entries for
    halt_duration_days.
  - Tickers keep their own 3-day bar calendars (anchors differ by fetch
    start) — the loop runs over the union of dates and touches each
    ticker only on its own bar dates.
"""
from dataclasses import dataclass, field

import pandas as pd

from backtest.constraints import EntryOrder, check_all_entry_constraints
from backtest.leap_pricing import PRICING_LABEL, leap_delta
from backtest.portfolio_state import PortfolioState
from backtest.signals import AblationConfig


@dataclass
class Trade:
    ticker: str
    kind: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: float
    exit_date: pd.Timestamp | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    priced_as: str = "shares"   # "shares" | "leap_delta_approx" — report label

    @property
    def is_open(self) -> bool:
        return self.exit_date is None


@dataclass
class RejectedEntry:
    date: pd.Timestamp
    ticker: str
    reasons: list


@dataclass
class BacktestResult:
    strategy: str
    window_label: str
    seed_cash: float
    trades: list = field(default_factory=list)          # closed AND open
    rejected_entries: list = field(default_factory=list)
    equity_curve: pd.Series | None = None
    cash_curve: pd.Series | None = None
    halts: list = field(default_factory=list)

    @property
    def closed_trades(self):
        return [t for t in self.trades if not t.is_open]

    @property
    def open_trades(self):
        return [t for t in self.trades if t.is_open]


def simulate(
    signal_frames: dict,
    cfg: dict,
    ablation: AblationConfig,
    window: tuple | None = None,
    seed_cash: float = 100_000.0,
    strategy: str = "?",
    window_label: str = "combined",
    leap_tickers: frozenset = frozenset(),
) -> BacktestResult:
    """signal_frames: {ticker: full-history signal frame from
    build_signal_frame}. `window` (start, end) slices each frame AFTER
    signals were computed on full history (locked anti-lookahead design:
    indicators/UT state must never be re-derived on a sub-range)."""
    slippage = cfg["backtest"]["slippage_pct"]
    frames = {}
    for tkr, f in signal_frames.items():
        sliced = f.loc[window[0] : window[1]] if window is not None else f
        if len(sliced) > 0:
            frames[tkr] = sliced

    all_dates = sorted(set().union(*[set(f.index) for f in frames.values()]))
    if not all_dates:
        raise ValueError("simulate: empty window — no bars for any ticker")

    state = PortfolioState(seed_cash, all_dates[0])
    result = BacktestResult(strategy, window_label, seed_cash)
    open_trades: dict[str, Trade] = {}
    pending_entries: dict[str, pd.Timestamp] = {}   # ticker -> signal date
    pending_exits: dict[str, str] = {}              # ticker -> exit reason
    equity_hist, cash_hist = [], []

    delta = leap_delta(cfg)

    for date in all_dates:
        todays = {t: f.loc[date] for t, f in frames.items() if date in f.index}

        # ---- 1. fill pending EXITS at today's open --------------------
        for tkr in sorted(pending_exits):
            if tkr in todays and tkr in state.positions:
                pos = state.positions[tkr]
                fill = todays[tkr]["Open"] * (1 - slippage)
                if pos.kind == "leap" and pos.delta is not None:
                    # exit the delta-approximated position at its modeled
                    # value, consistent with Position.market_value
                    cost_b = pos.cost_basis
                    modeled = cost_b + pos.delta * (pos.shares * fill - cost_b)
                    state.positions[tkr].last_price = fill
                    state.positions.pop(tkr)
                    state.cash.deposit(date, modeled, "sale", tkr)
                    proceeds = modeled
                else:
                    proceeds = state.close_position(date, tkr, fill)
                tr = open_trades.pop(tkr)
                tr.exit_date, tr.exit_price = date, fill
                tr.exit_reason = pending_exits[tkr]
                cost = tr.shares * tr.entry_price
                tr.pnl = proceeds - cost
                tr.pnl_pct = tr.pnl / cost
                result.trades.append(tr)
                del pending_exits[tkr]

        # ---- 2. fill pending ENTRIES at today's open (alphabetical) ---
        for tkr in sorted(pending_entries):
            if tkr not in todays:
                continue
            del pending_entries[tkr]
            if tkr in state.positions and not ablation.ladder_enabled:
                continue  # single-entry primary: never add to a held name
            kind = "leap" if tkr in leap_tickers else "equity"
            cap = (
                cfg["leap"]["single_entry_pct_of_book"]
                if kind == "leap"
                else cfg["sizing"]["max_position_pct_of_book"]
            )
            dollars = cap * state.total_equity
            if ablation.ladder_enabled and kind == "equity":
                # ladder ablation: the cap is built in max_tranches_per_name
                # equal slices instead of one entry (LEAPs never ladder —
                # leap.no_tranche_ladder is unconditional)
                dollars /= cfg["sizing"]["max_tranches_per_name"]
            order = EntryOrder(
                date, tkr, kind, dollars,
                is_tranche_add=tkr in state.positions,
                delta=delta if kind == "leap" else None,
            )
            ok, reasons = check_all_entry_constraints(state, order, cfg)
            if not ok:
                result.rejected_entries.append(RejectedEntry(date, tkr, reasons))
                continue
            fill = todays[tkr]["Open"] * (1 + slippage)
            shares = dollars / fill
            state.open_or_add(date, tkr, kind, fill, shares, order.delta)
            if tkr not in open_trades:
                open_trades[tkr] = Trade(
                    tkr, kind, date, fill, shares,
                    priced_as=PRICING_LABEL if kind == "leap" else "shares",
                )
            else:
                pos = state.positions[tkr]
                t = open_trades[tkr]
                t.shares = pos.shares
                t.entry_price = pos.cost_basis / pos.shares

        # ---- 3. read today's CLOSE signals -> new pendings ------------
        for tkr, row in todays.items():
            if tkr in state.positions and row["exit_signal"] and tkr not in pending_exits:
                pending_exits[tkr] = row["exit_reason"]
            elif (
                tkr not in state.positions
                and row["entry_signal"]
                and tkr not in pending_entries
            ):
                pending_entries[tkr] = date
            elif (
                ablation.ladder_enabled
                and tkr in state.positions
                and state.positions[tkr].kind == "equity"
                and row["entry_signal"]
                and tkr not in pending_entries
            ):
                # tranche add (ablation only): needs room in the ladder and
                # price >= 1.5 x ATR below the previous tranche's entry
                pos = state.positions[tkr]
                spacing = (
                    cfg["sizing"]["tranche_spacing_atr_multiple"] * row["atr"]
                )
                if (
                    len(pos.tranches) < cfg["sizing"]["max_tranches_per_name"]
                    and row["Close"] <= pos.tranches[-1].price - spacing
                ):
                    pending_entries[tkr] = date

        # ---- 4. mark-to-market + kill switch --------------------------
        state.mark_to_market(date, {t: r["Close"] for t, r in todays.items()})
        cb = cfg["circuit_breakers"]
        if (
            state.drawdown_from_peak >= cb["account_drawdown_halt_pct"]
            and (state.halted_until is None or date >= state.halted_until)
        ):
            state.halted_until = date + pd.Timedelta(days=cb["halt_duration_days"])
            result.halts.append(date)
        equity_hist.append(state.total_equity)
        cash_hist.append(state.cash.balance)

    result.trades.extend(open_trades.values())   # still-open at window end
    result.equity_curve = pd.Series(equity_hist, index=all_dates, name="equity")
    result.cash_curve = pd.Series(cash_hist, index=all_dates, name="cash")
    return result
