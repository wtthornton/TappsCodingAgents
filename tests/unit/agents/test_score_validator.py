"""
Tests for Score Validator - Tests score validation and the TypeError fix.

Tests the fix for TypeError when validate_all_scores receives a dict with
non-score keys like "metrics".
"""

import pytest

from tapps_agents.agents.reviewer.score_validator import ScoreValidator
from tapps_agents.core.language_detector import Language

pytestmark = pytest.mark.unit


class TestScoreValidator:
    """Tests for ScoreValidator class."""

    def test_validate_score_with_float(self):
        """Test validate_score with a valid float score."""
        validator = ScoreValidator()
        result = validator.validate_score(7.5, "complexity")
        
        assert result.valid is True
        assert result.score == 7.5
        assert result.category == "complexity"
        assert result.error is None

    def test_validate_score_out_of_range(self):
        """Test validate_score with score outside valid range."""
        validator = ScoreValidator()
        result = validator.validate_score(15.0, "complexity")
        
        assert result.valid is False
        assert result.score == 15.0
        assert result.error is not None
        assert "outside valid range" in result.error

    def test_validate_all_scores_with_metrics_key(self):
        """
        Test validate_all_scores with scores dict containing 'metrics' key.
        
        This reproduces the TypeError: '<' not supported between instances of 'dict' and 'float'
        that occurs when validate_all_scores tries to validate non-score keys.
        """
        validator = ScoreValidator()
        
        # Simulate the actual scores dict structure from CodeScorer.score_file()
        scores = {
            "complexity_score": 5.0,
            "security_score": 8.0,
            "maintainability_score": 7.0,
            "test_coverage_score": 6.0,
            "performance_score": 9.0,
            "overall_score": 75.0,
            "metrics": {  # This is a dict, not a float!
                "complexity": 5.0,
                "security": 8.0,
            },
            "linting_score": 8.5,
            "type_checking_score": 7.5,
            "duplication_score": 9.0,
        }
        
        # This should NOT raise TypeError
        # The fix should filter out non-score keys or handle them gracefully
        results = validator.validate_all_scores(
            scores, language=Language.PYTHON, context=None
        )
        
        # Should only validate score keys, not "metrics"
        assert "complexity_score" in results or "complexity" in results
        assert "security_score" in results or "security" in results
        assert "metrics" not in results  # Should be filtered out

    def test_validate_all_scores_with_only_score_keys(self):
        """Test validate_all_scores with only valid score keys."""
        validator = ScoreValidator()
        
        scores = {
            "complexity": 5.0,
            "security": 8.0,
            "maintainability": 7.0,
            "overall": 75.0,
        }
        
        results = validator.validate_all_scores(
            scores, language=Language.PYTHON, context=None
        )
        
        assert len(results) == 4
        assert all(result.valid for result in results.values())

    def test_validate_all_scores_filters_non_numeric(self):
        """Test that validate_all_scores filters out non-numeric values."""
        validator = ScoreValidator()
        
        scores = {
            "complexity_score": 5.0,
            "security_score": 8.0,
            "metrics": {"some": "dict"},  # Dict value
            "some_string": "not a number",  # String value
            "some_list": [1, 2, 3],  # List value
            "overall_score": 75.0,
        }
        
        # Should not raise TypeError
        results = validator.validate_all_scores(
            scores, language=Language.PYTHON, context=None
        )
        
        # Should only contain numeric score keys
        assert "metrics" not in results
        assert "some_string" not in results
        assert "some_list" not in results


class TestLintingSuggestions:
    """Test linting category suggestion generation."""

    def test_linting_suggestions_below_threshold_python(self):
        """Test linting suggestions for Python when score < 7.0."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="linting",
            score=5.0,
            language=Language.PYTHON
        )
        
        assert len(suggestions) > 0
        assert any("ruff" in s.lower() for s in suggestions)
        assert any("check" in s.lower() for s in suggestions)

    def test_linting_suggestions_below_threshold_typescript(self):
        """Test linting suggestions for TypeScript when score < 7.0."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="linting",
            score=5.0,
            language=Language.TYPESCRIPT
        )
        
        assert len(suggestions) > 0
        assert any("eslint" in s.lower() for s in suggestions)

    def test_linting_suggestions_no_language(self):
        """Test linting suggestions when language is None."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="linting",
            score=5.0,
            language=None
        )
        
        assert len(suggestions) > 0
        # Should have base suggestions
        assert any("linting tool" in s.lower() or "code style" in s.lower() for s in suggestions)


class TestTypeCheckingSuggestions:
    """Test type checking category suggestion generation."""

    def test_type_checking_suggestions_below_threshold_python(self):
        """Test type checking suggestions for Python when score < 7.0."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="type_checking",
            score=5.0,
            language=Language.PYTHON
        )
        
        assert len(suggestions) > 0
        assert any("mypy" in s.lower() for s in suggestions)
        assert any("type hint" in s.lower() or "type annotation" in s.lower() for s in suggestions)

    def test_type_checking_suggestions_below_threshold_typescript(self):
        """Test type checking suggestions for TypeScript when score < 7.0."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="type_checking",
            score=5.0,
            language=Language.TYPESCRIPT
        )
        
        assert len(suggestions) > 0
        assert any("typescript" in s.lower() or "tsconfig" in s.lower() for s in suggestions)
        assert any("strict" in s.lower() for s in suggestions)

    def test_type_checking_suggestions_no_language(self):
        """Test type checking suggestions when language is None."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="type_checking",
            score=5.0,
            language=None
        )
        
        assert len(suggestions) > 0
        # Should have base suggestions
        assert any("type annotation" in s.lower() or "type hint" in s.lower() for s in suggestions)


class TestDuplicationSuggestions:
    """Test duplication category suggestion generation."""

    def test_duplication_suggestions_below_threshold_python(self):
        """Test duplication suggestions for Python when score < 7.0."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="duplication",
            score=5.0,
            language=Language.PYTHON
        )
        
        assert len(suggestions) > 0
        assert any("jscpd" in s.lower() or "duplicate" in s.lower() for s in suggestions)
        assert any("reusable" in s.lower() or "utility" in s.lower() for s in suggestions)

    def test_duplication_suggestions_below_threshold_react(self):
        """Test duplication suggestions for React when score < 7.0."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="duplication",
            score=5.0,
            language=Language.REACT
        )
        
        assert len(suggestions) > 0
        assert any("react" in s.lower() or "component" in s.lower() for s in suggestions)
        assert any("hook" in s.lower() or "hoc" in s.lower() for s in suggestions)

    def test_duplication_suggestions_no_language(self):
        """Test duplication suggestions when language is None."""
        validator = ScoreValidator()
        suggestions = validator._generate_category_suggestions(
            category="duplication",
            score=5.0,
            language=None
        )
        
        assert len(suggestions) > 0
        # Should have base suggestions
        assert any("duplicate" in s.lower() or "reusable" in s.lower() for s in suggestions)
