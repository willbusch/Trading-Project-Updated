"""The daily live scanner report — Phase 1 of the original project vision.

DECISION-SUPPORT ONLY. Recommends; the owner executes. No order placement
anywhere in this module, ever.

Every signal computed here comes from the SAME tested modules the backtest
uses (`backtest.fib_features.build_fib_frame`, `backtest.drawdown_gate`,
`backtest.fib_exit`) — this file only selects the latest row and formats
it. Any divergence between what this reports and what the backtest would
compute for the same date is a bug (see tests/test_scanner.py's
signal-parity test).

Uses the winning cell from the 2026-07-19 universe run (daily entry /
weekly exit) and the winning equity exit variant from the 2026-07-20
final ablation (see backtest.fib_ablation_final / STRATEGY.md Part 5).
"""
import json
from pathlib import Path

import pandas as pd

from backtest.fib_exit import LeapSimpleExit
from backtest.fib_features import build_fib_frame
from backtest.fib_simulator import EQUITY_EXIT_VARIANTS
from backtest.fib_universe import gate_of, load_universe
from screener.config import load_config

ENTRY_TF, EXIT_TF = "daily", "weekly"
LIVE_POSITIONS_PATH = Path("data/live_positions_snapshot.json")


def _latest_frames(cfg, tickers, leap_tickers):
    """One build_fib_frame per ticker, winning cell, hybrid anchor —
    identical call to what the backtest makes for this cell. Returns
    {ticker: last_row} plus any tickers that failed to load."""
    rows, failed = {}, []
    for t in tickers:
        try:
            frame = build_fib_frame(t, gate_of(t, leap_tickers), ENTRY_TF, EXIT_TF,
                                    cfg, use_hybrid=True)
            rows[t] = frame.iloc[-1]
        except Exception as e:              # noqa: BLE001 — report, don't crash the run
            failed.append((t, f"{type(e).__name__}: {e}"))
    return rows, failed


def eligible_and_firing(rows: dict):
    """Section 1 (ELIGIBLE) and section 2 (FIRING) — pure filters over the
    already-computed `eligible` / `entry_ut_buy` columns. No signal math
    happens in this function."""
    eligible = [
        {"ticker": t, "dd_pct": r["dd_pct"], "high_2yr": r["high_2yr"],
         "dip_low": r["dip_low"], "close": r["Close"]}
        for t, r in rows.items() if bool(r["eligible"])
    ]
    eligible.sort(key=lambda x: -x["dd_pct"])
    firing = [e for e in eligible if bool(rows[e["ticker"]]["entry_ut_buy"])]
    return eligible, firing


def open_positions_section(cfg, rows: dict, exit_variant: str):
    """Section 3. Reads data/live_positions_snapshot.json (written by
    scanner.refresh.save_live_positions). Anchors (dip_low, two_yr_high)
    are looked up as of the position's recorded entry_date when known —
    same anchors the backtest would have frozen at entry. If entry_date is
    missing from the API response, falls back to TODAY's anchor and labels
    the row APPROXIMATE rather than silently treating it as exact."""
    if not LIVE_POSITIONS_PATH.exists():
        return {"available": False, "positions": [],
                "note": "No live_positions_snapshot.json — run scanner.refresh first."}

    snap = json.loads(LIVE_POSITIONS_PATH.read_text())
    out = []
    for h in snap.get("holdings", []):
        t = h["ticker"]
        if t not in rows:
            out.append({"ticker": t, "error": "not in current universe scan"})
            continue
        # BUG FIX (2026-07-20, found live-testing this scaffold): must use
        # the POSITION's own kind, not an empty leap_tickers set — a LEAP
        # held here uses the 25% gate for its anchor, not the 40% equity
        # gate, or its dip_low never accumulates (NaN fraction downstream).
        gate = 0.25 if h["kind"] == "leap" else 0.40
        approximate = h.get("entry_date") is None
        try:
            frame = build_fib_frame(t, gate, ENTRY_TF, EXIT_TF, cfg, use_hybrid=True)
        except Exception as e:
            out.append({"ticker": t, "error": f"{type(e).__name__}: {e}"})
            continue
        if approximate or pd.Timestamp(h["entry_date"]) not in frame.index:
            anchor_row = frame.iloc[-1]
            approximate = True
        else:
            anchor_row = frame.loc[pd.Timestamp(h["entry_date"])]

        from backtest.drawdown_gate import price_fraction
        dip_low, two_yr_high = anchor_row["dip_low"], anchor_row["high_2yr"]
        current_close = rows[t]["Close"]
        frac = price_fraction(current_close, dip_low, two_yr_high)
        machine = (LeapSimpleExit(dip_low, two_yr_high) if h["kind"] == "leap"
                   else EQUITY_EXIT_VARIANTS[exit_variant](dip_low, two_yr_high))
        weekly_ut_sell_active = bool(rows[t]["exit_ut_sell"])
        out.append({
            "ticker": t, "kind": h["kind"], "fib_fraction": frac,
            "levels": machine.levels, "weekly_ut_sell_active": weekly_ut_sell_active,
            "anchor_approximate": approximate,
        })
    return {"available": True, "positions": out}


def violations_section(cfg, positions_result: dict):
    """Section 4: live book vs STRATEGY.md's reconciled targets."""
    if not LIVE_POSITIONS_PATH.exists():
        return {"available": False, "violations": [],
                "note": "No live_positions_snapshot.json — run scanner.refresh first."}
    snap = json.loads(LIVE_POSITIONS_PATH.read_text())
    equity_total = snap.get("total_equity", 0)
    holdings = snap.get("holdings", [])
    violations = []

    n_equity = sum(1 for h in holdings if h["kind"] == "equity")
    n_leap = sum(1 for h in holdings if h["kind"] == "leap")
    if n_equity > cfg["sizing"]["equity_slots"]:
        violations.append(f"Equity slots: {n_equity} held vs {cfg['sizing']['equity_slots']} max")
    if n_leap > cfg["sizing"]["leap_slots"]:
        violations.append(f"LEAP slots: {n_leap} held vs {cfg['sizing']['leap_slots']} max")

    if equity_total > 0:
        cash_pct = snap.get("cash", 0) / equity_total
        if cash_pct < cfg["sizing"]["min_cash_floor_pct"]:
            violations.append(f"Cash floor: {cash_pct:.1%} vs {cfg['sizing']['min_cash_floor_pct']:.0%} min")
        leap_pct = sum(
            h["quantity"] * h["avg_entry_price"] for h in holdings if h["kind"] == "leap"
        ) / equity_total
        if leap_pct > cfg["leap"]["sleeve_cap_pct_of_book"]:
            violations.append(f"LEAP sleeve: {leap_pct:.1%} vs {cfg['leap']['sleeve_cap_pct_of_book']:.0%} max")
        for h in holdings:
            if h["kind"] != "equity":
                continue
            pos_pct = h["quantity"] * h["avg_entry_price"] / equity_total
            if pos_pct > cfg["sizing"]["max_position_pct_of_book"]:
                violations.append(
                    f"{h['ticker']} size: {pos_pct:.1%} vs "
                    f"{cfg['sizing']['max_position_pct_of_book']:.0%} max"
                )
    return {"available": True, "violations": violations}


def render_report(cfg=None, exit_variant: str = "simple_09") -> str:
    cfg = cfg or load_config()
    tickers, leap_tickers, meta = load_universe()
    rows, failed = _latest_frames(cfg, tickers, leap_tickers)
    eligible, firing = eligible_and_firing(rows)
    positions = open_positions_section(cfg, rows, exit_variant)
    violations = violations_section(cfg, positions)

    L = [f"# Daily Scan — {pd.Timestamp.now().date()}", "",
        "> Decision-support only. Recommends; you execute. No orders placed by this tool.", ""]

    L.append(f"## 1. ELIGIBLE ({len(eligible)} names ≥40%/25% below hybrid anchor, quality-gated)\n")
    L.append("| Ticker | Drawdown | Close | 2yr High | Dip Low |")
    L.append("|---|---|---|---|---|")
    for e in eligible[:30]:
        L.append(f"| {e['ticker']} | {e['dd_pct']:.1%} | {e['close']:.2f} | "
                 f"{e['high_2yr']:.2f} | {e['dip_low']:.2f} |")
    if len(eligible) > 30:
        L.append(f"| ... | {len(eligible)-30} more | | | |")

    L.append(f"\n## 2. FIRING TODAY ({len(firing)} eligible names with a UT buy on {ENTRY_TF})\n")
    if firing:
        L.append("| Ticker | Drawdown | Close |")
        L.append("|---|---|---|")
        for f in firing:
            L.append(f"| {f['ticker']} | {f['dd_pct']:.1%} | {f['close']:.2f} |")
    else:
        L.append("*None firing today.*")

    L.append("\n## 3. OPEN POSITIONS\n")
    if not positions["available"]:
        L.append(f"*{positions['note']}*")
    elif not positions["positions"]:
        L.append("*No open positions on file.*")
    else:
        L.append("| Ticker | Kind | Fib fraction | Next level up | Weekly UT sell active | Anchor |")
        L.append("|---|---|---|---|---|---|")
        for p in positions["positions"]:
            if "error" in p:
                L.append(f"| {p['ticker']} | — | — | — | — | {p['error']} |")
                continue
            nxt = min((lv for f, lv in p["levels"].items() if f > p["fib_fraction"]), default=None)
            anchor_note = "APPROXIMATE (today)" if p["anchor_approximate"] else "exact (entry date)"
            L.append(f"| {p['ticker']} | {p['kind']} | {p['fib_fraction']:.2f} | "
                     f"{nxt if nxt is None else round(nxt,2)} | "
                     f"{'YES' if p['weekly_ut_sell_active'] else 'no'} | {anchor_note} |")

    L.append("\n## 4. VIOLATIONS (live book vs STRATEGY.md)\n")
    if not violations["available"]:
        L.append(f"*{violations['note']}*")
    elif not violations["violations"]:
        L.append("*None.*")
    else:
        for v in violations["violations"]:
            L.append(f"- {v}")

    if failed:
        L.append(f"\n## Coverage note\n\n{len(failed)}/{len(tickers)} names failed to load: "
                 f"{', '.join(t for t, _ in failed[:10])}"
                 f"{' ...' if len(failed) > 10 else ''}")

    L.append(f"\n---\n*Universe: {meta['note']}*")
    return "\n".join(L)


if __name__ == "__main__":
    print(render_report())
