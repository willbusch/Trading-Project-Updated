"""Generate the JSON data the results dashboard reads. Primary curves/
stats/trade-log now come from the 2026-07-22 "Beat-SPY Package" run — the
12-cell grid's #1-ranked cell by return/maxDD (`3day / both / trail_ut`,
full Part A: A2 top-10-cap LEAP eligibility, A3 spendable reserve, A4 slot
recycling, A5 LEAP decay exit, A6 LEAP-only kill switch, A7 trailing exit)
— consumed from the exact pickled grid/full-span run rather than
re-simulated, same consistency discipline as every prior round. See
reports/beat_spy_package.md for the full honest verdict: this cell does
NOT beat SPY risk-adjusted despite the enormous headline return, and the
mandatory overfitting guard flags it as concentration-driven, not proven
edge — both facts are carried into the dashboard's caveat banner.

Run this after any backtest change to regenerate reports/dashboard_data.json,
then re-run scripts/generate_dashboard.py to rebuild the HTML.
"""
import json
import pickle

import pandas as pd

from screener.data import fetch_daily_bars

WINNING_CELL = ("3day", "weekly")
WINNING_VARIANT = "trail_ut"
WINNING_SIZING = "both"


def _curve_to_json(curve: pd.Series) -> dict:
    return {"dates": [d.strftime("%Y-%m-%d") for d in curve.index],
           "values": [round(float(v), 2) for v in curve.values]}


def _align_and_serialize_curves(curves: dict) -> dict:
    """A8 fix (2026-07-22, "Beat-SPY Package"): the SPY benchmark curve
    used to truncate mid-chart because all three series were keyed to ONE
    shared `labels` array (the strategy curve's own dates) while each
    dataset supplied only a bare `values` array — Chart.js pairs values
    with labels POSITIONALLY, so any length/date mismatch between series
    (different start dates, different trading-day sets) silently
    misaligned or truncated whichever series was shorter.

    Fix: reindex every curve onto ONE shared union-of-dates index BEFORE
    serializing, forward-filling gaps (each curve is a daily
    mark-to-market equity value, so carrying the last known value forward
    across a missing date is the correct semantics, not a display hack).
    After this, DATA.curves.<name>.dates is IDENTICAL across every series
    — not just coincidentally equal-length — so keying all three Chart.js
    datasets off the strategy curve's `dates` array (kept as-is in the
    template) is now actually safe."""
    common_index = pd.DatetimeIndex(
        sorted(set().union(*[set(c.index) for c in curves.values()]))
    )
    out = {}
    for name, curve in curves.items():
        aligned = curve.reindex(common_index).ffill().bfill()
        out[name] = {"dates": [d.strftime("%Y-%m-%d") for d in aligned.index],
                     "values": [round(float(v), 2) for v in aligned.values]}
    return out


SCRATCH = ("/tmp/claude-0/-home-user-Trading-Project-Updated/"
          "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad")


def main():
    entry_tf, exit_tf = WINNING_CELL

    # CONSISTENCY DISCIPLINE (established 2026-07-21, continued here):
    # primary curves/stats/trade-log are loaded from the EXACT pickled
    # Beat-SPY Package grid/full-span run (reports/beat_spy_package.md),
    # not re-simulated — guarantees the dashboard and the written report
    # always show identical numbers for the same run.
    grid = pickle.load(open(f"{SCRATCH}/beat_spy_grid_results.pkl", "rb"))
    fullspan = pickle.load(open(f"{SCRATCH}/champion_fullspan.pkl", "rb"))
    res_plain = fullspan["res_plain"]
    res_spycash = fullspan["res_full_spycash"]
    start, end = grid["span"]
    vault_start = grid["vault_start"]

    champion_key = (entry_tf, WINNING_SIZING, WINNING_VARIANT)
    champ = grid["grid_results"][champion_key]

    spy = fetch_daily_bars("SPY")["Close"]
    spy_span = spy.loc[start:end]
    spy_curve = (spy_span / spy_span.iloc[0]) * 100_000.0

    # window-sliced stats come from the SAME grid run reports/beat_spy_package.md
    # reports, not a post-hoc date-filter of the full-span trade list — see
    # the 2026-07-21 consistency-fix note this pattern originates from.
    stats = {
        "pre_vault": {k: v for k, v in champ["combined (pre-vault)"].items() if k != "result"},
        "vault": {k: v for k, v in champ["VAULT (last 12mo, tested once)"].items() if k != "result"},
    }

    spy_bm = {
        "pre_vault": grid["benchmarks"]["spy_prevault"],
        "vault": grid["benchmarks"]["spy_vault"],
    }

    trade_log = []
    for t in res_plain.trades:
        trade_log.append({
            "ticker": t.ticker, "kind": t.kind,
            "entry_date": t.entry_date.strftime("%Y-%m-%d"),
            "entry_price": round(t.entry_price, 2),
            "exit_date": t.exit_date.strftime("%Y-%m-%d") if t.exit_date else None,
            "exit_price": round(t.exit_price, 2) if t.exit_price else None,
            "exit_reason": t.exit_reason or "OPEN",
            "hold_days": (t.exit_date - t.entry_date).days if t.exit_date else None,
            "pnl_pct": round(t.pnl_pct, 4) if t.pnl_pct is not None else None,
            "is_open": t.is_open,
        })
    trade_log.sort(key=lambda x: x["entry_date"])

    # 3-way exit ablation (2026-07-20, PRE-1.618 exit shape — still valid,
    # independent of A7), reused from that prior run (no re-simulation
    # needed — same underlying data)
    ablation = pickle.load(open(f"{SCRATCH}/final_ablation_results.pkl", "rb"))
    exit_comparison = {}
    for v in ["simple_05", "simple_09", "latch_v2"]:
        d = ablation["exit_results"][(v, "combined (pre-vault)")]
        exit_comparison[v] = {
            "expectancy_pct": d["trade"]["expectancy_pct"],
            "total_return": d["dd"]["total_return"],
            "n_closed": d["trade"]["n_closed"],
            "win_rate": d["trade"]["win_rate"],
            "gap_trades": d["gap"]["n_gap_trades"],
            "gap_giveback": d["gap"]["total_giveback_dollars"],
        }

    # 2026-07-20 tiered-drawdown-gate run (EXPERIMENTAL — reopened
    # research, not yet adopted as the official gate). Optional: only
    # included if that run's pickle exists.
    tiered_section = None
    try:
        tiered = pickle.load(open(f"{SCRATCH}/tiered_results_full.pkl", "rb"))
        flat_fresh = pickle.load(open(f"{SCRATCH}/flat_baseline_fresh.pkl", "rb"))
        TR = tiered["results"]
        tcells = [f"{e}/{x}" for e, x in tiered["cells"]]
        pv_w, va_w = "combined (pre-vault)", "VAULT (last 12mo, tested once)"
        matrix = []
        for cl in tcells:
            d = TR[(cl, pv_w)]; t = d["trade"]; dd = d["dd"]
            vd = TR[(cl, va_w)]["trade"]
            matrix.append({
                "cell": cl, "total_return": dd["total_return"],
                "prevault_exp": t["expectancy_pct"], "prevault_n": t["n_closed"],
                "vault_exp": vd["expectancy_pct"], "vault_n": vd["n_closed"],
                "year_spread": TR[(cl, "FULL SPAN")]["year_spread"],
            })
        matrix.sort(key=lambda r: -(r["total_return"] or -9))
        tiered_section = {
            "matrix": matrix,
            "flat_baseline": {
                "prevault_n": flat_fresh[pv_w]["trade"]["n_closed"],
                "prevault_exp": flat_fresh[pv_w]["trade"]["expectancy_pct"],
                "prevault_ret": flat_fresh[pv_w]["dd"]["total_return"],
                "vault_n": flat_fresh[va_w]["trade"]["n_closed"],
                "vault_exp": flat_fresh[va_w]["trade"]["expectancy_pct"],
                "vault_ret": flat_fresh[va_w]["dd"]["total_return"],
            },
            "tiered_baseline_cell": {
                "prevault_n": TR[(tcells[0], pv_w)]["trade"]["n_closed"],
                "prevault_exp": TR[(tcells[0], pv_w)]["trade"]["expectancy_pct"],
                "prevault_ret": TR[(tcells[0], pv_w)]["dd"]["total_return"],
                "vault_n": TR[(tcells[0], va_w)]["trade"]["n_closed"],
                "vault_exp": TR[(tcells[0], va_w)]["trade"]["expectancy_pct"],
                "vault_ret": TR[(tcells[0], va_w)]["dd"]["total_return"],
            },
        }
        print("tiered section embedded:", len(matrix), "cells")
    except FileNotFoundError:
        print("no tiered results found, skipping that dashboard section")

    leap_correction = None
    try:
        leap_correction = json.load(open(f"{SCRATCH}/leap_correction.json"))
    except FileNotFoundError:
        pass

    data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "cell": f"{entry_tf}/{exit_tf}", "exit_variant": WINNING_VARIANT,
        "equity_sizing": WINNING_SIZING,
        "leap_pricing_label": "black_scholes_delta_curve",
        "leap_correction": leap_correction,
        "vault_start": vault_start.strftime("%Y-%m-%d"),
        "span": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
        "curves": _align_and_serialize_curves({
            "strategy": res_plain.equity_curve,
            "strategy_spy_idle_cash": res_spycash.equity_curve,
            "spy_buy_hold": spy_curve,
        }),
        "stats": stats,
        "spy_benchmark": spy_bm,
        "trade_log": trade_log,
        "exit_comparison": exit_comparison,
        "tiered_gate": tiered_section,
        "seed_cash": 100_000,
    }

    out_path = "reports/dashboard_data.json"
    json.dump(data, open(out_path, "w"), default=str)
    print("wrote", out_path)
    print("pre_vault stats:", stats["pre_vault"]["trade"]["n_closed"], "trades")
    print("vault stats:", stats["vault"]["trade"]["n_closed"], "trades")
    print("trade log:", len(trade_log), "total trades")


if __name__ == "__main__":
    main()
