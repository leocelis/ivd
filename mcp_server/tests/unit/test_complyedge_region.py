"""The IVD ComplyEdge tenant lives in the US region; every surface must say so.

runtime_check.sh defaulted to eu.api.complyedge.io while the tenant (slug
``ivd``) is served from api.complyedge.io. The EU API answers a US key with
401 wrong_region, so the CI runtime probe could never record a check, and
the docs pointed readers at an EU seal URL that returns 404.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEAL = "https://api.complyedge.io/v1/public/badge/ivd.svg"


def test_runtime_probe_defaults_to_the_us_api():
    script = (ROOT / "scripts" / "compliance" / "runtime_check.sh").read_text()
    m = re.search(r'API_URL="\$\{COMPLYEDGE_API_URL:-([^}]+)\}"', script)
    assert m, "runtime_check.sh must set API_URL with a default"
    assert m.group(1) == "https://api.complyedge.io"


def test_no_tracked_file_points_at_the_eu_api():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    hits = [f for f in files
            if f != "mcp_server/tests/unit/test_complyedge_region.py"
            and (ROOT / f).is_file()
            and "eu.api.complyedge.io" in (ROOT / f).read_text(errors="ignore")]
    assert hits == []


def test_readme_and_site_embed_the_us_seal_as_an_image():
    for name in ("README.md", "index.html"):
        text = (ROOT / name).read_text()
        assert f'<img src="{SEAL}" alt="ComplyEdge Enforcement Seal" height="26" />' in text, name
        assert 'href="https://trust.complyedge.io/ivd"' in text, name
