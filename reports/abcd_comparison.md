# A/B/C/D Strategy Comparison — Engine-Validation Pass (2026-07-19)

> **ENGINE-VALIDATION PASS — NOT PROOF OF EDGE.** This backtest runs only
> on 7 names the owner currently holds. Those names were picked (and are
> still held) partly BECAUSE they went up — that is survivorship bias, by
> design, and it inflates every number below. Results here validate that
> the engine's mechanics (signals, sizing, constraints, cash rule) behave
> correctly. They do NOT establish that any strategy has an edge. No
> threshold may be changed, no capital deployed, and no strategy declared
> a winner on the basis of these numbers alone.

## Window: combined (pre-vault)

| Strategy | Closed | Win rate | Expectancy | Profit factor | Total return | CAGR | Max DD | Avg invested | Rejected | LEAP pricing |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 9 (+3 open) | 55.6% | 26.7% | 3.34 | 32.7% | 6.5% | 28.0% | 30.4% | 1 | MSFT: leap_delta_approx (static delta 0.55) |
| B | 19 (+0 open) | 73.7% | 32.4% | 5.49 | 128.7% | 20.2% | 14.2% | 40.2% | 3 | MSFT: leap_delta_approx (static delta 0.55) |
| C | 0 (+0 open) | — | — | — | 0.0% | 0.0% | 0.0% | 0.0% | 0 | MSFT: leap_delta_approx (static delta 0.55) |
| D | 8 (+2 open) | 62.5% | 34.4% | 4.18 | 40.0% | 7.8% | 20.1% | 29.2% | 0 | MSFT: leap_delta_approx (static delta 0.55) |

**C arm stats:** 0 fired (avg arm→trigger — days), 18 armed-then-expired unfired (avg forgone return 3.1% over the armed window).

**D arm stats:** 13 fired (avg arm→trigger 51.08 days), 12 armed-then-expired unfired (avg forgone return 15.3% over the armed window).

## Window: half 1 (2021-07-19 → 2024-01-01)

| Strategy | Closed | Win rate | Expectancy | Profit factor | Total return | CAGR | Max DD | Avg invested | Rejected | LEAP pricing |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 5 (+3 open) | 20.0% | -8.3% | 0.54 | 14.2% | 5.6% | 28.0% | 42.6% | 0 | MSFT: leap_delta_approx (static delta 0.55) |
| B | 5 (+5 open) | 60.0% | 17.8% | 2.43 | 30.9% | 11.7% | 13.4% | 33.9% | 1 | MSFT: leap_delta_approx (static delta 0.55) |
| C | 0 (+0 open) | — | — | — | 0.0% | 0.0% | 0.0% | 0.0% | 0 | MSFT: leap_delta_approx (static delta 0.55) |
| D | 6 (+2 open) | 50.0% | 19.3% | 2.05 | 30.5% | 11.5% | 20.1% | 45.8% | 0 | MSFT: leap_delta_approx (static delta 0.55) |

**C arm stats:** 0 fired (avg arm→trigger — days), 15 armed-then-expired unfired (avg forgone return 0.8% over the armed window).

**D arm stats:** 11 fired (avg arm→trigger 56.09 days), 9 armed-then-expired unfired (avg forgone return 15.4% over the armed window).

## Window: half 2 (2024-01-01 → 2026-01-17)

| Strategy | Closed | Win rate | Expectancy | Profit factor | Total return | CAGR | Max DD | Avg invested | Rejected | LEAP pricing |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 1 (+3 open) | 100.0% | 0.7% | inf | -1.9% | -0.9% | 5.5% | 6.6% | 1 | MSFT: leap_delta_approx (static delta 0.55) |
| B | 10 (+0 open) | 80.0% | 40.0% | 5.70 | 68.3% | 29.1% | 14.2% | 31.9% | 1 | MSFT: leap_delta_approx (static delta 0.55) |
| C | 0 (+0 open) | — | — | — | 0.0% | 0.0% | 0.0% | 0.0% | 0 | MSFT: leap_delta_approx (static delta 0.55) |
| D | 0 (+2 open) | — | — | — | -1.7% | -0.8% | 2.5% | 1.1% | 0 | MSFT: leap_delta_approx (static delta 0.55) |

**C arm stats:** 0 fired (avg arm→trigger — days), 3 armed-then-expired unfired (avg forgone return 14.9% over the armed window).

**D arm stats:** 2 fired (avg arm→trigger 23.50 days), 3 armed-then-expired unfired (avg forgone return 14.9% over the armed window).

## Window: VAULT (final 6mo, tested once)

| Strategy | Closed | Win rate | Expectancy | Profit factor | Total return | CAGR | Max DD | Avg invested | Rejected | LEAP pricing |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 3 (+3 open) | 66.7% | 0.3% | 0.88 | 5.9% | 12.5% | 13.5% | 58.1% | 2 | MSFT: leap_delta_approx (static delta 0.55) |
| B | 3 (+2 open) | 0.0% | -15.8% | 0.00 | -4.4% | -8.9% | 8.7% | 22.9% | 0 | MSFT: leap_delta_approx (static delta 0.55) |
| C | 0 (+0 open) | — | — | — | 0.0% | 0.0% | 0.0% | 0.0% | 0 | MSFT: leap_delta_approx (static delta 0.55) |
| D | 0 (+2 open) | — | — | — | 9.5% | 20.6% | 3.8% | 19.3% | 0 | MSFT: leap_delta_approx (static delta 0.55) |

**C arm stats:** 0 fired (avg arm→trigger — days), 7 armed-then-expired unfired (avg forgone return -7.7% over the armed window).

**D arm stats:** 3 fired (avg arm→trigger 85.33 days), 5 armed-then-expired unfired (avg forgone return 1.0% over the armed window).

## Benchmark — SPY buy-and-hold (same span, pre-vault)

Total return 62.8%, CAGR 11.4%, max drawdown 25.4%.

## UT / volume parameter sweeps

**UT sweep (scored on Strategy B pre-vault expectancy, stable-neighborhood rule):**
chosen key_value=**4.0**, atr_period=**7**. 

⚠️ **Both sweeps chose EDGE-of-grid cells** (key_value 4.0 is the sweep maximum; volume
multiplier 2.0 is its sweep maximum). An edge solution means the true optimum may lie
outside the swept range — treat both chosen values as provisional, not tuned.

| key_value | atr_period | expectancy | n_trades |
|---|---|---|---|
| 1.000 | 7 | 0.028 | 125 |
| 1.000 | 10 | 0.028 | 126 |
| 1.000 | 13 | 0.040 | 121 |
| 1.000 | 16 | 0.040 | 120 |
| 1.000 | 19 | 0.029 | 118 |
| 1.500 | 7 | 0.059 | 77 |
| 1.500 | 10 | 0.048 | 82 |
| 1.500 | 13 | 0.049 | 82 |
| 1.500 | 16 | 0.057 | 82 |
| 1.500 | 19 | 0.055 | 83 |
| 2.000 | 7 | 0.081 | 51 |
| 2.000 | 10 | 0.104 | 50 |
| 2.000 | 13 | 0.091 | 52 |
| 2.000 | 16 | 0.084 | 53 |
| 2.000 | 19 | 0.074 | 54 |
| 2.500 | 7 | 0.136 | 36 |
| 2.500 | 10 | 0.139 | 37 |
| 2.500 | 13 | 0.130 | 39 |
| 2.500 | 16 | 0.121 | 39 |
| 2.500 | 19 | 0.144 | 40 |
| 3.000 | 7 | 0.158 | 32 |
| 3.000 | 10 | 0.194 | 30 |
| 3.000 | 13 | 0.183 | 32 |
| 3.000 | 16 | 0.218 | 31 |
| 3.000 | 19 | 0.217 | 31 |
| 3.500 | 7 | 0.301 | 22 |
| 3.500 | 10 | 0.340 | 21 |
| 3.500 | 13 | 0.261 | 23 |
| 3.500 | 16 | 0.222 | 24 |
| 3.500 | 19 | 0.230 | 24 |
| 4.000 | 7 | 0.324 | 19 |
| 4.000 | 10 | 0.313 | 19 |
| 4.000 | 13 | 0.335 | 19 |
| 4.000 | 16 | 0.267 | 20 |
| 4.000 | 19 | 0.269 | 20 |


**Volume-multiplier sweep for Strategy D (1-D, same rule):** chosen **2.0x**. 
(The sweep RANGE itself is an ASSUMED-NOT-CONFIRMED reconstruction default — Addendum 1 never
reached the Code session; see config.yaml strategy_d.)

| multiplier | expectancy | n_trades |
|---|---|---|
| 1.000 | 0.001 | 18 |
| 1.250 | 0.027 | 15 |
| 1.500 | 0.080 | 11 |
| 1.750 | 0.086 | 10 |
| 2.000 | 0.086 | 10 |


## Ablations (combined pre-vault window)

| ablation | strategy | expectancy | n_closed | total_return |
|---|---|---|---|---|
| baseline | A | 0.267 | 9 | 0.327 |
| baseline | B | 0.324 | 19 | 1.287 |
| baseline | C | — | 0 | 0.000 |
| baseline | D | 0.344 | 8 | 0.400 |
| ladder_enabled | A | 0.344 | 9 | 0.234 |
| ladder_enabled | B | 0.339 | 21 | 0.474 |
| ladder_enabled | C | — | 0 | 0.000 |
| ladder_enabled | D | 0.396 | 8 | 0.207 |
| rsi_70_60_exit | A | 0.137 | 9 | 0.159 |
| rsi_70_60_exit | B | 0.251 | 22 | 1.154 |
| rsi_70_60_exit | C | — | 0 | 0.000 |
| rsi_70_60_exit | D | 0.274 | 8 | 0.294 |
| no_leap (MSFT as equity) | A | 0.305 | 9 | 0.358 |
| no_leap (MSFT as equity) | B | 0.339 | 19 | 1.338 |
| no_leap (MSFT as equity) | C | — | 0 | 0.000 |
| no_leap (MSFT as equity) | D | 0.381 | 8 | 0.429 |

Reading: the 3-tranche ladder does not obviously beat single-entry (higher per-trade expectancy,
lower total return — it deploys less capital); the retired 70→60 momentum exit HURT every strategy
that traded; removing the LEAP delta-approximation (pricing MSFT as plain equity) helps slightly,
i.e. the delta model drags as expected in an up-market for MSFT.

## Notes, caveats, and open flags

- **SPEC GAP — Strategy D is a reconstruction.** Addendum 1 (which defined D and the A/B/C/D build) never reached the Code session; only Addendum 2 arrived. D's volume-average window (20 three-day bars, prior bars only) and the sweep range (1.0–2.0 × 0.25) are ASSUMED defaults flagged in config.yaml, awaiting owner confirmation or veto. The 1.25x multiplier itself IS owner-specified.
- **Strategy C took ZERO trades in every window under the swept UT(4.0, 7) parameters.** Diagnosis (not an engine bug): arming worked — 18 arms set pre-vault — but a key_value-4.0 trailing stop is so wide that UT never produced a buy flip inside any armed (RSI 35→50) window; all 18 arms expired unfired (avg forgone return +3.1% over the armed windows). Under default UT(1.0, 10), C fires 18/23 arms → 16 closed trades, 50% win, +6.7% expectancy, +17.1% total return (see Sensitivity below). Methodology note: the sweep was scored on Strategy B alone and then applied to C — that coupling choice is exactly what this engine-validation pass exists to surface.
- **Vault divergence is a live overfit warning:** Strategy B went from +128.7% total return pre-vault (swept params, 74% win) to −4.4% with 0/3 wins in the 6-month vault. With n=3 that is not itself conclusive — but it is the exact pattern overfitting produces, and the vault has now been SPENT (it may not be re-tested against tweaked parameters).
- LEAP pricing: MSFT modeled via the delta-adjusted underlying-exposure approximation (static delta 0.55 = config midpoint), labeled on every row it touches. Feasibility spike confirmed Robinhood DOES serve full daily history for expired option contracts (MSFT Jun-2023 $300C: 493/493 real bars) — a future proof-of-edge pass can upgrade to real premiums; see backtest/leap_pricing.py for why this pass stayed uniform.
- NFLX runs on the equity path only (fails LEAP eligibility — established owner decision); MSFT is the sole LEAP candidate.
- Execution model: signals on 3-day bar closes fill at next bar open, 0.1% slippage each way, full-position exits (UT sell > RSI≥80 escape hatch), single-entry primary, alphabetical same-bar tie-break, 15% equity / 20% LEAP sizing, 5% cash floor, 2 new positions/week, 30% drawdown kill switch (30 days).
- SMA(200) is absent from all entry logic per the 2026-07-19 owner override (Addendum 2) — removed entirely, not ablated.
- Weekly not-making-lower-lows filter: current week's low >= lowest low of the prior 8 fully closed calendar weeks; the forming week is never consulted.

## Sensitivity: C and B under DEFAULT UT(1.0, 10), pre-vault (labeled extra — not the headline config)

| Strategy | Closed | Win rate | Expectancy | Total return | Max DD |
|---|---|---|---|---|---|
| B @ UT(1.0,10) | 126 | 39% | +2.8% | +54.3% | 23.1% |
| C @ UT(1.0,10) | 16 | 50% | +6.7% | +17.1% | 11.5% |

C's arm machinery under default UT: 18 fired (avg arm→trigger 55 days), 5 expired unfired
(avg forgone return +12.5% over the armed window).

*Report generated by backtest/orchestrate.py; every number above comes from the shared
simulate() engine — one engine, different inputs.*
