"""
Integration tests for PlannerAgent commands.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.agents.planner import PlannerAgent


@pytest.mark.integration
class TestPlannerAgent:
    """Integration tests for PlannerAgent."""

    @pytest.fixture
    def mock_mal_with_responses(self):
        """Create a mock MAL with specific responses for planner."""
        mal = MagicMock()

        # Mock complexity estimation (returns "3")
        async def generate_complexity(prompt, **kwargs):
            if "complexity" in prompt.lower() or "scale of 1-5" in prompt.lower():
                return "3"
            elif "acceptance criteria" in prompt.lower() or "tasks:" in prompt.lower():
                return """ACCEPTANCE CRITERIA:
- Criterion 1: Feature works as expected
- Criterion 2: All edge cases handled
- Criterion 3: Tests pass

TASKS:
1. Implement feature logic
2. Add unit tests
3. Update documentation"""
            else:
                return "Mock plan response with stories and dependencies"

        mal.generate = AsyncMock(side_effect=generate_complexity)
        mal.close = AsyncMock()
        return mal

    @pytest.mark.asyncio
    async def test_planner_initialization(self, mock_mal_with_responses):
        """Test that PlannerAgent initializes correctly."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        assert planner.agent_id == "planner"
        assert planner.agent_name == "Planner Agent"
        assert planner.mal is not None

    @pytest.mark.asyncio
    async def test_planner_help_command(self, mock_mal_with_responses):
        """Test help command returns help information."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        result = await planner.run("help")

        assert result["type"] == "help"
        assert "content" in result
        assert "*plan" in result["content"]
        assert "*create-story" in result["content"]
        assert "*list-stories" in result["content"]

    @pytest.mark.asyncio
    async def test_planner_plan_command(self, mock_mal_with_responses):
        """Test plan command creates a plan."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        description = "Add user authentication feature"
        result = await planner.run("plan", description=description)

        assert result["type"] == "plan"
        assert result["description"] == description
        assert "plan" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_planner_plan_command_missing_description(
        self, mock_mal_with_responses
    ):
        """Test plan command returns error when description is missing."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        result = await planner.run("plan")

        assert "error" in result
        assert "description" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_planner_create_story_command(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test create-story command creates a story file."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        # Set stories directory to temp path
        planner.stories_dir = tmp_path / "stories"
        await planner.activate()

        description = "User should be able to log in with Google"
        result = await planner.run("create-story", description=description)

        assert result["type"] == "story"
        assert "story_id" in result
        assert "story_file" in result
        assert "metadata" in result
        assert "acceptance_criteria" in result
        assert "tasks" in result

        # Check story file was created
        story_file = Path(result["story_file"])
        assert story_file.exists()
        assert story_file.suffix == ".md"

        # Check file content
        content = story_file.read_text()
        assert result["story_id"] in content
        assert description in content

    @pytest.mark.asyncio
    async def test_planner_create_story_with_epic(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test create-story command with epic parameter."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        planner.stories_dir = tmp_path / "stories"
        await planner.activate()

        description = "Add shopping cart functionality"
        epic = "checkout"
        result = await planner.run("create-story", description=description, epic=epic)

        assert result["type"] == "story"
        assert result["metadata"]["epic"] == epic
        assert epic in result["story_id"]

    @pytest.mark.asyncio
    async def test_planner_create_story_with_priority(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test create-story command with priority parameter."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        planner.stories_dir = tmp_path / "stories"
        await planner.activate()

        description = "Critical security fix"
        priority = "high"
        result = await planner.run(
            "create-story", description=description, priority=priority
        )

        assert result["type"] == "story"
        assert result["metadata"]["priority"] == priority

    @pytest.mark.asyncio
    async def test_planner_create_story_missing_description(
        self, mock_mal_with_responses
    ):
        """Test create-story command returns error when description is missing."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        result = await planner.run("create-story")

        assert "error" in result
        assert "description" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_planner_list_stories_empty(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test list-stories command when no stories exist."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        planner.stories_dir = tmp_path / "stories"
        await planner.activate()

        result = await planner.run("list-stories")

        assert result["type"] == "list_stories"
        assert result["count"] == 0
        assert result["stories"] == []

    @pytest.mark.asyncio
    async def test_planner_list_stories_with_files(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test list-stories command lists existing stories."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        planner.stories_dir = stories_dir
        await planner.activate()

        # Create a test story file
        story_file = stories_dir / "story-test-login.md"
        story_content = """# Test Login Story

```yaml
story_id: test-login
title: Test Login Story
epic: authentication
status: draft
priority: high
complexity: 3
```

Description here
"""
        story_file.write_text(story_content)

        result = await planner.run("list-stories")

        assert result["type"] == "list_stories"
        assert result["count"] == 1
        assert len(result["stories"]) == 1
        assert result["stories"][0]["story_id"] == "test-login"
        assert result["stories"][0]["epic"] == "authentication"

    @pytest.mark.asyncio
    async def test_planner_list_stories_filter_by_epic(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test list-stories command filters by epic."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        planner.stories_dir = stories_dir
        await planner.activate()

        # Create two story files with different epics
        story1 = stories_dir / "story-auth-1.md"
        story1.write_text(
            """# Auth Story

```yaml
story_id: auth-1
epic: authentication
status: draft
```
"""
        )

        story2 = stories_dir / "story-checkout-1.md"
        story2.write_text(
            """# Checkout Story

```yaml
story_id: checkout-1
epic: checkout
status: draft
```
"""
        )

        result = await planner.run("list-stories", epic="authentication")

        assert result["type"] == "list_stories"
        assert result["count"] == 1
        assert result["stories"][0]["epic"] == "authentication"

    @pytest.mark.asyncio
    async def test_planner_list_stories_filter_by_status(
        self, mock_mal_with_responses, tmp_path: Path
    ):
        """Test list-stories command filters by status."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir(parents=True)
        planner.stories_dir = stories_dir
        await planner.activate()

        # Create two story files with different statuses
        story1 = stories_dir / "story-draft.md"
        story1.write_text(
            """# Draft Story

```yaml
story_id: draft-1
status: draft
```
"""
        )

        story2 = stories_dir / "story-done.md"
        story2.write_text(
            """# Done Story

```yaml
story_id: done-1
status: done
```
"""
        )

        result = await planner.run("list-stories", status="draft")

        assert result["type"] == "list_stories"
        assert result["count"] == 1
        assert result["stories"][0]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_planner_unknown_command(self, mock_mal_with_responses):
        """Test that unknown commands return error."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        result = await planner.run("unknown_command")

        assert "error" in result
        assert (
            "unknown" in result["error"].lower() or "command" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_planner_estimate_complexity(self, mock_mal_with_responses):
        """Test complexity estimation."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        description = "Simple feature"
        complexity = await planner._estimate_complexity(description)

        assert isinstance(complexity, int)
        assert 1 <= complexity <= 5

    @pytest.mark.asyncio
    async def test_planner_generate_story_details(self, mock_mal_with_responses):
        """Test story details generation."""
        planner = PlannerAgent(mal=mock_mal_with_responses)
        await planner.activate()

        description = "User login feature"
        acceptance_criteria, tasks = await planner._generate_story_details(description)

        assert isinstance(acceptance_criteria, list)
        assert isinstance(tasks, list)
        assert len(acceptance_criteria) > 0
        assert len(tasks) > 0
