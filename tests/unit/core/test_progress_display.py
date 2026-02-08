"""
Unit tests for phase-grid progress display (phase-grid wiring).
"""

import pytest

from tapps_agents.core.progress_display import (
    generate_status_report,
    phases_from_step_dicts,
)

pytestmark = pytest.mark.unit


class TestPhasesFromStepDicts:
    """Tests for phases_from_step_dicts helper."""

    def test_builds_phases_from_step_dicts(self):
        """Builds phase list with name, percentage, status, icon."""
        steps = [
            {"step_number": 1, "step_name": "Enhance", "success": True},
            {"step_number": 2, "step_name": "Plan", "success": True},
            {"step_number": 3, "step_name": "Implement", "success": False},
        ]
        phases = phases_from_step_dicts(
            steps,
            name_key="step_name",
            name_prefix="Phase",
            success_key="success",
            index_key="step_number",
        )
        assert len(phases) == 3
        assert phases[0]["name"] == "Phase 1: Enhance"
        assert phases[0]["percentage"] == 100.0
        assert phases[0]["status"] == "COMPLETE"
        assert phases[0]["icon"] == "\u2705"
        assert phases[2]["status"] == "FAILED"
        assert phases[2]["icon"] == "\u274c"

    def test_story_prefix(self):
        """Story prefix and story_id as label."""
        steps = [
            {"step_number": 1, "step_name": "RP-001", "success": True},
            {"step_number": 2, "step_name": "RP-002", "success": False},
        ]
        phases = phases_from_step_dicts(
            steps,
            name_key="step_name",
            name_prefix="Story",
            success_key="success",
            index_key="step_number",
        )
        assert phases[0]["name"] == "Story 1: RP-001"
        assert phases[1]["name"] == "Story 2: RP-002"

    def test_empty_steps(self):
        """Empty steps returns empty list."""
        assert phases_from_step_dicts([]) == []


class TestGenerateStatusReportWithPhases:
    """Tests that generate_status_report with phases produces phase-grid text."""

    def test_report_contains_total_line(self):
        """Report includes TOTAL line when show_total=True."""
        phases = [
            {"name": "Phase 1: A", "percentage": 100.0, "status": "COMPLETE", "icon": "\u2705"},
            {"name": "Phase 2: B", "percentage": 100.0, "status": "FAILED", "icon": "\u274c"},
        ]
        report = generate_status_report(phases, title="Progress Summary", use_unicode=True, show_total=True)
        assert "Progress Summary" in report
        assert "TOTAL:" in report
        assert "1/2" in report or "2/2" in report


class TestSimpleModeOutputAggregatorPhaseGrid:
    """Tests that Simple Mode markdown summary includes phase-grid when steps present."""

    def test_format_summary_includes_phase_grid(self):
        """format_summary(MARKDOWN) prepends phase-grid when steps exist."""
        from tapps_agents.core.output_formatter import OutputFormat
        from tapps_agents.simple_mode.output_aggregator import SimpleModeOutputAggregator

        agg = SimpleModeOutputAggregator(workflow_id="w1", workflow_type="build")
        agg.add_step_output(1, "Enhance", "enhancer", {}, success=True)
        agg.add_step_output(2, "Plan", "planner", {}, success=True)
        summary = agg.format_summary(format=OutputFormat.MARKDOWN)
        assert "Progress Summary" in summary
        assert "Phase 1: Enhance" in summary
        assert "Phase 2: Plan" in summary
        assert "TOTAL:" in summary
        assert "Workflow Summary" in summary
