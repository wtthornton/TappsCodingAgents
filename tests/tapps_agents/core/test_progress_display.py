"""Tests for progress_display module (phase-grid format)."""

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.core.progress_display import (
    create_progress_bar,
    create_status_line,
    generate_status_report,
)


class TestCreateProgressBar:
    """Tests for create_progress_bar."""

    def test_zero_unicode(self):
        assert create_progress_bar(0, width=10, use_unicode=True) == "[          ]"

    def test_half_unicode(self):
        assert create_progress_bar(50, width=10, use_unicode=True) == "[█████     ]"

    def test_full_unicode(self):
        assert create_progress_bar(100, width=10, use_unicode=True) == "[██████████]"

    def test_zero_ascii(self):
        assert create_progress_bar(0, width=10, use_unicode=False) == "[          ]"

    def test_half_ascii(self):
        assert create_progress_bar(50, width=10, use_unicode=False) == "[#####     ]"

    def test_full_ascii(self):
        assert create_progress_bar(100, width=10, use_unicode=False) == "[##########]"

    def test_clamps_over_100(self):
        assert create_progress_bar(150, width=10, use_unicode=True) == "[██████████]"

    def test_clamps_under_zero(self):
        assert create_progress_bar(-10, width=10, use_unicode=True) == "[          ]"

    def test_custom_width(self):
        assert create_progress_bar(50, width=4, use_unicode=True) == "[██  ]"


class TestCreateStatusLine:
    """Tests for create_status_line."""

    def test_alignment_unicode(self):
        line = create_status_line(
            "Phase 0: Prep",
            100,
            "COMPLETE",
            "\u2705",
            use_unicode=True,
            name_width=20,
        )
        assert line.startswith("Phase 0: Prep        ")
        assert "[██████████]" in line
        assert "100%" in line
        assert "COMPLETE" in line

    def test_alignment_ascii(self):
        line = create_status_line(
            "Phase 1: Build",
            50,
            "IN PROGRESS",
            "\u27a1\ufe0f",
            use_unicode=False,
            name_width=20,
        )
        assert line.startswith("Phase 1: Build       ")
        assert "[#####     ]" in line
        assert " 50%" in line
        assert "IN PROGRESS" in line


class TestGenerateStatusReport:
    """Tests for generate_status_report."""

    def test_empty_phases(self):
        out = generate_status_report([], show_total=False)
        assert out.strip() == "Progress Summary"

    def test_single_phase_no_sub_items(self):
        phases = [
            {"name": "Phase 0: Prep", "percentage": 100, "status": "COMPLETE", "icon": "\u2705"},
        ]
        out = generate_status_report(phases, use_unicode=True, show_total=True)
        assert "Progress Summary" in out
        assert "Phase 0: Prep" in out
        assert "100%" in out
        assert "COMPLETE" in out
        assert "TOTAL: 100.0% complete (1/1 phases)" in out

    def test_multiple_phases_with_sub_items(self):
        phases = [
            {
                "name": "Phase 0: Prep",
                "percentage": 100,
                "status": "COMPLETE",
                "icon": "\u2705",
                "sub_items": ["Duration: 2m"],
            },
            {
                "name": "Phase 1: Build",
                "percentage": 0,
                "status": "PENDING",
                "icon": "\u23f3",
            },
        ]
        out = generate_status_report(phases, use_unicode=True, show_total=True)
        assert "Phase 0: Prep" in out
        assert "Phase 1: Build" in out
        assert "TOTAL: 50.0% complete (1/2 phases)" in out
        assert "\u2514" in out or "Duration" in out

    def test_ascii_mode_sub_items_use_dash_prefix(self):
        phases = [
            {
                "name": "Phase 0: Test",
                "percentage": 100,
                "status": "COMPLETE",
                "icon": "\u2705",
                "sub_items": ["Tests: 5/5"],
            },
        ]
        out = generate_status_report(phases, use_unicode=False, show_total=True)
        assert "  - Tests: 5/5" in out
        assert "[##########]" in out
