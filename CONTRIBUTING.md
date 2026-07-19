# Contributing to IVD

IVD is a research-grounded methodology for human-AI collaboration. Every design decision traces to specific LLM cognitive research (see [DECISIONS.md](DECISIONS.md) for the full decision log with evidence).

## How to Participate

**Issues and discussions are welcome.** If you're using IVD and encounter a bug, have a question, or want to propose a recipe — open an issue or start a discussion.

**Pull requests are not being accepted at this time.** The framework is maintained by a single author and evolves through a structured decision process governed by [`ivd_system_intent.yaml`](ivd_system_intent.yaml). This ensures every change is grounded in research and aligned with the framework's cognitive foundations.

This will evolve as the project matures and external validation grows.

## Contribution Ownership (Developer Certificate of Origin)

Anything you submit to this project — an issue, a recipe suggestion, feedback, or
(once opened) a pull request — must be something you have the right to submit under
the MIT License. IVD uses the industry-standard **[Developer Certificate of Origin
(DCO) 1.1](https://developercertificate.org/)** (originated by the Linux Foundation;
used by the Linux kernel, Kubernetes, Docker, GitLab, and most major OSS projects) as
the standard for this:

> By making a contribution to this project, I certify that: (a) the contribution was
> created in whole or in part by me and I have the right to submit it under the open
> source license indicated in the file; or (b) the contribution is based upon previous
> work that, to the best of my knowledge, is covered under an appropriate open source
> license and I have the right under that license to submit that work with
> modifications, whether created in whole or in part by me, under the same open source
> license, as indicated in the file; or (c) the contribution was provided directly to
> me by some other person who certified (a), (b), or (c) and I have not modified it.

For future pull requests, sign off commits with `git commit -s` (adds a
`Signed-off-by:` trailer). For issue-based recipe or feedback submissions today, opening
the issue constitutes the same certification.

## EU AI Act compliance (TrustLint + runtime proof)

IVD ships with **[ComplyEdge TrustLint](https://complyedge.io)** — offline EU AI Act screening on all LLM-facing artifacts (`recipes/`, `templates/`, `*_intent.yaml`). No API key required for the offline gate.

```bash
pip install 'trustlint>=2.0.1'
./scripts/compliance/check.sh
```

CI runs the same offline gate on every PR. Optional runtime proof (BYOK):

```bash
export COMPLYEDGE_API_KEY=ce_...   # env only — never commit
./scripts/compliance/runtime_check.sh
```

Runtime checks feed the live [enforcement seal](https://api.complyedge.io/v1/public/badge/ivd.svg) and [trust page](https://trust.complyedge.io/ivd). See [`docs/integrations/COMPLYEDGE.md`](docs/integrations/COMPLYEDGE.md).

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
