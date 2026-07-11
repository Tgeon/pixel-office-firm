"""Hairy's quality signal: NHTSA recalls & complaints (free, no key).

Quality problems often precede financial ones — recall counts and trends
per make are direct engineering-health evidence.
"""

from __future__ import annotations

import datetime

from ._core import TTL, company, get_json, md_table, report

BASE = "https://api.nhtsa.gov"


def _models_with_issues(make: str, year: int, issue_type: str) -> list[str]:
    d = get_json(f"{BASE}/products/vehicle/models", TTL["news"],
                 params={"modelYear": year, "make": make, "issueType": issue_type})
    return [r.get("model", "") for r in d.get("results", []) if r.get("model")]


def _recalls_for(make: str, model: str, year: int) -> list[dict]:
    d = get_json(f"{BASE}/recalls/recallsByVehicle", TTL["news"],
                 params={"make": make, "model": model, "modelYear": year})
    return d.get("results", [])


def recalls(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    this_year = datetime.date.today().year
    years = range(this_year - a.years + 1, this_year + 1)

    campaigns: dict[str, dict] = {}
    per_year: dict[int, int] = {}
    for make in info["makes"]:
        for y in years:
            try:
                for model in _models_with_issues(make, y, "r"):
                    for r in _recalls_for(make, model, y):
                        cid = r.get("NHTSACampaignNumber", f"{make}-{model}-{y}")
                        campaigns.setdefault(cid, {
                            "Campaign": cid,
                            "Date": r.get("ReportReceivedDate", ""),
                            "Make/Model": f"{make} {model}",
                            "Component": r.get("Component", ""),
                            "Summary": (r.get("Summary", "") or "")[:120],
                        })
                        per_year[y] = per_year.get(y, 0) + 0  # counted below
            except Exception:  # noqa: BLE001 — keep sweeping other make/years
                continue

    # count campaigns per model year mentioned
    for c in campaigns.values():
        y = (c["Date"] or "")[:4]
        if y.isdigit():
            per_year[int(y)] = per_year.get(int(y), 0) + 1

    trend = " · ".join(f"{y}: {per_year.get(y, 0)}" for y in sorted(per_year)) or "n/a"
    rows = sorted(campaigns.values(), key=lambda c: c["Date"], reverse=True)
    body = (
        f"Makes: {', '.join(info['makes'])} · model years {years.start}–{years.stop - 1}\n\n"
        f"**{len(campaigns)} unique recall campaigns** · campaigns by report year: {trend}\n\n"
        + md_table(rows, columns=["Date", "Make/Model", "Component", "Summary"], max_rows=15)
    )
    return {"md": report(f"{info['short']} ({t}) NHTSA recalls", body, "NHTSA"),
            "data": {"count": len(campaigns), "by_year": per_year,
                     "campaigns": rows[:15]}}


def complaints(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    this_year = datetime.date.today().year
    years = range(this_year - a.years + 1, this_year + 1)
    total = 0
    by_make: dict[str, int] = {}
    for make in info["makes"]:
        for y in years:
            try:
                for model in _models_with_issues(make, y, "c")[:8]:
                    d = get_json(f"{BASE}/complaints/complaintsByVehicle", TTL["news"],
                                 params={"make": make, "model": model, "modelYear": y})
                    n = d.get("count", len(d.get("results", [])))
                    by_make[make] = by_make.get(make, 0) + n
                    total += n
            except Exception:  # noqa: BLE001
                continue
    rows = [{"Make": m, "Complaints": n} for m, n in sorted(by_make.items(),
                                                            key=lambda x: -x[1])]
    body = (f"Model years {years.start}–{years.stop - 1} · total consumer complaints: "
            f"**{total:,}** (top models per make sampled)\n\n" + md_table(rows))
    return {"md": report(f"{info['short']} ({t}) NHTSA complaints", body, "NHTSA"),
            "data": {"total": total, "by_make": by_make}}


COMMANDS = {"recalls": recalls, "complaints": complaints}
