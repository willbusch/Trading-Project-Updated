---
name: handoff-to-chat
description: Use this skill when the user asks to "handoff to chat," "sync to chat," "catch up chat," "session report," or "what changed" — any request to summarize everything done in the current Claude Code session so it can be pasted into Claude chat. Bridges the memory gap between Claude Code and Claude chat by scanning all changes since the last handoff, producing a structured report, and logging it so the next handoff has an anchor point.
---

# Handoff To Chat

Bridge Code to Chat. Chat has NO memory of this session. Produce a report the user pastes into chat so it knows exactly what changed and why.

## Step 1 — Find the anchor
- Read HANDOFF.md (repo root). The top entry has a LAST_COMMIT: <hash> line = the last handoff point.
- If HANDOFF.md doesn't exist, create it and diff the last 20 commits instead.

## Step 2 — Scan everything since the anchor
- git log --oneline <anchor>..HEAD — commits since last handoff
- git diff --stat <anchor>..HEAD — files touched
- git diff <anchor>..HEAD — READ actual changes, understand intent
- git status + git diff — uncommitted/half-finished work
- Read PLAN.md / ROADMAP.md / STRATEGY.md to map changes against the plan

## Step 3 — Write the report (fill every section)

# HANDOFF TO CHAT — [date/time]

## TL;DR (3 lines max)
What got done this session, plain English.

## MAJOR CHANGES
- [file]: what changed + WHY it matters to the strategy/project

## MINOR CHANGES
- [file]: small edits, config tweaks, fixes

## CURRENT STATE
- What works now that didn't before
- What's broken or half-finished
- New files/folders added

## DECISIONS MADE
- Choices chat should know (e.g. "switched volume window to 10 bars")

## NEXT STEP
- Single next action, per ROADMAP.md

## OPEN QUESTIONS FOR CHAT
- Anything needing strategy-level input

## Step 4 — Log it (this is the anchor for next time)
Prepend to HANDOFF.md:

---
## [date/time]
LAST_COMMIT: <current HEAD hash>
[paste the TL;DR + NEXT STEP here]
---

## Rules
- Translate code to plain trading/strategy language. Chat cares about WHY, not syntax.
- Never dump raw diffs. Summarize intent.
- Empty section → write "None."
- Report under ~400 words so it pastes cleanly.
- HANDOFF.md is append-only history; newest on top.
