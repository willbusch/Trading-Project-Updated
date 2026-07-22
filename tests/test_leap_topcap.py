"""A2 (2026-07-22, "Beat-SPY Package"): top-10-by-market-cap-proxy LEAP
eligibility. Tests the ranking module directly (backtest/leap_topcap.py)
and its lookahead safety."""
import numpy as np
import pandas as pd

from backtest.leap_topcap import (
    historical_cap_proxy_matrix,
    implied_shares_outstanding,
    top_n_by_cap_matrix,
)


def _frame(prices: list, start="2020-01-02") -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=len(prices))
    close = pd.Series(prices, index=dates)
    return pd.DataFrame({"Close": close})


def test_implied_shares_uses_current_cap_over_latest_close():
    frames = {"AAPL": _frame([100.0, 110.0, 120.0])}
    shares = implied_shares_outstanding(frames, {"AAPL": 1_200_000_000.0})
    assert shares["AAPL"] == 1_200_000_000.0 / 120.0


def test_historical_cap_proxy_scales_with_actual_past_price():
    """The whole point of the proxy: a name's PROXY cap in the past must
    reflect its OWN lower historical price, not today's price applied
    retroactively — this is what fixes the MU-2021 problem."""
    # price ramps 50 -> 200; current (last) cap is $200B -> implied shares = 1B
    frames = {"MU": _frame([50.0, 100.0, 150.0, 200.0])}
    caps = historical_cap_proxy_matrix(frames, {"MU": 200_000_000_000.0})
    assert caps["MU"].iloc[0] == 50_000_000_000.0     # early: much smaller proxy cap
    assert caps["MU"].iloc[-1] == 200_000_000_000.0    # today: matches the real snapshot


def test_top_n_ranking_excludes_a_name_only_top_by_todays_snapshot():
    """MU-2021-style case: MU's TODAY cap is huge, but back when its price
    was a fraction of today's, its proxy cap should rank far outside the
    top N even while a genuinely large name (steady $2T co.) stays in."""
    dates = pd.bdate_range("2020-01-02", periods=3)
    mu = pd.DataFrame({"Close": [20.0, 20.0, 200.0]}, index=dates)   # 10x runup
    giant = pd.DataFrame({"Close": [1000.0, 1000.0, 1000.0]}, index=dates)
    frames = {"MU": mu, "GIANT": giant}
    # today's snapshot: MU $200B (small vs GIANT's $2T)
    market_caps = {"MU": 200_000_000_000.0, "GIANT": 2_000_000_000_000.0}
    top1 = top_n_by_cap_matrix(frames, market_caps, top_n=1)
    assert top1["GIANT"].all()               # always #1
    assert not top1["MU"].iloc[0]             # MU excluded early (small proxy cap then)
    assert not top1["MU"].iloc[-1]            # still excluded even after its runup (GIANT bigger)


def test_topcap_ranking_is_forward_only():
    """LOOKAHEAD TEST: the top-N membership on any date D must depend only
    on prices up to and including D. Truncating the future must not change
    ranking decisions already made on the shared prefix."""
    rng = np.random.default_rng(1)
    n = 200
    dates = pd.bdate_range("2019-01-02", periods=n)
    frames = {
        t: pd.DataFrame({"Close": 100 + np.cumsum(rng.normal(0, 1, n))}, index=dates)
        for t in ["AAA", "BBB", "CCC", "DDD", "EEE"]
    }
    market_caps = {t: 100e9 * (i + 1) for i, t in enumerate(frames)}
    full = top_n_by_cap_matrix(frames, market_caps, top_n=2)

    cut = 120
    trunc_frames = {t: f.iloc[:cut] for t, f in frames.items()}
    trunc = top_n_by_cap_matrix(trunc_frames, market_caps, top_n=2)

    pd.testing.assert_frame_equal(full.iloc[:cut], trunc, check_names=False)


def test_eligible_tickers_by_year_reports_membership():
    from backtest.leap_topcap import eligible_tickers_by_year
    dates = pd.bdate_range("2020-01-02", periods=260 * 2)   # ~2 years
    small = pd.DataFrame({"Close": [10.0] * len(dates)}, index=dates)
    big = pd.DataFrame({"Close": [1000.0] * len(dates)}, index=dates)
    frames = {"SMALL": small, "BIG": big}
    market_caps = {"SMALL": 10e9, "BIG": 1000e9}
    top1 = top_n_by_cap_matrix(frames, market_caps, top_n=1)
    by_year = eligible_tickers_by_year(top1)
    for year, names in by_year.items():
        assert names == ["BIG"]
