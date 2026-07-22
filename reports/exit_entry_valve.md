# Exit/Entry Analysis + Smarter Valve

**Run date:** 2026-07-22
**Source:** the existing 2026-07-22 12-cell grid (Part 1, no new sim) + one
targeted valve test on the champion cell (Part 2). Champion cell =
`3day / both / ut_trail`.

> **This is STILL the survivorship-biased proxy universe with current-snapshot
> market caps, and SPY price history only reaches back to 2021-07. Beating SPY
> here is NECESSARY but NOT SUFFICIENT evidence of edge — the headline returns
> rest on 2–3 large LEAP trades, and vault numbers are directional at best. Do
> not let a good number end the skepticism.**

---

## Part 1 — answers extracted from the existing 12-cell run

### 1a. Trailing mechanic: ut_trail vs pct_trail(20%)

| Mechanic | Avg return | Avg max DD | Avg return÷DD | Pairs won (of 6) |
|---|---:|---:|---:|---:|
| ut_trail | 507.6% | 47.5% | 10.70 | 2 |
| pct_trail(20%) | 517.4% | 47.4% | 10.93 | 4 |

Biggest runners are **identical** across both mechanics in the champion pair
(META LEAP +449%, TSLA LEAP ×2 at +180%/+164%). The two large pairwise swings
(3day/deepen: pct +187% ahead; 3day/both: ut +136% ahead) are the same 2–3
LEAP trades landing on slightly different exit bars, not a mechanic effect.

**Verdict: the trailing mechanic is essentially a wash — pct_trail is
marginally ahead on average, ut_trail won only 2 of 6 head-to-head pairs.**
The champion cell's ut_trail win is one of those two lucky cells, **not a real
edge**. Confidence: high that the difference is noise.

### 1b. Entry timeframe: daily vs 3-day

| Timeframe | Avg return | Avg max DD | Avg return÷DD | Avg trades | Avg win rate |
|---|---:|---:|---:|---:|---:|
| daily | 364.1% | 47.1% | 7.78 | 17.0 | 62.7% |
| 3-day | 660.9% | 47.7% | 13.85 | 15.2 | 60.9% |

But the pairwise breakdown shows the 3-day "win" is **an interaction with
sizing, not a standalone edge**: with `diversify` sizing, **daily** wins by
~300%; with `deepen`/`both` sizing, **3-day** wins by 400–700%. Trade counts
(17 vs 15) and win rates (63% vs 61%) are near-identical.

**Verdict: no genuine standalone timeframe edge.** 3-day only looks better
because it happens to pair with the two sizing modes that caught the big LEAP
trades. Confidence: medium-high that this is a pairing artifact, not a
timeframe property.

### 1c. The 0.5–0.9 dead zone ("what if a stock only goes to 0.5?")

Definition used: a trade whose fib fraction entered [0.5, 0.9) and spent ≥126
trading days (~6 months) there cumulatively **without ever closing ≥0.9**,
measured over its actual hold window.

- **Champion cell: ZERO** such trades.
- **Pooled across all 12 cells: 6 of 215 equity trade-instances (3%)** stalled
  in the dead zone.

**Verdict: the no-man's-land is a real theoretical risk but empirically rare
in this data (3%), and does not occur at all in the winning configuration.**
Because the champion cell had none, the hypothetical "0.5–0.9 zone exit after
12 months stalled" would have changed nothing in the winner. Diagnostic only —
no exit rule was changed. (Caveat: small, curated sample; on a broader or
less survivorship-clean universe this could bind more often.)

---

## Part 2 — underperformance-triggered valve (one targeted test)

**The change:** replace the recycling valve's trigger. Old: held ≥12mo AND
underwater AND better candidate waiting. New: held ≥12mo AND **trailing SPY by
≥5% annualized over the position's own hold window** AND better candidate
waiting. Winners that BEAT SPY are never touched. Everything else identical.
LEAP is never touched.

**Three-way test, champion cell (3day/both/ut_trail), pre-vault selection window:**

| Variant | Return | Max DD | Return÷DD | Recycles | Trades | Win rate |
|---|---:|---:|---:|---:|---:|---:|
| No valve | 1040.6% | 47.5% | 21.91 | 0 | 9 | 100% |
| Underwater (old) | 1064.2% | 48.2% | 22.07 | 6 | 17 | 64.7% |
| **Underperformance (new)** | **1221.0%** | **47.2%** | **25.89** | 3 | 13 | 84.6% |

**What each valve recycled:**

- **Underwater** freed only small losers — MUFG (−4.6%), MMM (−3.8%), LYG
  (−1.7%), BABA (−11.7%), NEM (−27%). It never touches a winner, so the
  mediocre winners that were the actual slot-blockers stayed put.
- **Underperformance** freed the right targets — **RCL** (−55.3% vs SPY −9.2%),
  **NEM** (−10.3% vs SPY +29.0%), and crucially **VZ** (+2.5% but trailing SPY
  +12.3%) — a *mediocre winner* the underwater trigger structurally cannot see.

### The two findings that override the headline number

**1. It does NOT capture the Oct–Dec 2022 mega-caps — the exact failure it was
built for.** In all three variants, META enters as a **LEAP** on 2022-03-21;
GOOG/GOOGL/AMZN/NVDA **never enter** in the Oct–Dec 2022 window (or at all as
equities). Root cause: those names are top-10-by-cap **LEAP-eligible**, so when
they clear the gate they contend for the **single LEAP slot** — which was
already occupied by the 2022 META LEAP riding its ~2-year hold. The recycling
valve only frees **equity** slots and explicitly never touches the LEAP, so it
**structurally cannot admit them.** The owner's named failure is LEAP-slot
contention, not equity-slot contention; this valve does not address it.

**2. SPY data coverage compromises the test.** Cached SPY history starts
**2021-07-01**. The underperformance trigger needs SPY's price at each
position's entry date, so it is **blind to every position entered before
mid-2021** — including the 2020-vintage holds (UBS, SCHW) the owner
specifically complained about. Its comparison to the underwater trigger (which
uses no SPY and sees the full history) is therefore **not apples-to-apples**,
and its win is on partial coverage.

### Honest verdict

The underperformance trigger is **better-targeted in principle** (it recycles
lagging mediocre winners, which the underwater trigger cannot) and it improved
this one cell on every headline metric. **But** it does not solve the specific
problem it was built for, its evaluation is compromised by SPY data coverage,
and — as with every result in this project — the returns still rest on 2–3
large LEAP trades and one cell. **Recommendation: mark PENDING OWNER ADOPTION,
not promoted.** Two things would have to be resolved first: (a) extend SPY
history back to the full backtest span so the trigger can actually evaluate
2020-vintage holds, and (b) recognise that fixing the 2022 mega-cap capture
requires a change to **LEAP-slot** handling (e.g. more than one LEAP slot, or a
LEAP-slot valve), which is out of scope for this equity-only mechanic and was
not tested.

---

## Definition-of-done check

1. ✅ 1a/1b/1c answered with numbers + plain verdicts + confidence reads.
2. ✅ Three-way valve test run and reported honestly, including that the 2022
   mega-caps do NOT fire and exactly what got recycled.
3. ✅ Dashboard rebuilt: strategy cards, essential stats, Notes & Takeaways,
   winner crowned, archive collapsed, caveats prominent
   (`reports/results_dashboard.html`).
4. ⏸️ STRATEGY.md: the valve test's winner is marked **pending owner
   adoption**, not auto-promoted (see the override log entry).
5. ✅ HANDOFF.md updated.
