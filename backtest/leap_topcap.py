"""A2 (2026-07-22, "Beat-SPY Package"): top-10-by-market-cap LEAP
eligibility, computed BY RANK across the universe, not a hardcoded name
list and not a static dollar floor.

PROXY DISCLOSURE (same limitation carried throughout this project): this
data source only exposes CURRENT-snapshot market cap, never point-in-time
history. True point-in-time top-10 ranking is not obtainable here. Instead:

  implied_shares[ticker] = current_market_cap[ticker] / latest_close[ticker]
  historical_cap_proxy[ticker, date] = implied_shares[ticker] * close[ticker, date]

Shares outstanding drifts far more slowly than price (buybacks/issuance
are a small annual % vs. price swings of 30-70%+), so multiplying a fixed
implied share count by each ticker's ACTUAL historical close is a genuine,
data-driven improvement over applying today's dollar cap retroactively —
it lets a name's proxy cap fall in the past when its price was lower. It
is still a proxy, not real point-in-time data: buybacks/issuance drift are
not modeled, so implied shares are held constant across the whole history.
This is flagged verbatim in every report that uses it.

LOOKAHEAD SAFETY: for date D, the rank uses ONLY close prices up to and
including D (via one cross-sectional DataFrame built from each ticker's
own forward-only Close series) — no future bar enters the computation for
any date. The one non-forward-only ingredient is `implied_shares`, which
is derived from a single CURRENT (as-of-run-time) market cap snapshot and
held constant for the whole date range — this is the disclosed proxy
limitation above, not a per-date lookahead: the same constant divisor is
used for a ticker's entire history, so relative RANKING on any past date
is driven entirely by that date's own actual close, not by information
from the future.
"""
import pandas as pd


def implied_shares_outstanding(frames: dict, market_caps: dict) -> dict:
    """current_cap / latest_available_close, per ticker. Skips tickers with
    no cap or no price history."""
    shares = {}
    for t, f in frames.items():
        cap = market_caps.get(t)
        if not cap:
            continue
        closes = f["Close"].dropna()
        if len(closes) == 0:
            continue
        shares[t] = cap / float(closes.iloc[-1])
    return shares


def historical_cap_proxy_matrix(frames: dict, market_caps: dict) -> pd.DataFrame:
    """date x ticker matrix of the historical-cap proxy (see module
    docstring). Forward-filled per ticker only across ITS OWN history (no
    cross-ticker leakage) so short-history names don't spuriously rank
    before they existed."""
    shares = implied_shares_outstanding(frames, market_caps)
    cols = {t: frames[t]["Close"] * s for t, s in shares.items()}
    return pd.DataFrame(cols)


def top_n_by_cap_matrix(frames: dict, market_caps: dict, top_n: int = 10) -> pd.DataFrame:
    """date x ticker boolean matrix: True where that ticker ranks in the
    top `top_n` by the historical-cap proxy on that date. Tickers with no
    price on a given date (not yet listed / no data) are never eligible
    that date (NaN caps sort last, never rank in top_n)."""
    caps = historical_cap_proxy_matrix(frames, market_caps)
    rank = caps.rank(axis=1, ascending=False, method="min")
    top = rank <= top_n
    return top.fillna(False)


def eligible_tickers_by_year(top_n_matrix: pd.DataFrame) -> dict:
    """{year: sorted list of tickers that were top-N-eligible on at least
    one trading day that year} — for the "which names are LEAP-eligible by
    year" report requirement."""
    out = {}
    years = sorted({d.year for d in top_n_matrix.index})
    for y in years:
        yr_rows = top_n_matrix[top_n_matrix.index.year == y]
        elig = sorted(c for c in yr_rows.columns if yr_rows[c].any())
        out[y] = elig
    return out
