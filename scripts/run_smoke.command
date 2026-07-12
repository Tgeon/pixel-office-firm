#!/bin/zsh
# Double-clickable smoke test runner. Writes results to data/smoke_output.txt
# so the Cowork session can read them. Safe to re-run anytime.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/.."
mkdir -p data
echo "smoke test started $(date)" > data/smoke_output.txt
uv run python scripts/smoke_test.py 2>&1 | tee -a data/smoke_output.txt
echo "smoke test finished $(date) exit=$?" >> data/smoke_output.txt
sleep 2
