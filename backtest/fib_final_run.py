"""2026-07-21 — the locked, adopted configuration: daily/weekly cell (the
ONLY cell run — locked per owner decision), tiered drawdown gate (now
official, not experimental), ratio-based slot tiebreak, real Black-Scholes
LEAP pricing, and the new sizing (4 equity slots, 33% dedicated LEAP
reserve, 0.55-0.65 delta). This is what STRATEGY.md documents as current.
"""
import time
from collections import Counter

import pandas as pd

from backtest.fib_reporting import (
    benchmark_spy,
    compute_the_gap,
    compute_trade_stats,
    exit_breakdown,
)
from backtest.fib_simulator import simulate_fib
from backtest.fib_universe import build_universe_frames, deployment_pct, load_universe
from backtest.reporting import compute_drawdown_stats
from screener.data import fetch_daily_bars

FAR_PAST = pd.Timestamp("1900-01-01")
FAR_FUTURE = pd.Timestamp("2100-01-01")
CELL = ("daily", "weekly")
EXIT_VARIANT = "simple_09"


def year_spread(trades) -> dict:
    return dict(sorted(Counter(t.entry_date.year for t in trades).items()))


def run_final(cfg):
    tickers, leap_tickers, meta = load_universe()
    market_caps = meta["market_caps"]
    entry_tf, exit_tf = CELL

    t0 = time.time()
    frames = build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg,
                                   market_caps=market_caps)
    print(f"frames built in {time.time()-t0:.1f}s")

    end = max(fetch_daily_bars(t).index.max() for t in tickers[:5])
    start = pd.Timestamp("2018-01-02")
    vault_start = end - pd.DateOffset(months=12)
    boundary = pd.Timestamp(cfg["backtest"]["split_half_boundary"])
    windows = {
        "combined (pre-vault)": (FAR_PAST, vault_start),
        f"half-1 (→ {boundary.date()})": (FAR_PAST, boundary),
        f"half-2 ({boundary.date()} → vault)": (boundary, vault_start),
        "VAULT (last 12mo, tested once)": (vault_start, FAR_FUTURE),
    }

    results = {}
    for wlabel, win in windows.items():
        t0 = time.time()
        res = simulate_fib(frames, cfg, window=win, seed_cash=cfg["backtest"]["seed_cash"],
                           cell=f"{entry_tf}/{exit_tf}", window_label=wlabel,
                           leap_tickers=leap_tickers, exit_variant=EXIT_VARIANT)
        results[wlabel] = {
            "trade": compute_trade_stats(res), "dd": compute_drawdown_stats(res.equity_curve),
            "deployment": deployment_pct(res), "gap": compute_the_gap(res),
            "exits": exit_breakdown(res), "year_spread": year_spread(res.closed_trades),
            "result": res,
        }
        print(f"  {wlabel}: {results[wlabel]['trade']['n_closed']} trades in {time.time()-t0:.1f}s")

    # full-span, unsliced, for the trade log / year-spread / mega-cap-wins check
    t0 = time.time()
    res_full = simulate_fib(frames, cfg, seed_cash=cfg["backtest"]["seed_cash"],
                            cell=f"{entry_tf}/{exit_tf}", window_label="full",
                            leap_tickers=leap_tickers, exit_variant=EXIT_VARIANT)
    results["FULL SPAN"] = {
        "trade": compute_trade_stats(res_full), "dd": compute_drawdown_stats(res_full.equity_curve),
        "deployment": deployment_pct(res_full), "year_spread": year_spread(res_full.closed_trades),
        "result": res_full,
    }
    print(f"  FULL SPAN: {results['FULL SPAN']['trade']['n_closed']} trades in {time.time()-t0:.1f}s")

    benchmarks = {
        "spy_prevault": benchmark_spy(cfg, start, vault_start),
        "spy_vault": benchmark_spy(cfg, vault_start, end),
    }
    return {
        "results": results, "windows": list(windows) + ["FULL SPAN"],
        "benchmarks": benchmarks, "span": (start, end), "vault_start": vault_start,
        "n_names": len(tickers),
    }
