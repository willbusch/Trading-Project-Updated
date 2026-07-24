---
name: trader-profile
description: Generate or refresh the owner's plain-English "how I trade" profile — philosophy, universe, entry signal, exit signal, risk & money management, current portfolio (with live rule-compliance flags), strengths, weaknesses, behavioral patterns, and what needs work. Use whenever the owner asks for their trader profile, "how I trade," "who am I as a trader," "my trading philosophy," "update/refresh my profile," or wants to be brought up to speed on their own strategy and book. Regenerates docs/TRADER-PROFILE.md from the current STRATEGY.md + config.yaml + portfolio.yaml so it never drifts.
---

# Trader Profile

Produce a **plain-English, full-detail** picture of how the owner trades, so
they can reread it, keep their portfolio updated, and see what needs work.
The audience is the owner reading about themselves — simple wording, no
jargon, full candor. Money is on the line: tell the truth, including the
uncomfortable parts.

**Output:** regenerate `docs/TRADER-PROFILE.md` (overwrite it — it is a
living doc, never hand-edited). Offer to render an HTML version only if asked.

## Step 1 — read the current source of truth (always, don't use memory)
- `docs/STRATEGY.md` — the rules of record (philosophy, universe, entry,
  exit, risk). This is what the owner actually trades by; base the mechanics
  on it, not on the latest research variant.
- `config.yaml` — the exact numbers (drawdown tiers, sizing %, slots, cash
  floor, kill switch). Pull live values; never hardcode.
- `portfolio.yaml` — the current book. Compute each holding's market value
  (quantity × live_price), % of book, and unrealized P&L, and the total book.
- Note freshness: portfolio.yaml flags which lines are live vs. carried from
  an old audit vs. estimated. Surface those flags verbatim — do not present
  stale data as current.

## Step 2 — check the book against the rules (this is the point)
Compare the live book to `config.yaml`'s risk limits and flag every
violation plainly:
- position count vs. max slots; LEAP count vs. 1; LEAP sleeve % vs.
  `leap.sleeve_cap_pct_of_book`; largest equity vs.
  `sizing.max_position_pct_of_book`; cash vs. `sizing.min_cash_floor_pct`;
  any LEAP underlying that isn't top-10-by-cap (ineligible).
- Call out losers and any position that was averaged-down without a trigger.

## Step 3 — render docs/TRADER-PROFILE.md with these titled sections
1. **Philosophy** — what I believe (plain bullets).
2. **What I Buy** — the universe/quality gate as a simple table + the
   survivorship-bias caveat.
3. **When I Buy** — the drawdown gate (tiers) + the UT-Bot trigger, both
   required; LEAP vs. shares.
4. **When I Sell** — the Fibonacci recovery zones in plain terms, no stops,
   trailing past 1.618, LEAP decay tightening, and THE CASH RULE.
5. **How I Size & Manage Risk** — slots, sizing, LEAP sleeve, cash floor,
   weekly cap, kill switch, tiebreak — as a table.
6. **My Current Portfolio** — the holdings table with % of book + unrealized,
   a freshness warning, and a "🔴 what's broken right now" list of every rule
   violation.
7. **Strengths** — what the owner does well.
8. **Weaknesses & Risks** — the honest hard part (concentration + leverage +
   no stops; rules broken in the live book; unproven edge; never traded a
   bear).
9. **Behavioral Patterns to Watch** — about the person, not the strategy
   (the average-down itch, overriding own rules, big-single-bet comfort,
   letting winners balloon). Constructive, specific, drawn from the
   documented history.
10. **What Needs Work** — a short, actionable improvement list (Phase 0 first).
11. **Honest Status** — plausible-not-proven; the edge leans on a few LEAP
    trades; forward testing is the only real proof left.
12. **Key Numbers** — the latest backtest metrics vs SPY, with the
    concentration caveat.

## Step 4 — keep it honest
- Full candor is the default (the owner asked for it). Do not soften the
  book violations or the "edge is unproven" verdict.
- Simple wording throughout — imagine explaining it to a smart friend who
  doesn't trade.
- Date the file ("Last generated: <date>").

## Optional — live portfolio pull
If the owner asks for the CURRENT book (not the yaml snapshot), pull live via
the Robinhood MCP tools (get_equity_positions, get_option_positions,
get_accounts for cash) BEFORE Step 1, reconcile against portfolio.yaml, and
note which account(s) were reachable. Otherwise use portfolio.yaml as-is with
its freshness flags.

## After generating
Mention any newly-surfaced book violations to the owner in chat, and offer to
run `handoff-to-chat` if they want the update synced.
