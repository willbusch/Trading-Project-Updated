"""Reusable ingestion for the universe run: parse any get_equity_historicals
tool-result file(s) and write each symbol to the parquet cache. Idempotent —
re-running re-ingests. Prints per-symbol coverage.

Usage: python scripts/ingest_universe.py <file1.txt> [file2.txt ...]
       python scripts/ingest_universe.py --all   (globs the tool-results dir)
"""
import glob
import json
import sys

from screener.data import DataFetchError, DataIntegrityError, ingest_robinhood_bars

TOOL_RESULTS = (
    "/root/.claude/projects/-home-user-Trading-Project-Updated/"
    "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/tool-results/"
    "mcp-robinhood-get_equity_historicals-*.txt"
)


def ingest_file(path: str) -> list:
    with open(path) as f:
        raw = json.load(f)
    out = []
    for r in raw["data"]["results"]:
        sym = r["symbol"]
        bars = [b for b in r["bars"] if not b.get("interpolated", False)]
        try:
            df = ingest_robinhood_bars(sym, bars)
            out.append((sym, len(df), str(df.index.min().date()), str(df.index.max().date())))
        except (DataFetchError, DataIntegrityError) as e:
            out.append((sym, 0, "FAILED", str(e)[:60]))
    return out


def main(argv):
    files = sorted(glob.glob(TOOL_RESULTS)) if argv == ["--all"] else argv
    total = 0
    for path in files:
        for sym, n, lo, hi in ingest_file(path):
            total += 1
            print(f"{sym:8s} {n:5d} bars  {lo} -> {hi}")
    print(f"\ningested {total} symbol-rows from {len(files)} file(s)")


if __name__ == "__main__":
    main(sys.argv[1:])
