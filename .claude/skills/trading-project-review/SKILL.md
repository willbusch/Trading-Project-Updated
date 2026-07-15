---
name: trading-project-review
description: Review the state of the Trader-Resp stock screener project — read PLAN.md, STRATEGY.md, and the code, then report back as a checklist covering what's working, what needs work, what could be better, what we're currently building, and what the next step is. Use this skill whenever the user asks about project status, progress, "where are we," "what's next," "what needs work," "review the plan," "what's left," or asks to check/update PLAN.md. Also use it when the user returns to the project after a break and needs to re-orient, or before starting a new stage or step. Trigger this even if the user just asks a vague "what should I work on" — this skill is how you find out.
---

# Trading Project Review

Produce an honest, checklist-style status review of the Trader-Resp stock
screener project. The user is building a three-stage trading pipeline
(screen → buy signals → sell signals) plus a backtest, driven by a written
strategy.

The goal is orientation and honesty, not cheerleading. The user wants to know
what is *actually* done versus what merely exists, and what to do next.

## Step 1 — Read the project state (do this first, always)

Read these files before saying anything about status. Do not rely on memory or
on what was discussed earlier in the conversation — the repo is the source of
truth and may have changed.

1. **`PLAN.md`** — the roadmap: stages, steps, and their status tags.
2. **`STRATEGY.md`** — the trader's philosophy. Every stage exists to encode
   these rules; check whether the code actually matches them.
3. **`config.yaml`** — the live thresholds. A filter that exists in code but is
   commented out here is **not** actually running.
4. **The code** — at minimum skim `screener/` (`screen.py`, `data.py`,
   `discount.py`, `signals_metrics.py`, `portfolio.py`) and `tests/`.
5. **`portfolio.yaml`** if present (gitignored; may be absent) — the real
   holdings that Stage 3 and any backtest key off.

If a file is missing, say so rather than guessing at its contents.

## Step 2 — Run the tests (if the environment allows)

```bash
python -m pytest -q
```

Report the actual pass/fail count. If tests can't run (no network to install
deps, etc.), say that plainly instead of implying they passed.

## Step 3 — Produce the checklist

Output in exactly this structure. Keep it scannable.

### ✅ What's working
Things that are built, tested, AND actually active. Be specific — name the
module or config key. A feature that is written but switched off in
`config.yaml` does **not** belong here.

### ⚠️ What needs work
Things that are partially done, disabled, fragile, or don't fully match
`STRATEGY.md`. For each, say concretely what's missing. Common instances in
this project:
- Filters implemented in code but commented out in `config.yaml`
- Rules in `STRATEGY.md` that the code can't express yet
- Metrics computed but not wired into a filter or signal
- Anything verified only on synthetic data and never run against live yfinance

### 💡 What could be better
Genuine improvements, not busywork. Look for:
- Gaps between `STRATEGY.md` and what the code enforces
- Thresholds that may be too loose/strict and would benefit from a real run
- Data caveats worth surfacing (thin option quotes, missing yfinance
  financials, seasonal noise in QoQ revenue)
- Places where the user's actual portfolio doesn't match their stated strategy

### 📍 Where we are now
The specific stage and step currently in progress, and what remains to finish
*that step*.

### ➡️ Next step
One concrete, actionable next task. Not a list — a single next move, with a
sentence on why it's the highest-value thing right now.

## Honesty requirements (important)

This project involves real money, so accuracy matters more than encouragement.

- **Never mark something done that isn't.** "Built but disabled" is not done.
  "Passes synthetic tests" is not "works."
- **Distinguish verified from assumed.** If the code has never been run against
  live market data, say so explicitly — that gap has bitten this project before.
- **Surface strategy/code drift.** If `STRATEGY.md` says one thing and the code
  does another, that is the most important thing in the review. Lead with it.
- **Flag the portfolio mismatch if relevant.** Some of the user's real holdings
  may not fit the stated strategy. If the rules being built wouldn't have
  produced their actual trades, that's worth naming.
- **Do not recommend trades.** This is a research/decision-support tool. Report
  on the code and the rules, never on whether to buy or sell anything.
- **Backtests are not promises.** If a backtest exists, note the overfitting and
  changing-market caveats rather than presenting results as predictive.

## Optional: update PLAN.md

If the user asks to update the plan (or if the review reveals `PLAN.md` is
clearly stale), rewrite it to match reality — same stage/step structure, updated
status tags, refreshed "order of attack" and snapshot sections. Offer this;
don't do it unprompted.

## Project reference: the stage/step structure

For orientation, the project is organized as:

- **Stage 1 — Eligibility:** which stocks are even worth looking at
  (growth check, tiered deep-discount by market cap, quality gates, output)
- **Stage 2 — Buy signals:** instrument choice (shares vs LEAPS), entry metrics
  (MACD histogram, volume ratio), the *ordered* entry sequence
  (RSI cross → then MACD turn → then volume surge), sizing
- **Stage 3 — Sell signals:** options pricing, the downside momentum turn,
  "rejection from a level," emitting exits
- **Stage 4 — Validation:** backtest, after-close price refresh

The $500B market-cap line does double duty in this strategy: it sets both the
required drawdown (25% vs 40%) and the instrument (LEAPS vs shares). If a review
touches either, check both.
