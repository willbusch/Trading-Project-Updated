import pandas as pd
import pytest

from screener.indicators import atr, rsi, sma


def test_sma_matches_manual_average():
    close = pd.Series([10, 20, 30, 40, 50], index=pd.RangeIndex(5))
    result = sma(close, period=3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == pytest.approx((10 + 20 + 30) / 3)
    assert result.iloc[3] == pytest.approx((20 + 30 + 40) / 3)
    assert result.iloc[4] == pytest.approx((30 + 40 + 50) / 3)


def test_rsi_matches_hand_computed_wilder_reference():
    # Hand-computed reference (Wilder's smoothing, SMA-seeded), see PR/commit
    # notes for the by-hand derivation:
    #   closes = [10, 11, 12, 11, 13]
    #   diffs  = [ _,  1,  1, -1,  2]
    #   gains  = [ _,  1,  1,  0,  2] -> seed(period=3) at idx3 = mean(1,1,0)=0.6667
    #                                    idx4 = (0.6667*2 + 2) / 3 = 1.1111
    #   losses = [ _,  0,  0,  1,  0] -> seed at idx3 = mean(0,0,1)=0.3333
    #                                    idx4 = (0.3333*2 + 0) / 3 = 0.2222
    #   RSI[3] = 100 - 100/(1 + 0.6667/0.3333) = 66.667
    #   RSI[4] = 100 - 100/(1 + 1.1111/0.2222) = 83.333
    close = pd.Series([10, 11, 12, 11, 13], index=pd.RangeIndex(5))
    result = rsi(close, period=3)

    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert pd.isna(result.iloc[2])
    assert result.iloc[3] == pytest.approx(66.667, abs=0.01)
    assert result.iloc[4] == pytest.approx(83.333, abs=0.01)


def test_rsi_all_gains_approaches_100():
    close = pd.Series(range(1, 20), index=pd.RangeIndex(19))  # strictly increasing
    result = rsi(close, period=3)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_rsi_all_losses_approaches_0():
    close = pd.Series(range(19, 0, -1), index=pd.RangeIndex(19))  # strictly decreasing
    result = rsi(close, period=3)
    assert result.iloc[-1] == pytest.approx(0.0)


def test_rsi_flat_series_is_neutral_50():
    close = pd.Series([10] * 10, index=pd.RangeIndex(10))
    result = rsi(close, period=3)
    assert result.iloc[-1] == pytest.approx(50.0)


def test_atr_matches_hand_computed_wilder_reference():
    # Hand-computed reference (same derivation approach as RSI test):
    #   high  = [12, 13, 14, 13, 15]
    #   low   = [ 9, 10, 11, 10, 12]
    #   close = [10, 11, 12, 11, 13]
    #   TR[1] = max(13-10, |13-10|, |10-10|) = 3
    #   TR[2] = max(14-11, |14-11|, |11-11|) = 3
    #   TR[3] = max(13-10, |13-12|, |10-12|) = 3
    #   TR[4] = max(15-12, |15-11|, |12-11|) = 4
    #   seed(period=3) at idx3 = mean(3,3,3) = 3.0
    #   idx4 = (3.0*2 + 4) / 3 = 3.3333
    high = pd.Series([12, 13, 14, 13, 15], index=pd.RangeIndex(5))
    low = pd.Series([9, 10, 11, 10, 12], index=pd.RangeIndex(5))
    close = pd.Series([10, 11, 12, 11, 13], index=pd.RangeIndex(5))

    result = atr(high, low, close, period=3)

    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert pd.isna(result.iloc[2])
    assert result.iloc[3] == pytest.approx(3.0, abs=0.001)
    assert result.iloc[4] == pytest.approx(3.3333, abs=0.001)
