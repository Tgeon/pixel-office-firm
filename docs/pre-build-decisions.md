# Pixel Office Firm — Decision Record

**Status: all blocking decisions made — ready to build.** 19 deferrable items remain, safe to settle mid-build.

---

## Decided ✅

### Foundation

| Decision | Choice |
|---|---|
| Framework basis | TradingAgents (arXiv 2412.20138) |
| Coverage | Major automakers + EV startups |
| Data budget | Free sources only (see data-source-catalog.md) |
| Language | Python |
| Dev environment | VS Code + GitHub repo |
| Firm framing | Consulting unit — finance + engineering insights, not a trading desk |
| Layout | 7 agents (Tom, John, David, Amy, Baldy, Hairy, Theo); no risk team, facilitator, or manager stage |
| Run model | Daily digest + on-demand deep analysis |

### Runtime & models

| # | Decision | Choice |
|---|---|---|
| 1.1 | Agent runtime | **Claude Code subagents** — Pixel Agents renders them natively; agents call Python dataflows via bash |
| 1.2 | LLM models | **Hybrid:** subscription Claude for deep-think (Baldy, Hairy, Theo); local Ollama (v0.14+ native Anthropic API) for quick-think fetch/summarize |
| 1.3 | Budget | Covered by subscription + free local models. ⚠️ Verify Agent SDK credit allowance before automating the headless digest (4.1) |
| 3.1 | Pixel Agents integration | Native — extension watches Claude Code sessions out of the box |

### The report contract

| # | Decision | Choice |
|---|---|---|
| 1.5 | Report schema | **Markdown + YAML frontmatter** per agent report: `agent, ticker, date, stance, confidence, key_findings[], sources[]` + prose body. Human-readable, machine-parseable |
| 5.1 | Rating scale | **Five outlook tiers** — Strong Positive / Positive / Neutral / Negative / Strong Negative — with a stated **6–12 month horizon**. Consulting opinion on trajectory, not a trade signal |
| 5.2 | Confidence | **Computed 3-check rubric** → High/Med/Low from (1) data coverage, (2) agent agreement, (3) evidence recency. Checklist prints in every report |
| 5.3 | Score structure | **Two sub-scores + overall:** Financial Outlook tier (Tom/John/David/Amy) + Engineering Health tier (Baldy/Hairy) + Theo's narratively derived overall rating |
| 5.4 | Disclaimer | Standard research/education, not-financial-advice footer auto-appended to **every** report and digest |

### Scope

| # | Decision | Choice |
|---|---|---|
| 2.1 | v1 tickers (12) | **TSLA, TM, F, GM, STLA, HMC, RIVN, LCID, NIO, XPEV, LI, PSNY** — all exchange-listed. OTC ADRs (VWAGY, HYMTF, BYDDY) → v2 |
| 2.2 | v1 sources (8) | **yfinance, Finnhub, FRED, SEC EDGAR, Google News RSS, Reddit/PRAW, NHTSA recalls, OICA+IEA CSVs.** Keys needed: Finnhub, FRED, Reddit. Rest of catalog → v2 |

### Digest & surfaces

| # | Decision | Choice |
|---|---|---|
| 3.2 | Digest surface | **`digest/YYYY-MM-DD.md`** auto-opened in VS Code markdown preview, docked beside the pixel office. Webview sidebar → v2 |
| 4.2 | Digest content | **Movers + one-liners:** top 3 movers get a paragraph (what/why/does it change our view); other 9 get one line (price Δ, headline, sentiment arrow, event flags); + 2-line macro note |

### Engineering hygiene

| # | Decision | Choice |
|---|---|---|
| 6.1 | Repo layout | `.claude/agents/` (7 subagent defs) · `dataflows/` · `data/` (gitignored) · `reports/` · `digest/` · `scripts/` · `office/` |
| 6.2 | Py tooling | **Python 3.12 + uv** (venv, lockfile, installs) |
| 6.3 | Secrets | **`.env` (gitignored) + `.env.example` (committed)**, python-dotenv, keys loaded only inside `dataflows/` — subagents see script outputs, never raw keys |

---

## Open — deferrable ⏳ (19)

Settle these as they come up during the build; suggested defaults noted.

| # | Decision | Suggested default |
|---|---|---|
| 1.4 | Analyst parallelism | Sequential v1 (easier debugging); parallel v2 for pixel-office effect |
| 1.6 | Debate protocol | 2 rounds Baldy↔Hairy, Baldy opens, ~300-word turns |
| 1.7 | Memory / decision log | v2 — append verdicts to `memory/decisions.md`, recall same-ticker history |
| 1.8 | Error handling | Skip failed agent, note the gap in Theo's report; never abort a run |
| 2.3 | Cache store & TTLs | SQLite in `data/cache.db`; quotes 15min, news 6h, fundamentals 7d, static monthly |
| 2.4 | Sentiment scorer | VADER v1 (zero setup), FinBERT v2 |
| 2.5 | Static dataset ingestion | `scripts/refresh_static.py`, files in `data/static/` (gitignored), run monthly |
| 2.6 | Knowledge-base retrieval | Direct DataFrame lookups v1; RAG only if researchers demonstrably need it |
| 3.3 | Deep-report surface | `reports/<TICKER>/YYYY-MM-DD.md`, opened on completion |
| 3.4 | Office scene design | Default sprites v1; custom automotive-themed desks/assets v2 |
| 3.5 | Digest animation | Deep runs only animate; digest runs headless |
| 3.6 | Deep-run trigger | CLI/command-palette v1; click-Theo v2 |
| 4.1 | Digest trigger | Manual command v1 → scheduled once Agent SDK credit allowance is confirmed |
| 4.3 | Digest freshness window | Trailing 24h |
| 5.5 | Evaluation plan | Log every rating; monthly spot-check vs price action + known events |
| 6.4 | License | MIT if public, decide at repo creation |
| 6.5 | Testing | pytest for dataflows with mocked API responses; agents tested by running them |
| 6.6 | CI | GitHub Actions lint+test on push (cheap to add once tests exist) |
| 6.7 | Git workflow | Direct to main, solo project |

---

## Build order

1. Repo scaffold (6.1–6.3) + `.env` keys signup (Finnhub, FRED, Reddit)
2. `dataflows/` — 8 v1 sources, each returning normalized dicts/DataFrames, with cache
3. Report contract — frontmatter schema, rating/confidence/disclaimer templates
4. The 7 subagent definitions in `.claude/agents/` + deep-run orchestration
5. Daily digest script
6. Pixel office — install Pixel Agents, verify agents render, tune scene

The office is the reward, not the foundation.
