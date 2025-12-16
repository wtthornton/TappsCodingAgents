"""
Unit tests for Context7 refresh queue.
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tapps_agents.context7.refresh_queue import RefreshQueue, RefreshTask

pytestmark = pytest.mark.unit


class TestRefreshTask:
    def test_task_creation(self):
        task = RefreshTask(
            library="react", topic="hooks", priority=7, reason="staleness"
        )
        assert task.library == "react"
        assert task.topic == "hooks"
        assert task.priority == 7
        assert task.reason == "staleness"
        assert task.added_at is not None

    def test_task_to_dict(self):
        task = RefreshTask(
            library="react", topic="hooks", priority=7, reason="staleness"
        )
        task_dict = task.to_dict()
        assert task_dict["library"] == "react"
        assert task_dict["topic"] == "hooks"
        assert task_dict["priority"] == 7
        assert "added_at" in task_dict

    def test_task_from_dict(self):
        data = {
            "library": "vue",
            "topic": "components",
            "priority": 5,
            "reason": "staleness",
            "added_at": "2024-01-01T00:00:00Z",
        }
        task = RefreshTask.from_dict(data)
        assert task.library == "vue"
        assert task.topic == "components"
        assert task.priority == 5


class TestRefreshQueue:
    @pytest.fixture
    def temp_queue_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yield Path(f.name)
        if Path(f.name).exists():
            Path(f.name).unlink()

    @pytest.fixture
    def queue(self, temp_queue_file):
        return RefreshQueue(temp_queue_file)

    def test_queue_initialization(self, temp_queue_file):
        queue = RefreshQueue(temp_queue_file)
        assert queue.queue_file == temp_queue_file
        assert len(queue.tasks) == 0

    def test_add_task(self, queue):
        task = queue.add_task("react", "hooks", priority=7)
        assert task.library == "react"
        assert task.topic == "hooks"
        assert task.priority == 7
        assert len(queue.tasks) == 1

    def test_add_task_no_topic(self, queue):
        task = queue.add_task("react", None, priority=5)
        assert task.library == "react"
        assert task.topic is None
        assert len(queue.tasks) == 1

    def test_add_task_duplicate_updates(self, queue):
        queue.add_task("react", "hooks", priority=5)
        queue.add_task("react", "hooks", priority=8)

        assert len(queue.tasks) == 1
        assert queue.tasks[0].priority == 8  # Should update to higher priority

    def test_remove_task(self, queue):
        queue.add_task("react", "hooks")
        assert len(queue.tasks) == 1

        removed = queue.remove_task("react", "hooks")
        assert removed is True
        assert len(queue.tasks) == 0

    def test_remove_task_not_found(self, queue):
        removed = queue.remove_task("nonexistent", "topic")
        assert removed is False

    def test_get_next_task_empty_queue(self, queue):
        task = queue.get_next_task()
        assert task is None

    def test_get_next_task_priority_order(self, queue):
        queue.add_task("lib1", "topic1", priority=3)
        queue.add_task("lib2", "topic2", priority=8)
        queue.add_task("lib3", "topic3", priority=5)

        task = queue.get_next_task()
        assert task is not None
        assert task.priority == 8  # Highest priority first

    def test_get_next_task_oldest_first_same_priority(self, queue):
        queue.add_task("lib1", "topic1", priority=5)
        queue.add_task("lib2", "topic2", priority=5)

        next_task = queue.get_next_task()
        assert next_task.library == "lib1"  # Older task first

    def test_get_next_task_max_priority_filter(self, queue):
        queue.add_task("lib1", "topic1", priority=3)
        queue.add_task("lib2", "topic2", priority=8)

        task = queue.get_next_task(max_priority=5)
        assert task is not None
        assert task.priority == 3  # Only tasks with priority <= 5

    def test_get_next_task_scheduled_filter(self, queue):
        future_time = (datetime.now(UTC) + timedelta(hours=1)).isoformat() + "Z"
        queue.add_task("lib1", "topic1", priority=5, scheduled_for=future_time)

        task = queue.get_next_task()
        assert task is None  # Scheduled for future, not available yet

    def test_get_all_tasks(self, queue):
        queue.add_task("lib1", "topic1")
        queue.add_task("lib2", "topic2")

        all_tasks = queue.get_all_tasks()
        assert len(all_tasks) == 2
        assert all_tasks is not queue.tasks  # Should be a copy

    def test_mark_task_completed_success(self, queue):
        queue.add_task("react", "hooks")
        queue.mark_task_completed("react", "hooks")

        assert len(queue.tasks) == 0  # Should be removed on success

    def test_mark_task_completed_failure(self, queue):
        queue.add_task("react", "hooks")
        queue.mark_task_completed("react", "hooks", error="API error")

        assert len(queue.tasks) == 1  # Should remain in queue
        assert queue.tasks[0].attempts == 1
        assert queue.tasks[0].error == "API error"
        assert queue.tasks[0].last_attempt is not None

    def test_mark_task_completed_multiple_attempts(self, queue):
        queue.add_task("react", "hooks")
        queue.mark_task_completed("react", "hooks", error="Error 1")
        queue.mark_task_completed("react", "hooks", error="Error 2")

        assert queue.tasks[0].attempts == 2

    def test_queue_persistence_yaml(self, temp_queue_file):
        queue1 = RefreshQueue(temp_queue_file)
        queue1.add_task("react", "hooks", priority=7)
        queue1.add_task("vue", "components", priority=5)

        # Create new queue instance (should load from file)
        queue2 = RefreshQueue(temp_queue_file)
        assert len(queue2.tasks) == 2

        # Check tasks loaded correctly
        task = queue2.get_next_task()
        assert task.library == "react"  # Higher priority

    def test_queue_persistence_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            queue_file = Path(f.name)

        try:
            queue1 = RefreshQueue(queue_file)
            queue1.add_task("react", "hooks")

            queue2 = RefreshQueue(queue_file)
            assert len(queue2.tasks) == 1
        finally:
            if queue_file.exists():
                queue_file.unlink()

    def test_queue_stale_entries(self, queue):
        now = datetime.now(UTC)
        entries = [
            {
                "library": "react",
                "topic": "hooks",
                "last_updated": (now - timedelta(days=35)).isoformat() + "Z",  # Stale
            },
            {
                "library": "vue",
                "topic": "components",
                "last_updated": (now - timedelta(days=10)).isoformat() + "Z",  # Fresh
            },
            {
                "library": "angular",
                "topic": "routing",
                "last_updated": (now - timedelta(days=40)).isoformat()
                + "Z",  # Very stale
            },
        ]

        queued = queue.queue_stale_entries(entries, reference_date=now)
        assert queued == 2  # react and angular are stale

    def test_queue_stale_entries_priority(self, queue):
        now = datetime.now(UTC)
        entries = [
            {
                "library": "react",
                "topic": "hooks",
                "last_updated": (now - timedelta(days=50)).isoformat()
                + "Z",  # Very stale
            },
            {
                "library": "vue",
                "topic": "components",
                "last_updated": (now - timedelta(days=35)).isoformat()
                + "Z",  # Moderately stale
            },
        ]

        queued = queue.queue_stale_entries(entries, reference_date=now)
        assert queued == 2

        # Check priorities
        tasks = queue.get_all_tasks()
        very_stale_task = next(t for t in tasks if t.library == "react")
        moderate_stale_task = next(t for t in tasks if t.library == "vue")

        assert very_stale_task.priority > moderate_stale_task.priority

    def test_queue_stale_entries_with_library_type(self, queue):
        now = datetime.now(UTC)
        entries = [
            {
                "library": "jwt-auth",
                "topic": "tokens",
                "last_updated": (now - timedelta(days=8)).isoformat()
                + "Z",  # Stale for critical
            }
        ]

        library_type_map = {"jwt-auth": "critical"}
        queued = queue.queue_stale_entries(entries, library_type_map)

        # Critical libraries stale after 7 days, so this should be queued
        assert queued == 1

    def test_clear_queue(self, queue):
        queue.add_task("lib1", "topic1")
        queue.add_task("lib2", "topic2")
        assert len(queue.tasks) == 2

        queue.clear_queue()
        assert len(queue.tasks) == 0

    def test_size(self, queue):
        assert queue.size() == 0
        queue.add_task("lib1", "topic1")
        assert queue.size() == 1
        queue.add_task("lib2", "topic2")
        assert queue.size() == 2

    def test_load_queue_missing_file(self):
        with tempfile.NamedTemporaryFile(delete=True) as f:
            queue_file = Path(f.name)

        # File doesn't exist, should start empty
        queue = RefreshQueue(queue_file)
        assert len(queue.tasks) == 0

    def test_load_queue_invalid_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            queue_file = Path(f.name)

        try:
            # Should handle invalid YAML gracefully
            queue = RefreshQueue(queue_file)
            assert len(queue.tasks) == 0
        finally:
            if queue_file.exists():
                queue_file.unlink()
