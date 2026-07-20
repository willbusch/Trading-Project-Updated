# Latched-Fib Strategy — 12-Name Sample, Timeframe Matrix (2026-07-19)

> "12-name curated sample — survivorship bias, mechanics validation, NOT
> edge. LEAP P&L uses a 0.55-delta approximation ignoring theta —
> optimistic. HOOD/SOFI stale-anchor entries excluded from headline.
> Absolute edge requires the full SPY/QQQ universe run."

## Headline verdict

- **Best cell by pre-vault expectancy: `daily/weekly` (daily UT entry / weekly UT exit).**
- **Does it beat buy-and-hold-same-names? NO.** In the 12-month vault the best cell took **0 trades** (sat in cash, −5%) while equal-weight buy-hold of the same 12 names returned **+65.0%**. Pre-vault the strategy's CAGR (18%) also trails the same-names benchmark (29.7%).
- **Does latched beat simple? NO.** On this sample they are identical (same 8 trades, same +191% total, same 27% maxDD) — the latch never armed-and-saved a single trade. Its only observable effect was reclassifying one trade in The Gap. The zones look like complexity, not edge, in this sample.
- **Leak-hunt (mandatory, per >50%-CAGR rule): PASSED.** No cell exceeds 18% CAGR. The high per-trade expectancy (~99% on the best cell) comes from long holds (avg 413 days) of deeply-corrected names that recovered — i.e. survivorship, not lookahead. Every entry fraction is low (0.01–0.51 = buying near the dip). Both the exit state machine and the full simulator pass explicit forward-only lookahead tests (truncating future bars leaves already-closed trades unchanged).

## Full matrix — every cell, every window

Sorted within each window is not applied; headline sort is by **vault** then pre-vault expectancy below.

| Cell | Window | Closed | Win | Exp/trade | Total ret | CAGR | MaxDD | Rejected | StaleExcl |
|---|---|---|---|---|---|---|---|---|---|
| weekly/weekly | combined (pre-vault) | 6 | 100.0% | 76.5% | 115.9% | 12.5% | 12.6% | 11 | 4 |
| weekly/weekly | half-1 (→ 2024-01-01) | 0 | — | — | 33.7% | 6.0% | 12.6% | 10 | 2 |
| weekly/weekly | half-2 (2024-01-01 → vault) | 1 | 100.0% | 19.8% | 24.5% | 15.3% | 6.4% | 1 | 2 |
| weekly/weekly | VAULT (last 12mo, tested once) | 0 | — | — | 5.2% | 5.2% | 12.0% | 2 | 0 |
| weekly/3day | combined (pre-vault) | 7 | 100.0% | 69.2% | 114.2% | 12.4% | 12.6% | 11 | 4 |
| weekly/3day | half-1 (→ 2024-01-01) | 1 | 100.0% | 31.4% | 31.0% | 5.6% | 12.6% | 10 | 2 |
| weekly/3day | half-2 (2024-01-01 → vault) | 2 | 100.0% | 39.8% | 26.9% | 16.7% | 5.4% | 1 | 2 |
| weekly/3day | VAULT (last 12mo, tested once) | 0 | — | — | 5.2% | 5.2% | 12.0% | 2 | 0 |
| 3day/3day | combined (pre-vault) | 8 | 100.0% | 67.4% | 121.8% | 13.0% | 13.5% | 14 | 5 |
| 3day/3day | half-1 (→ 2024-01-01) | 2 | 100.0% | 40.4% | 40.9% | 7.1% | 13.5% | 14 | 2 |
| 3day/3day | half-2 (2024-01-01 → vault) | 2 | 100.0% | 50.3% | 22.1% | 13.9% | 7.1% | 0 | 3 |
| 3day/3day | VAULT (last 12mo, tested once) | 0 | — | — | -0.9% | -0.9% | 18.9% | 5 | 0 |
| 3day/weekly | combined (pre-vault) | 7 | 100.0% | 79.4% | 132.2% | 13.7% | 13.5% | 14 | 5 |
| 3day/weekly | half-1 (→ 2024-01-01) | 1 | 100.0% | 45.0% | 44.1% | 7.6% | 13.5% | 14 | 2 |
| 3day/weekly | half-2 (2024-01-01 → vault) | 1 | 100.0% | 37.4% | 19.6% | 12.3% | 7.1% | 0 | 3 |
| 3day/weekly | VAULT (last 12mo, tested once) | 0 | — | — | -0.9% | -0.9% | 18.9% | 5 | 0 |
| daily/daily | combined (pre-vault) | 9 | 100.0% | 67.9% | 147.6% | 14.9% | 25.9% | 68 | 15 |
| daily/daily | half-1 (→ 2024-01-01) | 4 | 100.0% | 41.7% | 32.2% | 5.8% | 16.1% | 66 | 4 |
| daily/daily | half-2 (2024-01-01 → vault) | 3 | 100.0% | 48.1% | 24.9% | 15.5% | 22.2% | 2 | 14 |
| daily/daily | VAULT (last 12mo, tested once) | 1 | 100.0% | 25.6% | -3.5% | -3.6% | 19.8% | 6 | 0 |
| daily/3day | combined (pre-vault) | 8 | 100.0% | 76.0% | 152.3% | 15.2% | 28.2% | 68 | 15 |
| daily/3day | half-1 (→ 2024-01-01) | 2 | 100.0% | 38.0% | 35.8% | 6.3% | 16.4% | 66 | 4 |
| daily/3day | half-2 (2024-01-01 → vault) | 2 | 100.0% | 41.2% | 19.9% | 12.5% | 26.0% | 2 | 14 |
| daily/3day | VAULT (last 12mo, tested once) | 0 | — | — | -5.2% | -5.2% | 25.1% | 11 | 0 |
| daily/weekly | combined (pre-vault) | 8 | 100.0% | 98.6% | 190.9% | 17.7% | 26.8% | 59 | 1 |
| daily/weekly | half-1 (→ 2024-01-01) | 2 | 100.0% | 43.3% | 40.1% | 7.0% | 18.7% | 57 | 1 |
| daily/weekly | half-2 (2024-01-01 → vault) | 1 | 100.0% | 33.8% | 17.2% | 10.9% | 26.8% | 2 | 14 |
| daily/weekly | VAULT (last 12mo, tested once) | 0 | — | — | -5.2% | -5.2% | 25.1% | 11 | 0 |

## Headline: cells sorted by VAULT expectancy

| Cell | Vault closed | Vault exp | Vault totret | Pre-vault exp |
|---|---|---|---|---|
| daily/daily | 1 | 25.6% | -3.5% | 67.9% |
| weekly/weekly | 0 | — | 5.2% | 76.5% |
| weekly/3day | 0 | — | 5.2% | 69.2% |
| 3day/3day | 0 | — | -0.9% | 67.4% |
| 3day/weekly | 0 | — | -0.9% | 79.4% |
| daily/3day | 0 | — | -5.2% | 76.0% |
| daily/weekly | 0 | — | -5.2% | 98.6% |

**Every cell took 0–1 trades in the 12-month vault** — the drawdown gate simply did not clear + trigger for most names in the last year (they were near highs, not 40% corrected). The strategy is structurally a rare-event dip-buyer; a 12-month vault is too short to contain a meaningful number of its signals. This is a sample-size limitation, not necessarily a failure of edge — but on the evidence available it sat in cash while the names rose.

## Benchmarks

| Benchmark | Pre-vault total | Pre-vault CAGR | Pre-vault maxDD | Vault total | Vault CAGR |
|---|---|---|---|---|---|
| SPY buy-hold | 45.9% | 9.8% | 25.4% | 18.4% | 18.4% |
| **Equal-weight same-12 ⭐** | 183.3% | 29.7% | 54.5% | 65.0% | 65.5% |

⭐ The decisive benchmark. The strategy must beat equal-weight-same-names in the vault to be worth running; it does not (0 trades vs +65%).

## Ablation — latched vs simple (best cell, pre-vault)

| Variant | Closed | Win | Exp | Total ret | MaxDD | Gap trades |
|---|---|---|---|---|---|---|
| latched | 8 | 100.0% | 98.6% | 190.9% | 26.8% | 0 |
| simple | 8 | 100.0% | 98.6% | 190.9% | 26.8% | 1 |

**Verdict: latched does NOT beat simple.** Identical trade set and returns; the latch never armed-then-saved a trade in this sample. Recommend treating the latch as unvalidated complexity until a larger sample shows it protecting a real trade.

## The Gap (accepted open risk — no exit below 0.5)

Best cell, pre-vault: **0 gap trades**, total give-back $0. With a 100%-win-rate survivorship sample, no held name fell into the sub-0.5 no-exit trap during the test — so The Gap risk is real by design but did not materialize on these curated names. Expect it to bite on the full universe, where losers exist.

## Stale-anchor both-ways diagnostic (HOOD + SOFI, best cell, pre-vault)

| Variant | Closed | Stale excluded | Win | Exp | Total ret |
|---|---|---|---|---|---|
| excluded | 1 | 0 | 100.0% | 311.2% | 61.6% |
| included | 1 | 0 | 100.0% | 311.2% | 61.6% |

On the winning **daily/weekly** cell the two are identical: the stale-flagged HOOD/SOFI dates never coincided with a daily UT-buy, so no stale entry was ever a candidate on this cell (0 excluded). The big HOOD +311% winner was a CLEAN, non-stale 2023-08-01 entry. Stale exclusion (Option 1) is wired and active — it simply had nothing to exclude on the headline cell. It does bite on 3-day-entry cells where HOOD/SOFI's stale dates align with 3-day UT buys (see the per-cell StaleExcl column).

## Mechanics notes

- Execution: daily clock. Higher-timeframe UT signals placed on the daily bar equal to the bar's last trading day; filled next daily open, 0.1% slippage. Entry anchors (2yr high, dip-low) frozen at the signal bar's close — no fill-bar leak.
- LEAP path: MSFT/META/NVDA/NFLX/TSLA ($500B+), 25% gate, simple-Fib exit, 0.55-delta approx (ignores theta — optimistic), single LEAP slot, modeled 2yr expiry exit. **Expired-worthless LEAPs cannot be modeled by the delta-approx** (no strike/theta) — reported as N/A, a known limitation; exit breakdown shows `leap_ut_sell`/`leap_modeled_expiry` instead. Held MSFT Dec-2027 LEAP (~1.4yr) is below the new 1.75yr entry floor — flagged, would not be a fresh entry.
- Slot tiebreak (was unset; now defined): when >5 equities qualify same-day → deepest drawdown first, then earliest gate-clear, then alphabetical.
- Short histories (HIMS/HOOD/SOFI from 2021): the 504-day anchor is NaN until 2yr of data exists, so no entry can fire before then — handled explicitly, not padded.
- SMA(200): absent from all logic (owner override). Universe flag for the full SPY/QQQ run: designed, not built — see docs/PLAN.md.
