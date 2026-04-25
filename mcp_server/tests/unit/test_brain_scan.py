# mcp_server/tests/unit/test_brain_scan.py

"""Unit tests for `mcp_server.knowledge.brain.scan_directory`.

Locks in the contract from `mcp_server_intent.yaml::embedding_content_scope`:
embeddings must include framework docs / recipes / templates and must NEVER
include `_private/`, `mcp_server/`, dotfile dirs, or other content listed in
`brain.SKIP_DIRS`.

The deploy build (`deploy/build.sh`) re-runs `embed.py` on every push to main;
without these tests, a regression in `scan_directory` would silently start
shipping private content into the public ivd_search index.
"""

from pathlib import Path

from mcp_server.knowledge.brain import (
    PRIVATE_PREFIX,
    SKIP_DIRS,
    scan_directory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repo(root: Path) -> None:
    """Build a fixture repo with both 'should embed' and 'must NOT embed' content."""
    # public content — these MUST appear in the scan
    (root / "framework.md").write_text("# Public IVD framework doc\n")
    (root / "recipes").mkdir()
    (root / "recipes" / "agent-classifier.yaml").write_text("recipe:\n  name: x\n")
    (root / "templates").mkdir()
    (root / "templates" / "intent.yaml").write_text("scope:\n  level: module\n")

    # private content — these MUST be excluded
    (root / "_private").mkdir()
    (root / "_private" / "secrets.md").write_text("# DO NOT EMBED — private notes\n")
    (root / "_private" / "books").mkdir()
    (root / "_private" / "books" / "draft.md").write_text("# DO NOT EMBED\n")

    # other underscore-prefixed dir (e.g. _drafts) — also excluded by convention
    (root / "_drafts").mkdir()
    (root / "_drafts" / "wip.md").write_text("# DO NOT EMBED\n")

    # SKIP_DIRS members — also excluded
    (root / "mcp_server").mkdir()
    (root / "mcp_server" / "server.py").write_text("# implementation, not knowledge\n")
    (root / "deploy").mkdir()
    (root / "deploy" / "build.sh").write_text("#!/bin/bash\n")
    (root / "temp").mkdir()
    (root / "temp" / "scratch.md").write_text("# scratch\n")

    # dotfile dir — excluded by the dotfile rule
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")


def _names(scan_results) -> set[str]:
    return {r["name"] for r in scan_results}


def _paths(scan_results) -> list[str]:
    return [r["path"] for r in scan_results]


def _rel_parts(scan_results, root: Path) -> list[tuple[str, ...]]:
    """Return scan result paths as tuples of parts relative to `root`.

    Avoids substring false positives on macOS where tmp_path resolves to
    `/private/var/folders/...` (which contains the literal substring `_private`).
    """
    return [Path(r["path"]).resolve().relative_to(root.resolve()).parts for r in scan_results]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_private_prefix_is_underscore(self):
        """The private convention is the underscore prefix — locked."""
        assert PRIVATE_PREFIX == "_"

    def test_underscore_private_in_skip_dirs(self):
        """`_private` is also explicitly listed in SKIP_DIRS for grep-ability."""
        assert "_private" in SKIP_DIRS


# ---------------------------------------------------------------------------
# Private content exclusion (the user-requested invariant)
# ---------------------------------------------------------------------------

class TestPrivateExclusion:
    def test_private_dir_never_embedded(self, tmp_path: Path):
        """`_private/` and any file inside it must NEVER appear in scan results."""
        _make_repo(tmp_path)
        results = scan_directory(str(tmp_path))
        for parts in _rel_parts(results, tmp_path):
            assert "_private" not in parts, (
                f"Private file leaked into embedding scan: {'/'.join(parts)}"
            )
        assert "secrets.md" not in _names(results)
        assert "draft.md" not in _names(results)

    def test_underscore_prefixed_dirs_excluded(self, tmp_path: Path):
        """All `_*` dirs (not just _private) are excluded — convention, not a list."""
        _make_repo(tmp_path)
        results = scan_directory(str(tmp_path))
        for parts in _rel_parts(results, tmp_path):
            assert "_drafts" not in parts, (
                f"`_drafts/` leaked into embedding scan: {'/'.join(parts)}"
            )

    def test_dotfile_dirs_excluded(self, tmp_path: Path):
        """`.git/` and other dotfile dirs are excluded by the dotfile rule."""
        _make_repo(tmp_path)
        results = scan_directory(str(tmp_path))
        for parts in _rel_parts(results, tmp_path):
            assert ".git" not in parts, (
                f"`.git/` leaked into embedding scan: {'/'.join(parts)}"
            )

    def test_mcp_server_dir_excluded(self, tmp_path: Path):
        """`mcp_server/` (server implementation, not knowledge) excluded."""
        _make_repo(tmp_path)
        results = scan_directory(str(tmp_path))
        for parts in _rel_parts(results, tmp_path):
            assert "mcp_server" not in parts, (
                f"mcp_server source leaked into embedding scan: {'/'.join(parts)}"
            )


# ---------------------------------------------------------------------------
# Public content inclusion (positive complement)
# ---------------------------------------------------------------------------

class TestPublicInclusion:
    def test_root_md_included(self, tmp_path: Path):
        _make_repo(tmp_path)
        assert "framework.md" in _names(scan_directory(str(tmp_path)))

    def test_recipes_included(self, tmp_path: Path):
        _make_repo(tmp_path)
        assert "agent-classifier.yaml" in _names(scan_directory(str(tmp_path)))

    def test_templates_included(self, tmp_path: Path):
        _make_repo(tmp_path)
        assert "intent.yaml" in _names(scan_directory(str(tmp_path)))


# ---------------------------------------------------------------------------
# Real repo smoke check (defensive — tied to the live build)
# ---------------------------------------------------------------------------

class TestRealRepo:
    def test_real_repo_excludes_private(self, framework_root: Path):
        """Run the real scan against the real repo; never include `_private/`.

        This is the test the deploy build relies on: if `_private/` ever
        starts appearing in scan_directory output, the embed step would
        ship private content to the public knowledge base.
        """
        results = scan_directory(str(framework_root))
        for path in _paths(results):
            rel = Path(path).relative_to(framework_root)
            parts = rel.parts
            assert "_private" not in parts, (
                f"_private leaked from REAL repo scan: {rel}"
            )
            assert "mcp_server" not in parts, (
                f"mcp_server leaked from REAL repo scan: {rel}"
            )
