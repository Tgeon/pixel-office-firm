"""Validate a report against the contract (docs/report-contract.md).

    uv run python scripts/validate_report.py reports/TSLA/2026-07-11-tom.md

Exit 0 = valid. Agents must validate their own report after writing it.
No external deps: minimal YAML-frontmatter parser (scalars + string lists).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

AGENTS = {"tom", "john", "david", "amy", "baldy", "hairy", "theo"}
TIERS = {"strong_positive", "positive", "neutral", "negative", "strong_negative"}
CONF = {"high", "medium", "low"}
REQUIRED = ["agent", "ticker", "date", "stance", "confidence", "key_findings", "sources"]
THEO_EXTRA = ["financial_outlook", "engineering_health", "horizon_months"]
DISCLAIMER_SNIPPET = "not financial, investment, or trading advice"


def parse_frontmatter(text: str) -> dict | None:
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    fm: dict = {}
    current_list = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^\s+-\s+", line) and current_list is not None:
            fm[current_list].append(line.split("-", 1)[1].strip().strip('"').strip("'"))
        elif ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip(), val.split("#")[0].strip().strip('"').strip("'")
            if val == "":
                fm[key] = []
                current_list = key
            else:
                fm[key] = val
                current_list = None
    return fm


def validate(path: Path) -> list[str]:
    problems: list[str] = []
    text = path.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return ["no YAML frontmatter block found (must start with --- on line 1)"]

    for k in REQUIRED:
        if k not in fm:
            problems.append(f"missing frontmatter field: {k}")

    agent = str(fm.get("agent", "")).lower()
    if agent not in AGENTS:
        problems.append(f"agent must be one of {sorted(AGENTS)}, got {agent!r}")
    if str(fm.get("stance", "")) not in TIERS:
        problems.append(f"stance must be one of {sorted(TIERS)}, got {fm.get('stance')!r}")
    if str(fm.get("confidence", "")) not in CONF:
        problems.append(f"confidence must be one of {sorted(CONF)}, got {fm.get('confidence')!r}")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(fm.get("date", ""))):
        problems.append(f"date must be YYYY-MM-DD, got {fm.get('date')!r}")

    kf = fm.get("key_findings", [])
    if not isinstance(kf, list) or not 1 <= len(kf) <= 6:
        problems.append("key_findings must be a list of 1-6 items")
    if not isinstance(fm.get("sources", []), list) or not fm.get("sources"):
        problems.append("sources must be a non-empty list")

    if agent == "theo":
        for k in THEO_EXTRA:
            if k not in fm:
                problems.append(f"verdict missing field: {k}")
        for k in ("financial_outlook", "engineering_health"):
            if k in fm and fm[k] not in TIERS:
                problems.append(f"{k} must be a valid tier, got {fm[k]!r}")
        if "horizon_months" in fm and not str(fm["horizon_months"]).isdigit():
            problems.append("horizon_months must be an integer (6-12)")
        if "Confidence rubric" not in text:
            problems.append("verdict must include the filled 'Confidence rubric' table")

    if DISCLAIMER_SNIPPET not in text:
        problems.append("missing required disclaimer footer (see docs/report-contract.md)")

    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    failures = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        problems = validate(p)
        if problems:
            failures += 1
            print(f"INVALID {p}")
            for x in problems:
                print(f"  - {x}")
        else:
            print(f"VALID   {p}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
