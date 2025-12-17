# Architecture Overview

**Version**: 2.0.2  
**Last Updated**: January 2026

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

- **Built-in experts** (16): framework-provided technical domains (Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning) with 83 knowledge files.
- **Industry experts** (project-defined): configured in `.tapps-agents/experts.yaml` and optionally backed by a file-based knowledge base under `.tapps-agents/knowledge/<domain>/*.md`.

### 3) Model Abstraction Layer (MAL)

MAL lives in `tapps_agents/core/mal.py` and is configured by `mal:` in `.tapps-agents/config.yaml`.

It supports:

- local provider: **Ollama**
- optional cloud fallback providers: **Anthropic**, **OpenAI**

**Runtime policy (Cursor-first):**
- When running under Cursor (Skills / Background Agents), the framework runs **tools-only** and MAL is **disabled**.
- When running headlessly, MAL is optional and can be enabled explicitly.

See `docs/HOW_IT_WORKS.md` for the full “brain vs hands” model.

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
- **Governance Layer**: Do-not-index filters (secrets, tokens, credentials, PII), prompt-injection handling, retention & scope controls, optional human approval mode
- **Observability & Quality Improvement**: Metrics tracking (expert confidence, RAG quality, Context7 KB hit rate) with scheduled KB maintenance jobs

**Status**: Design phase - See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md)

## Related Documentation

- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/WORKFLOW_SELECTION_GUIDE.md`
- `docs/PROJECT_PROFILING_GUIDE.md`
- `SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md` - Comprehensive analysis of planned improvements
- `docs/prd/epic-1-sdlc-quality-engine.md` - SDLC Quality Engine epic
- `docs/prd/epic-2-dynamic-expert-rag-engine.md` - Dynamic Expert & RAG Engine epic
