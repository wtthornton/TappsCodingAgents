"""
Unit tests for PlannerAgent helper methods.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.planner import PlannerAgent


@pytest.mark.unit
class TestPlannerAgentHelpers:
    """Test cases for PlannerAgent helper methods."""

    @pytest.fixture
    def planner_agent(self):
        """Create a PlannerAgent instance for testing."""
        return PlannerAgent()

    def test_generate_story_id_basic(self, planner_agent):
        """Test story ID generation from description."""
        description = "User should be able to log in"
        story_id = planner_agent._generate_story_id(description)

        assert isinstance(story_id, str)
        assert story_id.startswith("story-")
        assert "log" in story_id.lower() or "in" in story_id.lower()

    def test_generate_story_id_with_epic(self, planner_agent):
        """Test story ID generation with epic prefix."""
        description = "Add shopping cart"
        epic = "checkout"
        story_id = planner_agent._generate_story_id(description, epic=epic)

        assert isinstance(story_id, str)
        assert story_id.startswith("checkout-")
        assert "cart" in story_id.lower() or "shopping" in story_id.lower()

    def test_generate_story_id_special_characters(self, planner_agent):
        """Test story ID generation handles special characters."""
        description = "User's profile & settings!!!"
        story_id = planner_agent._generate_story_id(description)

        assert isinstance(story_id, str)
        assert " " not in story_id
        assert "'" not in story_id
        assert "&" not in story_id
        assert "!" not in story_id

    def test_extract_title_short(self, planner_agent):
        """Test title extraction from short description."""
        description = "User login feature"
        title = planner_agent._extract_title(description)

        assert title == "User login feature"
        assert len(title) <= 60

    def test_extract_title_long(self, planner_agent):
        """Test title extraction from long description."""
        description = "This is a very long description that exceeds the maximum length limit of 60 characters and should be truncated"
        title = planner_agent._extract_title(description)

        assert len(title) <= 60
        assert title.endswith("...")

    def test_extract_title_multiline(self, planner_agent):
        """Test title extraction from multiline description."""
        description = "First line\nSecond line\nThird line"
        title = planner_agent._extract_title(description)

        assert title == "First line"

    def test_infer_domain_backend(self, planner_agent):
        """Test domain inference for backend."""
        description = "Create API endpoint for user authentication"
        domain = planner_agent._infer_domain(description)

        assert domain == "backend"

    def test_infer_domain_frontend(self, planner_agent):
        """Test domain inference for frontend."""
        description = "Create UI component for user login page"
        domain = planner_agent._infer_domain(description)

        assert domain == "frontend"

    def test_infer_domain_testing(self, planner_agent):
        """Test domain inference for testing."""
        description = "Add test specs for authentication feature"
        domain = planner_agent._infer_domain(description)

        assert domain == "testing"

    def test_infer_domain_documentation(self, planner_agent):
        """Test domain inference for documentation."""
        description = "Write user documentation"
        domain = planner_agent._infer_domain(description)

        assert domain == "documentation"

    def test_infer_domain_general(self, planner_agent):
        """Test domain inference defaults to general."""
        description = "Some random feature"
        domain = planner_agent._infer_domain(description)

        assert domain == "general"

    def test_indent_yaml_multiline(self, planner_agent):
        """Test YAML multiline indentation."""
        text = "Line 1\nLine 2\nLine 3"
        indented = planner_agent._indent_yaml_multiline(text, indent=2)

        assert indented.startswith("  Line 1")
        assert "  Line 2" in indented
        assert "  Line 3" in indented

    def test_read_story_metadata_valid(self, planner_agent, tmp_path: Path):
        """Test reading story metadata from valid file."""
        story_file = tmp_path / "story-test.md"
        content = """# Test Story

```yaml
story_id: test-story
title: Test Story
epic: test-epic
status: draft
```

Content here
"""
        story_file.write_text(content, encoding="utf-8")

        metadata = planner_agent._read_story_metadata(story_file)

        assert metadata["story_id"] == "test-story"
        assert metadata["title"] == "Test Story"
        assert metadata["epic"] == "test-epic"
        assert metadata["status"] == "draft"

    def test_read_story_metadata_invalid_yaml(self, planner_agent, tmp_path: Path):
        """Test reading story metadata from file with invalid YAML."""
        story_file = tmp_path / "story-invalid.md"
        content = """# Test Story

```yaml
story_id: test-story
title: [invalid yaml
```

Content here
"""
        story_file.write_text(content, encoding="utf-8")

        metadata = planner_agent._read_story_metadata(story_file)

        assert metadata == {}

    def test_read_story_metadata_no_yaml(self, planner_agent, tmp_path: Path):
        """Test reading story metadata from file without YAML."""
        story_file = tmp_path / "story-no-yaml.md"
        content = """# Test Story

Just regular markdown content.
"""
        story_file.write_text(content, encoding="utf-8")

        metadata = planner_agent._read_story_metadata(story_file)

        assert metadata == {}

    @pytest.mark.asyncio
    async def test_generate_user_stories_standard_format(self, planner_agent):
        """Test _generate_user_stories generates stories in standard format."""
        from unittest.mock import AsyncMock, patch
        
        functional_reqs = ["User can login", "User can logout"]
        
        mock_mal = AsyncMock()
        mock_mal.generate = AsyncMock(return_value='[{"story": "As a user, I want to login, so that I can access my account", "user": "user", "goal": "to login", "benefit": "I can access my account", "acceptance_criteria": ["Login form works", "Authentication succeeds"], "story_points": 3}]')
        
        with patch("tapps_agents.agents.planner.agent.MAL", return_value=mock_mal):
            stories = await planner_agent._generate_user_stories(
                "Add user authentication",
                functional_reqs,
            )
        
        assert len(stories) > 0
        story = stories[0]
        assert "story" in story
        assert "As a" in story["story"]
        assert "I want" in story["story"]
        assert "so that" in story["story"]
        assert "user" in story
        assert "goal" in story
        assert "benefit" in story
        assert "acceptance_criteria" in story
        assert "story_points" in story

    @pytest.mark.asyncio
    async def test_generate_user_stories_fallback(self, planner_agent):
        """Test _generate_user_stories fallback when LLM fails."""
        from unittest.mock import AsyncMock, patch
        
        with patch("tapps_agents.agents.planner.agent.MAL") as mock_mal_class:
            mock_mal = AsyncMock()
            mock_mal.generate = AsyncMock(side_effect=Exception("LLM error"))
            mock_mal_class.return_value = mock_mal
            
            stories = await planner_agent._generate_user_stories(
                "Add feature",
                [],
            )
        
        # Should return fallback story
        assert len(stories) == 1
        assert "story" in stories[0]
        assert "As a" in stories[0]["story"]

    def test_format_plan_markdown(self, planner_agent):
        """Test _format_plan_markdown generates proper markdown."""
        functional_reqs = ["User can login", "User can logout"]
        non_functional_reqs = ["Secure", "Fast"]
        user_stories = [
            {
                "story": "As a user, I want to login, so that I can access my account",
                "user": "user",
                "goal": "to login",
                "benefit": "I can access my account",
                "acceptance_criteria": ["Login form works", "Authentication succeeds"],
                "story_points": 3,
            },
            {
                "story": "As a user, I want to logout, so that I can secure my session",
                "user": "user",
                "goal": "to logout",
                "benefit": "I can secure my session",
                "acceptance_criteria": ["Logout button works", "Session is cleared"],
                "story_points": 2,
            },
        ]
        
        requirements_result = {
            "summary": {
                "overview": "User authentication system",
            },
        }
        
        markdown = planner_agent._format_plan_markdown(
            description="Add user authentication",
            requirements_result=requirements_result,
            functional_reqs=functional_reqs,
            non_functional_reqs=non_functional_reqs,
            user_stories=user_stories,
        )
        
        assert "# Plan: Add user authentication" in markdown
        assert "## Overview" in markdown
        assert "User authentication system" in markdown
        assert "## Requirements" in markdown
        assert "### Functional Requirements" in markdown
        assert "- User can login" in markdown
        assert "- User can logout" in markdown
        assert "### Non-Functional Requirements" in markdown
        assert "- Secure" in markdown
        assert "- Fast" in markdown
        assert "## User Stories" in markdown
        assert "### Story 1:" in markdown
        assert "As a user, I want to login" in markdown
        assert "**Story Points:** 3" in markdown
        assert "**Acceptance Criteria:**" in markdown
        assert "- [ ] Login form works" in markdown
        assert "### Story 2:" in markdown
        assert "As a user, I want to logout" in markdown

    def test_format_plan_markdown_empty_stories(self, planner_agent):
        """Test _format_plan_markdown with empty user stories."""
        markdown = planner_agent._format_plan_markdown(
            description="Test",
            requirements_result={},
            functional_reqs=[],
            non_functional_reqs=[],
            user_stories=[],
        )
        
        assert "# Plan: Test" in markdown
        assert "(User stories to be generated)" in markdown