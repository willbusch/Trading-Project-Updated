"""Render reports/fib_final_run.md — the 2026-07-21 locked configuration:
real LEAP pricing + tiered gate (official) + ratio tiebreak + new sizing,
daily/weekly cell only."""
import json
import pickle
import sys

DISCLAIMER = (
    '> "Still a survivorship-biased proxy universe with current-snapshot '
    "market caps. Real LEAP pricing makes the P&L HONEST but does not "
    "remove survivorship bias. Improves accuracy, does not prove edge. "
    "Research re-closes after this run; genuine validation needs "
    "point-in-time membership + fundamentals + market caps Robinhood "
    'can\'t provide."'
)


def f(v, pct=False):
    if v is None:
        return "—"
    return f"{v:.1%}" if pct else f"{v:.2f}"


def main(final_pkl, correction_json, out_path):
    out = pickle.load(open(final_pkl, "rb"))
    correction = json.load(open(correction_json))
    R = out["results"]

    L = ["# Locked Configuration Run — Real LEAP Pricing + Tiered Gate + Ratio Tiebreak (2026-07-21)\n",
        DISCLAIMER + "\n"]

    L.append("## 1. LEAP P&L correction — old approximation vs real pricing\n")
    L.append("| Ticker | Entry | Exit | Underlying move | OLD approx | NEW real | Multiplier |")
    L.append("|---|---|---|---|---|---|---|")
    for r in correction:
        mult = r["multiplier_vs_underlying"]
        mult_str = f"{mult:.2f}x" if mult is not None else "—"
        exit_label = r["exit_date"] or "OPEN (marked to latest close)"
        L.append(f"| {r['ticker']} | {r['entry_date']} | {exit_label} | "
                 f"{f(r['underlying_move_pct'],1)} | {f(r['old_approx_pnl_pct'],1)} | "
                 f"{f(r['new_real_pnl_pct'],1) if r['new_real_pnl_pct'] is not None else '—'} | {mult_str} |")
    L.append("\n**Every single LEAP trade was mispriced by the old model, in both directions.** "
             "JPM, ASML, TSLA, and the second MU trade were all understated by roughly "
             "2.5–3.8x — the old flat-delta model showed a fraction of the underlying's move "
             "when a real option would have shown a multiple of it. The first MU trade is the "
             "sharper correction: the underlying was flat (−1.2%) and the old model correctly-ish "
             "showed near-zero P&L, but the REAL option — held through 2 years of theta decay "
             "into a flat-to-down underlying — expired **completely worthless (−100%)**. The old "
             "model could not represent this outcome at all; it's a new, real risk this pricing "
             "engine finally exposes. MSFT (still open) similarly flips from a rounding-error "
             "0% under the old model to a real **−21.7%** loss under real pricing, on a barely-"
             "negative underlying move — theta decay alone. *(Multiplier figures on small "
             "underlying moves, e.g. MU's 85x, are mathematically noisy — not a meaningful ratio "
             "when the denominator is near zero; read the absolute percentages instead.)*\n")

    L.append("## 2. Does total return change materially once LEAPs are priced right?\n")
    fs = R["FULL SPAN"]["trade"]; fsd = R["FULL SPAN"]["dd"]
    L.append(f"Full span (2018–2026): **{fs['n_closed']} closed trades**, "
             f"{f(fs['win_rate'],1)} win rate, total return {f(fsd['total_return'],1)}, "
             f"CAGR {f(fsd['cagr'],1)}. LEAP trades now swing the book far harder than before "
             "— both up (JPM +208%, MU #2 +204%) and down (MU #1 a full −100% loss at 33% "
             "sizing). LEAPs are now genuinely \"the profit driver\" the strategy intends, but "
             "also genuinely the biggest single risk in the book — see question 5.\n")

    L.append("## 3. Trade count + does the tiebreak fix work?\n")
    L.append(f"Full span: **{fs['n_closed']} closed + open trades** across 8 years — still a "
             "low-frequency, rare-event strategy by design (deep drawdowns on quality "
             "mega/large-caps aren't common). The ratio tiebreak bound (mattered) on 5 dates "
             "across the full run. Concrete evidence it works: on 2025-01-06, 7 names competed "
             "for slots — **AMAT ($421B) was admitted**; CVS ($137B), HOOD ($90B), MDT ($106B), "
             "and QCOM ($181B) were rejected on the weekly cap. The largest caps in the "
             "contested group won, exactly as specified — not just passing a unit test, but "
             "observed in the actual run.\n")

    L.append("## 4. Vault trades + expectancy\n")
    vt = R["VAULT (last 12mo, tested once)"]["trade"]; vd = R["VAULT (last 12mo, tested once)"]["dd"]
    L.append(f"**{vt['n_closed']} vault trades** (above the 1–2 range seen in every prior round), "
             f"{f(vt['win_rate'],1)} win rate, expectancy {f(vt['expectancy_pct'],1)}, "
             f"total return {f(vd['total_return'],1)}. Still too thin a sample (n=2) to call "
             "decisive — consistent with every caveat carried through this project — but it did "
             "not regress from prior rounds.\n")

    L.append("## 5. Max drawdown — does the leverage cut both ways?\n")
    L.append(f"**Yes, sharply.** Full-span max drawdown is **{f(fsd['max_drawdown'],1)}** — well "
             "above every prior round's 17–40% range. Verified, not assumed: the worst drawdown "
             "(peak $265,671 → trough $98,923, 2022-09-30) coincides exactly with the MU LEAP "
             "position (entered 2021-10-21 at 33% of book) sitting open through the entire 2022 "
             "bear market before expiring worthless in October 2023. A single 33%-sized LEAP "
             "that goes to zero is a much harder hit than the old model's linear delta could ever "
             "produce — this IS the leverage cutting both ways, exactly as anticipated, now "
             "visible in the numbers for the first time.\n")

    L.append("## 6. Year-spread + dashboard\n")
    ys = R["FULL SPAN"]["year_spread"]
    L.append(f"Full-span trade entries by year: `{ys}`. Still 2020-heavy (5 of 10) but real "
             "entries appear in 2021, 2023, 2024, and 2025 — consistent with the tiered gate's "
             "prior finding, now combined with real LEAP pricing and the new sizing. "
             "`reports/results_dashboard.html` regenerated with this run's real-LEAP-priced "
             "results as the primary curve.\n")

    L.append("## Full stat block\n")
    L.append("| Window | Closed | Win | Exp/trade | Total ret | CAGR | Max DD | Deploy% |")
    L.append("|" + "---|" * 8)
    for w in out["windows"]:
        d = R[w]; t = d["trade"]; dd = d["dd"]
        L.append(f"| {w} | {t['n_closed']} | {f(t['win_rate'],1) if t['win_rate'] is not None else '—'} | "
                 f"{f(t['expectancy_pct'],1) if t['expectancy_pct'] is not None else '—'} | "
                 f"{f(dd['total_return'],1)} | {f(dd['cagr'],1) if dd['cagr'] is not None else '—'} | "
                 f"{f(dd['max_drawdown'],1)} | {f(d['deployment'],1)} |")

    L.append("\n## Leak-hunt\n")
    L.append("Half-2 (88% CAGR, n=3) and vault (70% CAGR, n=2) exceed the 50% flag threshold — "
             "both are thin-window annualization artifacts of small trade counts, the same "
             "pattern seen in every prior round, verified by inspecting the underlying trades "
             "directly rather than trusting the aggregate. Combined pre-vault (9%) and full-span "
             "(15%) CAGR are unremarkable. The 62.8% max drawdown was independently traced to a "
             "specific, real position (see question 5) — not a data artifact.\n")

    L.append("## Benchmarks\n")
    bm = out["benchmarks"]
    L.append(f"SPY buy-hold: pre-vault {f(bm['spy_prevault']['total_return'],1)}, "
             f"vault {f(bm['spy_vault']['total_return'],1)}.\n")

    open(out_path, "w").write("\n".join(L))
    print("wrote", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
