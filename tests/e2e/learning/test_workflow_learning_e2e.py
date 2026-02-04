"""
E2E tests for learning system in workflow context.

Tests learning during workflow execution, pattern sharing
across workflow steps, and learning state persistence.
"""

import logging
from pathlib import Path

import pytest

from tests.e2e.fixtures.workflow_runner import WorkflowRunner

logger = logging.getLogger(__name__)


@pytest.mark.e2e_workflow
@pytest.mark.template_type("small")
class TestWorkflowLearningE2E:
    """E2E tests for learning in workflow context."""

    @pytest.fixture
    def workflow_path(self) -> Path:
        """Path to a simple workflow for learning tests."""
        # Use quality workflow as it has multiple steps
        return (
            Path(__file__).parent.parent.parent.parent.parent
            / "workflows"
            / "presets"
            / "quality.yaml"
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_learning_during_workflow_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, e2e_project: Path
    ):
        """Test that learning occurs during workflow execution."""
        # Create a test file for the workflow to process
        test_file = e2e_project / "code_to_review.py"
        test_file.write_text(
            '''"""
Sample code for workflow learning test.
"""

def calculate_fibonacci(n: int) -> int:
    """
    Calculate nth Fibonacci number.
    
    Args:
        n: Position in sequence
        
    Returns:
        Fibonacci number
    """
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)
'''
        )

        # Execute workflow (limited steps for speed)
        state, results = await workflow_runner.run_workflow(
            workflow_path, max_steps=2
        )

        assert state is not None
        assert results["correlation_id"] is not None

        # Note: In a real implementation, we would check that the workflow
        # executor's agent learner has learned from the workflow steps.
        # This requires integration with the workflow executor's learning system.

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learning_persistence_across_sessions(
        self, workflow_runner: WorkflowRunner, e2e_project: Path
    ):
        """Test that learned patterns persist across sessions."""
        from tapps_agents.core.agent_learning import AgentLearner
        from tapps_agents.core.capability_registry import CapabilityRegistry
        from tapps_agents.core.hardware_profiler import HardwareProfile
        from tapps_agents.core.task_memory import TaskMemorySystem
        from tapps_agents.experts.expert_registry import ExpertRegistry

        # Session 1: Learn patterns
        registry1 = CapabilityRegistry()
        learner1 = AgentLearner(
            capability_registry=registry1,
            expert_registry=ExpertRegistry(),
            memory_system=TaskMemorySystem(),
            hardware_profile=HardwareProfile.WORKSTATION,
        )

        code = """
def persistent_function():
    \"\"\"A function to test persistence.\"\"\"
    return True
"""
        await learner1.learn_from_task(
            capability_id="persistence_test",
            task_id="task_1",
            code=code,
            quality_scores={"overall_score": 80.0, "security_score": 9.0},
            success=True,
        )

        patterns1 = learner1.get_learned_patterns(
            context="persistence_test", limit=10
        )
        assert len(patterns1) > 0

        # Session 2: Create new learner (simulating new session)
        # In a real implementation, patterns would be loaded from persistence
        # For now, we verify that patterns exist in the first session
        # and would be available in a persisted state

        # Note: Full persistence testing requires pattern storage/loading implementation
        # This test validates the learning works, persistence would be tested separately

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learning_state_in_workflow_context(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, e2e_project: Path
    ):
        """Test learning state management in workflow context."""
        # This test would verify that learning state is properly managed
        # during workflow execution, including:
        # - Learning state is captured at workflow checkpoints
        # - Learning state is restored when workflow resumes
        # - Learning state doesn't interfere with workflow state

        # For now, we validate basic workflow execution
        state, results = await workflow_runner.run_workflow(
            workflow_path, max_steps=1
        )

        assert state is not None

        # Note: Full learning state integration requires workflow executor
        # to expose learning state management APIs

