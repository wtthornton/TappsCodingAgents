"""
Example usage of LongDurationManager for 30+ hour operations.

This demonstrates how to use the LongDurationManager for tasks that run
for extended periods with automatic checkpointing, failure recovery, and
progress tracking.
"""

import time
import traceback
from datetime import UTC, datetime

from tapps_agents.core import (
    CheckpointManager,
    DurabilityLevel,
    LongDurationManager,
    SessionManager,
)


def simulate_long_task(
    manager: LongDurationManager, task_id: str, duration_hours: float = 0.1
):
    """
    Simulate a long-running task with progress updates.

    Args:
        manager: LongDurationManager instance
        task_id: Task ID
        duration_hours: Duration in hours (default 0.1 = 6 minutes for demo)
    """
    total_steps = 100
    step_duration = (duration_hours * 3600) / total_steps  # seconds per step

    print(f"Starting long task: {task_id}")
    print(f"Total steps: {total_steps}")
    print(f"Step duration: {step_duration:.2f} seconds")
    print()

    for step in range(1, total_steps + 1):
        # Simulate work
        time.sleep(step_duration)

        # Update progress
        progress = step / total_steps
        manager.update_progress(
            task_id=task_id,
            progress=progress,
            current_step=f"Processing step {step}/{total_steps}",
            steps_completed=step,
            total_steps=total_steps,
            context={
                "current_step": step,
                "last_update": datetime.now(UTC).isoformat(),
            },
        )

        # Print progress every 10 steps
        if step % 10 == 0:
            snapshot = manager.get_progress_snapshot(task_id)
            if snapshot:
                print(
                    f"Progress: {snapshot.progress * 100:.1f}% - {snapshot.current_step}"
                )
                if snapshot.estimated_remaining:
                    print(f"  Estimated remaining: {snapshot.estimated_remaining}")
                print()

        # Simulate occasional failures (for demo purposes)
        if step == 50:
            print("Simulating failure at step 50...")
            try:
                raise Exception("Simulated failure for demonstration")
            except Exception as e:
                manager.handle_failure(
                    task_id=task_id,
                    failure_type="simulated_error",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                )
                print("Failure recorded. Recovering from checkpoint...")

                # Recover from checkpoint
                checkpoint = manager.recover_from_failure(task_id)
                if checkpoint:
                    print(
                        f"Recovered from checkpoint at {checkpoint.progress * 100:.1f}%"
                    )
                    print(
                        f"Resuming from step {int(checkpoint.progress * total_steps)}"
                    )
                    # In real scenario, you would restore state from checkpoint
                    # and continue from there
                print()

    # Complete task
    manager.complete_task(
        task_id=task_id,
        final_context={
            "completed_at": datetime.now(UTC).isoformat(),
            "total_steps": total_steps,
        },
    )
    print(f"Task {task_id} completed!")


def example_basic_usage():
    """Example 1: Basic long-duration task."""
    print("=" * 60)
    print("Example 1: Basic Long-Duration Task")
    print("=" * 60)
    print()

    # Initialize components
    session_manager = SessionManager()
    checkpoint_manager = CheckpointManager()

    # Create long-duration manager
    manager = LongDurationManager(
        session_manager=session_manager, checkpoint_manager=checkpoint_manager
    )

    # Start task
    task_id = manager.start_long_duration_task(
        task_id="example-task-1",
        agent_id="example-agent",
        command="process_data",
        durability_level=DurabilityLevel.STANDARD,
        initial_context={
            "started_at": datetime.now(UTC).isoformat(),
            "task_type": "data_processing",
        },
    )

    print(f"Started task: {task_id}")
    print()

    # Simulate long task
    simulate_long_task(manager, task_id, duration_hours=0.05)  # 3 minutes for demo

    # Get final snapshot
    snapshot = manager.get_progress_snapshot(task_id)
    if snapshot:
        print(f"\nFinal Progress: {snapshot.progress * 100:.1f}%")
        print(f"Elapsed Time: {snapshot.elapsed_time}")

    print()


def example_context_manager():
    """Example 2: Using context manager for automatic cleanup."""
    print("=" * 60)
    print("Example 2: Context Manager Usage")
    print("=" * 60)
    print()

    session_manager = SessionManager()
    checkpoint_manager = CheckpointManager()

    # Use context manager for automatic cleanup
    with LongDurationManager(
        session_manager=session_manager, checkpoint_manager=checkpoint_manager
    ) as manager:
        task_id = manager.start_long_duration_task(
            task_id="example-task-2",
            agent_id="example-agent",
            command="analyze_codebase",
            durability_level=DurabilityLevel.HIGH,  # High durability for critical task
            initial_context={"codebase_path": "/path/to/code"},
        )

        print(f"Started task: {task_id}")
        print("Using HIGH durability (2 min checkpoints + artifact backup)")
        print()

        # Simulate task
        simulate_long_task(manager, task_id, duration_hours=0.05)

    # Context manager automatically stops checkpoint thread
    print("Context manager cleaned up automatically")
    print()


def example_progress_tracking():
    """Example 3: Progress tracking and velocity calculation."""
    print("=" * 60)
    print("Example 3: Progress Tracking")
    print("=" * 60)
    print()

    session_manager = SessionManager()
    checkpoint_manager = CheckpointManager()
    manager = LongDurationManager(
        session_manager=session_manager, checkpoint_manager=checkpoint_manager
    )

    task_id = manager.start_long_duration_task(
        task_id="example-task-3",
        agent_id="example-agent",
        command="build_system",
        durability_level=DurabilityLevel.BASIC,
    )

    # Make several progress updates
    for i in range(1, 6):
        manager.update_progress(
            task_id=task_id,
            progress=i * 0.2,
            current_step=f"Phase {i}",
            steps_completed=i,
            total_steps=5,
        )
        time.sleep(1)  # Small delay to see velocity calculation

    # Get progress snapshot
    snapshot = manager.get_progress_snapshot(task_id)
    if snapshot:
        print("Progress Snapshot:")
        print(f"  Progress: {snapshot.progress * 100:.1f}%")
        print(f"  Current Step: {snapshot.current_step}")
        print(f"  Steps: {snapshot.steps_completed}/{snapshot.total_steps}")
        print(f"  Elapsed: {snapshot.elapsed_time}")
        if snapshot.estimated_remaining:
            print(f"  Estimated Remaining: {snapshot.estimated_remaining}")
        print()

    # Get progress history
    history = manager.get_progress_history(task_id, limit=5)
    print("Recent Progress History:")
    for entry in history:
        print(
            f"  {entry.timestamp.strftime('%H:%M:%S')}: {entry.progress * 100:.1f}% - {entry.current_step}"
        )
    print()

    # Calculate velocity
    velocity = manager.calculate_progress_velocity(task_id)
    if velocity:
        print("Progress Velocity:")
        print(f"  Progress per hour: {velocity.progress_per_hour:.2f}%")
        if velocity.estimated_completion_time:
            print(f"  Estimated completion: {velocity.estimated_completion_time}")
        print()

    manager.complete_task(task_id)
    print()


def example_failure_recovery():
    """Example 4: Failure recovery scenario."""
    print("=" * 60)
    print("Example 4: Failure Recovery")
    print("=" * 60)
    print()

    session_manager = SessionManager()
    checkpoint_manager = CheckpointManager()
    manager = LongDurationManager(
        session_manager=session_manager, checkpoint_manager=checkpoint_manager
    )

    task_id = manager.start_long_duration_task(
        task_id="example-task-4",
        agent_id="example-agent",
        command="complex_operation",
        durability_level=DurabilityLevel.STANDARD,
    )

    # Make some progress
    for i in range(1, 4):
        manager.update_progress(
            task_id=task_id,
            progress=i * 0.25,
            current_step=f"Step {i}",
            steps_completed=i,
            total_steps=4,
        )
        time.sleep(0.5)

    # Simulate failure
    print("Simulating failure...")
    try:
        raise RuntimeError("Simulated system crash")
    except Exception as e:
        manager.handle_failure(
            task_id=task_id,
            failure_type="crash",
            error_message=str(e),
            stack_trace=traceback.format_exc(),
        )
        print("Failure recorded")
        print()

    # Get failure history
    failures = manager.get_failure_history(task_id)
    print(f"Failure History ({len(failures)} failures):")
    for failure in failures:
        print(f"  {failure.timestamp.strftime('%H:%M:%S')}: {failure.failure_type}")
        print(f"    Error: {failure.error_message[:50]}...")
        print(f"    Checkpoint available: {failure.checkpoint_available}")
    print()

    # Recover from failure
    checkpoint = manager.recover_from_failure(task_id)
    if checkpoint:
        print("Recovery successful!")
        print(f"  Recovered from: {checkpoint.progress * 100:.1f}%")
        print(f"  Last step: {checkpoint.context.get('current_step', 'N/A')}")
        print(f"  Checkpoint time: {checkpoint.checkpoint_time}")
        print()
        print("In a real scenario, you would:")
        print("  1. Restore state from checkpoint.context")
        print("  2. Resume execution from checkpoint position")
        print("  3. Continue with remaining work")
    else:
        print("No checkpoint available for recovery")

    print()


def example_multiple_tasks():
    """Example 5: Multiple concurrent tasks."""
    print("=" * 60)
    print("Example 5: Multiple Concurrent Tasks")
    print("=" * 60)
    print()

    session_manager = SessionManager()
    checkpoint_manager = CheckpointManager()
    manager = LongDurationManager(
        session_manager=session_manager, checkpoint_manager=checkpoint_manager
    )

    # Start multiple tasks
    task_ids = []
    for i in range(3):
        task_id = manager.start_long_duration_task(
            task_id=f"concurrent-task-{i}",
            agent_id=f"agent-{i}",
            command="process",
            durability_level=DurabilityLevel.BASIC,
        )
        task_ids.append(task_id)
        print(f"Started task: {task_id}")

    print()

    # Update progress for each task
    for task_id in task_ids:
        manager.update_progress(
            task_id=task_id,
            progress=0.5,
            current_step="Halfway done",
            steps_completed=5,
            total_steps=10,
        )

    # List active tasks
    active_tasks = manager.list_active_tasks()
    print(f"Active Tasks ({len(active_tasks)}):")
    for task_id in active_tasks:
        snapshot = manager.get_progress_snapshot(task_id)
        if snapshot:
            print(
                f"  {task_id}: {snapshot.progress * 100:.1f}% - {snapshot.current_step}"
            )
    print()

    # Complete all tasks
    for task_id in task_ids:
        manager.complete_task(task_id)

    print("All tasks completed")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Long-Duration Operations Examples")
    print("=" * 60)
    print()

    try:
        example_basic_usage()
        example_context_manager()
        example_progress_tracking()
        example_failure_recovery()
        example_multiple_tasks()

        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
