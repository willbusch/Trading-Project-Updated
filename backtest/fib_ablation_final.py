"""2026-07-20 FINAL structural ablation — the last research pass before
the phase closes (see docs/PLAN.md "RESEARCH PHASE CLOSED").

Two ablations, both on the universe winning cell (daily/weekly):
  1. Three-way EQUITY exit variant: simple_05 (champion) vs simple_09
     (owner's earlier idea) vs latch_v2 (owner's new full-latch design).
  2. Deployment throttle: baseline (5 equity slots / 2 new positions per
     week) vs loosened (6 equity slots / 3 per week).

VAULT DISCIPLINE (judgment call, documented — see the chat handoff):
re-scoring the SAME held-out 12-month vault across 5 candidate variants
would mean peeking it five times, which defeats "tested once." Selection
between variants is done on PRE-VAULT (combined) expectancy ONLY. Vault
performance is still computed and reported for every variant, transparently,
but never used to pick a winner — preserving the vault's integrity as
closely as possible given the ask.

No parameter sweeps — five named structural variants only, per guardrail.
"""
import copy
import time

import pandas as pd

from backtest.fib_reporting import (
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
WINNING_CELL = ("daily", "weekly")

EXIT_VARIANTS = ["simple_05", "simple_09", "latch_v2"]


def _windows(cfg, end, vault_start):
    boundary = pd.Timestamp(cfg["backtest"]["split_half_boundary"])
    return {
        "combined (pre-vault)": (FAR_PAST, vault_start),
        f"half-1 (→ {boundary.date()})": (FAR_PAST, boundary),
        f"half-2 ({boundary.date()} → vault)": (boundary, vault_start),
        "VAULT (last 12mo, tested once)": (vault_start, FAR_FUTURE),
    }


def run_final_ablation(cfg):
    tickers, leap_tickers, meta = load_universe()
    entry_tf, exit_tf = WINNING_CELL
    print(f"building frames for winning cell {entry_tf}/{exit_tf} ...")
    t0 = time.time()
    frames = build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg)
    print(f"  frames built in {time.time()-t0:.1f}s")

    end = max(fetch_daily_bars(t).index.max() for t in tickers[:5])
    start = pd.Timestamp("2018-01-02")
    vault_start = end - pd.DateOffset(months=12)
    windows = _windows(cfg, end, vault_start)

    spy = fetch_daily_bars("SPY")["Close"]
    spy_ret = spy.pct_change()

    # ---- Ablation 1: three-way equity exit variant ---------------------
    exit_results = {}
    for variant in EXIT_VARIANTS:
        t0 = time.time()
        for wlabel, win in windows.items():
            res = simulate_fib(frames, cfg, window=win,
                               seed_cash=cfg["backtest"]["seed_cash"],
                               cell=f"{entry_tf}/{exit_tf}", window_label=wlabel,
                               leap_tickers=leap_tickers, exit_variant=variant)
            res_spy = simulate_fib(frames, cfg, window=win,
                                   seed_cash=cfg["backtest"]["seed_cash"],
                                   cell=f"{entry_tf}/{exit_tf}", window_label=wlabel,
                                   leap_tickers=leap_tickers, exit_variant=variant,
                                   idle_cash_spy=spy_ret)
            exit_results[(variant, wlabel)] = {
                "trade": compute_trade_stats(res),
                "dd": compute_drawdown_stats(res.equity_curve),
                "dd_spycash": compute_drawdown_stats(res_spy.equity_curve),
                "exits": exit_breakdown(res),
                "gap": compute_the_gap(res),
                "deployment": deployment_pct(res),
            }
        print(f"  exit variant {variant} done in {time.time()-t0:.1f}s")

    prevault_exp = {
        v: exit_results[(v, "combined (pre-vault)")]["trade"]["expectancy_pct"]
        for v in EXIT_VARIANTS
    }
    winning_variant = max(
        (v for v in EXIT_VARIANTS if prevault_exp[v] is not None),
        key=lambda v: prevault_exp[v], default=EXIT_VARIANTS[0],
    )

    # ---- Ablation 2: deployment throttle -------------------------------
    cfg_loose = copy.deepcopy(cfg)
    cfg_loose["sizing"]["equity_slots"] = 6
    cfg_loose["circuit_breakers"]["max_new_positions_per_week"] = 3

    throttle_results = {}
    for label, tcfg in [("baseline (5 slots / 2 per wk)", cfg),
                        ("loosened (6 slots / 3 per wk)", cfg_loose)]:
        t0 = time.time()
        for wlabel, win in windows.items():
            res = simulate_fib(frames, tcfg, window=win,
                               seed_cash=tcfg["backtest"]["seed_cash"],
                               cell=f"{entry_tf}/{exit_tf}", window_label=wlabel,
                               leap_tickers=leap_tickers, exit_variant=winning_variant)
            res_spy = simulate_fib(frames, tcfg, window=win,
                                   seed_cash=tcfg["backtest"]["seed_cash"],
                                   cell=f"{entry_tf}/{exit_tf}", window_label=wlabel,
                                   leap_tickers=leap_tickers, exit_variant=winning_variant,
                                   idle_cash_spy=spy_ret)
            throttle_results[(label, wlabel)] = {
                "trade": compute_trade_stats(res),
                "dd": compute_drawdown_stats(res.equity_curve),
                "dd_spycash": compute_drawdown_stats(res_spy.equity_curve),
                "deployment": deployment_pct(res),
            }
        print(f"  throttle {label} done in {time.time()-t0:.1f}s")

    from backtest.fib_reporting import benchmark_spy
    benchmarks = {
        "spy_prevault": benchmark_spy(cfg, start, vault_start),
        "spy_vault": benchmark_spy(cfg, vault_start, end),
    }

    return {
        "exit_results": exit_results,
        "prevault_exp": prevault_exp,
        "winning_variant": winning_variant,
        "throttle_results": throttle_results,
        "windows": list(windows),
        "benchmarks": benchmarks,
        "span": (start, end),
        "vault_start": vault_start,
        "n_names": len(tickers),
    }
