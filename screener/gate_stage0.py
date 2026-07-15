"""Stage 0 gate: print RSI(3) on 3-day bars for a set of tickers so the
values can be eyeballed against TradingView before proceeding.

    python -m screener.gate_stage0 MSFT HIMS
"""
import sys

from screener.config import load_config
from screener.data import fetch_daily_bars
from screener.indicators import rsi
from screener.resample import resample_to_n_day_bars


def run_gate(tickers, period="3y", n_rows=8):
    cfg = load_config()
    bar_size = cfg["resampling"]["bar_size_days"]
    rsi_period = cfg["indicators"]["rsi_period"]

    for ticker in tickers:
        print(f"\n=== {ticker} ===")
        daily = fetch_daily_bars(ticker, period=period)
        print(f"Daily bars fetched: {len(daily)} "
              f"({daily.index[0].date()} to {daily.index[-1].date()})")

        bars_3d = resample_to_n_day_bars(daily, n=bar_size)
        bars_3d["RSI3"] = rsi(bars_3d["Close"], period=rsi_period)

        print(f"3-day bars: {len(bars_3d)}")
        print(f"\nLast {n_rows} 3-day bars (Close, n_days in bar, RSI({rsi_period})):")
        tail = bars_3d[["Close", "n_days", "RSI3"]].tail(n_rows)
        for date, row in tail.iterrows():
            partial = " (partial/forming)" if row["n_days"] < bar_size else ""
            print(f"  {date.date()}  Close={row['Close']:.2f}  "
                  f"n_days={int(row['n_days'])}{partial}  RSI3={row['RSI3']:.2f}")


if __name__ == "__main__":
    tickers = sys.argv[1:] or ["MSFT", "HIMS"]
    run_gate(tickers)
