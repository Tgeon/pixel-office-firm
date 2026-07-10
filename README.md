# Pixel Office Firm 🏢🚗

A multi-agent AI consulting firm that analyzes automotive companies — finance *and* engineering — rendered as a pixel-art office in VS Code.

Built on the [TradingAgents](https://arxiv.org/abs/2412.20138) multi-agent framework, running as [Claude Code](https://code.claude.com) subagents visualized with [Pixel Agents](https://marketplace.visualstudio.com/items?itemName=pablodelucca.pixel-agents).

## The Firm

| Agent | Team | Role |
|---|---|---|
| **Tom** | Analysts | Real-time charts & technicals |
| **John** | Analysts | Fundamentals & real value (filings, insider activity) |
| **David** | Analysts | News & macroeconomics |
| **Amy** | Analysts | Investor & enthusiast sentiment |
| **Baldy** | Research | Bull case — grounds for positive impact |
| **Hairy** | Research | Bear case — what goes wrong |
| **Theo** | Representative | Synthesizes everything, presents to the client |

## Output

Every analysis produces a five-tier **outlook rating** (Strong Positive → Strong Negative, 6–12 month horizon) with two sub-scores — **Financial Outlook** and **Engineering Health** — plus an auditable confidence level.

Two run modes: a **daily digest** across the 12-ticker universe, and **on-demand deep analysis** of a single company.

## Coverage

TSLA · TM · F · GM · STLA · HMC · RIVN · LCID · NIO · XPEV · LI · PSNY

## Setup

```bash
uv sync                      # Python 3.12 env + deps
cp .env.example .env         # then fill in your free API keys
```

Free API keys needed: [Finnhub](https://finnhub.io/register), [FRED](https://fredaccount.stlouisfed.org/apikeys), [Reddit](https://www.reddit.com/prefs/apps).

## Repo layout

```
.claude/agents/   the 7 firm agents (Claude Code subagent definitions)
dataflows/        one Python module per data source, normalized outputs
data/             cache + static datasets (gitignored)
reports/          deep-analysis outputs, one folder per ticker
digest/           daily digest markdown files
scripts/          orchestration + maintenance scripts
office/           pixel office sprites & config
docs/             data source catalog, decision record
```

## Disclaimer

This is a research and educational project. Nothing it produces is financial, investment, or trading advice.
