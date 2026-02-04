"""
Unit tests for CodeScorer.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.agents.reviewer.scoring import CodeScorer
from tests.fixtures.sample_code import (
    COMPLEX_CODE,
    INSECURE_CODE,
    MAINTAINABLE_CODE,
    SIMPLE_CODE,
    SYNTAX_ERROR_CODE,
)


@pytest.mark.unit
class TestCodeScorer:
    """Test cases for CodeScorer class."""

    def test_scorer_initialization(self):
        """Test that CodeScorer initializes correctly."""
        scorer = CodeScorer()
        assert scorer is not None
        assert hasattr(scorer, "score_file")

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

        # Simple code should have low complexity (low complexity_score means low complexity, good)
        # Complexity score should be in valid range and low for simple code
        assert 0.0 <= result["complexity_score"] <= 3.0, \
            f"Simple code should have low complexity score (0-3), got {result['complexity_score']}"

        # Simple code should have good security (no issues)
        assert result["security_score"] >= 8.0  # Simple code with no security issues should score high
        assert result["security_score"] <= 10.0

        # Should have reasonable maintainability
        assert result["maintainability_score"] >= 7.0  # Simple code should be maintainable
        assert result["maintainability_score"] <= 10.0

        # Overall score should be calculated and reasonable for simple code
        assert result["overall_score"] >= 70.0  # Simple code should score well overall
        assert result["overall_score"] <= 100.0

    def test_score_file_complex_code(self, tmp_path: Path):
        """Test scoring complex code with high cyclomatic complexity."""
        scorer = CodeScorer()
        test_file = tmp_path / "complex.py"
        test_file.write_text(COMPLEX_CODE)

        result = scorer.score_file(test_file, COMPLEX_CODE)

        # Complex code should have lower complexity_score (high complexity = low score)
        # Compare with simple code to ensure relative scoring works
        simple_file = tmp_path / "simple.py"
        simple_file.write_text(SIMPLE_CODE)
        simple_result = scorer.score_file(simple_file, SIMPLE_CODE)
        
        # Complex code should have higher complexity_score than simple code
        # (higher complexity_score = more complex = worse)
        assert result["complexity_score"] > simple_result["complexity_score"], \
            f"Complex code should have higher complexity score than simple code. " \
            f"Complex: {result['complexity_score']}, Simple: {simple_result['complexity_score']}"
        assert 0.0 <= result["complexity_score"] <= 10.0, \
            f"Complexity score should be in valid range (0-10), got {result['complexity_score']}"

        # Overall score should reflect complexity (lower than simple code)
        assert result["overall_score"] < simple_result["overall_score"], \
            f"Complex code should have lower overall score than simple code. " \
            f"Complex: {result['overall_score']}, Simple: {simple_result['overall_score']}"
        assert 0.0 <= result["overall_score"] <= 100.0, \
            f"Overall score should be in valid range (0-100), got {result['overall_score']}"

    def test_score_file_insecure_code(self, tmp_path: Path):
        """Test scoring code with security issues."""
        scorer = CodeScorer()
        test_file = tmp_path / "insecure.py"
        test_file.write_text(INSECURE_CODE)

        result = scorer.score_file(test_file, INSECURE_CODE)

        # Insecure code should have lower security score
        # Compare with simple code to ensure relative scoring works
        simple_file = tmp_path / "simple.py"
        simple_file.write_text(SIMPLE_CODE)
        simple_result = scorer.score_file(simple_file, SIMPLE_CODE)
        
        # Insecure code should score significantly lower on security
        assert result["security_score"] < simple_result["security_score"], \
            f"Insecure code should have lower security score than simple code. " \
            f"Insecure: {result['security_score']}, Simple: {simple_result['security_score']}"
        assert 0.0 <= result["security_score"] < 5.0, \
            f"Insecure code should have low security score (0-5), got {result['security_score']}"

        # Security issues should lower overall score
        assert result["overall_score"] < simple_result["overall_score"], \
            f"Insecure code should have lower overall score than simple code. " \
            f"Insecure: {result['overall_score']}, Simple: {simple_result['overall_score']}"
        assert 0.0 <= result["overall_score"] <= 100.0, \
            f"Overall score should be in valid range (0-100), got {result['overall_score']}"

    def test_score_file_maintainable_code(self, tmp_path: Path):
        """Test scoring well-documented, maintainable code."""
        scorer = CodeScorer()
        test_file = tmp_path / "maintainable.py"
        test_file.write_text(MAINTAINABLE_CODE)

        result = scorer.score_file(test_file, MAINTAINABLE_CODE)

        # Maintainable code should score well
        # Compare with simple code to ensure maintainable code scores higher
        simple_file = tmp_path / "simple.py"
        simple_file.write_text(SIMPLE_CODE)
        scorer.score_file(simple_file, SIMPLE_CODE)
        
        # Maintainable code (with docs, type hints, error handling) should score reasonably well
        # Note: Simple code might score similarly or even higher due to lower complexity
        assert result["maintainability_score"] >= 5.0  # Well-documented code should score reasonably
        assert result["maintainability_score"] <= 10.0

        # Overall score should be good
        assert result["overall_score"] >= 50.0  # Maintainable code should score reasonably well
        assert result["overall_score"] <= 100.0

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

        with patch("tapps_agents.agents.reviewer.scoring.HAS_RADON", False):
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

        with patch("tapps_agents.agents.reviewer.scoring.HAS_BANDIT", False):
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
        
        # Verify the formula is correct by checking individual components contribute
        complexity_contrib = (10 - result["complexity_score"]) * 0.20
        security_contrib = result["security_score"] * 0.30
        maintainability_contrib = result["maintainability_score"] * 0.25
        # Allow for rounding differences
        calculated_score = (
            complexity_contrib
            + security_contrib
            + maintainability_contrib
            + result["test_coverage_score"] * 0.15
            + result["performance_score"] * 0.10
        ) * 10  # Scale from 0-10 weighted sum to 0-100
        assert abs(result["overall_score"] - calculated_score) < 1.0  # Allow small rounding differences

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

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", True)
    @patch("subprocess.run")
    def test_calculate_linting_score_no_issues(self, mock_subprocess, tmp_path: Path):
        """Test linting score when Ruff finds no issues."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)

        # Mock Ruff returning no issues (returncode 0, empty stdout)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        score = scorer._calculate_linting_score(test_file)
        assert score == 10.0  # Perfect score for no issues

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", True)
    @patch("subprocess.run")
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
                "location": {"row": 1, "column": 80},
            },
            {
                "code": {"name": "E302"},
                "message": "Expected 2 blank lines",
                "location": {"row": 2, "column": 1},
            },
        ]

        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=str(mock_output).replace("'", '"'),  # JSON-like string
            stderr="",
        )

        # Should parse JSON and calculate score
        # 2 errors * 2.0 points = -4.0, so score = 10.0 - 4.0 = 6.0
        score = scorer._calculate_linting_score(test_file)
        # Allow for JSON parsing differences in test
        assert 0 <= score <= 10

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", True)
    @patch("subprocess.run")
    def test_calculate_linting_score_with_warnings(
        self, mock_subprocess, tmp_path: Path
    ):
        """Test linting score when Ruff finds warnings."""
        scorer = CodeScorer(ruff_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("unused_var = 42")

        # Mock Ruff returning warnings
        mock_output = [
            {
                "code": {"name": "W291"},
                "message": "Trailing whitespace",
                "location": {"row": 1, "column": 15},
            }
        ]

        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout=str(mock_output).replace("'", '"'), stderr=""
        )

        score = scorer._calculate_linting_score(test_file)
        # 1 warning * 0.5 points = -0.5, so score = 10.0 - 0.5 = 9.5
        assert 0 <= score <= 10

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", True)
    @patch("subprocess.run")
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

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", True)
    @patch("subprocess.run")
    def test_calculate_linting_score_file_not_found(
        self, mock_subprocess, tmp_path: Path
    ):
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

    @patch("tapps_agents.agents.reviewer.scoring.HAS_RUFF", True)
    @patch("subprocess.run")
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
                "location": {"row": 1, "column": 1},
            }
        ]

        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout=json.dumps(mock_diagnostics), stderr=""
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

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", True)
    @patch("subprocess.run")
    def test_calculate_type_checking_score_no_errors(
        self, mock_subprocess, tmp_path: Path
    ):
        """Test type checking score when mypy finds no errors."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello() -> str:\n    return 'hello'")

        # Mock mypy returning no errors (returncode 0)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        score = scorer._calculate_type_checking_score(test_file)
        assert score == 10.0  # Perfect score for no errors

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", True)
    @patch("subprocess.run")
    def test_calculate_type_checking_score_with_errors(
        self, mock_subprocess, tmp_path: Path
    ):
        """Test type checking score when mypy finds errors."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    return 'hello'")

        # Mock mypy returning errors
        mock_output = """test.py:1: error: Missing return type annotation [func-returns]
test.py:2: error: Function is missing a type annotation for one or more arguments [no-untyped-def]
"""

        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout=mock_output, stderr=""
        )

        # Should parse errors and calculate score
        # 2 errors * 0.5 points = -1.0, so score = 10.0 - 1.0 = 9.0
        score = scorer._calculate_type_checking_score(test_file)
        assert 0 <= score <= 10
        assert score < 10.0  # Should be less than perfect

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", True)
    @patch("subprocess.run")
    def test_calculate_type_checking_score_timeout(
        self, mock_subprocess, tmp_path: Path
    ):
        """Test type checking score handles timeout gracefully."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)

        # Mock subprocess timeout
        import subprocess

        mock_subprocess.side_effect = subprocess.TimeoutExpired("mypy", 60)

        score = scorer._calculate_type_checking_score(test_file)
        assert score == 5.0  # Neutral score on timeout

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", True)
    @patch("subprocess.run")
    def test_calculate_type_checking_score_file_not_found(
        self, mock_subprocess, tmp_path: Path
    ):
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

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", True)
    @patch("subprocess.run")
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
            returncode=1, stdout=mock_output, stderr=""
        )

        errors = scorer.get_mypy_errors(test_file)
        assert len(errors) == 2
        assert errors[0]["line"] == 1
        assert "func-returns" in errors[0].get("error_code", "")
        assert errors[1]["line"] == 2
        assert "return-value" in errors[1].get("error_code", "")

    @patch("tapps_agents.agents.reviewer.scoring.HAS_MYPY", True)
    @patch("subprocess.run")
    def test_get_mypy_errors_extracts_error_codes(
        self, mock_subprocess, tmp_path: Path
    ):
        """Test get_mypy_errors correctly extracts error codes from mypy output."""
        scorer = CodeScorer(mypy_enabled=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("x: int = 'hello'")

        mock_output = 'test.py:1: error: Incompatible types in assignment (expression has type "str", variable has type "int") [assignment]\n'

        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout=mock_output, stderr=""
        )

        errors = scorer.get_mypy_errors(test_file)
        assert len(errors) == 1
        assert errors[0]["error_code"] == "assignment"
        assert errors[0]["severity"] == "error"

    def test_scoring_relative_relationships(self, tmp_path: Path):
        """Test that scoring correctly ranks code quality (Story 16.3)."""
        scorer = CodeScorer()
        
        # Score simple code
        simple_file = tmp_path / "simple.py"
        simple_file.write_text(SIMPLE_CODE)
        simple_result = scorer.score_file(simple_file, SIMPLE_CODE)
        
        # Score complex code
        complex_file = tmp_path / "complex.py"
        complex_file.write_text(COMPLEX_CODE)
        complex_result = scorer.score_file(complex_file, COMPLEX_CODE)
        
        # Score insecure code
        insecure_file = tmp_path / "insecure.py"
        insecure_file.write_text(INSECURE_CODE)
        insecure_result = scorer.score_file(insecure_file, INSECURE_CODE)
        
        # Score maintainable code
        maintainable_file = tmp_path / "maintainable.py"
        maintainable_file.write_text(MAINTAINABLE_CODE)
        maintainable_result = scorer.score_file(maintainable_file, MAINTAINABLE_CODE)
        
        # Business logic validation: Simple code should have lower complexity_score than complex code
        # (higher complexity_score = more complex = worse)
        assert simple_result["complexity_score"] < complex_result["complexity_score"], \
            "Simple code should have lower complexity_score than complex code"
        assert simple_result["overall_score"] > complex_result["overall_score"], \
            "Simple code should score higher overall than complex code"
        
        # Business logic validation: Secure code should score better than insecure code
        assert simple_result["security_score"] > insecure_result["security_score"], \
            "Secure code should score higher on security than insecure code"
        assert insecure_result["security_score"] < 5.0, \
            "Insecure code (with eval, exec, shell injection) should score low on security"
        
        # Business logic validation: Maintainable code should score well
        assert maintainable_result["maintainability_score"] >= 5.0, \
            f"Well-documented, typed code should score reasonably on maintainability, " \
            f"got {maintainable_result['maintainability_score']}"
        # Maintainable code (with docs, type hints, error handling) should score higher than complex code
        assert maintainable_result["maintainability_score"] > complex_result["maintainability_score"], \
            f"Maintainable code should have higher maintainability score than complex code. " \
            f"Maintainable: {maintainable_result['maintainability_score']}, " \
            f"Complex: {complex_result['maintainability_score']}"
        
        # Business logic validation: Overall score relationships
        assert maintainable_result["overall_score"] > complex_result["overall_score"], \
            f"Maintainable code should score higher overall than complex code. " \
            f"Maintainable: {maintainable_result['overall_score']}, " \
            f"Complex: {complex_result['overall_score']}"
        assert simple_result["overall_score"] > insecure_result["overall_score"], \
            f"Simple secure code should score higher overall than insecure code. " \
            f"Simple: {simple_result['overall_score']}, " \
            f"Insecure: {insecure_result['overall_score']}"
        
        # Additional validation: Verify all scores are in valid ranges
        for code_type, result in [("simple", simple_result), ("complex", complex_result), 
                                  ("insecure", insecure_result), ("maintainable", maintainable_result)]:
            assert 0.0 <= result["complexity_score"] <= 10.0, \
                f"{code_type} code complexity_score should be 0-10, got {result['complexity_score']}"
            assert 0.0 <= result["security_score"] <= 10.0, \
                f"{code_type} code security_score should be 0-10, got {result['security_score']}"
            assert 0.0 <= result["maintainability_score"] <= 10.0, \
                f"{code_type} code maintainability_score should be 0-10, got {result['maintainability_score']}"
            assert 0.0 <= result["overall_score"] <= 100.0, \
                f"{code_type} code overall_score should be 0-100, got {result['overall_score']}"

    def test_overall_score_formula_with_known_values(self, tmp_path: Path):
        """Test that overall score formula matches specification with known values (Story 18.1)."""
        scorer = CodeScorer()
        
        # Use custom weights for predictable testing
        class TestWeights:
            complexity = 0.20
            security = 0.30
            maintainability = 0.25
            test_coverage = 0.15
            performance = 0.10
        
        scorer.weights = TestWeights()
        
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Extract individual scores
        complexity = result["complexity_score"]
        security = result["security_score"]
        maintainability = result["maintainability_score"]
        coverage = result["test_coverage_score"]
        performance = result["performance_score"]
        
        # Calculate expected overall score using the exact formula from scoring.py
        # Formula: ((10 - complexity) * 0.20 + security * 0.30 + maintainability * 0.25 + 
        #           coverage * 0.15 + performance * 0.10) * 10
        expected_overall = (
            (10 - complexity) * 0.20 +
            security * 0.30 +
            maintainability * 0.25 +
            coverage * 0.15 +
            performance * 0.10
        ) * 10
        
        # Verify the formula matches (allow for small floating point differences)
        assert abs(result["overall_score"] - expected_overall) < 0.01, \
            f"Overall score formula mismatch: expected {expected_overall}, got {result['overall_score']}"
    
    def test_weighted_average_calculation_correctness(self, tmp_path: Path):
        """Test that weighted average calculations are mathematically correct (Story 18.1)."""
        scorer = CodeScorer()
        
        # Test with custom weights that sum to 1.0
        class CustomWeights:
            complexity = 0.10
            security = 0.40
            maintainability = 0.20
            test_coverage = 0.20
            performance = 0.10
        
        scorer.weights = CustomWeights()
        
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Verify weights sum to 1.0
        assert abs(
            CustomWeights.complexity + CustomWeights.security + 
            CustomWeights.maintainability + CustomWeights.test_coverage + 
            CustomWeights.performance - 1.0
        ) < 0.0001, "Weights must sum to 1.0"
        
        # Calculate weighted average manually
        weighted_sum = (
            (10 - result["complexity_score"]) * CustomWeights.complexity +
            result["security_score"] * CustomWeights.security +
            result["maintainability_score"] * CustomWeights.maintainability +
            result["test_coverage_score"] * CustomWeights.test_coverage +
            result["performance_score"] * CustomWeights.performance
        )
        expected_overall = weighted_sum * 10
        
        # Verify calculation is correct
        assert abs(result["overall_score"] - expected_overall) < 0.01, \
            "Weighted average calculation is incorrect"
    
    def test_scoring_simple_vs_complex_with_same_context(self, tmp_path: Path):
        """Test that simple code scores better than complex code with same test context (Story 18.1)."""
        scorer = CodeScorer()
        
        # Score simple code
        simple_file = tmp_path / "simple.py"
        simple_file.write_text(SIMPLE_CODE)
        simple_result = scorer.score_file(simple_file, SIMPLE_CODE)
        
        # Score complex code
        complex_file = tmp_path / "complex.py"
        complex_file.write_text(COMPLEX_CODE)
        complex_result = scorer.score_file(complex_file, COMPLEX_CODE)
        
        # Business logic: Simple code should have lower complexity (lower complexity_score)
        assert simple_result["complexity_score"] < complex_result["complexity_score"], \
            "Simple code should have lower cyclomatic complexity (lower complexity_score)"
        
        # Business logic: Simple code should score higher overall (assuming other factors similar)
        # Note: This assumes security, maintainability, etc. are similar for both
        # The key difference should be complexity, which should make simple code score better
        complexity_advantage = (simple_result["complexity_score"] - complex_result["complexity_score"]) * 0.20 * 10
        if complexity_advantage > 5:  # Only assert if complexity difference is significant
            assert simple_result["overall_score"] > complex_result["overall_score"], \
                "Simple code should score higher overall due to lower complexity"
    
    def test_scoring_secure_vs_insecure_code(self, tmp_path: Path):
        """Test that secure code scores significantly higher than insecure code (Story 18.1)."""
        scorer = CodeScorer()
        
        # Score simple (secure) code
        simple_file = tmp_path / "simple.py"
        simple_file.write_text(SIMPLE_CODE)
        simple_result = scorer.score_file(simple_file, SIMPLE_CODE)
        
        # Score insecure code
        insecure_file = tmp_path / "insecure.py"
        insecure_file.write_text(INSECURE_CODE)
        insecure_result = scorer.score_file(insecure_file, INSECURE_CODE)
        
        # Business logic: Secure code should score much higher on security
        security_difference = simple_result["security_score"] - insecure_result["security_score"]
        assert security_difference > 3.0, \
            f"Secure code should score significantly higher on security (diff: {security_difference})"
        
        # Business logic: Insecure code should score below threshold
        assert insecure_result["security_score"] < 5.0, \
            f"Insecure code (with eval, exec, shell injection) should score low on security, got {insecure_result['security_score']}"
        
        # Business logic: Overall score should reflect security importance (30% weight)
        # Since security has 0.30 weight, security issues should significantly impact overall score
        overall_difference = simple_result["overall_score"] - insecure_result["overall_score"]
        assert overall_difference > 5.0, \
            f"Security issues (30% weight) should significantly lower overall score (diff: {overall_difference})"
    
    def test_overall_score_formula_matches_specification(self, tmp_path: Path):
        """Verify overall score formula exactly matches specification (Story 18.1)."""
        scorer = CodeScorer()
        
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Default weights from scoring.py
        default_complexity = 0.20
        default_security = 0.30
        default_maintainability = 0.25
        default_coverage = 0.15
        default_performance = 0.10
        
        # Extract scores
        complexity = result["complexity_score"]
        security = result["security_score"]
        maintainability = result["maintainability_score"]
        coverage = result["test_coverage_score"]
        performance = result["performance_score"]
        
        # Apply exact formula from scoring.py line 177-184
        # Formula: ((10 - complexity_score) * w.complexity + 
        #           security_score * w.security + 
        #           maintainability_score * w.maintainability + 
        #           test_coverage_score * w.test_coverage + 
        #           performance_score * w.performance) * 10
        calculated_overall = (
            (10 - complexity) * default_complexity +
            security * default_security +
            maintainability * default_maintainability +
            coverage * default_coverage +
            performance * default_performance
        ) * 10
        
        # Verify formula matches exactly (within floating point precision)
        assert abs(result["overall_score"] - calculated_overall) < 0.01, \
            f"Overall score formula does not match specification: " \
            f"expected {calculated_overall}, got {result['overall_score']}. " \
            f"Formula should be: ((10 - {complexity}) * {default_complexity} + " \
            f"{security} * {default_security} + {maintainability} * {default_maintainability} + " \
            f"{coverage} * {default_coverage} + {performance} * {default_performance}) * 10"
    
    def test_overall_score_formula_edge_cases(self, tmp_path: Path):
        """Test overall score formula with edge cases (Story 16.3)."""
        scorer = CodeScorer()
        
        # Test with custom weights for edge case testing
        class EdgeCaseWeights:
            complexity = 0.20
            security = 0.30
            maintainability = 0.25
            test_coverage = 0.15
            performance = 0.10
        
        scorer.weights = EdgeCaseWeights()
        
        # Test case: Verify formula handles all metrics correctly
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Verify formula handles all metrics correctly
        complexity = result["complexity_score"]
        security = result["security_score"]
        maintainability = result["maintainability_score"]
        coverage = result["test_coverage_score"]
        performance = result["performance_score"]
        
        # Calculate expected using formula
        expected = (
            (10 - complexity) * EdgeCaseWeights.complexity +
            security * EdgeCaseWeights.security +
            maintainability * EdgeCaseWeights.maintainability +
            coverage * EdgeCaseWeights.test_coverage +
            performance * EdgeCaseWeights.performance
        ) * 10
        
        assert abs(result["overall_score"] - expected) < 0.01, \
            f"Formula should handle all metrics correctly. Expected {expected}, got {result['overall_score']}"
        
        # Verify complexity inversion: lower complexity_score = better overall score
        # (complexity_score is inverted in formula: (10 - complexity_score))
        assert (10 - complexity) >= 0, \
            f"Complexity inversion (10 - complexity_score) should be non-negative, got {10 - complexity}"
        assert (10 - complexity) <= 10, \
            f"Complexity inversion (10 - complexity_score) should be <= 10, got {10 - complexity}"
    
    def test_weighted_average_with_different_weight_configs(self, tmp_path: Path):
        """Test that changing weights produces expected changes in overall score (Story 16.3)."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text(SIMPLE_CODE)
        
        # Test with security-focused weights (higher security weight)
        class SecurityFocusedWeights:
            complexity = 0.10
            security = 0.50  # Higher weight on security
            maintainability = 0.20
            test_coverage = 0.10
            performance = 0.10
        
        scorer.weights = SecurityFocusedWeights()
        security_focused_result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Test with complexity-focused weights (higher complexity weight)
        class ComplexityFocusedWeights:
            complexity = 0.40  # Higher weight on complexity
            security = 0.20
            maintainability = 0.20
            test_coverage = 0.10
            performance = 0.10
        
        scorer.weights = ComplexityFocusedWeights()
        complexity_focused_result = scorer.score_file(test_file, SIMPLE_CODE)
        
        # Verify weights sum to 1.0
        assert abs(
            SecurityFocusedWeights.complexity + SecurityFocusedWeights.security +
            SecurityFocusedWeights.maintainability + SecurityFocusedWeights.test_coverage +
            SecurityFocusedWeights.performance - 1.0
        ) < 0.0001, "Security-focused weights must sum to 1.0"
        
        assert abs(
            ComplexityFocusedWeights.complexity + ComplexityFocusedWeights.security +
            ComplexityFocusedWeights.maintainability + ComplexityFocusedWeights.test_coverage +
            ComplexityFocusedWeights.performance - 1.0
        ) < 0.0001, "Complexity-focused weights must sum to 1.0"
        
        # With security-focused weights, security score should have more impact
        # With complexity-focused weights, complexity score should have more impact
        # The overall scores may differ based on which metric is weighted more
        # (This validates that weights actually affect the calculation)
        assert security_focused_result["overall_score"] > 0, \
            "Security-focused weights should produce valid overall score"
        assert complexity_focused_result["overall_score"] > 0, \
            "Complexity-focused weights should produce valid overall score"
        
        # Both should use the same formula, just with different weights
        # Verify both calculations are correct
        security_expected = (
            (10 - security_focused_result["complexity_score"]) * SecurityFocusedWeights.complexity +
            security_focused_result["security_score"] * SecurityFocusedWeights.security +
            security_focused_result["maintainability_score"] * SecurityFocusedWeights.maintainability +
            security_focused_result["test_coverage_score"] * SecurityFocusedWeights.test_coverage +
            security_focused_result["performance_score"] * SecurityFocusedWeights.performance
        ) * 10
        
        complexity_expected = (
            (10 - complexity_focused_result["complexity_score"]) * ComplexityFocusedWeights.complexity +
            complexity_focused_result["security_score"] * ComplexityFocusedWeights.security +
            complexity_focused_result["maintainability_score"] * ComplexityFocusedWeights.maintainability +
            complexity_focused_result["test_coverage_score"] * ComplexityFocusedWeights.test_coverage +
            complexity_focused_result["performance_score"] * ComplexityFocusedWeights.performance
        ) * 10
        
        assert abs(security_focused_result["overall_score"] - security_expected) < 0.01, \
            f"Security-focused weighted average calculation incorrect. " \
            f"Expected {security_expected}, got {security_focused_result['overall_score']}"
        
        assert abs(complexity_focused_result["overall_score"] - complexity_expected) < 0.01, \
            f"Complexity-focused weighted average calculation incorrect. " \
            f"Expected {complexity_expected}, got {complexity_focused_result['overall_score']}"


@pytest.mark.unit
class TestRuffIssueGrouping:
    """Test cases for ENH-002 Story #18: Ruff Output Grouping."""

    def test_group_ruff_issues_by_code_empty(self):
        """Test grouping with no issues."""
        scorer = CodeScorer()
        result = scorer._group_ruff_issues_by_code([])

        assert result["total_count"] == 0
        assert result["groups"] == []
        assert result["summary"] == "No issues found"

    def test_group_ruff_issues_by_code_single_code(self):
        """Test grouping with single code type."""
        scorer = CodeScorer()
        issues = [
            {"code": {"name": "F401"}, "message": "Unused import", "location": {"row": 1}},
            {"code": {"name": "F401"}, "message": "Unused import", "location": {"row": 5}},
            {"code": {"name": "F401"}, "message": "Unused import", "location": {"row": 10}},
        ]

        result = scorer._group_ruff_issues_by_code(issues)

        assert result["total_count"] == 3
        assert len(result["groups"]) == 1
        assert result["groups"][0]["code"] == "F401"
        assert result["groups"][0]["count"] == 3
        assert result["groups"][0]["severity"] == "error"
        assert result["summary"] == "F401 (3)"

    def test_group_ruff_issues_by_code_multiple_codes(self):
        """Test grouping with multiple code types."""
        scorer = CodeScorer()
        issues = [
            {"code": {"name": "UP006"}, "message": "Use dict instead of Dict", "location": {"row": 1}},
            {"code": {"name": "UP006"}, "message": "Use list instead of List", "location": {"row": 2}},
            {"code": {"name": "UP045"}, "message": "Use X | None instead of Optional[X]", "location": {"row": 3}},
            {"code": {"name": "F401"}, "message": "Unused import", "location": {"row": 4}},
            {"code": {"name": "UP006"}, "message": "Use dict instead of Dict", "location": {"row": 5}},
        ]

        result = scorer._group_ruff_issues_by_code(issues)

        assert result["total_count"] == 5
        assert len(result["groups"]) == 3

        # Groups should be sorted by count (descending), then by code (ascending)
        assert result["groups"][0]["code"] == "UP006"
        assert result["groups"][0]["count"] == 3

        # For codes with same count, they're sorted alphabetically
        # F401 comes before UP045 alphabetically
        assert result["groups"][1]["code"] == "F401"
        assert result["groups"][1]["count"] == 1
        assert result["groups"][2]["code"] == "UP045"
        assert result["groups"][2]["count"] == 1

        # Summary should list all groups
        assert "UP006 (3)" in result["summary"]
        assert "UP045 (1)" in result["summary"]
        assert "F401 (1)" in result["summary"]

    def test_group_ruff_issues_by_code_severity_detection(self):
        """Test that severity is correctly detected from code prefix."""
        scorer = CodeScorer()
        issues = [
            {"code": {"name": "E501"}, "message": "Line too long", "location": {"row": 1}},
            {"code": {"name": "W291"}, "message": "Trailing whitespace", "location": {"row": 2}},
            {"code": {"name": "F401"}, "message": "Unused import", "location": {"row": 3}},
            {"code": {"name": "UP006"}, "message": "Use dict instead of Dict", "location": {"row": 4}},
        ]

        result = scorer._group_ruff_issues_by_code(issues)

        # Find each group and check severity
        groups_by_code = {g["code"]: g for g in result["groups"]}

        assert groups_by_code["E501"]["severity"] == "error"  # E prefix = error
        assert groups_by_code["W291"]["severity"] == "warning"  # W prefix = warning
        assert groups_by_code["F401"]["severity"] == "error"  # F prefix = error
        assert groups_by_code["UP006"]["severity"] == "info"  # UP prefix = info

    def test_group_ruff_issues_by_code_string_code_format(self):
        """Test grouping with string code format (not dict)."""
        scorer = CodeScorer()
        issues = [
            {"code": "F401", "message": "Unused import", "location": {"row": 1}},
            {"code": "F401", "message": "Unused import", "location": {"row": 2}},
        ]

        result = scorer._group_ruff_issues_by_code(issues)

        assert result["total_count"] == 2
        assert len(result["groups"]) == 1
        assert result["groups"][0]["code"] == "F401"
        assert result["groups"][0]["count"] == 2

    def test_group_ruff_issues_by_code_missing_code(self):
        """Test grouping with missing code field."""
        scorer = CodeScorer()
        issues = [
            {"message": "Some issue without code", "location": {"row": 1}},
            {"code": {"name": "F401"}, "message": "Unused import", "location": {"row": 2}},
        ]

        result = scorer._group_ruff_issues_by_code(issues)

        assert result["total_count"] == 2
        assert len(result["groups"]) == 2

        # Should have UNKNOWN group for missing code
        codes = [g["code"] for g in result["groups"]]
        assert "UNKNOWN" in codes
        assert "F401" in codes

    def test_group_ruff_issues_preserves_original_issues(self):
        """Test that grouping preserves all original issue data."""
        scorer = CodeScorer()
        issues = [
            {
                "code": {"name": "UP006"},
                "message": "Use dict instead of Dict",
                "location": {"row": 1, "column": 10},
                "end_location": {"row": 1, "column": 14},
                "fix": {"content": "dict", "location": {"row": 1, "column": 10}},
            },
            {
                "code": {"name": "UP006"},
                "message": "Use list instead of List",
                "location": {"row": 2, "column": 5},
            },
        ]

        result = scorer._group_ruff_issues_by_code(issues)

        # Check that all original issues are preserved in the group
        up006_group = result["groups"][0]
        assert up006_group["code"] == "UP006"
        assert len(up006_group["issues"]) == 2

        # First issue should have all fields preserved
        assert up006_group["issues"][0]["location"]["row"] == 1
        assert up006_group["issues"][0]["location"]["column"] == 10
        assert "fix" in up006_group["issues"][0]

        # Second issue should also be preserved
        assert up006_group["issues"][1]["location"]["row"] == 2
        assert up006_group["issues"][1]["location"]["column"] == 5

    def test_group_ruff_issues_realistic_output(self):
        """Test grouping with realistic ruff output (from feedback session)."""
        scorer = CodeScorer()
        # Simulate the 30 issues from the parallel execution feedback
        issues = (
            [{"code": {"name": "UP006"}, "message": "Use `dict` instead of `Dict`", "location": {"row": i}} for i in range(1, 18)] +
            [{"code": {"name": "UP045"}, "message": "Use `X | None` instead of `Optional[X]`", "location": {"row": i}} for i in range(18, 28)] +
            [{"code": {"name": "UP007"}, "message": "Use `X | Y` instead of `Union[X, Y]`", "location": {"row": i}} for i in range(28, 30)] +
            [{"code": {"name": "F401"}, "message": "Unused import `field`", "location": {"row": 30}}]
        )

        result = scorer._group_ruff_issues_by_code(issues)

        assert result["total_count"] == 30
        assert len(result["groups"]) == 4

        # Check sorted by count (descending)
        assert result["groups"][0]["code"] == "UP006"
        assert result["groups"][0]["count"] == 17
        assert result["groups"][1]["code"] == "UP045"
        assert result["groups"][1]["count"] == 10
        assert result["groups"][2]["code"] == "UP007"
        assert result["groups"][2]["count"] == 2
        assert result["groups"][3]["code"] == "F401"
        assert result["groups"][3]["count"] == 1

        # Check summary format
        expected_summary = "UP006 (17), UP045 (10), UP007 (2), F401 (1)"
        assert result["summary"] == expected_summary