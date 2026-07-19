import pandas as pd
import pytest

from screener.weekly import (
    is_not_making_lower_lows,
    resample_to_weekly_bars,
    weekly_filter_for_dates,
)


def _daily(dates, lows, base=100.0):
    idx = pd.DatetimeIndex(dates, name="Date")
    return pd.DataFrame(
        {
            "Open": [base] * len(idx),
            "High": [base + 5] * len(idx),
            "Low": lows,
            "Close": [base] * len(idx),
            "Volume": [1_000] * len(idx),
        },
        index=idx,
    )


def test_weekly_bars_are_calendar_anchored_not_fetch_start_anchored():
    # Start the fetch mid-week (Wednesday 2024-01-03). A fetch-start anchor
    # would put 5 days in the first bar; a calendar anchor puts only
    # Wed/Thu/Fri (3 days) in the week ending Fri 2024-01-05.
    dates = pd.bdate_range("2024-01-03", "2024-01-12")  # Wed .. next Fri
    df = _daily(dates, lows=range(90, 90 + len(dates)))

    weekly = resample_to_weekly_bars(df)

    assert len(weekly) == 2
    assert weekly["n_days"].tolist() == [3, 5]
    # label = last actual trading day of each week
    assert weekly.index[0] == pd.Timestamp("2024-01-05")
    assert weekly.index[1] == pd.Timestamp("2024-01-12")
    # OHLCV aggregation: Low = min of the week's daily lows
    assert weekly["Low"].iloc[0] == 90
    assert weekly["Low"].iloc[1] == 93
    assert weekly["Volume"].iloc[0] == 3_000


def test_weekly_bar_labeled_by_last_trading_day_on_holiday_week():
    # Week of 2024-07-01: July 4th holiday removed -> 4 trading days,
    # last trading day Friday 2024-07-05 still present; drop the Friday
    # too so the week ends Wednesday 2024-07-03.
    dates = pd.DatetimeIndex(
        ["2024-07-01", "2024-07-02", "2024-07-03", "2024-07-08", "2024-07-09"]
    )
    df = _daily(dates, lows=[100, 99, 98, 97, 96])

    weekly = resample_to_weekly_bars(df)

    assert weekly.index[0] == pd.Timestamp("2024-07-03")
    assert weekly["n_days"].iloc[0] == 3


def test_lower_lows_filter_hand_derived():
    # 6 weeks of lows, lookback = 3:
    #   lows: [10, 9, 8, 8.5, 7, 9]
    #   week 3 (8.5): prior-3 min = min(10,9,8) = 8  -> 8.5 >= 8  -> passes
    #   week 4 (7):   prior-3 min = min(9,8,8.5) = 8 -> 7 < 8     -> FAILS (new low)
    #   week 5 (9):   prior-3 min = min(8,8.5,7) = 7 -> 9 >= 7    -> passes
    weekly = pd.DataFrame(
        {"Low": [10, 9, 8, 8.5, 7, 9]},
        index=pd.bdate_range("2024-01-05", periods=6, freq="W-FRI"),
    )

    passes = is_not_making_lower_lows(weekly, lookback_weeks=3)

    # warmup: first 3 weeks have no full prior window -> False
    assert passes.iloc[:3].tolist() == [False, False, False]
    assert passes.iloc[3] == True  # noqa: E712
    assert passes.iloc[4] == False  # noqa: E712
    assert passes.iloc[5] == True  # noqa: E712


def test_weekly_filter_for_dates_uses_only_fully_closed_weeks():
    # Two full weeks then a partial third week. Evaluating mid-week 3 must
    # use week 2's verdict, never the forming week's partial low.
    dates = pd.bdate_range("2024-01-01", "2024-01-16")  # Mon w1 .. Tue w3
    lows = [100] * 5 + [99] * 5 + [1, 1]  # week 3 crashes (partial)
    df = _daily(dates, lows=lows)

    verdicts = weekly_filter_for_dates(
        pd.DatetimeIndex(["2024-01-16"]), df, lookback_weeks=1
    )

    # week 2 low (99) >= week 1 low (100)? no wait: 99 < 100 would fail —
    # use week 2's verdict: 99 < prior-1-week min (100) -> making a lower
    # low -> False. The forming week's 1s must NOT be what drives this.
    assert verdicts.iloc[0] == False  # noqa: E712

    # Same shape but week 2 holds above week 1's low -> True at the same
    # mid-week-3 date, proving the crash-in-progress week is ignored.
    lows_ok = [100] * 5 + [101] * 5 + [1, 1]
    df_ok = _daily(dates, lows=lows_ok)
    verdicts_ok = weekly_filter_for_dates(
        pd.DatetimeIndex(["2024-01-16"]), df_ok, lookback_weeks=1
    )
    assert verdicts_ok.iloc[0] == True  # noqa: E712


def test_lower_lows_rejects_bad_lookback():
    weekly = pd.DataFrame(
        {"Low": [1.0]}, index=pd.DatetimeIndex(["2024-01-05"])
    )
    with pytest.raises(ValueError):
        is_not_making_lower_lows(weekly, lookback_weeks=0)
