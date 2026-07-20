"""Latched-Fib strategy runner: the 7-cell timeframe matrix across
combined / split-half / vault windows, both benchmarks, The Gap, and the
latched-vs-simple ablation on the best pre-vault cell. Vault touched once.
"""
import pandas as pd

from backtest.drawdown_gate import price_fraction  # noqa: F401 (used indirectly)
from backtest.fib_features import build_fib_frame
from backtest.fib_reporting import (
    benchmark_equal_weight,
    benchmark_spy,
    compute_the_gap,
    compute_trade_stats,
    exit_breakdown,
)
from backtest.fib_simulator import simulate_fib
from backtest.reporting import compute_drawdown_stats

FAR_PAST = pd.Timestamp("1900-01-01")
FAR_FUTURE = pd.Timestamp("2100-01-01")

# 12-name curated sample; $500B+ underlyings get the LEAP path + 25% gate.
NAMES = ["NFLX", "MSFT", "META", "NVDA", "AMD", "NOW", "ORCL", "MU", "TSLA",
         "HIMS", "HOOD", "SOFI"]
LEAP_TICKERS = frozenset({"MSFT", "META", "NVDA", "NFLX", "TSLA"})

# 7 distinct matrix cells (entry_tf, exit_tf)
CELLS = [
    ("weekly", "weekly"), ("weekly", "3day"),
    ("3day", "3day"), ("3day", "weekly"),
    ("daily", "daily"), ("daily", "3day"), ("daily", "weekly"),
]


def cell_label(entry_tf, exit_tf):
    return f"{entry_tf}/{exit_tf}"


def _gate(ticker):
    return 0.25 if ticker in LEAP_TICKERS else 0.40


def build_all_frames(cfg):
    """{(entry_tf, exit_tf): {ticker: frame}} — built once, sliced per
    window downstream (never re-resampled per window)."""
    frames = {}
    for entry_tf, exit_tf in CELLS:
        frames[(entry_tf, exit_tf)] = {
            t: build_fib_frame(t, _gate(t), entry_tf, exit_tf, cfg) for t in NAMES
        }
    return frames


def _run_cell(cell_frames, cfg, window, label, **kw):
    return simulate_fib(
        cell_frames, cfg, window=window,
        seed_cash=cfg["backtest"]["seed_cash"],
        cell=kw.get("cell", "?"), window_label=label,
        leap_tickers=LEAP_TICKERS, **{k: v for k, v in kw.items() if k != "cell"},
    )


def run_matrix(cfg):
    all_frames = build_all_frames(cfg)

    end = max(f.index.max() for cell in all_frames.values() for f in cell.values())
    start = min(f.index.min() for cell in all_frames.values() for f in cell.values())
    vault_start = end - pd.DateOffset(months=12)     # 12-month vault
    boundary = pd.Timestamp(cfg["backtest"]["split_half_boundary"])

    windows = {
        "combined (pre-vault)": (FAR_PAST, vault_start),
        f"half-1 (→ {boundary.date()})": (FAR_PAST, boundary),
        f"half-2 ({boundary.date()} → vault)": (boundary, vault_start),
        "VAULT (last 12mo, tested once)": (vault_start, FAR_FUTURE),
    }

    results = {}   # (cell_label, window_label) -> dict
    for entry_tf, exit_tf in CELLS:
        cl = cell_label(entry_tf, exit_tf)
        cframes = all_frames[(entry_tf, exit_tf)]
        for wlabel, win in windows.items():
            res = _run_cell(cframes, cfg, win, wlabel, cell=cl)
            results[(cl, wlabel)] = {
                "trade": compute_trade_stats(res),
                "dd": compute_drawdown_stats(res.equity_curve),
                "exits": exit_breakdown(res),
                "gap": compute_the_gap(res),
                "result": res,
            }

    # best pre-vault cell by expectancy (vault NOT peeked for this choice)
    prevault_exp = {
        cl: results[(cl, "combined (pre-vault)")]["trade"]["expectancy_pct"]
        for cl in {cell_label(e, x) for e, x in CELLS}
    }
    best_cell = max(
        (c for c, e in prevault_exp.items() if e is not None),
        key=lambda c: prevault_exp[c], default=cell_label(*CELLS[0]),
    )

    # ablation: latched vs simple on the best cell, combined pre-vault
    be, bx = next((e, x) for e, x in CELLS if cell_label(e, x) == best_cell)
    bframes = all_frames[(be, bx)]
    latched = _run_cell(bframes, cfg, (FAR_PAST, vault_start), "ablation", cell=best_cell)
    simple = _run_cell(bframes, cfg, (FAR_PAST, vault_start), "ablation",
                       cell=best_cell, simple_exit=True)
    ablation = {
        "best_cell": best_cell,
        "latched": {"trade": compute_trade_stats(latched),
                    "dd": compute_drawdown_stats(latched.equity_curve),
                    "gap": compute_the_gap(latched)},
        "simple": {"trade": compute_trade_stats(simple),
                   "dd": compute_drawdown_stats(simple.equity_curve),
                   "gap": compute_the_gap(simple)},
    }

    # both-ways stale diagnostic on the best cell (HOOD/SOFI), pre-vault
    stale_names = ["HOOD", "SOFI"]
    stale_frames = {t: bframes[t] for t in stale_names}
    excl = _run_cell(stale_frames, cfg, (FAR_PAST, vault_start), "stale-excl",
                     cell=best_cell)
    incl = _run_cell(stale_frames, cfg, (FAR_PAST, vault_start), "stale-incl",
                     cell=best_cell, include_stale=True)
    stale_diag = {
        "excluded": compute_trade_stats(excl),
        "included": compute_trade_stats(incl),
        "excluded_dd": compute_drawdown_stats(excl.equity_curve),
        "included_dd": compute_drawdown_stats(incl.equity_curve),
    }

    benchmarks = {
        "spy": benchmark_spy(cfg, start, vault_start),
        "equal_weight": benchmark_equal_weight(NAMES, start, vault_start),
        "spy_vault": benchmark_spy(cfg, vault_start, end),
        "equal_weight_vault": benchmark_equal_weight(NAMES, vault_start, end),
    }

    return {
        "results": results, "windows": list(windows),
        "best_cell": best_cell, "ablation": ablation,
        "stale_diag": stale_diag, "benchmarks": benchmarks,
        "span": (start, end), "vault_start": vault_start,
        "prevault_exp": prevault_exp,
    }
