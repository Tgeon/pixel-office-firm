---
description: Run a full firm analysis on a ticker — 4 analysts, researcher debate, Theo's verdict
argument-hint: TICKER (one of TSLA TM F GM STLA HMC RIVN LCID NIO XPEV LI PSNY)
---

Run a deep analysis on ticker **$ARGUMENTS** following the firm's pipeline.

Setup:
- TICKER = $ARGUMENTS uppercased. If it's not in the v1 universe
  (TSLA, TM, F, GM, STLA, HMC, RIVN, LCID, NIO, XPEV, LI, PSNY), stop and say so.
- DATE = today, YYYY-MM-DD. Create `reports/<TICKER>/` if missing.
- Every subagent gets told: the TICKER, the DATE, and that it must follow its
  agent definition. Do not do any analysis yourself — you are the dispatcher.

Note: when launched from the pixel office, the dataflows cache is pre-warmed
in parallel — agents' commands should return instantly. Do not skip commands
because of this; run them normally.

Pipeline (4 stages, strictly in order):

1. **Analyst floor** — launch the four analyst subagents (tom, john, david, amy),
   each producing its report for TICKER/DATE. They are independent — launch all
   four in parallel.
2. **Cases (parallel)** — launch baldy AND hairy simultaneously, both in
   round 1: each reads only the four analyst reports and writes their own case
   blind to the other's. Neither sees the opposing case yet — this keeps the
   debate honest.
3. **Rebuttal exchange (parallel)** — launch baldy and hairy again
   simultaneously, both in round 2: each reads the other's now-complete case
   and fills in their report's "Rebuttal (round 2)" section.
4. **Verdict** — launch theo. He synthesizes all six reports into
   `reports/<TICKER>/<date>-verdict.md` and presents the 5-line client summary.

After stage 5: run
`uv run python scripts/validate_report.py reports/<TICKER>/<DATE>-*.md`
and report the validation results. If any report is INVALID, relaunch that
agent once to fix it. Then relay Theo's client summary verbatim.

If a stage fails (agent errors out, report missing), note the gap and continue
the pipeline — a missing analyst lowers Theo's coverage score but never aborts
the run.
