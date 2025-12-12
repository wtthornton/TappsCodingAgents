# Architecture Overview

**Version**: 2.0.0  
**Last Updated**: December 2025

## System Architecture

TappsCodingAgents is organized around a two-layer agent model:

- **Execution layer (Workflow Agents)**: fixed set of 13 SDLC-oriented agents.
- **Knowledge layer (Experts)**: built-in technical experts plus optional project-defined business experts.

## High-Level Components

### 1) Workflow Agents (Execution Layer)

Agents live under `tapps_agents/agents/` and share a common interface via `tapps_agents/core/agent_base.py`.

Agents:

- analyst, planner
- architect, designer
- implementer, debugger, documenter
- tester
- reviewer, improver
- ops
- orchestrator
- enhancer

Agents are invoked:

- **Via CLI**: `tapps-agents ...` (or `python -m tapps_agents.cli ...`)
- **Via Python API**: instantiate agent, `await activate()`, `await run(...)`, `await close()`

### 2) Expert System (Knowledge Layer)

Experts live under `tapps_agents/experts/`.

- **Built-in experts**: framework-provided technical domains.
- **Industry experts** (project-defined): configured in `.tapps-agents/experts.yaml` and optionally backed by a file-based knowledge base under `.tapps-agents/knowledge/<domain>/*.md`.

### 3) Model Abstraction Layer (MAL)

MAL lives in `tapps_agents/core/mal.py` and is configured by `mal:` in `.tapps-agents/config.yaml`.

It supports:

- local provider: **Ollama**
- optional cloud fallback providers: **Anthropic**, **OpenAI**

### 4) Configuration System

Configuration is defined by Pydantic models in `tapps_agents/core/config.py` and loaded from `.tapps-agents/config.yaml` (searched upward from the working directory).

See `docs/CONFIGURATION.md`.

### 5) Workflow Engine

Workflow definition + execution lives under `tapps_agents/workflow/`.

Key pieces:

- **Workflow parsing**: `tapps_agents/workflow/parser.py`
- **Workflow execution**: `tapps_agents/workflow/executor.py`
- **Workflow recommendations**: `tapps_agents/workflow/recommender.py`

#### Workflow State Persistence

Workflow state is persisted to:

- `.tapps-agents/workflow-state/`

When advanced state management is enabled (default in `WorkflowExecutor`), state persistence includes:

- versioned state format (`CURRENT_STATE_VERSION = "2.0"`)
- checksum validation
- migration support
- recovery from history (`.tapps-agents/workflow-state/history/`)

### 6) Project Profiling

Project profiling lives in `tapps_agents/core/project_profile.py` and persists to:

- `.tapps-agents/project-profile.yaml`

See `docs/PROJECT_PROFILING_GUIDE.md`.

### 7) Context7 Integration

Context7 integration lives under `tapps_agents/context7/` and is configured via `context7:` in `.tapps-agents/config.yaml`.

### 8) Quality Analysis (Reviewer)

The Reviewer agent integrates static scoring and optional tooling (Phase 6): Ruff, mypy, duplication checks, dependency auditing, and multi-format reporting.

Report generation is implemented in `tapps_agents/agents/reviewer/report_generator.py` and defaults to writing under `reports/quality/`.

### 9) Analytics Dashboard

Analytics lives in `tapps_agents/core/analytics_dashboard.py` and is exposed via the CLI `analytics` commands.

By default it stores history in:

- `.tapps-agents/analytics/history/*.jsonl`

## Related Documentation

- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/WORKFLOW_SELECTION_GUIDE.md`
- `docs/PROJECT_PROFILING_GUIDE.md`
