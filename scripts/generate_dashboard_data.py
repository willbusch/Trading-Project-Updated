"""Generate the JSON data the results dashboard reads. Re-runs the
winning cell (daily/weekly, simple_09 exit) as ONE continuous full-span
backtest — the ablation runs stored only window-sliced summary stats, not
raw equity curves, so this reconstructs the curves the dashboard needs
from the same tested modules (no reimplementation of signal logic).

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
    print("building frames ...")
    t0 = time.time()
    frames = build_universe_frames(tickers, leap_tickers, entry_tf, exit_tf, cfg)
    print(f"  done in {time.time()-t0:.1f}s")

    end = max(fetch_daily_bars(t).index.max() for t in tickers[:5])
    start = pd.Timestamp("2018-01-02")
    vault_start = end - pd.DateOffset(months=12)

    spy = fetch_daily_bars("SPY")["Close"]
    spy_ret = spy.pct_change()

    res_plain = simulate_fib(frames, cfg, seed_cash=cfg["backtest"]["seed_cash"],
                             cell=f"{entry_tf}/{exit_tf}", window_label="full",
                             leap_tickers=leap_tickers, exit_variant=WINNING_VARIANT)
    res_spycash = simulate_fib(frames, cfg, seed_cash=cfg["backtest"]["seed_cash"],
                               cell=f"{entry_tf}/{exit_tf}", window_label="full",
                               leap_tickers=leap_tickers, exit_variant=WINNING_VARIANT,
                               idle_cash_spy=spy_ret)

    spy_span = spy.loc[start:end]
    spy_curve = (spy_span / spy_span.iloc[0]) * cfg["backtest"]["seed_cash"]

    from backtest.fib_reporting import compute_trade_stats, benchmark_spy
    from backtest.reporting import compute_drawdown_stats

    windows = {
        "pre_vault": (pd.Timestamp("1900-01-01"), vault_start),
        "vault": (vault_start, pd.Timestamp("2100-01-01")),
    }
    stats = {}
    for wlabel, (ws, we) in windows.items():
        sub_curve = res_plain.equity_curve.loc[ws:we]
        sub_trades = [t for t in res_plain.closed_trades if ws <= t.entry_date <= we]

        class _R:
            pass
        r = _R()
        r.closed_trades = sub_trades
        r.open_trades = []
        r.equity_curve = sub_curve
        r.rejected_entries = []
        r.stale_excluded = []
        dd = compute_drawdown_stats(sub_curve) if len(sub_curve) > 1 else {
            "total_return": None, "cagr": None, "max_drawdown": None}
        trade = compute_trade_stats(r)
        stats[wlabel] = {"trade": trade, "dd": dd}

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

    data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "cell": f"{entry_tf}/{exit_tf}", "exit_variant": WINNING_VARIANT,
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
