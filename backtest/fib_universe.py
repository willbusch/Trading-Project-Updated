"""Full-universe runner for the latched-Fib strategy (CHANGE 1-4 applied).

Universe = data/universe_snapshot.json — a CURRENT-membership,
CURRENT-fundamentals proxy (see that file's `note`). This is NOT a
point-in-time SPY/QQQ backtest; the survivorship + fundamental-snapshot
biases all cut in the strategy's favor and are flagged verbatim in the
report header.

CHANGE 1: equity exit is the SIMPLE exit (no latch) — simple_exit=True.
CHANGE 2: hybrid anchor (use_hybrid=True).
CHANGE 3: quality gate = static membership in the scanned list (proxy).
CHANGE 4: third benchmark = strategy with idle cash earning SPY.
"""
import json
import time

import pandas as pd

from backtest.fib_features import build_fib_frame
from backtest.fib_reporting import (
    benchmark_spy,
    compute_the_gap,
    compute_trade_stats,
    exit_breakdown,
)
from backtest.fib_simulator import simulate_fib
from backtest.reporting import compute_drawdown_stats
from screener.data import fetch_daily_bars

FAR_PAST = pd.Timestamp("1900-01-01")
FAR_FUTURE = pd.Timestamp("2100-01-01")

# 3 best pre-vault cells from the 12-name round + daily/daily — the reduced
# set used if the full 7 is impractical at universe scale (FLAGGED in report).
REDUCED_CELLS = [("daily", "weekly"), ("3day", "weekly"),
                 ("weekly", "weekly"), ("daily", "daily")]
FULL_CELLS = [
    ("weekly", "weekly"), ("weekly", "3day"),
    ("3day", "3day"), ("3day", "weekly"),
    ("daily", "daily"), ("daily", "3day"), ("daily", "weekly"),
]


def load_universe(path="data/universe_snapshot.json"):
    u = json.load(open(path))
    return u["tickers"], frozenset(u["leap_tickers"]), u


def gate_of(ticker, leap_tickers):
    return 0.25 if ticker in leap_tickers else 0.40


def build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg):
    frames = {}
    for t in tickers:
        try:
            frames[t] = build_fib_frame(
                t, gate_of(t, leap_tickers), entry_tf, exit_tf, cfg, use_hybrid=True,
            )
        except Exception as e:                       # noqa: BLE001 - report coverage
            print(f"  SKIP {t}: {type(e).__name__} {e}")
    return frames


def deployment_pct(result) -> float:
    """Fraction of bars with any capital invested (1 - cash/equity > eps)."""
    invested = 1.0 - result.cash_curve / result.equity_curve
    return float((invested > 1e-6).mean())


def eligibility_over_time(frames) -> pd.Series:
    """Count of names clearing the gate on each date — the universe run's
    core question: is there ALWAYS something 40%-down + quality-screened?"""
    elig = pd.DataFrame({t: f["eligible"] for t, f in frames.items()})
    return elig.sum(axis=1)


def run_universe(cfg, cells=None, smoke_one=False):
    tickers, leap_tickers, meta = load_universe()
    cells = cells or FULL_CELLS
    if smoke_one:
        cells = [("daily", "weekly")]

    spy = fetch_daily_bars("SPY")["Close"]
    spy_ret = spy.pct_change()

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

    results, extension_stats, elig_stats = {}, {}, {}
    for entry_tf, exit_tf in cells:
        cl = f"{entry_tf}/{exit_tf}"
        t0 = time.time()
        frames = build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg)
        # anchor-extension frequency (CHANGE 2 report)
        ext = pd.DataFrame(
            {t: f["anchor_extended"] for t, f in frames.items()}
        ).fillna(False).astype(bool)          # ragged indices -> NaN -> False
        extension_stats[cl] = {
            "pct_bars_extended": float(ext.to_numpy().mean()),
            "names_ever_extended": int(ext.any().sum()),
        }
        elig_stats[cl] = eligibility_over_time(frames)
        for wlabel, win in windows.items():
            base = dict(cell=cl, window_label=wlabel, leap_tickers=leap_tickers,
                        simple_exit=True)  # CHANGE 1
            res = simulate_fib(frames, cfg, window=win,
                               seed_cash=cfg["backtest"]["seed_cash"], **base)
            res_spy = simulate_fib(frames, cfg, window=win,
                                   seed_cash=cfg["backtest"]["seed_cash"],
                                   idle_cash_spy=spy_ret, **base)  # CHANGE 4
            results[(cl, wlabel)] = {
                "trade": compute_trade_stats(res),
                "dd": compute_drawdown_stats(res.equity_curve),
                "dd_spycash": compute_drawdown_stats(res_spy.equity_curve),
                "exits": exit_breakdown(res),
                "gap": compute_the_gap(res),
                "deployment": deployment_pct(res),
                "result": res,
            }
        print(f"  cell {cl} done in {time.time()-t0:.1f}s")

    prevault_exp = {
        cl: results[(cl, "combined (pre-vault)")]["trade"]["expectancy_pct"]
        for cl in {f"{e}/{x}" for e, x in cells}
    }
    benchmarks = {
        "spy_prevault": benchmark_spy(cfg, start, vault_start),
        "spy_vault": benchmark_spy(cfg, vault_start, end),
    }
    return {
        "results": results, "windows": list(windows), "cells": cells,
        "prevault_exp": prevault_exp, "benchmarks": benchmarks,
        "extension_stats": extension_stats, "elig_stats": elig_stats,
        "span": (start, end), "vault_start": vault_start,
        "universe_meta": meta, "n_names": len(tickers),
    }
