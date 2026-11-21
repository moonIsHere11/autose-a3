Seven pipeline runs (one per issue, plus fresh `/autose` re-runs of I1 and I3 after harness fixes) and 13 review-only
runs, all on GitHub Actions. Per-run data is in `results/results.csv`, with links in `results/runs.md`.

**Pass rate per stage** (first run of each of the 5 issues; *first try* = passed on the first attempt):

| Stage | Passed within budget | First try | What the code check caught |
|---|---|---|---|
| 1 Requirements | 5/5 | 4/5 | I3: fuzzy word "correctly" in a *Then* clause; Analyst rewrote it |
| 2 Design | 5/5 | 4/5 | I5: Changes table named a non-existent symbol `(module)` |
| 3 Implementation | 4/5 | 5/5 | every attempt compiled, imported and type-checked; I5 exhausted its budget (6 attempts + 1 redesign) because the full suite stayed red |
| 4 Testing | **4/5** | 2/5 | I3: 3 AC tests red on head, so back to Builder (fixed); I4: test file not written, Tester redone; **I5: stopped**, see below |
| 5 Release | 4/4 (I5 not released) | 4/4 | PR opened, pytest + mypy on head green, status `autose/ci` posted |
| 6 Review | first runs: 2/4 approved (I2, I4) | 2/4 | I1: changes requested (false positive), then rework crashed on the restart bug; I3: review crashed (quota). Fresh re-runs: I3 approved; I1 took both rounds (rework re-entered at *implementation*, review 2 approved) |

**Hidden acceptance tests on the final PR branches: I1 4/4, I2 4/4, I3 4/4, I4 4/4, so 16/16.** Passing the hidden tests
does not make every PR correct: **PR #13 (I3) contains an unrequested, breaking change** (below). I5 produced no PR.
It stopped correctly: its spec asks for behaviour that an existing test (`test_query_cache_documents_are_shared_with_cache`)
pins as documented contract, so no implementation could pass the full suite. The stop reason in `test_report.md`
quotes that test. The hidden I5 tests encode my reading of a vague issue, which the maintainers' own test contradicts.
Stopping and handing the contract question to a human is the right outcome, reached at a cost of 6 Builder
attempts (see Hindsight).

**What the reviewer caught, and where it was wrong.** On the seeded PRs (E1), the full reviewer identified 3 of 4
defects (2/4 with a valid verdict, and S5's label is contested, see E1). It missed the approach-level S1 and never
rejected the correct S4. **In the pipeline it missed spec drift on PR #13.** The I3 issue asks only for
`between()`. The Analyst added an acceptance criterion for `where('stats.score')` that the issue never asked for, and the Builder made
`where()` split keys on dots. That breaks existing users of literal dotted keys:
`db.insert({'a.b': 1}); db.search(where('a.b') == 1)` returns 1 document on base and **0 on PR #13**. The reviewer
(on the degraded fallback model) approved it. This is exactly the spec drift that ADR-008 says a reviewer without the
spec should catch; the hidden tests did not cover it. The other three PRs were correct, so every `changes_requested`
in the pipeline was a **false positive**: twice on I1. (a) Run 44921520773:
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
