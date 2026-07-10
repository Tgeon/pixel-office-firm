# Pixel Office Firm — Data Source Catalog

**Task 1 deliverable** · Scope: major public automakers + EV startups · Budget: free only · Stack: Python
Framework reference: [TradingAgents (arXiv 2412.20138)](https://arxiv.org/abs/2412.20138) · [Official repo](https://github.com/TauricResearch/TradingAgents)

## Confirmed Project Decisions

| Decision | Choice |
|---|---|
| Dev environment | VS Code + GitHub repo |
| Office visualization | [Pixel Agents extension](https://marketplace.visualstudio.com/items?itemName=pablodelucca.pixel-agents) ([GitHub](https://github.com/pixel-agents-hq/pixel-agents)); custom local environment as fallback |
| Firm framing | **Consulting unit** — insights on both finance *and* engineering, not a trading desk |
| Verdict format | Five-tier rating + qualitative confidence + Theo's narrative |
| Run model | Daily digest (sidebar-style summary across the universe) + detailed per-company analysis on demand |
| Firm layout | 7 agents as designed — no risk team, no facilitator, no manager approval stage. Theo stays presenter-only |

**Pixel Agents caveat:** the extension visualizes agents by watching **Claude Code session transcripts** (JSONL) — it doesn't natively render arbitrary Python/LangGraph agents. Two viable paths when we build: (a) run each firm agent as a Claude Code subagent so Pixel Agents picks them up automatically, or (b) it's open source and fully customizable (custom sprites/office assets; a [standalone web fork](https://github.com/rolandal/pixel-agents-standalone) exists), so we can adapt it or emit compatible transcript files from our own pipeline. Decide at build time; fallback is a custom pixel office.

---

## Ticker Universe

| Group | Tickers |
|---|---|
| Major automakers | TSLA, TM (Toyota), F, GM, STLA (Stellantis), HMC (Honda), VWAGY (VW ADR), HYMTF (Hyundai OTC) |
| EV startups | RIVN, LCID, NIO, XPEV, LI, BYDDY (BYD ADR), PSNY (Polestar) |

Note: OTC/ADR tickers (VWAGY, HYMTF, BYDDY) have thinner data on some free APIs — yfinance covers them all.

---

## Quick Reference: Agent → Source Map

| Agent | Role | Primary sources | Backup |
|---|---|---|---|
| **Tom** | Real-time charts & technicals | yfinance, Finnhub | Alpha Vantage |
| **John** | Fundamentals & real value | SEC EDGAR, yfinance fundamentals, FMP | Finnhub, SimFin |
| **David** | News & macro | FRED, Google News RSS, GDELT, EIA | Alpha Vantage news, marketaux |
| **Amy** | Public/investor sentiment | Reddit (PRAW), Alpha Vantage sentiment, Google Trends | StockTwits, YouTube API |
| **Baldy / Hairy** | Bull/bear research | OICA, IEA EV data, NHTSA (recalls + vPIC), Kaggle datasets, company IR reports | fueleconomy.gov, state EV registrations |
| **Theo** | Presenter | Consumes all of the above + analyst estimates (yfinance) | — |

---

## 1. Market Data & Technicals — Tom

### yfinance ⭐ primary
- **Provides:** OHLCV history (any interval down to 1m), delayed quotes (~15 min), covers all tickers incl. ADRs
- **Access:** `pip install yfinance` — no key, no signup. Same backbone the TradingAgents repo uses
- **Limits:** Unofficial scraper; can break when Yahoo changes endpoints. Cache aggressively
```python
import yfinance as yf
df = yf.download(["TSLA","RIVN","F"], period="1y", interval="1d")
```

### Finnhub — [finnhub.io](https://finnhub.io/)
- **Provides:** Real-time US quotes, candles, company news, basic financials
- **Access:** Free key, **60 calls/min** — the most generous free real-time tier
- **Limits:** US-listed only on free tier (fine for everything except deep ADR data)

### Alpha Vantage — [alphavantage.co](https://www.alphavantage.co/)
- **Provides:** Daily/intraday OHLCV, 50+ built-in technical indicators (RSI, MACD), news + sentiment
- **Access:** Free key; already a supported key in the TradingAgents repo (`ALPHA_VANTAGE_API_KEY`)
- **Limits:** ~25 requests/day free — use for indicators/sentiment, not bulk quotes

### Indicator computation (local, unlimited)
- `stockstats` or `pandas-ta` — compute MACD/RSI/Bollinger from yfinance data locally instead of burning API calls. This is what the reference repo does.

---

## 2. Fundamentals & Valuation — John

### SEC EDGAR APIs ⭐ primary — [sec.gov EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation)
- **Provides:** All 10-K/10-Q/8-K filings, XBRL company facts (revenue, margins, debt, inventory, capex) as JSON
- **Access:** Free, no key — just set a User-Agent header. `pip install edgartools` makes it painless
- **Why it matters:** Ground truth for "actual real value" — auto inventories and capex straight from filings. US filers only (Toyota/Honda file 20-Fs, also on EDGAR)

### yfinance fundamentals
- `.info`, `.balance_sheet`, `.income_stmt`, `.cashflow` — quick ratios (P/E, EV/EBITDA, book value) for the whole universe including ADRs

### Financial Modeling Prep — [financialmodelingprep.com](https://site.financialmodelingprep.com/)
- **Provides:** Clean historical financial statements, ratios, DCF values
- **Access:** Free key, ~250 requests/day
- **Limits:** Free tier restricted to US-listed symbols

### Finnhub basic financials
- Company profile, peer lists, margin/valuation metrics — shares the 60/min key from Tom's stack

### Insider transactions & sentiment *(explicit input in the paper, §5.2)*
- **SEC Form 4 filings via EDGAR** — every insider buy/sell for US filers, free, no key (same `edgartools` stack)
- **Finnhub `/stock/insider-sentiment` and `/stock/insider-transactions`** — pre-aggregated monthly insider sentiment (MSPR), free tier
- **Use:** John flags heavy insider selling/buying as a real-value signal; Hairy uses insider selling in the bear case

---

## 3. News & Macroeconomics — David

### FRED API ⭐ primary — [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/fred) *(verified live, data through May 2026)*
- **Access:** Free key, `pip install fredapi`
- **Key automotive series:**

| Series ID | What it is |
|---|---|
| `TOTALSA` | Total US vehicle sales (SAAR, monthly) |
| `ALTSALES` | Light-weight vehicle sales: autos + light trucks |
| `DAUPSA` | Domestic auto production |
| `AUINSA` / `AISRSA` | Domestic auto inventories / inventory-sales ratio |
| `DAUTOSAAR` | Domestic auto retail sales |
| `MRTSSM44112USN` | Used-car dealer retail sales |
| `UMCSENT` | Consumer sentiment (U. Michigan) |
| `FEDFUNDS`, `T10Y2Y` | Rates / yield curve (auto loans are rate-sensitive) |
| `CUSR0000SETA01` | CPI: new vehicles |

### Google News RSS (via `feedparser`)
- **Provides:** Real-time headlines per company/topic, free, no key: `https://news.google.com/rss/search?q=Rivian+production`
- **Limits:** Headlines + snippets only; treat as a signal feed

### GDELT 2.0 — [gdeltproject.org](https://www.gdeltproject.org/)
- **Provides:** Global news event database with tone scoring, updated every 15 min, no key
- **Access:** DOC 2.0 REST API or BigQuery public dataset
- **Why:** Free macro/geopolitical event coverage (tariffs, plant closures, strikes) at global scale

### EIA API — [eia.gov/opendata](https://www.eia.gov/opendata/)
- **Provides:** Gasoline prices, electricity prices — direct demand drivers for ICE vs EV
- **Access:** Free key

### marketaux — [marketaux.com](https://www.marketaux.com/)
- **Provides:** Entity-tagged financial news with sentiment, 5,000+ sources
- **Access:** Free tier (~100 req/day) — good backup to Google News

---

## 4. Public & Investor Sentiment — Amy

### Reddit via PRAW ⭐ primary — [praw.readthedocs.io](https://praw.readthedocs.io/)
- **Provides:** Posts/comments from investor subs (r/stocks, r/wallstreetbets, r/investing) and enthusiast subs (r/cars, r/electricvehicles, r/teslamotors, r/Rivian, r/whatcarshouldIbuy)
- **Access:** Free Reddit app credentials, 100 queries/min — plenty
- **Why:** Amy's brief is *both* the average investor and the automotive enthusiast — the enthusiast subs are the differentiator vs generic sentiment feeds
- **Pipeline:** score text locally with VADER (`nltk`) or FinBERT (`transformers`) — free, no API cost

### Alpha Vantage News & Sentiment
- Pre-scored ticker-level sentiment (−1 to +1) — shares Tom's key; a few calls/day is enough for a daily sentiment pulse

### Google Trends via `pytrends`
- Search-interest proxy for consumer demand ("Rivian R2", "Tesla Model Y") — free, unofficial

### StockTwits public API
- Ticker-stream messages with user-tagged bullish/bearish labels — free public endpoints, retail-investor mood in raw form

### YouTube Data API (free quota: 10k units/day)
- Comment sentiment on reviews from major auto channels — the strongest "enthusiast opinion" signal available free

---

## 5. Manufacturing, Production & Engineering — Baldy & Hairy

### OICA production/sales statistics — [oica.net/production-statistics](https://oica.net/production-statistics/)
- **Provides:** Global vehicle production & sales by country and manufacturer, 1999–present (annual)
- **Access:** Free downloads; tidy CSVs via the [jhelvy/oica](https://jhelvy.github.io/oica/) GitHub package — grab CSVs directly from the repo in Python
- **Use:** Baseline production-share and growth trends per manufacturer

### IEA Global EV Data Explorer — [iea.org Global EV Data Explorer](https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer)
- **Provides:** EV sales, stock, share, charging infrastructure by country/year — free CSV download
- **Use:** Bull case (Baldy): adoption curves; Bear case (Hairy): markets where growth is stalling

### NHTSA APIs — [nhtsa.gov datasets & APIs](https://www.nhtsa.gov/nhtsa-datasets-and-apis)
- **Recalls & Complaints API:** recalls/complaints per make/model — Hairy's best free weapon (quality problems precede financial ones). Free, no key
- **vPIC Vehicle API** ([vpic.nhtsa.dot.gov/api](https://vpic.nhtsa.dot.gov/api/)): specs, VIN decode, plant/manufacturer info — engineering grounding. Free, no key

### fueleconomy.gov Web Services — [fueleconomy.gov/feg/ws](https://www.fueleconomy.gov/feg/ws/)
- **Provides:** EPA fuel economy/efficiency for every model — objective engineering-competitiveness metric. Free XML/JSON, no key

### State EV registration data (live)
- **Washington State** ([data.wa.gov](https://data.wa.gov/), Socrata API): full EV registration records by make/model, updated monthly, free — a real-time-ish proxy for brand-level EV demand

### Kaggle datasets — [kaggle.com automotive tag](https://www.kaggle.com/datasets?tags=12402-Automobiles+and+Vehicles)
- [Vehicle Sales Data](https://www.kaggle.com/datasets/syedanwarafridi/vehicle-sales-data) — 500k+ used-vehicle transactions with prices (residual-value signal)
- [EV Dataset](https://www.kaggle.com/datasets/geoffnel/evs-one-electric-vehicle-dataset) — specs comparison across EVs
- Free with Kaggle account, `pip install kaggle` CLI
- **Use:** Static knowledge base / embedding corpus for the researchers, not live data

### Company IR pages (quarterly production & delivery reports)
- Tesla, Rivian, NIO, XPeng, Li Auto publish quarterly production/delivery numbers as press releases — the single most market-moving automotive datapoint. Scrape IR RSS or catch via 8-K on EDGAR (free)

### Argonne National Laboratory — [Light Duty Electric Drive Vehicles Monthly Sales](https://www.anl.gov/esia/light-duty-electric-drive-vehicles-monthly-sales-updates)
- Monthly US EV/PHEV sales estimates, free download — fresher than OICA/IEA annual data

---

## 6. Theo (Representative)

Theo consumes structured reports from the six agents and produces the client-facing verdict: **five-tier rating + qualitative confidence**, covering both the financial case (Tom/John/David/Amy) and the engineering case (Baldy/Hairy's production, quality, and spec evidence). Additional direct inputs:
- **Analyst estimates & price targets:** `yf.Ticker("TSLA").analyst_price_targets`, `.recommendations` — free consensus context for framing the firm's own view
- Everything else arrives as agent reports; per the confirmed layout, the Baldy/Hairy debate ends after fixed rounds and Theo presents both sides with his synthesis — no facilitator picks a "winner," no risk-team stage

---

## Implementation Notes

**API keys needed (all free signups):** Finnhub, Alpha Vantage, FRED, EIA, FMP, Reddit (client id/secret), Kaggle. No key: yfinance, SEC EDGAR, Google News RSS, GDELT, NHTSA, fueleconomy.gov, OICA CSVs, StockTwits.

**Rate-limit budget (free tiers):**

| Source | Limit | Strategy |
|---|---|---|
| Finnhub | 60/min | Tom's live quotes |
| Alpha Vantage | ~25/day | Sentiment + indicator spot-checks only |
| FMP | ~250/day | John's daily fundamentals refresh |
| FRED | 120/min | Effectively unlimited for this use |
| Reddit | 100/min | Amy's hourly scans |
| yfinance | unofficial | Cache; back off on errors |

**Two run tiers (per the confirmed run model):**

- **Daily digest** (~15 tickers, every morning): cheap sources only — yfinance batch download (1 call), Finnhub quotes/news (~30 calls), FRED macro (~10 calls), one Reddit sweep. Zero Alpha Vantage/FMP usage. Light LLM summarization, no debate.
- **On-demand deep analysis** (1 ticker): full pipeline — all six agents + Baldy/Hairy debate, EDGAR filings, insider data, NHTSA/spec lookups, full sentiment scan. This is where the daily Alpha Vantage (~25) and FMP (~250) budgets get spent, and where the paper's ~11 LLM calls + 20 tool calls per prediction applies.

**Parity with the paper's dataset (§5.2):** the paper's inputs are historical prices ✓ (yfinance/Finnhub), news ✓ (Google News/GDELT/marketaux — paper used Bloomberg/Yahoo/EODHD/FinnHub/Reddit), social sentiment ✓ (Reddit/StockTwits — **X/Twitter excluded: no free API tier**), insider sentiment & transactions ✓ (EDGAR Form 4 + Finnhub), financial statements ✓ (EDGAR), company profiles ✓ (Finnhub/yfinance), and 60 technical indicators per asset ✓ (`pandas-ta` computes 130+ locally). Full free-tier coverage of every input category, plus the automotive-specific layer the paper doesn't have.

**Architecture tips (mirrors the TradingAgents repo):**

1. Build a `dataflows/`-style interface layer — one Python module per source returning normalized DataFrames/dicts, so agents call `get_price_history(ticker)` not raw APIs.
2. Cache everything (SQLite or parquet, like the repo's `~/.tradingagents/cache/`). Static datasets (OICA, IEA, Kaggle, NHTSA bulk) download once and refresh monthly.
3. Two data tiers: **live** (prices, news, Reddit — fetched per analysis run) and **knowledge base** (production stats, specs, recalls — preloaded, queried by the researchers).
4. Keep `.env` for keys, same pattern as the repo's `.env.example`.

---

## Sources consulted
- [TradingAgents paper (arXiv)](https://arxiv.org/abs/2412.20138) · [TauricResearch/TradingAgents repo](https://github.com/TauricResearch/TradingAgents)
- [Best Free Stock Market APIs 2026 (DEV)](https://dev.to/nexgendata/best-free-stock-market-apis-and-data-tools-in-2026-a-developers-honest-comparison-1926) · [Yahoo Finance API guide (MarketXLS)](https://marketxls.com/blog/yahoo-finance-api-ultimate-guide) · [Best free stock APIs tested 2026](https://thenextgennexus.com/2026/05/15/10-best-free-stock-market-apis-2026/)
- [Finnhub](https://finnhub.io/) · [Alpha Vantage](https://www.alphavantage.co/) · [marketaux](https://www.marketaux.com/)
- [FRED TOTALSA (verified)](https://fred.stlouisfed.org/series/TOTALSA)
- [OICA production statistics](https://oica.net/production-statistics/) · [jhelvy/oica package](https://jhelvy.github.io/oica/) · [IEA Global EV Data Explorer](https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer)
- [NHTSA vPIC API](https://vpic.nhtsa.dot.gov/api/) · [NHTSA datasets & APIs](https://www.nhtsa.gov/nhtsa-datasets-and-apis)
- [Kaggle Vehicle Sales Data](https://www.kaggle.com/datasets/syedanwarafridi/vehicle-sales-data) · [Kaggle EV dataset](https://www.kaggle.com/datasets/geoffnel/evs-one-electric-vehicle-dataset)
