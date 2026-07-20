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

    def step(self, price: float, ut_sell: bool):
        frac = price_fraction(price, self.dip_low, self.two_yr_high)
        if frac != frac:
            return False, None
        if frac >= 1.618:
            return True, "fib_1618_hard"
        if frac >= 0.9 and ut_sell:
            return True, "leap_ut_sell"
        return False, None
