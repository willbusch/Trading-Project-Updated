from pathlib import Path

import pytest

from screener.config import load_config

CACHE = Path("data_cache/MSFT_daily.parquet")


@pytest.mark.skipif(not CACHE.exists(), reason="requires cached data")
def test_eligible_and_firing_match_build_fib_frame_directly():
    """Signal-parity test: the scanner must not reimplement eligibility or
    UT-buy math — it can only read the columns build_fib_frame already
    computed. Verify report.py's numbers for a sample ticker are byte-
    identical to calling build_fib_frame directly for the same date."""
    from backtest.fib_features import build_fib_frame
    from scanner.report import ENTRY_TF, EXIT_TF, _latest_frames

    cfg = load_config()
    tickers = ["MSFT", "NVDA", "AMD"]
    leap_tickers = frozenset({"MSFT", "NVDA"})

    rows, failed = _latest_frames(cfg, tickers, leap_tickers)
    assert not failed

    for t in tickers:
        from backtest.fib_universe import gate_of
        direct_frame = build_fib_frame(t, gate_of(t, leap_tickers), ENTRY_TF, EXIT_TF,
                                       cfg, use_hybrid=True)
        direct_last = direct_frame.iloc[-1]

        assert bool(rows[t]["eligible"]) == bool(direct_last["eligible"])
        assert bool(rows[t]["entry_ut_buy"]) == bool(direct_last["entry_ut_buy"])
        a, b = rows[t]["dd_pct"], direct_last["dd_pct"]
        assert (a != a and b != b) or a == pytest.approx(b)   # both NaN, or equal
        assert rows[t]["Close"] == direct_last["Close"]


@pytest.mark.skipif(not CACHE.exists(), reason="requires cached data")
def test_open_positions_uses_leap_gate_for_leap_holdings(tmp_path, monkeypatch):
    """Regression test for a live bug: open_positions_section originally
    computed the anchor gate from an empty leap_tickers set, so a real
    LEAP holding got evaluated against the 40% equity gate instead of
    25%, leaving dip_low NaN and the reported fib_fraction NaN too."""
    import json

    from scanner.report import _latest_frames, open_positions_section

    snap = {
        "as_of": "test", "total_equity": 100000, "cash": 0,
        "holdings": [{"ticker": "MSFT", "kind": "leap", "quantity": 3,
                      "avg_entry_price": 400.0, "entry_date": None}],
    }
    live_path = tmp_path / "live_positions_snapshot.json"
    live_path.write_text(json.dumps(snap))
    monkeypatch.setattr("scanner.report.LIVE_POSITIONS_PATH", live_path)
    # isolate from any real portfolio.yaml in the repo root
    monkeypatch.setattr("scanner.report.PORTFOLIO_YAML_PATH", tmp_path / "nonexistent.yaml")

    cfg = load_config()
    rows, _ = _latest_frames(cfg, ["MSFT"], frozenset({"MSFT"}))
    result = open_positions_section(cfg, rows, "simple_09")
    assert result["available"]
    pos = result["by_account"]["account_1"]["positions"][0]
    assert "error" not in pos
    frac = pos["fib_fraction"]
    assert frac == frac, "fib_fraction is NaN — the LEAP-gate bug regressed"


@pytest.mark.skipif(not CACHE.exists(), reason="requires cached data")
def test_render_report_runs_without_live_positions_file(tmp_path, monkeypatch):
    """The report must degrade gracefully (not crash) when NEITHER account
    source exists yet — the common state before the first manual refresh.
    Isolated from any real portfolio.yaml / live_positions_snapshot.json
    in the repo (both may exist and contain real financial data)."""
    from scanner.report import render_report

    monkeypatch.setattr("scanner.report.LIVE_POSITIONS_PATH", tmp_path / "nonexistent.json")
    monkeypatch.setattr("scanner.report.PORTFOLIO_YAML_PATH", tmp_path / "nonexistent.yaml")

    cfg = load_config()
    out = render_report(cfg)
    assert "1. ELIGIBLE" in out
    assert "2. FIRING TODAY" in out
    assert "3. OPEN POSITIONS" in out
    assert "4. VIOLATIONS" in out
    assert "No order" in out or "no orders" in out.lower()
