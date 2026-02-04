"""
Tests for domain-to-directory name mapping.
"""

import pytest

from tapps_agents.experts.domain_utils import (
    DOMAIN_TO_DIRECTORY_MAP,
    sanitize_domain_for_path,
)

pytestmark = pytest.mark.unit


class TestDomainMapping:
    """Test domain-to-directory name mapping."""

    def test_performance_optimization_mapping(self):
        """Test performance-optimization maps to performance."""
        domain = "performance-optimization"
        result = sanitize_domain_for_path(domain)

        assert result == "performance"

    def test_ai_agent_framework_mapping(self):
        """Test ai-agent-framework maps to ai-frameworks."""
        domain = "ai-agent-framework"
        result = sanitize_domain_for_path(domain)

        assert result == "ai-frameworks"

    def test_testing_strategies_mapping(self):
        """Test testing-strategies maps to testing."""
        domain = "testing-strategies"
        result = sanitize_domain_for_path(domain)

        assert result == "testing"

    def test_standard_domain_no_mapping(self):
        """Test that standard domains don't use mapping."""
        domain = "security"
        result = sanitize_domain_for_path(domain)

        assert result == "security"

    def test_url_domain_handling(self):
        """Test URL domain handling."""
        url_domain = "https://example.com/docs"
        result = sanitize_domain_for_path(url_domain)

        # Should extract hostname and path
        assert "example.com" in result
        assert "docs" in result

    def test_special_characters_handling(self):
        """Test special character handling."""
        domain = "domain with spaces & special/chars"
        result = sanitize_domain_for_path(domain)

        # Should replace special chars with hyphens
        assert " " not in result
        assert "/" not in result
        assert "&" not in result

    def test_empty_domain(self):
        """Test empty domain handling."""
        result = sanitize_domain_for_path("")

        assert result == "unknown"

    def test_mapping_dictionary(self):
        """Test that mapping dictionary is defined."""
        assert isinstance(DOMAIN_TO_DIRECTORY_MAP, dict)
        assert "performance-optimization" in DOMAIN_TO_DIRECTORY_MAP
        assert "ai-agent-framework" in DOMAIN_TO_DIRECTORY_MAP
        assert "testing-strategies" in DOMAIN_TO_DIRECTORY_MAP
