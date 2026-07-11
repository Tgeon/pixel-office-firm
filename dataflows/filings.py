"""John's ground truth: SEC EDGAR — XBRL financials and Form 4 insider filings.

Uses edgartools. EDGAR requires an identity header (EDGAR_IDENTITY in .env).
"""

from __future__ import annotations

import os

from ._core import company, md_table, report


def _edgar_company(ticker: str):
    from edgar import Company, set_identity  # deferred: heavy import
    set_identity(os.getenv("EDGAR_IDENTITY", "pixel-office-firm research"))
    return Company(ticker)


def financials(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    try:
        c = _edgar_company(t)
        fin = c.get_financials()
        if fin is None:
            raise ValueError("no XBRL financials on EDGAR (foreign filer may use 20-F)")
        income = fin.income_statement()
        balance = fin.balance_sheet()
        parts = []
        for label, stmt in (("Income statement", income), ("Balance sheet", balance)):
            try:
                df = stmt.to_dataframe() if hasattr(stmt, "to_dataframe") else stmt
                head = df.head(14).reset_index()
                rows = head.astype(str).to_dict("records")
                parts.append(f"### {label}\n\n" + md_table(rows, max_rows=14))
            except Exception as e:  # noqa: BLE001
                parts.append(f"### {label}\n\n_unavailable: {e}_")
        body = "\n\n".join(parts)
        data = {"available": True}
    except Exception as e:  # noqa: BLE001 — filers vary; report the gap honestly
        body = (f"_EDGAR financials unavailable for {t}: {e}_\n\n"
                "Fallback: use `dataflows prices fundamentals` (yfinance) instead.")
        data = {"available": False, "error": str(e)}
    return {"md": report(f"{info['short']} ({t}) EDGAR financials", body, "SEC EDGAR"),
            "data": data}


def insider(a) -> dict:
    t = a.ticker.upper()
    info = company(t)
    try:
        c = _edgar_company(t)
        filings = c.get_filings(form="4").head(15)
        rows = []
        for f in filings:
            rows.append({
                "Filed": str(getattr(f, "filing_date", "")),
                "Form": getattr(f, "form", "4"),
                "Description": str(getattr(f, "primary_doc_description", "") or "Form 4"),
            })
        body = (f"{len(rows)} most recent Form 4 (insider transaction) filings.\n\n"
                + md_table(rows))
        data = {"count": len(rows), "rows": rows}
    except Exception as e:  # noqa: BLE001
        body = f"_Form 4 lookup failed for {t}: {e}_"
        data = {"error": str(e)}
    return {"md": report(f"{info['short']} ({t}) insider filings (Form 4)", body, "SEC EDGAR"),
            "data": data}


COMMANDS = {"financials": financials, "insider": insider}
