# IVD Gaps: Existing Projects, Project Context, and Project Map

**Created:** 2026-02-04  
**Purpose:** Cross-check whether the framework addresses creating intents for existing projects, reusing project context (rules, architecture, tools, docs), and installing IVD with a root-level master intent + "map to the stars" (intents referencing master intent and specific project routes/paths).  
**Status:** Gap analysis complete

---

## 1. What You Mentioned (List)

1. **Creating artifacts for existing projects**  
   - The codebase already has documentation and code (same repo).  
   - When creating a new intent we should consider the existing project, not assume greenfield.

2. **Reusing and referencing existing project assets when creating new intents**
   - Reuse **existing code rules** (e.g. .cursorrules, lint/format rules).
   - Reuse **architecture principles** (e.g. docs/ARCHITECTURE.md, ADRs).
   - Reuse **tools, scripts, functions, libraries** (don’t duplicate; reference where they live).
   - **Reference existing docs** so intents point to current explanations and runbooks.

3. **Installing IVD in a new (or existing) project — scaffold at root**
   - When “installing” IVD in a project, the scaffold should create a **master intent at root level**.
   - That master intent should hold **all this information**: code rules, architecture principles, tools, scripts, key paths, references to existing docs — i.e. **project context**.

4. **New intents reference (1) master intent and (2) specific routes inside the project**
   - As we create new intents (co-located with code), they should:
     - **(1)** Reference the **master intent** (project-level system intent).
     - **(2)** Reference **specific routes/paths** inside the project — like a **“map to the stars”** (Escape from LA): a navigable map of where things live (entrypoints, modules, scripts, key docs).

---

## 2. Cross-Check: Does the Framework Address This?

### 2.1 Creating artifacts for existing projects

| Aspect | Addressed? | Where | Notes |
|--------|------------|--------|--------|
| Intent for a module that already exists | **Partially** | framework.md "Step 1: Create Intent Artifact for Existing Module" | Describes `ivd intent create <path>` that analyzes existing code, extracts constants, searches git/playground/docs. |
| Workflow for “existing project” (brownfield) | **No** | — | No dedicated “existing project” or “brownfield” workflow. No “discover project first, then create intents that fit.” |
| Consider existing conventions before writing intent | **No** | — | No step “load project code rules and architecture before writing intent.” |

**Verdict:** The framework supports **creating an intent from existing code** for one module. It does **not** define a full “existing project” workflow (discover conventions, docs, tools; then create intents that reference them).

---

### 2.2 Reusing code rules, architecture, tools, scripts, libraries, existing docs

| Aspect | Addressed? | Where | Notes |
|--------|------------|--------|--------|
| Intent schema section for “project code rules” | **No** | templates/intent.yaml, framework.md | No `project_conventions`, `code_rules`, or `references` section in the canonical intent schema. |
| Intent schema section for “architecture principles” | **No** | — | No field like `architecture_ref` or `adr_ref`. |
| Referencing tools, scripts, functions, libraries | **No** | — | No optional section “reuse: scripts, libs” or “implementation.reuse”. |
| Referencing existing docs | **Partial** | rationale.evidence, implementation.documentation | Evidence and docs can be linked; no structured “existing_docs” or “project_docs” list. |
| INTENT_LEVELS_GUIDE parent_intent | **Yes** | templates/intent_levels_guide.md, templates/intent.yaml | Workflow/module can reference parent system intent (`parent_intent: "../../book_system_intent.yaml"`). Present in templates/intent.yaml as optional commented field. |

**Verdict:** Reuse of **existing** code rules, architecture, tools, scripts, and docs is **not** modeled in the intent schema. Only “evidence” and “documentation” links exist; no project-level conventions or reuse list. Parent intent is documented in the guide but not in the canonical template.

---

### 2.3 Installing IVD: scaffold creates master intent at root with project context

| Aspect | Addressed? | Where | Notes |
|--------|------------|--------|--------|
| System-level intent at repo root | **Yes** | framework.md, templates | `system_intent.yaml` or `{project}_system_intent.yaml` at root is documented. |
| “Install IVD” / bootstrap flow | **No** | — | No documented “ivd init” or “ivd bootstrap” that creates the project. |
| Scaffold creates system intent | **Yes** | tools: ivd_scaffold(level='system', name=...) | Creates a file from generic intent.yaml; does **not** pre-fill project context. |
| Master intent contains “project context” | **No** | — | No schema for “code rules, architecture, tools, key paths, project map” in system intent. |
| research/ivd_implementation_roadmap | **Partial** | migrate_to_ivd(), IVDConfig, .ivd/ | Migration from .cursorrules to .ivd/; no “create system_intent.yaml with project map and conventions.” |

**Verdict:** System intent at root exists as a concept and can be scaffolded as a **generic** intent. There is **no** “install IVD” flow that creates a **project-specific** master intent filled with code rules, architecture, tools, and project map.

---

### 2.4 New intents reference (1) master intent and (2) specific routes (map to the stars)

| Aspect | Addressed? | Where | Notes |
|--------|------------|--------|--------|
| Child intent references parent system intent | **Yes** | INTENT_LEVELS_GUIDE, templates/intent.yaml, framework.md | Example: `parent_intent: "../../book_system_intent.yaml"`. Present in templates/intent.yaml as optional commented field with examples. |
| Intent references “specific routes/paths” in project | **No** | — | No “project_map”, “key_paths”, “routes”, or “discovery_map” in intent schema. |
| “Map to the stars” (navigable project map) | **No** | — | No concept of a project-level map of entrypoints, modules, scripts, key docs that intents point into. |
| System intent as “map” of the project | **No** | — | System intent is product/platform scope, not “where things live” (paths, routes, entrypoints). |

**Verdict:** Referencing the **master** (system) intent is possible in practice and shown in the guide, but **not** in the canonical template. Referencing **specific routes/paths** (project map) is **not** in the framework.

---

## 3. Gaps by Area

### 3.1 Framework (framework.md, ivd_system_intent.yaml)

- No **“existing project / brownfield”** section or principle.
- No **schema for project-level context** in system intent, e.g.:
  - `code_rules` / `conventions` (e.g. paths to .cursorrules, lint configs)
  - `architecture_principles` / `architecture_docs` (e.g. ARCHITECTURE.md, ADRs)
  - `tools_scripts` (key scripts, CLIs, entrypoints)
  - `libraries` / `reuse` (shared libs to use, not reimplement)
  - `project_map` / `key_paths` / `routes` (navigable map of important paths)
- No **requirement** that new intents reference the project system intent or the project map.
- “Create intent for existing module” is **generate-from-code only**; no “consider existing conventions and docs when writing intent.”

### 3.2 Docs (cookbook, README, cheatsheet, INTENT_LEVELS_GUIDE)

- **README** Quick Start: “Copy ivd folder” — no “run ivd init to create project system intent with project context.”
- **Cookbook:** “Check before building” (list features) only; no “load project conventions and map before writing intent.”
- **INTENT_LEVELS_GUIDE & templates/intent.yaml:** `parent_intent` is present in both as optional commented field. No `project_map` / `key_paths`.
- No dedicated doc: **“Installing IVD in an existing project”** or **“Bootstrap: create master intent with project map.”**

### 3.3 Tools (mcp_api/ivd/tools.py)

- **ivd_scaffold:** Creates a blank/generic intent at the canonical location. Does **not**:
  - Create or update a project root system intent with project context.
  - Pre-fill from .cursorrules, ARCHITECTURE.md, or key paths.
- No **ivd_init** / **ivd_bootstrap** tool that:
  - Creates `system_intent.yaml` (or `{project}_system_intent.yaml`) at project root.
  - Optionally fills it with: code_rules, architecture_refs, tools_scripts, project_map (key_paths/routes).
- No tool to **“generate or update project system intent from existing .cursorrules, docs, key paths.”**
- **project_root** is used only for “where to put/find artifacts,” not “load project context from this root.”

### 3.4 Book (book_system_intent.yaml, Part IV, Ch17)

- **Ch17 “Getting Started: The First Week”** is placeholder only (e.g. “Day 1: Install Templates and Read Core Principles”). No:
  - “Create project master intent with project map.”
  - “Reference existing codebase rules and routes when writing intents.”
- **Part IV Adoption:** No chapter or section on **“IVD for existing/brownfield projects”** or **“Project bootstrap and project map.”**
- No **“map to the stars”** / project navigation / key paths concept in the book.

---

## 4. Summary Table

| Your point | Framework | Docs | Tools | Book |
|------------|-----------|------|--------|------|
| Creating artifacts for existing projects | Partial (create from existing code only) | No brownfield workflow | Same | Not covered |
| Reuse code rules, architecture, tools, scripts, libs, existing docs | No schema | No | No | No |
| Install IVD → scaffold master intent at root with project context | No project-context schema | No bootstrap doc | No init/bootstrap | No |
| New intents reference (1) master intent | Guide example only, not in template | In INTENT_LEVELS_GUIDE | No enforcement | No |
| New intents reference (2) specific routes (map to the stars) | No | No | No | No |

---

## 5. Recommended Directions (for future work)

- **Schema:** Add optional **project context** to system intent: `code_rules`, `architecture_refs`, `tools_scripts`, `project_map` (key_paths/routes). Add optional `parent_intent` and `key_paths` (or `project_map_ref`) to module/workflow/task intents.
- **Process:** Document **“IVD for existing projects”**: discover conventions and map first, then create intents that reference them; and **“Bootstrap”**: create/update root system intent with project context.
- **Tools:** Add **ivd_init** / **ivd_bootstrap** that creates/updates project root system intent (and optionally project map); consider tools that ingest .cursorrules/docs to pre-fill context.
- **Book:** In Ch17 and Part IV, add **“First week: project master intent and map”** and **“Adopting IVD in an existing codebase”** (reference master intent and routes).

This document can be used to drive framework extensions, doc updates, tool changes, and book content.
