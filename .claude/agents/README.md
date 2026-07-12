# Firm Agents

The seven Claude Code subagent definitions. Trigger a full run with:

    /analyze TSLA

Pipeline (see `.claude/commands/analyze.md`): analysts in parallel → Baldy's
bull case → Hairy's bear case + rebuttal → Baldy's rebuttal → Theo's verdict.

| Agent | Role | Model | Sources |
|---|---|---|---|
| `tom.md` | Technical analyst | haiku | prices history, finnhub quote |
| `john.md` | Fundamentals analyst | haiku | fundamentals, profile, insider, EDGAR |
| `david.md` | News & macro analyst | haiku | macro snapshot, news, finnhub news |
| `amy.md` | Sentiment analyst | haiku | social pulse (Reddit RSS + StockTwits) |
| `baldy.md` | Bull researcher | sonnet | analyst reports + industry + recalls |
| `hairy.md` | Bear researcher | sonnet | analyst reports + recalls/complaints |
| `theo.md` | Representative | sonnet | all six reports → verdict |

Every agent writes to `reports/<TICKER>/` under the contract in
`docs/report-contract.md` and self-validates with `scripts/validate_report.py`.

Model note (decision 1.2): analysts run quick-think (haiku), researchers and
Theo run deep-think (sonnet). Swap `model:` to an Ollama-served model later
for zero-cost analysts once local models are configured.
