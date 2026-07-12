"""Stage a believable mid-run telemetry sequence so the floor animates for
demos and screenshots — no LLM calls, no API cost, real event vocabulary.

    uv run python scripts/demo_events.py        # stage the show
    uv run python scripts/demo_events.py clear  # end the demo run cleanly
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

EVENTS = Path(__file__).resolve().parent.parent / "data" / "events.jsonl"
T = "GM"


def emit(ago: float, agent: str, state: str, note: str, payload=None):
    e = {"ts": time.time() - ago, "agent": agent, "state": state,
         "note": note, "ticker": T}
    if payload:
        e["payload"] = payload
    with EVENTS.open("a") as f:
        f.write(json.dumps(e) + "\n")


SHOW = [
    (40, "floor", "run_start", "Client requested analysis of GM"),
    (38, "floor", "work", "PREFETCH: warming 14 sources for GM"),
    (36, "tom", "start", "Charts up. Let's see GM's tape"),
    (35, "john", "start", "Pulling the filings. Trust, but verify"),
    (35, "david", "start", "Wires are hot — GM headlines incoming"),
    (34, "amy", "start", "Scanning r/Chevy and the twits"),
    (32, "tom", "work", "$ prices history GM"),
    (30, "tom", "data", "prices history (2s)", {"kind": "chart", "value": {
        "closes": [44.8, 45.1, 44.6, 45.9, 46.3, 46.0, 46.8, 47.4, 47.1, 47.9,
                   48.2, 47.6, 48.5, 49.1, 48.8, 49.6, 50.2, 49.8, 50.6, 51.1,
                   50.7, 51.4, 52.0, 51.6, 52.3], "rsi": 61}}),
    (28, "david", "data", "news company (1s)", {"kind": "headlines", "value": [
        "GM raises full-year guidance on truck demand",
        "Ultium cell output doubles quarter over quarter",
        "Dealers report tight full-size SUV inventory"]}),
    (26, "amy", "data", "social pulse (1s)", {"kind": "sentiment", "value":
        {"pos": 14, "neg": 6, "neu": 9, "bull": 22, "bear": 9}}),
    (24, "john", "find", "Net cash improved $1.1B QoQ; buyback pace steady"),
    (22, "tom", "find", "GM +2.3% today — riding above SMA50 since May"),
    (20, "john", "write", "Writing my report"),
    (18, "amy", "find", "Enthusiasts hyped on the new Bolt; investors cooler"),
    (15, "baldy", "start", "Time to build the bull case"),
    (15, "hairy", "start", "Someone has to check the brakes"),
    (12, "baldy", "work", "$ industry evs"),
    (10, "hairy", "find", "Warranty provisions up two quarters straight"),
    (8, "baldy", "find", "Ultium ramp is a margin inflection into 2027"),
    (6, "hairy", "work", "$ recalls complaints GM --years 2"),
    (4, "baldy", "write", "Writing my report"),
]


def main() -> int:
    EVENTS.parent.mkdir(exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        emit(0, "floor", "run_done", "Demo sequence complete")
        print("demo cleared")
        return 0
    for ago, agent, state, note, *pl in SHOW:
        emit(ago, agent, state, note, pl[0] if pl else None)
    print(f"staged {len(SHOW)} demo events — floor is live for ~40s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
