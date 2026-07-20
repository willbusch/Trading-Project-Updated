# Latched-Fib Strategy — Full-Universe Run (2026-07-19)

> "Universe run with CURRENT-membership survivorship (names screened by TODAY's market cap, profitability, and liquidity — a name unprofitable or small in 2018 but large-cap-profitable now is included for the whole history) and a 0.55-delta LEAP approximation ignoring theta. Vault tested once. This is the closest available approximation to an edge verdict; live validation still required before real capital."

## REQUIRED VERDICTS (plain language)

Winning cell by **vault** expectancy: **`daily/weekly`**.

1. **Beat SPY buy-and-hold in the vault?** **YES** — winning cell vault return 37.7% vs SPY 18.4%.
2. **Beat SPY with idle-cash-in-SPY variant?** **YES** — variant vault return 42.0% vs SPY 18.4%. (This is the honest bar: it neutralizes cash drag.)
3. **Deployed (not in cash) what % of the run?** Winning cell: **99.6%** of bars in the vault; 72.4% pre-vault.
4. Full stat block per cell/window below. 5. The Gap below. 6. Eligibility stats below.

### ⚠️ READ THIS before trusting the YES above

- **100% win rate in EVERY window of ALL four cells** is the survivorship signature, not skill. This universe is defined by names that are large-cap AND profitable in 2026 — buying any of them 40% down and holding to recovery wins essentially by construction. Every large winner is a Feb–Mar 2020 COVID-crash entry (bought near the dip, fraction 0.00–0.15) in a name we already know recovered.
- **The vault verdict rests on 2 trades** (winning cell). One to three trades per cell in a 12-month vault is not statistically meaningful — treat 'beat SPY' as *suggestive*, not proven.
- **The edge, if any, is real relative to cash drag**: the SPY-idle-cash variant also beat SPY by a similar margin, so the result is not merely lucky cash timing. But it is dominated by one regime (the COVID crash + recovery) and one survivorship-selected name set. Honest verdict: **not proof of edge; the closest approximation available, and it clears the bar — barely, on thin evidence.**

## ⚠️ Cell-set reduction (flagged)

Full 7-cell matrix was impractical at universe scale (~143s per cell × 7 × the double idle-cash runs). Ran the **4-cell reduced set** = the 3 best pre-vault cells from the 12-name round (daily/weekly, 3day/weekly, weekly/weekly) + daily/daily, per the build prompt's authorized fallback.

## Full stat block — every cell, every window

| Cell | Window | Closed | Win | Exp/trade | Total ret | Ret (SPY-idle-cash) | CAGR | MaxDD | Avg hold (d) | Trades/yr | Deploy% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| daily/weekly | combined (pre-vault) | 13 | 100.0% | 47.3% | 152.9% | 167.4% | 13.1% | 40.5% | 586.62 | 1.72 | 72.4% |
| daily/weekly | half-1 (→ 2024-01-01) | 9 | 100.0% | 47.4% | 87.6% | 89.6% | 11.1% | 40.5% | 502.56 | 1.50 | 65.3% |
| daily/weekly | half-2 (2024-01-01 → vault) | 4 | 100.0% | 50.8% | 61.1% | 57.5% | 36.3% | 17.1% | 264.25 | 2.60 | 99.2% |
| daily/weekly | VAULT (last 12mo, tested once) | 2 | 100.0% | 74.7% | 37.7% | 42.0% | 37.8% | 5.8% | 176.50 | 2.00 | 99.6% |
| 3day/weekly | combined (pre-vault) | 11 | 100.0% | 42.9% | 113.4% | 128.0% | 10.6% | 26.0% | 471.45 | 1.46 | 73.1% |
| 3day/weekly | half-1 (→ 2024-01-01) | 7 | 100.0% | 41.7% | 56.5% | 57.6% | 7.8% | 26.0% | 345.57 | 1.17 | 66.2% |
| 3day/weekly | half-2 (2024-01-01 → vault) | 7 | 100.0% | 66.8% | 111.7% | 119.1% | 62.8% | 14.4% | 243.71 | 4.55 | 99.2% |
| 3day/weekly | VAULT (last 12mo, tested once) | 1 | 100.0% | 11.1% | 22.0% | 18.8% | 22.0% | 14.2% | 117.00 | 1.00 | 98.4% |
| weekly/weekly | combined (pre-vault) | 15 | 100.0% | 40.7% | 147.6% | 186.5% | 12.8% | 21.9% | 509.47 | 1.99 | 72.8% |
| weekly/weekly | half-1 (→ 2024-01-01) | 10 | 100.0% | 35.3% | 97.9% | 103.9% | 12.1% | 21.9% | 399.60 | 1.67 | 65.9% |
| weekly/weekly | half-2 (2024-01-01 → vault) | 4 | 100.0% | 92.5% | 68.6% | 84.0% | 40.4% | 19.6% | 250.00 | 2.60 | 95.3% |
| weekly/weekly | VAULT (last 12mo, tested once) | 2 | 100.0% | 28.6% | 15.7% | 23.8% | 15.7% | 11.4% | 70.00 | 2.00 | 99.2% |
| daily/daily | combined (pre-vault) | 20 | 100.0% | 36.6% | 187.7% | 207.8% | 15.0% | 40.5% | 379.10 | 2.65 | 72.4% |
| daily/daily | half-1 (→ 2024-01-01) | 14 | 100.0% | 27.5% | 90.8% | 92.2% | 11.4% | 40.5% | 357.43 | 2.34 | 65.3% |
| daily/daily | half-2 (2024-01-01 → vault) | 6 | 100.0% | 55.9% | 81.3% | 85.0% | 47.2% | 16.9% | 244.17 | 3.90 | 99.2% |
| daily/daily | VAULT (last 12mo, tested once) | 3 | 100.0% | 68.9% | 39.1% | 42.9% | 39.1% | 5.9% | 214.67 | 3.00 | 99.6% |

## Headline — cells sorted by VAULT expectancy

| Cell | Vault closed | Vault exp | Vault ret | Vault ret (SPY-cash) | Pre-vault exp |
|---|---|---|---|---|---|
| daily/weekly | 2 | 74.7% | 37.7% | 42.0% | 47.3% |
| daily/daily | 3 | 68.9% | 39.1% | 42.9% | 36.6% |
| weekly/weekly | 2 | 28.6% | 15.7% | 23.8% | 40.7% |
| 3day/weekly | 1 | 11.1% | 22.0% | 18.8% | 42.9% |

## Benchmarks

| Benchmark | Pre-vault total | Pre-vault CAGR | Vault total | Vault CAGR |
|---|---|---|---|---|
| SPY buy-hold | 45.9% | 9.8% | 18.4% | 18.4% |

Note: buy-hold-same-names is impractical at 200-name universe scale (equal-weighting the whole universe ≈ a beta index), so SPY buy-hold + the SPY-idle-cash variant are the two benchmarks, per the build prompt. The SPY-idle-cash variant is the decisive one.

## Eligibility over time (the universe run's core question)

On the winning cell, names clearing the 40%/25% gate on a given day: **mean 16.0, min 0, max 98**. There was **something eligible to buy on 77% of days** (503/2146 days had zero eligible). So yes — there is almost always *something* 40%-down and quality-screened, but the 5-slot book + 2-per-week pace means only a fraction is ever held (see Deploy%).

## Hybrid-anchor extension frequency (CHANGE 2)

On the winning cell, the extended (~4yr) anchor was used on **14.8% of all name-bars**, and **146 of 200 names** used it at some point — the hybrid anchor is doing real work, not a rare edge case. It replaces the 12-name round's stale-exclusion: young post-IPO names now get their true peak instead of being dropped.

## The Gap (accepted open risk — no exit below 0.5)

Winning cell, pre-vault: **0 gap trades**, total give-back $0. (Trades that peaked above entry, never hit 1.618, never triggered a zone exit, and closed at a loss or gave back >50% of peak gain.)

## Exit-type breakdown (winning cell, all windows)

`{'simple_1618_hard': 5, 'simple_ut_sell': 22, 'leap_modeled_expiry': 1}`

Expired-worthless LEAPs: **N/A** — the 0.55-delta approximation has no strike/theta, so it structurally cannot produce a worthless expiry (a known, flagged limitation). `leap_modeled_expiry` marks LEAPs that reached the 2yr modeled horizon instead.

## Coverage & mechanics

- Universe coverage: **200/200 names loaded (100%)**, daily bars 2018-01 → 2026-07-17.
- Universe source: Robinhood scanner (live, current-market); filters `MARKET_CAP>=10e9 AND NET_PROFIT_MARGIN>0 AND AVG_VOLUME(30d)>1e6`. CURRENT membership + CURRENT fundamentals — survivorship + fundamental-snapshot bias baked across all history. Top 200 of 396 matches by market cap (scanner returns 200 max). NOT point-in-time SPY/QQQ (no membership filter exists in the data source).
- CHANGE 1 (latch dropped): equity exit is the simple version (0.5→1.618 any UT sell → exit; 1.618 hard). Latch code kept for reference, off the active path.
- Forward-only: exit machine, full simulator, AND the new hybrid anchor all pass explicit lookahead tests (truncating future bars leaves earlier anchors/trades unchanged).
