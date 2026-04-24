# Judgment, Explained

> Plain-English on-ramp to the IVD Judgment phase.  Read this first
> if you want to understand **what problem Judgment solves and how**
> before reading the canonical spec.
>
> - For the canonical spec: [`judgment_layer.md`](judgment_layer.md)
> - To watch it work in 5 seconds: [`examples/judgment_demo/`](examples/judgment_demo/)
> - For the 9 MCP tools cheatsheet: [`cheatsheet.md`](cheatsheet.md) §Part 2.5

---

## The problem

You use AI coding agents — Cursor, Claude Code, Copilot, Cline,
whatever.  They're great.  But they have one annoying habit:

**They make the same mistake on Monday that you corrected on Friday.**

Not because they're broken.  Because each chat session is a goldfish.
The model has no memory between conversations.  So every Monday it
reaches for the same defaults from its training data — and ignores
the conventions your team standardized on.

Concretely, this looks like:

- The agent keeps using `render()` instead of your `renderWithProviders()` helper
- It keeps writing `try/except: pass` instead of your `Result<T, E>` error pattern
- It keeps putting files in `utils/` instead of your `src/features/<feature>/` layout
- It keeps using `requests` instead of your project's `httpx_client` wrapper

You correct it.  The fix lives for one chat session.  Then it
evaporates.

**The cost:** you spend 10 minutes a day re-teaching the same lesson
to the same agent.  Multiplied across your team and across a year,
that's hundreds of hours of context that never accumulates anywhere.

---

## Why "just put it in `.cursorrules`" doesn't actually work

The natural reaction is: *"I'll just write the rules down once."*
Sure — for one or two rules.  But that approach breaks down fast:

- After 6 months your `.cursorrules` is 800 lines and nobody knows
  which rules still matter
- A rule that mattered in March is wrong in October but nobody
  remembered to delete it
- New rules conflict with old rules and the agent can't tell which
  to obey
- There's no record of *why* each rule exists — just a flat wall of
  "do this, don't do that"
- The agent treats a one-off pet peeve and a bedrock convention as
  equally important

You end up with a pile of static rules that decays into noise.

---

## What Judgment does

Judgment is a discipline (and a small piece of tooling) for **turning
the corrections you make anyway into a living, weighted, decaying
knowledge base** that the agent inherits automatically.

It works in three steps.  Each step is one MCP tool call.  Together
they take maybe 30 seconds of your day per correction.

### Step 1 — Capture (when you correct the agent)

You correct the agent.  Instead of just typing the fix into chat, you
also tell Judgment:

> "Here's what the agent did.  Here's what was wrong.  Here's the
> right pattern."

Judgment writes that to disk under `.judgment/ledger/raw/`.  One YAML
file per correction.  Takes 5 seconds.

### Step 2 — Codify (turn the correction into a structured lesson)

Judgment asks the agent: *"OK, look at what just got captured.
What's the **root cause** here?  What's the **fix**?  In what kind of
code does this apply?"*

The agent fills in a small, structured form (`diagnosed_cause`,
`proposed_fix`, etc.).  That gets saved to `.judgment/ledger/codified/`.
The correction is now a structured lesson, not a Slack message.

### Step 3 — Detect patterns (let lessons compound)

Once the same root cause shows up **three times** (across any code,
any week, any developer), Judgment promotes it from "individual
correction" to **Pattern**.  A Pattern is a *promoted* lesson — it
has earned its way out of the noise floor by recurring.

A Pattern carries:

- `member_count` — how many incidents fed it (signal strength)
- `weighted_confidence` — weighted by how senior the corrector was
  (so a junior dev's pet peeve doesn't outweigh the staff engineer's
  architectural rule)
- `freshness` — fresh / aging / stale (lessons decay; old patterns
  fade)
- `recommended_fix` — the consolidated rule

### Step 4 — Inject (every future agent run gets the patterns)

Before the next coding request, Judgment injects all the live
Patterns into the agent's system message — at the top, where the
model attends most strongly.  The agent now writes its next test (or
component, or migration) with your project's conventions baked in,
automatically.

---

## The picture in one diagram

```
You correct the agent       →  Capture     (5 sec)   →  raw lesson on disk
You correct it again        →  Capture     (5 sec)   →  raw lesson on disk
Same root cause, 3rd time   →  Capture     (5 sec)   →  raw lesson on disk

                                Detect     →   PATTERN PROMOTED
                                              (member_count: 3, confidence: 1.0)

Next coding request         →  Inject     →   Agent's system message now
                                              contains the pattern, hard-attached.

Agent generates code        →   The code follows the pattern.
                                Same model. Same temperature. Same prompt.
                                Different output.
```

---

## Why this beats the alternatives

|                                          | `.cursorrules` (static) | Vector DB / RAG               | **Judgment**                                       |
| ---------------------------------------- | ----------------------- | ----------------------------- | -------------------------------------------------- |
| Decay over time                          | Manual cleanup          | None                          | Automatic half-life                                |
| Provenance ("why is this rule here?")    | None                    | None                          | Linked to the 3 incidents that produced it         |
| Confidence weighting                     | None                    | Cosine distance               | Weighted by corrector's seniority                  |
| Promotion threshold (signal vs noise)    | All rules equal weight  | All chunks ranked by similarity | Only patterns with ≥ N incidents enter context   |
| Audit trail                              | None                    | None                          | SHA-256 hash of every injected payload             |
| Survives a model swap (4o → 5)           | Maybe                   | Maybe                         | Yes — the lessons live in YOUR repo                |
| What you read                            | A flat 800-line text file | A list of similar code snippets | A short list of explicit, weighted, dated rules |

---

## The simplest possible mental model

> **Judgment is a journal.**  Every time you correct the agent, you
> write one line in the journal.  Once any lesson shows up in the
> journal three times, it gets promoted to a "house rule."  House
> rules are stapled to the front of every future conversation with
> the agent.  Old house rules that haven't been reinforced fade out
> automatically.

That's it.  That's the whole idea.  Everything else — the YAML
schema, the MCP tools, the engine version stamps, the promotion
algorithm — is plumbing in service of that one idea.

---

## Why it matters strategically

The model layer is commoditizing.  GPT-5 will know more React than
GPT-4o; Claude 4 will know more Python than Claude 3.  Every team
has access to the same models.

What every team does **not** have access to is **your** project's
conventions, **your** team's hard-won lessons, **your** specific way
of doing error handling and testing and file layout.  That knowledge
is the only thing left that can differentiate your codebase six
months from now.

Judgment is the discipline that turns that knowledge from "Slack
messages and chat corrections that evaporate" into **"a structured,
compounding asset that lives in your repo and that every future
agent run inherits automatically."**

That's the problem.  That's the fix.  That's why it's worth the
30 seconds per correction.

---

## See it work (5 seconds, no setup)

```bash
python examples/judgment_demo/run_demo.py
```

Walks the entire loop end-to-end against a real `.judgment/`
directory and writes four human-readable artifacts (`before.md`,
`after.md`, `diff.md`, `llm_responses.md`) showing the same AI
coding agent producing **different code** on the same request after
Judgment compounds three corrections into a single Pattern.

Set `OPENAI_API_KEY` to make a real `gpt-4o-mini` call (~$0.001) and
see the live behavioral diff.  Full narrative + verdict:
[`examples/judgment_demo/README.md`](examples/judgment_demo/README.md).

---

## Where to go next

- **Watch it work:** [`examples/judgment_demo/`](examples/judgment_demo/)
- **The 9 MCP tools:** [`cheatsheet.md`](cheatsheet.md) §Part 2.5
- **The canonical spec (10-step loop, schemas, internals):**
  [`judgment_layer.md`](judgment_layer.md)
- **Where Judgment fits in the full IVD framework:**
  [`framework.md`](framework.md) §Principle 9
- **Architectural decisions that shaped Judgment v3.1:**
  [`DECISIONS.md`](DECISIONS.md)
