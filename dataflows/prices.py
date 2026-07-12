"""Tom's primary source: yfinance — price history, fundamentals, analyst views.

Technical indicators are computed locally with pandas (free, unlimited).
"""

from __future__ import annotations

import pandas as pd

from . import _core
from ._core import company, md_table, report


def _yf_ticker(symbol: str):
    import yfinance as yf  # deferred: slow import
    return yf.Ticker(symbol)


# ------------------------------------------------------------- indicators

def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.where(loss != 0)
    out = 100 - (100 / (1 + rs))
    return out.where(loss != 0, 100.0)  # zero losses in window → RSI 100


def macd(close: pd.Series):
    fast = close.ewm(span=12, adjust=False).mean()
    slow = close.ewm(span=26, adjust=False).mean()
    line = fast - slow
    signal = line.ewm(span=9, adjust=False).mean()
    return line, signal


# ------------------------------------------------------------- commands

def history(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    df = _yf_ticker(t).history(period=a.period, interval="1d", auto_adjust=True)
    if df.empty:
        return {"md": report(f"{t} price history", "_no price data returned_", "yfinance"),
                "data": {}}

    close = df["Close"]
    df["SMA20"] = close.rolling(20).mean()
    df["SMA50"] = close.rolling(50).mean()
    df["RSI14"] = rsi(close)
    macd_line, macd_sig = macd(close)

    last = df.iloc[-1]
    period_ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
    vol = close.pct_change().std() * (252 ** 0.5) * 100
    trend = "above" if last["Close"] > last["SMA50"] else "below"

    header = (
        f"**{info['short']} ({t})** — last close **${last['Close']:,.2f}** · "
        f"{a.period} return **{period_ret:+.1f}%** · annualized vol {vol:.0f}%\n\n"
        f"- RSI(14): {last['RSI14']:.0f} "
        f"({'overbought' if last['RSI14'] > 70 else 'oversold' if last['RSI14'] < 30 else 'neutral'})\n"
        f"- MACD: {macd_line.iloc[-1]:+.2f} vs signal {macd_sig.iloc[-1]:+.2f} "
        f"({'bullish' if macd_line.iloc[-1] > macd_sig.iloc[-1] else 'bearish'} crossover state)\n"
        f"- Price is {trend} the 50-day average "
        f"(SMA20 ${last['SMA20']:,.2f} / SMA50 ${last['SMA50']:,.2f})\n"
    )

    tail = df.tail(10).reset_index()
    tail["Date"] = tail["Date"].dt.strftime("%Y-%m-%d")
    rows = tail[["Date", "Open", "High", "Low", "Close", "Volume"]].to_dict("records")

    return {
        "md": report(f"{t} price history ({a.period})", header + "\n" + md_table(rows), "yfinance"),
        "data": {"last_close": float(last["Close"]), "period_return_pct": float(period_ret),
                 "rsi14": float(last["RSI14"]), "rows": rows,
                 "closes": [round(float(v), 2) for v in close.tail(90)]},
    }


def fundamentals(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    raw = _yf_ticker(t).info or {}
    fields = {
        "Market cap": raw.get("marketCap"),
        "Trailing P/E": raw.get("trailingPE"),
        "Forward P/E": raw.get("forwardPE"),
        "Price/Book": raw.get("priceToBook"),
        "EV/EBITDA": raw.get("enterpriseToEbitda"),
        "Profit margin": raw.get("profitMargins"),
        "Operating margin": raw.get("operatingMargins"),
        "Revenue (ttm)": raw.get("totalRevenue"),
        "Revenue growth": raw.get("revenueGrowth"),
        "Total debt": raw.get("totalDebt"),
        "Total cash": raw.get("totalCash"),
        "Free cash flow": raw.get("freeCashflow"),
        "Shares outstanding": raw.get("sharesOutstanding"),
        "Beta": raw.get("beta"),
    }
    rows = [{"Metric": k, "Value": v if v is not None else "n/a"} for k, v in fields.items()]
    return {
        "md": report(f"{info['short']} ({t}) fundamentals snapshot", md_table(rows), "yfinance"),
        "data": fields,
    }


def analyst(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    tk = _yf_ticker(t)
    parts, data = [], {}

    try:
        pt = tk.analyst_price_targets or {}
        data["price_targets"] = pt
        parts.append(
            f"Price targets — low ${pt.get('low')}, mean **${pt.get('mean')}**, "
            f"high ${pt.get('high')} (current ${pt.get('current')})"
        )
    except Exception as e:  # noqa: BLE001 — source gaps are expected, note and move on
        parts.append(f"_price targets unavailable: {e}_")

    try:
        recs = tk.recommendations
        if recs is not None and not recs.empty:
            rows = recs.head(4).to_dict("records")
            data["recommendations"] = rows
            parts.append("\nRecent recommendation mix (analyst counts):\n\n" + md_table(rows))
    except Exception as e:  # noqa: BLE001
        parts.append(f"_recommendations unavailable: {e}_")

    return {"md": report(f"{info['short']} ({t}) analyst consensus", "\n".join(parts), "yfinance"),
            "data": data}


COMMANDS = {"history": history, "fundamentals": fundamentals, "analyst": analyst}
