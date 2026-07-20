"""Drawdown-gate anchors for the latched-Fib strategy: rolling 2yr high,
dip low, drawdown %, and gate eligibility — all forward-only (no future
bars referenced at any point).

504 trading days ~= 2 calendar years; `rolling(..., min_periods=504)`
means the anchor is NaN (gate never eligible) until 2 full years of
history exist, per the "handle short histories explicitly" guardrail.
"""
import pandas as pd

TWO_YEAR_TRADING_DAYS = 504


def rolling_high(close: pd.Series, window: int = TWO_YEAR_TRADING_DAYS) -> pd.Series:
    return close.rolling(window, min_periods=window).max()


def drawdown_pct(close: pd.Series, high: pd.Series) -> pd.Series:
    return 1.0 - close / high


def is_gate_eligible(close: pd.Series, threshold: float, window: int = TWO_YEAR_TRADING_DAYS) -> pd.Series:
    high = rolling_high(close, window)
    dd = drawdown_pct(close, high)
    return dd >= threshold


def dip_low_since_gate_clear(low: pd.Series, eligible: pd.Series) -> pd.Series:
    """Lowest low since the gate most recently cleared, through the
    current bar (never future bars). Resets each time a new eligible
    episode begins after an ineligible gap."""
    episode_id = (eligible & ~eligible.shift(1, fill_value=False)).cumsum()
    episode_id = episode_id.where(eligible)
    return low.groupby(episode_id).cummin()
