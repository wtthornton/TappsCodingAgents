# TappsCodingAgents

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](README.md)
[![Version](https://img.shields.io/badge/version-1.6.0-blue.svg)](CHANGELOG.md)

**A specification framework for defining, configuring, and orchestrating coding agents.**

## Overview

TappsCodingAgents provides a standardized framework for building AI coding agents with:

> **Note**: This project both **develops** the TappsCodingAgents framework AND **uses** it for its own development (self-hosting). See [Project Context](.cursor/rules/project-context.mdc) for details.

- **Workflow Agents** (13): Standard SDLC task execution + Prompt Enhancement
- **Industry Experts** (N): Business domain knowledge with weighted decision-making
- **Model Abstraction Layer (MAL)**: Hybrid local/cloud model routing
- **RAG Integration**: Retrieval-augmented generation for domain knowledge
- **Fine-Tuning Support**: LoRA adapters for domain specialization
- **Claude Code Compatible**: Native Agent Skills format
- **Prompt Enhancement Utility**: Transform simple prompts into comprehensive, context-aware prompts

### Enhanced Features (v1.1)

- **Code Scoring System**: Objective quality metrics (complexity, security, maintainability)
- **Tiered Context Injection**: 90%+ token savings with intelligent caching
- **MCP Gateway**: Unified Model Context Protocol interface for tool access
- **YAML Workflow Definitions**: Declarative, version-controlled orchestration
- **Greenfield/Brownfield Workflows**: Context-appropriate workflows for project types

## Current Status (December 2025)

✅ **Phase 6 Complete - Modern Quality Analysis**
- **Ruff Integration** ✅ (10-100x faster Python linting, 2025 standard)
- **mypy Type Checking** ✅ (Static type analysis, 2025 standard)
- **Comprehensive Reporting** ✅ (JSON, Markdown, HTML with historical tracking)
- **TypeScript & JavaScript Support** ✅ (ESLint, TypeScript compiler integration)
- **Multi-Service Analysis** ✅ (Batch analysis with service-level aggregation)
- **Dependency Security Auditing** ✅ (pip-audit, pipdeptree integration)
- **Code Duplication Detection** ✅ (jscpd for Python and TypeScript)
- See [Phase 6 Summary](docs/PHASE6_SUMMARY.md) for details

✅ **Phase 5 Complete - Context7 Integration**
- **Context7 Integration** - KB-first caching, auto-refresh, performance analytics (177/207 tests passing, production-ready)
- Cross-references system, KB cleanup automation, agent integration helper
- Integrated into Architect, Implementer, and Tester agents
- Comprehensive CLI commands for KB management

✅ **Core Framework Complete:**
- **All 13 Workflow Agents** (analyst, planner, architect, designer, implementer, tester, debugger, documenter, reviewer, improver, ops, orchestrator, enhancer)
- **Complete Code Scoring System** (5/5 metrics: complexity, security, maintainability, test_coverage, performance)
- **Model Abstraction Layer (MAL)** - Ollama + Cloud Fallback (Anthropic & OpenAI)
- **Tiered Context System** (90%+ token savings, 3 tiers with caching)
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
├── agents/                        # Agent Skills (coming)
├── knowledge/                     # RAG templates (coming)
├── adapters/                      # Fine-tuning templates (coming)
└── config/                        # Configuration templates (coming)
```

## Documentation

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - 🚀 Get started in 10 minutes
- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[API Reference](docs/API.md)** - Python API and CLI documentation
- **[Enhancer Agent Guide](docs/ENHANCER_AGENT.md)** - Prompt enhancement utility documentation

### Core Guides
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System architecture and design
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration reference
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup and workflows

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

**Phase**: Implementation Phase - Phase 6 Complete, Enhancer Agent Added  
**Version**: 1.6.0  
**Last Updated**: December 2025

## Self-Hosting

This project uses its own framework for development:
- **5 Industry Experts** configured (AI frameworks, code quality, architecture, DevOps, documentation)
- **Enhancer Agent** actively used (23+ enhancement sessions)
- **Context7 Integration** with KB cache
- Configuration in `.tapps-agents/` directory

See [Self-Hosting Setup](implementation/SELF_HOSTING_SETUP_COMPLETE.md) for details.

## License

See LICENSE file for details.
