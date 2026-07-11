"""Unified dataflows CLI (decision: one entry point for all agents).

Usage:
    uv run python -m dataflows <module> <command> [ticker] [--json] [--days N]
                                                  [--period P] [--series ID]
                                                  [--query Q] [--years N]

Modules & commands:
    prices    history|fundamentals|analyst  TICKER   [--period 6mo]
    finnhub   quote|news|insider|profile    TICKER   [--days 7]
    macro     snapshot | series --series TOTALSA
    filings   financials|insider           TICKER
    news      company TICKER [--days 7] | topic --query "..." | sector
    social    reddit|stocktwits|pulse      TICKER
    recalls   recalls|complaints           TICKER   [--years 3]
    industry  refresh | production | sales | evs

Output is markdown (for agent context). Add --json for raw data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys

MODULES = {
    "prices": "dataflows.prices",
    "finnhub": "dataflows.finnhub_data",
    "macro": "dataflows.macro",
    "filings": "dataflows.filings",
    "news": "dataflows.news",
    "social": "dataflows.social",
    "recalls": "dataflows.recalls",
    "industry": "dataflows.industry",
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dataflows", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("module", choices=sorted(MODULES))
    p.add_argument("command")
    p.add_argument("ticker", nargs="?", default=None)
    p.add_argument("--json", action="store_true", dest="as_json")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--years", type=int, default=3)
    p.add_argument("--period", default="6mo")
    p.add_argument("--series", default=None)
    p.add_argument("--query", default=None)
    a = p.parse_args(argv)

    mod = importlib.import_module(MODULES[a.module])
    commands = getattr(mod, "COMMANDS")
    if a.command not in commands:
        p.error(f"unknown command {a.command!r} for {a.module}; "
                f"choose from: {', '.join(sorted(commands))}")

    result = commands[a.command](a)  # -> {"md": str, "data": Any}
    print(json.dumps(result["data"], indent=2, default=str) if a.as_json else result["md"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
