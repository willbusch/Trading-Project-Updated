"""A8 (2026-07-22): regression test for the SPY benchmark curve truncating
mid-chart. Root cause: Chart.js datasets shared ONE labels array while each
series supplied only a bare values array, paired positionally — any
length/date mismatch silently misaligned or truncated the shorter one.

Fixed by reindexing every curve onto one shared date union before
serializing. As of the 2026-07-22 dashboard redesign this logic lives in
scripts/generate_dashboard.py::_align, which additionally leaves LEADING
gaps as null (rather than back-filling) so a shorter series — SPY starts
2021-07 — begins mid-chart honestly instead of showing a misleading flat
line before its data exists.
"""
import importlib.util
from pathlib import Path

import pandas as pd

_SPEC = importlib.util.spec_from_file_location(
    "generate_dashboard",
    Path(__file__).resolve().parents[1] / "scripts" / "generate_dashboard.py",
)
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)
_align = _mod._align


def test_all_series_share_one_date_axis_of_equal_length():
    full = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0],
                     index=pd.bdate_range("2020-01-02", periods=5))
    short = pd.Series([100.0, 105.0, 110.0],
                      index=pd.bdate_range("2020-01-06", periods=3))
    out = _align({"strategy": full, "spy": short})
    n = len(out["_dates"])
    assert n == 5
    assert len(out["strategy"]) == len(out["spy"]) == n   # no truncation


def test_leading_gap_is_null_not_backfilled():
    """A shorter/later-starting series must be null before its first real
    date — NOT back-filled into a flat line that misrepresents history."""
    full = pd.Series([100.0, 200.0, 300.0, 400.0],
                     index=pd.bdate_range("2020-01-02", periods=4))
    short = pd.Series([50.0, 60.0],
                      index=pd.bdate_range("2020-01-06", periods=2))
    out = _align({"strategy": full, "spy": short})
    # first two dates precede the short series -> null; then its real values,
    # forward-filled within its own coverage.
    assert out["spy"][0] is None
    assert out["spy"][1] is None
    assert out["spy"][2] == 50.0
    assert out["spy"][3] == 60.0


def test_full_coverage_series_has_no_nulls_and_keeps_its_values():
    idx = pd.bdate_range("2020-01-02", periods=3)
    a = pd.Series([1.0, 2.0, 3.0], index=idx)
    b = pd.Series([10.0, 20.0, 30.0], index=idx)
    out = _align({"a": a, "b": b})
    assert out["a"] == [1.0, 2.0, 3.0]
    assert out["b"] == [10.0, 20.0, 30.0]
    assert None not in out["a"] and None not in out["b"]
