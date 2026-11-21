---
title: "AutoSE A3: Architecting an Agentic SDLC Workflow"
subtitle: "Issue in, independently reviewed pull request out, on a tinydb fork"
author: "Mohit Sriram (2024101101)"
date: "21 November 2026"
geometry: "a4paper,margin=1.7cm"
fontsize: 10pt
colorlinks: true
header-includes:
  - \usepackage{booktabs}
  - \usepackage{float}
  - \floatplacement{figure}{H}
  - \setlength{\parskip}{3pt}
  - \renewcommand{\arraystretch}{1.05}
---

**Fork:** <https://github.com/moonIsHere11/tinydb-autose> (tinydb @ `edff96a`, plus documented bug-seeding commit `8f8e5e9`).
**Submission repo:** <https://github.com/moonIsHere11/autose-a3>. **Every run cited here is linked in `results/runs.md`.**

**Thesis.** Two ideas shape the design. (1) *Agents are capability profiles, not stages.* An agent boundary is
drawn where what a component may **see** or **do** changes: who reads untrusted text, who can write which paths, who
holds which credential. (2) *The harness is the judge.* No model certifies its own stage: every check is code, and
the testing check is **red/green**, so a test counts only if it fails on the old code and passes on the new.

# 1 Architecture

![Component view. Top: the single workflow as an unrolled, bounded job DAG with each job's token scope. Right: the four LLM roles inside the harness process, the code gates, the network-less sandbox every agent command runs in, and GitHub. Only code-only jobs (blue) hold write tokens.](component.pdf){width=100%}

Table: Stage map: agent, artifact and the code check per stage (full version with inputs and withheld inputs in `architecture/views/stage-map.md`).

| # | Stage | Agent / component (model) | Artifact | Check, decided by code | On failure |
|---|---|------|---|--------|------|
| 1 | Requirements | Analyst (flash-lite) | `spec.md` | parses; 1-6 `AC-n`, each Given/When/Then; fuzzy-word lint on *Then* | retry with gate feedback (2x), then stop |
| 2 | Design | Analyst (flash-lite) | `design.md` | Changes table; every MODIFY `file::Class.method` exists per AST | retry (2x), then stop |
| 3 | Implementation | Builder (flash-lite) | `diff.patch` | diff touches only `tinydb/`; compileall, import, `mypy` in sandbox | retry within budget of 3 |
| 4 | Testing | Tester (flash-lite) | `test_report.md` | each AC has `test_acN_*`; **red on base, green on head**; full suite green | test fault: Tester rewrites; code fault: back to 3; 3 fails: back to 2 once; then stop |
| 5 | Release | `ship_*` script (no LLM) | `pr.md` + PR link | PR open; pytest + mypy on PR head = commit status `autose/ci` | stop, reason in ledger |
| 6 | Review | Reviewer (3-flash-preview) | `review.md` | approval needs executed commands; findings need evidence | approach: back to 2; code: back to 3; max 2 rounds; human decides |

**Which agent handles which stage.** The *Analyst* runs stages 1 and 2 (two invocations with different prompts,
same read-only profile). It is the only worker that reads the raw issue. The *Builder* runs stage 3: it can write only
under `tinydb/`, never sees the issue, and receives the spec, the design and the harness-extracted source of the
symbols the design names. The *Tester* runs stage 4: it can write only `tests/autose/` and writes tests from the spec.
Stage 5 is **not an agent**: `ship_*` is a script that applies the patch, pushes `autose/issue-N`, opens the PR from
a template (no agent prose), runs CI (pytest + mypy) itself, because pushes made with `GITHUB_TOKEN` trigger no other
workflow, and posts the commit status `autose/ci`. The *Reviewer* runs stage 6 in its own job on a fresh VM with a
different model. The back-edges (test failure to implementation, exhausted implementation to design, review
`approach` to design, review `code` to implementation) are decided by the state machine, never by a model.

**Sequence view: one real run, trigger to review** (issue #2, [run 44921915844](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921915844), [PR #12](https://github.com/moonIsHere11/tinydb-autose/pull/12); times UTC from the Actions API and `events.json`; mermaid version in `architecture/views/sequence.md`).

| t (UTC) | from -> to | message / effect |
|---|---|---|
| 15:57:3x | maintainer -> GitHub | adds label `autose` to issue #2 |
| 15:57:39 | `gate` -> GitHub | sender permission = write (ok); ledger comment posted; artifact `issue` uploaded |
| 15:58:35 | `build`: Analyst -> gate | `spec.md`, 2 ACs, Given/When/Then (ok) (issue text was seen only here, in `<untrusted_issue>` tags) |
| 15:59:04 | Analyst -> gate | `design.md`: `tinydb/middlewares.py::CachingMiddleware.flush` exists per AST (ok) |
| 16:00:11 | Builder -> sandbox -> gate | gets spec + design + `flush` source, no issue; one edit; compileall + import + mypy (ok) |
| 16:02:12 | Tester -> sandbox -> gate | `test_issue_2.py`; AC-1 **red on base, green on head**; AC-2 `[regression-only]`; 229 passed (ok) |
| 16:02:36 | `ship_0` -> GitHub | push `autose/issue-2`, open PR #12 from template, pytest + mypy on head, status `autose/ci` = success |
| 16:02:47-16:20:44 | `review_1` (attempt 1) | downloads **only** `issue`; model quota errors exhausted the old fallback chain -> job failed; `finalize` logged the stop |
| 16:22:57 | `review_1` (attempt 2, re-run failed jobs) | fresh VM, harness from master; 5 sandboxed commands (pytest + probes) |
| 16:23:51 | Reviewer -> GitHub | review posted on PR #12: **approve** |
| 16:24:07 | `finalize` -> GitHub | ledger: "reviewer approved; awaiting a maintainer's merge decision". Nothing is merged. |

# 2 Design decisions

Table: All ADRs (full text in `architecture/decisions/`).

| ADR | Decision | Chosen | Main option rejected | Main reason | Status |
|---|------|--------|-------|-------|---|
| 001 | D1 Splitting the work | 4 capability profiles (Analyst, Builder, Tester, Reviewer); Release is a script | One agent per stage | Boundaries where permissions change, not where stages change | Accepted |
| 002 | D2 Control flow | Code state machine inside an unrolled, bounded Actions DAG | LLM orchestrator | Loop bound and fresh reviewer context guaranteed by structure | Accepted |
| 003 | D3 Hand-offs | Named, gate-checked artifacts per role; raw issue withheld from Builder/Tester, spec/design withheld from Reviewer | Shared full transcript | Injection quarantine and reviewer independence | Accepted |
| 004 | D4 State | Per-job Actions artifacts + one run-ledger issue comment; branch carries only code | Artifacts committed to the PR branch | Reviewer would read the reasoning; restart reuses Actions re-run | Accepted |
| 005 | D5 Tools | Own harness, per-role allowlists, `docker --network none` sandbox, gh/REST only in deterministic steps | GitHub MCP server for agents | The LLM never needs GitHub or a credential | Accepted |
| 006 | D6 Models | gemma-4-31b-it workers, gemini-3-flash-preview reviewer | Same model for all roles | Uncorrelated reviewer errors within a free-tier budget | Superseded by 011 |
| 007 | D7 Checks | Code-decided gates; red-on-base / green-on-head tests | LLM judge per stage | Vacuous tests and self-certification are rejected mechanically | Accepted |
| 008 | D8 Reviewer independence | Separate job + different model + withheld artifacts + evidence gate | Same job with a new prompt | Independence of process, inputs, model, permissions and incentive | Accepted |
| 009 | D9 Safety and failures | Quarantine, no credentials in sandbox, budgets, structural bounds | Prompt-only defence | Injection can at worst produce a bad diff on a branch | Accepted |
| 010 | D10 Triggers | Label or `/autose` by write-permission users; per-issue queued concurrency | `issues: opened` for everyone | Only people who could push can spend the budget | Accepted |
| 011 | D6 Models (revised) | gemini-3.5-flash-lite workers (Gemma fallback), gemini-3-flash-preview reviewer | Keep Gemma workers with longer timeouts | Measured 503s and ~20 s/call made runs infeasible | Accepted |
| 012 | D8/D7 Evidence gate (revised) | Evidence must match executed output or a real file:line; verdict + evidence enforced in-loop | Non-empty evidence text, checked after finish | E1: hollow evidence on S5, missing verdict on S3 | Accepted |

**Decision 1: split by trust boundary, and put a sandbox under every agent (ADR-001, ADR-005, ADR-009).**
The obvious splits are one agent for everything (one context that reads attacker text *and* holds write tools)
or one agent per stage (six prompts, but stages 1 and 2 need exactly the same permissions and inputs, so the extra
boundary buys nothing). Instead I asked *at which points does what a component may see or do change?* That gives
four profiles plus code. The raw issue, the only attacker-controlled input, reaches the read-only Analyst and the
no-push Reviewer. The agent that can edit code only ever sees the gate-checked spec, a dual-LLM-style quarantine.
On top of that, every `run` command executes in `docker run --network none` with an empty environment, so even a
fully hijacked agent has no API key, no GitHub token and no network: the worst it can do is write a bad diff in its
own path scope. That diff then still has to pass code gates and an independent review, and a human merges. The
LLM never touches GitHub, which is also why I rejected the GitHub MCP server: it would hand the model a
credential-bearing tool it never needs. Cost: I had to write my own small harness (Gemini models have no
`--allowedTools`-style sandbox), and every command pays a container start-up (~0.5 s).

**Decision 2: the testing check is red/green, decided by code (ADR-007).** "New tests pass" is the usual check, and
it is the weakest point of an agentic pipeline: the same system that writes the code can write tests that cannot
fail (asserting the bug, testing an unrelated path, `assert True`). The harness runs the Tester's file twice: against
the base commit (each acceptance criterion needs at least one *failing* test there, and a collection error from a
missing API counts as red) and against the head (all must pass), then runs the full suite. ACs that only guard existing
behaviour are tagged `[regression-only]` in the spec and are exempt from red. This turns "all acceptance criteria are
testable" into something checked mechanically rather than by prompting. It costs one extra sandboxed pytest run per
evaluation, and occasionally an extra Tester attempt. E2 below measures what it actually rejected.

**Decision 3: an unrolled, bounded job DAG with an independent reviewer (ADR-002, ADR-008).** The review loop is
bounded at two rounds, so I unrolled it into jobs instead of looping: `review_1 -> rework_1 -> ship_1 -> review_2`.
Each review is a separate job on a separate VM, so the reviewer's fresh context and the two-round bound are
properties of the YAML, not of a counter an LLM could get around. GitHub constraints point the same way: Actions
has no cycles, and events created with `GITHUB_TOKEN` do not start new workflow runs, so a self-re-triggering design
would need a PAT (a stronger credential). The reviewer job downloads **only** the `issue` artifact, never `work-*`, so
spec, design and transcripts are physically absent from its VM. It computes the diff itself from git, gets a different
model and an adversarial prompt, and must pass an **evidence gate**: an approval is refused until it has executed
at least one command, and findings without evidence are dropped. The harness and prompts are restored from the
default branch before review, so a PR under review cannot rewrite its own reviewer. Cost: the DAG has eight jobs with
repeated set-up (~40 s each), and a third review round is impossible by construction, which is the point.

# 3 Decision experiments

Variant definitions are in `experiment/variants.md` and were written before running. Ground truth for seeded PRs comes
from `experiment/seeded_prs/labels.csv` (hidden tests plus existing suite on each branch).

**E1: ADR-008, reviewer independence.** Five seeded PRs, each reviewed by the *full* reviewer (different model,
issue + diff + repo only, adversarial prompt, evidence gate) and by a *naive* reviewer (workers' model, sees the
author's PR description "...all existing tests pass", plain "review this PR" prompt, no evidence gate). Same tools and
sandbox. A defect counts as *identified* only if a finding names the actual defect.

| PR (truth) | Full reviewer | Naive reviewer |
|---|---|---|
| S1 #6 (approach: OR made non-cacheable) | approve, 3 cmds: **missed** | approve: **missed** |
| S2 #7 (code: counter reset before flush, data loss) | changes requested, exact defect, probe evidence (3 cmds) | approve with **0 commands** (existing suite fails 2 tests on this branch) |
| S3 #8 (code: exclusive bounds) | exact defect with probe (6 cmds), but **no `verdict:` line** -> `invalid` | changes requested for the **wrong reason** ("missing unit tests") |
| S4 #9 (correct control) | approve (3 cmds); first attempt approved with 0 cmds -> rejected by gate | approve |
| S5 #10 (code: shallow copy, nested leak) | changes requested, exact defect, but evidence **hollow** (only ran pytest) | approve (ran pytest) |
| **Defects identified** | **3/4** (2/4 with a valid verdict) | **0/4** |
| False rejections (S4) | 0/1 | 0/1 |
| Mean commands executed | 3.2 | 0.4 |

*Re-test of S5 under ADR-012* ([run 44924483558](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44924483558)):
the primary reviewer model was rate-limited at that moment, so **every call was served by the fallback
`gemini-flash-lite-latest`** (logged in `usage.json`). It ran 7 commands, but its probes only mutated top-level keys,
and it **approved**, missing the nested-copy defect that the primary model had found. ADR-012's gate behaved correctly
(nothing ungrounded was kept), but the outcome was decided by the *model*. That is a confound for ADR-012, and
direct evidence for ADR-011's claim that reviewer strength, not just reviewer independence, is what catches subtle
defects.

*Reading.* Independence plus the adversarial mandate made the difference between finding defects and rubber-stamping:
the naive reviewer approved a PR whose own branch fails the existing suite, on the author's word that "all existing
tests pass". The prediction in `variants.md` was half right. The full reviewer did catch the subtle S5, but it **missed
the approach-level S1**, as did everything else in the pipeline: a functionally correct change that quietly
disables the query cache passes every behavioural test and every probe, and only the hidden `test_cache_still_used`
catches it. E1 also showed the evidence gate to be **weaker than ADR-008 claimed**: it checked the *form* of the
evidence after the fact. **Design changes:** (1) during E1, the gate moved inside the loop (a `finish` that approves
with zero commands is refused); (2) after E1, ADR-012: evidence must be grounded (match executed output or a real
`file:line`), and a missing verdict is refused in-loop.

**E2: ADR-007, red/green vs green-only test gate.** Replay of every logged testing evaluation (first build of each
issue: 5 builds, 12 evaluations) under both policies, plus a mutation check: each pipeline-written test file is run against the seeded
*wrong* fix for the same issue.

| | Red/green (deployed) | Green-only (replayed) |
|---|---|---|
| evaluations accepted / rejected | 4 / 8 | 4 / 8 (identical decisions) |
| rejections by cause | head failures 7 (6 = I5 contract conflict), file not written 1; **vacuous 0** | same |
| `[regression-only]` exemptions used | 2 (I2 AC-2, I4 AC-2) | n/a |
| ...of which actually vacuous | **1 (I2 AC-2)**: new behaviour, passes on base only because `WRITE_CACHE_SIZE=10` hides it | accepted too |

| Pipeline tests run against ... | S1 (wrong fix for I1) | S2 (wrong fix for I2) | S3 (wrong fix for I3) |
|---|---|---|---|
| result | 2/2 pass: **does not catch** | 1 fails: catches | 2 fail: catches |

*Reading (a negative result).* In live runs, the red/green rule **never fired**: every Tester suite already failed on
base, so green-only would have decided identically. The only vacuous test that got through came in through the
**escape hatch I added to avoid false rejections**: the Analyst tagged new behaviour `[regression-only]`. Red/green is
cheap insurance (one extra sandboxed pytest run per evaluation), but on these tasks it bought nothing measurable, and
its exemption became the weak point. **Design change (ADR-007 consequence, not yet implemented):** the harness, not
the Analyst, should grant `[regression-only]`. Grant it only when the AC's test also passes on base *and* the AC cites
an existing test or documented behaviour, and have the reviewer see which ACs were exempted.

# 4 Results

Seven pipeline runs (one per issue, plus fresh `/autose` re-runs of I1 and I3 after harness fixes) and 13 review-only
runs, all on GitHub Actions. Per-run data is in `results/results.csv`, with links in `results/runs.md`.

**Pass rate per stage** (first run of each of the 5 issues; *first try* = passed on the first attempt):

| Stage | Passed within budget | First try | What the code check caught |
|---|---|---|---|
| 1 Requirements | 5/5 | 4/5 | I3: fuzzy word "correctly" in a *Then* clause; Analyst rewrote it |
| 2 Design | 5/5 | 4/5 | I5: Changes table named a non-existent symbol `(module)` |
| 3 Implementation | 5/5 | 5/5 | (each attempt compiled, imported and type-checked) |
| 4 Testing | **4/5** | 2/5 | I3: 3 AC tests red on head, so back to Builder (fixed); I4: test file not written, Tester redone; **I5: stopped**, see below |
| 5 Release | 4/4 | 4/4 | PR opened, pytest + mypy on head green, status `autose/ci` posted |
| 6 Review | 4/4 approved | 3/4 | I1 (fresh run) took both rounds: review 1 requested changes, rework re-entered at *implementation*, review 2 approved |

**Hidden acceptance tests on the final PR branches: I1 4/4, I2 4/4, I3 4/4, I4 4/4, so 16/16.** I5 produced no PR.
It stopped correctly: its spec asks for behaviour that an existing test (`test_query_cache_documents_are_shared_with_cache`)
pins as documented contract, so no implementation could pass the full suite. The stop reason in `test_report.md`
quotes that test. The hidden I5 tests encode my reading of a vague issue, which the maintainers' own test contradicts.
Stopping and handing the contract question to a human is the right outcome, reached at a cost of 6 Builder
attempts (see Hindsight).

**What the reviewer caught, and where it was wrong.** On the seeded PRs (E1), the full reviewer identified 3 of 4
defects. It missed the approach-level S1 and never rejected the correct S4. In the pipeline, all four PRs were correct
(hidden tests 16/16), so every `changes_requested` there was a **false positive**: twice on I1. (a) Run 44921520773:
"`frozenset` removes duplicate sub-query hashes", a property of code the PR did not touch. (b) Fresh run: a reviewer
running on the *degraded* fallback model claimed `__or__` "still uses 'and'" at `queries.py:131`, reading the diff's
removed line as current code. That citation passed ADR-012's grounding because line 131 exists: **grounding checks
that a citation exists, not that it is true.** In (a) the rework then crashed on the restart bug. In (b) the rework Builder
made no substantive change and review 2 approved. The bound of two rounds is what kept false positives cheap.

**Reliability and cost.** 13 jobs failed: 11 reviewer jobs crashed on provider errors: free-tier 503 "high demand", per-minute 429s under
concurrency, and a **20 requests/day cap** on most Flash models, discovered mid-run. The other 2 (`rework_1` and the dependent `ship_1`) were the stale-artifact restart bug
(ADR-004 amendment). Every affected issue was recovered by
*Re-run failed jobs* or a fresh trigger after a harness fix (ADR-011, ADR-004 amendment). Wall time per build job:
3.6 to 11.6 min. Total: **1.74 M tokens (1.58 M in, 0.16 M out) over 20 Actions runs**, at $0 (free tier, no billing),
plus local development smoke runs not counted here.

# 5 Hindsight

**I would change D2/D7 first: add a "contract conflict" check before implementation.** The state machine treats
every red full suite after an implementation as *the Builder's fault* and sends work back to stage 3. Issue I5 showed
the flaw. The vague issue asks for behaviour that an **existing test deliberately forbids**
(`test_query_cache_documents_are_shared_with_cache` pins "documents are shared with the cache"). The new AC tests
passed on every attempt. Only that contract test failed, and no implementation can satisfy both. The pipeline did the
*right* final thing: it stopped before release and wrote the conflicting test into `test_report.md`. But it spent
6 Builder attempts and one redesign (~10 minutes and a large share of the run's tokens) getting there.
The fix is cheap and belongs in code, not in a prompt. After the design stage, run the existing tests that exercise
the symbols in the design's Changes table against a *spec probe*, or simply classify a failure as a **contract
conflict** when every new AC test passes and only pre-existing tests fail. Then route it straight to a human
("the spec contradicts an existing test: change the contract?") instead of to the Builder. I did not anticipate
this because I had modelled back-edges as *code fault -> implementation, approach fault -> design*. I5 shows a third
kind of fault, *requirements versus contract*, which only a human can resolve, and a principled SDLC pipeline needs
an explicit edge for it.

Second on the list: ADR-006/011. I chose models on capability and independence, but on a free tier the binding
constraint was **availability and daily quota** (20 requests per day for the Flash models). I would design the model
layer as a budgeted resource from the start: a per-role quota ledger and a reviewer that is never more than one
fallback away from a model with a different daily pool.

# 6 Limitations and threats to validity

1. **Tiny samples, one run each.** Five issues, five seeded PRs, and in general one pipeline run per issue. LLM
   outputs vary between runs (temperature 0.2, plus model fallbacks), so a pass or fail on one issue is an
   anecdote, not a rate. The E1 comparison (5 PRs x 2 variants) can show large effects at best; differences of one PR
   are within noise.
2. **The person who wrote the defects also wrote the reviewer prompt.** The reviewer prompt suggests probing
   "nested fields, middleware, persistence, repeated/cached queries", and those overlap with the seeded defect
   classes (S2 middleware, S5 nested copy). The full reviewer may look better in E1 partly because of that, not
   only because of independence. A fair test needs defects written by someone who has not seen the prompt.
3. **Synthetic, small tasks on a well-known library.** Two of the bugs are one-line defects re-injected from A2,
   and tinydb is probably in the models' training data. Real issues are larger and less clean. The hidden tests
   were written by the same person as the issues, so they encode one reading of each issue, which matters most for
   the vague issue (I5).
4. **Infrastructure noise is mixed into the results.** Free-tier 503 "high demand" and 429 quota errors crashed
   some jobs, which were then restarted with *Re-run failed jobs* after harness fixes. Some calls were served by
   fallback models. All of this is visible in the run links and `usage.json`, but it means some "stage failed"
   outcomes are about availability rather than the design.
5. **E2 is a replay, not a live A/B.** Replaying logged test outcomes under the green-only policy isolates the gate
   policy from sampling noise, but under green-only the pipeline would have stopped iterating earlier and later
   stages would have seen different inputs.
6. **Isolation is enforced by the harness, not by the model provider.** The reviewer is denied spec and design
   because they never reach its VM, and agents have no network or credentials. But text can still flow through
   allowed channels: an injection in the issue can shape the spec the Builder reads, and the reviewer reads the raw
   issue too. The quarantine limits the *capability* of an injected instruction, not its *influence*.

\newpage

# Appendix A: Runs

Every row links to a real GitHub Actions run on the fork. Generated by `results/collect.py`.

Notes: *stages* are the build job's code checks (requ/desi/impl/test); *review verdicts* come from the newest
attempt's `review.json`; *hidden tests* are run against the PR branch head **at collection time**. For issues 1 and 3
that head was produced by the later fresh run (`/autose` comment), because both reuse branch `autose/issue-N` and PR.
A run's *conclusion* is `failure` when any job failed, including the provider-quota crashes that were then
restarted with *Re-run failed jobs* (attempts are visible on each run page). Seeded PRs: #6 S1, #7 S2, #8 S3,
#9 S4 (correct control), #10 S5; labels in `experiment/seeded_prs/labels.csv`.

| run | trigger | subject | stages | review verdicts | PR | hidden tests | tokens (in/out) | conclusion |
|---|---|---|---|---|---|---|---|---|
| [44921313683](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921313683) | issue_comment | Fix OR query cache key | review-only | invalid (full) | [#9](https://github.com/moonIsHere11/tinydb-autose/pull/9) | - | 24432/12383 | success |
| [44921495443](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921495443) | issue_comment | Fix OR query cache key | review-only | approve (full) | [#9](https://github.com/moonIsHere11/tinydb-autose/pull/9) | - | 110086/34910 | success |
| [44921520773](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921520773) | issues | Wrong results when I run an OR query after an AND  | requ(ok) desi(ok) impl(ok) test(ok) | changes_requested (full) | [#11](https://github.com/moonIsHere11/tinydb-autose/pull/11) | 4 passed | 46244/3162 | failure |
| [44921822505](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921822505) | issue_comment | Fix wrong results for OR queries after AND queries | review-only | approve (full) | [#6](https://github.com/moonIsHere11/tinydb-autose/pull/6) | - | 20556/1324 | success |
| [44921824353](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921824353) | issue_comment | Fix CachingMiddleware flushing on every write | review-only | changes_requested (full) | [#7](https://github.com/moonIsHere11/tinydb-autose/pull/7) | - | 26386/26279 | success |
| [44921826021](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921826021) | issue_comment | Add Query.between() range test | review-only | invalid (full) | [#8](https://github.com/moonIsHere11/tinydb-autose/pull/8) | - | 12277/661 | success |
| [44921827020](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921827020) | issue_comment | Fix OR query cache key | review-only | -  | [#9](https://github.com/moonIsHere11/tinydb-autose/pull/9) | - | 0/0 | failure |
| [44921828940](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921828940) | issue_comment | Return copies from search() so callers cannot corr | review-only | changes_requested (full) | [#10](https://github.com/moonIsHere11/tinydb-autose/pull/10) | - | 32168/17959 | success |
| [44921862212](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921862212) | issue_comment | Fix wrong results for OR queries after AND queries | review-only | approve (naive) | [#6](https://github.com/moonIsHere11/tinydb-autose/pull/6) | - | 3137/153 | success |
| [44921864482](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921864482) | issue_comment | Fix CachingMiddleware flushing on every write | review-only | approve (naive) | [#7](https://github.com/moonIsHere11/tinydb-autose/pull/7) | - | 610/93 | success |
| [44921866305](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921866305) | issue_comment | Add Query.between() range test | review-only | changes_requested (naive) | [#8](https://github.com/moonIsHere11/tinydb-autose/pull/8) | - | 1688/182 | success |
| [44921867652](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921867652) | issue_comment | Fix OR query cache key | review-only | approve (naive) | [#9](https://github.com/moonIsHere11/tinydb-autose/pull/9) | - | 669/115 | success |
| [44921869487](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921869487) | issue_comment | Return copies from search() so callers cannot corr | review-only | approve (naive) | [#10](https://github.com/moonIsHere11/tinydb-autose/pull/10) | - | 3433/219 | success |
| [44921915844](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921915844) | issues | CachingMiddleware stops caching after the first fl | requ(ok) desi(ok) impl(ok) test(ok) | approve (full) | [#12](https://github.com/moonIsHere11/tinydb-autose/pull/12) | 4 passed | 82611/4231 | success |
| [44921921389](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921921389) | issues | Feature request: range query (`between`) | requ(ok) desi(ok) impl(ok) test(ok) | -  | [#13](https://github.com/moonIsHere11/tinydb-autose/pull/13) | 4 passed | 266928/9578 | failure |
| [44921926432](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921926432) | issues | Feature request: batch upsert | requ(ok) desi(ok) impl(ok) test(ok) | approve (full) | [#14](https://github.com/moonIsHere11/tinydb-autose/pull/14) | 4 passed | 232480/8854 | success |
| [44921931884](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921931884) | issues | search() sometimes shows data that isn't in the da | requ(ok) desi(ok) impl(x) | -  | - | - | 151516/7976 | success |
| [44924437059](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44924437059) | issue_comment | Wrong results when I run an OR query after an AND  | requ(ok) desi(ok) impl(ok) test(ok) | changes_requested / approve (full) | [#11](https://github.com/moonIsHere11/tinydb-autose/pull/11) | 4 passed | 143663/14557 | success |
| [44924465704](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44924465704) | issue_comment | Feature request: range query (`between`) | requ(ok) desi(ok) impl(ok) test(ok) | approve (full) | [#13](https://github.com/moonIsHere11/tinydb-autose/pull/13) | 4 passed | 406451/16900 | success |
| [44924483558](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44924483558) | issue_comment | Return copies from search() so callers cannot corr | review-only | approve (full) | [#10](https://github.com/moonIsHere11/tinydb-autose/pull/10) | - | 17264/819 | success |

**Total tokens over all runs:** 1,582,599 input + 160,355 output = 1,742,954.

# Appendix B: Repository map

The `README.md` of the submission repository lists the layout. Full ADRs are in `architecture/decisions/` (ADR-006
is kept, marked *Superseded by ADR-011*). The harness and prompts are in `workflow/.autose/`. The issues, hidden
tests, seeded PRs with ground-truth labels and the variant definitions are in `experiment/`.
