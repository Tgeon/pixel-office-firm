"""Unified dataflows CLI (decision: one entry point for all agents).

Usage:
    uv run python -m dataflows <module> <command> [ticker] [--json] [--days N]
                                                  [--period P] [--series ID]
                                                  [--query Q] [--years N]
                                                  [--agent NAME]

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
--agent NAME enables office telemetry: the pixel floor sees every command
you run and key data payloads (charts, headlines, sentiment) render on the
office wall screens automatically.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

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

EVENTS = Path(__file__).resolve().parent.parent / "data" / "events.jsonl"


def _emit(agent: str, state: str, note: str, ticker: str | None, payload=None):
    EVENTS.parent.mkdir(exist_ok=True)
    e = {"ts": time.time(), "agent": agent, "state": state,
         "note": note[:140], "ticker": ticker}
    if payload is not None:
        e["payload"] = payload
    with EVENTS.open("a") as f:
        f.write(json.dumps(e) + "\n")


def _payload(module: str, command: str, data) -> tuple[str, object] | None:
    """Distill a command's data into a small wall-screen payload."""
    try:
        if module == "prices" and command == "history":
            return "chart", {"closes": data.get("closes", [])[-90:],
                             "rsi": data.get("rsi14")}
        if module == "finnhub" and command == "quote":
            return "quote", {"c": data.get("c"), "dp": data.get("dp")}
        if module == "news" or (module == "finnhub" and command == "news"):
            items = data if isinstance(data, list) else []
            heads = [i.get("Headline") or i.get("headline") or "" for i in items[:6]]
            return "headlines", [h[:90] for h in heads if h]
        if module == "social":
            d = data if isinstance(data, dict) else {}
            r = d.get("reddit", d)
            st = d.get("stocktwits", {})
            return "sentiment", {"pos": r.get("pos", 0), "neg": r.get("neg", 0),
                                 "neu": r.get("neu", 0),
                                 "bull": st.get("bullish", 0), "bear": st.get("bearish", 0)}
        if module == "recalls" and command == "recalls":
            return "recalls", {"count": data.get("count", 0),
                               "by_year": data.get("by_year", {})}
    except Exception:  # noqa: BLE001 — telemetry must never break the data path
        pass
    return None


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
    p.add_argument("--agent", default=None)
    a = p.parse_args(argv)

    mod = importlib.import_module(MODULES[a.module])
    commands = getattr(mod, "COMMANDS")
    if a.command not in commands:
        p.error(f"unknown command {a.command!r} for {a.module}; "
                f"choose from: {', '.join(sorted(commands))}")

    tick = a.ticker.upper() if a.ticker else None
    if a.agent:
        _emit(a.agent, "work", f"$ {a.module} {a.command}"
              + (f" {tick}" if tick else ""), tick)
    t0 = time.time()
    try:
        result = commands[a.command](a)  # -> {"md": str, "data": Any}
    except BaseException as e:
        if a.agent:
            _emit(a.agent, "error", f"{a.module} {a.command} failed: {e}", tick)
        raise
    if a.agent:
        pl = _payload(a.module, a.command, result.get("data"))
        if pl:
            _emit(a.agent, "data", f"{a.module} {a.command} ({time.time()-t0:.0f}s)",
                  tick, payload={"kind": pl[0], "value": pl[1]})
    print(json.dumps(result["data"], indent=2, default=str) if a.as_json else result["md"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
