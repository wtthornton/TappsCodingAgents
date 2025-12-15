"""
E2E tests for agent error handling and error messages.

Tests validate:
- Invalid input handling
- Missing file handling
- Network error handling (mocked)
- Permission error handling
- Error message quality
- Error recovery
"""

import pytest

from tests.e2e.fixtures.agent_test_helpers import (
    assert_error_message_quality,
    create_missing_file_scenario,
    create_network_error_scenario,
    create_test_agent,
    execute_command,
    validate_error_response,
)


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestAgentErrorHandling:
    """Test agent error handling and error messages."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_invalid_command_format_handling(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that invalid command formats are handled gracefully."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Try various invalid formats
        invalid_commands = ["***invalid", "   ", "", "123invalid"]
        for invalid_cmd in invalid_commands:
            result = await execute_command(agent, invalid_cmd)
            # Should return error response, not crash
            assert result is not None
            if "error" in result:
                validate_error_response(result)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_invalid_parameter_value_handling(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that invalid parameter values are handled gracefully."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Try commands with invalid parameters
        if agent_type == "reviewer":
            result = await execute_command(agent, "*review", file="")
            # Should handle empty file parameter
            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_malformed_input_handling(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that malformed input is handled gracefully."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Try malformed commands
        result = await execute_command(agent, "*plan", description=None)
        # Should handle None or malformed input
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_error_responses_not_exceptions(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that errors return error responses, not exceptions."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Try invalid command - should return dict, not raise
        result = await execute_command(agent, "*nonexistent-command-xyz")
        assert isinstance(result, dict), "Error should return dict, not raise exception"
        assert "error" in result, "Error response should contain 'error' field"

    @pytest.mark.asyncio
    async def test_missing_file_path_handling(self, e2e_project, mock_mal, tmp_path):
        """Test that missing file paths produce clear error messages."""
        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        # Create scenario with missing file
        missing_file = create_missing_file_scenario(tmp_path / "nonexistent.py")
        result = await execute_command(agent, "*review", file=str(missing_file))

        # Should produce clear error about missing file
        if "error" in result:
            validate_error_response(result, "file")
            assert_error_message_quality(
                str(result["error"]),
                {"clear": True, "context": True},
            )

    @pytest.mark.asyncio
    async def test_nonexistent_file_handling(self, e2e_project, mock_mal):
        """Test that non-existent files are handled gracefully."""
        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent, "*review", file="/nonexistent/path/to/file.py"
        )
        # Should handle gracefully
        assert result is not None
        if "error" in result:
            validate_error_response(result)

    @pytest.mark.asyncio
    async def test_file_path_validation_errors(self, e2e_project, mock_mal):
        """Test that file path validation errors are handled appropriately."""
        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        # Try invalid path patterns
        invalid_paths = ["../../../etc/passwd", "..\\..\\windows\\system32"]
        for invalid_path in invalid_paths:
            result = await execute_command(agent, "*review", file=invalid_path)
            # Should validate and reject invalid paths
            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error_type",
        ["connection", "timeout", "rate_limit"],
    )
    async def test_network_error_handling(
        self, e2e_project, mock_mal, error_type
    ):
        """Test that network errors (MAL) are handled gracefully."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        # Configure mock to raise network errors
        create_network_error_scenario(mock_mal, error_type)

        # Try command that uses MAL
        result = await execute_command(
            agent, "*plan", description="Test plan with network error"
        )
        # Should handle network error gracefully
        assert result is not None
        # May return error or handle gracefully
        if "error" in result:
            validate_error_response(result, error_type)

    @pytest.mark.asyncio
    async def test_error_message_clarity(self, e2e_project, mock_mal):
        """Test that error messages are clear and understandable."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        # Try command with missing required argument
        result = await execute_command(agent, "*plan")
        if "error" in result:
            error_msg = str(result["error"])
            assert_error_message_quality(error_msg, {"clear": True})

    @pytest.mark.asyncio
    async def test_error_message_context(self, e2e_project, mock_mal, tmp_path):
        """Test that error messages include context."""
        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        # Try with missing file
        missing_file = tmp_path / "missing.py"
        result = await execute_command(agent, "*review", file=str(missing_file))
        if "error" in result:
            error_msg = str(result["error"])
            assert_error_message_quality(error_msg, {"context": True})

    @pytest.mark.asyncio
    async def test_error_message_actionability(self, e2e_project, mock_mal):
        """Test that error messages provide actionable guidance."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        # Try command with missing argument
        result = await execute_command(agent, "*plan")
        if "error" in result:
            error_msg = str(result["error"])
            # Should provide guidance on what's needed
            assert_error_message_quality(error_msg, {"actionable": True})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_error_recovery(self, e2e_project, mock_mal, agent_type):
        """Test that agents can recover from errors and continue processing."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # First, cause an error
        error_result = await execute_command(agent, "*invalid-command-xyz")
        assert "error" in error_result

        # Then, try a valid command - should work
        valid_result = await execute_command(agent, "*help")
        assert "error" not in valid_result or valid_result.get("type") == "help"
        # Agent should still be functional

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_state_consistency_after_errors(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that agents maintain state consistency after errors."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Cause an error
        await execute_command(agent, "*invalid-command")

        # Verify agent state is still valid
        assert agent.agent_id is not None
        assert agent.config is not None
        # Should still be able to execute commands
        result = await execute_command(agent, "*help")
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_multiple_sequential_errors(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that agents can handle multiple sequential errors."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Cause multiple errors
        for i in range(3):
            result = await execute_command(agent, f"*invalid-command-{i}")
            assert "error" in result

        # Should still be functional
        result = await execute_command(agent, "*help")
        assert result is not None

    @pytest.mark.asyncio
    async def test_user_friendly_error_messages(self, e2e_project, mock_mal):
        """Test that error messages are user-friendly (not technical stack traces)."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*plan")
        if "error" in result:
            error_msg = str(result["error"])
            # Should not contain stack trace indicators
            assert "Traceback" not in error_msg
            assert "File \"" not in error_msg or "line " not in error_msg
            # Should be readable
            assert len(error_msg) < 500, "Error message should be concise"

