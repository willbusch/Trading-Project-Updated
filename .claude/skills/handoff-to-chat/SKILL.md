---
name: handoff-to-chat
description: Use this skill when the user asks to "handoff to chat," "sync to chat," "catch up chat," "session report," or "what changed" — any request to package the current Claude Code session for Claude chat. Produces ONE copy-paste block containing (1) current strategy metrics, (2) all changes since the last handoff, and (3) a built-in analyst prompt telling chat how to respond. Bridges the memory gap so chat acts as Code's second brain.
---

# Handoff To Chat

Produce ONE self-contained block the user pastes into Claude chat. Chat has NO memory of this session. The block must carry the numbers, the changes, AND the instructions — so the user pastes one thing and nothing else.

## Step 1 — Find the anchor
- Read HANDOFF.md (repo root). Top entry's LAST_COMMIT: <hash> = last handoff point.
- If HANDOFF.md doesn't exist, create it and diff the last 20 commits.

## Step 2 — Ask before assembling (every run)
Use the AskUserQuestion tool to pop up two questions. Always ask both, every
time this skill runs — priority and tone can shift session to session (after
a backtest, a drawdown, a new signal idea), so never silently reuse a past
answer or guess.

1. **Priority** — "What should chat prioritize improving first?"
   Options: Win rate · Avg R / payoff ratio · Max drawdown / risk ·
   Whatever's weakest (let chat decide). The tool's built-in "Other" option
   covers anything more specific (e.g. "the LEAP sleeve specifically").

2. **Pushback level** — "How hard should chat push back on weak points?"
   Options:
   - **Gentle** — soft suggestions, mostly validating.
   - **Firm but balanced** — direct, names weaknesses plainly, no
     sugarcoating, but not harsh.
   - **Brutal / no filter** — tell it bluntly, accuracy over feelings.

Capture the two answers as `[PRIORITY]` and `[PUSHBACK LEVEL]` for Step 5.

If `AskUserQuestion` is unavailable in whatever context is running this
skill, fall back to "whatever's weakest" and "firm but balanced" and say so
in the output — but this should be rare; always prefer asking.

## Step 3 — Pull strategy metrics
- From the most recent backtest artifact/output in this session, extract: win rate, avg R per trade, max drawdown, # of trades. If a metric is missing, write "N/A."
- From config.yaml and STRATEGY.md, extract: timeframe, stop logic, entry rules in effect.
- If no backtest ran this session, write "No new backtest this session — metrics unchanged from last handoff."

## Step 4 — Scan changes since the anchor
- git log --oneline <anchor>..HEAD
- git diff --stat <anchor>..HEAD
- git diff <anchor>..HEAD — READ the changes, understand intent
- git status + git diff — uncommitted/half-finished work
- Map changes against PLAN.md / ROADMAP.md

## Step 5 — Assemble the paste block (output EXACTLY this, filled in)

```
# HANDOFF TO CHAT — [date/time]

## STRATEGY SNAPSHOT
- Win rate: [x%]   Avg R: [x]   Max drawdown: [x%]   # trades: [x]
- Timeframe: [from config/STRATEGY]
- Stop logic: [from config/STRATEGY]
- Entry rules in effect: [short summary]

## WHAT CHANGED THIS SESSION
- MAJOR: [file — what + WHY it matters to the edge]
- MINOR: [file — small edits/fixes]
- DECISIONS: [choices chat should know, e.g. "volume window → 10 bars"]

## CURRENT STATE
- Working now: [...]
- Broken/half-finished: [...]

## NEXT STEP (per ROADMAP)
- [single next action]

---

## PROMPT FOR CHAT — act on everything above
You are my top-tier financial analyst with deep technical-analysis and
quantitative expertise. You are Claude Code's second brain — the snapshot
above is the full, current state of my trading strategy.

Your job: make this strategy better from where it stands. "Better" = higher
win rate, higher % won per trade, better avg R, lower risk/drawdown.

Rules for your response:
- Prioritize improving [PRIORITY] first.
- Push back at a [PUSHBACK LEVEL] level — tell me what's weak, don't just agree.
- Give me CONCEPTUAL suggestions first. I approve before anything becomes
  backtest-ready rules. Do NOT hand me code or exact parameters yet.
- ALWAYS flag trade-offs where a change would lower win rate but raise total
  profit (or vice versa) — that's where the edge hides.
- End with: (1) the ONE sharpest change to make next, and (2) a short ranked
  backup list.
```

## Step 6 — Log the anchor
Prepend to HANDOFF.md:
```
---
## [date/time]
LAST_COMMIT: <current HEAD hash>
[STRATEGY SNAPSHOT one-liner + NEXT STEP]
---
```

## Rules
- Output the paste block and nothing else the user has to edit.
- Translate code → plain trading/strategy language.
- Never dump raw diffs. Summarize intent.
- [PRIORITY] and [PUSHBACK LEVEL] always come from the live Step 2 pop-up —
  never silently defaulted or reused from a previous run.
- Keep the whole block tight enough to paste cleanly.
