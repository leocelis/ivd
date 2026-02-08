# IVD Recipes

Reusable patterns for common development scenarios.

## Available Recipes

- **teaching-before-intent.yaml** - When the user lacks technical knowledge: AI creates educational artifact, user understands, then intent flow (Principle 6 extension, canonical)
- **discovery-before-intent.yaml** - When the user can't describe what they want: propose goals/recipes/options, user picks, then intent flow (Principle 6 extension, experimental)
- **agent-classifier.yaml** - AI classification agent pattern
- **coordinator-intent-propagation.yaml** - Multi-agent coordination with intent flow
- **data-field-mapping.yaml** - Field mapping and data sources for integrations and ETL
- **doc-meeting-insights.yaml** - Extract insights from meeting transcripts
- **infra-background-job.yaml** - Background job processing infrastructure
- **infra-structured-logging.yaml** - Structured JSON logging for services and tool dispatch layers
- **workflow-orchestration.yaml** - Multi-step workflow pattern

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
