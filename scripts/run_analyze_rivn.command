#!/bin/zsh
# One-shot: run the firm's full /analyze pipeline on RIVN headlessly.
# Logs to data/analyze_rivn.log so the Cowork session can follow along.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/.."
mkdir -p data
echo "analyze RIVN started $(date)" > data/analyze_rivn.log
claude -p "/analyze RIVN" \
  --permission-mode acceptEdits \
  --allowedTools "Task,Read,Write,Edit,Glob,Grep,Bash(uv run*),Bash(mkdir*),Bash(ls*),Bash(cat*),Bash(date*)" \
  2>&1 | tee -a data/analyze_rivn.log
echo "analyze RIVN finished $(date) exit=$?" >> data/analyze_rivn.log
sleep 2
