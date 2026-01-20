---
title: Source Tree Organization
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [architecture, source-tree, organization]
---

# Source Tree Organization

This document describes the organization of the TappsCodingAgents source code.

## Project Root Structure

```
TappsCodingAgents/
├── tapps_agents/          # Main package
├── tests/                  # Test suite
├── docs/                   # Documentation (implementation/, archive/, releases/, context7/, operations/)
├── scripts/                # Utility scripts (see scripts/README.md)
├── workflows/              # Workflow presets (YAML); source for tapps_agents/resources/workflows/presets
├── templates/              # Templates (agent_roles, project_types, tech_stacks, user_roles, cursor-rules-template)
├── requirements/           # Requirements and specs (see requirements/README.md); distinct from requirements.txt
├── schemas/                # JSON schemas
├── .tapps-agents/         # Project configuration (runtime)
├── .cursor/                # Cursor IDE integration (rules, background-agents, mcp.json)
└── .claude/                # Cursor Skills (canonical; agents/ removed as legacy)
```

## Main Package: `tapps_agents/`

### Core Modules (`tapps_agents/core/`)

**Purpose**: Core framework functionality

**Key Files:**
- `agent_base.py`: Base class for all agents
- `instructions.py`: Instruction models (CodeGeneration, TestGeneration, etc.)
- `config.py`: Configuration models (Pydantic)
- `project_profile.py`: Project profiling system
- `analytics_dashboard.py`: Analytics and metrics
- `role_template_loader.py`: User role template loading

### Agents (`tapps_agents/agents/`)

**Purpose**: Workflow agent implementations

**Structure:**
```
agents/
├── analyst/          # Requirements gathering
├── planner/          # User story creation
├── architect/        # System architecture design
├── designer/         # API and data model design
├── implementer/      # Code generation
├── debugger/         # Error analysis
├── documenter/       # Documentation generation
├── tester/           # Test generation
├── reviewer/         # Code quality review
├── improver/         # Code improvement
├── ops/              # Security and operations
├── orchestrator/     # YAML workflow coordination
├── enhancer/         # Prompt enhancement
└── evaluator/        # Framework effectiveness evaluation
```

**Each agent directory contains:**
- `agent.py`: Main agent implementation
- `SKILL.md`: Cursor Skill definition (if applicable)
- Additional agent-specific modules

### Workflow Engine (`tapps_agents/workflow/`)

**Purpose**: Workflow definition, parsing, and execution

**Key Modules:**
- `parser.py`: YAML workflow parsing with strict schema
- `executor.py`: Workflow execution
- `parallel_executor.py`: Parallel step execution
- `cursor_executor.py`: Cursor-native execution
- `manifest.py`: Task manifest generation
- `rules_generator.py`: Cursor Rules documentation generation
- `agent_handlers/`: Agent-specific execution handlers (Strategy Pattern)

### Simple Mode (`tapps_agents/simple_mode/`)

**Purpose**: Natural language orchestration

**Key Modules:**
- `handler.py`: Simple Mode handler
- `orchestrators/`: Workflow orchestrators (build, review, fix, test, epic, etc.)
- `agent_contracts.py`: Pydantic contracts for agent tasks
- `file_inference.py`: Intelligent file path inference
- `result_formatters.py`: Output formatting
- `step_dependencies.py`: DAG-based dependency management
- `step_results.py`: Structured step results

### Expert System (`tapps_agents/experts/`)

**Purpose**: Knowledge layer with built-in and industry experts

**Key Modules:**
- `expert_registry.py`: Expert registration and lookup
- `builtin_registry.py`: Built-in expert definitions
- `expert_engine.py`: Expert consultation engine
- `simple_rag.py`: File-based RAG
- `vector_rag.py`: Vector-based RAG
- `knowledge/`: Knowledge files (117 markdown files across domains)

**Built-in Experts (16):**
- Security, Performance, Testing, Data Privacy, Accessibility, UX
- Code Quality, Software Architecture, DevOps, Documentation
- AI Frameworks, Observability, API Design, Cloud Infrastructure
- Database, Agent Learning

### Context7 Integration (`tapps_agents/context7/`)

**Purpose**: Library documentation lookup and caching

**Key Modules:**
- `lookup.py`: Context7 API client
- `kb_cache.py`: Knowledge base cache
- `async_cache.py`: Async LRU cache (2025 enhancement)
- `circuit_breaker.py`: Failure handling (2025 enhancement)
- `cache_prewarm.py`: Cache pre-warming (2025 enhancement)
- `analytics.py`: Cache analytics and metrics

### CLI (`tapps_agents/cli/`)

**Purpose**: Command-line interface

**Structure:**
```
cli/
├── commands/         # Command implementations
├── parsers/          # Argument parsers
├── validators/        # Command validators
├── utils/            # CLI utilities
└── __main__.py       # Entry point
```

### MCP Gateway (`tapps_agents/mcp/`)

**Purpose**: Unified Model Context Protocol interface

**Structure:**
```
mcp/
├── gateway.py        # MCP gateway
├── servers/          # MCP server implementations
│   ├── context7.py   # Context7 MCP server
│   ├── playwright.py  # Playwright MCP server
│   ├── filesystem.py # Filesystem MCP server
│   ├── git.py        # Git MCP server
│   └── analysis.py   # Analysis MCP server
└── tool_registry.py  # Tool registry
```

### Health Monitoring (`tapps_agents/health/`)

**Purpose**: System health checks and monitoring

**Structure:**
```
health/
├── checks/           # Health check implementations
│   ├── environment.py
│   ├── context7_cache.py
│   ├── knowledge_base.py
│   └── ...
└── orchestrator.py   # Health check orchestration
```

### Quality System (`tapps_agents/quality/`)

**Purpose**: Quality gates and enforcement

**Key Modules:**
- `quality_gates.py`: Quality gate evaluation
- `coverage_analyzer.py`: Coverage analysis
- `secret_scanner.py`: Secret/PII scanning
- `enforcement.py`: Quality enforcement logic

### Continuous Bug Fix (`tapps_agents/continuous_bug_fix/`)

**Purpose**: Automated bug finding and fixing

**Key Modules:**
- `continuous_bug_fixer.py`: Main coordinator
- `bug_finder.py`: Test failure detection
- `bug_fix_coordinator.py`: Bug fix orchestration
- `commit_manager.py`: Git commit management

## Test Suite: `tests/`

**Structure:**
```
tests/
├── unit/             # Unit tests (fast, isolated)
├── integration/      # Integration tests (with real services)
└── e2e/              # End-to-end tests (full system)
    ├── smoke/        # Fast smoke tests
    ├── workflows/    # Workflow execution tests
    ├── scenarios/    # User journey tests
    └── cli/          # CLI command tests
```

## Configuration: `.tapps-agents/`

**Runtime Configuration:**
```
.tapps-agents/
├── config.yaml           # Main configuration
├── experts.yaml          # Industry expert definitions
├── project-profile.yaml  # Project profiling results
├── workflow-state/       # Workflow state persistence
├── analytics/            # Analytics history
└── kb/                   # Knowledge base cache
```

## Cursor Integration: `.cursor/` and `.claude/`

**Structure:**
```
.cursor/
├── rules/            # Cursor Rules (8 .mdc files)
└── mcp.json         # MCP server configuration

.claude/
└── skills/           # Cursor Skills (14 agent skills + simple-mode)
```

## Documentation: `docs/`

**Structure:**
```
docs/
├── architecture/     # Architecture shards (this directory), ADRs in decisions/
├── implementation/   # EPIC/PHASE plans, implementation notes (from former root implementation/)
├── archive/          # Archived summaries, cleanup/analysis docs; stories in archive/stories/
├── releases/         # Release notes (RELEASE_NOTES_*.md, RELEASE_*_INSTRUCTIONS)
├── context7/         # Context7 integration docs
├── operations/       # Deployment, release process, package distribution
├── guides/           # User guides
├── prd/              # Product requirements documents
└── workflows/        # Workflow documentation
```

## Key Design Principles

### Modularity

- **One responsibility per module**: Each module has a clear, single purpose
- **Agent independence**: Agents can be used independently or in workflows
- **Plugin architecture**: Experts and handlers use registry patterns

### Separation of Concerns

- **Execution layer**: Agents handle task execution
- **Knowledge layer**: Experts provide domain knowledge
- **Orchestration layer**: Workflows and Simple Mode coordinate agents

### Extensibility

- **Custom experts**: Project-defined industry experts
- **Custom workflows**: YAML-based workflow definitions
- **Custom skills**: Cursor Skills can be extended

## Related Documentation

- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Coding Standards**: `docs/architecture/coding-standards.md`
- **Tech Stack**: `docs/architecture/tech-stack.md`

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team
