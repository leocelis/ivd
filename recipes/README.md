# IVD Recipes

Reusable patterns for common development scenarios.

## Available Recipes

### Verification & Agent Discipline
- **agent-rules-ivd.yaml** — IVD verification rules for agent instruction files (`.cursorrules`, `.clinerules`, Copilot system prompts). Embeds the full 6-rule IVD workflow: intent before implementation, post-implementation verification protocol, stress-test step, empirical refinement, constraint quality. **Start here.**

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
