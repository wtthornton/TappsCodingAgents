"""
Unit tests for progress update system (Story 8.1).
"""

from datetime import datetime

import pytest

from tapps_agents.workflow.models import StepExecution, WorkflowState
from tapps_agents.workflow.progress_updates import (
    ProgressCalculator,
    ProgressUpdate,
    ProgressUpdateGenerator,
    UpdatePriority,
    UpdateQueue,
    UpdateType,
)


@pytest.fixture
def sample_state():
    """Create a sample workflow state for testing."""
    state = WorkflowState(
        workflow_id="test-workflow-1",
        started_at=datetime.now(),
        current_step="step-2",
        completed_steps=["step-1"],
        skipped_steps=[],
        status="running",
    )
    state.step_executions = [
        StepExecution(
            step_id="step-1",
            agent="dev",
            action="implement",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
        ),
        StepExecution(
            step_id="step-2",
            agent="qa",
            action="test",
            started_at=datetime.now(),
            status="running",
        ),
    ]
    return state


@pytest.mark.unit
class TestProgressCalculator:
    """Tests for ProgressCalculator."""

    def test_calculate_progress_basic(self, sample_state):
        """Test basic progress calculation."""
        calculator = ProgressCalculator(total_steps=5)
        progress = calculator.calculate_progress(sample_state)

        assert progress["total_steps"] == 5
        assert progress["completed"] == 1
        assert progress["running"] == 1
        assert progress["percentage"] == 20.0  # 1/5 = 20%

    def test_calculate_progress_no_steps(self):
        """Test progress calculation with no steps."""
        state = WorkflowState(
            workflow_id="test",
            started_at=datetime.now(),
            status="running",
        )
        calculator = ProgressCalculator(total_steps=0)
        progress = calculator.calculate_progress(state)

        assert progress["percentage"] == 0.0
        assert progress["total_steps"] == 0

    def test_calculate_progress_all_completed(self):
        """Test progress calculation when all steps completed."""
        state = WorkflowState(
            workflow_id="test",
            started_at=datetime.now(),
            completed_steps=["step-1", "step-2", "step-3"],
            status="completed",
        )
        calculator = ProgressCalculator(total_steps=3)
        progress = calculator.calculate_progress(state)

        assert progress["completed"] == 3
        assert progress["percentage"] == 100.0

    def test_calculate_progress_with_skipped(self):
        """Test progress calculation with skipped steps."""
        state = WorkflowState(
            workflow_id="test",
            started_at=datetime.now(),
            completed_steps=["step-1"],
            skipped_steps=["step-2"],
            status="running",
        )
        calculator = ProgressCalculator(total_steps=3)
        progress = calculator.calculate_progress(state)

        assert progress["completed"] == 1
        assert progress["skipped"] == 1
        assert progress["percentage"] == pytest.approx(66.67, rel=0.01)  # 2/3


@pytest.mark.unit
class TestProgressUpdateGenerator:
    """Tests for ProgressUpdateGenerator."""

    def test_generate_update_step_started(self, sample_state):
        """Test generating step started update."""
        calculator = ProgressCalculator(total_steps=5)
        generator = ProgressUpdateGenerator(calculator)

        update = generator.generate_update(
            update_type=UpdateType.STEP_STARTED,
            state=sample_state,
            step_id="step-2",
            agent="qa",
            action="test",
        )

        assert update.update_type == UpdateType.STEP_STARTED
        assert update.agent == "qa"
        assert update.action == "test"
        assert update.priority == UpdatePriority.HIGH

    def test_generate_update_workflow_completed(self, sample_state):
        """Test generating workflow completed update."""
        calculator = ProgressCalculator(total_steps=5)
        generator = ProgressUpdateGenerator(calculator)
        sample_state.status = "completed"

        update = generator.generate_update(
            update_type=UpdateType.WORKFLOW_COMPLETED,
            state=sample_state,
        )

        assert update.update_type == UpdateType.WORKFLOW_COMPLETED
        assert update.priority == UpdatePriority.CRITICAL

    def test_generate_update_with_error(self, sample_state):
        """Test generating update with error."""
        calculator = ProgressCalculator(total_steps=5)
        generator = ProgressUpdateGenerator(calculator)

        update = generator.generate_update(
            update_type=UpdateType.STEP_FAILED,
            state=sample_state,
            error="Test error message",
        )

        assert update.update_type == UpdateType.STEP_FAILED
        assert update.error == "Test error message"
        assert update.priority == UpdatePriority.CRITICAL

    def test_format_for_chat_basic(self):
        """Test formatting update for chat."""
        calculator = ProgressCalculator(total_steps=5)
        generator = ProgressUpdateGenerator(calculator)

        update = ProgressUpdate(
            update_type=UpdateType.STEP_STARTED,
            timestamp=datetime.now(),
            step_number=2,
            total_steps=5,
            percentage=40.0,
            status="running",
            agent="dev",
            action="implement",
            step_id="step-2",
        )

        formatted = generator.format_for_chat(update)
        assert "Step Started" in formatted
        assert "Step 2 of 5" in formatted
        assert "40.0%" in formatted
        assert "dev" in formatted
        assert "implement" in formatted

    def test_format_for_chat_progress_bar(self):
        """Test progress bar generation."""
        calculator = ProgressCalculator(total_steps=10)
        generator = ProgressUpdateGenerator(calculator)

        update = ProgressUpdate(
            update_type=UpdateType.STEP_PROGRESS,
            timestamp=datetime.now(),
            percentage=75.0,
        )

        formatted = generator.format_for_chat(update)
        assert "75.0%" in formatted
        assert "█" in formatted  # Progress bar character

    def test_format_for_chat_with_error(self):
        """Test formatting update with error."""
        calculator = ProgressCalculator(total_steps=5)
        generator = ProgressUpdateGenerator(calculator)

        update = ProgressUpdate(
            update_type=UpdateType.STEP_FAILED,
            timestamp=datetime.now(),
            error="Test error",
        )

        formatted = generator.format_for_chat(update)
        assert "Step Failed" in formatted
        assert "Test error" in formatted


@pytest.mark.unit
class TestUpdateQueue:
    """Tests for UpdateQueue."""

    def test_add_critical_update_immediate(self):
        """Test that critical updates are sent immediately."""
        queue = UpdateQueue(min_interval_seconds=10.0)
        update = ProgressUpdate(
            update_type=UpdateType.WORKFLOW_FAILED,
            timestamp=datetime.now(),
            priority=UpdatePriority.CRITICAL,
        )

        assert queue.add_update(update) is True

    def test_add_normal_update_throttled(self):
        """Test that normal updates are throttled."""
        queue = UpdateQueue(min_interval_seconds=1.0)
        update1 = ProgressUpdate(
            update_type=UpdateType.STEP_PROGRESS,
            timestamp=datetime.now(),
            priority=UpdatePriority.NORMAL,
        )
        update2 = ProgressUpdate(
            update_type=UpdateType.STEP_PROGRESS,
            timestamp=datetime.now(),
            priority=UpdatePriority.NORMAL,
        )

        # First update should be sent
        assert queue.add_update(update1) is True
        # Second update should be queued (within interval)
        assert queue.add_update(update2) is False

    def test_get_queued_updates(self):
        """Test getting queued updates."""
        queue = UpdateQueue(min_interval_seconds=0.1)
        update = ProgressUpdate(
            update_type=UpdateType.STEP_PROGRESS,
            timestamp=datetime.now(),
            priority=UpdatePriority.NORMAL,
        )

        # Add update (will be queued if interval not met)
        sent = queue.add_update(update)
        # If sent immediately, queue another one
        if sent:
            update2 = ProgressUpdate(
                update_type=UpdateType.STEP_PROGRESS,
                timestamp=datetime.now(),
                priority=UpdatePriority.NORMAL,
            )
            queue.add_update(update2)
        
        # Should have at least one queued update
        assert len(queue.queue) > 0
        
        # Should be able to get it after interval
        import time
        time.sleep(0.15)
        queued = queue.get_queued_updates()
        assert len(queued) > 0

    def test_flush_queue(self):
        """Test flushing queue."""
        queue = UpdateQueue(min_interval_seconds=10.0)  # Large interval to force queuing
        updates = [
            ProgressUpdate(
                update_type=UpdateType.STEP_PROGRESS,
                timestamp=datetime.now(),
                priority=UpdatePriority.NORMAL,
            )
            for _ in range(3)
        ]

        # First update might be sent, rest should be queued
        for update in updates:
            queue.add_update(update)

        # Flush should return all queued updates
        flushed = queue.flush_queue()
        # Should have at least the updates that were queued
        assert len(flushed) >= 2  # At least 2 should be queued
        assert len(queue.queue) == 0

    def test_rate_limiting(self):
        """Test rate limiting."""
        queue = UpdateQueue(max_updates_per_minute=2)
        updates = [
            ProgressUpdate(
                update_type=UpdateType.STEP_PROGRESS,
                timestamp=datetime.now(),
                priority=UpdatePriority.NORMAL,
            )
            for _ in range(5)
        ]

        sent_count = 0
        for update in updates:
            if queue.add_update(update):
                sent_count += 1

        # Should respect rate limit
        assert sent_count <= 2

