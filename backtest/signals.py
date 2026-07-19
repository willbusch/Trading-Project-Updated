"""Per-strategy signal generation — pure functions: feature frame in,
per-bar entry/exit signal columns out. No portfolio state in here; the
simulator decides what signals become trades.

Entry logic (Addendum 2, 2026-07-19 — SMA(200) gate REMOVED from all
strategies, owner override):

  A: RSI(14) <= 35 on 3-day bars AND weekly not-making-lower-lows
  B: UT Bot buy signal (no weekly filter — B is the pure UT baseline)
  C: RSI <= 35 ARMS -> UT buy fires while armed, AND weekly filter
  D: RSI <= 35 ARMS -> volume > multiplier x avg fires while armed,
     AND weekly filter

Arm state machine (C and D, locked by Addendum 2): the arm sets when RSI
touches <= strategy_c.arm_touch_rsi_level, and cancels ONLY when RSI
crosses back above strategy_c.arm_expiry_rsi_level — no day cap, no
time-based backstop. A fired trigger consumes the arm (re-arming requires
a fresh RSI touch); a trigger on the same bar as the arming touch counts
(both are known at that bar's close). Consumption happens at SIGNAL
level — if the portfolio can't take the trade (slots/cash), that's a
missed trade in the report, not a preserved arm.

Exit hierarchy — ONE shared implementation for all strategies, priority
order: UT Bot sell (primary) > RSI >= 80 euphoria escape hatch >
[ablation-only] RSI 70-touch-then-cross-below-60 momentum exit. Exits are
full-position (locked plan decision; the partial trim/50% rules stay
scoped to the future live dashboard).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class AblationConfig:
    """Toggles threaded through signals AND simulator so ablation runs
    never duplicate engine logic. NOTE: the SMA(200) with/without ablation
    was deliberately DELETED (Addendum 2: full removal, not an ablation)."""
    ladder_enabled: bool = False          # 3-tranche ladder (primary = single entry)
    rsi_70_60_exit_enabled: bool = False  # retired momentum exit, ablation only
    include_leap: bool = True             # model the MSFT LEAP sleeve or equities-only


def compute_armed_and_trigger(
    rsi: pd.Series, trigger: pd.Series, arm_level: float, expiry_level: float
) -> pd.DataFrame:
    """Run the arm state machine over the bar sequence. Returns columns:
    armed (state as of each bar's close, AFTER consumption), fired (bool,
    trigger fired while armed on this bar), armed_at (the bar date of the
    arming touch, for arm-to-trigger lag stats), expired (bool, arm
    cancelled this bar by RSI reclaiming the expiry level)."""
    n = len(rsi)
    rsi_v = rsi.to_numpy(dtype=float)
    trig_v = trigger.to_numpy(dtype=bool)

    armed = np.zeros(n, dtype=bool)
    fired = np.zeros(n, dtype=bool)
    expired = np.zeros(n, dtype=bool)
    armed_at = np.full(n, None, dtype=object)
    expired_armed_at = np.full(n, None, dtype=object)  # arm date of an arm
    # that expired unfired on this bar — the forgone-return window is
    # [expired_armed_at[i], index[i]]

    is_armed = False
    armed_since = None
    for i in range(n):
        if np.isnan(rsi_v[i]):
            continue
        if is_armed and rsi_v[i] > expiry_level:
            is_armed = False
            expired_armed_at[i] = armed_since
            armed_since = None
            expired[i] = True
        if rsi_v[i] <= arm_level:
            if not is_armed:
                armed_since = rsi.index[i]
            is_armed = True
        if is_armed and trig_v[i]:
            fired[i] = True
            armed_at[i] = armed_since
            is_armed = False          # consumed
            armed_since = None
        armed[i] = is_armed

    return pd.DataFrame(
        {
            "armed": armed,
            "fired": fired,
            "armed_at": armed_at,
            "expired": expired,
            "expired_armed_at": expired_armed_at,
        },
        index=rsi.index,
    )


def compute_exit_signals(
    frame: pd.DataFrame, cfg: dict, ablation: AblationConfig
) -> pd.DataFrame:
    """The ONE shared exit-hierarchy computation, used identically by all
    four strategies. Returns columns: exit_signal (bool), exit_reason
    (str, the highest-priority reason on that bar)."""
    rsi = frame["rsi"]
    euphoria = rsi >= cfg["exit"]["rsi3_euphoria_threshold"]

    if ablation.rsi_70_60_exit_enabled:
        touch = cfg["exit"]["rsi3_momentum_touch_threshold"]
        cross = cfg["exit"]["rsi3_momentum_cross_below"]
        rsi_v = rsi.to_numpy(dtype=float)
        momentum = np.zeros(len(frame), dtype=bool)
        armed = False
        for i in range(len(frame)):
            if np.isnan(rsi_v[i]):
                continue
            if rsi_v[i] >= touch:
                armed = True
            elif armed and rsi_v[i] < cross:
                momentum[i] = True
                armed = False
        momentum = pd.Series(momentum, index=frame.index)
    else:
        momentum = pd.Series(False, index=frame.index)

    reason = pd.Series("", index=frame.index, dtype=object)
    reason[momentum] = "rsi_momentum_70_60"
    reason[euphoria] = "rsi_euphoria_80"
    reason[frame["ut_sell"]] = "ut_sell"          # highest priority last = wins
    return pd.DataFrame(
        {"exit_signal": reason != "", "exit_reason": reason}, index=frame.index
    )


def build_signal_frame(
    frame: pd.DataFrame,
    strategy: str,
    cfg: dict,
    ablation: AblationConfig,
    volume_multiplier: float | None = None,
) -> pd.DataFrame:
    """frame + entry_signal/exit_signal/exit_reason columns for one
    strategy ('A'|'B'|'C'|'D'), plus armed/fired/armed_at/expired columns
    for C and D (reporting needs them for the missed-trade/forgone-return
    and arm-to-trigger-lag stats)."""
    out = frame.copy()
    arm_level = cfg["strategy_c"]["arm_touch_rsi_level"]
    expiry_level = cfg["strategy_c"]["arm_expiry_rsi_level"]

    if strategy == "A":
        out["entry_signal"] = (
            (frame["rsi"] <= cfg["entry"]["rsi3_buy_threshold"]) & frame["weekly_ok"]
        )
    elif strategy == "B":
        out["entry_signal"] = frame["ut_buy"]
    elif strategy == "C":
        # weekly_ok is part of the trigger condition itself, so a UT buy
        # that fails the weekly filter does NOT consume the arm — the arm
        # stays live for a later qualifying trigger.
        trigger = frame["ut_buy"] & frame["weekly_ok"]
        arm = compute_armed_and_trigger(frame["rsi"], trigger, arm_level, expiry_level)
        out = out.join(arm)
        out["entry_signal"] = arm["fired"]
    elif strategy == "D":
        mult = (
            cfg["strategy_d"]["volume_multiplier"]
            if volume_multiplier is None
            else volume_multiplier
        )
        # same weekly-gate-inside-trigger rule as C
        vol_trigger = (frame["vol_ratio"] > mult) & frame["weekly_ok"]
        arm = compute_armed_and_trigger(frame["rsi"], vol_trigger, arm_level, expiry_level)
        out = out.join(arm)
        out["entry_signal"] = arm["fired"]
    else:
        raise ValueError(f"unknown strategy {strategy!r} (expected A/B/C/D)")

    exits = compute_exit_signals(frame, cfg, ablation)
    out["exit_signal"] = exits["exit_signal"]
    out["exit_reason"] = exits["exit_reason"]
    return out
