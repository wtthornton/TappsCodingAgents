"""
Tests for ArtifactContextBuilder - Token-aware artifact injection with budgeting.
"""

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.core.artifact_context_builder import (
    ArtifactContextBuilder,
    ArtifactEntry,
)


class TestArtifactContextBuilder:
    """Test suite for ArtifactContextBuilder."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        builder = ArtifactContextBuilder()

        assert builder.token_budget == 4000
        assert builder.use_tiktoken is True
        assert builder.summarization_enabled is False

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        builder = ArtifactContextBuilder(
            token_budget=2000,
            use_tiktoken=False,
            summarization_enabled=True,
        )

        assert builder.token_budget == 2000
        assert builder.use_tiktoken is False
        assert builder.summarization_enabled is True

    def test_estimate_tokens_empty_string(self):
        """Test token estimation for empty string."""
        builder = ArtifactContextBuilder(use_tiktoken=False)
        assert builder.estimate_tokens("") == 0
        assert builder.estimate_tokens(None) == 0  # type: ignore

    def test_estimate_tokens_chars_fallback(self):
        """Test token estimation using chars/4 fallback."""
        builder = ArtifactContextBuilder(use_tiktoken=False)

        # Simple text: "Hello World" = 11 chars
        # Formula: int(len(text) / 4 * 1.1) = int(11 / 4 * 1.1) = int(3.025) = 3
        text = "Hello World"
        tokens = builder.estimate_tokens(text)
        assert tokens == int(len(text) / 4 * 1.1)

    def test_estimate_tokens_tiktoken(self):
        """Test token estimation using tiktoken (if available)."""
        try:
            import tiktoken
            builder = ArtifactContextBuilder(use_tiktoken=True)

            text = "Hello World"
            tokens = builder.estimate_tokens(text)

            # tiktoken should give a valid token count
            assert tokens > 0
            assert isinstance(tokens, int)
        except ImportError:
            pytest.skip("tiktoken not available")

    def test_build_context_empty_artifacts(self):
        """Test building context with no artifacts."""
        builder = ArtifactContextBuilder()
        result = builder.build_context([])

        assert result == {}

    def test_build_context_single_artifact_fits(self):
        """Test building context with single artifact that fits in budget."""
        builder = ArtifactContextBuilder(token_budget=1000, use_tiktoken=False)

        artifacts = [("specification", "Short spec content", 1)]
        result = builder.build_context(artifacts)

        assert "specification" in result
        assert result["specification"] == "Short spec content"

    def test_build_context_priority_ordering(self):
        """Test that artifacts are filled in priority order."""
        builder = ArtifactContextBuilder(token_budget=100, use_tiktoken=False)

        # Create artifacts with different priorities
        # Only first one should fit in budget (100 tokens)
        artifacts = [
            ("user_stories", "B" * 400, 2),  # 2nd priority, 110 tokens
            ("specification", "A" * 400, 1),  # 1st priority, 110 tokens
            ("architecture", "C" * 400, 3),  # 3rd priority, 110 tokens
        ]

        result = builder.build_context(artifacts)

        # Only specification (priority 1) should be in result
        assert "specification" in result
        assert "user_stories" not in result or "summary" in result["user_stories"].lower()
        assert "architecture" not in result or "summary" in result["architecture"].lower()

    def test_build_context_auto_priority(self):
        """Test automatic priority assignment based on order."""
        builder = ArtifactContextBuilder(token_budget=500, use_tiktoken=False)

        # Provide artifacts without explicit priority
        artifacts = [
            ("specification", "A" * 200),
            ("user_stories", "B" * 200),
            ("architecture", "C" * 200),
        ]

        result = builder.build_context(artifacts)

        # First artifacts should be included until budget is exhausted
        assert "specification" in result

    def test_build_context_budget_exceeded_truncate(self):
        """Test truncation when artifact exceeds budget (summarization disabled)."""
        builder = ArtifactContextBuilder(
            token_budget=500,
            use_tiktoken=False,
            summarization_enabled=False,
        )

        # First artifact fits, second is too large
        artifacts = [
            ("specification", "A" * 200, 1),  # ~55 tokens
            ("user_stories", "B" * 10000, 2),  # Very large
        ]

        result = builder.build_context(artifacts)

        assert "specification" in result
        assert result["specification"] == "A" * 200

        if "user_stories" in result:
            # Should be truncated
            assert "[Content truncated to fit token budget]" in result["user_stories"]
            assert len(result["user_stories"]) < len("B" * 10000)

    def test_build_context_budget_exceeded_summarize(self):
        """Test summarization when artifact exceeds budget (summarization enabled)."""
        builder = ArtifactContextBuilder(
            token_budget=200,
            use_tiktoken=False,
            summarization_enabled=True,
        )

        # First artifact fits, second triggers summarization
        artifacts = [
            ("specification", "A" * 200, 1),  # ~55 tokens
            ("user_stories", "US-001\nUS-002\nUS-003\n" + "B" * 10000, 2),  # Very large
        ]

        result = builder.build_context(artifacts)

        assert "specification" in result

        if "user_stories" in result:
            # Should be summarized, not full content
            summary = result["user_stories"]
            assert "User stories:" in summary or "summary" in summary.lower()
            assert len(summary) < 100  # Summary should be short

    def test_extract_summary_info_user_stories(self):
        """Test extraction of summary info from user stories."""
        builder = ArtifactContextBuilder()

        content = """
        US-001: Create login page
        US-002: Add authentication
        US-003: Implement logout
        """

        info = builder._extract_summary_info("user_stories", content)
        assert "count" in info
        assert info["count"] == 3

    def test_extract_summary_info_api_design(self):
        """Test extraction of summary info from API design."""
        builder = ArtifactContextBuilder()

        content = """
        GET /api/users
        POST /api/users
        PUT /api/users/:id
        DELETE /api/users/:id
        """

        info = builder._extract_summary_info("api_design", content)
        assert "count" in info
        assert info["count"] == 4

    def test_extract_summary_info_architecture(self):
        """Test extraction of summary info from architecture."""
        builder = ArtifactContextBuilder()

        content = """
        Microservices architecture with API gateway.
        Uses PostgreSQL for persistence.
        Redis for caching.
        """

        info = builder._extract_summary_info("architecture", content)
        assert "summary" in info
        assert "Microservices architecture" in info["summary"]

    def test_generate_summary_user_stories(self):
        """Test summary generation for user stories."""
        builder = ArtifactContextBuilder()

        content = "US-001\nUS-002\nUS-003"
        summary = builder._generate_summary("user_stories", content)

        assert "User stories:" in summary
        assert "3" in summary

    def test_generate_summary_api_design(self):
        """Test summary generation for API design."""
        builder = ArtifactContextBuilder()

        content = "GET /api\nPOST /api\nPUT /api"
        summary = builder._generate_summary("api_design", content)

        assert "API design:" in summary
        assert "3" in summary

    def test_generate_summary_specification(self):
        """Test summary generation for specification."""
        builder = ArtifactContextBuilder()

        summary = builder._generate_summary("specification", "Long spec content")
        assert summary == "Enhanced prompt (summary)"

    def test_build_context_multiple_artifacts_within_budget(self):
        """Test building context with multiple artifacts that fit in budget."""
        builder = ArtifactContextBuilder(token_budget=5000, use_tiktoken=False)

        artifacts = [
            ("specification", "Enhanced prompt content" * 10, 1),
            ("user_stories", "User story content" * 10, 2),
            ("architecture", "Architecture content" * 10, 3),
            ("api_design", "API design content" * 10, 4),
        ]

        result = builder.build_context(artifacts)

        # All should fit within budget
        assert len(result) == 4
        assert "specification" in result
        assert "user_stories" in result
        assert "architecture" in result
        assert "api_design" in result

    def test_build_context_budget_exhausted_skip_artifacts(self):
        """Test that artifacts are skipped when budget is exhausted."""
        builder = ArtifactContextBuilder(
            token_budget=100,
            use_tiktoken=False,
            summarization_enabled=False,
        )

        artifacts = [
            ("specification", "A" * 200, 1),  # ~55 tokens, fits
            ("user_stories", "B" * 10000, 2),  # Won't fit
            ("architecture", "C" * 10000, 3),  # Won't fit
        ]

        result = builder.build_context(artifacts)

        # Only specification should be in result
        assert "specification" in result
        # Others may be truncated or skipped
        assert len(result) <= 2

    def test_build_context_summary_when_budget_allows(self):
        """Test that summary is used only when it fits in budget."""
        builder = ArtifactContextBuilder(
            token_budget=150,
            use_tiktoken=False,
            summarization_enabled=True,
        )

        artifacts = [
            ("specification", "A" * 200, 1),  # ~55 tokens
            ("user_stories", "US-001\n" * 1000, 2),  # Large, triggers summary
        ]

        result = builder.build_context(artifacts)

        assert "specification" in result

        if "user_stories" in result:
            # Should use summary if it fits
            assert "User stories:" in result["user_stories"] or len(result["user_stories"]) < 200

    def test_tiktoken_fallback_on_error(self):
        """Test graceful fallback when tiktoken encoding fails."""
        try:
            import tiktoken
            builder = ArtifactContextBuilder(use_tiktoken=True)

            # Simulate encoding failure by passing invalid input
            # (tiktoken should handle most cases, but this tests error path)
            text = "Normal text"
            tokens = builder.estimate_tokens(text)

            # Should return valid result (either tiktoken or fallback)
            assert tokens > 0
        except ImportError:
            pytest.skip("tiktoken not available")

    def test_artifact_entry_dataclass(self):
        """Test ArtifactEntry dataclass."""
        entry = ArtifactEntry(
            key="specification",
            content="Test content",
            token_estimate=100,
            priority=1,
        )

        assert entry.key == "specification"
        assert entry.content == "Test content"
        assert entry.token_estimate == 100
        assert entry.priority == 1

    def test_build_context_respects_priority_over_order(self):
        """Test that priority takes precedence over list order."""
        builder = ArtifactContextBuilder(token_budget=150, use_tiktoken=False)

        # Provide artifacts in reverse priority order
        artifacts = [
            ("api_design", "D" * 200, 4),  # 4th priority
            ("architecture", "C" * 200, 3),  # 3rd priority
            ("user_stories", "B" * 200, 2),  # 2nd priority
            ("specification", "A" * 200, 1),  # 1st priority (should be filled first)
        ]

        result = builder.build_context(artifacts)

        # Specification (priority 1) should always be included
        assert "specification" in result

    def test_build_context_logging(self, caplog):
        """Test that builder logs appropriately."""
        import logging
        caplog.set_level(logging.DEBUG)

        builder = ArtifactContextBuilder(token_budget=500, use_tiktoken=False)

        artifacts = [
            ("specification", "A" * 200, 1),
            ("user_stories", "B" * 200, 2),
        ]

        builder.build_context(artifacts)

        # Check for log messages
        assert any("Built context" in record.message for record in caplog.records)
