# Dataflows: one module per data source, each returning normalized dicts/DataFrames.
# Contract (see CLAUDE.md): agents run these via bash/CLI, never call APIs directly.
# API keys are loaded here (python-dotenv) and nowhere else.
#
# v1 sources (build order):
#   prices.py       — yfinance: OHLCV, fundamentals snapshots, analyst estimates
#   finnhub_data.py — real-time quotes, company news, insider sentiment
#   macro.py        — FRED: auto sales, production, inventories, rates, CPI
#   filings.py      — SEC EDGAR: financials (XBRL), Form 4 insider transactions
#   news.py         — Google News RSS per ticker/topic
#   social.py       — Reddit via PRAW + VADER scoring
#   recalls.py      — NHTSA recalls & complaints per make/model
#   industry.py     — OICA + IEA static CSVs: production, sales, EV adoption
