## How TappsCodingAgents Works (Cursor-first, 2025)

This project is designed to work **inside Cursor** with agents, while keeping **local LLM support optional**.

### The mental model

- **Cursor is the “brain”** (LLM reasoning).
  - Cursor uses **whatever model the developer configured** (Auto or pinned).  
  - This repo does **not** hardcode a model selection for Cursor.
- **TappsCodingAgents is the “hands”** (deterministic execution).
  - Runs workflows, quality tools, reporting, worktree isolation, caching, etc.

### Key directories

**In this framework repo (shipped templates):**
- **`tapps_agents/resources/claude/skills/`**: Packaged Skills templates (14 agent skills + Simple Mode skill = 15 total).
- **`tapps_agents/resources/cursor/rules/*.mdc`**: Packaged Cursor Rules templates (8 rule files, including `simple-mode.mdc`, `command-reference.mdc`, and `cursor-mode-usage.mdc`).
- **`tapps_agents/resources/workflows/presets/`**: Workflow presets (8 presets, including 3 Simple Mode workflows).

**In target repos (after `tapps-agents init`):**
- **`.claude/skills/`**: Installed Cursor Skills definitions (copied from packaged templates).
- **`.cursor/`**:
  - `.cursor/rules/*.mdc`: Installed Cursor Rules (copied from packaged templates).
- **`.tapps-agents/`**: Runtime state (config + caches + reports + worktrees).  
  Most of this is **machine-local** and should not be committed.

**Multi-Scope Skill Discovery:**
- **REPO Scope**: `.claude/skills/` (current, parent, git root) - Project-specific skills
- **USER Scope**: `~/.tapps-agents/skills/` - Personal skills across all projects
- **SYSTEM Scope**: Package skills directory - Built-in framework skills
- **Precedence**: REPO > USER > SYSTEM (project skills override personal/system skills)

### Runtime model policy (Cursor-first)

**All execution modes:**

- The framework runs **tools-only** and prepares instruction objects for Cursor Skills.
- Agents never call LLMs directly - they create structured instruction objects.
- Instructions are executed by Cursor Skills, which use the developer's configured model.
- No local LLM (Ollama) or API keys required - Cursor handles all LLM operations.


### Recommended setup for another repo

From the target project root (after installing `tapps-agents`):

- `tapps-agents init`
  - Copies Cursor Rules templates from `tapps_agents/resources/cursor/rules/*.mdc` → `.cursor/rules/` (including `simple-mode.mdc`)
  - Copies Skills templates from `tapps_agents/resources/claude/skills/` → `.claude/skills/` (including Simple Mode skill)
  - Copies workflow presets from `tapps_agents/resources/workflows/presets/*.yaml` → `workflows/presets/` (including 3 Simple Mode workflows)
  - Optionally creates `.tapps-agents/config.yaml`

**For new users:**
- `tapps-agents simple-mode init` - Run the Simple Mode onboarding wizard
- `tapps-agents simple-mode on` - Enable Simple Mode for streamlined, task-first interface
- See [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) for complete documentation

### Keeping Cursor fast

This repo includes `.cursorignore` to prevent Cursor from indexing large/generated directories (venv, caches, reports, worktrees).

**2025 Performance Enhancements** ✅ (January 2026):
- **Non-blocking cache**: Lock-free in-memory LRU cache eliminates 150+ second timeouts
- **Streaming responses**: Progressive workflow feedback prevents Cursor response timeouts
- **Circuit breaker**: Fail-fast semantics prevent cascading failures
- **Cache pre-warming**: Automatic dependency detection and pre-warming during `init`
- **Durable state**: Workflows can resume from any checkpoint after interruption
- See [Simple Mode Timeout Analysis](SIMPLE_MODE_TIMEOUT_ANALYSIS_AND_ENHANCEMENTS.md) for complete details

## SDLC Quality Engine (Planned)

The framework is being enhanced with a **self-correcting quality engine** that achieves "zero issues" consistently across any codebase.

### Current State

- Workflows execute linearly with score-based gates
- Quality checks primarily evaluate numeric scoring
- Limited automatic remediation loopback

### Planned Enhancements

**Pluggable Validation Layer:**
- Adapts to detected project stack (languages, frameworks, tooling)
- Loads appropriate validators based on project profile and repo signals
- Emits standardized Issues Manifest for machine-actionable remediation

**Comprehensive Verification:**
- Expansion beyond unit tests to include: build/compile checks, integration tests, static analysis (linters/type checks), dependency audits, security scans, policy checks, artifact integrity checks

**Composite Gating Model:**
- Gates evaluate issues + verification outcomes, not just scores
- Hard fail conditions: critical issues, verification failures, missing artifacts
- Soft fail/loopback conditions: high issues above threshold, regression vs baseline, low expert confidence

**Bounded Loopback Protocol:**
- When issues exist, workflow loops back with structured fix plan
- Applies changes, re-runs validations, only proceeds when clean
- Bounded retries with escalation rules

**Traceability Matrix:**
- Lightweight mapping: requirements → stories → validations
- Enables machine-checkable completeness verification

See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 1: SDLC Quality Engine](prd/epic-1-sdlc-quality-engine.md) for details.

## Dynamic Expert & RAG Engine (Planned)

An always-on **Dynamic Knowledge/Expert Orchestrator** that automatically enriches agents with project-relevant information.

### Current State

- Built-in technical experts (16 domains)
- Configuration-only experts via `.tapps-agents/experts.yaml`
- RAG backends (VectorKnowledgeBase with SimpleKnowledgeBase fallback)
- Context7 KB cache integration
- Unified Cache for tiered context

### Planned Enhancements

**Automatic Expert Creation:**
- Technical experts: Framework-controlled, automatically consulted based on detected domains
- Project/business experts: Generated automatically from repo signals as config-only experts
- Creates `.tapps-agents/domains.md` and `.tapps-agents/experts.yaml` automatically

**Knowledge Ingestion Pipeline:**
- Project sources: requirements, architecture docs, ADRs, runbooks, prior SDLC reports
- Dependency sources: Context7 KB (library/framework docs, patterns, pitfalls, security notes)
- Operational sources: CI failures, runtime exceptions, monitoring alerts → "known issues" KB entries

**Expert Engine Runtime:**
- Continuously detects what domain knowledge is needed
- Proactively consults the right experts
- Populates knowledge stores as agents learn
- Measures and improves retrieval quality over time

**Governance & Safety:**
- Do-not-index filters: secrets, tokens, credentials, PII
- Prompt-injection handling: retrieved text treated as untrusted, labeled with sources
- Retention & scope: project-local KB remains local
- Optional human approval mode for new experts/KB entries

**Observability & Quality Improvement:**
- Metrics: expert consultation confidence, RAG quality, Context7 KB hit rate
- Scheduled KB maintenance: identifies weak areas, proposes KB additions

See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md) for details.


