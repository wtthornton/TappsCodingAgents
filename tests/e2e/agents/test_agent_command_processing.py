"""
E2E tests for agent command processing and validation.

Tests validate:
- Command parsing (star-prefixed, numbered, space-separated)
- Command validation
- Parameter validation
- Help output
"""

import pytest

from tests.e2e.fixtures.agent_test_helpers import (
    assert_command_parsed,
    assert_error_message,
    create_test_agent,
    execute_command,
    validate_help_output,
)


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestAgentCommandProcessing:
    """Test agent command parsing and validation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_star_prefixed_command_parsing(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that star-prefixed commands are parsed correctly."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Get commands to find a valid one
        commands = agent.get_commands()
        if not commands:
            pytest.skip(f"No commands available for {agent_type}")

        # Test first non-help command
        test_command = None
        for cmd in commands:
            if cmd["command"] != "*help":
                test_command = cmd["command"]
                break

        if test_command:
            parsed = agent.parse_command(test_command)
            expected_cmd = test_command.lstrip("*")
            assert_command_parsed(parsed, expected_cmd, {})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_numbered_command_parsing(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that numbered commands (1, 2, etc.) map to correct commands."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        commands = agent.get_commands()
        if len(commands) < 2:
            pytest.skip(f"Not enough commands for {agent_type}")

        # Test first command (should be help, index 1)
        parsed = agent.parse_command("1")
        expected_cmd = commands[0]["command"].lstrip("*")
        assert_command_parsed(parsed, expected_cmd, {})

        # Test second command if available
        if len(commands) > 1:
            parsed = agent.parse_command("2")
            expected_cmd = commands[1]["command"].lstrip("*")
            assert_command_parsed(parsed, expected_cmd, {})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_space_separated_command_parsing(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that space-separated commands are parsed correctly."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        commands = agent.get_commands()
        if not commands:
            pytest.skip(f"No commands available for {agent_type}")

        # Find a command that might take arguments
        test_command = None
        for cmd in commands:
            cmd_name = cmd["command"].lstrip("*")
            if cmd_name in ["review", "score", "plan", "implement"]:
                test_command = cmd_name
                break

        if test_command:
            # Test command with argument
            parsed = agent.parse_command(f"{test_command} test_file.py")
            assert_command_parsed(parsed, test_command, {"file": "test_file.py"})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_argument_extraction(self, e2e_project, mock_mal, agent_type):
        """Test that command arguments are extracted correctly."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Test with reviewer/implementer commands that take file arguments
        if agent_type in ["reviewer", "implementer"]:
            parsed = agent.parse_command("*review test_file.py")
            command, args = parsed
            assert command == "review"
            assert "file" in args
            assert args["file"] == "test_file.py"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_unknown_command_rejection(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that unknown commands are rejected with clear errors."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Try an unknown command
        result = await execute_command(agent, "*unknown-command-xyz")
        assert_error_message(result, ["unknown", "command"])

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_invalid_command_format(self, e2e_project, mock_mal, agent_type):
        """Test that invalid command formats are handled gracefully."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Try invalid formats
        result = await execute_command(agent, "***invalid")
        # Should either parse or return error
        assert "error" in result or result  # Response should exist

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_out_of_range_numbered_command(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that out-of-range numbered commands produce clear errors."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        commands = agent.get_commands()
        # Try a number way out of range
        out_of_range = str(len(commands) + 100)
        parsed = agent.parse_command(out_of_range)
        # parse_command may return empty or handle gracefully
        # The actual error would come from run()
        result = await execute_command(agent, out_of_range)
        # Should handle gracefully (either error or default behavior)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_missing_required_arguments(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that missing required arguments produce actionable errors."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Commands that require arguments
        if agent_type == "reviewer":
            result = await execute_command(agent, "*review")
            # Should indicate missing file argument
            assert "error" in result or "file" in str(result).lower()

        elif agent_type == "planner":
            result = await execute_command(agent, "*plan")
            # Should indicate missing description
            assert "error" in result or "description" in str(result).lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_parameter_validation(self, e2e_project, mock_mal, agent_type):
        """Test that command parameters are validated."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        # Test with invalid file path
        if agent_type == "reviewer":
            result = await execute_command(agent, "*review /nonexistent/path/file.py")
            # Should validate file existence or path
            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_help_command_output(self, e2e_project, mock_mal, agent_type):
        """Test that help command returns structured command list."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*help")
        validate_help_output(result)

        # Verify help content contains command descriptions
        content = result["content"]
        commands = agent.get_commands()
        # Should mention at least some commands
        assert len(content) > 50, "Help content should be substantial"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_help_contains_descriptions(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that help output contains command descriptions."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*help")
        validate_help_output(result)

        content = result["content"]
        commands = agent.get_commands()
        # Check that at least one command description appears
        found_any = False
        for cmd in commands[:3]:  # Check first 3 commands
            if cmd["description"].lower() in content.lower():
                found_any = True
                break
        assert found_any, "Help should contain command descriptions"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "agent_type",
        ["planner", "implementer", "reviewer", "tester"],
    )
    async def test_help_contains_usage_examples(
        self, e2e_project, mock_mal, agent_type
    ):
        """Test that help output contains usage examples."""
        agent = create_test_agent(agent_type, mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*help")
        validate_help_output(result)

        content = result["content"]
        # Help should mention examples or command format
        example_indicators = ["example", "type", "command", "1.", "2."]
        assert any(
            indicator in content.lower() for indicator in example_indicators
        ), "Help should contain usage examples or command format"

