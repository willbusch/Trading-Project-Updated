"""Multi-timeframe UT Bot signals projected onto a single DAILY execution
clock, so the timeframe-matrix cells (weekly / 3-day / daily entry × exit)
all advance on the same calendar.

Forward-only guarantee (the #1 lookahead risk in this strategy):
  A UT signal computed on a weekly or 3-day bar is not KNOWN until that
  bar's last constituent trading day has closed. Each higher-timeframe
  bar is labeled (by resample.py / weekly.py) with its last trading day,
  and that date exists in the daily index. We place the bar's buy/sell
  EVENT on exactly that daily date and nowhere else. The simulator fills
  entries/exits at the NEXT daily bar's open, which supplies the correct
  one-bar delay. Nothing is ever placed on a daily bar that precedes the
  higher-timeframe bar's close, so no future information leaks.

buy/sell are EVENTS (true on one daily bar each), never forward-filled —
forward-filling a weekly buy would re-fire it every day of the week.
"""
import pandas as pd

from screener.resample import resample_to_n_day_bars
from screener.ut_bot import ut_bot_signals
from screener.weekly import resample_to_weekly_bars

TIMEFRAMES = ("daily", "3day", "weekly")


def _events_from_bars(bars: pd.DataFrame, daily_index: pd.DatetimeIndex,
                      key_value: float, atr_period: int) -> pd.DataFrame:
    ut = ut_bot_signals(bars["High"], bars["Low"], bars["Close"],
                        key_value=key_value, atr_period=atr_period)
    buy = pd.Series(False, index=daily_index)
    sell = pd.Series(False, index=daily_index)
    # bar labels are last-trading-day dates that exist in the daily index
    buy.loc[ut.index[ut["buy"].to_numpy()]] = True
    sell.loc[ut.index[ut["sell"].to_numpy()]] = True
    return pd.DataFrame({"ut_buy": buy, "ut_sell": sell}, index=daily_index)


def ut_events_on_daily(daily: pd.DataFrame, timeframe: str,
                       key_value: float = 1.0, atr_period: int = 10) -> pd.DataFrame:
    """Daily-indexed ut_buy / ut_sell EVENT columns for the requested
    timeframe. `daily` is the raw daily OHLCV frame (from fetch_daily_bars)."""
    if timeframe == "daily":
        ut = ut_bot_signals(daily["High"], daily["Low"], daily["Close"],
                            key_value=key_value, atr_period=atr_period)
        return pd.DataFrame(
            {"ut_buy": ut["buy"].to_numpy(), "ut_sell": ut["sell"].to_numpy()},
            index=daily.index,
        )
    if timeframe == "3day":
        bars = resample_to_n_day_bars(daily, 3)
        if len(bars) and bars["n_days"].iloc[-1] < 3:
            bars = bars.iloc[:-1]           # drop the still-forming final bar
        return _events_from_bars(bars, daily.index, key_value, atr_period)
    if timeframe == "weekly":
        bars = resample_to_weekly_bars(daily)
        if len(bars) and bars.index[-1].dayofweek != 4:
            bars = bars.iloc[:-1]           # drop a forming (non-Friday-ending) week
        return _events_from_bars(bars, daily.index, key_value, atr_period)
    raise ValueError(f"unknown timeframe {timeframe!r} (expected one of {TIMEFRAMES})")
