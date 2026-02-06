"""Tests for html_renderer module — HTML generation from data dict."""

from tapps_agents.dashboard.html_renderer import HTMLRenderer


def _sample_data():
    """Minimal valid data dict for rendering."""
    return {
        "meta": {
            "project_name": "test-project",
            "generated_at": "2026-02-06T14:00:00Z",
            "days": 30,
            "tapps_agents_version": "3.6.3",
        },
        "health": {
            "overall_score": 82,
            "checks": [
                {"name": "environment", "status": "healthy", "score": 95, "details": {}, "remediation": []},
                {"name": "cache", "status": "degraded", "score": 55, "details": {"entries": 12}, "remediation": ["Run init"]},
            ],
            "trends": {},
        },
        "agents": {
            "summary": {"total": 14, "active": 5, "avg_success_rate": 90.0},
            "agents": [
                {"name": "implementer", "executions": 40, "success_rate": 95.0, "avg_duration_ms": 12000, "last_run": "2026-02-06T12:00:00", "trend": [30, 35, 38, 40]},
                {"name": "reviewer", "executions": 30, "success_rate": 88.0, "avg_duration_ms": 8000, "last_run": "2026-02-06T11:00:00", "trend": [20, 25, 28, 30]},
                {"name": "debugger", "executions": 5, "success_rate": 60.0, "avg_duration_ms": 20000, "last_run": "2026-02-05T08:00:00", "trend": [1, 3, 4, 5]},
                {"name": "documenter", "executions": 0, "success_rate": 0, "avg_duration_ms": 0, "last_run": "", "trend": []},
            ],
        },
        "experts": {
            "summary": {"total": 6, "active": 3, "avg_confidence": 0.78},
            "experts": [
                {"id": "expert-security", "consultations": 15, "avg_confidence": 0.85, "first_pass_rate": 90.0, "quality_impact": 2.5, "domains": ["security"]},
                {"id": "expert-perf", "consultations": 5, "avg_confidence": 0.45, "first_pass_rate": 60.0, "quality_impact": 0.5, "domains": ["performance"]},
            ],
            "confidence_distribution": {"low": 1, "medium": 0, "high": 2, "very_high": 1},
            "roi": {"time_saved_hours": 12.5, "bugs_prevented": 8, "roi_percentage": 340},
        },
        "cache": {
            "summary": {"total_entries": 25, "hit_rate": 72.0, "total_tokens": 50000, "total_size_bytes": 120000},
            "libraries": [
                {"name": "fastapi", "topics": 5, "hits": 20, "tokens": 15000, "size_bytes": 40000, "last_accessed": "2026-02-06T10:00:00"},
                {"name": "pydantic", "topics": 3, "hits": 0, "tokens": 8000, "size_bytes": 20000, "last_accessed": ""},
            ],
            "skill_usage": [],
            "rag_quality_score": 0.75,
        },
        "quality": {
            "gate_pass_rate": 78.0,
            "avg_score": 76.5,
            "dimensions": {"complexity": 80, "security": 85, "maintainability": 75, "test_coverage": 70, "performance": 65, "structure": 72, "devex": 68},
            "score_trend": [70, 72, 74, 76, 78],
            "recent_failures": [
                {"workflow": "wf-1", "step": "review", "skill": "reviewer", "date": "2026-02-05T09:00:00", "error": "Score below threshold"},
            ],
        },
        "workflows": {
            "summary": {"total": 50, "success_rate": 88.0, "avg_duration_ms": 15000},
            "workflows": [
                {"name": "standard", "executions": 30, "success_rate": 90.0, "avg_duration_ms": 12000, "avg_steps": 4, "last_run": "2026-02-06T13:00:00"},
            ],
            "preset_distribution": {"minimal": 5, "standard": 30, "comprehensive": 10, "full_sdlc": 5},
            "epics": [
                {"id": "epic-51", "title": "YAML Automation", "stories_total": 8, "stories_done": 5, "updated_at": "2026-02-06T12:00:00"},
            ],
        },
        "learning": {
            "first_pass_trend": [{"date": "2026-01-10", "rate": 0.7}, {"date": "2026-01-20", "rate": 0.78}, {"date": "2026-02-01", "rate": 0.85}],
            "auto_generated_experts": [],
            "weight_adjustments": [
                {"expert": "expert-security", "old_weight": 0.8, "new_weight": 0.85, "reason": "improved", "date": "2026-02-01"},
            ],
            "kb_growth": [],
        },
        "events": [
            {"timestamp": "2026-02-06T13:00:00", "event_type": "workflow_started", "workflow_id": "wf-50", "step_id": "", "status": "running", "details": "{}"},
            {"timestamp": "2026-02-06T13:05:00", "event_type": "workflow_completed", "workflow_id": "wf-50", "step_id": "", "status": "success", "details": "{}"},
        ],
        "recommendations": [
            {"tab": "agents", "message": "Agent debugger has a 60% success rate."},
            {"tab": "cache", "message": "1 library has 0 hits (pydantic). Consider removing."},
        ],
    }


class TestHTMLRenderer:
    def test_render_returns_html(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_title(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "test-project" in html

    def test_contains_all_tabs(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        for tab_id in ["tab-agents", "tab-experts", "tab-cache", "tab-quality", "tab-workflows", "tab-learning", "tab-health"]:
            assert f'id="{tab_id}"' in html, f"Missing tab: {tab_id}"

    def test_contains_agent_data(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "implementer" in html
        assert "reviewer" in html
        assert "debugger" in html

    def test_contains_expert_data(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "expert-security" in html
        assert "expert-perf" in html

    def test_contains_cache_data(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "fastapi" in html
        assert "pydantic" in html

    def test_contains_quality_dimensions(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        # Radar chart or dimension data should be present
        assert "complexity" in html.lower() or "Quality Dimensions" in html

    def test_contains_recommendations(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "60% success rate" in html
        assert "0 hits" in html

    def test_contains_events(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "workflow_started" in html
        assert "wf-50" in html

    def test_contains_embedded_json(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert 'id="dashboard-data"' in html
        assert "application/json" in html

    def test_contains_css(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "<style>" in html
        assert "#1a1a2e" in html  # dark theme background

    def test_contains_js(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "<script>" in html
        assert "data-sort" in html  # sortable tables

    def test_health_checks_rendered(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "environment" in html
        assert "healthy" in html
        assert "degraded" in html

    def test_epic_progress_rendered(self):
        renderer = HTMLRenderer()
        html = renderer.render(_sample_data())
        assert "YAML Automation" in html
        assert "5/8" in html

    def test_empty_data(self):
        """Should render without crashing even with empty data."""
        renderer = HTMLRenderer()
        empty = {
            "meta": {"project_name": "empty", "generated_at": "", "days": 30, "tapps_agents_version": "0.0.0"},
            "health": {"overall_score": 0, "checks": [], "trends": {}},
            "agents": {"summary": {"total": 14, "active": 0, "avg_success_rate": 0}, "agents": []},
            "experts": {"summary": {"total": 0, "active": 0, "avg_confidence": 0}, "experts": [], "confidence_distribution": {}, "roi": {}},
            "cache": {"summary": {"total_entries": 0, "hit_rate": 0, "total_tokens": 0, "total_size_bytes": 0}, "libraries": [], "skill_usage": [], "rag_quality_score": 0},
            "quality": {"gate_pass_rate": 0, "avg_score": 0, "dimensions": {}, "score_trend": [], "recent_failures": []},
            "workflows": {"summary": {"total": 0, "success_rate": 0, "avg_duration_ms": 0}, "workflows": [], "preset_distribution": {}, "epics": []},
            "learning": {"first_pass_trend": [], "auto_generated_experts": [], "weight_adjustments": [], "kb_growth": []},
            "events": [],
            "recommendations": [],
        }
        html = renderer.render(empty)
        assert "<!DOCTYPE html>" in html
