"""Top-level comparison runner. Windows, sweeps, the single vault
validation, and ablations are all just different inputs to the same
simulate() call — no engine logic lives here.

Methodology (locked decisions):
  - Feature frames are built ONCE per ticker on full history; windows are
    slices. The UT sweep is the one exception that rebuilds frames (UT
    params change the path-dependent trailing stop), still full-history.
  - Sweeps run on PRE-VAULT data only. The vault (most recent
    backtest.vault_months) is touched exactly once, with final parameters.
  - Sweep selection optimizes the 3x3 (or 1-D ±1) NEIGHBORHOOD average
    expectancy, requiring the chosen cell's own expectancy to sit within
    20% of its neighborhood average — the stable plateau, not the peak.
  - MSFT is the only LEAP candidate (NFLX fails LEAP eligibility and
    tests on the equity path — established owner decision). The
    include_leap=False ablation prices MSFT as plain equity instead.
"""
import numpy as np
import pandas as pd

from backtest.features import build_feature_frame
from backtest.leap_pricing import PRICING_LABEL, leap_delta
from backtest.reporting import (
    compute_arm_extras,
    compute_benchmark_stats,
    compute_drawdown_stats,
    compute_trade_stats,
    compute_utilization_stats,
)
from backtest.signals import AblationConfig, build_signal_frame
from backtest.simulator import simulate

STRATEGIES = ["A", "B", "C", "D"]
FAR_PAST = pd.Timestamp("1900-01-01")
FAR_FUTURE = pd.Timestamp("2100-01-01")


def expectancy_of(result):
    closed = result.closed_trades
    return (sum(t.pnl_pct for t in closed) / len(closed)) if closed else None


def _run(
    frames, strategy, cfg, window, ablation=None, volume_multiplier=None, label=""
):
    ablation = ablation or AblationConfig()
    sf = {
        t: build_signal_frame(f, strategy, cfg, ablation, volume_multiplier)
        for t, f in frames.items()
    }
    leaps = frozenset({"MSFT"}) if ablation.include_leap else frozenset()
    res = simulate(
        sf, cfg, ablation, window=window,
        seed_cash=cfg["backtest"]["seed_cash"],
        strategy=strategy, window_label=label, leap_tickers=leaps,
    )
    return res, sf


def sweep_ut(tickers, cfg, prevault_window):
    """Grid over (key_value, atr_period), scored by Strategy B pre-vault
    expectancy. Returns (chosen_key, chosen_atr, grid_rows, note)."""
    ut = cfg["ut_bot"]
    keys = list(
        np.arange(ut["key_value_sweep_min"], ut["key_value_sweep_max"] + 1e-9,
                  ut["key_value_sweep_step"])
    )
    atrs = list(
        range(ut["atr_period_sweep_min"], ut["atr_period_sweep_max"] + 1,
              ut["atr_period_sweep_step"])
    )
    exp = {}
    n_trades = {}
    for k in keys:
        for a in atrs:
            frames = {
                t: build_feature_frame(t, cfg, ut_key_value=k, ut_atr_period=a)
                for t in tickers
            }
            res, _ = _run(frames, "B", cfg, prevault_window, label="sweep")
            exp[(k, a)] = expectancy_of(res)
            n_trades[(k, a)] = len(res.closed_trades)

    best, best_nbhd = None, -np.inf
    flagged = None
    for (k, a), e in exp.items():
        if e is None:
            continue
        nbhd = [
            exp.get((k + dk, a + da))
            for dk in (-ut["key_value_sweep_step"], 0, ut["key_value_sweep_step"])
            for da in (-ut["atr_period_sweep_step"], 0, ut["atr_period_sweep_step"])
        ]
        nbhd = [x for x in nbhd if x is not None]
        m = sum(nbhd) / len(nbhd)
        stable = abs(e - m) <= 0.2 * abs(m) if m != 0 else True
        if m > best_nbhd and stable:
            best_nbhd, best = m, (k, a)
        if m > best_nbhd and not stable and best is None:
            flagged = (k, a)
    note = ""
    if best is None:
        best = flagged or max(
            (kv for kv, e in exp.items() if e is not None),
            key=lambda kv: exp[kv],
        )
        note = (
            "WARNING: no grid cell satisfied the 20%-of-neighborhood "
            "stability requirement; fell back to the best available cell — "
            "treat the chosen UT parameters as UNSTABLE."
        )
    rows = [
        {"key_value": k, "atr_period": a, "expectancy": exp[(k, a)],
         "n_trades": n_trades[(k, a)]}
        for (k, a) in sorted(exp)
    ]
    return best[0], best[1], rows, note


def sweep_volume_multiplier(frames, cfg, prevault_window):
    """1-D sweep for Strategy D's multiplier, ±1-cell neighborhood, same
    stability rule. NOTE: the sweep RANGE is an ASSUMED-NOT-CONFIRMED
    reconstruction default (Addendum 1 never arrived) — see config.yaml."""
    sd = cfg["strategy_d"]
    mults = list(
        np.arange(sd["volume_multiplier_sweep_min"],
                  sd["volume_multiplier_sweep_max"] + 1e-9,
                  sd["volume_multiplier_sweep_step"])
    )
    exp, n_trades = {}, {}
    for m in mults:
        res, _ = _run(frames, "D", cfg, prevault_window,
                      volume_multiplier=m, label="sweep")
        exp[m] = expectancy_of(res)
        n_trades[m] = len(res.closed_trades)

    best, best_nbhd = None, -np.inf
    for i, m in enumerate(mults):
        if exp[m] is None:
            continue
        nbhd = [exp[x] for x in mults[max(0, i - 1): i + 2] if exp[x] is not None]
        avg = sum(nbhd) / len(nbhd)
        stable = abs(exp[m] - avg) <= 0.2 * abs(avg) if avg != 0 else True
        if avg > best_nbhd and stable:
            best_nbhd, best = avg, m
    note = ""
    if best is None:
        candidates = [m for m in mults if exp[m] is not None]
        best = max(candidates, key=lambda m: exp[m]) if candidates else sd["volume_multiplier"]
        note = "WARNING: volume sweep had no stable cell; fell back to best/default."
    rows = [
        {"multiplier": m, "expectancy": exp[m], "n_trades": n_trades[m]}
        for m in mults
    ]
    return best, rows, note


def run_comparison(tickers, cfg):
    frames = {t: build_feature_frame(t, cfg) for t in tickers}

    end = max(f.index.max() for f in frames.values())
    start = min(f.index.min() for f in frames.values())
    vault_start = end - pd.DateOffset(months=cfg["backtest"]["vault_months"])
    boundary = pd.Timestamp(cfg["backtest"]["split_half_boundary"])

    windows = {
        "combined (pre-vault)": (FAR_PAST, vault_start),
        f"half 1 ({start.date()} → {boundary.date()})": (FAR_PAST, boundary),
        f"half 2 ({boundary.date()} → {vault_start.date()})": (boundary, vault_start),
    }
    prevault = (FAR_PAST, vault_start)

    # ---- sweeps: pre-vault ONLY ---------------------------------------
    ut_key, ut_atr, ut_grid, ut_note = sweep_ut(tickers, cfg, prevault)
    vol_mult, vol_grid, vol_note = sweep_volume_multiplier(frames, cfg, prevault)

    # final frames: chosen UT params (affects B's and C's triggers)
    final_frames = {
        t: build_feature_frame(t, cfg, ut_key_value=ut_key, ut_atr_period=ut_atr)
        for t in tickers
    }

    # ---- main windows + the ONE vault validation ----------------------
    per_window = {}
    all_windows = dict(windows)
    all_windows[f"VAULT (final {cfg['backtest']['vault_months']}mo, tested once)"] = (
        vault_start, FAR_FUTURE
    )
    for label, win in all_windows.items():
        per_window[label] = {}
        for strat in STRATEGIES:
            res, sf = _run(
                final_frames, strat, cfg, win,
                volume_multiplier=vol_mult if strat == "D" else None, label=label,
            )
            entry = {
                "trade": compute_trade_stats(res),
                "dd": compute_drawdown_stats(res.equity_curve),
                "util": compute_utilization_stats(res),
                "leap_label": (
                    f"MSFT: {PRICING_LABEL} (static delta {leap_delta(cfg):.2f})"
                ),
                "result": res,
            }
            if strat in ("C", "D"):
                entry["extras"] = compute_arm_extras(sf, window=win)
            per_window[label][strat] = entry

    # ---- ablations: combined pre-vault, every strategy ----------------
    ablations = {
        "baseline": AblationConfig(),
        "ladder_enabled": AblationConfig(ladder_enabled=True),
        "rsi_70_60_exit": AblationConfig(rsi_70_60_exit_enabled=True),
        "no_leap (MSFT as equity)": AblationConfig(include_leap=False),
    }
    ablation_results = {}
    for ab_label, ab in ablations.items():
        for strat in STRATEGIES:
            res, _ = _run(
                final_frames, strat, cfg, prevault, ablation=ab,
                volume_multiplier=vol_mult if strat == "D" else None,
                label=f"ablation:{ab_label}",
            )
            ablation_results[(ab_label, strat)] = {
                "expectancy": expectancy_of(res),
                "n_closed": len(res.closed_trades),
                "total_return": compute_drawdown_stats(res.equity_curve)["total_return"],
            }

    benchmark = compute_benchmark_stats(cfg, start, vault_start)

    return {
        "per_window": per_window,
        "ablation_results": ablation_results,
        "benchmark": benchmark,
        "ut_sweep": {"chosen": (ut_key, ut_atr), "grid": ut_grid, "note": ut_note},
        "vol_sweep": {"chosen": vol_mult, "grid": vol_grid, "note": vol_note},
        "vault_start": vault_start,
        "span": (start, end),
    }
