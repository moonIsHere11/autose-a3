# Architecture decision records

Nygard format. Superseded ADRs stay in place and point to their replacement.

| ADR | Decision | Chosen | Main option rejected | Main reason | Status |
|---|---|---|---|---|---|
| [001](ADR-001.md) | D1 Splitting the work | 4 capability profiles (Analyst, Builder, Tester, Reviewer); Release is a script | One agent per stage | Boundaries where permissions change, not where stages change | Accepted |
| [002](ADR-002.md) | D2 Control flow | Code state machine inside an unrolled, bounded Actions DAG | LLM orchestrator | Loop bound and fresh reviewer context guaranteed by structure | Accepted |
| [003](ADR-003.md) | D3 Hand-offs | Named, gate-checked artifacts per role; raw issue withheld from Builder/Tester, spec/design withheld from Reviewer | Shared full transcript | Injection quarantine and reviewer independence | Accepted |
| [004](ADR-004.md) | D4 State | Per-job Actions artifacts + one run-ledger issue comment; branch carries only code | Artifacts committed to the PR branch | Reviewer would read the reasoning; restart reuses Actions re-run | Accepted |
| [005](ADR-005.md) | D5 Tools | Own harness, per-role allowlists, `docker --network none` sandbox, gh/REST only in deterministic steps | GitHub MCP server for agents | The LLM never needs GitHub or a credential | Accepted |
| [006](ADR-006.md) | D6 Models | gemma-4-31b-it workers, gemini-3-flash-preview reviewer | Same model for all roles | Uncorrelated reviewer errors within a free-tier budget | Superseded by 011 |
| [007](ADR-007.md) | D7 Checks | Code-decided gates; red-on-base / green-on-head tests | LLM judge per stage | Vacuous tests and self-certification are rejected mechanically | Accepted |
| [008](ADR-008.md) | D8 Reviewer independence | Separate job + different model + withheld artifacts + evidence gate | Same job with a new prompt | Independence of process, inputs, model, permissions and incentive | Accepted; amended by 012 |
| [009](ADR-009.md) | D9 Safety and failures | Quarantine, no credentials in sandbox, budgets, structural bounds | Prompt-only defence | Injection can at worst produce a bad diff on a branch | Accepted |
| [010](ADR-010.md) | D10 Triggers | Label or `/autose` by write-permission users; per-issue queued concurrency | `issues: opened` for everyone | Only people who could push can spend the budget | Accepted |
| [011](ADR-011.md) | D6 Models (revised) | gemini-3.5-flash-lite workers (Gemma fallback), gemini-3-flash-preview reviewer | Keep Gemma workers with longer timeouts | Measured 503s and ~20 s/call made runs infeasible | Accepted |
| [012](ADR-012.md) | D8/D7 Evidence gate (revised) | Evidence must match executed output or a real file:line; verdict + evidence enforced in-loop | Non-empty evidence text, checked after finish | E1: hollow evidence on S5, missing verdict on S3 | Accepted |
