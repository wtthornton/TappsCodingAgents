"""
Tests for Adaptive Domain Detector
"""

import pytest
from pathlib import Path

from tapps_agents.experts.adaptive_domain_detector import (
    AdaptiveDomainDetector,
    DomainSuggestion,
)


@pytest.fixture
def detector(tmp_path):
    """Create detector instance."""
    return AdaptiveDomainDetector(project_root=tmp_path)


@pytest.mark.asyncio
async def test_detect_from_prompt(detector):
    """Test domain detection from prompt."""
    prompt = "Create an OAuth2 refresh token client for Zoho API"
    suggestions = await detector.detect_domains(prompt=prompt)
    
    assert len(suggestions) > 0
    oauth2_suggestion = next(
        (s for s in suggestions if "oauth2" in s.domain.lower()), None
    )
    assert oauth2_suggestion is not None
    assert oauth2_suggestion.confidence > 0.5
    assert oauth2_suggestion.source == "prompt"


@pytest.mark.asyncio
async def test_detect_from_code_patterns(detector):
    """Test domain detection from code patterns."""
    code = """
class OAuth2Client:
    def __init__(self, refresh_token, token_url):
        self.refresh_token = refresh_token
        self.token_url = token_url
    
    def _refresh_access_token(self):
        resp = requests.post(self.token_url, data={"refresh_token": self.refresh_token})
        return resp.json()["access_token"]
"""
    suggestions = await detector.detect_domains(code_context=code)
    
    assert len(suggestions) > 0
    api_client_suggestion = next(
        (s for s in suggestions if "api" in s.domain.lower() or "oauth" in s.domain.lower()), None
    )
    assert api_client_suggestion is not None


@pytest.mark.asyncio
async def test_detect_from_consultation_gaps(detector):
    """Test domain detection from consultation gaps."""
    consultation_history = [
        {
            "domain": "api-design-integration",
            "confidence": 0.5,  # Low confidence
            "query": "How to implement OAuth2 refresh token flow?",
        }
    ]
    suggestions = await detector.detect_domains(consultation_history=consultation_history)
    
    # Should detect gap and suggest domain
    assert len(suggestions) > 0


@pytest.mark.asyncio
async def test_recurring_patterns(detector):
    """Test recurring pattern detection."""
    history = [
        DomainSuggestion(
            domain="oauth2-refresh-tokens",
            confidence=0.7,
            source="prompt",
            priority="high",
        ),
        DomainSuggestion(
            domain="oauth2-refresh-tokens",
            confidence=0.8,
            source="code_pattern",
            priority="high",
        ),
        DomainSuggestion(
            domain="oauth2-refresh-tokens",
            confidence=0.75,
            source="prompt",
            priority="high",
        ),
    ]
    
    recurring = await detector.detect_recurring_patterns(history)
    assert len(recurring) > 0
    assert any(s.domain == "oauth2-refresh-tokens" for s in recurring)
