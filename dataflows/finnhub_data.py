"""Finnhub free tier (60 calls/min): real-time quotes, company news,
insider sentiment, company profile. Shared by Tom (quotes) and John (insider).
"""

from __future__ import annotations

import time

from ._core import TTL, company, env_key, get_json, md_table, report

BASE = "https://finnhub.io/api/v1"


def _get(path: str, ttl: int, **params) -> dict | list:
    params["token"] = env_key("FINNHUB_API_KEY")
    return get_json(f"{BASE}/{path}", ttl, params=params)


def quote(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    q = _get("quote", TTL["quote"], symbol=t)
    change = q.get("dp") or 0.0
    body = (
        f"**{info['short']} ({t})** — **${q.get('c', 0):,.2f}** "
        f"({change:+.2f}% today)\n\n"
        f"- Open ${q.get('o', 0):,.2f} · High ${q.get('h', 0):,.2f} · "
        f"Low ${q.get('l', 0):,.2f} · Prev close ${q.get('pc', 0):,.2f}"
    )
    return {"md": report(f"{t} real-time quote", body, "Finnhub"), "data": q}


def news(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    to = time.strftime("%Y-%m-%d")
    frm = time.strftime("%Y-%m-%d", time.localtime(time.time() - a.days * 86400))
    items = _get("company-news", TTL["news"], symbol=t, **{"from": frm, "to": to}) or []
    rows = [
        {
            "Date": time.strftime("%m-%d", time.localtime(i.get("datetime", 0))),
            "Headline": i.get("headline", ""),
            "Source": i.get("source", ""),
        }
        for i in items[:20]
    ]
    body = f"{len(items)} stories in the last {a.days} days.\n\n" + md_table(rows)
    return {"md": report(f"{info['short']} ({t}) company news", body, "Finnhub"),
            "data": items[:20]}


def insider(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    frm = time.strftime("%Y-%m-%d", time.localtime(time.time() - 365 * 86400))
    d = _get("stock/insider-sentiment", TTL["fundamentals"], symbol=t, **{"from": frm,
             "to": time.strftime("%Y-%m-%d")})
    entries = (d or {}).get("data", [])
    rows = [
        {"Month": f"{e.get('year')}-{e.get('month'):02d}", "Net shares": e.get("change"),
         "MSPR": e.get("mspr")}
        for e in entries[-12:]
    ]
    note = ("MSPR ranges -100 (heavy selling) to +100 (heavy buying); "
            "sustained negatives often precede weakness.")
    body = (note + "\n\n" + md_table(rows)) if rows else "_no insider sentiment data_"
    return {"md": report(f"{info['short']} ({t}) insider sentiment (12mo)", body, "Finnhub"),
            "data": entries[-12:]}


def profile(a) -> dict:
    t = a.ticker.upper()
    p = _get("stock/profile2", TTL["fundamentals"], symbol=t) or {}
    m = (_get("stock/metric", TTL["fundamentals"], symbol=t, metric="all") or {}).get("metric", {})
    rows = [
        {"Field": "Name", "Value": p.get("name")},
        {"Field": "Market cap ($M)", "Value": p.get("marketCapitalization")},
        {"Field": "Shares out (M)", "Value": p.get("shareOutstanding")},
        {"Field": "IPO", "Value": p.get("ipo")},
        {"Field": "52w high", "Value": m.get("52WeekHigh")},
        {"Field": "52w low", "Value": m.get("52WeekLow")},
        {"Field": "P/E (ttm)", "Value": m.get("peTTM")},
        {"Field": "P/S (ttm)", "Value": m.get("psTTM")},
        {"Field": "Gross margin (ttm)", "Value": m.get("grossMarginTTM")},
        {"Field": "ROE (ttm)", "Value": m.get("roeTTM")},
    ]
    return {"md": report(f"{t} profile & key metrics", md_table(rows), "Finnhub"),
            "data": {"profile": p, "metrics": m}}


COMMANDS = {"quote": quote, "news": news, "insider": insider, "profile": profile}
