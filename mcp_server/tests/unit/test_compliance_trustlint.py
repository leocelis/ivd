# mcp_server/tests/unit/test_compliance_trustlint.py

"""TrustLint / ComplyEdge compliance gate for IVD LLM-facing artifacts."""

import json
import subprocess
from pathlib import Path

import pytest

from mcp_server.tools._paths import get_framework_path
from mcp_server.tools.recipes import load_recipe_tool, list_recipes_tool


REPO_ROOT = get_framework_path()
CHECK_SCRIPT = REPO_ROOT / "scripts" / "compliance" / "check.sh"


def _resolve_rules_dir() -> Path:
    cache = REPO_ROOT / ".trustlint-cache" / "rules"
    if cache.exists() and any(cache.rglob("*.yaml")):
        return cache
    home = Path.home() / ".trustlint" / "rules"
    if home.exists() and any(home.rglob("*.yaml")):
        return home
    raise FileNotFoundError("TrustLint rules not bootstrapped — run ./scripts/compliance/check.sh")


def _rules_dir_or_skip() -> Path:
    """Return the bootstrapped rules dir, or skip when it is unavailable.

    The corpus is fetched from a third-party GitHub release at test time, so its
    availability is an *external* dependency: offline runners, a moved upstream
    release, or GitHub API rate limiting all make it unreachable. None of those
    is an IVD regression, so they must not fail the suite — the checks that
    depend on the corpus skip instead.
    """
    try:
        return _resolve_rules_dir()
    except FileNotFoundError:
        pytest.skip(
            "TrustLint rule corpus unavailable (offline, upstream release moved, "
            "or GitHub rate limit) — external dependency, not an IVD regression"
        )


@pytest.fixture(scope="session", autouse=True)
def _ensure_trustlint_rules():
    """Bootstrap rules from the public ComplyEdge/complyedge release once per session.

    Best-effort: a failed bootstrap is not fatal. Tests that need the corpus call
    ``_rules_dir_or_skip()`` and skip themselves; tests that only inspect repo
    files (recipe, config, docs) still run.
    """
    try:
        _resolve_rules_dir()
    except FileNotFoundError:
        try:
            subprocess.run(["bash", str(CHECK_SCRIPT)], cwd=str(REPO_ROOT), check=True, timeout=300)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            pass  # rule-dependent tests skip themselves via _rules_dir_or_skip()


class TestComplianceRecipe:
    def test_recipe_listed(self):
        data = json.loads(list_recipes_tool())
        names = [r["name"] for r in data["recipes"]]
        assert "compliance-trustlint" in names

    def test_recipe_loadable_with_fences(self):
        result = load_recipe_tool("compliance-trustlint")
        assert "<BEGIN-COMPLYEDGE v1.0>" in result
        assert "<END-COMPLYEDGE v1.0>" in result
        assert "trustlint check" in result.lower()

    def test_repo_has_trustlint_config(self):
        cfg = REPO_ROOT / ".trustlint.yaml"
        assert cfg.is_file()
        text = cfg.read_text()
        assert "jurisdiction: EU" in text
        assert "recipes/**/*.yaml" in text


class TestExternalDependencyDegradation:
    """The rule corpus is fetched from a third-party GitHub release at test time.

    A 403 rate-limit there once turned the whole Tests job red for a change that
    touched none of this. Unreachable-corpus must degrade to skip, never to fail.
    """

    def test_unreachable_corpus_skips_rather_than_fails(self, monkeypatch):
        def _boom():
            raise FileNotFoundError("not bootstrapped")

        monkeypatch.setattr(
            "mcp_server.tests.unit.test_compliance_trustlint._resolve_rules_dir", _boom
        )
        with pytest.raises(pytest.skip.Exception):
            _rules_dir_or_skip()

    def test_available_corpus_is_returned_unchanged(self):
        """Must not over-fire: a present corpus resolves normally."""
        try:
            expected = _resolve_rules_dir()
        except FileNotFoundError:
            pytest.skip("corpus not bootstrapped in this environment")
        assert _rules_dir_or_skip() == expected


class TestComplianceCheckScript:
    def test_check_script_exists_and_executable(self):
        assert CHECK_SCRIPT.is_file()

    @pytest.mark.skipif(
        subprocess.run(["which", "trustlint"], capture_output=True).returncode != 0,
        reason="trustlint not installed",
    )
    def test_full_repo_scan_passes(self):
        """All current IVD LLM-facing artifacts must be EU-clean."""
        _rules_dir_or_skip()  # external corpus — skip rather than fail when unreachable
        proc = subprocess.run(
            ["bash", str(CHECK_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr

    @pytest.mark.skipif(
        subprocess.run(["which", "trustlint"], capture_output=True).returncode != 0,
        reason="trustlint not installed",
    )
    def test_detects_art5_violation(self, tmp_path: Path):
        bad = tmp_path / "bad_intent.yaml"
        bad.write_text(
            "constraints:\n"
            "  - name: social_scoring\n"
            "    requirement: Deploy social credit score for all citizens\n",
            encoding="utf-8",
        )
        rules_dir = _rules_dir_or_skip()
        proc = subprocess.run(
            ["trustlint", "--rules-dir", str(rules_dir), "check", str(bad), "-j", "EU"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1
        assert "EU_AI_ACT" in proc.stdout + proc.stderr or "SOCIAL" in proc.stdout.upper()


class TestComplyEdgeIntegration:
    def test_complyedge_integration_doc_exists(self):
        doc = REPO_ROOT / "docs" / "integrations" / "COMPLYEDGE.md"
        assert doc.is_file()
        text = doc.read_text(encoding="utf-8")
        assert "ivd" in text
        assert "runtime_check.sh" in text
        assert "trust.complyedge.io/ivd" in text
        assert "Customer #0" not in text
        assert "dogfood" not in text.lower()

    def test_runtime_check_script_exists(self):
        script = REPO_ROOT / "scripts" / "compliance" / "runtime_check.sh"
        assert script.is_file()

    def test_readme_live_badge_embed(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "api.complyedge.io/v1/public/badge/ivd.svg" in readme
        assert "trust.complyedge.io/ivd" in readme
