# Roadmap

Informal — updated as priorities shift. For what already shipped, see
[CHANGELOG.md](CHANGELOG.md).

## Shipped

- Core loop: Intent → Implementation → Verification (18 core MCP tools)
- Spec-tool import (`ivd_import_spec`): parse GitHub Spec Kit / OpenSpec `spec.md`
  into an IVD constraint scaffold
- Judgment phase (v3.0, opt-in via `.judgment/`) — compounding corrections
- Canon phase (v3.1) — human-translation-layer rules + MCP tools
- `pyproject.toml` packaging (`pip install .` / `pip install -e .`)
- Offline runnable demo of the core loop (`examples/intent_demo/`)

## Next

- **Publish to PyPI** so `uvx ivd-mcp` works without cloning. Requires a maintained
  release process (see "Release integrity" below) before it ships.
- **Release integrity**: tag `v3.0.0` and `v3.1.0` retroactively (or fold into a fresh
  `v3.2.0` release), so the GitHub Releases page, the version badge, and `main` agree.
  Going forward, every version bump gets a git tag + GitHub release + CHANGELOG entry
  in the same PR.
- **`ivd_search` without an API key**: ship pre-built embeddings as a release artifact,
  or evaluate a local embedding model, so semantic search doesn't require an
  `OPENAI_API_KEY` in the default local setup.
- **Lint/typecheck in CI**: `ruff` + `mypy` are configured in `pyproject.toml`
  ([DEVELOPMENT.md](DEVELOPMENT.md)). First real run (2026-07-18) against the existing
  codebase: `ruff` flags import-order (I001) in 5 pre-existing files (not enforced
  before now — deliberately not bulk-reformatted, see comment in `pyproject.toml`);
  `mypy` surfaces 16 pre-existing type errors across 9 files (`discover.py`,
  `scaffold.py`, `learning.py`, `validate.py`, `judgment/schema.py`, `judgment/inject.py`,
  `judgment/detect.py`, `mcp_server/tools/judgment.py`, `mcp_server/knowledge/brain.py`).
  None are regressions from new code — new modules (e.g. `import_spec.py`) are clean
  under both. Wiring either into CI as a *required* check needs this pre-existing debt
  cleared first, or CI would fail on day one for reasons unrelated to a given PR.
- **Windows install path**: mostly unblocked by `pyproject.toml`/PyPI (pip and uvx work
  cross-platform); the bash-only `mcp_server/devops/*.sh` scripts remain
  macOS/Linux-only for local dev.

## Explicitly not planned right now

- Renaming the project. "IVD" collides with an established meaning (in-vitro
  diagnostics) and the SEO cost is real, but a rename is a one-way brand decision that
  needs to be made deliberately, not folded into an audit pass.
- A general external-contribution / PR-acceptance policy change. Current policy
  (issues and discussions welcome, PRs not yet accepted — see
  [CONTRIBUTING.md](CONTRIBUTING.md)) is a maintainer-bandwidth decision, not a bug.
