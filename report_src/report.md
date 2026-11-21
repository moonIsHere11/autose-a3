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

{{STAGE_TABLE}}

**Which agent handles which stage.** The *Analyst* runs stages 1 and 2 (two invocations with different prompts,
same read-only profile). It is the only worker that reads the raw issue. The *Builder* runs stage 3: it can write only
under `tinydb/`, never sees the issue, and receives the spec, the design and the harness-extracted source of the
symbols the design names. The *Tester* runs stage 4: it can write only `tests/autose/` and writes tests from the spec.
Stage 5 is **not an agent**: `ship_*` is a script that applies the patch, pushes `autose/issue-N`, opens the PR from
a template (no agent prose), runs CI (pytest + mypy) itself, because pushes made with `GITHUB_TOKEN` trigger no other
workflow, and posts the commit status `autose/ci`. The *Reviewer* runs stage 6 in its own job on a fresh VM with a
different model. The back-edges (test failure to implementation, exhausted implementation to design, review
`approach` to design, review `code` to implementation) are decided by the state machine, never by a model.

{{SEQUENCE}}

# 2 Design decisions

{{ADR_TABLE}}

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
bounded at two rounds, so I unrolled it into jobs instead of looping: `review_1 → rework_1 → ship_1 → review_2`.
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

{{EXPERIMENTS}}

# 4 Results

{{RESULTS}}

# 5 Hindsight

{{HINDSIGHT}}

# 6 Limitations and threats to validity

{{LIMITATIONS}}

\newpage

# Appendix A: Runs

{{RUNS}}

# Appendix B: Repository map

The `README.md` of the submission repository lists the layout. `demo.mp4` (no audio) walks through the completed run of issue #1 after the fact (see Limitation 7). Full ADRs are in `architecture/decisions/` (ADR-006
is kept, marked *Superseded by ADR-011*). The harness and prompts are in `workflow/.autose/`. The issues, hidden
tests, seeded PRs with ground-truth labels and the variant definitions are in `experiment/`.
