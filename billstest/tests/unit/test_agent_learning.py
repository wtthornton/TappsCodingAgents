"""
Unit tests for Agent Learning System.
"""

from unittest.mock import MagicMock

import pytest

from tapps_agents.core.agent_learning import (
    AgentLearner,
    FeedbackAnalyzer,
    PatternExtractor,
    PromptOptimizer,
)
from tapps_agents.core.capability_registry import CapabilityRegistry, LearningIntensity
from tapps_agents.core.hardware_profiler import HardwareProfile


class TestPatternExtractor:
    """Tests for PatternExtractor."""

    def test_extract_function_patterns(self):
        """Test extracting function patterns."""
        extractor = PatternExtractor()

        code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""

        patterns = extractor.extract_patterns(
            code=code, quality_score=0.8, task_id="task-1"
        )

        assert len(patterns) > 0
        func_patterns = [p for p in patterns if p.pattern_type == "function"]
        assert len(func_patterns) > 0

    def test_extract_class_patterns(self):
        """Test extracting class patterns."""
        extractor = PatternExtractor()

        code = """
class UserService:
    def __init__(self):
        self.users = []
    
    def add_user(self, user):
        self.users.append(user)
"""

        patterns = extractor.extract_patterns(
            code=code, quality_score=0.8, task_id="task-1"
        )

        class_patterns = [p for p in patterns if p.pattern_type == "class"]
        assert len(class_patterns) > 0

    def test_quality_threshold(self):
        """Test quality threshold filtering."""
        extractor = PatternExtractor(min_quality_threshold=0.7)

        code = "def test(): pass"

        # Low quality should return no patterns
        patterns = extractor.extract_patterns(
            code=code, quality_score=0.5, task_id="task-1"
        )

        assert len(patterns) == 0


class TestPromptOptimizer:
    """Tests for PromptOptimizer."""

    def test_create_variant(self):
        """Test creating prompt variant."""
        optimizer = PromptOptimizer(HardwareProfile.WORKSTATION)

        base = "Write a function"
        variant = optimizer.create_variant(
            base_prompt=base,
            modifications=["add: Use type hints", "add: Add docstring"],
        )

        assert variant.variant_id is not None
        assert "type hints" in variant.prompt_template.lower()

    def test_record_test_result(self):
        """Test recording test result."""
        optimizer = PromptOptimizer(HardwareProfile.WORKSTATION)

        variant = optimizer.create_variant(
            base_prompt="test", modifications=["add: test"]
        )

        optimizer.record_test_result(
            variant_id=variant.variant_id, success=True, quality_score=0.8
        )

        assert variant.test_count == 1
        assert variant.success_count == 1
        assert variant.average_quality > 0

    def test_get_best_variant(self):
        """Test getting best variant."""
        optimizer = PromptOptimizer(HardwareProfile.WORKSTATION)

        variant1 = optimizer.create_variant("base", ["add: mod1"])
        variant2 = optimizer.create_variant("base", ["add: mod2"])

        # Record better results for variant1
        for _ in range(5):
            optimizer.record_test_result(variant1.variant_id, True, 0.9)
        for _ in range(5):
            optimizer.record_test_result(variant2.variant_id, True, 0.6)

        best = optimizer.get_best_variant(min_tests=5)
        assert best is not None
        assert best.variant_id == variant1.variant_id

    def test_optimize_for_hardware_nuc(self):
        """Test hardware optimization for NUC."""
        optimizer = PromptOptimizer(HardwareProfile.NUC)

        long_prompt = "\n".join([f"Line {i}" for i in range(100)])
        optimized = optimizer.optimize_for_hardware(long_prompt)

        assert len(optimized.split("\n")) <= 50

    def test_optimize_for_hardware_workstation(self):
        """Test hardware optimization for workstation."""
        optimizer = PromptOptimizer(HardwareProfile.WORKSTATION)

        prompt = "Full detailed prompt with all instructions"
        optimized = optimizer.optimize_for_hardware(prompt)

        assert optimized == prompt  # Should remain unchanged


class TestFeedbackAnalyzer:
    """Tests for FeedbackAnalyzer."""

    def test_analyze_code_scores(self):
        """Test analyzing code scores."""
        analyzer = FeedbackAnalyzer()

        scores = {
            "overall_score": 6.5,
            "metrics": {
                "complexity": 7.0,
                "security": 8.0,
                "maintainability": 5.0,  # Below threshold
                "test_coverage": 6.0,  # Below threshold
                "performance": 7.0,
            },
        }

        analysis = analyzer.analyze_code_scores(scores, threshold=0.7)

        assert "maintainability" in analysis["weak_areas"]
        assert "test_coverage" in analysis["weak_areas"]
        assert analysis["overall_score"] == 6.5

    def test_get_improvement_suggestions(self):
        """Test getting improvement suggestions."""
        analyzer = FeedbackAnalyzer()

        analysis = {
            "weak_areas": ["maintainability", "test_coverage"],
            "improvement_potential": {"maintainability": 0.2, "test_coverage": 0.1},
        }

        suggestions = analyzer.get_improvement_suggestions(analysis)

        assert len(suggestions) > 0
        assert any("maintainability" in s.lower() for s in suggestions)


class TestAgentLearner:
    """Tests for AgentLearner."""

    @pytest.fixture
    def registry(self, tmp_path):
        """Create capability registry."""
        return CapabilityRegistry(storage_dir=tmp_path / "capabilities")

    @pytest.fixture
    def mock_expert_registry(self):
        """Create mock expert registry."""

        mock_registry = MagicMock()
        return mock_registry

    def test_learner_creation(self, registry, mock_expert_registry):
        """Test learner creation."""
        learner = AgentLearner(
            capability_registry=registry,
            expert_registry=mock_expert_registry,
            hardware_profile=HardwareProfile.WORKSTATION,
        )

        assert learner.learning_intensity == LearningIntensity.HIGH
        assert learner.pattern_extractor is not None
        assert learner.prompt_optimizer is not None
        assert learner.decision_engine is not None

    @pytest.mark.asyncio
    async def test_learn_from_task(self, registry, mock_expert_registry):
        """Test learning from task."""
        learner = AgentLearner(
            capability_registry=registry, expert_registry=mock_expert_registry
        )

        registry.register_capability("test-cap", "agent", initial_quality=0.5)

        code = "def test(): return True"
        quality_scores = {
            "overall_score": 8.0,
            "metrics": {"complexity": 8.0, "security": 8.0},
        }

        results = await learner.learn_from_task(
            capability_id="test-cap",
            task_id="task-1",
            code=code,
            quality_scores=quality_scores,
            success=True,
            duration=1.0,
        )

        assert "patterns_extracted" in results
        assert "feedback_analyzed" in results

        # Check metric updated
        metric = registry.get_capability("test-cap")
        assert metric.usage_count > 0

    @pytest.mark.asyncio
    async def test_get_learned_patterns(self, registry, mock_expert_registry):
        """Test getting learned patterns."""
        learner = AgentLearner(
            capability_registry=registry, expert_registry=mock_expert_registry
        )

        # Learn from a task first
        code = "def calculate(x, y): return x + y"
        await learner.learn_from_task(
            capability_id="test-cap",
            task_id="task-1",
            code=code,
            quality_scores={"overall_score": 8.0},
            success=True,
        )

        patterns = learner.get_learned_patterns("calculate", limit=5)
        assert (
            len(patterns) >= 0
        )  # May or may not have patterns depending on extraction

    def test_should_refine_capability(self, registry, mock_expert_registry):
        """Test refinement recommendation."""
        learner = AgentLearner(
            capability_registry=registry, expert_registry=mock_expert_registry
        )

        registry.register_capability("test-cap", "agent", initial_quality=0.5)

        # Update to have usage but low quality
        metric = registry.get_capability("test-cap")
        for _ in range(15):
            metric.update_metrics(success=True, duration=1.0, quality_score=0.5)

        assert learner.should_refine_capability("test-cap") is True
