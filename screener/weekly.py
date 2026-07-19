"""Weekly bar derivation + the "not making lower lows" entry filter.

Lives in screener/ (not backtest/) because STRATEGY.md makes this filter
part of the live entry signal too — Stage 1/2 will consume it later, and
the backtest engine must use the exact same implementation.

Anchoring rule — deliberately DIFFERENT from resample.py's 3-day bars:
weekly bars are CALENDAR-anchored (weeks ending Friday, i.e. Mon-Fri
trading days grouped together), not anchored to the start of fetched
history. A week is a real calendar object on TradingView's weekly chart;
"the prior 8 weeks" must mean the same 8 weeks regardless of how much
history was fetched. Each weekly bar is labeled with its LAST actual
trading day (Thursday if Friday was a holiday), which is also the moment
the bar becomes fully closed.

Lookahead rule: at any evaluation date t, only weekly bars whose last
trading day is <= t are usable — the currently-forming week is never
consulted. This is the locked design decision from the backtest plan
(reference only fully-closed weekly bars).
"""
import pandas as pd

from screener.resample import REQUIRED_COLUMNS


def resample_to_weekly_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Group daily bars into calendar weeks ending Friday.

    Per week: Open = first day's Open, High = max High, Low = min Low,
    Close = last day's Close, Volume = sum. Index label = the week's last
    actual trading day. `n_days` counts trading days in the week (4 on
    holiday-shortened weeks).
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"resample_to_weekly_bars: missing columns {missing}")
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS + ["n_days"])

    period = df.index.to_period("W-FRI")

    result = pd.DataFrame(
        {
            "Open": df["Open"].groupby(period).first(),
            "High": df["High"].groupby(period).max(),
            "Low": df["Low"].groupby(period).min(),
            "Close": df["Close"].groupby(period).last(),
            "Volume": df["Volume"].groupby(period).sum(),
            "n_days": df["Close"].groupby(period).size(),
        }
    )
    last_day = pd.Series(df.index, index=df.index).groupby(period).last()
    result.index = last_day.values
    result.index.name = df.index.name
    return result


def is_not_making_lower_lows(weekly: pd.DataFrame, lookback_weeks: int) -> pd.Series:
    """Boolean per weekly bar: True when that week's low is NOT a new
    `lookback_weeks`-week low, i.e. week_low >= min(Low of the prior N
    fully-closed weeks). A week that undercuts the prior N weeks' lowest
    low IS making a lower low and fails the filter.

    The first `lookback_weeks` weeks have no full prior window and return
    False — a warmup convention (same spirit as RSI's NaN warmup), chosen
    conservatively so no entry can pass the filter on insufficient history.
    """
    if lookback_weeks < 1:
        raise ValueError(
            f"is_not_making_lower_lows: lookback_weeks must be >= 1, got {lookback_weeks}"
        )
    prior_min = weekly["Low"].shift(1).rolling(lookback_weeks).min()
    passes = weekly["Low"] >= prior_min
    passes[prior_min.isna()] = False
    return passes.astype(bool)


def weekly_filter_for_dates(
    dates: pd.DatetimeIndex, daily: pd.DataFrame, lookback_weeks: int
) -> pd.Series:
    """Map the weekly lower-lows filter onto arbitrary evaluation dates
    (e.g. 3-day bar close dates): for each date t, the verdict of the most
    recent weekly bar fully closed as of t (last trading day <= t).

    Dates before the first usable weekly verdict return False (no history
    to judge -> filter fails, no entry).
    """
    weekly = resample_to_weekly_bars(daily)
    passes = is_not_making_lower_lows(weekly, lookback_weeks)
    # The final weekly bar is labeled with the last FETCHED day, which is
    # only a real weekly close if that day is the week's true end (Friday
    # for W-FRI). Otherwise the bar is still forming (or ended on an
    # unknowable holiday-shortened day) — drop it rather than let a
    # partial week's low leak into verdicts on its own label date.
    if len(passes) > 0 and passes.index[-1].dayofweek != 4:
        passes = passes.iloc[:-1]
    mapped = passes.reindex(dates, method="ffill")
    return mapped.fillna(False).astype(bool)
