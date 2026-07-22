---
name: run-backtest
description: Run a Trader-Resp backtest (single cell, the 12-cell grid, the cumulative attribution ladder, or a full research round) the canonical way, with the mandatory leak-hunt and overfitting discipline applied automatically. Use this skill whenever the user asks to run a backtest, run the grid, test a config change, "run the numbers," re-run the champion cell, do an attribution/ablation run, or check whether a change beats SPY. It wraps scripts/run_backtest.py so the harness (background execution, universe-snapshot-once, pickle locations, stats extraction) is never re-derived, and enforces the honest-verdict framing every run in this project requires.
---

# Run Backtest

The point of this skill is that this project has run six research generations
and every one re-derived the same run harness AND re-applied the same
skepticism by hand. This encodes both: the mechanics (via
`scripts/run_backtest.py`) and the discipline (leak-hunt, overfitting guard,
honest verdict). Follow it in order — do not skip the guard steps just
because a number looks good. **In this project, a number that looks too good
is treated as a bug until proven otherwise.**

## Step 0 — Environment + data (always, before any run)

1. If `python -m pytest -q` fails with `No module named ...`, the env isn't
   set up: `source .venv/bin/activate && export PYTHONPATH=$(pwd)`. (The
   SessionStart hook does this automatically once installed — if runs keep
   needing manual setup, the hook isn't active yet.)
2. `python scripts/run_backtest.py check` — confirms `data_cache/*.parquet`
   covers the full universe + SPY. **The cache is gitignored and a fresh
   container starts empty.** If names are missing, they must be re-ingested
   via the Robinhood MCP tools (`mcp__robinhood__get_equity_historicals` per
   name → `screener.data.ingest_robinhood_bars`, see `scanner/refresh.py`)
   BEFORE any run. Do not start a grid with a partial cache — it silently
   changes slot competition and invalidates the result.

## Step 1 — Pick the smallest run that answers the question

- Code change / sanity only → `run_backtest.py smoke` (~2s, 15 names, 1 cell).
- "Does this config beat SPY / what's the champion?" → `run_backtest.py grid`
  (~8 min, all 12 cells). **Launch in the background and poll** — never block
  a foreground `sleep`. Full universe `simulate_fib` is ~35–40s per cell.
- "Which single fix mattered?" → `run_backtest.py attribution` (reads the
  grid pickle, runs the 7-step ladder on the champion cell).
- A full round → `run_backtest.py all`.

Long runs: launch with `run_in_background: true`, then poll with an
`until ! ps -p <pid>` loop (or the task-completion notification). Results
pickle to the scratchpad under stable names (`beat_spy_grid_results.pkl`,
`beat_spy_ranking.pkl`, `beat_spy_ladder.pkl`) that the analysis and
dashboard steps read.

## Step 2 — Selection rule (never violate)

- Rank cells by **return ÷ max drawdown**, and show **max drawdown on every
  row**. A huge return next to a ~2× SPY drawdown is NOT a win.
- Selection happens on **pre-vault** metrics ONLY. The 12-month vault is
  tested ONCE and never used to choose between candidates.
- A cell only "beats SPY" if it beats SPY on **BOTH return AND max drawdown**,
  in **both** windows. State it in exactly those terms.

## Step 3 — Mandatory overfitting guard (print it, don't skip it)

The runner prints a first pass automatically; verify and expand it:

1. **Thin margin** — if #1 beats #2 by a small margin (rule of thumb <15%),
   say so plainly and treat the "winner" as within noise.
2. **Vault divergence** — every cell's vault number here rests on ~1 closed
   trade. Say "too thin to validate," don't present it as edge.
3. **Concentration** — pull the champion's trade log and check whether the
   return is carried by 2–3 large trades (especially LEAPs). If so, name
   them and flag it as likely lucky timing, not structural edge.
4. **Lookahead surfaces** — any NEW feature that could see the future
   (top-10-cap ranking, SPY-reserve mark-to-market, trailing-peak tracking)
   must have a passing truncation-invariance test. If a result got much
   better right after adding one, leak-hunt that feature specifically.

## Step 4 — Honest verdict (required, verbatim spirit)

Write the verdict in plain terms, and if it still loses to SPY
risk-adjusted, say so as a **valid and valuable finding, not a failure** —
"the honest answer is to index, proven rather than assumed." Do not soften a
loss and do not let a good number end the skepticism. This universe is still
survivorship-biased with current-snapshot caps; beating SPY here is
NECESSARY but NOT SUFFICIENT evidence of edge.

## Step 5 — Wire results through, don't re-derive

- Dashboard: `python scripts/generate_dashboard.py` — self-contained, reads
  the SAME pickles this skill produced, so the dashboard and any written
  report always agree (no re-simulation).
- Report/docs: update `reports/`, then `docs/STRATEGY.md` +
  `docs/PLAN.md` override logs, then hand off (the `handoff-to-chat` skill).

## Guardrails

- All thresholds/tiers/sizes are owner-specified. Implement exactly — never
  sweep or optimize beyond named cells without an explicit owner ask.
- Keep every existing test green; add a test for any new engineered feature,
  including a lookahead test if it could see the future.
- No trading. Backtest and reporting only.
