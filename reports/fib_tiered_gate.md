# Tiered Drawdown Gate — Reopened Research (2026-07-20)

> "This run REOPENS the formally-closed research phase. The data limitation is unchanged: survivorship-biased proxy universe, no point-in-time membership/fundamentals, and now also a CURRENT-market-cap proxy for the tier assignment itself (a name's tier is fixed at today's cap and applied across its entire backtest history). This run can IMPROVE the strategy; it CANNOT prove edge."

## The mechanical delta

Only the **$150B–$500B band** actually changes: 40% → 30%. $500B+ names were already 25% (auto-LEAP-tier under the old gate); sub-$150B names were already 40%. 73 of the 200 universe names fall in the affected band. Verified directly against the tested module (ORCL: 130→176 eligible days, 8→10 entry candidates under the looser threshold) — the per-ticker mechanism works exactly as specified.

## Watch-for questions — answered

1. **Trade count up vs flat-40%?** Mixed, and counterintuitively **down** on the baseline cell (daily/weekly: 12→9 pre-vault trades). Verified this is NOT a bug — it's a real emergent effect: more names now clear the gate and compete for the same 5-slot/2-per-week throttle, which changes WHICH names get traded, not just how many. Some of the flat-gate's biggest 2020 winners got crowded out by earlier entries into newly-eligible mid-caps under the deepest-drawdown-first tiebreak.
2. **Vault trades > 1?** **Unclear — and this itself is a finding.** Under tiering, 2 of 6 cells (daily/weekly, daily/3day) show 2 vault trades; the other 4 show 1. But when the flat-40% baseline was re-run FRESH in this same session (to make an apples-to-apples comparison), it ALSO produced 2 vault trades on daily/weekly — not the 1 the dashboard showed. The discrepancy traces to universe-snapshot timing: a handful of names (HIMS, SOFI) dropped in/out of the scanned universe between when the dashboard was generated and now, and — per the slot-competition dynamic in question 1 — that alone changes which trades fire. **Vault trade count on this cell is not a stable number; it moves with minor universe composition changes, which is itself evidence the vault sample is too thin to treat as decisive**, consistent with the standing "not statistically meaningful" caveat.
3. **Expectancy trade-off?** Yes, exactly as expected: daily/weekly expectancy dropped 93.9%→58.5% pre-vault (shallower dips = smaller per-trade moves), while trade count also fell rather than rising — the worst combination of the two possible outcomes on this specific cell, though other cells (weekly/weekly: 79.4% exp, 10 trades) did better on both axes.
4. **Deployment % up?** **No, essentially flat** — every tiered cell shows ~76% deployment vs the flat baseline's 72%. The gate loosening did not meaningfully increase time invested.
5. **Trade clustering — did it spread beyond COVID?** **Yes, measurably.** Full-span year-spread now includes real entries in 2021, 2022, 2023, 2024, 2025, and 2026 across the 6 cells — not just 2020. But 2020 still contributes 6–7 of each cell's 12–16 total trades (40–50%), so it remains the single richest year by a wide margin. The tiering worked directionally; it did not eliminate the crash-concentration problem.

## Full matrix (sorted by total return — owner's explicit choice; vault expectancy sits one column over, never hidden)

| Cell | Total Return | Pre-vault Exp | Pre-vault N | Vault Exp | Vault N | Years spread (full span) |
|---|---|---|---|---|---|---|
| weekly/3day | 258.7% | 75.8% | 11 | 23.7% ⚠️ weakest vault of the 6 | 1 | {2020: 7, 2021: 1, 2022: 1, 2023: 1, 2024: 2, 2025: 2} |
| weekly/weekly | 218.6% | 79.4% | 10 | 55.8% | 1 | {2020: 7, 2021: 1, 2022: 1, 2023: 1, 2024: 1, 2025: 4, 2026: 1} |
| daily/3day | 170.1% | 67.7% | 10 | 67.2% | 2 | {2020: 6, 2021: 2, 2022: 1, 2023: 1, 2024: 3, 2025: 1} |
| daily/weekly | 116.6% | 58.5% | 9 | 102.0% | 2 | {2020: 6, 2021: 2, 2023: 2, 2024: 2, 2025: 1} |
| 3day/3day | 110.1% | 57.5% | 10 | 99.1% | 1 | {2020: 6, 2021: 2, 2022: 1, 2023: 1, 2024: 1, 2025: 1} |
| 3day/weekly | 98.7% | 47.3% | 8 | 134.2% | 1 | {2020: 6, 2021: 2, 2023: 1, 2024: 2, 2025: 2, 2026: 1} |

**Read this table left-to-right before trusting the sort:** `weekly/3day` ranks #1 by total return (+259%) but has the weakest vault performance of all 6 cells (n=1, lowest vault expectancy) — exactly the 'one-COVID-trade winner dressed up as the champion' risk this table's second-and-third columns exist to catch. `weekly/weekly` and `weekly/3day` both look strong on total return AND have real trade counts (10-11 pre-vault), which is a more defensible read than the raw sort order alone.

## Tiered vs flat-40% — side by side, winning cell (daily/weekly, 0.9-floor exit)

| | Pre-vault N | Pre-vault Exp | Pre-vault Ret | Deploy% | Vault N | Vault Exp | Vault Ret |
|---|---|---|---|---|---|---|---|
| **Flat 40%/25%** | 12 | 93.9% | 415.8% | 72.4% | 2 | 94.5% | 45.9% |
| **Tiered 25/30/40** | 9 | 58.5% | 116.6% | 73.2% | 2 | 102.0% | 43.7% |

On the flat gate's own former champion cell, tiering LOWERED both trade count (12→9) and total return (415.8%→116.6%), and did NOT change vault trade count (2→2, both runs re-verified fresh this session) — only vault expectancy moved modestly (94.5%→102.0%). **This is a net negative on daily/weekly specifically, not an improvement.** Other cells in the matrix above (weekly/weekly, daily/3day) look more favorable on balance, but none of the 6 delivers an unambiguous win over the flat-gate champion.

## Leak-hunt

Passed. Full-span CAGR ranges 11%–23% across all 6 cells (weekly/weekly highest). No cell approaches the 50% flag threshold. Per-ticker eligibility mechanism verified directly against the tested module, not just trusted from aggregate output.

## Benchmarks (unchanged data span)

SPY buy-hold: pre-vault 45.9%, vault 18.4%.
