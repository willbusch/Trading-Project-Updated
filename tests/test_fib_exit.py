import pandas as pd
import pytest

from backtest.drawdown_gate import (
    fib_levels,
    is_stale_anchor,
    price_fraction,
)
from backtest.fib_exit import EquityLatchExit, LeapSimpleExit


# dip_low=0, high=100 -> fraction == price/100, fib levels at the round numbers
def _eq():
    return EquityLatchExit(dip_low=0.0, two_yr_high=100.0)


def test_fib_levels_and_fraction():
    lv = fib_levels(0.0, 100.0)
    assert lv[0.5] == pytest.approx(50)
    assert lv[1.1] == pytest.approx(110)
    assert lv[1.618] == pytest.approx(161.8)
    assert price_fraction(55, 0.0, 100.0) == pytest.approx(0.55)


def test_equity_hold_below_05_no_exit():
    m = _eq()
    for p in [10, 30, 49]:
        assert m.step(p, ut_sell=False) == (False, None)
        assert m.step(p, ut_sell=True) == (False, None)  # no sell zone below 0.5


def test_equity_05_11_ut_sell_immediate_exit():
    m = _eq()
    assert m.step(70, ut_sell=False) == (False, None)
    assert m.step(70, ut_sell=True) == (True, "fib_05_11_ut_sell")


def test_equity_latch_arms_and_triggers_at_11():
    m = _eq()
    # in 1.1-1.5 zone, UT sell arms (no immediate exit)
    assert m.step(120, ut_sell=True) == (False, None)
    assert m.latch_armed
    # a UT BUY does not disarm (we just don't exit); still armed
    assert m.step(130, ut_sell=False) == (False, None)
    assert m.latch_armed
    # price falls back through 1.1 -> latch triggers full exit
    assert m.step(108, ut_sell=False) == (True, "fib_latch_trigger")


def test_equity_reaching_15_cancels_latch():
    m = _eq()
    m.step(120, ut_sell=True)          # arm in latch zone
    assert m.latch_armed
    assert m.step(150, ut_sell=False) == (False, None)   # reach 1.5 -> cancel
    assert not m.latch_armed
    # now below 1.1 again but latch was cancelled -> no trigger
    assert m.step(105, ut_sell=False) == (False, None)


def test_equity_15_16_ut_sell_exits():
    m = _eq()
    assert m.step(155, ut_sell=False) == (False, None)
    assert m.step(155, ut_sell=True) == (True, "fib_15_16_ut_sell")


def test_equity_1618_hard_exit_regardless():
    m = _eq()
    assert m.step(162, ut_sell=False) == (True, "fib_1618_hard")


def test_leap_simple_exit():
    m = LeapSimpleExit(dip_low=0.0, two_yr_high=100.0)
    assert m.step(85, ut_sell=True) == (False, None)          # below 0.9 hold
    assert m.step(95, ut_sell=False) == (False, None)
    assert m.step(95, ut_sell=True) == (True, "leap_ut_sell")  # 0.9-1.618 UT sell
    m2 = LeapSimpleExit(0.0, 100.0)
    assert m2.step(170, ut_sell=False) == (True, "fib_1618_hard")


def test_leap_no_latch():
    # LEAP machine has no latch attribute/behavior — a sell in 1.1-1.5 with
    # a later dip does NOT trigger anything (unlike equity)
    m = LeapSimpleExit(0.0, 100.0)
    assert m.step(120, ut_sell=True) == (True, "leap_ut_sell")  # exits immediately


def test_exit_machine_is_forward_only():
    """LOOKAHEAD TEST: a machine sees only the current bar. Feeding a price
    path, then the SAME path truncated, must give identical decisions up to
    the truncation point — proving no future bar can influence a decision."""
    path = [10, 30, 70, 120, 130, 108, 45, 200]
    full, trunc = _eq(), _eq()
    decisions_full, decisions_trunc = [], []
    for i, p in enumerate(path):
        decisions_full.append(full.step(p, ut_sell=(i == 3)))
    for i, p in enumerate(path[:5]):
        decisions_trunc.append(trunc.step(p, ut_sell=(i == 3)))
    assert decisions_full[:5] == decisions_trunc


def test_stale_anchor_detection():
    # Build a series: high peak, then a long depressed stretch >504d so the
    # peak ages out of the 2yr window but stays within the 4yr window.
    n = 1100
    close = pd.Series(
        [200.0] + [50.0] * (n - 1),
        index=pd.bdate_range("2020-01-01", periods=n),
    )
    stale = is_stale_anchor(close)
    # early on (peak still inside 504d) -> not stale; deep in the depressed
    # stretch (peak aged out, still in 4yr window) -> stale
    assert not stale.iloc[400]
    assert stale.iloc[900]
