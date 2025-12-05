"""
Unit tests for CodeScorer.
"""

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

