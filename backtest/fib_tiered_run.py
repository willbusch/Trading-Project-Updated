"""2026-07-20 tiered-drawdown-gate run — REOPENS the formally-closed
research phase. Finding that drove this: the flat 40%/25% gate only ever
fired in the 2020 COVID crash (every backtest winner traced to a Feb-Mar
2020 entry), because a flat 40% threshold structurally locks out mega-caps
outside a crash. Owner's fix: scale the required drawdown to market-cap
tier so mega-caps qualify on ordinary pullbacks, not just once-a-decade
crashes. See backtest.fib_universe.gate_of_tiered for the tiers and the
current-market-cap-proxy data-limitation flag.

3 cells run first (daily/weekly baseline, 3day/weekly, weekly/weekly) —
same reduced-set precedent as the original universe run, flagged if it
stays at 3 rather than expanding to 6. Quality gate, LEAP kind assignment,
exit (simple_09), sizing, and vault discipline are all UNCHANGED from the
flat-gate run — the tiered gate is the only variable.
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
EXIT_VARIANT = "simple_09"

CELLS_REDUCED = [("daily", "weekly"), ("3day", "weekly"), ("weekly", "weekly")]
CELLS_FULL = CELLS_REDUCED + [("daily", "3day"), ("3day", "3day"), ("weekly", "3day")]


def year_spread(trades) -> dict:
    return dict(sorted(Counter(t.entry_date.year for t in trades).items()))


def run_tiered(cfg, cells=None):
    cells = cells or CELLS_REDUCED
    tickers, leap_tickers, meta = load_universe()
    market_caps = meta["market_caps"]

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
    for entry_tf, exit_tf in cells:
        cl = f"{entry_tf}/{exit_tf}"
        t0 = time.time()
        frames = build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg,
                                       market_caps=market_caps)
        for wlabel, win in windows.items():
            res = simulate_fib(frames, cfg, window=win,
                               seed_cash=cfg["backtest"]["seed_cash"],
                               cell=cl, window_label=wlabel,
                               leap_tickers=leap_tickers, exit_variant=EXIT_VARIANT)
            results[(cl, wlabel)] = {
                "trade": compute_trade_stats(res),
                "dd": compute_drawdown_stats(res.equity_curve),
                "exits": exit_breakdown(res),
                "gap": compute_the_gap(res),
                "deployment": deployment_pct(res),
                "year_spread": year_spread(res.closed_trades),
            }
        # full-span (unsliced) year-spread + deployment, for the "where do
        # trades cluster" question independent of window boundaries
        res_full = simulate_fib(frames, cfg, seed_cash=cfg["backtest"]["seed_cash"],
                                cell=cl, window_label="full",
                                leap_tickers=leap_tickers, exit_variant=EXIT_VARIANT)
        results[(cl, "FULL SPAN")] = {
            "trade": compute_trade_stats(res_full),
            "dd": compute_drawdown_stats(res_full.equity_curve),
            "deployment": deployment_pct(res_full),
            "year_spread": year_spread(res_full.closed_trades),
        }
        print(f"  cell {cl} done in {time.time()-t0:.1f}s")

    benchmarks = {
        "spy_prevault": benchmark_spy(cfg, start, vault_start),
        "spy_vault": benchmark_spy(cfg, vault_start, end),
    }
    return {
        "results": results, "cells": cells,
        "windows": list(windows) + ["FULL SPAN"],
        "benchmarks": benchmarks, "span": (start, end), "vault_start": vault_start,
    }
