"""David's headline feed: Google News RSS (no key, near-real-time)."""

from __future__ import annotations

import urllib.parse

from ._core import TTL, USER_AGENT, company, get_text, md_table, report

BASE = "https://news.google.com/rss/search"


def _fetch(query: str, days: int) -> list[dict]:
    import feedparser  # deferred import
    q = urllib.parse.quote(f"{query} when:{days}d")
    url = f"{BASE}?q={q}&hl=en-US&gl=US&ceid=US:en"
    xml = get_text(url, TTL["news"], headers={"User-Agent": USER_AGENT})
    feed = feedparser.parse(xml)
    items = []
    for e in feed.entries[:25]:
        items.append({
            "Date": (e.get("published", "") or "")[:16],
            "Headline": e.get("title", ""),
            "Source": (e.get("source", {}) or {}).get("title", ""),
            "link": e.get("link", ""),
        })
    return items


def _render(title: str, query: str, days: int) -> dict:
    items = _fetch(query, days)
    rows = [{k: i[k] for k in ("Date", "Headline", "Source")} for i in items]
    body = f"Query: `{query}` (last {days} days) — {len(items)} headlines.\n\n" + md_table(rows)
    return {"md": report(title, body, "Google News RSS"), "data": items}


def company_news(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    return _render(f"{info['short']} ({t}) news headlines", info["name"], a.days)


def topic(a) -> dict:
    q = a.query or "automotive industry"
    return _render(f"News: {q}", q, a.days)


def sector(a) -> dict:
    q = "automotive industry OR electric vehicles market OR car sales"
    return _render("Automotive sector news", q, a.days)


COMMANDS = {"company": company_news, "topic": topic, "sector": sector}
