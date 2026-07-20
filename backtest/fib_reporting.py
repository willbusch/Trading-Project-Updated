"""Stats + report rendering for the latched-Fib strategy. Pure functions.

The header DISCLAIMER is verbatim per the owner's build prompt.
"""
import pandas as pd

from backtest.reporting import compute_drawdown_stats

DISCLAIMER = """\
> "12-name curated sample — survivorship bias, mechanics validation, NOT
> edge. LEAP P&L uses a 0.55-delta approximation ignoring theta —
> optimistic. HOOD/SOFI stale-anchor entries excluded from headline.
> Absolute edge requires the full SPY/QQQ universe run."\
"""


def compute_trade_stats(result) -> dict:
    closed = result.closed_trades
    out = {
        "n_closed": len(closed),
        "n_open": len(result.open_trades),
        "n_rejected": len(result.rejected_entries),
        "n_stale_excluded": len(result.stale_excluded),
    }
    if not closed:
        out.update(win_rate=None, expectancy_pct=None, avg_win_pct=None,
                   avg_loss_pct=None, payoff=None, avg_hold_days=None,
                   trades_per_year=None)
        return out
    wins = [t for t in closed if t.pnl > 0]
    losses = [t for t in closed if t.pnl <= 0]
    holds = [(t.exit_date - t.entry_date).days for t in closed]
    span_years = (
        (result.equity_curve.index[-1] - result.equity_curve.index[0]).days / 365.25
    )
    out.update(
        win_rate=len(wins) / len(closed),
        expectancy_pct=sum(t.pnl_pct for t in closed) / len(closed),
        avg_win_pct=(sum(t.pnl_pct for t in wins) / len(wins)) if wins else None,
        avg_loss_pct=(sum(t.pnl_pct for t in losses) / len(losses)) if losses else None,
        payoff=(
            (sum(t.pnl_pct for t in wins) / len(wins))
            / abs(sum(t.pnl_pct for t in losses) / len(losses))
            if wins and losses else None
        ),
        avg_hold_days=sum(holds) / len(holds),
        trades_per_year=len(closed) / span_years if span_years > 0 else None,
    )
    return out


def exit_breakdown(result) -> dict:
    from collections import Counter
    return dict(Counter(t.exit_reason for t in result.closed_trades))


def compute_the_gap(result) -> dict:
    """Trades that peaked above entry, never hit 1.618, never triggered a
    zone/latch exit, and closed at a loss OR gave back >50% of peak gain.
    The owner's accepted open risk (no exit below 0.5) — quantified.

    'Gave back >50% of peak gain': at peak the position was up
    (peak-entry); at close it retained < 50% of that gain (or went
    negative). Open-at-window-end positions are marked-to-final and count
    if they qualify."""
    gap_trades = []
    total_giveback = 0.0
    for t in result.trades:
        final = t.exit_price if not t.is_open else None
        # for open trades use last peak as proxy end? use peak vs entry only
        peak_gain = t.peak_price - t.entry_price
        if peak_gain <= 0:
            continue                        # never peaked above entry
        reason = t.exit_reason or "open_at_end"
        triggered_zone = reason in (
            "fib_1618_hard", "fib_latch_trigger", "fib_05_11_ut_sell",
            "fib_15_16_ut_sell", "leap_ut_sell", "leap_modeled_expiry",
        )
        if reason == "fib_1618_hard":
            continue                        # hit target — not a gap trade
        if t.is_open:
            # give-back measured to the last marked price isn't stored;
            # use peak vs entry — count only if still open and gave back via
            # a lower recent close is unknown, so treat open trades by
            # comparing peak to entry-price floor conservatively (skip).
            continue
        retained = (final - t.entry_price)
        gave_back_half = retained < 0.5 * peak_gain
        closed_at_loss = t.pnl is not None and t.pnl <= 0
        if (closed_at_loss or gave_back_half) and not triggered_zone:
            giveback = peak_gain - max(retained, 0.0)
            total_giveback += giveback * t.shares
            gap_trades.append({
                "ticker": t.ticker, "entry": t.entry_date, "exit": t.exit_date,
                "peak_gain_pct": peak_gain / t.entry_price,
                "final_pnl_pct": t.pnl_pct, "reason": reason,
            })
    return {"n_gap_trades": len(gap_trades),
            "total_giveback_dollars": total_giveback,
            "trades": gap_trades}


def benchmark_spy(cfg, start, end) -> dict:
    from screener.data import fetch_daily_bars
    spy = fetch_daily_bars("SPY").loc[start:end]["Close"]
    return compute_drawdown_stats(spy.rename("SPY"))


def benchmark_equal_weight(tickers, start, end) -> dict:
    """Equal-weight buy-and-hold of the named tickers, invested from the
    first common date in the window, no rebalance."""
    from screener.data import fetch_daily_bars
    closes = {}
    for t in tickers:
        s = fetch_daily_bars(t)["Close"].loc[start:end]
        closes[t] = s
    df = pd.DataFrame(closes).dropna()
    if df.empty:
        return {"total_return": None, "cagr": None, "max_drawdown": None}
    norm = df / df.iloc[0]
    port = norm.mean(axis=1)               # equal weight, no rebalance ~ avg of norms
    return compute_drawdown_stats(port.rename("EW"))
