"""Data refresh for the live scanner (Phase 1).

REAL ARCHITECTURE CONSTRAINT (read before assuming this is a cron job):
this project's only market-data and brokerage access is via Robinhood MCP
tools, which are callable ONLY by the agent inside a conversation turn —
not by a standalone Python process. There is no API key or session this
script can use on its own. So the daily refresh is necessarily a two-step,
agent-driven process:

  1. THE AGENT calls the MCP tools listed in REFRESH_CHECKLIST below and
     passes each raw result to the matching `save_*` function here, which
     writes it into the same cache locations the backtest already reads
     (`data_cache/*.parquet`, `data/universe_snapshot.json`,
     `data/live_positions_snapshot.json`).
  2. `python -m scanner.report` (pure Python, no MCP) reads that cache and
     renders the 4-section daily report.

This module is step 1's glue — parsing + persisting, not fetching. It
never places an order and never will; every helper below is a pure
read-and-save.
"""
import json
from pathlib import Path

DATA_DIR = Path("data")
LIVE_POSITIONS_PATH = DATA_DIR / "live_positions_snapshot.json"

REFRESH_CHECKLIST = """
Daily refresh — run these MCP calls, then persist each result:

1. mcp__robinhood__create_scan (or run_scan on the existing scan_id) with
   the quality-gate filters (market cap >= $10B, net profit margin > 0,
   avg volume > 1M) -> pass the result to refresh.save_universe_scan().

2. mcp__robinhood__get_equity_historicals for each universe ticker
   (interval=day, a short recent window is enough for an incremental
   refresh) -> ingest via scripts/ingest_universe.py, same as the
   original bulk ingestion.

3. mcp__robinhood__get_equity_positions AND get_option_positions AND
   get_portfolio -> pass all three to refresh.save_live_positions().

4. Run `python -m scanner.report` to render the daily markdown report
   from the now-current cache.
"""


def save_universe_scan(scan_result: dict, path: str = "data/universe_snapshot.json") -> dict:
    """Parse a create_scan/run_scan MCP result into the same snapshot
    shape scripts/ingest_universe.py and fib_universe.py already expect."""
    rows = scan_result["results"]
    uni = []
    for r in rows:
        c = r["columns"]
        uni.append((c["Symbol"], float(c["Market cap"])))
    uni.sort(key=lambda x: -x[1])
    tickers = [s for s, _ in uni]
    leap = [s for s, mc in uni if mc >= 500e9]
    snapshot = {
        "as_of": scan_result.get("as_of", "unknown"),
        "source": "Robinhood scanner (live, current-market)",
        "scan_filters": "MARKET_CAP>=10e9 AND NET_PROFIT_MARGIN>0 AND AVG_VOLUME(30d)>1e6",
        "note": ("CURRENT membership + CURRENT fundamentals — survivorship + "
                "fundamental-snapshot bias baked across all history. NOT "
                "point-in-time SPY/QQQ (no membership filter exists in the "
                "data source)."),
        "leap_tier_min_market_cap": 500e9,
        "tickers": tickers,
        "leap_tickers": leap,
        "market_caps": {s: mc for s, mc in uni},
    }
    Path(path).write_text(json.dumps(snapshot, indent=1))
    return snapshot


def save_live_positions(
    equity_positions: dict,
    option_positions: dict,
    portfolio: dict,
    path: Path = LIVE_POSITIONS_PATH,
) -> dict:
    """Normalize raw MCP position results into one snapshot the report
    layer reads. Records whatever entry price/date each tool provides —
    if a position's true entry date isn't available from the API, the
    report layer falls back to a same-day anchor approximation and labels
    it as such rather than fabricating history."""
    holdings = []
    for p in equity_positions.get("results", equity_positions.get("positions", [])):
        holdings.append({
            "ticker": p.get("symbol") or p.get("ticker"),
            "kind": "equity",
            "quantity": float(p.get("quantity", 0)),
            "avg_entry_price": float(p.get("average_buy_price", p.get("avg_price", 0)) or 0),
            "entry_date": p.get("created_at") or p.get("entry_date"),
        })
    for p in option_positions.get("results", option_positions.get("positions", [])):
        holdings.append({
            "ticker": p.get("chain_symbol") or p.get("underlying_symbol") or p.get("symbol"),
            "kind": "leap",
            "quantity": float(p.get("quantity", 0)),
            "avg_entry_price": float(p.get("average_price", 0) or 0),
            "entry_date": p.get("created_at") or p.get("entry_date"),
        })
    snapshot = {
        "as_of": portfolio.get("as_of", "unknown"),
        "total_equity": float(portfolio.get("total_value", 0) or 0),
        "cash": float(portfolio.get("cash", 0) or 0),
        "holdings": holdings,
    }
    Path(path).write_text(json.dumps(snapshot, indent=1))
    return snapshot
