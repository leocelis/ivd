# mcp_server/tests/integration/test_judgment_demo.py

"""
Reproducibility test for the Judgment showcase demo.

The demo at ``examples/judgment_demo/run_demo.py`` is the runnable
showcase we point new users at when they ask "what does IVD Judgment
actually DO for me?".  It needs a regression guard that fires the
moment any of its user-visible claims stop being true.

This test re-runs the demo functions in-process (no subprocess noise),
points them at a tmp directory, and asserts the user-visible properties
any reader of the demo will check:

  1. The before/after/diff markdown files are produced and contain the
     literal phrases that make the demo land.
  2. The system message the agent sees AFTER Judgment includes the
     project's three testing conventions (MSW handlers,
     renderWithProviders helper, userEvent.setup discipline) that did
     not exist BEFORE.
  3. The diff is non-empty and surfaces those convention names.
  4. The canned LLM responses (used when OPENAI_API_KEY is unset) match
     the empirical pattern they document — framework defaults
     (vi.fn / bare render / userEvent.click without setup) in the
     BEFORE reply, project conventions (server.use / renderWithProviders
     / userEvent.setup) in the AFTER reply.

The third class of assertions is the most important: those project
conventions cannot have come from the model's training data, so seeing
them in the AFTER response IS the proof that Judgment changed the
agent's behavior.  If THIS test breaks, the demo no longer demonstrates
the feedback loop — and we want to know loudly before a user sees a
broken demo.

Reference:
    examples/judgment_demo/README.md  — the narrative the demo backs
    examples/judgment_demo/run_demo.py — the script under test
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEMO_PATH = REPO_ROOT / "examples" / "judgment_demo" / "run_demo.py"


# ---------------------------------------------------------------------------
# Import the demo as a module without executing main()
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def demo_module():
    """Import run_demo.py without firing its __main__ block."""
    spec = importlib.util.spec_from_file_location("judgment_demo.run_demo", DEMO_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["judgment_demo.run_demo"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Drive the demo against a tmp project (no demo/output side effects)
# ---------------------------------------------------------------------------

@pytest.fixture
def driven_demo(demo_module, tmp_path):
    """
    Run the full Judgment loop programmatically against tmp_path and
    return the rendered before/after/diff strings + the inject payload.
    """
    project_root = tmp_path / "your_project"
    project_root.mkdir()

    demo_module.init_judgment(project_root)
    for i, incident in enumerate(demo_module.INCIDENTS, start=1):
        demo_module.capture_incident(project_root, incident, i)

    inject_before = demo_module.show_state_before_detect(project_root)
    detect = demo_module.detect_patterns(project_root)
    inject_after = demo_module.show_state_after_detect(project_root)

    before_md = demo_module.render_before_md(demo_module.NEXT_AGENT_REQUEST)
    after_md = demo_module.render_after_md(demo_module.NEXT_AGENT_REQUEST, inject_after)
    diff_md = demo_module.render_diff_md(before_md, after_md)

    return {
        "module": demo_module,
        "project_root": project_root,
        "inject_before": inject_before,
        "inject_after": inject_after,
        "detect": detect,
        "before_md": before_md,
        "after_md": after_md,
        "diff_md": diff_md,
    }


# ---------------------------------------------------------------------------
# The three project conventions the demo is built around.  These strings
# are the contract: they MUST appear in the AFTER response and MUST NOT
# appear in the BEFORE artifact (which is just the bare system prompt).
# ---------------------------------------------------------------------------

# Substrings that uniquely identify each convention.  At least one
# variant per convention is required.
PROJECT_CONVENTIONS = {
    "msw_server_use":      ("server.use(",),
    "msw_handler":         ("http.get(", "http.post(", "rest.get(", "rest.post("),
    "render_with_providers": ("renderWithProviders(",),
    "user_event_setup":    ("userEvent.setup()",),
}

# Substrings that mark the framework defaults the BEFORE response
# reaches for instead of the project conventions.  These are the
# anti-patterns you corrected three times and that the canned
# CANNED_BEFORE_RESPONSE must keep showing.
FRAMEWORK_DEFAULTS_API_MOCK = (
    "global.fetch = vi.fn",
    "global.fetch = jest.fn",
    "vi.mock(",
    "jest.mock(",
    ".mockResolvedValue(",
    ".mockReturnValue(",
    "as jest.Mock",
    "as vi.Mock",
)


def _has_any(text: str, needles) -> bool:
    return any(n in text for n in needles)


def _has_bare_render(code: str) -> bool:
    """`render(` from @testing-library/react with no `renderWithProviders(`."""
    if "renderWithProviders(" in code:
        return False
    if "render(" not in code:
        return False
    return ("from '@testing-library/react'" in code
            or 'from "@testing-library/react"' in code)


def _has_userevent_click_without_setup(code: str) -> bool:
    if "userEvent.setup()" in code:
        return False
    return "userEvent.click(" in code or "fireEvent.click(" in code


# ---------------------------------------------------------------------------
# Property 1 — the demo runs cleanly end-to-end
# ---------------------------------------------------------------------------

class TestDemoRunsCleanly:
    def test_init_creates_judgment_folder(self, driven_demo):
        judgment_dir = driven_demo["project_root"] / ".judgment"
        assert judgment_dir.is_dir(), "init step did not create .judgment/"

    def test_three_incidents_land_in_codified(self, driven_demo):
        codified = driven_demo["project_root"] / ".judgment" / "ledger" / "codified"
        files = list(codified.glob("*.yaml"))
        assert len(files) == 3, (
            f"Demo should produce exactly 3 codified ledger entries, got {len(files)}"
        )

    def test_exactly_one_pattern_is_promoted(self, driven_demo):
        promoted = driven_demo["detect"]["promoted_patterns"]
        assert len(promoted) == 1, (
            f"Demo should promote exactly 1 pattern (3 incidents, same root cause); "
            f"got {len(promoted)}"
        )

    def test_pattern_carries_max_confidence(self, driven_demo):
        pattern = driven_demo["detect"]["promoted_patterns"][0]
        assert pattern["weighted_confidence"] == 1.0, (
            "Demo uses 3 expert-depth incidents; weighted_confidence must be 1.0 "
            "or the 'max signal' narrative breaks"
        )
        assert pattern["member_count"] == 3
        assert pattern["freshness"] == "fresh"


# ---------------------------------------------------------------------------
# Property 2 — the BEFORE/AFTER markdown files have the punch they advertise
# ---------------------------------------------------------------------------

class TestBeforeAfterMarkdown:
    """
    The point of the demo is that BEFORE and AFTER are different in a way
    a human can see immediately.  These tests pin the specific phrases
    that make that contrast visible to a reader.
    """

    def test_before_md_contains_user_request_and_no_lessons(self, driven_demo):
        before = driven_demo["before_md"]
        assert "## SYSTEM" in before
        assert "## USER" in before
        # The user request is the <UserMenu /> Vitest prompt — pin two
        # distinctive phrases so a request rewrite doesn't silently
        # break the test.
        assert "<UserMenu />" in before, (
            "BEFORE must contain the user request that the AFTER will be "
            "graded against"
        )
        assert "Vitest test file" in before, (
            "BEFORE must contain the user request specifically asking for "
            "a Vitest test file"
        )
        assert "LESSONS LEARNED" not in before, (
            "BEFORE must NOT contain the lessons block — that is the entire "
            "before/after delta"
        )
        # The project conventions must be ABSENT from the BEFORE system
        # message: those names live in the captured/promoted Pattern, not
        # in the base system prompt the agent gets on day one.
        for convention in ("renderWithProviders", "server.use", "userEvent.setup"):
            assert convention not in before, (
                f"BEFORE must NOT contain '{convention}' — Judgment hasn't "
                f"compounded yet, so the agent has no parametric or "
                f"contextual knowledge of this project-local helper"
            )

    def test_after_md_contains_lessons_and_all_three_conventions(self, driven_demo):
        after = driven_demo["after_md"]
        assert "LESSONS LEARNED" in after, (
            "AFTER must contain the LESSONS LEARNED block — that is the "
            "before/after delta any reader will look for first"
        )
        # Each of the three conventions must be referenced in the
        # injected guidance.  These names are project-local — their
        # presence in the system message is the entire reason the agent
        # adopts them in the next response.
        for convention in (
            "MSW",
            "renderWithProviders",
            "userEvent.setup()",
            "server.use",
            "src/test/test-utils",
            "src/test/mocks/server",
        ):
            assert convention in after, (
                f"AFTER must contain '{convention}' — without it the agent "
                f"would not learn the project's testing convention.  The "
                f"recommended_fix string was likely truncated."
            )
        assert "Confidence:** 1.0" in after or "Confidence:** 1.0 " in after, (
            "AFTER must show the confidence number so the agent treats "
            "the guidance as a hard constraint, not a suggestion"
        )
        assert "from 3 incidents" in after, (
            "AFTER must surface the member_count so the agent knows this "
            "isn't a one-off correction"
        )

    def test_after_includes_same_user_request_as_before(self, driven_demo):
        """The before/after delta must hold the user request constant."""
        before = driven_demo["before_md"]
        after = driven_demo["after_md"]
        request = driven_demo["module"].NEXT_AGENT_REQUEST
        assert request in before
        assert request in after


# ---------------------------------------------------------------------------
# Property 3 — the diff file actually shows the compounding
# ---------------------------------------------------------------------------

class TestDiffArtifact:
    def test_diff_contains_the_lessons_addition(self, driven_demo):
        diff = driven_demo["diff_md"]
        assert (
            "+ ## LESSONS LEARNED" in diff
            or "+ ## LESSONS LEARNED IN THIS PROJECT (from past corrections)" in diff
        ), (
            "diff.md must show the LESSONS LEARNED block as an addition — "
            "that block IS the visible compounding"
        )
        # At least one of the three project-convention names must be in
        # the added lines.  Without that, the diff is just structural
        # markdown and the user has nothing to point at.
        assert (
            "renderWithProviders" in diff
            or "server.use" in diff
            or "userEvent.setup" in diff
        ), (
            "diff.md must surface at least one of the project's testing "
            "conventions as added text"
        )

    def test_diff_is_non_trivial(self, driven_demo):
        diff = driven_demo["diff_md"]
        added_lines = [ln for ln in diff.splitlines() if ln.startswith("+ ")]
        assert len(added_lines) >= 5, (
            f"Diff should show at least 5 added lines; got {len(added_lines)}.  "
            "If this fires, render_diff_md or render_after_md regressed."
        )


# ---------------------------------------------------------------------------
# Property 4 — context state actually changed (auditable)
# ---------------------------------------------------------------------------

class TestContextDelta:
    def test_patterns_in_context_jump_from_zero_to_one(self, driven_demo):
        before = driven_demo["inject_before"]["context"]["patterns"]
        after = driven_demo["inject_after"]["context"]["patterns"]
        assert len(before) == 0, (
            "BEFORE detect_patterns there must be 0 patterns in context "
            "or the demo's narrative is wrong"
        )
        assert len(after) == 1, (
            f"AFTER detect_patterns there must be exactly 1 pattern; got {len(after)}"
        )

    def test_injection_hash_changes(self, driven_demo):
        before = driven_demo["inject_before"]["injection_hash"]
        after = driven_demo["inject_after"]["injection_hash"]
        assert before != after, (
            "injection_hash MUST change when a pattern enters context — "
            "this is the audit signal the demo advertises"
        )

    def test_recommended_fix_in_context_contains_all_three_conventions(
        self, driven_demo
    ):
        patterns = driven_demo["inject_after"]["context"]["patterns"]
        assert patterns, "no patterns in AFTER context"
        recommended_fix = patterns[0]["recommended_fix"]
        for required in (
            "MSW",
            "renderWithProviders",
            "userEvent.setup()",
        ):
            assert required in recommended_fix, (
                f"recommended_fix in injected context is missing '{required}' — "
                f"the agent would not learn the actual fix.  Got:\n{recommended_fix!r}"
            )


# ---------------------------------------------------------------------------
# Property 5 — the canned LLM outputs land the contrast
# ---------------------------------------------------------------------------

class TestCannedLlmOutputs:
    """
    When OPENAI_API_KEY is not set the demo falls back to canned outputs.
    Those outputs are what most offline readers will see, so they need to
    actually demonstrate the BEFORE/AFTER behavioral diff the README
    claims is the demo's core result:

      BEFORE: framework defaults (vi.fn / bare render / userEvent.click)
      AFTER : project conventions (server.use / renderWithProviders /
              userEvent.setup)
    """

    def test_canned_before_uses_framework_default_api_mock(self, demo_module):
        """The canned BEFORE must reach for vi.fn() / global.fetch /
        mockResolvedValue — the framework default.  Without this the
        contrast against MSW in the AFTER is invisible."""
        before = demo_module.CANNED_BEFORE_RESPONSE
        present = [t for t in FRAMEWORK_DEFAULTS_API_MOCK if t in before]
        assert present, (
            f"Canned BEFORE response must show the API-mocking framework "
            f"default — at least one of {FRAMEWORK_DEFAULTS_API_MOCK}.  "
            f"Got none.  The demo's before/after contrast vanishes "
            f"without this."
        )

    def test_canned_before_uses_bare_render(self, demo_module):
        before = demo_module.CANNED_BEFORE_RESPONSE
        assert _has_bare_render(before), (
            "Canned BEFORE response must use bare render(<UserMenu />) "
            "from @testing-library/react — the framework default the "
            "AFTER response is supposed to replace with renderWithProviders."
        )

    def test_canned_before_calls_userevent_click_without_setup(self, demo_module):
        before = demo_module.CANNED_BEFORE_RESPONSE
        assert _has_userevent_click_without_setup(before), (
            "Canned BEFORE response must call userEvent.click(...) (or "
            "fireEvent.click) without userEvent.setup() — the framework "
            "default the AFTER response is supposed to fix."
        )

    def test_canned_after_uses_msw_server_use(self, demo_module):
        after = demo_module.CANNED_AFTER_RESPONSE
        assert _has_any(after, PROJECT_CONVENTIONS["msw_server_use"]), (
            "Canned AFTER response must call server.use(...) — the "
            "project's MSW override pattern.  Without it the agent never "
            "learns the convention."
        )
        assert _has_any(after, PROJECT_CONVENTIONS["msw_handler"]), (
            "Canned AFTER response must use http.get/http.post or "
            "rest.get/rest.post inside server.use(...)."
        )

    def test_canned_after_uses_renderwithproviders(self, demo_module):
        after = demo_module.CANNED_AFTER_RESPONSE
        assert _has_any(after, PROJECT_CONVENTIONS["render_with_providers"]), (
            "Canned AFTER response must call renderWithProviders(<UserMenu />) "
            "— the project's render helper.  This name does not exist on "
            "the public internet, so its presence here proves the agent "
            "got it from the injected Pattern."
        )
        assert not _has_bare_render(after), (
            "Canned AFTER response must NOT also use a bare render() — "
            "that would mean the lesson was only partially applied."
        )

    def test_canned_after_uses_userevent_setup(self, demo_module):
        after = demo_module.CANNED_AFTER_RESPONSE
        assert _has_any(after, PROJECT_CONVENTIONS["user_event_setup"]), (
            "Canned AFTER response must call userEvent.setup() — the "
            "project's user-event v14+ discipline."
        )
        assert not _has_userevent_click_without_setup(after), (
            "Canned AFTER response must not call userEvent.click() / "
            "fireEvent.click() without setup() — the lesson was only "
            "partially applied."
        )

    def test_canned_after_dropped_api_mock_anti_pattern(self, demo_module):
        """The AFTER must drop the BEFORE's API-mocking anti-pattern in
        favor of MSW.  A bare jest.fn() spy inside an MSW handler is OK
        — only the API-stubbing idioms are anti-patterns."""
        after = demo_module.CANNED_AFTER_RESPONSE
        present = [t for t in FRAMEWORK_DEFAULTS_API_MOCK if t in after]
        assert not present, (
            f"Canned AFTER response should not contain API-mocking idioms "
            f"like {FRAMEWORK_DEFAULTS_API_MOCK}; found {present}.  These "
            f"are the patterns we explicitly told the agent to drop."
        )

    def test_canned_outputs_are_typescript_code_blocks(self, demo_module):
        for name, blob in (
            ("CANNED_BEFORE_RESPONSE", demo_module.CANNED_BEFORE_RESPONSE),
            ("CANNED_AFTER_RESPONSE", demo_module.CANNED_AFTER_RESPONSE),
        ):
            assert blob.startswith("```typescript"), (
                f"{name} must be a typescript code block (it's a Vitest "
                f"test file)"
            )
            assert blob.rstrip().endswith("```"), f"{name} must close its code fence"


# ---------------------------------------------------------------------------
# Property 6 — running the script as __main__ actually writes the artifacts
# ---------------------------------------------------------------------------

class TestScriptWritesArtifacts:
    """
    Smoke test: does ``run_demo.main()`` actually produce the four files
    the README directs users to read?  This catches the case where the
    script runs cleanly but writes to the wrong directory or skips a
    render call.
    """

    def test_main_creates_output_files(self, demo_module, monkeypatch, tmp_path):
        # Redirect output to a tmp directory so this test does not stomp
        # on the user's local examples/judgment_demo/output/.
        original_setup = demo_module.setup_clean_workspace

        def _setup_in_tmp() -> Path:
            project_root = tmp_path / "your_project"
            project_root.mkdir()
            return project_root

        monkeypatch.setattr(demo_module, "setup_clean_workspace", _setup_in_tmp)
        # Force offline canned mode regardless of an OPENAI_API_KEY in env.
        monkeypatch.setattr(
            demo_module,
            "call_llm_if_configured",
            lambda *a, **kw: (
                demo_module.CANNED_BEFORE_RESPONSE,
                demo_module.CANNED_AFTER_RESPONSE,
                False,
            ),
        )

        rc = demo_module.main()
        assert rc == 0, "demo main() returned non-zero"

        for name in ("before.md", "after.md", "diff.md", "llm_responses.md"):
            assert (tmp_path / name).is_file(), f"missing artifact: {name}"

        monkeypatch.setattr(demo_module, "setup_clean_workspace", original_setup)
