# IVD Recipes

Reusable patterns for common development scenarios.

## Available Recipes

### Verification & Agent Discipline
- **agent-rules-ivd.yaml** — IVD verification rules for agent instruction files (`.cursorrules`, `.clinerules`, Copilot system prompts). Embeds the full 6-rule IVD workflow: intent before implementation, post-implementation verification protocol, stress-test step, empirical refinement, constraint quality. **Start here.**
- **compliance-trustlint.yaml** — ComplyEdge TrustLint EU AI Act gate (offline, free tier). Run `./scripts/compliance/check.sh` after `ivd_scaffold` or recipe/intent edits; CI blocks merge on critical/high violations. Recipe ships `<BEGIN-COMPLYEDGE v1.0>` agent block + `.trustlint.yaml` + pre-commit hook. No API key in repo.
- **canon-rules.yaml** — Canon (Human Translation Layer) rules block (Phase 0a). Teaches any LLM-driven agent to emit R1 setting phase, R2 confidence markers (`✓ verified` / `~ inferred` / `? assumed`), R5 verification beats on irreversible actions, R10 folk-theory corrections, and R14 bounded identity. One canonical source → six per-client adapter views (Cursor, Cline, Claude Code, Copilot, Codex, Windsurf). Verified programmatically by the `canon_check` MCP tool and detected/installed via `canon_check_rules_installed` (never writes — always asks).

### Spec-Tool Integration
- **import-spec-kit.yaml** — Parse a GitHub Spec Kit `spec.md` (User Story + Given/When/Then) into an IVD constraint scaffold via `ivd_import_spec`, then bind each acceptance scenario to a real, executable test — the binding Spec Kit's own format doesn't provide by default.
- **import-openspec.yaml** — Parse an OpenSpec delta `spec.md` (Requirement + Scenario, GIVEN/WHEN/THEN/AND) via `ivd_import_spec`. Complements, not replaces, OpenSpec's own `/opsx:verify` — that command judges coverage by LLM keyword search over the codebase; this recipe adds a requirement that a real test must pass.

### Multi-Agent Patterns
- **coordinator-intent-propagation.yaml** — Multi-agent coordination with intent delegation (coordinator writes intent for each agent it routes to)
- **agent-capability-propagation.yaml** — Propagate agent capabilities up to coordinator routing (`interface.routing`); keeps LLM routing descriptions in sync with agent evolution
- **agent-role-based.yaml** — Context-dependent agent behavior: agents adopt different personas/modes based on routing context

### AI Workflow Patterns
- **workflow-orchestration.yaml** — Multi-step workflow orchestration across agents/modules
- **agent-classifier.yaml** — AI classification agent pattern
- **self-evaluating-workflow.yaml** — Continuous improvement loop: AI evaluates its own output against intent, flags gaps, re-runs

### Teaching & Discovery
- **teaching-before-intent.yaml** — When the user lacks technical knowledge: AI creates educational artifact, user confirms understanding, then intent flow (Principle 6 extension, canonical)
- **discovery-before-intent.yaml** — When the user can't describe what they want: propose goals/recipes/options, user picks, then intent flow (Principle 6 extension, experimental)

### Infrastructure Patterns
- **infra-background-job.yaml** — Background job processing infrastructure
- **infra-structured-logging.yaml** — Structured JSON logging for services and tool dispatch layers

### Data Patterns
- **data-field-mapping.yaml** — Field mapping and data sources for integrations and ETL
- **doc-meeting-insights.yaml** — Extract structured insights from meeting transcripts

### Judgment Phase Patterns (IVD v3.0+)
*Activated when a project has a `.judgment/` folder at its root. See `../judgment_layer.md`.*
- **capture-correction.yaml** — Capture and codify a single correction into the Judgment ledger
- **comparison-pair.yaml** — Pair two real runs to derive diagnostic hypotheses (Rung-1 alternative to A/B)
- **distill-pattern.yaml** — Convert an emergent pattern into a you-approvable recommendation (with optional draft recipe)

## How to Use

1. Browse recipes to find a pattern that matches your use case
2. Reference the recipe in your intent artifact:

   ```yaml
   recipe: "agent-classifier"
   recipe_version: "1.0"
   ```

3. Follow the recipe's template sections to create your implementation

## Creating New Recipes

See `../recipe-spec.md` for the recipe specification and structure.
