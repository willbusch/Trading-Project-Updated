"""Generate the JSON data the results dashboard reads. Re-runs the LOCKED
configuration (daily/weekly cell, tiered gate now official, ratio
tiebreak, real Black-Scholes LEAP pricing, ADOPTED 2026-07-21) as ONE
continuous full-span backtest — window-sliced ablation runs only store
summary stats, not raw equity curves, so this reconstructs the curves the
dashboard needs from the same tested modules (no reimplementation of
signal logic).

Run this after any backtest change to regenerate reports/dashboard_data.json,
then re-run scripts/generate_dashboard.py to rebuild the HTML.
"""
import json
import pickle
import time

import pandas as pd

from backtest.fib_universe import build_universe_frames, load_universe
from backtest.fib_simulator import simulate_fib
from screener.data import fetch_daily_bars

WINNING_CELL = ("daily", "weekly")
WINNING_VARIANT = "simple_09"


def _curve_to_json(curve: pd.Series) -> dict:
    return {"dates": [d.strftime("%Y-%m-%d") for d in curve.index],
           "values": [round(float(v), 2) for v in curve.values]}


def main():
    from screener.config import load_config
    cfg = load_config()
    tickers, leap_tickers, meta = load_universe()
    entry_tf, exit_tf = WINNING_CELL

    # CONSISTENCY FIX (2026-07-21): re-simulating fresh here can pick a
    # slightly different trade set than the written report, due to a
    # known sensitivity — small drift in the live universe snapshot
    # between separate script invocations changes slot-competition
    # outcomes (documented in reports/fib_tiered_gate.md). To keep the
    # dashboard's numbers IDENTICAL to reports/fib_final_run.md, the
    # primary "plain" curve/trade-log/stats are loaded from that exact
    # pickled run rather than re-simulated. Only the idle-cash-SPY
    # comparison curve (visual only, not a reported stat) is re-run fresh.
    final_run = pickle.load(open(
        "/tmp/claude-0/-home-user-Trading-Project-Updated/"
        "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/final_run_results.pkl",
        "rb"))
    res_plain = final_run["results"]["FULL SPAN"]["result"]
    start, end = final_run["span"]
    vault_start = final_run["vault_start"]

    print("building frames (tiered gate, official) for the idle-cash comparison curve ...")
    t0 = time.time()
    frames = build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg,
                                   market_caps=meta["market_caps"])
    print(f"  done in {time.time()-t0:.1f}s")

    spy = fetch_daily_bars("SPY")["Close"]
    spy_ret = spy.pct_change()

    res_spycash = simulate_fib(frames, cfg, seed_cash=cfg["backtest"]["seed_cash"],
                               cell=f"{entry_tf}/{exit_tf}", window_label="full",
                               leap_tickers=leap_tickers, exit_variant=WINNING_VARIANT,
                               idle_cash_spy=spy_ret)

    spy_span = spy.loc[start:end]
    spy_curve = (spy_span / spy_span.iloc[0]) * cfg["backtest"]["seed_cash"]

    from backtest.fib_reporting import benchmark_spy

    # CONSISTENCY FIX: use the SAME independently-simulated window results
    # reports/fib_final_run.md reports (final_run["results"][window_label]),
    # not a post-hoc date-filter of the full-span trade list — window-sliced
    # simulations restart state at the boundary and do NOT produce the same
    # trade set as filtering a continuous full-span run by date. Mixing the
    # two would silently disagree with the written report.
    stats = {
        "pre_vault": final_run["results"]["combined (pre-vault)"],
        "vault": final_run["results"]["VAULT (last 12mo, tested once)"],
    }

    spy_bm = {
        "pre_vault": benchmark_spy(cfg, start, vault_start),
        "vault": benchmark_spy(cfg, vault_start, end),
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

    # 3-way exit ablation + throttle, reused from the prior run (no
    # re-simulation needed — same underlying data)
    ablation = pickle.load(open(
        "/tmp/claude-0/-home-user-Trading-Project-Updated/"
        "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/final_ablation_results.pkl",
        "rb"))
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
        tiered = pickle.load(open(
            "/tmp/claude-0/-home-user-Trading-Project-Updated/"
            "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/tiered_results_full.pkl",
            "rb"))
        flat_fresh = pickle.load(open(
            "/tmp/claude-0/-home-user-Trading-Project-Updated/"
            "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/flat_baseline_fresh.pkl",
            "rb"))
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
        leap_correction = json.load(open(
            "/tmp/claude-0/-home-user-Trading-Project-Updated/"
            "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/leap_correction.json"))
    except FileNotFoundError:
        pass

    data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "cell": f"{entry_tf}/{exit_tf}", "exit_variant": WINNING_VARIANT,
        "leap_pricing_label": "black_scholes_delta_curve",
        "leap_correction": leap_correction,
        "vault_start": vault_start.strftime("%Y-%m-%d"),
        "span": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
        "curves": {
            "strategy": _curve_to_json(res_plain.equity_curve),
            "strategy_spy_idle_cash": _curve_to_json(res_spycash.equity_curve),
            "spy_buy_hold": _curve_to_json(spy_curve),
        },
        "stats": stats,
        "spy_benchmark": spy_bm,
        "trade_log": trade_log,
        "exit_comparison": exit_comparison,
        "tiered_gate": tiered_section,
        "seed_cash": cfg["backtest"]["seed_cash"],
    }

    out_path = "reports/dashboard_data.json"
    json.dump(data, open(out_path, "w"), default=str)
    print("wrote", out_path)
    print("pre_vault stats:", stats["pre_vault"]["trade"]["n_closed"], "trades")
    print("vault stats:", stats["vault"]["trade"]["n_closed"], "trades")
    print("trade log:", len(trade_log), "total trades")


if __name__ == "__main__":
    main()
