<p align="center">
  <strong>Intent-Verified Development (IVD)</strong><br>
  <em>A framework where AI writes the intent, implements against it, and verifies — so hallucinations are caught and turns drop to one.</em>
</p>

<p align="center">
  <a href="https://github.com/leocelis/ivd/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/version-2.4-blue?style=flat-square" alt="Version"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.12"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/MCP-compatible-purple?style=flat-square" alt="MCP Compatible"></a>
  <a href="https://github.com/leocelis/ivd"><img src="https://img.shields.io/badge/tests-211_passed-brightgreen?style=flat-square" alt="Tests"></a>
</p>

---

## The Problem

AI agents hallucinate not because they're bad — but because you're feeding the wrong knowledge system.

LLMs rely ~70% on **contextual knowledge** (the prompt) and ~30% on **parametric knowledge** (training data). When you give vague prose — a PRD, a user story, a chat message — the context channel is underloaded. The model fills the gaps from training. Those gaps are the hallucinations.

```
Without IVD                              With IVD

You: "Add CSV export"                    You: "Add CSV export for compliance"
AI:  [builds with wrong columns]         AI:  [writes intent.yaml with constraints]
You: "No, these columns, ISO dates"      You:  "Yes, that's what I meant"
AI:  [rewrites, still wrong]             AI:  [implements, verifies against constraints]
You: "Still not right..."                You:  "Done. First try."
  Many turns. Many hallucinations.         One turn. Zero hallucinations.
```

**IVD saturates the contextual channel** with structured, verifiable intent — so the model has nothing to guess.

---

## Quick Start

**Works locally. No API key required. Under 5 minutes.**

### 1. Clone and setup

```bash
git clone https://github.com/leocelis/ivd.git
cd ivd
./mcp_server/devops/setup.sh    # creates .venv, installs all deps
```

### 2. Add to your IDE

**Cursor** (Settings → Features → MCP):

```json
{
  "servers": {
    "ivd": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/ivd"
    }
  }
}
```

**VS Code / GitHub Copilot** (`.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "ivd": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/ivd"
    }
  }
}
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ivd": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/ivd"
    }
  }
}
```

### 3. Use it

Ask your AI agent to use IVD tools. For example:

- *"Use ivd_get_context to learn about the IVD framework"*
- *"Use ivd_scaffold to create an intent for my user authentication module"*
- *"Use ivd_validate to check my intent artifact"*

That's it. 14 of 15 tools work immediately with zero configuration.

### 4. Enable semantic search (optional)

`ivd_search` requires embeddings. Generate them once (~$0.01, under a minute):

```bash
export OPENAI_API_KEY=your-key
./mcp_server/devops/embed.sh
```

---

## How It Works

```
1. You describe      →  what you want (natural language)
2. AI writes         →  structured intent artifact (YAML with constraints and tests)
3. You review        →  "Is this what I meant?" (clarification before code)
4. AI stress-tests   →  edge cases, gaps, assumptions, constraint conflicts
5. AI implements     →  constraint-segmented (group → implement → re-read → verify → next)
6. AI verifies       →  full sweep: does every constraint pass?
```

The key insight: clarification happens at the **intent stage**, not after code. The AI writes a verifiable contract, you approve it, then implementation is mechanical — and self-verifying.

---

## MCP Tools

15 tools available to any MCP-compatible AI agent:

| Tool | What it does |
|------|-------------|
| `ivd_get_context` | Load framework principles, cookbook, or cheatsheet |
| `ivd_search` | Semantic search across all IVD knowledge |
| `ivd_validate` | Validate an intent artifact against IVD rules |
| `ivd_scaffold` | Generate a new intent artifact from a template |
| `ivd_init` | Initialize IVD in an existing project |
| `ivd_assess_coverage` | Scan a project and report intent coverage |
| `ivd_load_recipe` | Load a specific recipe pattern |
| `ivd_list_recipes` | Browse all available recipes |
| `ivd_load_template` | Load an intent or recipe template |
| `ivd_find_artifacts` | Discover intent artifacts in a project |
| `ivd_check_placement` | Verify artifact naming and placement |
| `ivd_list_features` | Derive feature inventory from intent metadata |
| `ivd_propose_inversions` | Generate inversion opportunities |
| `ivd_discover_goal` | Help users who don't know what to ask |
| `ivd_teach_concept` | Explain concepts before writing intent |

---

## The Eight Principles

| # | Principle | Core Idea |
|---|-----------|-----------|
| 1 | **Intent is Primary** | Not code, not docs — intent. Everything derives from it. |
| 2 | **Understanding Must Be Executable** | Prose fails silently. Executable constraints fail loudly. |
| 3 | **Bidirectional Synchronization** | Changes flow in any direction with verification. |
| 4 | **Continuous Verification** | Verify alignment at every commit, every change. |
| 5 | **Layered Understanding** | Intent, Constraints, Rationale, Alternatives, Risks. |
| 6 | **AI as Understanding Partner** | AI writes, implements, verifies. Not just executes. |
| 7 | **Understanding Survives Implementation** | Rewrites, team changes, tech shifts — intent persists. |
| 8 | **Innovation through Inversion** | State the default, invert it, evaluate, implement. |

Deep dive: [purpose.md](purpose.md) · [framework.md](framework.md) · [cheatsheet.md](cheatsheet.md)

---

## Recipes

13 reusable patterns that encode proven solutions:

| Recipe | Pattern |
|--------|---------|
| [agent-rules-ivd](recipes/agent-rules-ivd.yaml) | Embed IVD verification in `.cursorrules` or any agent config |
| [workflow-orchestration](recipes/workflow-orchestration.yaml) | Multi-step process orchestration |
| [agent-classifier](recipes/agent-classifier.yaml) | AI classification agents |
| [agent-role-based](recipes/agent-role-based.yaml) | Context-dependent agent behavior |
| [agent-capability-propagation](recipes/agent-capability-propagation.yaml) | Propagate agent capabilities to coordinator routing |
| [coordinator-intent-propagation](recipes/coordinator-intent-propagation.yaml) | Multi-agent intent delegation |
| [self-evaluating-workflow](recipes/self-evaluating-workflow.yaml) | Continuous improvement loops |
| [data-field-mapping](recipes/data-field-mapping.yaml) | Data source/target field mapping |
| [infra-background-job](recipes/infra-background-job.yaml) | Background job processing |
| [infra-structured-logging](recipes/infra-structured-logging.yaml) | Structured JSON logging |
| [teaching-before-intent](recipes/teaching-before-intent.yaml) | Teach concepts before writing intent |
| [discovery-before-intent](recipes/discovery-before-intent.yaml) | Goal discovery before intent |
| [doc-meeting-insights](recipes/doc-meeting-insights.yaml) | Documentation extraction from meetings |

---

## Configuration

IVD works out of the box with zero configuration. Optional settings for advanced use:

```bash
cp .env.example .env
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | For `ivd_search` | Generate embeddings and run semantic search |
| `REDIS_URL` | No | Session storage for remote server deployment |
| `IVD_API_KEYS` | No | Auth for remote server deployment |

Embeddings are not shipped in the repo — they are generated locally. To enable `ivd_search`:

```bash
export OPENAI_API_KEY=your-key
./mcp_server/devops/embed.sh          # generate (~$0.01)
./mcp_server/devops/embed.sh --force  # regenerate all
./mcp_server/devops/embed.sh --dry-run # preview what gets embedded
```

---

## Hosted Server

A hosted IVD MCP server is available for users who prefer not to run it locally.

**Request access:** [leo@leocelis.com](mailto:leo@leocelis.com)

Once you have an API key, connect via SSE:

**Cursor** (Settings → Features → MCP):

```json
{
  "servers": {
    "ivd-remote": {
      "type": "sse",
      "url": "https://mcp.ivdframework.dev/sse",
      "headers": { "Authorization": "Bearer your-api-key" }
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ivd-remote": {
      "url": "https://mcp.ivdframework.dev/sse",
      "headers": { "Authorization": "Bearer your-api-key" }
    }
  }
}
```

All 15 tools are available on the hosted server, including `ivd_search` (embeddings are pre-generated).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [purpose.md](purpose.md) | Why IVD exists — the cognitive case, two knowledge systems |
| [framework.md](framework.md) | Complete specification — principles, rules, validation |
| [cookbook.md](cookbook.md) | Practical guide — step-by-step with real examples |
| [cheatsheet.md](cheatsheet.md) | Quick reference — one-page summary |

---

## Development

```bash
# Setup
./mcp_server/devops/setup.sh             # Create venv, install deps

# Run tests
./mcp_server/devops/test.sh              # All tests (unit + e2e)
./mcp_server/devops/test.sh --unit       # Unit only
./mcp_server/devops/test.sh --e2e        # E2E only

# Embeddings (requires OPENAI_API_KEY)
./mcp_server/devops/embed.sh             # Generate embeddings
./mcp_server/devops/embed.sh --dry-run   # Preview what gets embedded
./mcp_server/devops/embed.sh --force     # Regenerate everything

# Search embeddings locally (requires generated brain + OPENAI_API_KEY)
./mcp_server/devops/search.sh "query"
```

---

## The Book

A comprehensive book on Intent-Verified Development — the cognitive foundations, case studies, and the full methodology — is coming soon.

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT](LICENSE) · Created by [Leo Celis](https://github.com/leocelis)
