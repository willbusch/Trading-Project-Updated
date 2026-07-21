"""Synthetic-frame test for the 2026-07-21 ratio-based slot tiebreak:
drawdown / that name's own gate threshold, not raw drawdown. A mega-cap
with a shallower raw drawdown but a much easier gate should win a
contested slot over a small-cap with a deeper raw drawdown but a much
harder gate — the exact case the owner specified.
"""
import pandas as pd

from backtest.fib_simulator import simulate_fib


def _frame(dd_pct: float, gate_threshold: float, fire_day: pd.Timestamp,
          dates: pd.DatetimeIndex) -> pd.DataFrame:
    n = len(dates)
    close = pd.Series(100.0, index=dates)
    return pd.DataFrame({
        "Open": close, "High": close, "Low": close, "Close": close,
        "high_2yr": close / (1 - dd_pct),
        "dip_low": close * 0.9,
        "dd_pct": dd_pct,
        "gate_threshold": gate_threshold,
        "eligible": True,
        "stale": False,
        "gate_clear_date": dates[0],
        "entry_ut_buy": [d == fire_day for d in dates],
        "exit_ut_sell": False,
        "realized_vol": 0.3,
    }, index=dates)


def test_ratio_tiebreak_lets_easier_gated_mega_cap_win_over_deeper_raw_drawdown():
    dates = pd.bdate_range("2024-01-02", periods=10)
    fire_day = dates[2]

    # MEGA: 32% down, 25% gate -> ratio 1.28
    mega = _frame(dd_pct=0.32, gate_threshold=0.25, fire_day=fire_day, dates=dates)
    # SMALL: 44% down, 40% gate -> ratio 1.10 (deeper raw drawdown, but
    # a much harder gate to clear, so the ratio is lower)
    small = _frame(dd_pct=0.44, gate_threshold=0.40, fire_day=fire_day, dates=dates)

    frames = {"MEGA": mega, "SMALL": small}
    cfg = {
        "backtest": {"slippage_pct": 0.001, "seed_cash": 100_000.0},
        "sizing": {"equity_slots": 1, "leap_slots": 0, "max_position_pct_of_book": 0.5,
                  "min_cash_floor_pct": 0.0},
        "leap": {"sleeve_cap_pct_of_book": 0.0, "single_entry_pct_of_book": 0.0,
                "delta_min": 0.55, "delta_max": 0.65, "fib_modeled_expiry_years": 2.0},
        "circuit_breakers": {"max_new_positions_per_week": 5,
                            "account_drawdown_halt_pct": 0.99, "halt_duration_days": 30},
    }
    res = simulate_fib(frames, cfg, cell="test", leap_tickers=frozenset())

    entered = {t.ticker for t in res.trades}
    # only 1 equity slot -> exactly one of the two enters; it must be the
    # higher-ratio name (MEGA), not the deeper-raw-drawdown name (SMALL)
    assert entered == {"MEGA"}, (
        f"expected MEGA (ratio 1.28) to win the single slot over SMALL "
        f"(raw drawdown deeper but ratio only 1.10); entered={entered}"
    )
