# Component view

Target: fork of `msiemens/tinydb` pinned at `edff96a` (https://github.com/moonIsHere11/tinydb-autose). The workflow
`.github/workflows/autose.yml` and the harness under `.autose/` live on the fork's default branch `master`.
Hidden acceptance tests never live in the fork.

```mermaid
flowchart TB
  subgraph GH[GitHub: fork]
    ISSUE[Issue / PR comment<br/>label 'autose' or '/autose']
    BR[branch autose/issue-N]
    PR[Pull request]
    LEDGER[Run ledger comment<br/>on the issue]
    ART[(Actions artifacts<br/>spec.md design.md diff.patch<br/>test_report.md pr.md review.md<br/>transcript.jsonl usage.json)]
  end

  subgraph WF[autose.yml: one workflow, unrolled bounded DAG]
    GATE[gate<br/>deterministic: who, what, which mode]
    BUILD[build job<br/>state machine: stages 1-4]
    SHIP0[ship_0<br/>deterministic release + CI]
    REV1[review_1<br/>separate VM]
    RW1[rework_1<br/>if changes requested]
    SHIP1[ship_1]
    REV2[review_2<br/>separate VM]
    FIN[finalize<br/>posts 'human decides']
    GATE --> BUILD --> SHIP0 --> REV1 --> RW1 --> SHIP1 --> REV2 --> FIN
    REV1 -. approve .-> FIN
  end

  subgraph H[Harness process: holds GEMINI_API_KEY, never a GitHub token]
    SM[State machine + gates<br/>code decides every transition]
    AN[Analyst<br/>stages 1-2<br/>list / read / grep]
    BU[Builder<br/>stage 3<br/>+ write tinydb/ + run]
    TE[Tester<br/>stage 4<br/>+ write tests/autose/ + run]
    RV[Reviewer<br/>stage 6<br/>list / read / grep / run]
  end

  SB[[Sandbox: docker run --network none<br/>no key, no token, cpu/mem/pid limits, 150 s<br/>repo rw (builder/tester) or ro (reviewer), /scratch]]
  GEM[(Gemini API<br/>workers: gemini-3.5-flash-lite (Gemma 4 fallback)<br/>reviewer: gemini-3-flash-preview)]

  ISSUE --> GATE
  BUILD --> SM
  RW1 --> SM
  SM --> AN & BU & TE
  REV1 --> RV
  REV2 --> RV
  AN & BU & TE & RV -->|LLM calls| GEM
  BU & TE & RV -->|run tool| SB
  SHIP0 & SHIP1 -->|gh / REST: push, open PR| BR & PR
  REV1 & REV2 -->|harness posts review| PR
  GATE & SHIP0 & FIN -->|update| LEDGER
  BUILD & SHIP0 & REV1 & REV2 -->|upload / download by name| ART
```

Legend: rectangles in `WF` are Actions jobs. Rectangles in `H` are LLM roles; each role is a
capability profile (tool allowlist + write scope + inputs), not a stage. `gate`, `ship_*` and
`finalize` contain no LLM. Solid arrows are calls; the dotted arrow is the early exit when
review 1 approves.

## Permission matrix

| Job | GITHUB_TOKEN permissions | LLM role(s) | Agent tools | Write scope | Sees raw issue |
|---|---|---|---|---|---|
| gate | contents: read, issues: write, pull-requests: read | none | none | none | parses it (code only) |
| build | contents: read | Analyst, Builder, Tester | Analyst: list, read, grep, finish. Builder/Tester: + write, replace, run | Builder: `tinydb/`. Tester: `tests/autose/` | Analyst only |
| ship_0 / ship_1 | contents: write, pull-requests: write, issues: write, statuses: write | none | none | branch `autose/issue-N` | no |
| review_1 / review_2 | contents: read, pull-requests: write, issues: write (harness posts after agent exits) | Reviewer | list, read, grep, run (repo mounted read-only, persistent `/scratch`) | none | yes (plus diff + repo at PR head) |
| rework_1 | contents: read | Analyst (approach) or Builder (code), then Tester | as in build | as in build | Analyst only |
| finalize | contents: read, issues: write | none | none | none | no |

Workflow-level `permissions: {}`. Agent jobs check out with `persist-credentials: false`.
No job has a merge path. The reviewer job overwrites `.autose/` with the default branch's copy before running, so a PR under review cannot change the reviewer's own prompt or harness.
