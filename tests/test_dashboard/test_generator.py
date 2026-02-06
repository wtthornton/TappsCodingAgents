"""Tests for generator module — orchestration and recommendations engine."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.dashboard.generator import DashboardGenerator, _generate_recommendations


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal .tapps-agents directory."""
    tapps = tmp_path / ".tapps-agents"
    tapps.mkdir()
    (tapps / "analytics").mkdir()
    (tapps / "metrics").mkdir()
    (tapps / "events").mkdir()
    (tapps / "learning").mkdir()
    (tapps / "kb" / "context7-cache").mkdir(parents=True)
    return tmp_path


class TestDashboardGenerator:
    def test_generate_creates_file(self, tmp_project):
        gen = DashboardGenerator(project_root=tmp_project)
        output = gen.generate(open_browser=False)
        assert output.exists()
        assert output.name == "dashboard.html"

    def test_generate_custom_output(self, tmp_project):
        out = tmp_project / "custom" / "report.html"
        gen = DashboardGenerator(project_root=tmp_project)
        result = gen.generate(output_path=out, open_browser=False)
        assert result == out.resolve()
        assert result.exists()

    def test_generate_custom_days(self, tmp_project):
        gen = DashboardGenerator(project_root=tmp_project)
        output = gen.generate(days=7, open_browser=False)
        content = output.read_text(encoding="utf-8")
        # Verify the embedded JSON has days=7
        assert '"days": 7' in content

    def test_output_is_valid_html(self, tmp_project):
        gen = DashboardGenerator(project_root=tmp_project)
        output = gen.generate(open_browser=False)
        content = output.read_text(encoding="utf-8")
        assert content.startswith("<!DOCTYPE html>")
        assert "</html>" in content

    def test_output_contains_embedded_json(self, tmp_project):
        gen = DashboardGenerator(project_root=tmp_project)
        output = gen.generate(open_browser=False)
        content = output.read_text(encoding="utf-8")
        assert 'id="dashboard-data"' in content

    def test_verbose_mode(self, tmp_project):
        gen = DashboardGenerator(project_root=tmp_project)
        output = gen.generate(verbose=True, open_browser=False)
        assert output.exists()

    def test_output_under_500kb(self, tmp_project):
        gen = DashboardGenerator(project_root=tmp_project)
        output = gen.generate(open_browser=False)
        size_kb = output.stat().st_size / 1024
        assert size_kb < 500, f"Dashboard is {size_kb:.0f}KB, should be < 500KB"


class TestRecommendationsEngine:
    def test_low_agent_success_rate(self):
        data = {
            "agents": {"agents": [{"name": "debugger", "executions": 10, "success_rate": 60}]},
            "experts": {"summary": {"active": 1}, "experts": []},
            "cache": {"summary": {"hit_rate": 80}, "libraries": []},
            "quality": {"gate_pass_rate": 80},
            "workflows": {"summary": {"success_rate": 90}},
            "health": {"checks": []},
        }
        recs = _generate_recommendations(data)
        assert any("debugger" in r["message"] and "60%" in r["message"] for r in recs)

    def test_unused_agents(self):
        data = {
            "agents": {"agents": [
                {"name": "ops", "executions": 0, "success_rate": 0},
                {"name": "documenter", "executions": 0, "success_rate": 0},
            ]},
            "experts": {"summary": {"active": 1}, "experts": []},
            "cache": {"summary": {"hit_rate": 80}, "libraries": []},
            "quality": {"gate_pass_rate": 80},
            "workflows": {"summary": {"success_rate": 90}},
            "health": {"checks": []},
        }
        recs = _generate_recommendations(data)
        assert any("never been used" in r["message"] for r in recs)

    def test_low_expert_confidence(self):
        data = {
            "agents": {"agents": []},
            "experts": {
                "summary": {"active": 1},
                "experts": [{"id": "expert-perf", "consultations": 5, "avg_confidence": 0.4}],
            },
            "cache": {"summary": {"hit_rate": 80}, "libraries": []},
            "quality": {"gate_pass_rate": 80},
            "workflows": {"summary": {"success_rate": 90}},
            "health": {"checks": []},
        }
        recs = _generate_recommendations(data)
        assert any("expert-perf" in r["message"] and "low confidence" in r["message"] for r in recs)

    def test_low_cache_hit_rate(self):
        data = {
            "agents": {"agents": []},
            "experts": {"summary": {"active": 1}, "experts": []},
            "cache": {"summary": {"hit_rate": 30}, "libraries": []},
            "quality": {"gate_pass_rate": 80},
            "workflows": {"summary": {"success_rate": 90}},
            "health": {"checks": []},
        }
        recs = _generate_recommendations(data)
        assert any("Cache hit rate" in r["message"] for r in recs)

    def test_zero_hit_libraries(self):
        data = {
            "agents": {"agents": []},
            "experts": {"summary": {"active": 1}, "experts": []},
            "cache": {
                "summary": {"hit_rate": 80},
                "libraries": [{"name": "unused-lib", "hits": 0}],
            },
            "quality": {"gate_pass_rate": 80},
            "workflows": {"summary": {"success_rate": 90}},
            "health": {"checks": []},
        }
        recs = _generate_recommendations(data)
        assert any("0 hits" in r["message"] for r in recs)

    def test_degraded_health(self):
        data = {
            "agents": {"agents": []},
            "experts": {"summary": {"active": 1}, "experts": []},
            "cache": {"summary": {"hit_rate": 80}, "libraries": []},
            "quality": {"gate_pass_rate": 80},
            "workflows": {"summary": {"success_rate": 90}},
            "health": {"checks": [{"name": "cache", "status": "degraded", "score": 55, "remediation": ["Run init"]}]},
        }
        recs = _generate_recommendations(data)
        assert any("cache" in r["message"] and "degraded" in r["message"] for r in recs)

    def test_no_recs_for_healthy_project(self):
        data = {
            "agents": {"agents": [{"name": "implementer", "executions": 20, "success_rate": 95}]},
            "experts": {"summary": {"active": 3}, "experts": [{"id": "e1", "consultations": 10, "avg_confidence": 0.9}]},
            "cache": {"summary": {"hit_rate": 85}, "libraries": [{"name": "lib", "hits": 5}]},
            "quality": {"gate_pass_rate": 90},
            "workflows": {"summary": {"success_rate": 92}},
            "health": {"checks": [{"name": "env", "status": "healthy", "score": 95}]},
        }
        recs = _generate_recommendations(data)
        assert len(recs) == 0


class TestCLIIntegration:
    def test_parser_registered(self):
        """Verify the dashboard parser is registered in the CLI."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers

        parser = create_root_parser()
        register_all_parsers(parser)
        # Should parse without error
        args = parser.parse_args(["dashboard", "--no-open", "--days", "7"])
        assert args.agent == "dashboard"
        assert args.no_open is True
        assert args.days == 7
