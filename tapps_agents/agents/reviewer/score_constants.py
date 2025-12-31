"""
Score Constants and Type-Safe Score Handling

This module provides constants and utilities for consistent score handling
across the reviewer agent. It ensures that score scales (0-10 vs 0-100) are
handled consistently throughout the codebase.
"""

from dataclasses import dataclass
from typing import Any


class ComplexityConstants:
    """Constants for complexity scoring calculations."""
    
    # Maximum expected cyclomatic complexity for a function
    # Functions with complexity > 50 are extremely complex and should be refactored
    MAX_EXPECTED_COMPLEXITY = 50.0
    
    # Scaling factor: divide by this to normalize to 0-10 scale
    # MAX_COMPLEXITY / SCALING_FACTOR = 10.0
    # So SCALING_FACTOR = MAX_COMPLEXITY / 10 = 5.0
    SCALING_FACTOR = MAX_EXPECTED_COMPLEXITY / 10.0  # 5.0
    
    # Maximum score (upper bound)
    MAX_SCORE = 10.0


class SecurityConstants:
    """Constants for security scoring calculations."""
    
    # Penalty per insecure pattern found
    # 2 points per issue means:
    # - 1 issue: 8/10 score
    # - 5 issues: 0/10 score
    INSECURE_PATTERN_PENALTY = 2.0
    
    # Maximum score
    MAX_SCORE = 10.0


@dataclass
class ScoreScales:
    """Constants for score scales used throughout the reviewer agent."""
    
    # Individual metric scores (complexity, security, maintainability, etc.)
    # These are on a 0-10 scale
    INDIVIDUAL_SCORE_MIN = 0.0
    INDIVIDUAL_SCORE_MAX = 10.0
    
    # Overall score is on a 0-100 scale (weighted sum of individual scores)
    OVERALL_SCORE_MIN = 0.0
    OVERALL_SCORE_MAX = 100.0
    
    # Test coverage can be represented as 0-10 (percentage/10) or 0-100 (percentage)
    # We use 0-10 internally, 0-100 for display
    TEST_COVERAGE_SCALE_FACTOR = 10.0  # Multiply 0-10 to get 0-100


class ScoreNormalizer:
    """Utility class for normalizing scores between different scales."""
    
    @staticmethod
    def normalize_overall_score(score: float, from_scale_100: bool = True) -> float:
        """
        Normalize overall score between 0-10 and 0-100 scales.
        
        Args:
            score: The score to normalize
            from_scale_100: If True, converts from 0-100 to 0-10. If False, converts from 0-10 to 0-100.
        
        Returns:
            Normalized score
        """
        if from_scale_100:
            # Convert 0-100 to 0-10
            return score / ScoreScales.TEST_COVERAGE_SCALE_FACTOR
        else:
            # Convert 0-10 to 0-100
            return score * ScoreScales.TEST_COVERAGE_SCALE_FACTOR
    
    @staticmethod
    def normalize_test_coverage(score: float, from_percentage: bool = False) -> float:
        """
        Normalize test coverage score.
        
        Args:
            score: The score to normalize (0-10 or 0-100)
            from_percentage: If True, score is 0-100 (percentage). If False, score is 0-10.
        
        Returns:
            Normalized score to 0-10 scale
        """
        if from_percentage:
            # Convert 0-100 to 0-10
            return score / ScoreScales.TEST_COVERAGE_SCALE_FACTOR
        else:
            # Already 0-10, just return
            return score
    
    @staticmethod
    def test_coverage_to_percentage(score_0_10: float) -> float:
        """
        Convert test coverage score from 0-10 scale to 0-100 percentage.
        
        Args:
            score_0_10: Test coverage score on 0-10 scale
        
        Returns:
            Test coverage percentage (0-100)
        """
        return score_0_10 * ScoreScales.TEST_COVERAGE_SCALE_FACTOR
    
    @staticmethod
    def validate_individual_score(score: float, metric_name: str) -> float:
        """
        Validate and clamp an individual metric score to 0-10 range.
        
        Args:
            score: The score to validate
            metric_name: Name of the metric (for error messages)
        
        Returns:
            Clamped score in 0-10 range
        
        Raises:
            ValueError: If score is invalid (NaN, Infinity)
        """
        import math
        
        if math.isnan(score) or math.isinf(score):
            raise ValueError(f"Invalid {metric_name} score: {score} (NaN or Infinity)")
        
        return max(
            ScoreScales.INDIVIDUAL_SCORE_MIN,
            min(ScoreScales.INDIVIDUAL_SCORE_MAX, score)
        )
    
    @staticmethod
    def validate_overall_score(score: float) -> float:
        """
        Validate and clamp overall score to 0-100 range.
        
        Args:
            score: The score to validate
        
        Returns:
            Clamped score in 0-100 range
        
        Raises:
            ValueError: If score is invalid (NaN, Infinity)
        """
        import math
        
        if math.isnan(score) or math.isinf(score):
            raise ValueError(f"Invalid overall score: {score} (NaN or Infinity)")
        
        return max(
            ScoreScales.OVERALL_SCORE_MIN,
            min(ScoreScales.OVERALL_SCORE_MAX, score)
        )


def extract_scores_normalized(scores: dict[str, Any]) -> dict[str, float]:
    """
    Extract and normalize scores from a scores dictionary to consistent scales.
    
    This function ensures:
    - Individual metrics (complexity, security, maintainability, performance) are 0-10
    - Test coverage is 0-10 (represents percentage/10)
    - Overall score is 0-100
    
    Args:
        scores: Dictionary containing scores (may have inconsistent scales)
    
    Returns:
        Dictionary with normalized scores on correct scales
    """
    normalizer = ScoreNormalizer()
    
    # Extract individual scores (should already be 0-10)
    complexity_score = normalizer.validate_individual_score(
        scores.get("complexity_score", 5.0), "complexity"
    )
    security_score = normalizer.validate_individual_score(
        scores.get("security_score", 5.0), "security"
    )
    maintainability_score = normalizer.validate_individual_score(
        scores.get("maintainability_score", 5.0), "maintainability"
    )
    performance_score = normalizer.validate_individual_score(
        scores.get("performance_score", 5.0), "performance"
    )
    
    # Test coverage: normalize to 0-10 scale
    test_coverage_raw = scores.get("test_coverage_score", 0.0)
    # Check if it's already 0-10 or if it's 0-100
    # If > 10, assume it's 0-100 and convert
    test_coverage_score = normalizer.normalize_test_coverage(
        test_coverage_raw,
        from_percentage=(test_coverage_raw > 10.0)
    )
    test_coverage_score = normalizer.validate_individual_score(
        test_coverage_score, "test_coverage"
    )
    
    # Overall score: normalize to 0-100 scale
    overall_score_raw = scores.get("overall_score", 0.0)
    # If <= 10, assume it's on 0-10 scale and convert to 0-100
    # If > 10, assume it's already 0-100
    if overall_score_raw <= 10.0:
        overall_score = normalizer.normalize_overall_score(
            overall_score_raw, from_scale_100=False
        )
    else:
        overall_score = normalizer.normalize_overall_score(
            overall_score_raw, from_scale_100=True
        ) * ScoreScales.TEST_COVERAGE_SCALE_FACTOR  # Convert back to 0-100
    overall_score = normalizer.validate_overall_score(overall_score)
    
    return {
        "complexity_score": complexity_score,
        "security_score": security_score,
        "maintainability_score": maintainability_score,
        "test_coverage_score": test_coverage_score,
        "performance_score": performance_score,
        "overall_score": overall_score,
    }
