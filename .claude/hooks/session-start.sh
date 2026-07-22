#!/bin/bash
# SessionStart hook — Trader-Resp
#
# Removes the "which python has the deps?" fumbling that costs tokens at the
# start of every Claude Code on the web session. This project keeps its deps
# in a project-local .venv (gitignored) and imports its own packages
# (screener/, backtest/, scanner/) by path, so a fresh session otherwise
# hits "No module named pandas" / "No module named screener" before it can
# do anything. This hook guarantees both are set up before the session
# starts, and persists them for the whole session.
#
# Scope: web/remote only (gated on CLAUDE_CODE_REMOTE). Idempotent — safe to
# run every session; the .venv persists in cached container state so only
# the first run pays the install cost.
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment. Local runs
# manage their own environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# 1. Ensure the project virtualenv exists and has the pinned deps.
#    Creating the venv is the slow step and only happens once per container
#    (cached thereafter); the pip install is a fast no-op when satisfied.
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt

# 2. Persist for the whole session: put the venv on PATH so `python` and
#    `pytest` resolve to it without activation, and make the project's own
#    packages importable from anywhere (screener/, backtest/, scanner/).
echo "export PATH=\"$CLAUDE_PROJECT_DIR/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
echo "export PYTHONPATH=\"$CLAUDE_PROJECT_DIR\"" >> "$CLAUDE_ENV_FILE"

echo "[session-start] venv ready; PATH + PYTHONPATH persisted. Run tests with: python -m pytest -q"
