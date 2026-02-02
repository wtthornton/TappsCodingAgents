---
title: TappsCodingAgents Documentation Index
version: 3.5.39
status: active
last_updated: 2026-01-20
tags: [documentation, index, navigation]
---

# TappsCodingAgents Documentation

Welcome to the documentation for TappsCodingAgents.

## 🚀 Quick Start Paths

**New to TappsCodingAgents?**
1. **[Quick Start Guide](guides/QUICK_START.md)** - Get up and running in 5 minutes
2. **[Simple Mode Guide](SIMPLE_MODE_GUIDE.md)** - Start with natural language commands
3. **[Current Defaults](CURRENT_DEFAULTS.md)** - Understand what happens by default

**Setting up in a project?**
1. Run `tapps-agents init` to set up Cursor integration
2. See **[Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)**
3. Try `@simple-mode *build "description"` in Cursor chat

**Framework developer?**
1. Read **[Project Context](PROJECT_CONTEXT.md)** - Understand dual nature
2. See **[Architecture Overview](ARCHITECTURE.md)** - System architecture
3. Review **[Architecture Decisions](architecture/decisions/)** - ADRs for major decisions

## 📚 Documentation Structure

### Getting Started
- **[Quick Start Guide](guides/QUICK_START.md)** - Get up and running quickly
- **[Simple Mode Guide](SIMPLE_MODE_GUIDE.md)** - 🎯 Simple Mode for new users (task-first, natural language)
- **[Epic Workflow Guide](EPIC_WORKFLOW_GUIDE.md)** - Execute Epic documents with story dependency resolution
- **[Current Defaults](CURRENT_DEFAULTS.md)** - What happens by default (no surprises)
- **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
- **[Model Selection](MODEL_SELECTION.md)** - model_profile resolution and overrides
- **[API Reference](API.md)** - Python API + CLI overview

### Core Concepts
- **[Project Context](PROJECT_CONTEXT.md)** - Framework development vs. self-hosting
- **[Project Structure](PROJECT_STRUCTURE.md)** - File organization and cleanup best practices
- **[How It Works (Cursor-first)](HOW_IT_WORKS.md)** - The "brain vs hands" model, directories, and runtime policy
- **[Architecture Overview](ARCHITECTURE.md)** - System architecture and key modules
- **[YAML Workflow Architecture Design](YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)** - YAML-first architecture with generated artifacts (Epics 6-10 Complete)
- **[Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)** - Choosing and running workflows
- **[Workflow Execution Summary](WORKFLOW_EXECUTION_SUMMARY.md)** - Quick reference for parallel execution
- **[Quick Start: 2025 Optimizations](QUICK_START_OPTIMIZATIONS.md)** - Quick reference for new performance optimizations

### Experts
- **[Expert Setup Wizard](EXPERT_SETUP_WIZARD.md)** - CLI wizard for experts and knowledge base
- **[Expert Configuration Guide](EXPERT_CONFIG_GUIDE.md)** - Expert configuration details
- **[Built-in Experts Guide](BUILTIN_EXPERTS_GUIDE.md)** - Built-in technical domains
- **[Expert Priority Guidelines](expert-priority-guide.md)** - How to configure expert priorities effectively
- **[Knowledge Base Organization Guide](knowledge-base-guide.md)** - Knowledge base structure for RAG optimization

### Customization
- **[User Role Templates Guide](USER_ROLE_TEMPLATES_GUIDE.md)** - Role-specific agent customization (senior-dev, junior-dev, tech-lead, PM, QA)
- **[Customization Guide](CUSTOMIZATION_GUIDE.md)** - Project-specific agent customizations
- **[Plugins and Extensions](PLUGINS_AND_EXTENSIONS.md)** - Custom skills, commands, rules, and MCPs

### Cursor AI Integration
- **[Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Skills + Claude Desktop Commands setup
- **[Multi-Tool Integration Guide](tool-integrations.md)** - Using TappsCodingAgents with Cursor, Claude Code CLI, VS Code + Continue, Codespaces, etc.
- **[Rules and Commands Toggles](RULES_AND_COMMANDS_TOGGLES.md)** - Cursor toggles (Import Agent Skills, Include CLAUDE.md, Import Claude Commands, Import Claude Plugins) and TappsCodingAgents
- **[Claude Desktop Commands Guide](CLAUDE_DESKTOP_COMMANDS.md)** - Using commands in Claude Desktop
- **[Simple Mode Guide](SIMPLE_MODE_GUIDE.md)** - 🎯 Simple Mode for new users (includes workflow enforcement and suggestions)
- **[Workflow Enforcement Guide](WORKFLOW_ENFORCEMENT_GUIDE.md)** - Guide for AI assistants on when to suggest workflows
- **[Workflow Quick Reference](WORKFLOW_QUICK_REFERENCE.md)** - Quick reference for all Simple Mode workflows
- **[Custom Skills Guide](CUSTOM_SKILLS_GUIDE.md)** - Creating, validating, and managing custom Skills
- **[Cursor Rules Setup Guide](CURSOR_RULES_SETUP.md)** - Cursor Rules setup (auto-generated from YAML workflows - Epic 8)
- **[Multi-Agent Orchestration Guide](MULTI_AGENT_ORCHESTRATION_GUIDE.md)**
- **[Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md)** - How Full SDLC workflow uses parallel execution
- **[Parallel Execution Optimization 2025](PARALLEL_EXECUTION_OPTIMIZATION_2025.md)** - Optimization recommendations and 2025 best practices
- **[YAML Workflow Architecture Design](YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)** - YAML-first architecture with generated artifacts (Epics 6-10)

### Operations
- **[Deployment Guide](operations/DEPLOYMENT.md)**
- **[Release Guide](operations/RELEASE_GUIDE.md)** - Version and release process
- **[Release Quick Reference](operations/RELEASE_QUICK_REFERENCE.md)** | **[Release Version Tag Warning](operations/RELEASE_VERSION_TAG_WARNING.md)**
- **[Package Distribution Guide](operations/PACKAGE_DISTRIBUTION_GUIDE.md)** - PyPI and distribution
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Includes Playwright MCP troubleshooting
- **[Path Normalization Guide](PATH_NORMALIZATION_GUIDE.md)** - Cross-platform path handling, Windows absolute path conversion
- **[Checkpoint & Resume Guide](CHECKPOINT_RESUME_GUIDE.md)** - State persistence and workflow resumption
- **[Simple Mode Timeout Analysis](SIMPLE_MODE_TIMEOUT_ANALYSIS_AND_ENHANCEMENTS.md)** - 2025 performance enhancements and timeout fixes
- **[Test Stack Documentation](test-stack.md)** - Comprehensive testing strategy, infrastructure, and quality gates
- **[Test Suite Documentation](../tests/README.md)** - Complete test suite overview
- **[E2E Test Suite](../tests/e2e/README.md)** - End-to-end test documentation
- **[Playwright MCP Integration](PLAYWRIGHT_MCP_INTEGRATION.md)** - Playwright MCP detection and integration guide

### Quality Improvements (Completed)
- **[Reviewer Agent Feedback Improvements](REVIEWER_FEEDBACK_IMPROVEMENTS_SUMMARY.md)** - ✅ All 6 phases complete (2026-01-16): Test coverage detection fix, maintainability issues, structured feedback, performance issues, type checking scores, context-aware quality gates
- **[Reviewer Agent Feedback Implementation Plan](REVIEWER_FEEDBACK_IMPLEMENTATION_PLAN.md)** - Detailed implementation plan and progress tracking
- **[Quality Improvements - Epic 19](QUALITY_IMPROVEMENTS_EPIC_19.md)** - Maintainability improvements summary
- **[Complexity Reduction - Epic 20](COMPLEXITY_REDUCTION_EPIC_20.md)** - Complexity reduction achievements and refactoring details
- **[Workflow Enforcement & Suggestions](WORKFLOW_ENFORCEMENT_GUIDE.md)** - ✅ Complete (2026-01-16): Proactive workflow suggestions, mandatory test generation (80%+ coverage), test coverage gates (70% minimum), enhanced output visibility
- **[Workflow Quick Reference](WORKFLOW_QUICK_REFERENCE.md)** - Quick reference guide for all Simple Mode workflows
- **[Hybrid Flow Evaluation Recommendations](HYBRID_FLOW_EVALUATION_RECOMMENDATIONS.md)** - High-impact recommendations from HomeIQ evaluation with actionable items and quick wins

### SDLC & Quality Engine (Planned)
- **[SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md)** - Comprehensive analysis of SDLC improvements and Dynamic Expert Engine
- **[Epic 1: SDLC Quality Engine](prd/epic-1-sdlc-quality-engine.md)** - Self-correcting quality engine with pluggable validation, composite gating, and bounded loopback
- **[Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md)** - Always-on orchestrator for automatic expert creation and knowledge ingestion
- **[Epic Summary: SDLC Improvements](prd/EPIC_SUMMARY_SDLC_IMPROVEMENTS.md)** - High-level overview of all planned improvements

### Features & Capabilities
- **[Beads Integration](BEADS_INTEGRATION.md)** - Optional task tracking (bd); epic sync, *build/*fix hooks; `tapps-agents beads`; doctor reports status; init hints `bd init`
- **[Setup, Init, and Doctor Recommendations](SETUP_INIT_DOCTOR_RECOMMENDATIONS.md)** - Issues and improvement recommendations for tapps-agents init, doctor, and Beads setup
- **[Context7 Integration](context7/CONTEXT7_CACHE_OPTIMIZATION.md)** - KB-first caching, analytics, cross-reference resolution
- **[Context7 Integration Patterns](context7/CONTEXT7_PATTERNS.md)** - Best practices and patterns for Context7 usage
- **[MCP Gateway](PLAYWRIGHT_MCP_INTEGRATION.md)** - Unified Model Context Protocol interface (Context7, Playwright, Filesystem, Git, Analysis)
- **[MCP Systems Comparative Score](MCP_SYSTEMS_COMPARATIVE_SCORE.md)** - TappsCodingAgents-style scoring of LocalMCP, codefortify, agentforge-mcp
- **[MCP Systems Improvement Recommendations](MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS.md)** - Actions from competing systems to make TappsCodingAgents far ahead (MCP server, 7-category scoring, npm audit, *enhance/*breakdown, etc.)
- **[MCP Standards Compliance](MCP_STANDARDS.md)** - JSON-RPC 2.0 and JSON Schema 2020-12 compliance
- **Health & Usage** - CLI: `tapps-agents health overview` (1000-foot view), `health usage dashboard|agents|workflows|system|trends`; performance metrics, trends, agent/workflow statistics. Implementation: `tapps_agents/health/`, `tapps_agents/core/analytics_dashboard.py`
- **[Health Monitoring](../tapps_agents/health/)** - System health checks, resource usage tracking
- **[State Management](CHECKPOINT_RESUME_GUIDE.md)** - Workflow state persistence, resume, cleanup
- **[Governance & Safety](../tapps_agents/experts/governance.py)** - Secrets/PII filtering, knowledge ingestion safety

### Standards & Guidelines
- **[AI Comment Guidelines](AI_COMMENT_GUIDELINES.md)** - AI comment tag conventions and usage
- **[Documentation Metadata Standards](DOCUMENTATION_METADATA_STANDARDS.md)** - Metadata standards for documentation files
- **[Test Stack Documentation](test-stack.md)** - Comprehensive testing strategy and infrastructure
- **[Architecture Shards](architecture/)** - Lean architecture documentation (tech-stack, source-tree, coding-standards, performance-guide, testing-strategy)
- **[Architecture Decisions](architecture/decisions/)** - ADR system and decision records
- **[MCP Standards Compliance](MCP_STANDARDS.md)** - MCP standards compliance (JSON-RPC 2.0, JSON Schema 2020-12)
- **[Context7 Integration Patterns](CONTEXT7_PATTERNS.md)** - Best practices for Context7 integration

### Requirements & Dependencies
- **[Dependency Policy](DEPENDENCY_POLICY.md)** - pyproject.toml is source of truth; optional extras
- **[Dependency Conflict (pipdeptree)](DEPENDENCY_CONFLICT_PIPDEPTREE.md)** - pipdeptree/packaging conflict and resolution
- **[Requirements Index](../requirements/README.md)** - Requirements documentation index
- **[Project Requirements](../requirements/PROJECT_REQUIREMENTS.md)** - Complete project requirements document
- **[Agent API Specification](../requirements/agent_api.md)** - Agent API specification
- **[Tech Stack Requirements](../requirements/TECH_STACK.md)** - Technology stack requirements

### Archive
- **[Documentation Archive](archive/README.md)** - Historical docs (completed improvements, session feedback, superseded planning, epic-specific). Current behavior is in the docs above.

**For contributors and AI:** When adding documentation, put **user-facing content** in docs linked from this index. Put **session feedback**, **implementation-complete summaries**, and **superseded planning** in [archive/](archive/README.md) (`archive/feedback/`, `archive/completed-improvements/`, `archive/planning/`). Do not create new `*_IMPLEMENTED.md` or `*_COMPLETE.md` in `docs/` root—update the canonical doc (e.g. CONFIGURATION.md, ARCHITECTURE.md) or add to archive.

## Common Tasks Quick Reference

**I want to...**

- **Set up TappsCodingAgents in my project** → [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- **Build a new feature** → [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) → Use `@simple-mode *build "description"`
- **Fix a bug** → [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) → Use `@simple-mode *fix <file> "description"`
- **Review code quality** → [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) → Use `@simple-mode *review <file>`
- **Generate tests** → [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) → Use `@simple-mode *test <file>`
- **Configure agents** → [Configuration Guide](CONFIGURATION.md)
- **Configure prompt enhancement (CLI auto_enhancement, workflow EnhancerHandler)** → [CONFIGURATION.md: auto_enhancement](CONFIGURATION.md#automatic-prompt-enhancement-auto_enhancement)
- **Add custom experts** → [Expert Setup Wizard](EXPERT_SETUP_WIZARD.md)
- **Understand the architecture** → [Architecture Overview](ARCHITECTURE.md)
- **Troubleshoot issues** → [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Deploy to production** → [Deployment Guide](operations/DEPLOYMENT.md)
- **Check coding standards** → [Coding Standards](architecture/coding-standards.md)
- **View API reference** → [API Reference](API.md)

## Topic-Based Navigation

### By Role

**Developer:**
- [Quick Start Guide](guides/QUICK_START.md)
- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Configuration Guide](CONFIGURATION.md)
- [API Reference](API.md)

**Framework Developer:**
- [Project Context](PROJECT_CONTEXT.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Architecture Decisions](architecture/decisions/)
- [Coding Standards](architecture/coding-standards.md)

**DevOps/QA:**
- [Test Stack Documentation](test-stack.md)
- [Deployment Guide](operations/DEPLOYMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### By Topic

**Testing:**
- [Test Stack Documentation](test-stack.md)
- [Test Suite Documentation](../tests/README.md)
- [E2E Test Suite](../tests/e2e/README.md)

**Architecture:**
- [Architecture Overview](ARCHITECTURE.md)
- [Architecture Shards](architecture/)
- [Architecture Decisions](architecture/decisions/)

**Integration:**
- [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [MCP Standards Compliance](MCP_STANDARDS.md)
- [Context7 Integration Patterns](CONTEXT7_PATTERNS.md)

**Standards:**
- [AI Comment Guidelines](AI_COMMENT_GUIDELINES.md)
- [Documentation Metadata Standards](DOCUMENTATION_METADATA_STANDARDS.md)
- [Coding Standards](architecture/coding-standards.md)

**Workflows:**
- [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md)
- [Workflow Quick Reference](WORKFLOW_QUICK_REFERENCE.md)
- [Epic Workflow Guide](EPIC_WORKFLOW_GUIDE.md)
- [YAML Workflow Architecture Design](YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)

**Performance:**
- [Quick Start: 2025 Optimizations](QUICK_START_OPTIMIZATIONS.md)
- [Parallel Execution Optimization 2025](PARALLEL_EXECUTION_OPTIMIZATION_2025.md)
- [Simple Mode Timeout Analysis](SIMPLE_MODE_TIMEOUT_ANALYSIS_AND_ENHANCEMENTS.md)
- [Performance Guide](architecture/performance-guide.md)

## Search by Keyword

Looking for something specific? Try these keywords:

- **"beads" / "bd" / "task tracking"** → [Beads Integration](BEADS_INTEGRATION.md)
- **"setup"** → [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md), [Configuration Guide](CONFIGURATION.md)
- **"workflow"** → [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md), [Workflow Quick Reference](WORKFLOW_QUICK_REFERENCE.md)
- **"test"** → [Test Stack Documentation](test-stack.md), [Test Suite Documentation](../tests/README.md)
- **"expert"** → [Expert Setup Wizard](EXPERT_SETUP_WIZARD.md), [Expert Configuration Guide](EXPERT_CONFIG_GUIDE.md)
- **"architecture"** → [Architecture Overview](ARCHITECTURE.md), [Architecture Shards](architecture/)
- **"api"** → [API Reference](API.md), [Agent API Specification](../requirements/agent_api.md)
- **"mcp"** → [MCP Standards Compliance](MCP_STANDARDS.md), [Playwright MCP Integration](PLAYWRIGHT_MCP_INTEGRATION.md), [MCP Systems Comparative Score](MCP_SYSTEMS_COMPARATIVE_SCORE.md), [MCP Systems Improvement Recommendations](MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS.md)
- **"context7"** → [Context7 Integration Patterns](context7/CONTEXT7_PATTERNS.md), [Context7 Cache Optimization](context7/CONTEXT7_CACHE_OPTIMIZATION.md)
- **"cursor"** → [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md), [Cursor Rules Setup Guide](CURSOR_RULES_SETUP.md)
- **"deployment"** → [Deployment Guide](operations/DEPLOYMENT.md)
- **"troubleshooting"** → [Troubleshooting Guide](TROUBLESHOOTING.md)
- **"standards"** → [AI Comment Guidelines](AI_COMMENT_GUIDELINES.md), [Documentation Metadata Standards](DOCUMENTATION_METADATA_STANDARDS.md), [Coding Standards](architecture/coding-standards.md)

---

**Documentation Version**: 3.5.39  
**Last Reviewed**: January 2026
