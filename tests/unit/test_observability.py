"""
Tests for Observability & Quality Improvement Loop.
"""


import pytest

from tapps_agents.experts.observability import (
    ObservabilitySystem,
    WeakArea,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


def test_observability_system_initialization(temp_project):
    """Test Observability System initialization."""
    system = ObservabilitySystem(project_root=temp_project)
    assert system.project_root == temp_project
    assert system.metrics_dir.exists()


def test_record_consultation(temp_project):
    """Test recording consultation metrics."""
    system = ObservabilitySystem(project_root=temp_project)
    system.record_consultation(
        expert_id="expert-python",
        domain="python",
        confidence=0.85,
        agreement_level=0.9,
        rag_quality=0.75,
        threshold_met=True,
    )

    assert len(system.consultation_metrics) == 1
    assert system.consultation_metrics[0].expert_id == "expert-python"
    assert system.consultation_metrics[0].confidence == 0.85


def test_record_context7_metrics(temp_project):
    """Test recording Context7 metrics."""
    system = ObservabilitySystem(project_root=temp_project)
    system.record_context7_metrics(
        hit_rate=0.85,
        latency_ms=150.0,
        total_requests=100,
        cache_hits=85,
        cache_misses=15,
    )

    assert len(system.context7_metrics) == 1
    assert system.context7_metrics[0].hit_rate == 0.85
    assert system.context7_metrics[0].latency_ms == 150.0


def test_record_rag_metrics(temp_project):
    """Test recording RAG metrics."""
    system = ObservabilitySystem(project_root=temp_project)
    system.record_rag_metrics(
        retrieval_hit_rate=0.80,
        low_quality_queries=[{"query": "test", "quality": 0.3}],
        total_queries=100,
        successful_retrievals=80,
    )

    assert len(system.rag_metrics) == 1
    assert system.rag_metrics[0].retrieval_hit_rate == 0.80


def test_identify_weak_areas(temp_project):
    """Test weak area identification."""
    system = ObservabilitySystem(project_root=temp_project)

    # Add low-quality metrics
    for _i in range(5):
        system.record_consultation(
            expert_id="expert-python",
            domain="python",
            confidence=0.5,
            rag_quality=0.3,  # Low quality
        )

    weak_areas = system.identify_weak_areas(threshold=0.5)
    assert len(weak_areas) > 0
    assert weak_areas[0].domain == "python"
    assert weak_areas[0].rag_quality < 0.5


def test_generate_improvement_proposals(temp_project):
    """Test improvement proposal generation."""
    system = ObservabilitySystem(project_root=temp_project)

    weak_area = WeakArea(
        domain="python",
        rag_quality=0.3,
        low_quality_queries=["query1", "query2"],
        priority="high",
    )

    proposals = system.generate_improvement_proposals([weak_area])
    assert len(proposals) == 1
    assert proposals[0].domain == "python"
    assert proposals[0].priority == "high"
    assert "template" in proposals[0].template.lower()


def test_run_maintenance_job(temp_project):
    """Test maintenance job execution."""
    system = ObservabilitySystem(project_root=temp_project)

    # Add some metrics
    system.record_consultation(
        expert_id="expert-python",
        domain="python",
        confidence=0.5,
        rag_quality=0.3,
    )

    results = system.run_maintenance_job()
    assert "timestamp" in results
    assert "weak_areas_identified" in results
    assert "proposals_generated" in results

    # Check that files were created
    proposals_file = temp_project / ".tapps-agents" / "metrics" / "improvement_proposals.json"
    assert proposals_file.exists()

    weak_areas_file = temp_project / ".tapps-agents" / "metrics" / "weak_areas.json"
    assert weak_areas_file.exists()


def test_get_metrics_summary(temp_project):
    """Test metrics summary generation."""
    system = ObservabilitySystem(project_root=temp_project)

    # Add metrics
    system.record_consultation(
        expert_id="expert-python",
        domain="python",
        confidence=0.8,
        rag_quality=0.7,
    )
    system.record_context7_metrics(hit_rate=0.85, latency_ms=150.0, total_requests=100, cache_hits=85, cache_misses=15)
    system.record_rag_metrics(
        retrieval_hit_rate=0.80,
        low_quality_queries=[],
        total_queries=100,
        successful_retrievals=80,
    )

    summary = system.get_metrics_summary()
    assert "consultation_metrics" in summary
    assert "context7_metrics" in summary
    assert "rag_metrics" in summary
    assert summary["consultation_metrics"]["total_consultations"] == 1

