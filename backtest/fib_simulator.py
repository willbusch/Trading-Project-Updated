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
first (RATIO-based, see below), then earliest gate-clear date, then
ticker alphabetical.

BUG FIX (2026-07-22, found while implementing the "Beat-SPY Package"):
the fill loop used to iterate `sorted(pending_entries)` — ALPHABETICAL —
which silently discarded the ratio-based rank order established when
candidates are frozen into `pending_entries` (dict insertion order, which
DOES preserve the rank). The ratio tiebreak was therefore never actually
deciding contested slots; ticker alphabetical order was. Fixed by
iterating `list(pending_entries)` (insertion/rank order) instead. See
tests/test_ratio_tiebreak.py for a regression test using tickers where
alphabetical and ratio order disagree.
"""
import math
from dataclasses import dataclass, field

import pandas as pd

from backtest.constraints import EntryOrder, check_all_entry_constraints
from backtest.fib_exit import (
    EquityLatchExit,
    FullLatchExitV2,
    LeapDecayExit,
    LeapSimpleExit,
    SimpleFloorExit,
    TrailingFibExit,
)
from backtest.leap_bs_pricing import (
    CONTRACT_MULTIPLIER,
    PRICING_LABEL,
    bs_call_price,
    solve_strike_for_delta,
    target_delta,
)
from backtest.portfolio_state import PortfolioState

# EQUITY exit variant registry (2026-07-20 three-way ablation, extended
# 2026-07-22 with A7's trailing variants). LEAP exit is chosen separately
# (LeapSimpleExit or, when leap_decay_exit=True, LeapDecayExit — A5)
# regardless of this setting — equity and LEAP exits are independent.
EQUITY_EXIT_VARIANTS = {
    "simple_05": lambda dl, hi: SimpleFloorExit(dl, hi, floor=0.5),   # 12-name-round champion
    "simple_09": lambda dl, hi: SimpleFloorExit(dl, hi, floor=0.9),   # pre-A7 official (1.618 hard exit)
    "latch_v2": lambda dl, hi: FullLatchExitV2(dl, hi),               # owner's full-latch design
    "latched_v1": lambda dl, hi: EquityLatchExit(dl, hi),             # original design, reference only
    # A7 (2026-07-22): 1.618 no longer force-sells; trailing exit instead.
    "trail_ut": lambda dl, hi: TrailingFibExit(dl, hi, floor=0.9, mechanic="ut_trail"),
    "trail_pct20": lambda dl, hi: TrailingFibExit(dl, hi, floor=0.9, mechanic="pct_trail", pct_trail_pct=0.20),
    "trail_pct15": lambda dl, hi: TrailingFibExit(dl, hi, floor=0.9, mechanic="pct_trail", pct_trail_pct=0.15),
}

# B2 (2026-07-22) equity sizing variants — all divide the SAME 65%
# equity budget (cfg sizing.equity_budget_pct). "diversify": 6 slots,
# flat entry, never adds. "deepen": 4 slots, enters at 2/3 of the 16.25%
# cap, adds the remaining 1/3 ONLY if the name deepens a full tier below
# its own entry drawdown (using that ticker's OWN gate_threshold as the
# "one tier" unit — a name's gate is fixed per its cap tier, so "one tier
# deeper" = dd_pct_now >= dd_pct_at_entry + gate_threshold; documented
# judgment call, since tier WIDTHS themselves are not uniform 25/30/40).
# "both": 5 slots, same per-unit economics as diversify/deepen, adds
# allowed. None (default) = flat single-entry at cfg's configured
# max_position_pct_of_book/equity_slots, i.e. Part A's locked 4x16.25%
# with no two-stage add — unchanged from every run before this feature.
def _equity_sizing_variants(cfg: dict) -> dict:
    budget = cfg.get("sizing", {}).get("equity_budget_pct", 0.65)
    unit = budget / 6.0
    return {
        "diversify": dict(equity_slots=6, initial_pct=unit, add_pct=0.0, allow_deepen=False),
        "deepen": dict(equity_slots=4, initial_pct=unit, add_pct=unit / 2.0, allow_deepen=True),
        "both": dict(equity_slots=5, initial_pct=unit, add_pct=unit / 2.0, allow_deepen=True),
    }


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
    cost_basis: float = 0.0              # total $ paid across all tranches (B2 deepen-adds)
    entry_dd_pct: float = 0.0            # dd_pct at entry signal — B2 deepen trigger reference
    deepened: bool = False               # B2: has the single allowed deepen-add already fired

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
    recycle_events: list = field(default_factory=list)   # A4: (date, closed_ticker, waiting_ticker)

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
    # equity exit only; see EQUITY_EXIT_VARIANTS. "simple_09" is the
    # pre-A7 STRATEGY.md-official winner of the 2026-07-20 three-way
    # ablation; "trail_ut"/"trail_pct20"/"trail_pct15" are A7 (2026-07-22).
    exit_variant: str = "simple_09",
    idle_cash_spy: "pd.Series | None" = None,  # A3/CHANGE 4: daily SPY return
                                          # credited to idle cash (reserve + floor)
    leap_topcap_eligibility: bool = False,   # A2 (2026-07-22): kind decided by
                                          # top-10-by-cap-proxy rank at entry date,
                                          # not the static leap_tickers set
    leap_decay_exit: bool = False,       # A5 (2026-07-22): LEAP exit floor 0.9->0.7
                                          # past 50% of modeled runway to expiry
    slot_recycling: bool = False,        # A4 (2026-07-22): opportunity-cost valve
    equity_sizing_variant: str | None = None,  # B2 (2026-07-22): "diversify"|"deepen"|"both"
    recycle_trigger: str = "underwater",  # 2026-07-22 valve v2: "underwater" (A4
                                          # original) | "underperformance" (trails
                                          # SPY by >= recycle_underperf_margin
                                          # annualized over the position's hold window)
    spy_close: "pd.Series | None" = None,  # SPY close LEVELS (not returns) — required
                                          # only when recycle_trigger="underperformance"
) -> FibResult:
    slippage = cfg["backtest"]["slippage_pct"]
    seed_cash = cfg["backtest"]["seed_cash"] if seed_cash is None else seed_cash

    # local cfg copy so B2's slot/cap override never mutates the caller's
    # shared config object (this function is called ~dozens of times per
    # grid run against the SAME cfg dict).
    cfg = dict(cfg)
    cfg["sizing"] = dict(cfg["sizing"])
    sizing_variant = None
    if equity_sizing_variant is not None:
        sizing_variant = _equity_sizing_variants(cfg)[equity_sizing_variant]
        cfg["sizing"]["equity_slots"] = sizing_variant["equity_slots"]
        cfg["sizing"]["max_position_pct_of_book"] = (
            sizing_variant["initial_pct"] + sizing_variant["add_pct"]
        )

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
    min_hold_days = cfg.get("slot_recycling", {}).get("min_hold_days", 365)

    for date in all_dates:
        todays = {t: f.loc[date] for t, f in sliced.items() if date in f.index}

        # 1. pending EXITS at open
        for tkr in sorted(pending_exits):
            if tkr in todays and tkr in state.positions:
                pos = state.positions[tkr]
                underlying_open = todays[tkr]["Open"]
                if pos.kind == "leap" and pos.strike is not None:
                    # Real Black-Scholes exit valuation (2026-07-21): the
                    # premium at the fill bar, K and sigma still frozen at
                    # entry, T decayed to today — genuine theta, not a
                    # linear delta multiplier.
                    t_remaining = max((pos.expiry_date - date).days / 365.25, 0.0)
                    raw_premium = bs_call_price(underlying_open, pos.strike, t_remaining, pos.sigma)
                    fill = raw_premium * (1 - slippage) * CONTRACT_MULTIPLIER
                    proceeds = max(pos.shares * fill, 0.0)
                    state.positions.pop(tkr)
                    state.cash.deposit(date, proceeds, "sale", tkr)
                else:
                    fill = underlying_open * (1 - slippage)
                    proceeds = state.close_position(date, tkr, fill)
                tr = open_trades.pop(tkr)
                exit_machines.pop(tkr, None)
                tr.exit_date, tr.exit_price = date, fill
                tr.exit_reason = pending_exits[tkr]
                cost = tr.cost_basis if tr.cost_basis else tr.shares * tr.entry_price
                tr.pnl = proceeds - cost
                tr.pnl_pct = tr.pnl / cost
                result.trades.append(tr)
                del pending_exits[tkr]

        # 2. pending ENTRIES at open (constraint-gated)
        from backtest.drawdown_gate import price_fraction
        for tkr in list(pending_entries):
            if tkr not in todays:
                continue
            _snap = pending_entries.pop(tkr)
            is_add = _snap.get("is_tranche_add", False)

            # B2 deepen-add: tops up an EXISTING equity position.
            if is_add:
                if tkr not in state.positions or tkr not in open_trades:
                    continue   # position closed before the add could fill
                dollars = _snap["add_dollars"]
                order = EntryOrder(date, tkr, "equity", dollars, is_tranche_add=True)
                ok, reasons = check_all_entry_constraints(state, order, cfg)
                if not ok:
                    result.rejected_entries.append(FibRejected(date, tkr, reasons))
                    continue
                fill = todays[tkr]["Open"] * (1 + slippage)
                shares = dollars / fill
                state.open_or_add(date, tkr, "equity", fill, shares)
                tr = open_trades[tkr]
                tr.shares += shares
                tr.cost_basis += dollars
                tr.deepened = True
                continue

            if tkr in state.positions:
                continue
            if leap_topcap_eligibility:
                kind = "leap" if _snap.get("leap_eligible_topcap", False) else "equity"
            else:
                kind = "leap" if tkr in leap_tickers else "equity"
            cap = (cfg["leap"]["single_entry_pct_of_book"] if kind == "leap"
                   else (sizing_variant["initial_pct"] if sizing_variant is not None
                        else cfg["sizing"]["max_position_pct_of_book"]))
            dollars = cap * state.total_equity
            two_yr_high, dip_low = _snap["high_2yr"], _snap["dip_low"]

            if kind == "leap":
                sigma = _snap["realized_vol"]
                if sigma != sigma:   # NaN: insufficient trailing history to price
                    result.rejected_entries.append(
                        FibRejected(date, tkr, ["insufficient realized-vol history"]))
                    continue
                T0 = cfg["leap"]["fib_modeled_expiry_years"]
                dtarget = target_delta(cfg)
                strike = solve_strike_for_delta(_snap["signal_close"], dtarget, T0, sigma)
                underlying_open = todays[tkr]["Open"]
                raw_premium = bs_call_price(underlying_open, strike, T0, sigma)
                contract_cost = raw_premium * (1 + slippage) * CONTRACT_MULTIPLIER
                if not (contract_cost == contract_cost) or contract_cost <= 0:
                    result.rejected_entries.append(
                        FibRejected(date, tkr, ["degenerate option price"]))
                    continue
                num_contracts = math.floor(dollars / contract_cost)
                if num_contracts < 1:
                    result.rejected_entries.append(
                        FibRejected(date, tkr, ["book too small for 1 contract"]))
                    continue
                order = EntryOrder(date, tkr, kind, num_contracts * contract_cost, delta=dtarget)
                ok, reasons = check_all_entry_constraints(state, order, cfg)
                if not ok:
                    result.rejected_entries.append(FibRejected(date, tkr, reasons))
                    continue
                expiry_date = date + pd.Timedelta(days=int(T0 * 365.25))
                state.open_or_add(date, tkr, kind, contract_cost, num_contracts,
                                  delta=dtarget, strike=strike, expiry_date=expiry_date,
                                  sigma=sigma, underlying_price=underlying_open)
                machine = (LeapDecayExit(dip_low, two_yr_high, cfg["leap"].get("decay_tighten_at_frac", 0.5),
                                        cfg["leap"].get("decay_floor_before", 0.9),
                                        cfg["leap"].get("decay_floor_after", 0.7))
                          if leap_decay_exit else LeapSimpleExit(dip_low, two_yr_high))
                exit_machines[tkr] = machine
                cost0 = num_contracts * contract_cost
                open_trades[tkr] = FibTrade(
                    tkr, kind, date, contract_cost, num_contracts, two_yr_high, dip_low,
                    price_fraction(underlying_open, dip_low, two_yr_high), peak_price=underlying_open,
                    priced_as=PRICING_LABEL, stale_at_entry=bool(_snap["stale"]),
                    cost_basis=cost0,
                )
                continue

            order = EntryOrder(date, tkr, kind, dollars, delta=None)
            ok, reasons = check_all_entry_constraints(state, order, cfg)
            if not ok:
                result.rejected_entries.append(FibRejected(date, tkr, reasons))
                continue
            fill = todays[tkr]["Open"] * (1 + slippage)
            shares = dollars / fill
            state.open_or_add(date, tkr, kind, fill, shares)
            machine = EQUITY_EXIT_VARIANTS[exit_variant](dip_low, two_yr_high)
            exit_machines[tkr] = machine
            open_trades[tkr] = FibTrade(
                tkr, kind, date, fill, shares, two_yr_high, dip_low,
                price_fraction(fill, dip_low, two_yr_high), peak_price=fill,
                priced_as="shares", stale_at_entry=bool(_snap["stale"]),
                cost_basis=dollars, entry_dd_pct=float(_snap.get("dd_pct_at_signal", 0.0)),
            )

        # 3. read CLOSE signals -> schedule next-bar exits / collect entries
        entry_candidates = []
        for tkr, row in todays.items():
            price = row["Close"]
            if tkr in state.positions:
                open_trades[tkr].peak_price = max(open_trades[tkr].peak_price, price)
                if tkr in pending_exits:
                    continue
                tr = open_trades[tkr]
                # LEAP modeled expiry ("rides to Fib target OR expiry"):
                # force-exit at entry + fib_modeled_expiry_years. force-close
                # 6mo rule is suspended for this strategy.
                if tr.kind == "leap":
                    T0 = cfg["leap"]["fib_modeled_expiry_years"]
                    age_yrs = (date - tr.entry_date).days / 365.25
                    if age_yrs >= T0:
                        pending_exits[tkr] = "leap_modeled_expiry"
                        continue
                    age_frac = age_yrs / T0 if T0 > 0 else 0.0
                    do_exit, reason = exit_machines[tkr].step(price, bool(row["exit_ut_sell"]), age_frac=age_frac)
                    if do_exit:
                        pending_exits[tkr] = reason
                    continue

                # B2 deepen-add trigger: fires at most once per position,
                # only when this bar's drawdown has reached a full tier
                # deeper than the drawdown AT ENTRY (own gate_threshold as
                # the "one tier" unit — see _equity_sizing_variants doc).
                if (sizing_variant is not None and sizing_variant["allow_deepen"]
                        and not tr.deepened and tkr not in pending_entries):
                    if row["dd_pct"] >= tr.entry_dd_pct + row["gate_threshold"]:
                        pending_entries[tkr] = {
                            "is_tranche_add": True,
                            "add_dollars": sizing_variant["add_pct"] * state.total_equity,
                        }

                do_exit, reason = exit_machines[tkr].step(price, bool(row["exit_ut_sell"]))
                if do_exit:
                    pending_exits[tkr] = reason
            else:
                if (row["eligible"] and row["entry_ut_buy"]
                        and tkr not in pending_entries):
                    if row["stale"] and not include_stale:
                        result.stale_excluded.append((date, tkr))
                        continue
                    entry_candidates.append((tkr, row))

        # RATIO-BASED slot-selection tiebreak (2026-07-21, owner override —
        # replaces the old raw-deepest-drawdown-first rule): rank by
        # drawdown / that name's OWN tier threshold — how far PAST its own
        # gate it is, not the raw depth. A $600B name 32% down (1.28x its
        # 25% gate) now beats an $80B name 44% down (1.10x its 40% gate),
        # letting mega-caps win contested slots instead of always losing
        # to small-caps that can post deeper raw drawdowns. Falls back to
        # earliest gate-clear, then alphabetical — unchanged. This order
        # is preserved into pending_entries' insertion order and MUST be
        # respected at fill time (see the module-level bug-fix note).
        entry_candidates.sort(
            key=lambda tr: (
                -(tr[1]["dd_pct"] / tr[1]["gate_threshold"]),
                tr[1]["gate_clear_date"],
                tr[0],
            )
        )

        # slot-time recycling valve. Fires for the SINGLE best-ranked
        # waiting EQUITY candidate that would otherwise be rejected because
        # equity slots are full, freeing ONE held equity position that is
        # held >= min_hold_days AND fails the eligibility test below. This
        # is an opportunity-cost valve, not a stop-loss; the LEAP is never
        # touched.
        #
        # Two triggers (2026-07-22 valve v2, owner-specified):
        #   "underwater" (A4 original): position currently below its entry
        #       price. FINDING: this targeted the wrong thing — the real
        #       slot-blockers were mediocre WINNERS (e.g. UBS +49% over
        #       ~1160d ~= 15%/yr), which this trigger never touches.
        #   "underperformance" (v2): position's annualized return over its
        #       OWN hold window trails SPY's annualized return over the
        #       identical window by >= recycle_underperf_margin (5%). A
        #       winner that BEATS SPY is never eligible; a mediocre winner
        #       that lags SPY by >5%/yr now is.
        if slot_recycling and cfg.get("slot_recycling", {}).get("enabled", True):
            equity_limit = cfg["sizing"]["equity_slots"]
            margin = cfg.get("slot_recycling", {}).get("recycle_underperf_margin", 0.05)
            if state.slots_used("equity") >= equity_limit:
                for tkr, row in entry_candidates:
                    if tkr in state.positions or tkr in pending_entries:
                        continue
                    is_leap_kind = (bool(row.get("leap_eligible_topcap", False))
                                    if leap_topcap_eligibility else tkr in leap_tickers)
                    if is_leap_kind:
                        continue
                    recyclable = []
                    for ptkr, pos in state.positions.items():
                        if pos.kind != "equity":
                            continue
                        entry_date = pos.tranches[0].date
                        if (date - entry_date).days < min_hold_days:
                            continue
                        entry_price = pos.cost_basis / pos.shares if pos.shares else pos.last_price
                        pos_ret = pos.last_price / entry_price - 1.0
                        if recycle_trigger == "underperformance":
                            hold_years = max((date - entry_date).days / 365.25, 1e-9)
                            pos_ann = (1.0 + pos_ret) ** (1.0 / hold_years) - 1.0
                            if spy_close is None:
                                continue
                            spy_e = spy_close.asof(entry_date)
                            spy_n = spy_close.asof(date)
                            if not (spy_e and spy_e > 0 and spy_n and spy_n > 0):
                                continue
                            spy_ann = (spy_n / spy_e) ** (1.0 / hold_years) - 1.0
                            gap = pos_ann - spy_ann     # negative = lagging SPY
                            if gap > -margin:           # not lagging by the full margin -> keep
                                continue
                            recyclable.append((ptkr, gap, entry_date))
                        else:  # "underwater"
                            if pos.last_price >= entry_price:   # winners untouched
                                continue
                            recyclable.append((ptkr, pos_ret, entry_date))
                    if recyclable:
                        # worst first (most underwater / most-lagging-SPY), then oldest
                        recyclable.sort(key=lambda x: (x[1], x[2]))
                        worst_tkr = recyclable[0][0]
                        if worst_tkr not in pending_exits:
                            pending_exits[worst_tkr] = "slot_recycle_valve"
                            result.recycle_events.append((date, worst_tkr, tkr))
                    break   # only ever consider the single top-ranked waiting candidate per bar

        for tkr, row in entry_candidates:
            # freeze anchors at THIS bar's close (all known now) so the
            # fill bar can't leak into them
            snap = {
                "high_2yr": row["high_2yr"],
                "dip_low": row["dip_low"],
                "stale": bool(row["stale"]),
                "realized_vol": row["realized_vol"],   # sigma proxy, signal-bar-frozen
                "signal_close": row["Close"],            # K solved from THIS bar, not the fill
                "dd_pct_at_signal": float(row["dd_pct"]),
            }
            if leap_topcap_eligibility:
                snap["leap_eligible_topcap"] = bool(row.get("leap_eligible_topcap", False))
            pending_entries[tkr] = snap

        # A3/CHANGE 4: credit idle cash the day's SPY return before marking
        # (2026-07-22: this now covers the LEAP reserve too when spendable
        # — the reserve is no longer distinguished from ordinary idle cash,
        # it is ALL held in SPY per A1/A3).
        if idle_cash_spy is not None and date in idle_cash_spy.index:
            r_spy = idle_cash_spy.loc[date]
            bal = state.cash.balance
            if bal > 0 and r_spy == r_spy:
                pnl = bal * r_spy               # SPY moves the idle-cash sleeve
                if pnl >= 0:
                    state.cash.deposit(date, pnl, "spy_idle_yield", "SPY")
                else:                          # down day: |pnl| < bal, safe
                    state.cash.withdraw(date, -pnl, "spy_idle_yield", "SPY")

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
