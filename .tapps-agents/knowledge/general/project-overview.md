# Project Overview

## TappsCodingAgents v3.6.1

A software development framework providing 14 workflow agents covering the complete SDLC, with Cursor Skills integration, expert system, adaptive learning, and CLI/Python API.

## Scale

- **~1,183 Python files** (687 package + 438 test + 58 other)
- **~151,400 lines of code**
- **35 top-level directories**
- **14 workflow agents**: analyst, architect, debugger, designer, documenter, enhancer, evaluator, implementer, improver, ops, orchestrator, planner, reviewer, tester
- **22 Cursor Skills** (14 agent + simple-mode + expert + patterns + utilities)
- **868+ tests** (core: 368+, init_autofill: 130+, cleanup: 86)

## Core Capabilities

### Workflow Orchestration
- Simple Mode: natural language → intent parsing → workflow selection → agent dispatch
- Adaptive checkpoints: auto-switch workflows based on task complexity
- 4 presets: minimal (2 steps), standard (4), comprehensive (7), full SDLC (9)

### Expert System
- Built-in technical domain experts
- Auto-generated project-specific experts from knowledge bases
- RAG (Retrieval-Augmented Generation) with keyword search
- Adaptive scoring weights that improve with usage

### Context7 Integration
- External MCP server for live library documentation
- Local cache with fuzzy matching and library detection
- Agent helper API for seamless integration

### Epic Management
- Story DAG with dependency resolution
- Wave-based parallel execution with conflict detection
- State persistence and session handoff
- Beads integration for task hydration/dehydration

### Quality Pipeline
- 7-category code scoring
- Ruff linting, mypy type checking, bandit security scanning
- Coverage enforcement (≥75% general, ≥80% core)
- Automatic loopback on quality gate failures

## Technology Stack

- **Python ≥3.12** with asyncio
- **Pydantic v2** for configuration and data models
- **httpx** + **aiohttp** for HTTP clients
- **rich** for terminal UI
- **PyYAML** for configuration
- **pytest** ecosystem (asyncio, mock, cov, xdist, timeout, sugar, rich, html)
- **Ruff** for linting, **mypy** for type checking, **bandit** for security

## Key Directories

```
tapps_agents/       # Main package (687 files)
tests/              # Test suite (438 files)
.tapps-agents/      # Project configuration, cache, knowledge, task specs
.claude/            # Claude Code skills and agents
.cursor/            # Cursor IDE rules and background agents
docs/               # Documentation (architecture, guides, API)
scripts/            # Build, release, version management
```

## Key Concepts

- **Dual nature**: Framework development vs. self-hosting (framework develops itself)
- **Dogfooding**: Framework code changes MUST use Full SDLC workflow
- **Adaptive learning**: Auto-generates experts, adjusts scoring weights, improves first-pass correctness
- **Beads integration**: Task specs hydrate to Beads on SessionStart, dehydrate on SessionEnd

## Important Notes

- Framework changes (`tapps_agents/` package) require `tapps-agents simple-mode full --prompt "..." --auto`
- Quality gates are enforced: overall ≥70, security ≥6.5, coverage ≥75%
- Use `tapps-agents health overview` for system health and metrics
