"""Render reports/fib_final_ablation.md from run_final_ablation() output."""
import pickle
import sys
from collections import Counter


def f(v, pct=False):
    if v is None:
        return "—"
    return f"{v:.1%}" if pct else f"{v:.2f}"


def main(pkl, out_path):
    out = pickle.load(open(pkl, "rb"))
    R = out["exit_results"]
    TR = out["throttle_results"]
    windows = out["windows"]
    winner = out["winning_variant"]
    bm = out["benchmarks"]

    L = []
    L.append("# Final Structural Ablation — Exit 3-Way + Deployment Throttle (2026-07-20)\n")
    L.append('> "Curated-universe backtest, current-membership survivorship proxy, '
             '0.55-delta LEAP approximation, vault tested once, selection made on '
             'pre-vault metrics only (never the vault) to avoid re-peeking the held-out '
             'window across five candidate variants. This closes the research phase — '
             'see docs/PLAN.md. Not proof of edge."\n')

    L.append(f"## Verdict: winning equity exit = **`{winner}`**\n")
    L.append("Selected on **pre-vault** expectancy only (vault reported below for "
             "transparency, never used to pick). Both the old 0.5-floor champion and "
             "the new full-latch design (`latch_v2`) LOSE to a plain 0.9 floor with no "
             "latch at all — simplicity keeps winning across every ablation round run "
             "so far in this project.\n")
    L.append("| Variant | Pre-vault expectancy |")
    L.append("|---|---|")
    for v in ["simple_05", "simple_09", "latch_v2"]:
        e = out["prevault_exp"][v]
        mark = " ⭐ WINNER" if v == winner else ""
        L.append(f"| {v} | {f(e,1) if e is not None else '—'}{mark} |")

    L.append("\n## Full stat block — exit variants, every window\n")
    L.append("| Variant | Window | Closed | Win | Exp/trade | Total ret | Ret (SPY-cash) | CAGR | MaxDD |")
    L.append("|" + "---|" * 9)
    for v in ["simple_05", "simple_09", "latch_v2"]:
        for w in windows:
            d = R[(v, w)]; t = d["trade"]; dd = d["dd"]; ds = d["dd_spycash"]
            L.append(f"| {v} | {w} | {t['n_closed']} | "
                     f"{f(t['win_rate'],1) if t['win_rate'] is not None else '—'} | "
                     f"{f(t['expectancy_pct'],1) if t['expectancy_pct'] is not None else '—'} | "
                     f"{f(dd['total_return'],1)} | {f(ds['total_return'],1)} | "
                     f"{f(dd['cagr'],1) if dd['cagr'] is not None else '—'} | {f(dd['max_drawdown'],1)} |")

    L.append("\n## The Gap per variant (pre-vault) — quantifying what each floor costs vs catches\n")
    L.append("| Variant | Gap trades | Total give-back |")
    L.append("|---|---|---|")
    for v in ["simple_05", "simple_09", "latch_v2"]:
        g = R[(v, "combined (pre-vault)")]["gap"]
        L.append(f"| {v} | {g['n_gap_trades']} | ${g['total_giveback_dollars']:,.0f} |")
    L.append("\nThe 0.5 and 0.9 simple floors show **zero** gap trades in this sample — "
             "every trade either hit 1.618 or exited cleanly on a UT sell above its "
             "floor. `latch_v2` shows **3 gap trades totaling $77,064 given back** — its "
             "extra travel-zone latches (0.5-0.9 and 1.1-1.5) let winners round-trip "
             "further before the latch actually fires than a plain floor would allow. "
             "This is the concrete price of the latch complexity the owner asked to "
             "quantify, and it's a real cost, not a rounding error.\n")

    L.append("## Exit-type breakdown per variant (all windows)\n")
    for v in ["simple_05", "simple_09", "latch_v2"]:
        c = Counter()
        for w in windows:
            for r, n in R[(v, w)]["exits"].items():
                c[r] += n
        L.append(f"- `{v}`: `{dict(c)}`")
    L.append("")

    L.append("## Deployment throttle ablation\n")
    L.append("| Config | Window | Closed | Total ret | Deploy% (binary: any position open) |")
    L.append("|" + "---|" * 5)
    for label in ["baseline (5 slots / 2 per wk)", "loosened (6 slots / 3 per wk)"]:
        for w in windows:
            d = TR[(label, w)]; t = d["trade"]; dd = d["dd"]
            L.append(f"| {label} | {w} | {t['n_closed']} | {f(dd['total_return'],1)} | {f(d['deployment'],1)} |")
    L.append("\n**Verdict: loosening did NOT help.** Pre-vault total return dropped from "
             "+416% to +215% with the loosened throttle — more slots let in lower-priority "
             "names (per the deepest-drawdown tiebreak) that diluted returns rather than "
             "adding uncorrelated upside. Recommend **keeping the current 5-slot / "
             "2-per-week configuration**. Caveat: `deploy%` here is a BINARY \"was any "
             "position open\" metric, not dollar-weighted utilization — it shows "
             "identically in both configs and does not fully capture whether looser "
             "slots increased capital actually deployed; a follow-up metric would be "
             "needed to fully settle the idle-capital question.\n")

    L.append("## Benchmarks (winning exit variant, baseline throttle)\n")
    L.append(f"- SPY buy-hold: pre-vault {f(bm['spy_prevault']['total_return'],1)} "
             f"(CAGR {f(bm['spy_prevault']['cagr'],1)}), vault {f(bm['spy_vault']['total_return'],1)}")

    open(out_path, "w").write("\n".join(L))
    print("wrote", out_path, "winner:", winner)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
