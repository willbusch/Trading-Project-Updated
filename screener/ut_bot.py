"""UT Bot Alerts, ported from the original Pine v4 script (see docs/PLAN.md
for the source). Heikin Ashi option is OFF per spec — this only supports
the regular-close path (`h = input(false, ...)` branch).

Faithful-port notes (things that would silently diverge from TradingView
if done the "obvious" way instead of literally):

- `ema(src, 1)` in the Pine is mathematically `src` itself — alpha =
  2/(1+1) = 1, so ema[i] = src[i] with zero smoothing. The above/below
  crossover checks below compare directly against `src`, which is the
  same computation, not an approximation of it.
- Pine's `atr()` = `rma(tr, length)`, and Pine's `rma` seeds with
  `sma(src, length)` on its first defined bar — i.e. NaN until `length`
  bars are available, then SMA-seeded recursive average from there. That
  is exactly the Wilder smoothing already implemented in
  `screener.indicators.atr()` for this project's ATR(14), so it's reused
  here rather than reimplemented.
- `nz(xATRTrailingStop[1], 0)` matters: while ATR(c) is still NaN (first
  `c-1` bars), the trailing stop is NaN too (arithmetic with NaN produces
  NaN). Once ATR first becomes defined, the previous trailing stop's NaN
  is treated as 0 for that one comparison/branch — for real (positive)
  prices this always sends the stop into the "src > prevstop" branch on
  its first defined bar, seeding it at `close - nLoss`. This is
  implemented literally below, not approximated.
"""
import numpy as np
import pandas as pd

from screener.indicators import atr as _atr


def ut_bot_signals(
    high: pd.Series, low: pd.Series, close: pd.Series,
    key_value: float = 1.0, atr_period: int = 10,
) -> pd.DataFrame:
    """Compute the UT Bot trailing stop, position state, and buy/sell
    signals. Returns a DataFrame aligned to `close.index` with columns:
    trailing_stop, pos (1/-1/0), buy (bool), sell (bool).
    """
    n = len(close)
    src = close.to_numpy(dtype=float)
    atr_series = _atr(high, low, close, atr_period).to_numpy(dtype=float)
    n_loss = key_value * atr_series

    stop = np.full(n, np.nan)
    pos = np.zeros(n, dtype=int)
    buy = np.zeros(n, dtype=bool)
    sell = np.zeros(n, dtype=bool)

    for i in range(n):
        if np.isnan(n_loss[i]):
            # ATR(c) not yet defined -> trailing stop stays undefined,
            # matching Pine (arithmetic with na propagates na).
            continue

        prev_stop_raw = stop[i - 1] if i > 0 else np.nan
        prev_stop_nz = 0.0 if np.isnan(prev_stop_raw) else prev_stop_raw
        prev_src = src[i - 1] if i > 0 else np.nan

        if src[i] > prev_stop_nz and (not np.isnan(prev_src)) and prev_src > prev_stop_nz:
            stop[i] = max(prev_stop_nz, src[i] - n_loss[i])
        elif src[i] < prev_stop_nz and (not np.isnan(prev_src)) and prev_src < prev_stop_nz:
            stop[i] = min(prev_stop_nz, src[i] + n_loss[i])
        else:
            stop[i] = src[i] - n_loss[i] if src[i] > prev_stop_nz else src[i] + n_loss[i]

        prev_pos = pos[i - 1] if i > 0 else 0
        if (not np.isnan(prev_src)) and prev_src < prev_stop_nz and src[i] > stop[i]:
            pos[i] = 1
        elif (not np.isnan(prev_src)) and prev_src > prev_stop_nz and src[i] < stop[i]:
            pos[i] = -1
        else:
            pos[i] = prev_pos

        # above = crossover(src, stop): src[1] <= stop[1] and src > stop
        # below = crossover(stop, src): stop[1] <= src[1] and stop > src
        if i > 0 and not np.isnan(stop[i - 1]):
            above = (prev_src <= stop[i - 1]) and (src[i] > stop[i])
            below = (stop[i - 1] <= prev_src) and (stop[i] > src[i])
        else:
            above = False
            below = False

        buy[i] = (src[i] > stop[i]) and above
        sell[i] = (src[i] < stop[i]) and below

    return pd.DataFrame(
        {"trailing_stop": stop, "pos": pos, "buy": buy, "sell": sell},
        index=close.index,
    )
