"""
Unit tests for Parallel Step Executor.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.workflow.models import StepExecution, WorkflowStep
from tapps_agents.workflow.parallel_executor import (
    ParallelStepExecutor,
    RetryConfig,
    StepExecutionResult,
)

pytestmark = pytest.mark.unit


class TestRetryConfig:
    """Test cases for RetryConfig."""

    def test_retry_config_creation(self):
        """Test creating retry config."""
        config = RetryConfig(
            max_attempts=3,
            initial_backoff_seconds=2.0,
            backoff_multiplier=2.0
        )
        
        assert config.max_attempts == 3
        assert config.initial_backoff_seconds == 2.0
        assert config.backoff_multiplier == 2.0

    def test_should_retry_max_attempts(self):
        """Test retry decision at max attempts."""
        config = RetryConfig(max_attempts=3)
        
        assert config.should_retry(3, Exception()) is False
        assert config.should_retry(4, Exception()) is False

    def test_should_retry_below_max(self):
        """Test retry decision below max attempts."""
        config = RetryConfig(max_attempts=3)
        
        assert config.should_retry(1, Exception()) is True
        assert config.should_retry(2, Exception()) is True

    def test_get_backoff_seconds(self):
        """Test backoff calculation."""
        config = RetryConfig(
            initial_backoff_seconds=1.0,
            backoff_multiplier=2.0,
            max_backoff_seconds=10.0
        )
        
        assert config.get_backoff_seconds(1) == 1.0
        assert config.get_backoff_seconds(2) == 2.0
        assert config.get_backoff_seconds(3) == 4.0
        # Should cap at max_backoff
        assert config.get_backoff_seconds(10) <= 10.0


class TestParallelStepExecutor:
    """Test cases for ParallelStepExecutor."""

    @pytest.fixture
    def executor(self):
        """Create a ParallelStepExecutor instance."""
        return ParallelStepExecutor(max_parallel=2)

    def test_executor_initialization(self, executor):
        """Test executor initialization."""
        assert executor.max_parallel == 2
        assert executor.default_timeout_seconds is not None

    def test_find_ready_steps_no_dependencies(self, executor):
        """Test finding ready steps with no dependencies."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["req"], creates=["plan"]),
        ]
        
        ready = executor.find_ready_steps(
            steps,
            completed_step_ids=set(),
            running_step_ids=set(),
            available_artifacts=set()
        )
        
        assert len(ready) == 1
        assert ready[0].id == "step1"

    def test_find_ready_steps_with_dependencies(self, executor):
        """Test finding ready steps with dependencies met."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["req"], creates=["plan"]),
        ]
        
        ready = executor.find_ready_steps(
            steps,
            completed_step_ids={"step1"},
            running_step_ids=set(),
            available_artifacts={"req"}
        )
        
        assert len(ready) == 1
        assert ready[0].id == "step2"

    def test_find_ready_steps_excludes_running(self, executor):
        """Test that running steps are excluded."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
        ]
        
        ready = executor.find_ready_steps(
            steps,
            completed_step_ids=set(),
            running_step_ids={"step1"},
            available_artifacts=set()
        )
        
        assert len(ready) == 0

    @pytest.mark.asyncio
    async def test_execute_step_success(self, executor):
        """Test executing a step successfully."""
        step = WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"])
        
        async def step_fn(step_execution):
            return {"status": "success"}
        
        result = await executor._execute_step(
            step,
            step_fn,
            retry_config=RetryConfig(max_attempts=1)
        )
        
        assert isinstance(result, StepExecutionResult)
        assert result.error is None
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_step_with_retry(self, executor):
        """Test executing a step with retry."""
        step = WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"])
        attempt_count = 0
        
        async def step_fn(step_execution):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Temporary error")
            return {"status": "success"}
        
        retry_config = RetryConfig(
            max_attempts=3,
            initial_backoff_seconds=0.1,
            retryable_errors=(Exception,)
        )
        
        result = await executor._execute_step(step, step_fn, retry_config=retry_config)
        
        assert result.error is None
        assert result.attempts == 2

