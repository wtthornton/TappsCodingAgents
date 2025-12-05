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

## Current Status (Phase 5 - Week 15 Complete)

✅ **Implemented:**
- Reviewer Agent (99% test coverage) with Code Scoring
- Planner Agent (91% test coverage) with Story Generation
- Implementer Agent (68% test coverage) with Code Generation & Refactoring
- Tester Agent (84% test coverage) with Test Generation & Execution
- Debugger Agent (92% test coverage) with Error Analysis & Code Tracing
- Documenter Agent (88% test coverage) with API Docs & README Generation
- Orchestrator Agent (66% test coverage) with Workflow Coordination & Gate Decisions
- Analyst Agent (Requirements gathering, stakeholder analysis, competitive research)
- Architect Agent (System design, architecture diagrams, technology selection)
- Designer Agent (API contracts, data models, UI/UX specifications)
- **Improver Agent** (Code refactoring, performance optimization, quality improvements)
- **Ops Agent** (Security scanning, compliance checks, deployment, infrastructure)
- Complete Code Scoring System (5/5 metrics: complexity, security, maintainability, test_coverage, performance)
- Configuration System (YAML-based, Pydantic validated)
- BaseAgent with BMAD-METHOD patterns (star commands, activation instructions, path validation)
- Model Abstraction Layer (MAL) for Ollama + **Cloud Fallback (Anthropic/OpenAI)**
- Tiered Context System (90%+ token savings, 3 tiers with caching)
- MCP Gateway (Unified tool access with filesystem, Git, and analysis servers)
- YAML Workflow Definitions (Workflow parser, executor, artifact tracking, conditional steps)
- **Industry Experts Framework** (Weighted decision-making, domain configuration, expert registry)
- **Configuration-Only Experts** (YAML-based expert definition, no code classes required)
- **Simple File-Based RAG** (Knowledge base retrieval for experts)
- **Workflow Expert Integration** (Agents consult experts for domain knowledge)
- **Cloud MAL Fallback** (Anthropic & OpenAI support with automatic fallback)
- **307+ tests passing, 82% coverage for MAL, 98% coverage for expert config**

🎉 **All 12 Workflow Agents Complete!**

🚧 **Future Work (Optional Enhancements):**
- Greenfield/Brownfield workflow detection
- Workflow state persistence (advanced)
- Example expert implementations (templates)
- Vector DB RAG (if simple RAG insufficient)
- Fine-tuning support (LoRA adapters)

## Key Features

### Two-Layer Agent Model

| Layer | Type | Purpose | Count |
|-------|------|---------|-------|
| **Knowledge** | Industry Experts | Business domain authority | N (per project) |
| **Execution** | Workflow Agents | SDLC task execution | 12 (fixed) |

### Workflow Agents (12)

- **Planning**: analyst ✅, planner ✅ (Story Generation)
- **Design**: architect ✅, designer ✅
- **Development**: implementer ✅ (Code Generation & Refactoring), debugger ✅ (Error Analysis & Code Tracing), documenter ✅ (API Docs & README Generation)
- **Testing**: tester ✅ (Test Generation & Execution)
- **Quality**: reviewer ✅ (with Code Scoring), improver ✅ (Refactoring & Optimization)
- **Operations**: ops ✅ (Security, Compliance, Deployment)
- **Orchestration**: orchestrator ✅ (Workflow Coordination)

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
