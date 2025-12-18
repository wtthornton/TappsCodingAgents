"""
Tests for Expert Engine runtime component.
"""

import pytest

from tapps_agents.experts.expert_engine import (
    ExpertEngine,
    KnowledgeNeed,
    ExpertRoutingPlan,
)
from tapps_agents.experts.expert_registry import ExpertRegistry


@pytest.fixture
def expert_registry(tmp_path):
    """Create a test expert registry."""
    return ExpertRegistry(project_root=tmp_path, load_builtin=False)


@pytest.fixture
def expert_engine(expert_registry):
    """Create a test expert engine."""
    return ExpertEngine(expert_registry=expert_registry, enable_metrics=True)


def test_expert_engine_initialization(expert_engine):
    """Test Expert Engine initialization."""
    assert expert_engine.expert_registry is not None
    assert expert_engine.enable_metrics is True
    assert expert_engine.metrics.knowledge_needs_detected == 0


def test_detect_knowledge_need_with_query(expert_engine):
    """Test knowledge need detection with explicit query."""
    need = expert_engine.detect_knowledge_need(
        query="How to implement authentication?",
        domain="security",
    )
    assert need is not None
    assert need.query == "How to implement authentication?"
    assert need.domain == "security"
    assert need.priority == "normal"


def test_detect_knowledge_need_with_step_context(expert_engine):
    """Test knowledge need detection from step context."""
    step_context = {
        "agent": "architect",
        "action": "design_system",
        "notes": "Design authentication system",
        "consults": ["expert-security"],
    }
    need = expert_engine.detect_knowledge_need(step_context=step_context)
    assert need is not None
    assert "architect" in need.query
    assert "design_system" in need.query
    assert need.domain == "security"


def test_detect_knowledge_need_no_context(expert_engine):
    """Test knowledge need detection with no context returns None."""
    need = expert_engine.detect_knowledge_need()
    assert need is None


def test_generate_routing_plan(expert_engine):
    """Test expert routing plan generation."""
    knowledge_need = KnowledgeNeed(
        domain="security",
        query="How to implement authentication?",
    )
    plan = expert_engine.generate_routing_plan(knowledge_need)
    assert plan is not None
    assert plan.knowledge_need == knowledge_need
    assert isinstance(plan.expert_ids, list)
    assert plan.domains == ["security"]
    assert plan.reasoning != ""


def test_generate_retrieval_plan(expert_engine):
    """Test knowledge retrieval plan generation."""
    knowledge_need = KnowledgeNeed(
        domain="security",
        query="How to implement authentication?",
    )
    plan = expert_engine.generate_retrieval_plan(knowledge_need)
    assert plan is not None
    assert plan.knowledge_need == knowledge_need
    assert isinstance(plan.context7_sources, list)
    assert isinstance(plan.local_kb_sources, list)
    assert plan.retrieval_strategy in ["context7_only", "local_only", "hybrid"]


@pytest.mark.asyncio
async def test_consult_with_plan_no_experts(expert_engine):
    """Test consultation with plan when no experts are registered."""
    knowledge_need = KnowledgeNeed(
        domain="security",
        query="How to implement authentication?",
    )
    routing_plan = ExpertRoutingPlan(
        knowledge_need=knowledge_need,
        expert_ids=["expert-security"],
        domains=["security"],
    )
    # Should raise error since no experts are registered
    with pytest.raises(ValueError):
        await expert_engine.consult_with_plan(routing_plan)


def test_write_knowledge_validation(expert_engine):
    """Test knowledge write with validation."""
    from tapps_agents.experts.expert_engine import KnowledgeWriteRequest

    # Test with potential secret
    write_request = KnowledgeWriteRequest(
        domain="security",
        content="API key: sk-1234567890",
        source="test",
    )
    result = expert_engine.write_knowledge(write_request, validate=True)
    assert result["success"] is False
    assert "secret" in result["error"].lower()

    # Test with valid content
    write_request = KnowledgeWriteRequest(
        domain="security",
        content="Authentication best practices: Use OAuth2 for API access.",
        source="test",
        validated=True,
    )
    result = expert_engine.write_knowledge(write_request, validate=True)
    assert result["success"] is True


def test_get_metrics(expert_engine):
    """Test metrics retrieval."""
    metrics = expert_engine.get_metrics()
    assert metrics is not None
    assert metrics.knowledge_needs_detected == 0
    assert metrics.expert_consultations == 0
    assert metrics.knowledge_writes == 0

    # Trigger some activity
    expert_engine.detect_knowledge_need(query="test", domain="test")
    metrics = expert_engine.get_metrics()
    assert metrics.knowledge_needs_detected == 1

