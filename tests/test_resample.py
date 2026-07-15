import pandas as pd

from screener.resample import resample_to_n_day_bars


def _make_daily(rows):
    """rows: list of (date_str, open, high, low, close, volume)"""
    dates = [pd.Timestamp(r[0]) for r in rows]
    df = pd.DataFrame(
        {
            "Open": [r[1] for r in rows],
            "High": [r[2] for r in rows],
            "Low": [r[3] for r in rows],
            "Close": [r[4] for r in rows],
            "Volume": [r[5] for r in rows],
        },
        index=pd.DatetimeIndex(dates, name="Date"),
    )
    return df


def test_full_groups_aggregate_correctly():
    rows = [
        ("2026-01-05", 10, 12, 9, 11, 100),
        ("2026-01-06", 11, 13, 10, 12, 150),
        ("2026-01-07", 12, 14, 11, 13, 200),
        ("2026-01-08", 13, 15, 12, 14, 120),
        ("2026-01-09", 14, 16, 13, 15, 130),
        ("2026-01-12", 15, 17, 14, 16, 140),
    ]
    df = _make_daily(rows)
    bars = resample_to_n_day_bars(df, n=3)

    assert len(bars) == 2

    bar1 = bars.iloc[0]
    assert bar1["Open"] == 10
    assert bar1["High"] == 14
    assert bar1["Low"] == 9
    assert bar1["Close"] == 13
    assert bar1["Volume"] == 100 + 150 + 200
    assert bar1["n_days"] == 3
    assert bars.index[0] == pd.Timestamp("2026-01-07")

    bar2 = bars.iloc[1]
    assert bar2["Open"] == 13
    assert bar2["High"] == 17
    assert bar2["Low"] == 12
    assert bar2["Close"] == 16
    assert bar2["Volume"] == 120 + 130 + 140
    assert bar2["n_days"] == 3
    assert bars.index[1] == pd.Timestamp("2026-01-12")


def test_partial_final_bar_is_kept_not_dropped():
    rows = [
        ("2026-01-05", 10, 12, 9, 11, 100),
        ("2026-01-06", 11, 13, 10, 12, 150),
        ("2026-01-07", 12, 14, 11, 13, 200),
        ("2026-01-08", 13, 15, 12, 14, 120),
    ]
    df = _make_daily(rows)
    bars = resample_to_n_day_bars(df, n=3)

    assert len(bars) == 2
    assert bars.iloc[0]["n_days"] == 3
    assert bars.iloc[1]["n_days"] == 1
    assert bars.iloc[1]["Open"] == 13
    assert bars.iloc[1]["Close"] == 14
    assert bars.index[1] == pd.Timestamp("2026-01-08")


def test_empty_input_returns_empty_output():
    df = _make_daily([])
    bars = resample_to_n_day_bars(df, n=3)
    assert bars.empty


def test_missing_column_raises():
    df = _make_daily([("2026-01-05", 10, 12, 9, 11, 100)]).drop(columns=["Volume"])
    try:
        resample_to_n_day_bars(df, n=3)
        assert False, "expected ValueError"
    except ValueError:
        pass
