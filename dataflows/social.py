"""Amy's sentiment stack.

Reddit: PRAW when credentials exist in .env (pending Data API approval),
otherwise public subreddit RSS via feedparser. StockTwits: public symbol
stream with user-tagged bullish/bearish labels. Scoring: VADER, local.
"""

from __future__ import annotations

import os

from ._core import (INVESTOR_SUBS, TTL, USER_AGENT, company, get_json,
                    get_text, md_table, report)


def _vader():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    return SentimentIntensityAnalyzer()


def _score(texts: list[str]) -> dict:
    an = _vader()
    pos = neg = neu = 0
    scored = []
    for t in texts:
        c = an.polarity_scores(t)["compound"]
        scored.append((c, t))
        if c >= 0.05:
            pos += 1
        elif c <= -0.05:
            neg += 1
        else:
            neu += 1
    scored.sort(key=lambda x: x[0])
    return {"pos": pos, "neg": neg, "neu": neu, "total": len(texts),
            "most_negative": [t for _, t in scored[:3]],
            "most_positive": [t for _, t in scored[-3:]][::-1]}


def _praw_available() -> bool:
    return bool(os.getenv("REDDIT_CLIENT_ID", "").strip()
                and os.getenv("REDDIT_CLIENT_SECRET", "").strip())


def _reddit_titles_praw(subs: list[str], query: str, limit: int = 25) -> list[str]:
    import praw
    r = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.getenv("REDDIT_USER_AGENT", USER_AGENT),
    )
    titles = []
    for sub in subs:
        for post in r.subreddit(sub).search(query, time_filter="week", limit=limit):
            titles.append(post.title)
    return titles


def _reddit_titles_rss(subs: list[str], query: str) -> list[str]:
    """Fallback path: public subreddit RSS, filtered by query terms locally."""
    import feedparser
    terms = [w.lower() for w in query.split() if len(w) > 2]
    titles = []
    for sub in subs:
        try:
            xml = get_text(f"https://www.reddit.com/r/{sub}/.rss", TTL["news"],
                           headers={"User-Agent": os.getenv("REDDIT_USER_AGENT", USER_AGENT)})
            for e in feedparser.parse(xml).entries:
                title = e.get("title", "")
                if any(w in title.lower() for w in terms):
                    titles.append(f"[r/{sub}] {title}")
        except Exception:  # noqa: BLE001 — a blocked sub shouldn't kill the sweep
            continue
    return titles


def reddit(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    subs = info["subs"] + INVESTOR_SUBS
    query = f"{info['short']} {t}"
    if _praw_available():
        mode = "Reddit API (PRAW)"
        titles = _reddit_titles_praw(subs, info["short"])
    else:
        mode = "subreddit RSS fallback (Reddit API approval pending)"
        titles = _reddit_titles_rss(subs, f"{info['short']} {t} {info['name']}")
    s = _score(titles)
    body = (
        f"Mode: {mode} · subs: {', '.join('r/' + x for x in subs)} · query: `{query}`\n\n"
        f"**{s['total']} matching posts** — {s['pos']} positive / {s['neg']} negative / "
        f"{s['neu']} neutral (VADER)\n\n"
        f"Most positive:\n" + "\n".join(f"- {x}" for x in s["most_positive"] or ["_none_"]) +
        "\n\nMost negative:\n" + "\n".join(f"- {x}" for x in s["most_negative"] or ["_none_"])
    )
    return {"md": report(f"{info['short']} ({t}) Reddit sentiment", body, mode), "data": s}


def stocktwits(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    try:
        d = get_json(f"https://api.stocktwits.com/api/2/streams/symbol/{t}.json", TTL["quote"])
        msgs = d.get("messages", [])
    except Exception as e:  # noqa: BLE001
        return {"md": report(f"{t} StockTwits", f"_stream unavailable: {e}_", "StockTwits"),
                "data": {"error": str(e)}}
    bullish = bearish = untagged = 0
    texts = []
    for m in msgs:
        texts.append(m.get("body", ""))
        s = ((m.get("entities") or {}).get("sentiment") or {}).get("basic")
        if s == "Bullish":
            bullish += 1
        elif s == "Bearish":
            bearish += 1
        else:
            untagged += 1
    v = _score(texts)
    body = (
        f"Last {len(msgs)} messages — user-tagged: **{bullish} bullish / {bearish} bearish** "
        f"({untagged} untagged) · VADER: {v['pos']} pos / {v['neg']} neg / {v['neu']} neu\n\n"
        f"Sample negative:\n" + "\n".join(f"- {x[:140]}" for x in v["most_negative"] or ["_none_"])
    )
    return {"md": report(f"{info['short']} ({t}) StockTwits pulse", body, "StockTwits"),
            "data": {"bullish": bullish, "bearish": bearish, "vader": v}}


def pulse(a) -> dict:
    r = reddit(a)
    s = stocktwits(a)
    return {"md": r["md"] + "\n" + s["md"],
            "data": {"reddit": r["data"], "stocktwits": s["data"]}}


COMMANDS = {"reddit": reddit, "stocktwits": stocktwits, "pulse": pulse}
