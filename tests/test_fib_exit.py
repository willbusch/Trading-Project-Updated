import pandas as pd
import pytest

from backtest.drawdown_gate import (
    fib_levels,
    is_stale_anchor,
    price_fraction,
)
from backtest.fib_exit import (
    EquityLatchExit,
    FullLatchExitV2,
    LeapSimpleExit,
    SimpleFloorExit,
)


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


def _v2():
    return FullLatchExitV2(dip_low=0.0, two_yr_high=100.0)


def test_simple_floor_exit_05_matches_old_change1_default():
    m = SimpleFloorExit(0.0, 100.0, floor=0.5)
    assert m.step(30, ut_sell=True) == (False, None)           # below floor
    assert m.step(70, ut_sell=False) == (False, None)
    assert m.step(70, ut_sell=True) == (True, "simple_05_ut_sell")
    m2 = SimpleFloorExit(0.0, 100.0, floor=0.5)
    assert m2.step(162, ut_sell=False) == (True, "fib_1618_hard")


def test_simple_floor_exit_09_matches_leap_simple_shape():
    m = SimpleFloorExit(0.0, 100.0, floor=0.9)
    assert m.step(85, ut_sell=True) == (False, None)           # below 0.9
    assert m.step(95, ut_sell=True) == (True, "simple_09_ut_sell")


def test_v2_hold_below_05():
    m = _v2()
    for p in [10, 30, 49]:
        assert m.step(p, ut_sell=True) == (False, None)


def test_v2_05_09_latch_arms_and_triggers_at_05():
    m = _v2()
    assert m.step(70, ut_sell=True) == (False, None)           # arm in 0.5-0.9
    assert m.latch_09_armed
    assert m.step(80, ut_sell=False) == (False, None)          # buy-equivalent: stays armed
    assert m.latch_09_armed
    assert m.step(45, ut_sell=False) == (True, "latch_v2_09_trigger")  # falls to 0.5 -> exit


def test_v2_09_11_immediate_zone():
    m = _v2()
    assert m.step(100, ut_sell=False) == (False, None)
    assert m.step(100, ut_sell=True) == (True, "latch_v2_09_11_ut_sell")


def test_v2_11_15_latch_arms_and_triggers_at_11():
    m = _v2()
    assert m.step(120, ut_sell=True) == (False, None)          # arm in 1.1-1.5
    assert m.latch_11_armed
    assert m.step(105, ut_sell=False) == (True, "latch_v2_11_trigger")


def test_v2_higher_zone_supersedes_lower_latch():
    m = _v2()
    m.step(70, ut_sell=True)                                   # arm 0.5-0.9 latch
    assert m.latch_09_armed
    m.step(100, ut_sell=False)                                 # rise into 0.9-1.1 (no sell)
    assert not m.latch_09_armed                                # superseded, cleared
    # falling all the way back to 0.5 now should NOT trigger the old arm
    assert m.step(45, ut_sell=False) == (False, None)


def test_v2_touching_15_arms_permanently_survives_pullback():
    """The owner's explicit example: touch 1.5, pull back, a later UT sell
    at 1.43 (still >0.5, below 1.5) exits anyway."""
    m = _v2()
    assert m.step(150, ut_sell=False) == (False, None)         # touch 1.5, no sell yet
    assert m.touched_15
    assert m.step(143, ut_sell=False) == (False, None)         # pulled back, no sell
    assert m.step(143, ut_sell=True) == (True, "latch_v2_touched15_ut_sell")


def test_v2_touched_15_beats_lower_zone_arming_logic():
    """Once touched_15, the position no longer arms/re-arms lower latches —
    it's governed solely by the permanent rule until it exits."""
    m = _v2()
    m.step(150, ut_sell=False)                                 # touch 1.5
    m.step(70, ut_sell=True)                                   # deep pullback with a sell signal
    # touched_15 path returns on ut_sell, so this should have exited already;
    # verify directly instead with a non-selling pullback then a later sell
    m2 = _v2()
    m2.step(150, ut_sell=False)
    m2.step(70, ut_sell=False)                                 # pullback, no sell
    assert not m2.latch_09_armed                                # never armed via the old zone logic
    assert m2.step(70, ut_sell=True) == (True, "latch_v2_touched15_ut_sell")


def test_v2_hard_exit_at_1618_regardless_of_state():
    m = _v2()
    assert m.step(162, ut_sell=False) == (True, "fib_1618_hard")


def test_v2_is_forward_only():
    """LOOKAHEAD TEST for the new exit variant, same structural proof as
    the original EquityLatchExit test."""
    path = [10, 60, 100, 120, 150, 143, 90, 200]
    full, trunc = _v2(), _v2()
    decisions_full = [full.step(p, ut_sell=(i in (1, 5))) for i, p in enumerate(path)]
    decisions_trunc = [trunc.step(p, ut_sell=(i in (1, 5))) for i, p in enumerate(path[:6])]
    assert decisions_full[:6] == decisions_trunc


def test_hybrid_anchor_uses_extended_high_when_504_is_stale():
    from backtest.drawdown_gate import hybrid_anchor_high
    n = 1100
    close = pd.Series(
        [200.0] + [50.0] * (n - 1),
        index=pd.bdate_range("2020-01-01", periods=n),
    )
    high, extended = hybrid_anchor_high(close)
    # deep in the depressed stretch the 504d high has decayed to 50, but the
    # extended window still sees the 200 peak -> hybrid uses 200
    assert high.iloc[900] == pytest.approx(200.0)
    assert extended.iloc[900]
    # early on, the 200 peak is still inside 504d -> not extended, high==200
    assert not extended.iloc[400]


def test_hybrid_anchor_is_forward_only():
    """LOOKAHEAD TEST for CHANGE 2: the extended high at date D must equal
    the max of close up to D only. Truncating future bars must not change
    the anchor at any earlier date."""
    from backtest.drawdown_gate import hybrid_anchor_high
    import numpy as np
    rng = np.random.default_rng(0)
    n = 1300
    close = pd.Series(
        100 + np.cumsum(rng.normal(0, 1, n)),
        index=pd.bdate_range("2019-01-01", periods=n),
    )
    full, _ = hybrid_anchor_high(close)
    cut = 1000
    trunc, _ = hybrid_anchor_high(close.iloc[:cut])
    # anchors on the shared prefix must be identical
    pd.testing.assert_series_equal(full.iloc[:cut], trunc, check_names=False)


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
