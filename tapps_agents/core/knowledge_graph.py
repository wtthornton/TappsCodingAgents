"""
Knowledge Graph for Task Relationships

Tracks relationships between tasks to enable knowledge discovery.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .task_memory import TaskMemory, TaskMemorySystem

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of task relationships."""

    SIMILAR = "similar"  # Tasks with similar patterns
    DEPENDS = "depends"  # Task dependencies
    IMPROVES = "improves"  # Task improvements
    RELATED = "related"  # Related tasks in same domain
    FOLLOWS = "follows"  # Sequential task relationship


@dataclass
class RelationshipEdge:
    """Edge representing a task relationship."""

    from_task: str
    to_task: str
    relationship_type: RelationshipType
    strength: float = 1.0  # 0.0 to 1.0
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "from_task": self.from_task,
            "to_task": self.to_task,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> RelationshipEdge:
        """Create from dictionary."""
        data = data.copy()
        data["relationship_type"] = RelationshipType(data["relationship_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class TaskNode:
    """Node representing a task in the knowledge graph."""

    task_id: str
    memory: TaskMemory | None = None
    incoming_edges: list[RelationshipEdge] = field(default_factory=list)
    outgoing_edges: list[RelationshipEdge] = field(default_factory=list)

    def get_related_tasks(
        self, relationship_type: RelationshipType | None = None
    ) -> list[str]:
        """
        Get related task IDs.

        Args:
            relationship_type: Optional relationship type filter

        Returns:
            List of related task IDs
        """
        related = set()

        for edge in self.incoming_edges:
            if relationship_type is None or edge.relationship_type == relationship_type:
                related.add(edge.from_task)

        for edge in self.outgoing_edges:
            if relationship_type is None or edge.relationship_type == relationship_type:
                related.add(edge.to_task)

        return list(related)


class KnowledgeGraph:
    """Graph of task relationships."""

    def __init__(self, memory_system: TaskMemorySystem | None = None):
        """
        Initialize knowledge graph.

        Args:
            memory_system: Optional task memory system for loading memories
        """
        self.nodes: dict[str, TaskNode] = {}
        self.edges: list[RelationshipEdge] = []
        self.memory_system = memory_system

    def add_node(self, task_id: str, memory: TaskMemory | None = None):
        """
        Add a task node to the graph.

        Args:
            task_id: Task identifier
            memory: Optional task memory
        """
        if task_id not in self.nodes:
            self.nodes[task_id] = TaskNode(task_id=task_id, memory=memory)
        elif memory:
            self.nodes[task_id].memory = memory

    def add_edge(
        self,
        from_task: str,
        to_task: str,
        relationship_type: RelationshipType,
        strength: float = 1.0,
        metadata: dict | None = None,
    ):
        """
        Add a relationship edge.

        Args:
            from_task: Source task ID
            to_task: Target task ID
            relationship_type: Type of relationship
            strength: Relationship strength (0.0 to 1.0)
            metadata: Optional metadata
        """
        # Ensure nodes exist
        self.add_node(from_task)
        self.add_node(to_task)

        # Create edge
        edge = RelationshipEdge(
            from_task=from_task,
            to_task=to_task,
            relationship_type=relationship_type,
            strength=strength,
            metadata=metadata or {},
        )

        # Add to edges list
        self.edges.append(edge)

        # Update node edges
        self.nodes[from_task].outgoing_edges.append(edge)
        self.nodes[to_task].incoming_edges.append(edge)

        logger.debug(
            f"Added {relationship_type.value} edge: {from_task} -> {to_task} "
            f"(strength: {strength})"
        )

    def detect_relationships(self, task_id: str, memory: TaskMemory):
        """
        Automatically detect relationships for a task.

        Args:
            task_id: Task identifier
            memory: Task memory
        """
        self.add_node(task_id, memory)

        # Find similar tasks based on patterns and command
        if self.memory_system:
            similar_memories = self.memory_system.retrieve_memories(
                query=memory.command, agent_id=memory.agent_id, limit=10
            )

            for similar_memory in similar_memories:
                if similar_memory.task_id != task_id:
                    # Calculate similarity strength
                    strength = self._calculate_similarity(memory, similar_memory)

                    if strength > 0.5:  # Threshold for similarity
                        self.add_edge(
                            task_id,
                            similar_memory.task_id,
                            RelationshipType.SIMILAR,
                            strength=strength,
                        )

        # Add explicit similar_tasks relationships
        for similar_id in memory.similar_tasks:
            if similar_id != task_id:
                self.add_edge(
                    task_id, similar_id, RelationshipType.RELATED, strength=0.8
                )

    def _calculate_similarity(self, memory1: TaskMemory, memory2: TaskMemory) -> float:
        """
        Calculate similarity between two memories.

        Args:
            memory1: First memory
            memory2: Second memory

        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0

        # Command similarity
        if memory1.command.lower() == memory2.command.lower():
            score += 0.4
        elif (
            memory1.command.lower() in memory2.command.lower()
            or memory2.command.lower() in memory1.command.lower()
        ):
            score += 0.2

        # Pattern overlap
        patterns1 = set(memory1.patterns_used)
        patterns2 = set(memory2.patterns_used)
        if patterns1 and patterns2:
            overlap = len(patterns1 & patterns2) / max(len(patterns1), len(patterns2))
            score += overlap * 0.3

        # Learning overlap
        learnings1 = set(learning.lower() for learning in memory1.key_learnings)
        learnings2 = set(learning.lower() for learning in memory2.key_learnings)
        if learnings1 and learnings2:
            overlap = len(learnings1 & learnings2) / max(
                len(learnings1), len(learnings2)
            )
            score += overlap * 0.3

        return min(score, 1.0)

    def get_related_tasks(
        self,
        task_id: str,
        relationship_type: RelationshipType | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """
        Get tasks related to a given task.

        Args:
            task_id: Task identifier
            relationship_type: Optional relationship type filter
            limit: Optional result limit

        Returns:
            List of related task IDs
        """
        if task_id not in self.nodes:
            return []

        related = self.nodes[task_id].get_related_tasks(relationship_type)

        if limit:
            related = related[:limit]

        return related

    def find_path(
        self, from_task: str, to_task: str, max_depth: int = 3
    ) -> list[str] | None:
        """
        Find a path between two tasks.

        Args:
            from_task: Source task ID
            to_task: Target task ID
            max_depth: Maximum path depth

        Returns:
            List of task IDs forming the path, or None if no path found
        """
        if from_task == to_task:
            return [from_task]

        if from_task not in self.nodes or to_task not in self.nodes:
            return None

        # Simple BFS path finding
        queue = [(from_task, [from_task])]
        visited = {from_task}

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            node = self.nodes[current]
            for edge in node.outgoing_edges:
                next_task = edge.to_task

                if next_task == to_task:
                    return path + [next_task]

                if next_task not in visited:
                    visited.add(next_task)
                    queue.append((next_task, path + [next_task]))

        return None

    def get_subgraph(self, task_ids: set[str]) -> KnowledgeGraph:
        """
        Get a subgraph containing only specified tasks.

        Args:
            task_ids: Set of task IDs to include

        Returns:
            New KnowledgeGraph containing only specified tasks
        """
        subgraph = KnowledgeGraph(self.memory_system)

        # Add nodes
        for task_id in task_ids:
            if task_id in self.nodes:
                subgraph.add_node(task_id, self.nodes[task_id].memory)

        # Add edges
        for edge in self.edges:
            if edge.from_task in task_ids and edge.to_task in task_ids:
                subgraph.add_edge(
                    edge.from_task,
                    edge.to_task,
                    edge.relationship_type,
                    edge.strength,
                    edge.metadata,
                )

        return subgraph

    def to_dict(self) -> dict:
        """Convert graph to dictionary."""
        return {
            "nodes": {
                task_id: {
                    "task_id": node.task_id,
                    "memory": node.memory.to_dict() if node.memory else None,
                }
                for task_id, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
        }

    @classmethod
    def from_dict(
        cls, data: dict, memory_system: TaskMemorySystem | None = None
    ) -> KnowledgeGraph:
        """
        Create graph from dictionary.

        Args:
            data: Dictionary representation
            memory_system: Optional memory system

        Returns:
            KnowledgeGraph instance
        """
        graph = cls(memory_system)

        # Add nodes
        for task_id, node_data in data.get("nodes", {}).items():
            memory = None
            if node_data.get("memory"):
                memory = TaskMemory.from_dict(node_data["memory"])
            graph.add_node(task_id, memory)

        # Add edges
        for edge_data in data.get("edges", []):
            edge = RelationshipEdge.from_dict(edge_data)
            graph.edges.append(edge)
            graph.nodes[edge.from_task].outgoing_edges.append(edge)
            graph.nodes[edge.to_task].incoming_edges.append(edge)

        return graph


class GraphQuery:
    """Query interface for knowledge graph."""

    def __init__(self, graph: KnowledgeGraph):
        """
        Initialize graph query.

        Args:
            graph: Knowledge graph to query
        """
        self.graph = graph

    def find_similar_tasks(self, task_id: str, limit: int = 5) -> list[str]:
        """
        Find tasks similar to a given task.

        Args:
            task_id: Task identifier
            limit: Maximum results

        Returns:
            List of similar task IDs
        """
        return self.graph.get_related_tasks(task_id, RelationshipType.SIMILAR, limit)

    def find_dependencies(self, task_id: str) -> list[str]:
        """
        Find tasks that a task depends on.

        Args:
            task_id: Task identifier

        Returns:
            List of dependency task IDs
        """
        return self.graph.get_related_tasks(task_id, RelationshipType.DEPENDS)

    def find_improvements(self, task_id: str) -> list[str]:
        """
        Find tasks that improve a given task.

        Args:
            task_id: Task identifier

        Returns:
            List of improvement task IDs
        """
        return self.graph.get_related_tasks(task_id, RelationshipType.IMPROVES)

    def find_related_domain_tasks(self, task_id: str, limit: int = 10) -> list[str]:
        """
        Find tasks in the same domain.

        Args:
            task_id: Task identifier
            limit: Maximum results

        Returns:
            List of related task IDs
        """
        return self.graph.get_related_tasks(task_id, RelationshipType.RELATED, limit)
