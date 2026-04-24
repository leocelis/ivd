# mcp_server/tools/canon.py

"""
Canon MCP tools — Phase 0b of the Canon GTM, hosted inside the IVD MCP server.

Four tools:
  canon_render               — Tier 1 inference + render of any AI text
  canon_check                — audit a CanonDocument or raw text
  canon_diff                 — diff two audit reports (before/after)
  canon_check_rules_installed — detect Phase 0a rules block in agent files
                                  and (optionally) emit a write payload the
                                  AGENT must ask the user to apply

Hosting model: these tools live in the existing IVD MCP server tool catalog
(see PRD v0.7 §11.0b, Tech Spec v0.6 §9B). No separate Canon MCP binary, no
new `mcpServers` entry required for any existing IVD client.

Opt-out: setting `IVD_CANON_TOOLS_ENABLED=false` makes all four tools return
the standard "tool disabled" response (still registered, still discoverable
in tools/list, but inactive — keeps the per-client tool ABI stable).

Reference:
  external/canon/CANON_PRD.md           v0.7
  external/canon/CANON_TECH_SPEC.md     v0.6 §9B, §9C
  external/canon/canon_system_intent.yaml v5
  ivd/recipes/canon-rules.yaml                    v1.0  (Phase 0a rules block)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from termcolor import colored

from canon import (
    AuditReport,
    CanonContract,
    CanonDocument,
    Stakes,
    audit as canon_audit,
    diff_audit as canon_diff_audit,
    infer as canon_infer,
    render as canon_render_engine,
)
from canon.contract import RFinding
from mcp_server.tools._paths import get_framework_path, project_root

LOG = "Canon"

# -----------------------------------------------------------------------------
# Opt-out gate (PRD §11.0b)
# -----------------------------------------------------------------------------

_OPT_OUT_ENV = "IVD_CANON_TOOLS_ENABLED"
_DISABLED_MESSAGE = (
    "Canon MCP tools are disabled on this IVD MCP server "
    f"({_OPT_OUT_ENV}=false). Re-enable by unsetting the env var."
)


def _is_canon_enabled() -> bool:
    """Honor the single Canon opt-out knob (PRD §11.0b)."""
    val = os.environ.get(_OPT_OUT_ENV, "true")
    return val.strip().lower() not in ("false", "0", "no", "off")


def _disabled_response() -> Dict[str, Any]:
    return {"enabled": False, "message": _DISABLED_MESSAGE}


# -----------------------------------------------------------------------------
# Stakes parsing
# -----------------------------------------------------------------------------

def _parse_stakes(raw: Optional[str]) -> Stakes:
    if not raw:
        return Stakes.MEDIUM
    raw = raw.strip().lower()
    try:
        return Stakes(raw)
    except ValueError:
        return Stakes.MEDIUM


# -----------------------------------------------------------------------------
# Contract input parsing (Tier 2)
# -----------------------------------------------------------------------------

def _contract_from_input(contract_dict: Dict[str, Any]) -> CanonContract:
    """Permissive: accept a partial Tier-2 Contract; missing fields default."""
    from canon.contract import ConfidenceMark, DecisionPoint
    marks = []
    for m in contract_dict.get("confidence_marks", []) or []:
        marks.append(ConfidenceMark(
            claim=m.get("claim", ""),
            tier=m.get("tier", "assumed"),
            evidence=m.get("evidence"),
        ))
    decisions = []
    for d in contract_dict.get("decision_points", []) or []:
        decisions.append(DecisionPoint(
            action=d.get("action", ""),
            stakes=_parse_stakes(d.get("stakes")),
            reversible=bool(d.get("reversible", True)),
            smallest_undo=d.get("smallest_undo"),
        ))
    return CanonContract(
        setting=contract_dict.get("setting", ""),
        body=contract_dict.get("body", ""),
        confidence_marks=marks,
        decision_points=decisions,
        folk_theory_corrections=contract_dict.get("folk_theory_corrections", []) or [],
        identity_statement=contract_dict.get("identity_statement", "I am an AI assistant."),
        domain_pack=contract_dict.get("domain_pack", "general"),
        stakes=_parse_stakes(contract_dict.get("stakes")),
    )


# =============================================================================
# Tool: canon_render
# =============================================================================

def canon_render_tool(
    text: Optional[str] = None,
    contract: Optional[Dict[str, Any]] = None,
    stakes: Optional[str] = None,
    domain_pack: Optional[str] = None,
    identity_statement: Optional[str] = None,
    output_format: str = "markdown",
) -> str:
    """Render any AI output as a CanonDocument (Tier 1 from text, Tier 2 from contract)."""
    print(colored(f"[{LOG}] canon_render: tier={'2' if contract else '1'} fmt={output_format}", "cyan"))

    if not _is_canon_enabled():
        return json.dumps(_disabled_response(), indent=2)

    if not text and not contract:
        return json.dumps({
            "error": "Provide either `text` (Tier 1) or `contract` (Tier 2).",
        }, indent=2)

    parsed_stakes = _parse_stakes(stakes)
    pack = domain_pack or "general"

    if contract:
        canon_contract = _contract_from_input(contract)
        if stakes:
            canon_contract.stakes = parsed_stakes
        if domain_pack:
            canon_contract.domain_pack = pack
        if identity_statement:
            canon_contract.identity_statement = identity_statement
    else:
        canon_contract = canon_infer(
            text or "",
            domain_pack=pack,
            stakes=parsed_stakes,
            identity_statement=identity_statement or "I am an AI assistant.",
        )

    document = canon_render_engine(canon_contract)
    report = canon_audit(document)

    out: Dict[str, Any] = {
        "tier": 2 if contract else 1,
        "engine_version": report.engine_version,
        "audit": report.to_json(),
        "document": document.to_json(),
    }
    if output_format in ("markdown", "both"):
        out["markdown"] = document.to_markdown()
    if output_format == "markdown":
        out.pop("document", None)

    return json.dumps(out, indent=2, default=str)


# =============================================================================
# Tool: canon_check
# =============================================================================

def canon_check_tool(
    text: Optional[str] = None,
    document: Optional[Dict[str, Any]] = None,
    stakes: Optional[str] = None,
    domain_pack: Optional[str] = None,
) -> str:
    """Audit a CanonDocument (or raw text — auto-rendered first) against R-invariants."""
    print(colored(f"[{LOG}] canon_check: source={'document' if document else 'text'}", "cyan"))

    if not _is_canon_enabled():
        return json.dumps(_disabled_response(), indent=2)

    if not text and not document:
        return json.dumps({
            "error": "Provide either `text` (auto-render then audit) or `document` (audit a rendered CanonDocument).",
        }, indent=2)

    parsed_stakes = _parse_stakes(stakes)
    pack = domain_pack or "general"

    if document:
        # Pull straight into a CanonDocument and audit.
        doc = CanonDocument(
            setting_phase=document.get("setting_phase", ""),
            body_with_marks=document.get("body_with_marks", ""),
            verification_beats=document.get("verification_beats", []) or [],
            folk_theory_notes=document.get("folk_theory_notes", []) or [],
            identity_statement=document.get("identity_statement", ""),
            raw_input=document.get("raw_input", ""),
            domain_pack=document.get("domain_pack", pack),
            stakes=_parse_stakes(document.get("stakes") or stakes),
        )
    else:
        contract = canon_infer(text or "", domain_pack=pack, stakes=parsed_stakes)
        doc = canon_render_engine(contract)

    report = canon_audit(doc)
    return json.dumps(report.to_json(), indent=2, default=str)


# =============================================================================
# Tool: canon_diff
# =============================================================================

def canon_diff_tool(
    before: Dict[str, Any],
    after: Dict[str, Any],
) -> str:
    """Diff two audit reports — before / after — and return per-R movement."""
    print(colored(f"[{LOG}] canon_diff", "cyan"))

    if not _is_canon_enabled():
        return json.dumps(_disabled_response(), indent=2)

    if not before or not after:
        return json.dumps({
            "error": "Provide both `before` and `after` audit reports (output of canon_check).",
        }, indent=2)

    def _to_report(d: Dict[str, Any]) -> AuditReport:
        findings = [
            RFinding(
                r=f.get("r", ""),
                status=f.get("status", "skipped"),
                severity=f.get("severity", "info"),
                detail=f.get("detail", ""),
            )
            for f in d.get("findings", []) or []
        ]
        return AuditReport(
            findings=findings,
            overall=d.get("overall", "pass"),
            partial=bool(d.get("partial", False)),
            stakes=_parse_stakes(d.get("stakes")),
            domain_pack=d.get("domain_pack", "general"),
            engine_version=d.get("engine_version", "0.1.0"),
        )

    before_report = _to_report(before)
    after_report = _to_report(after)
    diff = canon_diff_audit(before_report, after_report)
    return json.dumps(diff.to_json(), indent=2, default=str)


# =============================================================================
# Tool: canon_check_rules_installed
# =============================================================================
#
# Detects whether the Phase 0a Canon rules block is present in any of the
# active project's agent instruction files. Critically, this tool DOES NOT
# write anything — it returns a payload the agent must offer to the user
# with explicit permission before editing instruction files.
#
# Invariants (PRD v0.7 §11.0b, NFR canon_check_rules_installed_no_writes):
#   - never write to disk
#   - return the per-target adapter view + insertion strategy
#   - tell the agent in `agent_instructions` to ask the user first
# -----------------------------------------------------------------------------

# Match either "ivd" or "canon" inside the fence label, version-tolerant.
_BEGIN_RE = re.compile(r"<BEGIN-(IVD|CANON)\s+v[\d.]+>", re.IGNORECASE)
_END_RE = re.compile(r"<END-(IVD|CANON)\s+v[\d.]+>", re.IGNORECASE)


def _detect_block(file_text: str, kind: str) -> Optional[Dict[str, Any]]:
    """Detect a Canon or IVD rules block in a file's text.

    Returns {present, version} or None when not found.
    """
    kind_upper = kind.upper()
    found_begin = None
    found_end = None
    for m in _BEGIN_RE.finditer(file_text):
        if m.group(1).upper() == kind_upper:
            found_begin = m
            break
    for m in _END_RE.finditer(file_text):
        if m.group(1).upper() == kind_upper:
            found_end = m
            break
    if not (found_begin and found_end):
        return None
    fence_label = found_begin.group(0)
    version_match = re.search(r"v([\d.]+)", fence_label)
    return {
        "present": True,
        "version": version_match.group(1) if version_match else "unknown",
    }


def _resolve_target_path(root: Path, file_str: str) -> Path:
    if file_str.startswith("~/"):
        return Path(os.path.expanduser(file_str))
    return root / file_str


def _load_canon_recipe() -> Optional[Dict[str, Any]]:
    """Load canon-rules.yaml as a flat dict.

    The recipe file has a top-level `recipe:` block plus sibling top-level
    keys (`install_targets`, `block_markers`, `agent_rules_block`, …). We
    flatten so callers can read everything from one dict.
    """
    recipe_path = get_framework_path() / "recipes" / "canon-rules.yaml"
    if not recipe_path.exists():
        return None
    try:
        with recipe_path.open("r") as f:
            doc = yaml.safe_load(f) or {}
        flat: Dict[str, Any] = {}
        # `recipe:` block first (so siblings can override if needed)
        recipe_section = doc.get("recipe") or {}
        if isinstance(recipe_section, dict):
            flat.update(recipe_section)
        # Then merge top-level siblings
        for key, val in doc.items():
            if key == "recipe":
                continue
            flat[key] = val
        return flat
    except Exception:
        return None


def canon_check_rules_installed_tool(
    project_root_arg: Optional[str] = None,
    install_missing: bool = False,
) -> str:
    """Detect whether IVD + Canon rules blocks are installed in the project's agent files.

    NEVER writes to disk. When a block is missing, returns a payload the agent
    must offer to the user with explicit permission.
    """
    print(colored(f"[{LOG}] canon_check_rules_installed: install_missing={install_missing}", "cyan"))

    if not _is_canon_enabled():
        return json.dumps(_disabled_response(), indent=2)

    try:
        root = project_root(project_root_arg, require_exists=True)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e)}, indent=2)

    recipe = _load_canon_recipe()
    if not recipe:
        return json.dumps({
            "error": "canon-rules recipe not found",
            "expected_path": "ivd/recipes/canon-rules.yaml",
        }, indent=2)

    install_targets = recipe.get("install_targets", []) or []
    adapter_views = recipe.get("agent_rules_block", {}) or {}
    block_markers = recipe.get("block_markers", {})

    per_target: List[Dict[str, Any]] = []
    any_canon_missing = False
    any_canon_installed = False
    any_file_present = False

    for tgt in install_targets:
        client = tgt.get("client", "")
        rel = tgt.get("file", "")
        adapter_view_key = tgt.get("adapter_view", "")
        target_path = _resolve_target_path(root, rel)

        entry: Dict[str, Any] = {
            "client": client,
            "file": rel,
            "absolute_path": str(target_path),
            "file_exists": target_path.exists(),
            "ivd_block": None,
            "canon_block": None,
            "adapter_view": adapter_view_key,
            "optional": bool(tgt.get("optional", False)),
        }

        if target_path.exists():
            any_file_present = True
            try:
                file_text = target_path.read_text()
            except (OSError, PermissionError) as e:
                entry["read_error"] = str(e)
                per_target.append(entry)
                continue

            entry["ivd_block"] = _detect_block(file_text, "IVD")
            entry["canon_block"] = _detect_block(file_text, "CANON")

            if entry["canon_block"] and entry["canon_block"].get("present"):
                any_canon_installed = True
            elif not entry["optional"]:
                any_canon_missing = True
                # Provide ready-to-paste payload only when the file already
                # exists and the block is missing.
                view_text = adapter_views.get(adapter_view_key, "")
                if view_text:
                    entry["install_payload"] = {
                        "strategy": "append-fenced-block-to-existing-file",
                        "fence_begin": block_markers.get("begin", "<BEGIN-CANON v1.0>"),
                        "fence_end": block_markers.get("end", "<END-CANON v1.0>"),
                        "block_text": view_text,
                        "instruction_to_agent": (
                            "Ask the user for explicit permission BEFORE writing this block "
                            "to the file. Do not modify content outside the fence markers. "
                            "If the user declines, do not retry."
                        ),
                    }
        else:
            # File does not exist: only suggest creating the canonical file
            # if it is a primary (non-optional) target.
            if not entry["optional"]:
                any_canon_missing = True
                view_text = adapter_views.get(adapter_view_key, "")
                if view_text:
                    entry["install_payload"] = {
                        "strategy": "create-new-file-with-fenced-block",
                        "fence_begin": block_markers.get("begin", "<BEGIN-CANON v1.0>"),
                        "fence_end": block_markers.get("end", "<END-CANON v1.0>"),
                        "block_text": view_text,
                        "instruction_to_agent": (
                            "Ask the user for explicit permission BEFORE creating this file. "
                            "Many projects intentionally use only one or two agent clients; do "
                            "not create files for clients the user does not use."
                        ),
                    }

        per_target.append(entry)

    overall_status = (
        "installed" if any_canon_installed and not any_canon_missing
        else "partial" if any_canon_installed and any_canon_missing
        else "missing" if any_canon_missing
        else "no_agent_files_detected" if not any_file_present
        else "unknown"
    )

    next_steps: List[str] = []
    if overall_status in ("missing", "partial"):
        next_steps.append(
            "Show the user the per_target.install_payload entries and ASK PERMISSION before writing. "
            "The user may accept some clients and decline others."
        )
        next_steps.append(
            "If the user accepts, write only the fenced block (BEGIN-CANON / END-CANON) to the agreed files. "
            "Preserve all content outside the fence."
        )
    if overall_status == "no_agent_files_detected":
        next_steps.append(
            "No agent instruction files detected in the project root. Ask the user which "
            "agent client(s) they use (Cursor, Cline, Claude Code, Copilot, Codex, Windsurf), "
            "then offer to create the corresponding file with the Canon Rules block."
        )

    if install_missing:
        # Defensive: this tool NEVER writes. Honor the constraint regardless.
        next_steps.insert(
            0,
            "NOTE: install_missing=true requested but canon_check_rules_installed never writes "
            "to disk. The agent must obtain explicit user consent and perform the file edits itself "
            "using the per_target.install_payload entries.",
        )

    result = {
        "project_root": str(root),
        "overall_status": overall_status,
        "summary": {
            "any_canon_installed": any_canon_installed,
            "any_canon_missing": any_canon_missing,
            "any_agent_file_present": any_file_present,
        },
        "recipe_version": recipe.get("version", "1.0"),
        "block_markers": block_markers,
        "per_target": per_target,
        "permission_discipline": (
            "This tool detects state only — it never writes to disk. The agent MUST obtain "
            "explicit user permission before editing any instruction file. No silent edits."
        ),
        "next_steps": next_steps,
    }

    print(colored(f"[{LOG}] rules_status={overall_status} ({len(per_target)} targets)", "green"))
    return json.dumps(result, indent=2, default=str)
