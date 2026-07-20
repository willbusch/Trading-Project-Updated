"""Drawdown-gate anchors for the latched-Fib strategy: rolling 2yr high,
dip low, drawdown %, and gate eligibility — all forward-only (no future
bars referenced at any point).

504 trading days ~= 2 calendar years; `rolling(..., min_periods=504)`
means the anchor is NaN (gate never eligible) until 2 full years of
history exist, per the "handle short histories explicitly" guardrail.
"""
import pandas as pd

TWO_YEAR_TRADING_DAYS = 504
STALE_LOOKBACK_TRADING_DAYS = 1008          # ~4yr — the window used to DETECT a
                                            # peak that aged out of the 504d anchor
FIB_FRACTIONS = (0.5, 0.9, 1.0, 1.1, 1.5, 1.618)


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


def is_stale_anchor(
    close: pd.Series,
    window: int = TWO_YEAR_TRADING_DAYS,
    stale_window: int = STALE_LOOKBACK_TRADING_DAYS,
) -> pd.Series:
    """Per bar (forward-only): True when the rolling `window`-day high is
    PROVABLY stale — a higher high existed within `stale_window` days but
    OUTSIDE the `window` (so the 504-day anchor has 'forgotten' the real
    recent peak). The exact HOOD/SOFI 2021-IPO-peak case. Both maxima look
    only backward, so no lookahead.

    In the 12-name round this drove Option-1 EXCLUSION. In the universe
    round the HYBRID ANCHOR (below) instead FIXES these bars by using the
    extended-window high, so nothing is excluded — this function now just
    flags where the extension fires (for the frequency report)."""
    high_504 = close.rolling(window, min_periods=window).max()
    high_long = close.rolling(stale_window, min_periods=window).max()
    return (high_long > high_504 + 1e-9).fillna(False)


def hybrid_anchor_high(
    close: pd.Series,
    window: int = TWO_YEAR_TRADING_DAYS,
    ext_window: int = STALE_LOOKBACK_TRADING_DAYS,
):
    """CHANGE 2 (universe run): 504-day rolling high by default; when a
    name's true multi-year peak sits OUTSIDE the 504d window but within
    ~4yr (ext_window), use the extended-lookback high instead — so young
    post-IPO names that spent >2yr depressed get their real peak, not a
    decayed one, without reaching to ancient irrelevant highs.

    Returns (high, extended) where `extended` marks bars using the longer
    window. Both maxima are trailing → forward-only (the extended high at
    date D uses only close[D-ext_window+1 .. D]). Lookahead-tested.
    """
    high_504 = close.rolling(window, min_periods=window).max()
    high_ext = close.rolling(ext_window, min_periods=window).max()
    extended = (high_ext > high_504 + 1e-9).fillna(False)
    high = high_504.where(~extended, high_ext)
    return high, extended


def fib_levels(dip_low: float, two_yr_high: float) -> dict:
    """Absolute price levels for each Fib fraction:
    level = dip_low + f * (two_yr_high - dip_low)."""
    span = two_yr_high - dip_low
    return {f: dip_low + f * span for f in FIB_FRACTIONS}


def price_fraction(price: float, dip_low: float, two_yr_high: float) -> float:
    """Where price sits on the move (dip_low=0.0, two_yr_high=1.0,
    target=1.618). NaN-safe against a degenerate zero-width move."""
    span = two_yr_high - dip_low
    if span <= 0:
        return float("nan")
    return (price - dip_low) / span
