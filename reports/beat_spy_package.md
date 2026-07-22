# Beat-SPY Package — Entry/Sizing/Trailing Comparison

**Run date:** 2026-07-22
**Universe:** 200-name current-snapshot proxy (`data/universe_snapshot.json`)
**Span:** 2018-01-02 → 2026-07-17 · Vault: last 12 months (2025-07-17 → 2026-07-17), tested once

> **This is STILL the survivorship-biased proxy universe with current-snapshot
> market caps. Top-10-by-cap, tiered gates, and reserve modeling all lean on
> point-in-time data we do not truly have. A package that beats SPY here is
> NECESSARY but NOT SUFFICIENT evidence — it tunes the machine; only live
> forward signals prove edge. If the package STILL loses to SPY risk-adjusted,
> that is a decisive and valuable finding, not a failure: it would mean the
> honest answer is to index, proven rather than assumed. Do not let a good
> number end the skepticism.**

## Headline verdict, up front

**No cell in this 12-cell grid beats SPY on both return AND max drawdown.**
Every cell crushes SPY on raw return (127%–1064% vs SPY's 45.9% pre-vault).
**Every cell also has roughly DOUBLE SPY's max drawdown** (44.9%–48.9% vs
SPY's 25.4% pre-vault; 20.3% vs SPY's 9.1% in the vault). Per the rule this
run was scoped under — both required, or it isn't a win — **the package does
not beat SPY risk-adjusted**, even in its best configuration. The enormous
return numbers are real (see trade log), but they are almost entirely three
LEAP trades that happened to land inside TSLA's and META's largest
individual-stock rallies in this dataset's history — see the overfitting
guard below before trusting the ranking table.

---

## Part A — what was built (A1–A8)

| # | Change | Status |
|---|---|---|
| A1 | Sizing: 30% LEAP / 65% across 4 equities (~16.25% each) / 5% cash floor. Position size measured at entry only — a winner growing past its entry size was already never trimmed (no trim logic exists). | ✅ config.yaml |
| A2 | LEAP eligibility: static $500B floor → **top-10-by-market-cap-proxy, RANKED, by entry date**. Proxy: implied shares (`current_cap ÷ current_close`) × historical close. See table below. | ✅ `backtest/leap_topcap.py` |
| A3 | LEAP reserve **REVERSED** from a wall to spendable working capital, held in SPY, mark-to-market. | ✅ `check_leap_reserve` + `reserve_spendable` |
| A4 | Slot-time recycling valve: ≥365d held + underwater + better candidate waiting → force-recycle. Winners never touched. | ✅ `fib_simulator.py` |
| A5 | LEAP exit floor tightens 0.9→0.7 past 50% of modeled runway. No hard time-close. | ✅ `LeapDecayExit` |
| A6 | Kill switch narrowed to LEAP-only; equity dip-buys pass through a halt. | ✅ `check_kill_switch` |
| A7 | 1.618 no longer hard-sells equities — switches to a trailing exit (ut_trail / pct_trail). | ✅ `TrailingFibExit` |
| A8 | Dashboard SPY-curve truncation bug fixed (all curves reindexed to a shared date union before serializing). | ✅ `generate_dashboard_data.py` |

**Bonus fix (found while building A4):** the entry-fill loop iterated
`sorted(pending_entries)` — alphabetical — which silently discarded the
2026-07-21 ratio-based slot tiebreak's rank order. The prior run's
"AMAT beat 4 smaller candidates" result may have been alphabetical luck (A
sorts early), not the ratio rule actually deciding. Fixed; regression test
added (`tests/test_beat_spy_package.py`).

31 new tests added for A2–A8 (ranking, lookahead safety, winner-protection,
peak-tracking lookahead, kill-switch scope, dashboard alignment). Full suite:
**120 passed** before the grid ran.

### A2 — LEAP-eligible names by year (top-10-by-cap-proxy)

| Year | LEAP-eligible tickers |
|---|---|
| 2018 | AAPL, AMZN, BABA, BRK.B, CVX, GOOG, GOOGL, JNJ, JPM, UNH, V, VZ, WMT |
| 2019 | AAPL, AMZN, BABA, BRK.B, GOOG, GOOGL, JNJ, JPM, META, V, WMT |
| 2020 | AAPL, AMZN, BABA, BRK.B, GOOG, GOOGL, JNJ, JPM, META, TSLA, TSM, V, WMT |
| 2021 | AAPL, AMZN, BABA, BRK.B, GOOG, GOOGL, JNJ, JPM, META, MSFT, NVDA, TSLA, TSM, V, WMT |
| 2022 | AAPL, AMZN, BRK.B, GOOG, GOOGL, JNJ, META, MSFT, NVDA, TSLA, TSM, UNH, V, WMT |
| 2023 | AAPL, AMZN, AVGO, BRK.B, GOOG, GOOGL, JNJ, LLY, META, MSFT, NVDA, TSLA, TSM, UNH, V |
| 2024 | AAPL, AMZN, AVGO, BRK.B, GOOG, GOOGL, LLY, META, MSFT, NVDA, TSLA, TSM |
| 2025–26 | AAPL, AMZN, AVGO, BRK.B, GOOG, GOOGL, META, MSFT, NVDA, TSLA, TSM |

(Union of any-day-in-year top-10 membership — the daily top 10 is exactly 10;
this list is wider because rank churns within the year, and GOOG/GOOGL count
as two tickers for one company.)

**MU is never in this list, in any year.** Confirmed excluded — MU's ~$80B
2021 cap never came close to a top-10-by-cap-proxy rank, unlike the flat
$500B-of-TODAY floor that let it in retroactively. The MU LEAP that drove
last round's 62.8% max drawdown and −100% expiry **no longer occurs under
any of the 12 cells or the attribution ladder.** MU appears once, as an
**equity** trade (entry 2022-07-18, exit 2024-04-22, **+73.0%**) — a clean,
unambiguous correction, not a marginal one.

---

## Part B — 12-cell grid, ranked by return ÷ max drawdown

Max drawdown shown on every row per the mandatory rule — **an enormous
return with a still-large drawdown is not a win.**

| Rank | Cell (entry / sizing / trailing) | Ratio | Return | Max DD | CAGR | Deploy | Trades | Win% | Vault trades | Vault exp. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3day / both / trail_ut | 22.1 | 1064.2% | 48.2% | 38.5% | 73.1% | 17 | 64.7% | 1 | 253%¹ |
| 2 | 3day / deepen / trail_pct20 | 20.1 | 949.0% | 47.2% | 36.6% | 73.1% | 13 | 69.2% | 1 | 237%¹ |
| 3 | 3day / both / trail_pct20 | 19.3 | 928.6% | 48.2% | 36.2% | 73.1% | 16 | 62.5% | 1 | 237%¹ |
| 4 | 3day / deepen / trail_ut | 16.2 | 761.8% | 47.2% | 33.1% | 73.1% | 13 | 69.2% | 1 | 253%¹ |
| 5 | daily / diversify / trail_pct20 | 10.0 | 446.9% | 44.9% | 25.3% | 73.2% | 20 | 65.0% | 1 | 254%¹ |
| 6 | daily / diversify / trail_ut | 9.8 | 440.2% | 44.9% | 25.1% | 73.2% | 20 | 65.0% | 2 | 174% |
| 7 | daily / deepen / trail_pct20 | 6.8 | 321.5% | 47.3% | 21.0% | 73.2% | 14 | 64.3% | 1 | 254%¹ |
| 8 | daily / both / trail_pct20 | 6.8 | 331.3% | 48.9% | 21.4% | 73.2% | 17 | 58.8% | 1 | 254%¹ |
| 9 | daily / both / trail_ut | 6.7 | 327.4% | 48.9% | 21.3% | 73.2% | 17 | 58.8% | 1 | 270%¹ |
| 10 | daily / deepen / trail_ut | 6.6 | 317.5% | 47.8% | 20.9% | 73.2% | 14 | 64.3% | 1 | 270%¹ |
| 11 | 3day / diversify / trail_ut | 2.8 | 134.5% | 47.8% | 12.0% | 73.1% | 16 | 50.0% | 1 | 253%¹ |
| 12 | 3day / diversify / trail_pct20 | 2.7 | 127.2% | 47.8% | 11.5% | 73.1% | 16 | 50.0% | 1 | 237%¹ |
| — | **SPY buy-and-hold (pre-vault)** | 1.8 | 45.9% | 25.4% | 9.8% | 100% | — | — | — | — |

¹ Vault "expectancy" is a **single closed trade** (MRVL, +253% or similar,
depending on how much capital the step had compounded into by the vault
window) — see the overfitting guard. It is not a statistically meaningful
number in any cell.

**Vault window, champion cell:** return 34.5%, max DD 20.3%, deployment
98.4%. **SPY vault:** return 18.4%, max DD 9.1%. Same story as pre-vault:
return wins, drawdown loses.

---

## Mandatory overfitting guard — flagged, not silently crowned

This is the widest sweep this project has run (12 cells). Two independent
red flags on the #1 cell, both required to be checked:

**1. Thin margin over 2nd place: 9.7%.** `3day/both/trail_ut` (ratio 22.1)
vs `3day/deepen/trail_pct20` (ratio 20.1) — a margin easily inside the noise
band of a 13–17-trade sample.

**2. Vault divergence.** Every cell's "vault expectancy" is driven by
**exactly one closed trade** (MRVL, entered 2025-08-01, exited 2026-06-29,
+253%) — the SAME trade dominates almost every cell's vault number, because
a single-LEAP-slot, low-frequency strategy on a 12-month held-out window
simply does not generate enough NEW decisions to validate anything. Most of
what shows up as "vault performance" is really the *already-open* pre-vault
book (5–7 open positions, including a live TSLA LEAP) being marked to
market, not new out-of-sample signal quality. **Treat every vault number in
this report as directional at best, not proof.**

**3. Concentration in a tiny number of trades (found during leak-hunting).**
The champion cell's pre-vault trade log has only 17 trades over 6.5 years,
and its return is dominated by exactly **3 LEAP legs**: TSLA (May 2021,
+164%), META (Mar 2022, +449%), TSLA again (Aug 2024, +180%). All three are
genuine, correctly-computed Black-Scholes convexity on two of the single
largest individual-stock rallies in the entire dataset's history — not a
pricing bug — but a strategy whose headline number rests on catching TSLA
twice and META once, with only ONE LEAP slot total, is a fragile,
lucky-timing story, not demonstrated structural edge. **This is exactly what
the guardrail told us to leak-hunt hardest, since A2 (the hindsight-flavored
change) is what unlocked these two names for LEAP sizing.**

**4. Entry-timeframe bimodality is itself evidence against the 3-day
result.** The 3-day timeframe produces BOTH the best 4 cells (ranks 1–4) AND
the worst 2 cells (ranks 11–12) in the entire grid, purely by swapping the
equity-sizing variant. The `daily` timeframe, by contrast, is stable and
consistent (ranks 5–10, a tight band) regardless of which sizing variant is
paired with it. A genuine structural edge from the entry timeframe should
not flip from best-in-grid to worst-in-grid on an unrelated axis — that
pattern is the signature of a couple of large, idiosyncratic trades landing
inside (or missing) the 3-day sampling grid, not a repeatable mechanism.

**Conclusion of the guard:** the raw #1 cell (`3day/both/trail_ut`) is
**not** trustworthy as "the winner." The more defensible pick, on
robustness grounds (higher trade count, stable across both grid dimensions,
comparable max drawdown), is **`daily/diversify`** (ranks 5–6, ratio ≈9.8–10,
20 trades, max DD 44.9%) — still not a risk-adjusted win over SPY, but not
resting on 2–3 coin flips either.

---

## Cumulative attribution — champion cell (`3day/both`), baseline → +A7

| Step | Pre-vault return | Pre-vault max DD | Trades | Recycles | Vault return | Vault max DD |
|---|---:|---:|---:|---:|---:|---:|
| baseline (pre-Part-A structure) | 91.5% | 54.9% | 7 | 0 | 15.3% | 18.9% |
| +A2 (top10-cap LEAP eligibility) | **1042.5%** | **40.1%** | 10 | 0 | 15.3% | 18.9% |
| +A3 (reserve spendable + SPY idle-cash) | 1139.4% | 47.5% | 11 | 0 | 20.9% | 20.3% |
| +A4 (slot recycling valve) | 881.8% | 46.6% | 15 | 5 | 20.9% | 20.3% |
| +A5 (LEAP decay-aware exit) | 881.8% | 46.6% | 15 | 5 | 20.9% | 20.3% |
| +A6 (kill switch LEAP-only) | 1034.5% | 48.2% | 17 | 6 | 20.9% | 20.3% |
| +A7 (trailing exit, full package) | 1064.2% | 48.2% | 17 | 6 | 34.5% | 20.3% |

(Final row matches the grid's champion-cell number exactly — a useful
internal consistency check that the ladder and the grid agree.)

**Reading it:**
- **A2 is overwhelmingly the load-bearing fix** — it is the only step that
  improved BOTH return (91.5%→1042.5%) and risk (54.9%→40.1% max DD)
  simultaneously. Every other step trades one for the other.
- **A3 added return but WORSENED max drawdown** (40.1%→47.5%) — spending
  the reserve on equities adds exposure without a matching risk cut.
- **A4 (recycling) actually REDUCED return** in this specific run (1139.4%→
  881.8%) while only marginally improving max DD — 5 legacy positions
  (MUFG, MMM, LYG, BABA, NEM) were force-recycled, and the replacement
  trades didn't outperform them enough inside this window to offset the
  turnover. A genuine, non-cherry-picked cost/benefit finding, not a free
  lunch.
- **A5 had ZERO measurable effect in this run** — no open LEAP happened to
  cross the 50%-runway threshold while also getting a UT sell signal in the
  tightened 0.7–0.9 zone during this particular backtest. Not proof it's
  useless generally, just inert here.
- **A6 is the clear #2 fix** — unlocked 2 more trades (15→17) and pushed
  return back up (881.8%→1034.5%), confirming the kill-switch-scope
  diagnosis was real, at a small further drawdown cost.
- **A7 added a modest final lift** (1034.5%→1064.2%) with no change to max
  drawdown or trade count, exactly as expected for a mechanic that only
  changes what happens after 1.618 is already touched.

---

## The 7 key questions, answered directly

1. **Does the winning cell beat SPY on BOTH return and max drawdown?**
   **No.** Return: yes, overwhelmingly. Max drawdown: no — every one of the
   12 cells runs 44.9%–48.9% max DD pre-vault, roughly DOUBLE SPY's 25.4%.
   Same pattern in the vault (20.3% vs SPY's 9.1%). Per the rule this run
   was scoped under, that is not a win.

2. **Does deployment rise materially off the 73% baseline?** **No.**
   Deployment held at 73.1–73.2% across literally every cell and every
   attribution step, baseline through +A7. Freeing the LEAP reserve (A3)
   changed WHAT filled the remaining capital, not the FRACTION OF DAYS
   invested — slots were already usually full under the old wall model too.

3. **Do the Oct–Dec 2022 mega-cap entries now actually fire?** **Partially,
   with an important nuance.** NVDA (LEAP, 2022-02-01), META (LEAP,
   2022-03-21), AMD (equity, 2022-05-03), and TSM (LEAP, 2023-05-26) all
   get entries unlocked somewhere in the 12-cell grid that were blocked
   before — but none of them land specifically in the diagnosed Oct–Dec
   2022 window, and **GOOG/GOOGL/AMZN never enter in any of the 12 cells**,
   even though GOOG/GOOGL are LEAP-topcap-eligible the whole time — their
   drawdown+UT-trigger combination simply never aligned in this backtest.
   Reported honestly rather than rounded up to "yes."

4. **Does MU#1 stop being a −100% / 62.8%-DD event?** **Yes, cleanly.**
   MU is never LEAP-eligible under the new top-10-by-cap rule in any year of
   the backtest (confirmed above). It appears exactly once, as an equity
   trade, +73.0%. The specific failure mode that drove the prior round's
   headline drawdown is gone.

5. **Which single fix moved the needle most?** **A2 (top-10-by-cap LEAP
   eligibility)**, by a wide margin — the only step that improved return
   AND risk together. A6 (kill-switch scope) is a clear second. A4
   (recycling) had a real, measurable cost in this run. A5 (decay exit) had
   no measurable effect at all in this particular backtest.

6. **Daily or 3-day entry timeframe — meaningful or noise?** **Noise, most
   likely.** 3-day produces both the best AND worst cells in the entire
   grid depending on sizing variant; daily is stable and mid-pack regardless
   of sizing variant. That instability pattern, combined with the
   concentration finding above (2–3 trades driving the top cells), points to
   idiosyncratic trade-timing luck, not a structural entry-timeframe edge.

7. **Diversify, deepen, or both — real difference or noise?** **Mostly
   noise for `daily`** (all three variants land in a tight 6.6–10.0 ratio
   band); **large but likely spurious for `3day`** (diversify is worst in
   the whole grid, deepen/both are best) — the same concentration effect as
   question 6, not evidence that "deepen" or "both" is a genuinely better
   sizing mechanism.

---

## Bottom line

The Part A package (A1–A8) is a real, substantial improvement over the prior
locked configuration — it fixes the MU-2021 mispricing, adds real dry-powder
flexibility, and unlocks entries the old kill switch and static LEAP floor
were blocking. Every one of the 7 diagnosed problems from the prior round's
post-mortem is measurably better. **But none of that adds up to a
risk-adjusted win over SPY.** Every cell in the 12-cell grid still runs
roughly double SPY's max drawdown, and the raw #1 cell's enormous headline
return is concentrated in 2–3 large, plausibly lucky LEAP trades rather than
broad-based structural edge — exactly the "too good to be true" pattern this
project's own discipline says to distrust. **The honest conclusion is: this
package tunes the machine, it does not prove the machine beats an index
fund on a risk-adjusted basis. Indexing remains the evidence-backed default
until a genuinely out-of-sample (not backtested) track record says
otherwise.**
