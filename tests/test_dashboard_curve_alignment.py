"""A8 (2026-07-22, "Beat-SPY Package"): regression test for the SPY
benchmark curve truncating mid-chart. Root cause: Chart.js datasets shared
ONE `labels` array (the strategy curve's dates) while each series supplied
only a bare `values` array, paired positionally — any length/date mismatch
between series silently misaligned or truncated the shorter one. Fixed by
reindexing every curve onto one shared union-of-dates index before
serializing (scripts/generate_dashboard_data.py::_align_and_serialize_curves).
"""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

_SPEC = importlib.util.spec_from_file_location(
    "generate_dashboard_data",
    Path(__file__).resolve().parents[1] / "scripts" / "generate_dashboard_data.py",
)
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)
_align_and_serialize_curves = _mod._align_and_serialize_curves


def test_curves_with_different_date_ranges_share_identical_labels():
    # strategy curve runs the full span; SPY-idle-cash curve starts later
    # (a real scenario: no LEAP entries until year 2 -> that comparison
    # curve is shorter) — before the fix this truncated the labels array.
    full = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0],
                     index=pd.bdate_range("2020-01-02", periods=5))
    short = pd.Series([100.0, 105.0, 110.0],
                      index=pd.bdate_range("2020-01-06", periods=3))
    out = _align_and_serialize_curves({"strategy": full, "other": short})
    assert out["strategy"]["dates"] == out["other"]["dates"]
    assert len(out["strategy"]["values"]) == len(out["other"]["values"]) == 5


def test_alignment_forward_fills_missing_leading_and_trailing_dates():
    full = pd.Series([100.0, 200.0, 300.0, 400.0],
                     index=pd.bdate_range("2020-01-02", periods=4))
    short = pd.Series([50.0, 60.0],
                      index=pd.bdate_range("2020-01-03", periods=2))
    out = _align_and_serialize_curves({"strategy": full, "other": short})
    # "other" has no value for the first date -> back-filled from its own
    # first known value; no value for the last two dates -> forward-filled
    # from its last known value. Nothing is ever null/dropped.
    assert out["other"]["values"] == [50.0, 50.0, 60.0, 60.0]


def test_alignment_preserves_original_values_on_shared_dates():
    idx = pd.bdate_range("2020-01-02", periods=3)
    a = pd.Series([1.0, 2.0, 3.0], index=idx)
    b = pd.Series([10.0, 20.0, 30.0], index=idx)
    out = _align_and_serialize_curves({"a": a, "b": b})
    assert out["a"]["values"] == [1.0, 2.0, 3.0]
    assert out["b"]["values"] == [10.0, 20.0, 30.0]
