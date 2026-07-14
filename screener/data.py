"""Daily OHLCV fetch via yfinance, cached to disk as parquet.

Rule: never silently fill missing data. If yfinance returns nothing, returns
gaps inside the requested range, or returns NaNs in OHLCV columns, this
module raises. It does not forward-fill, drop, or interpolate on your behalf.
"""
from pathlib import Path

import pandas as pd
import yfinance as yf

from screener.config import load_config

OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


class DataFetchError(Exception):
    """Raised when yfinance returns nothing usable for a ticker."""


class DataIntegrityError(Exception):
    """Raised when fetched data contains missing/NaN values that would
    otherwise need to be silently filled."""


def _cache_path(ticker: str) -> Path:
    cfg = load_config()
    cache_dir = Path(cfg["data"]["cache_dir"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{ticker.upper()}_daily.parquet"


def _validate(df: pd.DataFrame, ticker: str) -> None:
    if df is None or df.empty:
        raise DataFetchError(f"{ticker}: yfinance returned no data.")

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


def fetch_daily_bars(ticker: str, period: str = "5y", refresh: bool = False) -> pd.DataFrame:
    """Fetch daily OHLCV for `ticker`, using the parquet cache unless
    `refresh=True`. Raises DataFetchError / DataIntegrityError rather than
    returning partial or filled data.
    """
    cache_file = _cache_path(ticker)

    if cache_file.exists() and not refresh:
        df = pd.read_parquet(cache_file)
        _validate(df, ticker)
        return df

    raw = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if raw is not None and not raw.empty:
        raw = raw[[c for c in OHLCV_COLUMNS if c in raw.columns]]
        raw.index.name = "Date"

    _validate(raw, ticker)

    raw.to_parquet(cache_file)
    return raw
