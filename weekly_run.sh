#!/bin/bash
set -e
REPO=/Users/kumaresaperumal/Ideas/brand-listener
cd "$REPO"

# Run with venv python (has all dependencies)
"$REPO/venv/bin/python3" main.py --schedule --run-now >> "$REPO/reports/cron.log" 2>&1

# Only commit/push if there are non-ignored changes (reports/ is gitignored)
if ! git diff --quiet HEAD || git status --porcelain | grep -qv "^??"; then
    git add -A
    git commit -m "chore: weekly auto-run $(date +%Y-%m-%d) Week $(date +%V)" || true
    git push
fi
