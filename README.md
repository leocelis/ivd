<p align="center">
  <strong>Intent-Verified Development</strong>
</p>

<p align="center">
  <em>The Framework for the AI Agents Era</em>
</p>

<p align="center">
  <a href="https://mcp.ivdframework.dev/health"><img src="https://img.shields.io/badge/MCP_Server-live-brightgreen?style=flat-square" alt="MCP Server"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/version-1.3-blue?style=flat-square" alt="Version"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.12"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/tests-114_passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/license-private_alpha-orange?style=flat-square" alt="License"></a>
</p>

---

**Documentation**: [framework.md](framework.md) | **Cookbook**: [cookbook.md](cookbook.md) | **Cheatsheet**: [cheatsheet.md](cheatsheet.md) | **MCP Server**: [mcp.ivdframework.dev](https://mcp.ivdframework.dev/health)

---

IVD is a methodology where **the AI writes the intent, implements against it, and verifies** — eliminating many-turn correction cycles and hallucinations at the source.

```
Without IVD                              With IVD

You: "Add CSV export"                    You: "Add CSV export for compliance"
AI:  [builds with wrong columns]         AI:  [writes intent.yaml with constraints]
You: "No, these columns, ISO dates"      You:  "Yes, that's what I meant"
AI:  [rewrites, still wrong]             AI:  [implements, runs tests, verifies]
You: "Still not right..."                You:  "Done. First try."
[Many turns. Many hallucinations.]       [One turn. Zero hallucinations.]
```

## Why IVD?

Traditional artifacts (PRDs, user stories, prompts) are **prose written by humans** — AI reads them, guesses, and hallucinates. IVD inverts this:

| | Traditional | IVD |
|---|---|---|
| **Who writes** | Human writes requirements | AI writes structured intent |
| **Format** | Prose (ambiguous) | YAML with constraints and tests |
| **Verification** | Manual review | AI verifies against executable constraints |
| **Result** | AI guesses, many turns | AI verifies, one turn |

## How It Works

```
1. You describe    →  what you want (natural language)
2. AI writes       →  structured intent artifact (YAML with constraints, tests)
3. You review      →  "Is this what I meant?" (clarification before code)
4. AI implements   →  against the intent
5. AI verifies     →  does my code pass the constraints?
```

## Quick Start

### Copy to Your Project

```bash
# Copy the full framework
cp -r ivd/ /your-project/docs/

# Or just the essentials
cp -r ivd/{README.md,framework.md,cookbook.md,recipes,templates} /target/
```

### Initialize an Existing Project

```bash
# Scans your project and generates a system intent
ivd init --project-root /path/to/your/project
```

### Create Your First Intent

```bash
# 1. Copy the template
cp templates/intent.yaml my-module/my_module_intent.yaml

# 2. Set the scope
# scope:
#   level: "module"        # system | workflow | module | task
#   type: "feature"        # product | process | feature | function

# 3. Fill in the intent — or let the AI write it for you
```

## MCP Server

IVD ships with a **Model Context Protocol (MCP) server** that gives any AI agent direct access to the framework — 14 tools for searching, validating, scaffolding, and discovering IVD artifacts.

**Remote (SSE)**

```json
{
  "mcpServers": {
    "ivd": {
      "url": "https://mcp.ivdframework.dev/sse",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

**Local (stdio)**

```json
{
  "mcpServers": {
    "ivd": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/ivd"
    }
  }
}
```

### Available Tools

| Tool | What it does |
|------|-------------|
| `ivd_get_context` | Load framework principles, cookbook, or cheatsheet |
| `ivd_search` | Semantic search across all IVD knowledge (embeddings) |
| `ivd_validate` | Validate an intent artifact against IVD rules |
| `ivd_scaffold` | Generate a new intent artifact from a template |
| `ivd_init` | Initialize IVD in an existing project (system intent) |
| `ivd_load_recipe` | Load a specific recipe pattern |
| `ivd_list_recipes` | Browse all available recipes |
| `ivd_load_template` | Load an intent template |
| `ivd_find_artifacts` | Discover intent artifacts in a project |
| `ivd_check_placement` | Verify artifact naming and placement |
| `ivd_list_features` | Derive feature inventory from intent metadata |
| `ivd_propose_inversions` | Generate inversion opportunities (Principle 8) |
| `ivd_discover_goal` | Help users who don't know what to ask |
| `ivd_teach_concept` | Explain concepts before writing intent |

## The Eight Principles

IVD is built on eight immutable principles:

| # | Principle | Core Idea |
|---|-----------|-----------|
| 1 | **Intent is Primary** | Not code, not docs — intent. Everything derives from it. |
| 2 | **Understanding Must Be Executable** | Prose fails silently. Executable constraints fail loudly. |
| 3 | **Bidirectional Synchronization** | Changes flow in any direction with verification. |
| 4 | **Continuous Verification** | Verify alignment at every commit, every change. |
| 5 | **Layered Understanding** | Intent, Constraints, Rationale, Alternatives, Risks. |
| 6 | **AI as Understanding Partner** | AI writes the intent, implements, verifies. Not just executes. |
| 7 | **Understanding Survives Implementation** | Rewrites, team changes, tech shifts — intent persists. |
| 8 | **Innovation through Inversion** | State the default, invert it, evaluate, implement. |

## Recipes

Reusable patterns that encode proven solutions:

| Recipe | Pattern |
|--------|---------|
| [workflow-orchestration](recipes/workflow-orchestration.yaml) | Multi-step process orchestration |
| [agent-classifier](recipes/agent-classifier.yaml) | AI classification agents |
| [infra-background-job](recipes/infra-background-job.yaml) | Background job processing |
| [data-field-mapping](recipes/data-field-mapping.yaml) | Data source/target field mapping |
| [coordinator-intent-propagation](recipes/coordinator-intent-propagation.yaml) | Multi-agent intent delegation |
| [teaching-before-intent](recipes/teaching-before-intent.yaml) | Teaching concepts before intent |
| [discovery-before-intent](recipes/discovery-before-intent.yaml) | Goal discovery before intent |
| [doc-meeting-insights](recipes/doc-meeting-insights.yaml) | Documentation extraction |

## Intent Levels

IVD supports four levels of granularity:

```
SYSTEM       →  Entire system or product
  ↓
WORKFLOW     →  Multi-step process across modules
  ↓
MODULE       →  Feature, agent, or component
  ↓
TASK         →  Function, method, or API endpoint
```

| Level | Location | Example |
|-------|----------|---------|
| System | Root: `system_intent.yaml` | `system_intent.yaml` |
| Workflow | `workflows/{name}_intent.yaml` | `workflows/lead_qualification_intent.yaml` |
| Module | `{module}/{module}_intent.yaml` | `agent/marketing/marketing_intent.yaml` |
| Task | `{module}/intents/{task}_intent.yaml` | `agent/marketing/intents/gen_article_intent.yaml` |

## Project Structure

```
ivd/
├── README.md                           # This file
├── purpose.md                          # Why IVD exists (vision)
├── framework.md                        # Complete specification
├── cookbook.md                          # Practical guide with examples
├── cheatsheet.md                       # Quick reference
├── recipe-spec.md                      # Recipe specification
├── ivd_system_intent.yaml              # System intent (rules for extending IVD)
│
├── recipes/                            # Reusable pattern templates
│   ├── workflow-orchestration.yaml
│   ├── agent-classifier.yaml
│   ├── infra-background-job.yaml
│   └── ...
│
├── templates/                          # Blank templates
│   ├── intent.yaml                     # Intent artifact template
│   ├── recipe.yaml                     # Recipe template
│   └── examples/                       # Complete worked examples
│
├── research/                           # Research and validation
│
├── mcp_server/                         # MCP server (14 tools)
│   ├── server.py                       # Stdio + SSE transports
│   ├── tools/                          # Tool implementations
│   ├── knowledge/                      # Embedding engine
│   ├── brain/ivd/                      # Pre-built embeddings
│   ├── tests/                          # Unit, E2E, smoke tests
│   └── devops/                         # Deploy, embed, test scripts
│
└── book/                               # IVD book (private alpha)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [purpose.md](purpose.md) | Why IVD exists — vision, philosophy, breakthrough insight |
| [framework.md](framework.md) | Complete IVD specification — principles, rules, validation |
| [cookbook.md](cookbook.md) | Practical guide — step-by-step with real examples |
| [cheatsheet.md](cheatsheet.md) | Quick reference — one-page summary |
| [recipe-spec.md](recipe-spec.md) | How to create and maintain recipes |
| [templates/intent_levels_guide.md](templates/intent_levels_guide.md) | When to use system vs workflow vs module vs task |

## Development

### Run Tests

```bash
./mcp_server/devops/test.sh              # All tests (unit + e2e)
./mcp_server/devops/test.sh --unit       # Unit tests only
./mcp_server/devops/test.sh --e2e        # E2E tests only
./mcp_server/devops/test.sh --smoke      # Smoke tests (live server)
```

### Generate Embeddings

```bash
./mcp_server/devops/embed.sh             # Regenerate all embeddings
./mcp_server/devops/search.sh "query"    # Query embeddings locally
```

### Deploy

```bash
./mcp_server/devops/deploy.sh            # Full deploy (embed + test + push + verify)
./mcp_server/devops/deploy.sh --status   # Check deployment status
./mcp_server/devops/deploy.sh --health   # Health check
./mcp_server/devops/deploy.sh --smoke    # Post-deploy smoke tests
```

## Portability

IVD is **zero-dependency** — just Markdown and YAML files. Copy it to any project:

```bash
cp -r ivd/{README.md,framework.md,cookbook.md,recipes,templates} /your-project/docs/
```

No build step. No package manager. No runtime. Works everywhere.

## The Methodology in One Sentence

> **AI writes the intent, implements against it, verifies — so hallucinations are caught and turns drop to one.**

---

**Created by** Leo Celis | **Version** 1.3 | **Status** Private Alpha
