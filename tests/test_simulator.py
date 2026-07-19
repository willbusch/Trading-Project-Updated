from pathlib import Path

import pandas as pd
import pytest

from backtest.signals import AblationConfig
from backtest.simulator import simulate

CFG = {
    "sizing": {
        "equity_slots": 5,
        "leap_slots": 1,
        "max_position_pct_of_book": 0.15,
        "min_cash_floor_pct": 0.05,
        "max_tranches_per_name": 3,
        "tranche_spacing_atr_multiple": 1.5,
    },
    "leap": {
        "single_entry_pct_of_book": 0.20,
        "sleeve_cap_pct_of_book": 0.25,
        "delta_min": 0.50,
        "delta_max": 0.60,
    },
    "circuit_breakers": {
        "max_new_positions_per_week": 2,
        "account_drawdown_halt_pct": 0.30,
        "halt_duration_days": 30,
    },
    "backtest": {"slippage_pct": 0.001},
}


def _signal_frame(dates, opens, closes, entries, exits):
    n = len(dates)
    return pd.DataFrame(
        {
            "Open": opens,
            "Close": closes,
            "atr": [1.0] * n,
            "entry_signal": entries,
            "exit_signal": exits,
            "exit_reason": ["ut_sell" if e else "" for e in exits],
        },
        index=pd.DatetimeIndex(dates),
    )


def test_entry_and_exit_fill_next_bar_open_with_slippage():
    dates = pd.bdate_range("2024-01-01", periods=5)
    f = _signal_frame(
        dates,
        opens=[100, 102, 104, 106, 108],
        closes=[101, 103, 105, 107, 109],
        entries=[True, False, False, False, False],
        exits=[False, False, True, False, False],
    )
    res = simulate({"XXX": f}, CFG, AblationConfig(), seed_cash=100_000.0)

    assert len(res.closed_trades) == 1
    tr = res.closed_trades[0]
    # signal bar0 -> entry at bar1 open 102 * 1.001
    assert tr.entry_date == dates[1]
    assert tr.entry_price == pytest.approx(102 * 1.001)
    # 15% of book at entry
    assert tr.shares * tr.entry_price == pytest.approx(0.15 * 100_000.0)
    # exit signal bar2 -> exit at bar3 open 106 * 0.999
    assert tr.exit_date == dates[3]
    assert tr.exit_price == pytest.approx(106 * 0.999)
    assert tr.pnl == pytest.approx(tr.shares * (106 * 0.999 - 102 * 1.001))
    # all proceeds landed in cash; equity curve exists for all 5 bars
    assert len(res.equity_curve) == 5
    assert res.cash_curve.iloc[-1] == pytest.approx(
        100_000.0 - tr.shares * tr.entry_price + tr.shares * tr.exit_price
    )


def test_weekly_cap_and_alphabetical_tiebreak():
    dates = pd.bdate_range("2024-01-01", periods=3)  # all same week
    mk = lambda: _signal_frame(
        dates, [100] * 3, [100] * 3,
        entries=[True, False, False], exits=[False] * 3,
    )
    frames = {"CCC": mk(), "AAA": mk(), "BBB": mk()}
    res = simulate(frames, CFG, AblationConfig(), seed_cash=100_000.0)

    entered = sorted(t.ticker for t in res.trades)
    assert entered == ["AAA", "BBB"]  # cap 2/week, alphabetical wins
    assert len(res.rejected_entries) == 1
    assert res.rejected_entries[0].ticker == "CCC"
    assert any("weekly_cap" in r for r in res.rejected_entries[0].reasons)


def test_signal_on_final_bar_never_executes():
    dates = pd.bdate_range("2024-01-01", periods=2)
    f = _signal_frame(dates, [100, 100], [100, 100],
                      entries=[False, True], exits=[False, False])
    res = simulate({"XXX": f}, CFG, AblationConfig(), seed_cash=100_000.0)
    assert res.trades == []


def test_leap_ticker_priced_as_delta_approx_and_labeled():
    dates = pd.bdate_range("2024-01-01", periods=4)
    f = _signal_frame(
        dates, [100, 100, 120, 120], [100, 110, 120, 120],
        entries=[True, False, False, False], exits=[False, True, False, False],
    )
    res = simulate(
        {"MSFT": f}, CFG, AblationConfig(),
        seed_cash=100_000.0, leap_tickers=frozenset({"MSFT"}),
    )
    tr = res.closed_trades[0]
    assert tr.kind == "leap"
    assert tr.priced_as == "leap_delta_approx"
    # 20% single-entry sizing for the LEAP
    assert tr.shares * tr.entry_price == pytest.approx(0.20 * 100_000.0)
    # P&L is delta-scaled (delta = midpoint 0.55): share pnl x 0.55
    share_pnl = tr.shares * (120 * 0.999 - 100 * 1.001)
    assert tr.pnl == pytest.approx(0.55 * share_pnl)


def test_kill_switch_halts_entries_after_drawdown():
    # 12 bars across 3 calendar weeks. 4 names enter (2 in week 1, 2 in
    # week 2, respecting the weekly cap) -> ~60% invested; then all held
    # names crash 100 -> 30 at bar 8 (60% x 70% = 42% account drawdown,
    # over the 30% halt line). A fresh name signaling after the crash, in
    # week 3 (weekly cap clear), must be rejected by the kill switch.
    dates = pd.bdate_range("2024-01-01", periods=12)
    crash = [100.0] * 8 + [30.0] * 4

    def held(entry_bar):
        e = [False] * 12
        e[entry_bar] = True
        return _signal_frame(dates, crash, crash, e, [False] * 12)

    e_late = [False] * 12
    e_late[9] = True
    frames = {
        "AAA": held(0),
        "BBB": held(0),
        "CCC": held(4),
        "DDD": held(4),
        "EEE": _signal_frame(dates, [100.0] * 12, [100.0] * 12, e_late, [False] * 12),
    }
    res = simulate(frames, CFG, AblationConfig(), seed_cash=100_000.0)

    assert len(res.halts) >= 1
    assert res.halts[0] == dates[8]
    eee_rejects = [r for r in res.rejected_entries if r.ticker == "EEE"]
    assert len(eee_rejects) == 1
    assert any("kill_switch" in x for x in eee_rejects[0].reasons)


@pytest.mark.skipif(
    not Path("data_cache/MSFT_daily.parquet").exists(),
    reason="requires cached MSFT data",
)
def test_smoke_strategy_b_msft_real_data():
    """THE hard gate (Addendum 2): Strategy B, single ticker, combined
    window, real cached data — must run end-to-end before anything scales
    out."""
    from backtest.features import build_feature_frame
    from backtest.signals import build_signal_frame
    from screener.config import load_config

    cfg = load_config()
    frame = build_feature_frame("MSFT", cfg)
    sf = build_signal_frame(frame, "B", cfg, AblationConfig())
    res = simulate({"MSFT": sf}, cfg, AblationConfig(), strategy="B")

    assert len(res.trades) >= 1                      # UT flips: B must trade
    assert res.equity_curve.notna().all()
    assert (res.cash_curve >= -1e-6).all()           # never negative cash
    for t in res.closed_trades:
        assert t.exit_date > t.entry_date
        assert t.exit_reason != ""
    # every exit in B comes from the shared hierarchy
    assert all(
        t.exit_reason in ("ut_sell", "rsi_euphoria_80") for t in res.closed_trades
    )
