# STRATEGY.md

**Version:** 5.0
**Last updated:** July 22, 2026
**Owner:** Will Busch
**Companion files:** `PLAN.md`, `GOAL.md`, `investor-one-pager-will-busch.md`, `portfolio-audit-2026-07-20.md`, `reports/beat_spy_package.md`

> **The one-line thesis:**
> *I buy quality that's temporarily broken, and I hold until it retraces most of the way back.*
>
> Entry is fear, defined by price against its own recent history relative
> to a market-cap-scaled bar. Exit is a structured retracement zone, not a
> fixed target. This is a **full-cycle system**, not a bounce trade —
> holds run months, sometimes years. LEAPs are priced as real options now,
> not a linear approximation — they are the intended profit driver and the
> single largest source of risk in the book, in that order.

---

## ⚠️ STATUS: STILL LOSES TO SPY RISK-ADJUSTED — "BEAT-SPY PACKAGE" RUN, 2026-07-22

**The 2026-07-21 run's headline finding (8.9% CAGR / 62.8% max drawdown,
losing to SPY on both counts) prompted an 8-part fix package (A1–A8:
sizing, top-10-by-cap LEAP eligibility, spendable reserve, slot recycling,
LEAP decay exit, LEAP-only kill switch, trailing exit, dashboard fix) plus
a 12-cell entry/sizing/trailing comparison grid. Full detail:
`reports/beat_spy_package.md`.**

**Result: every fix landed as designed and materially improved the
strategy — but the package STILL does not beat SPY risk-adjusted.** Every
one of the 12 cells tested now runs 44.9%–48.9% max drawdown pre-vault
(down from 62.8%, a real improvement) — but that is still roughly DOUBLE
SPY's 25.4% max drawdown over the same span. Raw returns are enormous
(127%–1064% pre-vault) but the top-ranked cells are concentrated in 2–3
large LEAP trades (TSLA twice, META once) that happened to land inside two
of the largest individual-stock rallies in this dataset's history — flagged
explicitly in the report as a likely lucky-timing result, not proven edge,
per this project's own "too good to be true = leak-hunt it" discipline.
**Per the rule this run was scoped under — beat SPY on BOTH return and max
drawdown, or it isn't a win — the honest verdict is NO.** See
`reports/beat_spy_package.md` for the full 7-question answer set, the
12-cell ranking table, the overfitting guard, and the cumulative
attribution ladder (which fix mattered: A2, top-10-by-cap LEAP eligibility,
by a wide margin — the only step that improved both return AND risk
together).

**MU-2021 is fixed.** The flat $500B floor that let a ~$80B-cap MU qualify
for a LEAP on today's snapshot cap is gone — LEAP eligibility is now
top-10-by-market-cap-proxy, ranked, at the entry date. MU is never in that
top-10 list in any year of the backtest; the −100%/62.8%-drawdown MU LEAP
does not recur anywhere in the 12-cell grid.

---

## ⚠️ PRIOR STATUS (2026-07-21, superseded by the run above): LOCKED CONFIGURATION, RESEARCH RE-CLOSED

Backtested across five research generations (2026-07-19 through 21). This
version locks the configuration: **daily entry / weekly exit is the only
cell run** (no longer a matrix search), the **tiered drawdown gate is now
official** (was experimental as of 2026-07-20), the **slot tiebreak is
ratio-based** (drawdown ÷ that name's own gate threshold, not raw
drawdown), and — the headline change — **LEAP P&L is now priced with a
real Black-Scholes engine**, not the flat 0.55-delta approximation every
prior version used. See Part 2 and Part 4 below for what changed and why;
full run: `reports/fib_final_run.md`.

**What real LEAP pricing changed:** every existing LEAP trade was
mispriced by the old model. JPM, ASML, TSLA, and one MU trade were
understated 2.5–3.8x (the old model showed a *fraction* of the
underlying's move; a real option shows a *multiple* of it — genuine
leverage). A second MU trade — underlying nearly flat — went from
"roughly breakeven" under the old model to **expired completely
worthless (−100%)** under real pricing, a theta-driven outcome the old
linear model could not represent at all. Full-span max drawdown rose to
**62.8%** (vs 17–40% in every prior round) — traced directly to that same
MU LEAP sitting open through the entire 2022 bear market at 33% of book
before expiring worthless. **This is leverage cutting both ways, exactly
as the design change intended to expose, not a bug.**

Still: **no real capital is deployed on this system.** The data
limitation is unchanged and now extends to three things instead of two:
survivorship-biased universe membership, current-snapshot market-cap
tiering, AND (new) sigma modeled from realized (not implied) volatility.
Real LEAP pricing makes the P&L **honest**; it does not remove
survivorship bias and does not prove edge. Genuine validation needs
point-in-time membership, fundamentals, and market caps — Robinhood
cannot provide any of the three. Research formally re-closes after this
run (see `docs/PLAN.md`).

---

## PART 0 — RETIREMENT NOTE: the RSI(3) system

**Formally retired 2026-07-19**, after three research generations replaced
it piece by piece: RSI(3)+SMA(200) entry → UT-Bot + drawdown-gate entry;
RSI(70/60) momentum exit → Fibonacci-zone exit; 3-tranche ATR ladder →
single entry. The RSI system is preserved in code
(`backtest/{signals,simulator,orchestrate,reporting}.py`, the "A/B/C/D"
strategies) for reference and is no longer run, tracked, or reported on.
Its full history and the four owner overrides that preceded its
retirement are in `docs/PLAN.md`'s override log.

**This document previously described the RSI(3) system as current through
2026-07-19 without noting the replacement — that gap is the drift this
rewrite closes.** The engine swap itself (RSI+SMA → drawdown-gate+UT-Bot+Fib)
is now logged as an override below, which it should have been at the time.

---

## PART 1 — THE UNIVERSE (What We Buy)

### Quality Gate — fail any, disqualified

| Filter | Rule | Why |
|---|---|---|
| **Index** | SPY or QQQ membership | Institutional coverage, real liquidity, no delisting risk. **Data caveat below — read it.** |
| **Market cap — equities** | **≥ $10B** at evaluation time | Big enough to survive a drawdown. |
| **Market cap — LEAPs** | **Top 10 US companies by market-cap PROXY, ranked, as of the entry date** (CHANGED 2026-07-22, was a flat $500B+ floor) | Leverage only on the very largest names, evaluated AT THE TIME, not retroactively. Replaces the NFLX rule's mechanism (still true in spirit) — see Part 1a. |
| **Profitability** | Positive trailing net profit margin | Screens out dying companies riding the same 40%-down filter as temporarily-hated quality. |
| **Avg volume** | **> 1M/day** | Exit as easily as entry. |
| **Sector** | Any | The chart is the thesis. |

**🔴 DATA CAVEAT — read before trusting the eligible list:** the data source
(Robinhood MCP) has **no point-in-time index-membership filter** and **no
historical fundamentals** — only current snapshots. The backtested and
live-scanned universe is actually *"names that are large-cap, profitable,
and liquid today,"* not *"names that were in SPY/QQQ and profitable at each
historical date."* This is a survivorship + fundamental-snapshot proxy,
not a true point-in-time SPY/QQQ screen. It inflates every historical
result in the strategy's favor. Fixing this requires a different data
source — flagged as the top open item in `PLAN.md`.

### Anti-Portfolio — never, regardless of setup

- Penny stocks / sub-$10
- Meme stocks, crypto
- 0DTE, weeklies, any short-dated option
- **LEAPs on anything outside the top 10 US companies by market-cap proxy at entry** (CHANGED 2026-07-22, was "under $500B" — see Part 1a)
- OTM LEAPs at entry
- LEAPs under 1.75 years to expiry at entry

### Part 1a — Top-10-by-Cap LEAP Eligibility (CHANGED 2026-07-22, replaces the flat $500B floor)

**The flat $500B floor applied TODAY's market cap retroactively across a
name's entire backtest history** — this is exactly what let a ~$80B-cap
2021 MU qualify for a LEAP, because MU is >$500B *today*. Replaced by a
RANK: a LEAP underlying must be in the **top 10 US companies by market-cap
proxy AS OF THE ENTRY DATE** — computed BY RANK, not a hardcoded name list
(explicitly rejects hindsight-biased "Mag 7" hardcoding).

**Proxy method** (`backtest/leap_topcap.py`) — true point-in-time market
cap doesn't exist in this data source (current-snapshot only, same
limitation as everywhere else in this document): implied shares
outstanding are backed out as `current_cap ÷ latest_close`, then
multiplied by each ticker's OWN historical close to get a genuine
time-varying cap proxy, ranked cross-sectionally per date. Shares
outstanding drifts far more slowly than price, so this is a real
improvement over the flat floor, but it is still a proxy (buybacks/
issuance drift held constant across history) — flagged, not hidden.

**Confirmed: MU is never in the top-10 list in any year of the backtest.**
The specific LEAP that drove the 2026-07-21 run's 62.8% max drawdown and
−100% expiry does not recur. Full year-by-year eligible-name table:
`reports/beat_spy_package.md`.

---

## PART 2 — THE ENTRY (When We Buy)

### The Drawdown Gate — TIERED (✅ ADOPTED 2026-07-21, was experimental 2026-07-20)

Price is below its own hybrid 2-year-high anchor by at least:

| Market cap | Required drawdown |
|---|---|
| **$500B+** | **25%** |
| **$150B – $500B** | **30%** |
| **Under $150B** | **40%** |

LEAP underlyings keep the existing $500B+ requirement (additive to the
quality gate); their drawdown threshold is the 25% row, unchanged from
before. **No hard cap floor** — smaller names simply need a deeper
drawdown to qualify, they are never outright excluded by cap alone (the
$10B+ quality-gate floor still applies separately, upstream, in Part 1).

**The mechanical delta vs the prior flat 40%/25% gate:** only the
**$150B–$500B band actually changes** (40%→30%) — $500B+ names were
already 25% and sub-$150B names were already 40% under the old gate.
73 of the 200 universe names fall in the affected band.

**🔴 Data limitation (flagged, not hidden):** market cap is a CURRENT
snapshot only — no point-in-time history exists from this data source, so
a name's tier is fixed at TODAY's cap and applied across its entire
backtest history. This is the same current-proxy limitation universe
membership already carries, extended to the tier assignment itself. The
anchor/eligibility computation downstream is still strictly forward-only
and lookahead-tested — only the threshold VALUE is a static input, not a
time-varying lookahead.

**History (2026-07-20 exploration, `reports/fib_tiered_gate.md`):** trades
spread across 2021–2026 instead of clustering almost entirely in 2020 —
real, verified improvement on the crash-concentration problem. On the
former flat-gate champion cell specifically it LOWERED trade count and
total return via an emergent slot-competition effect (more eligible names
compete for the same throttle, crowding out some big winners) — verified
as real, not a bug. No single cell in that 6-cell exploration delivered an
unambiguous win. **Adopted anyway on 2026-07-21** as part of the locked
configuration (alongside real LEAP pricing and the ratio tiebreak below) —
the owner's call, not a data-driven "winner." `reports/fib_final_run.md`
has the run under the full locked configuration.

**The hybrid anchor:** a rolling 504-trading-day (2yr) high by default;
when a name's true multi-year peak sits *outside* the 504-day window but
within ~4 years, the extended-lookback high is used instead. This fixes
the "aged-out peak" problem young or long-depressed names hit under a
strict 2yr window (HOOD/SOFI's 2021 IPO peaks are the reference case —
see `backtest/drawdown_gate.py`). Forward-only; lookahead-tested.

**Dip low:** the lowest low since the drawdown gate most recently cleared,
through the entry bar — never a future bar.

**Fib levels** (fractions of the dip-low-to-high move):
`level = dip_low + fraction × (two_yr_high − dip_low)`, at 0.5 / 0.9 / 1.0
/ 1.1 / 1.5 / 1.618.

### The Trigger

A **UT-Bot buy signal** (key=1, ATR period=10, Heikin Ashi off) on the
entry timeframe. **LOCKED 2026-07-21: daily entry / weekly exit is the
only cell run** — no longer a timeframe matrix search. (UT-Bot ported from
the Pine v4 "UT Bot Alerts" script; see `screener/ut_bot.py`.)

*No RSI, no SMA(200), no weekly-lower-lows filter in the active entry
logic — all replaced by the drawdown gate + UT-Bot trigger above.*

---

## PART 3 — SIZING (Equities)

| Rule | Value |
|---|---|
| **Position sizing** | Single entry, one shot by default — **no tranche ladder** (demoted to an unused ablation variant; the RSI system's 3-tranche ATR ladder is retired with it). Position size is measured **AT ENTRY ONLY** — a winner growing past its entry size is NOT a violation and is never trimmed (no trim/rebalance logic exists in this codebase, confirmed 2026-07-22). |
| **Max position** | **16.25% of book** per name (CHANGED 2026-07-22, was 15% — book is now 30% LEAP / 65% across 4 equities / 5% cash floor, see below) |
| **Slots** | **4 equity + 1 LEAP** (5 total) — unchanged 2026-07-22. |
| **Max new positions per week** | **2** |
| **Min cash floor** | **5%** — held in SPY, not idle cash, and spendable same-day (CHANGED 2026-07-22, see Part 4a-reserve below) |
| **Full slots** | New candidates WAIT for a natural Fib exit **OR the new 2026-07-22 slot-time recycling valve** — see Part 3a. Still no displacement of a position in profit, ever. |

### Part 3a — Slot-Time Recycling Valve (NEW 2026-07-22)

An **opportunity-cost valve, NOT a stop-loss.** A held equity position
becomes eligible for forced recycle only if ALL of: held ≥ 12 months,
currently BELOW its entry price, AND a higher-ranked candidate (by the
existing ratio tiebreak) is waiting for a slot that is full. **Winners in
profit are never touched by this rule, ever.** See
`backtest/fib_simulator.py`'s slot-recycling block and
`tests/test_beat_spy_package.py`.

**2026-07-22 finding:** in the champion cell of the Beat-SPY run, this
valve fired 5–6 times pre-vault and force-closed legacy names (MUFG, MMM,
LYG, BABA, NEM) — but the replacement trades did NOT outperform enough
within the window to offset the turnover; pre-vault return actually
DROPPED when this valve was added on top of A2/A3 (see the cumulative
attribution table in `reports/beat_spy_package.md`). Kept as a real,
tested feature — genuinely reduces dead capital — but it is not a free
lunch, and that tradeoff is now on the record rather than assumed away.

### Slot-Selection Tiebreak — RATIO-BASED (CHANGED 2026-07-21)

When more names clear the gate + trigger on the same day than there are
free slots: rank by **drawdown ÷ that name's own tier threshold** — how
far PAST its own gate it is, not the raw depth. A $600B name 32% down
(1.28× its 25% gate) now beats an $80B name 44% down (1.10× its 40%
gate), letting mega-caps win contested slots instead of always losing to
small-caps that can post deeper raw drawdowns. Falls back to **earliest
gate-clear date**, then **alphabetical** — unchanged. Verified working in
the 2026-07-21 run, not just unit-tested: on 2025-01-06, AMAT ($421B) won
a contested slot over CVS ($137B), HOOD ($90B), MDT ($106B), and QCOM
($181B). (Old rule — deepest raw drawdown first, defined 2026-07-19 —
retired; kept in code for reference.)

---

## PART 4 — THE LEAP SLEEVE (Different Rules)

| Rule | Spec | Why |
|---|---|---|
| **Underlying** | **Top 10 US companies by market-cap proxy, ranked, as of entry date** (CHANGED 2026-07-22, was a flat $500B+ floor) | Leverage only on the very largest names, evaluated AT THE TIME — see Part 1a. |
| **Entry trigger** | Same drawdown gate (25% tier) + UT-Bot buy | The LEAP is the equity thesis with a multiplier. |
| **Delta at entry** | **0.55–0.65** (midpoint 0.60, unchanged since 2026-07-21) | Owner override — see override log. |
| **Expiry** | **1.75 years minimum** at entry, **2 years preferred** (2.0yr also used as the modeled tenor T0 for strike-solving and theta decay) | Time to be right; hard floor, not a target. |
| **Force-close-at-6-months** | **SUSPENDED for this strategy only.** LEAPs ride to the Fib exit or the modeled 2-year expiry. | The Fib exit is the only exit signal this strategy trusts; a time-based override would contradict it. |
| **Sizing** | Single entry, **30% of book cap** (CHANGED 2026-07-22, was 33%) — single-entry cap and total-sleeve cap are IDENTICAL by design, since only ONE LEAP is ever held at a time (no stacking) | Book is now 30% LEAP / 65% across 4 equities / 5% cash floor. |
| **Pricing model** | Real Black-Scholes delta-curve engine (unchanged since 2026-07-21). | See `backtest/leap_bs_pricing.py`. |
| **Exit floor (NEW 2026-07-22)** | Tightens from 0.9 to 0.7 once the position has burned ≥50% of its modeled runway to expiry. **No hard time-based force-close** (explicitly rejected by the owner) — a LEAP that never gets a UT sell signal above the tightened floor still rides to 1.618 or modeled expiry exactly as before. | Risk-reduction as an aging option's convexity thins out, without a hard time-close. See `backtest/fib_exit.py::LeapDecayExit`. |

### 4a. Real LEAP Pricing (2026-07-21 — retires the flat approximation)

**The flat static-delta model is gone.** Every LEAP trade in the backtest
was previously priced as `cost_basis + 0.55 × (underlying's dollar move)`
— a straight line. That systematically UNDERSTATED LEAP returns: it made
options look like a fraction of the underlying's move when a real option
is a multiple of it, and it could never produce a worthless expiry no
matter how far out of the money the position drifted.

**The new model:** genuine Black-Scholes pricing, with strike (K) and
volatility (σ) **frozen at entry** and only the underlying price (S) and
remaining time (T) evolving day to day:
- **σ** = the underlying's own trailing 252-day realized volatility as of
  the entry signal bar — the standard proxy for implied vol when no
  historical vol surface is available (this data source doesn't serve
  one). Forward-only by construction (a rolling stat).
- **K** is solved from the target delta (0.55–0.65 midpoint = 0.60) at
  entry via closed-form delta inversion.
- Position sizing is now **real contracts at a real premium** (dollars ÷
  premium-per-contract, floored to whole contracts), not a delta-scaled
  share-equivalent.

This produces real convexity (percentage moves LARGER than the
underlying's, not smaller), real theta decay, and — restored — a genuine
possibility of **expiring worthless**. Verified in the 2026-07-21
correction run (`reports/fib_final_run.md`): JPM/ASML/TSLA were
understated 2.5–3.8× by the old model; one MU trade flipped from
"roughly breakeven" to **expired completely worthless (−100%)** under
real pricing, on an underlying that barely moved — pure theta decay the
old model could never show.

**Disclosed simplifications** (minor next to the core convexity fix): σ
is *realized*, not *implied*, volatility, held constant for the trade's
life rather than tracking a real IV surface; the risk-free rate is a
constant 4% assumption (no historical yield curve is available either).
Real historical option data (confirmed reachable for expired contracts —
see the 2026-07-19 feasibility spike) was used as a **post-hoc validation
check** against this model's output for the specific trades this backtest
produced, not as the live pricing engine — the simulator cannot call
Robinhood MCP tools mid-run (architecture constraint, see
`scanner/refresh.py`), so it cannot know which contract to fetch before
the simulation that decides which trades occur has already run.

### 4b. LEAP Reserve — REVERSED 2026-07-22: spendable working capital, not a wall

**This section directly REVERSES the 2026-07-21 "dedicated reserve, not
backfilled" model below it (kept, struck through in spirit, for the
override-log record).** The owner's explicit 2026-07-22 call: the 30% LEAP
allocation sits in **SPY, mark-to-market daily** (not idle cash) — and
equities MAY draw on it. When a LEAP qualifies, SPY/free capital is sold to
fund it; the reserve is working capital, not a wall that blocks a qualified
equity entry.

- **LEAP held:** 1 LEAP (30%) + 4 equities (16.25% each = 65%) + 5% cash
  (in SPY).
- **No LEAP qualifies:** the 30% is available to equities too, subject only
  to the normal 4-slot / 16.25%-per-name / 5%-cash-floor limits — it is NOT
  reserved from them.

Enforced by `backtest/constraints.py:check_leap_reserve`, now gated by
`leap.reserve_spendable` (default `true`): when set, the reserve-wall check
no-ops for equity orders entirely; only the ordinary cash-floor check
applies. Idle cash (which now includes the former "reserve") is marked to
SPY's daily return via `idle_cash_spy`, matching the wording above.

**2026-07-22 finding:** in the champion cell, this change (A3) added
return but WORSENED max drawdown (40.1%→47.5% pre-vault in the cumulative
attribution table) — spending the reserve on equities adds exposure
without a matching risk cut. Kept as the owner's explicit call, logged
honestly rather than framed as a pure win.

### 4b-prior (2026-07-21, REVERSED above — kept for the override-log record)

The 33% LEAP allocation was **reserved capital**, not backfilled into a
5th equity when no LEAP currently qualified — enforced by the same
`check_leap_reserve` function, before `reserve_spendable` existed.
**Rationale at the time:** the LEAP is the intended profit driver; keep
dedicated dry powder ready to strike a leveraged mega-cap bet the moment
one qualifies. See the override log for the explicit reversal record.

### 4c. Live Execution Only — the VOO Reserve (NOT modeled in the backtest)

**This is a live cash-management rule, never simulated.** Idle capital —
the 33% LEAP reserve AND the 5% floor — is held in **VOO, not literal
cash**, when trading for real. A triggering setup sells VOO to fund the
entry. Dry powder earns market returns while waiting instead of sitting
idle.

The backtest does not model this: the existing SPY-idle-cash benchmark
already captures functionally identical behavior (idle funds earning the
index), so building it into the simulator would duplicate logic without
adding information.

**The tradeoff (documented, not resolved):** VOO breathes with the
market. In a downturn, the reserve is DOWN exactly when dip-buy setups
are triggering — the trade becomes "sell a down index to buy a
deeper-down quality name," which is acceptable by design, but it means
the reserve is not a fixed-dollar floor. Size accordingly.

### Expired-Worthless LEAPs

**Now representable** (was "cannot be modeled" under the retired flat
approximation — see Part 4a). A LEAP whose underlying stays flat or drops
while held through its modeled 2-year tenor can and does expire at zero
under the real pricing engine; the 2026-07-21 run produced exactly one
such case (MU, entered 2021-10-21).

### The NFLX Lesson (retained from the RSI system — still true)

$112C, June 2027, NFLX at $73.65 = 34% OTM, 11 months left at entry. Violated
three rules at once: sub-$500B underlying, deep OTM, no trigger at entry.
Held to expiry by owner decision (2026-07-15 override) despite failing the
current strategy on all three counts — a known, accepted exception, not a
precedent.

---

## PART 5 — THE EXIT (When We Sell)

*Fibonacci retracement zones, referencing the same anchors frozen at entry.
Price is expressed as a fraction of the dip-low-to-high move
(dip_low = 0.0, two_yr_high = 1.0, target = 1.618).*

### Equity Exit — CHANGED 2026-07-22: 1.618 is no longer a hard exit

**The 2026-07-20 winner (0.9 floor, no latch) is UNCHANGED below 1.618.**
What changes is what happens AT 1.618 — it no longer force-sells the
position (`backtest.fib_exit.TrailingFibExit`, config keys
`exit_variant="trail_ut"` / `"trail_pct20"` / `"trail_pct15"`):

| Zone | Rule |
|---|---|
| below 0.9 | Hold — unchanged |
| 0.9 → 1.618 | Any UT sell (exit timeframe) → full exit — unchanged |
| **1.618+** | **No longer a hard exit.** Switches PERMANENTLY into a trailing exit off the running peak price: `ut_trail` (exit on the next UT-sell event while trailing) or `pct_trail` (exit on a 15–20% retracement from peak). Tested both in the 2026-07-22 12-cell grid. |

**Why:** the 2026-07-21 run's post-mortem found winners like HOOD (+427%)
and APP (+314%) were force-sold at the fixed 1.618 target while still
climbing. This removes that cap. Peak-price tracking is forward-only by
construction and lookahead-tested (`tests/test_fib_exit.py`).

The pre-1.618 design (0.9 floor, no latch) is still the winner of the
2026-07-20 three-way ablation (beat both the prior 0.5-floor champion and
a full-latch design) — see `reports/fib_final_ablation.md`. That part of
the exit is unchanged.

### LEAP Exit — simple, no latch

| Zone | Rule |
|---|---|
| below 0.9 | Hold |
| 0.9 → 1.618 | Any UT sell (exit timeframe) → full exit |
| 1.618 | Hard automatic exit |

### 🚨 THE CASH RULE — unchanged, still the most important line in this document

> **ALL proceeds from ANY sale go to CASH. Never directly into a position I
> am currently underwater on.**

Enforced structurally in `backtest/constraints.py` / `portfolio_state.py`,
with an adversarial test guarding it — same-bar sale proceeds cannot fund
an add to an underwater name. This rule survived the engine replacement
unchanged; it is the one piece of the original strategy that was never in
question.

### There Is No Loss Exit Below the Floor

By design: below the exit floor (0.5 or 0.9, depending on the ablation
winner), a losing or flat position is held, not sold on a stop. **"The
Gap"** — trades that peaked above entry, never reached 1.618, never
triggered a zone exit, and closed at a loss or gave back most of their
peak gain — is tracked explicitly in every backtest report as the
quantified cost of this design choice.

---

## PART 6 — RISK CONTROLS

| Control | Limit |
|---|---|
| Max positions | **5** (4 equity + 1 LEAP) |
| Max single equity position | **16.25%** — CHANGED 2026-07-22, was 15% |
| Max LEAP sleeve (single entry, real option notional) | **30%** — CHANGED 2026-07-22, was 33% |
| LEAP reserve when no LEAP held | **30%, held in SPY, SPENDABLE by equities** — REVERSED 2026-07-22, was "33% cash, not backfilled" |
| Min cash | **5%**, held in SPY, spendable same-day |
| Tranche ladder | **Retired** for the default cell (single entry only); a 2-stage deepen-add is a tested B2 grid variant only, see `reports/beat_spy_package.md` |
| Max new positions per week | **2** |
| Full slots | Natural exit, **or the new 2026-07-22 slot-time recycling valve** (Part 3a) — never a winner in profit |
| **🛑 ACCOUNT KILL SWITCH** | **−30% trigger UNCHANGED. SCOPE narrowed 2026-07-22: halts new LEAP entries/sizing-ups only. Equity dip-buys continue uninterrupted through a halt.** |
| LEAP exit floor | Tightens 0.9→0.7 past 50% of modeled runway to expiry — new 2026-07-22, no hard time-close |

### Why the kill switch (and why its scope narrowed)

No stops on open losers + leverage (LEAP sleeve, real leverage via
Black-Scholes pricing) + concentration (5 slots, one of them a single-name
option position) = a real path to a very bad year — the 2026-07-21 run's
62.8% max drawdown was the concrete proof. The halt doesn't force a sale —
it stops new entries from digging the hole deeper while a position is
frozen. **2026-07-22 change:** the ALL-entries halt was found to be
blocking the exact Oct–Dec 2022 dip-buy entries the strategy exists to
catch (a 30%+ account drawdown and a generational equity dip-buying
opportunity can coincide) — narrowed so only new LEAP risk is frozen
during a halt, not equity dip-buying. The −30% trigger itself is unchanged.

---

## PART 7 — CURRENT BOOK vs. THIS STRATEGY

### Reconciled, 2026-07-20 — two accounts, not one

The 2026-07-19 "zero equities" scare was a connection gap, not a sold
book: the equity sleeve lives in a **second Robinhood account this
session's connection cannot reach.** Full detail, per-position figures,
and the ORCL average-down write-up: `docs/portfolio-audit-2026-07-20.md`
and `portfolio.yaml`. Account 1 (LEAPs) was pulled live; Account 2
(equities) is carried from the 2026-07-14 audit, marked to live quotes,
except ORCL, which reflects today's trade.

| Rule (v3.0) | Limit | Actual (combined book) | Status |
|---|---|---|---|
| Total positions | 6 (5 equity + 1 LEAP) | **7** (5 equity + 2 LEAP) | ❌ VIOLATED — LEAP slot |
| Max single equity position | 15% | **HIMS at 27.5%** | ❌ VIOLATED (worse than July 14's 26.7% — pure appreciation) |
| LEAP sleeve | 25% | **35.8%** | ❌ VIOLATED |
| Min cash floor | 5% | **~0.2%** (estimated — see audit doc) | ❌ VIOLATED (badly) |
| **NFLX LEAP** | Ineligible — fails $500B rule | **Still held** | ❌ VIOLATED |

**🔴 Today's change: ORCL added to, not fixed.** +5 shares @ $125.00,
averaging the 31-share $148.00 lot down to a $144.81 blended basis on 36
shares — on the book's only losing position. Checked against the actual
v3.0 entry rules (same code the backtest uses): ORCL clears the 40%
drawdown gate (62.2% off its hybrid 2yr high) but had **no UT-Bot buy
signal firing** that day. **Gate cleared, trigger didn't — this reads as
a discretionary average-down, not a rule-triggered entry.** Reported as
fact; the owner decides what it means. Full mechanics in the audit doc.

**Every rule in the book is still broken, and nothing has been fixed
since July 14.** Phase 0 ("fix the book") remains untouched — see
`PLAN.md`.

---

## OVERRIDE LOG

*Rules changed from a prior version of this document, and why.*

| Date | Override | Reverses |
|---|---|---|
| 2026-07-14 | 200 SMA trend filter | *(RSI-system era; see retired history below)* |
| 2026-07-15 | Max single position 25% → 20% | RSI-system Part 6 |
| 2026-07-15 | NFLX LEAP held to expiry | "close NFLX" guidance |
| 2026-07-19 | Max equity position 20% → **15%** | the 2026-07-15 override above |
| 2026-07-19 | Cash floor 10% → **5%** | RSI-system Part 6 |
| 2026-07-19 | LEAP delta 0.70–0.80 → **0.50–0.60** | RSI-system deep-ITM rule |
| 2026-07-19 | Slots made explicit: **5 equity + 1 LEAP** | (new keys) |
| 2026-07-19 | SMA(200) gate removed from all entry logic | RSI-system trend filter |
| 2026-07-19 | Single-entry primary; 3-tranche ladder demoted to ablation-only | RSI-system tranche ladder |
| **2026-07-19** | **🔴 ENGINE REPLACED: RSI(3)+SMA(200) entry / RSI(70→60) exit → drawdown-gate+UT-Bot entry / Fibonacci-zone exit.** This is the single largest change in the project's history and was not logged as an override at the time it happened — three research generations (A/B/C/D → 12-name Fib matrix → 200-name universe run) occurred before this document was updated to match. Logged retroactively 2026-07-20 per the project review's lead finding. | The entire RSI(3) mean-reversion system described in STRATEGY.md v2.0 |
| 2026-07-19 | LEAP force-close-at-6-months **suspended, strategy-scoped only** — LEAPs ride to the Fib exit or 2yr modeled expiry | RSI-system force-close rule (still active globally for any strategy that doesn't explicitly suspend it) |
| 2026-07-19 | Slot-selection tiebreak defined: deepest drawdown → earliest gate-clear → alphabetical | (previously unset) |
| 2026-07-20 | Equity exit floor: see the three-way ablation in `reports/` — winner promoted here once run completes | RSI-system Trigger 1/Trigger 2 exits |
| 2026-07-20 | Tiered drawdown gate introduced (25%/30%/40% by market-cap tier) — EXPERIMENTAL | flat 40%/25% gate |
| **2026-07-21** | **Tiered drawdown gate ADOPTED as official** — no longer experimental | flat 40%/25% gate (kept in code for reference) |
| 2026-07-21 | Timeframe LOCKED to daily entry / weekly exit — no longer a matrix search | the 6-cell (and prior 7-cell) matrix searches |
| 2026-07-21 | Slot tiebreak changed to RATIO-based (drawdown ÷ tier threshold) | the 2026-07-19 raw-deepest-drawdown-first rule |
| 2026-07-21 | LEAP delta 0.50–0.60 → **0.55–0.65** | the 2026-07-19 override above |
| 2026-07-21 | LEAP single-entry/sleeve cap 20%/25% → **33%/33%** (identical, since only 1 LEAP is ever held) | the 2026-07-15/07-19 overrides above |
| 2026-07-21 | Equity slots 5 → **4**; the 5th slot's capital becomes the dedicated 33% LEAP reserve | the 2026-07-19 "5 equity + 1 LEAP" override |
| **2026-07-21** | **🔴 LEAP PRICING REPLACED: flat 0.55-delta static approximation → real Black-Scholes delta-curve engine.** Every historical LEAP trade was mispriced by the old model (JPM/ASML/TSLA/one MU trade understated 2.5–3.8×; a second MU trade flips from "roughly breakeven" to expired completely worthless). Full-span max drawdown rose to 62.8% as a direct, traced result — leverage cutting both ways, not a bug. | `backtest/leap_pricing.py`'s flat approximation (kept in code for reference) |
| 2026-07-21 | VOO reserve documented as a live-execution-only cash-management rule — never modeled in the backtest | (new rule, no prior equivalent) |
| 2026-07-22 | Sizing: 30% LEAP / 65% across 4 equities (16.25% each) / 5% cash floor — max equity position 15%→**16.25%**, LEAP single/sleeve cap 33%→**30%** | the 2026-07-21 33%/15% sizing |
| **2026-07-22** | **🔴 LEAP ELIGIBILITY REPLACED: flat $500B market-cap floor → top-10-by-market-cap-proxy, RANKED, at the entry date.** Confirmed MU never qualifies under the new rule in any year — the specific mispricing that drove the 62.8% max drawdown does not recur. | the flat $500B floor (kept in code for reference) |
| **2026-07-22** | **🔴 LEAP RESERVE REVERSED: "dedicated reserve, not backfilled" (2026-07-21) → spendable working capital, held in SPY, mark-to-market.** Equities may now draw on the reserve when a LEAP doesn't currently qualify. | the 2026-07-21 "dedicated LEAP reserve" model (Part 4b-prior, kept for the record) |
| 2026-07-22 | New slot-time recycling valve: a held equity ≥12mo old AND underwater AND blocking a higher-ranked waiting candidate may be force-recycled. Winners in profit are never touched. | the 2026-07-19/21 "no displacement, ever" rule (now has one narrow, tested exception) |
| 2026-07-22 | LEAP exit floor tightens 0.9→0.7 past 50% of modeled runway to expiry. No hard time-based force-close. | the flat 0.9-floor-for-life LEAP exit |
| 2026-07-22 | Kill switch SCOPE narrowed to LEAP entries/sizing-ups only; equity dip-buys pass through a halt uninterrupted. The −30% trigger itself is unchanged. | the 2026-07-19 "halt ALL new entries" kill switch |
| **2026-07-22** | **🔴 EQUITY EXIT CHANGED: the 1.618 hard exit is retired.** Touching 1.618 now switches the position into a trailing exit (UT-signal-based or %-retracement-based) instead of force-selling. | the 2026-07-20 exit-ablation winner's 1.618 hard-exit clause (the 0.9-floor/no-latch shape below 1.618 is unchanged) |
| 2026-07-22 | Dashboard SPY-benchmark curve truncation bug fixed — all curves reindexed to one shared date union before serializing, instead of sharing one series' bare labels array positionally | (bug fix, no prior rule) |
| 2026-07-22 | **Fill-order bug fixed:** the entry-fill loop iterated `sorted(pending_entries)` (alphabetical), silently discarding the 2026-07-21 ratio-based slot-tiebreak's rank order. Found while building the slot-recycling valve; regression test added. | unintentional bug in the 2026-07-21 ratio-tiebreak implementation, not a design change |
| 2026-07-22 | **HONEST VERDICT: the "Beat-SPY Package" (A1–A8) still does not beat SPY risk-adjusted.** Every one of 12 tested cells runs ~2x SPY's max drawdown despite enormous raw returns; the top-ranked cells are concentrated in 2–3 plausibly-lucky LEAP trades (TSLA x2, META x1) per the mandatory overfitting guard. Full detail: `reports/beat_spy_package.md`. | supersedes no prior claim — this is the first run explicitly scoped to answer "does this beat SPY risk-adjusted," and the honest answer is no |

**Known spec gap (2026-07-19, still open):** Strategy D (RSI-armed,
volume-triggered) was reconstructed from a partial spec; two of its
parameters were never owner-confirmed. **Moot** — Strategy D is retired
with the rest of the RSI system.

---

*Reviewed after each research generation. Backtests are not promises —
survivorship bias, changing market regimes, and the data source's
current-snapshot limitation all apply. No rule may be changed while a
position it governs is underwater.*
