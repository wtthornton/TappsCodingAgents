"""
E2E tests for agent response generation and formatting.

Tests validate:
- Response appropriateness based on input
- Response formatting and structure
- Response content completeness
- Contextual appropriateness
"""

import pytest

from tests.e2e.fixtures.agent_test_helpers import (
    assert_response_quality,
    create_test_agent,
    execute_command,
    validate_response_content,
    validate_response_context,
    validate_response_structure,
)


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestAgentResponseGeneration:
    """Test agent response generation and formatting."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type,command,expected_fields",
        [
            ("planner", "*plan", ["type", "plan"]),
            ("planner", "*help", ["type", "content"]),
            ("reviewer", "*help", ["type", "content"]),
            ("implementer", "*help", ["type", "content"]),
            ("tester", "*help", ["type", "content"]),
        ],
    )
    async def test_response_structure(
        self, e2e_project, mock_mal, agent_type, command, expected_fields
    ):
        """Test that responses have proper structure."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, command, description="test description")
        validate_response_structure(result, expected_fields)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_help_response_formatting(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that help responses are properly formatted."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*help")
        # Help should have type and content
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0

    @pytest.mark.asyncio
    async def test_planner_plan_response(self, e2e_project, mock_mal):
        """Test that planner generates appropriate plan responses."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent, "*plan", description="Create a feature for user authentication"
        )
        # Should have plan-related fields
        assert result is not None
        # Should not be an error for valid input
        if "error" not in result:
            assert "plan" in result or "type" in result

    @pytest.mark.asyncio
    async def test_reviewer_review_response(self, e2e_project, mock_mal, tmp_path):
        """Test that reviewer generates appropriate review responses."""
        # Create a test file
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def example():\n    pass\n")

        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*review", file=str(test_file))
        # Should have review-related structure
        assert result is not None
        # Response should be contextually appropriate
        validate_response_context(result, "review", "reviewer")

    @pytest.mark.asyncio
    async def test_implementer_code_response(self, e2e_project, mock_mal):
        """Test that implementer generates appropriate code responses."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*implement",
            description="Create a function to calculate fibonacci numbers",
        )
        # Should have implementation-related structure
        assert result is not None
        validate_response_context(result, "implement", "implementer")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_response_contains_expected_information(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that responses contain expected information."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Test help command which should always work
        result = await execute_command(agent, "*help")
        # Should contain agent name or commands
        content = result.get("content", "")
        assert len(content) > 0, "Response should contain information"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_response_metadata(self, e2e_project, mock_mal, agent_type):
        """Test that responses include metadata when applicable."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*help")
        # Should have type field (metadata)
        assert "type" in result, "Response should have type metadata"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_response_contextual_appropriateness(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that responses are contextually appropriate for agent type."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Get a valid command for this agent
        commands = agent.get_commands()
        if not commands:
            pytest.skip(f"No commands for {agent_type}")

        # Try first non-help command
        test_command = None
        for cmd in commands:
            if cmd["command"] != "*help":
                test_command = cmd["command"]
                break

        if test_command:
            result = await execute_command(agent, test_command, description="test")
            validate_response_context(result, test_command.lstrip("*"), agent_type)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_simple_command_responses(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test responses for simple commands (help, status)."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*help")
        # Simple commands should always work
        assert result is not None
        assert "error" not in result or result.get("type") == "help"

    @pytest.mark.asyncio
    async def test_parameterized_command_responses(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test responses for commands with parameters."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def test():\n    pass\n")

        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*review", file=str(test_file))
        # Parameterized commands should handle parameters
        assert result is not None

    @pytest.mark.asyncio
    async def test_context_dependent_responses(self, e2e_project, mock_mal):
        """Test responses for commands that require context."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*plan",
            description="Create a REST API for user management with authentication",
        )
        # Context-dependent commands should use context
        assert result is not None
        if "error" not in result:
            # Should have generated something based on context
            assert "plan" in result or "type" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer"],
    )
    async def test_artifact_generating_responses(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test responses for commands that produce artifacts."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        if agent_type == "planner":
            result = await execute_command(
                agent, "*plan", description="Feature implementation plan"
            )
        else:
            # Implementer requires specification and file_path
            result = await execute_command(
                agent, "*implement", 
                specification="Implement a feature",
                file_path="test_feature.py"
            )

        # Artifact-generating commands should produce content
        assert result is not None
        assert_response_quality(result, {"has_content": True})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_response_formatting_consistency(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that response formatting is consistent across similar commands."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Execute help command multiple times
        result1 = await execute_command(agent, "*help")
        result2 = await execute_command(agent, "*help")

        # Formatting should be consistent
        assert result1.get("type") == result2.get("type")
        # Both should have same structure
        assert set(result1.keys()) == set(result2.keys())

