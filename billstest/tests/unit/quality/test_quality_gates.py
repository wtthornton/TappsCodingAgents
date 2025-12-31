"""
Unit tests for Quality Gates.
"""

import pytest

from tapps_agents.quality.quality_gates import (
    QualityGate,
    QualityGateResult,
    QualityThresholds,
)

pytestmark = pytest.mark.unit


class TestQualityThresholds:
    """Test cases for QualityThresholds."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = QualityThresholds()
        
        assert thresholds.overall_min == 8.0
        assert thresholds.security_min == 8.5
        assert thresholds.maintainability_min == 7.0
        assert thresholds.complexity_max == 5.0
        assert thresholds.test_coverage_min == 80.0
        assert thresholds.performance_min == 7.0

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresholds = QualityThresholds(
            overall_min=9.0,
            security_min=9.5,
            maintainability_min=8.0
        )
        
        assert thresholds.overall_min == 9.0
        assert thresholds.security_min == 9.5
        assert thresholds.maintainability_min == 8.0

    def test_from_dict(self):
        """Test creating thresholds from dictionary."""
        data = {
            "overall_min": 9.0,
            "security_min": 9.5,
            "maintainability_min": 8.0,
            "complexity_max": 4.0,
            "test_coverage_min": 90.0,
            "performance_min": 8.0
        }
        
        thresholds = QualityThresholds.from_dict(data)
        
        assert thresholds.overall_min == 9.0
        assert thresholds.security_min == 9.5
        assert thresholds.maintainability_min == 8.0
        assert thresholds.complexity_max == 4.0
        assert thresholds.test_coverage_min == 90.0
        assert thresholds.performance_min == 8.0


class TestQualityGate:
    """Test cases for QualityGate."""

    @pytest.fixture
    def gate(self):
        """Create a QualityGate instance."""
        return QualityGate()

    def test_gate_initialization(self, gate):
        """Test gate initialization."""
        assert gate.thresholds is not None
        assert isinstance(gate.thresholds, QualityThresholds)

    def test_evaluate_passing_scores(self, gate):
        """Test evaluating passing scores."""
        # Use correct score keys (with _score suffix) and proper scales
        scores = {
            "overall_score": 90.0,  # 0-100 scale
            "security_score": 9.5,  # 0-10 scale
            "maintainability_score": 8.0,  # 0-10 scale
            "complexity_score": 4.0,  # 0-10 scale (lower is better)
            "test_coverage_score": 8.0,  # 0-10 scale (represents 80%)
            "performance_score": 8.0  # 0-10 scale
        }
        
        result = gate.evaluate(scores)
        
        assert isinstance(result, QualityGateResult)
        assert result.passed is True
        assert result.overall_passed is True
        assert result.security_passed is True
        assert len(result.failures) == 0

    def test_evaluate_failing_scores(self, gate):
        """Test evaluating failing scores."""
        # Use correct score keys (with _score suffix) and proper scales
        scores = {
            "overall_score": 70.0,  # 0-100 scale, below threshold (8.0/10 = 80/100)
            "security_score": 7.0,  # 0-10 scale, below 8.5
            "maintainability_score": 6.0,  # 0-10 scale, below 7.0
            "complexity_score": 6.0,  # 0-10 scale, above 5.0 (lower is better)
            "test_coverage_score": 7.0,  # 0-10 scale (represents 70%), below 80%
            "performance_score": 6.0  # 0-10 scale, below 7.0
        }
        
        result = gate.evaluate(scores)
        
        assert isinstance(result, QualityGateResult)
        assert result.passed is False
        assert result.overall_passed is False
        assert result.security_passed is False
        assert len(result.failures) > 0

    def test_evaluate_partial_failure(self, gate):
        """Test evaluating scores with partial failures."""
        # Use correct score keys (with _score suffix) and proper scales
        scores = {
            "overall_score": 85.0,  # 0-100 scale, passes (>= 80)
            "security_score": 7.0,  # 0-10 scale, fails (< 8.5)
            "maintainability_score": 8.0,  # 0-10 scale, passes
            "complexity_score": 4.0,  # 0-10 scale, passes (<= 5.0)
            "test_coverage_score": 8.5,  # 0-10 scale (represents 85%), passes
            "performance_score": 8.0  # 0-10 scale, passes
        }
        
        result = gate.evaluate(scores)
        
        assert isinstance(result, QualityGateResult)
        assert result.passed is False  # Security failed
        assert result.overall_passed is True
        assert result.security_passed is False
        assert "security" in result.failures[0].lower()

    def test_evaluate_custom_thresholds(self):
        """Test evaluating with custom thresholds."""
        custom_thresholds = QualityThresholds(
            overall_min=9.0,
            security_min=9.5
        )
        gate = QualityGate(thresholds=custom_thresholds)
        
        # Use correct score keys (with _score suffix) and proper scales
        scores = {
            "overall_score": 85.0,  # 0-100 scale, below custom 9.0/10 = 90/100
            "security_score": 9.0,  # 0-10 scale, below custom 9.5
            "maintainability_score": 8.0,
            "complexity_score": 4.0,
            "test_coverage_score": 8.5,
            "performance_score": 8.0
        }
        
        result = gate.evaluate(scores)
        
        assert result.passed is False
        assert result.overall_passed is False


class TestQualityGateResult:
    """Test cases for QualityGateResult."""

    def test_result_creation(self):
        """Test creating a quality gate result."""
        thresholds = QualityThresholds()
        result = QualityGateResult(
            passed=True,
            overall_passed=True,
            security_passed=True,
            maintainability_passed=True,
            complexity_passed=True,
            test_coverage_passed=True,
            performance_passed=True,
            failures=[],
            warnings=[],
            scores={"overall": 9.0},
            thresholds=thresholds
        )
        
        assert result.passed is True
        assert len(result.failures) == 0
        assert "overall" in result.scores

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        thresholds = QualityThresholds()
        result = QualityGateResult(
            passed=True,
            overall_passed=True,
            security_passed=True,
            maintainability_passed=True,
            complexity_passed=True,
            test_coverage_passed=True,
            performance_passed=True,
            failures=[],
            warnings=[],
            scores={"overall": 9.0},
            thresholds=thresholds
        )
        
        data = result.to_dict()
        
        assert data["passed"] is True
        assert "scores" in data
        assert "thresholds" in data
        assert data["thresholds"]["overall_min"] == 8.0

