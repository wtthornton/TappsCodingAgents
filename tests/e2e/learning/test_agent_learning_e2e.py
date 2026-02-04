"""
E2E tests for agent learning system with real agent execution.

Tests learning from actual agent tasks, pattern extraction,
and pattern reuse across multiple tasks.
"""

import logging
from pathlib import Path

import pytest

from tapps_agents.core.agent_learning import AgentLearner
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.task_memory import TaskMemorySystem
from tapps_agents.experts.expert_registry import ExpertRegistry

logger = logging.getLogger(__name__)


@pytest.mark.e2e_workflow
@pytest.mark.template_type("small")
class TestAgentLearningE2E:
    """E2E tests for agent learning with real execution."""

    @pytest.fixture
    def capability_registry(self):
        """Create a capability registry for testing."""
        return CapabilityRegistry()

    @pytest.fixture
    def expert_registry(self):
        """Create an expert registry for testing."""
        return ExpertRegistry()

    @pytest.fixture
    def task_memory_system(self):
        """Create a task memory system for testing."""
        return TaskMemorySystem()

    @pytest.fixture
    def agent_learner(
        self, capability_registry, expert_registry, task_memory_system
    ):
        """Create an AgentLearner instance for E2E testing."""
        return AgentLearner(
            capability_registry=capability_registry,
            expert_registry=expert_registry,
            memory_system=task_memory_system,
            hardware_profile=HardwareProfile.WORKSTATION,
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learn_from_successful_task(self, agent_learner, e2e_project: Path):
        """Test learning from a successful agent task."""
        # Create a simple Python file with good code
        test_file = e2e_project / "test_code.py"
        test_file.write_text(
            '''"""
A well-structured Python module.
"""

def calculate_sum(numbers: list[int]) -> int:
    """
    Calculate the sum of a list of numbers.
    
    Args:
        numbers: List of integers to sum
        
    Returns:
        Sum of all numbers
    """
    return sum(numbers)


def calculate_average(numbers: list[int]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: List of integers
        
    Returns:
        Average as a float
    """
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
'''
        )

        # Read the code
        code = test_file.read_text()

        # Learn from this task
        result = await agent_learner.learn_from_task(
            capability_id="code_generation",
            task_id="task_1",
            code=code,
            quality_scores={
                "overall_score": 85.0,
                "security_score": 9.0,
                "maintainability_score": 8.5,
            },
            success=True,
            duration=2.5,
        )

        # Verify learning occurred
        assert result["security_checked"] is True
        assert result["security_score"] >= 7.0
        assert result["patterns_extracted"] > 0

        # Verify patterns were stored
        patterns = agent_learner.get_learned_patterns(
            context="code_generation", limit=10
        )
        assert len(patterns) > 0

        # Verify capability metrics were updated
        metric = agent_learner.capability_registry.get_capability("code_generation")
        assert metric is not None
        assert metric.usage_count == 1
        assert metric.success_rate == 1.0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learn_across_multiple_tasks(
        self, agent_learner, e2e_project: Path
    ):
        """Test learning across multiple tasks and pattern reuse."""
        # Task 1: Learn a pattern
        code1 = """
def process_data(data: list) -> dict:
    \"\"\"Process data and return results.\"\"\"
    return {
        "count": len(data),
        "sum": sum(data) if data else 0,
    }
"""
        result1 = await agent_learner.learn_from_task(
            capability_id="data_processing",
            task_id="task_1",
            code=code1,
            quality_scores={"overall_score": 80.0, "security_score": 9.0},
            success=True,
        )

        assert result1["patterns_extracted"] > 0

        # Task 2: Learn another pattern
        code2 = """
def validate_input(value: str) -> bool:
    \"\"\"Validate input string.\"\"\"
    return value and len(value.strip()) > 0
"""
        result2 = await agent_learner.learn_from_task(
            capability_id="data_processing",
            task_id="task_2",
            code=code2,
            quality_scores={"overall_score": 75.0, "security_score": 8.5},
            success=True,
        )

        assert result2["patterns_extracted"] > 0

        # Verify both patterns are available
        patterns = agent_learner.get_learned_patterns(
            context="data_processing", limit=10
        )
        assert len(patterns) >= 2

        # Verify capability metrics reflect both tasks
        metric = agent_learner.capability_registry.get_capability("data_processing")
        assert metric.usage_count == 2
        assert metric.success_rate == 1.0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learn_from_failure_and_recovery(
        self, agent_learner, e2e_project: Path
    ):
        """Test learning from failures and subsequent recovery."""
        # Task 1: Failure
        bad_code = """
def broken_function():
    eval('unsafe code')
    return None
"""
        result1 = await agent_learner.learn_from_task(
            capability_id="code_generation",
            task_id="task_fail_1",
            code=bad_code,
            quality_scores={"overall_score": 30.0, "security_score": 2.0},
            success=False,
        )

        # Should extract anti-patterns
        assert result1["anti_patterns_extracted"] > 0
        assert result1["failure_analyzed"] is True

        # Task 2: Success after learning
        good_code = """
def safe_function():
    \"\"\"A safe function.\"\"\"
    return True
"""
        result2 = await agent_learner.learn_from_task(
            capability_id="code_generation",
            task_id="task_success_1",
            code=good_code,
            quality_scores={"overall_score": 85.0, "security_score": 9.0},
            success=True,
        )

        # Should extract patterns
        assert result2["patterns_extracted"] > 0

        # Verify anti-patterns are stored separately
        anti_patterns = agent_learner.anti_pattern_extractor.get_anti_patterns_for_context(
            context="code_generation", limit=5
        )
        assert len(anti_patterns) > 0

        # Verify patterns exclude anti-patterns by default
        patterns = agent_learner.get_learned_patterns(
            context="code_generation", exclude_anti_patterns=True
        )
        assert all(not p.is_anti_pattern for p in patterns)

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_pattern_retrieval_and_reuse(
        self, agent_learner, e2e_project: Path
    ):
        """Test that learned patterns can be retrieved and used."""
        # Learn a pattern
        code = """
def helper_function(x: int, y: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return x + y
"""
        await agent_learner.learn_from_task(
            capability_id="helper_functions",
            task_id="task_learn",
            code=code,
            quality_scores={"overall_score": 80.0, "security_score": 9.0},
            success=True,
        )

        # Retrieve patterns for similar context
        patterns = agent_learner.get_learned_patterns(
            context="helper_functions", limit=5
        )

        assert len(patterns) > 0
        assert all(p.quality_score >= 0.7 for p in patterns)
        assert all(p.security_score >= 7.0 for p in patterns)

        # Verify pattern metadata
        pattern = patterns[0]
        assert pattern.pattern_id is not None
        assert pattern.pattern_type in ["function", "class", "import", "structure"]
        assert pattern.code_snippet is not None
        assert pattern.usage_count >= 1
        assert pattern.success_rate >= 0.0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learning_explainability_e2e(self, agent_learner, e2e_project: Path):
        """Test learning explainability in E2E scenario."""
        code = """
def explained_function():
    \"\"\"A function for explainability testing.\"\"\"
    return True
"""
        await agent_learner.learn_from_task(
            capability_id="explainability_test",
            task_id="task_explain",
            code=code,
            quality_scores={"overall_score": 80.0, "security_score": 9.0},
            success=True,
        )

        # Get explanation
        explanation = agent_learner.explain_learning(
            capability_id="explainability_test", task_id="task_explain"
        )

        assert explanation is not None
        assert explanation["capability_id"] == "explainability_test"
        assert "decision_statistics" in explanation

        # Verify decision logging
        decision_stats = agent_learner.decision_logger.get_decision_statistics()
        assert decision_stats["total_decisions"] > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_meta_learning_optimization_e2e(
        self, agent_learner, e2e_project: Path
    ):
        """Test meta-learning optimization in E2E scenario."""
        # Perform multiple learning sessions
        for i in range(3):
            code = f"""
def function_{i}():
    \"\"\"Function {i}.\"\"\"
    return {i}
"""
            await agent_learner.learn_from_task(
                capability_id="meta_learning_test",
                task_id=f"task_{i}",
                code=code,
                quality_scores={"overall_score": 75.0 + i * 5, "security_score": 9.0},
                success=True,
            )

        # Run optimization
        optimization = await agent_learner.optimize_learning(
            capability_id="meta_learning_test"
        )

        assert optimization is not None
        assert "quality_assessment" in optimization
        assert "learning_gaps" in optimization
        assert "improvement_suggestions" in optimization

        # Verify effectiveness tracking
        effectiveness = agent_learner.effectiveness_tracker.calculate_improvement_rate(
            capability_id="meta_learning_test", days=30
        )
        assert effectiveness["sessions_count"] >= 3

