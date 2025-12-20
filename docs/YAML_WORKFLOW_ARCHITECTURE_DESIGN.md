# YAML-Driven Workflow Architecture Design Document

**TappsCodingAgents Workflow Orchestration Strategy**  
**Date:** January 2025  
**Status:** ✅ Implementation Complete (Phases 1-4)

---

## Executive Summary

This document analyzes how to leverage YAML to drive workflows, integrate Cursor TODOs, and determine whether TappsCodingAgents should be restructured as Docker MCP servers (similar to TappMCP, LocalMCP, codefortify) or split into multiple MCPs (like HomeIQ).

### Key Findings

1. **YAML workflows are first-class** in TappsCodingAgents - YAML is the single source of truth with strict schema enforcement. All YAML structures are executed (Epic 6 complete). The `parallel_tasks` structure was removed in favor of dependency-based parallelism using standard `steps`.

2. **Task manifests enable TODO-driven execution** - Task manifests are auto-generated from workflow YAML + state (Epic 7 complete), providing structured task checklists that serve the same purpose as Cursor TODOs.

3. **Current architecture is Cursor-first** - The framework follows a "Cursor is brain, TappsCodingAgents is hands" model, which is sound and preserved.

4. **Docker MCP is optional** - Moving to Docker MCP should be a deployment/portability decision, not a workflow-definition decision. It's not necessary for the YAML-driven workflow goal.

### Recommended Direction

**Primary Path:** Keep TappsCodingAgents as Python framework + CLI + Cursor Skills/Rules, but make YAML the **single source of truth** with strict schema enforcement and generated artifacts (task manifests, Cursor Rules docs, Background Agent configs).

**Optional Enhancement:** Add a single Dockerized MCP "runner" server (deterministic tools only) for cross-IDE portability and remote execution, but only after YAML→state→TODO cohesion is solid.

**Do Not:** Split into multiple MCPs or HomeIQ-style microservices unless you have specific multi-team, multi-IDE, or heavy scaling requirements that justify the complexity.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [YAML-Driven Workflow Strategy](#yaml-driven-workflow-strategy)
3. [Cursor TODOs Integration](#cursor-todos-integration)
4. [MCP/Docker Architecture Options](#mcpdocker-architecture-options)
5. [Reference Architecture Patterns](#reference-architecture-patterns)
6. [Recommendations](#recommendations)
7. [Decision Framework](#decision-framework)
8. [Implementation Phases](#implementation-phases)

---

## Current State Analysis

### What TappsCodingAgents Already Has

#### ✅ Strong Foundation

1. **YAML Workflow Definitions**
   - Location: `workflows/presets/*.yaml` (full-sdlc, rapid-dev, maintenance, quality, quick-fix)
   - Parser: `tapps_agents/workflow/parser.py` with schema validation
   - Schema versions: v1.0 and v2.0 supported
   - Structure: Steps with `id`, `agent`, `action`, `requires`, `creates`, `gate`, `consults`, etc.

2. **Workflow Execution Engine**
   - **Dependency-based parallelism**: Steps automatically run in parallel when `requires/creates` allow (default max: 8 concurrent)
   - **Worktree isolation**: Each step gets its own git worktree to prevent conflicts
   - **State persistence**: Workflow state saved to `.tapps-agents/workflow-state/` with versioning, validation, migration
   - **Progress tracking**: Real-time updates via `ProgressUpdateManager` and Cursor chat integration
   - **Auto-execution**: Background Agents can auto-execute workflow steps via `.cursor-skill-command.txt` files

3. **Cursor Integration**
   - **Skills**: 13 agent skills in `.claude/skills/` (reviewer, implementer, tester, etc.)
   - **Rules**: 6 Cursor Rules in `.cursor/rules/*.mdc` (workflow-presets, quick-reference, etc.)
   - **Background Agents**: Config in `.cursor/background-agents.yaml` with auto-execution support
   - **Runtime policy**: Framework runs tools-only; Cursor handles all LLM operations

4. **Multi-Agent Orchestration**
   - `MultiAgentOrchestrator` class for parallel agent execution
   - Worktree-based conflict resolution
   - Result aggregation and performance monitoring
   - Example workflows: `multi-agent-review-and-test.yaml`, `multi-agent-refactor.yaml`

5. **Generated Artifacts** ✅ (Epics 6-9 Complete)
   - **Task Manifests** (Epic 7): Auto-generated from workflow YAML + state
   - **Cursor Rules Documentation** (Epic 8): Auto-generated from workflow YAML
   - **Background Agent Configs** (Epic 9): Auto-generated from workflow steps
   - **Strict Schema Enforcement** (Epic 6): All YAML structures validated and executed

### Architecture Philosophy (Current)

**From `docs/HOW_IT_WORKS.md`:**

> **Cursor is the "brain"** (LLM reasoning).  
> Cursor uses **whatever model the developer configured** (Auto or pinned).  
> This repo does **not** hardcode a model selection for Cursor.
>
> **TappsCodingAgents is the "hands"** (deterministic execution).  
> Runs workflows, quality tools, reporting, worktree isolation, caching, etc.

This is a **sound architecture** that should be preserved. The question is: how do we make YAML the authoritative source of truth while maintaining this separation?

---

## YAML-Driven Workflow Strategy

### Goal: Make YAML the Single Source of Truth

To truly "drive the workflow" with YAML, we need to:

1. **Make YAML the canonical workflow contract** (not just a preset file)
2. **Enforce strict schema validation** (fail fast on unsupported fields)
3. **Generate all derived artifacts** from YAML (docs, task manifests, Background Agent configs)
4. **Eliminate "YAML theater"** (if it's in YAML, it must execute)

### Strategy 1: YAML as Canonical Contract

#### What YAML Should Own

- **Step graph**: Sequential and parallel step definitions
- **Dependencies**: `requires` and `creates` artifacts
- **Gating rules**: Quality gates, scoring thresholds, conditional logic
- **Artifact expectations**: What files/directories should be created
- **Retry/loopback policy**: How to handle failures
- **Parallel intent**: Explicit parallel task blocks (if needed)
- **Expert consultation**: Which domain experts to consult
- **Context tiers**: Token optimization settings

#### What Code Should Own

- **Execution engine semantics**: How steps actually run
- **Safety constraints**: Timeouts, resource limits, error handling
- **Adapters**: Cursor Skills invocation, Background Agent integration, MCP Gateway
- **State management**: Persistence, recovery, migration
- **Progress reporting**: Real-time updates, metrics collection

#### Pros

- ✅ **Single source of truth**: One place to update workflows
- ✅ **Reviewable & versionable**: YAML diffs = process diffs
- ✅ **Composable**: Build workflow libraries (enterprise, hotfix, compliance)
- ✅ **Human-readable**: Non-developers can understand and modify workflows

#### Cons

- ⚠️ **Schema management cost**: Must version, validate, and enforce conventions
- ⚠️ **Human readability degrades**: If YAML becomes too expressive (condition DSLs, nested parallel blocks)
- ⚠️ **Tooling dependency**: Need good YAML editors, validators, generators

### Strategy 2: Strict Schema + Compiled Outputs

Treat YAML like source code:

1. **Validate on load** (already exists via `WorkflowSchemaValidator`)
2. **Fail fast on unsupported fields** (currently, extra fields may be silently ignored)
3. **Generate compiled artifacts**:
   - **Workflow execution plan** (normalized JSON) stored in workflow state
   - **Human task checklist** (markdown/JSON) for TODO integration
   - **Cursor Rules documentation** (auto-generated from YAML)
   - **Background Agent configs** (generated from workflow steps)

#### Pros

- ✅ **Prevents drift**: Docs and runtime can't diverge
- ✅ **Enables tooling**: Visualizers, planners, audits
- ✅ **Version control friendly**: Generated artifacts can be committed or ignored

#### Cons

- ⚠️ **Requires discipline**: Schema versioning, migration, compatibility policy
- ⚠️ **Build step**: Need to regenerate artifacts when YAML changes

### Strategy 3: Explicit Multi-Agent Semantics

You have two valid approaches to parallelism:

#### A. Dependency-Based Parallelism (Current Default)

**How it works:**
- Steps become "ready" when their `requires` artifacts exist
- All ready steps execute in parallel (up to `max_parallel` limit)
- No explicit coordination needed

**Example:**
```yaml
- id: review
  requires: [src/]  # Can run in parallel with...
  
- id: testing
  requires: [src/]  # ...this step (both only need src/)
```

**Pros:**
- ✅ Automatic - no manual coordination
- ✅ Scales well - works for any number of independent steps
- ✅ Already implemented and working

**Cons:**
- ⚠️ Less explicit - parallelism is inferred, not declared
- ⚠️ Harder to express "fan-out/fan-in" patterns

#### B. Explicit Parallel Task Blocks (REMOVED - Epic 6) ✅

**Status:** Removed in Epic 6 (January 2025)

**Decision:**
- **Removed `parallel_tasks`** - Converted workflows to use standard `steps` with dependency-based parallelism
- **Rationale**: Dependency-based parallelism already handles all use cases, simpler architecture, no functionality loss

**Current Approach:**
- Use standard `steps` with `requires` dependencies
- Steps with no dependencies or whose dependencies are met run in parallel automatically
- No need for explicit `parallel_tasks` syntax

**Example (Current):**
```yaml
steps:
  - id: auth-reviewer
    agent: reviewer
    action: review_code
    requires: []  # No dependencies = runs immediately in parallel
    
  - id: api-reviewer
    agent: reviewer
    action: review_code
    requires: []  # Runs in parallel with auth-reviewer
    
  - id: aggregate
    agent: orchestrator
    action: aggregate_results
    requires:
      - auth-review-report.json  # Waits for both reviews
      - api-review-report.json
```

---

## Cursor TODOs Integration

### Reality Check: Cursor TODO API

**Finding:** Cursor does **not** expose a stable, documented external API to programmatically create/update a first-class "TODO list" object.

**Evidence:**
- No TODO-related MCP tools in the codebase
- Progress updates use `print()` to Cursor chat (not a structured API)
- No references to Cursor TODO management in documentation

**Implication:** We cannot directly "drive the process" via Cursor's native TODO system (if it exists). We need an alternative approach.

### Practical Designs for "TODO-Driven Execution"

#### Option A: "TODOs as Projection" (Recommended)

**Concept:** YAML workflow → Runtime state → Generated task list artifact

**How it works:**
1. Workflow YAML defines steps
2. Executor tracks state in `.tapps-agents/workflow-state/{workflow_id}/state.json`
3. Generator creates a **task manifest** (markdown checklist or JSON) from YAML + state
4. Humans and agents interact with the manifest
5. State updates automatically refresh the manifest

**Task Manifest Format:**
```markdown
# Workflow: Full SDLC Pipeline

## Status: Running (Step 3 of 9)

### Completed Steps
- [x] Requirements gathering (analyst) - Completed 2025-12-19 10:00:00
- [x] Story creation (planner) - Completed 2025-12-19 10:15:00
- [x] System design (architect) - Completed 2025-12-19 10:30:00

### Current Step
- [ ] API design (designer) - **IN PROGRESS**
  - Requires: `architecture.md` ✅
  - Creates: `api-specs/` ⏳
  - Worktree: `api-design`
  - Command: `@designer design-api ...`

### Upcoming Steps
- [ ] Implementation (implementer) - Waiting for `api-specs/`
- [ ] Code review (reviewer) - Waiting for `src/`
- [ ] Testing (tester) - Waiting for `src/`
- [ ] Security scan (ops) - Waiting for `src/`
- [ ] Documentation (documenter) - Waiting for `src/`
- [ ] Finalization (orchestrator) - Waiting for all steps

### Artifacts
- ✅ `requirements.md` (created by requirements step)
- ✅ `stories/` (created by planning step)
- ✅ `architecture.md` (created by design step)
- ⏳ `api-specs/` (expected from api_design step)
- ⏳ `src/` (expected from implementation step)
```

**Pros:**
- ✅ **Always consistent** with workflow truth + actual execution state
- ✅ **Works today** with file/state-based architecture
- ✅ **Supports teams** (commit the plan, keep runtime local)
- ✅ **Agent-readable**: Agents can parse and update the manifest
- ✅ **Human-readable**: Clear checklist format

**Cons:**
- ⚠️ Not a "native" Cursor TODO panel (it's a file artifact)
- ⚠️ Requires conventions for status updates, ownership, artifact links
- ⚠️ Manual refresh needed (unless auto-generated on state changes)

**Implementation:**
- Add `TaskManifestGenerator` class
- Generate manifest on workflow start, step completion, state load
- Store in `.tapps-agents/workflow-state/{workflow_id}/task-manifest.md`
- Optionally sync to a visible location (e.g., `workflow-tasks.md` in project root)

#### Option B: Dedicated "Todo MCP" Tool (Optional Later)

**Concept:** Create a standalone MCP server (like PromptMCP's `promptmcp.todo`) that manages tasks as a database.

**Reference:** `LocalMCP` (PromptMCP) has a `promptmcp.todo` tool with:
- Hierarchical tasks (subtasks, parent-child)
- Dependency tracking
- Project organization
- Status management (pending, in-progress, completed, cancelled)
- Priority levels
- Category organization

**How it could work:**
1. Workflow executor creates tasks in Todo MCP when workflow starts
2. Tasks update as steps complete
3. Cursor (or other MCP clients) can query/update tasks via MCP tools
4. Tasks become the "control plane" for workflow execution

**Pros:**
- ✅ Real task database with dependencies, metrics, cross-project rollups
- ✅ Could become the "process control plane"
- ✅ MCP-native (works with any MCP client)
- ✅ Rich querying and analytics

**Cons:**
- ⚠️ Another service to run and secure
- ⚠️ Risk of **two sources of truth** (YAML vs. Todo MCP) unless Todo MCP is a projection of workflow state
- ⚠️ Additional complexity (database, API, synchronization)

**Recommendation:**
- **Don't build this now** - Option A (task manifest) is sufficient
- **Consider this later** if you need:
  - Cross-project task management
  - Rich analytics and reporting
  - Multi-user collaboration features

#### Option C: AI Session Todo List (Ephemeral, Not Process Backbone)

**Concept:** Use the AI agent's internal todo list during a single execution session.

**How it works:**
- Agent maintains a todo list in its context
- Updates as workflow progresses
- Helps guide execution and keep agent organized

**Pros:**
- ✅ Fast, frictionless for one person in one session
- ✅ Helps keep agent honest and organized
- ✅ No infrastructure needed

**Cons:**
- ❌ Not durable (lost when session ends)
- ❌ Not auditable (no permanent record)
- ❌ Not shareable (can't collaborate)
- ❌ Not a system of record

**Recommendation:**
- **Use this for agent guidance** (good practice)
- **Don't rely on it for process control** (too ephemeral)

### Recommended Approach: Hybrid

1. **Task Manifest (Option A)** as the system of record
   - Generated from YAML + state
   - Committed to version control (optional)
   - Human and agent readable

2. **AI Session Todo List (Option C)** for agent guidance
   - Agent maintains internal todos during execution
   - Helps with step-by-step execution
   - Ephemeral but useful

3. **Todo MCP (Option B)** only if needed later
   - For cross-project management
   - For rich analytics
   - For multi-user collaboration

---

## MCP/Docker Architecture Options

### Reference Architectures Analyzed

#### 1. TappMCP (Docker MCP Server)
- **Structure**: Single Docker container with MCP server
- **Tools**: `smart_vibe`, `smart_plan`, `smart_write`, etc.
- **Integration**: Context7, VibeTapp intelligence system
- **Deployment**: Docker Compose, HTTP + MCP servers

#### 2. LocalMCP / PromptMCP (Docker MCP Server)
- **Structure**: Single Docker container with MCP server
- **Tools**: `promptmcp.enhance`, `promptmcp.todo`, `promptmcp.breakdown`
- **Integration**: Context7-only architecture, SQLite + LRU cache
- **Deployment**: Docker Compose, HTTP server (port 3001) + MCP server (stdio)

#### 3. codefortify (MCP Integration Package)
- **Structure**: npm package with MCP server
- **Tools**: Validation, scoring, testing, server management
- **Integration**: Context7 standards, quality scoring
- **Deployment**: npm install, MCP server via stdio

#### 4. HomeIQ (Microservices Architecture)
- **Structure**: 30+ microservices in Docker Compose
- **Services**: AI services, data enrichment, device intelligence, etc.
- **Integration**: Home Assistant, InfluxDB, SQLite, MQTT
- **Deployment**: Docker Compose with 31 containers

### Architecture Options for TappsCodingAgents

#### Option 1: Stay Cursor-First (Current Approach) - **Recommended as Primary**

**Structure:**
- Python framework + CLI
- Cursor Skills (`.claude/skills/`)
- Cursor Rules (`.cursor/rules/`)
- Background Agents (`.cursor/background-agents.yaml`)
- File-based state (`.tapps-agents/workflow-state/`)

**Pros:**
- ✅ **Lowest complexity** - no server lifecycle, ports, auth, containers
- ✅ **Already working** - current architecture is sound
- ✅ **Cursor-native** - leverages Cursor's built-in features
- ✅ **Simple mental model** - files, state, commands
- ✅ **No deployment overhead** - works out of the box

**Cons:**
- ⚠️ **Cursor-specific** - tied to Cursor workflows and conventions
- ⚠️ **Harder to reuse** - other MCP clients/IDEs need a bridge
- ⚠️ **Local execution only** - can't offload to remote servers easily

**When to use:**
- Primary development workflow
- Single-user or small team
- Cursor-only environment
- Simple deployment requirements

#### Option 2: Add One Optional "TappsCodingAgents Runner MCP" (Docker-Friendly) - **Best Incremental MCP Move**

**Structure:**
- Single Docker container with MCP server
- Deterministic tools only (no LLM calls)
- Workflow operations, quality checks, state management
- Cursor remains the LLM runtime

**MCP Tools:**
```python
# Workflow operations
- tapps.workflow.list: List available workflows
- tapps.workflow.start: Start a workflow
- tapps.workflow.status: Get workflow status
- tapps.workflow.resume: Resume interrupted workflow

# Deterministic checks
- tapps.reviewer.lint: Run linting
- tapps.reviewer.type-check: Run type checking
- tapps.reviewer.security-scan: Run security scan
- tapps.reviewer.report: Generate quality report

# State management
- tapps.state.get: Get workflow state
- tapps.state.list: List all workflow states
- tapps.artifacts.get: Get workflow artifacts
```

**Pros:**
- ✅ **Portable** - works with any MCP-compatible client (Cursor, others)
- ✅ **Remote execution** - can run on different machines
- ✅ **Better ops story** - health endpoints, metrics, standardized deploy
- ✅ **Isolation** - Docker provides process isolation
- ✅ **Preserves architecture** - Cursor still handles LLM, MCP handles tools

**Cons:**
- ⚠️ **Server lifecycle** - need to manage container, ports, auth
- ⚠️ **Versioning** - need to version MCP API surface
- ⚠️ **Potential duplication** - Background Agents already do some of this
- ⚠️ **Additional complexity** - another service to maintain

**When to use:**
- Cross-IDE usage (non-Cursor MCP clients)
- Remote execution needs
- Centralized observability across repos
- Team wants standardized deployment

**Implementation:**
- Create `tapps_agents/mcp/server.py` (MCP server implementation)
- Add `Dockerfile` and `docker-compose.yml`
- Expose MCP tools for workflow operations and deterministic checks
- Keep Cursor Skills for LLM-driven operations

#### Option 3: Break into Multiple MCPs (Prompt/Todo, Quality, Workflow, Security, Docs, etc.)

**Structure:**
- Separate MCP servers for each domain
- Each server has focused tools
- Orchestration via workflow MCP or client-side coordination

**Example Split:**
- **Workflow MCP**: Workflow operations, state management
- **Quality MCP**: Linting, type checking, security scanning
- **Todo MCP**: Task management, dependencies, progress
- **Docs MCP**: Documentation generation, API docs
- **Security MCP**: Security scanning, compliance checks

**Pros:**
- ✅ **Modularity** - clear boundaries, independent scaling
- ✅ **Fault isolation** - failure in one doesn't affect others
- ✅ **Team ownership** - different teams can own different MCPs
- ✅ **Technology diversity** - each MCP can use different tech stack

**Cons:**
- ❌ **High coordination overhead** - versioning, contracts, orchestration
- ❌ **More failure modes** - distributed system complexity
- ❌ **Configuration drift** - multiple configs to keep in sync
- ❌ **Overkill for current needs** - unless you have specific requirements

**When to use:**
- Multiple teams building independent capabilities
- Different scaling requirements per domain
- Need for technology diversity (e.g., Python for workflow, Node.js for quality)
- Multi-IDE, multi-project requirements

**Recommendation:**
- **Don't do this now** - too much complexity for current needs
- **Consider later** if you have:
  - Multiple teams with different domains
  - Heavy scaling requirements
  - Need for technology diversity

#### Option 4: HomeIQ-Style Microservices (30+ Services)

**Structure:**
- One microservice per agent/capability
- Each service in its own container
- Service mesh for communication
- Centralized orchestration

**Pros:**
- ✅ **Maximum isolation** - each service is independent
- ✅ **Independent scaling** - scale only what you need
- ✅ **Clear ownership** - one service = one team
- ✅ **Technology diversity** - each service can use different stack

**Cons:**
- ❌ **Very expensive complexity** - 30+ services to manage
- ❌ **Rebuild orchestration** - need service discovery, load balancing, etc.
- ❌ **Overkill for dev workflow framework** - HomeIQ is a production platform
- ❌ **Negative ROI** - complexity cost >> value for most use cases

**When to use:**
- Building a production platform (like HomeIQ)
- Need for extreme scalability and isolation
- Multiple teams with different tech stacks
- Enterprise deployment requirements

**Recommendation:**
- **Don't do this** - overkill for TappsCodingAgents
- HomeIQ is a production home automation platform, not a dev workflow framework
- The complexity is justified for HomeIQ's use case, not for TappsCodingAgents

---

## Recommendations

### Primary Recommendation: YAML-First with Generated Artifacts

**Strategy:** ✅ **IMPLEMENTED** (Epics 6-9, January 2025)

1. ✅ **YAML is the single source of truth** with strict schema enforcement (Epic 6)
2. ✅ **All derived artifacts generated** from YAML (task manifests, Cursor Rules docs, Background Agent configs) (Epics 7-9)
3. ✅ **Zero drift** - all YAML structures are executed (Epic 6)
4. ✅ **Task manifest generation** for TODO-driven execution (Epic 7)
5. ✅ **Cursor-first architecture** preserved - no Docker MCP needed for core workflow

**Implementation Status:**
1. ✅ **Phase 1**: YAML schema enforcement complete - `parallel_tasks` removed, strict validation enforced
2. ✅ **Phase 2**: Task manifest generation complete - manifests auto-generated from workflow state
3. ✅ **Phase 3**: Cursor Rules docs auto-generation complete - docs sync with YAML
4. ✅ **Phase 4**: Background Agent configs auto-generation complete - configs generated from workflows

### Optional Enhancement: Single Docker MCP Runner

**When to add:**
- Need cross-IDE portability
- Need remote execution
- Need centralized observability
- Team wants standardized deployment

**What it should do:**
- Expose deterministic tools only (no LLM calls)
- Workflow operations (list, start, status, resume)
- Quality checks (lint, type-check, security-scan)
- State management (get state, list states, get artifacts)

**What it should NOT do:**
- Duplicate Cursor Skills (LLM operations stay in Cursor)
- Replace Background Agents (use for remote execution only)
- Become the primary interface (Cursor-first remains primary)

### Do Not: Multiple MCPs or Microservices

**Reasoning:**
- Too much complexity for current needs
- Coordination overhead >> value
- Current architecture is sound and working
- Can always split later if requirements change

---

## Decision Framework

Use this framework to make architecture decisions:

### If Your Primary Goal Is...

**"YAML drives SDLC inside Cursor"**
- ✅ Stay Cursor-first
- ✅ Fix schema drift
- ✅ Add generated task manifests
- ❌ Don't add Docker MCP (not needed)

**"Portability across tools/IDEs"**
- ✅ Add single Docker MCP runner
- ✅ Keep Cursor-first as primary
- ✅ Use MCP for cross-IDE compatibility

**"Remote execution or centralized ops"**
- ✅ Add single Docker MCP runner
- ✅ Expose workflow operations via MCP
- ✅ Keep deterministic tools in MCP, LLM in Cursor

**"Multiple teams building independent capabilities"**
- ⚠️ Consider multiple MCPs (but only after YAML contract is stable)
- ⚠️ Ensure clear boundaries and contracts
- ⚠️ Plan for coordination overhead

**"Extreme scalability and isolation"**
- ⚠️ Consider microservices (but only if you're building a platform)
- ⚠️ Be prepared for significant complexity
- ⚠️ Ensure ROI justifies the cost

### Decision Matrix

| Requirement | Cursor-First | Single MCP | Multiple MCPs | Microservices |
|------------|--------------|------------|---------------|---------------|
| **YAML-driven workflows** | ✅ Primary | ✅ Supported | ✅ Supported | ✅ Supported |
| **Cursor integration** | ✅ Native | ✅ Via MCP | ✅ Via MCP | ✅ Via MCP |
| **Cross-IDE portability** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Remote execution** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Complexity** | 🟢 Low | 🟡 Medium | 🟠 High | 🔴 Very High |
| **Deployment overhead** | 🟢 None | 🟡 Low | 🟠 Medium | 🔴 High |
| **Team coordination** | 🟢 None | 🟡 Low | 🟠 High | 🔴 Very High |
| **Fault isolation** | 🟡 Medium | 🟡 Medium | 🟢 High | 🟢 Very High |
| **Scaling flexibility** | 🟡 Medium | 🟡 Medium | 🟢 High | 🟢 Very High |

**Legend:**
- 🟢 = Good / Low
- 🟡 = Medium
- 🟠 = High
- 🔴 = Very High

---

## Implementation Phases

### ✅ Phase 1: YAML Schema Enforcement (Complete - Epic 6, January 2025)

**Status:** ✅ Complete

**Completed:**
1. ✅ **Audited YAML files** - Identified all structures (steps, parallel_tasks, etc.)
2. ✅ **Decided on `parallel_tasks`**: Removed from YAML (Option A selected)
3. ✅ **Enforced strict schema** - Fail fast on unsupported fields
4. ✅ **Schema versioning** - Support migration between versions
5. ✅ **Updated documentation** - Removed references to unsupported features

**Deliverables:**
- ✅ Updated `WorkflowParser` - Removed `parallel_tasks` support, strict validation
- ✅ Updated `WorkflowExecutor` - Uses dependency-based parallelism only
- ✅ Schema validation that fails on unsupported fields
- ✅ Migration guide for schema versions

### ✅ Phase 2: Task Manifest Generation (Complete - Epic 7, January 2025)

**Status:** ✅ Complete

**Completed:**
1. ✅ **Created `TaskManifestGenerator` class**
   - Input: Workflow YAML + WorkflowState
   - Output: Markdown task checklist
2. ✅ **Generate on workflow events**:
   - Workflow start
   - Step completion
   - State load/resume
3. ✅ **Artifact tracking**:
   - Expected artifacts (from `creates` field)
   - Actual artifacts (from state)
   - Missing artifacts (blocking steps)
4. ✅ **Status indicators**:
   - ✅ Completed
   - ⏳ In progress
   - ⏸️ Blocked
   - ❌ Failed
   - ⏭️ Skipped

**Deliverables:**
- ✅ `TaskManifestGenerator` class
- ✅ Task manifest files in `.tapps-agents/workflow-state/{workflow_id}/task-manifest.md`
- ✅ Documentation on task manifest format

### ✅ Phase 3: Auto-Generate Cursor Rules Docs (Complete - Epic 8, January 2025)

**Status:** ✅ Complete

**Completed:**
1. ✅ **Created `CursorRulesGenerator` class**
   - Input: Workflow YAML files
   - Output: `.cursor/rules/workflow-presets.mdc` content
2. ✅ **Extract workflow metadata**:
   - Name, description, version
   - Step sequence
   - Quality gates
   - When to use
3. ✅ **Generate markdown**:
   - Workflow descriptions
   - Step sequences
   - Usage examples
   - Quality gate thresholds
4. ✅ **Integration with `tapps-agents init`**:
   - Generate rules on init
   - Update rules when workflows change

**Deliverables:**
- ✅ `CursorRulesGenerator` class
- ✅ Auto-generated `.cursor/rules/workflow-presets.mdc`
- ✅ Integration with `tapps-agents init`
- ✅ Documentation on rules generation

### ✅ Phase 4: Auto-Generate Background Agent Configs (Complete - Epic 9, January 2025)

**Status:** ✅ Complete

**Completed:**
1. ✅ **Enhanced `BackgroundAgentGenerator`**:
   - Generate configs for all workflow steps
   - Add watch_paths for auto-execution
   - Add triggers for natural language
2. ✅ **Integration with workflow execution**:
   - Generate configs when workflow starts
   - Clean up configs when workflow completes
3. ✅ **Config validation**:
   - Ensure generated configs are valid
   - Test with Cursor Background Agents

**Deliverables:**
- ✅ Enhanced `BackgroundAgentGenerator`
- ✅ Auto-generated `.cursor/background-agents.yaml` entries
- ✅ Integration with workflow execution
- ✅ Documentation on config generation

### Phase 5: Optional - Single Docker MCP Runner (Low Priority)

**Goal:** Add optional MCP server for cross-IDE portability

**Tasks:**
1. **Create MCP server implementation**:
   - `tapps_agents/mcp/server.py`
   - MCP protocol handlers
   - Tool implementations
2. **Expose deterministic tools**:
   - Workflow operations (list, start, status, resume)
   - Quality checks (lint, type-check, security-scan)
   - State management (get state, list states, get artifacts)
3. **Add Docker support**:
   - `Dockerfile`
   - `docker-compose.yml`
   - Health checks
4. **Documentation**:
   - MCP server setup
   - Tool reference
   - Integration with Cursor and other clients

**Deliverables:**
- MCP server implementation
- Docker configuration
- Tool documentation
- Integration guide

**Timeline:** 2-3 weeks (only if needed)

---

## Conclusion

### Key Takeaways

1. ✅ **YAML workflows are first-class** - YAML is the single source of truth with strict schema enforcement. All structures are executed (Epic 6 complete).

2. ✅ **Task manifests enable TODO-driven execution** - Task manifests are auto-generated from workflow YAML + state (Epic 7 complete), providing structured task checklists.

3. ✅ **Current architecture is sound** - The "Cursor is brain, TappsCodingAgents is hands" model is preserved and working well.

4. **Docker MCP is optional** - It's a deployment/portability decision, not a workflow-definition decision. Don't add it unless you need cross-IDE portability or remote execution.

5. **Multiple MCPs are overkill** - Unless you have specific multi-team, multi-IDE, or heavy scaling requirements, the complexity isn't justified.

### Implementation Status

✅ **Phases 1-4 Complete** (January 2025):
1. ✅ **YAML schema enforcement** (Phase 1) - YAML is authoritative, zero drift
2. ✅ **Task manifest generation** (Phase 2) - TODO-driven execution enabled
3. ✅ **Auto-generated Cursor Rules** (Phase 3) - Docs sync with YAML
4. ✅ **Auto-generated Background Agent configs** (Phase 4) - Configs generated from workflows

⏸️ **Phase 5: Optional Docker MCP** - Deferred until needed for portability

### Success Criteria

- ✅ All YAML structures are executed (no "YAML theater")
- ✅ Task manifests are always in sync with workflow state
- ✅ Cursor Rules docs are auto-generated from YAML
- ✅ Background Agent configs are auto-generated from workflows
- ✅ Single source of truth (YAML) with generated artifacts

---

## Appendix: Reference Implementations

### TappMCP Architecture
- **Location**: https://github.com/wtthornton/TappMCP
- **Structure**: Single Docker container, MCP + HTTP servers
- **Tools**: `smart_vibe`, `smart_plan`, `smart_write`, etc.
- **Integration**: Context7, VibeTapp intelligence system

### LocalMCP / PromptMCP Architecture
- **Location**: https://github.com/wtthornton/LocalMCP
- **Structure**: Single Docker container, MCP + HTTP servers
- **Tools**: `promptmcp.enhance`, `promptmcp.todo`, `promptmcp.breakdown`
- **Integration**: Context7-only, SQLite + LRU cache

### codefortify Architecture
- **Location**: https://github.com/wtthornton/codefortify
- **Structure**: npm package with MCP server
- **Tools**: Validation, scoring, testing, server management
- **Integration**: Context7 standards, quality scoring

### HomeIQ Architecture
- **Location**: https://github.com/wtthornton/HomeIQ
- **Structure**: 30+ microservices in Docker Compose
- **Services**: AI services, data enrichment, device intelligence
- **Integration**: Home Assistant, InfluxDB, SQLite, MQTT

---

**Document Status:** ✅ Complete (Phases 1-4 Implemented)  
**Last Updated:** January 2025  
**Implementation Complete:** Epics 6-9 (January 2025)

