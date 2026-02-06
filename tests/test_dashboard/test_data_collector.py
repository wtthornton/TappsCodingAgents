"""Tests for data_collector module — metrics gathering from subsystems."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.dashboard.data_collector import DashboardDataCollector


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal .tapps-agents directory structure."""
    tapps = tmp_path / ".tapps-agents"
    tapps.mkdir()
    (tapps / "analytics").mkdir()
    (tapps / "metrics").mkdir()
    (tapps / "events").mkdir()
    (tapps / "learning").mkdir()
    (tapps / "kb" / "context7-cache").mkdir(parents=True)
    return tmp_path


class TestCollectAll:
    def test_returns_required_keys(self, tmp_project):
        collector = DashboardDataCollector(tmp_project, days=7)
        data = collector.collect_all()
        assert "meta" in data
        assert "health" in data
        assert "agents" in data
        assert "experts" in data
        assert "cache" in data
        assert "quality" in data
        assert "workflows" in data
        assert "learning" in data
        assert "events" in data
        assert "recommendations" in data

    def test_meta_has_project_name(self, tmp_project):
        collector = DashboardDataCollector(tmp_project, days=30)
        data = collector.collect_all()
        assert data["meta"]["project_name"] == tmp_project.name
        assert data["meta"]["days"] == 30
        assert "generated_at" in data["meta"]

    def test_serializable(self, tmp_project):
        """The entire payload must be JSON-serializable."""
        collector = DashboardDataCollector(tmp_project, days=7)
        data = collector.collect_all()
        serialized = json.dumps(data, default=str)
        assert len(serialized) > 0


class TestCollectHealth:
    def test_defaults_on_missing_collector(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_health()
        assert "overall_score" in result
        assert "checks" in result

    @patch("tapps_agents.dashboard.data_collector.DashboardDataCollector.collect_health")
    def test_mocked_health(self, mock_health, tmp_project):
        mock_health.return_value = {
            "overall_score": 85,
            "checks": [{"name": "env", "status": "healthy", "score": 90, "details": {}, "remediation": []}],
            "trends": {},
        }
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_health()
        assert result["overall_score"] == 85
        assert len(result["checks"]) == 1


class TestCollectAgents:
    def test_defaults_on_empty(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_agents()
        assert result["summary"]["total"] == 14
        assert isinstance(result["agents"], list)


class TestCollectExperts:
    def test_defaults_on_empty(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_experts()
        assert "summary" in result
        assert "confidence_distribution" in result
        assert "roi" in result


class TestCollectCache:
    def test_defaults_on_empty(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_cache()
        assert result["summary"]["total_entries"] == 0
        assert isinstance(result["libraries"], list)


class TestCollectQuality:
    def test_defaults_on_empty(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_quality()
        assert "gate_pass_rate" in result
        assert "dimensions" in result


class TestCollectWorkflows:
    def test_defaults_on_empty(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_workflows()
        assert "summary" in result
        assert "workflows" in result
        assert "epics" in result


class TestCollectLearning:
    def test_defaults_on_empty(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_learning()
        assert isinstance(result["first_pass_trend"], list)
        assert isinstance(result["weight_adjustments"], list)

    def test_reads_performance_jsonl(self, tmp_project):
        learning_dir = tmp_project / ".tapps-agents" / "learning"
        perf_file = learning_dir / "expert_performance.jsonl"
        perf_file.write_text(
            json.dumps({"first_pass_success_rate": 0.85, "last_updated": "2026-01-01T00:00:00"}) + "\n",
            encoding="utf-8",
        )
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_learning()
        assert len(result["first_pass_trend"]) == 1
        assert result["first_pass_trend"][0]["rate"] == 0.85


class TestCollectEvents:
    def test_empty_events(self, tmp_project):
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_events()
        assert result == []

    def test_reads_event_files(self, tmp_project):
        events_dir = tmp_project / ".tapps-agents" / "events"
        event = {
            "timestamp": "2026-01-01T12:00:00",
            "event_type": "workflow_started",
            "workflow_id": "wf-1",
            "step_id": "",
            "status": "running",
            "data": {"preset": "standard"},
        }
        (events_dir / "wf-1-2026-01-01-started.json").write_text(
            json.dumps(event), encoding="utf-8"
        )
        collector = DashboardDataCollector(tmp_project)
        result = collector.collect_events()
        assert len(result) == 1
        assert result[0]["event_type"] == "workflow_started"
