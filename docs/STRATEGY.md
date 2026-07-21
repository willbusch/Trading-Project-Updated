# STRATEGY.md

**Version:** 4.0
**Last updated:** July 21, 2026
**Owner:** Will Busch
**Companion files:** `PLAN.md`, `GOAL.md`, `investor-one-pager-will-busch.md`, `portfolio-audit-2026-07-20.md`

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

## ⚠️ STATUS: PLAUSIBLE, NOT PROVEN — LOCKED CONFIGURATION, RESEARCH RE-CLOSED 2026-07-21

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
| **Market cap — LEAPs** | **$500B+ ONLY** | Leverage only on names that can't go to zero. The NFLX rule. |
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
- **LEAPs on anything under $500B** — the NFLX rule
- OTM LEAPs at entry
- LEAPs under 1.75 years to expiry at entry

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
| **Position sizing** | Single entry, one shot — **no tranche ladder** (demoted to an unused ablation variant; the RSI system's 3-tranche ATR ladder is retired with it) |
| **Max position** | **15% of book** per name |
| **Slots** | **4 equity + 1 LEAP** (5 total) — CHANGED 2026-07-21, was 5+1. The 5th equity slot's capital is now the dedicated LEAP reserve, see Part 4a. |
| **Max new positions per week** | **2** |
| **Min cash floor** | **5%** |
| **Full slots** | New candidates WAIT for a natural Fib exit — **no displacement of an existing position, ever** (reverted 2026-07-21 after being briefly considered). |

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
| **Underlying** | **$500B+ market cap only** | Cannot go to zero. NFLX fails this. |
| **Entry trigger** | Same drawdown gate (25% tier) + UT-Bot buy | The LEAP is the equity thesis with a multiplier. |
| **Delta at entry** | **0.55–0.65** (CHANGED 2026-07-21, was 0.50–0.60; midpoint used to solve the modeled strike is now 0.60, was 0.55) | Owner override — see override log. |
| **Expiry** | **1.75 years minimum** at entry, **2 years preferred** (2.0yr also used as the modeled tenor T0 for strike-solving and theta decay) | Time to be right; hard floor, not a target. |
| **Force-close-at-6-months** | **SUSPENDED for this strategy only.** LEAPs ride to the Fib exit or the modeled 2-year expiry. The global 6-month force-close rule (`config.yaml leap.force_close_months_to_expiry`) is untouched for any future strategy that doesn't explicitly suspend it. | The Fib exit is the only exit signal this strategy trusts; a time-based override would contradict it. |
| **Sizing** | Single entry, **33% of book cap** (CHANGED 2026-07-21, was 20%) — single-entry cap and total-sleeve cap are now IDENTICAL by design, since only ONE LEAP is ever held at a time (no stacking) | The LEAP is the intended profit driver — see Part 4a. |
| **Pricing model** | **✅ Real Black-Scholes delta-curve engine (CHANGED 2026-07-21).** The flat 0.55-delta static approximation is RETIRED — see below. | See `backtest/leap_bs_pricing.py`. |

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

### 4b. Dedicated LEAP Reserve (2026-07-21, owner's model)

The 33% LEAP allocation is **reserved capital**, not backfilled into a
5th equity when no LEAP currently qualifies:

- **LEAP held:** 1 LEAP (33%) + 4 equities (15% each = 60%) + ~7% cash.
- **No LEAP qualifies:** 4 equities (60%) + the 33% sits as **cash**, dry
  powder for the next qualifying mega-cap setup. It does NOT fund a 5th
  or 6th equity position.

Enforced by `backtest/constraints.py:check_leap_reserve` — while no LEAP
is held, an equity entry may not leave cash below (33% reserve + 5%
floor) of the book. Once a LEAP is held, its 33% is already deployed as a
real position, not idle cash, so only the normal 5% floor applies.

**Rationale (owner):** the LEAP is the intended profit driver; keep
dedicated dry powder ready to strike a leveraged mega-cap bet the moment
one qualifies, rather than being fully deployed in equities and forced to
sell something to fund it. Consistent with the patient dip-buyer
philosophy; avoids the forced-over-deployment the 2026-07-20 throttle
ablation showed actively hurt returns.

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

### Equity Exit

**Winner of the 2026-07-20 three-way ablation: a plain 0.9 floor, no
latch.** (`backtest.fib_exit.SimpleFloorExit(floor=0.9)`, config key
`exit_variant="simple_09"`.)

| Zone | Rule |
|---|---|
| below 0.9 | Hold |
| 0.9 → 1.618 | Any UT sell (exit timeframe) → full exit |
| 1.618 | Hard automatic exit |

Beat both the prior 0.5-floor champion (pre-vault expectancy +93.9% vs
+45.8%) **and** a new, more complex full-latch design the owner proposed
that same day (+82.4%) — see `reports/fib_final_ablation.md`. Simplicity
has now won every exit-design ablation run in this project's history. The
full-latch design (`FullLatchExitV2`) is kept in code for reference; its
extra travel-zone latches were shown to cost real money (3 gap trades,
$77,064 given back pre-vault) without a matching expectancy benefit.

Selection was made on **pre-vault** expectancy only — the 12-month vault
was deliberately not used to pick a winner among the three candidates, to
avoid re-peeking the same held-out window repeatedly (see the ablation
report's methodology note).

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
| Max positions | **5** (4 equity + 1 LEAP) — CHANGED 2026-07-21, was 6 (5+1) |
| Max single equity position | **15%** |
| Max LEAP sleeve (single entry, real option notional) | **33%** — CHANGED 2026-07-21, was 20% |
| LEAP reserve when no LEAP held | **33% held as cash** (VOO live), not backfilled to equities — new 2026-07-21 |
| Min cash | **5%** |
| Tranche ladder | **Retired** (single entry only) |
| Max new positions per week | **2** |
| Full slots | **No displacement** — new candidates wait for a natural exit |
| **🛑 ACCOUNT KILL SWITCH** | **−30% → HALT all new entries for 30 days** |

### Why the kill switch

No stops on open losers + leverage (LEAP sleeve, now REAL leverage via
Black-Scholes pricing, not a linear approximation) + concentration (5
slots, one of them a 33% single-name option position) = a real path to a
very bad year — the 2026-07-21 run's 62.8% max drawdown is the concrete
proof, not a hypothetical. The halt doesn't force a sale — it stops new
entries from digging the hole deeper while a position is frozen.

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

**Known spec gap (2026-07-19, still open):** Strategy D (RSI-armed,
volume-triggered) was reconstructed from a partial spec; two of its
parameters were never owner-confirmed. **Moot** — Strategy D is retired
with the rest of the RSI system.

---

*Reviewed after each research generation. Backtests are not promises —
survivorship bias, changing market regimes, and the data source's
current-snapshot limitation all apply. No rule may be changed while a
position it governs is underwater.*
