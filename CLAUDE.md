# Pixel Office Firm — Project Context

You are working inside a multi-agent "consulting firm" that analyzes automotive companies. Full spec lives in `docs/pre-build-decisions.md` (all decisions) and `docs/data-source-catalog.md` (data sources).

## Core rules

- **The report contract:** every agent report is markdown with YAML frontmatter: `agent, ticker, date, stance, confidence, key_findings[], sources[]`, then a prose body. Reports go in `reports/<TICKER>/`.
- **Ratings** are five outlook tiers (Strong Positive / Positive / Neutral / Negative / Strong Negative), 6–12 month horizon, always with two sub-scores: Financial Outlook + Engineering Health.
- **Confidence** is computed, not vibes: data coverage + agent agreement + evidence recency → High/Med/Low, checklist shown in the report.
- **Disclaimer footer** on every report and digest: research/education, not financial advice.
- **Data access:** agents never call APIs directly — they run scripts in `dataflows/` via bash and read the normalized output. API keys live in `.env`, loaded only inside dataflows.
- **Ticker universe (v1):** TSLA, TM, F, GM, STLA, HMC, RIVN, LCID, NIO, XPEV, LI, PSNY.
- **Debate:** Baldy (bull) and Hairy (bear) debate for 2 rounds, Baldy opens. No facilitator — Theo presents both sides plus his synthesis; he does not pick a "winner."
- **Errors:** if a source or agent fails, skip it and note the gap in the report. Never abort a run.

## Tooling

- Python 3.12, managed with `uv` (run scripts via `uv run`).
- Sentiment scoring: VADER (v1).
- Cache: SQLite at `data/cache.db` — quotes 15min TTL, news 6h, fundamentals 7d.

## The agents

Tom (technicals), John (fundamentals/insider), David (news/macro), Amy (sentiment) — analysts, quick-think work.
Baldy (bull researcher), Hairy (bear researcher), Theo (client representative) — deep-think work.
