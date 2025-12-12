"""
Unit tests for Task Memory System.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.task_memory import (
    MemoryCompressor,
    MemoryIndex,
    MemoryStorage,
    TaskMemory,
    TaskMemorySystem,
    TaskOutcome,
)


class TestTaskMemory:
    """Tests for TaskMemory dataclass."""

    def test_memory_creation(self):
        """Test memory creation."""
        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        assert memory.task_id == "test-task"
        assert memory.quality_score == 0.8
        assert memory.outcome == TaskOutcome.SUCCESS

    def test_relevance_score(self):
        """Test relevance score calculation."""
        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="design system",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
            key_learnings=["Use modular design", "Follow patterns"],
            patterns_used=["MVC", "Repository"],
        )

        # High relevance for matching command
        score = memory.get_relevance_score("design", "design system")
        assert score > 0.5

        # Lower relevance for unrelated query
        score = memory.get_relevance_score("unrelated query")
        assert score < 0.5

    def test_serialization(self):
        """Test memory serialization."""
        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
            key_learnings=["learning1"],
            patterns_used=["pattern1"],
        )

        data = memory.to_dict()
        assert data["task_id"] == "test-task"
        assert data["outcome"] == "success"

        restored = TaskMemory.from_dict(data)
        assert restored.task_id == memory.task_id
        assert restored.outcome == memory.outcome


class TestMemoryIndex:
    """Tests for MemoryIndex."""

    def test_index_creation(self):
        """Test index creation."""
        index = MemoryIndex()
        assert len(index.all_memories) == 0

    def test_add_memory(self):
        """Test adding memory to index."""
        index = MemoryIndex()
        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        index.add_memory(memory)
        assert len(index.all_memories) == 1
        assert "test-agent" in index.by_agent
        assert "test command" in index.by_command

    def test_search_by_agent(self):
        """Test searching by agent."""
        index = MemoryIndex()

        memory1 = TaskMemory(
            task_id="task-1",
            agent_id="agent-1",
            command="command1",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        memory2 = TaskMemory(
            task_id="task-2",
            agent_id="agent-2",
            command="command2",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.9,
        )

        index.add_memory(memory1)
        index.add_memory(memory2)

        results = index.search(agent_id="agent-1")
        assert len(results) == 1
        assert results[0].task_id == "task-1"

    def test_search_by_command(self):
        """Test searching by command."""
        index = MemoryIndex()

        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="design system",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        index.add_memory(memory)

        results = index.search(command="design")
        assert len(results) == 1
        assert results[0].task_id == "test-task"

    def test_search_by_quality(self):
        """Test searching by quality threshold."""
        index = MemoryIndex()

        memory1 = TaskMemory(
            task_id="task-1",
            agent_id="agent",
            command="command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.3,
        )

        memory2 = TaskMemory(
            task_id="task-2",
            agent_id="agent",
            command="command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.9,
        )

        index.add_memory(memory1)
        index.add_memory(memory2)

        results = index.search(min_quality=0.5)
        assert len(results) == 1
        assert results[0].task_id == "task-2"


class TestMemoryCompressor:
    """Tests for MemoryCompressor."""

    def test_compress_memory(self):
        """Test memory compression."""
        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
            key_learnings=["learn1", "learn2", "learn3", "learn4", "learn5"],
            patterns_used=["pattern1", "pattern2", "pattern3"],
            context={"detail1": "value1", "detail2": "value2", "summary": "test"},
        )

        compressed = MemoryCompressor.compress_memory(memory)

        assert len(compressed.key_learnings) == 3
        assert len(compressed.patterns_used) == 2
        assert "summary" in compressed.context
        assert "detail1" not in compressed.context

    def test_should_compress(self):
        """Test compression decision."""
        assert MemoryCompressor.should_compress(HardwareProfile.NUC)
        assert not MemoryCompressor.should_compress(HardwareProfile.WORKSTATION)


class TestMemoryStorage:
    """Tests for MemoryStorage."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_save_and_load_memory(self, temp_dir):
        """Test saving and loading memory."""
        storage = MemoryStorage(temp_dir, HardwareProfile.WORKSTATION)

        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        assert storage.save_memory(memory)

        loaded = storage.get_memory("test-task")
        assert loaded is not None
        assert loaded.task_id == memory.task_id
        assert loaded.quality_score == memory.quality_score

    def test_compressed_storage(self, temp_dir):
        """Test compressed storage for NUC."""
        storage = MemoryStorage(temp_dir, HardwareProfile.NUC)

        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        assert storage.save_memory(memory)
        assert storage.memories_file.suffix == ".gz"

        loaded = storage.get_memory("test-task")
        assert loaded is not None

    def test_delete_memory(self, temp_dir):
        """Test deleting memory."""
        storage = MemoryStorage(temp_dir, HardwareProfile.WORKSTATION)

        memory = TaskMemory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
        )

        storage.save_memory(memory)
        assert storage.get_memory("test-task") is not None

        assert storage.delete_memory("test-task")
        assert storage.get_memory("test-task") is None


class TestTaskMemorySystem:
    """Tests for TaskMemorySystem."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_store_and_retrieve(self, temp_dir):
        """Test storing and retrieving memories."""
        system = TaskMemorySystem(storage_dir=temp_dir)

        system.store_memory(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
            key_learnings=["learning1"],
            patterns_used=["pattern1"],
        )

        memories = system.retrieve_memories("test", agent_id="test-agent")
        assert len(memories) > 0
        assert memories[0].task_id == "test-task"

    def test_get_similar_tasks(self, temp_dir):
        """Test getting similar tasks."""
        system = TaskMemorySystem(storage_dir=temp_dir)

        # Store two similar tasks
        system.store_memory(
            task_id="task-1",
            agent_id="agent",
            command="design system",
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
            patterns_used=["MVC"],
        )

        system.store_memory(
            task_id="task-2",
            agent_id="agent",
            command="design architecture",
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.9,
            patterns_used=["MVC"],
        )

        similar = system.get_similar_tasks("task-1")
        assert len(similar) > 0
