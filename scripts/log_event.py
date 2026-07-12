"""Office telemetry: agents log what they're doing so the pixel floor can
animate them. Appends one JSON line to data/events.jsonl.

    uv run python scripts/log_event.py <agent> <state> "<note>" [TICKER]

states: start | work | write | done | error | run_start | run_done
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

EVENTS = Path(__file__).resolve().parent.parent / "data" / "events.jsonl"


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    EVENTS.parent.mkdir(exist_ok=True)
    with EVENTS.open("a") as f:
        f.write(json.dumps({
            "ts": time.time(),
            "agent": sys.argv[1].lower(),
            "state": sys.argv[2].lower(),
            "note": sys.argv[3][:140],
            "ticker": (sys.argv[4].upper() if len(sys.argv) > 4 else None),
        }) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
