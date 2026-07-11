"""Mocked unit tests for the dataflows layer (no network required).

Live verification happens via scripts/smoke_test.py on a real machine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataflows import _core  # noqa: E402
from dataflows import finnhub_data, macro, news, prices, social  # noqa: E402


def args(**kw) -> argparse.Namespace:
    base = {"ticker": "TSLA", "as_json": False, "days": 7, "years": 3,
            "period": "6mo", "series": None, "query": None}
    base.update(kw)
    return argparse.Namespace(**base)


@pytest.fixture(autouse=True)
def temp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "CACHE_DB", tmp_path / "cache.db")
    monkeypatch.setattr(_core, "DATA_DIR", tmp_path)


# ---------------------------------------------------------------- core

def test_cache_roundtrip():
    calls = []

    def fetch():
        calls.append(1)
        return {"v": 42}

    assert _core.cached("k", 60, fetch) == {"v": 42}
    assert _core.cached("k", 60, fetch) == {"v": 42}
    assert len(calls) == 1  # second hit served from cache


def test_universe_rejects_unknown():
    with pytest.raises(SystemExit):
        _core.company("AAPL")


def test_md_table_escapes_pipes():
    out = _core.md_table([{"a": "x|y"}])
    assert "x/y" in out


# ---------------------------------------------------------------- indicators

def test_rsi_bounds():
    up = pd.Series(range(1, 40), dtype=float)
    val = prices.rsi(up).iloc[-1]
    assert 50 < val <= 100


def test_macd_crossover_sign():
    rising = pd.Series([1.0] * 30 + list(range(1, 30)))
    line, signal = prices.macd(rising)
    assert line.iloc[-1] > signal.iloc[-1]  # rising prices → bullish state


# ---------------------------------------------------------------- finnhub

def test_finnhub_quote_renders(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test")
    fake = {"c": 250.5, "dp": -1.2, "o": 255, "h": 256, "l": 249, "pc": 253.5}
    with mock.patch.object(finnhub_data, "get_json", return_value=fake):
        out = finnhub_data.quote(args())
    assert "$250.50" in out["md"] and "-1.20%" in out["md"]


def test_finnhub_insider_mspr(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test")
    fake = {"data": [{"year": 2026, "month": 5, "change": -1000, "mspr": -45.2}]}
    with mock.patch.object(finnhub_data, "get_json", return_value=fake):
        out = finnhub_data.insider(args())
    assert "2026-05" in out["md"] and "MSPR" in out["md"]


# ---------------------------------------------------------------- macro

def test_macro_series(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "test")
    fake = {"observations": [
        {"date": "2026-05-01", "value": "16.485"},
        {"date": "2026-04-01", "value": "16.395"},
    ]}
    with mock.patch.object(macro, "get_json", return_value=fake):
        out = macro.series(args(series="TOTALSA"))
    assert "16.49" in out["md"] or "16.485" in json.dumps(out["data"])


# ---------------------------------------------------------------- news

SAMPLE_RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Rivian ramps R2 production</title>
<pubDate>Fri, 10 Jul 2026 12:00:00 GMT</pubDate>
<source url="https://x.com">Example Wire</source>
<link>https://example.com/1</link></item>
</channel></rss>"""


def test_news_parses_rss():
    with mock.patch.object(news, "get_text", return_value=SAMPLE_RSS):
        out = news.company_news(args(ticker="RIVN"))
    assert "Rivian ramps R2 production" in out["md"]


# ---------------------------------------------------------------- social

def test_social_vader_scoring():
    s = social._score(["I love this stock, amazing growth",
                       "terrible quarter, awful management",
                       "the car is a car"])
    assert s["pos"] == 1 and s["neg"] == 1 and s["neu"] == 1


def test_social_reddit_rss_fallback(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    rss = SAMPLE_RSS.replace("Rivian ramps R2 production",
                             "Tesla FSD update impressions megathread")
    with mock.patch.object(social, "get_text", return_value=rss):
        out = social.reddit(args(ticker="TSLA"))
    assert "RSS fallback" in out["md"]
    assert "Tesla FSD" in out["md"]


def test_social_stocktwits_tags():
    fake = {"messages": [
        {"body": "to the moon", "entities": {"sentiment": {"basic": "Bullish"}}},
        {"body": "short it", "entities": {"sentiment": {"basic": "Bearish"}}},
        {"body": "meh", "entities": {"sentiment": None}},
    ]}
    with mock.patch.object(social, "get_json", return_value=fake):
        out = social.stocktwits(args())
    assert "1 bullish / 1 bearish" in out["md"]
