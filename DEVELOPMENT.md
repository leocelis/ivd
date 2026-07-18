# Development

## Setup

```bash
git clone https://github.com/leocelis/ivd.git
cd ivd
./mcp_server/devops/setup.sh    # creates .venv, installs all deps (macOS/Linux)
# or, using the packaging metadata:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,search,compliance]"
```

## Running tests

```bash
./mcp_server/devops/test.sh              # all tests (unit + e2e)
./mcp_server/devops/test.sh --unit       # unit only
./mcp_server/devops/test.sh --e2e        # e2e only

# equivalent, directly:
.venv/bin/python -m pytest mcp_server/tests --ignore=mcp_server/tests/smoke -q
```

Tests run fully offline — no API keys required. `mcp_server/tests/unit/test_embeddings.py`
skips cleanly without `OPENAI_API_KEY`.

## Lint and type-check

`ruff` and `mypy` are configured in `pyproject.toml`:

```bash
.venv/bin/ruff check .
.venv/bin/mypy mcp_server canon judgment
```

Neither is wired into CI yet as a required check — see [ROADMAP.md](ROADMAP.md). Run
them locally before opening an issue/PR with a code change.

## Adding a new MCP tool

A tool touches three places. Using `ivd_get_context` as the pattern to copy:

1. **Implementation** — a function in `mcp_server/tools/<module>.py` that returns a
   JSON-serializable dict (tools return `json.dumps(...)` strings — see any existing
   tool function for the exact contract).
2. **Export** — add the function to `mcp_server/tools/__init__.py`'s import/export list
   so `registry.py` can import it.
3. **Registration** — in `mcp_server/registry.py`, add two entries:
   - a `Tool(name=..., description=..., inputSchema={...})` object in the tool list
     (this is what `tools/list` returns to the MCP client)
   - a `"tool_name": lambda **kwargs: your_function(...)` entry in `TOOL_HANDLERS`
     (this is what actually dispatches the call)

There is no decorator-based auto-registration — both places must be updated by hand and
kept in sync. `registry.py`'s own module docstring states the current tool count per
phase (core / judgment / canon); update it if you add or remove a tool, since that count
is what README.md, `.env.example`, and `server.json` are meant to mirror.

## Adding a recipe

Drop a new `recipes/<name>.yaml` following the shape of an existing recipe (see
`recipes/README.md`), then add a row to the Recipes table in `README.md`.

## Project layout

```
mcp_server/   MCP server, tool implementations, tests
canon/        Canon (Phase 0) engine — human-translation-layer rules + tools
judgment/     Judgment (Phase 4) engine — capture/codify/cluster/inject
recipes/      Reusable IVD patterns (YAML)
templates/    Intent artifact templates
examples/     Runnable demos (judgment_demo/, intent_demo/)
docs/         Positioning, integration guides
deploy/       DigitalOcean App Platform deployment files (hosted server only —
              irrelevant to local/self-hosted use)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the current policy on issues, discussions,
and pull requests.
