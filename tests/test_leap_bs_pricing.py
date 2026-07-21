import math

import pandas as pd
import pytest

from backtest.leap_bs_pricing import (
    bs_call_delta,
    bs_call_price,
    realized_vol,
    solve_strike_for_delta,
    target_delta,
)


def test_call_price_at_expiry_is_intrinsic_value():
    assert bs_call_price(S=150, K=100, T=0, sigma=0.3) == pytest.approx(50)
    assert bs_call_price(S=80, K=100, T=0, sigma=0.3) == pytest.approx(0)


def test_call_delta_bounds():
    d = bs_call_delta(S=100, K=100, T=1.0, sigma=0.3)
    assert 0.0 <= d <= 1.0
    deep_itm = bs_call_delta(S=300, K=100, T=1.0, sigma=0.3)
    assert deep_itm > 0.9
    deep_otm = bs_call_delta(S=30, K=100, T=1.0, sigma=0.3)
    assert deep_otm < 0.1


def test_solve_strike_for_delta_round_trips():
    S, T, sigma = 400.0, 2.0, 0.35
    for target in (0.55, 0.60, 0.65):
        K = solve_strike_for_delta(S, target, T, sigma)
        d = bs_call_delta(S, K, T, sigma)
        assert d == pytest.approx(target, abs=1e-6)


def test_target_delta_is_config_midpoint():
    cfg = {"leap": {"delta_min": 0.55, "delta_max": 0.65}}
    assert target_delta(cfg) == pytest.approx(0.60)


def test_higher_vol_means_higher_premium():
    low = bs_call_price(S=100, K=100, T=1.0, sigma=0.15)
    high = bs_call_price(S=100, K=100, T=1.0, sigma=0.50)
    assert high > low


def test_convexity_leap_move_exceeds_underlying_move():
    """The core fix this engine exists for: a 0.60-delta LEAP that runs
    ITM should show a LARGER percentage move than the underlying itself
    — genuine leverage, not the old flat-delta model's linear fraction."""
    S0, T0, sigma = 100.0, 2.0, 0.35
    K = solve_strike_for_delta(S0, 0.60, T0, sigma)
    premium0 = bs_call_price(S0, K, T0, sigma)

    S1, T1 = 150.0, 1.0   # underlying +50% a year later, K & sigma frozen
    premium1 = bs_call_price(S1, K, T1, sigma)

    underlying_move = (S1 - S0) / S0
    leap_move = (premium1 - premium0) / premium0
    assert leap_move > underlying_move


def test_realized_vol_is_forward_only():
    """LOOKAHEAD TEST: truncating future bars must not change realized
    vol at any earlier date — rolling() is backward-looking by
    construction, verified explicitly per the guardrail."""
    import numpy as np
    rng = np.random.default_rng(1)
    n = 500
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, n)),
                      index=pd.bdate_range("2020-01-01", periods=n))
    full = realized_vol(close)
    cut = 400
    trunc = realized_vol(close.iloc[:cut])
    pd.testing.assert_series_equal(full.iloc[:cut], trunc, check_names=False)


def test_realized_vol_positive_and_reasonable():
    import numpy as np
    rng = np.random.default_rng(2)
    n = 400
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))),
                      index=pd.bdate_range("2020-01-01", periods=n))
    vol = realized_vol(close)
    last = vol.iloc[-1]
    assert last == last            # not NaN
    assert 0.1 < last < 1.0        # sane annualized vol range
