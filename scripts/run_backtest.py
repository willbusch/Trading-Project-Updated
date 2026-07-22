"""Canonical backtest runner — one committed entry point that replaces the
throwaway scratchpad scripts written fresh every research generation.

WHY THIS EXISTS: each research round re-derived the same harness (launch a
full-universe run, poll it, pickle results, extract stats, leak-hunt). This
consolidates that into one parameterized CLI so the next round is a flag,
not a re-write. It also fixes the universe-snapshot-timing sensitivity
PLAN.md parked: frames are built ONCE per invocation from the committed
data/universe_snapshot.json + data_cache, so every cell/window/ladder step
in a single run sees an identical universe (no cross-invocation drift).

USAGE (venv + PYTHONPATH assumed — the SessionStart hook sets both; if not,
`source .venv/bin/activate && PYTHONPATH=. python scripts/run_backtest.py ...`):

    python scripts/run_backtest.py check          # data-cache coverage only, no run
    python scripts/run_backtest.py smoke          # 1 cell, ~15 names — fast sanity
    python scripts/run_backtest.py grid           # full 12-cell grid (~8 min)
    python scripts/run_backtest.py attribution    # 7-step ladder on the champion cell
    python scripts/run_backtest.py all            # grid + ranking + attribution + champion

Results pickle to the scratchpad (see SCRATCH below) under stable names the
analysis/dashboard steps read. Long runs should be launched in the
background (run_in_background) and polled — a full grid is ~8 minutes.

DATA DEPENDENCY (read before assuming a run will work): the price bars in
data_cache/*.parquet are GITIGNORED and populated by the agent via the
Robinhood MCP tools (see scanner/refresh.py REFRESH_CHECKLIST). A fresh
container starts with an EMPTY cache. `run_backtest.py check` reports
coverage and names exactly what's missing so a run never fails cryptically
mid-flight — always run `check` first in a new session.
"""
import argparse
import os
import pickle
import sys
import time
import warnings

warnings.filterwarnings("ignore")

SCRATCH = os.environ.get(
    "TRADER_SCRATCH",
    "/tmp/claude-0/-home-user-Trading-Project-Updated/"
    "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad",
)


def _load():
    """Deferred imports so `check` can report a missing-deps/env problem
    with a clear message instead of an import traceback."""
    from screener.config import load_config
    from backtest.fib_universe import load_universe
    return load_config, load_universe


def cmd_check(_args):
    """Report data-cache coverage vs the universe list. No simulation."""
    import glob
    from backtest.fib_universe import load_universe

    tickers, leap_tickers, meta = load_universe()
    cache_dir = "data_cache"
    present = {
        os.path.basename(p).replace("_daily.parquet", "")
        for p in glob.glob(os.path.join(cache_dir, "*_daily.parquet"))
    }
    needed = set(tickers) | {"SPY"}
    missing = sorted(needed - present)
    print(f"universe names:        {len(tickers)}")
    print(f"cache files present:   {len(present)}")
    print(f"needed (universe+SPY): {len(needed)}")
    if missing:
        print(f"\n‼️  MISSING {len(missing)} names — re-ingest via Robinhood MCP before running:")
        print("   ", ", ".join(missing))
        print("\n   (agent-orchestrated: mcp__robinhood__get_equity_historicals per name,")
        print("    then screener.data.ingest_robinhood_bars — see scanner/refresh.py)")
        return 1
    print("\n✅ cache covers the full universe + SPY. Backtests can run.")
    return 0


def _build_all_frames(cfg):
    """Build frames ONCE per timeframe, shared across every cell/window in
    this invocation — the fix for the cross-invocation universe drift."""
    from backtest.beat_spy_grid import build_frames_for_entry_tf, B1_ENTRY_TFS
    from backtest.fib_universe import load_universe

    tickers, leap_tickers, meta = load_universe()
    frames_by_tf = {}
    for tf in B1_ENTRY_TFS:
        frames_by_tf[tf] = build_frames_for_entry_tf(
            tickers, leap_tickers, tf, cfg, meta["market_caps"])
    return frames_by_tf, leap_tickers, meta


def cmd_smoke(_args):
    """One cell, a small slice of names — fast end-to-end sanity that the
    whole Part-A pipeline still runs after a code change."""
    from screener.config import load_config
    from backtest.fib_universe import load_universe, build_universe_frames
    from backtest.fib_simulator import simulate_fib
    from screener.data import fetch_daily_bars

    cfg = load_config()
    tickers, leap_tickers, meta = load_universe()
    subset = tickers[:15]
    frames = build_universe_frames(subset, leap_tickers, "daily", "weekly", cfg,
                                   market_caps=meta["market_caps"], add_topcap_column=True)
    spy_ret = fetch_daily_bars("SPY")["Close"].pct_change()
    t0 = time.time()
    res = simulate_fib(frames, cfg, seed_cash=cfg["backtest"]["seed_cash"], cell="smoke",
                       leap_tickers=leap_tickers, exit_variant="trail_ut", idle_cash_spy=spy_ret,
                       leap_topcap_eligibility=True, leap_decay_exit=True, slot_recycling=True,
                       equity_sizing_variant="both")
    print(f"smoke OK in {time.time()-t0:.1f}s — {len(res.trades)} trades, "
         f"{len(res.recycle_events)} recycles, kinds={set(t.kind for t in res.trades)}")
    return 0


def cmd_grid(_args):
    from screener.config import load_config
    from backtest.beat_spy_grid import run_grid

    cfg = load_config()
    t0 = time.time()
    grid = run_grid(cfg)
    print(f"grid done in {time.time()-t0:.1f}s")
    frames_by_tf = grid.pop("frames_by_tf")
    pickle.dump(grid, open(f"{SCRATCH}/beat_spy_grid_results.pkl", "wb"))
    pickle.dump(frames_by_tf, open(f"{SCRATCH}/beat_spy_grid_frames.pkl", "wb"))
    print(f"wrote {SCRATCH}/beat_spy_grid_results.pkl (+ frames)")
    _rank_and_print(grid)
    return 0


def _rank_and_print(grid):
    gr = grid["grid_results"]
    pv, va = "combined (pre-vault)", "VAULT (last 12mo, tested once)"
    rows = []
    for cell_key, res in gr.items():
        d = res[pv]
        ret, dd = d["dd"]["total_return"], d["dd"]["max_drawdown"]
        ratio = ret / dd if dd and dd > 0 else float("nan")
        rows.append((ratio, cell_key, ret, dd, d["trade"]["n_closed"],
                     res[va]["trade"]["n_closed"]))
    rows.sort(key=lambda r: -(r[0] if r[0] == r[0] else -999))
    spy = grid["benchmarks"]["spy_prevault"]
    print("\nrank  cell                                   ratio    return   maxDD  trades  vault_n")
    for i, (ratio, ck, ret, dd, n, vn) in enumerate(rows):
        print(f"{i+1:<5} {str(ck):<38}{ratio:>7.2f}{ret:>10.1%}{dd:>8.1%}{n:>8}{vn:>9}")
    print(f"SPY (pre-vault): return {spy['total_return']:.1%}, maxDD {spy['max_drawdown']:.1%}")
    if len(rows) > 1:
        margin = (rows[0][0] - rows[1][0]) / abs(rows[1][0]) if rows[1][0] else float("inf")
        print(f"\n⚠️  OVERFITTING GUARD: #1 beats #2 by {margin:.1%} "
             f"({'THIN — treat as noise' if margin < 0.15 else 'clear'}). "
             f"Champion vault_n={rows[0][5]} "
             f"({'TOO THIN to validate' if rows[0][5] <= 2 else 'ok'}).")
    pickle.dump({"rows": rows}, open(f"{SCRATCH}/beat_spy_ranking.pkl", "wb"))


def cmd_attribution(_args):
    from screener.config import load_config
    from backtest.beat_spy_grid import run_attribution_ladder, _windows
    from backtest.fib_universe import load_universe
    from screener.data import fetch_daily_bars

    cfg = load_config()
    grid = pickle.load(open(f"{SCRATCH}/beat_spy_grid_results.pkl", "rb"))
    frames_by_tf = pickle.load(open(f"{SCRATCH}/beat_spy_grid_frames.pkl", "rb"))
    ranking = pickle.load(open(f"{SCRATCH}/beat_spy_ranking.pkl", "rb"))
    champ_cell = ranking["rows"][0][1]
    entry_tf, sizing, trailing = champ_cell
    _, leap_tickers, meta = load_universe()
    spy_ret = fetch_daily_bars("SPY")["Close"].pct_change()
    windows = _windows(cfg, grid["vault_start"])
    print(f"attribution ladder on champion cell {champ_cell}")
    ladder = run_attribution_ladder(cfg, entry_tf, sizing, trailing,
                                    frames_by_tf[entry_tf], leap_tickers, spy_ret, windows)
    pickle.dump(ladder, open(f"{SCRATCH}/beat_spy_ladder.pkl", "wb"))
    print(f"wrote {SCRATCH}/beat_spy_ladder.pkl")
    return 0


def cmd_all(args):
    rc = cmd_grid(args)
    if rc == 0:
        rc = cmd_attribution(args)
    return rc


COMMANDS = {
    "check": cmd_check, "smoke": cmd_smoke, "grid": cmd_grid,
    "attribution": cmd_attribution, "all": cmd_all,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=list(COMMANDS), help="what to run")
    args = ap.parse_args()
    try:
        _load()
    except ModuleNotFoundError as e:
        print(f"‼️  environment not set up ({e}). Activate the venv + set PYTHONPATH:")
        print("   source .venv/bin/activate && export PYTHONPATH=$(pwd)")
        print("   (the SessionStart hook does this automatically once installed)")
        return 2
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
