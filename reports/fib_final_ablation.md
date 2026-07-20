# Final Structural Ablation — Exit 3-Way + Deployment Throttle (2026-07-20)

> "Curated-universe backtest, current-membership survivorship proxy, 0.55-delta LEAP approximation, vault tested once, selection made on pre-vault metrics only (never the vault) to avoid re-peeking the held-out window across five candidate variants. This closes the research phase — see docs/PLAN.md. Not proof of edge."

## Verdict: winning equity exit = **`simple_09`**

Selected on **pre-vault** expectancy only (vault reported below for transparency, never used to pick). Both the old 0.5-floor champion and the new full-latch design (`latch_v2`) LOSE to a plain 0.9 floor with no latch at all — simplicity keeps winning across every ablation round run so far in this project.

| Variant | Pre-vault expectancy |
|---|---|
| simple_05 | 45.8% |
| simple_09 | 93.9% ⭐ WINNER |
| latch_v2 | 82.4% |

## Full stat block — exit variants, every window

| Variant | Window | Closed | Win | Exp/trade | Total ret | Ret (SPY-cash) | CAGR | MaxDD |
|---|---|---|---|---|---|---|---|---|
| simple_05 | combined (pre-vault) | 13 | 92.3% | 45.8% | 142.0% | 159.4% | 12.4% | 40.5% |
| simple_05 | half-1 (→ 2024-01-01) | 9 | 88.9% | 43.2% | 74.3% | 79.0% | 9.7% | 40.5% |
| simple_05 | half-2 (2024-01-01 → vault) | 4 | 100.0% | 50.8% | 61.1% | 57.5% | 36.3% | 17.1% |
| simple_05 | VAULT (last 12mo, tested once) | 2 | 100.0% | 94.5% | 45.9% | 49.0% | 46.0% | 6.5% |
| simple_09 | combined (pre-vault) | 12 | 91.7% | 93.9% | 415.8% | 449.3% | 24.3% | 40.5% |
| simple_09 | half-1 (→ 2024-01-01) | 5 | 80.0% | 67.8% | 90.7% | 99.2% | 11.4% | 40.5% |
| simple_09 | half-2 (2024-01-01 → vault) | 1 | 100.0% | 139.4% | 64.2% | 71.6% | 38.0% | 18.2% |
| simple_09 | VAULT (last 12mo, tested once) | 2 | 100.0% | 94.5% | 45.9% | 49.0% | 46.0% | 6.5% |
| latch_v2 | combined (pre-vault) | 14 | 92.9% | 82.4% | 271.2% | 302.4% | 19.0% | 40.5% |
| latch_v2 | half-1 (→ 2024-01-01) | 7 | 85.7% | 58.0% | 110.1% | 118.7% | 13.2% | 40.5% |
| latch_v2 | half-2 (2024-01-01 → vault) | 2 | 100.0% | 104.4% | 60.9% | 68.2% | 36.2% | 17.3% |
| latch_v2 | VAULT (last 12mo, tested once) | 2 | 100.0% | 94.5% | 45.9% | 49.0% | 46.0% | 6.5% |

## The Gap per variant (pre-vault) — quantifying what each floor costs vs catches

| Variant | Gap trades | Total give-back |
|---|---|---|
| simple_05 | 0 | $0 |
| simple_09 | 0 | $0 |
| latch_v2 | 3 | $77,064 |

The 0.5 and 0.9 simple floors show **zero** gap trades in this sample — every trade either hit 1.618 or exited cleanly on a UT sell above its floor. `latch_v2` shows **3 gap trades totaling $77,064 given back** — its extra travel-zone latches (0.5-0.9 and 1.1-1.5) let winners round-trip further before the latch actually fires than a plain floor would allow. This is the concrete price of the latch complexity the owner asked to quantify, and it's a real cost, not a rounding error.

## Exit-type breakdown per variant (all windows)

- `simple_05`: `{'fib_1618_hard': 4, 'simple_05_ut_sell': 17, 'leap_ut_sell': 5, 'leap_modeled_expiry': 2}`
- `simple_09`: `{'fib_1618_hard': 6, 'leap_ut_sell': 4, 'simple_09_ut_sell': 8, 'leap_modeled_expiry': 2}`
- `latch_v2`: `{'fib_1618_hard': 7, 'leap_ut_sell': 3, 'latch_v2_09_11_ut_sell': 4, 'latch_v2_09_trigger': 8, 'leap_modeled_expiry': 2, 'latch_v2_touched15_ut_sell': 1}`

## Deployment throttle ablation

| Config | Window | Closed | Total ret | Deploy% (binary: any position open) |
|---|---|---|---|---|
| baseline (5 slots / 2 per wk) | combined (pre-vault) | 12 | 415.8% | 72.4% |
| baseline (5 slots / 2 per wk) | half-1 (→ 2024-01-01) | 5 | 90.7% | 65.3% |
| baseline (5 slots / 2 per wk) | half-2 (2024-01-01 → vault) | 1 | 64.2% | 99.2% |
| baseline (5 slots / 2 per wk) | VAULT (last 12mo, tested once) | 2 | 45.9% | 99.6% |
| loosened (6 slots / 3 per wk) | combined (pre-vault) | 11 | 214.9% | 72.4% |
| loosened (6 slots / 3 per wk) | half-1 (→ 2024-01-01) | 5 | 136.7% | 65.3% |
| loosened (6 slots / 3 per wk) | half-2 (2024-01-01 → vault) | 1 | 82.7% | 99.2% |
| loosened (6 slots / 3 per wk) | VAULT (last 12mo, tested once) | 2 | 41.2% | 99.6% |

**Verdict: loosening did NOT help.** Pre-vault total return dropped from +416% to +215% with the loosened throttle — more slots let in lower-priority names (per the deepest-drawdown tiebreak) that diluted returns rather than adding uncorrelated upside. Recommend **keeping the current 5-slot / 2-per-week configuration**. Caveat: `deploy%` here is a BINARY "was any position open" metric, not dollar-weighted utilization — it shows identically in both configs and does not fully capture whether looser slots increased capital actually deployed; a follow-up metric would be needed to fully settle the idle-capital question.

## Benchmarks (winning exit variant, baseline throttle)

- SPY buy-hold: pre-vault 45.9% (CAGR 9.8%), vault 18.4%