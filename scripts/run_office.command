#!/bin/zsh
# Launch the pixel trading floor at http://localhost:8787
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/.."
( sleep 2 && open "http://localhost:8787" ) &
uv run uvicorn office.server:app --port 8787 --reload --timeout-graceful-shutdown 3
