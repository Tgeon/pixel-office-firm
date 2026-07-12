"""Shared infrastructure for all dataflows: env, cache, universe, helpers.

Agents never import this directly — they use the CLI:
    uv run python -m dataflows <module> <command> [ticker] [options]
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
STATIC_DIR = DATA_DIR / "static"
CACHE_DB = DATA_DIR / "cache.db"

load_dotenv(REPO_ROOT / ".env")

USER_AGENT = "pixel-office-firm/0.1 (personal research; contact: " + os.getenv("EDGAR_IDENTITY", "unknown") + ")"

# TTLs in seconds, per data class (see docs/pre-build-decisions.md 2.3)
TTL = {
    "quote": 15 * 60,
    "news": 6 * 3600,
    "fundamentals": 7 * 24 * 3600,
    "static": 30 * 24 * 3600,
}

# ---------------------------------------------------------------- universe

# v1 ticker universe (decision 2.1). makes = NHTSA make names.
UNIVERSE: dict[str, dict] = {
    "TSLA": {"name": "Tesla, Inc.", "short": "Tesla", "makes": ["TESLA"],
             "subs": ["teslamotors", "electricvehicles"]},
    "TM":   {"name": "Toyota Motor Corporation", "short": "Toyota", "makes": ["TOYOTA", "LEXUS"],
             "subs": ["Toyota", "cars"]},
    "F":    {"name": "Ford Motor Company", "short": "Ford", "makes": ["FORD", "LINCOLN"],
             "subs": ["Ford", "cars"]},
    "GM":   {"name": "General Motors Company", "short": "GM", "makes": ["CHEVROLET", "GMC", "CADILLAC", "BUICK"],
             "subs": ["Chevy", "cars"]},
    "STLA": {"name": "Stellantis N.V.", "short": "Stellantis", "makes": ["JEEP", "RAM", "DODGE", "CHRYSLER"],
             "subs": ["Jeep", "cars"]},
    "HMC":  {"name": "Honda Motor Co., Ltd.", "short": "Honda", "makes": ["HONDA", "ACURA"],
             "subs": ["Honda", "cars"]},
    "RIVN": {"name": "Rivian Automotive, Inc.", "short": "Rivian", "makes": ["RIVIAN"],
             "subs": ["Rivian", "electricvehicles"]},
    "LCID": {"name": "Lucid Group, Inc.", "short": "Lucid", "makes": ["LUCID"],
             "subs": ["lucidmotors", "electricvehicles"]},
    "NIO":  {"name": "NIO Inc.", "short": "NIO", "makes": ["NIO"],
             "subs": ["Nio", "electricvehicles"]},
    "XPEV": {"name": "XPeng Inc.", "short": "XPeng", "makes": ["XPENG"],
             "subs": ["XPeng", "electricvehicles"]},
    "LI":   {"name": "Li Auto Inc.", "short": "Li Auto", "makes": ["LI AUTO"],
             "subs": ["electricvehicles", "CarsIndia"]},
    "PSNY": {"name": "Polestar Automotive Holding UK PLC", "short": "Polestar", "makes": ["POLESTAR"],
             "subs": ["Polestar", "electricvehicles"]},
}

INVESTOR_SUBS = ["stocks", "investing", "wallstreetbets"]


def company(ticker: str) -> dict:
    t = ticker.upper()
    if t not in UNIVERSE:
        raise SystemExit(
            f"Unknown ticker {t!r}. v1 universe: {', '.join(UNIVERSE)}"
        )
    return UNIVERSE[t]


# ---------------------------------------------------------------- cache

def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(CACHE_DB, timeout=15)  # tolerate concurrent server threads
    conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, ts REAL, payload TEXT)")
    return conn


def cached(key: str, ttl: int, fetch):
    """Return fetch() result, cached as JSON under key for ttl seconds."""
    k = hashlib.sha256(key.encode()).hexdigest()
    conn = _db()
    try:
        row = conn.execute("SELECT ts, payload FROM cache WHERE key=?", (k,)).fetchone()
        if row and (time.time() - row[0]) < ttl:
            return json.loads(row[1])
        value = fetch()
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, ts, payload) VALUES (?,?,?)",
            (k, time.time(), json.dumps(value)),
        )
        conn.commit()
        return value
    finally:
        conn.close()


def get_json(url: str, ttl: int, params: dict | None = None, headers: dict | None = None):
    """HTTP GET returning parsed JSON, cached."""
    full = url + ("?" + "&".join(f"{a}={b}" for a, b in sorted((params or {}).items())) if params else "")

    def fetch():
        h = {"User-Agent": USER_AGENT}
        h.update(headers or {})
        r = requests.get(url, params=params, headers=h, timeout=30)
        r.raise_for_status()
        return r.json()

    return cached(full, ttl, fetch)


def get_text(url: str, ttl: int, headers: dict | None = None) -> str:
    def fetch():
        h = {"User-Agent": USER_AGENT}
        h.update(headers or {})
        r = requests.get(url, headers=h, timeout=60)
        r.raise_for_status()
        return r.text

    return cached("text:" + url, ttl, fetch)


def env_key(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Missing {name} in .env — see .env.example")
    return v


# ---------------------------------------------------------------- markdown

def md_table(rows: list[dict], columns: list[str] | None = None, max_rows: int = 25) -> str:
    if not rows:
        return "_no data_"
    cols = columns or list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows[:max_rows]:
        out.append("| " + " | ".join(_fmt(r.get(c, "")) for c in cols) + " |")
    if len(rows) > max_rows:
        out.append(f"\n_...and {len(rows) - max_rows} more rows_")
    return "\n".join(out)


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v).replace("|", "/").replace("\n", " ")[:160]


def report(title: str, body: str, source: str) -> str:
    stamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    return f"## {title}\n\n{body}\n\n_Source: {source} · retrieved {stamp}_\n"
