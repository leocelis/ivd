# mcp_server/tests/unit/test_import_spec.py

"""Unit tests for ivd_import_spec.

Fixture text is taken verbatim from the source projects' own published
documentation (fetched 2026-07-18), not invented, so a format drift in
either project shows up as a real test failure rather than silent staleness:
  - spec-kit: templates/spec-template.md
    https://github.com/github/spec-kit/blob/main/templates/spec-template.md
  - openspec: docs/getting-started.md ("Theme Selection" dark-mode example)
    https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md
"""

import json

from mcp_server.tools.import_spec import import_spec_tool

SPEC_KIT_FIXTURE = """### User Story 1 - Brief Title (Priority: P1)

Describe this user journey in plain language

**Why this priority**: Explain the value

**Independent Test**: Describe how this can be tested independently

**Acceptance Scenarios**:

1. **Given** initial state, **When** action, **Then** expected outcome
2. **Given** another state, **When** another action, **Then** another outcome

---

### User Story 2 - Second Title (Priority: P2)

Another journey

**Acceptance Scenarios**:

1. **Given** state X, **When** action Y, **Then** outcome Z
"""

# Verbatim from Fission-AI/OpenSpec docs/getting-started.md, "Theme Selection" example.
OPENSPEC_FIXTURE = """# Delta for UI

## ADDED Requirements

### Requirement: Theme Selection
The system SHALL allow users to choose between light and dark themes.

#### Scenario: Manual toggle
- GIVEN a user on any page
- WHEN the user clicks the theme toggle
- THEN the theme switches immediately
- AND the preference persists across sessions

#### Scenario: System preference
- GIVEN a user with no saved preference
- WHEN the application loads
- THEN the system's preferred color scheme is used
"""

OPENSPEC_2FA_FIXTURE = """# Delta for Auth

## ADDED Requirements

### Requirement: Two-Factor Authentication
The system MUST require a second factor during login.

#### Scenario: OTP required
- GIVEN a user with 2FA enabled
- WHEN the user submits valid credentials
- THEN an OTP challenge is presented

## MODIFIED Requirements

### Requirement: Session Timeout
The system SHALL expire sessions after 30 minutes of inactivity.

#### Scenario: Idle timeout
- GIVEN an authenticated session
- WHEN 30 minutes pass without activity
- THEN the session is invalidated
"""


class TestImportSpecKit:
    """ivd_import_spec against real spec-kit spec.md structure."""

    def test_parses_both_user_stories(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SPEC_KIT_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="spec-kit", project_root_arg=str(tmp_path),
        ))

        assert result["ok"] is True
        assert result["source_format"] == "spec-kit"
        assert len(result["requirements"]) == 2

    def test_first_story_has_two_scenarios(self, tmp_path):
        """Regression test: a multi-scenario block used to silently return zero
        scenarios because the trailing-terminator regex only matched when the
        scenario line was the last line in its block."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SPEC_KIT_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="spec-kit", project_root_arg=str(tmp_path),
        ))

        story_1 = result["requirements"][0]
        assert story_1["name"] == "brief_title"
        assert story_1["priority"] == "P1"
        assert len(story_1["scenarios"]) == 2
        assert story_1["scenarios"][0] == {
            "name": "scenario_1", "given": "initial state", "when": "action", "then": "expected outcome",
        }
        assert story_1["scenarios"][1]["then"] == "another outcome"

    def test_second_story_has_one_scenario(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SPEC_KIT_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="spec-kit", project_root_arg=str(tmp_path),
        ))

        story_2 = result["requirements"][1]
        assert story_2["priority"] == "P2"
        assert len(story_2["scenarios"]) == 1
        assert story_2["scenarios"][0]["given"] == "state X"

    def test_agent_instructions_present(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SPEC_KIT_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="spec-kit", project_root_arg=str(tmp_path),
        ))

        assert "test" in result["agent_instructions"]
        assert "agent_instructions" in result


class TestImportOpenSpec:
    """ivd_import_spec against real OpenSpec delta-spec structure."""

    def test_parses_theme_selection_requirement(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(OPENSPEC_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="openspec", project_root_arg=str(tmp_path),
        ))

        assert result["ok"] is True
        assert len(result["requirements"]) == 1
        req = result["requirements"][0]
        assert req["name"] == "theme_selection"
        assert req["requirement"] == "The system SHALL allow users to choose between light and dark themes."
        assert len(req["scenarios"]) == 2

    def test_and_line_appends_to_preceding_then(self, tmp_path):
        """Regression test: '- AND ...' lines must fold into whichever of
        GIVEN/WHEN/THEN preceded them, not be silently dropped."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(OPENSPEC_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="openspec", project_root_arg=str(tmp_path),
        ))

        manual_toggle = result["requirements"][0]["scenarios"][0]
        assert manual_toggle["name"] == "manual_toggle"
        assert "theme switches immediately" in manual_toggle["then"]
        assert "persists across sessions" in manual_toggle["then"]

    def test_multiple_requirements_added_and_modified(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(OPENSPEC_2FA_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="openspec", project_root_arg=str(tmp_path),
        ))

        names = [r["name"] for r in result["requirements"]]
        assert names == ["two_factor_authentication", "session_timeout"]
        assert result["requirements"][0]["scenarios"][0]["then"] == "an OTP challenge is presented"


class TestImportSpecErrorPaths:
    """Error handling — must degrade gracefully, never raise."""

    def test_unsupported_format(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(OPENSPEC_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="jira", project_root_arg=str(tmp_path),
        ))

        assert result["ok"] is False
        assert "supported_formats" in result
        assert set(result["supported_formats"]) == {"spec-kit", "openspec"}

    def test_missing_file(self, tmp_path):
        result = json.loads(import_spec_tool(
            spec_path="does_not_exist.md", source_format="openspec", project_root_arg=str(tmp_path),
        ))

        assert result["ok"] is False
        assert "not found" in result["error"].lower()

    def test_missing_project_root(self):
        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="openspec", project_root_arg="/nonexistent/root/xyz",
        ))

        assert result["ok"] is False
        assert "error" in result

    def test_no_matching_structure_returns_warning_not_crash(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Just a title\n\nSome unrelated prose with no headers IVD recognizes.\n")

        result = json.loads(import_spec_tool(
            spec_path="spec.md", source_format="openspec", project_root_arg=str(tmp_path),
        ))

        assert result["ok"] is True
        assert result["requirements"] == []
        assert "warning" in result

    def test_absolute_spec_path(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(OPENSPEC_FIXTURE)

        result = json.loads(import_spec_tool(
            spec_path=str(spec_file), source_format="openspec", project_root_arg=str(tmp_path),
        ))

        assert result["ok"] is True
        assert len(result["requirements"]) == 1

    def test_default_project_root_is_ivd_framework_root(self):
        """No project_root_arg → resolves against the IVD repo itself, not a crash."""
        result = json.loads(import_spec_tool(
            spec_path="does_not_exist_anywhere.md", source_format="openspec",
        ))
        assert result["ok"] is False
        assert "not found" in result["error"].lower()
