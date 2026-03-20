# Deploying IVD MCP Server (Remote / SSE)

Most users should run IVD **locally via stdio** — see the [main README](../README.md) for setup.

This directory contains files for deploying the IVD MCP server as a remote SSE endpoint on DigitalOcean App Platform.

## Files

| File | Purpose |
|------|---------|
| `Procfile` | Process definition for DO App Platform |
| `runtime.txt` | Python version pin |
| `wsgi.py` | WSGI entry point — creates the SSE app |

## How Deployment Works

1. Push to `main` triggers DO auto-deploy
2. DO runs the **build command**: installs deps + generates embeddings from framework files
3. DO starts the server using `wsgi.py`

Embeddings are generated at build time from the public framework files in the repo. No pre-built brain is shipped — it's created fresh on every deploy.

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
build_command: "pip install -r requirements.txt && python mcp_server/devops/embed.py"
run_command: "python deploy/wsgi.py --port 8080"
```

To update the live app spec with `doctl`, point to your own `app.yaml` (see the [doctl docs](https://docs.digitalocean.com/reference/doctl/reference/apps/update/)):

```bash
doctl apps update <app_id> --spec path/to/app.yaml
```

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
