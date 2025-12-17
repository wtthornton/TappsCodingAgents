# TappsCodingAgents

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](README.md)
[![Version](https://img.shields.io/badge/version-2.0.2-blue.svg)](CHANGELOG.md)

**A specification framework for defining, configuring, and orchestrating coding agents.**

## Overview

TappsCodingAgents provides a standardized framework for building AI coding agents with:

> **Note**: This project both **develops** the TappsCodingAgents framework AND **uses** it for its own development (self-hosting). See [Project Context](docs/PROJECT_CONTEXT.md) for details.

- **Workflow Agents** (13): Standard SDLC task execution + Prompt Enhancement
- **Industry Experts** (N): Business domain knowledge with weighted decision-making
- **Built-in Experts** (16): Framework-controlled technical domain experts (Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning)
- **Expert Integration** (6 agents): Architect, Implementer, Reviewer, Tester, Designer, and Ops agents consult relevant experts for enhanced decision-making
- **Project Profiling System** (v1.0.0+): Automatic detection of project characteristics (deployment type, tenancy, user scale, compliance, security) for context-aware expert guidance
- **Improved Confidence System**: Weighted confidence calculation with agent-specific thresholds and metrics tracking, including project context relevance
- **Model Abstraction Layer (MAL)**: Hybrid local/cloud model routing
- **RAG Integration**: Retrieval-augmented generation for domain knowledge
- **Fine-Tuning Support**: LoRA adapters for domain specialization
- **Cursor AI Integration** ✅: Complete integration with Cursor AI (all 7 phases)
  - **13 Cursor Skills** (All agents available as Cursor Skills)
  - **Custom Skills Support** ✅ (Create, validate, and integrate custom Skills)
  - **Background Agents** (Offload heavy tasks to cloud/remote)
  - **Background Agent Auto-Execution** ✅ (Automatic workflow step execution with polling)
  - **Multi-Agent Orchestration** (Parallel execution with conflict resolution)
  - **Context7 Integration** (KB-first caching + analytics)
  - **NUC Optimization** (Resource monitoring, fallback strategy)
  - **Governance & Safety Layer** ✅ (Secrets/PII filtering, prompt injection handling, approval workflow)
- **User Role Templates** ✅: Role-specific agent customization (senior-dev, junior-dev, tech-lead, PM, QA)
  - Customize agent behavior based on user role
  - 5 built-in role templates with sensible defaults
  - Fully customizable and extensible
- **Claude Code Compatible**: Native Agent Skills format
- **Prompt Enhancement Utility**: Transform simple prompts into comprehensive, context-aware prompts
- **Project Profiling**: Automatic detection of project characteristics for context-aware expert advice

### How it works (no confusion version)

- **Cursor is the LLM runtime**: Skills and Background Agents use the developer’s configured model in Cursor (Auto or pinned).
- **This framework is the tooling layer**: workflows, quality tools, reporting, worktrees, caching.
- **Local LLM is optional (headless-only)**: MAL (Ollama/cloud) is intended for CLI/CI usage outside Cursor.

See:
- `docs/HOW_IT_WORKS.md`
- `docs/CURRENT_DEFAULTS.md`
- `docs/PR_MODE_GUIDE.md`

### Enhanced Features (v1.6.0+)

- **Code Scoring System**: Objective quality metrics (complexity, security, maintainability)
- **Tiered Context Injection**: 90%+ token savings with intelligent caching
- **MCP Gateway**: Unified Model Context Protocol interface for tool access
- **YAML Workflow Definitions**: Declarative, version-controlled orchestration
- **Greenfield/Brownfield Workflows**: Context-appropriate workflows for project types
- **Cursor AI Integration**: Complete 7-phase integration with Cursor AI
  - Cursor Skills for all 13 agents
  - Background Agents for heavy tasks
  - Multi-agent orchestration
  - Context7 KB-first caching
  - NUC optimization for low-power hardware

## Current Status (January 2026)

🎉 **PHASE 5 EXPERT FRAMEWORK ENHANCEMENT COMPLETE** 🎉

✅ **Phase 5: Expert Framework Enhancement - High Priority Experts**
- **4 New Built-in Experts** ✅ (Observability, API Design, Cloud Infrastructure, Database)
- **32 New Knowledge Files** ✅ (~120,000+ words of expert knowledge)
- **Enhanced Agent Support** ✅ (Updated expert consultation for Architect, Implementer, Designer, Ops, Reviewer, Tester agents)
- **Total Built-in Experts: 16** (Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database, Agent Learning)
- **Total Knowledge Files: 83** (across 11 knowledge domains: security, performance, testing, data-privacy-compliance, accessibility, user-experience, observability-monitoring, api-design-integration, cloud-infrastructure, database-data-management, agent-learning)
- See [Built-in Experts Guide](docs/BUILTIN_EXPERTS_GUIDE.md) and [Phase 5 Implementation Plan](implementation/PHASE5_EXPERT_IMPLEMENTATION_PLAN.md)

🎉 **ALL 7 PHASES COMPLETE - Cursor AI Integration Plan 2025** 🎉

🎉 **JANUARY 2026 ENHANCEMENTS COMPLETE** 🎉

✅ **P2 Medium Priority Enhancements - All Complete**
- **Project Profiling System** ✅ (Auto-detection of project characteristics for context-aware expert guidance)
- **Modernize Project Configuration** ✅ (Migrated to pyproject.toml with build system)
- **Advanced Workflow State Persistence** ✅ (State validation, migration, versioning, enhanced recovery)
- **State Persistence Configuration** ✅ (Configurable checkpoint frequency, cleanup policies, runtime reload)
- **Advanced Analytics Dashboard** ✅ (Performance metrics, historical trends, CLI commands)
- **Custom Skills Support** ✅ (Create, validate, and integrate custom Skills)
- **Background Agent Auto-Execution** ✅ (Automatic workflow step execution with polling and monitoring)
- **Governance & Safety Layer** ✅ (Secrets/PII filtering, prompt injection handling, approval workflow)

✅ **P3 Low Priority Enhancements - Critical Items Complete**
- **Error Handling Improvements** ✅ (Custom exception types, improved error messages)
- **Configuration Management Improvements** ✅ (All expert thresholds moved to configuration)
- **Documentation Alignment** ✅ (Updated version numbers, marked historical docs)

✅ **Phase 7 Complete - NUC Optimization**
- **Resource Monitoring** ✅ (CPU, memory, disk usage tracking with alerts)
- **Background Agent Fallback** ✅ (Automatic task routing based on resource constraints)
- **Performance Benchmarks** ✅ (Before/after optimization comparisons)
- **NUC Configuration** ✅ (Optimized settings for low-power hardware)
- See [NUC Setup Guide](docs/NUC_SETUP_GUIDE.md) and [Phase 7 Summary](implementation/PHASE7_NUC_OPTIMIZATION_COMPLETE.md)

✅ **Phase 6 Complete - Context7 Optimization + Security**
- **Security Audit Tools** ✅ (SecurityAuditor, APIKeyManager for SOC 2 compliance)
- **KB Usage Analytics** ✅ (Tracking, dashboard, performance metrics)
- **Cross-Reference Resolution** ✅ (Automatic linking of related documentation)
- **Cache Pre-population** ✅ (Dependency-based warming)
- See [Context7 Security & Privacy](docs/CONTEXT7_SECURITY_PRIVACY.md) and [Phase 6 Summary](implementation/PHASE6_CONTEXT7_OPTIMIZATION_SECURITY_COMPLETE.md)

✅ **Phase 5 Complete - Multi-Agent Orchestration**
- **Parallel Agent Execution** ✅ (Multi-agent workflows with conflict resolution)
- **Git Worktree Management** ✅ (Isolated agent changes, no conflicts)
- **Result Aggregation** ✅ (Collecting and summarizing multi-agent outputs)
- **Performance Monitoring** ✅ (Speedup tracking, efficiency metrics)
- See [Multi-Agent Orchestration Guide](docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md) and [Phase 5 Summary](implementation/PHASE5_MULTI_AGENT_ORCHESTRATION_COMPLETE.md)

✅ **Phase 4 Complete - Background Agents Integration**
- **Cursor Background Agents** ✅ (Offload heavy tasks to cloud/remote agents)
- **CLI Wrapper** ✅ (Command-line interface for Background Agents)
- **Progress Reporting** ✅ (Real-time task progress tracking)
- **Result Delivery** ✅ (File, PR, web app delivery methods)
- See [Background Agents Guide](docs/BACKGROUND_AGENTS_GUIDE.md) and [Phase 4 Summary](implementation/PHASE4_BACKGROUND_AGENTS_COMPLETE.md)

✅ **Phase 3 Complete - Remaining Agents + Advanced Features**
- **All 13 Cursor Skills** ✅ (Analyst, Planner, Architect, Designer, Implementer, Tester, Debugger, Documenter, Reviewer, Improver, Ops, Orchestrator, Enhancer)
- **Context7 Integration** ✅ (KB-first caching for library documentation)
- **Industry Experts** ✅ (Domain expert consultation framework)
- **YAML Workflows** ✅ (Declarative multi-step task definitions)
- **Tiered Context System** ✅ (90%+ token savings)
- **MCP Gateway** ✅ (Unified tool access)
- See [Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md) and [Phase 3 Summary](implementation/PHASE3_REMAINING_AGENTS_COMPLETE.md)

✅ **Phase 2 Complete - Quality Tools Integration**
- **Ruff Integration** ✅ (10-100x faster Python linting, 2025 standard)
- **mypy Type Checking** ✅ (Static type analysis, 2025 standard)
- **Comprehensive Reporting** ✅ (JSON, Markdown, HTML with historical tracking)
- **TypeScript & JavaScript Support** ✅ (ESLint, TypeScript compiler integration)
- **Multi-Service Analysis** ✅ (Batch analysis with service-level aggregation)
- **Dependency Security Auditing** ✅ (pip-audit, pipdeptree integration)
- **Code Duplication Detection** ✅ (jscpd for Python and TypeScript)
- See [Quality Tools Usage Examples](docs/QUALITY_TOOLS_USAGE_EXAMPLES.md) and [Phase 2 Summary](implementation/PHASE2_QUALITY_TOOLS_COMPLETE.md)

✅ **Phase 1 Complete - Core Agents to Skills**
- **4 Core Cursor Skills** ✅ (Reviewer, Implementer, Tester, Debugger)
- **Context7 Integration** ✅ (KB-first caching)
- **Cache Pre-population** ✅ (Common libraries pre-loaded)
- See [Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md) and [Phase 1 Summary](implementation/PHASE1_CURSOR_SKILLS_COMPLETE.md)

✅ **Core Framework Complete:**
- **All 13 Workflow Agents** (analyst, planner, architect, designer, implementer, tester, debugger, documenter, reviewer, improver, ops, orchestrator, enhancer)
- **Complete Code Scoring System** (5/5 metrics: complexity, security, maintainability, test_coverage, performance)
- **Model Abstraction Layer (MAL)** - Ollama + Cloud Fallback (Anthropic & OpenAI)
- **Tiered Context System** (90%+ token savings, 3 tiers with caching)
- **Unified Cache Architecture** ✅ (Single interface for all caching systems with hardware auto-detection)
- **MCP Gateway** (Unified tool access with filesystem, Git, and analysis servers)
- **YAML Workflow Definitions** (Parser, executor, artifact tracking, conditional steps)
- **Industry Experts Framework** (Weighted decision-making, domain configuration, expert registry)
- **Configuration-Only Experts** (YAML-based expert definition, no code classes required)
- **Simple File-Based RAG** (Knowledge base retrieval for experts)
- **Scale-Adaptive Workflow Selection** (Project type auto-detection, workflow recommendation)
- **Comprehensive test suite** (1200+ unit tests, integration tests, and E2E tests with parallel execution support - see `tests/`)

✅ **Enhancer Agent - Prompt Enhancement Utility (v1.6.0)**
- **7-Stage Enhancement Pipeline** - Transforms simple prompts into comprehensive, context-aware prompts
- **Industry Expert Integration** - Automatic domain detection and weighted expert consultation
- **Multiple Usage Modes** - Full enhancement, quick enhancement, stage-by-stage execution
- **Session Management** - Resume interrupted enhancements
- **Multiple Output Formats** - Markdown, JSON, YAML
- See [Enhancer Agent Guide](docs/ENHANCER_AGENT.md) for details

🎉 **All Core Framework Features Complete!**

✅ **January 2026 Critical Features Complete:**
- **Custom Skills Support** ✅ - Create, validate, and integrate custom Skills
- **Background Agent Auto-Execution** ✅ - Automatic workflow execution with monitoring
- **State Persistence Configuration** ✅ - Configurable checkpointing and cleanup policies
- **Governance & Safety Layer** ✅ - Security and safety controls for knowledge ingestion

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
- **Governance & Safety**: Do-not-index filters for secrets/PII, prompt-injection handling, retention & scope controls, optional human approval mode
- **Observability & Quality Improvement**: Metrics tracking (expert confidence, RAG quality, Context7 KB hit rate) with scheduled KB maintenance jobs

**Status**: Design phase - See [SDLC Improvements Analysis](SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](docs/prd/epic-2-dynamic-expert-rag-engine.md)

## Key Features

### Two-Layer Agent Model

| Layer | Type | Purpose | Count |
|-------|------|---------|-------|
| **Knowledge** | Industry Experts | Business domain authority | N (per project) |
| **Execution** | Workflow Agents | SDLC task execution | 13 (fixed) |

### Workflow Agents (13)

- **Planning**: analyst ✅, planner ✅ (Story Generation)
- **Design**: architect ✅, designer ✅
- **Development**: implementer ✅ (Code Generation & Refactoring), debugger ✅ (Error Analysis & Code Tracing), documenter ✅ (API Docs & README Generation)
- **Testing**: tester ✅ (Test Generation & Execution)
- **Quality**: reviewer ✅ (with Code Scoring & Phase 6 Quality Tools), improver ✅ (Refactoring & Optimization)
- **Operations**: ops ✅ (Security, Compliance, Deployment, Dependency Auditing)
- **Orchestration**: orchestrator ✅ (Workflow Coordination)
- **Enhancement**: enhancer ✅ (Prompt Enhancement Utility with Expert Integration)

### Code Scoring System

The Reviewer Agent includes a comprehensive code scoring system with 5 objective metrics:

1. **Complexity Score** (0-10): Cyclomatic complexity analysis using Radon
2. **Security Score** (0-10): Vulnerability detection using Bandit + heuristics
3. **Maintainability Score** (0-10): Maintainability Index using Radon MI
4. **Test Coverage Score** (0-10): Coverage data parsing + heuristic analysis
5. **Performance Score** (0-10): Static analysis (function size, nesting depth, pattern detection)

All metrics are configurable with weighted scoring and quality thresholds.

### Industry Experts

- Business domain authorities (not technical specialists)
- 1:1 mapping: N domains → N experts
- Weighted decision-making (Primary: 51%, Others: 49%/(N-1))
- RAG + Fine-tuning capabilities
- Consult-based integration with workflow agents

## Project Structure

```
TappsCodingAgents/
├── requirements/                  # Specification documents
│   ├── PROJECT_REQUIREMENTS.md    # Main requirements document
│   ├── agent_api.md               # Agent API specification
│   ├── agents.md                  # Agent types specification
│   ├── model_profiles.yaml        # Model configurations
│   └── template/                  # Templates and schemas
│
├── tapps_agents/                  # Framework source code
│   ├── agents/                    # All 13 workflow agents
│   │   ├── reviewer/             # Code review & scoring
│   │   ├── implementer/          # Code generation
│   │   ├── tester/               # Test generation
│   │   └── ...                   # 10 more agents
│   ├── core/                     # Core framework components
│   ├── context7/                 # Context7 KB integration
│   ├── experts/                  # Industry experts framework
│   ├── workflow/                 # Workflow engine
│   └── mcp/                      # MCP Gateway
├── agents/                        # Cursor Skills (legacy location)
├── workflows/                     # YAML workflow definitions
├── examples/                      # Example configurations
├── docs/                          # Comprehensive documentation
├── requirements/                 # Project specifications
└── tests/                         # Test suite
    ├── unit/                      # Unit tests (fast, isolated)
    ├── integration/               # Integration tests (with real services)
    └── e2e/                       # End-to-end tests (see tests/e2e/README.md)
```

## Documentation

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - 🚀 Get started in 10 minutes
- **[Cursor AI Integration Plan 2025](docs/CURSOR_AI_INTEGRATION_PLAN_2025.md)** - Complete integration roadmap (all 7 phases complete)
- **[Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Install and use Cursor Skills
- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[API Reference](docs/API.md)** - Python API and CLI documentation
- **[Enhancer Agent Guide](docs/ENHANCER_AGENT.md)** - Prompt enhancement utility documentation

### Core Guides
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System architecture and design
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration reference
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup and workflows
- **[User Role Templates Guide](docs/USER_ROLE_TEMPLATES_GUIDE.md)** - Customize agents by role (senior-dev, junior-dev, tech-lead, PM, QA)
- **[Customization Guide](docs/CUSTOMIZATION_GUIDE.md)** - Project-specific agent customizations

### Cursor AI Integration
- **[Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Install and configure Cursor Skills
- **[Custom Skills Guide](docs/CUSTOM_SKILLS_GUIDE.md)** - Create, validate, and manage custom Skills
- **[Background Agents Guide](docs/BACKGROUND_AGENTS_GUIDE.md)** - Configure Background Agents for heavy tasks
- **[Background Agent Auto-Execution Guide](docs/BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md)** - Automatic workflow execution
- **[Multi-Agent Orchestration Guide](docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md)** - Parallel agent execution
- **[Unified Cache Architecture](implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md)** - Single interface for all caching systems
- **[Unified Cache Integration Guide](implementation/UNIFIED_CACHE_INTEGRATION_GUIDE.md)** - Using unified cache in agents
- **[Context7 Cache Optimization](docs/CONTEXT7_CACHE_OPTIMIZATION.md)** - Optimize cache hit rates
- **[Context7 Security & Privacy](docs/CONTEXT7_SECURITY_PRIVACY.md)** - Security best practices
- **[NUC Setup Guide](docs/NUC_SETUP_GUIDE.md)** - Optimize for low-power hardware

### Operations
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Checkpoint & Resume Guide](docs/CHECKPOINT_RESUME_GUIDE.md)** - State persistence and workflow resumption
- **[Test Suite Documentation](tests/README.md)** - Complete test suite overview and E2E test guide
- **[E2E Test Suite](tests/e2e/README.md)** - End-to-end test documentation (smoke, workflow, scenario, CLI tests)
- **[Test Performance Guide](docs/TEST_PERFORMANCE_GUIDE.md)** - Optimize test execution (5-10x faster with parallel execution)
- **[Hardware Recommendations](docs/HARDWARE_RECOMMENDATIONS.md)** - Optimal computer specs for fast development
- **[Security Policy](SECURITY.md)** - Security guidelines

### Contributing
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute
- **[Changelog](CHANGELOG.md)** - Version history and changes

### Reference
- **[Project Requirements](requirements/PROJECT_REQUIREMENTS.md)** - Complete specification
- **[Technology Stack](requirements/TECH_STACK.md)** - Recommended technologies

## Status

**Phase**: ✅ **All 7 Phases Complete - Cursor AI Integration Plan 2025**  
**Version**: 2.0.2  
**Last Updated**: January 2026  
**Cursor AI Integration**: ✅ Complete (Phases 1-7)  
**Dependencies**: ✅ Updated to latest 2025 stable versions (pytest 9.x, ruff 0.14.8, mypy 1.19.0, etc.)

### Integration Status
- ✅ Phase 1: Core Agents to Skills
- ✅ Phase 2: Quality Tools Integration
- ✅ Phase 3: Remaining Agents + Advanced Features
- ✅ Phase 4: Background Agents Integration
- ✅ Phase 5: Multi-Agent Orchestration
- ✅ Phase 6: Context7 Optimization + Security
- ✅ Phase 7: NUC Optimization

See [Cursor AI Integration Plan 2025](docs/CURSOR_AI_INTEGRATION_PLAN_2025.md) for complete details.

## Self-Hosting

This project uses its own framework for development:
- **5 Industry Experts** configured (AI frameworks, code quality, architecture, DevOps, documentation)
- **Enhancer Agent** actively used (23+ enhancement sessions)
- **Context7 Integration** with KB cache
- **13 Cursor Skills** available in `.claude/skills/`
- **Background Agents** configured in `.cursor/background-agents.yaml`
- **NUC Optimization** enabled for resource-constrained environments
- Configuration in `.tapps-agents/` directory

See [Self-Hosting Setup](implementation/SELF_HOSTING_SETUP_COMPLETE.md) for details.

## GitHub Best Practices (2025)

This project follows 2025 GitHub best practices for open-source development:

### ✅ Automated Dependency Management
- **Dependabot** configured for automated dependency updates (weekly for pip, monthly for GitHub Actions)
- Dependency grouping to reduce PR noise
- Automatic security vulnerability scanning

### ✅ Code Review & Ownership
- **CODEOWNERS** file for automatic code review assignments
- Clear ownership structure for different parts of the codebase

### ✅ Issue & Pull Request Templates
- Structured **bug report** template for consistent issue reporting
- **Feature request** template for enhancement proposals
- **Pull request** template with checklist and guidelines
- Issue templates guide users to appropriate channels (Discussions, Security Advisories)

### ✅ Continuous Integration
- **GitHub Actions** workflows with:
  - Separate jobs for linting, type checking, and testing
  - Concurrency control to cancel in-progress runs
  - Caching for faster builds
  - Coverage reporting with Codecov integration
  - Latest action versions (actions/checkout@v4, actions/setup-python@v5, codecov/codecov-action@v4)

### ✅ Security
- **SECURITY.md** with vulnerability reporting guidelines
- Security best practices documentation
- Automated dependency vulnerability scanning

### ✅ Documentation
- Comprehensive **README.md** with clear project overview
- **CONTRIBUTING.md** with contribution guidelines
- **CHANGELOG.md** following Keep a Changelog format
- Extensive documentation in `docs/` directory

### ✅ Project Health
- Clear license (MIT) in LICENSE file
- Community guidelines in CONTRIBUTING.md
- Security policy in SECURITY.md
- Issue templates for better issue management

## License

See [LICENSE](LICENSE) file for details.
