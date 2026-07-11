# Dataflows: one module per data source, unified CLI in __main__.py.
# Agents run: uv run python -m dataflows <module> <command> [ticker]
# See __main__.py docstring for the full command reference.
#
# Modules:
#   prices        yfinance — history/indicators, fundamentals, analyst (Tom, John)
#   finnhub_data  Finnhub — quotes, company news, insider sentiment (Tom, John)
#   macro         FRED — auto sales/production/inventories, rates (David)
#   filings       SEC EDGAR — XBRL financials, Form 4 insiders (John)
#   news          Google News RSS — company/topic/sector headlines (David)
#   social        Reddit (PRAW or RSS fallback) + StockTwits + VADER (Amy)
#   recalls       NHTSA — recalls & complaints per make (Hairy)
#   industry      OICA production/sales + IEA EV adoption, static (Baldy/Hairy)
