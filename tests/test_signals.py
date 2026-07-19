import numpy as np
import pandas as pd
import pytest

from backtest.signals import (
    AblationConfig,
    build_signal_frame,
    compute_armed_and_trigger,
    compute_exit_signals,
)

CFG = {
    "entry": {"rsi3_buy_threshold": 35},
    "exit": {
        "rsi3_euphoria_threshold": 80,
        "rsi3_momentum_touch_threshold": 70,
        "rsi3_momentum_cross_below": 60,
    },
    "strategy_c": {"arm_touch_rsi_level": 35, "arm_expiry_rsi_level": 50},
    "strategy_d": {"volume_multiplier": 1.25},
}


def _frame(rsi, ut_buy=None, ut_sell=None, weekly_ok=None, vol_ratio=None):
    n = len(rsi)
    idx = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame(
        {
            "rsi": rsi,
            "ut_buy": ut_buy if ut_buy is not None else [False] * n,
            "ut_sell": ut_sell if ut_sell is not None else [False] * n,
            "weekly_ok": weekly_ok if weekly_ok is not None else [True] * n,
            "vol_ratio": vol_ratio if vol_ratio is not None else [1.0] * n,
        },
        index=idx,
    )


def test_strategy_a_needs_rsi_and_weekly_and_has_no_sma_gate():
    f = _frame(
        rsi=[40, 35, 30, 40, 30],
        weekly_ok=[True, True, False, True, True],
    )
    out = build_signal_frame(f, "A", CFG, AblationConfig())
    # bar1: rsi 35 <= 35 & weekly ok -> entry; bar2: rsi 30 but weekly fails;
    # bar4: rsi 30 & weekly ok -> entry
    assert out["entry_signal"].tolist() == [False, True, False, False, True]


def test_strategy_b_is_pure_ut_buy():
    f = _frame(rsi=[50] * 4, ut_buy=[False, True, False, True], weekly_ok=[False] * 4)
    out = build_signal_frame(f, "B", CFG, AblationConfig())
    # weekly filter is irrelevant to B
    assert out["entry_signal"].tolist() == [False, True, False, True]


def test_arm_machine_arms_fires_and_consumes():
    # rsi dips to 35 (arm), stays low, trigger fires twice — only the
    # first fire counts (arm consumed), until a re-touch re-arms.
    rsi = pd.Series([40, 35, 45, 45, 45, 34, 45], dtype=float)
    trig = pd.Series([False, False, False, True, True, False, True])
    res = compute_armed_and_trigger(rsi, trig, 35, 50)
    assert res["fired"].tolist() == [False, False, False, True, False, False, True]
    # armed_at records the arming touch bar for lag stats
    assert res["armed_at"].iloc[3] == rsi.index[1]
    assert res["armed_at"].iloc[6] == rsi.index[5]


def test_arm_expires_only_on_rsi_reclaiming_50_no_day_cap():
    # rsi arms at 35, then hovers in 36..49 for many bars — arm must stay
    # live indefinitely (no day cap), then die the bar rsi exceeds 50.
    hover = [36, 49, 48, 47, 46, 45, 44, 43, 42, 41, 49, 49, 49, 49, 49]
    rsi = pd.Series([35.0] + hover + [51.0, 45.0], dtype=float)
    trig = pd.Series([False] * len(rsi))
    res = compute_armed_and_trigger(rsi, trig, 35, 50)
    assert res["armed"].iloc[: len(hover) + 1].all()  # live through the hover
    assert res["expired"].iloc[len(hover) + 1] == True  # noqa: E712
    assert not res["armed"].iloc[len(hover) + 1 :].any()  # 45 alone doesn't re-arm


def test_arm_same_bar_touch_and_trigger_fires():
    rsi = pd.Series([45.0, 33.0], dtype=float)
    trig = pd.Series([False, True])
    res = compute_armed_and_trigger(rsi, trig, 35, 50)
    assert res["fired"].iloc[1] == True  # noqa: E712


def test_strategy_c_weekly_blocked_trigger_preserves_arm():
    # armed at bar1; UT buy at bar2 fails weekly filter -> no entry, arm
    # survives; UT buy at bar4 with weekly ok -> entry.
    f = _frame(
        rsi=[45, 34, 45, 45, 45],
        ut_buy=[False, False, True, False, True],
        weekly_ok=[True, True, False, True, True],
    )
    out = build_signal_frame(f, "C", CFG, AblationConfig())
    assert out["entry_signal"].tolist() == [False, False, False, False, True]


def test_strategy_d_volume_trigger_and_sweep_override():
    f = _frame(
        rsi=[34, 45, 45, 45],
        vol_ratio=[1.0, 1.1, 1.3, 2.1],
    )
    out = build_signal_frame(f, "D", CFG, AblationConfig())
    # default 1.25x: fires at bar2 (1.3)
    assert out["entry_signal"].tolist() == [False, False, True, False]
    # swept to 2.0x: bar2's 1.3 no longer qualifies; fires at bar3 (2.1)
    out2 = build_signal_frame(f, "D", CFG, AblationConfig(), volume_multiplier=2.0)
    assert out2["entry_signal"].tolist() == [False, False, False, True]


def test_exit_hierarchy_priority_ut_over_euphoria_over_momentum():
    f = _frame(
        rsi=[85, 85, 50],
        ut_sell=[True, False, False],
    )
    ab = AblationConfig(rsi_70_60_exit_enabled=True)
    exits = compute_exit_signals(f, CFG, ab)
    # bar0: both UT sell and rsi>=80 true -> UT wins the reason field
    assert exits["exit_reason"].iloc[0] == "ut_sell"
    assert exits["exit_reason"].iloc[1] == "rsi_euphoria_80"
    # bar2: momentum exit (touched >=70 at bars 0-1, crossed below 60)
    assert exits["exit_reason"].iloc[2] == "rsi_momentum_70_60"
    # and with the ablation OFF (primary config) the momentum exit is dead
    exits_primary = compute_exit_signals(f, CFG, AblationConfig())
    assert exits_primary["exit_signal"].tolist() == [True, True, False]


def test_unknown_strategy_raises():
    with pytest.raises(ValueError):
        build_signal_frame(_frame(rsi=[50.0]), "E", CFG, AblationConfig())


def test_nan_rsi_warmup_never_arms_or_enters():
    f = _frame(rsi=[np.nan, np.nan, 34, 45], ut_buy=[True, True, False, True])
    out = build_signal_frame(f, "C", CFG, AblationConfig())
    assert out["entry_signal"].tolist() == [False, False, False, True]
