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
import yaml

from backtest.fib_exit import LeapSimpleExit
from backtest.fib_features import build_fib_frame
from backtest.fib_simulator import EQUITY_EXIT_VARIANTS
from backtest.fib_universe import gate_of, load_universe
from screener.config import load_config

ENTRY_TF, EXIT_TF = "daily", "weekly"
LIVE_POSITIONS_PATH = Path("data/live_positions_snapshot.json")   # Account 1 (MCP-reachable)
PORTFOLIO_YAML_PATH = Path("portfolio.yaml")                      # both accounts, manually maintained


def _load_two_account_book():
    """Two accounts, never merged for display. Account 1 prefers the
    live MCP snapshot when present (fresher); portfolio.yaml is the
    fallback / manually-reconciled source for whichever account this
    session's MCP connection can't reach (Account 2, currently)."""
    accounts = {}
    if PORTFOLIO_YAML_PATH.exists():
        doc = yaml.safe_load(PORTFOLIO_YAML_PATH.read_text())
        for key in ("account_1", "account_2"):
            if key in doc:
                accounts[key] = doc[key]
    if LIVE_POSITIONS_PATH.exists():
        live = json.loads(LIVE_POSITIONS_PATH.read_text())
        accounts["account_1"] = {
            "label": "Account 1 (live MCP pull)",
            "cash": live.get("cash", 0), "total_value": live.get("total_equity", 0),
            "holdings": live.get("holdings", []),
        }
    return accounts


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
    """Section 3. Reads the two-account book (Account 1 live via MCP when
    available, Account 2 from portfolio.yaml — see _load_two_account_book).
    Positions from each account are kept in separate groups, never merged.
    Anchors (dip_low, two_yr_high) are looked up as of the position's
    recorded entry_date when known — same anchors the backtest would have
    frozen at entry. If entry_date is missing, falls back to TODAY's
    anchor and labels the row APPROXIMATE rather than silently treating it
    as exact."""
    accounts = _load_two_account_book()
    if not accounts:
        return {"available": False, "by_account": {},
                "note": "No portfolio.yaml or live_positions_snapshot.json found."}

    by_account = {}
    for acct_key, acct in accounts.items():
        out = []
        for h in acct.get("holdings", []):
            t = h["ticker"]
            if t not in rows:
                out.append({"ticker": t, "error":
                           "does not currently clear the quality gate "
                           "($10B+ cap / positive margin / liquidity) — "
                           "held, but outside the scanned universe"})
                continue
            # BUG FIX (2026-07-20, found live-testing this scaffold): must
            # use the POSITION's own kind, not an empty leap_tickers set —
            # a LEAP held here uses the 25% gate for its anchor, not the
            # 40% equity gate, or its dip_low never accumulates (NaN
            # fraction downstream).
            gate = 0.25 if h["kind"] == "leap" else 0.40
            entry_date = h.get("entry_date")
            approximate = entry_date is None
            try:
                frame = build_fib_frame(t, gate, ENTRY_TF, EXIT_TF, cfg, use_hybrid=True)
            except Exception as e:
                out.append({"ticker": t, "error": f"{type(e).__name__}: {e}"})
                continue
            if approximate or pd.Timestamp(entry_date) not in frame.index:
                anchor_row = frame.iloc[-1]
                approximate = True
            else:
                anchor_row = frame.loc[pd.Timestamp(entry_date)]

            from backtest.drawdown_gate import price_fraction
            dip_low, two_yr_high = anchor_row["dip_low"], anchor_row["high_2yr"]
            if dip_low != dip_low:   # NaN: no eligible-gate episode to anchor to
                out.append({"ticker": t, "kind": h["kind"], "fib_fraction": None,
                           "note": "not currently in (or recently in) a "
                                   "Fib-eligible drawdown episode — no anchor "
                                   "to measure against; likely held under "
                                   "the retired pre-Fib rules"})
                continue
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
        by_account[acct_key] = {"label": acct.get("label", acct_key), "positions": out}
    return {"available": True, "by_account": by_account}


def violations_section(cfg, accounts: dict):
    """Section 4: live book vs STRATEGY.md's reconciled targets, computed
    on the COMBINED book across both accounts (matches this project's
    established convention — the original portfolio audit treated total
    exposure as one book even though it spans two real accounts). Position
    values use LIVE prices where available (portfolio.yaml's live_price),
    falling back to cost basis when no live mark is recorded."""
    if not accounts:
        return {"available": False, "violations": [],
                "note": "No portfolio.yaml or live_positions_snapshot.json found."}

    def mark(h):
        return h.get("live_price", h["avg_entry_price"])

    all_holdings = []
    total_cash = 0.0
    total_value = 0.0
    total_leap_value = 0.0
    for acct in accounts.values():
        acct_cash = acct.get("cash", 0) or 0
        acct_holdings = acct.get("holdings", [])
        # BUG FIX (2026-07-20): each account must fall back to its OWN
        # derived value independently — a global "if total_value==0" check
        # silently dropped Account 2's equity value whenever Account 1
        # already had an explicit total_value, understating the combined
        # book and wildly overstating every position's % of book.
        acct_value = acct.get("total_value") or (
            acct_cash + sum(h["quantity"] * mark(h) for h in acct_holdings)
        )
        total_cash += acct_cash
        total_value += acct_value
        all_holdings.extend(acct_holdings)

        # BUG FIX (2026-07-20): LEAP dollar exposure must use the LIVE
        # account value, not quantity*avg_entry_price (cost basis) — we
        # don't have a live per-contract options mark, but when an
        # account is ENTIRELY leaps, its own total_value already IS the
        # live valuation. Falls back to cost basis (flagged as an
        # approximation) only for accounts we can't value this way.
        acct_leaps = [h for h in acct_holdings if h["kind"] == "leap"]
        if acct_leaps and len(acct_leaps) == len(acct_holdings) and acct.get("total_value"):
            total_leap_value += acct["total_value"]
        else:
            total_leap_value += sum(h["quantity"] * mark(h) for h in acct_leaps)

    violations = []
    n_equity = sum(1 for h in all_holdings if h["kind"] == "equity")
    n_leap = sum(1 for h in all_holdings if h["kind"] == "leap")
    if n_equity > cfg["sizing"]["equity_slots"]:
        violations.append(f"Equity slots: {n_equity} held vs {cfg['sizing']['equity_slots']} max")
    if n_leap > cfg["sizing"]["leap_slots"]:
        violations.append(f"LEAP slots: {n_leap} held vs {cfg['sizing']['leap_slots']} max")

    if total_value > 0:
        cash_pct = total_cash / total_value
        if cash_pct < cfg["sizing"]["min_cash_floor_pct"]:
            violations.append(f"Cash floor: {cash_pct:.1%} vs {cfg['sizing']['min_cash_floor_pct']:.0%} min")
        leap_pct = total_leap_value / total_value
        if leap_pct > cfg["leap"]["sleeve_cap_pct_of_book"]:
            violations.append(f"LEAP sleeve: {leap_pct:.1%} vs {cfg['leap']['sleeve_cap_pct_of_book']:.0%} max")
        for h in all_holdings:
            if h["kind"] != "equity":
                continue
            pos_pct = h["quantity"] * mark(h) / total_value
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
    accounts = _load_two_account_book()
    violations = violations_section(cfg, accounts)

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

    L.append("\n## 3. OPEN POSITIONS (by account — never merged)\n")
    if not positions["available"]:
        L.append(f"*{positions['note']}*")
    elif not positions["by_account"]:
        L.append("*No open positions on file.*")
    else:
        for acct_key, acct in positions["by_account"].items():
            L.append(f"### {acct['label']}\n")
            if not acct["positions"]:
                L.append("*No positions.*\n")
                continue
            L.append("| Ticker | Kind | Fib fraction | Next level up | Weekly UT sell active | Anchor |")
            L.append("|---|---|---|---|---|---|")
            for p in acct["positions"]:
                if "error" in p:
                    L.append(f"| {p['ticker']} | — | — | — | — | {p['error']} |")
                    continue
                if p.get("fib_fraction") is None:
                    L.append(f"| {p['ticker']} | {p['kind']} | — | — | — | {p['note']} |")
                    continue
                nxt = min((lv for f, lv in p["levels"].items() if f > p["fib_fraction"]), default=None)
                anchor_note = "APPROXIMATE (today)" if p["anchor_approximate"] else "exact (entry date)"
                L.append(f"| {p['ticker']} | {p['kind']} | {p['fib_fraction']:.2f} | "
                         f"{nxt if nxt is None else round(nxt,2)} | "
                         f"{'YES' if p['weekly_ut_sell_active'] else 'no'} | {anchor_note} |")
            L.append("")

    L.append("\n## 4. VIOLATIONS (combined book across both accounts vs STRATEGY.md)\n")
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
