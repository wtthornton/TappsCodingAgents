"""
Tests for Expert Suggester
"""

import pytest
from pathlib import Path

from tapps_agents.experts.adaptive_domain_detector import DomainSuggestion
from tapps_agents.experts.expert_suggester import ExpertSuggester


@pytest.fixture
def suggester(tmp_path):
    """Create suggester instance."""
    return ExpertSuggester(project_root=tmp_path)


@pytest.mark.asyncio
async def test_suggest_expert(suggester):
    """Test expert suggestion generation."""
    usage_context = {
        "confidence": 0.85,
        "frequency": 5,
        "source": "prompt",
    }
    
    suggestion = await suggester.suggest_expert(
        domain="oauth2-refresh-tokens",
        usage_context=usage_context,
        confidence_threshold=0.7,
    )
    
    assert suggestion is not None
    assert suggestion.expert_id.startswith("expert-")
    assert suggestion.primary_domain == "oauth2-refresh-tokens"
    assert suggestion.confidence >= 0.7
    assert len(suggestion.suggested_knowledge) > 0


@pytest.mark.asyncio
async def test_suggest_from_domain_detection(suggester):
    """Test suggestion from domain detection."""
    domain_suggestion = DomainSuggestion(
        domain="oauth2-refresh-tokens",
        confidence=0.85,
        source="prompt",
        priority="high",
        usage_frequency=5,
    )
    
    expert_suggestion = await suggester.suggest_from_domain_detection(domain_suggestion)
    
    assert expert_suggestion is not None
    assert expert_suggestion.expert_id == "expert-oauth2-refresh-tokens"
    assert expert_suggestion.primary_domain == "oauth2-refresh-tokens"


@pytest.mark.asyncio
async def test_expert_exists_check(suggester):
    """Test expert existence check."""
    # Should return False for non-existent expert
    exists = suggester._expert_exists("expert-nonexistent")
    assert exists is False
