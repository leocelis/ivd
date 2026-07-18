# mcp_server/tools/import_spec.py

"""Tool: ivd_import_spec — parse a Spec Kit or OpenSpec artifact into an IVD constraint scaffold.

Read-only. Does not call an LLM and does not write to disk — it extracts the
structured requirement/scenario content both source formats already contain,
then hands the calling agent a scaffold plus instructions to draft real
constraints (each needing a `test:` field neither source format provides).

Supported formats, verified against the source projects on 2026-07-18:
  - "spec-kit": github/spec-kit's spec.md — ### User Story N (Priority: PN)
    blocks containing an **Acceptance Scenarios**: list of
    "N. **Given** X, **When** Y, **Then** Z" lines.
    Reference: https://github.com/github/spec-kit/blob/main/templates/spec-template.md
  - "openspec": Fission-AI/OpenSpec's spec.md / delta spec.md —
    ### Requirement: <name> blocks containing #### Scenario: <name>
    blocks with "- GIVEN ...", "- WHEN ...", "- THEN ..." lines.
    Reference: https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from termcolor import colored

from mcp_server.tools._paths import project_root

LOG = "IVD Tools"

SUPPORTED_FORMATS = ("spec-kit", "openspec")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower())
    return slug.strip("_")


# ─────────────────────────────────────────────────────────────────────────
# spec-kit parsing
# ─────────────────────────────────────────────────────────────────────────

_SPEC_KIT_STORY_RE = re.compile(
    r"^###\s+User Story\s+\d+\s*-\s*(?P<title>.+?)\s*\(Priority:\s*(?P<priority>P\d+)\)\s*$",
    re.MULTILINE,
)
_SPEC_KIT_SCENARIO_RE = re.compile(
    r"\*\*Given\*\*\s*(?P<given>[^\n]+?),\s*\*\*When\*\*\s*(?P<when>[^\n]+?),\s*\*\*Then\*\*\s*(?P<then>[^\n]+)",
    re.IGNORECASE,
)


def _parse_spec_kit(text: str) -> List[Dict]:
    headers = list(_SPEC_KIT_STORY_RE.finditer(text))
    requirements = []
    for i, m in enumerate(headers):
        block_start = m.end()
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[block_start:block_end]

        scenarios = []
        for j, sm in enumerate(_SPEC_KIT_SCENARIO_RE.finditer(block), start=1):
            scenarios.append({
                "name": f"scenario_{j}",
                "given": sm.group("given").strip().rstrip("."),
                "when": sm.group("when").strip().rstrip("."),
                "then": sm.group("then").strip().rstrip("."),
            })

        title = m.group("title").strip()
        requirements.append({
            "name": _slugify(title),
            "title": title,
            "priority": m.group("priority"),
            "requirement": title,
            "scenarios": scenarios,
        })
    return requirements


# ─────────────────────────────────────────────────────────────────────────
# openspec parsing
# ─────────────────────────────────────────────────────────────────────────

_OPENSPEC_REQ_RE = re.compile(
    r"^###\s+Requirement:\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)
_OPENSPEC_SCENARIO_HEADER_RE = re.compile(
    r"^####\s+Scenario:\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)
_OPENSPEC_GWT_RE = re.compile(
    r"^-\s*(?P<kind>GIVEN|WHEN|THEN|AND)\s+(?P<text>.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def _parse_openspec_scenarios(block: str) -> List[Dict]:
    headers = list(_OPENSPEC_SCENARIO_HEADER_RE.finditer(block))
    scenarios = []
    for i, sm in enumerate(headers):
        s_start = sm.end()
        s_end = headers[i + 1].start() if i + 1 < len(headers) else len(block)
        s_block = block[s_start:s_end]

        # AND continues whichever of GIVEN/WHEN/THEN most recently preceded it
        # (e.g. "- THEN X" followed by "- AND Y" both belong under "then").
        gwt = {"given": "", "when": "", "then": ""}
        last_kind = None
        for gm in _OPENSPEC_GWT_RE.finditer(s_block):
            kind = gm.group("kind").lower()
            text = gm.group("text").strip()
            if kind == "and":
                if last_kind is None:
                    continue  # malformed spec — AND with no preceding GWT line
                gwt[last_kind] = f"{gwt[last_kind]}; {text}" if gwt[last_kind] else text
            else:
                gwt[kind] = text
                last_kind = kind

        scenarios.append({
            "name": _slugify(sm.group("title")),
            "given": gwt["given"],
            "when": gwt["when"],
            "then": gwt["then"],
        })
    return scenarios


def _parse_openspec(text: str) -> List[Dict]:
    headers = list(_OPENSPEC_REQ_RE.finditer(text))
    requirements = []
    for i, m in enumerate(headers):
        block_start = m.end()
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[block_start:block_end]

        # Prose is everything before the first scenario sub-header.
        first_scenario = _OPENSPEC_SCENARIO_HEADER_RE.search(block)
        prose_end = first_scenario.start() if first_scenario else len(block)
        prose = block[:prose_end].strip()

        title = m.group("title").strip()
        requirements.append({
            "name": _slugify(title),
            "title": title,
            "requirement": prose or title,
            "scenarios": _parse_openspec_scenarios(block),
        })
    return requirements


_PARSERS = {
    "spec-kit": _parse_spec_kit,
    "openspec": _parse_openspec,
}


# ─────────────────────────────────────────────────────────────────────────
# Tool entry point
# ─────────────────────────────────────────────────────────────────────────

def import_spec_tool(
    spec_path: str,
    source_format: str,
    project_root_arg: Optional[str] = None,
) -> str:
    """Parse a Spec Kit or OpenSpec artifact into an IVD constraint scaffold."""
    print(colored(f"[{LOG}] ivd_import_spec: format={source_format}, path={spec_path}", "cyan"))

    if source_format not in SUPPORTED_FORMATS:
        return json.dumps({
            "ok": False,
            "error": f"Unsupported source_format '{source_format}'",
            "supported_formats": list(SUPPORTED_FORMATS),
        }, indent=2)

    try:
        root = project_root(project_root_arg)
    except FileNotFoundError as e:
        return json.dumps({"ok": False, "error": str(e)}, indent=2)

    candidate = Path(spec_path)
    resolved = candidate if candidate.is_absolute() else (root / candidate)

    if not resolved.is_file():
        return json.dumps({
            "ok": False,
            "error": f"Spec file not found: {resolved}",
            "hint": "spec_path is resolved relative to project_root when not absolute.",
        }, indent=2)

    text = resolved.read_text(encoding="utf-8")
    requirements = _PARSERS[source_format](text)

    if not requirements:
        return json.dumps({
            "ok": True,
            "source_format": source_format,
            "spec_path": str(resolved),
            "requirements": [],
            "warning": (
                "No requirements/user-stories matched the expected structure for "
                f"'{source_format}'. The file may use a customized template, or may "
                "not be the artifact type this parser targets."
            ),
        }, indent=2)

    result = {
        "ok": True,
        "source_format": source_format,
        "spec_path": str(resolved),
        "requirements": requirements,
        "agent_instructions": (
            "For each entry in `requirements`, draft one IVD constraint: "
            "`name` (reuse the given name), `requirement` (the prose requirement — "
            "for scenarios, state what must hold across GIVEN/WHEN/THEN), and a "
            "`test` field pointing at a real, executable pytest node "
            "(e.g. 'tests/test_foo.py::test_bar'). Neither Spec Kit's Acceptance "
            "Scenarios nor OpenSpec's Scenarios are bound to executable tests by "
            "default — that binding is what this step adds. Add `imported_from: "
            "{tool: <source_format>, source_path: <spec_path>}` to the resulting "
            "intent artifact for traceability, then continue with ivd_validate."
        ),
    }

    print(colored(f"[{LOG}] Parsed {len(requirements)} requirement(s) from {source_format} spec", "green"))
    return json.dumps(result, indent=2)
