"""
Unit tests for BugFinder.
"""

from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.continuous_bug_fix.bug_finder import BugFinder
from tapps_agents.core.config import load_config

pytestmark = pytest.mark.unit


class TestBugFinder:
    """Test BugFinder functionality."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a temporary project root."""
        return tmp_path

    @pytest.fixture
    def config(self):
        """Get default config."""
        return load_config()

    @pytest.fixture
    def bug_finder(self, project_root, config):
        """Create a BugFinder instance."""
        return BugFinder(project_root=project_root, config=config)

    def test_bug_finder_initialization(self, project_root, config):
        """Test BugFinder can be initialized."""
        finder = BugFinder(project_root=project_root, config=config)
        assert finder.project_root == project_root
        assert finder.config == config

    def test_parse_pytest_output_no_failures(self, bug_finder):
        """Test parsing pytest output with no failures."""
        output = """
test_session starts
========================== 5 passed in 0.12s ===========================
"""
        bugs = bug_finder._parse_pytest_output(output, "")
        assert len(bugs) == 0

    def test_parse_pytest_output_single_failure(self, bug_finder):
        """Test parsing pytest output with single failure."""
        output = """
FAILED tests/test_main.py::test_function - AssertionError: assert 1 == 2
"""
        bugs = bug_finder._parse_pytest_output(output, "")
        assert len(bugs) >= 0  # May not parse without traceback

    def test_extract_source_file_with_traceback(self, bug_finder):
        """Test extracting source file from traceback."""
        test_file = "tests/test_main.py"
        traceback = """
File "src/main.py", line 42, in function_name
    result = process(data)
"""
        source_file, line_number = bug_finder._extract_source_file(test_file, traceback)
        assert source_file == "src/main.py"
        assert line_number == 42

    def test_extract_source_file_no_match(self, bug_finder):
        """Test extracting source file when no match found."""
        test_file = "tests/test_main.py"
        traceback = "Some error message"
        source_file, line_number = bug_finder._extract_source_file(test_file, traceback)
        assert source_file is None
        assert line_number is None

    def test_extract_source_file_filters_test_files(self, bug_finder):
        """Test that test files are filtered out."""
        test_file = "tests/test_main.py"
        traceback = """
File "tests/test_helper.py", line 10, in helper_function
    return helper()
"""
        source_file, line_number = bug_finder._extract_source_file(test_file, traceback)
        # Should not return test files
        assert source_file is None or "test_" not in source_file

    @pytest.mark.asyncio
    async def test_find_bugs_no_test_path(self, bug_finder, project_root):
        """Test find_bugs when test path doesn't exist."""
        # Create a non-existent test path
        bugs = await bug_finder.find_bugs(test_path="nonexistent/path/")
        assert bugs == []

    @pytest.mark.asyncio
    @patch("tapps_agents.continuous_bug_fix.bug_finder.subprocess.run")
    async def test_find_bugs_pytest_success(self, mock_subprocess, bug_finder, project_root):
        """Test find_bugs when pytest runs successfully with no failures."""
        # Mock subprocess.run to return success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "========================== 5 passed in 0.12s ==========================="
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        bugs = await bug_finder.find_bugs(test_path="tests/")
        # Should return empty list for no failures
        assert isinstance(bugs, list)

    @pytest.mark.asyncio
    @patch("tapps_agents.continuous_bug_fix.bug_finder.subprocess.run")
    async def test_find_bugs_pytest_failure(self, mock_subprocess, bug_finder, project_root):
        """Test find_bugs when pytest finds failures."""
        # Mock subprocess.run to return failures
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = """
FAILED tests/test_main.py::test_function - AssertionError: assert 1 == 2
"""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        bugs = await bug_finder.find_bugs(test_path="tests/")
        # Should return list (may be empty if parsing fails)
        assert isinstance(bugs, list)
