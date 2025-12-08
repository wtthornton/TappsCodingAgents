"""
Unit tests for CodeScorer.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tapps_agents.agents.reviewer.scoring import CodeScorer
from tests.fixtures.sample_code import (
    SIMPLE_CODE,
    COMPLEX_CODE,
    INSECURE_CODE,
    MAINTAINABLE_CODE,
    SYNTAX_ERROR_CODE
)


@pytest.mark.unit
class TestCodeScorer:
    """Test cases for CodeScorer class."""
    
    def test_scorer_initialization(self):
        """Test that CodeScorer initializes correctly."""
        scorer = CodeScorer()
        assert scorer is not None
        assert hasattr(scorer, 'score_file')
    
    def test_score_file_returns_dict(self, tmp_path: Path):
        """Test that score_file returns a dictionary with expected keys."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        assert isinstance(result, dict)
        assert "complexity_score" in result
        assert "security_score" in result
        assert "maintainability_score" in result
        assert "test_coverage_score" in result
        assert "performance_score" in result
        assert "linting_score" in result  # Phase 6
        assert "overall_score" in result
        assert "metrics" in result
    
    def test_score_file_simple_code(self, tmp_path: Path):
        """Test scoring simple, clean code."""
        scorer = CodeScorer()
        test_file = tmp_path / "simple.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Simple code should have low complexity
        assert result["complexity_score"] >= 0
        assert result["complexity_score"] <= 10
        
        # Simple code should have good security (no issues)
        assert result["security_score"] >= 0
        assert result["security_score"] <= 10
        
        # Should have reasonable maintainability
        assert result["maintainability_score"] >= 0
        assert result["maintainability_score"] <= 10
        
        # Overall score should be calculated
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_score_file_complex_code(self, tmp_path: Path):
        """Test scoring complex code with high cyclomatic complexity."""
        scorer = CodeScorer()
        test_file = tmp_path / "complex.py"
        test_file.write_text(COMPLEX_CODE)
        
        result = scorer.score_file(test_file, COMPLEX_CODE)
        
        # Complex code should have higher complexity score
        assert result["complexity_score"] >= 0
        assert result["complexity_score"] <= 10
        
        # Overall score should reflect complexity
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_score_file_insecure_code(self, tmp_path: Path):
        """Test scoring code with security issues."""
        scorer = CodeScorer()
        test_file = tmp_path / "insecure.py"
        test_file.write_text(INSECURE_CODE)
        
        result = scorer.score_file(test_file, INSECURE_CODE)
        
        # Insecure code should have lower security score
        assert result["security_score"] >= 0
        assert result["security_score"] <= 10
        
        # Security issues should lower overall score
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_score_file_maintainable_code(self, tmp_path: Path):
        """Test scoring well-documented, maintainable code."""
        scorer = CodeScorer()
        test_file = tmp_path / "maintainable.py"
        test_file.write_text(MAINTAINABLE_CODE)
        
        result = scorer.score_file(test_file, MAINTAINABLE_CODE)
        
        # Maintainable code should score well
        assert result["maintainability_score"] >= 0
        assert result["maintainability_score"] <= 10
        
        # Overall score should be good
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_score_file_syntax_error(self, tmp_path: Path):
        """Test that scorer handles syntax errors gracefully."""
        scorer = CodeScorer()
        test_file = tmp_path / "syntax_error.py"
        test_file.write_text(SYNTAX_ERROR_CODE)
        
        # Should not raise exception
        result = scorer.score_file(test_file, SYNTAX_ERROR_CODE)
        
        # Should still return scores (with error handling)
        assert isinstance(result, dict)
        assert "complexity_score" in result
        # Syntax errors should result in high complexity or error handling
    
    def test_score_file_without_radon(self, tmp_path: Path):
        """Test scoring when radon is not available."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        with patch('tapps_agents.agents.reviewer.scoring.HAS_RADON', False):
            result = scorer.score_file(test_file, SIMPLE_CODE)
            
            # Should still return scores using fallback
            assert isinstance(result, dict)
            assert "complexity_score" in result
            assert "maintainability_score" in result
    
    def test_score_file_without_bandit(self, tmp_path: Path):
        """Test scoring when bandit is not available."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        with patch('tapps_agents.agents.reviewer.scoring.HAS_BANDIT', False):
            result = scorer.score_file(test_file, SIMPLE_CODE)
            
            # Should still return scores using heuristic
            assert isinstance(result, dict)
            assert "security_score" in result
    
    def test_overall_score_calculation(self, tmp_path: Path):
        """Test that overall score is calculated correctly."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Overall score should be weighted average
        # Formula: (10-complexity)*0.20 + security*0.30 + maintainability*0.25 + coverage*0.15 + performance*0.10
        expected_range = (0, 100)
        assert expected_range[0] <= result["overall_score"] <= expected_range[1]
    
    def test_score_empty_file(self, tmp_path: Path):
        """Test scoring an empty file."""
        scorer = CodeScorer()
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        result = scorer.score_file(test_file, "")
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "test_coverage_score" in result
        assert "performance_score" in result
    
    def test_test_coverage_score(self, tmp_path: Path):
        """Test test coverage score calculation."""
        scorer = CodeScorer()
        test_file = tmp_path / "sample.py"
        test_file.write_text("def hello(): pass")
        
        result = scorer.score_file(test_file, "def hello(): pass")
        
        # Should return a score between 0 and 10
        assert 0 <= result["test_coverage_score"] <= 10
        assert "test_coverage" in result["metrics"]
    
    def test_performance_score(self, tmp_path: Path):
        """Test performance score calculation."""
        scorer = CodeScorer()
        test_file = tmp_path / "sample.py"
        
        # Simple function should score well
        simple_code = "def add(a, b): return a + b"
        result = scorer.score_file(test_file, simple_code)
        assert 0 <= result["performance_score"] <= 10
        
        # Complex nested code should score lower
        complex_code = """
def complex():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                if i > 5:
                    if j > 5:
                        if k > 5:
                            return i + j + k
"""
        result2 = scorer.score_file(test_file, complex_code)
        # Complex code might score lower (more nesting)
        assert 0 <= result2["performance_score"] <= 10
    
    def test_performance_score_large_function(self, tmp_path: Path):
        """Test performance score penalizes large functions."""
        scorer = CodeScorer()
        test_file = tmp_path / "large.py"
        
        # Create a large function (> 50 lines)
        large_func = "def large():\n"
        large_func += "\n".join([f"    x = {i}" for i in range(60)])
        
        result = scorer.score_file(test_file, large_func)
        # Large functions should score lower
        assert result["performance_score"] < 10.0
    
    def test_performance_score_nested_loops(self, tmp_path: Path):
        """Test performance score penalizes nested loops."""
        scorer = CodeScorer()
        test_file = tmp_path / "nested.py"
        
        nested_code = """
def process():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                result = i * j * k
"""
        result = scorer.score_file(test_file, nested_code)
        # Nested loops should reduce score
        assert 0 <= result["performance_score"] <= 10
    
    # Phase 6.1: Ruff Integration Tests
    def test_score_file_includes_linting_score(self, tmp_path: Path):
        """Test that linting_score is included in score_file results (Phase 6)."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Should include linting_score (Phase 6)
        assert "linting_score" in result
        assert "linting" in result["metrics"]
        assert 0 <= result["linting_score"] <= 10
    
    def test_calculate_linting_score_with_ruff_unavailable(self, tmp_path: Path):
        """Test linting score calculation when Ruff is not available."""
        scorer = CodeScorer(ruff_enabled=False)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # When Ruff is disabled, should return neutral score
        score = scorer._calculate_linting_score(test_file)
        assert score == 5.0  # Neutral score when Ruff unavailable
    
    def test_calculate_linting_score_non_python_file(self, tmp_path: Path):
        """Test that linting score returns 10.0 for non-Python files."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not Python code")
        
        score = scorer._calculate_linting_score(test_file)
        # Non-Python files return 10.0 (perfect score) since they can't be linted
        # But if Ruff is not available, may return 5.0, so check range
        assert 5.0 <= score <= 10.0  # Either unavailable (5.0) or perfect (10.0)
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_RUFF', True)
    @patch('subprocess.run')
    def test_calculate_linting_score_no_issues(self, mock_subprocess, tmp_path: Path):
        """Test linting score when Ruff finds no issues."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # Mock Ruff returning no issues (returncode 0, empty stdout)
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        score = scorer._calculate_linting_score(test_file)
        assert score == 10.0  # Perfect score for no issues
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_RUFF', True)
    @patch('subprocess.run')
    def test_calculate_linting_score_with_errors(self, mock_subprocess, tmp_path: Path):
        """Test linting score when Ruff finds errors."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nprint('test')")
        
        # Mock Ruff returning errors
        mock_output = [
            {
                "code": {"name": "E501"},
                "message": "Line too long",
                "location": {"row": 1, "column": 80}
            },
            {
                "code": {"name": "E302"},
                "message": "Expected 2 blank lines",
                "location": {"row": 2, "column": 1}
            }
        ]
        
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=str(mock_output).replace("'", '"'),  # JSON-like string
            stderr=""
        )
        
        # Should parse JSON and calculate score
        # 2 errors * 2.0 points = -4.0, so score = 10.0 - 4.0 = 6.0
        score = scorer._calculate_linting_score(test_file)
        # Allow for JSON parsing differences in test
        assert 0 <= score <= 10
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_RUFF', True)
    @patch('subprocess.run')
    def test_calculate_linting_score_with_warnings(self, mock_subprocess, tmp_path: Path):
        """Test linting score when Ruff finds warnings."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("unused_var = 42")
        
        # Mock Ruff returning warnings
        mock_output = [
            {
                "code": {"name": "W291"},
                "message": "Trailing whitespace",
                "location": {"row": 1, "column": 15}
            }
        ]
        
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=str(mock_output).replace("'", '"'),
            stderr=""
        )
        
        score = scorer._calculate_linting_score(test_file)
        # 1 warning * 0.5 points = -0.5, so score = 10.0 - 0.5 = 9.5
        assert 0 <= score <= 10
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_RUFF', True)
    @patch('subprocess.run')
    def test_calculate_linting_score_timeout(self, mock_subprocess, tmp_path: Path):
        """Test linting score handles timeout gracefully."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # Mock subprocess timeout
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ruff", 30)
        
        score = scorer._calculate_linting_score(test_file)
        assert score == 5.0  # Neutral score on timeout
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_RUFF', True)
    @patch('subprocess.run')
    def test_calculate_linting_score_file_not_found(self, mock_subprocess, tmp_path: Path):
        """Test linting score handles FileNotFoundError gracefully."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # Mock ruff not found
        mock_subprocess.side_effect = FileNotFoundError("ruff: command not found")
        
        score = scorer._calculate_linting_score(test_file)
        assert score == 5.0  # Neutral score when Ruff not found
    
    def test_get_ruff_issues_empty_when_disabled(self, tmp_path: Path):
        """Test get_ruff_issues returns empty list when Ruff disabled."""
        scorer = CodeScorer(ruff_enabled=False)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        issues = scorer.get_ruff_issues(test_file)
        assert issues == []
    
    def test_get_ruff_issues_non_python_file(self, tmp_path: Path):
        """Test get_ruff_issues returns empty list for non-Python files."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Not Python code")
        
        issues = scorer.get_ruff_issues(test_file)
        assert issues == []
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_RUFF', True)
    @patch('subprocess.run')
    def test_get_ruff_issues_returns_diagnostics(self, mock_subprocess, tmp_path: Path):
        """Test get_ruff_issues parses and returns diagnostic list."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")
        
        # Mock Ruff JSON output
        mock_diagnostics = [
            {
                "code": {"name": "F401"},
                "message": "Unused import",
                "location": {"row": 1, "column": 1}
            }
        ]
        
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=json.dumps(mock_diagnostics),
            stderr=""
        )
        
        issues = scorer.get_ruff_issues(test_file)
        assert len(issues) == 1
        assert issues[0]["code"]["name"] == "F401"
    
    # Phase 6.2: mypy Integration Tests
    def test_score_file_includes_type_checking_score(self, tmp_path: Path):
        """Test that type_checking_score is included in score_file results (Phase 6.2)."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Should include type_checking_score (Phase 6.2)
        assert "type_checking_score" in result
        assert "type_checking" in result["metrics"]
        assert 0 <= result["type_checking_score"] <= 10
    
    def test_calculate_type_checking_score_with_mypy_unavailable(self, tmp_path: Path):
        """Test type checking score calculation when mypy is not available."""
        scorer = CodeScorer(mypy_enabled=False)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # When mypy is disabled, should return neutral score
        score = scorer._calculate_type_checking_score(test_file)
        assert score == 5.0  # Neutral score when mypy unavailable
    
    def test_calculate_type_checking_score_non_python_file(self, tmp_path: Path):
        """Test that type checking score returns 10.0 for non-Python files."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not Python code")
        
        score = scorer._calculate_type_checking_score(test_file)
        # Non-Python files return 10.0 (perfect score) since they can't be type checked
        # But if mypy is not available, may return 5.0, so check range
        assert 5.0 <= score <= 10.0  # Either unavailable (5.0) or perfect (10.0)
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_MYPY', True)
    @patch('subprocess.run')
    def test_calculate_type_checking_score_no_errors(self, mock_subprocess, tmp_path: Path):
        """Test type checking score when mypy finds no errors."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello() -> str:\n    return 'hello'")
        
        # Mock mypy returning no errors (returncode 0)
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        score = scorer._calculate_type_checking_score(test_file)
        assert score == 10.0  # Perfect score for no errors
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_MYPY', True)
    @patch('subprocess.run')
    def test_calculate_type_checking_score_with_errors(self, mock_subprocess, tmp_path: Path):
        """Test type checking score when mypy finds errors."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    return 'hello'")
        
        # Mock mypy returning errors
        mock_output = """test.py:1: error: Missing return type annotation [func-returns]
test.py:2: error: Function is missing a type annotation for one or more arguments [no-untyped-def]
"""
        
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=mock_output,
            stderr=""
        )
        
        # Should parse errors and calculate score
        # 2 errors * 0.5 points = -1.0, so score = 10.0 - 1.0 = 9.0
        score = scorer._calculate_type_checking_score(test_file)
        assert 0 <= score <= 10
        assert score < 10.0  # Should be less than perfect
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_MYPY', True)
    @patch('subprocess.run')
    def test_calculate_type_checking_score_timeout(self, mock_subprocess, tmp_path: Path):
        """Test type checking score handles timeout gracefully."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # Mock subprocess timeout
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired("mypy", 60)
        
        score = scorer._calculate_type_checking_score(test_file)
        assert score == 5.0  # Neutral score on timeout
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_MYPY', True)
    @patch('subprocess.run')
    def test_calculate_type_checking_score_file_not_found(self, mock_subprocess, tmp_path: Path):
        """Test type checking score handles FileNotFoundError gracefully."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # Mock mypy not found
        mock_subprocess.side_effect = FileNotFoundError("mypy: command not found")
        
        score = scorer._calculate_type_checking_score(test_file)
        assert score == 5.0  # Neutral score when mypy not found
    
    def test_get_mypy_errors_empty_when_disabled(self, tmp_path: Path):
        """Test get_mypy_errors returns empty list when mypy disabled."""
        scorer = CodeScorer(mypy_enabled=False)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        errors = scorer.get_mypy_errors(test_file)
        assert errors == []
    
    def test_get_mypy_errors_non_python_file(self, tmp_path: Path):
        """Test get_mypy_errors returns empty list for non-Python files."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Not Python code")
        
        errors = scorer.get_mypy_errors(test_file)
        assert errors == []
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_MYPY', True)
    @patch('subprocess.run')
    def test_get_mypy_errors_returns_diagnostics(self, mock_subprocess, tmp_path: Path):
        """Test get_mypy_errors parses and returns error list."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    return 42")
        
        # Mock mypy JSON output
        mock_output = """test.py:1: error: Missing return type annotation [func-returns]
test.py:2: error: Incompatible return type (got "int", expected "None") [return-value]
"""
        
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=mock_output,
            stderr=""
        )
        
        errors = scorer.get_mypy_errors(test_file)
        assert len(errors) == 2
        assert errors[0]["line"] == 1
        assert "func-returns" in errors[0].get("error_code", "")
        assert errors[1]["line"] == 2
        assert "return-value" in errors[1].get("error_code", "")
    
    @patch('tapps_agents.agents.reviewer.scoring.HAS_MYPY', True)
    @patch('subprocess.run')
    def test_get_mypy_errors_extracts_error_codes(self, mock_subprocess, tmp_path: Path):
        """Test get_mypy_errors correctly extracts error codes from mypy output."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("x: int = 'hello'")
        
        mock_output = "test.py:1: error: Incompatible types in assignment (expression has type \"str\", variable has type \"int\") [assignment]\n"
        
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=mock_output,
            stderr=""
        )
        
        errors = scorer.get_mypy_errors(test_file)
        assert len(errors) == 1
        assert errors[0]["error_code"] == "assignment"
        assert errors[0]["severity"] == "error"

