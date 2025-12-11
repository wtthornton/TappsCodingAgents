# TappsCodingAgents

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](README.md)
[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](CHANGELOG.md)

**A specification framework for defining, configuring, and orchestrating coding agents.**

## Overview

TappsCodingAgents provides a standardized framework for building AI coding agents with:

> **Note**: This project both **develops** the TappsCodingAgents framework AND **uses** it for its own development (self-hosting). See [Project Context](docs/PROJECT_CONTEXT.md) for details.

- **Workflow Agents** (13): Standard SDLC task execution + Prompt Enhancement
- **Industry Experts** (N): Business domain knowledge with weighted decision-making
- **Built-in Experts** (15): Framework-controlled technical domain experts (Security, Performance, Testing, Data Privacy, Accessibility, UX, Code Quality, Software Architecture, DevOps, Documentation, AI Frameworks, Observability, API Design, Cloud Infrastructure, Database)
- **Expert Integration** (6 agents): Architect, Implementer, Reviewer, Tester, Designer, and Ops agents consult relevant experts for enhanced decision-making
- **Project Profiling System** (v1.0.0+): Automatic detection of project characteristics (deployment type, tenancy, user scale, compliance, security) for context-aware expert guidance
- **Improved Confidence System** (v2.1.0): Weighted confidence calculation with agent-specific thresholds and metrics tracking, including project context relevance
- **Model Abstraction Layer (MAL)**: Hybrid local/cloud model routing
- **RAG Integration**: Retrieval-augmented generation for domain knowledge
- **Fine-Tuning Support**: LoRA adapters for domain specialization
- **Cursor AI Integration** ✅: Complete integration with Cursor AI (all 7 phases)
  - **13 Cursor Skills** (All agents available as Cursor Skills)
  - **Background Agents** (Offload heavy tasks to cloud/remote)
  - **Multi-Agent Orchestration** (Parallel execution with conflict resolution)
  - **Context7 Integration** (KB-first caching, 95%+ hit rate)
  - **NUC Optimization** (Resource monitoring, fallback strategy)
- **Claude Code Compatible**: Native Agent Skills format
- **Prompt Enhancement Utility**: Transform simple prompts into comprehensive, context-aware prompts
- **Project Profiling**: Automatic detection of project characteristics for context-aware expert advice

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
- **Total Built-in Experts: 15** (up from 11)
- **Total Knowledge Files: 84** (up from 52)
- See [Built-in Experts Guide](docs/BUILTIN_EXPERTS_GUIDE.md) and [Phase 5 Implementation Plan](implementation/PHASE5_EXPERT_IMPLEMENTATION_PLAN.md)

🎉 **ALL 7 PHASES COMPLETE - Cursor AI Integration Plan 2025** 🎉

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
- **Cache Pre-population** ✅ (Dependency-based warming, 95%+ hit rate target)
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
- **500+ tests passing** across all components

✅ **Enhancer Agent - Prompt Enhancement Utility (v1.6.0)**
- **7-Stage Enhancement Pipeline** - Transforms simple prompts into comprehensive, context-aware prompts
- **Industry Expert Integration** - Automatic domain detection and weighted expert consultation
- **Multiple Usage Modes** - Full enhancement, quick enhancement, stage-by-stage execution
- **Session Management** - Resume interrupted enhancements
- **Multiple Output Formats** - Markdown, JSON, YAML
- See [Enhancer Agent Guide](docs/ENHANCER_AGENT.md) for details

🎉 **All Core Framework Features Complete!**

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

### Cursor AI Integration
- **[Cursor Skills Installation Guide](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)** - Install and configure Cursor Skills
- **[Background Agents Guide](docs/BACKGROUND_AGENTS_GUIDE.md)** - Configure Background Agents for heavy tasks
- **[Multi-Agent Orchestration Guide](docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md)** - Parallel agent execution
- **[Unified Cache Architecture](implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md)** - Single interface for all caching systems
- **[Unified Cache Integration Guide](implementation/UNIFIED_CACHE_INTEGRATION_GUIDE.md)** - Using unified cache in agents
- **[Context7 Cache Optimization](docs/CONTEXT7_CACHE_OPTIMIZATION.md)** - Optimize cache hit rates
- **[Context7 Security & Privacy](docs/CONTEXT7_SECURITY_PRIVACY.md)** - Security best practices
- **[NUC Setup Guide](docs/NUC_SETUP_GUIDE.md)** - Optimize for low-power hardware

### Operations
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
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
**Version**: 1.6.1  
**Last Updated**: December 2025  
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
- **Context7 Integration** with KB cache (95%+ hit rate)
- **13 Cursor Skills** available in `.claude/skills/`
- **Background Agents** configured in `.cursor/background-agents.yaml`
- **NUC Optimization** enabled for resource-constrained environments
- Configuration in `.tapps-agents/` directory

See [Self-Hosting Setup](implementation/SELF_HOSTING_SETUP_COMPLETE.md) for details.

## License

See LICENSE file for details.
