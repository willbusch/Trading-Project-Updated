---
name: handoff-to-chat
description: Use this skill when the user asks to "handoff to chat," "sync to chat," "catch up chat," "session report," or "what changed" — any request to package the current Claude Code session for Claude chat. Scans all changes since the last handoff, pulls current strategy facts, prints ONE data block for the user to paste into chat, and logs the handoff to HANDOFF.md so both sessions stay synced through one shared file.
---

# Handoff To Chat

Print ONE block the user pastes into chat. Carry FACTS ONLY — no analyst prompt, no advice (chat's Project instructions handle the thinking). HANDOFF.md is the shared memory between Code sessions; keep it current.

## Step 1 — Find the anchor
- Read HANDOFF.md (repo root). Top entry's LAST_COMMIT: <hash> = last handoff point.
- If HANDOFF.md doesn't exist, create it and diff the last 20 commits.

## Step 2 — Pull strategy facts
- From config.yaml + STRATEGY.md: RSI period(s), entry/exit rules, timeframe, stop logic, sizing, universe. Note any null/undefined keys that affect the signal.
- From the most recent backtest artifact/output this session (if any): win rate, avg R, max drawdown, # trades. If none ran, write "No new backtest this session."

## Step 3 — Scan changes since the anchor
- git log --oneline <anchor>..HEAD
- git diff --stat <anchor>..HEAD
- git diff <anchor>..HEAD — READ the changes, understand intent
- git status + git diff — uncommitted/half-finished work
- Map against docs/PLAN.md / ROADMAP.md

## Step 4 — Print the paste block (output EXACTLY this, filled in)

```
# HANDOFF TO CHAT — [date/time]

## STRATEGY SNAPSHOT
- RSI / entry / exit: [...]
- Timeframe: [...]   Stop logic: [...]   Sizing: [...]
- Undefined keys affecting signal: [list or None]
- Backtest: win rate [x] / avg R [x] / drawdown [x] / #trades [x]  (or "none this session")

## WHAT CHANGED THIS SESSION
- MAJOR: [file — what + WHY it matters]
- MINOR: [file — small edits/fixes]
- DECISIONS: [choices, e.g. "volume window → 10 bars"]

## CURRENT STATE
- Working now: [...]
- Broken/half-finished: [...]

## NEXT STEP (per PLAN/ROADMAP)
- [single next action]

## OPEN LOOPS
- [anything unverified or blocking, e.g. "RSI not confirmed vs TradingView"]
```

## Step 5 — Log to HANDOFF.md (do this automatically)
Prepend to HANDOFF.md:
```
---
## [date/time] — HANDOFF
LAST_COMMIT: <current HEAD hash>
SNAPSHOT: [one-line strategy state]
NEXT: [next step]
---
```

## Step 6 — Also log decisions coming BACK from chat
When the user pastes a chat-drafted prompt for you to execute, after finishing,
prepend to HANDOFF.md:
```
---
## [date/time] — EXECUTED (from chat)
DID: [what you changed]
LAST_COMMIT: <new HEAD hash>
---
```

## Rules
- Output the paste block and nothing else the user must edit.
- Facts only — no advice, no analyst prompt.
- Translate code → plain trading/strategy language. Never dump raw diffs.
- HANDOFF.md is append-only, newest on top. You read and write it yourself; the user never touches it.
