"""Daily OHLCV, sourced exclusively from Robinhood (via the Robinhood MCP
tools), cached to disk as parquet.

Robinhood's MCP tools are only callable by the Claude Code agent, not from
plain Python — so this module cannot "fetch" data itself the way a library
like yfinance would. Its job is split accordingly:

  - `ingest_robinhood_bars()` is the only way new data enters the cache. The
    agent calls the Robinhood `get_equity_historicals` MCP tool, then passes
    the raw `bars` list for one symbol to this function, which validates it
    and writes the parquet cache.
  - `fetch_daily_bars()` only ever reads from that cache. If the cache is
    missing or stale, it raises loudly rather than silently reaching for any
    other data source (e.g. yfinance) — there is no fallback source, by
    design, so a screener run never silently mixes data providers.

Rule either way: never silently fill missing data. If Robinhood returns
nothing usable, or the cache is empty/corrupt, this module raises. It does
not forward-fill, drop, or interpolate on your behalf.
"""
from pathlib import Path

import pandas as pd

from screener.config import load_config

OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


class DataFetchError(Exception):
    """Raised when there is no usable cached data for a ticker, or the
    Robinhood payload passed to ingest_robinhood_bars() is empty/malformed."""


class DataIntegrityError(Exception):
    """Raised when data contains missing/NaN values that would otherwise
    need to be silently filled."""


def _cache_path(ticker: str) -> Path:
    cfg = load_config()
    cache_dir = Path(cfg["data"]["cache_dir"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{ticker.upper()}_daily.parquet"


def _validate(df: pd.DataFrame, ticker: str) -> None:
    if df is None or df.empty:
        raise DataFetchError(
            f"{ticker}: no cached data and no data source to fetch from. "
            f"Populate the cache first via ingest_robinhood_bars() using the "
            f"Robinhood MCP tool (get_equity_historicals) — this module never "
            f"fetches on its own."
        )

    missing_cols = [c for c in OHLCV_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataFetchError(f"{ticker}: missing expected columns {missing_cols}.")

    nan_mask = df[OHLCV_COLUMNS].isna()
    if nan_mask.any().any():
        bad_rows = df.index[nan_mask.any(axis=1)]
        raise DataIntegrityError(
            f"{ticker}: NaN values in OHLCV data on {len(bad_rows)} row(s), "
            f"e.g. {list(bad_rows[:5].astype(str))}. Refusing to silently fill."
        )


def ingest_robinhood_bars(ticker: str, bars: list) -> pd.DataFrame:
    """Convert one symbol's raw `bars` list from the Robinhood
    `get_equity_historicals` MCP tool response into the cached OHLCV format,
    validate it, and write the parquet cache. Returns the resulting
    DataFrame.

    `bars` elements are expected to have: begins_at, open_price, high_price,
    low_price, close_price, volume (the shape Robinhood's tool returns).
    This is the only path by which fresh data enters the cache — there is no
    automatic/implicit fetch anywhere else in this module.
    """
    if not bars:
        raise DataFetchError(f"{ticker}: Robinhood returned no bars to ingest.")

    rows = []
    for b in bars:
        rows.append(
            {
                "Date": pd.Timestamp(b["begins_at"]).tz_localize(None),
                "Open": float(b["open_price"]),
                "High": float(b["high_price"]),
                "Low": float(b["low_price"]),
                "Close": float(b["close_price"]),
                "Volume": int(b["volume"]),
            }
        )
    df = pd.DataFrame(rows).set_index("Date").sort_index()
    df.index.name = "Date"

    _validate(df, ticker)

    df.to_parquet(_cache_path(ticker))
    return df


def fetch_daily_bars(ticker: str) -> pd.DataFrame:
    """Load daily OHLCV for `ticker` from the parquet cache. Raises
    DataFetchError if nothing has been ingested yet for this ticker, or
    DataIntegrityError if the cached data has NaNs. Never fetches on its
    own — see ingest_robinhood_bars().
    """
    cache_file = _cache_path(ticker)

    if not cache_file.exists():
        _validate(None, ticker)

    df = pd.read_parquet(cache_file)
    _validate(df, ticker)
    return df
