"""
Unit tests for Score Constants and Normalization.
"""

import math
import pytest

from tapps_agents.agents.reviewer.score_constants import (
    ComplexityConstants,
    SecurityConstants,
    ScoreNormalizer,
    ScoreScales,
    extract_scores_normalized,
)

pytestmark = pytest.mark.unit


class TestScoreConstants:
    """Tests for score constants."""

    def test_complexity_constants(self):
        """Test ComplexityConstants values."""
        assert ComplexityConstants.MAX_EXPECTED_COMPLEXITY == 50.0
        assert ComplexityConstants.SCALING_FACTOR == 5.0
        assert ComplexityConstants.MAX_SCORE == 10.0

    def test_security_constants(self):
        """Test SecurityConstants values."""
        assert SecurityConstants.INSECURE_PATTERN_PENALTY == 2.0
        assert SecurityConstants.MAX_SCORE == 10.0

    def test_score_scales(self):
        """Test ScoreScales values."""
        assert ScoreScales.INDIVIDUAL_SCORE_MIN == 0.0
        assert ScoreScales.INDIVIDUAL_SCORE_MAX == 10.0
        assert ScoreScales.OVERALL_SCORE_MIN == 0.0
        assert ScoreScales.OVERALL_SCORE_MAX == 100.0
        assert ScoreScales.TEST_COVERAGE_SCALE_FACTOR == 10.0


class TestScoreNormalizer:
    """Tests for ScoreNormalizer."""

    def test_normalize_overall_score_from_100_to_10(self):
        """Test converting overall score from 0-100 to 0-10."""
        normalizer = ScoreNormalizer()
        result = normalizer.normalize_overall_score(85.0, from_scale_100=True)
        assert result == 8.5

    def test_normalize_overall_score_from_10_to_100(self):
        """Test converting overall score from 0-10 to 0-100."""
        normalizer = ScoreNormalizer()
        result = normalizer.normalize_overall_score(8.5, from_scale_100=False)
        assert result == 85.0

    def test_normalize_test_coverage_from_percentage(self):
        """Test converting test coverage from 0-100 to 0-10."""
        normalizer = ScoreNormalizer()
        result = normalizer.normalize_test_coverage(80.0, from_percentage=True)
        assert result == 8.0

    def test_normalize_test_coverage_already_0_10(self):
        """Test test coverage already on 0-10 scale."""
        normalizer = ScoreNormalizer()
        result = normalizer.normalize_test_coverage(8.0, from_percentage=False)
        assert result == 8.0

    def test_test_coverage_to_percentage(self):
        """Test converting test coverage from 0-10 to percentage."""
        normalizer = ScoreNormalizer()
        result = normalizer.test_coverage_to_percentage(8.0)
        assert result == 80.0

    def test_validate_individual_score_valid(self):
        """Test validating valid individual score."""
        normalizer = ScoreNormalizer()
        result = normalizer.validate_individual_score(7.5, "test")
        assert result == 7.5

    def test_validate_individual_score_clamp_high(self):
        """Test clamping high individual score."""
        normalizer = ScoreNormalizer()
        result = normalizer.validate_individual_score(15.0, "test")
        assert result == 10.0

    def test_validate_individual_score_clamp_low(self):
        """Test clamping low individual score."""
        normalizer = ScoreNormalizer()
        result = normalizer.validate_individual_score(-5.0, "test")
        assert result == 0.0

    def test_validate_individual_score_nan(self):
        """Test validating NaN individual score raises ValueError."""
        normalizer = ScoreNormalizer()
        with pytest.raises(ValueError, match="Invalid.*NaN"):
            normalizer.validate_individual_score(float("nan"), "test")

    def test_validate_individual_score_inf(self):
        """Test validating Infinity individual score raises ValueError."""
        normalizer = ScoreNormalizer()
        with pytest.raises(ValueError, match="Invalid.*Infinity"):
            normalizer.validate_individual_score(float("inf"), "test")

    def test_validate_overall_score_valid(self):
        """Test validating valid overall score."""
        normalizer = ScoreNormalizer()
        result = normalizer.validate_overall_score(75.0)
        assert result == 75.0

    def test_validate_overall_score_clamp_high(self):
        """Test clamping high overall score."""
        normalizer = ScoreNormalizer()
        result = normalizer.validate_overall_score(150.0)
        assert result == 100.0

    def test_validate_overall_score_clamp_low(self):
        """Test clamping low overall score."""
        normalizer = ScoreNormalizer()
        result = normalizer.validate_overall_score(-10.0)
        assert result == 0.0

    def test_validate_overall_score_nan(self):
        """Test validating NaN overall score raises ValueError."""
        normalizer = ScoreNormalizer()
        with pytest.raises(ValueError, match="Invalid.*NaN"):
            normalizer.validate_overall_score(float("nan"))

    def test_validate_overall_score_inf(self):
        """Test validating Infinity overall score raises ValueError."""
        normalizer = ScoreNormalizer()
        with pytest.raises(ValueError, match="Invalid.*Infinity"):
            normalizer.validate_overall_score(float("inf"))


class TestExtractScoresNormalized:
    """Tests for extract_scores_normalized function."""

    def test_extract_scores_with_0_10_scale(self):
        """Test extracting scores already on correct scales."""
        scores = {
            "complexity_score": 3.0,
            "security_score": 8.5,
            "maintainability_score": 7.5,
            "test_coverage_score": 8.0,  # 0-10 scale
            "performance_score": 7.0,
            "overall_score": 85.0,  # 0-100 scale
        }
        result = extract_scores_normalized(scores)
        assert result["complexity_score"] == 3.0
        assert result["security_score"] == 8.5
        assert result["maintainability_score"] == 7.5
        assert result["test_coverage_score"] == 8.0
        assert result["performance_score"] == 7.0
        assert result["overall_score"] == 85.0

    def test_extract_scores_with_test_coverage_percentage(self):
        """Test extracting scores with test coverage as percentage."""
        scores = {
            "complexity_score": 3.0,
            "security_score": 8.5,
            "maintainability_score": 7.5,
            "test_coverage_score": 80.0,  # 0-100 percentage (will be converted)
            "performance_score": 7.0,
            "overall_score": 85.0,
        }
        result = extract_scores_normalized(scores)
        assert result["test_coverage_score"] == 8.0  # Converted to 0-10

    def test_extract_scores_with_overall_0_10(self):
        """Test extracting scores with overall on 0-10 scale."""
        scores = {
            "complexity_score": 3.0,
            "security_score": 8.5,
            "maintainability_score": 7.5,
            "test_coverage_score": 8.0,
            "performance_score": 7.0,
            "overall_score": 8.5,  # 0-10 scale (will be converted to 0-100)
        }
        result = extract_scores_normalized(scores)
        assert result["overall_score"] == 85.0  # Converted to 0-100

    def test_extract_scores_with_missing_values(self):
        """Test extracting scores with missing values uses defaults."""
        scores = {
            "complexity_score": 3.0,
            # Missing other scores
        }
        result = extract_scores_normalized(scores)
        assert result["complexity_score"] == 3.0
        assert result["security_score"] == 5.0  # Default
        assert result["maintainability_score"] == 5.0  # Default
        assert result["test_coverage_score"] == 0.0  # Default
        assert result["performance_score"] == 5.0  # Default
        assert result["overall_score"] == 0.0  # Default

    def test_extract_scores_clamps_values(self):
        """Test extracting scores clamps invalid values."""
        scores = {
            "complexity_score": 15.0,  # Above max, will be clamped
            "security_score": -5.0,  # Below min, will be clamped
            "maintainability_score": 7.5,
            "test_coverage_score": 8.0,
            "performance_score": 7.0,
            "overall_score": 150.0,  # Above max, will be clamped
        }
        result = extract_scores_normalized(scores)
        assert result["complexity_score"] == 10.0  # Clamped
        assert result["security_score"] == 0.0  # Clamped
        assert result["overall_score"] == 100.0  # Clamped

    def test_extract_scores_validates_nan(self):
        """Test extracting scores validates NaN values."""
        scores = {
            "complexity_score": float("nan"),
            "security_score": 8.5,
            "maintainability_score": 7.5,
            "test_coverage_score": 8.0,
            "performance_score": 7.0,
            "overall_score": 85.0,
        }
        with pytest.raises(ValueError, match="Invalid.*NaN"):
            extract_scores_normalized(scores)
