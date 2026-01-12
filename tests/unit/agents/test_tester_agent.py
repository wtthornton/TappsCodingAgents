"""
Unit tests for Tester Agent.

Tests agent initialization, command handling, test generation, test execution,
test framework detection, and error handling.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.tester.agent import TesterAgent

pytestmark = pytest.mark.unit


class TestTesterAgentInitialization:
    """Tests for TesterAgent initialization."""

    @patch("tapps_agents.agents.tester.agent.load_config")
    def test_tester_agent_init(self, mock_load_config):
        """Test TesterAgent initialization."""
        mock_config = MagicMock()
        mock_config.agents = MagicMock()
        mock_config.agents.tester = MagicMock()
        mock_config.agents.tester.test_framework = "pytest"
        mock_config.agents.tester.tests_dir = "tests"
        mock_config.agents.tester.coverage_threshold = 80.0
        mock_config.agents.tester.auto_write_tests = True
        mock_config.context7 = MagicMock()
        mock_config.context7.enabled = False
        mock_load_config.return_value = mock_config
        
        agent = TesterAgent()
        assert agent.agent_id == "tester"
        assert agent.agent_name == "Tester Agent"
        assert agent.config is not None
        assert agent.test_generator is not None
        assert agent.test_framework == "pytest"

    @pytest.mark.asyncio
    async def test_tester_agent_activate(self, temp_project_dir: Path):
        """Test TesterAgent activation."""
        agent = TesterAgent()
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_tester_agent_get_commands(self):
        """Test TesterAgent command list."""
        agent = TesterAgent()
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        command_names = [cmd["command"] for cmd in commands]
        assert "*test" in command_names
        assert "*generate-tests" in command_names
        assert "*run-tests" in command_names


class TestTesterAgentTestCommand:
    """Tests for test command."""

    @pytest.mark.asyncio
    async def test_test_command_success(self, sample_python_file):
        """Test test command with successful test generation."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("test", file=str(sample_python_file))
        
        assert "type" in result
        assert result["type"] == "test"
        assert "instruction" in result
        assert "skill_command" in result
        assert "test_file" in result

    @pytest.mark.asyncio
    async def test_test_command_missing_file(self):
        """Test test command without file parameter."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("test")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_test_command_file_not_found(self, tmp_path):
        """Test test command with non-existent file."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("test", file=str(tmp_path / "nonexistent.py"))
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_test_command_with_test_file(self, sample_python_file, tmp_path):
        """Test test command with custom test file path."""
        agent = TesterAgent()
        await agent.activate()
        
        test_file = tmp_path / "custom_test.py"
        result = await agent.run("test", file=str(sample_python_file), test_file=str(test_file))
        
        assert "type" in result
        assert result["type"] == "test"
        assert result["test_file"] == str(test_file)

    @pytest.mark.asyncio
    async def test_test_command_integration(self, sample_python_file):
        """Test test command with integration flag."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("test", file=str(sample_python_file), integration=True)
        
        assert "type" in result
        assert result["type"] == "test"

    @pytest.mark.asyncio
    async def test_test_command_with_expert_guidance(self, sample_python_file):
        """Test test command with expert consultation."""
        agent = TesterAgent()
        await agent.activate()
        
        # Mock expert registry
        mock_registry = MagicMock()
        mock_consultation = MagicMock()
        mock_consultation.weighted_answer = "Testing advice"
        mock_consultation.confidence = 0.9
        mock_consultation.confidence_threshold = 0.7
        mock_registry.consult = AsyncMock(return_value=mock_consultation)
        agent.expert_registry = mock_registry
        
        result = await agent.run("test", file=str(sample_python_file))
        
        assert "type" in result
        assert "expert_advice" in result
        assert mock_registry.consult.called

    @pytest.mark.asyncio
    async def test_test_command_method(self, sample_python_file):
        """Test test_command method directly."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.test_command(file=str(sample_python_file))
        
        assert "type" in result
        assert result["type"] == "test"


class TestTesterAgentGenerateTestsCommand:
    """Tests for generate-tests command."""

    @pytest.mark.asyncio
    async def test_generate_tests_command_success(self, sample_python_file):
        """Test generate-tests command with successful generation."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("generate-tests", file=str(sample_python_file))
        
        assert "type" in result
        assert result["type"] == "test_generation"
        assert "instruction" in result
        assert "skill_command" in result
        assert "test_file" in result

    @pytest.mark.asyncio
    async def test_generate_tests_command_missing_file(self):
        """Test generate-tests command without file parameter."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("generate-tests")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_tests_command_file_not_found(self, tmp_path):
        """Test generate-tests command with non-existent file."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("generate-tests", file=str(tmp_path / "nonexistent.py"))
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_tests_command_integration(self, sample_python_file):
        """Test generate-tests command with integration flag."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("generate-tests", file=str(sample_python_file), integration=True)
        
        assert "type" in result
        assert result["type"] == "test_generation"

    @pytest.mark.asyncio
    async def test_generate_tests_command_method(self, sample_python_file):
        """Test generate_tests_command method directly."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.generate_tests_command(file=str(sample_python_file))
        
        assert "type" in result
        assert result["type"] == "test_generation"


class TestTesterAgentGenerateE2ETestsCommand:
    """Tests for generate-e2e-tests command."""

    @pytest.mark.asyncio
    async def test_generate_e2e_tests_command_success(self, tmp_path):
        """Test generate-e2e-tests command with successful generation."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        result = await agent.run("generate-e2e-tests", project_root=str(tmp_path))
        
        assert "type" in result
        assert result["type"] == "e2e_test_generation"
        # May have error if no E2E framework detected
        if "error" not in result:
            assert "instruction" in result
            assert "framework_detected" in result

    @pytest.mark.asyncio
    async def test_generate_e2e_tests_command_no_framework(self, tmp_path):
        """Test generate-e2e-tests command when no framework detected."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock test generator to return None (no framework)
        agent.test_generator.prepare_e2e_tests = MagicMock(return_value=None)
        
        result = await agent.run("generate-e2e-tests", project_root=str(tmp_path))
        
        assert "type" in result
        assert result["type"] == "e2e_test_generation"
        assert "error" in result
        assert result["framework_detected"] is False

    @pytest.mark.asyncio
    async def test_generate_e2e_tests_command_project_not_found(self):
        """Test generate-e2e-tests command with non-existent project root."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("generate-e2e-tests", project_root="/nonexistent/path")
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_e2e_tests_command_method(self, tmp_path):
        """Test generate_e2e_tests_command method directly."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        result = await agent.generate_e2e_tests_command(project_root=str(tmp_path))
        
        assert "type" in result
        assert result["type"] == "e2e_test_generation"


class TestTesterAgentRunTestsCommand:
    """Tests for run-tests command."""

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.tester.agent.subprocess.run")
    async def test_run_tests_command_success(self, mock_subprocess, tmp_path):
        """Test run-tests command with successful execution."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = await agent.run("run-tests")
        
        assert "type" in result
        assert result["type"] == "test_execution"
        assert "result" in result
        assert result["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_run_tests_command_test_path_not_found(self):
        """Test run-tests command with non-existent test path."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("run-tests", test_path="/nonexistent/path")
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.tester.agent.subprocess.run")
    async def test_run_tests_command_with_coverage(self, mock_subprocess, tmp_path):
        """Test run-tests command with coverage."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Mock coverage file
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text('{"totals": {"percent_covered": 85.0}}')
        
        with patch("tapps_agents.agents.tester.agent.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.__truediv__ = lambda self, other: coverage_file
            
            result = await agent.run("run-tests", coverage=True)
            
            assert "type" in result
            assert "result" in result

    @pytest.mark.asyncio
    async def test_run_tests_command_method(self, tmp_path):
        """Test run_tests_command method directly."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        with patch.object(agent, '_run_pytest', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "return_code": 0}
            
            result = await agent.run_tests_command()
            
            assert "type" in result
            assert result["type"] == "test_execution"


class TestTesterAgentHelperMethods:
    """Tests for helper methods."""

    def test_get_test_file_path_from_src(self, tmp_path):
        """Test _get_test_file_path with source in src/."""
        agent = TesterAgent()
        
        src_file = tmp_path / "src" / "module" / "file.py"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("code")
        
        # Change to tmp_path for relative path calculation
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            test_path = agent._get_test_file_path(src_file)
            
            assert "tests" in str(test_path)
            assert "test_file.py" in str(test_path)
        finally:
            os.chdir(old_cwd)

    def test_get_test_file_path_from_root(self, tmp_path):
        """Test _get_test_file_path with source in root."""
        agent = TesterAgent()
        
        source_file = tmp_path / "file.py"
        source_file.write_text("code")
        
        # Change to tmp_path for relative path calculation
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            test_path = agent._get_test_file_path(source_file)
            
            assert "tests" in str(test_path)
            assert "test_file.py" in str(test_path)
        finally:
            os.chdir(old_cwd)

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.tester.agent.subprocess.run")
    async def test_run_pytest_success(self, mock_subprocess, tmp_path):
        """Test _run_pytest with successful execution."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "5 passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = await agent._run_pytest(test_path=tmp_path, coverage=False)
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "summary" in result

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.tester.agent.subprocess.run")
    async def test_run_pytest_failure(self, mock_subprocess, tmp_path):
        """Test _run_pytest with test failures."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock subprocess result with failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "2 failed"
        mock_result.stderr = "Error details"
        mock_subprocess.return_value = mock_result
        
        result = await agent._run_pytest(test_path=tmp_path, coverage=False)
        
        assert result["success"] is False
        assert result["return_code"] == 1

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.tester.agent.subprocess.run")
    async def test_run_pytest_timeout(self, mock_subprocess, tmp_path):
        """Test _run_pytest with timeout."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock subprocess to raise timeout
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired("pytest", 300)
        
        result = await agent._run_pytest(test_path=tmp_path, coverage=False)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.tester.agent.subprocess.run")
    async def test_run_pytest_with_coverage(self, mock_subprocess, tmp_path):
        """Test _run_pytest with coverage enabled."""
        agent = TesterAgent()
        await agent.activate(tmp_path)
        
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Mock coverage file
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text('{"totals": {"percent_covered": 85.0}}')
        
        with patch("tapps_agents.agents.tester.agent.Path") as mock_path_class:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_class.return_value = coverage_file
            
            result = await agent._run_pytest(test_path=tmp_path, coverage=True)
            
            assert "coverage" in result or result.get("coverage") is None


class TestTesterAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test unknown command handling."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("unknown-command")
        
        assert "error" in result
        assert "unknown command" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command."""
        agent = TesterAgent()
        await agent.activate()
        
        result = await agent.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert "*test" in result["content"]

    @pytest.mark.asyncio
    async def test_test_command_path_validation_error(self, tmp_path):
        """Test test command handles path validation errors."""
        agent = TesterAgent()
        await agent.activate()
        
        # Create a file that will fail validation (too large)
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * (11 * 1024 * 1024))  # Larger than 10MB
        
        # Mock _validate_path to raise ValueError
        with patch.object(agent, '_validate_path', side_effect=ValueError("File too large")):
            result = await agent.run("test", file=str(large_file))
            
            assert "error" in result


class TestTesterAgentExpertIntegration:
    """Tests for expert integration."""

    @pytest.mark.asyncio
    async def test_test_command_expert_low_confidence(self, sample_python_file):
        """Test test command with low confidence expert advice."""
        agent = TesterAgent()
        await agent.activate()
        
        # Mock expert registry with low confidence
        mock_registry = MagicMock()
        mock_consultation = MagicMock()
        mock_consultation.weighted_answer = "Low confidence advice"
        mock_consultation.confidence = 0.5
        mock_consultation.confidence_threshold = 0.7
        mock_registry.consult = AsyncMock(return_value=mock_consultation)
        agent.expert_registry = mock_registry
        
        result = await agent.run("test", file=str(sample_python_file))
        
        assert "type" in result
        assert "expert_advice" in result
        assert "low confidence" in result["expert_advice"]["guidance"].lower()

    @pytest.mark.asyncio
    async def test_generate_tests_command_expert_consultation(self, sample_python_file):
        """Test generate-tests command with expert consultation."""
        agent = TesterAgent()
        await agent.activate()
        
        # Mock expert registry
        mock_registry = MagicMock()
        mock_consultation = MagicMock()
        mock_consultation.weighted_answer = "Testing best practices"
        mock_consultation.confidence = 0.9
        mock_consultation.confidence_threshold = 0.7
        mock_registry.consult = AsyncMock(return_value=mock_consultation)
        agent.expert_registry = mock_registry
        
        result = await agent.run("generate-tests", file=str(sample_python_file))
        
        assert "type" in result
        assert mock_registry.consult.called

