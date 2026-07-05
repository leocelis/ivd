# Contributing to IVD

IVD is a research-grounded methodology for human-AI collaboration. Every design decision traces to specific LLM cognitive research (see [DECISIONS.md](DECISIONS.md) for the full decision log with evidence).

## How to Participate

**Issues and discussions are welcome.** If you're using IVD and encounter a bug, have a question, or want to propose a recipe — open an issue or start a discussion.

**Pull requests are not being accepted at this time.** The framework is maintained by a single author and evolves through a structured decision process governed by [`ivd_system_intent.yaml`](ivd_system_intent.yaml). This ensures every change is grounded in research and aligned with the framework's cognitive foundations.

This will evolve as the project matures and external validation grows.

## EU AI Act compliance (TrustLint + runtime proof)

IVD ships with **[ComplyEdge TrustLint](https://complyedge.io)** — offline EU AI Act screening on all LLM-facing artifacts (`recipes/`, `templates/`, `*_intent.yaml`). No API key required for the offline gate.

```bash
pip install 'trustlint>=2.0.0'
./scripts/compliance/check.sh
```

CI runs the same offline gate on every PR. Optional runtime proof (BYOK):

```bash
export COMPLYEDGE_API_KEY=ce_...   # env only — never commit
./scripts/compliance/runtime_check.sh
```

Runtime checks feed the live [enforcement seal](https://api.complyedge.io/v1/public/badge/ivd.svg) and [trust page](https://trust.complyedge.io/ivd). See [`docs/COMPLYEDGE_CUSTOMER0.md`](docs/COMPLYEDGE_CUSTOMER0.md).

Cloud audit (`trustlint scan`) is BYOK opt-in — never commit `COMPLYEDGE_API_KEY`.

First-time setup downloads the rule corpus automatically via `./scripts/compliance/check.sh` (public ComplyEdge/complyedge release).

## Reporting Bugs

Open an issue with:

- **IVD version** (check `ivd_system_intent.yaml` header)
- **Agent/IDE** you're using (Cursor, Claude Desktop, VS Code, etc.)
- **What happened** vs **what you expected**
- **Intent artifact** (paste the YAML if relevant)
- **Steps to reproduce**

## Suggesting Recipes

If you've found a pattern that works well with IVD, open an issue with:

- **Use case** — what problem does this recipe solve?
- **Target agent/IDE** — where have you used it?
- **Proposed recipe snippet** (optional)

## Questions and Discussion

For general questions, usage tips, or sharing how you're using IVD — use GitHub Discussions.
