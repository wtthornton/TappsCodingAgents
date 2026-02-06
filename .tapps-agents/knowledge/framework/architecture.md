# Framework Architecture

## Overview

TappsCodingAgents v3.6.1 — 14 workflow agents, Simple Mode orchestration, Epic management, expert system with RAG, Context7 integration, and health checks. ~1,183 Python files, ~151,400 LOC.

## Package Structure

| Module | Files | Purpose |
|--------|-------|---------|
| `core/` | 177 | Config, agent_base, startup, validators, generators |
| `workflow/` | 115 | Executor, state, parallel, checkpoints, artifacts, analytics |
| `agents/` | 95 | 14 agent implementations (analyst→tester) |
| `cli/` | 67 | argparse CLI, 28 commands, 16 parsers, feedback manager |
| `simple_mode/` | 51 | Intent parsing, 15 orchestrators, checkpoints |
| `experts/` | 42 | Expert engine, RAG, voting, governance, auto-generation |
| `context7/` | 28 | MCP gateway, cache, fuzzy matcher, library detector |
| `health/` | 17 | Doctor checks, analytics, execution metrics |
| `quality/` | 12 | Scoring, code analysis, duplication detection |
| `mcp/` | 8 | Model Context Protocol server modules |
| `epic/` | 7 | Epic orchestration, state manager, parallel strategies |
| `session/` | 5 | Session lifecycle, atexit hooks |
| `beads/` | 10 | Beads integration, hydration, client |
| `utils/` | 20+ | Cleanup, file helpers, path validation |

## Key Components

- **BaseAgent** (`core/agent_base.py`): ABC with `activate()`, `get_commands()`, `run()`. Uses `ExpertSupportMixin`. All 14 agents inherit from this.
- **ProjectConfig** (`core/config.py`): ~30 nested Pydantic v2 models. Loaded from `.tapps-agents/config.yaml`.
- **CLI** (`cli/main.py`): `create_root_parser()` → `register_all_parsers()` → `route_command()`. Windows encoding handling.
- **Simple Mode**: Intent parsing → workflow selection → orchestrator dispatch → adaptive checkpoints.
- **Epic System**: Story DAG → wave computation → parallel execution → state persistence → Beads integration.
- **Session**: Process-global `_session_id` with atexit-registered SessionEnd hooks and optional state files.

## Configuration

- `.tapps-agents/config.yaml` for agents and thresholds
- `.cursor/rules/` and `.claude/skills/` for Cursor/Claude Code integration
- `.tapps-agents/experts.yaml` for expert definitions
- `.tapps-agents/task-specs/` for task specifications (hydrated to Beads)

## Quality Gates

- Overall score ≥70 (≥75 for framework code)
- Security score ≥6.5 (≥8.5 for framework)
- Coverage ≥75% (≥80% for core modules)
- Ruff (E, F, I, UP, B rules), mypy, bandit

## Known Architecture Issues (2026-02)

1. **MRO chain broken** in BaseAgent `__init__` — missing `super().__init__()` breaks mixin cooperative inheritance
2. **Config model uses dict-style `model_config`** instead of Pydantic v2 `ConfigDict`
3. **Workflow engine is distributed** across 97+ files with no single entry point
4. **3 inconsistent error handling patterns** across agents (return-tuple, raise, Result object)
5. **Path validation is decentralized** — each module implements its own checks
