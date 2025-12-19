"""
Task Memory System for Knowledge Retention

Stores and retrieves task outcomes and learnings for future use.
"""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .hardware_profiler import HardwareProfile, HardwareProfiler

logger = logging.getLogger(__name__)


class TaskOutcome(Enum):
    """Task outcome types."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class TaskMemory:
    """Memory of a completed task."""

    task_id: str
    agent_id: str
    command: str
    timestamp: datetime
    outcome: TaskOutcome
    quality_score: float  # 0.0 to 1.0
    key_learnings: list[str] = field(default_factory=list)
    patterns_used: list[str] = field(default_factory=list)
    similar_tasks: list[str] = field(default_factory=list)  # Related task IDs
    context: dict[str, Any] = field(default_factory=dict)  # Task context
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["outcome"] = self.outcome.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskMemory:
        """Create from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["outcome"] = TaskOutcome(data["outcome"])
        return cls(**data)

    def get_relevance_score(self, query: str, command: str | None = None) -> float:
        """
        Calculate relevance score for a query.

        Args:
            query: Query string
            command: Optional command to match

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        query_lower = query.lower()

        # Command match (high weight)
        if command and command.lower() in self.command.lower():
            score += 0.4

        # Key learnings match
        for learning in self.key_learnings:
            if query_lower in learning.lower():
                score += 0.2
                break

        # Patterns match
        for pattern in self.patterns_used:
            if query_lower in pattern.lower():
                score += 0.2
                break

        # Context match
        context_str = json.dumps(self.context, default=str).lower()
        if query_lower in context_str:
            score += 0.1

        # Quality score boost
        score += self.quality_score * 0.1

        return min(score, 1.0)


class MemoryIndex:
    """Indexes memories for fast retrieval."""

    def __init__(self):
        """Initialize memory index."""
        self.by_agent: dict[str, list[TaskMemory]] = {}
        self.by_command: dict[str, list[TaskMemory]] = {}
        self.by_outcome: dict[TaskOutcome, list[TaskMemory]] = {}
        self.by_pattern: dict[str, list[TaskMemory]] = {}
        self.all_memories: list[TaskMemory] = []

    def add_memory(self, memory: TaskMemory):
        """Add memory to index."""
        self.all_memories.append(memory)

        # Index by agent
        if memory.agent_id not in self.by_agent:
            self.by_agent[memory.agent_id] = []
        self.by_agent[memory.agent_id].append(memory)

        # Index by command
        if memory.command not in self.by_command:
            self.by_command[memory.command] = []
        self.by_command[memory.command].append(memory)

        # Index by outcome
        if memory.outcome not in self.by_outcome:
            self.by_outcome[memory.outcome] = []
        self.by_outcome[memory.outcome].append(memory)

        # Index by patterns
        for pattern in memory.patterns_used:
            if pattern not in self.by_pattern:
                self.by_pattern[pattern] = []
            self.by_pattern[pattern].append(memory)

    def search(
        self,
        query: str | None = None,
        agent_id: str | None = None,
        command: str | None = None,
        outcome: TaskOutcome | None = None,
        min_quality: float = 0.0,
        limit: int = 10,
    ) -> list[TaskMemory]:
        """
        Search memories with filters.

        Args:
            query: Optional query string
            agent_id: Optional agent filter
            command: Optional command filter
            outcome: Optional outcome filter
            min_quality: Minimum quality score
            limit: Maximum results

        Returns:
            List of matching memories, sorted by relevance
        """
        candidates = self.all_memories.copy()

        # Filter by agent
        if agent_id:
            candidates = [m for m in candidates if m.agent_id == agent_id]

        # Filter by command
        if command:
            candidates = [m for m in candidates if command.lower() in m.command.lower()]

        # Filter by outcome
        if outcome:
            candidates = [m for m in candidates if m.outcome == outcome]

        # Filter by quality
        candidates = [m for m in candidates if m.quality_score >= min_quality]

        # Score and sort
        if query:
            scored = [(m, m.get_relevance_score(query, command)) for m in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)
            candidates = [m for m, score in scored if score > 0]

        # Sort by quality and timestamp
        candidates.sort(key=lambda m: (m.quality_score, m.timestamp), reverse=True)

        return candidates[:limit]


class MemoryCompressor:
    """Compresses memories for NUC devices."""

    @staticmethod
    def compress_memory(memory: TaskMemory) -> TaskMemory:
        """
        Compress memory by removing non-essential data.

        Args:
            memory: Memory to compress

        Returns:
            Compressed memory
        """
        # Keep only essential learnings (first 3)
        compressed_learnings = memory.key_learnings[:3]

        # Keep only essential patterns (first 2)
        compressed_patterns = memory.patterns_used[:2]

        # Remove detailed context, keep only summary
        compressed_context = {
            "summary": memory.context.get("summary", ""),
            "domain": memory.context.get("domain", ""),
        }

        return TaskMemory(
            task_id=memory.task_id,
            agent_id=memory.agent_id,
            command=memory.command,
            timestamp=memory.timestamp,
            outcome=memory.outcome,
            quality_score=memory.quality_score,
            key_learnings=compressed_learnings,
            patterns_used=compressed_patterns,
            similar_tasks=memory.similar_tasks[:5],  # Limit to 5
            context=compressed_context,
            metadata={},  # Remove metadata
        )

    @staticmethod
    def should_compress(hardware_profile: HardwareProfile) -> bool:
        """
        Determine if compression should be used.

        Args:
            hardware_profile: Hardware profile

        Returns:
            True if compression should be used
        """
        return hardware_profile == HardwareProfile.NUC


class MemoryStorage:
    """Handles memory persistence."""

    def __init__(
        self, storage_dir: Path, hardware_profile: HardwareProfile | None = None
    ):
        """
        Initialize memory storage.

        Args:
            storage_dir: Directory to store memories
            hardware_profile: Hardware profile for optimization
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Detect hardware profile if not provided
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.hardware_profile = hardware_profile
        self.compression_enabled = MemoryCompressor.should_compress(hardware_profile)
        self.memories_file = self.storage_dir / "memories.json"
        if self.compression_enabled:
            self.memories_file = self.storage_dir / "memories.json.gz"

    def save_memory(self, memory: TaskMemory) -> bool:
        """
        Save memory to disk.

        Args:
            memory: Memory to save

        Returns:
            True if successful
        """
        try:
            # Load existing memories
            memories = self.load_all_memories()

            # Add or update memory
            existing_index = None
            for i, m in enumerate(memories):
                if m.task_id == memory.task_id:
                    existing_index = i
                    break

            if existing_index is not None:
                memories[existing_index] = memory
            else:
                memories.append(memory)

            # Compress if needed
            if self.compression_enabled:
                memories = [MemoryCompressor.compress_memory(m) for m in memories]

            # Save to file
            data = [m.to_dict() for m in memories]
            json_str = json.dumps(data, indent=2, default=str)

            if self.compression_enabled:
                with gzip.open(self.memories_file, "wt", encoding="utf-8") as f:
                    f.write(json_str)
            else:
                with open(self.memories_file, "w", encoding="utf-8") as f:
                    f.write(json_str)

            logger.info(f"Saved memory for task {memory.task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save memory for task {memory.task_id}: {e}")
            return False

    def load_all_memories(self) -> list[TaskMemory]:
        """
        Load all memories from disk.

        Returns:
            List of all memories
        """
        if not self.memories_file.exists():
            return []

        try:
            if self.compression_enabled:
                with gzip.open(self.memories_file, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                with open(self.memories_file, encoding="utf-8") as f:
                    data = json.load(f)

            return [TaskMemory.from_dict(m) for m in data]
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            return []

    def get_memory(self, task_id: str) -> TaskMemory | None:
        """
        Get memory for a specific task.

        Args:
            task_id: Task identifier

        Returns:
            TaskMemory if found, None otherwise
        """
        memories = self.load_all_memories()
        for memory in memories:
            if memory.task_id == task_id:
                return memory
        return None

    def delete_memory(self, task_id: str) -> bool:
        """
        Delete memory for a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        memories = self.load_all_memories()
        original_count = len(memories)
        memories = [m for m in memories if m.task_id != task_id]

        if len(memories) == original_count:
            return False

        # Save updated list
        data = [m.to_dict() for m in memories]
        json_str = json.dumps(data, indent=2, default=str)

        try:
            if self.compression_enabled:
                with gzip.open(self.memories_file, "wt", encoding="utf-8") as f:
                    f.write(json_str)
            else:
                with open(self.memories_file, "w", encoding="utf-8") as f:
                    f.write(json_str)

            logger.info(f"Deleted memory for task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory for task {task_id}: {e}")
            return False


class MemoryRetriever:
    """Retrieves relevant memories for tasks."""

    def __init__(self, storage: MemoryStorage):
        """
        Initialize memory retriever.

        Args:
            storage: Memory storage instance
        """
        self.storage = storage
        self.index = MemoryIndex()
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild memory index from storage."""
        memories = self.storage.load_all_memories()
        self.index = MemoryIndex()
        for memory in memories:
            self.index.add_memory(memory)

    def retrieve_relevant(
        self,
        query: str,
        agent_id: str | None = None,
        command: str | None = None,
        limit: int = 5,
    ) -> list[TaskMemory]:
        """
        Retrieve relevant memories for a query.

        Args:
            query: Query string
            agent_id: Optional agent filter
            command: Optional command filter
            limit: Maximum results

        Returns:
            List of relevant memories
        """
        # Rebuild index to ensure it's up to date
        self._rebuild_index()

        return self.index.search(
            query=query,
            agent_id=agent_id,
            command=command,
            min_quality=0.3,  # Minimum quality threshold
            limit=limit,
        )

    def get_similar_tasks(self, task_id: str, limit: int = 5) -> list[TaskMemory]:
        """
        Get tasks similar to a given task.

        Args:
            task_id: Task identifier
            limit: Maximum results

        Returns:
            List of similar task memories
        """
        memory = self.storage.get_memory(task_id)
        if not memory:
            return []

        # Use similar_tasks list if available
        if memory.similar_tasks:
            similar = []
            for similar_id in memory.similar_tasks[:limit]:
                similar_memory = self.storage.get_memory(similar_id)
                if similar_memory:
                    similar.append(similar_memory)
            return similar

        # Otherwise, search by patterns and command
        self._rebuild_index()
        return self.index.search(
            command=memory.command, agent_id=memory.agent_id, limit=limit
        )


class TaskMemorySystem:
    """Main task memory system."""

    def __init__(
        self,
        storage_dir: Path | None = None,
        hardware_profile: HardwareProfile | None = None,
    ):
        """
        Initialize task memory system.

        Args:
            storage_dir: Directory for memory storage (default: .tapps-agents/memory)
            hardware_profile: Hardware profile (auto-detected if None)
        """
        if storage_dir is None:
            storage_dir = Path(".tapps-agents/memory")

        self.storage = MemoryStorage(storage_dir, hardware_profile)
        self.retriever = MemoryRetriever(self.storage)
        self.hardware_profile = hardware_profile or HardwareProfiler().detect_profile()

    def store_memory(
        self,
        task_id: str,
        agent_id: str,
        command: str,
        outcome: TaskOutcome,
        quality_score: float,
        key_learnings: list[str] | None = None,
        patterns_used: list[str] | None = None,
        similar_tasks: list[str] | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Store a task memory.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            command: Command executed
            outcome: Task outcome
            quality_score: Quality score (0.0 to 1.0)
            key_learnings: Optional key learnings
            patterns_used: Optional patterns used
            similar_tasks: Optional similar task IDs
            context: Optional task context
            metadata: Optional metadata

        Returns:
            True if successful
        """
        memory = TaskMemory(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            timestamp=datetime.now(UTC),
            outcome=outcome,
            quality_score=quality_score,
            key_learnings=key_learnings or [],
            patterns_used=patterns_used or [],
            similar_tasks=similar_tasks or [],
            context=context or {},
            metadata=metadata or {},
        )

        return self.storage.save_memory(memory)

    def retrieve_memories(
        self,
        query: str,
        agent_id: str | None = None,
        command: str | None = None,
        limit: int = 5,
    ) -> list[TaskMemory]:
        """
        Retrieve relevant memories.

        Args:
            query: Query string
            agent_id: Optional agent filter
            command: Optional command filter
            limit: Maximum results

        Returns:
            List of relevant memories
        """
        return self.retriever.retrieve_relevant(query, agent_id, command, limit)

    def get_memory(self, task_id: str) -> TaskMemory | None:
        """
        Get memory for a specific task.

        Args:
            task_id: Task identifier

        Returns:
            TaskMemory if found, None otherwise
        """
        return self.storage.get_memory(task_id)

    def get_similar_tasks(self, task_id: str, limit: int = 5) -> list[TaskMemory]:
        """
        Get similar tasks.

        Args:
            task_id: Task identifier
            limit: Maximum results

        Returns:
            List of similar task memories
        """
        return self.retriever.get_similar_tasks(task_id, limit)
