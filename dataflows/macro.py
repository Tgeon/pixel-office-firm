"""David's macro source: FRED automotive & economy series."""

from __future__ import annotations

from ._core import TTL, env_key, get_json, md_table, report

BASE = "https://api.stlouisfed.org/fred"

# Curated automotive/economy dashboard (see docs/data-source-catalog.md)
SERIES = {
    "TOTALSA": "Total US vehicle sales (SAAR, M units)",
    "ALTSALES": "Light vehicle sales: autos + light trucks (SAAR)",
    "DAUPSA": "Domestic auto production (units, SA)",
    "AUINSA": "Domestic auto inventories",
    "AISRSA": "Auto inventory/sales ratio",
    "UMCSENT": "Consumer sentiment (U. Michigan)",
    "FEDFUNDS": "Federal funds rate (%)",
    "T10Y2Y": "10y-2y treasury spread (%)",
    "CUSR0000SETA01": "CPI: new vehicles (index)",
}


def _observations(series_id: str, limit: int = 30) -> list[dict]:
    d = get_json(
        f"{BASE}/series/observations",
        TTL["news"],
        params={
            "series_id": series_id,
            "api_key": env_key("FRED_API_KEY"),
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        },
    )
    obs = [o for o in d.get("observations", []) if o.get("value") not in (".", None)]
    return obs


def snapshot(a) -> dict:
    rows, data = [], {}
    for sid, label in SERIES.items():
        try:
            obs = _observations(sid, limit=14)
            latest, year_ago = obs[0], (obs[12] if len(obs) > 12 else obs[-1])
            cur, prev = float(latest["value"]), float(year_ago["value"])
            yoy = (cur / prev - 1) * 100 if prev else 0.0
            rows.append({"Series": label, "Latest": cur, "Date": latest["date"],
                         "YoY %": f"{yoy:+.1f}"})
            data[sid] = {"latest": cur, "date": latest["date"], "yoy_pct": yoy}
        except Exception as e:  # noqa: BLE001 — skip failed series, note the gap
            rows.append({"Series": label, "Latest": "error", "Date": "-", "YoY %": str(e)[:40]})
    return {"md": report("US macro & automotive snapshot", md_table(rows), "FRED"),
            "data": data}


def series(a) -> dict:
    sid = (a.series or a.ticker or "TOTALSA").upper()
    obs = _observations(sid, limit=24)
    rows = [{"Date": o["date"], "Value": float(o["value"])} for o in obs]
    label = SERIES.get(sid, sid)
    return {"md": report(f"FRED series {sid} — {label}", md_table(rows), "FRED"),
            "data": rows}


COMMANDS = {"snapshot": snapshot, "series": series}
