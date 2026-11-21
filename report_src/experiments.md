Variant definitions are in `experiment/variants.md` and were written before running. Ground truth for seeded PRs comes
from `experiment/seeded_prs/labels.csv` (hidden tests plus existing suite on each branch).

**E1: ADR-008, reviewer independence.** Five seeded PRs, each reviewed by the *full* reviewer (different model,
issue + diff + repo only, adversarial prompt, evidence gate) and by a *naive* reviewer (workers' model, sees the
author's PR description "…all existing tests pass", plain "review this PR" prompt, no evidence gate). Same tools and
sandbox. A defect counts as *identified* only if a finding names the actual defect.

| PR (truth) | Full reviewer | Naive reviewer |
|---|---|---|
| S1 #6 (approach: OR made non-cacheable) | approve, 3 cmds: **missed** | approve: **missed** |
| S2 #7 (code: counter reset before flush, data loss) | changes requested, exact defect, probe evidence (3 cmds) | approve with **0 commands** (existing suite fails 2 tests on this branch) |
| S3 #8 (code: exclusive bounds) | exact defect with probe (6 cmds), but **no `verdict:` line** → `invalid` | changes requested for the **wrong reason** ("missing unit tests") |
| S4 #9 (correct control) | approve (3 cmds); first attempt approved with 0 cmds → rejected by gate | approve |
| S5 #10 (code: shallow copy, nested leak) | changes requested, exact defect, but evidence **hollow** (only ran pytest) | approve (ran pytest) |
| **Defects identified** | **3/4 named; 2/4 with a valid verdict** (S5 label contested) | **0/4** |
| False rejections (S4) | 0/1 | 0/1 |
| Mean commands executed | 3.2 | 0.4 |

*Re-test of S5 under ADR-012* ([run 44924483558](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44924483558)):
the primary reviewer model was rate-limited at that moment, so **every call was served by the fallback
`gemini-flash-lite-latest`** (logged in `usage.json`). It ran 7 commands, but its probes only mutated top-level keys,
and it **approved**, missing the nested-copy defect that the primary model had found. ADR-012's gate behaved correctly
(nothing ungrounded was kept), but the outcome was decided by the *model*. That is a confound for ADR-012, and
direct evidence for ADR-011's claim that reviewer strength, not just reviewer independence, is what catches subtle
defects.

*Caveats on E1.* (1) The variants differ in **five** factors at once (model, inputs including a PR description that
falsely claims "all existing tests pass", prompt, adversarial mandate, evidence gate), not one, despite `variants.md`'s
intent; E1 measures the *bundle* of ADR-008 choices, not independence alone. (2) The full reviewer prompt names
probe areas (query hashes, middleware write counting, nested fields) that overlap the seeded defect classes.
(3) **S5's label is contested:** the upstream test `test_query_cache_documents_are_shared_with_cache` pins nested
sharing as documented behaviour (the same test that made I5 stop), so "nested mutation leaks" is arguably the contract,
not a defect. Counting S5 as not-a-defect, the full reviewer's tally is 2/3 named, 1/3 with a valid verdict.
Under the final ADR-012 system (S5 re-test) the result is S2 caught, S3 no valid verdict, S1 and S5 missed.

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
| …of which actually vacuous | **1 (I2 AC-2)**: new behaviour, passes on base only because `WRITE_CACHE_SIZE=10` hides it | accepted too |

| Pipeline tests run against … | S1 (wrong fix for I1) | S2 (wrong fix for I2) | S3 (wrong fix for I3) |
|---|---|---|---|
| result | 2/2 pass: **does not catch** | 1 fails: catches | 2 fail: catches |

*Reading (a negative result).* In live runs, the red/green rule **never fired**: every Tester suite already failed on
base, so green-only would have decided identically. The only vacuous test that got through came in through the
**escape hatch I added to avoid false rejections**: the Analyst tagged new behaviour `[regression-only]`. Red/green is
cheap insurance (one extra sandboxed pytest run per evaluation), but on these tasks it bought nothing measurable, and
its exemption became the weak point. **Design change (ADR-007 consequence, not yet implemented):** the harness, not
the Analyst, should grant `[regression-only]`. Grant it only when the AC's test also passes on base *and* the AC cites
an existing test or documented behaviour, and have the reviewer see which ACs were exempted.
