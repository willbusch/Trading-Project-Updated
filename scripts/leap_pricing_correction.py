"""LEAP pricing correction demo (2026-07-21): for each existing LEAP trade
in the trade log, recompute its P&L under the NEW Black-Scholes engine
using the SAME entry/exit dates and underlying prices already on record,
and show it beside the OLD flat-0.55-delta approximation's number.

This does not require re-running the simulator — it isolates the pricing
model as the only variable, holding entry/exit timing fixed.
"""
import json

import pandas as pd

from backtest.fib_features import build_fib_frame
from backtest.leap_bs_pricing import (
    CONTRACT_MULTIPLIER,
    bs_call_price,
    solve_strike_for_delta,
    target_delta,
)
from screener.config import load_config

T0 = 2.0  # fib_modeled_expiry_years


def old_approx_pnl(entry_price, exit_price, delta=0.55):
    """The retired flat-delta model: pnl% = delta * underlying %move."""
    underlying_move_pct = (exit_price - entry_price) / entry_price
    return delta * underlying_move_pct


def new_real_pnl(ticker, entry_date, entry_price, exit_date, exit_price, cfg):
    frame = build_fib_frame(ticker, 0.25, "daily", "weekly", cfg, use_hybrid=True)
    entry_ts = pd.Timestamp(entry_date)
    if entry_ts not in frame.index:
        return None, "entry date not in cached history"
    sigma = frame.loc[entry_ts, "realized_vol"]
    if sigma != sigma:
        return None, "insufficient realized-vol history at entry"
    dtarget = target_delta(cfg)
    K = solve_strike_for_delta(entry_price, dtarget, T0, sigma)
    entry_premium = bs_call_price(entry_price, K, T0, sigma)
    cost = entry_premium * CONTRACT_MULTIPLIER

    if exit_date is None:
        exit_ts = frame.index[-1]
        exit_price = frame.loc[exit_ts, "Close"]
    else:
        exit_ts = pd.Timestamp(exit_date)
    t_remaining = max((entry_ts + pd.Timedelta(days=int(T0 * 365.25)) - exit_ts).days / 365.25, 0.0)
    exit_premium = bs_call_price(exit_price, K, t_remaining, sigma)
    proceeds = exit_premium * CONTRACT_MULTIPLIER
    pnl_pct = (proceeds - cost) / cost
    return pnl_pct, {"sigma": sigma, "strike": K, "entry_premium": entry_premium,
                     "exit_premium": exit_premium}


def main():
    cfg = load_config()
    d = json.load(open("reports/dashboard_data.json"))
    leap_trades = [t for t in d["trade_log"] if t["kind"] == "leap"]

    print(f"{'Ticker':7s} {'Entry':11s} {'Exit':11s} {'Underlying%':>12s} "
         f"{'OLD approx':>11s} {'NEW real':>11s} {'Multiplier':>11s}")
    rows = []
    for t in leap_trades:
        exit_price = t["exit_price"]
        if exit_price is None:   # still open -> mark both models to the SAME latest close
            frame = build_fib_frame(t["ticker"], 0.25, "daily", "weekly", cfg, use_hybrid=True)
            exit_price = frame["Close"].iloc[-1]
        old_pnl = old_approx_pnl(t["entry_price"], exit_price)
        new_pnl, detail = new_real_pnl(
            t["ticker"], t["entry_date"], t["entry_price"],
            t["exit_date"], exit_price, cfg,
        )
        underlying_pct = (exit_price - t["entry_price"]) / t["entry_price"]
        mult = (new_pnl / underlying_pct) if (new_pnl is not None and underlying_pct != 0) else None
        status = "OPEN" if t["is_open"] else t["exit_date"]
        print(f"{t['ticker']:7s} {t['entry_date']:11s} {str(status):11s} "
             f"{underlying_pct*100:11.1f}% {old_pnl*100:10.1f}% "
             f"{'N/A' if new_pnl is None else f'{new_pnl*100:.1f}%':>11s} "
             f"{'N/A' if mult is None else f'{mult:.2f}x':>11s}")
        rows.append({
            "ticker": t["ticker"], "entry_date": t["entry_date"], "exit_date": t["exit_date"],
            "underlying_move_pct": underlying_pct, "old_approx_pnl_pct": old_pnl,
            "new_real_pnl_pct": new_pnl, "multiplier_vs_underlying": mult, "detail": detail,
        })
    json.dump(rows, open("/tmp/claude-0/-home-user-Trading-Project-Updated/"
                         "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad/"
                         "leap_correction.json", "w"), default=str, indent=1)


if __name__ == "__main__":
    main()
