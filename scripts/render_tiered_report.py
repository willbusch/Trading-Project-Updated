"""Render reports/fib_tiered_gate.md — the tiered-drawdown-gate run."""
import pickle
import sys

DISCLAIMER = (
    '> "This run REOPENS the formally-closed research phase. The data '
    "limitation is unchanged: survivorship-biased proxy universe, no "
    "point-in-time membership/fundamentals, and now also a CURRENT-market-cap "
    "proxy for the tier assignment itself (a name's tier is fixed at today's "
    "cap and applied across its entire backtest history). This run can "
    'IMPROVE the strategy; it CANNOT prove edge."'
)


def f(v, pct=False):
    if v is None:
        return "—"
    return f"{v:.1%}" if pct else f"{v:.2f}"


def main(tiered_pkl, out_path):
    tiered = pickle.load(open(tiered_pkl, "rb"))
    flat = pickle.load(open(
        "/tmp/claude-0/-home-user-Trading-Project-Updated/"
        "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/final_ablation_results.pkl",
        "rb"))

    R = tiered["results"]
    cells = [f"{e}/{x}" for e, x in tiered["cells"]]
    windows = [w for w in tiered["windows"] if w != "FULL SPAN"]
    pv, vw = "combined (pre-vault)", "VAULT (last 12mo, tested once)"

    L = ["# Tiered Drawdown Gate — Reopened Research (2026-07-20)\n", DISCLAIMER + "\n"]

    L.append("## The mechanical delta\n")
    L.append("Only the **$150B–$500B band** actually changes: 40% → 30%. "
             "$500B+ names were already 25% (auto-LEAP-tier under the old "
             "gate); sub-$150B names were already 40%. 73 of the 200 "
             "universe names fall in the affected band. Verified directly "
             "against the tested module (ORCL: 130→176 eligible days, "
             "8→10 entry candidates under the looser threshold) — the "
             "per-ticker mechanism works exactly as specified.\n")

    L.append("## Watch-for questions — answered\n")
    L.append("1. **Trade count up vs flat-40%?** Mixed, and counterintuitively "
             "**down** on the baseline cell (daily/weekly: 12→9 pre-vault "
             "trades). Verified this is NOT a bug — it's a real emergent "
             "effect: more names now clear the gate and compete for the "
             "same 5-slot/2-per-week throttle, which changes WHICH names get "
             "traded, not just how many. Some of the flat-gate's biggest "
             "2020 winners got crowded out by earlier entries into newly-"
             "eligible mid-caps under the deepest-drawdown-first tiebreak.")
    L.append("2. **Vault trades > 1?** **Barely.** 2 of 6 cells (daily/weekly, "
             "daily/3day) reached 2 vault trades; the other 4 stayed at 1. "
             "This is real movement, not nothing — but it's not the "
             "transformation the hypothesis hoped for.")
    L.append("3. **Expectancy trade-off?** Yes, exactly as expected: "
             "daily/weekly expectancy dropped 93.9%→58.5% pre-vault (shallower "
             "dips = smaller per-trade moves), while trade count also fell "
             "rather than rising — the worst combination of the two "
             "possible outcomes on this specific cell, though other cells "
             "(weekly/weekly: 79.4% exp, 10 trades) did better on both axes.")
    L.append("4. **Deployment % up?** **No, essentially flat** — every "
             "tiered cell shows ~76% deployment vs the flat baseline's 72%. "
             "The gate loosening did not meaningfully increase time invested.")
    L.append("5. **Trade clustering — did it spread beyond COVID?** **Yes, "
             "measurably.** Full-span year-spread now includes real entries "
             "in 2021, 2022, 2023, 2024, 2025, and 2026 across the 6 cells — "
             "not just 2020. But 2020 still contributes 6–7 of each cell's "
             "12–16 total trades (40–50%), so it remains the single richest "
             "year by a wide margin. The tiering worked directionally; it "
             "did not eliminate the crash-concentration problem.\n")

    L.append("## Full matrix (sorted by total return — owner's explicit choice; "
             "vault expectancy sits one column over, never hidden)\n")
    L.append("| Cell | Total Return | Pre-vault Exp | Pre-vault N | Vault Exp | "
             "Vault N | Years spread (full span) |")
    L.append("|" + "---|" * 7)
    rows = []
    for cl in cells:
        d = R[(cl, pv)]; t = d["trade"]; dd = d["dd"]
        vd = R[(cl, vw)]["trade"]
        ys = R[(cl, "FULL SPAN")]["year_spread"]
        rows.append((cl, dd["total_return"], t["expectancy_pct"], t["n_closed"],
                    vd["expectancy_pct"], vd["n_closed"], ys))
    rows.sort(key=lambda r: -(r[1] or -9))
    for cl, ret, exp, n, vexp, vn, ys in rows:
        flag = " ⚠️ weakest vault of the 6" if vn == min(r[5] for r in rows) and (vexp or 0) == min(
            (r[4] or 9) for r in rows if r[5] == vn) else ""
        L.append(f"| {cl} | {f(ret,1)} | {f(exp,1)} | {n} | {f(vexp,1)}{flag} | {vn} | {ys} |")

    L.append("\n**Read this table left-to-right before trusting the sort:** "
             "`weekly/3day` ranks #1 by total return (+259%) but has the "
             "weakest vault performance of all 6 cells (n=1, lowest vault "
             "expectancy) — exactly the 'one-COVID-trade winner dressed up "
             "as the champion' risk this table's second-and-third columns "
             "exist to catch. `weekly/weekly` and `weekly/3day` both look "
             "strong on total return AND have real trade counts (10-11 "
             "pre-vault), which is a more defensible read than the raw sort "
             "order alone.\n")

    L.append("## Tiered vs flat-40% — side by side, winning cell (daily/weekly, 0.9-floor exit)\n")
    L.append("| | Pre-vault N | Pre-vault Exp | Pre-vault Ret | Deploy% | Vault N | Vault Exp | Vault Ret |")
    L.append("|---|---|---|---|---|---|---|---|")
    fd = flat["exit_results"]
    fpv, fva = fd[("simple_09", pv)], fd[("simple_09", vw)]
    L.append(f"| **Flat 40%/25%** | {fpv['trade']['n_closed']} | "
             f"{f(fpv['trade']['expectancy_pct'],1)} | {f(fpv['dd']['total_return'],1)} | "
             f"{f(fpv['deployment'],1)} | {fva['trade']['n_closed']} | "
             f"{f(fva['trade']['expectancy_pct'],1)} | {f(fva['dd']['total_return'],1)} |")
    tpv, tva = R[(cells[0], pv)], R[(cells[0], vw)]
    L.append(f"| **Tiered 25/30/40** | {tpv['trade']['n_closed']} | "
             f"{f(tpv['trade']['expectancy_pct'],1)} | {f(tpv['dd']['total_return'],1)} | "
             f"{f(tpv['deployment'],1)} | {tva['trade']['n_closed']} | "
             f"{f(tva['trade']['expectancy_pct'],1)} | {f(tva['dd']['total_return'],1)} |")
    L.append("\nOn the flat gate's own former champion cell, tiering LOWERED "
             "both trade count and total return, while modestly raising "
             "vault trade count (1→2) and vault expectancy (94.5%→102%). "
             "It's a genuine trade-off, not a strict improvement, on this "
             "specific cell — other cells in the matrix above look more "
             "favorable on balance.\n")

    L.append("## Leak-hunt\n")
    L.append("Passed. Full-span CAGR ranges 11%–23% across all 6 cells "
             "(weekly/weekly highest). No cell approaches the 50% flag "
             "threshold. Per-ticker eligibility mechanism verified directly "
             "against the tested module, not just trusted from aggregate "
             "output.\n")

    L.append("## Benchmarks (unchanged data span)\n")
    bm = tiered["benchmarks"]
    L.append(f"SPY buy-hold: pre-vault {f(bm['spy_prevault']['total_return'],1)}, "
             f"vault {f(bm['spy_vault']['total_return'],1)}.\n")

    open(out_path, "w").write("\n".join(L))
    print("wrote", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
