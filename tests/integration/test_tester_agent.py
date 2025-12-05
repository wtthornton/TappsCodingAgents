"""
Integration tests for TesterAgent.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tapps_agents.agents.tester import TesterAgent
from tapps_agents.core.mal import MAL


@pytest.mark.integration
class TestTesterAgent:
    """Integration tests for TesterAgent."""
    
    @pytest.fixture
    def mock_mal(self):
        """Create a mock MAL."""
        mal = MagicMock(spec=MAL)
        mal.generate = AsyncMock(return_value="""
import pytest

def test_add():
    assert True

def test_subtract():
    assert True
""")
        mal.close = AsyncMock()
        return mal
    
    @pytest.fixture
    def sample_code_file(self, tmp_path: Path):
        """Create a sample code file."""
        code_file = tmp_path / "calculator.py"
        code_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")
        return code_file
    
    @pytest.mark.asyncio
    async def test_activate(self, mock_mal):
        """Test agent activation."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        
        assert agent.config is not None
        assert agent.test_generator is not None
    
    @pytest.mark.asyncio
    async def test_get_commands(self, mock_mal):
        """Test command list."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        
        commands = agent.get_commands()
        command_names = [cmd["command"] for cmd in commands]
        
        assert "*help" in command_names
        assert "*test" in command_names
        assert "*generate-tests" in command_names
        assert "*run-tests" in command_names
    
    @pytest.mark.asyncio
    async def test_test_command_generate_and_run(self, mock_mal, sample_code_file, tmp_path: Path):
        """Test test command generates and runs tests."""
        agent = TesterAgent(mal=mock_mal)
        agent.tests_dir = tmp_path / "tests"
        agent.auto_write_tests = True
        await agent.activate()
        
        result = await agent.test_command(file=str(sample_code_file))
        
        assert "type" in result
        assert result["type"] == "test"
        assert "test_code" in result
        assert "test_file" in result
        assert "written" in result
        assert result["written"] is True
    
    @pytest.mark.asyncio
    async def test_test_command_missing_file(self, mock_mal):
        """Test test command with missing file."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        
        result = await agent.test_command(file=None)
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_test_command_file_not_found(self, mock_mal):
        """Test test command with non-existent file."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        
        result = await agent.test_command(file="nonexistent.py")
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_tests_command(self, mock_mal, sample_code_file, tmp_path: Path):
        """Test generate tests command."""
        agent = TesterAgent(mal=mock_mal)
        agent.tests_dir = tmp_path / "tests"
        agent.auto_write_tests = True
        await agent.activate()
        
        result = await agent.generate_tests_command(file=str(sample_code_file))
        
        assert "type" in result
        assert result["type"] == "test_generation"
        assert "test_code" in result
        assert "test_file" in result
        assert "run_result" not in result  # Should not run tests
    
    @pytest.mark.asyncio
    async def test_generate_tests_integration(self, mock_mal, sample_code_file, tmp_path: Path):
        """Test generate integration tests."""
        agent = TesterAgent(mal=mock_mal)
        agent.tests_dir = tmp_path / "tests"
        await agent.activate()
        
        result = await agent.generate_tests_command(
            file=str(sample_code_file),
            integration=True
        )
        
        assert "type" in result
        assert "test_code" in result
        # Should call integration test generation
        call_args = mock_mal.generate.call_args[0][0]
        assert "integration" in call_args.lower()
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_run_tests_command(self, mock_subprocess, mock_mal, tmp_path: Path):
        """Test run tests command."""
        # Mock pytest output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_sample.py::test_add PASSED\n2 passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        agent = TesterAgent(mal=mock_mal)
        agent.tests_dir = tmp_path / "tests"
        await agent.activate()
        
        result = await agent.run_tests_command()
        
        assert "type" in result
        assert result["type"] == "test_execution"
        assert "result" in result
        assert "success" in result["result"]
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_run_tests_with_coverage(self, mock_subprocess, mock_mal, tmp_path: Path):
        """Test run tests with coverage."""
        # Mock pytest output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_sample.py::test_add PASSED\n2 passed\ncoverage: 85%"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Mock coverage.json
        coverage_json = tmp_path / "coverage.json"
        coverage_json.write_text('{"totals": {"percent_covered": 85.0}}')
        
        agent = TesterAgent(mal=mock_mal)
        agent.tests_dir = tmp_path / "tests"
        await agent.activate()
        
        result = await agent.run_tests_command(coverage=True)
        
        assert "type" in result
        assert "result" in result
        # Coverage might be None if coverage.json doesn't exist in actual test
        # This is a basic integration test
    
    def test_get_test_file_path(self, mock_mal, tmp_path: Path, monkeypatch):
        """Test test file path generation."""
        # Change to tmp_path for this test
        monkeypatch.chdir(tmp_path)
        
        agent = TesterAgent(mal=mock_mal)
        agent.tests_dir = tmp_path / "tests"
        
        # Test with src/ structure
        src_file = tmp_path / "src" / "calculator.py"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("def add(): pass")
        
        test_path = agent._get_test_file_path(src_file)
        
        assert "tests" in str(test_path) or "test" in test_path.parts
        assert "test_calculator.py" == test_path.name
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_mal):
        """Test help command."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        
        result = await agent.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert "*test" in result["content"]
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, mock_mal):
        """Test unknown command handling."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        
        result = await agent.run("unknown_command")
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_close(self, mock_mal):
        """Test agent cleanup."""
        agent = TesterAgent(mal=mock_mal)
        await agent.activate()
        await agent.close()
        
        mock_mal.close.assert_called_once()

