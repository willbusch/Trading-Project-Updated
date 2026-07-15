"""Daily -> N-day bar resampling.

RSI(3) computed on 3-day bars is a different number from RSI(3) computed on
daily bars — it's the same indicator formula applied to a coarser series.
Getting the bar construction right matters more than the RSI formula itself.
"""
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def resample_to_n_day_bars(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Group consecutive daily bars into non-overlapping N-day bars.

    Resampling rule (document this — it's the thing the Stage 0 gate exists
    to verify against TradingView):
      - `df` must already be sorted ascending by date with no gaps other than
        normal non-trading days (weekends/holidays), i.e. one row per trading
        day.
      - Bars are built by counting off `n` trading days at a time starting
        from the FIRST row of `df`: bar 1 = trading days [0..n-1], bar 2 =
        [n..2n-1], etc. The anchor is the start of the fetched history, not a
        calendar boundary (not week-start, not today's date, not exchange
        holidays-adjusted). Fetching a longer or shorter history shifts which
        calendar dates fall in which bar.
      - Per bar: Open = first day's Open, High = max High, Low = min Low,
        Close = last day's Close, Volume = sum of Volume.
      - The bar's index label is the date of its LAST trading day (the day
        the bar "closes").
      - If `len(df)` isn't a multiple of `n`, the final bar has fewer than
        `n` days — it represents the most recently forming/incomplete bar,
        kept rather than dropped. Its `n_days` column will be < n.

    Returns a DataFrame with columns Open/High/Low/Close/Volume/n_days.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"resample_to_n_day_bars: missing columns {missing}")
    if n < 1:
        raise ValueError(f"resample_to_n_day_bars: n must be >= 1, got {n}")

    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS + ["n_days"])

    group_id = np.arange(len(df)) // n

    open_ = df["Open"].groupby(group_id).first()
    high = df["High"].groupby(group_id).max()
    low = df["Low"].groupby(group_id).min()
    close = df["Close"].groupby(group_id).last()
    volume = df["Volume"].groupby(group_id).sum()
    n_days = df["Close"].groupby(group_id).size()
    bar_dates = pd.Series(df.index, index=df.index).groupby(group_id).last()

    result = pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
            "n_days": n_days,
        }
    )
    result.index = bar_dates.values
    result.index.name = df.index.name
    return result
