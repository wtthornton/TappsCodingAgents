# TappsCodingAgents

**A specification framework for defining, configuring, and orchestrating coding agents.**

## Overview

TappsCodingAgents provides a standardized framework for building AI coding agents with:

- **Workflow Agents** (12): Standard SDLC task execution
- **Industry Experts** (N): Business domain knowledge with weighted decision-making
- **Model Abstraction Layer (MAL)**: Hybrid local/cloud model routing
- **RAG Integration**: Retrieval-augmented generation for domain knowledge
- **Fine-Tuning Support**: LoRA adapters for domain specialization
- **Claude Code Compatible**: Native Agent Skills format

### Enhanced Features (v1.1)

- **Code Scoring System**: Objective quality metrics (complexity, security, maintainability)
- **Tiered Context Injection**: 90%+ token savings with intelligent caching
- **MCP Gateway**: Unified Model Context Protocol interface for tool access
- **YAML Workflow Definitions**: Declarative, version-controlled orchestration
- **Greenfield/Brownfield Workflows**: Context-appropriate workflows for project types

## Current Status (Phase 1 - Week 3 Day 2 Complete)

✅ **Implemented:**
- Reviewer Agent (99% test coverage) with Code Scoring
- Planner Agent (91% test coverage) with Story Generation
- Complete Code Scoring System (5/5 metrics: complexity, security, maintainability, test_coverage, performance)
- Configuration System (YAML-based, Pydantic validated)
- BaseAgent with BMAD-METHOD patterns (star commands, activation instructions)
- Model Abstraction Layer (MAL) for Ollama
- 96 tests passing, 69% overall coverage

🚧 **In Progress:**
- Additional workflow agents (10 remaining)
- MCP Gateway
- Tiered Context System
- Workflow Engine

## Key Features

### Two-Layer Agent Model

| Layer | Type | Purpose | Count |
|-------|------|---------|-------|
| **Knowledge** | Industry Experts | Business domain authority | N (per project) |
| **Execution** | Workflow Agents | SDLC task execution | 12 (fixed) |

### Workflow Agents (12)

- **Planning**: analyst, planner ✅ (Story Generation)
- **Design**: architect, designer
- **Development**: implementer, debugger, documenter
- **Quality**: reviewer ✅ (with Code Scoring), improver
- **Testing**: tester
- **Operations**: ops
- **Orchestration**: orchestrator

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

- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - **For Developers:** How to use this framework
- **[Project Manager Guide](docs/PROJECT_MANAGER_GUIDE.md)** - **For PMs:** Leveraging AI agents for project success
- **[Project Requirements](requirements/PROJECT_REQUIREMENTS.md)** - Complete specification document
- **[Technology Stack](requirements/TECH_STACK.md)** - Recommended technologies and configurations

## Status

**Phase**: Design  
**Version**: 1.1.0-draft

## License

See LICENSE file for details.
