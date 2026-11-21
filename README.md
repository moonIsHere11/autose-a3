# AutoSE A3: An Agentic SDLC Workflow (issue in, reviewed PR out)

| | |
|---|---|
| **Fork (where the workflow runs)** | https://github.com/moonIsHere11/tinydb-autose |
| **Upstream + pinned commit** | `msiemens/tinydb` @ **`edff96a`** (`edff96aeb2616402e9489d46e90a592c05565621`) |
| **Experiment seeding commit** | `8f8e5e9` on the fork: re-injects the two A2 bugs used by issues #1 and #2 (documented in `experiment/`) |
| **Workflow** | [`.github/workflows/autose.yml`](https://github.com/moonIsHere11/tinydb-autose/blob/master/.github/workflows/autose.yml) (copy in `workflow/`) |
| **Models** | Workers (Analyst, Builder, Tester): `gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` → `gemma-4-31b-it` fallback. Reviewer: `gemini-3-flash-preview` → `gemini-3.5-flash`. See ADR-006 (superseded) and ADR-011. |
| **Cost** | Free-tier Gemini API key with billing disabled = hard $0 cap. Token totals in `results/runs.md`. |
| **Report / demo** | [`report.pdf`](report.pdf) · demo video: **DEMO_LINK_TODO** |

## How to trigger
A user with write access to the fork either
- adds the label **`autose`** to an issue → full pipeline (spec → design → code → tests → PR → independent review, ≤2 review rounds), or
- comments **`/autose`** on an issue (same), or **`/autose review`** on an open PR → independent review only
  (`/autose review naive` runs the experiment's naive reviewer variant).

Progress is visible in a single **run ledger** comment on the issue, the Actions run (job summaries + artifacts
`spec.md`, `design.md`, `diff.patch`, `test_report.md`, `pr.md`, `review.md`, transcripts, `usage.json`), the PR,
and the review posted on the PR. The workflow **never merges**.

## Design in one paragraph
Agents are **capability profiles**, not stages: a read-only **Analyst** (stages 1-2, the only worker that reads
the raw issue), a **Builder** that can only write `tinydb/` and never sees the issue, a **Tester** that can
only write `tests/autose/`, and an **independent Reviewer** in its own job, on a different model, that sees only
the issue, the diff and the repository at the PR head. **Release is not an agent**: a deterministic script is the
only code holding a write token. Every agent command runs in `docker --network none` with no credentials.
Control flow is a code state machine inside an **unrolled, bounded Actions DAG**
(`gate → build → ship_0 → review_1 → rework_1 → ship_1 → review_2 → finalize`), so the two-round review limit
and the reviewer's fresh context are structural. Every stage check is code; the testing check is
**red/green**: each acceptance criterion's test must fail on the base commit and pass on the head.

## Results at a glance
- **7 pipeline runs + 13 review-only runs**, all real and linked in [`results/runs.md`](results/runs.md).
- 4/5 issues produced a PR. **Hidden acceptance tests 16/16** on those PRs. The vague issue (I5) **stopped
  correctly** before release: its request contradicts an existing test that pins documented behaviour.
- The full DAG (review → rework → second review) ran for real on issue #1.
- **E1 (reviewer independence):** the full reviewer identified 3/4 seeded defects. The naive reviewer identified 0/4
  and approved a PR whose own branch fails the existing suite. Both approved the correct control PR.
- **E2 (red/green gate):** a negative result. It never fired in live runs. The one vacuous test came in through its
  `[regression-only]` exemption.
- ADRs changed by evidence: ADR-006 → **ADR-011** (models), ADR-008 → **ADR-012** (grounded evidence), and
  amendments to ADR-003 and ADR-004.

## Repository layout
```
README.md                 this file
report.pdf                the report (≤ 8 pages + appendices)
architecture/views/       component view, sequence view (real run), stage map
architecture/decisions/   ADR-001 … ADR-011 (ADR-006 superseded by ADR-011), index in README.md
workflow/                 copy of .github/workflows/ + .autose/ (harness, prompts, sandbox) from the fork
experiment/issues/        the 5 issue texts (2 bugs, 2 features, 1 vague)
experiment/hidden_tests/  hidden acceptance tests (never in the fork)
experiment/seeded_prs/    5 reviewer-check PRs: diffs + labels.csv (ground truth)
experiment/variants.md    what each decision-experiment variant changes
results/results.csv       one row per real run
results/runs.md           links to every Actions run, PR and review
results/collect.py        regenerates the two files above from GitHub
```

## AI use
This assignment was built with substantial help from Claude Code (Claude Opus 5.5): it drafted the ADRs and
views from design decisions discussed with me, wrote the harness/workflow code, and the collection script.
I reviewed the generated material. All runs, PRs and reviews linked in `results/runs.md` are real
GitHub Actions executions on the fork.
