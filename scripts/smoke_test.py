"""Live smoke test — exercises every dataflow against real APIs.

Run on your machine (needs .env keys + internet):

    uv run python scripts/smoke_test.py

Paste the full output back to Claude for one-round fixes.
"""

from __future__ import annotations

import subprocess
import sys
import time

CASES = [
    ("prices", ["prices", "history", "TSLA", "--period", "3mo"]),
    ("prices-fund", ["prices", "fundamentals", "RIVN"]),
    ("prices-analyst", ["prices", "analyst", "F"]),
    ("finnhub-quote", ["finnhub", "quote", "TSLA"]),
    ("finnhub-news", ["finnhub", "news", "GM", "--days", "5"]),
    ("finnhub-insider", ["finnhub", "insider", "TSLA"]),
    ("macro-snapshot", ["macro", "snapshot"]),
    ("macro-series", ["macro", "series", "--series", "TOTALSA"]),
    ("filings-financials", ["filings", "financials", "TSLA"]),
    ("filings-insider", ["filings", "insider", "RIVN"]),
    ("news-company", ["news", "company", "LCID"]),
    ("news-sector", ["news", "sector"]),
    ("social-reddit", ["social", "reddit", "TSLA"]),
    ("social-stocktwits", ["social", "stocktwits", "NIO"]),
    ("industry-refresh", ["industry", "refresh"]),
    ("industry-production", ["industry", "production"]),
    ("industry-sales", ["industry", "sales"]),
    ("industry-evs", ["industry", "evs"]),
    ("recalls", ["recalls", "recalls", "RIVN", "--years", "2"]),
    ("recalls-complaints", ["recalls", "complaints", "LCID", "--years", "2"]),
    ("finnhub-profile", ["finnhub", "profile", "XPEV"]),
    ("news-topic", ["news", "topic", "--query", "EV battery supply chain"]),
    ("social-pulse", ["social", "pulse", "RIVN"]),
]

def main() -> int:
    failures = 0
    for name, argv in CASES:
        t0 = time.time()
        p = subprocess.run([sys.executable, "-m", "dataflows", *argv],
                           capture_output=True, text=True, timeout=300)
        dur = time.time() - t0
        ok = p.returncode == 0 and len(p.stdout.strip()) > 50
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{status}] {name:<20} ({dur:5.1f}s)")
        if not ok:
            print("  stdout:", (p.stdout or "").strip()[:400])
            print("  stderr:", (p.stderr or "").strip()[-600:])
        else:
            first = next((ln for ln in p.stdout.splitlines() if ln.strip()), "")
            print(f"   {first[:100]}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
