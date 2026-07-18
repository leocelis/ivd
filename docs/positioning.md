# IVD vs. what you're probably already doing

You already have a way to give an AI agent context: a `CLAUDE.md`, a
`.cursorrules` file, a spec-driven workflow, or your agent's built-in plan
mode. This doc is an honest answer to "why would I add IVD on top of that,"
including where the honest answer is "you probably don't need to."

Feature sets for all of these move fast — verify current behavior against
each project's own docs before treating this table as current.

| | Static rules files (`CLAUDE.md`, `.cursorrules`, `AGENTS.md`) | Agent plan mode (built into Claude Code, Cursor, etc.) | Spec-driven workflows (GitHub Spec Kit, Kiro specs, similar) | BDD (Cucumber/Gherkin) | IVD |
|---|---|---|---|---|---|
| **What it captures** | Standing conventions, always-loaded | A plan for *this task*, reviewed once, then discarded | A spec document per feature, usually prose + acceptance criteria | Behavior scenarios in Given/When/Then | An intent artifact per module/task: constraints, each bound to an executable test |
| **Machine-checkable?** | No — prose the agent reads and may or may not follow | No — the plan is prose; execution isn't checked against it after the fact | Partially — acceptance criteria are usually still prose | Yes — Gherkin scenarios run as tests | Yes — every constraint has a `test:` field; `ivd_validate` and the verification protocol check the implementation against it, not just the spec against itself |
| **Survives the task** | Yes, by design (that's its job) | No — plan mode's plan isn't a durable artifact once the task ships | Sometimes — depends on whether specs are kept current post-ship | Yes, if you maintain the feature files | Yes — intent artifacts live alongside code, `changelog:` tracks drift |
| **Catches an LLM ignoring its own instructions** | No — this is exactly the read-acknowledge-violate failure mode IVD's constraint-segmented implementation targets | No | No, unless the spec's acceptance criteria happen to be automated | Yes, for behavior the scenarios cover | Yes, that's the specific problem the verification protocol exists to catch |
| **Setup cost** | Low — one file | None — built into the agent | Medium — spec authoring workflow | Medium-high — scenario authoring, step definitions | Medium — intent artifact authoring, stress test, constraint tests |
| **Best for** | Team conventions, style, architecture that rarely changes | One-off tasks where you want to review the approach before code | Feature-level requirements docs, especially cross-functional (PM + eng) | User-facing behavior with clear black-box scenarios | Any task where the AI's *interpretation* of ambiguous intent is the actual risk — not just "did the code compile" |

## Where IVD is redundant with what you have

- **Trivial changes** (typo, rename, one-line fix): plan mode or nothing is enough. IVD says this explicitly (`framework.md`, Principle 6, "When to skip").
- **You already maintain rigorous BDD scenarios with real step definitions**: those scenarios are, in IVD's terms, already near-zero-entropy constraints with real tests. You don't need to also write an intent artifact — you could adopt IVD's verification *discipline* (re-read from disk, constraint-segmented implementation) without adopting its artifact format.
- **Your team already treats spec documents as the source of truth and keeps them current**: the gap IVD closes is specs going stale or specs being prose an AI can only guess at satisfying. If your spec process already produces testable acceptance criteria and keeps them in sync with code, you've built your own version of the constraint layer.

## Where IVD adds something the others don't

The specific failure mode IVD targets is not "the AI didn't have context" — static rules files and plan mode both solve that. It's **the AI had the context, acknowledged it, and violated it anyway**, a pattern documented across real agent sessions (see `framework.md` §Principle 6, citing anthropics/claude-code issues #26848, #6120, #32290, #742). Prose-based context — rules files, plan mode's plan, most spec documents — has no mechanism to catch this after the fact. A constraint with a `test:` field does: either the test passes or it doesn't.

The second thing none of the alternatives above do: **compounding corrections across runs** (the Judgment phase). A rules file you edit by hand doesn't cluster your last ten corrections into a pattern with a confidence score. That's opt-in and separate from the core loop — see [`judgment_explained.md`](../judgment_explained.md) — but it's the piece with no direct analogue in the tools above.

## You don't have to choose

If you already use GitHub Spec Kit or OpenSpec, `ivd_import_spec` reads the `spec.md` either already produces and hands back a constraint scaffold — you keep the planning workflow you have and add the `test:` binding neither format provides by default. OpenSpec's own `/opsx:verify` command (the `openspec-verify-change` skill) already tries to solve part of this — but by design it works via LLM keyword search over the codebase and existence-checks ("does a test happen to cover this scenario"), not by requiring a test to actually run and pass. See [`recipes/import-spec-kit.yaml`](../recipes/import-spec-kit.yaml) and [`recipes/import-openspec.yaml`](../recipes/import-openspec.yaml).

## The honest tradeoff

IVD costs more setup than a rules file and more than plan mode. It's worth that cost specifically when: the task is non-trivial, the AI's interpretation of an ambiguous requirement is the actual risk (not just code correctness), and you want that interpretation checked by something other than a second read-through. For everything else, use what you already have — IVD says so in its own framework doc, not just here.
