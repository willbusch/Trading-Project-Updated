"""LEAP pricing for the backtest — model choice, delta resolution, and the
per-name label every report row must carry (Addendum 2 requirement).

FEASIBILITY SPIKE RESULT (2026-07-19, recorded so this decision is
auditable): Robinhood's option-historicals endpoint DOES serve full daily
OHLC history for EXPIRED contracts — tested on the MSFT 2023-06-16 $300
call: 493/493 real bars (zero interpolated), 2021-07-01 through
2023-06-15. So real historical LEAP premiums are available in principle.

Why this pass still uses the delta-adjusted approximation UNIFORMLY:
  1. Historical greeks are NOT served, so selecting "the 0.50-0.60-delta,
     18+-month contract" at each historical entry date requires a pricing
     model anyway — real premiums don't remove the modeling assumption,
     they move it into contract selection.
  2. Sweep and ablation variants shift entry dates, each needing its own
     agent-orchestrated fetches (MCP tools are not callable from Python).
     Pricing headline runs on real premiums while sweeps use the
     approximation would make the A/B/C/D comparison internally
     inconsistent.
  For an ENGINE-VALIDATION pass, one consistent, honestly-labeled model
  beats a mixed one. Upgrade path for a future proof-of-edge pass: entry
  dates are deterministic from signal frames, so contracts can be
  pre-selected and their real bars ingested before simulation.

The approximation (implemented in portfolio_state.Position.market_value
and the simulator's exit fill): LEAP P&L = static delta x the P&L of an
equivalent-notional share position, delta held constant for the trade's
life at the midpoint of the owner's configured range. Understates option
leverage; ignores theta decay and IV changes. Every trade row it touches
is labeled PRICING_LABEL.
"""

PRICING_LABEL = "leap_delta_approx"


def leap_delta(cfg: dict) -> float:
    """Static delta used for the trade's life: midpoint of the owner's
    configured delta range (0.50-0.60 per the 2026-07-19 override -> 0.55).
    Config-derived, not a free parameter."""
    return (cfg["leap"]["delta_min"] + cfg["leap"]["delta_max"]) / 2
