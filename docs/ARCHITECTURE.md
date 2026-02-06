---
title: Architecture Index
version: 3.6.4
status: active
last_updated: 2026-02-05
tags: [architecture, index, system-design, components]
---

# Architecture

## Canonical source

- **Architecture overview**: `docs/ARCHITECTURE.md` (this file)

## Architecture shards

Lean, focused docs under `docs/architecture/` for small agent context:

- **[Technology Stack](architecture/tech-stack.md)** - Technology stack overview, dependencies, and platform support
- **[Source Tree](architecture/source-tree.md)** - Source code organization and module structure
- **[Coding Standards](architecture/coding-standards.md)** - Coding conventions, style guide, and best practices
- **[Performance Guide](architecture/performance-guide.md)** - Performance optimization strategies and metrics
- **[Testing Strategy](architecture/testing-strategy.md)** - Testing approach and coverage requirements

For comprehensive testing infrastructure documentation, see [Test Stack Documentation](test-stack.md).

# Architecture Overview

**Version**: 3.6.4
**Last Updated**: February 2026

## System Architecture

TappsCodingAgents is organized around a two-layer agent model:

- **Execution layer (Workflow Agents)**: fixed set of 14 SDLC-oriented agents.
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
- evaluator

Agents are invoked:

- **Via CLI**: `tapps-agents ...` (or `python -m tapps_agents.cli ...`)
- **Via Python API**: instantiate agent, `await activate()`, `await run(...)`, `await close()`

### 2) Expert System (Knowledge Layer)

Experts live under `tapps_agents/experts/`.

- **Built-in experts** (16): framework-provided technical domains (Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning) with 119 knowledge files across 16 domains.
- **Industry experts** (project-defined): configured in `.tapps-agents/experts.yaml` and optionally backed by a file-based knowledge base under `.tapps-agents/knowledge/<domain>/*.md`.

### 3) Instruction-Based Architecture

Agents prepare structured instruction objects (defined in `tapps_agents/core/instructions.py`) that are executed via Cursor Skills.

**Instruction Models:**
- `CodeGenerationInstruction` - For code generation and refactoring
- `TestGenerationInstruction` - For test generation
- `DocumentationInstruction` - For documentation generation
- `ErrorAnalysisInstruction` - For error analysis and debugging
- `GenericInstruction` - For other agent operations

**Runtime model:**
- All agents prepare instruction objects instead of calling LLMs directly
- Instructions are executed by Cursor Skills, which use the developer's configured model
- No local LLM or API keys required - Cursor handles all LLM operations

See `docs/HOW_IT_WORKS.md` for the full "brain vs hands" model.

### 4) Configuration System

Configuration is defined by Pydantic models in `tapps_agents/core/config.py` and loaded from `.tapps-agents/config.yaml` (searched upward from the working directory).

**User Role Templates:**
- Role templates customize agent behavior based on user role (senior-dev, junior-dev, tech-lead, PM, QA)
- Templates stored in `templates/user_roles/` and loaded via `tapps_agents/core/role_template_loader.py`
- Applied during agent activation before project customizations
- Configuration via `user_role` field in `.tapps-agents/config.yaml`

See `docs/CONFIGURATION.md` and `docs/USER_ROLE_TEMPLATES_GUIDE.md`.

### 5) Workflow Engine

Workflow definition + execution lives under `tapps_agents/workflow/`.

Key pieces:

- **Workflow parsing**: `tapps_agents/workflow/parser.py` - YAML parsing with strict schema enforcement (Epic 6)
- **Parallel execution**: `tapps_agents/workflow/parallel_executor.py` - Executes independent steps in parallel (up to 8 concurrent)
- **Cursor executor**: `tapps_agents/workflow/cursor_executor.py` - Cursor-native execution with parallel support
- **Task manifest generation**: `tapps_agents/workflow/manifest.py` - Auto-generated task checklists (Epic 7)
- **Cursor Rules generation**: `tapps_agents/workflow/rules_generator.py` - Auto-generated Cursor Rules docs (Epic 8)

**YAML-First Architecture** ✅ (Epics 6-10 Complete):
- **YAML is the single source of truth** - All workflow definitions in YAML with strict schema enforcement
- **Strict schema validation** - Parser rejects unknown fields (Epic 6)
- **Auto-generated artifacts**:
  - **Task Manifests** (Epic 7): Auto-generated from workflow YAML + state
  - **Cursor Rules Documentation** (Epic 8): Auto-generated from workflow YAML
- **Dependency-based parallelism** - Automatic parallel execution based on step dependencies (no `parallel_tasks`)
- See [YAML Workflow Architecture Design](YAML_WORKFLOW_ARCHITECTURE_DESIGN.md) for complete details

**Execution Features:**
- Automatic parallel execution of independent workflow steps
- Worktree isolation for concurrent step execution
- See [Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md) for complete execution flow documentation
- **Workflow execution**: `tapps_agents/workflow/executor.py`
- **Workflow recommendations**: `tapps_agents/workflow/recommender.py`
- **Agent handlers**: `tapps_agents/workflow/agent_handlers/` (Epic 20)
  - Strategy Pattern implementation for agent-specific execution logic
  - 12 handler classes (one per agent type), including **EnhancerHandler** for enhance steps (full-sdlc optional, rapid-dev, Epic)
  - `AgentHandlerRegistry` for handler management
  - Reduces complexity and eliminates code duplication
  - CLI prompt enhancement: `auto_enhancement`, `PROMPT_ARGUMENT_MAP` (see [CONFIGURATION.md](CONFIGURATION.md#automatic-prompt-enhancement-auto_enhancement))

#### Workflow State Persistence

Workflow state is persisted to:

- `.tapps-agents/workflow-state/`

When advanced state management is enabled (default in `WorkflowExecutor`), state persistence includes:

- versioned state format (`CURRENT_STATE_VERSION = "2.0"`)
- checksum validation
- migration support
- recovery from history (`.tapps-agents/workflow-state/history/`)

**2025 Enhancements** ✅ (January 2026):
- **Durable Workflow State** (`tapps_agents/workflow/durable_state.py`):
  - Event-sourced state with append-only event log (JSONL format)
  - Checkpoint-based resume from any failure point
  - Complete audit trail for workflow execution
  - `get_resumable_workflows()` for listing workflows that can be resumed
- **Streaming Workflow Executor** (`tapps_agents/workflow/streaming.py`):
  - Progressive streaming with per-step timeouts
  - Automatic checkpointing on timeout
  - SSE and Markdown formatting for Cursor integration
  - Resume command generation (`@simple-mode *resume <workflow_id>`)

### 5.1) Simple Mode Architecture (v3.3.0)

Simple Mode lives under `tapps_agents/simple_mode/` and provides natural language orchestration with enhanced quality controls.

**Core Modules (v3.3.0):**
- **Agent Contract Validation** (`agent_contracts.py`):
  - Pydantic v2 contracts for type-safe agent task validation
  - Pre-execution parameter validation prevents "Unknown command" errors
  - 7 agent contracts: EnhancerTask, PlannerTask, ArchitectTask, DesignerTask, ImplementerTask, ReviewerTask, TesterTask
- **Target File Inference** (`file_inference.py`):
  - Intelligent file path inference from natural language descriptions
  - Pattern-based routing (API→api/, Model→models/, Service→services/, etc.)
  - Context-aware inference from previous workflow steps
- **Result Formatters** (`result_formatters.py`):
  - Decorator-based formatter registry pattern (@register_formatter)
  - Converts raw agent output to formatted markdown documentation
  - Per-agent formatters for enhancer, planner, architect, designer, implementer, reviewer, tester
- **Step Dependency Management** (`step_dependencies.py`):
  - DAG-based step dependency graph
  - Topological sorting for execution ordering
  - Failure cascade handling with skip logic
  - Parallel execution support with `asyncio.TaskGroup`
- **Structured Step Results** (`step_results.py`):
  - Pydantic v2 models for type-safe step results (StepResult, WorkflowResult)
  - Status tracking: SUCCESS, FAILED, SKIPPED, RUNNING
  - Result parser with error handling

**Orchestrators** (`orchestrators/`):
- BuildOrchestrator, ReviewOrchestrator, FixOrchestrator, TestOrchestrator
- EpicOrchestrator (multi-story execution with dependency resolution)
- ExploreOrchestrator, RefactorOrchestrator, PlanAnalysisOrchestrator, PROrchestrator
- ResumeOrchestrator (checkpoint-based workflow resume)

See [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) for usage documentation.

### 5.2) Epic Orchestration

Epic orchestration lives under `tapps_agents/epic/` and provides multi-story execution with dependency resolution.

**Key Modules:**
- `orchestrator.py`: Epic orchestration engine with parallel wave execution
- `state_manager.py`: Atomic state persistence (JSON + JSONL append-only memory)
- `parser.py`: Epic document parsing (markdown with story extraction)
- `models.py`: Epic and story data models
- `beads_sync.py`: Beads task tracking integration
- `markdown_sync.py`: Markdown progress synchronization

**Features:**
- Wave-based parallel story execution with topological dependency sorting
- Atomic state writes with content checksums for drift detection
- Story handoff artifacts between dependent stories
- Configurable via `EpicConfig` on `ProjectConfig` (story_workflow_mode, max_parallel_stories, parallel_strategy)
- Agent-teams stub for Claude Code CLI integration (falls back to asyncio)

**Configuration** (in `.tapps-agents/config.yaml`):
```yaml
epic:
  story_workflow_mode: "full"  # or "story-only"
  max_parallel_stories: 3
  parallel_strategy: "asyncio"  # or "agent-teams"
  detect_file_overlap: true
  memory_last_k: 5
```

### 6) Project Profiling

Project profiling lives in `tapps_agents/core/project_profile.py` and persists to:

- `.tapps-agents/project-profile.yaml`

See `docs/PROJECT_PROFILING_GUIDE.md`.

### 7) Context7 Integration

Context7 integration lives under `tapps_agents/context7/` and is configured via `context7:` in `.tapps-agents/config.yaml`.

**2025 Performance Enhancements** ✅ (January 2026):
- **Non-Blocking Cache** (`tapps_agents/context7/async_cache.py`):
  - `AsyncLRUCache`: Thread-safe in-memory cache with O(1) operations
  - Background write queue for non-blocking disk persistence
  - Atomic file rename pattern (no file locking needed)
  - `CacheStats` for monitoring hit rates and performance
- **Circuit Breaker** (`tapps_agents/context7/circuit_breaker.py`):
  - `CircuitBreaker`: CLOSED → OPEN → HALF_OPEN state machine
  - `ParallelExecutor`: Bounded concurrency (default: 5) with fail-fast
  - Global circuit breaker for Context7 operations
  - Auto-recovery after configurable timeout (default: 30s)
- **Cache Pre-warming** (`tapps_agents/context7/cache_prewarm.py`):
  - `DependencyDetector`: Detects from requirements.txt, pyproject.toml, package.json
  - `CachePrewarmer`: Background pre-warming with priority ordering
  - Integration with `tapps-agents init` for automatic population
  - Expert library prioritization (fastapi, pytest, react, etc.)
- **Lock Timeout Optimization** (`tapps_agents/context7/cache_locking.py`):
  - Reduced timeout from 30s → 5s (3s for cache store)
  - Graceful degradation on lock failures
  - **Result**: Eliminated 150+ second cache lock timeouts

### 8) Quality Analysis (Reviewer)

The Reviewer agent integrates static scoring and optional tooling (Phase 6): Ruff, mypy, duplication checks, dependency auditing, and multi-format reporting.

Report generation is implemented in `tapps_agents/agents/reviewer/report_generator.py` and defaults to writing under `reports/quality/`.

### 9) Analytics Dashboard

Analytics lives in `tapps_agents/core/analytics_dashboard.py` and is exposed via the CLI `health usage` commands (e.g. `health usage dashboard`, `health usage agents`).

By default it stores history in:

- `.tapps-agents/analytics/history/*.jsonl`

### 9.1) Performance Insight Dashboard

A self-contained HTML dashboard providing full visual insight into tapps-agents performance. Generated via `tapps-agents dashboard`.

**Module:** `tapps_agents/dashboard/`

- `generator.py`: Main orchestrator — collects data, renders HTML, writes output, opens browser
- `data_collector.py`: Gathers metrics from all subsystems (health, agents, experts, cache, quality, workflows, learning, events)
- `html_renderer.py`: Renders a single-file HTML page with dark theme, 8 tabs, inline CSS/JS
- `svg_charts.py`: Pure-Python SVG chart generators (ring gauge, bar chart, sparkline, radar, horizontal bar, status badge, number pill)

**Output:** `.tapps-agents/dashboard/dashboard.html` (default), <500KB, zero external dependencies

**CLI:** `tapps-agents dashboard [--no-open] [--output <path>] [--days <n>] [--verbose]`

**Difference from Analytics Dashboard (9):** Analytics Dashboard is text/JSON terminal output for quick checks. Performance Insight Dashboard is a rich HTML report with charts, tables, and a recommendations engine.

### 10) SDLC Quality Engine (Planned)

The SDLC Quality Engine transforms the workflow system from a linear pipeline with score-only gates into a self-correcting quality engine.

**Planned Components:**

- **Pluggable Validation Layer** (`tapps_agents/quality/validation/`): Stack-agnostic validation that loads validators based on detected project profile and repository signals
  - Inputs: `.tapps-agents/project-profile.yaml`, repo signals (languages, frameworks, dependency manifests, build/test tooling, CI config)
  - Outputs: Standardized Issues Manifest, Validation Summary
- **Issues Manifest Schema**: Standardized issue representation with fields: id, severity, category, evidence, repro, suggested_fix, owner_step
- **Composite Gating Model**: Gates evaluate issues + verification outcomes (not just scores)
  - Hard fail: critical issues, verification failures, missing artifacts
  - Soft fail/loopback: high issues above threshold, regression vs baseline, low expert confidence
- **Bounded Loopback Protocol**: Deterministic remediation with structured fix plans, re-validation, bounded retries, and escalation rules
- **Traceability Matrix**: Lightweight requirements → stories → validations mapping

**Status**: Design phase - See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 1: SDLC Quality Engine](prd/epic-1-sdlc-quality-engine.md)

### 11) Dynamic Expert & RAG Engine (Planned)

An always-on orchestrator that automatically detects project domains, creates and curates experts/knowledge, and continuously enriches agents with project-relevant information.

**Planned Components:**

- **Domain/Stack Detector**: Maps repo signals to expert domains
- **Expert Synthesizer**: Automatically writes `.tapps-agents/domains.md` and `.tapps-agents/experts.yaml` from signals
- **Knowledge Ingestion Pipeline**: 
  - Project sources: requirements, architecture docs, ADRs, runbooks, prior SDLC reports
  - Dependency sources: Context7 KB (library/framework docs, patterns, pitfalls)
  - Operational sources: CI failures, runtime exceptions, monitoring alerts → "known issues" KB entries
- **Expert Engine Runtime**: Continuously detects needed domain knowledge, proactively consults experts, populates knowledge stores
- **Governance Layer**: Do-not-index filters (secrets, tokens, credentials, PII), prompt-injection handling, retention & scope controls
- **Observability & Quality Improvement**: Metrics tracking (expert confidence, RAG quality, Context7 KB hit rate) with scheduled KB maintenance jobs

**Status**: Design phase - See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md)

### 12) Claude Code Integration

Claude Code integration provides subagents and settings for the Claude Code CLI.

**Resources** (packaged in `tapps_agents/resources/claude/`):
- `agents/`: 6 subagent definitions (code-reviewer, debugger-agent, researcher, epic-orchestrator, story-executor, security-auditor)
- `settings.json`: Project-level Claude Code settings template
- `settings.local.json.example`: Local overrides template

**Installed to** (by `tapps-agents init`):
- `.claude/agents/`: 6 subagent `.md` files
- `.claude/settings.json`: Permissions and environment configuration
- `.claude/settings.local.json`: Optional local overrides (git-ignored)

**Doctor Checks** (`tapps_agents/core/doctor.py`):
- `CLAUDE_CODE_CLI`: Checks for `claude` CLI binary
- `CLAUDE_CODE_SETTINGS`: Validates settings files exist
- `CLAUDE_CODE_PERMISSIONS`: Checks configured permissions
- `CLAUDE_CODE_ENV`: Checks `TAPPS_AGENTS_MODE` environment variable
- `CLAUDE_CODE_AGENTS`: Checks for subagent `.md` files

## Architecture Decisions

Major architectural decisions are documented as ADRs (Architecture Decision Records):

- **[ADR-001: Instruction-Based Architecture](architecture/decisions/ADR-001-instruction-based-architecture.md)** - Agents prepare instruction objects for Cursor Skills execution
- **[ADR-002: Equal Platform Support Policy](architecture/decisions/ADR-002-equal-platform-support.md)** - Framework provides equal support for Claude Desktop, Cursor IDE, and Claude Code CLI
- **[ADR-003: Expert System Design](architecture/decisions/ADR-003-expert-system-design.md)** - Two-layer expert system (built-in + industry experts)
- **[ADR-004: YAML-First Workflow Architecture](architecture/decisions/ADR-004-yaml-first-workflows.md)** - YAML as single source of truth with strict schema enforcement

**For all ADRs, see:** [Architecture Decisions Directory](architecture/decisions/)

## Related Documentation

- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/WORKFLOW_SELECTION_GUIDE.md`
- `docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md` - YAML-first architecture with generated artifacts (Epics 6-10)
- `docs/PROJECT_PROFILING_GUIDE.md`
- `SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md` - Comprehensive analysis of planned improvements
- `docs/prd/epic-1-sdlc-quality-engine.md` - SDLC Quality Engine epic
- `docs/prd/epic-2-dynamic-expert-rag-engine.md` - Dynamic Expert & RAG Engine epic
- `docs/prd/epic-6-yaml-schema-enforcement.md` - YAML Schema Enforcement epic (complete)
- `docs/prd/epic-7-task-manifest-generation.md` - Task Manifest Generation epic (complete)
- `docs/prd/epic-8-automated-documentation-generation.md` - Automated Documentation Generation epic (complete)
