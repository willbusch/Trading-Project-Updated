"""Feature-frame construction — the single seam between raw data and the
backtest.

`build_feature_frame()` composes screener.data + screener.resample +
screener.weekly + screener.indicators + screener.ut_bot exactly once per
ticker, on FULL cached history, always. Backtest windows are produced by
slicing the returned frame downstream — never by re-fetching or
re-resampling a sub-range, because:

  - resample.py's 3-day bars anchor to the start of the fetched history,
    so resampling a shorter range shifts every bar boundary; and
  - UT Bot's trailing stop is a path-dependent ratchet, so its value on a
    given bar depends on all prior bars.

Deliberately NOT computed here: SMA(200). Removed from all strategy entry
logic by owner override 2026-07-19 (Addendum 2) — display-only use later,
never part of the signal path.
"""
import pandas as pd

from screener.data import fetch_daily_bars
from screener.indicators import atr, rsi
from screener.resample import resample_to_n_day_bars
from screener.ut_bot import ut_bot_signals
from screener.weekly import weekly_filter_for_dates


def build_feature_frame(
    ticker: str,
    cfg: dict,
    ut_key_value: float | None = None,
    ut_atr_period: int | None = None,
) -> pd.DataFrame:
    """One row per COMPLETED 3-day bar (a trailing forming bar with
    n_days < bar_size_days is dropped — signals never fire on a partial
    bar). Columns:

      Open/High/Low/Close/Volume/n_days   3-day bars
      rsi                                 RSI(indicators.rsi_period) on 3-day closes
      atr                                 ATR(indicators.atr_period) on 3-day bars
                                          (tranche-ladder ablation spacing)
      ut_stop, ut_pos, ut_buy, ut_sell    UT Bot on 3-day bars
      weekly_ok                           weekly not-making-lower-lows verdict
                                          as of each bar's close (fully-closed
                                          weeks only)
      vol_avg                             trailing mean Volume of the PRIOR
                                          strategy_d.volume_avg_bars bars
                                          (excludes the bar itself)
      vol_ratio                           Volume / vol_avg (NaN during warmup)
                                          — Strategy D compares this against
                                          its multiplier, so sweeping the
                                          multiplier needs no recompute

    `ut_key_value` / `ut_atr_period` override config for the UT sweep.
    """
    daily = fetch_daily_bars(ticker)

    bar_size = cfg["resampling"]["bar_size_days"]
    bars = resample_to_n_day_bars(daily, bar_size)
    if len(bars) > 0 and bars["n_days"].iloc[-1] < bar_size:
        bars = bars.iloc[:-1]

    frame = bars.copy()
    frame["rsi"] = rsi(frame["Close"], cfg["indicators"]["rsi_period"])
    frame["atr"] = atr(
        frame["High"], frame["Low"], frame["Close"], cfg["indicators"]["atr_period"]
    )

    ut = ut_bot_signals(
        frame["High"],
        frame["Low"],
        frame["Close"],
        key_value=cfg["ut_bot"]["key_value"] if ut_key_value is None else ut_key_value,
        atr_period=cfg["ut_bot"]["atr_period"] if ut_atr_period is None else ut_atr_period,
    )
    frame["ut_stop"] = ut["trailing_stop"]
    frame["ut_pos"] = ut["pos"]
    frame["ut_buy"] = ut["buy"]
    frame["ut_sell"] = ut["sell"]

    frame["weekly_ok"] = weekly_filter_for_dates(
        frame.index, daily, cfg["entry"]["weekly_lower_low_lookback_weeks"]
    )

    vol_avg = frame["Volume"].shift(1).rolling(cfg["strategy_d"]["volume_avg_bars"]).mean()
    frame["vol_avg"] = vol_avg
    frame["vol_ratio"] = frame["Volume"] / vol_avg

    return frame
