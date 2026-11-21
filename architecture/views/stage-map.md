# Stage map

Workers use `gemma-4-31b-it` (fallback `gemma-4-26b-a4b-it` after retries on 429/503).
The Reviewer uses `gemini-3-flash-preview`. Every check below is code; no LLM certifies its own stage.

| # | Stage | Agent / component | Model | Inputs (and deliberately withheld) | Artifact | Check (code) | On failure |
|---|---|---|---|---|---|---|---|
| 1 | Requirements | Analyst (job `build`) | gemma-4-31b-it | Raw issue wrapped in `<untrusted_issue>`, condensed A1 requirements-spec skill, read-only repo. | `spec.md` | Spec parses; at least 1 `AC-n`; every AC has Given/When/Then; fuzzy-word lint (fast, easy, robust, ...) on ACs. | Retry with gate feedback (2 retries), then stop with reason in `spec.md`. |
| 2 | Design | Analyst (job `build`) | gemma-4-31b-it | `spec.md`, A2 `ARCHITECTURE.md`, read-only repo. | `design.md` | Changes table present; each `file::function` exists per AST, or is marked NEW. | Retry with feedback (2 retries), then stop. |
| 3 | Implementation | Builder (job `build`) | gemma-4-31b-it | `spec.md`, `design.md`, repo. Withheld: raw issue (injection quarantine). | `diff.patch` | Diff non-empty; touches only `tinydb/`; `compileall` and `import tinydb` pass in sandbox. | Retry; counts against the implementation budget. |
| 4 | Testing | Tester (job `build`) | gemma-4-31b-it | `spec.md`, repo with the change. Withheld: Builder transcript and reasoning. | `test_report.md` | Every AC id appears in a test name in `tests/autose/`; each AC test fails on base and passes on head (red/green); full suite passes on head. | Back to stage 3 with failure output (3 attempts), then back to stage 2 once, then stop. |
| 5 | Release | `ship_0` / `ship_1` (script, no LLM) | none | Diff and test report from artifacts. | `pr.md` + PR link | PR open; CI job (full pytest + mypy) green on PR head. | Stop with reason in `pr.md` and ledger. |
| 6 | Review | Reviewer (job `review_1`, `review_2`) | gemini-3-flash-preview | Raw issue, harness-computed `git diff base...head`, repo at PR head. Withheld: `spec.md`, `design.md`, `test_report.md`, PR body, all worker transcripts. | `review.md` | Verdict JSON valid; approval requires at least one executed command (evidence gate); findings without evidence are dropped. Approve, or 2 rounds used. | `approach` finding returns to stage 2, `code` finding to stage 3 (job `rework_1`), at most twice. Then `finalize`: a human decides. |
