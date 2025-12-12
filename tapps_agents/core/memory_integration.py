"""
Memory Integration for Agents

Provides memory-aware capabilities for agents to use task memories.
"""

import logging
from typing import Any

from .hardware_profiler import HardwareProfiler
from .knowledge_graph import KnowledgeGraph
from .task_memory import TaskMemory, TaskMemorySystem, TaskOutcome

logger = logging.getLogger(__name__)


class MemoryContextInjector:
    """Injects relevant memories into agent context."""

    def __init__(self, memory_system: TaskMemorySystem):
        """
        Initialize context injector.

        Args:
            memory_system: Task memory system
        """
        self.memory_system = memory_system

    def inject_memories(
        self,
        context: dict[str, Any],
        query: str,
        agent_id: str | None = None,
        command: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Inject relevant memories into context.

        Args:
            context: Agent context dictionary
            query: Query string for memory retrieval
            agent_id: Optional agent filter
            command: Optional command filter
            limit: Maximum memories to inject

        Returns:
            Updated context with memories
        """
        # Retrieve relevant memories
        memories = self.memory_system.retrieve_memories(
            query=query, agent_id=agent_id, command=command, limit=limit
        )

        if not memories:
            return context

        # Format memories for context
        memory_context = {
            "relevant_memories": [
                {
                    "task_id": m.task_id,
                    "command": m.command,
                    "outcome": m.outcome.value,
                    "quality_score": m.quality_score,
                    "key_learnings": m.key_learnings,
                    "patterns_used": m.patterns_used,
                }
                for m in memories
            ],
            "memory_count": len(memories),
        }

        # Add to context
        context["_memory_context"] = memory_context

        logger.info(f"Injected {len(memories)} memories into context")

        return context

    def format_memories_for_prompt(self, memories: list[TaskMemory]) -> str:
        """
        Format memories as a prompt string.

        Args:
            memories: List of memories

        Returns:
            Formatted string for prompt
        """
        if not memories:
            return ""

        lines = ["## Relevant Past Experiences:"]

        for i, memory in enumerate(memories, 1):
            lines.append(f"\n### Experience {i} (Task: {memory.task_id})")
            lines.append(f"- Command: {memory.command}")
            lines.append(f"- Outcome: {memory.outcome.value}")
            lines.append(f"- Quality Score: {memory.quality_score:.2f}")

            if memory.key_learnings:
                lines.append("- Key Learnings:")
                for learning in memory.key_learnings:
                    lines.append(f"  • {learning}")

            if memory.patterns_used:
                lines.append("- Patterns Used:")
                for pattern in memory.patterns_used:
                    lines.append(f"  • {pattern}")

        return "\n".join(lines)


class MemoryUpdater:
    """Updates memory after task completion."""

    def __init__(
        self,
        memory_system: TaskMemorySystem,
        knowledge_graph: KnowledgeGraph | None = None,
    ):
        """
        Initialize memory updater.

        Args:
            memory_system: Task memory system
            knowledge_graph: Optional knowledge graph
        """
        self.memory_system = memory_system
        self.knowledge_graph = knowledge_graph or KnowledgeGraph(memory_system)

    def update_memory(
        self,
        task_id: str,
        agent_id: str,
        command: str,
        outcome: TaskOutcome,
        quality_score: float,
        key_learnings: list[str] | None = None,
        patterns_used: list[str] | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Update memory after task completion.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            command: Command executed
            outcome: Task outcome
            quality_score: Quality score (0.0 to 1.0)
            key_learnings: Optional key learnings
            patterns_used: Optional patterns used
            context: Optional task context
            metadata: Optional metadata

        Returns:
            True if successful
        """
        # Store memory
        success = self.memory_system.store_memory(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            outcome=outcome,
            quality_score=quality_score,
            key_learnings=key_learnings,
            patterns_used=patterns_used,
            similar_tasks=None,  # Will be detected by graph
            context=context,
            metadata=metadata,
        )

        if success:
            # Get stored memory
            memory = self.memory_system.get_memory(task_id)
            if memory:
                # Update knowledge graph
                self.knowledge_graph.detect_relationships(task_id, memory)

                logger.info(f"Updated memory for task {task_id}")

        return success

    def extract_learnings_from_context(self, context: dict[str, Any]) -> list[str]:
        """
        Extract key learnings from agent context.

        Args:
            context: Agent context

        Returns:
            List of key learnings
        """
        learnings = []

        # Extract from various context fields
        if "learnings" in context:
            learnings.extend(context["learnings"])

        if "insights" in context:
            learnings.extend(context["insights"])

        if "notes" in context:
            learnings.append(context["notes"])

        # Extract from summary if available
        if "summary" in context:
            learnings.append(f"Summary: {context['summary']}")

        return learnings[:10]  # Limit to 10 learnings

    def extract_patterns_from_context(self, context: dict[str, Any]) -> list[str]:
        """
        Extract patterns from agent context.

        Args:
            context: Agent context

        Returns:
            List of patterns
        """
        patterns = []

        # Extract from patterns field
        if "patterns" in context:
            patterns.extend(context["patterns"])

        # Extract from techniques field
        if "techniques" in context:
            patterns.extend(context["techniques"])

        # Extract from approaches field
        if "approaches" in context:
            patterns.extend(context["approaches"])

        return patterns[:10]  # Limit to 10 patterns


class MemoryAwareMixin:
    """Mixin to add memory awareness to agents."""

    # Implementers are expected to provide a stable agent identifier
    # (e.g., via BaseAgent).
    agent_id: str

    def __init__(self, *args, **kwargs):
        """Initialize memory-aware mixin."""
        super().__init__(*args, **kwargs)

        # Initialize memory system
        hardware_profile = kwargs.get("hardware_profile")
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.memory_system = TaskMemorySystem(hardware_profile=hardware_profile)
        self.knowledge_graph = KnowledgeGraph(memory_system=self.memory_system)
        self.memory_injector = MemoryContextInjector(self.memory_system)
        self.memory_updater = MemoryUpdater(self.memory_system, self.knowledge_graph)
        self.memory_enabled = True

    def enable_memory(self, enabled: bool = True):
        """
        Enable or disable memory.

        Args:
            enabled: Whether to enable memory
        """
        self.memory_enabled = enabled

    def retrieve_relevant_memories(
        self, query: str, command: str | None = None, limit: int = 5
    ) -> list[TaskMemory]:
        """
        Retrieve relevant memories for a query.

        Args:
            query: Query string
            command: Optional command filter
            limit: Maximum results

        Returns:
            List of relevant memories
        """
        if not self.memory_enabled:
            return []

        return self.memory_system.retrieve_memories(
            query=query, agent_id=self.agent_id, command=command, limit=limit
        )

    def inject_memories_into_context(
        self, context: dict[str, Any], query: str, command: str | None = None
    ) -> dict[str, Any]:
        """
        Inject relevant memories into context.

        Args:
            context: Agent context
            query: Query string
            command: Optional command filter

        Returns:
            Updated context
        """
        if not self.memory_enabled:
            return context

        return self.memory_injector.inject_memories(
            context=context, query=query, agent_id=self.agent_id, command=command
        )

    def store_task_memory(
        self,
        task_id: str,
        command: str,
        outcome: TaskOutcome,
        quality_score: float,
        key_learnings: list[str] | None = None,
        patterns_used: list[str] | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Store task memory after completion.

        Args:
            task_id: Task identifier
            command: Command executed
            outcome: Task outcome
            quality_score: Quality score
            key_learnings: Optional key learnings
            patterns_used: Optional patterns used
            context: Optional task context
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.memory_enabled:
            return False

        # Extract learnings and patterns from context if not provided
        if not key_learnings and context:
            key_learnings = self.memory_updater.extract_learnings_from_context(context)

        if not patterns_used and context:
            patterns_used = self.memory_updater.extract_patterns_from_context(context)

        return self.memory_updater.update_memory(
            task_id=task_id,
            agent_id=self.agent_id,
            command=command,
            outcome=outcome,
            quality_score=quality_score,
            key_learnings=key_learnings,
            patterns_used=patterns_used,
            context=context,
            metadata=metadata,
        )

    def get_similar_tasks(self, task_id: str, limit: int = 5) -> list[TaskMemory]:
        """
        Get similar tasks.

        Args:
            task_id: Task identifier
            limit: Maximum results

        Returns:
            List of similar task memories
        """
        if not self.memory_enabled:
            return []

        return self.memory_system.get_similar_tasks(task_id, limit)

    def get_memory_context_prompt(
        self, query: str, command: str | None = None
    ) -> str:
        """
        Get formatted memory context for prompt.

        Args:
            query: Query string
            command: Optional command filter

        Returns:
            Formatted prompt string
        """
        if not self.memory_enabled:
            return ""

        memories = self.retrieve_relevant_memories(query, command)
        return self.memory_injector.format_memories_for_prompt(memories)
