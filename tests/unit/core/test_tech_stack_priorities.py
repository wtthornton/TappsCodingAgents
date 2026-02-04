"""
Tests for tech stack priority mapping.

Tests priority mapping functions for framework-to-expert priorities.
"""

import pytest

from tapps_agents.core.tech_stack_priorities import (
    FRAMEWORK_PRIORITY_MAPPINGS,
    get_priorities_for_frameworks,
    get_priority_for_framework,
    get_supported_frameworks,
    normalize_framework_name,
)


@pytest.mark.unit
class TestGetPriorityForFramework:
    """Tests for get_priority_for_framework function."""

    def test_fastapi_priority_mapping(self):
        """Test FastAPI priority mapping returns correct priorities."""
        priorities = get_priority_for_framework("FastAPI")
        
        assert priorities["expert-api-design"] == 1.0
        assert priorities["expert-observability"] == 0.9
        assert priorities["expert-performance"] == 0.8
        assert "expert-api-design" in priorities

    def test_django_priority_mapping(self):
        """Test Django priority mapping returns correct priorities."""
        priorities = get_priority_for_framework("Django")
        
        assert priorities["expert-software-architecture"] == 1.0
        assert priorities["expert-database"] == 0.9
        assert priorities["expert-security"] == 0.8

    def test_react_priority_mapping(self):
        """Test React priority mapping returns correct priorities."""
        priorities = get_priority_for_framework("React")
        
        assert priorities["expert-user-experience"] == 1.0
        assert priorities["expert-software-architecture"] == 0.9
        assert priorities["expert-performance"] == 0.8

    def test_nextjs_priority_mapping(self):
        """Test Next.js priority mapping returns correct priorities."""
        priorities = get_priority_for_framework("Next.js")
        
        assert priorities["expert-software-architecture"] == 1.0
        assert priorities["expert-user-experience"] == 0.9
        assert priorities["expert-performance"] == 0.8

    def test_nestjs_priority_mapping(self):
        """Test NestJS priority mapping returns correct priorities."""
        priorities = get_priority_for_framework("NestJS")
        
        assert priorities["expert-api-design"] == 1.0
        assert priorities["expert-software-architecture"] == 0.9
        assert priorities["expert-observability"] == 0.8

    def test_case_insensitive_matching(self):
        """Test that framework matching is case-insensitive."""
        priorities_lower = get_priority_for_framework("fastapi")
        priorities_upper = get_priority_for_framework("FASTAPI")
        priorities_mixed = get_priority_for_framework("FastApi")
        priorities_exact = get_priority_for_framework("FastAPI")
        
        assert priorities_lower == priorities_exact
        assert priorities_upper == priorities_exact
        assert priorities_mixed == priorities_exact

    def test_unknown_framework_returns_empty(self):
        """Test that unknown framework returns empty dict."""
        priorities = get_priority_for_framework("UnknownFramework")
        
        assert priorities == {}

    def test_empty_framework_returns_empty(self):
        """Test that empty framework returns empty dict."""
        priorities = get_priority_for_framework("")
        
        assert priorities == {}

    def test_priority_values_in_valid_range(self):
        """Test that all priority values are between 0.0 and 1.0."""
        for framework in get_supported_frameworks():
            priorities = get_priority_for_framework(framework)
            for expert_id, priority in priorities.items():
                assert 0.0 <= priority <= 1.0, (
                    f"Priority {priority} for {expert_id} in {framework} "
                    f"is outside valid range [0.0, 1.0]"
                )

    def test_returns_copy_not_reference(self):
        """Test that function returns a copy, not a reference to internal data."""
        priorities1 = get_priority_for_framework("FastAPI")
        priorities2 = get_priority_for_framework("FastAPI")
        
        # Modify one, should not affect the other
        priorities1["test-expert"] = 0.5
        
        assert "test-expert" not in priorities2


@pytest.mark.unit
class TestGetPrioritiesForFrameworks:
    """Tests for get_priorities_for_frameworks function."""

    def test_single_framework(self):
        """Test that single framework returns same as get_priority_for_framework."""
        single = get_priority_for_framework("FastAPI")
        multiple = get_priorities_for_frameworks(["FastAPI"])
        
        assert single == multiple

    def test_multiple_frameworks_combines(self):
        """Test that multiple frameworks combine priorities correctly."""
        priorities = get_priorities_for_frameworks(["FastAPI", "React"])
        
        # Should include experts from both frameworks
        assert "expert-api-design" in priorities  # From FastAPI
        assert "expert-user-experience" in priorities  # From React

    def test_multiple_frameworks_takes_maximum(self):
        """Test that when expert appears in multiple frameworks, takes maximum priority."""
        # Create a test case - if an expert has different priorities in different frameworks
        fastapi_priorities = get_priority_for_framework("FastAPI")
        nestjs_priorities = get_priority_for_framework("NestJS")
        
        combined = get_priorities_for_frameworks(["FastAPI", "NestJS"])
        
        # expert-api-design should have 1.0 (max of both)
        if "expert-api-design" in fastapi_priorities and "expert-api-design" in nestjs_priorities:
            assert combined["expert-api-design"] == max(
                fastapi_priorities["expert-api-design"],
                nestjs_priorities["expert-api-design"]
            )

    def test_empty_list_returns_empty(self):
        """Test that empty framework list returns empty dict."""
        priorities = get_priorities_for_frameworks([])
        
        assert priorities == {}

    def test_unknown_frameworks_ignored(self):
        """Test that unknown frameworks in list are ignored."""
        priorities = get_priorities_for_frameworks(["FastAPI", "UnknownFramework"])
        
        # Should still have FastAPI priorities
        assert "expert-api-design" in priorities
        assert priorities["expert-api-design"] == 1.0


@pytest.mark.unit
class TestGetSupportedFrameworks:
    """Tests for get_supported_frameworks function."""

    def test_returns_all_frameworks(self):
        """Test that function returns all supported frameworks."""
        frameworks = get_supported_frameworks()
        
        assert "FastAPI" in frameworks
        assert "Django" in frameworks
        assert "React" in frameworks
        assert "Next.js" in frameworks
        assert "NestJS" in frameworks

    def test_returns_non_empty_list(self):
        """Test that function returns non-empty list."""
        frameworks = get_supported_frameworks()
        
        assert len(frameworks) > 0

    def test_frameworks_match_mappings_keys(self):
        """Test that returned frameworks match mapping keys exactly."""
        frameworks = get_supported_frameworks()
        
        assert set(frameworks) == set(FRAMEWORK_PRIORITY_MAPPINGS.keys())


@pytest.mark.unit
class TestNormalizeFrameworkName:
    """Tests for normalize_framework_name function."""

    def test_exact_match(self):
        """Test that exact match returns normalized name."""
        assert normalize_framework_name("FastAPI") == "FastAPI"
        assert normalize_framework_name("React") == "React"

    def test_case_insensitive_match(self):
        """Test that case-insensitive match works."""
        assert normalize_framework_name("fastapi") == "FastAPI"
        assert normalize_framework_name("REACT") == "React"
        assert normalize_framework_name("next.js") == "Next.js"

    def test_unknown_framework_returns_none(self):
        """Test that unknown framework returns None."""
        assert normalize_framework_name("UnknownFramework") is None
        assert normalize_framework_name("") is None

    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        assert normalize_framework_name("  FastAPI  ") == "FastAPI"
        assert normalize_framework_name("\tReact\n") == "React"

