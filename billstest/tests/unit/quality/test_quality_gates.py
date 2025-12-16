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
        scores = {
            "overall": 9.0,
            "security": 9.5,
            "maintainability": 8.0,
            "complexity": 4.0,
            "test_coverage": 85.0,
            "performance": 8.0
        }
        
        result = gate.evaluate(scores)
        
        assert isinstance(result, QualityGateResult)
        assert result.passed is True
        assert result.overall_passed is True
        assert result.security_passed is True
        assert len(result.failures) == 0

    def test_evaluate_failing_scores(self, gate):
        """Test evaluating failing scores."""
        scores = {
            "overall": 7.0,  # Below 8.0
            "security": 7.0,  # Below 8.5
            "maintainability": 6.0,  # Below 7.0
            "complexity": 6.0,  # Above 5.0
            "test_coverage": 70.0,  # Below 80.0
            "performance": 6.0  # Below 7.0
        }
        
        result = gate.evaluate(scores)
        
        assert isinstance(result, QualityGateResult)
        assert result.passed is False
        assert result.overall_passed is False
        assert result.security_passed is False
        assert len(result.failures) > 0

    def test_evaluate_partial_failure(self, gate):
        """Test evaluating scores with partial failures."""
        scores = {
            "overall": 8.5,  # Pass
            "security": 7.0,  # Fail
            "maintainability": 8.0,  # Pass
            "complexity": 4.0,  # Pass
            "test_coverage": 85.0,  # Pass
            "performance": 8.0  # Pass
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
        
        scores = {
            "overall": 8.5,  # Below custom 9.0
            "security": 9.0,  # Below custom 9.5
            "maintainability": 8.0,
            "complexity": 4.0,
            "test_coverage": 85.0,
            "performance": 8.0
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

