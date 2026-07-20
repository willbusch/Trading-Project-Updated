# STRATEGY.md

**Version:** 3.0
**Last updated:** July 20, 2026
**Owner:** Will Busch
**Companion files:** `PLAN.md`, `GOAL.md`, `investor-one-pager-will-busch.md`, `portfolio-audit-2026-07-14.md`

> **The one-line thesis:**
> *I buy quality that's temporarily broken, and I hold until it retraces most of the way back.*
>
> Entry is fear, defined by price against its own recent history. Exit is a
> structured retracement zone, not a fixed target. This is a **full-cycle
> system**, not a bounce trade — holds run months, sometimes years.

---

## ⚠️ STATUS: PLAUSIBLE, NOT PROVEN

Backtested across three research generations (2026-07-19/20). The universe
run cleared SPY buy-and-hold and the SPY-idle-cash benchmark in a 12-month
vault — but on **2 trades**, with a **100% win rate in every window of
every cell tested**, which is the signature of survivorship bias (the
universe is defined by names that are large-cap and profitable *today*),
not of demonstrated skill. Every large winner traces to the Feb–Mar 2020
COVID crash and recovery — one regime, one name set, selected after the
fact. **No real capital is deployed on this system until a data source
supporting point-in-time index membership and historical fundamentals
becomes available and the backtest is re-run against it.** See
`reports/fib_matrix.md` and `reports/fib_universe.md` for full results and
caveats.

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

### The Drawdown Gate

Price is **≥40% below its own hybrid 2-year-high anchor** (equities) or
**≥25% below** (LEAP underlyings, additive to the $500B+ filter).

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
entry timeframe. **Winning configuration from the universe run: daily
entry timeframe.** (UT-Bot ported from the Pine v4 "UT Bot Alerts" script;
see `screener/ut_bot.py`.)

*No RSI, no SMA(200), no weekly-lower-lows filter in the active entry
logic — all replaced by the drawdown gate + UT-Bot trigger above.*

---

## PART 3 — SIZING (Equities)

| Rule | Value |
|---|---|
| **Position sizing** | Single entry, one shot — **no tranche ladder** (demoted to an unused ablation variant; the RSI system's 3-tranche ATR ladder is retired with it) |
| **Max position** | **15% of book** per name |
| **Slots** | **5 equity + 1 LEAP** (6 total) |
| **Max new positions per week** | **2** |
| **Min cash floor** | **5%** |

### Slot-Selection Tiebreak

When more names clear the gate + trigger on the same day than there are
free slots: **deepest drawdown first**, then **earliest gate-clear date**,
then **alphabetical**. (Defined 2026-07-19 — was previously an unset rule.)

---

## PART 4 — THE LEAP SLEEVE (Different Rules)

| Rule | Spec | Why |
|---|---|---|
| **Underlying** | **$500B+ market cap only** | Cannot go to zero. NFLX fails this. |
| **Entry trigger** | Same drawdown gate (25%) + UT-Bot buy | The LEAP is the equity thesis with a multiplier. |
| **Delta at entry** | **0.50–0.60** | Changed 2026-07-19 from the RSI-system's 0.70–0.80 deep-ITM rule — see override log. |
| **Expiry** | **1.75 years minimum** at entry, **2 years preferred** | Time to be right; hard floor, not a target. |
| **Force-close-at-6-months** | **SUSPENDED for this strategy only.** LEAPs ride to the Fib exit or the modeled 2-year expiry. The global 6-month force-close rule (`config.yaml leap.force_close_months_to_expiry`) is untouched for any future strategy that doesn't explicitly suspend it. | The Fib exit is the only exit signal this strategy trusts; a time-based override would contradict it. |
| **Sizing** | Delta-adjusted notional, single entry, **20% of book cap** | No tranche ladder on options — never average down. |
| **Pricing model** | **0.55-delta static approximation** (midpoint of 0.50–0.60), ignoring theta and IV — **optimistic**. Documented limitation, not a bug: real historical option premiums exist for expired contracts but selecting *which* contract at each historical entry requires greeks anyway, so one consistent approximation beats a mixed model. | See `backtest/leap_pricing.py`. |
| **Expired-worthless LEAPs** | **Cannot be modeled** — the delta-approximation has no strike/theta, so it structurally cannot produce a worthless expiry. Reported as N/A, a known limitation. | |

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
| Max positions | **6** (5 equity + 1 LEAP) |
| Max single equity position | **15%** |
| Max LEAP sleeve (single entry, delta-adjusted notional) | **20%** |
| Min cash | **5%** |
| Tranche ladder | **Retired** (single entry only) |
| Max new positions per week | **2** |
| **🛑 ACCOUNT KILL SWITCH** | **−30% → HALT all new entries for 30 days** |

### Why the kill switch

No stops on open losers + leverage (LEAP sleeve) + concentration (6 slots)
= a real path to a very bad year. The halt doesn't force a sale — it stops
new entries from digging the hole deeper while a position is frozen.

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

**Known spec gap (2026-07-19, still open):** Strategy D (RSI-armed,
volume-triggered) was reconstructed from a partial spec; two of its
parameters were never owner-confirmed. **Moot** — Strategy D is retired
with the rest of the RSI system.

---

*Reviewed after each research generation. Backtests are not promises —
survivorship bias, changing market regimes, and the data source's
current-snapshot limitation all apply. No rule may be changed while a
position it governs is underwater.*
