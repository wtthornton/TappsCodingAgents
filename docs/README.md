# TappsCodingAgents Documentation

Welcome to the documentation for TappsCodingAgents.

## 📚 Documentation Structure

### Getting Started
- **[Quick Start Guide](guides/QUICK_START.md)** - Get up and running quickly
- **[Simple Mode Guide](SIMPLE_MODE_GUIDE.md)** - 🎯 Simple Mode for new users (task-first, natural language)
- **[Epic Workflow Guide](EPIC_WORKFLOW_GUIDE.md)** - Execute Epic documents with story dependency resolution
- **[Current Defaults](CURRENT_DEFAULTS.md)** - What happens by default (no surprises)
- **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
- **[API Reference](API.md)** - Python API + CLI overview

### Core Concepts
- **[Project Context](PROJECT_CONTEXT.md)** - Framework development vs. self-hosting
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

### Customization
- **[User Role Templates Guide](USER_ROLE_TEMPLATES_GUIDE.md)** - Role-specific agent customization (senior-dev, junior-dev, tech-lead, PM, QA)
- **[Customization Guide](CUSTOMIZATION_GUIDE.md)** - Project-specific agent customizations

### Cursor AI Integration
- **[Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Skills + Claude Desktop Commands setup
- **[Claude Desktop Commands Guide](CLAUDE_DESKTOP_COMMANDS.md)** - Using commands in Claude Desktop
- **[Simple Mode Guide](SIMPLE_MODE_GUIDE.md)** - 🎯 Simple Mode for new users
- **[Custom Skills Guide](CUSTOM_SKILLS_GUIDE.md)** - Creating, validating, and managing custom Skills
- **[Cursor Rules Setup Guide](CURSOR_RULES_SETUP.md)** - Cursor Rules setup (auto-generated from YAML workflows - Epic 8)
- **[Multi-Agent Orchestration Guide](MULTI_AGENT_ORCHESTRATION_GUIDE.md)**
- **[Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md)** - How Full SDLC workflow uses parallel execution
- **[Parallel Execution Optimization 2025](PARALLEL_EXECUTION_OPTIMIZATION_2025.md)** - Optimization recommendations and 2025 best practices
- **[YAML Workflow Architecture Design](YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)** - YAML-first architecture with generated artifacts (Epics 6-10)

### Operations
- **[Deployment Guide](DEPLOYMENT.md)**
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Includes Playwright MCP troubleshooting
- **[Checkpoint & Resume Guide](CHECKPOINT_RESUME_GUIDE.md)** - State persistence and workflow resumption
- **[Simple Mode Timeout Analysis](SIMPLE_MODE_TIMEOUT_ANALYSIS_AND_ENHANCEMENTS.md)** - 2025 performance enhancements and timeout fixes
- **[Test Suite Documentation](../tests/README.md)** - Complete test suite overview
- **[E2E Test Suite](../tests/e2e/README.md)** - End-to-end test documentation
- **[Playwright MCP Integration](PLAYWRIGHT_MCP_INTEGRATION.md)** - Playwright MCP detection and integration guide

### Quality Improvements (Completed)
- **[Quality Improvements - Epic 19](QUALITY_IMPROVEMENTS_EPIC_19.md)** - Maintainability improvements summary
- **[Complexity Reduction - Epic 20](COMPLEXITY_REDUCTION_EPIC_20.md)** - Complexity reduction achievements and refactoring details

### SDLC & Quality Engine (Planned)
- **[SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md)** - Comprehensive analysis of SDLC improvements and Dynamic Expert Engine
- **[Epic 1: SDLC Quality Engine](prd/epic-1-sdlc-quality-engine.md)** - Self-correcting quality engine with pluggable validation, composite gating, and bounded loopback
- **[Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md)** - Always-on orchestrator for automatic expert creation and knowledge ingestion
- **[Epic Summary: SDLC Improvements](prd/EPIC_SUMMARY_SDLC_IMPROVEMENTS.md)** - High-level overview of all planned improvements

### Features & Capabilities
- **[Context7 Integration](CONTEXT7_CACHE_OPTIMIZATION.md)** - KB-first caching, analytics, cross-reference resolution
- **[MCP Gateway](PLAYWRIGHT_MCP_INTEGRATION.md)** - Unified Model Context Protocol interface (Context7, Playwright, Filesystem, Git, Analysis)
- **[Analytics Dashboard](../tapps_agents/core/analytics_dashboard.py)** - Performance metrics, trends, agent/workflow statistics
- **[Health Monitoring](../tapps_agents/health/)** - System health checks, resource usage tracking
- **[State Management](CHECKPOINT_RESUME_GUIDE.md)** - Workflow state persistence, resume, cleanup
- **[Governance & Safety](../tapps_agents/experts/governance.py)** - Secrets/PII filtering, approval workflows

---

**Documentation Version**: 3.2.9  
**Last Reviewed**: January 2026
