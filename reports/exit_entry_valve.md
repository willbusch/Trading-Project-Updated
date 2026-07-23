# Exit/Entry Analysis + Smarter Valve

**Run date:** 2026-07-22 (Part 2 CORRECTED 2026-07-22b after a SPY-data fix)
**Source:** the existing 2026-07-22 12-cell grid (Part 1, no new sim) + one
targeted valve test on the champion cell (Part 2). Champion cell =
`3day / both / ut_trail`.

> **🔴 CORRECTION (2026-07-22b): the first Part 2 run used SPY price history
> that only reached back to 2021-07, which made the underperformance valve
> BLIND to every position entered before mid-2021. SPY history has since been
> extended back to 2018 (data fix), and Part 2 was re-run. The conclusion
> REVERSED: the underperformance valve went from apparent winner to WORST of
> the three. The corrected numbers are below; the original (broken-data)
> numbers are struck through where they appeared. This is exactly why the
> data fix was flagged as necessary before trusting the result.**

> **This is STILL the survivorship-biased proxy universe with current-snapshot
> market caps. Beating SPY here is NECESSARY but NOT SUFFICIENT evidence of
> edge — 87% of the winner's gains come from just 2 LEAP trades (one TSLA LEAP
> alone = 60%); strip those and the strategy returns ~13%/yr (SPY-like) at
> ~1.5× SPY's drawdown. Vault numbers are directional at best. Do not let a
> good number end the skepticism.**

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

**Three-way test, champion cell (3day/both/ut_trail), pre-vault window — CORRECTED
(SPY history extended to 2018; idle cash now earns SPY from 2018, and the
underperformance valve can finally see pre-2021 holds):**

| Variant | Return | Max DD | Return÷DD | Sharpe | Calmar | Recycles | Trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| **No valve** | **1434.4%** | **47.8%** | **30.01** | 1.03 | 0.91 | 0 | 9 |
| Underwater | 1448.0% | 48.3% | 30.00 | 1.07 | 0.91 | 6 | 17 |
| Underperformance | 1237.0% | 48.3% | 25.60 | 1.01 | 0.85 | 8 | 18 |

*(Original broken-data numbers, for the record: no-valve 1040.6%/21.91,
underwater 1064.2%/22.07, underperformance 1221.0%/**25.89 — apparent winner**.
Those are superseded.)*

**The result reversed.** On corrected data the **underperformance valve is the
WORST of the three** (return÷DD 25.60 vs ~30.0). No-valve and underwater are a
statistical tie at the top; no-valve wins by a hair with the lowest max
drawdown. **Recycling does not earn its keep** — turning it on (either trigger)
does not beat leaving it off.

**Why the underperformance valve got worse once it could see everything:** with
SPY back to 2018 it recycled 8 positions instead of 3, and several were fine
holdings it evicted for lagging SPY — **UBS (+22.6% vs SPY +31.1%)** and **MMM
(+20.7% vs SPY +28.8%)** — whose replacements then did worse (**WDC −31.6%**,
**RCL −55.3%**). "Trailing SPY for a year" is a **bad eviction signal**: quality
names routinely lag the index for a stretch and then recover, so forcing them
out at the lag locks in the underperformance and pays for churn.

### The finding that survives the correction

**Neither valve captures the Oct–Dec 2022 mega-caps — the exact failure this
work was meant to fix.** In all three variants META enters as a **LEAP**
(2022-03-21); GOOG/GOOGL/AMZN/NVDA never enter. Those names are top-10-by-cap
**LEAP-eligible**, so they contend for the **single LEAP slot** (occupied by the
2022 META LEAP), not equity slots. The valve only frees **equity** slots and
never touches the LEAP, so it **structurally cannot admit them.** The owner's
named failure is LEAP-slot contention; no equity-slot valve can address it.

### Honest verdict

**Do NOT adopt the underperformance valve.** Corrected for the SPY-data bug it
is the worst of the three, because "lagging SPY" evicts good-enough holdings
that recover. Recycling in general adds nothing here (no-valve ties underwater).
The one thing the owner actually wanted — catching the 2022 mega-cap dips — is a
**LEAP-slot** problem (needs more LEAP slots or a LEAP-slot valve), untested and
out of scope for an equity-only mechanic. The config default stays "underwater"
in name but the practical recommendation is **run no valve**; the code for both
triggers remains available and tested.

**Methodological note (the real lesson):** the first Part 2 run "found" a winner
that was an artifact of the benchmark data starting too late. The fix (extend
SPY to 2018) flipped the conclusion. Every SPY comparison in the whole project
prior to this fix was measured over 2021-07+ only — now corrected.

---

## Definition-of-done check

1. ✅ 1a/1b/1c answered with numbers + plain verdicts + confidence reads.
2. ✅ Three-way valve test run and reported honestly, including that the 2022
   mega-caps do NOT fire and exactly what got recycled.
3. ✅ Dashboard rebuilt: strategy cards, essential stats, Notes & Takeaways,
   winner crowned, archive collapsed, caveats prominent
   (`reports/results_dashboard.html`).
4. ✅ STRATEGY.md: after the data-fix correction, the underperformance valve
   is logged as **tested and NOT adopted** (it's the worst of the three on
   corrected data); no active rule changed. See the override log.
5. ✅ HANDOFF.md updated.

---

## Financial-analyst read (2026-07-22b, full corrected window 2018–2025)

| | CAGR | Max DD | Sharpe | Sortino | Calmar |
|---|---:|---:|---:|---:|---:|
| Strategy (no valve) | 43.7% | 47.8% | 1.03 | 1.50 | 0.91 |
| SPY (now full window) | 11.9% | 34.1% | 0.47 | 0.57 | 0.35 |

**Does it beat SPY?** On risk-adjusted ratios (Sharpe/Sortino/Calmar) — yes,
even over the corrected full window. On absolute drawdown — no (48% vs 34%,
~1.4×). **But the ratios are not trustworthy:** the strategy made 9 closed
trades and **87% of gains come from 2 LEAP trades** (one TSLA LEAP = 60%). LEAP
trades are **94% of net P&L**. Strip the top 2 and the strategy returns ~161%
total over 7.5 years (~13%/yr) — **SPY-like, at ~1.5× the drawdown.** A 43% CAGR
is the signature of leverage + luck on a handful of trades, not a repeatable
edge. **Verdict: a well-built machine expressing a legitimate thesis, but this
backtest proves "two leveraged mega-cap bets worked," not "the strategy has
edge." The only real test left is forward (paper/small-live), not more
backtesting.**
