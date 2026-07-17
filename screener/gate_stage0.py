"""Stage 0 gate: print RSI on 3-day bars for a set of tickers so the values
can be eyeballed against TradingView before proceeding.

Data must already be cached (see screener/data.py — the agent populates the
cache via the Robinhood MCP tool + ingest_robinhood_bars(), since this
script cannot call MCP tools itself when run standalone):

    python -m screener.gate_stage0 MSFT HIMS
"""
import sys

from screener.config import load_config
from screener.data import fetch_daily_bars
from screener.indicators import rsi
from screener.resample import resample_to_n_day_bars


def run_gate(tickers, n_rows=8):
    cfg = load_config()
    bar_size = cfg["resampling"]["bar_size_days"]
    rsi_period = cfg["indicators"]["rsi_period"]

    for ticker in tickers:
        print(f"\n=== {ticker} ===")
        daily = fetch_daily_bars(ticker)
        print(f"Daily bars: {len(daily)} "
              f"({daily.index[0].date()} to {daily.index[-1].date()})")

        bars_3d = resample_to_n_day_bars(daily, n=bar_size)
        bars_3d[f"RSI{rsi_period}"] = rsi(bars_3d["Close"], period=rsi_period)

        print(f"3-day bars: {len(bars_3d)}")
        print(f"\nLast {n_rows} 3-day bars (Close, n_days in bar, RSI({rsi_period})):")
        tail = bars_3d[["Close", "n_days", f"RSI{rsi_period}"]].tail(n_rows)
        for date, row in tail.iterrows():
            partial = " (partial/forming)" if row["n_days"] < bar_size else ""
            print(f"  {date.date()}  Close={row['Close']:.2f}  "
                  f"n_days={int(row['n_days'])}{partial}  "
                  f"RSI{rsi_period}={row[f'RSI{rsi_period}']:.2f}")


if __name__ == "__main__":
    tickers = sys.argv[1:] or ["MSFT", "HIMS"]
    run_gate(tickers)
