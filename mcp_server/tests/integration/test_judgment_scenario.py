# mcp_server/tests/integration/test_judgment_scenario.py

"""
IVD Judgment Phase — End-to-End Scenario Test.

This is not a structural test.  It is a narrative simulation of a real
problem that repeats, the Judgment phase catching it, and the feedback loop
closing so the next agent run does not make the same mistake.

─────────────────────────────────────────────────────────────────────────────
THE SCENARIO
─────────────────────────────────────────────────────────────────────────────

  The Problem
  ───────────
  your AI coding agent keeps generating JWT verification code that silently
  accepts expired tokens.  The ``exp`` (expiry) claim is present but never
  validated — the library's ``decode()`` method requires an explicit
  ``options={"verify_exp": True}`` flag, and every generated snippet omits it.

  This surfaces three times in two weeks:
    Incident 1  auth service  → token accepted 2h after expiry in prod
    Incident 2  mobile API    → refresh-token handler skips expiry check
    Incident 3  admin panel   → JWT middleware trusts exp-less tokens entirely

  All three share the same root cause: the agent does not know the library
  default is unsafe.

  The Judgment Feedback Loop
  ──────────────────────────
  Step 0  you initialise the Judgment phase for the project.
  Step 1  Each incident is captured as a raw ledger entry (< 30 s each).
  Step 2  Each entry is codified with the five canonical fields.
  Step 3  After incident 3, you run detect_patterns.
             → The engine sees 3 codified entries sharing the same
               ``diagnosed_cause`` (jwt_library_defaults_unsafe).
             → A Pattern is promoted: id="code__jwt-library-defaults-unsafe",
               weighted_confidence=1.0 (all expert-depth), freshness="fresh".
  Step 4  you run inject_context before the next agent task.
             BEFORE detect_patterns → no patterns in context.
             AFTER  detect_patterns → the specific ``recommended_fix`` appears
             in context.patterns[0].recommended_fix.
  Step 5  you run propose_recommendation.
             → A draft recipe is emitted referencing the pattern.
             → The recommendation YAML is written to disk.

  The Proof
  ─────────
  The test asserts the "before" and "after" inject_context calls explicitly:

    BEFORE:  context.patterns == []   (agent had no guidance)
    AFTER:   context.patterns[0].recommended_fix contains
             "verify_exp: True"       (agent now has the exact fix)

  That delta — from zero guidance to specific, actionable guidance derived
  purely from your own corrections — is the compounding organizational
  judgment the Judgment phase is designed to produce.

─────────────────────────────────────────────────────────────────────────────

Run this test:

    ./mcp_server/devops/test.sh --integration -k scenario -v
    python -m pytest mcp_server/tests/integration/test_judgment_scenario.py -v

Reference:
    ivd/judgment_layer.md           — canonical spec
    ivd/framework.md §Principle 9   — Judgment Compounds
    ivd/cookbook.md §Principle 9    — activation and compounding
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from judgment import JUDGMENT_DIRNAME, PATTERN_PROMOTION_THRESHOLD
from mcp_server.tools.judgment import (
    judgment_capture_tool,
    judgment_detect_patterns_tool,
    judgment_inject_context_tool,
    judgment_init_tool,
    judgment_propose_recommendation_tool,
    judgment_save_codified_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _j(raw: str) -> Dict[str, Any]:
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Scenario data  ← the "real world" incidents
# ---------------------------------------------------------------------------

PROJECT_DOMAINS = ["code", "security"]

# Each incident is a tuple: (raw_correction, codified_fields, domain_depth)
#
# The key design rule: ``diagnosed_cause`` is the CANONICAL ROOT-CAUSE LABEL —
# identical across all three incidents.  The engine clusters by the slugified
# first line of that field (detect.py line 66).  The raw_correction and
# expected_result differ because the symptom manifested differently each time;
# the root cause did not.  This is how the Judgment phase is meant to be used:
# same root cause, different surface manifestations.
CANONICAL_CAUSE = (
    "jwt_library_defaults_unsafe: PyJWT's jwt.decode() silently skips expiry "
    "validation unless options={'verify_exp': True} is passed explicitly."
)

CANONICAL_FIX = (
    "Always pass options={'verify_exp': True} (and 'require': ['exp'] to reject "
    "exp-less tokens) to every jwt.decode() call.  Extract into a single shared "
    "verify_token() helper so individual handlers cannot omit the flag."
)

INCIDENTS = [
    (
        # Incident 1 — auth service, caught by audience signal
        "Auth service accepted a JWT token 2 hours after its expiry timestamp. "
        "The token passed decode() without error.  Discovered during a security "
        "audit when an expired session was still able to call /api/orders.",
        {
            "expected_result": (
                "JWT tokens must be rejected after their `exp` timestamp. "
                "The auth service should return HTTP 401 for any expired token."
            ),
            "detected_via": "audience_signal",
            "diagnosed_cause": CANONICAL_CAUSE,
            "proposed_fix": CANONICAL_FIX,
            "fix_action_type": "prompt_patch",
        },
        "expert",
    ),
    (
        # Incident 2 — mobile API refresh handler, caught by you code review
        "Mobile API refresh-token handler called jwt.decode() with no options "
        "kwarg.  A user whose account was suspended 3 days ago was still able "
        "to refresh their session because the exp claim was never validated.",
        {
            "expected_result": (
                "Suspended accounts must not obtain new access tokens.  The "
                "refresh endpoint must validate expiry before issuing a new token."
            ),
            "detected_via": "user_review",
            "diagnosed_cause": CANONICAL_CAUSE,
            "proposed_fix": CANONICAL_FIX,
            "fix_action_type": "prompt_patch",
        },
        "expert",
    ),
    (
        # Incident 3 — admin panel middleware, caught by you code review
        "Admin panel JWT middleware accepted tokens that had no 'exp' claim at "
        "all.  The agent-generated middleware only checked the signature, not "
        "the claims.  A crafted exp-less token was accepted indefinitely.",
        {
            "expected_result": (
                "Tokens without an 'exp' claim must be rejected at the middleware "
                "level.  All issued tokens must carry an expiry."
            ),
            "detected_via": "user_review",
            "diagnosed_cause": CANONICAL_CAUSE,
            "proposed_fix": CANONICAL_FIX,
            "fix_action_type": "prompt_patch",
        },
        "expert",
    ),
]

# The root cause slug that must appear in the promoted pattern's id.
EXPECTED_CAUSE_SLUG = "jwt-library-defaults-unsafe"

# A substring of the fix that MUST appear in the injected context after
# the pattern is detected — this is the core feedback-loop assertion.
EXPECTED_FIX_SIGNAL = "verify_exp"


# ---------------------------------------------------------------------------
# The Scenario
# ---------------------------------------------------------------------------

class TestJwtExpiryScenario:
    """
    Full scenario: repeated JWT expiry incidents → pattern detection →
    context injection closes the feedback loop.
    """

    # -----------------------------------------------------------------------
    # Step 0 — Initialise
    # -----------------------------------------------------------------------

    def test_step0_init_creates_judgment_tree(self, tmp_path):
        result = _j(judgment_init_tool(
            project_root_arg=str(tmp_path),
            domains=PROJECT_DOMAINS,
        ))
        assert result["ok"], f"init failed: {result}"
        judgment_root = tmp_path / JUDGMENT_DIRNAME
        assert judgment_root.is_dir()
        assert (judgment_root / "baselines" / "code_baseline.yaml").exists()
        assert (judgment_root / "baselines" / "security_baseline.yaml").exists()

    # -----------------------------------------------------------------------
    # Step 1+2 — Capture + Codify each incident
    # -----------------------------------------------------------------------

    def test_step1_capture_incident_1(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=PROJECT_DOMAINS))
        raw, codified, depth = INCIDENTS[0]
        cap = _j(judgment_capture_tool(
            raw_correction=raw,
            source="user_review",
            domain="code",
            project_root_arg=str(tmp_path),
        ))
        assert cap["ok"], cap
        raw_files = list((tmp_path / JUDGMENT_DIRNAME / "ledger" / "raw").glob("*.yaml"))
        assert len(raw_files) == 1, "Expected exactly 1 raw ledger file after incident 1"

    def test_step2_codify_transitions_raw_to_codified(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=PROJECT_DOMAINS))
        raw, codified, depth = INCIDENTS[0]
        cap = _j(judgment_capture_tool(
            raw_correction=raw, source="user_review",
            domain="code", project_root_arg=str(tmp_path),
        ))
        save = _j(judgment_save_codified_tool(
            entry_id=cap["entry_id"],
            codified_yaml=yaml.safe_dump({"codified": codified, "domain_depth": depth}),
            project_root_arg=str(tmp_path),
        ))
        assert save["ok"], save
        raw_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "raw"
        codified_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "codified"
        assert not list(raw_dir.glob("*.yaml")), "Raw file should be gone after codify"
        assert len(list(codified_dir.glob("*.yaml"))) == 1

    # -----------------------------------------------------------------------
    # Step 3 — Before-detect: no patterns yet, inject returns empty patterns
    # -----------------------------------------------------------------------

    def test_step3_no_patterns_before_detect(self, tmp_path):
        """
        This is the 'before' snapshot.  The agent has been given no guidance.
        If it were running NOW it would make the same JWT mistake again.
        """
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=PROJECT_DOMAINS))
        # Capture all 3 incidents but do NOT run detect_patterns yet
        for i, (raw, codified, depth) in enumerate(INCIDENTS):
            cap = _j(judgment_capture_tool(
                raw_correction=raw, source="user_review",
                domain="code", project_root_arg=str(tmp_path),
            ))
            _j(judgment_save_codified_tool(
                entry_id=cap["entry_id"],
                codified_yaml=yaml.safe_dump({"codified": codified, "domain_depth": depth}),
                project_root_arg=str(tmp_path),
            ))

        inj = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path),
            domain="code",
        ))
        assert inj["ok"], inj
        patterns_before = inj["context"]["patterns"]
        assert patterns_before == [], (
            "BEFORE detect_patterns there must be zero patterns in context — "
            f"the agent would have received no guidance.  Got: {patterns_before}"
        )

    # -----------------------------------------------------------------------
    # Step 4 — Detect: pattern is promoted from the 3 codified entries
    # -----------------------------------------------------------------------

    def _setup_all_incidents(self, project: Path) -> None:
        """Capture + codify all 3 incidents. Helper reused by multiple steps."""
        _j(judgment_init_tool(project_root_arg=str(project), domains=PROJECT_DOMAINS))
        for raw, codified, depth in INCIDENTS:
            cap = _j(judgment_capture_tool(
                raw_correction=raw, source="user_review",
                domain="code", project_root_arg=str(project),
            ))
            _j(judgment_save_codified_tool(
                entry_id=cap["entry_id"],
                codified_yaml=yaml.safe_dump({"codified": codified, "domain_depth": depth}),
                project_root_arg=str(project),
            ))

    def test_step4_detect_promotes_jwt_pattern(self, tmp_path):
        self._setup_all_incidents(tmp_path)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        assert det["ok"], det
        assert len(det["promoted_patterns"]) >= 1, (
            f"Expected at least 1 promoted pattern, got: {det['promoted_patterns']}"
        )
        pattern_id = det["promoted_patterns"][0]["pattern_id"]
        assert EXPECTED_CAUSE_SLUG in pattern_id, (
            f"Pattern id should contain '{EXPECTED_CAUSE_SLUG}', got: '{pattern_id}'"
        )

    def test_step4_pattern_yaml_on_disk_has_correct_cause(self, tmp_path):
        self._setup_all_incidents(tmp_path)
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        patterns_dir = tmp_path / JUDGMENT_DIRNAME / "patterns"
        yamls = list(patterns_dir.glob("*.yaml"))
        assert len(yamls) == 1, f"Expected 1 pattern file, got {len(yamls)}"
        artifact = yaml.safe_load(yamls[0].read_text())
        assert artifact["member_count"] == len(INCIDENTS), (
            f"Pattern should have {len(INCIDENTS)} members, got {artifact['member_count']}"
        )
        assert artifact["fix_action_type"] == "prompt_patch"
        assert EXPECTED_CAUSE_SLUG in artifact["id"]
        # The engine stamped it — confirm it has a hash and version
        assert artifact.get("engine_version") is not None
        assert artifact.get("detection_hash") is not None

    def test_step4_pattern_confidence_reflects_expert_depth(self, tmp_path):
        """
        All 3 incidents were coded as ``domain_depth=expert``.
        Expert entries have the highest weight (1.0) so weighted_confidence
        should equal 1.0 — the signal is maximally strong.
        """
        self._setup_all_incidents(tmp_path)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        conf = det["promoted_patterns"][0]["weighted_confidence"]
        assert conf == 1.0, (
            f"All expert-depth entries should yield weighted_confidence=1.0, got {conf}"
        )

    # -----------------------------------------------------------------------
    # Step 5 — The feedback loop closes: inject_context NOW contains the fix
    # -----------------------------------------------------------------------

    def test_step5_inject_context_after_detect_contains_fix(self, tmp_path):
        """
        The core feedback-loop assertion.

        After detect_patterns, inject_context must return the specific fix
        that would prevent the agent from generating unsafe JWT code.
        The critical assertion is that ``verify_exp`` appears in the injected
        context — that is exactly the piece of knowledge the agent was missing
        in every incident.

        Before:  context.patterns == []          (agent is blind)
        After:   context.patterns[0]             (agent has the guidance)
                   .recommended_fix contains 'verify_exp'
        """
        self._setup_all_incidents(tmp_path)

        # --- BEFORE ---
        inj_before = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        patterns_before = inj_before["context"]["patterns"]

        # --- detect ---
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))

        # --- AFTER ---
        inj_after = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        patterns_after = inj_after["context"]["patterns"]

        # 1. The before/after delta exists
        assert patterns_before == [], (
            "BEFORE: agent had no pattern guidance — it would repeat the mistake"
        )
        assert len(patterns_after) >= 1, (
            "AFTER: at least one pattern must appear in context"
        )

        # 2. The fix signal is present
        first_pattern = patterns_after[0]
        recommended_fix = first_pattern.get("recommended_fix", "")
        assert EXPECTED_FIX_SIGNAL in recommended_fix, (
            f"The injected context must contain '{EXPECTED_FIX_SIGNAL}' in "
            f"recommended_fix so the agent knows the exact fix.  Got:\n"
            f"  recommended_fix = {recommended_fix!r}"
        )

        # 3. The cause slug is right
        assert EXPECTED_CAUSE_SLUG in first_pattern.get("pattern_id", ""), (
            f"Pattern in context should reference '{EXPECTED_CAUSE_SLUG}'"
        )

        # 4. The context carries freshness + confidence so the agent can judge weight
        assert first_pattern.get("freshness") in ("fresh", "aging"), (
            "Injected pattern must be fresh or aging to be actionable"
        )
        assert first_pattern.get("weighted_confidence", 0) > 0, (
            "Injected pattern must have a positive confidence score"
        )

        # 5. The hashes differ — the two calls returned different context states
        assert inj_before["injection_hash"] != inj_after["injection_hash"], (
            "injection_hash must change when patterns are added to the context"
        )

    def test_step5_recent_corrections_present_before_pattern_promoted(self, tmp_path):
        """
        Even before a pattern exists, inject_context returns the raw
        codified corrections as ``recent_corrections``.  This is the
        'early signal' layer — useful before 3 incidents accumulate.
        """
        self._setup_all_incidents(tmp_path)
        # No detect_patterns call — patterns layer is empty
        inj = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        recent = inj["context"]["recent_corrections"]
        assert len(recent) == len(INCIDENTS), (
            f"Expected {len(INCIDENTS)} recent_corrections (one per incident), "
            f"got {len(recent)}"
        )
        # Each correction should mention the cause
        causes = " ".join(
            (r.get("diagnosed_cause") or "") for r in recent
        )
        assert "jwt" in causes.lower(), (
            "recent_corrections should surface the JWT cause text"
        )

    # -----------------------------------------------------------------------
    # Step 6 — Propose recommendation writes an actionable draft
    # -----------------------------------------------------------------------

    def test_step6_propose_recommendation_references_pattern(self, tmp_path):
        self._setup_all_incidents(tmp_path)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        pattern_id = det["promoted_patterns"][0]["pattern_id"]

        rec = _j(judgment_propose_recommendation_tool(
            pattern_id=pattern_id,
            project_root_arg=str(tmp_path),
            notes="Surfaced from 3 independent incidents across auth/mobile/admin.",
        ))
        assert rec["ok"], rec
        assert rec["fix_action_type"] == "prompt_patch"
        assert rec["awaiting"] == "user_approval"

        # Verify the YAML on disk
        rec_dir = tmp_path / JUDGMENT_DIRNAME / "recommendations"
        yamls = list(rec_dir.glob("*.yaml"))
        assert len(yamls) == 1
        artifact = yaml.safe_load(yamls[0].read_text())

        assert artifact["source_pattern"] == pattern_id
        assert artifact["state"] == "draft"
        summary = artifact.get("pattern_summary") or {}
        assert summary.get("member_count") == len(INCIDENTS)
        assert EXPECTED_FIX_SIGNAL in (summary.get("recommended_fix") or ""), (
            f"Recommendation summary must include '{EXPECTED_FIX_SIGNAL}'"
        )

    def test_step6_draft_recipe_is_generated_for_prompt_patch(self, tmp_path):
        """
        For fix_action_type=prompt_patch the engine auto-generates a starter
        recipe YAML that you can paste directly into recipes/.
        """
        self._setup_all_incidents(tmp_path)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        pattern_id = det["promoted_patterns"][0]["pattern_id"]
        rec = _j(judgment_propose_recommendation_tool(
            pattern_id=pattern_id,
            project_root_arg=str(tmp_path),
        ))
        draft = rec.get("draft_recipe_yaml")
        assert draft is not None, "prompt_patch should produce a draft recipe"
        parsed_recipe = yaml.safe_load(draft)
        assert "recipe" in parsed_recipe, "Draft should be a valid recipe skeleton"
        assert parsed_recipe["recipe"].get("category") == "judgment"
        assert pattern_id in (parsed_recipe.get("source_pattern") or ""), (
            "Draft recipe must reference the source pattern"
        )

    # -----------------------------------------------------------------------
    # Step 7 — The full story as one sequential test
    # -----------------------------------------------------------------------

    def test_full_jwt_scenario_end_to_end(self, tmp_path):
        """
        The complete scenario in one sequential test that tells the full story.
        This is the definitive 'does the Judgment phase work?' test.
        Read it top-to-bottom to understand the compounding feedback loop.
        """
        # ── Setup ──────────────────────────────────────────────────────────
        init = _j(judgment_init_tool(
            project_root_arg=str(tmp_path), domains=PROJECT_DOMAINS,
        ))
        assert init["ok"]

        # ── No guidance yet ────────────────────────────────────────────────
        inj0 = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        assert inj0["context"]["patterns"] == [], "No patterns before any incidents"

        # ── Three incidents happen ─────────────────────────────────────────
        entry_ids = []
        for raw, codified, depth in INCIDENTS:
            cap = _j(judgment_capture_tool(
                raw_correction=raw, source="user_review",
                domain="code", project_root_arg=str(tmp_path),
            ))
            assert cap["ok"]
            save = _j(judgment_save_codified_tool(
                entry_id=cap["entry_id"],
                codified_yaml=yaml.safe_dump({"codified": codified, "domain_depth": depth}),
                project_root_arg=str(tmp_path),
            ))
            assert save["ok"]
            entry_ids.append(cap["entry_id"])

        # Still no patterns — only 3 codified entries, detect not run yet
        inj1 = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        assert inj1["context"]["patterns"] == [], (
            "No patterns until detect_patterns is called"
        )
        # But recent_corrections IS already useful
        assert len(inj1["context"]["recent_corrections"]) == 3, (
            "recent_corrections should have 3 entries before detect"
        )

        # ── you run detect_patterns ───────────────────────────────────────
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        assert det["ok"]
        assert len(det["promoted_patterns"]) == 1, (
            f"Expected exactly 1 pattern promoted, got: {det['promoted_patterns']}"
        )
        pattern = det["promoted_patterns"][0]
        assert pattern["member_count"] == 3
        assert pattern["weighted_confidence"] == 1.0
        assert EXPECTED_CAUSE_SLUG in pattern["pattern_id"]

        # ── The feedback loop closes ───────────────────────────────────────
        inj2 = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        assert inj2["ok"]
        patterns_in_context = inj2["context"]["patterns"]

        assert len(patterns_in_context) == 1, (
            "Exactly one pattern should be in context after detect"
        )
        fix_in_context = patterns_in_context[0]["recommended_fix"]
        assert EXPECTED_FIX_SIGNAL in fix_in_context, (
            f"\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  THE FEEDBACK LOOP DID NOT CLOSE.\n"
            f"  The injected context did not contain '{EXPECTED_FIX_SIGNAL}'.\n"
            f"  The next agent run would repeat the JWT expiry mistake.\n"
            f"  Got recommended_fix:\n  {fix_in_context!r}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        # ── Hash audit trail ───────────────────────────────────────────────
        # Context changed — hashes must differ
        assert inj0["injection_hash"] != inj2["injection_hash"], (
            "injection_hash must change when a pattern enters context"
        )
        # Context is stable when nothing changes — running again gives same hash
        inj3 = _j(judgment_inject_context_tool(
            project_root_arg=str(tmp_path), domain="code",
        ))
        assert inj2["injection_hash"] == inj3["injection_hash"], (
            "injection_hash must be stable when context has not changed"
        )

        # ── Recommendation ─────────────────────────────────────────────────
        rec = _j(judgment_propose_recommendation_tool(
            pattern_id=pattern["pattern_id"],
            project_root_arg=str(tmp_path),
        ))
        assert rec["ok"]
        assert rec["fix_action_type"] == "prompt_patch"
        assert rec["draft_recipe_yaml"] is not None

        rec_dir = tmp_path / JUDGMENT_DIRNAME / "recommendations"
        assert len(list(rec_dir.glob("*.yaml"))) == 1

        # ── Final state summary ────────────────────────────────────────────
        # 3 codified entries, 0 raw, 1 pattern, 1 recommendation
        codified_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "codified"
        raw_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "raw"
        patterns_dir = tmp_path / JUDGMENT_DIRNAME / "patterns"

        assert len(list(raw_dir.glob("*.yaml"))) == 0, "No raw entries should remain"
        assert len(list(codified_dir.glob("*.yaml"))) == 3
        assert len(list(patterns_dir.glob("*.yaml"))) == 1
        assert len(list(rec_dir.glob("*.yaml"))) == 1
