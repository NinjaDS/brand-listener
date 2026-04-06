#!/bin/bash
cd /Users/kumaresaperumal/ideas/brand-listener
python3 main.py --schedule --run-now >> /Users/kumaresaperumal/ideas/brand-listener/reports/cron.log 2>&1
git add -A
git commit -m "chore: weekly auto-run $(date +%Y-%m-%d) Week $(date +%V)"
git push
