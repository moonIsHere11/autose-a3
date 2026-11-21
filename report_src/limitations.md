1. **Tiny samples, one run each.** Five issues, five seeded PRs, and in general one pipeline run per issue. LLM
   outputs vary between runs (temperature 0.2, plus model fallbacks), so a pass or fail on one issue is an
   anecdote, not a rate. The E1 comparison (5 PRs × 2 variants) can show large effects at best; differences of one PR
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
