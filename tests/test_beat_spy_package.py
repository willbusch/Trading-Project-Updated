"""Simulator-level integration tests for the 2026-07-22 "Beat-SPY Package":
the fill-order bug fix (found while implementing this round), A2
(top-10-cap LEAP eligibility wired into the entry-kind decision), and A4
(slot-time recycling valve)."""
import pandas as pd

from backtest.fib_simulator import simulate_fib


def _synthetic_frame(dates, fire_day, dd_pct, gate_threshold, price=100.0):
    close = pd.Series(price, index=dates)
    return pd.DataFrame({
        "Open": close, "High": close, "Low": close, "Close": close,
        "high_2yr": close / (1 - dd_pct), "dip_low": close * 0.9,
        "dd_pct": dd_pct, "gate_threshold": gate_threshold,
        "eligible": True, "stale": False, "gate_clear_date": dates[0],
        "entry_ut_buy": [d == fire_day for d in dates], "exit_ut_sell": False,
        "realized_vol": 0.3,
    }, index=dates)


def _base_cfg(equity_slots=1, leap_slots=0):
    return {
        "backtest": {"slippage_pct": 0.001, "seed_cash": 1_000_000.0},
        "sizing": {"equity_slots": equity_slots, "leap_slots": leap_slots,
                  "max_position_pct_of_book": 0.5, "min_cash_floor_pct": 0.0},
        "leap": {"sleeve_cap_pct_of_book": 0.5, "single_entry_pct_of_book": 0.5,
                "delta_min": 0.55, "delta_max": 0.65, "fib_modeled_expiry_years": 2.0},
        "circuit_breakers": {"max_new_positions_per_week": 5,
                            "account_drawdown_halt_pct": 0.99, "halt_duration_days": 30},
    }


def test_fill_order_respects_ratio_rank_not_alphabetical():
    """Regression for the bug found 2026-07-22: step 2 used to iterate
    `sorted(pending_entries)` (alphabetical), silently overriding the
    ratio-based rank order computed in step 3. AAA sorts before ZZZ
    alphabetically but has the WORSE ratio here — under the bug AAA would
    win the single slot; after the fix ZZZ (better ratio) must win."""
    dates = pd.bdate_range("2024-01-02", periods=10)
    fire_day = dates[2]
    aaa = _synthetic_frame(dates, fire_day, dd_pct=0.44, gate_threshold=0.40)  # ratio 1.10
    zzz = _synthetic_frame(dates, fire_day, dd_pct=0.32, gate_threshold=0.25)  # ratio 1.28
    frames = {"AAA": aaa, "ZZZ": zzz}
    res = simulate_fib(frames, _base_cfg(), cell="test", leap_tickers=frozenset())
    entered = {t.ticker for t in res.trades}
    assert entered == {"ZZZ"}, (
        f"expected ZZZ (better ratio 1.28) to win over AAA (ratio 1.10, but "
        f"alphabetically first); entered={entered} — fill-order bug regressed"
    )


def test_leap_topcap_eligibility_wired_into_simulator_kind_decision():
    """A2: when leap_topcap_eligibility=True, entry KIND is decided by the
    frozen leap_eligible_topcap column, not the static leap_tickers set."""
    dates = pd.bdate_range("2024-01-02", periods=10)
    fire_day = dates[2]
    bigco = _synthetic_frame(dates, fire_day, dd_pct=0.30, gate_threshold=0.30)
    bigco["leap_eligible_topcap"] = True
    smallco = _synthetic_frame(dates, fire_day, dd_pct=0.30, gate_threshold=0.30)
    smallco["leap_eligible_topcap"] = False

    cfg = _base_cfg(equity_slots=5, leap_slots=1)
    res = simulate_fib(
        {"BIGCO": bigco, "SMALLCO": smallco}, cfg, cell="test",
        leap_tickers=frozenset(),   # static set says NEITHER is a LEAP name
        leap_topcap_eligibility=True,
    )
    kinds = {t.ticker: t.kind for t in res.trades}
    assert kinds.get("BIGCO") == "leap"
    assert kinds.get("SMALLCO") == "equity"


def test_leap_topcap_eligibility_off_falls_back_to_static_set():
    """Backward compatibility: leap_topcap_eligibility=False (default) must
    reproduce the pre-A2 behavior even if a topcap column is present."""
    dates = pd.bdate_range("2024-01-02", periods=10)
    fire_day = dates[2]
    bigco = _synthetic_frame(dates, fire_day, dd_pct=0.30, gate_threshold=0.30)
    bigco["leap_eligible_topcap"] = True
    cfg = _base_cfg(equity_slots=5, leap_slots=1)
    res = simulate_fib({"BIGCO": bigco}, cfg, cell="test", leap_tickers=frozenset())
    kinds = {t.ticker: t.kind for t in res.trades}
    assert kinds.get("BIGCO") == "equity"   # static set (empty) still governs


def _recycling_frames(old_price_after_entry: float):
    n = 400
    dates = pd.bdate_range("2020-01-02", periods=n)
    old_fire, new_fire = dates[2], dates[380]

    old_price = pd.Series(100.0, index=dates)
    old_price.loc[dates[50]:] = old_price_after_entry
    old = pd.DataFrame({
        "Open": old_price, "High": old_price, "Low": old_price, "Close": old_price,
        "high_2yr": 10_000.0, "dip_low": 0.0, "dd_pct": 0.30, "gate_threshold": 0.30,
        "eligible": [d == old_fire for d in dates], "stale": False,
        "gate_clear_date": dates[0],
        "entry_ut_buy": [d == old_fire for d in dates], "exit_ut_sell": False,
        "realized_vol": 0.3,
    }, index=dates)

    new_price = pd.Series(50.0, index=dates)
    new = pd.DataFrame({
        "Open": new_price, "High": new_price, "Low": new_price, "Close": new_price,
        "high_2yr": new_price / (1 - 0.30), "dip_low": new_price * 0.9, "dd_pct": 0.30,
        "gate_threshold": 0.30, "eligible": [d == new_fire for d in dates], "stale": False,
        "gate_clear_date": dates[0],
        "entry_ut_buy": [d == new_fire for d in dates], "exit_ut_sell": False,
        "realized_vol": 0.3,
    }, index=dates)
    return {"OLD": old, "NEW": new}, dates


def test_slot_recycling_valve_recycles_underwater_long_held_loser():
    frames, dates = _recycling_frames(old_price_after_entry=60.0)   # OLD falls underwater
    cfg = _base_cfg(equity_slots=1, leap_slots=0)
    cfg["slot_recycling"] = {"enabled": True, "min_hold_days": 365}
    res = simulate_fib(frames, cfg, cell="test", leap_tickers=frozenset(), slot_recycling=True)

    assert len(res.recycle_events) >= 1
    assert res.recycle_events[0][1] == "OLD"
    entered = {t.ticker for t in res.trades}
    assert "NEW" in entered
    old_trade = next(t for t in res.trades if t.ticker == "OLD")
    assert old_trade.exit_reason == "slot_recycle_valve"


def test_slot_recycling_valve_never_touches_a_winner():
    """Opportunity-cost valve, NOT a stop-loss: a position trading ABOVE
    its entry price must never be force-recycled, even when held long and
    a better candidate is waiting for a full slot."""
    frames, dates = _recycling_frames(old_price_after_entry=150.0)  # OLD stays a winner
    cfg = _base_cfg(equity_slots=1, leap_slots=0)
    cfg["slot_recycling"] = {"enabled": True, "min_hold_days": 365}
    res = simulate_fib(frames, cfg, cell="test", leap_tickers=frozenset(), slot_recycling=True)

    assert len(res.recycle_events) == 0
    entered = {t.ticker for t in res.trades}
    assert "NEW" not in entered   # slot never freed, so NEW never enters
    rejected_tickers = {r.ticker for r in res.rejected_entries}
    assert "NEW" in rejected_tickers


def test_slot_recycling_off_by_default_does_nothing():
    frames, dates = _recycling_frames(old_price_after_entry=60.0)
    cfg = _base_cfg(equity_slots=1, leap_slots=0)
    cfg["slot_recycling"] = {"enabled": True, "min_hold_days": 365}
    # slot_recycling PARAM defaults False even though cfg says enabled —
    # the function-level toggle is what the attribution ladder controls.
    res = simulate_fib(frames, cfg, cell="test", leap_tickers=frozenset())
    assert len(res.recycle_events) == 0
