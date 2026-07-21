"""Black-Scholes delta-curve LEAP pricing engine (2026-07-21).

RETIRES the flat delta-adjusted approximation in `backtest/leap_pricing.py`
(kept in code for reference only, no longer used by the simulator).

ARCHITECTURE CONSTRAINT this design works around: the simulator is a
standalone Python module and cannot call Robinhood MCP tools mid-run, so
"real Robinhood historical option prices" cannot be the LIVE pricing
engine driving the backtest loop — that would require knowing which LEAP
trades occur before running the simulation that decides them. This module
is instead a genuine options-pricing model: real convexity, real theta
decay, real delta evolution toward 1.0 as the underlying moves ITM, and
(new) a genuine possibility of expiring worthless — none of which the
flat approximation could produce. After a run, the specific LEAP trades it
produces can be spot-checked against real historical option data as a
validation layer (see scripts/leap_pricing_validation.py) — that is the
"real data" half of the fix; this module is the "delta-curve fallback"
half, and per the owner's guardrail, every LEAP row is flagged with which
applies.

Strike K and volatility sigma are FROZEN at entry:
  - sigma = the underlying's own trailing realized volatility as of the
    ENTRY SIGNAL bar (not the fill bar) — a standard proxy for implied
    vol when no historical vol surface is available. Forward-only by
    construction (a trailing rolling stat).
  - K is solved from the target delta (0.55-0.65 midpoint = 0.60) at
    entry via the closed-form delta inversion below.
Only the underlying price S and remaining time T evolve day to day as the
position is marked to market — this is what produces real theta and real
convexity, without needing daily option quotes.

Disclosed simplifications (minor next to the core convexity fix):
  - sigma is REALIZED (trailing) volatility, not implied, and held
    constant for the trade's life rather than following a real IV
    surface that moves independently of realized vol.
  - the risk-free rate is a constant assumption — no historical yield
    curve is available from this data source either.
"""
import math
from statistics import NormalDist

PRICING_LABEL = "black_scholes_delta_curve"
RISK_FREE_RATE = 0.04           # constant assumption; no historical yield curve available
CONTRACT_MULTIPLIER = 100
REALIZED_VOL_WINDOW = 252       # trading days, ~1yr trailing


def target_delta(cfg: dict) -> float:
    """Midpoint of the owner's configured delta range (0.55-0.65 -> 0.60)."""
    return (cfg["leap"]["delta_min"] + cfg["leap"]["delta_max"]) / 2


def bs_call_price(S: float, K: float, T: float, sigma: float, r: float = RISK_FREE_RATE) -> float:
    """European call price (Black-Scholes). T in years. Degenerates to
    intrinsic value at/after expiry or on a degenerate input — this is
    exactly how a real option behaves at T=0, and is how "expired
    worthless" (S < K) becomes representable again."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(S - K, 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * NormalDist().cdf(d1) - K * math.exp(-r * T) * NormalDist().cdf(d2)


def bs_call_delta(S: float, K: float, T: float, sigma: float, r: float = RISK_FREE_RATE) -> float:
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 1.0 if S > K else 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return NormalDist().cdf(d1)


def solve_strike_for_delta(S: float, delta: float, T: float, sigma: float,
                          r: float = RISK_FREE_RATE) -> float:
    """Invert delta = N(d1) for K, given S, T, sigma, r — closed-form,
    no iterative solver needed. Used ONLY at entry, from data available
    at (or before) the entry signal bar."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return S
    d1 = NormalDist().inv_cdf(delta)
    rhs = d1 * sigma * math.sqrt(T) - (r + 0.5 * sigma * sigma) * T
    return S / math.exp(rhs)


def realized_vol(close, window: int = REALIZED_VOL_WINDOW):
    """Annualized trailing realized volatility from daily log returns.
    A pandas Series in, a pandas Series out — rolling(), so forward-only
    by construction (no future bar can enter a trailing window)."""
    import numpy as np
    log_ret = np.log(close / close.shift(1))
    return log_ret.rolling(window, min_periods=window).std() * math.sqrt(252)
