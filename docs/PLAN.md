# PLAN.md

**Project:** Trader-Resp — Drawdown-Gated Fibonacci Screener + Backtest
**Owner:** Will Busch
**Last updated:** July 20, 2026
**Read alongside:** `STRATEGY.md` (v3.0 — Fib strategy is now official), `GOAL.md`, `CLAUDE-CODE-PROMPT.md`

---

## STATUS SNAPSHOT

| Phase | What | Status |
|---|---|---|
| **0** | Fix the book | 🔴 NOT STARTED — **blocked on a new question, not the old one.** The 2026-07-20 live scanner pull found NO equity positions in any linked account (only 2 LEAPs, 84% sleeve, 0% cash) — materially different from the July 14 manual audit's 7-position book. Owner must confirm which is real before Phase 0 proceeds. See STRATEGY.md Part 7. |
| **1** | Dashboard / live scanner (screener → BUY/SELL) | 🟡 IN PROGRESS — scaffolded 2026-07-20 |
| **2** | Pinescript port | 🟢 DONE — UT-Bot ported (`screener/ut_bot.py`), tested |
| **3** | **Backtest — THE GATE** | 🟢 DONE TO THE DATA CEILING — three research generations run (A/B/C/D retired → 12-name Fib matrix → 200-name universe run → final structural ablation). Cleared the honest benchmark on thin evidence; **edge is plausible, not proven** — the data source's lack of point-in-time membership/fundamentals is now the binding constraint, not more backtesting. Research phase closed 2026-07-20; see the override log. |
| **4** | Live, small | 🔴 BLOCKED — not on Phase 3 anymore, but on Phase 0 (book not reconciled) and the open data-source question |
| **5** | Scale to full size | 🔴 BLOCKED on Phases 0 + 4 |

**Currently in progress:** Phase 1 (live scanner) and Phase 0 (fix the
book — now unblocked, not yet started).

**This table previously said "Phase 0, nothing started" while three full
backtest research generations sat undocumented below it — that contradiction
was flagged in the 2026-07-19 project review and is fixed as of this
update.**

---

## OWNER OVERRIDE LOG

Dated record of every owner decision that reverses or supersedes what
STRATEGY.md / GOAL.md / this plan previously said. Config.yaml comments
point here. **STRATEGY.md was rewritten to v3.0 on 2026-07-20** to match
the active system — the doc-drift gap flagged below is closed for
STRATEGY.md; GOAL.md is a separate, smaller open item.

| Date | Override | Reverses |
|---|---|---|
| 2026-07-15 | NFLX LEAP held to expiry | PLAN.md/STRATEGY.md "close NFLX" guidance |
| 2026-07-15 | Max single position 25% → 20% (stocks AND options, same-underlying bucketed) | STRATEGY.md Part 6 |
| 2026-07-19 | Max equity position 20% → **15%** ("LOCKED DECISIONS", A/B/C/D build) | the 2026-07-15 override above |
| 2026-07-19 | Cash floor 10% → **5%** | STRATEGY.md |
| 2026-07-19 | LEAP delta 0.70–0.80 → **0.50–0.60** | STRATEGY.md deep-ITM rule |
| 2026-07-19 | Slots made explicit: **5 equity + 1 LEAP** | (new keys, no prior explicit value) |
| 2026-07-19 | **SMA(200) gate removed from ALL strategy entry logic** (A/C/D), not kept as an ablation; display-only use permitted later (Addendum 2) | STRATEGY.md trend filter + this plan's Grade A/B/C half-size tiers |
| 2026-07-19 | Arm expiry for C/D locked: RSI(14) reclaims 50 is the ONLY expiry — no day cap (Addendum 2) | (confirms existing config; forecloses any time-based backstop) |
| 2026-07-19 | Single-entry is PRIMARY for equities; 3-tranche ladder demoted to ablation-only | STRATEGY.md tranche ladder |

**Strategy D open loop — CLOSED 2026-07-20.** The two unconfirmed
parameters (`volume_avg_bars`, sweep range) are moot: Strategy D and the
rest of the RSI-system A/B/C/D suite are formally retired (kept in code
for reference only, see STRATEGY.md Part 0). No further action needed.

---

## RESEARCH PHASE RE-CLOSED — 2026-07-21 (real LEAP pricing + locked config)

Final research pass. The dashboard surfaced that the +415% headline result
was essentially one event — every backtest winner traced to a Feb-Mar 2020
COVID entry, AND every LEAP trade was mispriced by the flat 0.55-delta
approximation (understated 2.5-3.8x on winners; couldn't represent
"expired worthless" at all). Fixed both, in priority order:

1. **Real LEAP pricing** (backtest/leap_bs_pricing.py) — Black-Scholes,
   strike+sigma frozen at entry (sigma = trailing realized vol, no
   historical IV surface available), S and T evolve daily. Retires the
   flat approximation entirely. Verified: JPM/ASML/TSLA/one MU trade
   understated 2.5-3.8x by the old model; a second MU trade flips from
   "roughly breakeven" to expired completely worthless (-100%) under real
   pricing. Full-span max drawdown rose to 62.8% (was 17-40% every prior
   round) — traced directly to that same MU LEAP sitting open through the
   entire 2022 bear market at 33% of book. Leverage cutting both ways,
   confirmed not a bug.
2. **Tiered drawdown gate ADOPTED as official** (was experimental
   2026-07-20) — 25%/30%/40% by market-cap tier.
3. **Ratio-based tiebreak** (drawdown / tier threshold) replaces raw
   deepest-drawdown-first — verified working in the actual run (AMAT
   $421B won a contested slot over four smaller/harder-gated names).
4. **Sizing changed**: 4 equity slots (was 5) + 1 LEAP at 33% (was 20%),
   dedicated LEAP reserve model (33% held as cash, NOT backfilled to a
   5th equity, when no LEAP qualifies) — enforced by a new constraint
   check, `check_leap_reserve`.
5. **Timeframe LOCKED** to daily entry / weekly exit — matrix search
   retired, one configuration going forward.
6. **VOO reserve** documented in STRATEGY.md as a live-execution-only
   cash-management rule (idle capital held in VOO, sold to fund entries)
   — explicitly NOT modeled in the backtest; the existing SPY-idle-cash
   benchmark already captures the functionally identical behavior.

Vault trade count: 2 (above the 1-2 range seen in every prior round, still
too thin to call decisive). Full run: `reports/fib_final_run.md`. Dashboard
regenerated with real-LEAP-priced results as primary
(`reports/results_dashboard.html`).

**Research formally re-closes.** The ceiling remains data: survivorship-
biased universe, current-snapshot market-cap tiering, and now also
realized-vol-as-IV-proxy — three simplifications, all disclosed, none
removable without a data source Robinhood cannot provide (point-in-time
membership + fundamentals + market caps). No further strategy iteration
is planned without one.

**PARKED for a future run (do not build without an explicit owner ask):**
a lower reconciliation between the dashboard's fresh-re-simulation
sensitivity and the report's window-sliced results was fixed for THIS
run (dashboard now consumes the exact pickled report run rather than
re-simulating) — but the underlying universe-snapshot-timing sensitivity
itself (small drift in scanned market data between separate script
invocations changes which trades fire, via slot competition) remains a
structural fragility worth a real fix if this project continues:
snapshotting the universe list once per research generation instead of
re-scanning live each run would remove the sensitivity entirely.

---

## RESEARCH PHASE REOPENED — 2026-07-20 (tiered drawdown gate, superseded by the re-close above)

The "closed" note directly below was accurate for less than a day. The
dashboard surfaced a finding that demanded a re-open: every backtest
winner traced to a Feb–Mar 2020 COVID entry, because a flat 40% drawdown
gate structurally locks mega-caps out of qualifying outside a crash. Owner
specified a tiered gate (25%/30%/40% by market-cap band) to test whether
that's fixable without a new data source. Result: genuine improvement on
trade-year-spread (2021–2026 now represented, not just 2020), but NOT a
clean win — it lowered trade count and return on the prior champion cell.
No single re-tested cell beats the flat-gate baseline unambiguously.
Full write-up: `reports/fib_tiered_gate.md`. STRATEGY.md's drawdown-gate
section now documents the tiered gate as the active experiment.

**Research phase re-closes** on the same terms as below: the ceiling is
still data (no point-in-time membership/fundamentals), now also extended
to market-cap tiering itself (current-snapshot proxy, flagged in
STRATEGY.md). Further iteration past this specific tiered-gate test
requires the same missing data source as everything else in this
section.

---

## RESEARCH PHASE CLOSED — 2026-07-20 (superseded by the reopen note above)

After the final structural ablation (see `reports/` for the run), no
further strategy iteration is planned on the current data source. The
ceiling isn't the engine — it's tested, forward-only, and reused across
every variant without incident. **The ceiling is data:** Robinhood MCP has
no point-in-time index membership and no historical fundamentals, so every
backtest here is a current-membership/current-fundamentals proxy no matter
how the strategy is tuned. Further iteration requires a different data
source. Until then, effort moves to Phase 0 (fix the book) and Phase 1
(the live scanner) — both of which use the *current* strategy definition
regardless of the unresolved edge question.

**PARKED — do not build without an explicit owner ask:** a below-0.5
latch refinement (armed-above-0.5 required; a UT sell below 0.5 exits
only if the trade was already armed above 0.5; a trade that never armed
above 0.5 holds through). The 2026-07-20 three-way ablation already
retired the latch concept entirely — `latch_v2`'s full latch design lost
to a plain 0.9 floor and cost $77,064 in quantified give-back with zero
expectancy benefit (`reports/fib_final_ablation.md`). This refinement is
only worth building if the owner explicitly wants to test whether the
below-0.5 tweak specifically changes that verdict — it is not queued as
follow-up work on its own.

---

## FULL-UNIVERSE RUN — 2026-07-19 (200-name proxy, edge-verdict attempt)

Scaled the Fib strategy from 12 curated names to a 200-name universe.
Four changes bundled: (1) latch DROPPED — equity exit is now the simple
version (proven equivalent in the 12-name ablation; latch code kept for
reference); (2) HYBRID ANCHOR (504d default, extended ~4yr when the true
peak aged out of the 2yr window) — replaces stale-exclusion, fires on
146/200 names; (3) QUALITY GATE = static membership in a live scanner list
($10B+ mkt cap, positive net margin, >1M avg vol); (4) SPY-WHEN-IDLE-CASH
benchmark to price cash drag directly.

- New: `backtest/fib_universe.py`, `scripts/ingest_universe.py`,
  `scripts/render_universe_report.py`, `data/universe_snapshot.json`.
  `drawdown_gate.hybrid_anchor_high` + `fib_features(use_hybrid=)` +
  `simulate_fib(idle_cash_spy=, simple_exit=)`. 59 tests green incl. a new
  hybrid-anchor lookahead test.
- DATA REALITY (the binding constraint): Robinhood has NO index-membership
  filter and only CURRENT fundamentals. So this is NOT a point-in-time
  SPY/QQQ run — it's a current-membership, current-fundamentals proxy
  (top-200 large-cap-profitable by today's snapshot). Severe survivorship +
  fundamental-snapshot bias, all favoring the strategy. Flagged verbatim in
  the report header. 100% coverage (200/200 names, daily 2018→2026).
- RUNTIME: ~143s/cell forced the prompt-authorized REDUCED 4-cell set
  (daily/weekly, 3day/weekly, weekly/weekly, daily/daily) instead of 7.
- VERDICTS (reports/fib_universe.md): winning cell daily/weekly. It DID beat
  SPY buy-hold in the vault (+37.7% vs +18.4%) AND the SPY-idle-cash variant
  (+42.0% vs +18.4%). BUT: 100% win rate in every window = survivorship
  signature; vault verdict rests on 2 trades; winners dominated by the
  COVID-crash cluster. Honest call: NOT proof of edge — clears the bar
  barely, on thin evidence. Leak-hunt passed (combined CAGR 11–15%; the
  >50% CAGR cells are short half-windows with n=6–7).
- OPEN: point-in-time membership + historical fundamentals are the only
  path to a real edge verdict and are NOT available from Robinhood — would
  need a different data source. Deployment only ~72% pre-vault despite
  something eligible 77% of days (5-slot/2-per-week throttle).

---

## LATCHED-FIB STRATEGY BUILT + RUN — 2026-07-19 (12-name matrix)

A/B/C/D formally RETIRED (code kept for reference, no longer run). The
drawdown-gated latched-Fib strategy is now the sole active strategy.

- New modules: `backtest/multi_tf.py` (UT on weekly/3-day/daily projected
  onto one daily clock, forward-only), `backtest/drawdown_gate.py`
  extended (Fib levels, dip-low-since-gate-clear, stale-anchor detection),
  `backtest/fib_exit.py` (equity latched + LEAP simple exit machines,
  forward-only), `backtest/fib_features.py`, `backtest/fib_simulator.py`
  (daily clock; reuses the risk framework + cash rule unchanged),
  `backtest/fib_reporting.py`, `backtest/fib_orchestrate.py`. 57 tests
  green incl. exit-machine AND simulator lookahead tests.
- Sample: 12 curated names (NFLX MSFT META NVDA AMD NOW ORCL MU TSLA HIMS
  HOOD SOFI); META/NVDA/AMD/MU/TSLA ingested this session (2019-01 →
  2026-07). $500B+ names get the LEAP path + 25% gate.
- Stale-anchor decision (Option 1): entries whose 504d anchor is provably
  stale (higher high within ~4yr but outside 2yr) EXCLUDED from headline;
  both-ways diagnostic shown for HOOD/SOFI.
- Slot tiebreak DEFINED (was unset): deepest drawdown → earliest
  gate-clear → alphabetical.
- LEAP force-close-6mo SUSPENDED strategy-scoped (global rule untouched);
  LEAP entry floor 1.75yr / 2yr preferred; modeled 2yr expiry exit.
- HEADLINE VERDICT (reports/fib_matrix.md): best cell `daily/weekly`.
  Does NOT beat equal-weight-buy-hold-same-names — took 0 vault trades
  (sat in cash) vs the benchmark's +65%. Latched does NOT beat simple
  (identical trade set; latch never armed-and-saved a trade). Leak-hunt
  passed (no cell >18% CAGR; high per-trade expectancy = long-hold
  survivorship, not lookahead).
- OPEN: full SPY/QQQ universe run (hybrid anchor for young names) — design
  noted, not built. Expired-worthless LEAPs can't be modeled by the
  delta-approx (no strike/theta) — reported N/A, a known limitation.

**Future universe run — hybrid anchor design (don't build yet):** 504-day
high by default, extended ~3–4yr lookback when a name's true peak sits
just outside the 2yr window, so young post-IPO names get their real peak
without reaching to ancient irrelevant highs. Ties into the stale-anchor
detector already built (`is_stale_anchor`).

---

## BACKTEST ENGINE BUILT + FIRST RUN — 2026-07-19 (A/B/C/D engine-validation pass, RETIRED)

The full portfolio backtest engine now exists and has run once on the 7
held names (survivorship-biased BY DESIGN — engine validation, not proof
of edge; the disclaimer is baked into `reports/abcd_comparison.md`).

- New: `screener/weekly.py` (calendar-anchored weekly bars + lower-lows
  filter) and `backtest/{features,signals,portfolio_state,constraints,
  leap_pricing,simulator,reporting,orchestrate}.py`. One shared
  `simulate()` engine; windows/sweeps/ablations are just inputs to it.
  43 tests green, including the adversarial cash-rule test (same-bar sale
  proceeds cannot fund an add to an underwater name).
- Headline findings (details + caveats in the report): Strategy C took
  ZERO trades under the B-optimized UT(4.0,7) sweep params — arms set but
  the wide stop never fired a buy inside an armed window; C works under
  default UT(1.0,10) (16 trades, +6.7% expectancy). Strategy B collapsed
  from +128.7% pre-vault to −4.4% in the vault (0/3 wins) — the vault is
  now SPENT. Both sweeps chose edge-of-grid cells (unstable). The 70→60
  momentum exit hurt everything it touched.
- LEAP pricing: uniform delta-adjusted approximation (static 0.55),
  labeled per-name. Spike confirmed Robinhood serves full daily history
  for EXPIRED contracts (MSFT Jun-23 $300C: 493/493 real bars) — upgrade
  path documented in `backtest/leap_pricing.py`.
- SPY ingested (1,266 daily bars, 2021-07-01 → 2026-07-17) for the
  benchmark: pre-vault buy-and-hold +62.8% total, 11.4% CAGR.
- OPEN: Strategy D's `volume_avg_bars` and sweep range are ASSUMED
  reconstruction defaults (Addendum 1 never reached the Code session) —
  see the override log's spec-gap entry; awaiting owner confirm/veto.

---

## STAGE 0 UPDATE — 2026-07-15: RSI(14) switch, Robinhood-only data

Three decisions made and implemented this session, ahead of `STRATEGY.md`
being formally updated to match (that update is still pending — see below):

- **Signal switched from RSI(3) to RSI(14) on 3-day bars.** `config.yaml`'s
  `indicators.rsi_period` is now `14`. `screener/indicators.py` itself
  didn't need to change — `rsi(close, period=...)` was already
  period-agnostic; only the config value and the entry/exit threshold
  numbers built around it change.
- **Robinhood (MCP) is now the sole data source.** `yfinance` has been
  removed from `screener/data.py` and `requirements.txt` entirely — there is
  no automatic fallback to any other provider. The module only ever reads
  from the parquet cache (`fetch_daily_bars()`); new data enters the cache
  exclusively via `ingest_robinhood_bars()`, called by the agent after
  pulling from the Robinhood `get_equity_historicals` MCP tool. This is a
  real architectural constraint, not a preference: MCP tools are only
  callable by the agent, not from a standalone Python script, so "fetch" is
  now necessarily an agent-orchestrated step rather than something
  `data.py` does on its own.
- **Two `config.yaml` keys resolved:** `avg_volume_lookback_days` was
  removed entirely (no longer a named threshold — Stage 1's volume filter
  will need to define how it computes average volume when that stage is
  built). `weekly_lower_low_lookback_weeks` is now `8`.

**RSI(14) validation gate — MSFT & HIMS, 3-day bars, Robinhood data,
5-year history (2021-07-15 to 2026-07-15):**

| | MSFT | HIMS |
|---|---|---|
| Close (latest) | $395.63 | $37.17 |
| RSI(14), 3-day (latest, partial bar) | 48.22 | 64.95 |
| RSI(14) range (5yr) | 26.72 – 80.28 | 19.74 – 84.56 |
| RSI(14) median (5yr) | 52.19 | 50.81 |

Values computed and presented for TradingView cross-check — **not yet
confirmed by the owner.** Same open loop as the original RSI(3) gate: the
numbers are ready to compare, the actual match/mismatch determination still
needs a human eyeballing TradingView's RSI(14)/3-day chart for both names.

**Threshold re-tune — proposed, NOT yet written into `config.yaml`.**
The old RSI(3)-era thresholds produce broken signal frequency under RSI(14)
— most notably, `RSI(14) >= 80` (the old euphoria exit) fired **once in 5
years** for MSFT (0.2 signals/year), because RSI(14) is a smoother
oscillator that rarely reaches RSI(3)'s extremes. Measured crossing
frequency across the same 5-year window (MSFT / HIMS, per year):

| Threshold | Old value | Old freq (MSFT/HIMS) | Proposed | New freq (MSFT/HIMS) |
|---|---|---|---|---|
| Entry (RSI < X) | 35 | 1.8 / 2.6 | **35 (unchanged)** | 1.8 / 2.6 |
| Euphoria exit (RSI ≥ X) | 80 | 0.2 / 0.6 | **70** | 1.6 / 2.4 |
| Momentum-break arm (touch ≥ X) | 70 | 1.0 / 1.6 (at 70→60) | **65** | 1.4 / 1.8 (at 65→55) |
| Momentum-break fire (cross < X) | 60 | ″ | **55** | ″ |

Rationale: entry at 35 already fires at a comparable rate to the old
system, no evidence it needs to move. Euphoria and momentum-break levels
needed to come down because RSI(14) simply doesn't reach the old extremes
often enough for those exits to function. **Awaiting owner confirmation
before these four numbers get written into `config.yaml`.**

**Doc drift flagged, not yet resolved:** `STRATEGY.md` (Parts 2 and 5)
still documents RSI(3) with the original 35/70/80/60 thresholds and the
reasoning specific to that period ("why 3-day, not daily," the 25-30% full-
cycle-capture math in `GOAL.md`). This handoff intentionally scoped the
`STRATEGY.md`/`GOAL.md` rewrite out — those documents carry `STRATEGY.md`'s
own quarterly-review / 7-day-cooldown governance and shouldn't be rewritten
as a side effect of a data-pipeline task. They need a deliberate update once
the RSI(14) thresholds above are confirmed, or this project has two
documents actively disagreeing about its own core signal.

---

## PHASE 0 — FIX THE BOOK
*Before any code enforces the strategy, the book has to obey it.*

| Step | Task | Status |
|---|---|---|
| 0.1 | **Close the NFLX LEAP.** Fails 3 rules: sub-$500B underlying, 34% OTM, no RSI trigger. Cleanest move available — fixes the LEAP overage *and* the cash floor in one trade. | ☐ |
| 0.2 | **Trim HIMS 26.7% → 22%.** Proceeds → **CASH.** Not to ORCL. | ☐ |
| 0.3 | **Get cash to 10%** (~$4,500). Steps 0.1 + 0.2 do most of it. | ☐ |
| 0.4 | **Consolidate to 6 names.** SOFI (6.5%) and NOW (11.2%) are the smallest convictions. One is a position; the other is a habit. Decide which. | ☐ |
| 0.5 | **Write the tranche ladder for every open name** — including the 1.5×ATR rungs. | ☐ |
| 0.6 | **Write the ORCL number.** 🔴 *Still open. Still refused.* | ☐ |

**GATE:** Book satisfies all six constraints in STRATEGY.md Part 6. If the dashboard's first run doesn't flag zero violations, Phase 0 isn't done.

---

## PHASE 1 — THE DASHBOARD
*Screener that scans SPY/QQQ, applies the criteria, emits BUY / SELL / HOLD.*

| Step | Task | Status |
|---|---|---|
| 1.1 | Repo scaffold + `config.yaml` — **every threshold a named key, zero magic numbers** | ☐ |
| 1.2 | `data.py` — Robinhood (MCP) fetch, parquet cache, **fail loudly on missing data, no fallback source** | ☑ (updated 2026-07-15, was yfinance) |
| 1.3 | **Daily → 3-day bar resampling.** Get this exactly right. RSI(14) on 3-day bars ≠ RSI(14) on daily. **Write a test.** | ☐ |
| 1.4 | `indicators.py` — RSI, SMA(200), ATR(14). Unit-test against a known reference. | ☐ |
| 1.5 | Universe build — SPY + QQQ constituents, dedupe, apply hard filters, tag `SHARES_ELIGIBLE` / `LEAP_ELIGIBLE` | ☐ |
| 1.6 | Signal engine — grade every name A / B / C / NO_TRADE | ☐ |
| 1.7 | `portfolio.py` — load `portfolio.yaml`, mark to market, compute % of book + tranche depth | ☐ |
| 1.8 | Sizing engine — emit tranche #, dollar amount, next ladder rung (1.5×ATR below) | ☐ |
| 1.9 | **Constraint checker** — slots, position cap, LEAP cap, cash floor, weekly cap, halt status. **Emit BLOCKED + reason.** | ☐ |
| 1.10 | **Cash rule enforcement** — write a test that tries to route sale proceeds into an underwater position and confirms it **fails.** | ☐ |
| 1.11 | UI — SIGNALS / BOOK / VIOLATIONS / BLOCKED panels. **Every signal shows its inputs.** Never a bare "BUY." | ☐ |

**GATE:** Run against the live book. It **must** flag the current violations (7 names, 38% LEAP, 1.5% cash, HIMS 26.7%, NFLX ineligible). If it doesn't, the constraint checker is broken.

---

## PHASE 2 — PINESCRIPT
*Same rules on the chart, so my eyes can confirm the code.*

| Step | Task | Status |
|---|---|---|
| 2.1 | Port entry/exit logic to Pine v5 | ☐ |
| 2.2 | Plot: RSI(14) on 3-day, SMA(200), tranche ladder rungs, entry/exit markers | ☐ |
| 2.3 | **Reconcile Pine vs Python on 3 names.** If they diverge, one is wrong. Find out which. | ☐ |

**GATE:** Pine signals and Python signals match. No divergence.

---

## PHASE 3 — THE BACKTEST 🎯
*The most important stage in the project. This is the verdict.*

| Step | Task | Status |
|---|---|---|
| 3.1 | 5 years, full SPY/QQQ universe, **all constraints enforced** (slots, tranches, cash floor, weekly cap, halt) | ☐ |
| 3.2 | Include commissions, slippage (0.1%), and **the cash drag from the 10% floor** | ☐ |
| 3.3 | **Report:** CAGR **vs SPY buy-and-hold**, **expectancy/trade**, win rate, avg win, avg loss, payoff ratio, max DD, recovery time | ☐ |
| 3.4 | **Slot utilization** — how often was capital idle? How long did frozen positions clog slots? How many names hit tranche 3 and stayed dead? | ☐ |
| 3.5 | **Cohort split: above-200-SMA vs below-200-SMA, separately.** 🎯 *This is my core hypothesis. This is the number I care most about.* | ☐ |
| 3.6 | **Ablation study** — run each variant, report each honestly: | ☐ |
| | • No 200 SMA filter — *does the filter earn its keep?* | |
| | • Fixed −7.5% ladder vs 1.5×ATR — *was the ATR change worth it?* | |
| | • 1 tranche vs 3 tranches — *does averaging down add value or destroy it?* | |
| | • **With a stop loss vs without** — *I reject stops. I still want the data.* | |
| | • Equities only vs equities + LEAP sleeve — *is the barbell real?* | |
| 3.7 | Current-state check: "would we be in a trade right now, and in what?" | ☐ |

### ⚠️ THE RULE FOR THIS PHASE
> **Run it once. Report it honestly. Do NOT tune parameters until the results look good.**
> That is overfitting, and it will cost real money. If the strategy doesn't work, **say so.**

**GATE — this is the decision point:**
- ✅ **Expectancy > +8%/trade AND beats SPY** → proceed to Phase 4.
- ❌ **Expectancy < +5% OR fails to beat SPY** → **STOP.** Go back to Phase 0. Change the strategy. Do not lever into a system with no edge.

---

## PHASE 4 — LIVE, SMALL

| Step | Task | Status |
|---|---|---|
| 4.1 | Trade the signals live. **1–2 tranches only.** No full ladder. | ☐ |
| 4.2 | **No LEAP sleeve yet.** Equities only. | ☐ |
| 4.3 | Journal every trade: signal, grade, tranche, size, thesis, exit, outcome | ☐ |
| 4.4 | Log the signals I *don't* take, and what would have happened | ☐ |

**GATE:** 20 logged trades. Live expectancy within shouting distance of the backtest.

---

## PHASE 5 — SCALE

| Step | Task | Status |
|---|---|---|
| 5.1 | Full 3-tranche ladder | ☐ |
| 5.2 | **Turn on the LEAP sleeve.** Deep-ITM, Mag7 only, IV-filtered. | ☐ |
| 5.3 | Full 25% position sizing | ☐ |

**Only if Phases 3 and 4 agree.** If the backtest says one thing and live trading says another, **live wins** — and I go back to Phase 0.

---

## ORDER OF ATTACK

1. **Close NFLX** *(today — fails 3 rules, fixes 2 violations)*
2. **Trim HIMS to cash** *(this week)*
3. **Build the dashboard** *(Phase 1)*
4. **Run the backtest** *(Phase 3 — the gate)*
5. **Then, and only then, decide if this strategy is real.**

---

## THE HONEST NOTE

Everything before Phase 3 is plumbing. **Phase 3 is the project.**

Every position in my book is green except one. Every time I've averaged down, the market bailed me out. **I have never traded through a bear market.** My edge and a bull market are currently indistinguishable from the inside.

**The backtest tells me which one I have.** If it says no edge, I don't proceed to Phase 5 — I go back to Phase 0 and change the strategy. **That is the entire reason this exists.**
