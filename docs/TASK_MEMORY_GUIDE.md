# Task Memory and Knowledge Retention Guide

**Version:** 2.0.6  
**Date:** January 2026  
**Status:** ✅ Complete

---

## Overview

The Task Memory system enables agents to retain knowledge from previous tasks for future use. This improves consistency, reduces redundant work, and enables agents to learn from past experiences.

**Key Features:**
- **Task Memory Storage**: Stores task outcomes, learnings, and patterns
- **Knowledge Graph**: Tracks relationships between tasks
- **Memory Retrieval**: Fast, relevant memory search
- **Hardware-Aware**: Optimized for NUC, Development, and Workstation profiles
- **Memory Integration**: Easy integration with agents via mixin

---

## Architecture

### Components

1. **TaskMemorySystem** - Main memory system
2. **MemoryStorage** - Handles persistence (file-based, compressed for NUC)
3. **MemoryIndex** - Fast in-memory search index
4. **KnowledgeGraph** - Tracks task relationships
5. **MemoryAwareMixin** - Adds memory capabilities to agents

### Memory Structure

```python
@dataclass
class TaskMemory:
    task_id: str
    agent_id: str
    command: str
    timestamp: datetime
    outcome: TaskOutcome  # SUCCESS, FAILURE, PARTIAL, CANCELLED
    quality_score: float  # 0.0 to 1.0
    key_learnings: List[str]
    patterns_used: List[str]
    similar_tasks: List[str]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
```

---

## Hardware-Aware Memory

The system automatically adjusts memory storage based on hardware profile:

| Hardware Profile | Storage | Compression | Memory Limit |
|-----------------|--------|------------|--------------|
| NUC | Essential only | Enabled (gzip) | <50MB |
| Development | Balanced | Disabled | <100MB |
| Workstation | Full memory | Disabled | <200MB |
| Server | Full memory | Disabled | <200MB |

---

## Usage

### Basic Memory Storage

```python
from tapps_agents.core.task_memory import TaskMemorySystem, TaskOutcome

# Initialize memory system
memory_system = TaskMemorySystem()

# Store task memory
memory_system.store_memory(
    task_id="task-123",
    agent_id="architect",
    command="design_system",
    outcome=TaskOutcome.SUCCESS,
    quality_score=0.85,
    key_learnings=[
        "Use modular architecture",
        "Follow domain-driven design"
    ],
    patterns_used=["MVC", "Repository", "Factory"],
    context={"domain": "e-commerce", "complexity": "high"}
)
```

### Memory Retrieval

```python
# Retrieve relevant memories
memories = memory_system.retrieve_memories(
    query="design system architecture",
    agent_id="architect",
    command="design_system",
    limit=5
)

for memory in memories:
    print(f"Task: {memory.task_id}")
    print(f"Quality: {memory.quality_score:.2f}")
    print(f"Learnings: {memory.key_learnings}")
```

### Knowledge Graph

```python
from tapps_agents.core.knowledge_graph import KnowledgeGraph, RelationshipType

# Initialize knowledge graph
graph = KnowledgeGraph(memory_system=memory_system)

# Add relationship
graph.add_edge(
    "task-1",
    "task-2",
    RelationshipType.SIMILAR,
    strength=0.8
)

# Find related tasks
related = graph.get_related_tasks("task-1", RelationshipType.SIMILAR)
print(f"Similar tasks: {related}")

# Find path between tasks
path = graph.find_path("task-1", "task-3")
print(f"Path: {path}")
```

---

## Integration with Agents

### Using MemoryAwareMixin

```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.memory_integration import MemoryAwareMixin
from tapps_agents.core.task_memory import TaskOutcome

class MyAgent(BaseAgent, MemoryAwareMixin):
    def __init__(self, *args, **kwargs):
        BaseAgent.__init__(self, *args, **kwargs)
        MemoryAwareMixin.__init__(self, *args, **kwargs)
    
    async def run(self, command: str, **kwargs):
        task_id = kwargs.get("task_id", f"task-{uuid.uuid4()}")
        
        # Retrieve relevant memories before task
        memories = self.retrieve_relevant_memories(
            query=command,
            command=command
        )
        
        # Inject memories into context
        context = kwargs.get("context", {})
        context = self.inject_memories_into_context(
            context=context,
            query=command,
            command=command
        )
        
        # Execute task
        try:
            result = await self._execute_task(command, context=context)
            
            # Store memory after completion
            self.store_task_memory(
                task_id=task_id,
                command=command,
                outcome=TaskOutcome.SUCCESS,
                quality_score=self._calculate_quality(result),
                context=context
            )
            
            return result
        except Exception as e:
            # Store failure memory
            self.store_task_memory(
                task_id=task_id,
                command=command,
                outcome=TaskOutcome.FAILURE,
                quality_score=0.0,
                key_learnings=[f"Error: {str(e)}"],
                context=context
            )
            raise
```

### Memory Context in Prompts

```python
# Get formatted memory context for prompt
memory_prompt = self.get_memory_context_prompt(
    query="design system",
    command="design_system"
)

# Include in agent prompt
prompt = f"""
{memory_prompt}

## Current Task
Design a new system architecture.
"""
```

---

## Memory Retrieval Strategies

### 1. Query-Based Retrieval

```python
# Search by natural language query
memories = memory_system.retrieve_memories(
    query="design modular architecture",
    limit=5
)
```

### 2. Command-Based Retrieval

```python
# Search by command
memories = memory_system.retrieve_memories(
    query="",
    command="design_system",
    limit=5
)
```

### 3. Agent-Based Retrieval

```python
# Search by agent
memories = memory_system.retrieve_memories(
    query="",
    agent_id="architect",
    limit=5
)
```

### 4. Similar Task Retrieval

```python
# Get similar tasks
similar = memory_system.get_similar_tasks("task-123", limit=5)
```

---

## Knowledge Graph Relationships

### Relationship Types

- **SIMILAR**: Tasks with similar patterns or approaches
- **DEPENDS**: Task dependencies (task-2 depends on task-1)
- **IMPROVES**: Task improvements (task-2 improves task-1)
- **RELATED**: Related tasks in same domain
- **FOLLOWS**: Sequential task relationship

### Automatic Relationship Detection

```python
# Knowledge graph automatically detects relationships
graph = KnowledgeGraph(memory_system=memory_system)

# Add task memory
memory = memory_system.get_memory("task-123")
graph.detect_relationships("task-123", memory)

# Relationships are automatically created based on:
# - Similar commands
# - Overlapping patterns
# - Shared learnings
```

### Manual Relationship Creation

```python
# Manually create relationships
graph.add_edge(
    "task-1",
    "task-2",
    RelationshipType.DEPENDS,
    strength=0.9,
    metadata={"reason": "task-2 requires task-1 output"}
)
```

---

## Best Practices

### 1. Memory Quality

- **Store High-Quality Memories**: Only store memories with quality_score > 0.5
- **Extract Key Learnings**: Focus on actionable insights
- **Track Patterns**: Store successful patterns for reuse

### 2. Memory Retrieval

- **Use Specific Queries**: More specific queries yield better results
- **Limit Results**: Use limit=5 for most cases
- **Filter by Agent**: Filter by agent_id for agent-specific memories

### 3. Knowledge Graph

- **Automatic Detection**: Let the system detect relationships automatically
- **Manual Relationships**: Add explicit relationships for important dependencies
- **Path Finding**: Use find_path() to discover task sequences

### 4. Performance

- **Memory Limits**: Keep memory storage under hardware limits
- **Index Rebuilding**: Index rebuilds automatically on retrieval
- **Compression**: Compression is automatic for NUC devices

---

## Examples

### Example 1: Storing Task Memory

```python
from tapps_agents.core.task_memory import TaskMemorySystem, TaskOutcome

memory_system = TaskMemorySystem()

# After task completion
memory_system.store_memory(
    task_id="design-2026-01-15",
    agent_id="architect",
    command="design_system",
    outcome=TaskOutcome.SUCCESS,
    quality_score=0.85,
    key_learnings=[
        "Microservices work well for this domain",
        "Event-driven architecture improves scalability"
    ],
    patterns_used=["Microservices", "Event Sourcing", "CQRS"],
    context={
        "domain": "e-commerce",
        "scale": "high",
        "complexity": "medium"
    }
)
```

### Example 2: Retrieving Memories

```python
# Before starting a new task
memories = memory_system.retrieve_memories(
    query="design microservices architecture",
    agent_id="architect",
    limit=3
)

# Use memories to guide new task
for memory in memories:
    print(f"Previous experience: {memory.task_id}")
    print(f"Quality: {memory.quality_score:.2f}")
    print(f"Learnings: {', '.join(memory.key_learnings)}")
```

### Example 3: Knowledge Graph Query

```python
from tapps_agents.core.knowledge_graph import GraphQuery

query = GraphQuery(graph)

# Find similar tasks
similar = query.find_similar_tasks("task-123", limit=5)

# Find dependencies
deps = query.find_dependencies("task-123")

# Find improvements
improvements = query.find_improvements("task-123")
```

---

## Troubleshooting

### Memory Not Found

**Problem**: `retrieve_memories()` returns empty list

**Solution**:
- Check if memories exist: `memory_system.storage.load_all_memories()`
- Verify query matches stored memories
- Check quality threshold (default: 0.3)

### Low Relevance Scores

**Problem**: Retrieved memories have low relevance

**Solution**:
- Use more specific queries
- Filter by agent_id or command
- Increase quality threshold

### Memory Storage Full

**Problem**: Memory storage exceeds limits

**Solution**:
- Enable compression (automatic for NUC)
- Delete old low-quality memories
- Increase storage limits in configuration

---

## Performance Considerations

### Storage

- **File Size**: Typical memory file: 10-100 KB
- **Compression**: gzip reduces size by 60-80% on NUC
- **Memory Limit**: NUC: <50MB, Workstation: <200MB

### Retrieval

- **Index Rebuild**: <100ms for 1000 memories
- **Search Time**: <50ms for typical queries
- **Memory Usage**: Index uses ~10MB per 1000 memories

### Best Practices

- Store only high-quality memories (quality_score > 0.5)
- Limit memory history (keep last 1000 tasks)
- Use compression for NUC devices
- Rebuild index periodically for large memory sets

---

## See Also

- [Task Memory System](../tapps_agents/core/task_memory.py)
- [Knowledge Graph](../tapps_agents/core/knowledge_graph.py)
- [Memory Integration](../tapps_agents/core/memory_integration.py)
- [Hardware Profiling](../tapps_agents/core/hardware_profiler.py)

