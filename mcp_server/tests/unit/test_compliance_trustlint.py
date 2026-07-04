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
    @pytest.fixture(autouse=True)
    def _ensure_trustlint_rules(self):
        """PyPI wheel may not bundle rules — download once per session."""
        rules_home = Path.home() / ".trustlint" / "rules"
        if not rules_home.exists() or not any(rules_home.rglob("*.yaml")):
            subprocess.run(["trustlint", "rules", "update"], check=True, timeout=120)

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
        proc = subprocess.run(
            ["trustlint", "check", str(bad), "-j", "EU"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1
        assert "EU_AI_ACT" in proc.stdout + proc.stderr or "SOCIAL" in proc.stdout.upper()
