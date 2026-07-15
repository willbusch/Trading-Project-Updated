---
name: trading-project-review
description: Review the state of the Trader-Resp RSI mean-reversion screener project — full-scan the repo (docs, config.yaml, code, tests) and report back as a top-level-readable status report covering what's working, what needs work, what could be better, where we are, and what's next. Use this skill whenever the user asks about project status, progress, "where are we," "what's next," "what needs work," "review the plan," "what's left," or asks to check/update docs/PLAN.md. Also use it when the user returns to the project after a break and needs to re-orient, or before starting a new stage or step. Trigger this even if the user just asks a vague "what should I work on" — this skill is how you find out.
---

# Trading Project Review

Produce an honest, full-scan status review of the Trader-Resp RSI
mean-reversion screener project. The user is building a seven-stage pipeline
(Stage 0 Foundation → Stage 6 Backtest, per `docs/CLAUDE-CODE-PROMPT.md`)
driven by a single written strategy (`docs/STRATEGY.md`): RSI(3) on 3-day
bars, an SMA(200) trend filter, and an ATR(14)-spaced 3-tranche ladder — no
other indicators.

The goal is orientation and honesty, not cheerleading. The user wants to know
what is *actually* done versus what merely exists, and what to do next.

## Step 1 — Full scan (do this first, always)

Read the actual repo — do not rely on memory or on what was discussed earlier
in the conversation. The repo is the source of truth and changes every
session. Read/enumerate all of the following:

1. **`docs/PLAN.md`** — the roadmap: Phases 0–5, steps, and status tags.
2. **`docs/STRATEGY.md`** — the trader's philosophy (universe, entry, tranche
   ladder, LEAP rules, exits, risk controls, override log). Every stage
   exists to encode these rules; check whether the code actually matches
   them.
3. **`docs/CLAUDE-CODE-PROMPT.md`** — the detailed build spec with the finer
   Stage 0–6 numbering that the code itself uses (e.g. `gate_stage0.py`).
   `docs/PLAN.md`'s Phases and this file's Stages don't map 1:1 — Phase 1
   alone spans Stages 0 through 4. Reconcile against both rather than
   picking one.
4. **`docs/GOAL.md`** — the return target and what "success" looks like;
   useful for judging whether a metric is even the right thing to chase.
5. **`config.yaml`** — every threshold as a named key. Flag any key whose
   value is `null` — that means a rule from `STRATEGY.md` is written down but
   deliberately left unresolved (e.g. lookback windows nobody's specified
   yet), not a bug, but a real gap consuming code can't work around.
6. **The code** — enumerate what actually exists under `screener/`,
   `backtest/`, and `dashboard/` (don't assume file names from a prior
   review; list the directory and read each file). Note directories that
   exist only as empty local scaffolding and were never actually committed
   (git doesn't track empty directories — if `dashboard/` has no files, it
   isn't really "started" even if the folder exists on disk).
7. **`tests/`** — enumerate and read each test file; note what's actually
   covered (which indicators, which edge cases) versus assumed.
8. **`requirements.txt`** — flag any import in the code that isn't pinned
   here, or any pinned package nothing imports.
9. **`HANDOFF.md`** if present — prior sessions' self-reported state; cross-
   check it against what's actually in the repo now rather than trusting it.
10. **`portfolio.yaml`** if present (gitignored, likely absent) — the real
    holdings that Stage 2 sizing and Stage 3 constraint-checking key off. If
    it's absent, say so explicitly — those stages can't be checked against a
    real book without it.

If a file referenced by `docs/PLAN.md` or `docs/STRATEGY.md` doesn't exist
yet, that absence is itself a review finding — report it, don't skip it or
guess at contents.

## Step 2 — Run the tests

```bash
python -m pytest -q
```

Report the actual pass/fail count. If tests can't run (missing deps, no venv,
etc.), say that plainly instead of implying they passed.

## Step 3 — Produce the report

Two layers: a scannable top section for someone re-orienting in 10 seconds,
then full detail underneath for someone who wants it.

### TOP — Status at a glance
One line per stage (Stage 0–6, per `docs/CLAUDE-CODE-PROMPT.md`): ✅ Done /
🔶 Partial / ⛔ Not started, plus a 3–5 word reason. Follow with a 2–3
sentence TL;DR: what's actually solid, the single biggest gap, what's next.

### ✅ What's working
Things built, tested, AND actually active — name the real module or config
key. A feature that's written but off in `config.yaml`, or a test that only
covers synthetic data, does **not** belong here.

### ⚠️ What needs work
Things partially done, disabled, fragile, or that don't fully match
`STRATEGY.md`. For each, say concretely what's missing. Watch for, in this
project specifically:
- `config.yaml` keys still `null` (unresolved thresholds)
- Rules in `STRATEGY.md` the code can't express yet (grading, sizing,
  constraint checker, cash-rule enforcement, LEAP rules — anything past
  Stage 1 as of this writing)
- A gate that ran once informally but was never confirmed by the user
  (e.g. RSI values eyeballed against TradingView but not signed off)
- Anything verified only against a non-primary data source (this project's
  intended source is yfinance; if a run substituted another source because
  of a network block, that substitution is a caveat, not a pass)
- Scaffolded-but-empty directories that look done from `ls` but aren't

### 💡 What could be better
Genuine improvements, not busywork:
- Gaps between `STRATEGY.md` and what the code enforces
- Thresholds that may be too loose/strict and would benefit from a real run
- Data caveats worth surfacing (resampling-anchor assumptions never
  validated against TradingView, thin option quotes, missing yfinance
  financials, seasonal noise)
- Places where the user's actual portfolio doesn't match their stated
  strategy (check `docs/portfolio-audit-*.md` if present)

### 📍 Where we are now
The specific stage/step in progress, and what remains to finish *that step*.

### ➡️ Next step
One concrete, actionable next task. Not a list — a single next move, with a
sentence on why it's the highest-value thing right now.

## Honesty requirements (important)

This project involves real money, so accuracy matters more than encouragement.

- **Never mark something done that isn't.** "Built but disabled" is not done.
  "Passes synthetic tests" is not "works." "Ran once on a substitute data
  source" is not "confirmed."
- **Distinguish verified from assumed.** If code has never been run against
  live market data via the intended source, say so explicitly — that gap has
  bitten this project before.
- **Surface strategy/code drift.** If `STRATEGY.md` says one thing and the
  code does another, that is the most important thing in the review. Lead
  with it.
- **Flag the portfolio mismatch if relevant.** Some of the user's real
  holdings may not fit the stated strategy. If the rules being built
  wouldn't have produced their actual trades, that's worth naming.
- **Do not recommend trades.** This is a research/decision-support tool.
  Report on the code and the rules, never on whether to buy or sell anything.
- **Backtests are not promises.** If a backtest exists (including an
  informal/exploratory one), note the overfitting and small-sample caveats
  rather than presenting results as predictive. An exploratory 2-name signal
  test is not the Stage 6 backtest and should never be reported as if it
  were.

## Optional: update docs/PLAN.md

If the user asks to update the plan (or the review reveals `docs/PLAN.md` is
clearly stale), rewrite it to match reality — same Phase/step structure,
updated status tags, refreshed "order of attack" and snapshot sections.
Offer this; don't do it unprompted.

## Project reference: the stage/step structure

Two documents describe this project's shape, at two granularities:

- **`docs/PLAN.md`** — Phase 0 (Fix the Book) → Phase 1 (Dashboard, which
  bundles config/data/resampling/indicators/universe/signals/sizing/
  constraints/UI) → Phase 2 (Pinescript) → Phase 3 (Backtest — the decision
  gate) → Phase 4 (Live, small) → Phase 5 (Scale).
- **`docs/CLAUDE-CODE-PROMPT.md`** — the finer Stage 0–6 breakdown actually
  reflected in code/commits:
  - **Stage 0 — Foundation:** `config.yaml`, yfinance fetch + parquet cache,
    documented daily→3-day resampling, Wilder-smoothed RSI/SMA/ATR. Gate:
    unit tests pass + eyeball RSI(3) on 3-day bars against TradingView.
  - **Stage 1 — Universe:** SPY+QQQ constituents (deduped), hard filters
    (market cap/price/volume), `SHARES_ELIGIBLE`/`LEAP_ELIGIBLE` tagging,
    `universe.csv`. Gate: count ~500–550.
  - **Stage 2 — Buy Signals:** RSI(3)<35 entry, SMA(200) trend filter, A/B/C/
    NO_TRADE grading, `portfolio.py` (mark-to-market, tranche depth), sizing
    engine, constraint checker (slots/position cap/LEAP cap/cash
    floor/weekly cap/halt).
  - **Stage 3 — Sell Signals:** RSI(3)≥80 euphoria exit; RSI touches ≥70 then
    crosses <60 momentum-break exit (primary); cash-rule enforcement
    (proceeds never fund an underwater position); LEAP 6-month-to-expiry
    flag.
  - **Stage 4 — Dashboard:** SIGNALS / BOOK / VIOLATIONS / BLOCKED panels.
  - **Stage 5 — Pinescript:** port entry/exit to Pine v5, reconcile against
    Python on 3 names.
  - **Stage 6 — Backtest:** 5 years, full universe, all constraints
    enforced, ablation study, above/below-200-SMA cohort split. The decision
    gate for the whole project — proceed only if expectancy clears the bar
    AND beats SPY buy-and-hold.

**There is no MACD, no volume-ratio entry sequence, no ordered
RSI→MACD→volume trigger chain, no options-pricing sell stage, and no
market-cap-tied drawdown split (25% vs 40%).** The strategy is a single
indicator — RSI(3) on 3-day bars — with an SMA(200) trend filter and an
ATR(14)-spaced tranche ladder. The $500B market-cap line does exactly one
job: it's the LEAP-eligibility cutoff (the "Mag7 rule"), nothing else. If a
review's findings reference any of the above, that's a sign the review
drifted from `docs/STRATEGY.md` and should be corrected against it, not
reported as fact.
