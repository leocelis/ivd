# Deploying IVD MCP Server (Remote / SSE)

Most users should run IVD **locally via stdio** — see the [main README](../README.md) for setup.

This directory contains files for deploying the IVD MCP server as a remote SSE endpoint on DigitalOcean App Platform.

## Files

| File | Purpose |
|------|---------|
| `build.sh` | **Canonical build script** — installs deps, generates embeddings, verifies brain |
| `Procfile` | Process definition for DO App Platform (run command) |
| `runtime.txt` | Python version pin |
| `wsgi.py` | WSGI entry point — creates the SSE app |

## How Deployment Works

1. Push to `main` triggers DO auto-deploy
2. DO runs the **build command** (`bash deploy/build.sh`), which:
   a. Installs Python dependencies from `requirements.txt`
   b. Verifies `OPENAI_API_KEY` is present (fails the build if not)
   c. Generates embeddings from the public framework files via `mcp_server/devops/embed.py`
   d. Verifies `mcp_server/brain/ivd/index.json` exists with ≥ 10 docs (fails the build on silent embed failure — prevents `ivd_search` from degrading to "Knowledge base not found" in production)
3. DO starts the server using `wsgi.py` (per `Procfile`)

Embeddings are generated at build time from the public framework files in the repo. No pre-built brain is shipped — it's created fresh on every deploy.

### What the embedding scan includes / excludes

The `scan_directory` function in `mcp_server/knowledge/brain.py` is the authoritative source. Two layers of defense ensure private content never ends up in the public knowledge base:

| Layer | Mechanism | Excludes |
|-------|-----------|----------|
| Git | `.gitignore` | `_private/`, `mcp_server/brain/`, `temp/`, `.env` — never even pushed |
| Embeddings | `brain.SKIP_DIRS` + `PRIVATE_PREFIX = "_"` + dotfile rule | `_private/`, any `_*` dir, any `.*` dir, `mcp_server/`, `deploy/`, `temp/`, etc. |

The `_private/` exclusion is locked in by `mcp_server/tests/unit/test_brain_scan.py::test_real_repo_excludes_private`, which runs as part of the standard pytest suite (and is therefore enforced in CI on every PR).

## Prerequisites

- DigitalOcean account with App Platform access
- Redis instance (for MCP session storage)
- OpenAI API key (for embedding generation at build time + search queries at runtime)

## Environment Variables

Set these in the DO dashboard (Settings → Environment Variables):

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Embedding generation + search queries |
| `REDIS_URL` | Yes | Redis connection string |
| `IVD_API_KEYS` | Yes | Comma-separated API keys for client auth |

## App Spec

Key settings used for the DO app spec:

```yaml
build_command: "bash deploy/build.sh"
run_command: "python deploy/wsgi.py --port 8080"
```

The `build_command` is intentionally a single call to `deploy/build.sh` so that ALL build steps are version-controlled in this repo (and reviewable in PRs) rather than living in the DO dashboard. To change build behavior, edit `deploy/build.sh` and push — no dashboard edit required.

To update the live app spec with `doctl`, point to your own `app.yaml` (see the [doctl docs](https://docs.digitalocean.com/reference/doctl/reference/apps/update/)):

```bash
doctl apps update <app_id> --spec path/to/app.yaml
```

**One-time DO dashboard update required:** if your DO app is currently configured with a different `build_command`, change it once to `bash deploy/build.sh` (Settings → App Spec → edit `build_command`). After that, no further dashboard edits are needed for build-time changes.

## Local Development (SSE mode)

To test the SSE server locally:

```bash
./mcp_server/devops/setup.sh
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and REDIS_URL
./mcp_server/devops/embed.sh
python deploy/wsgi.py --port 8080
```

## API Key Management

`IVD_API_KEYS` is a comma-separated list of tokens set in your DO environment variables. To add or revoke a key:

1. Generate a random token (e.g. `openssl rand -hex 32`)
2. Prepend a username prefix for easy identification: `alice_<token>`
3. Update `IVD_API_KEYS` in the DO dashboard (append or remove entries) and redeploy
