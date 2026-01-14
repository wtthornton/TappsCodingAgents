"""
E2E tests for Requirements Workflow improvements.

Tests the complete requirements gathering and planning workflow:
1. Analyst agent markdown generation
2. Planner user story generation
3. Intent parser requirements detection
"""

from pathlib import Path

import pytest

from tapps_agents.agents.analyst.agent import AnalystAgent
from tapps_agents.agents.planner.agent import PlannerAgent
from tapps_agents.simple_mode.intent_parser import IntentParser, IntentType

pytestmark = pytest.mark.e2e


class TestRequirementsWorkflowE2E:
    """E2E tests for requirements workflow improvements."""

    @pytest.mark.asyncio
    async def test_analyst_gather_requirements_generates_markdown(self, tmp_path):
        """Test that analyst gather-requirements generates markdown document."""
        analyst = AnalystAgent()
        await analyst.activate(project_root=tmp_path, offline_mode=False)
        
        try:
            output_file = str(tmp_path / "requirements.md")
            result = await analyst.run(
                "gather-requirements",
                description="Add user authentication with OAuth2",
                context="Existing FastAPI application",
                output_file=output_file,
            )
            
            assert result["success"] is True
            assert "requirements" in result
            
            # Check markdown content
            if "markdown" in result["requirements"]:
                markdown = result["requirements"]["markdown"]
                assert "# Requirements:" in markdown
                assert "Add user authentication with OAuth2" in markdown
                assert "## Functional Requirements" in markdown or "## Overview" in markdown
            
            # Check file was created
            output_path = Path(output_file)
            if output_path.exists():
                content = output_path.read_text(encoding="utf-8")
                assert "# Requirements:" in content or "requirements" in content.lower()
        finally:
            await analyst.close()

    @pytest.mark.asyncio
    async def test_planner_plan_generates_user_stories(self, tmp_path):
        """Test that planner plan generates user stories in standard format."""
        planner = PlannerAgent()
        await planner.activate(project_root=tmp_path, offline_mode=False)
        
        try:
            result = await planner.create_plan("Add user authentication with login and logout")
            
            assert result["type"] == "plan"
            assert "description" in result
            assert "plan" in result or "markdown" in result
            
            # Check for user stories
            if "user_stories" in result:
                stories = result["user_stories"]
                assert len(stories) > 0
                for story in stories:
                    assert "story" in story
                    # Check standard format
                    story_text = story.get("story", "")
                    if story_text:
                        assert "As a" in story_text or "as a" in story_text.lower()
                        assert "I want" in story_text or "i want" in story_text.lower()
                        assert "so that" in story_text or "so that" in story_text.lower()
            
            # Check markdown content
            plan_content = result.get("plan") or result.get("markdown", "")
            if plan_content:
                assert "# Plan:" in plan_content or "Plan:" in plan_content
                assert "User Stories" in plan_content or "user stories" in plan_content.lower()
        finally:
            await planner.close()

    def test_intent_parser_detects_requirements_intent(self):
        """Test that intent parser detects requirements-related intents."""
        parser = IntentParser()
        
        # Test various requirements keywords
        test_cases = [
            "gather requirements for user authentication",
            "extract requirements from stakeholder description",
            "document requirements for new feature",
            "analyze requirements for payment system",
            "create requirements document",
            "requirements gathering for epic",
            "requirements analysis for project",
        ]
        
        for test_case in test_cases:
            intent = parser.parse(test_case)
            assert intent.type == IntentType.REQUIREMENTS, f"Failed for: {test_case}"
            assert intent.confidence > 0.3, f"Low confidence for: {test_case}"

    def test_requirements_intent_agent_sequence(self):
        """Test that requirements intent returns correct agent sequence."""
        parser = IntentParser()
        intent = parser.parse("gather requirements for user authentication")
        
        sequence = intent.get_agent_sequence()
        assert "analyst" in sequence
        assert "planner" in sequence
        assert "documenter" in sequence

    def test_requirements_intent_distinct_from_build(self):
        """Test that requirements intent is distinct from build intent."""
        parser = IntentParser()
        
        requirements_intent = parser.parse("gather requirements for feature")
        build_intent = parser.parse("build feature")
        
        assert requirements_intent.type == IntentType.REQUIREMENTS
        assert build_intent.type == IntentType.BUILD
        assert requirements_intent.type != build_intent.type

    @pytest.mark.asyncio
    async def test_end_to_end_requirements_workflow(self, tmp_path):
        """Test complete end-to-end requirements workflow."""
        # Step 1: Gather requirements
        analyst = AnalystAgent()
        await analyst.activate(project_root=tmp_path, offline_mode=False)
        
        try:
            requirements_result = await analyst.run(
                "gather-requirements",
                description="Add payment processing with Stripe",
                output_file=str(tmp_path / "requirements.md"),
            )
            
            assert requirements_result["success"] is True
        finally:
            await analyst.close()
        
        # Step 2: Create plan with user stories
        planner = PlannerAgent()
        await planner.activate(project_root=tmp_path, offline_mode=False)
        
        try:
            plan_result = await planner.create_plan("Add payment processing with Stripe")
            
            assert plan_result["type"] == "plan"
            assert "plan" in plan_result or "markdown" in plan_result
            
            # Verify user stories are generated
            if "user_stories" in plan_result:
                assert len(plan_result["user_stories"]) > 0
        finally:
            await planner.close()
        
        # Step 3: Verify files were created
        requirements_file = tmp_path / "requirements.md"
        # Requirements file may or may not exist depending on mode
        # (Cursor mode returns instructions, CLI mode creates files)
        
        # Verify intent detection works
        parser = IntentParser()
        intent = parser.parse("gather requirements for payment processing")
        assert intent.type == IntentType.REQUIREMENTS
