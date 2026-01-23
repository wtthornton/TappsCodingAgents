# TappsCodingAgents

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](README.md)
[![Version](https://img.shields.io/badge/version-3.5.21-blue.svg)](CHANGELOG.md)

**A specification framework for defining, configuring, and orchestrating coding agents.**

TappsCodingAgents helps teams build and orchestrate AI coding agents with **quality gates**, **Cursor IDE integration**, and **full SDLC workflows**—so you get consistent, traceable results instead of one-off AI edits.

**Highlights:** 14 workflow agents (review, implement, test, fix, plan, …) · **Simple Mode** for natural language (`@simple-mode *build "feature"`) · Cursor Skills + Claude Desktop · 11 YAML workflow presets · Code scoring, experts, and MCP gateway.

**Prerequisites:** Python 3.13+, [Cursor IDE](https://cursor.com) or [Claude Desktop](https://claude.ai). Optional: [Context7](https://context7.com) API key for library docs.

---

## Table of Contents

- [Quick Start (5 min)](#-cursor-quick-start-5-minutes)
- [Simple Mode (New Users)](#-simple-mode-new-users)
- [Key Features](#key-features)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [For Framework Developers](#for-framework-developers--contributors)

---

## Overview

> **Note:** This project both **develops** the framework and **uses** it for its own development (self-hosting). See [Project Context](docs/PROJECT_CONTEXT.md).

**In the box:**
- **14 workflow agents** — Analyst, Planner, Architect, Designer, Implementer, Tester, Debugger, Documenter, Reviewer, Improver, Ops, Orchestrator, Enhancer, Evaluator
- **Simple Mode** — `@simple-mode *build "feature"`, `*review`, `*fix`, `*test`, and more in Cursor
- **Cursor Skills + Claude Desktop** — All agents as `@agent *command`; 15 Claude Desktop commands
- **11 YAML workflow presets** — rapid-dev, full-sdlc, maintenance, quality, quick-fix, and others
- **Experts & quality** — 16 built-in experts, 7-category code scoring, MCP gateway (Context7, Playwright, Git, …)

For the full list, see [Key Features](#key-features) and [Documentation](docs/README.md).

### How it works (no confusion version)

- **Cursor is the LLM runtime**: Skills use the developer's configured model in Cursor (Auto or pinned).
- **This framework is the tooling layer**: workflows, quality tools, reporting, worktrees, caching.
- **Cursor-native execution**: All LLM operations are handled by Cursor via Skills. No local LLM required.

See:
- `docs/HOW_IT_WORKS.md`
- `docs/CURRENT_DEFAULTS.md`
- `docs/PR_MODE_GUIDE.md`

### 🚀 Cursor Quick Start (5 minutes)

If you're using **Cursor IDE**, get started quickly:

1. **Install the framework:**

   Ensure Python 3.13+ (`python --version`). On Windows with multiple versions use `py -3.13`.

   ```bash
   # Linux/macOS:
   python3.13 -m pip install -e .
   # or: pip install -e .

   # Windows (if 3.13 is not default):
   py -3.13 -m pip install -e .
   ```

   Optionally run `python scripts/check_prerequisites.py` before installing.

   After installing, run `tapps-agents doctor` (or `python -m tapps_agents.cli doctor`) to verify the setup.

2. **Initialize Cursor integration:**

   Run `init` from your **project root**, not from the TappsCodingAgents framework directory.

   ```bash
   # Correct: from your project
   cd /path/to/your-project
   tapps-agents init
   # If 'tapps-agents' not found: python -m tapps_agents.cli init

   # Wrong: from the framework directory (creates config in the wrong place)
   # cd /path/to/TappsCodingAgents && tapps-agents init
   ```

   This installs:
   - ✅ **Cursor Skills** (`.claude/skills/`) - Use `@agent *command` in Cursor IDE
   - ✅ **Claude Desktop Commands** (`.claude/commands/`) - Use `@command` in Claude Desktop
   - ✅ **Cursor Rules** (`.cursor/rules/`)
   
   **Note:** If you get "command not found" error, use `python -m tapps_agents.cli` instead of `tapps-agents`. See [Troubleshooting Guide](docs/TROUBLESHOOTING_CLI_INSTALLATION.md) for details.

3. **Try it in Cursor IDE:**
   - Open Cursor chat
   - Type: `@reviewer *help`
   - Type: `@implementer *help`
   - Type: `@tester *help`
   - Type: `@evaluator *help`

4. **Or use Claude Desktop:**
   - Type: `@review src/api/auth.py`
   - Type: `@build "Create a user authentication feature"`
   - Type: `@test src/api/auth.py`


### 🎬 Try the Demo (5 minutes)

**Want to see it in action?** Run our interactive demo:

```bash
# Run the automated demo script
python demo/run_demo.py

# Or follow the quick start guide
cat demo/DEMO_QUICK_START.md
```

The demo showcases:
- ✅ Code scoring with objective metrics
- ✅ Code review with detailed feedback
- ✅ Quality tools (linting, type checking)
- ✅ Code generation workflows

See [Demo Plan](docs/DEMO_PLAN.md) for complete demo scenarios and instructions.

### 🎯 Simple Mode (New Users)

**New to TappsCodingAgents?** Try **Simple Mode** - a streamlined, task-first interface that hides complexity while showcasing the power of the framework:

1. **Initialize project** (first time setup):
   ```bash
   # If 'tapps-agents' command not found, use:
   python -m tapps_agents.cli init
   
   # OR if entry point is working:
   tapps-agents init
   ```
   This sets up configuration, Cursor Rules, workflow presets, Skills, and Claude Desktop Commands.

2. **Enable Simple Mode:**
   ```bash
   tapps-agents simple-mode on
   ```

3. **Run the onboarding wizard** (optional, recommended for new users):
   ```bash
   tapps-agents simple-mode init
   ```

4. **Use Simple Mode in Cursor chat:**
   
   Open Cursor chat and use natural language commands with `@simple-mode`:
   ```
   @simple-mode Build a user authentication module
   @simple-mode Review my authentication code
   @simple-mode Fix the error in auth.py
   @simple-mode Add tests for service.py
   @simple-mode Explore the authentication system
   @simple-mode Refactor legacy code in utils.py
   @simple-mode Plan analysis for OAuth2 migration
   @simple-mode PR "Add user authentication feature"
   @simple-mode *enhance "Add OAuth2 login"
   @simple-mode *breakdown "Migrate to microservices"
   @simple-mode *todo ready
   @simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
   ```
   
   Simple Mode automatically detects your intent and orchestrates the right agents.

**Note:** Simple Mode natural language commands work in Cursor chat (via `@simple-mode` skill). CLI management commands (`on`, `off`, `status`, `init`) are available for configuration.

**Simple Mode Features:**
- ✅ **Task-first interface** - Focus on what you want to achieve
- ✅ **Natural language commands** - Use plain English
- ✅ **Guided onboarding** - Interactive wizard for new users
- ✅ **Zero-config mode** - Smart defaults with auto-detection
- ✅ **Learning progression** - Unlock advanced features as you learn
- ✅ **Friendly error handling** - Clear messages with recovery suggestions

**Full Documentation:**
- [Simple Mode Guide](docs/SIMPLE_MODE_GUIDE.md) - Complete Simple Mode documentation
- [Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [Cursor Rules Setup Guide](docs/CURSOR_RULES_SETUP.md)
- [Cursor Integration Review](CURSOR_INTEGRATION_REVIEW.md) - Comprehensive integration status

### Enhanced Features (v1.6.0+)

- **Code Scoring System**: Objective quality metrics (complexity, security, maintainability)
- **Tiered Context Injection**: 90%+ token savings with intelligent caching
- **MCP Gateway**: Unified Model Context Protocol interface for tool access
  - **Context7 MCP Server**: Library documentation lookup (required, auto-configured)
  - **Playwright MCP Server**: Browser automation for E2E testing (optional, auto-detected)
  - **Beads (bd)** (optional): Task tracking; `tapps-agents beads`; doctor reports bd status; init hints `bd init` when detected. [Beads Integration](docs/BEADS_INTEGRATION.md)
- **YAML Workflow Definitions**: Declarative, version-controlled orchestration with strict schema enforcement
- **Greenfield/Brownfield Workflows**: Context-appropriate workflows for project types
- **YAML-First Architecture** ✅ (Epics 6-10 Complete):
  - **Strict Schema Enforcement** (Epic 6): All YAML structures validated and executed, no "YAML theater"
  - **Task Manifest Generation** (Epic 7): Auto-generated task checklists from workflow YAML + state
  - **Automated Documentation** (Epic 8): Cursor Rules auto-generated from workflow YAML
  - **Documentation Alignment** (Epic 10): All documentation aligned with YAML-first architecture
- **Cursor AI Integration**: Complete 7-phase integration with Cursor AI
  - Cursor Skills for all 14 agents
  - Multi-agent orchestration
  - Context7 KB-first caching

## Current Status

**Version** 3.5.21 · **Production ready** · All 7 Cursor AI integration phases complete · YAML-first architecture (Epics 6–10) · 14 workflow agents + Simple Mode · 16 built-in experts.

📋 [Changelog](CHANGELOG.md) · [Cursor AI Integration Plan](docs/CURSOR_AI_INTEGRATION_PLAN_2025.md) · [YAML Workflow Design](docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)

✅ **Core Framework Complete:**
- **All 14 Workflow Agents** ✅ (analyst, planner, architect, designer, implementer, tester, debugger, documenter, reviewer, improver, ops, orchestrator, enhancer, evaluator)
- **Complete Code Scoring System** ✅ (7 categories: complexity, security, maintainability, test_coverage, performance, structure, devex)
- **Instruction-Based Architecture** ✅ - Agents prepare structured instructions for Cursor Skills execution
- **Tiered Context System** ✅ (90%+ token savings, 3 tiers with caching)
- **Unified Cache Architecture** ✅ (Single interface for all caching systems with hardware auto-detection)
- **MCP Gateway** ✅ (Unified tool access with 5 servers: Context7, Playwright, Filesystem, Git, Analysis)
  - **MCP Server Detection**: Automatic detection of Context7 and Playwright MCP servers
  - **Setup Instructions**: Auto-generated setup instructions when MCP servers are missing
  - **Status Reporting**: `tapps-agents doctor` reports MCP server configuration status and Beads (bd) status (optional)
- **YAML Workflow Definitions** ✅ (Parser, executor, artifact tracking, conditional steps, gates)
  - **YAML-First Architecture** ✅ (Epics 6-10): YAML as single source of truth with strict schema enforcement
  - **Auto-Generated Artifacts** ✅: Task manifests, Cursor Rules docs
  - **Dependency-Based Parallelism**: Automatic parallel execution based on step dependencies (no `parallel_tasks`)
  - **11 Workflow Presets**: rapid-dev (enhance step), full-sdlc (optional enhance before requirements), maintenance, quality, quick-fix, feature-implementation, brownfield-analysis, simple-new-feature, simple-full, simple-improve-quality, simple-fix-issues
- **Industry Experts Framework** ✅ (Weighted decision-making, domain configuration, expert registry)
  - **16 Built-in Experts**: Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning
  - **100+ Knowledge Files**: Across 13 knowledge domains
  - **Configuration-Only Experts**: YAML-based expert definition, no code classes required
  - **RAG Integration**: Simple file-based and vector-based RAG for knowledge retrieval
- **Simple Mode** ✅ (10 orchestrators: build, review, fix, test, explore, refactor, plan-analysis, pr, epic, full; plus resume)
- **Scale-Adaptive Workflow Selection** ✅ (Project type auto-detection, workflow recommendation)
- **State Management** ✅ (Advanced workflow state persistence with checkpointing, migration, versioning, resume)
- **Analytics & Health** ✅ (Performance metrics, trends, system health monitoring, resource usage tracking)
- **Governance & Safety** ✅ (Secrets/PII filtering, knowledge ingestion safety)
- **Comprehensive test suite** ✅ (1200+ unit tests, integration tests, and E2E tests with parallel execution support - see `tests/`)

✅ **Enhancer Agent - Prompt Enhancement Utility (v1.6.0)**
- **7-Stage Enhancement Pipeline** - Transforms simple prompts into comprehensive, context-aware prompts
- **Industry Expert Integration** - Automatic domain detection and weighted expert consultation
- **Multiple Usage Modes** - Full enhancement, quick enhancement, stage-by-stage execution
- **Session Management** - Resume interrupted enhancements
- **Multiple Output Formats** - Markdown, JSON, YAML
- **Workflow integration** - full-sdlc (optional enhance step before requirements), rapid-dev, and Epic story workflows run the enhancer when an `enhance` step is present (EnhancerHandler). AnalystHandler and PlannerHandler consume `enhanced_prompt`/`description` from state.
- **CLI auto-enhancement** - `auto_enhancement` in config enhances low-quality prompts for implementer, planner, analyst (see [Configuration](docs/CONFIGURATION.md#automatic-prompt-enhancement-auto_enhancement)). `PROMPT_ARGUMENT_MAP` and `commands` control which agent/command pairs are eligible.
- See [Enhancer Agent Guide](docs/ENHANCER_AGENT.md) for details

🎉 **All Core Framework Features Complete!**

✅ **January 2026 Critical Features Complete:**
- **Custom Skills Support** ✅ - Create, validate, and integrate custom Skills
- **State Persistence Configuration** ✅ - Configurable checkpointing and cleanup policies
- **Governance & Safety Layer** ✅ - Security and safety controls for knowledge ingestion
- **Epic 20: Complexity Reduction** ✅ - Refactored high-complexity functions (122→C, 114→C, 66→C, 60→C, 64→A/B)
  - Agent handler extraction using Strategy Pattern
  - Workflow execution control flow simplification
  - Zero code duplication between execution paths
  - See [Complexity Reduction Summary](docs/COMPLEXITY_REDUCTION_EPIC_20.md)

## Upcoming Enhancements (Planned)

### SDLC Quality Engine Improvements

The framework is being enhanced to transform the SDLC from a linear pipeline with score-only gates into a **self-correcting quality engine** that achieves "zero issues" consistently across any codebase.

**Key Improvements:**
- **Pluggable Validation Layer**: Stack-agnostic validation that adapts to detected project profile and repository signals
- **Comprehensive Verification**: Expansion of "testing" into verification bundle (tests + linters + config checks + security scans + artifact integrity)
- **Standardized Issues Manifest**: Machine-actionable issue schema (id, severity, category, evidence, repro, suggested_fix, owner_step) for deterministic remediation
- **Composite Gating Model**: Gates evaluate issues + verification outcomes, not just numeric scores
  - Hard fail conditions: critical issues, verification failures, missing artifacts
  - Soft fail/loopback conditions: high issues above threshold, regression vs baseline, low expert confidence
- **Bounded Loopback Protocol**: Deterministic remediation with structured fix plans, re-validation, and bounded retries
- **Traceability Matrix**: Lightweight requirements → stories → validations mapping for completeness verification

**Status**: Design phase - See [SDLC Improvements Analysis](SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 1: SDLC Quality Engine](docs/prd/epic-1-sdlc-quality-engine.md)

### Dynamic Expert & RAG Engine

An always-on **Dynamic Knowledge/Expert Orchestrator** that automatically detects project domains, creates and curates experts/knowledge for the current project, and continuously enriches agents with the best available, project-relevant information.

**Key Features:**
- **Automatic Expert Creation**: Framework-controlled technical experts + project-controlled business/domain experts generated from repo signals
- **Knowledge Ingestion Pipeline**: Auto-fills RAG from project sources (requirements, architecture docs, ADRs), dependency sources (Context7 KB), and operational sources (CI failures, runtime exceptions)
- **Expert Engine Runtime**: Continuously detects what domain knowledge is needed, proactively consults the right experts, and populates knowledge stores as agents learn
- **Governance & Safety**: Do-not-index filters for secrets/PII, prompt-injection handling, retention & scope controls
- **Observability & Quality Improvement**: Metrics tracking (expert confidence, RAG quality, Context7 KB hit rate) with scheduled KB maintenance jobs

**Status**: Design phase - See [SDLC Improvements Analysis](SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](docs/prd/epic-2-dynamic-expert-rag-engine.md)

## Key Features

### Two-Layer Agent Model

| Layer | Type | Purpose | Count |
|-------|------|---------|-------|
| **Knowledge** | Industry Experts | Business domain authority | N (per project) |
| **Execution** | Workflow Agents | SDLC task execution | 14 (fixed) |

### Workflow Agents (14)

- **Planning**: 
  - **analyst** ✅ - Requirements gathering, stakeholder analysis, tech research, effort estimation, risk assessment, competitive analysis
  - **planner** ✅ - User story creation, task breakdown, story point estimation, acceptance criteria
- **Design**: 
  - **architect** ✅ - System architecture design, design patterns, tech selection, security architecture, boundary definition, architecture diagrams, pattern detection (*detect-patterns)
  - **designer** ✅ - API design, data model design, UI/UX design, wireframes, design systems
- **Development**: 
  - **implementer** ✅ - Code generation, refactoring, file writing with backup support
  - **debugger** ✅ - Error analysis, stack trace analysis, code execution tracing, root cause identification
  - **documenter** ✅ - API documentation, README generation, docstring generation, code documentation
- **Testing**: 
  - **tester** ✅ - Test generation (unit, integration), test execution, coverage analysis
- **Quality**: 
  - **reviewer** ✅ - Code review with 7-category scoring (complexity, security, maintainability, test coverage, performance, structure, devex), actionable feedback with specific issues and line numbers, structured feedback always provided, context-aware quality gates, linting (Ruff), type checking (mypy), duplication detection, security scanning, project analysis, service analysis
  - **improver** ✅ - Code refactoring, performance optimization, quality improvement suggestions
- **Operations**: 
  - **ops** ✅ - Security auditing, compliance checking (GDPR, HIPAA, PCI-DSS), dependency auditing, deployment planning
- **Orchestration**: 
  - **orchestrator** ✅ - Workflow coordination, step sequencing, gate decisions, workflow state management
- **Enhancement**: 
  - **enhancer** ✅ - 7-stage prompt enhancement pipeline (analysis, requirements, architecture, codebase, quality, strategy, synthesis), quick enhancement, stage-by-stage execution, session management
- **Evaluation**: 
  - **evaluator** ✅ - Framework effectiveness analysis, workflow evaluation, improvement recommendations, usage pattern analysis

### Code Scoring System

The Reviewer Agent includes a comprehensive code scoring system with 5 objective metrics and actionable feedback (2026-01-16):

**Enhanced Features:**
- ✅ **Accurate Test Coverage:** Returns 0.0% when no tests exist (not 5.0-6.0)
- ✅ **Maintainability Issues:** Specific issues with line numbers, severity, and suggestions
- ✅ **Structured Feedback:** Always provides actionable feedback (summary, strengths, issues, recommendations, priority)
- ✅ **Performance Issues:** Performance bottlenecks with line numbers and context
- ✅ **Accurate Type Checking:** Reflects actual mypy errors (not static 5.0)
- ✅ **Context-Aware Quality Gates:** Adapts thresholds for new/modified/existing files

The Reviewer Agent scoring system includes:

1. **Complexity Score** (0-10): Cyclomatic complexity analysis using Radon
2. **Security Score** (0-10): Vulnerability detection using Bandit + heuristics; npm audit for JS/TS
3. **Maintainability Score** (0-10): Maintainability Index using Radon MI
4. **Test Coverage Score** (0-10): Coverage data parsing + heuristic; Vitest/Jest/lcov for JS/TS
5. **Performance Score** (0-10): Static analysis (function size, nesting depth, pattern detection)
6. **Structure Score** (0-10): Project layout, key files (README, config, tests), conventions
7. **DevEx Score** (0-10): Docs (AGENTS.md, CLAUDE.md), config, tooling

All metrics are configurable with weighted scoring and quality thresholds.

### Industry Experts

- **Business Domain Experts** (N): Project-specific domain authorities (not technical specialists)
  - 1:1 mapping: N domains → N experts
  - Weighted decision-making (Primary: 51%, Others: 49%/(N-1))
  - RAG integration (simple file-based and vector-based)
  - Fine-tuning support (LoRA adapters - planned)
  - Consult-based integration with 6 workflow agents (Architect, Implementer, Reviewer, Tester, Designer, Ops)
- **Built-in Technical Experts** (16): Framework-controlled domain experts
  - Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning
  - 100+ knowledge files across 13 knowledge domains
  - Automatic domain detection and expert consultation
  - Project profiling for context-aware guidance
- **Expert Governance**: Secrets/PII filtering, prompt injection handling, knowledge ingestion safety

### CLI Commands

**Top-Level Commands:**
- `init` - Initialize project (Cursor Rules, Skills, config)
- `create <description>` - Create new project from natural language description
- `workflow <preset>` - Run workflow presets (rapid, full, fix, quality, hotfix, etc.)
- `continuous-bug-fix` - Continuously find and fix bugs from test failures (automated bug fixing loop)
- `score <file>` - Quick code quality scoring (shortcut for `reviewer score`)
- `doctor` - Environment diagnostics and validation
- `cursor verify` - Verify Cursor AI integration components
- `simple-mode <command>` - Simple Mode management (on, off, status, init, configure, progress, full, build, resume, enhance, breakdown, todo)
- `health <command>` - Health monitoring (check, dashboard, metrics, trends, usage). Use `health usage dashboard|agents|workflows|system|trends` for analytics (formerly `analytics`).
- `customize <command>` - Agent customization (init)
- `skill <command>` - Custom Skills management (validate, template)
- `install-dev` - Install development tools (ruff, mypy, pytest, pip-audit, pipdeptree)
- `setup-experts` - Expert setup wizard (init, add, remove, list)
- `status` - Unified status (active worktrees, progress)
- `generate-rules` - Generate Cursor Rules from workflow YAML

**Agent Commands** (use `tapps-agents <agent> help` for details):
- `analyst` - Requirements gathering, stakeholder analysis, tech research, effort estimation, risk assessment
- `architect` - System design, architecture diagrams, tech selection, security architecture, boundary definition
- `debugger` - Error debugging, stack trace analysis, code tracing
- `designer` - API design, data models, UI/UX design, wireframes, design systems
- `documenter` - Generate documentation, update README, document APIs
- `enhancer` - Prompt enhancement (full, quick, stage-by-stage, resume)
- `evaluator` - Framework effectiveness evaluation, workflow evaluation
- `implementer` - Code generation, refactoring
- `improver` - Code refactoring, performance optimization
- `ops` - Security scanning, compliance checks, dependency auditing, deployment planning, bundle analysis (audit-bundle)
- `orchestrator` - Workflow management, step coordination, gate decisions
- `planner` - Create plans, user stories, task breakdowns
- `reviewer` - Code review, scoring, actionable feedback with specific issues, structured feedback, context-aware quality gates, linting, type checking, reports, duplication detection, security scanning, project/service analysis
- `tester` - Generate and run tests, test coverage

**Workflow State Management:**
- `workflow state list` - List workflow states
- `workflow state show <id>` - Show workflow state details
- `workflow state cleanup` - Cleanup old workflow states
- `workflow cleanup-branches` - Cleanup workflow worktree branches
- `workflow resume` - Resume interrupted workflow

**Simple Mode Workflows** (in Cursor chat with `@simple-mode`):
- `*build <description>` - Complete feature development workflow (7 steps)
- `*review <file>` - Code quality review with improvements
- `*fix <file> <description>` - Systematic bug fixing workflow
- `*test <file>` - Test generation and execution
- `*explore <query>` - Codebase exploration and navigation
- `*refactor <file>` - Systematic code modernization with safety checks
- `*plan-analysis <description>` - Safe read-only code analysis and planning
- `*pr <title>` - Pull request creation with quality scores
- `*enhance "prompt"` - Prompt enhancement (EnhancerAgent)
- `*breakdown "prompt"` - Task breakdown (PlannerAgent)
- `*todo <bd args>` - Beads-backed todo (e.g. ready, create "Title")
- `*epic <epic-doc.md>` - Execute Epic documents with dependency resolution
- `*full <description>` - Full SDLC workflow (9 steps)

## Project Structure

```
TappsCodingAgents/
├── requirements/                  # Specification documents (see requirements/README.md)
│   ├── PROJECT_REQUIREMENTS.md    # Main requirements document
│   ├── agent_api.md               # Agent API specification
│   ├── agents.md                  # Agent types specification
│   ├── model_profiles.yaml        # Model configurations
│   └── template/                  # Templates and schemas
│
├── tapps_agents/                  # Framework source code
│   ├── agents/                    # All 14 workflow agents
│   │   ├── reviewer/             # Code review & scoring
│   │   ├── implementer/          # Code generation
│   │   ├── tester/               # Test generation
│   │   └── ...                   # 11 more agents (14 total)
│   ├── core/                     # Core framework components
│   ├── context7/                 # Context7 KB integration
│   ├── experts/                  # Industry experts framework
│   ├── workflow/                 # Workflow engine
│   └── mcp/                      # MCP Gateway
│
├── .claude/                       # Cursor Skills (canonical; init copies from tapps_agents/resources/claude)
├── workflows/                     # YAML workflow definitions and presets
├── examples/                      # Example configurations
├── docs/                          # Documentation
│   ├── implementation/           # EPIC/PHASE plans, IMPROVEMENT_PLAN.json
│   ├── archive/                  # Archived summaries; stories in archive/stories/
│   ├── releases/                 # Release notes
│   ├── context7/                 # Context7 integration
│   └── operations/               # Deployment, release, package distribution
├── scripts/                       # Utilities (see scripts/README.md)
├── templates/                     # Agent roles, project types, tech stacks, cursor-rules-template
└── tests/                         # Test suite
    ├── unit/                      # Unit tests (fast, isolated)
    ├── integration/               # Integration tests (with real services)
    └── e2e/                       # End-to-end tests (see tests/e2e/README.md)
```

## Documentation

### Getting Started
- **[Quick Start Guide](docs/guides/QUICK_START.md)** - 🚀 Get started in 10 minutes
- **[Simple Mode Guide](docs/SIMPLE_MODE_GUIDE.md)** - 🎯 Simple Mode for new users (task-first, natural language)
- **[Cursor AI Integration Plan 2025](docs/CURSOR_AI_INTEGRATION_PLAN_2025.md)** - Complete integration roadmap (all 7 phases complete)
- **[Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Install and use Cursor Skills
- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[API Reference](docs/API.md)** - Python API and CLI documentation
- **[Enhancer Agent Guide](docs/ENHANCER_AGENT.md)** - Prompt enhancement utility documentation

### Complete Command Reference
- **Cursor Rules**: `.cursor/rules/command-reference.mdc` (installed by `tapps-agents init`) - **Complete command reference with all commands, subcommands, and parameters**
- **Quick Reference**: `.cursor/rules/quick-reference.mdc` - Quick command reference for common tasks
- **Agent Capabilities**: `.cursor/rules/agent-capabilities.mdc` - Detailed agent capability descriptions
- **Simple Mode Guide**: `.cursor/rules/simple-mode.mdc` - Simple Mode workflow documentation

**Note**: After running `tapps-agents init`, all command reference documentation is available in `.cursor/rules/` directory. The `command-reference.mdc` file contains the most comprehensive documentation with all commands, subcommands, parameters, and examples.

### Core Guides
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System architecture and design
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration reference
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup and workflows
- **[User Role Templates Guide](docs/USER_ROLE_TEMPLATES_GUIDE.md)** - Customize agents by role (senior-dev, junior-dev, tech-lead, PM, QA)
- **[Customization Guide](docs/CUSTOMIZATION_GUIDE.md)** - Project-specific agent customizations

### Cursor AI Integration
- **[Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Install and configure Cursor Skills
- **[Custom Skills Guide](docs/CUSTOM_SKILLS_GUIDE.md)** - Create, validate, and manage custom Skills
- **[Cursor Rules Setup Guide](docs/CURSOR_RULES_SETUP.md)** - Cursor Rules setup (auto-generated from YAML workflows)
- **[Multi-Agent Orchestration Guide](docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md)** - Parallel agent execution
- **[YAML Workflow Architecture Design](docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)** - YAML-first architecture with generated artifacts
- **[Unified Cache Architecture](docs/implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md)** - Single interface for all caching systems
- **[Unified Cache Integration Guide](docs/implementation/UNIFIED_CACHE_INTEGRATION_GUIDE.md)** - Using unified cache in agents
- **[Context7 Cache Optimization](docs/CONTEXT7_CACHE_OPTIMIZATION.md)** - Optimize cache hit rates
- **[Context7 Security & Privacy](docs/context7/CONTEXT7_SECURITY_PRIVACY.md)** - Security best practices
- **[Playwright MCP Integration](docs/PLAYWRIGHT_MCP_INTEGRATION.md)** - Browser automation with Playwright MCP server
### Operations
- **[Deployment Guide](docs/operations/DEPLOYMENT.md)** - Production deployment instructions
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Checkpoint & Resume Guide](docs/CHECKPOINT_RESUME_GUIDE.md)** - State persistence and workflow resumption
- **[Test Suite Documentation](tests/README.md)** - Complete test suite overview and E2E test guide
- **[E2E Test Suite](tests/e2e/README.md)** - End-to-end test documentation (smoke, workflow, scenario, CLI tests)
- **[Test Performance Guide](docs/TEST_PERFORMANCE_GUIDE.md)** - Optimize test execution (5-10x faster with parallel execution)
- **[Hardware Recommendations](docs/HARDWARE_RECOMMENDATIONS.md)** - Optimal computer specs for fast development
- **[Security Policy](SECURITY.md)** - Security guidelines

### Contributing

**Get help:** [CONTRIBUTING](CONTRIBUTING.md) · [Documentation](docs/README.md)

- **[Contributing Guidelines](CONTRIBUTING.md)** — How to contribute
- **[Changelog](CHANGELOG.md)** — Version history and changes

### Version Management

When updating the version number, use the automated script to ensure all files are updated consistently:

```powershell
# Update version to 3.0.4 (or any version)
.\scripts\update_version.ps1 -Version 3.0.4

# Update core files only (skip documentation)
.\scripts\update_version.ps1 -Version 3.0.4 -SkipDocs
```

**What it updates:**
- ✅ `pyproject.toml` - Package version
- ✅ `tapps_agents/__init__.py` - Module version
- ✅ `README.md` - Version badge and references
- ✅ `docs/README.md` - Documentation version
- ✅ `docs/API.md` - API version
- ✅ `docs/ARCHITECTURE.md` - Architecture version
- ✅ `docs/implementation/IMPROVEMENT_PLAN.json` - Metadata version
- ✅ Other documentation files with version references

**After running the script:**
1. Review changes: `git diff`
2. Update `CHANGELOG.md` with release notes
3. Commit and push changes
4. Create git tag: `git tag v3.0.4 && git push origin v3.0.4`

See [Release Guide](docs/operations/RELEASE_GUIDE.md) for complete release process.

### Reference
- **[Project Requirements](requirements/PROJECT_REQUIREMENTS.md)** - Complete specification
- **[Technology Stack](requirements/TECH_STACK.md)** - Recommended technologies

## Status

**Phase**: ✅ **All 7 Phases Complete - Cursor AI Integration Plan 2025**  
**Version**: 3.5.21  
**Last Updated**: January 2026  
**Cursor AI Integration**: ✅ Complete (Phases 1-7)  
**Dependencies**: ✅ Updated to latest 2025 stable versions (pytest 9.x, ruff 0.14.8, mypy 1.19.0, etc.)

### Integration Status
- ✅ Phase 1: Core Agents to Skills
- ✅ Phase 2: Quality Tools Integration
- ✅ Phase 3: Remaining Agents + Advanced Features
- ✅ Phase 5: Multi-Agent Orchestration
- ✅ Phase 6: Context7 Optimization + Security
- ✅ Phase 7: NUC Optimization

See [Cursor AI Integration Plan 2025](docs/CURSOR_AI_INTEGRATION_PLAN_2025.md) for complete details.

## Self-Hosting

This project uses its own framework for development:
- **5 Industry Experts** configured (AI frameworks, code quality, architecture, DevOps, documentation)
- **Enhancer Agent** actively used (23+ enhancement sessions)
- **Context7 Integration** with KB cache
- **14 Cursor Skills** available in `.claude/skills/` (14 agent skills + simple-mode)
- **NUC Optimization** enabled for resource-constrained environments
- Configuration in `.tapps-agents/` directory

See [Self-Hosting Setup](docs/implementation/SELF_HOSTING_SETUP_COMPLETE.md) for details.

## Platform & repository

- **Windows:** Supported (Windows, Linux, macOS). Use UTF-8 for scripts and file I/O. See [Troubleshooting](docs/TROUBLESHOOTING.md) and [CONTRIBUTING](CONTRIBUTING.md) for encoding guidelines.
- **Repository:** Dependabot, CODEOWNERS, issue/PR templates, GitHub Actions, SECURITY.md. See [CONTRIBUTING](CONTRIBUTING.md) and [.github/](.github/).

## For Framework Developers & Contributors

- **Accuracy:** Agents and skills must report only verified facts. Do not assume success from tests or error handling. See project rules in `.cursor/rules/` and [CONTRIBUTING](CONTRIBUTING.md).
- **Framework changes:** When modifying `tapps_agents/`, use the Full SDLC workflow: `@simple-mode *full "Implement [description]"` or `tapps-agents simple-mode full --prompt "..." --auto`. See [Framework Development Workflow](docs/FRAMEWORK_DEVELOPMENT_WORKFLOW.md).

## License

See [LICENSE](LICENSE) file for details.
