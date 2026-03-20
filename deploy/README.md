# Deploying IVD MCP Server (Remote / SSE)

Most users should run IVD **locally via stdio** — see the [main README](../README.md) for setup.

This directory contains files for deploying the IVD MCP server as a remote SSE endpoint on DigitalOcean App Platform.

## Files

| File | Purpose |
|------|---------|
| `Procfile` | Process definition for DO App Platform |
| `runtime.txt` | Python version pin |
| `wsgi.py` | WSGI entry point — creates the SSE app |

## Prerequisites

- DigitalOcean account with App Platform access
- Redis instance (for MCP session storage)
- OpenAI API key (for embedding generation)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | For embedding operations |
| `REDIS_URL` | Yes | Redis connection string |
| `IVD_TRANSPORT` | No | Defaults to `sse` in this context |

## Deploy

1. Fork or push this repo to your GitHub account
2. Create a new App on DO App Platform pointing to the repo
3. Set the environment variables above
4. The `Procfile` handles the rest

For local development of the SSE server:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your-key
export REDIS_URL=redis://localhost:6379
python deploy/wsgi.py --port 8080
```
