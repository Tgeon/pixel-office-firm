---
description: Theo's morning digest — movers, one-liners, macro note across the 12-ticker universe
---

Produce today's digest by launching the **theo** subagent in digest mode with
these instructions:

1. Run `uv run python scripts/digest_data.py` (from the repo root) and read
   the JSON it prints.
2. Write `digest/<date>.md` (date from the JSON) in this exact structure:

   ```
   # Morning Digest — <date>

   ## Macro
   <2 lines max: latest TOTALSA vehicle-sales pace and Fed funds rate, with a
   one-phrase read on what it means for autos>

   ## Movers
   <one short paragraph per ticker in `movers`: what moved (the % and close),
   the likely why (use the headline; if the headline doesn't explain it, say
   the move lacks an obvious catalyst — never invent a reason), and whether it
   challenges our last verdict tier if one exists>

   ## The floor
   | Ticker | Δ% | Social | Last verdict | Top headline |
   <one row per remaining ticker: pct with sign, social arrow, verdict tier +
   age like "positive, 5d" or "—" if never analyzed, headline truncated ~70ch>

   ## Desk notes
   <1-3 bullets ONLY if warranted: a verdict older than 30d on a big mover
   ("worth a fresh /analyze"), a data gap, or a divergence between social
   arrows and price. Otherwise omit the section.>
   ```

3. End the file with the standard disclaimer footer (verbatim, from
   `docs/report-contract.md`).
4. Open the digest in preview so it docks beside the office:
   run `code -r "digest/<date>.md"` via bash, then tell the client the file
   path and give a 2-line spoken summary of the morning.

Notes for Theo: this is the quick morning pass — no deep analysis, no new
dataflows calls beyond digest_data.py, no stance changes. Movers paragraphs
are observation, not verdict revision.
