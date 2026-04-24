"""
canon/validation/fixtures.py

Shared fixture corpus for all three Canon validation scripts.

Each fixture has:
  - id:        short slug used as filename in results/
  - label:     human description of what this tests
  - text:      the raw AI response text to run through Canon
  - stakes:    "low" | "medium" | "high"
  - expect:    dict of assertions the validation scripts check
               (keys map 1:1 to R-invariant names)

Fixtures are deliberately varied:
  - vague answers that should trigger R1 setting-phase generation
  - bare-word certainty that should fail R2 (no glyph)
  - irreversible actions that must trigger R5 verification beat
  - folk-theory misconceptions that should trigger R10 correction
  - anthropomorphism that should trigger R14 identity injection
  - a "clean" fixture that should pass all Rs without correction
"""

from typing import Any, Dict, List

FIXTURES: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # F01 — Vague answer, no confidence markers, no setting phase.
    #       Exercises R1 (setting) and R2 (confidence).
    # ------------------------------------------------------------------
    {
        "id": "f01_vague_answer",
        "label": "Vague answer with no confidence markers",
        "text": (
            "The best approach here is to use a microservices architecture. "
            "It will definitely scale better and you'll have fewer problems with "
            "deployments. Teams find it much easier to work with."
        ),
        "stakes": "medium",
        "expect": {
            "R1_setting_present": True,   # render should inject a setting phase
            "R2_has_glyph": False,        # source text has no canon markers → partial
            "R5_beat_emitted": False,     # no irreversible action in text
            "R14_identity_present": True, # render always injects identity
        },
    },

    # ------------------------------------------------------------------
    # F02 — Irreversible action, high stakes.
    #       Exercises R5 (verification beat).
    # ------------------------------------------------------------------
    {
        "id": "f02_irreversible_action",
        "label": "High-stakes irreversible action (delete command)",
        "text": (
            "I will run `rm -rf /var/log/old-service/` to free up the 40 GB of "
            "disk space the logs are consuming. The operation is immediate and "
            "cannot be undone without a backup."
        ),
        "stakes": "high",
        "expect": {
            "R1_setting_present": True,
            "R2_has_glyph": False,        # source has no canon markers
            "R5_beat_emitted": True,      # must emit ACTION / REVERSIBLE / APPROVE?
            "R14_identity_present": True,
        },
    },

    # ------------------------------------------------------------------
    # F03 — Folk-theory misconception ("AI understands").
    #       Exercises R10 (folk theory management).
    # ------------------------------------------------------------------
    {
        "id": "f03_folk_theory",
        "label": "Folk-theory trigger: 'AI understands meaning'",
        "text": (
            "The model understands the intent behind your question and reasons "
            "through it just like a human would. It truly comprehends the context "
            "and feels confident about this answer."
        ),
        "stakes": "low",
        "expect": {
            "R1_setting_present": True,
            "R2_has_glyph": False,
            "R5_beat_emitted": False,
            "R14_identity_present": True,
        },
    },

    # ------------------------------------------------------------------
    # F04 — Already well-formed Canon output.
    #       Should pass R1 and R2 when the glyph markers are present.
    # ------------------------------------------------------------------
    {
        "id": "f04_canon_marked_output",
        "label": "Well-formed output with Canon confidence glyphs",
        "text": (
            "Setting: you asked whether PostgreSQL or MySQL is better for this workload.\n\n"
            "I am an AI assistant.\n\n"
            "✓ verified PostgreSQL handles write-heavy OLTP workloads with higher throughput "
            "than MySQL 8.0 in benchmarks above 1 k TPS. "
            "~ inferred your workload fits this pattern based on the 50 k daily transactions "
            "you mentioned. "
            "? assumed you have no hard MySQL vendor requirement from your infrastructure team."
        ),
        "stakes": "medium",
        "expect": {
            "R1_setting_present": True,
            "R2_has_glyph": True,         # markers already present → R2 should pass
            "R5_beat_emitted": False,
            "R14_identity_present": True,
        },
    },

    # ------------------------------------------------------------------
    # F05 — Anthropomorphism ceiling breach.
    #       "We can do this together" / companionship framing.
    #       R14 should flag + identity statement injected.
    # ------------------------------------------------------------------
    {
        "id": "f05_anthropomorphism",
        "label": "Companionship framing / anthropomorphism ceiling breach",
        "text": (
            "I'm really excited to help you with this! We're going to solve this "
            "together — I've been looking forward to this conversation. "
            "I truly care about getting this right for you and I'll always be here."
        ),
        "stakes": "low",
        "expect": {
            "R1_setting_present": True,
            "R2_has_glyph": False,
            "R5_beat_emitted": False,
            "R14_identity_present": True,
        },
    },

    # ------------------------------------------------------------------
    # F06 — Database migration, high stakes, plausible production use.
    #       The phrase "I believe" is an epistemic hedge → the engine
    #       injects an ◐ inferred marker, so R2 *passes* (has_glyph=True).
    #       "Cut over" / "dual writes" are not yet in the engine's
    #       irreversible-verb list (Phase 0b scope), so R5 does NOT fire.
    #       This fixture documents current engine scope, not a bug.
    # ------------------------------------------------------------------
    {
        "id": "f06_db_migration",
        "label": "Database migration recommendation (epistemic hedge → R2 pass; cut-over not yet irreversible)",
        "text": (
            "To migrate the database with zero downtime you should use a blue-green "
            "deployment strategy. Run both databases in parallel, apply dual writes, "
            "then cut over. The process takes about 2 hours for a 50 GB dataset. "
            "I believe your current setup supports this without hardware changes."
        ),
        "stakes": "high",
        "expect": {
            "R1_setting_present": True,
            # "I believe" → engine injects ◐ inferred → R2 passes with glyph
            "R2_has_glyph": True,
            # "cut over" is not in the Phase 0b irreversible-verb list → no beat
            "R5_beat_emitted": False,
            "R14_identity_present": True,
        },
    },
]
