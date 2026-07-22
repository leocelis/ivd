# Changelog

All notable changes to IVD are documented here. Full reasoning behind each change lives
in [DECISIONS.md](DECISIONS.md) (FDR entries — Framework Decision Records).

This project does not yet strictly follow [Semantic Versioning](https://semver.org/) or
[Keep a Changelog](https://keepachangelog.com/) format conventions, but is moving toward
both. See [ROADMAP.md](ROADMAP.md).

## [Unreleased]

- **Added `ivd_attest` — the process-attestation gate (33 tools, 19 core).**
  `ivd_validate` checks the *artifact*; nothing checked whether the agent actually
  *followed* the method. An agent could skip the Rule 4 stress test, single-pass nine
  constraints against Rule 1, never re-read from disk per Rule 2, and still emit an
  artifact that validates clean — the read-acknowledge-violate failure mode turned on
  IVD's own rules. `ivd_attest` mechanically checks Rule 1 (segmentation mandatory at
  3+ constraints), Rule 2 (re-read, per-constraint coverage, joint satisfaction),
  Rule 3 (provenance cross-check), and Rule 4 probe coverage, returning
  COMPLIANT | INCOMPLETE | VIOLATION.
  The load-bearing check is the **provenance cross-check**: it is derived from the
  artifact rather than the attestation, so a claimed `PASS` on a constraint whose only
  evidence is an `ai_generated` test is downgraded to `NEEDS_EXTERNAL_ORACLE`
  regardless of what the agent asserts — the one assertion an agent cannot self-grade.
  Structure-only (no LLM, no network, no disk write). Governed by
  `mcp_server/intents/attest_intent.yaml`; 24 new tests.
  Honest bound documented in LEGAL.md §3.11: the attestation is agent-supplied, so this
  converts a *silent* skip into a *visible claim* — it raises the floor, it does not
  close the gap.
- **`ivd_validate` now warns when a workflow- or system-level intent declares no
  termination contract** (`evaluation.cycle` with `max_iterations` + a stop condition).
  Unbounded iteration and unclear completion are among the largest multi-agent failure
  modes; task/module intents are exempt. Warning only — never an error, so legacy
  intents keep validating.
- **Fixed a stale claim in LEGAL.md §3.7 (R-006):** it stated `ivd_validate` "does not
  warn on constraint count." It does — the 7-constraint budget has been enforced at
  `validate.py`. Corrected to describe the advisory warning accurately.
- **Security:** bumped `mcp` 1.23.0 → 1.28.1 (`requirements.txt`,
  `mcp_server/requirements.txt`, `pyproject.toml` floor), clearing all 6 open
  Dependabot alerts (3 advisories: HTTP transport principal-verification,
  experimental task-handler isolation, WS Host/Origin validation). Validated
  in an isolated venv: server imports clean and the full transport/registry/
  auth surface passes.
- Judgment phase — closed two loop gaps (see `judgment_layer.md` v1.2):
  - Added `ivd_judgment_resolve` MCP tool — records an entry's resolution
    (`outcome`, optional `held` / `fix_applied`, auto `resolved_at`) and
    transitions `codified | paired → resolved`. Step 9 of the loop previously
    had no tool, so outcomes were never logged and future runs re-derived
    settled diagnoses. Tool count: 31 → 32 (10 judgment).
  - Added a 4th `ivd_judgment_inject_context` layer, **ruled_out** — surfaces
    `injection_status: rejected` comparison-pair hypotheses as a do-not-retry
    veto (negative knowledge), so the loop does not re-propose a falsified theory.
  - Added authored `never` / `related_files` fields to `Pattern` (do/never/related
    craft guidance), preserved across re-detection, excluded from `detection_hash`.
  - Additive-only: existing `.judgment/` folders keep working; new fields default
    empty. 9 new tests in `test_judgment.py` (incl. a re-detection regression
    guard: authored `never`/`related_files` survive re-detect and stay out of
    `detection_hash`).
- Added `ivd_import_spec` MCP tool — parses a GitHub Spec Kit or OpenSpec `spec.md`
  into an IVD constraint scaffold (User Story / Requirement + Given/When/Then
  scenarios), read-only, no LLM call. Neither source format binds a scenario to an
  executable test by default; this tool exists to add that binding without
  replacing either tool's own planning workflow. New `imported_from:` optional
  intent-artifact field for traceability. New recipes: `import-spec-kit.yaml`,
  `import-openspec.yaml`. Tool count: 30 → 31 (18 core).
- Added `pyproject.toml` — pip/editable installable, `ivd-mcp` console entry point,
  optional extras (`[search]`, `[compliance]`, `[dev]`).
- Added `examples/intent_demo/` — offline, runnable demonstration of the core
  Intent → Implementation → Verification loop (catching a hallucinated implementation
  against a structured intent artifact).
- Added `docs/positioning.md`, `ROADMAP.md`, `DEVELOPMENT.md`.
- Removed unsubstantiated "zero hallucinations" marketing language from README and
  `index.html`; replaced with claims the constraint-check mechanism can actually back.
- Fixed tool-count drift across README, `server.json`, `.env.example` (actual count is
  30 tools: 17 core + 9 Judgment + 4 Canon; two core tools — `ivd_review_intent` and
  `ivd_run_constraint_tests` — were previously undocumented in the count).
- Fixed recipe-count drift in README (table now lists all 18 recipes, including the
  3 Judgment recipes that were previously omitted).
- CI `compliance` job (TrustLint) is now non-blocking (`continue-on-error`) so a
  ComplyEdge-side release fetch failure can't fail unrelated contributor PRs.
- Fixed broken Quick Start MCP client config (`"command": "python"` pointed at system
  Python; dependencies are installed into `.venv/` by `setup.sh`) — now points at the
  venv's Python explicitly.

> **Note on versioning:** the last tagged GitHub release is `v2.4.0` (2026-03-20). The
> `v3.0` (Judgment phase) and `v3.1` (Canon phase) changes below shipped to `main` but
> were not tagged/released on GitHub. See [ROADMAP.md](ROADMAP.md) for the plan to close
> that gap.

## [3.1.0] — 2026-04-23 (shipped to main, not yet tagged)

### Added
- **Canon — Human Translation Layer** (Phase 0): `canon_render`, `canon_check`,
  `canon_diff`, `canon_check_rules_installed` MCP tools. Enforces five communication
  invariants (Setting Phase, Confidence Calibration, Verification Beat, Folk Theory
  Management, Anthropomorphism Ceiling) on top of any LLM output. See
  [canon_layer.md](canon_layer.md).
- `ivd_judgment_check_installed` — read-only detection of `.judgment/` activation
  state; does not write to disk.
- `recipes/canon-rules.yaml` — pasteable Canon Phase 0a rules block.

## [3.0.0] — 2026-03-21 (shipped to main, not yet tagged)

### Added
- **Judgment phase** (Principle 9, IVD's 4th phase): `ivd_judgment_init`,
  `ivd_judgment_capture`, `ivd_judgment_codify`, `ivd_judgment_save_codified`,
  `ivd_judgment_pair`, `ivd_judgment_detect_patterns`, `ivd_judgment_inject_context`,
  `ivd_judgment_propose_recommendation` — capture, codify, cluster, and inject
  real-world corrections as compounding contextual knowledge. Opt-in via `.judgment/`.
  See [judgment_layer.md](judgment_layer.md). (FDR-015, FDR-016)
- `recipes/capture-correction.yaml`, `recipes/comparison-pair.yaml`,
  `recipes/distill-pattern.yaml`.

## [2.4.0] — 2026-03-20

Initial public release (tagged GitHub release).

### Fixed (post-launch health audit, 2026-05-10 — FDR-017 through FDR-024)
- `ivd_list_features` returning duplicate artifacts (FDR-017)
- `ivd_validate` rejecting valid recipe artifacts (FDR-018)
- `ivd_init` guard not detecting existing named system intents (FDR-019)
- `ivd_list_recipes` returning opaque metadata for 8 of 17 recipes (FDR-020)
- `ivd_discover_goal` ignoring the `user_hint` parameter (FDR-021)
- `ivd_propose_inversions` returning a silent empty scaffold with no agent instruction
  (FDR-022)
- IVD rules block in `.cursorrules` missing detection fence markers (FDR-023)
- Published `LEGAL.md` — public disclosure of AI limitations, hosted-server data
  transmission, marketing-claim scope, and deployer obligations (FDR-024)

### Added (pre-launch foundation, 2026-02-09 — FDR-001 through FDR-014)
- Core IVD methodology: Intent → Implementation → Verification loop, 15 core MCP tools
- Intent Stress Test (Rule 4), Post-Implementation Verification Protocol (Rule 2)
- Constraint-Segmented Implementation for 3+ constraints (Rule/Principle basis in
  read-acknowledge-violate and lost-in-the-middle research)
- Interpretive Entropy Spectrum for non-code constraint design (FDR-010)
- Constraint Satisfiability checks and `constraint_satisfiability` block (FDR-011)
- Contextual Knowledge Source Hierarchy + 2-attempt enrichment trigger (FDR-013)
