# Locked Configuration Run — Real LEAP Pricing + Tiered Gate + Ratio Tiebreak (2026-07-21)

> "Still a survivorship-biased proxy universe with current-snapshot market caps. Real LEAP pricing makes the P&L HONEST but does not remove survivorship bias. Improves accuracy, does not prove edge. Research re-closes after this run; genuine validation needs point-in-time membership + fundamentals + market caps Robinhood can't provide."

## 1. LEAP P&L correction — old approximation vs real pricing

| Ticker | Entry | Exit | Underlying move | OLD approx | NEW real | Multiplier |
|---|---|---|---|---|---|---|
| JPM | 2020-03-11 | 2021-06-21 | 52.3% | 28.8% | 196.8% | 3.76x |
| MU | 2021-10-21 | 2023-10-24 | -1.2% | -0.6% | -100.0% | 85.03x |
| ASML | 2023-10-25 | 2024-04-22 | 45.3% | 24.9% | 143.0% | 3.16x |
| TSLA | 2024-04-25 | 2025-01-13 | 140.6% | 77.3% | 440.1% | 3.13x |
| MU | 2025-01-16 | 2025-10-17 | 90.7% | 49.9% | 230.9% | 2.55x |
| MSFT | 2026-02-26 | OPEN (marked to latest close) | -2.3% | -1.3% | -21.7% | 9.26x |

**Every single LEAP trade was mispriced by the old model, in both directions.** JPM, ASML, TSLA, and the second MU trade were all understated by roughly 2.5–3.8x — the old flat-delta model showed a fraction of the underlying's move when a real option would have shown a multiple of it. The first MU trade is the sharper correction: the underlying was flat (−1.2%) and the old model correctly-ish showed near-zero P&L, but the REAL option — held through 2 years of theta decay into a flat-to-down underlying — expired **completely worthless (−100%)**. The old model could not represent this outcome at all; it's a new, real risk this pricing engine finally exposes. MSFT (still open) similarly flips from a rounding-error 0% under the old model to a real **−21.7%** loss under real pricing, on a barely-negative underlying move — theta decay alone. *(Multiplier figures on small underlying moves, e.g. MU's 85x, are mathematically noisy — not a meaningful ratio when the denominator is near zero; read the absolute percentages instead.)*

## 2. Does total return change materially once LEAPs are priced right?

Full span (2018–2026): **10 closed trades**, 90.0% win rate, total return 241.6%, CAGR 15.5%. LEAP trades now swing the book far harder than before — both up (JPM +208%, MU #2 +204%) and down (MU #1 a full −100% loss at 33% sizing). LEAPs are now genuinely "the profit driver" the strategy intends, but also genuinely the biggest single risk in the book — see question 5.

## 3. Trade count + does the tiebreak fix work?

Full span: **10 closed + open trades** across 8 years — still a low-frequency, rare-event strategy by design (deep drawdowns on quality mega/large-caps aren't common). The ratio tiebreak bound (mattered) on 5 dates across the full run. Concrete evidence it works: on 2025-01-06, 7 names competed for slots — **AMAT ($421B) was admitted**; CVS ($137B), HOOD ($90B), MDT ($106B), and QCOM ($181B) were rejected on the weekly cap. The largest caps in the contested group won, exactly as specified — not just passing a unit test, but observed in the actual run.

## 4. Vault trades + expectancy

**2 vault trades** (above the 1–2 range seen in every prior round), 100.0% win rate, expectancy 243.9%, total return 69.8%. Still too thin a sample (n=2) to call decisive — consistent with every caveat carried through this project — but it did not regress from prior rounds.

## 5. Max drawdown — does the leverage cut both ways?

**Yes, sharply.** Full-span max drawdown is **62.8%** — well above every prior round's 17–40% range. Verified, not assumed: the worst drawdown (peak $265,671 → trough $98,923, 2022-09-30) coincides exactly with the MU LEAP position (entered 2021-10-21 at 33% of book) sitting open through the entire 2022 bear market before expiring worthless in October 2023. A single 33%-sized LEAP that goes to zero is a much harder hit than the old model's linear delta could ever produce — this IS the leverage cutting both ways, exactly as anticipated, now visible in the numbers for the first time.

## 6. Year-spread + dashboard

Full-span trade entries by year: `{2020: 5, 2021: 2, 2023: 1, 2024: 1, 2025: 1}`. Still 2020-heavy (5 of 10) but real entries appear in 2021, 2023, 2024, and 2025 — consistent with the tiered gate's prior finding, now combined with real LEAP pricing and the new sizing. `reports/results_dashboard.html` regenerated with this run's real-LEAP-priced results as the primary curve.

## Full stat block

| Window | Closed | Win | Exp/trade | Total ret | CAGR | Max DD | Deploy% |
|---|---|---|---|---|---|---|---|
| combined (pre-vault) | 7 | 85.7% | 72.0% | 90.6% | 8.9% | 62.8% | 73.2% |
| half-1 (→ 2024-01-01) | 5 | 80.0% | 58.2% | 36.3% | 5.3% | 62.8% | 66.4% |
| half-2 (2024-01-01 → vault) | 3 | 100.0% | 172.1% | 163.4% | 87.7% | 40.8% | 99.7% |
| VAULT (last 12mo, tested once) | 2 | 100.0% | 243.9% | 69.8% | 69.9% | 24.2% | 99.6% |
| FULL SPAN | 10 | 90.0% | 94.2% | 241.6% | 15.5% | 62.8% | 76.4% |

## Leak-hunt

Half-2 (88% CAGR, n=3) and vault (70% CAGR, n=2) exceed the 50% flag threshold — both are thin-window annualization artifacts of small trade counts, the same pattern seen in every prior round, verified by inspecting the underlying trades directly rather than trusting the aggregate. Combined pre-vault (9%) and full-span (15%) CAGR are unremarkable. The 62.8% max drawdown was independently traced to a specific, real position (see question 5) — not a data artifact.

## Benchmarks

SPY buy-hold: pre-vault 45.9%, vault 18.4%.
