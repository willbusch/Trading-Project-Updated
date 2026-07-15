"""RSI, SMA, ATR — implemented with Wilder's smoothing (RMA), which is
TradingView's default for RSI and ATR. This choice matters: a plain
exponential moving average with alpha=1/period seeded from the first
observation converges to a different value than Wilder's SMA-seeded
recursive average, especially for short periods like RSI(3). Since the
whole point of the Stage 0 gate is comparing our numbers to TradingView,
we match TradingView's convention rather than picking an arbitrary one.
"""
import numpy as np
import pandas as pd


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothed moving average (RMA).

    Seed = simple average of the first `period` values.
    Then: smoothed[i] = (smoothed[i-1] * (period - 1) + value[i]) / period.
    Returns a series aligned to `series.index`, NaN before the seed point.
    """
    values = series.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)

    if len(values) < period:
        return pd.Series(out, index=series.index)

    out[period - 1] = values[:period].mean()
    for i in range(period, len(values)):
        out[i] = (out[i - 1] * (period - 1) + values[i]) / period

    return pd.Series(out, index=series.index)


def sma(close: pd.Series, period: int) -> pd.Series:
    """Simple moving average of `close` over `period` bars."""
    return close.rolling(window=period, min_periods=period).mean()


def rsi(close: pd.Series, period: int) -> pd.Series:
    """Wilder's RSI over `period` bars.

    The first diff (bar 0) is structurally undefined (no prior close), so
    it's excluded before smoothing rather than treated as missing data.
    RSI itself stays NaN until `period` diffs are available (index `period`
    of the original series).
    """
    delta = close.diff()
    gains = delta.clip(lower=0).iloc[1:]
    losses = (-delta.clip(upper=0)).iloc[1:]

    avg_gain = _wilder_smooth(gains, period)
    avg_loss = _wilder_smooth(losses, period)

    rs = avg_gain / avg_loss
    rsi_vals = 100 - (100 / (1 + rs))
    # avg_loss == 0 with avg_gain > 0 -> RS is inf -> RSI should be 100.
    rsi_vals = rsi_vals.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)
    # avg_loss == 0 and avg_gain == 0 -> no movement at all -> RSI = 50 (neutral, TradingView convention).
    rsi_vals = rsi_vals.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)

    return rsi_vals.reindex(close.index)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Wilder's ATR over `period` bars."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    tr_for_smoothing = tr.iloc[1:]  # bar 0 has no prev_close, exclude before smoothing
    smoothed = _wilder_smooth(tr_for_smoothing, period)
    return smoothed.reindex(close.index)
