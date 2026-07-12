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

# EV sales (IEA Global EV Outlook data, mirrored by Our World in Data —
# stable public CSV; the IEA API itself is gated). Schema:
# Entity, Code, Year, Electric cars sold
IEA_EV_URL = "https://ourworldindata.org/grapher/electric-car-sales.csv"


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
    df = _load("iea_ev")  # OWID mirror: Entity, Code, Year, Electric cars sold
    value_c = "Electric cars sold"
    latest = int(df["Year"].max())
    recent = df[df["Year"] >= latest - 5]
    keep = ["World", "China", "Europe", "United States", "India"]
    pivot = (recent[recent["Entity"].isin(keep)]
             .pivot_table(index="Year", columns="Entity", values=value_c, aggfunc="sum"))
    rows = [dict({"Year": int(y)}, **{c: f"{v:,.0f}" for c, v in r.items() if pd.notna(v)})
            for y, r in pivot.iterrows()]
    yoy = pivot["World"].pct_change().iloc[-1] * 100 if "World" in pivot else 0
    body = (f"World EV sales {latest}: **{pivot['World'].iloc[-1]:,.0f}** "
            f"({yoy:+.0f}% YoY)\n\n" + md_table(rows))
    return {"md": report("EV sales by region (IEA via OWID)", body,
                         "IEA Global EV Outlook, mirrored by Our World in Data"),
            "data": rows}


COMMANDS = {"refresh": refresh, "production": production, "sales": sales, "evs": evs}
