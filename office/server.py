"""Pixel Office Firm — localhost trading floor.

    uv run uvicorn office.server:app --port 8787
    → http://localhost:8787

Serves the canvas floor, streams agent telemetry (SSE), launches analysis
runs headlessly via `claude -p "/analyze <TICKER>"` (Agent SDK credit),
and exposes ticker-tape + verdict data.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dataflows._core import UNIVERSE  # noqa: E402

EVENTS = ROOT / "data" / "events.jsonl"
REPORTS = ROOT / "reports"
ALLOWED_TOOLS = ("Task,Read,Write,Edit,Glob,Grep,"
                 "Bash(uv run*),Bash(mkdir*),Bash(ls*),Bash(cat*),Bash(date*)")

app = FastAPI(title="pixel-office-firm")
_run: dict = {"proc": None, "ticker": None, "started": None}


@app.get("/")
def index():
    return FileResponse(ROOT / "office" / "static" / "index.html")


@app.get("/api/config")
def config():
    return {"tickers": {t: u["short"] for t, u in UNIVERSE.items()},
            "agents": ["tom", "john", "david", "amy", "baldy", "hairy", "theo"]}


def _spawn(prompt: str, label: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["claude", "-p", prompt, "--permission-mode", "acceptEdits",
         "--allowedTools", ALLOWED_TOOLS],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


@app.post("/api/analyze/{ticker}")
def analyze(ticker: str):
    t = ticker.upper()
    if t not in UNIVERSE:
        return JSONResponse({"error": f"unknown ticker {t}"}, status_code=400)
    if _run["proc"] and _run["proc"].poll() is None:
        return JSONResponse({"error": f"run already in progress ({_run['ticker']})"},
                            status_code=409)
    _log("floor", "run_start", f"Client requested analysis of {t}", t)
    proc = _spawn(f"/analyze {t}", t)
    _run.update(proc=proc, ticker=t, started=time.time())
    threading.Thread(target=_watch, args=(proc, t), daemon=True).start()
    return {"ok": True, "ticker": t}


@app.post("/api/digest")
def run_digest():
    if _run["proc"] and _run["proc"].poll() is None:
        return JSONResponse({"error": f"run already in progress ({_run['ticker']})"},
                            status_code=409)
    _log("floor", "run_start", "Theo is preparing the morning digest", "DIGEST")
    proc = _spawn("/digest", "DIGEST")
    _run.update(proc=proc, ticker="DIGEST", started=time.time())
    threading.Thread(target=_watch, args=(proc, "DIGEST"), daemon=True).start()
    return {"ok": True}


@app.get("/api/digest")
def latest_digest():
    d = ROOT / "digest"
    files = sorted(d.glob("2*.md")) if d.exists() else []
    if not files:
        return JSONResponse({"error": "no digest yet"}, status_code=404)
    f = files[-1]
    return {"date": f.stem, "markdown": f.read_text()}


@app.get("/api/scoreboard")
def scoreboard():
    from scripts.digest_data import latest_verdict, price_moves
    try:
        moves = price_moves()
    except Exception:  # noqa: BLE001
        moves = {}
    out = {}
    for t, u in UNIVERSE.items():
        out[t] = {"name": u["short"], "pct": (moves.get(t) or {}).get("pct"),
                  "verdict": latest_verdict(t)}
    return out


MACRO_STRIP = {"TOTALSA": "VEHICLE SALES (SAAR M)", "FEDFUNDS": "FED FUNDS %",
               "AISRSA": "INV/SALES RATIO", "UMCSENT": "CONSUMER SENTIMENT"}


@app.get("/api/macro")
def macro_strip():
    from dataflows.macro import _observations
    out = {}
    for sid, label in MACRO_STRIP.items():
        try:
            obs = _observations(sid, limit=13)[::-1]  # oldest→newest
            out[sid] = {"label": label, "latest": float(obs[-1]["value"]),
                        "date": obs[-1]["date"],
                        "series": [float(o["value"]) for o in obs]}
        except Exception as e:  # noqa: BLE001
            out[sid] = {"label": label, "error": str(e)[:60]}
    return out


def _watch(proc: subprocess.Popen, ticker: str) -> None:
    code = proc.wait()
    _log("floor", "run_done" if code == 0 else "error",
         f"Run finished (exit {code})", ticker)


def _log(agent: str, state: str, note: str, ticker: str | None) -> None:
    EVENTS.parent.mkdir(exist_ok=True)
    with EVENTS.open("a") as f:
        f.write(json.dumps({"ts": time.time(), "agent": agent, "state": state,
                            "note": note, "ticker": ticker}) + "\n")


@app.get("/api/events")
async def events():
    async def stream():
        pos = EVENTS.stat().st_size if EVENTS.exists() else 0
        # replay last 30 lines so a fresh page shows current state
        if EVENTS.exists():
            for line in EVENTS.read_text().splitlines()[-30:]:
                yield f"data: {line}\n\n"
        while True:
            if EVENTS.exists():
                size = EVENTS.stat().st_size
                if size > pos:
                    with EVENTS.open() as f:
                        f.seek(pos)
                        for line in f.read().splitlines():
                            if line.strip():
                                yield f"data: {line}\n\n"
                    pos = size
                elif size < pos:
                    pos = 0
            yield ": ping\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/tape")
def tape():
    from scripts.digest_data import price_moves
    try:
        moves = price_moves()
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)[:100]}, status_code=502)
    return {t: {"name": UNIVERSE[t]["short"], **m} for t, m in moves.items()}


@app.get("/api/verdict/{ticker}")
def verdict(ticker: str):
    d = REPORTS / ticker.upper()
    best = None
    if d.exists():
        for f in d.glob("*-verdict.md"):
            m = re.match(r"(\d{4}-\d{2}-\d{2})-verdict", f.name)
            if m and (best is None or m.group(1) > best[0]):
                best = (m.group(1), f)
    if not best:
        return JSONResponse({"error": "no verdict yet"}, status_code=404)
    text = best[1].read_text()
    fm = {}
    for k in ("stance", "confidence", "financial_outlook", "engineering_health",
              "horizon_months"):
        m = re.search(rf"^{k}:\s*(\S+)", text, re.MULTILINE)
        fm[k] = m.group(1) if m else None
    findings = re.findall(r'^\s+-\s+"?(.+?)"?\s*$', text.split("sources:")[0]
                          .split("key_findings:")[-1], re.MULTILINE)
    return {"date": best[0], "path": str(best[1].relative_to(ROOT)),
            **fm, "key_findings": findings[:4]}
