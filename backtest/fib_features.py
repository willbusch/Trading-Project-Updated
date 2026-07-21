"""Per-ticker DAILY feature frame for the latched-Fib strategy. Composes
screener.data + backtest.drawdown_gate + backtest.multi_tf once per
(ticker, cell) on full history. All columns forward-only.

Columns (daily index):
  Open/High/Low/Close/Volume        raw daily bars
  high_2yr                          rolling 504d high (NaN until 2yr history)
  dd_pct                            drawdown vs high_2yr
  eligible                          dd_pct >= gate threshold (gate cleared)
  stale                             rolling-504d anchor provably stale (Option 1
                                    excludes these entries from the headline)
  dip_low                           lowest low since gate last cleared, thru bar
  entry_ut_buy                      UT buy EVENT on the cell's ENTRY timeframe
  exit_ut_sell                      UT sell EVENT on the cell's EXIT timeframe
  gate_threshold                    this ticker's drawdown-gate threshold (constant
                                    per ticker; ratio tiebreak = dd_pct/gate_threshold)
  realized_vol                      trailing 252d annualized realized vol (log
                                    returns), forward-only — sigma proxy for
                                    backtest.leap_bs_pricing (no historical IV
                                    surface is available from this data source)
"""
import pandas as pd

from backtest.drawdown_gate import (
    dip_low_since_gate_clear,
    drawdown_pct,
    hybrid_anchor_high,
    is_gate_eligible,
    is_stale_anchor,
    rolling_high,
)
from backtest.leap_bs_pricing import realized_vol as _realized_vol
from backtest.multi_tf import ut_events_on_daily
from screener.data import fetch_daily_bars


def build_fib_frame(
    ticker: str,
    gate_threshold: float,
    entry_tf: str,
    exit_tf: str,
    cfg: dict,
    use_hybrid: bool = False,
) -> pd.DataFrame:
    daily = fetch_daily_bars(ticker)
    key = cfg["ut_bot"]["key_value"]
    atrp = cfg["ut_bot"]["atr_period"]

    frame = daily.copy()
    if use_hybrid:
        # CHANGE 2: hybrid anchor fixes stale/young-name peaks in place, so
        # nothing is excluded; anchor_extended tracks where it fired.
        high, extended = hybrid_anchor_high(daily["Close"])
        frame["high_2yr"] = high
        frame["anchor_extended"] = extended
        frame["stale"] = False           # no exclusion under the hybrid anchor
    else:
        frame["high_2yr"] = rolling_high(daily["Close"])
        frame["anchor_extended"] = False
        frame["stale"] = is_stale_anchor(daily["Close"])
    frame["dd_pct"] = drawdown_pct(daily["Close"], frame["high_2yr"])
    frame["eligible"] = frame["dd_pct"] >= gate_threshold
    frame["gate_threshold"] = gate_threshold
    frame["dip_low"] = dip_low_since_gate_clear(daily["Low"], frame["eligible"])
    frame["realized_vol"] = _realized_vol(daily["Close"])

    # gate-clear date of the current eligible episode — the documented
    # SECONDARY slot-selection tiebreak (deepest drawdown is primary)
    elig = frame["eligible"]
    episode_id = (elig & ~elig.shift(1, fill_value=False)).cumsum().where(elig)
    starts = frame.index.to_series().groupby(episode_id).transform("first")
    frame["gate_clear_date"] = starts

    entry_ev = ut_events_on_daily(daily, entry_tf, key, atrp)
    exit_ev = ut_events_on_daily(daily, exit_tf, key, atrp)
    frame["entry_ut_buy"] = entry_ev["ut_buy"]
    frame["exit_ut_sell"] = exit_ev["ut_sell"]
    return frame
