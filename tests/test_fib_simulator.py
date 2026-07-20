from pathlib import Path

import pandas as pd
import pytest

from screener.config import load_config

CACHE = Path("data_cache/MSFT_daily.parquet")


def _cfg():
    return load_config()


@pytest.mark.skipif(not CACHE.exists(), reason="requires cached data")
def test_fib_smoke_one_cell_runs_end_to_end():
    from backtest.fib_features import build_fib_frame
    from backtest.fib_simulator import simulate_fib

    cfg = _cfg()
    names = ["MSFT", "NVDA", "AMD", "HIMS"]
    frames = {t: build_fib_frame(t, 0.40, "3day", "3day", cfg) for t in names}
    res = simulate_fib(frames, cfg, cell="3day/3day")

    assert res.equity_curve.notna().all()
    assert (res.cash_curve >= -1e-6).all()
    for t in res.closed_trades:
        assert t.exit_date > t.entry_date
        assert t.exit_reason is not None
        assert t.peak_price >= t.entry_price - 1e-9


@pytest.mark.skipif(not CACHE.exists(), reason="requires cached data")
def test_fib_simulator_is_forward_only_under_truncation():
    """LOOKAHEAD TEST at the SIMULATOR level: truncating the price history
    to an earlier end date must not change any trade that already closed
    before the truncation point. If a future bar leaked into an earlier
    decision, the earlier trades would differ."""
    from backtest.fib_features import build_fib_frame
    from backtest.fib_simulator import simulate_fib

    cfg = _cfg()
    names = ["MSFT", "NVDA", "AMD"]
    full = {t: build_fib_frame(t, 0.40, "3day", "3day", cfg) for t in names}
    cut = pd.Timestamp("2024-06-30")
    trunc = {t: f.loc[:cut] for t, f in full.items()}

    res_full = simulate_fib(full, cfg, cell="x")
    res_trunc = simulate_fib(trunc, cfg, cell="x")

    def closed_before(res):
        return {
            (t.ticker, t.entry_date, t.exit_date): round(t.pnl_pct, 8)
            for t in res.closed_trades
            if t.exit_date <= cut
        }

    a, b = closed_before(res_full), closed_before(res_trunc)
    assert a == b, "a trade closing before the cutoff changed when future bars were removed"


@pytest.mark.skipif(not CACHE.exists(), reason="requires cached data")
def test_stale_entries_excluded_by_default_included_with_flag():
    from backtest.fib_features import build_fib_frame
    from backtest.fib_simulator import simulate_fib

    cfg = _cfg()
    # HOOD is the known stale-anchor name from the diagnostic
    frames = {"HOOD": build_fib_frame("HOOD", 0.40, "3day", "3day", cfg)}
    excluded = simulate_fib(frames, cfg, cell="x", include_stale=False)
    included = simulate_fib(frames, cfg, cell="x", include_stale=True)

    assert len(excluded.stale_excluded) > 0
    # including stale entries yields at least as many trades
    assert len(included.trades) >= len(excluded.trades)
