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
this because I had modelled back-edges as *code fault → implementation, approach fault → design*. I5 shows a third
kind of fault, *requirements versus contract*, which only a human can resolve, and a principled SDLC pipeline needs
an explicit edge for it.

Second on the list: ADR-006/011. I chose models on capability and independence, but on a free tier the binding
constraint was **availability and daily quota** (20 requests per day for the Flash models). I would design the model
layer as a budgeted resource from the start: a per-role quota ledger and a reviewer that is never more than one
fallback away from a model with a different daily pool.
