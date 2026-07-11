"""Baldy & Hairy's knowledge base: industry production/sales (OICA) and
EV adoption (IEA). Static datasets downloaded into data/static/, refreshed
monthly via `dataflows industry refresh`.
"""

from __future__ import annotations

import io

import pandas as pd

from ._core import STATIC_DIR, TTL, get_text, md_table, report

OICA_FILES = {
    "production": "https://raw.githubusercontent.com/jhelvy/oica/main/data-raw/production.csv",
    "sales_country": "https://raw.githubusercontent.com/jhelvy/oica/main/data-raw/sales_country.csv",
    "sales_region": "https://raw.githubusercontent.com/jhelvy/oica/main/data-raw/sales_region.csv",
}

# IEA Global EV Data Explorer public API (CSV). If this URL drifts, download
# manually from https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer
# and save as data/static/iea_ev.csv
IEA_EV_URL = "https://api.iea.org/evs?parameters=EV%20sales&category=Historical&mode=Cars&csv=true"


def _path(name: str):
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    return STATIC_DIR / f"{name}.csv"


def refresh(a) -> dict:
    results = []
    for name, url in OICA_FILES.items():
        try:
            text = get_text(url, TTL["static"])
            _path(name).write_text(text)
            results.append({"Dataset": name, "Status": f"OK ({len(text.splitlines()) - 1} rows)"})
        except Exception as e:  # noqa: BLE001
            results.append({"Dataset": name, "Status": f"FAILED: {e}"})
    try:
        text = get_text(IEA_EV_URL, TTL["static"])
        _path("iea_ev").write_text(text)
        results.append({"Dataset": "iea_ev", "Status": f"OK ({len(text.splitlines()) - 1} rows)"})
    except Exception as e:  # noqa: BLE001
        results.append({"Dataset": "iea_ev",
                        "Status": f"FAILED ({e}) — download manually, see module docstring"})
    return {"md": report("Static dataset refresh", md_table(results), "OICA / IEA"),
            "data": results}


def _load(name: str) -> pd.DataFrame:
    p = _path(name)
    if not p.exists():
        raise SystemExit(f"{p} missing — run: uv run python -m dataflows industry refresh")
    return pd.read_csv(p)


def production(a) -> dict:
    df = _load("production")
    latest = int(df["year"].max())
    recent = df[df["year"] >= latest - 4]
    world = recent.groupby("year")["n"].sum().reset_index()
    world_rows = [{"Year": int(r.year), "Units": int(r.n)} for r in world.itertuples()]
    top = (recent[recent["year"] == latest].groupby("country")["n"].sum()
           .sort_values(ascending=False).head(12).reset_index())
    top_rows = [{"Country": r.country, f"{latest} units": int(r.n)} for r in top.itertuples()]
    body = ("### World vehicle production\n\n" + md_table(world_rows)
            + f"\n\n### Top producing countries ({latest})\n\n" + md_table(top_rows))
    return {"md": report("Global vehicle production (OICA)", body, "OICA via jhelvy/oica"),
            "data": {"world": world_rows, "top_countries": top_rows}}


def sales(a) -> dict:
    df = _load("sales_region")
    latest = int(df["year"].max())
    recent = df[df["year"] >= latest - 4]
    pivot = recent.pivot_table(index="year", columns="region", values="n", aggfunc="sum")
    rows = [dict({"Year": int(y)}, **{c: int(v) for c, v in r.items() if pd.notna(v)})
            for y, r in pivot.iterrows()]
    return {"md": report("Vehicle sales by region (OICA)", md_table(rows), "OICA via jhelvy/oica"),
            "data": rows}


def evs(a) -> dict:
    df = _load("iea_ev")
    # IEA explorer CSV: region/parameter/mode/powertrain/year/value (names can drift)
    cols = {c.lower(): c for c in df.columns}
    region_c = cols.get("region", cols.get("region_country", list(df.columns)[0]))
    year_c, value_c = cols.get("year", "year"), cols.get("value", "value")
    latest = int(df[year_c].max())
    recent = df[df[year_c] >= latest - 4]
    pivot = recent.pivot_table(index=year_c, columns=region_c, values=value_c, aggfunc="sum")
    keep = [c for c in ("World", "China", "Europe", "USA") if c in pivot.columns] or list(pivot.columns)[:5]
    rows = [dict({"Year": int(y)}, **{c: f"{v:,.0f}" for c, v in r[keep].items() if pd.notna(v)})
            for y, r in pivot.iterrows()]
    return {"md": report("EV sales by region (IEA)", md_table(rows), "IEA Global EV Data Explorer"),
            "data": rows}


COMMANDS = {"refresh": refresh, "production": production, "sales": sales, "evs": evs}
