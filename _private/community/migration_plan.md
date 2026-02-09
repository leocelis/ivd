# IVD Repository Migration Plan

> Extract IVD from `ada/ada/framework/ivd/` into standalone `leocelis/ivd` private repo,
> deploy MCP server on DigitalOcean, decouple all ADA dependencies.

**Source**: `ada/ada/framework/ivd/` + `ada/ada/mcp_api/ivd/`
**Target**: `leocelis/ivd` (GitHub, private)
**Reference**: `_private/community/community_adoption_intent.yaml`

---

## Target Repository Structure

```
leocelis/ivd
├── .gitignore
├── LICENSE                                  ← TBD (proprietary or MIT for framework)
├── README.md                                ← front door (from existing, adapted)
├── purpose.md
├── framework.md
├── cookbook.md
├── cheatsheet.md
├── recipe-spec.md
├── optimal_structure.md
├── ivd_system_intent.yaml
├── ivd_package_validation_intent.yaml
│
├── recipes/
│   ├── README.md
│   ├── agent-classifier.yaml
│   ├── coordinator-intent-propagation.yaml
│   ├── data-field-mapping.yaml
│   ├── discovery-before-intent.yaml
│   ├── doc-meeting-insights.yaml
│   ├── infra-background-job.yaml
│   ├── teaching-before-intent.yaml
│   └── workflow-orchestration.yaml
│
├── templates/
│   ├── intent.yaml
│   ├── recipe.yaml
│   ├── intent_levels_guide.md
│   ├── task_level_quick_ref.md
│   └── examples/
│       ├── task-level-intent-example.yaml
│       └── workflow-lead-qualification-example.yaml
│
├── research/
│   ├── README.md
│   ├── agent_knowledge_standards.md
│   ├── best_selling_programming_books.md
│   ├── best_selling_programming_books_intent.yaml
│   ├── coordinator_agent_design_patterns.md
│   ├── discovery_before_intent.md
│   ├── intent_artifact_placement_research.md
│   ├── intention_research.md
│   ├── ivd_existing_projects_and_project_map_gaps.md
│   ├── ivd_implementation_roadmap.md
│   ├── lp_research.md
│   ├── teaching_before_intent.md
│   └── validation_methodology.md
│
├── mcp_server/                              ← standalone MCP server
│   ├── brain/                               ← committed embeddings
│   │   └── ivd/                             ← KB subfolder (framework + book)
│   │       ├── index.json
│   │       ├── {hash}.npy
│   │       └── {hash}.json
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── context.py                       ← ivd_get_context
│   │   ├── recipes.py                       ← ivd_load_recipe, ivd_list_recipes
│   │   ├── templates.py                     ← ivd_load_template
│   │   ├── validate.py                      ← ivd_validate
│   │   ├── scaffold.py                      ← ivd_scaffold, ivd_init
│   │   ├── discover.py                      ← ivd_find_artifacts, ivd_check_placement, ivd_list_features
│   │   ├── inversions.py                    ← ivd_propose_inversions
│   │   ├── learning.py                      ← ivd_discover_goal, ivd_teach_concept
│   │   └── search.py                        ← ivd_search
│   ├── knowledge/                           ← ported from ada_libs/knowledge (standalone)
│   │   ├── __init__.py
│   │   ├── brain.py                         ← load_kb_embeddings, get_brain_root
│   │   ├── embedder.py                      ← generate_embeddings, find_most_similar
│   │   ├── processor.py                     ← extract_text, simple_chunk_text
│   │   └── config.py                        ← embedding model, chunk size, etc.
│   ├── __init__.py
│   ├── server.py                            ← SSE + stdio MCP server (standalone)
│   ├── auth.py                              ← API key auth (env-var based, no DB)
│   ├── registry.py                          ← tool registration + call dispatch
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── scripts/
│   ├── embed.sh                             ← generate embeddings (uses ADA tools initially)
│   └── embed_standalone.py                  ← future: standalone embedding script
│
├── _private/
│   ├── README.md
│   ├── ai_driven_dev/                       ← committed (historical)
│   │   ├── README.md
│   │   ├── ai_driven_development_guide.md
│   │   ├── from_lp_to_ivd.md
│   │   ├── meetings.md
│   │   └── meetings_index.md
│   ├── community/                           ← GITIGNORED (launch strategy)
│   │   └── community_adoption_intent.yaml
│   └── book/                                ← GITIGNORED (premium manuscript)
│       ├── README.md
│       ├── book_system_intent.yaml
│       ├── chapter_writing_process_intent.yaml
│       └── manuscript/
│           ├── front-matter/
│           ├── part-1-foundations/
│           │   ├── chapter-01-alignment-crisis/
│           │   ├── chapter-02-ivd-paradigm/
│           │   ├── chapter-03-eight-principles/
│           │   └── chapter-04-intent-artifacts/
│           ├── part-2-practice/
│           ├── part-3-validation/
│           ├── part-4-adoption/
│           └── back-matter/
│
└── .do/                                     ← DigitalOcean App Platform config
    └── app.yaml                             ← app spec for IVD MCP service
```

---

## .gitignore

```gitignore
# Private content - never committed
_private/community/
_private/book/

# Environment
.env
*.pyc
__pycache__/
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## Migration Steps

### Step 1: Create Repository

1. Create `leocelis/ivd` private repo on GitHub (no default files)
2. Clone locally to `~/workspace/leocelis/ivd/`
3. Initialize with `.gitignore` (above)

### Step 2: Copy Framework Content

Move from `ada/ada/framework/ivd/` → repo root:

| Source (ada/ada/framework/ivd/) | Destination (ivd/) | Notes |
|---|---|---|
| `README.md` | `README.md` | Adapt: remove ADA references, add getting-started path |
| `purpose.md` | `purpose.md` | Direct copy |
| `framework.md` | `framework.md` | Direct copy |
| `cookbook.md` | `cookbook.md` | Direct copy |
| `cheatsheet.md` | `cheatsheet.md` | Direct copy |
| `recipe-spec.md` | `recipe-spec.md` | Direct copy |
| `optimal_structure.md` | `optimal_structure.md` | Direct copy |
| `ivd_system_intent.yaml` | `ivd_system_intent.yaml` | Direct copy |
| `ivd_package_validation_intent.yaml` | `ivd_package_validation_intent.yaml` | Direct copy |
| `recipes/` | `recipes/` | Direct copy (entire directory) |
| `templates/` | `templates/` | Direct copy (entire directory) |
| `research/` | `research/` | Direct copy (entire directory) |
| `_private/README.md` | `_private/README.md` | Direct copy |
| `_private/ai_driven_dev/` | `_private/ai_driven_dev/` | Direct copy (committed) |
| `_private/community/` | `_private/community/` | Local only, gitignored |
| `book/` | `_private/book/` | Local only, gitignored |

**Post-copy review**: Grep all copied files for `ada`, `ADA`, `ada.`, `/ada/` references. Replace with generic or IVD-specific paths where needed.

### Step 3: Create Standalone MCP Server

Port from `ada/ada/mcp_api/` but remove all ADA dependencies.

#### 3a. Auth Module (`mcp_server/auth.py`)

**Current ADA auth** (`ada/mcp_api/auth.py`):
- Imports `ada.entity.key.utils.get_tenant_keys`
- Validates API key against ADA's `tenant_key` database table
- Tied to ADA's SQLAlchemy models and PostgreSQL

**New IVD auth** (`mcp_server/auth.py`):
- Read API keys from environment variable: `IVD_API_KEYS` (comma-separated)
- Same Bearer token validation logic
- No database dependency
- Keep `generate_api_key()` and `hash_api_key()` utilities
- Keep `MCP_AUTH_DISABLED` env var for local dev

```python
# Pseudocode for new auth
import os
VALID_KEYS = set(os.environ.get("IVD_API_KEYS", "").split(","))

async def validate_api_key(request):
    # Same Bearer extraction logic as ADA
    # Compare against VALID_KEYS set instead of DB query
```

#### 3b. Server Module (`mcp_server/server.py`)

**Current ADA server** (`ada/mcp_api/server.py`):
- Imports `ada.mcp_api.auth` and `ada.mcp_api.tools`
- Server name: `"ada-tool"`
- DO path setup with `/workspace` symlink for `ada.*` imports

**New IVD server** (`mcp_server/server.py`):
- Import from local `auth` and `registry`
- Server name: `"ivd-tool"`
- Remove `/workspace` symlink logic (no `ada.*` imports)
- Keep: SSE transport, SSEProxyMiddleware, SSEHandledResponse, health check
- Keep: stdio transport for local Cursor use
- Update health check to return IVD-specific info

#### 3c. Tool Registry (`mcp_server/registry.py`)

**Current ADA registry** (`ada/mcp_api/tools.py`):
- Aggregates Trello + IVD tools
- Generic `call_tool` dispatcher

**New IVD registry** (`mcp_server/registry.py`):
- IVD tools only (no Trello)
- Same `get_all_tools()`, `call_tool()` pattern
- Import from `mcp_server.tools.*`

#### 3d. IVD Tools (`mcp_server/tools/`)

**Current** (`ada/mcp_api/ivd/tools.py`): All 15 tools in one 1900-line file.

**New**: Split into logical modules for maintainability:

| Module | Tools | ADA Dependencies to Remove |
|---|---|---|
| `context.py` | `ivd_get_context` | `IVD_FRAMEWORK_PATH` → compute from repo root |
| `recipes.py` | `ivd_load_recipe`, `ivd_list_recipes` | Same path fix |
| `templates.py` | `ivd_load_template` | Same path fix |
| `validate.py` | `ivd_validate` | None (pure YAML parsing) |
| `scaffold.py` | `ivd_scaffold`, `ivd_init` | `_project_root()` → update default to IVD repo |
| `discover.py` | `ivd_find_artifacts`, `ivd_check_placement`, `ivd_list_features` | Same |
| `inversions.py` | `ivd_propose_inversions` | None (pure scaffolding) |
| `learning.py` | `ivd_discover_goal`, `ivd_teach_concept` | None |
| `search.py` | `ivd_search` | Remove `ada.ada_libs.knowledge.*` → use local `knowledge/` |

**Critical path changes:**
- `IVD_FRAMEWORK_PATH`: Currently `Path(__file__).parent.parent.parent / "framework" / "ivd"`. New: `Path(__file__).parent.parent.parent` (repo root IS the framework).
- `_project_root()`: Default changes from ADA repo to IVD repo root.
- `ivd_search`: Import from `mcp_server.knowledge.brain` instead of `ada.ada_libs.knowledge.brain`.
- `ivd_scaffold` description: Remove reference to `"ada intent create"`.

#### 3e. Knowledge Base (`mcp_server/knowledge/`)

Port from `ada/ada/ada_libs/knowledge/` with these changes:

| ADA File | IVD File | Changes |
|---|---|---|
| `brain.py` | `knowledge/brain.py` | `get_brain_root()` → resolve to `mcp_server/brain/`; remove `ada.*` imports |
| `embedder.py` | `knowledge/embedder.py` | Replace `ada.ada_libs.ada_ai.gptlib.utils.client` → direct `openai.OpenAI()`; replace `ada.ada_libs.ada_ai.gptlib.cost_tracking` → remove or log-only; replace `_num_tokens` → direct `tiktoken` |
| `processor.py` | `knowledge/processor.py` | Replace `ada.ada_libs.converters.*` → inline simple text extraction (IVD only has .md, .yaml, .txt files — no PDF/DOCX needed) |
| `config.py` | `knowledge/config.py` | Direct copy, remove ADA-specific comments |
| `utils.py` | `knowledge/config.py` (merge) | `get_embedding_cost()` and `estimate_chars_from_tokens()` → merge into config |

**Simplified processor for IVD** (only needs plain text + YAML + Markdown):

```python
def extract_text(file_path: str) -> Optional[str]:
    """IVD only has .md, .yaml, .txt — no PDF/DOCX converters needed."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
```

**Simplified embedder** (standalone OpenAI client):

```python
import openai
import tiktoken

client = openai.OpenAI()  # uses OPENAI_API_KEY env var
enc = tiktoken.get_encoding("cl100k_base")

def _num_tokens(text: str) -> int:
    return len(enc.encode(text))
```

#### 3f. Dependencies (`mcp_server/requirements.txt`)

```
mcp>=1.0.0
starlette>=0.36.0
uvicorn>=0.27.0
numpy>=1.26.0
openai>=1.12.0
tiktoken>=0.6.0
pyyaml>=6.0
termcolor>=2.4.0
```

**Removed ADA dependencies**: Flask, SQLAlchemy, Celery, Redis, mammoth, PyMuPDF, all ADA internal libs.

#### 3g. Dockerfile (`mcp_server/Dockerfile`)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY mcp_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code + brain data
COPY mcp_server/ ./mcp_server/

# Copy framework content (tools read recipes, templates, etc.)
COPY *.md *.yaml ./
COPY recipes/ ./recipes/
COPY templates/ ./templates/
COPY research/ ./research/

ENV PYTHONPATH=/app
ENV MCP_PATH_PREFIX=""

EXPOSE 9999

CMD ["python", "-m", "mcp_server.server", "--transport", "sse", "--port", "9999"]
```

#### 3h. DO App Spec (`.do/app.yaml`)

```yaml
name: ivd-mcp
region: nyc
services:
  - name: ivd-mcp
    github:
      repo: leocelis/ivd
      branch: main
      deploy_on_push: true
    dockerfile_path: mcp_server/Dockerfile
    http_port: 9999
    instance_size_slug: basic-xxs
    instance_count: 1
    routes:
      - path: /ivd-mcp
    envs:
      - key: IVD_API_KEYS
        scope: RUN_TIME
        type: SECRET
      - key: OPENAI_API_KEY
        scope: RUN_TIME
        type: SECRET
      - key: MCP_PATH_PREFIX
        scope: RUN_TIME
        value: "/ivd-mcp"
    health_check:
      http_path: /health
```

#### 3i. Environment Example (`mcp_server/.env.example`)

```
# IVD MCP Server Configuration

# API keys for MCP access (comma-separated)
IVD_API_KEYS=key1,key2,key3

# OpenAI API key (for ivd_search embedding generation)
OPENAI_API_KEY=sk-...

# Auth disable (local dev only)
MCP_AUTH_DISABLED=false

# Path prefix (for DO reverse proxy)
MCP_PATH_PREFIX=
```

### Step 4: Generate Initial Embeddings

Use ADA's existing `brain.sh` to generate embeddings from the IVD repo content:

```bash
# From ADA root, point at the new IVD repo
cd ~/workspace/leocelis/ada/ada
./tools/devops/knowledge/brain.sh embed ~/workspace/leocelis/ivd

# This generates brain/ivd/ in ADA's brain directory
# Copy the output to the IVD repo
cp -r brain/ivd ~/workspace/leocelis/ivd/mcp_server/brain/ivd
```

The embeddings will cover:
- All framework docs (README, purpose, framework, cookbook, cheatsheet, etc.)
- All recipes and templates
- All research documents
- `_private/ai_driven_dev/` (historical — committed, so visible to scanner)

**Book content**: Since `_private/book/` is gitignored but exists locally, add it to the embedding source:

```bash
# Embed book content separately, merge into same brain
./tools/devops/knowledge/brain.sh embed ~/workspace/leocelis/ivd/_private/book
cp -r brain/book ~/workspace/leocelis/ivd/mcp_server/brain/book
```

Update `ivd_search` to load from both `brain/ivd/` and `brain/book/` subdirectories.

**Future**: Create `scripts/embed_standalone.py` that uses the ported `mcp_server/knowledge/` modules directly, removing the ADA dependency for embedding generation.

### Step 5: Clean Up ADA

After the IVD repo is working independently:

1. **Remove IVD tools from ADA MCP**:
   - Delete `ada/mcp_api/ivd/` directory
   - Remove IVD imports from `ada/mcp_api/tools.py`
   - `get_all_tools()` returns only Trello tools

2. **Remove framework/ivd from ADA**:
   - Delete `ada/ada/framework/ivd/` directory
   - Or: replace with a pointer file `framework/ivd/MOVED.md` pointing to `leocelis/ivd`

3. **Update ADA .cursorrules**:
   - Remove IVD-specific references
   - Update `IVD_FRAMEWORK_INTENT.yaml` path reference
   - Add note: "IVD framework has moved to leocelis/ivd"

4. **Update ADA brain**:
   - Remove `brain/ivd/` from ADA's brain directory (embeddings moved to IVD repo)
   - ADA's `search_brain()` will no longer return IVD results (correct — IVD is independent)

### Step 6: Deploy IVD MCP to DO

1. Push `leocelis/ivd` to GitHub
2. Create DO App from `.do/app.yaml` (or via DO console)
3. Set environment variables:
   - `IVD_API_KEYS`: generate initial keys with `secrets.token_urlsafe(32)`
4. Configure custom domain: `mcp.ivdframework.dev`
5. Deploy and verify:
   - Health check: `GET https://mcp.ivdframework.dev/health`
   - SSE endpoint: `GET https://mcp.ivdframework.dev/sse` (with Bearer token)
   - Test tool call: `ivd_get_context`

### Step 7: Configure Cursor/Copilot for IVD MCP

**For Cursor**: Add to MCP configuration (Cursor → Settings → Features → MCP):

```json
{
  "servers": {
    "ivd": {
      "type": "http",
      "url": "https://mcp.ivdframework.dev/sse",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

**For GitHub Copilot (VS Code)**: Add to MCP settings:

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

For local development (stdio transport):

**Cursor**:
```json
{
  "servers": {
    "ivd-local": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_server.server", "--transport", "stdio"],
      "cwd": "/path/to/ivd"
    }
  }
}
```

**GitHub Copilot**:
```json
{
  "mcpServers": {
    "ivd-local": {
      "command": "python",
      "args": ["-m", "mcp_server.server", "--transport", "stdio"],
      "cwd": "/path/to/ivd"
    }
  }
}
```

---

## ADA Dependencies → Standalone Replacements

| ADA Dependency | Used By | Standalone Replacement |
|---|---|---|
| `ada.entity.key.utils.get_tenant_keys` | `auth.py` | Env var `IVD_API_KEYS` (comma-separated) |
| `ada.mcp_api.auth.validate_api_key` | `server.py` | Local `auth.validate_api_key` |
| `ada.mcp_api.tools.get_all_tools` | `server.py` | Local `registry.get_all_tools` |
| `ada.ada_libs.knowledge.brain.get_brain_root` | `ivd_search` | `Path(__file__).parent / "brain"` |
| `ada.ada_libs.knowledge.brain.load_kb_embeddings` | `ivd_search` | Ported to `knowledge/brain.py` |
| `ada.ada_libs.knowledge.embedder.generate_embeddings` | `ivd_search` | Ported to `knowledge/embedder.py` (direct OpenAI client) |
| `ada.ada_libs.knowledge.embedder.find_most_similar` | `ivd_search` | Ported to `knowledge/embedder.py` (numpy dot product) |
| `ada.ada_libs.knowledge.processor.extract_text` | embedding gen | Simplified: `.md`/`.yaml`/`.txt` only |
| `ada.ada_libs.knowledge.processor.simple_chunk_text` | embedding gen | Ported to `knowledge/processor.py` |
| `ada.ada_libs.knowledge.config.*` | embedder, processor | Ported to `knowledge/config.py` |
| `ada.ada_libs.ada_ai.gptlib.utils.client` | embedder | `openai.OpenAI()` |
| `ada.ada_libs.ada_ai.gptlib.utils._num_tokens` | embedder | `tiktoken.get_encoding("cl100k_base").encode()` |
| `ada.ada_libs.ada_ai.gptlib.cost_tracking` | embedder | Remove (or simple print log) |
| `ada.ada_libs.converters.pdf_extractor` | processor | Remove (IVD has no PDFs) |
| `ada.ada_libs.converters.docx_converter` | processor | Remove (IVD has no DOCX) |

---

## Constraints Verification (from community_adoption_intent.yaml)

| Constraint | How This Plan Satisfies It |
|---|---|
| `standalone_repo` | Zero `ada.*` imports in IVD repo; all dependencies ported or replaced |
| `no_tool_required` | Framework docs, templates, recipes are plain files; MCP is optional tooling |
| `single_getting_started_path` | README.md adapted as front door with numbered getting-started |
| `mcp_api_key_gated` | `auth.py` validates Bearer token against `IVD_API_KEYS` env var |
| `ivd_mcp_separate_service` | Own Dockerfile, own DO managed app, own route `/ivd-mcp` |
| `book_positioned_as_deep_dive` | Book in `_private/book/` (gitignored), not the entry point |

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Data loss during migration | Copy (not move) first; validate all files exist in new repo before deleting from ADA |
| Broken internal references | Grep for `framework/ivd`, `ada/`, `ada.` in all copied files; fix before first commit |
| Embedding quality degradation | Compare search results before/after with same test queries |
| ADA MCP breaks after IVD removal | Remove IVD from ADA only after IVD MCP is deployed and verified |
| Case-sensitivity issues (macOS → Linux) | All filenames already lowercase snake_case (fixed in previous audit) |
| Book content leaks | `.gitignore` covers `_private/book/` and `_private/community/`; verify with `git status` before every push |

---

## Execution Order Summary

1. ✅ **Create repo** → `leocelis/ivd` on GitHub (private)
2. ✅ **Copy framework content** → all docs, recipes, templates, research, _private/ai_driven_dev
3. **Port MCP server** → standalone server, auth, tools, knowledge modules
4. **Generate embeddings** → using ADA tools, output to `mcp_server/brain/`
5. **Test locally** → stdio transport, verify all 15 tools work
6. **Deploy to DO** → app spec, env vars, health check
7. **Test remote** → SSE transport with API key from Cursor
8. **Clean up ADA** → remove IVD tools, framework dir, update cursorrules
9. **Adapt README** → front door with getting-started path, remove ADA language
10. **Generate alpha keys** → distribute to first users
