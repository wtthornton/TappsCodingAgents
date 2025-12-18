# Code Organization Guide

This document describes the code organization patterns and structure of TappsCodingAgents.

## Directory Structure

```
tapps_agents/
├── agents/          # Workflow agents (execution layer)
├── cli/             # Command-line interface
├── context7/        # Context7 integration and caching
├── core/            # Core utilities and base classes
├── experts/         # Expert system (knowledge layer)
├── mcp/             # Model Context Protocol integration
├── quality/         # Quality analysis tools
├── resources/       # Static resources (templates, configs)
└── workflow/        # Workflow orchestration
```

## Module Organization Principles

### 1. Agents (`tapps_agents/agents/`)

**Purpose:** Workflow agents that execute SDLC tasks.

**Structure:**
- Each agent has its own directory (e.g., `reviewer/`, `planner/`)
- Each agent directory contains:
  - `agent.py` - Main agent class
  - `SKILL.md` - Agent skill definition
  - Additional modules as needed (e.g., `scoring.py`, `report_generator.py`)

**Pattern:**
- All agents inherit from `BaseAgent` (`tapps_agents/core/agent_base.py`)
- Agents implement the `run()` method to handle commands
- Agents use the expert system for domain knowledge

**Example:**
```python
from tapps_agents.core.agent_base import BaseAgent

class ReviewerAgent(BaseAgent):
    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        # Handle reviewer-specific commands
        pass
```

### 2. CLI (`tapps_agents/cli/`)

**Purpose:** Command-line interface for all agents and top-level commands.

**Structure:**
- `main.py` - Entry point and command routing
- `base.py` - Shared CLI utilities (error handling, formatting)
- `commands/` - Command handlers for each agent
- `parsers/` - Argument parser definitions

**Pattern:**
- Commands are organized by agent (e.g., `commands/reviewer.py`)
- Parsers are separated from handlers for clarity
- Shared utilities in `base.py` for consistency

**Import Pattern:**
```python
from tapps_agents.cli.base import run_agent_command, format_output
from tapps_agents.cli.commands import reviewer
```

### 3. Core (`tapps_agents/core/`)

**Purpose:** Core utilities, base classes, and shared functionality.

**Key Modules:**
- `agent_base.py` - Base agent class
- `config.py` - Configuration management
- `mal.py` - Model Abstraction Layer
- `context_manager.py` - Context management
- `error_envelope.py` - Error handling
- `customization_loader.py` - Customization system
- `skill_loader.py` - Skill loading and validation

**Pattern:**
- Base classes and interfaces
- Configuration and initialization
- Shared utilities (no agent-specific logic)
- Import from core: `from tapps_agents.core import ...`

### 3.5. Workflow Agent Handlers (`tapps_agents/workflow/agent_handlers/`) (Epic 20)

**Purpose:** Agent-specific execution logic using Strategy Pattern.

**Structure:**
- `base.py` - `AgentExecutionHandler` abstract base class
- `registry.py` - `AgentHandlerRegistry` for handler management
- Individual handler files (e.g., `debugger_handler.py`, `implementer_handler.py`)

**Pattern:**
- Each agent type has a dedicated handler class
- Handlers encapsulate agent-specific execution logic
- Registry manages handler lookup and instantiation
- Reduces complexity in `WorkflowExecutor` by delegating to handlers

**Example:**
```python
from tapps_agents.workflow.agent_handlers import AgentHandlerRegistry

registry = AgentHandlerRegistry()
handler = registry.get_handler("debugger", executor=self)
await handler.handle(step, state, run_agent_func, target_path, created_artifacts)
```

**Benefits:**
- Reduced complexity (122 → C)
- Zero code duplication
- Easy to extend (add new agents by creating handlers)
- Improved testability

### 4. Experts (`tapps_agents/experts/`)

**Purpose:** Expert system for domain knowledge and RAG.

**Structure:**
- `base_expert.py` - Base expert class
- `expert_registry.py` - Expert discovery and registration
- `expert_engine.py` - Expert orchestration
- `knowledge_ingestion.py` - Knowledge ingestion pipeline
- `governance.py` - Knowledge governance and safety
- `knowledge/` - Built-in knowledge files (83 files)

**Pattern:**
- Experts provide domain-specific knowledge
- RAG integration for knowledge retrieval
- Governance layer for safety and approval

### 5. Context7 (`tapps_agents/context7/`)

**Purpose:** Context7 library documentation integration.

**Key Modules:**
- `lookup.py` - Library documentation lookup
- `kb_cache.py` - Knowledge base caching
- `analytics.py` - Analytics and metrics
- `cache_warming.py` - Cache warming strategies

**Pattern:**
- Caching layer for Context7 queries
- Analytics for cache performance
- Integration with expert system

### 6. Workflow (`tapps_agents/workflow/`)

**Purpose:** Workflow orchestration and execution.

**Key Modules:**
- Workflow definition and execution
- State persistence
- Health checking
- Background agent management

## Import Guidelines

### 1. Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports

### 2. Import Patterns

**From core:**
```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.config import ProjectConfig, load_config
```

**From agents:**
```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent
```

**From experts:**
```python
from tapps_agents.experts.expert_registry import ExpertRegistry
```

**From CLI:**
```python
from tapps_agents.cli.base import run_agent_command
```

### 3. Circular Import Prevention

- Use `TYPE_CHECKING` for type-only imports
- Use `from __future__ import annotations` for forward references
- Avoid importing from `__init__.py` files that import from submodules

**Example:**
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .knowledge_ingestion import KnowledgeEntry
```

## Code Organization Best Practices

### 1. Module Size

- Keep modules focused and single-purpose
- Split large modules (>500 lines) into smaller, related modules
- Use subdirectories for related functionality

### 2. Naming Conventions

- **Modules:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`

### 3. Public vs Private

- Public API: No leading underscore
- Private/internal: Leading underscore (`_private_method`)
- Module-private: Double underscore (`__module_private`)

### 4. Documentation

- Module-level docstrings for all public modules
- Class docstrings for all public classes
- Function docstrings for all public functions
- Use type hints for all function signatures

## Dependency Graph

```
agents/ → core/ (base classes, config)
agents/ → experts/ (domain knowledge)
cli/ → agents/ (command execution)
cli/ → core/ (utilities)
experts/ → context7/ (library docs)
workflow/ → agents/ (orchestration)
workflow/ → core/ (utilities)
```

## Adding New Code

### Adding a New Agent

1. Create directory: `tapps_agents/agents/<agent_name>/`
2. Create `agent.py` with agent class inheriting from `BaseAgent`
3. Create `SKILL.md` with agent skill definition
4. Add CLI command handler: `tapps_agents/cli/commands/<agent_name>.py`
5. Add CLI parser: `tapps_agents/cli/parsers/<agent_name>.py`
6. Register in `tapps_agents/cli/main.py`

### Adding a New Core Utility

1. Add module to `tapps_agents/core/`
2. Export from `tapps_agents/core/__init__.py` if it's part of public API
3. Add docstrings and type hints
4. Update this documentation if it's a significant addition

### Adding a New Expert

1. Add knowledge files to `tapps_agents/experts/knowledge/<domain>/`
2. Register in expert registry (if built-in)
3. Or configure in `.tapps-agents/experts.yaml` (if project-specific)

## Maintenance

- Review module organization quarterly
- Refactor when modules exceed 500 lines
- Document new patterns as they emerge
- Keep dependency graph acyclic

