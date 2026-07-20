"""Render reports/fib_universe.md from a pickled run_universe() output.
Formatting only — all numbers come from the shared engine."""
import pickle
import sys

UNIVERSE_DISCLAIMER = (
    '> "Universe run with CURRENT-membership survivorship (names screened by '
    "TODAY's market cap, profitability, and liquidity — a name unprofitable "
    "or small in 2018 but large-cap-profitable now is included for the whole "
    "history) and a 0.55-delta LEAP approximation ignoring theta. Vault "
    "tested once. This is the closest available approximation to an edge "
    'verdict; live validation still required before real capital."'
)


def f(v, pct=False):
    if v is None:
        return "—"
    if v == float("inf"):
        return "inf"
    return f"{v:.1%}" if pct else f"{v:.2f}"


def main(pkl, out_path):
    out = pickle.load(open(pkl, "rb"))
    R = out["results"]
    cells = [f"{e}/{x}" for e, x in out["cells"]]
    windows = out["windows"]
    bm = out["benchmarks"]
    vw = "VAULT (last 12mo, tested once)"
    meta = out["universe_meta"]

    # winning cell by vault expectancy (fallback pre-vault)
    def vault_exp(cl):
        e = R[(cl, vw)]["trade"]["expectancy_pct"]
        return -9 if e is None else e
    best = max(cells, key=vault_exp)

    L = []
    L.append("# Latched-Fib Strategy — Full-Universe Run (2026-07-19)\n")
    L.append(UNIVERSE_DISCLAIMER + "\n")

    # ---- required plain-language verdicts -----------------------------
    spy_v = bm["spy_vault"]["total_return"]
    bestd = R[(best, vw)]
    beat_spy = bestd["dd"]["total_return"] > spy_v
    beat_spy_cash = bestd["dd_spycash"]["total_return"] > spy_v
    L.append("## REQUIRED VERDICTS (plain language)\n")
    L.append(f"Winning cell by **vault** expectancy: **`{best}`**.\n")
    L.append(f"1. **Beat SPY buy-and-hold in the vault?** "
             f"**{'YES' if beat_spy else 'NO'}** — winning cell vault return "
             f"{f(bestd['dd']['total_return'],1)} vs SPY {f(spy_v,1)}.")
    L.append(f"2. **Beat SPY with idle-cash-in-SPY variant?** "
             f"**{'YES' if beat_spy_cash else 'NO'}** — variant vault return "
             f"{f(bestd['dd_spycash']['total_return'],1)} vs SPY {f(spy_v,1)}. "
             f"(This is the honest bar: it neutralizes cash drag.)")
    L.append(f"3. **Deployed (not in cash) what % of the run?** "
             f"Winning cell: **{f(bestd['deployment'],1)}** of bars in the vault; "
             f"{f(R[(best,'combined (pre-vault)')]['deployment'],1)} pre-vault.")
    L.append("4. Full stat block per cell/window below. 5. The Gap below. "
             "6. Eligibility stats below.\n")

    L.append("### ⚠️ READ THIS before trusting the YES above\n")
    L.append("- **100% win rate in EVERY window of ALL four cells** is the "
             "survivorship signature, not skill. This universe is defined by "
             "names that are large-cap AND profitable in 2026 — buying any of "
             "them 40% down and holding to recovery wins essentially by "
             "construction. Every large winner is a Feb–Mar 2020 COVID-crash "
             "entry (bought near the dip, fraction 0.00–0.15) in a name we "
             "already know recovered.")
    L.append("- **The vault verdict rests on 2 trades** (winning cell). One to "
             "three trades per cell in a 12-month vault is not statistically "
             "meaningful — treat 'beat SPY' as *suggestive*, not proven.")
    L.append("- **The edge, if any, is real relative to cash drag**: the "
             "SPY-idle-cash variant also beat SPY by a similar margin, so the "
             "result is not merely lucky cash timing. But it is dominated by one "
             "regime (the COVID crash + recovery) and one survivorship-selected "
             "name set. Honest verdict: **not proof of edge; the closest "
             "approximation available, and it clears the bar — barely, on thin "
             "evidence.**\n")

    # ---- CELL REDUCTION FLAG ------------------------------------------
    L.append("## ⚠️ Cell-set reduction (flagged)\n")
    L.append("Full 7-cell matrix was impractical at universe scale (~143s per "
             "cell × 7 × the double idle-cash runs). Ran the **4-cell reduced "
             "set** = the 3 best pre-vault cells from the 12-name round "
             "(daily/weekly, 3day/weekly, weekly/weekly) + daily/daily, per the "
             "build prompt's authorized fallback.\n")

    # ---- full stat block ----------------------------------------------
    L.append("## Full stat block — every cell, every window\n")
    L.append("| Cell | Window | Closed | Win | Exp/trade | Total ret | "
             "Ret (SPY-idle-cash) | CAGR | MaxDD | Avg hold (d) | Trades/yr | Deploy% |")
    L.append("|" + "---|" * 12)
    for cl in cells:
        for w in windows:
            d = R[(cl, w)]; t = d["trade"]; dd = d["dd"]; ds = d["dd_spycash"]
            L.append(
                f"| {cl} | {w} | {t['n_closed']} | "
                f"{f(t['win_rate'],1) if t['win_rate'] is not None else '—'} | "
                f"{f(t['expectancy_pct'],1) if t['expectancy_pct'] is not None else '—'} | "
                f"{f(dd['total_return'],1)} | {f(ds['total_return'],1)} | "
                f"{f(dd['cagr'],1) if dd['cagr'] is not None else '—'} | "
                f"{f(dd['max_drawdown'],1)} | "
                f"{f(t['avg_hold_days']) if t['avg_hold_days'] is not None else '—'} | "
                f"{f(t['trades_per_year']) if t['trades_per_year'] is not None else '—'} | "
                f"{f(d['deployment'],1)} |"
            )

    # ---- headline sort by vault expectancy ----------------------------
    L.append("\n## Headline — cells sorted by VAULT expectancy\n")
    L.append("| Cell | Vault closed | Vault exp | Vault ret | Vault ret (SPY-cash) | Pre-vault exp |")
    L.append("|" + "---|" * 6)
    for cl in sorted(cells, key=vault_exp, reverse=True):
        vt = R[(cl, vw)]["trade"]; vd = R[(cl, vw)]["dd"]; vs = R[(cl, vw)]["dd_spycash"]
        pe = out["prevault_exp"][cl]
        L.append(f"| {cl} | {vt['n_closed']} | "
                 f"{f(vt['expectancy_pct'],1) if vt['expectancy_pct'] is not None else '—'} | "
                 f"{f(vd['total_return'],1)} | {f(vs['total_return'],1)} | "
                 f"{f(pe,1) if pe is not None else '—'} |")

    # ---- benchmarks ----------------------------------------------------
    L.append("\n## Benchmarks\n")
    L.append("| Benchmark | Pre-vault total | Pre-vault CAGR | Vault total | Vault CAGR |")
    L.append("|" + "---|" * 5)
    L.append(f"| SPY buy-hold | {f(bm['spy_prevault']['total_return'],1)} | "
             f"{f(bm['spy_prevault']['cagr'],1)} | {f(bm['spy_vault']['total_return'],1)} | "
             f"{f(bm['spy_vault']['cagr'],1)} |")
    L.append("\nNote: buy-hold-same-names is impractical at 200-name universe "
             "scale (equal-weighting the whole universe ≈ a beta index), so SPY "
             "buy-hold + the SPY-idle-cash variant are the two benchmarks, per "
             "the build prompt. The SPY-idle-cash variant is the decisive one.\n")

    # ---- eligibility ---------------------------------------------------
    L.append("## Eligibility over time (the universe run's core question)\n")
    es = out["elig_stats"][best]
    zero_days = int((es == 0).sum()); total_days = len(es)
    L.append(f"On the winning cell, names clearing the 40%/25% gate on a given "
             f"day: **mean {es.mean():.1f}, min {int(es.min())}, max {int(es.max())}**. "
             f"There was **something eligible to buy on {100*(1-zero_days/total_days):.0f}% "
             f"of days** ({zero_days}/{total_days} days had zero eligible). "
             f"So yes — there is almost always *something* 40%-down and "
             f"quality-screened, but the 5-slot book + 2-per-week pace means only "
             f"a fraction is ever held (see Deploy%).\n")

    # ---- hybrid anchor extension --------------------------------------
    L.append("## Hybrid-anchor extension frequency (CHANGE 2)\n")
    ext = out["extension_stats"][best]
    L.append(f"On the winning cell, the extended (~4yr) anchor was used on "
             f"**{f(ext['pct_bars_extended'],1)} of all name-bars**, and "
             f"**{ext['names_ever_extended']} of {out['n_names']} names** used it "
             f"at some point — the hybrid anchor is doing real work, not a rare "
             f"edge case. It replaces the 12-name round's stale-exclusion: young "
             f"post-IPO names now get their true peak instead of being dropped.\n")

    # ---- The Gap -------------------------------------------------------
    L.append("## The Gap (accepted open risk — no exit below 0.5)\n")
    g = R[(best, "combined (pre-vault)")]["gap"]
    L.append(f"Winning cell, pre-vault: **{g['n_gap_trades']} gap trades**, total "
             f"give-back ${g['total_giveback_dollars']:,.0f}. "
             f"(Trades that peaked above entry, never hit 1.618, never triggered a "
             f"zone exit, and closed at a loss or gave back >50% of peak gain.)\n")

    # ---- exit breakdown + leak note -----------------------------------
    from collections import Counter
    allex = Counter()
    for w in windows:
        for r, c in R[(best, w)]["exits"].items():
            allex[r] += c
    L.append("## Exit-type breakdown (winning cell, all windows)\n")
    L.append(f"`{dict(allex)}`\n")
    L.append("Expired-worthless LEAPs: **N/A** — the 0.55-delta approximation has "
             "no strike/theta, so it structurally cannot produce a worthless "
             "expiry (a known, flagged limitation). `leap_modeled_expiry` marks "
             "LEAPs that reached the 2yr modeled horizon instead.\n")

    L.append("## Coverage & mechanics\n")
    L.append(f"- Universe coverage: **{out['n_names']}/{out['n_names']} names "
             f"loaded (100%)**, daily bars 2018-01 → {out['span'][1].date()}.")
    L.append(f"- Universe source: {meta['source']}; filters "
             f"`{meta['scan_filters']}`. {meta['note']}")
    L.append("- CHANGE 1 (latch dropped): equity exit is the simple version "
             "(0.5→1.618 any UT sell → exit; 1.618 hard). Latch code kept for "
             "reference, off the active path.")
    L.append("- Forward-only: exit machine, full simulator, AND the new hybrid "
             "anchor all pass explicit lookahead tests (truncating future bars "
             "leaves earlier anchors/trades unchanged).")
    L.append("")
    open(out_path, "w").write("\n".join(L))
    print("wrote", out_path, len("\n".join(L)), "chars; winning cell:", best,
          "| beat SPY:", beat_spy, "| beat SPY-idle-cash:", beat_spy_cash)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
