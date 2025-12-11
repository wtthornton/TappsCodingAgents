"""
Unit tests for Knowledge Graph.
"""

import pytest
from datetime import datetime

from tapps_agents.core.knowledge_graph import (
    KnowledgeGraph,
    RelationshipType,
    RelationshipEdge,
    TaskNode,
    GraphQuery
)
from tapps_agents.core.task_memory import TaskMemory, TaskOutcome


class TestRelationshipEdge:
    """Tests for RelationshipEdge."""
    
    def test_edge_creation(self):
        """Test edge creation."""
        edge = RelationshipEdge(
            from_task="task-1",
            to_task="task-2",
            relationship_type=RelationshipType.SIMILAR,
            strength=0.8
        )
        
        assert edge.from_task == "task-1"
        assert edge.to_task == "task-2"
        assert edge.relationship_type == RelationshipType.SIMILAR
        assert edge.strength == 0.8
    
    def test_serialization(self):
        """Test edge serialization."""
        edge = RelationshipEdge(
            from_task="task-1",
            to_task="task-2",
            relationship_type=RelationshipType.SIMILAR,
            strength=0.8
        )
        
        data = edge.to_dict()
        assert data["from_task"] == "task-1"
        assert data["relationship_type"] == "similar"
        
        restored = RelationshipEdge.from_dict(data)
        assert restored.from_task == edge.from_task
        assert restored.relationship_type == edge.relationship_type


class TestTaskNode:
    """Tests for TaskNode."""
    
    def test_node_creation(self):
        """Test node creation."""
        node = TaskNode(task_id="test-task")
        assert node.task_id == "test-task"
        assert len(node.incoming_edges) == 0
        assert len(node.outgoing_edges) == 0
    
    def test_get_related_tasks(self):
        """Test getting related tasks."""
        node = TaskNode(task_id="test-task")
        
        edge1 = RelationshipEdge(
            from_task="task-1",
            to_task="test-task",
            relationship_type=RelationshipType.SIMILAR
        )
        
        edge2 = RelationshipEdge(
            from_task="test-task",
            to_task="task-2",
            relationship_type=RelationshipType.DEPENDS
        )
        
        node.incoming_edges.append(edge1)
        node.outgoing_edges.append(edge2)
        
        related = node.get_related_tasks()
        assert "task-1" in related
        assert "task-2" in related
        
        # Filter by type
        similar = node.get_related_tasks(RelationshipType.SIMILAR)
        assert "task-1" in similar
        assert "task-2" not in similar


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""
    
    def test_graph_creation(self):
        """Test graph creation."""
        graph = KnowledgeGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_node(self):
        """Test adding node."""
        graph = KnowledgeGraph()
        graph.add_node("task-1")
        
        assert "task-1" in graph.nodes
        assert graph.nodes["task-1"].task_id == "task-1"
    
    def test_add_edge(self):
        """Test adding edge."""
        graph = KnowledgeGraph()
        graph.add_edge(
            "task-1",
            "task-2",
            RelationshipType.SIMILAR,
            strength=0.8
        )
        
        assert len(graph.edges) == 1
        assert "task-1" in graph.nodes
        assert "task-2" in graph.nodes
        assert len(graph.nodes["task-1"].outgoing_edges) == 1
        assert len(graph.nodes["task-2"].incoming_edges) == 1
    
    def test_get_related_tasks(self):
        """Test getting related tasks."""
        graph = KnowledgeGraph()
        graph.add_edge("task-1", "task-2", RelationshipType.SIMILAR)
        graph.add_edge("task-1", "task-3", RelationshipType.DEPENDS)
        
        related = graph.get_related_tasks("task-1")
        assert "task-2" in related
        assert "task-3" in related
        
        # Filter by type
        similar = graph.get_related_tasks("task-1", RelationshipType.SIMILAR)
        assert "task-2" in similar
        assert "task-3" not in similar
    
    def test_find_path(self):
        """Test finding path between tasks."""
        graph = KnowledgeGraph()
        graph.add_edge("task-1", "task-2", RelationshipType.SIMILAR)
        graph.add_edge("task-2", "task-3", RelationshipType.DEPENDS)
        
        path = graph.find_path("task-1", "task-3")
        assert path == ["task-1", "task-2", "task-3"]
        
        # No path
        path = graph.find_path("task-1", "task-4")
        assert path is None
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        graph = KnowledgeGraph()
        
        memory1 = TaskMemory(
            task_id="task-1",
            agent_id="agent",
            command="design system",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.8,
            patterns_used=["MVC"]
        )
        
        memory2 = TaskMemory(
            task_id="task-2",
            agent_id="agent",
            command="design system",
            timestamp=datetime.utcnow(),
            outcome=TaskOutcome.SUCCESS,
            quality_score=0.9,
            patterns_used=["MVC", "Repository"]
        )
        
        similarity = graph._calculate_similarity(memory1, memory2)
        assert similarity > 0.5  # Should be similar


class TestGraphQuery:
    """Tests for GraphQuery."""
    
    def test_find_similar_tasks(self):
        """Test finding similar tasks."""
        graph = KnowledgeGraph()
        graph.add_edge("task-1", "task-2", RelationshipType.SIMILAR)
        graph.add_edge("task-1", "task-3", RelationshipType.DEPENDS)
        
        query = GraphQuery(graph)
        similar = query.find_similar_tasks("task-1")
        
        assert "task-2" in similar
        assert "task-3" not in similar
    
    def test_find_dependencies(self):
        """Test finding dependencies."""
        graph = KnowledgeGraph()
        graph.add_edge("task-1", "task-2", RelationshipType.DEPENDS)
        graph.add_edge("task-1", "task-3", RelationshipType.SIMILAR)
        
        query = GraphQuery(graph)
        deps = query.find_dependencies("task-1")
        
        assert "task-2" in deps
        assert "task-3" not in deps

