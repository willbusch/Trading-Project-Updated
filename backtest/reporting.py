"""Stats computation + report rendering. Pure functions over
BacktestResult / signal frames; no simulation logic.

DISCLAIMER below is the verbatim header required on EVERY rendered
output (locked requirement — verbatim, not paraphrased, not demoted to a
footnote).
"""
import pandas as pd

DISCLAIMER = """\
> **ENGINE-VALIDATION PASS — NOT PROOF OF EDGE.** This backtest runs only
> on 7 names the owner currently holds. Those names were picked (and are
> still held) partly BECAUSE they went up — that is survivorship bias, by
> design, and it inflates every number below. Results here validate that
> the engine's mechanics (signals, sizing, constraints, cash rule) behave
> correctly. They do NOT establish that any strategy has an edge. No
> threshold may be changed, no capital deployed, and no strategy declared
> a winner on the basis of these numbers alone."""

TRADING_DAYS_PER_YEAR = 252


def compute_trade_stats(result) -> dict:
    closed = result.closed_trades
    stats = {
        "n_closed": len(closed),
        "n_open_at_end": len(result.open_trades),
        "n_rejected": len(result.rejected_entries),
    }
    if not closed:
        stats.update(
            win_rate=None, expectancy_pct=None, avg_win_pct=None,
            avg_loss_pct=None, profit_factor=None, avg_bars_held=None,
            total_pnl=0.0,
        )
        return stats
    wins = [t for t in closed if t.pnl > 0]
    losses = [t for t in closed if t.pnl <= 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    stats.update(
        win_rate=len(wins) / len(closed),
        expectancy_pct=sum(t.pnl_pct for t in closed) / len(closed),
        avg_win_pct=(sum(t.pnl_pct for t in wins) / len(wins)) if wins else None,
        avg_loss_pct=(sum(t.pnl_pct for t in losses) / len(losses)) if losses else None,
        profit_factor=(gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        avg_bars_held=sum(
            (t.exit_date - t.entry_date).days for t in closed
        ) / len(closed),
        total_pnl=sum(t.pnl for t in closed),
    )
    return stats


def compute_drawdown_stats(equity_curve: pd.Series) -> dict:
    peak = equity_curve.cummax()
    dd = 1.0 - equity_curve / peak
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0
    years = (equity_curve.index[-1] - equity_curve.index[0]).days / 365.25
    cagr = (
        (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / years) - 1.0
        if years > 0
        else None
    )
    return {
        "total_return": total_return,
        "cagr": cagr,
        "max_drawdown": dd.max(),
        "end_equity": equity_curve.iloc[-1],
    }


def compute_utilization_stats(result) -> dict:
    invested_frac = 1.0 - result.cash_curve / result.equity_curve
    return {
        "avg_invested_pct": invested_frac.mean(),
        "pct_bars_fully_idle": (invested_frac < 1e-9).mean(),
        "avg_cash_pct": 1.0 - invested_frac.mean(),   # dead capital
        "n_halts": len(result.halts),
    }


def compute_arm_extras(signal_frames: dict, window=None) -> dict:
    """Strategy C/D extras: arm-to-trigger lag for fired arms, and the
    forgone-return log for armed-then-expired-unfired instances — the
    price return over the exact window the arm covered, [arm date, expiry
    date] (locked judgment: the concrete known window, not a hypothetical
    extended hold)."""
    lags, forgone = [], []
    for tkr, f in signal_frames.items():
        sub = f.loc[window[0] : window[1]] if window is not None else f
        if "fired" not in sub.columns:
            continue
        for date, row in sub[sub["fired"]].iterrows():
            if row["armed_at"] is not None:
                lags.append((date - row["armed_at"]).days)
        for date, row in sub[sub["expired"]].iterrows():
            start = row["expired_armed_at"]
            if start is None or start not in f.index:
                continue
            ret = f.loc[date, "Close"] / f.loc[start, "Close"] - 1.0
            forgone.append(
                {"ticker": tkr, "armed": start, "expired": date, "forgone_return": ret}
            )
    return {
        "n_fired": len(lags),
        "avg_arm_to_trigger_days": (sum(lags) / len(lags)) if lags else None,
        "n_expired_unfired": len(forgone),
        "avg_forgone_return": (
            sum(x["forgone_return"] for x in forgone) / len(forgone) if forgone else None
        ),
        "forgone_log": forgone,
    }


def compute_benchmark_stats(cfg: dict, start, end) -> dict:
    """SPY buy-and-hold over the same window (requires SPY in the cache)."""
    from screener.data import fetch_daily_bars

    spy = fetch_daily_bars("SPY").loc[start:end]["Close"]
    return compute_drawdown_stats(spy.rename("SPY"))


def _fmt(v, pct=False):
    if v is None:
        return "—"
    if v == float("inf"):
        return "inf"
    return f"{v:.1%}" if pct else (f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.2f}")


def render_report(
    title: str,
    per_window: dict,
    benchmark: dict,
    sweep_summary: str,
    ablation_summary: str,
    notes: list,
) -> str:
    """Formatting only. per_window: {window_label: {strategy: {"trade":...,
    "dd":..., "util":..., "extras":..., "leap_label": str|None}}}."""
    lines = [f"# {title}", "", DISCLAIMER, ""]
    for window, strategies in per_window.items():
        lines += [f"## Window: {window}", ""]
        header = (
            "| Strategy | Closed | Win rate | Expectancy | Profit factor | "
            "Total return | CAGR | Max DD | Avg invested | Rejected | LEAP pricing |"
        )
        lines += [header, "|" + "---|" * 11]
        for strat, s in strategies.items():
            t, d, u = s["trade"], s["dd"], s["util"]
            lines.append(
                f"| {strat} | {t['n_closed']} (+{t['n_open_at_end']} open) "
                f"| {_fmt(t['win_rate'], pct=True)} "
                f"| {_fmt(t['expectancy_pct'], pct=True)} "
                f"| {_fmt(t['profit_factor'])} "
                f"| {_fmt(d['total_return'], pct=True)} "
                f"| {_fmt(d['cagr'], pct=True)} "
                f"| {_fmt(d['max_drawdown'], pct=True)} "
                f"| {_fmt(u['avg_invested_pct'], pct=True)} "
                f"| {t['n_rejected']} "
                f"| {s.get('leap_label') or 'n/a (equities only)'} |"
            )
        for strat, s in strategies.items():
            ex = s.get("extras")
            if ex and ex["n_fired"] + ex["n_expired_unfired"] > 0:
                lines += [
                    "",
                    f"**{strat} arm stats:** {ex['n_fired']} fired "
                    f"(avg arm→trigger {_fmt(ex['avg_arm_to_trigger_days'])} days), "
                    f"{ex['n_expired_unfired']} armed-then-expired unfired "
                    f"(avg forgone return {_fmt(ex['avg_forgone_return'], pct=True)} "
                    f"over the armed window).",
                ]
        lines.append("")
    lines += [
        "## Benchmark — SPY buy-and-hold (same span, pre-vault)",
        "",
        f"Total return {_fmt(benchmark['total_return'], pct=True)}, "
        f"CAGR {_fmt(benchmark['cagr'], pct=True)}, "
        f"max drawdown {_fmt(benchmark['max_drawdown'], pct=True)}.",
        "",
        "## UT / volume parameter sweeps",
        "",
        sweep_summary,
        "",
        "## Ablations (combined pre-vault window)",
        "",
        ablation_summary,
        "",
        "## Notes, caveats, and open flags",
        "",
    ]
    lines += [f"- {n}" for n in notes]
    lines.append("")
    return "\n".join(lines)
