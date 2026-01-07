"""Tests for step_dependencies module."""

import pytest

from tapps_agents.simple_mode.step_dependencies import (
    STEP_BY_AGENT,
    STEP_BY_NUMBER,
    WORKFLOW_STEPS,
    StepDefinition,
    StepDependencyManager,
    StepExecutionState,
    WorkflowStep,
    get_agent_for_step,
    get_step_for_agent,
)


class TestWorkflowStep:
    """Tests for WorkflowStep enum."""

    def test_step_ordering(self):
        """Test that steps have correct numeric values."""
        assert WorkflowStep.ENHANCER == 1
        assert WorkflowStep.PLANNER == 2
        assert WorkflowStep.ARCHITECT == 3
        assert WorkflowStep.DESIGNER == 4
        assert WorkflowStep.IMPLEMENTER == 5
        assert WorkflowStep.REVIEWER == 6
        assert WorkflowStep.TESTER == 7
        assert WorkflowStep.VERIFICATION == 8


class TestStepDefinition:
    """Tests for StepDefinition model."""

    def test_create_step(self):
        """Test creating step definition."""
        step = StepDefinition(
            step=WorkflowStep.ENHANCER,
            agent_name="enhancer",
            command="enhance",
        )
        assert step.step == WorkflowStep.ENHANCER
        assert step.agent_name == "enhancer"
        assert len(step.dependencies) == 0

    def test_create_step_with_dependencies(self):
        """Test creating step with dependencies."""
        step = StepDefinition(
            step=WorkflowStep.PLANNER,
            agent_name="planner",
            command="create-story",
            dependencies=[WorkflowStep.ENHANCER],
        )
        assert WorkflowStep.ENHANCER in step.dependencies


class TestStepExecutionState:
    """Tests for StepExecutionState."""

    def test_initial_state(self):
        """Test initial state is empty."""
        state = StepExecutionState()
        assert len(state.completed) == 0
        assert len(state.failed) == 0
        assert len(state.skipped) == 0

    def test_mark_completed(self):
        """Test marking step as completed."""
        state = StepExecutionState()
        state.mark_completed(WorkflowStep.ENHANCER, {"result": "done"})
        assert WorkflowStep.ENHANCER in state.completed
        assert state.results[WorkflowStep.ENHANCER] == {"result": "done"}

    def test_mark_failed(self):
        """Test marking step as failed."""
        state = StepExecutionState()
        state.mark_failed(WorkflowStep.ARCHITECT, "Unknown command")
        assert WorkflowStep.ARCHITECT in state.failed
        assert "error" in state.results[WorkflowStep.ARCHITECT]

    def test_mark_skipped(self):
        """Test marking step as skipped."""
        state = StepExecutionState()
        state.mark_skipped(WorkflowStep.DESIGNER, "Dependency failed")
        assert WorkflowStep.DESIGNER in state.skipped
        assert "skipped" in state.results[WorkflowStep.DESIGNER]

    def test_mark_running(self):
        """Test marking step as running."""
        state = StepExecutionState()
        state.mark_running(WorkflowStep.ENHANCER)
        assert WorkflowStep.ENHANCER in state.running

    def test_all_processed(self):
        """Test all_processed property."""
        state = StepExecutionState()
        state.mark_completed(WorkflowStep.ENHANCER)
        state.mark_failed(WorkflowStep.ARCHITECT)
        state.mark_skipped(WorkflowStep.DESIGNER)
        
        processed = state.all_processed
        assert WorkflowStep.ENHANCER in processed
        assert WorkflowStep.ARCHITECT in processed
        assert WorkflowStep.DESIGNER in processed

    def test_has_critical_failures(self):
        """Test detecting critical failures."""
        state = StepExecutionState()
        state.mark_failed(WorkflowStep.IMPLEMENTER)
        assert state.has_critical_failures()


class TestStepDependencyManager:
    """Tests for StepDependencyManager."""

    @pytest.fixture
    def manager(self):
        """Create dependency manager."""
        return StepDependencyManager()

    def test_should_skip_no_failures(self, manager):
        """Test that step shouldn't skip with no failures."""
        state = StepExecutionState()
        state.mark_completed(WorkflowStep.ENHANCER)
        
        # Planner depends on Enhancer, which completed
        should_skip = manager.should_skip_step(WorkflowStep.PLANNER, state)
        assert not should_skip

    def test_should_skip_dependency_failed(self, manager):
        """Test that step should skip when dependency fails."""
        state = StepExecutionState()
        state.mark_failed(WorkflowStep.ENHANCER)
        
        # Planner depends on Enhancer, which failed
        should_skip = manager.should_skip_step(WorkflowStep.PLANNER, state)
        assert should_skip

    def test_get_skip_reason_single(self, manager):
        """Test skip reason for single failure."""
        state = StepExecutionState()
        state.mark_failed(WorkflowStep.ARCHITECT)
        
        reason = manager.get_skip_reason(WorkflowStep.DESIGNER, state)
        assert "Dependency step 3" in reason

    def test_get_skip_reason_multiple(self, manager):
        """Test skip reason for multiple failures."""
        state = StepExecutionState()
        state.mark_failed(WorkflowStep.PLANNER)
        state.mark_failed(WorkflowStep.DESIGNER)
        
        # Implementer depends on both Planner and Designer
        reason = manager.get_skip_reason(WorkflowStep.IMPLEMENTER, state)
        assert "Multiple dependencies failed" in reason

    def test_get_executable_steps_initial(self, manager):
        """Test getting executable steps at start."""
        state = StepExecutionState()
        executable = manager.get_executable_steps(state)
        
        # Only Enhancer has no dependencies
        assert WorkflowStep.ENHANCER in executable
        assert WorkflowStep.PLANNER not in executable

    def test_get_executable_steps_after_enhancer(self, manager):
        """Test getting executable steps after enhancer completes."""
        state = StepExecutionState()
        state.mark_completed(WorkflowStep.ENHANCER)
        
        executable = manager.get_executable_steps(state)
        # Planner and Architect both depend on Enhancer
        assert WorkflowStep.PLANNER in executable
        assert WorkflowStep.ARCHITECT in executable

    def test_get_parallel_steps(self, manager):
        """Test getting steps that can run in parallel."""
        state = StepExecutionState()
        state.mark_completed(WorkflowStep.ENHANCER)
        state.mark_completed(WorkflowStep.PLANNER)
        state.mark_completed(WorkflowStep.ARCHITECT)
        state.mark_completed(WorkflowStep.DESIGNER)
        state.mark_completed(WorkflowStep.IMPLEMENTER)
        
        # Reviewer and Tester can run in parallel
        parallel = manager.get_parallel_steps(state)
        assert WorkflowStep.REVIEWER in parallel
        assert WorkflowStep.TESTER in parallel

    def test_get_dependent_steps(self, manager):
        """Test getting dependent steps."""
        dependents = manager.get_dependent_steps(WorkflowStep.ENHANCER)
        # Planner and Architect depend on Enhancer
        assert WorkflowStep.PLANNER in dependents
        assert WorkflowStep.ARCHITECT in dependents

    def test_get_steps_to_skip_on_failure(self, manager):
        """Test getting all steps to skip after failure."""
        to_skip = manager.get_steps_to_skip_on_failure(WorkflowStep.ARCHITECT)
        # Designer depends on Architect, Implementer depends on Designer
        assert WorkflowStep.DESIGNER in to_skip

    def test_get_step_order(self, manager):
        """Test getting topologically sorted step order."""
        order = manager.get_step_order()
        
        # Enhancer must come first
        assert order[0] == WorkflowStep.ENHANCER
        # Verification must come last
        assert order[-1] == WorkflowStep.VERIFICATION
        
        # Check that dependencies come before dependents
        enhancer_idx = order.index(WorkflowStep.ENHANCER)
        planner_idx = order.index(WorkflowStep.PLANNER)
        assert enhancer_idx < planner_idx

    def test_validate_dag(self, manager):
        """Test DAG validation."""
        errors = manager.validate_dag()
        assert len(errors) == 0


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_step_for_agent(self):
        """Test getting step for agent name."""
        step = get_step_for_agent("architect")
        assert step == WorkflowStep.ARCHITECT

    def test_get_step_for_unknown_agent(self):
        """Test getting step for unknown agent."""
        step = get_step_for_agent("unknown")
        assert step is None

    def test_get_agent_for_step(self):
        """Test getting agent for step."""
        agent = get_agent_for_step(WorkflowStep.DESIGNER)
        assert agent == "designer"

    def test_step_by_number_index(self):
        """Test step by number index."""
        step_def = STEP_BY_NUMBER[WorkflowStep.IMPLEMENTER]
        assert step_def.agent_name == "implementer"

    def test_step_by_agent_index(self):
        """Test step by agent index."""
        step_def = STEP_BY_AGENT["reviewer"]
        assert step_def.step == WorkflowStep.REVIEWER
