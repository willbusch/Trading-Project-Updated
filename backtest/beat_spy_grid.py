"""2026-07-22 — "Beat-SPY Package": full Part A (A1-A8) + Part B 12-cell
grid (B1 entry timeframe x B2 equity sizing x B3 trailing mechanic) +
cumulative attribution ladder on the champion cell.

Exit timeframe is WEEKLY in every cell (owner-locked, not swept).
"""
import time
from collections import Counter

import pandas as pd

from backtest.fib_reporting import benchmark_spy, compute_trade_stats, exit_breakdown
from backtest.fib_simulator import simulate_fib
from backtest.fib_universe import build_universe_frames, deployment_pct, load_universe
from backtest.reporting import compute_drawdown_stats
from screener.data import fetch_daily_bars

FAR_PAST = pd.Timestamp("1900-01-01")
FAR_FUTURE = pd.Timestamp("2100-01-01")

B1_ENTRY_TFS = ["daily", "3day"]
B2_SIZING = ["diversify", "deepen", "both"]
B3_TRAILING = {"trail_ut": "ut_trail", "trail_pct20": "pct_trail_20", "trail_pct15": "pct_trail_15"}
B3_DEFAULT_PAIR = ["trail_ut", "trail_pct20"]   # the mandatory 2; pct15 run only if cheap

PART_A_ON = dict(
    leap_topcap_eligibility=True,   # A2
    leap_decay_exit=True,           # A5
    slot_recycling=True,            # A4
)


def year_spread(trades) -> dict:
    return dict(sorted(Counter(t.entry_date.year for t in trades).items()))


def _windows(cfg, vault_start):
    return {
        "combined (pre-vault)": (FAR_PAST, vault_start),
        "VAULT (last 12mo, tested once)": (vault_start, FAR_FUTURE),
    }


def build_frames_for_entry_tf(tickers, leap_tickers, entry_tf, cfg, market_caps):
    t0 = time.time()
    frames = build_universe_frames(
        tickers, leap_tickers, entry_tf, "weekly", cfg,
        market_caps=market_caps, add_topcap_column=True,
    )
    print(f"  frames[{entry_tf}/weekly] built in {time.time()-t0:.1f}s "
         f"({len(frames)} names)")
    return frames


def run_one(frames, cfg, entry_tf, sizing_variant, trailing_variant, leap_tickers,
           spy_ret, windows, part_a_on=True, extra_flags=None, cell_label=None):
    """One (cell, window) sweep. extra_flags/cfg overrides let the
    attribution ladder toggle individual A2-A7 features independently."""
    flags = dict(PART_A_ON) if part_a_on else dict(
        leap_topcap_eligibility=False, leap_decay_exit=False, slot_recycling=False)
    if extra_flags:
        flags.update(extra_flags)
    label = cell_label or f"{entry_tf}/weekly | {sizing_variant} | {trailing_variant}"
    out = {}
    for wlabel, win in windows.items():
        res = simulate_fib(
            frames, cfg, window=win, seed_cash=cfg["backtest"]["seed_cash"],
            cell=label, window_label=wlabel, leap_tickers=leap_tickers,
            exit_variant=trailing_variant, idle_cash_spy=spy_ret,
            equity_sizing_variant=sizing_variant, **flags,
        )
        out[wlabel] = {
            "trade": compute_trade_stats(res), "dd": compute_drawdown_stats(res.equity_curve),
            "deployment": deployment_pct(res), "exits": exit_breakdown(res),
            "n_recycle": len(res.recycle_events), "recycle_events": res.recycle_events,
            "year_spread": year_spread(res.closed_trades), "result": res,
        }
    return out


def run_grid(cfg, entry_tfs=None, sizing_variants=None, trailing_variants=None, verbose=True):
    entry_tfs = entry_tfs or B1_ENTRY_TFS
    sizing_variants = sizing_variants or B2_SIZING
    trailing_variants = trailing_variants or B3_DEFAULT_PAIR

    tickers, leap_tickers, meta = load_universe()
    market_caps = meta["market_caps"]
    spy = fetch_daily_bars("SPY")["Close"]
    spy_ret = spy.pct_change()

    end = max(fetch_daily_bars(t).index.max() for t in tickers[:5])
    start = pd.Timestamp("2018-01-02")
    vault_start = end - pd.DateOffset(months=12)
    windows = _windows(cfg, vault_start)

    frames_by_tf = {}
    for entry_tf in entry_tfs:
        frames_by_tf[entry_tf] = build_frames_for_entry_tf(
            tickers, leap_tickers, entry_tf, cfg, market_caps)

    grid_results = {}
    for entry_tf in entry_tfs:
        frames = frames_by_tf[entry_tf]
        for sizing in sizing_variants:
            for trailing in trailing_variants:
                t0 = time.time()
                cell_key = (entry_tf, sizing, trailing)
                grid_results[cell_key] = run_one(
                    frames, cfg, entry_tf, sizing, trailing, leap_tickers,
                    spy_ret, windows, part_a_on=True,
                )
                if verbose:
                    pv = grid_results[cell_key]["combined (pre-vault)"]
                    print(f"  cell {cell_key}: {pv['trade']['n_closed']} trades, "
                         f"ret={pv['dd']['total_return']:.1%}, "
                         f"maxDD={pv['dd']['max_drawdown']:.1%}  ({time.time()-t0:.1f}s)")

    benchmarks = {
        "spy_prevault": benchmark_spy(cfg, start, vault_start),
        "spy_vault": benchmark_spy(cfg, vault_start, end),
    }
    return {
        "grid_results": grid_results, "entry_tfs": entry_tfs,
        "sizing_variants": sizing_variants, "trailing_variants": trailing_variants,
        "benchmarks": benchmarks, "span": (start, end), "vault_start": vault_start,
        "n_names": len(tickers), "frames_by_tf": frames_by_tf,
        "leap_tickers": leap_tickers, "market_caps": market_caps, "spy_ret": spy_ret,
    }


def run_attribution_ladder(cfg, champion_entry_tf, champion_sizing, champion_trailing,
                           frames, leap_tickers, spy_ret, windows, verbose=True):
    """baseline -> +A2 -> +A3 -> +A4 -> +A5 -> +A6 -> +A7, on the CHAMPION
    cell's B1 (entry timeframe) and B2 (equity sizing) held constant
    throughout (B1/B2 are not A2-A7 toggles). B3 (trailing mechanic) only
    takes effect once A7 is switched on in the final step — before that,
    exit_variant is pinned to "simple_09" (the pre-A7 hard 1.618 exit),
    matching what every prior run before this one actually used."""
    cfg_wall = dict(cfg)
    cfg_wall["leap"] = {**cfg["leap"], "reserve_spendable": False}
    cfg_wall["circuit_breakers"] = {**cfg["circuit_breakers"], "leap_only_halt": False}

    cfg_a3 = dict(cfg)   # reserve_spendable True (cfg default), leap_only_halt still off
    cfg_a3["circuit_breakers"] = {**cfg["circuit_breakers"], "leap_only_halt": False}

    steps = [
        ("baseline", cfg_wall, dict(leap_topcap_eligibility=False, leap_decay_exit=False,
                                    slot_recycling=False), "simple_09", None),
        ("+A2 (top10-cap LEAP eligibility)", cfg_wall,
         dict(leap_topcap_eligibility=True, leap_decay_exit=False, slot_recycling=False),
         "simple_09", None),
        ("+A3 (reserve spendable + SPY idle-cash)", cfg_a3,
         dict(leap_topcap_eligibility=True, leap_decay_exit=False, slot_recycling=False),
         "simple_09", spy_ret),
        ("+A4 (slot recycling valve)", cfg_a3,
         dict(leap_topcap_eligibility=True, leap_decay_exit=False, slot_recycling=True),
         "simple_09", spy_ret),
        ("+A5 (LEAP decay-aware exit)", cfg_a3,
         dict(leap_topcap_eligibility=True, leap_decay_exit=True, slot_recycling=True),
         "simple_09", spy_ret),
        ("+A6 (kill switch LEAP-only)", cfg,
         dict(leap_topcap_eligibility=True, leap_decay_exit=True, slot_recycling=True),
         "simple_09", spy_ret),
        ("+A7 (trailing exit, full package)", cfg,
         dict(leap_topcap_eligibility=True, leap_decay_exit=True, slot_recycling=True),
         champion_trailing, spy_ret),
    ]

    ladder = {}
    for name, step_cfg, flags, exit_variant, idle_spy in steps:
        t0 = time.time()
        out = {}
        for wlabel, win in windows.items():
            res = simulate_fib(
                frames, step_cfg, window=win, seed_cash=step_cfg["backtest"]["seed_cash"],
                cell=f"attribution:{name}", window_label=wlabel, leap_tickers=leap_tickers,
                exit_variant=exit_variant, idle_cash_spy=idle_spy,
                equity_sizing_variant=champion_sizing, **flags,
            )
            out[wlabel] = {
                "trade": compute_trade_stats(res), "dd": compute_drawdown_stats(res.equity_curve),
                "deployment": deployment_pct(res), "n_recycle": len(res.recycle_events),
                "result": res,
            }
        ladder[name] = out
        if verbose:
            pv = out["combined (pre-vault)"]
            print(f"  {name}: ret={pv['dd']['total_return']:.1%}, "
                 f"maxDD={pv['dd']['max_drawdown']:.1%}, "
                 f"trades={pv['trade']['n_closed']}  ({time.time()-t0:.1f}s)")
    return ladder
