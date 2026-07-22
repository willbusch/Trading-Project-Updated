"""The latched-Fib exit state machines (equity + LEAP), as forward-only
per-position objects.

LOOKAHEAD GUARANTEE (the strategy's #1 risk): each machine exposes a
single `step(price, ut_sell)` method that advances by exactly one daily
bar. It has NO access to any series, index, or future bar — only the
current bar's price, the current bar's exit-timeframe UT-sell event, and
its own accumulated state (which was built solely from prior bars). A
machine therefore CANNOT reference the future; the lookahead test asserts
this structurally (feeding a truncated vs. full price path yields
identical decisions up to the truncation point).

Anchors (dip_low, two_yr_high, and thus every Fib level) are frozen at
entry and never updated — also forward-only.
"""
from dataclasses import dataclass, field

from backtest.drawdown_gate import fib_levels, price_fraction


@dataclass
class EquityLatchExit:
    """0.0-0.5 hold · 0.5-1.1 UT sell→exit · 1.1-1.5 latch (UT sell arms,
    trigger=1.1 level; UT buy does NOT disarm) · 1.5-1.618 reaching 1.5
    cancels latch, UT sell→exit · 1.618 hard exit."""
    dip_low: float
    two_yr_high: float
    latch_armed: bool = False
    levels: dict = field(default_factory=dict)

    def __post_init__(self):
        self.levels = fib_levels(self.dip_low, self.two_yr_high)

    def step(self, price: float, ut_sell: bool):
        """Return (exit: bool, reason: str|None) for this daily bar."""
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:                       # NaN degenerate move
            return False, None
        if frac >= 1.618:
            return True, "fib_1618_hard"
        if frac >= 1.5:
            self.latch_armed = False           # entering 1.5 cancels the latch
            if ut_sell:
                return True, "fib_15_16_ut_sell"
            return False, None
        if frac >= 1.1:                         # latch zone 1.1-1.5
            if ut_sell:
                self.latch_armed = True         # arm; trigger = the 1.1 level
            return False, None
        if frac >= 0.5:                         # 0.5-1.1
            if self.latch_armed:                # armed + price fell to/through 1.1
                return True, "fib_latch_trigger"
            if ut_sell:
                return True, "fib_05_11_ut_sell"
            return False, None
        # frac < 0.5
        if self.latch_armed:                    # armed + price fell below 1.1
            return True, "fib_latch_trigger"
        return False, None                      # no exit below 0.5 unarmed


@dataclass
class LeapSimpleExit:
    """below 0.9 hold · 0.9-1.618 any UT sell→exit · 1.618 hard exit.
    No latch (owner-specified)."""
    dip_low: float
    two_yr_high: float
    levels: dict = field(default_factory=dict)

    def __post_init__(self):
        self.levels = fib_levels(self.dip_low, self.two_yr_high)

    def step(self, price: float, ut_sell: bool, age_frac: float = 0.0):
        # age_frac accepted (and ignored) so the simulator can pass it
        # uniformly to whichever LEAP exit machine (this one or
        # LeapDecayExit) is active without branching on type.
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:
            return False, None
        if frac >= 1.618:
            return True, "fib_1618_hard"
        if frac >= 0.9 and ut_sell:
            return True, "leap_ut_sell"
        return False, None


@dataclass
class SimpleFloorExit:
    """CHANGE 1 (12-name round) generalized: below `floor` hold; floor→1.618
    any UT sell→exit; 1.618 hard exit. No latch. `floor` is 0.5 (the
    12-name-round champion, "Variant 1") or 0.9 (owner's earlier idea,
    "Variant 2") in the 2026-07-20 three-way exit ablation. Reused for
    both equities and LEAPs when a ablation cell calls for it."""
    dip_low: float
    two_yr_high: float
    floor: float = 0.5
    levels: dict = field(default_factory=dict)

    def __post_init__(self):
        self.levels = fib_levels(self.dip_low, self.two_yr_high)

    def step(self, price: float, ut_sell: bool):
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:
            return False, None
        if frac >= 1.618:
            return True, "fib_1618_hard"
        if frac >= self.floor and ut_sell:
            return True, f"simple_{str(self.floor).replace('.', '')}_ut_sell"
        return False, None


@dataclass
class LeapDecayExit:
    """A5 (2026-07-22, "Beat-SPY Package"): same shape as LeapSimpleExit
    (below floor hold · floor-1.618 any UT sell -> exit · 1.618 hard exit,
    no latch) EXCEPT the floor tightens 0.9 -> 0.7 once the position has
    burned >= `tighten_at_frac` of its modeled runway to expiry. This is a
    risk-REDUCTION mechanic (a tighter floor makes an ordinary UT sell
    fire sooner as the option ages), explicitly NOT a hard time-based
    force-close — a LEAP that never gets a UT sell signal above the
    tightened floor still rides to 1.618 or modeled expiry exactly as
    before. `age_frac` (0.0-1.0+, elapsed/T0) is supplied by the simulator
    each bar from the position's own entry/expiry dates — this class holds
    no calendar state of its own, so it stays a pure step(price, ut_sell,
    age_frac) function, same lookahead guarantee as every other machine
    here (each call sees only the current bar's inputs)."""
    dip_low: float
    two_yr_high: float
    tighten_at_frac: float = 0.5
    floor_before: float = 0.9
    floor_after: float = 0.7
    levels: dict = field(default_factory=dict)

    def __post_init__(self):
        self.levels = fib_levels(self.dip_low, self.two_yr_high)

    def step(self, price: float, ut_sell: bool, age_frac: float = 0.0):
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:
            return False, None
        if frac >= 1.618:
            return True, "fib_1618_hard"
        floor = self.floor_after if age_frac >= self.tighten_at_frac else self.floor_before
        if frac >= floor and ut_sell:
            return True, f"leap_decay_ut_sell_floor{floor}"
        return False, None


@dataclass
class TrailingFibExit:
    """A7 (2026-07-22, "Beat-SPY Package"): equity exit. UNCHANGED below
    1.618 — hold below `floor` (0.9), any weekly UT sell in the
    floor-1.618 zone exits (identical to SimpleFloorExit(floor=0.9), aka
    "simple_09"). CHANGED at 1.618: touching it no longer hard-sells.
    Instead the position switches PERMANENTLY into trailing mode:
      - mechanic="ut_trail": exit on the next UT-sell event while trailing
        (same signal, just no longer capped at the 1.618 hard-exit).
      - mechanic="pct_trail": exit once price retraces >= `pct_trail_pct`
        from the RUNNING PEAK PRICE observed since entering trailing mode.
    Peak-price tracking is forward-only by construction: `peak_price` is
    updated once per `step()` call from that bar's price only, so it can
    never reflect a future bar (lookahead test: truncating the price path
    fed to step() must reproduce identical decisions up to the truncation
    point, same discipline as every other machine in this file)."""
    dip_low: float
    two_yr_high: float
    floor: float = 0.9
    mechanic: str = "ut_trail"          # "ut_trail" | "pct_trail"
    pct_trail_pct: float = 0.20
    trailing: bool = False
    peak_price: float = float("-inf")
    levels: dict = field(default_factory=dict)

    def __post_init__(self):
        self.levels = fib_levels(self.dip_low, self.two_yr_high)

    def step(self, price: float, ut_sell: bool):
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:
            return False, None

        if not self.trailing:
            if frac >= 1.618:
                self.trailing = True
                self.peak_price = price
                # fall through to trailing logic below on this same bar
            else:
                if frac >= self.floor and ut_sell:
                    return True, "trail_floor_ut_sell"
                return False, None

        self.peak_price = max(self.peak_price, price)
        if self.mechanic == "ut_trail":
            if ut_sell:
                return True, "trail_ut_exit"
            return False, None
        retrace = 1.0 - (price / self.peak_price) if self.peak_price > 0 else 0.0
        if retrace >= self.pct_trail_pct:
            return True, f"trail_pct_{self.pct_trail_pct}_exit"
        return False, None


@dataclass
class FullLatchExitV2:
    """2026-07-20 three-way exit ablation, "Variant 3" — the owner's new
    full latched design, implemented exactly as specified:

      0.0 - 0.5   hold, nothing sells
      0.5 - 0.9   latch: UT sell arms (trigger = 0.5); falling to 0.5 -> exit
      0.9 - 1.1   immediate: any UT sell -> exit
      1.1 - 1.5   latch: UT sell arms (trigger = 1.1); falling to 1.1 -> exit
      touched 1.5+  PERMANENT arm: any SUBSEQUENT UT sell -> exit, at ANY
                    price level below 1.618, even if price has since fallen
                    back below 1.5 (explicit owner example: sell at 1.43
                    after having touched 1.5 -> exit). This is deliberately
                    a REVERSAL of the prior EquityLatchExit design, where
                    reaching 1.5 CANCELED the latch — here touching 1.5
                    ARMS one instead. Not a bug; the owner's new spec.
      1.618       hard automatic exit

    JUDGMENT CALL (documented, not silently resolved): "entering a higher
    regime supersedes the lower latch" is read as — moving into a higher
    zone without the lower latch having fired clears that lower latch's
    arm state; it does not carry forward if price later falls back into
    that zone (a fresh UT-sell arm is required to re-arm). The permanent
    1.5-touch arm is the one exception: once set, it is checked BEFORE
    any zone-specific logic and never cleared (short of a hard exit ending
    the position). A UT BUY never disarms anything, matching the original
    design.

    Trigger checks use `frac <= threshold` (not an exact zone-crossing
    check) so a single-bar gap through a zone still fires the trigger —
    same defensive handling as the original EquityLatchExit's boundary
    logic, extended to two latch levels.
    """
    dip_low: float
    two_yr_high: float
    latch_09_armed: bool = False   # 0.5-0.9 zone, trigger = 0.5
    latch_11_armed: bool = False   # 1.1-1.5 zone, trigger = 1.1
    touched_15: bool = False       # permanent once True
    levels: dict = field(default_factory=dict)

    def __post_init__(self):
        self.levels = fib_levels(self.dip_low, self.two_yr_high)

    def step(self, price: float, ut_sell: bool):
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:
            return False, None

        if frac >= 1.5:
            self.touched_15 = True

        if frac >= 1.618:
            return True, "fib_1618_hard"

        if self.touched_15:
            if ut_sell:
                return True, "latch_v2_touched15_ut_sell"
            return False, None                  # supersedes all lower-zone logic

        if self.latch_11_armed and frac <= 1.1:
            self.latch_11_armed = False
            return True, "latch_v2_11_trigger"

        if self.latch_09_armed and frac <= 0.5:
            self.latch_09_armed = False
            return True, "latch_v2_09_trigger"

        if 0.9 <= frac < 1.1:                   # immediate zone
            self.latch_09_armed = False         # superseded by higher zone
            if ut_sell:
                return True, "latch_v2_09_11_ut_sell"
            return False, None

        if 1.1 <= frac < 1.5:                   # latch zone (trigger 1.1)
            self.latch_09_armed = False         # superseded
            if ut_sell:
                self.latch_11_armed = True
            return False, None

        if 0.5 <= frac < 0.9:                   # latch zone (trigger 0.5)
            if ut_sell:
                self.latch_09_armed = True
            return False, None

        return False, None                      # frac < 0.5: hold
