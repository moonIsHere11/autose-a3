# Sequence view: one real run (issue #2, CachingMiddleware bug)

Run: https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921915844 (attempts 1 and 2) ·
Issue: https://github.com/moonIsHere11/tinydb-autose/issues/2 · PR: https://github.com/moonIsHere11/tinydb-autose/pull/12

All times are UTC on 2026-11-21, taken from the Actions job API and the harness's `events.json`. The run includes a
real restart: in attempt 1, `review_1` lost its model to free-tier quota errors and the job failed. `finalize`
recorded the stop. After a harness fix, *Re-run failed jobs* (attempt 2) re-ran only `review_1` and `finalize`,
reusing `gate`/`build`/`ship_0` and their artifacts (ADR-004).

```mermaid
sequenceDiagram
  autonumber
  actor M as Maintainer
  participant GH as GitHub (issue, PR, ledger)
  participant G as gate (code)
  participant B as build: state machine
  participant A as Analyst (flash-lite)
  participant Bu as Builder (flash-lite)
  participant T as Tester (flash-lite)
  participant S as ship_0 (code)
  participant R as review_1 (fresh VM, 3-flash-preview)
  participant F as finalize (code)

  M->>GH: 15:57:3x add label "autose" to issue #2
  GH->>G: issues.labeled
  G->>GH: 15:57:39 check sender permission (write) · post run ledger · upload artifact "issue"
  G->>B: 15:57:44 needs: gate (contents:read, no token to agents)
  B->>A: issue in <untrusted_issue> tags
  A-->>B: spec.md
  Note over B: 15:58:35 gate PASS: 2 testable ACs
  B->>A: spec.md + ARCHITECTURE.md
  A-->>B: design.md
  Note over B: 15:59:04 gate PASS: CachingMiddleware.flush exists (AST)
  B->>Bu: spec + design + source of CachingMiddleware.flush (no issue text)
  Bu-->>B: edit tinydb/middlewares.py (sandbox, --network none)
  Note over B: 16:00:11 gate PASS: compileall, import, mypy
  B->>T: spec.md only
  T-->>B: tests/autose/test_issue_2.py
  Note over B: 16:02:12 gate PASS: AC-1 red on base, green on head · AC-2 [regression-only] · 229 passed
  B->>S: artifact work-0 (16:02:15)
  S->>GH: 16:02:36 push autose/issue-2 · open PR #12 (pr.md template) · pytest+mypy · status autose/ci=success
  S->>R: needs: ship_0 (16:02:47)
  R->>R: downloads ONLY "issue" · restores .autose from master · computes git diff itself
  R--xR: 16:20:44 model quota exhausted (old fallback chain) · job fails
  R->>F: finalize (16:20:51) ledger: "stop: review_1 failed, a maintainer decides"
  Note over R: attempt 2 (Re-run failed jobs), harness from master with the quota fix
  R->>R: 16:22:57 review: 5 sandboxed commands (pytest + probes in /scratch)
  R->>GH: 16:23:51 post review on PR #12: verdict approve
  R->>F: 16:24:00 finalize
  F->>GH: ledger "final: reviewer approved; awaiting a maintainer's merge decision"
  Note over M,GH: The workflow never merges. A human decides.
```

Durations: gate 8 s · build 4 min 31 s (requirements 51 s, design 29 s, implementation 67 s, testing 2 min 1 s) ·
ship_0 28 s · review_1 attempt 2: 60 s · finalize 7 s.
