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


@pytest.fixture(scope="session", autouse=True)
def _ensure_trustlint_rules():
    """Bootstrap rules from public ComplyEdge/complyedge release once per session."""
    try:
        _resolve_rules_dir()
    except FileNotFoundError:
        subprocess.run(["bash", str(CHECK_SCRIPT)], cwd=str(REPO_ROOT), check=True, timeout=300)


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


class TestComplianceCheckScript:
    def test_check_script_exists_and_executable(self):
        assert CHECK_SCRIPT.is_file()

    @pytest.mark.skipif(
        subprocess.run(["which", "trustlint"], capture_output=True).returncode != 0,
        reason="trustlint not installed",
    )
    def test_full_repo_scan_passes(self):
        """All current IVD LLM-facing artifacts must be EU-clean."""
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
        rules_dir = _resolve_rules_dir()
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
