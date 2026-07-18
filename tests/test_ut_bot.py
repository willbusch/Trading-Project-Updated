import pandas as pd
import pytest

from screener.ut_bot import ut_bot_signals


def test_ut_bot_matches_hand_derived_seed_and_ratchet():
    # Hand-derived against the ported Pine logic (key_value=1.0, atr_period=3):
    #   TR = [1.0, 1.0, 1.0, 1.0, 1.3, 1.0, ...] (see derivation in commit/PR notes)
    #   ATR(3) Wilder-seeded (matches screener.indicators.atr): first defined
    #   at index 3 = mean(TR[1],TR[2],TR[3]) = mean(1,1,1) = 1.0
    #   nLoss[3] = 1.0 -> stop[3] seeds via nz(prev_stop,0)=0 branch:
    #     close[3]=10.7 > 0 and close[2]=11.0 > 0 -> stop[3] = max(0, 10.7-1.0) = 9.7
    #   ATR[4] = (1.0*2 + TR[4]=1.3)/3 = 1.1 -> nLoss[4]=1.1
    #     close[4]=11.5 > stop[3]=9.7 and close[3]=10.7 > stop[3]=9.7 (ratchet-up branch)
    #     -> stop[4] = max(9.7, 11.5-1.1) = max(9.7, 10.4) = 10.4
    high = pd.Series(
        [10.5, 11.0, 11.5, 11.2, 12.0, 12.5, 12.2, 13.0, 13.5, 13.2, 10.0, 9.5],
        index=pd.RangeIndex(12),
    )
    low = pd.Series(
        [9.5, 10.0, 10.5, 10.2, 11.0, 11.5, 11.2, 12.0, 12.5, 12.2, 9.0, 8.5],
        index=pd.RangeIndex(12),
    )
    close = pd.Series(
        [10.0, 10.5, 11.0, 10.7, 11.5, 12.0, 11.7, 12.5, 13.0, 12.7, 9.5, 9.0],
        index=pd.RangeIndex(12),
    )

    result = ut_bot_signals(high, low, close, key_value=1.0, atr_period=3)

    for i in range(3):
        assert pd.isna(result["trailing_stop"].iloc[i])
    assert result["trailing_stop"].iloc[3] == pytest.approx(9.7, abs=0.001)
    assert result["trailing_stop"].iloc[4] == pytest.approx(10.4, abs=0.001)


def test_ut_bot_sell_fires_on_sharp_drop_below_ratcheted_stop():
    # Same series as above: an uptrend ratchets the stop up, then a sharp
    # drop at index 10 (9.5, well below the ratcheted ~11.9 stop) should
    # flip position to short and fire a sell signal on that bar.
    high = pd.Series(
        [10.5, 11.0, 11.5, 11.2, 12.0, 12.5, 12.2, 13.0, 13.5, 13.2, 10.0, 9.5],
        index=pd.RangeIndex(12),
    )
    low = pd.Series(
        [9.5, 10.0, 10.5, 10.2, 11.0, 11.5, 11.2, 12.0, 12.5, 12.2, 9.0, 8.5],
        index=pd.RangeIndex(12),
    )
    close = pd.Series(
        [10.0, 10.5, 11.0, 10.7, 11.5, 12.0, 11.7, 12.5, 13.0, 12.7, 9.5, 9.0],
        index=pd.RangeIndex(12),
    )

    result = ut_bot_signals(high, low, close, key_value=1.0, atr_period=3)

    assert result["sell"].iloc[10] == True  # noqa: E712
    assert result["pos"].iloc[10] == -1
    assert not result["buy"].iloc[10]
    # no spurious signals before the drop
    assert not result["buy"].iloc[3:10].any()
    assert not result["sell"].iloc[3:10].any()


def test_ut_bot_no_signal_before_atr_warmup():
    high = pd.Series([10.5, 11.0], index=pd.RangeIndex(2))
    low = pd.Series([9.5, 10.0], index=pd.RangeIndex(2))
    close = pd.Series([10.0, 10.5], index=pd.RangeIndex(2))

    result = ut_bot_signals(high, low, close, key_value=1.0, atr_period=10)

    assert result["trailing_stop"].isna().all()
    assert not result["buy"].any()
    assert not result["sell"].any()
