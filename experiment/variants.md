# Decision experiments: what each variant changes

Two ADRs are tested. Each experiment changes exactly one decision and keeps everything else
(fork commit, issues, models for the other roles, budgets) fixed.

## E1: tests ADR-008 (reviewer independence)

**Question:** does the independence machinery (different model, withheld author reasoning, mandate
to break the change, evidence gate) actually make the reviewer catch more defects, or would a plain
"please review this PR" reviewer do as well?

**Subjects:** the 5 seeded PRs (#6-#10, `seeded_prs/`), ground truth in `seeded_prs/labels.csv`:
4 defective (1 approach-level, 3 code-level, from obvious to subtle) and 1 correct control (S4).
Ground truth was established by running the hidden tests and the existing suite on each branch.

| | **Full reviewer** (`/autose review`) | **Naive reviewer** (`/autose review naive`) |
|---|---|---|
| Model | `gemini-3-flash-preview` (differs from workers) | `gemini-3.5-flash-lite` (the workers' model) |
| Inputs | issue + diff + repo at PR head | issue's PR description written by the author (rationale + "all tests pass") + diff + repo |
| Prompt | `reviewer.md`: assume a defect exists, write probe scripts, categorise approach/code | `reviewer_naive.md`: "review this PR, decide if it can be approved" |
| Evidence gate | approval refused until ≥1 command executed; findings without evidence dropped | none |
| Tools / sandbox | identical (read, list, grep, run in `--network none`, repo read-only) | identical |

**Metrics:** defects caught (changes_requested on a defective PR, with a finding that names the real
defect), false rejections (changes_requested on S4), correct category (approach vs code), commands
executed, tokens.

**Prediction written before running:** the full reviewer catches more of S1 (approach) and S5 (subtle
nested-copy), the naive reviewer approves at least one defective PR on the author's word ("all tests pass").

## E2: tests ADR-007 (code-decided checks, red/green test gate)

**Question:** does requiring every acceptance-criterion test to **fail on the base commit** (red) as well as
pass on the head (green) change what the pipeline accepts, compared with the usual "new tests pass" gate?

| | **Red/green gate** (deployed) | **Green-only gate** (counterfactual) |
|---|---|---|
| Accepts a test suite when | every AC has a test, each non-regression AC has ≥1 test failing on base, all pass on head, full suite green | every AC has a test, all pass on head, full suite green |

**Method:** every testing-stage evaluation in every pipeline run is logged (`events.json`, `test_report.md`
with the per-test base/head table). We replay each evaluation under both gate variants from these logged
outcomes, so both variants see exactly the same tests. For each evaluation where the variants disagree,
we check whether the tests would have caught the bug, by running the hidden acceptance tests
against the head.

**Metrics:** number of test suites accepted by green-only but rejected by red/green (vacuous suites),
extra tester attempts the red/green gate cost, and whether runs accepted by red/green pass the
hidden tests more often.

**Why a replay and not two live pipelines:** the free-tier quota does not allow running every issue
twice, and a live re-run would also change the LLM outputs, which would confound the comparison.
The replay isolates the decision (the gate policy) from model sampling noise. Limitation: under
green-only, a run would have stopped iterating earlier, so later stages would have seen different
inputs. We report this as a threat to validity.
