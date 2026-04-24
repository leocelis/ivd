# mcp_server/tools/judgment.py

"""
IVD Judgment Phase MCP tools — Phase 4 of IVD (v3.0+, refactored in v3.1).

Nine tools (8 originals + ivd_judgment_check_installed, R6):

  1. ivd_judgment_init                    — bootstrap .judgment/
  2. ivd_judgment_capture                 — write a raw ledger entry
  3. ivd_judgment_codify                  — return a codify prompt for the agent
  4. ivd_judgment_save_codified           — persist agent-filled codify fields
  5. ivd_judgment_pair                    — capture a comparison_pair entry
  6. ivd_judgment_detect_patterns         — cluster ledger entries into patterns
  7. ivd_judgment_inject_context          — prioritized judgment context
  8. ivd_judgment_propose_recommendation  — draft recommendation against a pattern
  9. ivd_judgment_check_installed         — workspace-level activation visibility (R6)

All tools are *dormant* unless ``<project_root>/.judgment/`` exists at the
resolved project root (per-project opt-in gate). Additionally, the entire
toolset can be disabled at the server level by setting
``IVD_JUDGMENT_TOOLS_ENABLED=false`` (R4 — borrowed from Canon's
IVD_CANON_TOOLS_ENABLED knob; keeps tools registered but inactive so
tools/list output stays ABI-stable).

Architectural note:
  This module is a thin facade over the ``judgment`` engine package
  (``ivd/judgment/``). Schema, store, freshness, detection, injection, and
  validation all live in the engine; this module owns CLI ergonomics, MCP
  payload shaping, and the activation/opt-out gates.

Reference:
  ivd/judgment_layer.md                  (canonical spec)
  ivd/ivd_system_intent.yaml             (system intent v3.1)
  ivd/judgment/                          (engine package — borrowed pattern
                                          from ivd/canon/)
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from termcolor import colored

from judgment import (
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_INJECT_TOKEN_BUDGET,
    DEPTH_WEIGHT,
    ENGINE_VERSION,
    JUDGMENT_DIRNAME,
    JUDGMENT_SUBDIRS,
    PATTERN_PROMOTION_THRESHOLD,
    REQUIRED_CODIFIED_FIELDS,
    VALID_CAPABILITY_SUBTYPES,
    VALID_FIX_ACTION_TYPES,
    VALIDATORS,
    Baseline,
    Classification,
    CodifiedFields,
    ComparisonPair,
    Freshness,
    JudgmentStore,
    LedgerEntry,
    Pattern,
    PatternMembership,
    Recommendation,
    detect_patterns,
    inject_context,
    slugify,
    write_yaml,
)
from judgment.schema import _now_iso, _today
from judgment.validate import (
    validate_baseline,
    validate_comparison_pair,
    validate_ledger_entry,
    validate_pattern,
)
from mcp_server.tools._paths import project_root

LOG = "IVD Judgment"


# =============================================================================
# Server-level opt-out (R4 — analog to Canon's IVD_CANON_TOOLS_ENABLED)
# =============================================================================

_OPT_OUT_ENV = "IVD_JUDGMENT_TOOLS_ENABLED"
_DISABLED_MESSAGE = (
    "Judgment MCP tools are disabled on this IVD MCP server "
    f"({_OPT_OUT_ENV}=false). Re-enable by unsetting the env var."
)


def _is_judgment_enabled() -> bool:
    """Honor the single Judgment opt-out knob (R4)."""
    val = os.environ.get(_OPT_OUT_ENV, "true")
    return val.strip().lower() not in ("false", "0", "no", "off")


def _disabled_response(tool_name: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "enabled": False,
        "tool": tool_name,
        "message": _DISABLED_MESSAGE,
    }


# =============================================================================
# Per-project activation gate (folder presence)
# =============================================================================

def _store(project_root_arg: Optional[str]) -> JudgmentStore:
    return JudgmentStore(project_root(project_root_arg, require_exists=False))


def _judgment_active(project_root_arg: Optional[str]) -> bool:
    """Return True iff `.judgment/` exists at the resolved project root."""
    try:
        return _store(project_root_arg).is_active()
    except Exception:
        return False


def _dormant_response(tool_name: str, store: JudgmentStore) -> Dict[str, Any]:
    return {
        "ok": False,
        "tool": tool_name,
        "status": "dormant",
        "reason": (
            f"Judgment phase is not activated for this project. "
            f"No `{JUDGMENT_DIRNAME}/` folder found at {store.project_root}. "
            f"Run `ivd_judgment_init` first if you want to enable the Judgment phase."
        ),
        "activation": {
            "tool": "ivd_judgment_init",
            "creates": f"{store.project_root}/{JUDGMENT_DIRNAME}/",
        },
    }


def _gate(tool_name: str, project_root_arg: Optional[str]):
    """Returns (response_str | None, store).

    If the response is non-None, the caller should return it immediately
    (gates failed). Otherwise the store is ready to use.
    """
    if not _is_judgment_enabled():
        return json.dumps(_disabled_response(tool_name), indent=2), None
    store = _store(project_root_arg)
    if not store.is_active():
        return json.dumps(_dormant_response(tool_name, store), indent=2), store
    return None, store


# =============================================================================
# Tool 1: ivd_judgment_init
# =============================================================================

def judgment_init_tool(
    project_root_arg: Optional[str] = None,
    domains: Optional[List[str]] = None,
) -> str:
    """Bootstrap `.judgment/` folder with subdirs, config, and per-domain baselines."""
    print(colored(f"[{LOG}] ivd_judgment_init", "cyan"))

    if not _is_judgment_enabled():
        return json.dumps(_disabled_response("ivd_judgment_init"), indent=2)

    store = _store(project_root_arg)
    created, already = store.ensure_dirs()

    config_path = store.config_path()
    if not config_path.exists():
        config_payload = {
            "judgment_phase": {
                "version": "1.0",
                "ivd_version": "3.1",
                "engine_version": ENGINE_VERSION,
                "created": _now_iso(),
                "pattern_promotion_threshold": PATTERN_PROMOTION_THRESHOLD,
                "default_half_life_days": DEFAULT_HALF_LIFE_DAYS,
                "injection": {
                    "default_token_budget": DEFAULT_INJECT_TOKEN_BUDGET,
                    "include_what_works": True,
                },
                "notes": (
                    "Activation gate for the IVD Judgment phase. "
                    "While this folder exists, the 9 ivd_judgment_* tools are active "
                    "(unless IVD_JUDGMENT_TOOLS_ENABLED=false). "
                    "See ivd/judgment_layer.md for the full spec."
                ),
            }
        }
        write_yaml(config_path, config_payload)
        created.append(f"{JUDGMENT_DIRNAME}/config.yaml")
    else:
        already.append(f"{JUDGMENT_DIRNAME}/config.yaml")

    seeded: List[str] = []
    for domain in domains or []:
        slug = slugify(domain)
        bp = store.baseline_path(domain)
        if bp.exists():
            already.append(f"{JUDGMENT_DIRNAME}/baselines/{slug}_baseline.yaml")
            continue
        baseline = Baseline(
            domain_id=slug,
            created=_now_iso(),
            updated=_now_iso(),
        )
        baseline.goal_calibration["qualitative"] = (
            "TODO — describe what 'good' looks like in this domain"
        )
        from judgment.schema import ChangelogEntry
        baseline.changelog.append(
            ChangelogEntry(date=_today(), change="seeded by ivd_judgment_init")
        )
        write_yaml(bp, baseline.to_dict())
        seeded.append(f"{JUDGMENT_DIRNAME}/baselines/{slug}_baseline.yaml")
        created.append(seeded[-1])

    result = {
        "ok": True,
        "tool": "ivd_judgment_init",
        "engine_version": ENGINE_VERSION,
        "project_root": str(store.project_root),
        "judgment_root": str(store.root),
        "created": created,
        "already_present": already,
        "seeded_baselines": seeded,
        "next_steps": [
            "Edit baselines/<domain>_baseline.yaml — set goal_calibration, risk_hypotheses, half_life, depth",
            "Use ivd_judgment_capture as soon as a real correction shows up",
            "Run ivd_judgment_detect_patterns once you have ~3+ codified entries per domain",
        ],
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 2: ivd_judgment_capture
# =============================================================================

def judgment_capture_tool(
    raw_correction: str,
    domain: str,
    source: str = "leo_intuition",
    correction_type: str = "regression",
    project_root_arg: Optional[str] = None,
    agent: Optional[str] = None,
    model: Optional[str] = None,
    scope: Optional[str] = None,
    originated_from_tool: Optional[str] = None,
) -> str:
    """Capture a raw correction in < 30s. Returns the path of the new ledger entry."""
    print(colored(f"[{LOG}] ivd_judgment_capture: domain={domain}", "cyan"))

    gate, store = _gate("ivd_judgment_capture", project_root_arg)
    if gate is not None:
        return gate

    if not raw_correction or not raw_correction.strip():
        return json.dumps({"ok": False, "error": "raw_correction is required"}, indent=2)

    today = _today()
    slug = slugify(raw_correction.split("\n", 1)[0])
    entry_id = f"{today}_{slug}_correction"
    target = store.ledger_path("raw", entry_id)
    target, entry_id = store.next_unique_path(target)

    entry = LedgerEntry(
        id=entry_id,
        created=_now_iso(),
        state="raw",
        classification=Classification(
            type=correction_type,
            source=source,
            domain=domain,
            agent=agent,
            model=model,
            scope=scope,
        ),
        raw_correction=raw_correction.strip(),
        originated_from_tool=originated_from_tool,
    )
    from judgment.schema import ChangelogEntry
    entry.changelog.append(ChangelogEntry(date=today, change="captured (raw)"))
    write_yaml(target, entry.to_dict())

    result = {
        "ok": True,
        "tool": "ivd_judgment_capture",
        "entry_id": entry_id,
        "path": str(target),
        "state": "raw",
        "next_step": (
            "Run ivd_judgment_codify with this entry_id to structure the correction "
            "into the 5 canonical fields."
        ),
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 3: ivd_judgment_codify
# =============================================================================

CODIFY_PROMPT_TEMPLATE = """\
You are codifying a raw correction into the IVD Judgment ledger.

Raw correction (verbatim):
---
{raw}
---

Produce the 5 canonical codified fields. Be concrete, falsifiable, and specific.
Avoid platitudes ("better prompt"). Tie each field to the *actual* correction.

Required fields (return as YAML under a `codified:` key):

  expected_result: |
    What should the system have produced? Be specific (1-3 sentences).

  detected_via: |
    How was this caught? Choose one of:
      - user_review        (you eyeballed the output)
      - automated_test    (a test/lint failed)
      - audience_signal   (user, stakeholder, customer signal)
      - runtime_error     (exception / wrong type / etc.)
      - peer_review       (another agent or human reviewer)
    Add a 1-line note explaining how it surfaced.

  diagnosed_cause: |
    The root-cause hypothesis. Not "the model is bad" — name the *mechanism*
    (missing context, wrong constraint, ambiguous instruction, stale pattern,
    tool gap, model regression, etc.). 1-3 sentences.

  proposed_fix: |
    The specific fix. If it's a prompt change, name the section. If it's a
    capability gap, describe it. If it's an intent revision, point to the
    field. Actionable enough that the next agent can implement it.

  fix_action_type: |
    Choose one of:
      - prompt_patch          (tweak existing prompt / instructions)
      - intent_revision       (change a constraint, goal, or risk in an intent artifact)
      - capability_addition   (system needs a new tool / agent / dataset / partner)
      - domain_reassessment   (the goal calibration itself was wrong; re-baseline)

If you choose `capability_addition`, ALSO set `capability_subtype` to one of:
  build | buy | hire | partner

Optionally set:
  leo_domain_depth: expert | practitioner | adjacent | novice

Then call `ivd_judgment_save_codified` with:
  entry_id: "{entry_id}"
  codified_yaml: <your YAML>
"""


def judgment_codify_tool(
    entry_id: str,
    project_root_arg: Optional[str] = None,
) -> str:
    """Return a structured codify prompt for the agent to fill, plus the raw text."""
    print(colored(f"[{LOG}] ivd_judgment_codify: entry_id={entry_id}", "cyan"))

    gate, store = _gate("ivd_judgment_codify", project_root_arg)
    if gate is not None:
        return gate

    target = store.ledger_path("raw", entry_id)
    if not target.exists():
        return json.dumps({
            "ok": False,
            "tool": "ivd_judgment_codify",
            "error": f"Raw ledger entry not found: {entry_id}",
            "looked_at": str(target),
        }, indent=2)

    from judgment.store import read_yaml
    payload = read_yaml(target) or {}
    raw_text = payload.get("raw_correction", "")
    prompt = CODIFY_PROMPT_TEMPLATE.format(raw=raw_text, entry_id=entry_id)

    result = {
        "ok": True,
        "tool": "ivd_judgment_codify",
        "entry_id": entry_id,
        "raw_correction": raw_text,
        "codify_prompt": prompt,
        "expected_save_call": {
            "tool": "ivd_judgment_save_codified",
            "args": {"entry_id": entry_id, "codified_yaml": "<your YAML>"},
        },
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 4: ivd_judgment_save_codified
# =============================================================================

def judgment_save_codified_tool(
    entry_id: str,
    codified_yaml: str,
    project_root_arg: Optional[str] = None,
) -> str:
    """Persist agent-filled codify fields and transition entry from raw → codified."""
    print(colored(f"[{LOG}] ivd_judgment_save_codified: entry_id={entry_id}", "cyan"))

    gate, store = _gate("ivd_judgment_save_codified", project_root_arg)
    if gate is not None:
        return gate

    raw_path = store.ledger_path("raw", entry_id)
    if not raw_path.exists():
        return json.dumps({
            "ok": False,
            "error": f"Raw ledger entry not found: {entry_id}",
            "looked_at": str(raw_path),
        }, indent=2)

    try:
        parsed = yaml.safe_load(codified_yaml) or {}
    except yaml.YAMLError as e:
        return json.dumps({"ok": False, "error": f"YAML parse error: {e}"}, indent=2)

    if "codified" in parsed and isinstance(parsed["codified"], dict):
        codified = parsed["codified"]
        leo_depth = parsed.get("leo_domain_depth")
    else:
        codified = parsed
        leo_depth = parsed.pop("leo_domain_depth", None) if isinstance(parsed, dict) else None

    missing = [f for f in REQUIRED_CODIFIED_FIELDS if not codified.get(f)]
    errors: List[str] = []
    if missing:
        errors.append(f"Missing required codified fields: {missing}")

    fix_action = codified.get("fix_action_type")
    if fix_action and fix_action not in VALID_FIX_ACTION_TYPES:
        errors.append(
            f"fix_action_type '{fix_action}' invalid; expected one of {list(VALID_FIX_ACTION_TYPES)}"
        )

    if fix_action == "capability_addition":
        sub = codified.get("capability_subtype")
        if sub not in VALID_CAPABILITY_SUBTYPES:
            errors.append(
                "fix_action_type=capability_addition requires capability_subtype "
                f"∈ {list(VALID_CAPABILITY_SUBTYPES)}"
            )

    if errors:
        return json.dumps({
            "ok": False,
            "tool": "ivd_judgment_save_codified",
            "errors": errors,
        }, indent=2)

    from judgment.store import read_yaml
    raw_payload = read_yaml(raw_path) or {}
    raw_payload["state"] = "codified"
    raw_payload["codified"] = codified
    if leo_depth in DEPTH_WEIGHT:
        raw_payload["leo_domain_depth"] = leo_depth
    raw_payload.setdefault("changelog", []).append({"date": _today(), "change": "codified"})

    target = store.ledger_path("codified", entry_id)
    write_yaml(target, raw_payload)
    raw_path.unlink(missing_ok=True)

    result = {
        "ok": True,
        "tool": "ivd_judgment_save_codified",
        "entry_id": entry_id,
        "from": str(raw_path),
        "to": str(target),
        "state": "codified",
        "next_step": (
            "Once 3+ entries share a diagnosed_cause, run ivd_judgment_detect_patterns. "
            "If you have a comparable run, also consider ivd_judgment_pair."
        ),
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 5: ivd_judgment_pair
# =============================================================================

def judgment_pair_tool(
    domain: str,
    run_a: Dict[str, Any],
    run_b: Dict[str, Any],
    observed_differences: List[str],
    diagnostic_hypotheses: List[Dict[str, Any]],
    project_root_arg: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Capture a comparison_pair entry. Pearl Rung-1 alternative to A/B testing.

    Each diagnostic_hypothesis MUST include at least one ``competing_hypotheses``
    entry — the structural discipline that keeps this at Rung 1: association only.
    """
    print(colored(f"[{LOG}] ivd_judgment_pair: domain={domain}", "cyan"))

    gate, store = _gate("ivd_judgment_pair", project_root_arg)
    if gate is not None:
        return gate

    errors: List[str] = []
    if not isinstance(run_a, dict) or not isinstance(run_b, dict):
        errors.append("run_a and run_b must be dicts (ref, outcome, inputs, context, metadata)")
    if not observed_differences:
        errors.append("observed_differences is required (list of 1+ strings)")
    if not diagnostic_hypotheses:
        errors.append("diagnostic_hypotheses is required (list of 1+ dicts)")
    else:
        for i, dh in enumerate(diagnostic_hypotheses):
            if not isinstance(dh, dict):
                errors.append(f"diagnostic_hypotheses[{i}] is not a dict")
                continue
            if not dh.get("hypothesis"):
                errors.append(f"diagnostic_hypotheses[{i}] missing 'hypothesis' field")
            comps = dh.get("competing_hypotheses")
            if not comps or not isinstance(comps, list):
                errors.append(
                    f"diagnostic_hypotheses[{i}] missing 'competing_hypotheses' "
                    "(Rung-1 discipline: list at least one rival explanation)"
                )

    if errors:
        return json.dumps({"ok": False, "tool": "ivd_judgment_pair", "errors": errors}, indent=2)

    today = _today()
    slug = slugify(observed_differences[0])
    entry_id = f"{today}_{slug}_comparison_pair"
    target = store.ledger_path("paired", entry_id)
    target, entry_id = store.next_unique_path(target)

    pair = ComparisonPair(
        id=entry_id,
        created=_now_iso(),
        state="paired",
        classification=Classification(type="comparison_pair", domain=domain),
        run_a=run_a,
        run_b=run_b,
        observed_differences=observed_differences,
        diagnostic_hypotheses=diagnostic_hypotheses,
        notes=notes,
    )
    from judgment.schema import ChangelogEntry
    pair.changelog.append(ChangelogEntry(date=today, change="paired"))
    write_yaml(target, pair.to_dict())

    result = {
        "ok": True,
        "tool": "ivd_judgment_pair",
        "entry_id": entry_id,
        "path": str(target),
        "state": "paired",
        "injection_status": "plausible",
        "next_step": (
            "Need at least one independent corroborating pair (different author/week/model) "
            "before this hypothesis can be promoted to 'corroborated' for the What Works layer."
        ),
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 6: ivd_judgment_detect_patterns
# =============================================================================

def judgment_detect_patterns_tool(
    project_root_arg: Optional[str] = None,
    domain: Optional[str] = None,
    min_members: int = PATTERN_PROMOTION_THRESHOLD,
) -> str:
    """Cluster codified ledger entries by diagnosed_cause; emit pattern files."""
    print(colored(f"[{LOG}] ivd_judgment_detect_patterns", "cyan"))

    gate, store = _gate("ivd_judgment_detect_patterns", project_root_arg)
    if gate is not None:
        return gate

    promoted_patterns, skipped, scanned = detect_patterns(
        store, domain_filter=domain, min_members=min_members
    )

    promoted_summaries: List[Dict[str, Any]] = []
    for pattern in promoted_patterns:
        path = store.write_pattern(pattern)

        # Re-resolve members and stamp pattern_membership on each.
        from judgment.store import read_yaml
        for state in ("codified", "paired", "resolved"):
            sub = store.root / "ledger" / state
            if not sub.is_dir():
                continue
            for fp in sub.glob("*.yaml"):
                payload = read_yaml(fp) or {}
                if payload.get("id") in pattern.members:
                    payload["pattern_membership"] = {
                        "pattern_id": pattern.id,
                        "joined": _now_iso(),
                    }
                    write_yaml(fp, payload)

        promoted_summaries.append({
            "pattern_id": pattern.id,
            "path": str(path),
            "member_count": pattern.member_count,
            "weighted_confidence": pattern.weighted_confidence,
            "freshness": pattern.freshness,
            "fix_action_type": pattern.fix_action_type,
            "engine_version": pattern.engine_version,
            "detection_hash": pattern.detection_hash,
        })

    result = {
        "ok": True,
        "tool": "ivd_judgment_detect_patterns",
        "engine_version": ENGINE_VERSION,
        "scanned_entries": scanned,
        "promoted_patterns": promoted_summaries,
        "skipped_clusters": skipped,
        "next_step": (
            "Run ivd_judgment_propose_recommendation against any promoted pattern with "
            "freshness ∈ {fresh, aging} and weighted_confidence >= 0.5."
        ),
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 7: ivd_judgment_inject_context
# =============================================================================

def judgment_inject_context_tool(
    project_root_arg: Optional[str] = None,
    domain: Optional[str] = None,
    task_type: Optional[str] = None,
    token_budget: int = DEFAULT_INJECT_TOKEN_BUDGET,
) -> str:
    """Return prioritized judgment context for downstream agents.

    Layers (in priority order):
      1. Distilled patterns (3+ members, freshness ∈ {fresh, aging})
      2. Recent codified corrections in this domain (last 5)
      3. What Works — corroborated comparison_pair hypotheses

    ``task_type`` (e.g. "generate-script") is echoed back in the response so
    the calling agent can attach it to the system-message header without
    reformatting. It does not filter content in v1; it is reserved for
    task-scoped injection in a future release.

    Token budget is a soft cap (string-length proxy of 4 chars per token).
    The result includes ``engine_version`` and ``injection_hash`` so callers
    can diff context across runs (R3 — borrowed from Canon's audit hash).
    """
    print(colored(f"[{LOG}] ivd_judgment_inject_context", "cyan"))

    gate, store = _gate("ivd_judgment_inject_context", project_root_arg)
    if gate is not None:
        return gate

    injection = inject_context(
        store, domain=domain, task_type=task_type, token_budget=token_budget
    )
    payload = injection.to_dict()

    result = {
        "ok": True,
        "tool": "ivd_judgment_inject_context",
        "engine_version": payload["engine_version"],
        "injection_hash": payload["injection_hash"],
        "domain_filter": payload["domain_filter"],
        "task_type": payload["task_type"],
        "token_budget": payload["token_budget"],
        "approx_tokens": payload["approx_tokens"],
        "truncated": payload["truncated"],
        "context": payload["context"],
        "usage_note": (
            "Inject `context.patterns` (highest signal) and `context.what_works` "
            "into your downstream agent's system message. `recent_corrections` is "
            "useful when the agent works in the same domain as those entries."
        ),
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 8: ivd_judgment_propose_recommendation
# =============================================================================

def judgment_propose_recommendation_tool(
    pattern_id: str,
    project_root_arg: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Draft a recommendation against a detected pattern. Awaits your approval."""
    print(colored(f"[{LOG}] ivd_judgment_propose_recommendation: {pattern_id}", "cyan"))

    gate, store = _gate("ivd_judgment_propose_recommendation", project_root_arg)
    if gate is not None:
        return gate

    pattern = store.read_pattern(pattern_id)
    if not pattern:
        return json.dumps({
            "ok": False,
            "error": f"Pattern not found: {pattern_id}",
            "looked_at": str(store.pattern_path(pattern_id)),
        }, indent=2)

    if pattern.freshness == Freshness.EXPIRED.value:
        return json.dumps({
            "ok": False,
            "tool": "ivd_judgment_propose_recommendation",
            "error": f"Pattern {pattern_id} is expired and not promotable. Re-validate before recommending.",
        }, indent=2)

    fix_action = pattern.fix_action_type or "prompt_patch"
    today = _today()

    draft_recipe_yaml: Optional[str] = None
    if fix_action in ("prompt_patch", "intent_revision"):
        draft_recipe_yaml = yaml.safe_dump(
            {
                "recipe": {
                    "name": f"fix-{pattern_id}",
                    "version": "0.1",
                    "category": "judgment",
                    "created": today,
                    "author": "Leo Celis",
                },
                "description": (
                    f"Generated from IVD Judgment pattern `{pattern_id}` "
                    f"({pattern.member_count} ledger members, "
                    f"weighted_confidence={pattern.weighted_confidence})"
                ),
                "trigger": pattern.diagnosed_cause,
                "pattern": {
                    "fix_action_type": fix_action,
                    "fix": pattern.recommended_fix,
                },
                "verification": [
                    "Re-run the failing scenario; confirm the original symptom no longer reproduces.",
                    "Inject the new pattern into context for the next 3 runs and confirm no regression.",
                ],
                "source_pattern": pattern_id,
            },
            sort_keys=False,
        )

    capability_subtype: Optional[str] = None
    if fix_action == "capability_addition":
        counts: Counter = Counter()
        for state, fp, payload in store.iter_ledger("codified", "paired", "resolved"):
            if payload.get("id") in pattern.members:
                sub = (payload.get("codified") or {}).get("capability_subtype")
                if sub:
                    counts[sub] += 1
        if counts:
            capability_subtype = counts.most_common(1)[0][0]

    rec_id = f"{today}_recommendation_{pattern_id}"
    rec_path = store.recommendation_path(rec_id)
    rec_path, rec_id = store.next_unique_path(rec_path)

    recommendation = Recommendation(
        id=rec_id,
        created=_now_iso(),
        state="draft",
        source_pattern=pattern_id,
        pattern_summary={
            "domain": pattern.domain,
            "diagnosed_cause": pattern.diagnosed_cause,
            "recommended_fix": pattern.recommended_fix,
            "member_count": pattern.member_count,
            "weighted_confidence": pattern.weighted_confidence,
            "freshness": pattern.freshness,
        },
        fix_action_type=fix_action,
        capability_subtype=capability_subtype,
        draft_recipe_yaml=draft_recipe_yaml,
        notes=notes,
        next_actions=[
            "you review this recommendation; approves or rejects.",
            "On approval: apply the fix, then mark linked ledger entries as resolved.",
            "On rejection: archive recommendation and add a `rejected` changelog note.",
        ],
    )
    write_yaml(rec_path, recommendation.to_dict())

    result = {
        "ok": True,
        "tool": "ivd_judgment_propose_recommendation",
        "engine_version": ENGINE_VERSION,
        "recommendation_id": rec_id,
        "path": str(rec_path),
        "fix_action_type": fix_action,
        "capability_subtype": capability_subtype,
        "draft_recipe_yaml": draft_recipe_yaml,
        "awaiting": "leo_approval",
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Tool 9: ivd_judgment_check_installed (R6 — analog to canon_check_rules_installed)
# =============================================================================

def judgment_check_installed_tool(
    project_root_arg: Optional[str] = None,
    workspace_root: Optional[str] = None,
    max_depth: int = 3,
) -> str:
    """Detect Judgment-phase activation across one or more projects.

    Two modes:
      - workspace_root set:  scan ``workspace_root`` recursively (up to
                              ``max_depth``) for ``.judgment/`` folders and
                              return per-project activation summaries.
      - workspace_root unset: report on a single project_root_arg.

    NEVER writes to disk — read-only by design (analog to
    ``canon_check_rules_installed``'s never-writes invariant).
    """
    print(colored(
        f"[{LOG}] ivd_judgment_check_installed: workspace={workspace_root}",
        "cyan",
    ))

    if not _is_judgment_enabled():
        return json.dumps(_disabled_response("ivd_judgment_check_installed"), indent=2)

    def _summarize(judgment_dir: Path) -> Dict[str, Any]:
        """Build a per-project summary of a ``.judgment/`` folder."""
        proj = judgment_dir.parent
        out: Dict[str, Any] = {
            "project_root": str(proj),
            "judgment_root": str(judgment_dir),
            "activated": True,
            "engine_version": None,
            "ivd_version": None,
            "config_present": False,
            "baseline_count": 0,
            "ledger_counts": {},
            "pattern_count": 0,
            "recommendation_count": 0,
            "domains": [],
        }
        cfg_path = judgment_dir / "config.yaml"
        if cfg_path.is_file():
            try:
                cfg = yaml.safe_load(cfg_path.read_text()) or {}
                jp = cfg.get("judgment_phase") or {}
                out["config_present"] = True
                out["ivd_version"] = jp.get("ivd_version")
                out["engine_version"] = jp.get("engine_version")
            except yaml.YAMLError:
                out["config_present"] = False
        baseline_dir = judgment_dir / "baselines"
        if baseline_dir.is_dir():
            baselines = sorted(baseline_dir.glob("*_baseline.yaml"))
            out["baseline_count"] = len(baselines)
            domains = []
            for fp in baselines:
                stem = fp.stem
                if stem.endswith("_baseline"):
                    domains.append(stem[: -len("_baseline")])
            out["domains"] = domains
        ledger_dir = judgment_dir / "ledger"
        if ledger_dir.is_dir():
            for st_dir in sorted(ledger_dir.iterdir()):
                if st_dir.is_dir():
                    out["ledger_counts"][st_dir.name] = len(list(st_dir.glob("*.yaml")))
        patterns_dir = judgment_dir / "patterns"
        if patterns_dir.is_dir():
            out["pattern_count"] = len(list(patterns_dir.glob("*.yaml")))
        rec_dir = judgment_dir / "recommendations"
        if rec_dir.is_dir():
            out["recommendation_count"] = len(list(rec_dir.glob("*.yaml")))
        return out

    def _walk(root: Path, depth_left: int) -> List[Path]:
        """Yield .judgment/ folders found beneath root, up to depth_left."""
        found: List[Path] = []
        if depth_left < 0 or not root.is_dir():
            return found
        candidate = root / JUDGMENT_DIRNAME
        if candidate.is_dir():
            found.append(candidate)
        if depth_left == 0:
            return found
        try:
            for child in sorted(root.iterdir()):
                if not child.is_dir():
                    continue
                # Don't descend into VCS / virtualenv / node_modules / .judgment itself
                if child.name in {
                    ".git", ".hg", ".svn", "node_modules", ".venv", "venv",
                    "__pycache__", ".tox", "dist", "build", JUDGMENT_DIRNAME,
                }:
                    continue
                if child.name.startswith("."):
                    continue
                found.extend(_walk(child, depth_left - 1))
        except (PermissionError, OSError):
            pass
        return found

    summaries: List[Dict[str, Any]] = []

    if workspace_root:
        ws = Path(workspace_root).resolve()
        if not ws.exists():
            return json.dumps({
                "ok": False,
                "error": f"workspace_root does not exist: {ws}",
            }, indent=2)
        for jd in _walk(ws, max_depth):
            summaries.append(_summarize(jd))
        next_step = (
            f"Found {len(summaries)} project(s) with `.judgment/` under {ws} "
            f"(max_depth={max_depth})."
        )
    else:
        store = _store(project_root_arg)
        if store.is_active():
            summaries.append(_summarize(store.root))
            next_step = (
                f"Judgment phase ACTIVE at {store.project_root}. "
                "Use ivd_judgment_capture to record corrections."
            )
        else:
            summaries.append({
                "project_root": str(store.project_root),
                "judgment_root": str(store.root),
                "activated": False,
            })
            next_step = (
                f"Judgment phase NOT activated at {store.project_root}. "
                "Run ivd_judgment_init to enable."
            )

    activated_count = sum(1 for s in summaries if s.get("activated"))
    total_patterns = sum(s.get("pattern_count", 0) for s in summaries)
    total_ledger = sum(
        sum(s.get("ledger_counts", {}).values()) for s in summaries
    )

    result = {
        "ok": True,
        "tool": "ivd_judgment_check_installed",
        "engine_version": ENGINE_VERSION,
        "scope": "workspace" if workspace_root else "project",
        "workspace_root": str(Path(workspace_root).resolve()) if workspace_root else None,
        "project_root": str(_store(project_root_arg).project_root) if not workspace_root else None,
        "summary": {
            "projects_scanned": len(summaries),
            "projects_activated": activated_count,
            "total_patterns": total_patterns,
            "total_ledger_entries": total_ledger,
        },
        "projects": summaries,
        "permission_discipline": (
            "This tool detects state only — it never writes to disk. To activate "
            "Judgment in a project, the agent must call ivd_judgment_init "
            "explicitly (with the user's awareness)."
        ),
        "next_step": next_step,
    }
    return json.dumps(result, indent=2)


# =============================================================================
# Validators (re-exported for back-compat with existing imports)
# =============================================================================

__all__ = [
    "judgment_init_tool",
    "judgment_capture_tool",
    "judgment_codify_tool",
    "judgment_save_codified_tool",
    "judgment_pair_tool",
    "judgment_detect_patterns_tool",
    "judgment_inject_context_tool",
    "judgment_propose_recommendation_tool",
    "judgment_check_installed_tool",
    # validators (back-compat with mcp_server.tools.validate)
    "validate_baseline",
    "validate_ledger_entry",
    "validate_comparison_pair",
    "validate_pattern",
    "VALIDATORS",
    # opt-out helpers (used by tests)
    "_is_judgment_enabled",
    "_OPT_OUT_ENV",
]
