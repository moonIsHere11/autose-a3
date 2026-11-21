**Sequence view: one real run, trigger to review** (issue #2, [run 44921915844](https://github.com/moonIsHere11/tinydb-autose/actions/runs/44921915844), [PR #12](https://github.com/moonIsHere11/tinydb-autose/pull/12); times UTC from the Actions API and `events.json`; mermaid version in `architecture/views/sequence.md`).

| t (UTC) | from → to | message / effect |
|---|---|---|
| 15:57:3x | maintainer → GitHub | adds label `autose` to issue #2 |
| 15:57:39 | `gate` → GitHub | sender permission = write ✓; ledger comment posted; artifact `issue` uploaded |
| 15:58:35 | `build`: Analyst → gate | `spec.md`, 2 ACs, Given/When/Then ✓ (issue text was seen only here, in `<untrusted_issue>` tags) |
| 15:59:04 | Analyst → gate | `design.md`: `tinydb/middlewares.py::CachingMiddleware.flush` exists per AST ✓ |
| 16:00:11 | Builder → sandbox → gate | gets spec + design + `flush` source, no issue; one edit; compileall + import + mypy ✓ |
| 16:02:12 | Tester → sandbox → gate | `test_issue_2.py`; AC-1 **red on base, green on head**; AC-2 `[regression-only]`; 229 passed ✓ |
| 16:02:36 | `ship_0` → GitHub | push `autose/issue-2`, open PR #12 from template, pytest + mypy on head, status `autose/ci` = success |
| 16:02:47-16:20:44 | `review_1` (attempt 1) | downloads **only** `issue`; model quota errors exhausted the old fallback chain → job failed; `finalize` logged the stop |
| 16:22:57 | `review_1` (attempt 2, re-run failed jobs) | fresh VM, harness from master; 5 sandboxed commands (pytest + probes) |
| 16:23:51 | Reviewer → GitHub | review posted on PR #12: **approve** |
| 16:24:07 | `finalize` → GitHub | ledger: "reviewer approved; awaiting a maintainer's merge decision". Nothing is merged. |
