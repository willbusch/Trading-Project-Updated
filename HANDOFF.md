---
## 2026-07-22b — EXECUTED: SPY data fix + valve verdict REVERSED + dashboard legend/concentration
LAST_COMMIT: 77054a31953ed51a666211389fcbfdcec679eb1d

Triggered by the financial-analyst deep-dive on the dashboard, which caught
two things the headline numbers hid: (1) SPY comparison was apples-to-oranges
(strategy 2018-2025 vs SPY 2021-2025, because cached SPY only went back to
2021-07); (2) the returns are almost entirely 2-3 LEAP trades.

DID:
- DATA FIX: re-ingested SPY via Robinhood get_equity_historicals back to
  2017-12, merged into data_cache/SPY_daily.parquet (now 2017-12 -> 2026,
  2166 bars). NOTE: data_cache is gitignored, so this lives on disk only —
  a fresh container must re-ingest (run_backtest.py check will flag it).
- RE-RAN Part 2 three-way valve test on corrected SPY. THE VERDICT REVERSED:
    no-valve       ret 1434% maxDD 47.8% ret/DD 30.01  (winner, barely)
    underwater     ret 1448% maxDD 48.3% ret/DD 30.00  (tie)
    underperf      ret 1237% maxDD 48.3% ret/DD 25.60  (now WORST)
  The underperformance valve's earlier "win" was an ARTIFACT of SPY history
  starting 2021-07 (it was blind to pre-2021 holds). With full history it
  over-recycles: evicts fine winners lagging SPY (UBS +23%, MMM +21%) for
  replacements that did worse (WDC -32%, RCL -55%). "Lagging SPY for a year"
  is a bad eviction signal. NOT ADOPTED. Recycling in general doesn't earn
  its keep (no-valve ties underwater). STRATEGY.md override log corrected
  (was "pending adoption" -> now "tested and not adopted").
- ANALYST READ (corrected full window 2018-2025): strategy 43.7% CAGR /
  47.8% maxDD / Sharpe 1.03 / Calmar 0.91 vs SPY 11.9% / 34.1% / 0.47 / 0.35.
  Beats SPY risk-adjusted on Sharpe/Calmar BUT: 87% of gains = 2 LEAP trades
  (one TSLA LEAP = 60%), LEAP = 94% of net P&L; ex-top-2 return ~161% total
  (~13%/yr, SPY-like) at ~1.5x SPY drawdown. Edge is unproven — it's 2
  leveraged bets that worked. Only real test left is forward, not backtest.
- DASHBOARD rebuilt: added a plain-language LEGEND (core strategy + what each
  card changes), a CONCENTRATION callout per card (top-2 % of gains, LEAP %,
  ex-top-2 return), Sharpe/Calmar stats, and the corrected full-window SPY
  (curve no longer starts mid-chart). Winner flipped to No valve.

Tests: 124 passing. reports/exit_entry_valve.md corrected with the reversal
+ an analyst section.

OPEN RECOMMENDATIONS for the owner (from the analyst read):
1. Concentration is the whole ballgame — the result is 2 LEAP trades. Test
   2-3 SMALLER LEAP slots instead of 1x30% to kill the single-point-of-failure.
2. Stress-test the LEAP pricing (realized-vol-as-IV, flat 4% rate) on
   META/TSLA at +/-20-30% IV — the 2 trades driving everything are the most
   model-dependent.
3. The 2022 mega-cap capture is a LEAP-SLOT problem (needs more LEAP slots /
   a LEAP-slot valve), not equity — no equity valve can fix it.
4. Backtesting is exhausted on this data; forward paper/small-live is the
   only thing that resolves edge-vs-luck.
5. Phase 0 (fix the real book) still the highest-value untouched real-money item.

NEXT: owner picks a direction from the above. Awaiting answers to 5 analyst
questions (drawdown tolerance; diversify the LEAP sleeve?; goal = beat-SPY
vs leveraged-upside; capital/horizon; which follow-up to build first).
---

---
## 2026-07-22 — EXECUTED: Exit/Entry analysis + underperformance valve + dashboard redesign
LAST_COMMIT: d0f9d9e

DID: three parts, all on the EXISTING 12-cell grid data (only Part 2 ran
new sims). Full report: reports/exit_entry_valve.md.

PART 1 (no new sim — aggregated the existing grid):
- 1a Trailing mechanic ut_trail vs pct_trail: essentially a WASH. pct
  marginally ahead on average (517% vs 508% return, ret/DD 10.93 vs 10.70);
  ut won only 2/6 pairs; biggest runners identical. The champion's ut_trail
  win is one of the 2 lucky cells, not a mechanic edge.
- 1b Entry timeframe daily vs 3-day: 3-day's higher average is an
  INTERACTION with sizing, not a standalone edge (3-day wins with
  deepen/both, daily wins with diversify; trade counts + win rates
  near-equal). Low confidence 3-day is genuinely better.
- 1c 0.5-0.9 dead zone: champion cell had ZERO 6mo+ stalls; pooled 6/215
  equity trades (3%). Real in theory, rare in practice, doesn't bind the
  winner. Diagnostic only, no rule changed.

PART 2 (the ONE new mechanic test): underperformance-triggered valve —
recycle a held equity trailing SPY by >=5% annualized over its own hold
window (vs the old "underwater" trigger). Three-way on champion cell
(3day/both/ut_trail), pre-vault:
  no-valve       ret 1040.6% maxDD 47.5% ret/DD 21.91  0 recycles  9 trades
  underwater     ret 1064.2% maxDD 48.2% ret/DD 22.07  6 recycles 17 trades
  underperf(NEW) ret 1221.0% maxDD 47.2% ret/DD 25.89  3 recycles 13 trades
The new valve WON on this cell and recycled the RIGHT targets (VZ +2.5% but
lagging SPY +12% — a mediocre winner the underwater trigger can't see; plus
RCL/NEM deep laggards). BUT two blockers, both reported plainly:
  (1) It does NOT capture the Oct-Dec 2022 mega-caps it was built for.
      META enters as a LEAP (Mar 2022); GOOG/GOOGL/AMZN/NVDA never enter.
      Those names are top-10-cap LEAP-eligible -> they contend for the
      SINGLE LEAP slot (held by the 2022 META LEAP), NOT equity slots. The
      valve only frees equity slots and never touches the LEAP, so it
      STRUCTURALLY cannot admit them. Fixing this needs LEAP-slot changes,
      out of scope for this equity-only valve.
  (2) Cached SPY history starts 2021-07 -> the trigger is BLIND to
      pre-2021 (2020-vintage) holds, including the UBS/SCHW names the owner
      complained about. Win is partial-coverage, not apples-to-apples with
      underwater. FOLLOW-UP: ingest SPY back to 2018 to test properly.
  VERDICT: PENDING OWNER ADOPTION, not promoted. Config default stays
  "underwater". Code + 4 new tests live (recycle_trigger="underperformance").

PART 3: dashboard REDESIGNED (reports/results_dashboard.html) — grouped by
STRATEGY not chart type. 4 cards (no-valve / underwater / underperformance-
WINNER / SPY), essential stats only + a Notes & Takeaways block per card
(honest good AND bad), winner crowned by ret/DD with one-line reasoning,
equity curves on a shared axis (SPY honestly starts 2021-07, no back-fill),
Part 1 mechanic analysis, collapsible trade log + collapsed Archive of
retired-generation research. Caveat banner prominent up top. 116KB (was
191KB). generate_dashboard.py is now self-contained; the old two-step
generate_dashboard_data.py was removed.

Tests: 124 passing (added 4 underperformance-valve tests). Also this
session earlier: shipped the SessionStart hook + scripts/run_backtest.py +
run-backtest skill (env auto-setup + canonical runner).

NEXT: owner reviews the redesigned dashboard + the valve verdict. If the
underperformance valve is worth adopting, first ingest SPY back to 2018
(so it can see 2020-vintage holds) and separately decide whether to fix the
2022 mega-cap capture via LEAP-slot handling (a different, un-tested change).
Phase 0 (fix the real book) still the highest-value untouched real-money item.
---

---
## 2026-07-22 — EXECUTED: Beat-SPY Package (A1-A8) + 12-cell grid + attribution — HONEST VERDICT: still no
LAST_COMMIT: 470ab43

DID: implemented all 8 locked fixes (A1-A8) diagnosed from the 2026-07-21
run's 62.8%-max-drawdown post-mortem, then ran a 12-cell grid (2 entry
timeframes x 3 equity-sizing variants x 2 trailing mechanics) plus a
7-step cumulative attribution ladder on the champion cell. Full report:
`reports/beat_spy_package.md`.

A1 sizing (30% LEAP/65% equities/5% floor) - config only. A2 replaced the
flat $500B LEAP floor with a top-10-by-market-cap-PROXY rank at entry date
(backtest/leap_topcap.py, implied-shares x historical-close) - confirmed
MU never qualifies in any year; the 62.8%-drawdown MU LEAP does not recur.
A3 reversed the 2026-07-21 "dedicated reserve, wall" model to spendable
working capital in SPY. A4 added a slot-time recycling valve (>=365d held,
underwater, better candidate waiting -> recycle; winners never touched).
A5 tightens the LEAP exit floor 0.9->0.7 past 50% of modeled runway, no
hard time-close. A6 narrowed the kill switch to LEAP-only (equity dip-buys
pass through a halt). A7 retired the 1.618 hard exit for a trailing exit
(ut_trail/pct_trail). A8 fixed the dashboard's SPY-curve truncation bug
(all curves now reindexed to a shared date union before serializing).
BONUS FIX found while building A4: the entry-fill loop iterated
`sorted(pending_entries)` (alphabetical), silently discarding the
2026-07-21 ratio-tiebreak's rank order - the "AMAT beat 4 smaller names"
result may have been alphabetical luck, not the ratio rule. Fixed;
regression test added. 31 new tests, full suite 120 passed before the grid
ran.

RESULT - HONEST VERDICT: **the package still does NOT beat SPY
risk-adjusted.** Every one of the 12 tested cells runs 44.9%-48.9% max
drawdown pre-vault (real progress vs 62.8%, but still ~2x SPY's 25.4%);
same story in the vault (20.3% vs SPY's 9.1%). Raw returns are enormous
(127%-1064% pre-vault) but the MANDATORY OVERFITTING GUARD caught it: the
#1 cell beats #2 by only 9.7%, every cell's "vault expectancy" is a single
closed trade (statistically meaningless), and the top-ranked cells'
returns are concentrated in 2-3 LEAP trades (TSLA twice, META once) that
landed inside two of the dataset's largest individual-stock rallies -
flagged explicitly as likely lucky timing, not proven edge, per this
project's own "too good to be true = leak-hunt it" discipline. A2 (top-
10-cap LEAP eligibility) was overwhelmingly the load-bearing fix - the
only attribution step that improved BOTH return and max drawdown together
(theirs: 91.5%->1042.5% return, 54.9%->40.1% max DD). A4 (recycling)
actually REDUCED return in this run - a real cost, not a free lunch. A5
(decay exit) had zero measurable effect in this specific backtest.
Dashboard regenerated with the champion cell as primary, verdict panel now
shows return AND max-drawdown pills separately per window (was return-only
before). STRATEGY.md (v5.0) and PLAN.md updated with the full override log
and a new research-re-closed section.

NEXT: research re-closes again on the same data ceiling (survivorship-
biased universe, current-snapshot caps feeding the new top-10 proxy too,
realized-vol-as-IV). The evidence-backed default remains: index, don't run
this system with real capital, until a genuinely out-of-sample forward
track record says otherwise. Phase 0 (fix the real book) and the ORCL
average-down judgment call remain separately open from prior sessions.
---

---
## 2026-07-21 — HANDOFF
LAST_COMMIT: 38f6504
SNAPSHOT: Flat 0.55-delta LEAP approximation retired, replaced with a real Black-Scholes engine — every historical LEAP trade was mispriced (2.5-3.8x understated on winners; one MU trade flips to expired-worthless -100%). Full-span max drawdown rose to 62.8% (traced to that same MU LEAP), confirmed as real leverage risk, not a bug. Tiered gate adopted official, ratio tiebreak verified working in-run (AMAT beat 4 smaller names), sizing changed to 4 equity + 1 LEAP at 33%, daily/weekly locked. 89 tests green. Research formally re-closed.
NEXT: Owner reviews the dashboard's new LEAP-correction section (8) and reports/fib_final_run.md, decides whether the locked configuration (33% single-LEAP sizing + real convexity + 62.8% max DD) is an acceptable risk profile. Phase 0 (fix the real book) and the ORCL average-down judgment call remain separately open from two sessions ago.
---

---
## 2026-07-21 — EXECUTED (from chat): Real LEAP pricing + tiered gate adopted + tiebreak fix
DID (priority order, all 3 done):
T1 — REAL LEAP PRICING (backtest/leap_bs_pricing.py, new): retires the
flat 0.55-delta static approximation entirely. Black-Scholes engine —
strike (K) and volatility (sigma) FROZEN at entry, only underlying price
(S) and remaining time (T) evolve day to day. sigma = the underlying's own
trailing 252-day realized vol as of the entry SIGNAL bar (forward-only,
no historical IV surface available from this data source). K solved from
target delta (0.55-0.65 midpoint = 0.60) via closed-form inversion.
Position sizing now real contracts at a real premium, not a delta-scaled
share-equivalent. Wired into portfolio_state.Position (new strike/
expiry_date/sigma fields, market_value now calls the BS engine) and
fib_simulator.py's entry/exit fill logic. 8 new pricing tests incl. a
convexity test (LEAP % move > underlying % move) and a lookahead test on
realized_vol. Architecture note: real historical option data CANNOT drive
the simulator live (MCP tools aren't callable mid-run — same constraint
as scanner/refresh.py) so the BS engine is the actual pricing engine; real
option data was used as a post-hoc validation layer for the trades this
run produced, not the live engine.

CORRECTION DEMONSTRATED (scripts/leap_pricing_correction.py, same entry/
exit dates+prices as before, only the pricing model varies): JPM old
+28.8% -> new +196.8% (3.76x underlying's move). ASML +24.9% -> +143.0%
(3.16x). TSLA +77.3% -> +440.1% (3.13x). MU(2nd) +49.9% -> +230.9%
(2.55x). MU(1st): underlying nearly flat (-1.2%), old approx -0.6%, NEW
REAL -100.0% -- EXPIRED WORTHLESS, a real outcome the old linear model
could never represent. MSFT (still open): old ~0%, new -21.7% (theta
decay on a barely-negative underlying move).

T2 — SIZING + TIERED GATE + TIEBREAK + RESERVE + LOCK: LEAP delta 0.50-
0.60 -> 0.55-0.65. LEAP single-entry/sleeve cap 20%/25% -> 33%/33%
(identical by design, only 1 LEAP ever held). Equity slots 5 -> 4 (5th
slot's capital is now the dedicated LEAP reserve). Tiered gate (25/30/40
by market-cap tier) ADOPTED as official, no longer experimental. Ratio-
based tiebreak (drawdown / tier threshold) replaces raw deepest-drawdown-
first -- new check_leap_reserve constraint (33% reserved as cash, NOT
backfilled to equities, while no LEAP held). Daily/weekly cell LOCKED
(matrix search retired). No-displacement confirmed already-true (no
eviction logic exists). VOO reserve documented in STRATEGY.md as live-
execution-only, explicitly NOT modeled (SPY-idle-cash benchmark already
captures the same behavior). 6 new tests (ratio tiebreak + LEAP reserve).

T3 — RAN the locked config (daily/weekly, tiered gate, real LEAP pricing,
new sizing/tiebreak) full-span + all windows. Leak-hunt passed (9-15%
CAGR on meaningful windows; two thin-window CAGR spikes traced to n=2/3
samples, consistent with every prior round). VAULT: 2 trades (above the
1-2 range, still thin). MAX DRAWDOWN ROSE TO 62.8% (was 17-40% every
prior round) -- traced directly, not assumed: the MU LEAP (33% of book)
sat open through the entire 2022 bear market before expiring worthless in
Oct 2023; peak $265,671 -> trough $98,923 exactly overlaps that window.
Leverage cutting both ways, confirmed not a bug. Tiebreak verified working
in the actual run (not just unit-tested): AMAT ($421B) won a contested
slot over CVS/HOOD/MDT/QCOM (all smaller-cap, harder-gated) on 2025-01-06.
Full report: reports/fib_final_run.md.

Found + fixed a real consistency bug while building the dashboard: a
fresh re-simulation gave different trade counts (10/0) than the report's
window-sliced runs (7/2) -- traced to the known universe-snapshot-timing
sensitivity (documented last session) COMPOUNDED by a real methodology
mismatch (full-span-then-date-filter vs independently-simulated windows
produce different trades even from identical data, since window-slicing
restarts state at the boundary). Fixed by making the dashboard consume
the exact pickled report run instead of re-deriving stats.

Dashboard regenerated with real-LEAP-priced results as primary; new
section 8 (LEAP Pricing Correction table, the headline finding); section
7 relabeled ADOPTED (was EXPERIMENTAL); caveat banner updated to this
run's verbatim honest framing. Sent to owner for visual check.

STRATEGY.md rewritten to v4.0: LEAP pricing section rebuilt (4a real
pricing / 4b dedicated reserve / 4c VOO live-execution rule), tiered gate
marked ADOPTED, ratio tiebreak documented with the AMAT proof point, all
sizing tables synced (Part 3, Part 6), 9 new override-log entries.
PLAN.md: research RE-CLOSED (was reopened last session), with a parked
note on the deeper universe-snapshot-timing fix (snapshot once per
research generation instead of re-scanning live) if this project
continues.

89 tests green (14 new this session: 8 BS pricing tests incl. convexity +
lookahead, 5 LEAP-reserve constraint tests, 1 ratio-tiebreak integration
test — see tests/test_leap_bs_pricing.py, tests/test_leap_reserve.py,
tests/test_ratio_tiebreak.py).

LAST_COMMIT: 4da180bdb0a8733d7b2f6f7837aa706fc86ca7c6
---

---
## 2026-07-20 — HANDOFF
LAST_COMMIT: 5912806
SNAPSHOT: Tiered drawdown gate (25/30/40 by market-cap tier) implemented and re-tested across all 6 timeframe cells. Real improvement on trade year-spread (2021-2026, not just 2020) but NOT a clean win — lowered trade count/return on the former champion cell via a verified slot-competition effect. No cell beats the flat-gate baseline unambiguously. Dashboard regenerated with new section 7. 75 tests green.
NEXT: Owner reviews the dashboard's new tiered-gate section and reports/fib_tiered_gate.md, then decides whether to adopt tiering (and which cell, if any), keep the flat gate, or park this too. Phase 0 (fix the book) and the ORCL average-down judgment call remain separately open from last session.
---

---
## 2026-07-20 — EXECUTED (from chat): Tiered drawdown gate — research reopened
DID: Implemented and ran the owner-specified tiered drawdown gate (25%
$500B+ / 30% $150-500B / 40% under $150B, by CURRENT market cap — no
point-in-time data available, flagged as a proxy same as universe
membership). New: `backtest.fib_universe.gate_of_tiered` +
`build_universe_frames(market_caps=)` param (backward compatible, flat
gate stays default). 2 new tests. 75 tests green total.

Mechanical note: only the $150B-500B band actually changes (40%->30%) —
$500B+ names were already 25%, sub-$150B already 40%. 73/200 universe
names affected. Verified per-ticker (ORCL: 130->176 eligible days,
8->10 entry candidates) before trusting aggregate output.

Ran the full 6-cell timeframe matrix under the tiered gate (daily/3day/
weekly entry x 3day/weekly exit), ~130-165s/cell, ~15min total — did NOT
need to reduce to 3 cells, ran all 6. Leak-hunt passed (11-23% CAGR,
no cell near 50%).

HONEST RESULT (reports/fib_tiered_gate.md): trades now genuinely spread
across 2021-2026 (previously ~all 2020) - the crash-concentration
diagnosis was correct and the fix works directionally. BUT counterintuitively
LOWERED trade count + total return on the former champion cell
(daily/weekly: 12->9 trades, +416%->+117%) via a verified emergent effect
- more eligible names now compete for the same 5-slot/2-per-week throttle,
crowding out some of the flat gate's biggest winners. Not a bug - checked
directly. Vault trade counts stayed thin (1-2 per cell) and were shown to
be sensitive to minor universe-snapshot timing (re-running the flat
baseline fresh this session gave 2 vault trades, not the dashboard's
earlier-observed 1 - itself evidence the vault sample is too thin to
treat as decisive). Sorting by total return (owner's explicit choice)
surfaces weekly/3day as the "winner" (+259%) but it has the WEAKEST vault
performance of all 6 cells - flagged prominently as the exact
one-COVID-trade-dressed-as-champion risk the owner asked to guard against.

No single cell delivers an unambiguous win over the flat-gate baseline.
This IMPROVED the strategy's honesty about its own limits; it did NOT
prove edge - stated verbatim per the owner's framing requirement.

STRATEGY.md: drawdown-gate section rewritten to document the tiered gate
as the active experiment (not a proven replacement); status banner updated
to "research reopened." PLAN.md: reopened note added above the prior
closed note (kept, not deleted, for history).

Dashboard regenerated: new section 7 "Tiered Drawdown Gate - EXPERIMENTAL"
added to reports/results_dashboard.html (6-cell matrix + flat-vs-tiered
comparison, both re-run fresh this session for an apples-to-apples
comparison). Sent to owner for visual check alongside the update.

LAST_COMMIT: f066c008e5d7ced504ab00ecefb4e4e1940609d6
---

---
## 2026-07-20 — HANDOFF
LAST_COMMIT: edec90d
SNAPSHOT: Two-account book reconciled (equities were in an unreachable second account, not sold; ORCL updated to 36 sh/$144.81 basis) and reports/results_dashboard.html built (6 sections, real equity curves, sent to owner for visual sign-off). 73 tests green.
NEXT: Owner to confirm the dashboard renders correctly (chart, mobile layout), then decide on Phase 0 (fix the book) using the reconciled STRATEGY.md Part 7 targets, and separately weigh in on today's ORCL average-down.
---

---
## 2026-07-20 — EXECUTED (from chat): Book reconciled + results dashboard
DID (2 tasks):
T1 — Reconciled the "zero equities" mystery: not a sold book, a connection
gap. Account 1 (margin, live MCP) = the 2 LEAPs only. Account 2 (equities:
HIMS/NOW/HOOD/SOFI/ORCL) is not reachable via this session's Robinhood
connection; its figures now live in `portfolio.yaml` (gitignored — real
financial data) carried from the 2026-07-14 audit, marked to live quotes
pulled today, except ORCL which reflects today's trade: +5 sh @ $125.00,
31->36 shares, basis re-blended $148.00->$144.81. New dated snapshot
`docs/portfolio-audit-2026-07-20.md`. STRATEGY.md Part 7 rewritten: the
"zero equities" flag is gone, replaced with the reconciled combined-book
violation table (7 positions vs 6, LEAP sleeve 35.8% vs 25%, cash ~0.2%
vs 5%, HIMS 27.5% vs 15% — WORSE than July 14's 26.7%, pure appreciation).
ORCL add flagged with FACTS not judgment: clears the 40% drawdown gate
(62.2% off hybrid high) but had NO UT-buy signal firing that day — reads
as a discretionary average-down under the v3.0 rules, not a rule-triggered
entry (checked via backtest.fib_features directly, same code as always).
scanner/report.py now labels positions by account (never merged) and
computes violations on the combined book, matching the project's
established convention. Found + fixed THREE real bugs while wiring this
up: (1) violations_section's total_value fallback only fired when the
grand total was exactly zero, so Account 2's equity value silently
vanished from every % calculation whenever Account 1 already had one —
inflated every position's reported % of book by ~3x; (2) LEAP sleeve %
used cost basis instead of live account value (no live options mark was
being captured) — fixed to use each pure-LEAP account's own live
total_value; (3) held-but-not-Fib-eligible positions (HOOD) and
held-but-outside-the-current-quality-gate positions (HIMS, SOFI — smaller
caps that no longer clear $10B+/profitability) now get clear explanatory
notes instead of a raw NaN or a misleading "not found" error.

T2 — Built `reports/results_dashboard.html`, self-contained (inline CSS/JS,
Chart.js via CDN, all data embedded — no external calls, renders on
desktop + phone). Reconstructed real equity curves via
`scripts/generate_dashboard_data.py` (winning cell daily/weekly, 0.9-floor
exit, one continuous full-span run — the ablation only stored window
summary stats, not raw curves) -> `reports/dashboard_data.json`. All 6
required sections: equity curves (strategy / strategy-with-SPY-idle-cash /
SPY buy-hold, vault boundary marked), verdict panel (pre-vault + vault
stats separately, plain pill verdict), 3-way exit-ablation comparison
table (winner highlighted, latch's $77k give-back shown), The Gap
visualization (0 for the winner in this sample — flagged as unlikely to
stay 0 on a larger universe), sortable 22-row trade log ("kind" substituted
for "account" since backtest trades aren't tied to a real brokerage
account — flagged, not silently omitted), verbatim caveat banner. Sent to
the owner for visual sign-off before finalizing.

PLAN.md notes the below-0.5 latch refinement as PARKED, not queued —
only build if explicitly asked, since the 3-way ablation already retired
the latch concept outright.

73 tests green throughout (no new tests needed — this was records +
visualization, not new signal logic; existing scanner tests updated for
the two-account signature change).

LAST_COMMIT: c2cad73b0803e2331ba27d6ce31bd0ef91938bd6
---

---
## 2026-07-20 — HANDOFF
LAST_COMMIT: 0a6adec
SNAPSHOT: Fib strategy promoted to official (STRATEGY.md v3.0), final exit ablation run (plain 0.9-floor wins, latch design rejected), live scanner scaffolded and run against real Robinhood accounts. 73 tests green.
NEXT: Owner must confirm which book is real — the July 20 live scan found ZERO equity positions in any linked account (only 2 LEAPs, 84% sleeve, 0% cash), contradicting the July 14 manual audit's 7-position book. Phase 0 (fix the book) is blocked on this until resolved.
---

---
## 2026-07-20 — EXECUTED (from chat, morning prompt): Promote Fib, final ablation, scanner scaffold
DID (4 tasks, in dependency order):
T1 — STRATEGY.md rewritten to v3.0: drawdown-gated Fib is now the OFFICIAL
strategy, RSI(3) system formally retired (Part 0 retirement note), the
2026-07-19 engine swap logged as an override (it never had been). PLAN.md
status table fixed to match reality (was contradicting its own body per
the 2026-07-19 review); Strategy D open loop closed (moot, retired).
"PLAUSIBLE, NOT PROVEN" banner added up top — carries every caveat verbatim.

T2 — Final structural ablation on the universe winning cell (daily/weekly):
3-way equity exit (simple 0.5 floor / simple 0.9 floor / new full-latch
design FullLatchExitV2) + deployment throttle (5 slots/2-per-wk vs 6/3).
Selection used PRE-VAULT expectancy only (vault reported but not used to
pick, across 5 candidate variants — avoids re-peeking the same held-out
window). WINNER: simple 0.9-floor, no latch (exp +93.9% vs +45.8% old
champion vs +82.4% new latch design) — simplicity wins again. Latch design
costs $77,064 in quantified give-back (3 Gap trades) with no expectancy
edge. Throttle loosening HURT (return 4.16->2.15 pre-vault) — kept at 5/2.
STRATEGY.md's exit section updated with the winner. simulate_fib's default
exit_variant changed to "simple_09". Found + fixed a real bug while
generalizing: the old simple_exit=True path had silently forced LEAP exits
through the 0.5 equity floor instead of their documented 0.9 floor in the
prior universe run — now independent per position kind.
reports/fib_final_ablation.md has full detail.

T3 — Scaffolded scanner/ (Phase 1, the original project vision): refresh.py
(documents the agent-driven MCP refresh steps — no standalone automation is
possible, MCP tools are agent-turn-only) + report.py (pure Python, imports
ONLY tested backtest modules, 4-section daily report: ELIGIBLE, FIRING,
OPEN POSITIONS, VIOLATIONS). Signal-parity test green. RAN IT LIVE against
the real Robinhood accounts (read-only, no orders) as proof — see
reports/live_scan_2026-07-20.md. Found + fixed a second live bug: open-
positions anchor lookup used an empty leap_tickers set, breaking MSFT's
gate threshold (40% instead of 25%) and NaN'ing its Fib fraction.

🔴 T3 LIVE-DATA FINDING (not a bug — a real discrepancy): the live pull
found ZERO equity positions in ANY of the 3 linked Robinhood accounts —
only the 2 known LEAPs (NFLX, MSFT), 84% LEAP sleeve, 0% cash. This
contradicts the July 14 manual audit's "7 positions, HIMS 26.7%" book.
Either equities were sold since July 14 and the audit was never updated,
or they're in an account this session can't see. STRATEGY.md Part 7 now
carries BOTH the live pull and the stale audit side by side, flagged.
**This must be resolved before Phase 0 (fix the book) can proceed** — see
next-step below.

data/live_positions_snapshot.json is real account data — gitignored, never
committed (added to .gitignore this session, matching portfolio.yaml).

73 tests green (14 new this session: exit-variant + hybrid-anchor +
scanner tests, incl. 2 lookahead tests and 1 signal-parity test).

RESEARCH PHASE FORMALLY CLOSED (docs/PLAN.md) — further strategy iteration
needs a data source with point-in-time membership + historical fundamentals,
which Robinhood cannot provide. Effort moves to Phase 0 and Phase 1.

LAST_COMMIT: 7a0818791523419ff9a75abcfec9c4f99aa24495
---

---
## 2026-07-19 — HANDOFF
LAST_COMMIT: c236af6
SNAPSHOT: Full-universe (200-name current-membership proxy) Fib run complete. Winning cell daily/weekly beat SPY and the SPY-idle-cash variant in the 12mo vault, but on 2 trades with 100% win rate every window = survivorship; not proof of edge. 59 tests green.
NEXT: Owner decision — a real edge verdict needs point-in-time membership + historical fundamentals (NOT available from Robinhood; different data source required). Otherwise iterate the strategy or accept the proxy result as the ceiling of what this data can show.
---

---
## 2026-07-19 — EXECUTED (from chat): Full-universe run (200-name proxy)
DID: Scaled Fib strategy to a 200-name universe. 4 changes: (1) latch
DROPPED (simple equity exit now active; latch kept for reference), (2)
HYBRID ANCHOR (504d default, ~4yr extended when peak aged out; fires on
146/200 names), (3) quality gate = static membership in a live scanner
list ($10B+, positive net margin, >1M vol), (4) SPY-idle-cash benchmark.
New: fib_universe.py, scripts/ingest_universe.py, render_universe_report.py,
data/universe_snapshot.json, hybrid_anchor_high + use_hybrid + idle_cash_spy.
59 tests green incl. hybrid-anchor lookahead test. Ingested 190 names (100%
coverage, 2018→2026).
DATA REALITY: Robinhood has NO index-membership filter + only CURRENT
fundamentals -> this is a current-membership/current-fundamentals PROXY, not
point-in-time SPY/QQQ. Severe survivorship, flagged verbatim in report.
Runtime forced the authorized REDUCED 4-cell set (~143s/cell).
VERDICTS (reports/fib_universe.md): winning cell daily/weekly beat SPY in
vault (+37.7% vs +18.4%) AND SPY-idle-cash variant (+42.0% vs +18.4%). BUT
100% win rate every window = survivorship; vault rests on 2 trades; COVID
cluster dominates. Honest: NOT proof of edge, clears bar barely on thin
evidence. Leak-hunt passed (combined CAGR 11-15%).
OPEN: real edge verdict needs point-in-time membership + historical
fundamentals — NOT available from Robinhood; different data source required.
LAST_COMMIT: 572383b9b29b4ff2919bc4b3cc4311f7ceaceb2d
---

---
## 2026-07-19 — HANDOFF
LAST_COMMIT: 55e141a
SNAPSHOT: Latched-Fib strategy built + 7-cell timeframe matrix run on 12 curated names. Best cell daily/weekly does NOT beat equal-weight-buy-hold-same-names (0 vault trades vs +65%); latched does not beat simple; leak-hunt passed. A/B/C/D retired.
NEXT: Owner decision on whether to proceed to the full SPY/QQQ universe run (hybrid anchor for young names) or iterate the strategy given it sat in cash through the 12-month vault.
---

---
## 2026-07-19 — EXECUTED (from chat): Latched-Fib strategy, 12-name matrix
DID: Built the drawdown-gated latched-Fib strategy end-to-end and ran the
full 7-cell timeframe matrix on 12 curated names. A/B/C/D RETIRED (Strategy
D open loop closed as obsolete). New modules: multi_tf (UT on weekly/3day/
daily on one daily clock), drawdown_gate extended (Fib levels + stale
detection), fib_exit (latched equity + simple LEAP machines), fib_features,
fib_simulator (daily clock, reuses risk framework + cash rule untouched),
fib_reporting, fib_orchestrate. Ingested META/NVDA/AMD/MU/TSLA. Stale-anchor
Option 1 applied (exclude from headline + both-ways diagnostic). Slot
tiebreak defined (deepest DD → earliest gate-clear → alpha). LEAP force-
close suspended strategy-scoped; 1.75yr entry floor; 2yr modeled expiry.
57 tests green incl. exit-machine + simulator lookahead tests.
VERDICT (reports/fib_matrix.md): best cell daily/weekly. Does NOT beat
equal-weight-buy-hold-same-names — 0 vault trades (sat in cash) vs +65%.
Latched does NOT beat simple (identical; latch never fired). Leak-hunt
passed (no cell >18% CAGR; high per-trade exp = long-hold survivorship).
OPEN: full SPY/QQQ universe run (hybrid anchor) designed not built;
expired-worthless LEAPs unmodelable by delta-approx (reported N/A).
LAST_COMMIT: 08aec85787096b62734d750e39f254ce56393be2
---

---
## 2026-07-19 — HANDOFF
LAST_COMMIT: 3234db7
SNAPSHOT: A/B/C/D backtest engine built and run once on the 7 held names (engine-validation pass, survivorship-biased by design). Strategy D was reconstructed from Addendum 2 alone — Addendum 1 (which defined D) never reached this session; two of D's params are flagged assumptions pending owner confirm/veto.
NEXT: Get owner confirm/veto on strategy_d.volume_avg_bars (20) and the sweep range (1.0-2.0 step 0.25) in config.yaml; re-run D if either changes.
---

---
## 2026-07-19 — EXECUTED (Addendum 2; Addendum 1 NEVER ARRIVED — D reconstructed)
DID: Built and ran the full A/B/C/D backtest engine on the 7 held names.
New: screener/weekly.py + 8 backtest/ modules around ONE shared simulate()
engine; 43 tests green incl. the adversarial cash-rule test. Config owner
overrides applied and logged (15% equity cap, 5% cash floor, 0.50-0.60
LEAP delta, 5+1 slots, SMA(200) fully removed from signals per Addendum 2,
arm expiry locked to RSI-reclaims-50/no day cap). SPY ingested for the
benchmark. LEAP spike: Robinhood DOES serve expired-contract history;
this pass still used the labeled delta-0.55 approximation uniformly.
RESULTS (reports/abcd_comparison.md, survivorship disclaimer in header):
C took ZERO trades under B-swept UT(4.0,7) — arms set, never fired; C
works under default UT(1.0,10) (16 trades, +6.7% exp). B collapsed
+128.7% pre-vault -> -4.4% in the vault (VAULT NOW SPENT). Both sweeps
picked edge-of-grid cells (unstable). 70->60 exit hurt everything.
FLAGGED: Strategy D's volume_avg_bars=20 and sweep range 1.0-2.0 are
ASSUMED defaults (Addendum 1 missing) — need owner confirm/veto.
LAST_COMMIT: 3234db7
---

---
## 2026-07-17 — HANDOFF
LAST_COMMIT: 308c16d
SNAPSHOT: Full architecture designed (Plan-agent-assisted) for the A/B/C backtest engine on the 7 held names — 10 new files, one shared simulate() engine, ~10 judgment calls resolved and stated plainly. Zero implementation code written yet; awaiting owner go-ahead to start.
NEXT: Get explicit go/no-go on starting the 10-step build sequence, then execute it.
---

---
## 2026-07-17 — HANDOFF
LAST_COMMIT: dc9b056
SNAPSHOT: Building a 3-way strategy comparison (RSI-alone, UT-Bot-alone, RSI-armed/UT-triggered) on the owner's 7 held names. UT Bot ported and tested; RSI(14) re-tune proposal rejected and reverted; 20% position cap and NFLX-hold-to-expiry applied as owner overrides. Backtest engine itself not built yet.
NEXT: Confirm UT Bot signals (MSFT/HIMS/ORCL) against TradingView before building Strategy B/C and the backtest engine on top of it.
---

---
## 2026-07-15 — HANDOFF
LAST_COMMIT: 29c651b
SNAPSHOT: RSI(14)/Robinhood-only switch complete and unchanged since last handoff; RSI(14) values and threshold re-tune still awaiting confirmation.
NEXT: Confirm RSI(14) vs TradingView and confirm/reject the proposed threshold re-tune.
---

---
## 2026-07-15 — EXECUTED (from chat)
DID: Switched RSI(3)->RSI(14) on 3-day bars (config.yaml rsi_period),
made Robinhood MCP the sole data source (yfinance removed entirely from
screener/data.py and requirements.txt, no fallback), resolved two config
keys (avg_volume_lookback_days removed, weekly_lower_low_lookback_weeks
set to 8). Computed and presented RSI(14) values for MSFT/HIMS for
TradingView cross-check (not yet confirmed). Proposed re-tuned
entry/exit thresholds with 5-year signal-frequency evidence (old
euphoria threshold RSI>=80 was firing 0.2x/year for MSFT - functionally
dead) - proposal only, NOT written to config pending confirmation.
Added an RSI(14) unit test. docs/PLAN.md updated; STRATEGY.md/GOAL.md
deliberately left untouched (still describe RSI(3), flagged as open
drift). No Stage 1 work. 11/11 tests passing.
LAST_COMMIT: 9b41a7d
---

---
## 2026-07-15 — HANDOFF
LAST_COMMIT: b61d956
SNAPSHOT: Stage 0 foundation unchanged (built/tested); this session added two project-management skills (handoff-to-chat v3 facts-only, trading-project-review corrected + run once). yfinance still network-blocked.
NEXT: Confirm the Stage 0 RSI(3)/3-day values against TradingView for MSFT and HIMS.
---

---
## 2026-07-15
LAST_COMMIT: 87b55bb

**TL;DR:** Built and tested Stage 0 (data fetch, 3-day resampling, RSI/SMA/ATR indicators) per the build plan. Archived all six strategy source docs into the repo so they're permanently saved. Added this handoff skill so Code and Chat can stay in sync going forward.

**Next step:** Confirm the Stage 0 RSI(3) gate values against TradingView, then resolve the yfinance network block (or pick a real bulk data source) before starting Stage 1 (SPY/QQQ universe build).
---

# HANDOFF TO CHAT — 2026-07-15

## TL;DR (3 lines max)
Built and tested Stage 0 of the screener (data fetch, 3-day bar resampling, RSI/SMA/ATR indicators). Archived all six strategy source docs into the repo permanently. Ran a one-time RSI(3) eyeball check and an informal (non-authoritative) 2-name signal backtest at your request.

## MAJOR CHANGES
- `config.yaml`: every strategy threshold as a named key (universe filters, entry/exit, sizing, LEAP rules, circuit breakers). Two params — weekly lower-low lookback, avg-volume lookback window — are flagged TBD since STRATEGY.md doesn't quantify them yet.
- `screener/data.py`, `resample.py`, `indicators.py`: yfinance fetch with parquet caching that fails loudly on missing data (never silently fills), a documented daily→3-day resampling rule, and Wilder-smoothed RSI/SMA/ATR matching TradingView's default convention. 10 unit tests passing, including hand-derived reference values.
- Ran the Stage 0 gate once on MSFT/HIMS (via Robinhood, since this sandbox still blocks Yahoo Finance) and produced RSI(3)/3-day values — not yet confirmed correct against TradingView.
- `docs/`: archived all six strategy documents (build spec, strategy, goal, plan, investor one-pager, portfolio audit) so they're version-controlled instead of session-only uploads.

## MINOR CHANGES
- `requirements.txt` pinned (yfinance, pandas, numpy, pyarrow, PyYAML, pytest, lxml) after the sandbox's venv got wiped once mid-session.
- `.gitignore` added for venv/cache/pycache.
- PR #1 opened and merged into `main` for everything above.

## CURRENT STATE
- Works now: Stage 0 foundation (fetch/cache/resample/indicators) is built, tested, and has run once on real data.
- Broken/half-finished: Stage 1 (universe build) not started — needs a real bulk data source since yfinance is still network-blocked here and Robinhood isn't practical for 500+ names. Two config params still undefined.
- Also ran an informal, uncommitted 2-name signal backtest (MSFT/HIMS, no portfolio rules, no costs) at your request — exploratory only, not the real Stage 6 backtest, not saved to the repo.

## DECISIONS MADE
- RSI uses Wilder's SMA-seeded smoothing (TradingView's default), not a naive EMA.
- 3-day bars anchor to the start of fetched history, not a calendar boundary — documented, not yet confirmed against TradingView.
- Declined to tune RSI thresholds off the informal 2-name backtest (overfitting risk on n=23 trades). Logged two candidate variants (confirmation entry, LEAP/share exit asymmetry) for the real Stage 6 ablation study instead.

## NEXT STEP
Confirm the Stage 0 RSI(3) gate values against TradingView, then resolve the yfinance network block (or pick a real bulk data source) before starting Stage 1 (SPY/QQQ universe build) — per PLAN.md.

## OPEN QUESTIONS FOR CHAT
- Weekly "not making lower lows" lookback window — undefined in STRATEGY.md.
- Avg-volume filter lookback window (20d? 30d?) — undefined in STRATEGY.md.
- Whether to adopt the confirmation-entry / LEAP-exit-asymmetry ideas once the real backtest can test them.
