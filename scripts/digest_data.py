"""Gather everything the daily digest needs in one cheap pass.

    uv run python scripts/digest_data.py

Prints JSON: per-ticker price move, top headline, StockTwits mood, latest
verdict tier + age; plus a macro pair. The /digest command feeds this to Theo,
who writes digest/<date>.md (movers get paragraphs, the rest one-liners).
Zero Alpha Vantage/FMP usage; ~25 cached API calls total.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataflows._core import TTL, UNIVERSE, get_json  # noqa: E402
from dataflows import macro, news  # noqa: E402

REPORTS = Path(__file__).resolve().parent.parent / "reports"


def price_moves() -> dict[str, dict]:
    import yfinance as yf
    df = yf.download(list(UNIVERSE), period="5d", interval="1d",
                     auto_adjust=True, progress=False)["Close"]
    out = {}
    for t in UNIVERSE:
        try:
            s = df[t].dropna()
            out[t] = {"close": round(float(s.iloc[-1]), 2),
                      "pct": round(float(s.iloc[-1] / s.iloc[-2] - 1) * 100, 2)}
        except Exception as e:  # noqa: BLE001
            out[t] = {"close": None, "pct": None, "error": str(e)[:60]}
    return out


def top_headline(ticker: str) -> str:
    try:
        items = news._fetch(UNIVERSE[ticker]["name"], days=1)
        return items[0]["Headline"] if items else ""
    except Exception:  # noqa: BLE001
        return ""


def stocktwits_mood(ticker: str) -> str:
    try:
        d = get_json(f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json",
                     TTL["quote"])
        msgs = d.get("messages", [])
        bull = sum(1 for m in msgs if ((m.get("entities") or {}).get("sentiment") or {})
                   .get("basic") == "Bullish")
        bear = sum(1 for m in msgs if ((m.get("entities") or {}).get("sentiment") or {})
                   .get("basic") == "Bearish")
        if bull + bear == 0:
            return "→"
        return "↑" if bull > bear * 1.5 else "↓" if bear > bull * 1.5 else "→"
    except Exception:  # noqa: BLE001
        return "?"


def latest_verdict(ticker: str) -> dict | None:
    d = REPORTS / ticker
    if not d.exists():
        return None
    best = None
    for f in d.glob("*-verdict.md"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-verdict", f.name)
        if m and (best is None or m.group(1) > best[0]):
            stance = re.search(r"^stance:\s*(\S+)", f.read_text(), re.MULTILINE)
            best = (m.group(1), stance.group(1) if stance else "?")
    if not best:
        return None
    age = (datetime.date.today() - datetime.date.fromisoformat(best[0])).days
    return {"tier": best[1], "age_days": age}


def main() -> int:
    moves = price_moves()
    tickers = {}
    for t in UNIVERSE:
        tickers[t] = {
            "name": UNIVERSE[t]["short"],
            **moves.get(t, {}),
            "headline": top_headline(t),
            "social": stocktwits_mood(t),
            "verdict": latest_verdict(t),
        }
    ranked = sorted((t for t in tickers if tickers[t].get("pct") is not None),
                    key=lambda t: -abs(tickers[t]["pct"]))
    macro_pair = {}
    for sid in ("TOTALSA", "FEDFUNDS"):
        try:
            obs = macro._observations(sid, limit=2)
            macro_pair[sid] = {"value": float(obs[0]["value"]), "date": obs[0]["date"]}
        except Exception as e:  # noqa: BLE001
            macro_pair[sid] = {"error": str(e)[:60]}
    print(json.dumps({
        "date": str(datetime.date.today()),
        "movers": ranked[:3],
        "tickers": tickers,
        "macro": macro_pair,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
