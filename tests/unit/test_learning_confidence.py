"""
Unit tests for Learning Confidence Calculator.
"""

import pytest
from tapps_agents.core.learning_confidence import (
    LearningConfidenceCalculator,
    LearnedExperienceMetrics,
    ConfidenceFactors
)


class TestLearningConfidenceCalculator:
    """Test LearningConfidenceCalculator."""
    
    def test_calculate_learned_confidence_high_values(self):
        """Test confidence calculation with high values."""
        confidence = LearningConfidenceCalculator.calculate_learned_confidence(
            usage_count=100,
            success_rate=0.9,
            quality_score=0.85,
            context_relevance=1.0
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # Should be high with good metrics
    
    def test_calculate_learned_confidence_low_values(self):
        """Test confidence calculation with low values."""
        confidence = LearningConfidenceCalculator.calculate_learned_confidence(
            usage_count=2,
            success_rate=0.3,
            quality_score=0.4,
            context_relevance=0.5
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.5  # Should be low with poor metrics
    
    def test_calculate_learned_confidence_sample_size_penalty(self):
        """Test that low sample size reduces confidence."""
        low_sample = LearningConfidenceCalculator.calculate_learned_confidence(
            usage_count=2,
            success_rate=0.9,
            quality_score=0.9,
            context_relevance=1.0,
            min_sample_size=5
        )
        
        high_sample = LearningConfidenceCalculator.calculate_learned_confidence(
            usage_count=50,
            success_rate=0.9,
            quality_score=0.9,
            context_relevance=1.0,
            min_sample_size=5
        )
        
        assert high_sample > low_sample
    
    def test_calculate_learned_confidence_normalization(self):
        """Test that confidence is normalized to 0-1 range."""
        # Test with extreme values
        confidence = LearningConfidenceCalculator.calculate_learned_confidence(
            usage_count=1000,
            success_rate=1.5,  # Out of range
            quality_score=-0.5,  # Out of range
            context_relevance=2.0  # Out of range
        )
        
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_best_practice_confidence(self):
        """Test best practice confidence calculation."""
        # Mock ConsultationResult
        class MockConsultationResult:
            def __init__(self, confidence):
                self.confidence = confidence
        
        result = MockConsultationResult(0.85)
        confidence = LearningConfidenceCalculator.calculate_best_practice_confidence(result)
        
        assert confidence == 0.85
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_best_practice_confidence_none(self):
        """Test best practice confidence with None."""
        confidence = LearningConfidenceCalculator.calculate_best_practice_confidence(None)
        assert confidence == 0.0
    
    def test_combine_confidence_high_learned(self):
        """Test combining confidence when learned is high."""
        combined = LearningConfidenceCalculator.combine_confidence(
            learned_confidence=0.9,
            best_practice_confidence=0.7
        )
        
        assert 0.0 <= combined <= 1.0
        # Should be closer to learned (0.9) due to high learned confidence
        assert combined > 0.8
    
    def test_combine_confidence_high_best_practice(self):
        """Test combining confidence when best practice is high."""
        combined = LearningConfidenceCalculator.combine_confidence(
            learned_confidence=0.6,
            best_practice_confidence=0.8
        )
        
        assert 0.0 <= combined <= 1.0
        # Should be closer to best practice (0.8) due to high best practice confidence
        assert combined > 0.7
    
    def test_combine_confidence_equal_weight(self):
        """Test combining confidence with moderate values (equal weight)."""
        combined = LearningConfidenceCalculator.combine_confidence(
            learned_confidence=0.65,
            best_practice_confidence=0.65
        )
        
        assert 0.0 <= combined <= 1.0
        # Should be around average
        assert 0.6 <= combined <= 0.7
    
    def test_combine_confidence_no_best_practice(self):
        """Test combining confidence when best practice is None."""
        combined = LearningConfidenceCalculator.combine_confidence(
            learned_confidence=0.75,
            best_practice_confidence=None
        )
        
        assert combined == 0.75
    
    def test_combine_confidence_with_context(self):
        """Test combining confidence with context factors."""
        combined = LearningConfidenceCalculator.combine_confidence(
            learned_confidence=0.8,
            best_practice_confidence=0.7,
            context_factors={"relevance": 0.9}
        )
        
        assert 0.0 <= combined <= 1.0
    
    def test_calculate_from_metrics(self):
        """Test calculating confidence from LearnedExperienceMetrics."""
        metrics = LearnedExperienceMetrics(
            usage_count=50,
            success_rate=0.85,
            quality_score=0.8,
            sample_size=10
        )
        
        confidence = LearningConfidenceCalculator.calculate_from_metrics(metrics)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be good with these metrics

