# TappsCodingAgents - Project Requirements Document

**Version:** 2.0.0  
**Date:** January 2026  
**Status:** Implementation Phase - Core Framework Complete, Phase 5 Complete, Phase 6 Complete

---

## Implementation Status

### ✅ Completed Features

#### Core Framework (100%)
- ✅ **All 12 Workflow Agents** (analyst, planner, architect, designer, implementer, tester, debugger, documenter, reviewer, improver, ops, orchestrator)
- ✅ **BaseAgent** with BMAD-METHOD patterns (star commands, activation instructions, path validation)
- ✅ **Configuration System** (YAML-based, Pydantic validated)
- ✅ **Model Abstraction Layer (MAL)** with Ollama + Cloud Fallback (Anthropic & OpenAI)
- ✅ **Code Scoring System** (5/5 metrics: complexity, security, maintainability, test_coverage, performance)
- ✅ **Tiered Context System** (90%+ token savings, 3 tiers with caching)
- ✅ **MCP Gateway** (Unified tool access with filesystem, Git, and analysis servers)
- ✅ **YAML Workflow Definitions** (Parser, executor, artifact tracking, conditional steps, gates)

#### Industry Experts Framework (100%)
- ✅ **BaseExpert** class (concrete, no abstract requirement)
- ✅ **Configuration-Only Experts** (YAML-based expert definition, no code classes required)
- ✅ **Weight Distribution Algorithm** (51% primary authority model)
- ✅ **Domain Configuration System** (domains.md parser, expert_weights.yaml generation)
- ✅ **Expert Registry** (Expert management, weighted consultation, decision aggregation)
- ✅ **Simple File-Based RAG** (Knowledge base retrieval with markdown-aware chunking)
- ✅ **Workflow Expert Integration** (Agents consult experts for domain knowledge)
- ✅ **Example Expert Implementations** (4 example configurations, knowledge bases, templates)

#### Workflow System Enhancements (100%)
- ✅ **Scale-Adaptive Workflow Selection** (Project type auto-detection, workflow recommendation)
- ✅ **Project Type Detector** (Greenfield, Brownfield, Quick-Fix, Hybrid detection)
- ✅ **Workflow Recommender** (Intelligent workflow selection with confidence scoring)
- ✅ **Auto-Detection Integration** (Seamless integration with workflow executor)

#### Testing & Quality
- ✅ **323+ unit tests passing**
- ✅ **98% coverage** for expert configuration system
- ✅ **82% coverage** for MAL cloud fallback
- ✅ **95% coverage** for Simple RAG system
- ✅ **Comprehensive test suite** for all implemented components

### ⏸️ Deferred Features (Optional/Future)

- ⏸️ **Fine-Tuning Support (LoRA)** - Deferred to Phase 6 (optional enhancement)
- ⏸️ **Vector DB RAG** - Only if simple file-based RAG proves insufficient

### 🚧 Future Work (Enhancement Phases)

- ✅ **Context7 Integration - Complete** (Section 18) - KB-first caching, auto-refresh, performance analytics, cross-references, cleanup automation, agent integration (177/207 tests passing, production-ready)
- ✅ **Phase 6: Modern Quality Analysis** (Section 19) - ✅ **COMPLETE** (December 2025) - Ruff, mypy, TypeScript support, comprehensive reporting
- ✅ **Workflow State Persistence (Advanced)** - ✅ **COMPLETE** (January 2026) - Advanced state management with validation, migration, and recovery
- ✅ **Advanced Analytics Dashboard** - ✅ **COMPLETE** (January 2026) - Performance monitoring with metrics collection and CLI commands
- ✅ **Project Profiling System** - ✅ **COMPLETE** (January 2026) - Auto-detection of project characteristics for context-aware expert guidance
- ✅ **Modernize Project Configuration** - ✅ **COMPLETE** (January 2026) - Migrated to pyproject.toml with build system
- ✅ **Error Handling Improvements** - ✅ **COMPLETE** (January 2026) - Custom exception types and improved error handling
- ✅ **Configuration Management Improvements** - ✅ **COMPLETE** (January 2026) - All expert thresholds moved to configuration

### 📋 Next Priorities

Based on implementation status, the next priorities are:

#### ✅ Recently Completed

1. **Phase 3: Example Expert Implementations** ✅ **Complete**
   - ✅ Created 4 example expert configurations (home-automation, healthcare, financial-services, ecommerce)
   - ✅ Added templates for common domains (experts.yaml.template, domains.md.template)
   - ✅ Created example knowledge bases with real-world domain content
   - ✅ Documented best practices and usage examples
   - ✅ Comprehensive test suite (6/6 tests passing)

2. **Phase 4: Scale-Adaptive Workflow Selection** ✅ **Complete**
   - ✅ Implemented project type auto-detection (Greenfield, Brownfield, Quick-Fix, Hybrid)
   - ✅ Implemented workflow recommendation system with confidence scoring
   - ✅ Integrated with workflow executor for automatic workflow selection
   - ✅ Created comprehensive test suite (16/16 tests passing)
   - ✅ Documented usage and best practices (WORKFLOW_SELECTION_GUIDE.md)

#### ✅ Recently Completed (Continued)

3. **Phase 5: Context7 Integration** ✅ **Complete**
   - ✅ Core Integration (Phase 1): Cache structure, metadata management, KB-first lookup, MCP integration
   - ✅ Intelligence Layer (Phase 2): Fuzzy matching, staleness policies, refresh queue, analytics
   - ✅ Advanced Features (Phase 3): Cross-references system, KB cleanup automation, agent integration helper, CLI commands
   - ✅ Integrated into Architect, Implementer, and Tester agents
   - ✅ Comprehensive test suite: 177/207 tests passing (85.5%), core functionality production-ready
   - ✅ All components implemented and functional (see PHASE5_COMPLETION_REVIEW.md)

#### 🎯 Next Priorities

**Phase 6: Modern Quality Analysis Enhancements** (Enhancement Phase - Estimated 8-12 weeks) - **READY TO START**

**Objective:** Enhance code quality analysis with 2025 industry standards, modern tooling (Ruff, mypy, jscpd), TypeScript support, comprehensive reporting, and multi-service analysis. See Section 19 for complete details.

**Status:** ✅ **COMPLETE** (December 2025) - Phase 6 fully implemented. See PHASE6_STATUS.md for details.

**Key Components (2025 Standards):**
1. **Ruff Integration** (10-100x faster than pylint)
   - Version: `ruff>=0.8.0,<1.0` (2025 standard)
   - JSON output parsing
   - Auto-fix capabilities
   - Configuration via `ruff.toml` or `pyproject.toml`

2. **mypy Type Checking** (Static type analysis)
   - Version: `mypy>=1.13.0,<2.0` (2025 standard)
   - Strict mode support
   - Error codes for easy fixing
   - Configuration via `mypy.ini` or `pyproject.toml`

3. **Comprehensive Reporting Infrastructure**
   - Multi-format reports (JSON, Markdown, HTML)
   - Historical tracking and trend analysis
   - Interactive dashboards with Jinja2 + plotly
   - CI/CD integration ready

4. **Code Duplication Detection**
   - jscpd integration (Python + TypeScript)
   - Configurable thresholds (<3% duplication)
   - JSON output for programmatic parsing

5. **Multi-Service Analysis**
   - Auto-detect services in `services/` directory
   - Parallel analysis with asyncio
   - Service-level and project-level aggregation

6. **Dependency Analysis & Security Auditing**
   - pip-audit `>=2.6.0` for vulnerability scanning
   - pipdeptree `>=2.5.0` for dependency tree visualization
   - CVE tracking and severity levels

7. **TypeScript & JavaScript Support**
   - TypeScript `>=5.6.0`, ESLint `>=9.0.0` (2025 standards)
   - TypeScript compiler (tsc) integration
   - Complexity analysis for TS/JS
   - Jest, Vitest test framework support

8. **Agent Integration Enhancements**
   - Cross-agent quality data sharing
   - Automated quality-based gate decisions
   - Quality-aware planning
   - Coordinated quality improvements

**Implementation Phases:**
- 🚧 **Phase 6.1:** High Priority Core (4-5 weeks) - Ruff, mypy, Reporting Infrastructure
- 📋 **Phase 6.2:** Medium Priority Features (4-7 weeks) - Duplication, Multi-service, Dependencies, TypeScript, Agent Integration

#### 🔮 Future Enhancements

**Phase 6: Optional Advanced Features** (If Needed)
- Vector DB RAG (only if simple file-based RAG proves insufficient)
- Fine-tuning support (LoRA adapters) - for expert specialization
- Advanced workflow features (state persistence, analytics dashboard)

### 📊 Implementation Progress

| Category | Status | Completion |
|----------|--------|------------|
| **Workflow Agents** | ✅ Complete | 12/12 (100%) |
| **Code Scoring** | ✅ Complete | 5/5 metrics (100%) |
| **MAL (Local + Cloud)** | ✅ Complete | Ollama + Anthropic + OpenAI (100%) |
| **Tiered Context** | ✅ Complete | 3 tiers, caching (100%) |
| **MCP Gateway** | ✅ Complete | Filesystem, Git, Analysis (100%) |
| **YAML Workflows** | ✅ Complete | Parser, Executor, Tracking (100%) |
| **Industry Experts** | ✅ Complete | Config-based, RAG, Registry (100%) |
| **Simple RAG** | ✅ Complete | File-based, markdown-aware (100%) |
| **Example Experts** | ✅ Complete | 4 examples, templates, knowledge bases (100%) |
| **Scale-Adaptive Workflows** | ✅ Complete | Auto-detection, recommendation (100%) |
| **Testing** | ✅ Complete | 323+ tests, 82%+ coverage |
| **Context7 Integration** | ✅ Complete | Phase 5 (177/207 tests, production-ready) |
| **Modern Quality Analysis** | ✅ Ready to Start | Phase 6 (Enhancement - 2025 Standards) |
| **Fine-Tuning (LoRA)** | ⏸️ Deferred | Optional enhancement |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Vision](#2-project-vision)
3. [Framework Architecture](#3-framework-architecture)
4. [Agent Types](#4-agent-types)
5. [Workflow Agents](#5-workflow-agents)
6. [Industry Experts](#6-industry-experts)
7. [Weight Distribution Algorithm](#7-weight-distribution-algorithm)
8. [Model Abstraction Layer (MAL)](#8-model-abstraction-layer-mal)
9. [RAG Integration](#9-rag-integration)
10. [Fine-Tuning Support](#10-fine-tuning-support)
11. [Agent Skills Format](#11-agent-skills-format)
12. [Domain Configuration](#12-domain-configuration)
13. [Directory Structure](#13-directory-structure)
14. [Configuration Schemas](#14-configuration-schemas)
15. [Standard Workflows](#15-standard-workflows)
16. [Enhanced Features](#16-enhanced-features)
    - [Code Scoring System](#161-code-scoring-system)
    - [Tiered Context Injection](#162-tiered-context-injection)
    - [MCP Gateway Architecture](#163-mcp-gateway-architecture)
    - [YAML Workflow Definitions](#164-yaml-workflow-definitions)
    - [Greenfield vs Brownfield Workflows](#165-greenfield-vs-brownfield-workflows)
17. [Agent Command System & Activation](#17-agent-command-system--activation)
    - [Star-Prefixed Command System](#171-star-prefixed-command-system)
    - [Agent Activation Instructions](#172-agent-activation-instructions)
    - [Workflow Enhancement Patterns](#173-workflow-enhancement-patterns)
    - [Scale-Adaptive Workflow Selection](#174-scale-adaptive-workflow-selection)
18. [Context7 Integration (Enhancement Phase)](#18-context7-integration-enhancement-phase)
    - [Context7 Overview](#181-context7-overview)
    - [KB-First Caching System](#182-kb-first-caching-system)
    - [MCP Integration](#183-mcp-integration)
    - [Auto-Refresh System](#184-auto-refresh-system)
    - [Performance Analytics](#185-performance-analytics)
    - [Agent Integration](#186-agent-integration)
    - [Configuration Schema](#187-configuration-schema)
    - [Implementation Phases](#188-implementation-phases)
19. [Appendix](#19-appendix)

---

## 1. Executive Summary

### 1.1 What is TappsCodingAgents?

TappsCodingAgents is a **specification framework** for defining, configuring, and orchestrating coding agents. It provides:

- A standardized way to define agent capabilities and behaviors
- Support for business domain experts with weighted decision-making
- Hybrid model routing (local + cloud)
- Optional MCP (Model Context Protocol) integration via **MCP Gateway**
- RAG and fine-tuning capabilities for domain specialization
- **Code Scoring System** for objective quality metrics
- **Tiered Context Injection** for 90%+ token savings
- **YAML Workflow Definitions** for declarative orchestration
- **Greenfield vs Brownfield** workflow support

### 1.2 Key Characteristics

| Attribute | Value |
|-----------|-------|
| **Type** | Specification Framework |
| **Target Audience** | Internal Projects |
| **Scope** | Full Ecosystem (Agents + Tools + Integrations) |
| **Model Strategy** | Hybrid (Local-first, Cloud fallback) |
| **MCP Integration** | Optional |

### 1.3 Design Principles

1. **Single Responsibility**: Each agent does ONE thing exceptionally well
2. **Composable**: Agents work together via Orchestrator
3. **Phase-Aligned**: Agents map to SDLC phases
4. **Permission-Based**: Read-only vs write access based on role
5. **Business Domain Focus**: Experts are business authorities, not technical specialists

---

## 2. Project Vision

### 2.1 Goals

1. Create a **universal specification** for how coding agents should be defined and configured
2. Abstract AI model providers through the **Model Abstraction Layer (MAL)**
3. Support **RAG** for context retrieval and domain knowledge
4. Enable **multi-agent workflows** with weighted decision-making
5. Provide **quality and validation patterns** for agent outputs

### 2.2 Non-Goals

| Excluded | Reason |
|----------|--------|
| Project management features | Use external tools (Jira, Linear) |
| Git operations | Let IDE/CLI handle |
| Cloud deployment automation | Too infrastructure-specific |
| Real-time collaboration | Out of scope |
| Billing/cost tracking | Separate concern |

---

## 3. Framework Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROJECT CONFIGURATION                         │
│                                                                      │
│   Defines: domains.md + model profiles + agent selection             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│       INDUSTRY EXPERTS          │   │        WORKFLOW AGENTS          │
│       (Business Knowledge)      │   │        (SDLC Execution)         │
│                                 │   │                                 │
│  • N experts for N domains      │   │  • 12 fixed agents              │
│  • Weighted decision-making     │   │  • Standard SDLC coverage       │
│  • RAG + Fine-tuning           │   │  • Permission-based access      │
│  • Primary: 51% authority       │   │  • Consult experts as needed    │
└─────────────────────────────────┘   └─────────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │     ORCHESTRATOR      │
                        │                       │
                        │  • Coordinates agents │
                        │  • Manages workflows  │
                        │  • Enforces gates     │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  MODEL ABSTRACTION    │
                        │       LAYER (MAL)     │
                        │                       │
                        │  • Local-first        │
                        │  • Cloud fallback     │
                        │  • Task-based routing │
                        └───────────────────────┘
```

### 3.2 Two-Layer Agent Model

| Layer | Type | Purpose | Count |
|-------|------|---------|-------|
| **Knowledge Layer** | Industry Experts | Business domain knowledge | N (configurable) |
| **Execution Layer** | Workflow Agents | SDLC task execution | 12 (fixed) |

---

## 4. Agent Types

### 4.1 Agent Classification

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AGENT TYPES                                 │
├─────────────────────────────────┬───────────────────────────────────┤
│       INDUSTRY EXPERTS          │        WORKFLOW AGENTS            │
│       (Knowledge Layer)         │        (Execution Layer)          │
├─────────────────────────────────┼───────────────────────────────────┤
│ • Business domain authority     │ • Execute SDLC tasks              │
│ • Advisory role (read-only)     │ • Varied permissions (read/write) │
│ • 1:1 domain mapping            │ • Standard set                    │
│ • Weighted decision-making      │ • Minimal customization           │
│ • RAG + Fine-tuning support     │ • Consult experts                 │
│ • Per-project configuration     │ • Fixed capabilities              │
└─────────────────────────────────┴───────────────────────────────────┘
```

### 4.2 Comparison Matrix

| Aspect | Industry Expert | Workflow Agent |
|--------|-----------------|----------------|
| **Focus** | Business domain knowledge | SDLC task execution |
| **Role** | Advisory, consultative | Execution, production |
| **Permissions** | Read-only | Varies (read/write) |
| **Configuration** | Per-project domains | Standard set |
| **Customization** | RAG + Fine-tuning | Minimal |
| **Decision Authority** | Weighted by confidence | Executes decisions |
| **Count** | N (based on domains) | 12 (fixed) |

---

## 5. Workflow Agents

### 5.1 Agent Inventory (12 Agents)

#### Planning Phase (2 Agents)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **analyst** | Requirements gathering, technical research, effort/risk estimation | Read, Grep, Glob | analyst + estimator |
| **planner** | Create user stories + task breakdown | Read, Write, Grep, Glob | — |

#### Design Phase (2 Agents)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **architect** | System + security architecture design | Read, Write, Grep, Glob | — |
| **designer** | API contracts, data models, UI/UX specifications | Read, Write, Grep, Glob | designer + ui-designer |

#### Development Phase (3 Agents)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **implementer** | Write production code | Read, Write, Edit, Grep, Glob, Bash | — |
| **debugger** | Investigate and fix bugs | Read, Write, Edit, Grep, Glob, Bash | — |
| **documenter** | Write documentation | Read, Write, Grep, Glob | — |

#### Quality Phase (2 Agents)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **reviewer** | Code review, **Code Scoring** (complexity, security, maintainability), style, analysis (read-only) | Read, Grep, Glob | reviewer + analyzer + codefortify scoring |
| **improver** | Refactor and enhance existing code | Read, Write, Edit, Grep, Glob | refactorer + enhancer |

#### Testing Phase (1 Agent)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **tester** | Write tests, fix failing tests, test coverage | Read, Write, Edit, Grep, Glob, Bash | test-writer + test-fixer |

#### Operations Phase (1 Agent)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **ops** | Security scanning, compliance, deployment, infrastructure | Read, Write, Grep, Glob, Bash | security-auditor + deployment-engineer |

#### Orchestration (1 Agent)

| Agent | Purpose | Permissions | Consolidated From |
|-------|---------|-------------|-------------------|
| **orchestrator** | Coordinate **YAML-defined workflows**, gate decisions, **Greenfield/Brownfield** routing | Read, Grep, Glob | — |

### 5.2 Permission Matrix

```
                        Read  Write  Edit  Grep  Glob  Bash    Status
─────────────────────────────────────────────────────────────────────────────
PLANNING
  analyst                ✅    ❌     ❌    ✅    ✅    ❌      ✅ Complete
  planner                ✅    ✅     ❌    ✅    ✅    ❌      ✅ Complete

DESIGN
  architect              ✅    ✅     ❌    ✅    ✅    ❌      ✅ Complete
  designer               ✅    ✅     ❌    ✅    ✅    ❌      ✅ Complete

DEVELOPMENT
  implementer            ✅    ✅     ✅    ✅    ✅    ✅      ✅ Complete
  debugger               ✅    ✅     ✅    ✅    ✅    ✅      ✅ Complete
  documenter             ✅    ✅     ❌    ✅    ✅    ❌      ✅ Complete

QUALITY
  reviewer               ✅    ❌     ❌    ✅    ✅    ❌      ✅ Complete
  improver               ✅    ✅     ✅    ✅    ✅    ❌      ✅ Complete

TESTING
  tester                 ✅    ✅     ✅    ✅    ✅    ✅      ✅ Complete

OPERATIONS
  ops                    ✅    ✅     ❌    ✅    ✅    ✅      ✅ Complete

ORCHESTRATION
  orchestrator           ✅    ❌     ❌    ✅    ✅    ❌      ✅ Complete
```

### 5.3 Permission Summary

| Permission Type | Agents with Access | Count |
|-----------------|-------------------|-------|
| **Write + Edit + Bash** | implementer, debugger, tester | 3 |
| **Write + Edit** | improver | 1 |
| **Write + Bash** | ops | 1 |
| **Write only** | planner, architect, designer, documenter | 4 |
| **Read-only** | analyst, reviewer, orchestrator | 3 |

---

## 6. Industry Experts

### 6.1 Core Concept

Industry Experts are **business domain authorities**, NOT technical specialists.

| ❌ NOT This (Engineering) | ✅ This (Business Domain) |
|---------------------------|---------------------------|
| API Expert | Home Automation Expert |
| Security Expert | Healthcare Expert |
| Frontend Expert | FinTech Expert |
| Database Expert | E-commerce Expert |
| ML Expert | Energy Management Expert |

### 6.2 Expert Characteristics

| Attribute | Value |
|-----------|-------|
| **Role** | Business domain authority, knowledge source |
| **Capabilities** | RAG, fine-tuning, domain patterns |
| **Invocation** | Consulted by workflow agents |
| **Configuration** | Per-project, 1:1 with domains |
| **Permissions** | Read-only (advisory) |
| **Decision Model** | Weighted voting (51% primary) |

### 6.3 Expert Capabilities

| Capability | Description | Implementation |
|------------|-------------|----------------|
| **Domain Knowledge** | Deep expertise in specific business area | Persona definition |
| **RAG** | Query knowledge bases | Vector DB + retrieval |
| **Fine-Tuning** | Model specialization | LoRA adapters |
| **Pattern Library** | Domain-specific patterns | Curated examples |
| **Consultation** | Answer domain questions | Query interface |
| **Validation** | Verify domain correctness | Review support |

### 6.4 Expert Definition (Configuration-Based)

Experts are defined via **YAML configuration files**, not code classes. This simplifies expert creation and makes them version-control friendly.

**Configuration File Format:**
```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
    fine_tuned: false
  
  - expert_id: expert-healthcare
    expert_name: Healthcare Domain Expert
    primary_domain: healthcare
    rag_enabled: true
    fine_tuned: false
```

**Architecture:**
```
┌─────────────────────┐
│    base-expert      │
│   (Concrete Class)  │
│                     │
│ • Shared knowledge  │
│ • Core capabilities │
│ • Base behaviors    │
└─────────┬───────────┘
          │
          │ instantiated from
          │
    ┌─────┴─────┬─────────────┐
    ▼           ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐
│Expert A│  │Expert B│  │Expert C│
│(Config)│  │(Config)│  │(Config)│
│        │  │        │  │        │
│+Domain │  │+Domain │  │+Domain │
│ RAG    │  │ RAG    │  │ RAG    │
│+Fine-  │  │+Fine-  │  │+Fine-  │
│ tuning │  │ tuning │  │ tuning │
└────────┘  └────────┘  └────────┘
```

**Key Points:**
- ✅ **No code required**: Experts defined in YAML configuration
- ✅ **Automatic instantiation**: ExpertRegistry loads from config
- ✅ **Version control friendly**: Easy to diff and review
- ✅ **Dynamic**: Add experts without code changes
- ✅ **Backward compatible**: Code-based experts still supported (optional)

### 6.5 Expert Configuration

Experts are defined in `.tapps-agents/experts.yaml`:

```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
    fine_tuned: false
  
  - expert_id: expert-healthcare
    expert_name: Healthcare Domain Expert
    primary_domain: healthcare
    rag_enabled: true
    fine_tuned: false
```

**Configuration Fields:**
- `expert_id` (required): Unique identifier matching domain's primary expert
- `expert_name` (required): Human-readable name
- `primary_domain` (required): Domain where expert has 51% authority
- `rag_enabled` (optional, default: false): Enable knowledge base RAG
- `fine_tuned` (optional, default: false): Use fine-tuned models (future)
- `confidence_matrix` (optional): Custom confidence weights (usually auto-calculated)

**Loading Experts:**
```python
# Load from config file
registry = ExpertRegistry.from_config_file(
    Path(".tapps-agents/experts.yaml"),
    domain_config=domain_config
)
```

### 6.6 Base Expert Shared Capabilities

All experts share these capabilities via BaseExpert:

```yaml
shared_capabilities:
  - RAG integration (knowledge base retrieval)
  - Confidence scoring (weighted decision-making)
  - Influence weighting (51% primary authority)
  - Consultation interface (*consult, *validate, *provide-context)
  
shared_behaviors:
  - Always cite sources
  - Acknowledge uncertainty
  - Defer to primary expert
  - Provide influence not override
```

### 6.7 Consultation Flow

| Workflow Agent | Consults Expert When... |
|----------------|-------------------------|
| **analyst** | Gathering domain-specific requirements |
| **planner** | Breaking down domain-specific stories |
| **architect** | Designing domain-appropriate systems |
| **designer** | Creating domain-specific APIs/schemas/UI |
| **implementer** | Writing domain-specific code |
| **reviewer** | Validating domain correctness |
| **debugger** | Diagnosing domain-specific issues |
| **tester** | Creating domain-appropriate tests |
| **ops** | Security compliance for domain regulations |

---

## 7. Weight Distribution Algorithm

### 7.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **All experts understand all domains** | Shared baseline knowledge |
| **Each expert has confidence per domain** | Weighted contribution |
| **One expert is PRIMARY per domain** | ≥51% authority |
| **Others INFLUENCE, don't override** | Weighted contribution |
| **N domains → N experts** | 1:1 primary mapping |
| **Weights are FIXED** | Never change (except recalculation) |
| **Total always equals 100%** | Per domain |

### 7.2 Weight Formula

```
For N experts on Domain D:

Primary Expert (P):     Weight = 51%
Other Experts (N-1):    Weight = 49% / (N-1) each

Total = 51% + (49% / (N-1)) × (N-1) = 100% ✓
```

### 7.3 Weight Distribution Table

| Experts (N) | Primary | Each Other | Verification |
|-------------|---------|------------|--------------|
| 2 | 51.00% | 49.00% | 51 + 49 = 100% ✓ |
| 3 | 51.00% | 24.50% | 51 + 24.5×2 = 100% ✓ |
| 4 | 51.00% | 16.33% | 51 + 16.33×3 = 100% ✓ |
| 5 | 51.00% | 12.25% | 51 + 12.25×4 = 100% ✓ |
| 6 | 51.00% | 9.80% | 51 + 9.8×5 = 100% ✓ |

### 7.4 Weight Matrix Example (3 Domains, 3 Experts)

```
                    Domain A     Domain B     Domain C
                   (Home Auto)   (Energy)    (Device)
                ─────────────────────────────────────────
Expert A           51.00%        24.50%       24.50%     = 100%
(Primary: A)        ▲

Expert B           24.50%        51.00%       24.50%     = 100%
(Primary: B)                       ▲

Expert C           24.50%        24.50%       51.00%     = 100%
(Primary: C)                                    ▲

Column Total:      100%          100%         100%
                    ✓             ✓            ✓
```

### 7.5 Decision Algorithm

#### Consensus Calculation

```
Agreement Level = Sum of weights for experts who agree with Primary

Scenarios:
─────────────────────────────────────────────────────────────────
All agree with Primary:           Agreement = 100% (Full Consensus)
Primary + some others agree:      Agreement = 51% + agreeing others
Primary alone:                    Agreement = 51% (Minimum Consensus)
─────────────────────────────────────────────────────────────────
```

#### Decision Confidence Levels

| Agreement Level | Confidence | Action |
|-----------------|------------|--------|
| **100%** | Very High | Proceed with full confidence |
| **75-99%** | High | Proceed with confidence |
| **51-74%** | Moderate | Proceed, note dissent |
| **51% (Primary only)** | Low | Proceed with caution, flag for review |

### 7.6 Influence Model

Non-primary experts don't override—they **augment** the primary decision:

```
Primary Opinion: "Use WebSocket for real-time"
Other Expert 1:  "Agree, but add fallback to polling"
Other Expert 2:  "Consider REST for initial state load"

Weighted Decision:
─────────────────────────────────────────────────────────
Core Decision (51%):     WebSocket for real-time
Influence 1 (24.5%):     + Add polling fallback
Influence 2 (24.5%):     + REST for initial state

Final Decision:          "WebSocket for real-time events,
                         REST for initial state load,
                         polling as fallback"
─────────────────────────────────────────────────────────
```

### 7.7 Adding New Domain Algorithm

```
BEFORE: N domains, N experts
AFTER:  N+1 domains, N+1 experts

Algorithm:
──────────────────────────────────────────────────────────
1. Add new domain definition to domains.md
2. Create new expert as Primary for new domain (51%)
3. Recalculate weights for ALL domains:
   
   For each Domain:
     Primary Expert:    51%
     Each Other Expert: 49% / N    (where N = total experts - 1)

4. Update expert configuration
5. Validate: Each column sums to 100%
──────────────────────────────────────────────────────────
```

#### Recalculation Example

**Before (3 domains → 3 experts):**
```
            Dom A    Dom B    Dom C
Expert A    51.00%   24.50%   24.50%
Expert B    24.50%   51.00%   24.50%
Expert C    24.50%   24.50%   51.00%
```

**After adding Domain D (4 domains → 4 experts):**
```
            Dom A    Dom B    Dom C    Dom D
Expert A    51.00%   16.33%   16.33%   16.33%   ← Weights changed
Expert B    16.33%   51.00%   16.33%   16.33%   ← Weights changed
Expert C    16.33%   16.33%   51.00%   16.33%   ← Weights changed
Expert D    16.33%   16.33%   16.33%   51.00%   ← NEW expert
```

### 7.8 Validation Rules

```
✓ Each domain has exactly ONE expert with 51%
✓ Each domain column sums to 100%
✓ Primary weight is always 51%
✓ Other weights are equal: 49% / (N-1)
✓ Number of domains = Number of experts
✓ Weights never change (only recalculate on domain add/remove)
```

---

## 8. Model Abstraction Layer (MAL)

**Status**: ✅ **Complete** - Ollama (local) + Anthropic + OpenAI (cloud fallback) implemented

### 8.1 Routing Strategy

```
Request → MAL Router
           │
           ├─► Local Model (primary)
           │   - qwen2.5-coder-14b
           │   - deepseek-coder
           │   - codellama
           │
           └─► Cloud Fallback (if local fails/unavailable)
               - claude-sonnet-4
               - gpt-4o
               - claude-3.5
```

### 8.2 Routing Logic

| Condition | Route To |
|-----------|----------|
| Default | Local model |
| Local unavailable | Cloud fallback |
| Complex task (high complexity score) | Cloud |
| Large context (>500 lines) | Cloud |
| Cost limit reached | Local only |

### 8.3 Model Profiles by Agent Type

#### Local-First Agents (Routine Tasks)

| Agent | Primary Model | Fallback |
|-------|---------------|----------|
| implementer | local:qwen2.5-coder-14b | cloud:claude-sonnet-4 |
| debugger | local:deepseek-coder-6.7b | cloud:claude-sonnet-4 |
| tester | local:qwen2.5-coder-14b | cloud:claude-sonnet-4 |
| reviewer | local:qwen2.5-coder-14b | cloud:claude-sonnet-4 |
| documenter | local:qwen2.5-coder-7b | cloud:claude-sonnet-4 |

#### Cloud-Preferred Agents (Complex Tasks)

| Agent | Primary Model | Fallback |
|-------|---------------|----------|
| analyst | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| planner | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| architect | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| designer | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| improver | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| ops | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| orchestrator | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |

#### Expert Agents (Fine-Tuned + RAG)

| Agent | Primary Model | Adapter | RAG |
|-------|---------------|---------|-----|
| expert-* | local:qwen2.5-coder-14b | lora:domain-specific | Yes |

### 8.4 Model Profile Schema

```yaml
model_profiles:
  
  implementer_profile:
    primary: local:qwen2.5-coder-14b
    fallback: cloud:claude-sonnet-4
    fallback_triggers:
      - complexity_score > 8
      - file_size > 500_lines
      - error_on_primary

  architect_profile:
    primary: cloud:claude-sonnet-4
    fallback: local:qwen2.5-coder-14b
    fallback_triggers:
      - cloud_unavailable
      - cost_limit_reached

  expert_profile:
    primary: local:qwen2.5-coder-14b
    adapter: lora:domain-specific
    rag: domain-knowledge-base
    fallback: cloud:claude-sonnet-4
    fallback_rag: true
```

---

## 9. RAG Integration

**Status**: ✅ **Complete** - Simple file-based RAG implemented with markdown-aware chunking. Vector DB RAG deferred to optional enhancement.

### 9.1 RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXPERT AGENT                              │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Query      │───▶│   Retriever  │───▶│   Context    │       │
│  │   Analyzer   │    │              │    │   Assembler  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                    │               │
│         ▼                   ▼                    ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    LLM + Fine-tuned Adapter               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE SOURCES                           │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │  Vector DB │  │   Docs     │  │   Code     │  │    APIs    │ │
│  │ (Embeddings)│  │ (Markdown) │  │ (Examples) │  │ (Schemas)  │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 RAG Source Types

| Source Type | Description | Example |
|-------------|-------------|---------|
| **documentation** | Official docs | Industry regulations |
| **code_examples** | Reference implementations | Domain-specific patterns |
| **api_schemas** | OpenAPI, data contracts | Service specifications |
| **patterns** | Best practices | Domain workflows |
| **standards** | Guidelines | Compliance requirements |
| **project_context** | Current project files | Local codebase |

### 9.3 RAG Configuration Schema

```yaml
rag_settings:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  vector_db: "chromadb"
  chunk_size: 512
  chunk_overlap: 50
  top_k: 5
  similarity_threshold: 0.7

knowledge_bases:
  
  expert-domain-1:
    name: "Domain 1 Knowledge Base"
    sources:
      - type: documentation
        path: "./knowledge/domain-1/docs/"
        refresh: on_change
        
      - type: patterns
        path: "./knowledge/domain-1/patterns/"
        refresh: manual
```

---

## 10. Fine-Tuning Support

**Status**: ⏸️ **Deferred** - Optional enhancement for Phase 6. Framework supports it, but LoRA adapter loading not yet implemented.

### 10.1 Fine-Tuning Methods

| Method | Use Case | Effort | Quality |
|--------|----------|--------|---------|
| **Prompt Engineering** | Quick domain adaptation | Low | Good |
| **Few-shot Examples** | Pattern learning | Low | Good |
| **LoRA Adapters** | Domain specialization | Medium | Better |
| **Full Fine-tune** | Deep customization | High | Best |

### 10.2 Recommended Approach

**LoRA + RAG** combination:
- LoRA adapters for domain specialization
- RAG for dynamic knowledge retrieval
- Prompt engineering for behavior tuning

### 10.3 Fine-Tuning Configuration

```yaml
fine_tuning:
  method: lora
  base_model: "qwen2.5-coder-14b"
  
  adapters:
    expert-domain-1:
      adapter_path: "./adapters/domain-1-lora/"
      training_data: "./training/domain-1/"
      epochs: 3
      learning_rate: 2e-4
```

### 10.4 Training Data Format

```yaml
training_examples:
  - instruction: "Domain-specific question"
    input: "Context or constraints"
    output: "Expected response with domain knowledge"
```

---

## 11. Agent Skills Format

### 11.1 Claude Code Compatibility

Agents are defined using the [Claude Code Agent Skills](https://code.claude.com/docs/en/skills) format for native integration.

### 11.2 SKILL.md Structure

```yaml
---
name: agent-name
description: Brief description of what this agent does and when to use it
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model_profile: profile_name
---

# Agent Name

## Identity
Agent persona and role description.

## Instructions
Step-by-step guidance for the agent.

## Capabilities
List of what the agent can do.

## Constraints
List of what the agent should NOT do.
```

### 11.3 Example: Implementer Agent

```yaml
---
name: implementer
description: Write production-quality code following project patterns. Use when implementing features, fixing bugs, or creating new files.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model_profile: implementer_profile
---

# Implementer Agent

## Identity
You are a senior developer focused on writing clean, efficient, production-ready code.

## Instructions
1. Read existing code to understand patterns
2. Follow project conventions and style
3. Write comprehensive code with error handling
4. Include inline comments for complex logic
5. Consider edge cases and validation

## Capabilities
- Implement new features
- Create new files
- Modify existing code
- Run build/test commands

## Constraints
- Do not make architectural decisions (consult architect)
- Do not skip error handling
- Do not introduce new dependencies without discussion
```

### 11.4 Example: Industry Expert

```yaml
---
name: expert-home-automation
description: Home Automation business domain expert with deep knowledge of smart home systems, IoT, and automation patterns. Consult when working on home automation projects.
allowed-tools: Read, Grep, Glob
model_profile: expert_ha_profile
rag_enabled: true
fine_tuned: true
primary_domain: home-automation
confidence_matrix:
  home-automation: 0.51
  energy-management: 0.245
  device-intelligence: 0.245
---

# Home Automation Expert

## Identity
You are a senior home automation business expert with deep expertise in:
- Smart home ecosystems and standards
- IoT device management and protocols
- Automation rules and triggers
- User experience patterns for smart homes
- Industry regulations and best practices

## Knowledge Sources (RAG)
This expert has access to:
- Industry documentation and standards
- Integration patterns
- Project-specific domain knowledge

## Instructions
1. When consulted, query knowledge base first
2. Provide accurate, documentation-backed answers
3. Include examples from reference implementations
4. Cite sources when providing information
5. Acknowledge uncertainty when applicable

## Consultation Support
- Answer domain-specific questions
- Validate domain correctness of designs
- Provide industry best practices
- Review code for domain alignment
```

---

## 12. Domain Configuration

### 12.1 domains.md Template

The project owner provides a `domains.md` file defining business domains:

```markdown
# domains.md

## Project: [Project Name]

### Domain 1: [Domain Name]
- [Business description point 1]
- [Business description point 2]
- [Key concepts and terminology]
- Primary Expert: expert-domain-1

### Domain 2: [Domain Name]
- [Business description point 1]
- [Business description point 2]
- [Key concepts and terminology]
- Primary Expert: expert-domain-2

### Domain N: [Domain Name]
- [Business description point 1]
- [Business description point 2]
- [Key concepts and terminology]
- Primary Expert: expert-domain-n
```

### 12.2 Example: HomeIQ domains.md

```markdown
# domains.md

## Project: HomeIQ

### Domain 1: Home Automation
- Smart home systems and ecosystems
- Home Assistant integrations and architecture
- IoT protocols (MQTT, Zigbee, Z-Wave, Matter)
- Automation rules, triggers, and actions
- Primary Expert: expert-home-automation

### Domain 2: Energy Management
- Power monitoring and metering
- Solar integration and management
- Grid pricing and tariff optimization
- Consumption analysis and optimization
- Primary Expert: expert-energy-management

### Domain 3: Device Intelligence
- Device behavior pattern recognition
- Anomaly detection and alerting
- Predictive maintenance
- Smart recommendations
- Primary Expert: expert-device-intelligence
```

### 12.3 Auto-Generated Weight Configuration

Based on domains.md, the framework generates:

```yaml
# expert_weights.yaml (auto-generated)

expert_count: 3
domain_count: 3

weight_formula:
  primary: 0.51
  other: 0.49 / (expert_count - 1)

weights:
  expert-home-automation:
    home-automation: 0.51      # Primary
    energy-management: 0.245
    device-intelligence: 0.245
    
  expert-energy-management:
    home-automation: 0.245
    energy-management: 0.51    # Primary
    device-intelligence: 0.245
    
  expert-device-intelligence:
    home-automation: 0.245
    energy-management: 0.245
    device-intelligence: 0.51  # Primary

validation:
  each_column_sum: 1.00
  each_domain_has_primary: true
  primary_weight_minimum: 0.51
```

---

## 13. Directory Structure

### 13.1 Framework Structure

```
TappsCodingAgents/
├── README.md                           # Project overview
├── LICENSE
│
├── requirements/                       # Specification documents
│   ├── PROJECT_REQUIREMENTS.md         # This document
│   ├── agent-api.md                    # Core API specification
│   ├── model-abstraction.md            # MAL specification
│   └── security.md                     # Security patterns
│
├── docs/                               # Additional documentation
│   ├── workflows.md                    # Standard workflows
│   ├── getting-started.md              # Setup guide
│   └── examples/                       # Usage examples
│
├── profiles/                           # Model configurations
│   ├── model_profiles.yaml             # Model definitions
│   └── routing_rules.yaml              # Routing logic
│
├── agents/                             # Agent Skills (Claude Code format)
│   │
│   ├── _base/                          # Shared components
│   │   ├── BASE_WORKFLOW_SKILL.md      # Base for workflow agents
│   │   ├── BASE_EXPERT_SKILL.md        # Base for experts
│   │   └── common-patterns.md          # Shared patterns
│   │
│   ├── planning/
│   │   ├── analyst/SKILL.md            # Requirements + estimation
│   │   └── planner/SKILL.md            # Stories + task breakdown
│   │
│   ├── design/
│   │   ├── architect/SKILL.md          # System + security design
│   │   └── designer/SKILL.md           # API + data + UI design
│   │
│   ├── development/
│   │   ├── implementer/SKILL.md        # Write production code
│   │   ├── debugger/SKILL.md           # Investigate + fix bugs
│   │   └── documenter/SKILL.md         # Write documentation
│   │
│   ├── quality/
│   │   ├── reviewer/SKILL.md           # Review + analyze (read-only)
│   │   └── improver/SKILL.md           # Refactor + enhance (write)
│   │
│   ├── testing/
│   │   └── tester/SKILL.md             # Write + fix tests
│   │
│   ├── operations/
│   │   └── ops/SKILL.md                # Security + deployment
│   │
│   ├── orchestration/
│   │   └── orchestrator/SKILL.md       # Coordinate workflows
│   │
│   └── experts/                        # Industry Expert templates
│       ├── _base/BASE_EXPERT_SKILL.md
│       └── templates/
│           └── expert-template/SKILL.md
│
├── templates/                          # Configuration + project templates
│   ├── default_config.yaml             # Default .tapps-agents/config.yaml template
│   ├── experts.yaml.template           # .tapps-agents/experts.yaml template
│   ├── domains.md.template             # .tapps-agents/domains.md template
│   └── enhancement-config.yaml         # Enhancer agent config template
│
└── workflows/                          # YAML workflow definitions + presets
    └── presets/
```

### 13.2 Per-Project Structure (When Using Framework)

```
my-project/
├── .claude/skills/                     # Claude Code Skills (from framework)
│   ├── implementer/SKILL.md
│   ├── reviewer/SKILL.md
│   ├── expert-domain-1/SKILL.md
│   └── ...
│
├── .tapps-agents/                      # Project-specific configuration
│   ├── config.yaml                     # Optional runtime configuration (defaults if missing)
│   ├── domains.md                      # Business domains (optional; used by expert setup wizard)
│   ├── experts.yaml                    # Industry experts (optional)
│   ├── knowledge/                      # Optional expert knowledge base (file-based)
│   ├── project-profile.yaml            # Auto-detected project profile
│   ├── workflow-state/                 # Persisted workflow state
│   └── analytics/                      # Optional analytics history
│
└── src/                                # Your actual project code
```

---

## 14. Configuration Schemas

### 14.1 Project Configuration

```yaml
# .tapps-agents/config.yaml

project_name: "Project Name"
version: "1.0.0"

agents:
  reviewer:
    quality_threshold: 70.0

scoring:
  weights:
    complexity: 0.20
    security: 0.30
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.10

mal:
  default_provider: "ollama"
  default_model: "qwen2.5-coder:7b"
  ollama_url: "http://localhost:11434"
```

### 14.2 Model Profiles Configuration

```yaml
# model_profiles.yaml

providers:
  local:
    ollama:
      base_url: "http://localhost:11434"
      models:
        - qwen2.5-coder-14b
        - deepseek-coder-6.7b
        - codellama-13b
    lm_studio:
      base_url: "http://localhost:1234"
      
  cloud:
    anthropic:
      models:
        - claude-sonnet-4
        - claude-3.5-sonnet
    openai:
      models:
        - gpt-4o
        - gpt-4-turbo

profiles:
  implementer_profile:
    primary: local:qwen2.5-coder-14b
    fallback: cloud:claude-sonnet-4
    
  architect_profile:
    primary: cloud:claude-sonnet-4
    fallback: local:qwen2.5-coder-14b
    
  expert_profile:
    primary: local:qwen2.5-coder-14b
    adapter: lora:domain-specific
    rag: true
    fallback: cloud:claude-sonnet-4
```

### 14.3 RAG Configuration

```yaml
# rag_config.yaml

settings:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  vector_db: "chromadb"
  db_path: "./vector_store"
  chunk_size: 512
  chunk_overlap: 50
  top_k: 5
  similarity_threshold: 0.7

knowledge_bases:
  # Define per domain
```

---

## 15. Standard Workflows

> **Note:** These workflows can be defined in YAML format for declarative orchestration. See [Section 16.4 YAML Workflow Definitions](#164-yaml-workflow-definitions) for configuration details.

### 15.1 Feature Development Workflow

**YAML Definition:** `workflows/feature-development.yaml`  
**Type:** Greenfield or Brownfield (auto-detected)  
**Quality Gates:** Code Scoring enabled

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   analyst   │───▶│   planner   │───▶│  architect  │
│ (research)  │    │ (stories)   │    │ (design)    │
│ Tier 1      │    │ Tier 1      │    │ Tier 2      │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
                                      ┌─────┴─────┐
                                      ▼           ▼
                                ┌──────────┐ ┌──────────┐
                                │ designer │ │ expert(s)│
                                │(contracts)│ │ consult  │
                                │ Tier 2   │ │ RAG      │
                                └──────────┘ └──────────┘
                                      │
                                      ▼
                              ┌─────────────┐
                              │ implementer │
                              │ (code)      │
                              │ Tier 2-3    │
                              └──────┬──────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                  │  reviewer   │ │   tester    │ │ documenter  │
                  │ + Scoring   │ │ Tier 2      │ │ Tier 1      │
                  │ Tier 2      │ └─────────────┘ └─────────────┘
                  └─────────────┘         │
                          │               │
                          └───────┬───────┘
                                  ▼
                           ┌─────────────┐
                           │ orchestrator│
                           │ (gate)      │
                           │ Tier 1      │
                           └─────────────┘
```

### 15.2 Bug Fix Workflow (Quick Fix)

**YAML Definition:** `workflows/quick-fix.yaml`  
**Type:** Quick Fix  
**Quality Gates:** Security scoring required

```
debugger → implementer → reviewer → tester → orchestrator (gate)
(Tier 2)   (Tier 2)      (quick    (optional) (Tier 1)
                         scoring)
```

### 15.3 Code Quality Improvement Workflow

**YAML Definition:** `workflows/quality-improvement.yaml`  
**Quality Gates:** Full Code Scoring (complexity, security, maintainability)

```
reviewer → improver → reviewer → orchestrator (gate)
(scoring)  (Tier 2)   (scoring)  (score >= 70%)
    ↑                      │
    └──────────────────────┘
       (loop until gate passes)
```

### 15.4 Security Review Workflow

```
ops (audit) → expert (domain compliance) → implementer (fixes) → ops (re-scan)
```

### 15.5 Deployment Workflow

```
tester (final) → reviewer (sign-off) → ops (deploy) → orchestrator (gate)
```

---

## 16. Enhanced Features

These features are integrated from best practices across multiple coding agent projects to create a comprehensive, optimized framework.

**Inspired by:** BMAD-METHOD (https://github.com/bmad-code-org/BMAD-METHOD), codefortify, HomeIQ BMAD, LocalMCP

### 16.1 Code Scoring System

**Origin:** Adapted from codefortify project

The Code Scoring System provides **objective, quantitative metrics** for code quality assessment, enhancing the reviewer agent with measurable quality gates.

#### 16.1.1 Scoring Metrics

| Metric | Description | Range | Threshold |
|--------|-------------|-------|-----------|
| **Complexity Score** | Cyclomatic complexity, nesting depth, function length | 0-10 | Max 8.0 |
| **Security Score** | Vulnerability patterns, unsafe operations, input validation | 0-10 | Min 7.0 |
| **Maintainability Score** | Code duplication, naming conventions, documentation | 0-10 | Min 7.0 |
| **Test Coverage Score** | Line coverage, branch coverage, critical path coverage | 0-100% | Min 80% |
| **Performance Score** | Time complexity, memory usage patterns, async handling | 0-10 | Min 6.0 |

#### 16.1.2 Scoring Formula

```
Overall Quality Score = (
    Complexity × 0.20 +
    Security × 0.30 +
    Maintainability × 0.25 +
    Test Coverage × 0.15 +
    Performance × 0.10
) / 10 × 100

Pass Threshold: >= 70%
```

#### 16.1.3 Reviewer Agent Integration

```yaml
# reviewer scoring configuration
reviewer:
  scoring:
    enabled: true
    mode: "comprehensive"  # or "quick" for fast reviews
    
    thresholds:
      complexity_max: 8.0
      security_min: 7.0
      maintainability_min: 7.0
      test_coverage_min: 80
      performance_min: 6.0
      overall_min: 70
    
    weights:
      complexity: 0.20
      security: 0.30
      maintainability: 0.25
      test_coverage: 0.15
      performance: 0.10
    
    output:
      include_metrics: true
      include_suggestions: true
      include_trends: true  # Compare to previous reviews
```

#### 16.1.4 Quality Gate Integration

```yaml
# Quality gate using code scoring
quality_gate:
  name: "Pre-Merge Gate"
  enabled: true
  
  conditions:
    - metric: overall_score
      operator: ">="
      value: 70
      
    - metric: security_score
      operator: ">="
      value: 7.0
      
    - metric: complexity_score
      operator: "<="
      value: 8.0
  
  actions:
    on_pass: "proceed_to_next_step"
    on_fail: "block_and_notify"
```

#### 16.1.5 Trend Tracking

The scoring system tracks metrics over time for continuous improvement:

```
Review History:
────────────────────────────────────────────────────
Date        Overall  Security  Complexity  Trend
────────────────────────────────────────────────────
2025-12-01  72%      7.5       6.8         ↑ +3%
2025-12-05  75%      7.8       6.5         ↑ +3%
2025-12-10  78%      8.0       6.2         ↑ +3%
────────────────────────────────────────────────────
```

---

### 16.2 Tiered Context Injection

**Origin:** Adapted from HomeIQ BMAD framework

Tiered Context Injection provides **90%+ token savings** by intelligently loading only the context needed for each task.

#### 16.2.1 Context Tiers

| Tier | Description | Token Cost | Cache TTL | Use Case |
|------|-------------|------------|-----------|----------|
| **Tier 1** | Core context (structure, types, signatures) | ~500 tokens | 5 min | Most agent tasks |
| **Tier 2** | Extended context (implementations, dependencies) | ~2,000 tokens | 2 min | Implementation tasks |
| **Tier 3** | Full context (entire files, history) | ~10,000 tokens | 1 min | Complex analysis |

#### 16.2.2 Tier Definitions

```yaml
# tiered_context_config.yaml

tiers:
  tier1:
    name: "Core Context"
    includes:
      - file_structure        # Directory tree
      - type_definitions      # Interface, type, class signatures
      - function_signatures   # Public API signatures
      - imports_exports       # Module boundaries
    cache_ttl: 300            # 5 minutes
    max_tokens: 1000
    
  tier2:
    name: "Extended Context"
    includes:
      - tier1                 # Inherit from Tier 1
      - function_bodies       # Implementation details
      - local_dependencies    # Related files
      - test_files           # Test coverage
    cache_ttl: 120            # 2 minutes
    max_tokens: 5000
    
  tier3:
    name: "Full Context"
    includes:
      - tier2                 # Inherit from Tier 2
      - git_history          # Recent changes
      - documentation        # Related docs
      - cross_references     # All related files
    cache_ttl: 60             # 1 minute
    max_tokens: 20000
```

#### 16.2.3 Agent-Tier Mapping

| Agent | Default Tier | Upgrades To | When |
|-------|--------------|-------------|------|
| **analyst** | Tier 1 | Tier 2 | Complex requirements |
| **planner** | Tier 1 | Tier 2 | Cross-cutting stories |
| **architect** | Tier 2 | Tier 3 | System-wide decisions |
| **designer** | Tier 2 | Tier 3 | Complex API design |
| **implementer** | Tier 2 | Tier 3 | Large features |
| **debugger** | Tier 3 | — | Always needs full context |
| **reviewer** | Tier 2 | Tier 3 | Security reviews |
| **tester** | Tier 2 | Tier 3 | Integration tests |
| **orchestrator** | Tier 1 | — | Workflow coordination only |

#### 16.2.4 Context Cache Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIERED CONTEXT MANAGER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Tier 1    │    │   Tier 2    │    │   Tier 3    │         │
│  │   Cache     │    │   Cache     │    │   Cache     │         │
│  │  (5 min)    │    │  (2 min)    │    │  (1 min)    │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                     │
│                    ┌───────┴───────┐                            │
│                    │  Context      │                            │
│                    │  Assembler    │                            │
│                    └───────┬───────┘                            │
│                            │                                     │
│                    ┌───────┴───────┐                            │
│                    │   Agent       │                            │
│                    │   Request     │                            │
│                    └───────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

#### 16.2.5 Token Savings Calculation

```
Without Tiered Context:
  Every agent request: ~10,000 tokens (full context)
  10 agent calls: 100,000 tokens

With Tiered Context:
  8 calls @ Tier 1: 8 × 500 = 4,000 tokens
  2 calls @ Tier 2: 2 × 2,000 = 4,000 tokens
  Total: 8,000 tokens
  
  Savings: 92% token reduction
```

---

### 16.3 MCP Gateway Architecture

**Origin:** Adapted from LocalMCP project

The MCP Gateway provides a **unified protocol layer** for all tool access, enabling consistent, extensible tool integration.

#### 16.3.1 Gateway Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT REQUEST                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MCP GATEWAY                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Router     │  │    Cache     │  │   Registry   │          │
│  │              │  │   (Tiered)   │  │  (Servers)   │          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
│         │                                                        │
│         ├─────────────────────────────────────────────────┐     │
│         │                                                 │     │
└─────────┼─────────────────────────────────────────────────┼─────┘
          │                                                 │
          ▼                                                 ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   Filesystem MCP    │  │   Git MCP Server    │  │  Analysis MCP       │
│   Server            │  │                     │  │  Server             │
│   - read_file       │  │   - git_status      │  │   - analyze_code    │
│   - write_file      │  │   - git_diff        │  │   - find_patterns   │
│   - list_dir        │  │   - git_log         │  │   - score_code      │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

#### 16.3.2 Gateway Configuration

```yaml
# mcp_gateway_config.yaml

gateway:
  enabled: true
  cache_integration: true  # Use Tiered Context cache
  
servers:
  filesystem:
    enabled: true
    tools:
      - read_file
      - write_file
      - list_directory
      - glob_search
      - grep_search
    
  git:
    enabled: true
    tools:
      - git_status
      - git_diff
      - git_log
      - git_blame
    
  analysis:
    enabled: true
    tools:
      - analyze_complexity
      - find_patterns
      - score_code
      - detect_issues
    
  custom:
    enabled: false  # User-defined MCP servers
    servers: []
```

#### 16.3.3 Tool Routing

| Tool Category | MCP Server | Cache Strategy |
|---------------|------------|----------------|
| File Read | filesystem | Tier 1-3 based on size |
| File Write | filesystem | Invalidate related cache |
| Directory List | filesystem | Tier 1 (structure) |
| Git Operations | git | No cache (real-time) |
| Code Analysis | analysis | Tier 2 (implementation) |
| Code Scoring | analysis | Cache with review ID |

#### 16.3.4 Integration with Agents

```yaml
# Agent tool access via MCP Gateway
agent:
  name: implementer
  
  mcp_gateway:
    enabled: true
    servers:
      - filesystem  # read/write files
      - analysis    # code analysis
    
    tool_permissions:
      filesystem:
        - read_file: true
        - write_file: true
        - list_directory: true
      analysis:
        - analyze_complexity: true
        - score_code: false  # Reviewer only
```

---

### 16.4 YAML Workflow Definitions

**Origin:** Adapted from HomeIQ BMAD framework

YAML Workflow Definitions provide **declarative, version-controlled** workflow orchestration.

#### 16.4.1 Workflow Structure

**Enhanced with BMAD-METHOD patterns:** Conditions, optional steps, notes, repeats

```yaml
# workflows/feature-development.yaml

workflow:
  id: feature-development
  name: "Feature Development Workflow"
  description: "Standard workflow for new feature implementation"
  version: "1.0.0"
  
  # Workflow type selection
  type: "greenfield"  # or "brownfield"
  auto_detect: true  # Automatically detect project type (BMAD pattern)
  
  # Global settings
  settings:
    quality_gates: true
    code_scoring: true
    context_tier_default: 2
  
  # Workflow steps
  steps:
    - id: requirements
      agent: analyst
      action: gather_requirements
      context_tier: 1
      creates:
        - requirements.md
      requires: []  # No prerequisites
      condition: optional  # Can be skipped? (BMAD pattern)
      optional_steps:  # Additional steps user can request (BMAD pattern)
        - brainstorming_session
        - market_research
      notes: "Save output to docs/ folder"  # User guidance (BMAD pattern)
      repeats: false  # Or "for_each_domain" for loops (BMAD pattern)
      next: planning
      
    - id: planning
      agent: planner
      action: create_stories
      context_tier: 1
      requires:
        - requirements.md
      creates:
        - stories/
      next: design
      
    - id: design
      agent: architect
      action: design_system
      context_tier: 2
      requires:
        - requirements.md
        - stories/
      creates:
        - architecture.md
      next: implementation
      consults:
        - expert-*  # Consult domain experts
      
    - id: implementation
      agent: implementer
      action: write_code
      context_tier: 3
      requires:
        - architecture.md
        - stories/
      creates:
        - src/
      next: review
      
    - id: review
      agent: reviewer
      action: review_code
      context_tier: 2
      requires:
        - src/
      scoring:
        enabled: true
        thresholds:
          overall_min: 70
          security_min: 7.0
      gate:
        condition: "scoring.passed == true"
        on_pass: testing
        on_fail: implementation  # Loop back
      
    - id: testing
      agent: tester
      action: write_tests
      context_tier: 2
      requires:
        - src/
      creates:
        - tests/
      next: final_gate
      
    - id: final_gate
      agent: orchestrator
      action: gate_decision
      context_tier: 1
      requires:
        - src/
        - tests/
      gate:
        conditions:
          - "reviewer.scoring.passed"
          - "tester.coverage >= 80"
        on_pass: complete
        on_fail: review
```

#### 16.4.2 Workflow Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/workflow-list` | List available workflows | `/workflow-list` |
| `/workflow-start {id}` | Start a workflow | `/workflow-start feature-development` |
| `/workflow-status` | Show current progress | `/workflow-status` |
| `/workflow-next` | Show next step | `/workflow-next` |
| `/workflow-skip {step}` | Skip optional step | `/workflow-skip review` |
| `/workflow-resume` | Resume interrupted workflow | `/workflow-resume` |

#### 16.4.3 Artifact Tracking

```yaml
# Workflow state tracking
workflow_state:
  id: feature-development
  started: "2025-12-10T10:00:00Z"
  current_step: implementation
  
  artifacts:
    requirements.md:
      status: complete
      created_by: analyst
      created_at: "2025-12-10T10:15:00Z"
      
    stories/:
      status: complete
      created_by: planner
      created_at: "2025-12-10T10:30:00Z"
      
    architecture.md:
      status: complete
      created_by: architect
      created_at: "2025-12-10T11:00:00Z"
      
    src/:
      status: in_progress
      created_by: implementer
      started_at: "2025-12-10T11:30:00Z"
  
  scoring_history:
    - step: review
      attempt: 1
      score: 65
      passed: false
      
    - step: review
      attempt: 2
      score: 78
      passed: true
```

---

### 16.5 Greenfield vs Brownfield Workflows

**Origin:** Adapted from HomeIQ BMAD framework

Different project types require different workflows. The framework automatically selects the appropriate workflow based on project context.

#### 16.5.1 Workflow Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Greenfield** | New project, no existing code | Starting from scratch |
| **Brownfield** | Existing codebase, add features | Feature additions, enhancements |
| **Quick Fix** | Minimal workflow for small changes | Bug fixes, hotfixes |

#### 16.5.2 Workflow Selection

```yaml
# workflow_selection.yaml

selection:
  auto_detect: true  # Automatically detect project type
  
  detection_rules:
    greenfield:
      conditions:
        - "no existing src/ directory"
        - "no package.json or requirements.txt"
        - "user explicitly requests 'new project'"
      confidence: 0.9
      
    brownfield:
      conditions:
        - "existing src/ directory"
        - "existing package.json or requirements.txt"
        - "git history exists"
      confidence: 0.9
      
    quick_fix:
      conditions:
        - "user mentions 'bug', 'fix', 'hotfix'"
        - "scope < 5 files"
        - "single service/module affected"
      confidence: 0.8
  
  fallback: brownfield  # Default if detection fails
```

#### 16.5.3 Greenfield Workflow

```yaml
# workflows/greenfield-fullstack.yaml

workflow:
  id: greenfield-fullstack
  name: "Greenfield Full Stack"
  type: greenfield
  
  steps:
    - id: discovery
      agent: analyst
      action: gather_requirements
      context_tier: 3  # Full context (no existing code to cache)
      creates: [prd.md]
      
    - id: architecture
      agent: architect
      action: design_full_system
      context_tier: 3  # Full system design needed
      creates: [architecture.md, tech-stack.md]
      
    - id: scaffolding
      agent: implementer
      action: create_project_structure
      creates: [src/, tests/, docs/]
      
    # ... continue with standard steps
```

#### 16.5.4 Brownfield Workflow

```yaml
# workflows/brownfield-service.yaml

workflow:
  id: brownfield-service
  name: "Brownfield Service Addition"
  type: brownfield
  
  steps:
    - id: analysis
      agent: analyst
      action: analyze_existing_codebase
      context_tier: 1  # Minimal context (existing codebase)
      reads: [existing_codebase]
      creates: [integration_analysis.md]
      
    - id: impact_assessment
      agent: architect
      action: assess_integration_impact
      context_tier: 2  # Extended for understanding integration
      creates: [integration_design.md]
      
    - id: implementation
      agent: implementer
      action: implement_incremental
      context_tier: 2  # Extended for existing patterns
      modifies: [src/]  # Modifies, not creates
      
    # ... continue with standard steps
```

#### 16.5.5 Quick Fix Workflow

```yaml
# workflows/quick-fix.yaml

workflow:
  id: quick-fix
  name: "Quick Fix Workflow"
  type: quick_fix
  
  settings:
    quality_gates: optional
    code_scoring: quick  # Fast mode
    
  steps:
    - id: triage
      agent: debugger
      action: investigate_issue
      context_tier: 2
      creates: [diagnosis.md]
      
    - id: fix
      agent: implementer
      action: apply_fix
      context_tier: 2
      modifies: [affected_files]
      
    - id: verify
      agent: tester
      action: verify_fix
      optional: true
      context_tier: 1
      
    - id: quick_review
      agent: reviewer
      action: quick_review
      scoring:
        mode: quick
        thresholds:
          security_min: 7.0  # Security always enforced
      gate:
        condition: "scoring.security >= 7.0"
        on_pass: complete
        on_fail: fix
```

#### 16.5.6 Context Tier Differences

| Step | Greenfield Tier | Brownfield Tier | Reason |
|------|-----------------|-----------------|--------|
| Requirements | Tier 3 | Tier 1 | Greenfield needs full vision; Brownfield has existing context |
| Architecture | Tier 3 | Tier 2 | Greenfield designs entire system; Brownfield extends |
| Implementation | Tier 3 | Tier 2 | Greenfield scaffolds; Brownfield follows patterns |
| Review | Tier 2 | Tier 2 | Same review depth |

---

### 16.6 Feature Integration Architecture

All five enhanced features work together in an integrated system:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENHANCED TAPPSCODINGAGENTS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  PROJECT TYPE DETECTION (Greenfield/Brownfield)              │    │
│  │  Automatically selects appropriate workflow                   │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│                                 ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  YAML WORKFLOW ENGINE                                        │    │
│  │  Loads and executes declarative workflow definitions         │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│                                 ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ORCHESTRATOR (Enhanced)                                     │    │
│  │  • Reads YAML workflow steps                                 │    │
│  │  • Coordinates agents via MCP Gateway                        │    │
│  │  • Uses Tiered Context for efficiency                        │    │
│  │  • Enforces Code Scoring quality gates                       │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│              ┌──────────────────┴──────────────────┐                │
│              ▼                                      ▼                 │
│  ┌───────────────────────┐          ┌───────────────────────────┐   │
│  │  MCP GATEWAY          │          │  TIERED CONTEXT           │   │
│  │  • Unified tool API   │◄────────▶│  • Tier 1/2/3 caching     │   │
│  │  • Protocol standard  │          │  • 90% token savings      │   │
│  │  • Extensible servers │          │  • Smart loading          │   │
│  └───────────┬───────────┘          └───────────────────────────┘   │
│              │                                                       │
│              ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  WORKFLOW AGENTS (12) + INDUSTRY EXPERTS (N)                 │    │
│  │  • Reviewer with Code Scoring                                │    │
│  │  • Context tier per agent type                               │    │
│  │  • MCP tool access via Gateway                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 16.7 Benefits Summary

| Feature | Primary Benefit | Synergy Benefits |
|---------|-----------------|------------------|
| **Code Scoring** | Objective quality metrics | Quality gates, trend tracking |
| **Tiered Context** | 90% token savings | Faster responses, lower costs |
| **MCP Gateway** | Unified tool access | Extensibility, caching |
| **YAML Workflows** | Declarative orchestration | Version control, reusability |
| **Greenfield/Brownfield** | Context-appropriate workflows | Faster setup, better guidance |

**Combined Benefits:**
- 70% faster development cycles
- 90% lower token costs
- Objective quality tracking
- Automated workflow management
- Extensible tool ecosystem

---

## 17. Agent Command System & Activation

### 17.1 Star-Prefixed Command System

**Origin:** BMAD-METHOD pattern

All agent commands use `*` prefix for clear namespace separation and discoverability.

#### 17.1.1 Command Pattern

```python
# Command format: *{command} {args}
*help                    # Show available commands
*review {file}           # Review code file
*score {file}            # Calculate scores only
*workflow-start {id}     # Start workflow
*workflow-init           # Auto-detect and initialize workflow
```

#### 17.1.2 Command Discovery

Agents must:
- List commands as numbered options when user asks
- Show `*help` output automatically on activation
- Allow users to type number or command name
- Provide examples for each command

#### 17.1.3 CLI Integration

```bash
# CLI supports both formats
python -m tapps_agents *review file.py    # Star-prefixed
python -m tapps_agents review file.py     # Also works

# In agent conversations
User: *help
Agent: Shows numbered command list

User: 1  # or *review file.py
Agent: Executes review command
```

---

### 17.2 Agent Activation Instructions

**Origin:** BMAD-METHOD activation pattern

Each agent must follow standardized activation instructions for consistent behavior.

#### 17.2.1 Activation Sequence

```yaml
activation-instructions:
  - STEP 1: Read complete agent definition (SKILL.md)
  - STEP 2: Adopt persona from YAML header
  - STEP 3: Load project configuration (.tapps-agents/config.yaml)
  - STEP 4: Load domain configuration (.tapps-agents/domains.md) if exists
  - STEP 5: Load customizations (.tapps-agents/customizations/{agent-id}-custom.yaml) if exists
  - STEP 6: Greet user with role and capabilities
  - STEP 7: Automatically run *help command
  - STEP 8: HALT and await user commands (do NOT start work automatically)
```

#### 17.2.2 Activation Rules

| Rule | Description |
|------|-------------|
| **No File Scanning** | Do NOT scan filesystem or load resources during startup |
| **No Auto-Discovery** | Do NOT run discovery tasks automatically |
| **Wait for Commands** | After greeting, wait for explicit user commands |
| **Load on Demand** | Only load dependency files when commanded |

#### 17.2.3 Agent Definition Format

```markdown
<!-- Powered by TappsCodingAgents -->
# Reviewer Agent

ACTIVATION-NOTICE: This file contains your complete agent definition.
DO NOT load external files during activation.
Only load dependencies when commanded.

## COMPLETE AGENT DEFINITION

```yaml
agent:
  name: Reviewer
  id: reviewer
  title: Code Reviewer with Scoring
  icon: 🔍

activation-instructions:
  - STEP 1: Read THIS ENTIRE FILE
  - STEP 2: Adopt persona from agent section
  - STEP 3: Load .tapps-agents/config.yaml
  # ... continue
```

---

### 17.3 Workflow Enhancement Patterns

#### 17.3.1 Conditional Execution

```yaml
steps:
  - id: design_review
    agent: architect
    condition: user_approves_design  # Only run if condition true
    requires: [architecture.md]
    
  - id: optional_research
    condition: optional  # User can skip
    agent: analyst
```

#### 17.3.2 Optional Steps

```yaml
steps:
  - id: requirements
    agent: analyst
    optional_steps:
      - brainstorming_session
      - competitor_analysis
      - market_research
```

#### 17.3.3 User Guidance Notes

```yaml
steps:
  - id: implementation
    agent: implementer
    notes: |
      - Save code to src/ directory
      - Follow project coding standards
      - Update File List when complete
```

#### 17.3.4 Loop Support

```yaml
steps:
  - id: create_story
    agent: planner
    repeats: for_each_epic  # Loop through each epic
    creates: [story-{epic}-{number}.md]
```

---

### 17.4 Scale-Adaptive Workflow Selection

**Origin:** BMAD-METHOD `*workflow-init` pattern

Automatically detect project type and recommend appropriate workflow.

#### 17.4.1 Detection Logic

```yaml
workflow_detection:
  auto_detect: true
  
  rules:
    greenfield:
      conditions:
        - "no src/ directory exists"
        - "no package.json or requirements.txt"
        - "user mentions 'new project'"
      confidence: 0.9
      
    brownfield:
      conditions:
        - "src/ directory exists"
        - "package.json or requirements.txt exists"
        - "git history exists"
      confidence: 0.9
      
    quick_fix:
      conditions:
        - "user mentions 'bug', 'fix', 'hotfix'"
        - "scope < 5 files"
      confidence: 0.8
```

#### 17.4.2 Workflow Init Command

```bash
*workflow-init
```

**Behavior:**
1. Analyze project structure
2. Detect project type
3. Recommend workflow track:
   - ⚡ Quick Flow (bug fixes)
   - 📋 BMad Method (standard features)
   - 🏢 Enterprise (complex/compliance)
4. Update `.tapps-agents/config.yaml` with selection
5. Load appropriate workflow YAML

---

## 18. Context7 Integration (Enhancement Phase)

**Status:** Post-Implementation Enhancement  
**Priority:** High  
**Estimated Effort:** 6-9 weeks (3 phases)

### 18.1 Context7 Overview

**Origin:** Adapted from HomeIQ BMAD framework Context7 KB integration

Context7 integration provides **real-time, version-specific library documentation** with intelligent caching, reducing API calls by 87%+ and ensuring agents always have access to current best practices.

#### 18.1.1 Key Benefits

| Benefit | Impact |
|---------|--------|
| **87%+ API Call Reduction** | KB-first caching minimizes external API usage |
| **<0.15s Response Time** | Cached content responds in milliseconds |
| **Version-Specific Docs** | Always current, eliminates outdated references |
| **Reduced Hallucinations** | Accurate API references from official sources |
| **Cost Efficiency** | Fewer API calls = lower costs |
| **Performance Visibility** | Analytics track hit rates and optimization |

#### 18.1.2 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT REQUEST                                  │
│              (Library/Framework Question)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  KB-FIRST LOOKUP SYSTEM                          │
│                                                                  │
│  Step 1: Check KB Cache                                          │
│    ├─ Hit? → Return cached (0.12s avg)                          │
│    └─ Miss? → Step 2                                            │
│                                                                  │
│  Step 2: Fuzzy Match Lookup                                      │
│    ├─ Match Found? → Return fuzzy match                         │
│    └─ No Match? → Step 3                                        │
│                                                                  │
│  Step 3: Context7 API Call (via MCP)                            │
│    └─ Fetch fresh documentation                                  │
│                                                                  │
│  Step 4: Store in KB Cache                                       │
│    └─ Save for future use                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 18.2 KB-First Caching System

#### 18.2.1 Cache Structure

```
.tapps-agents/kb/context7-cache/
├── index.yaml                    # Master index of all cached docs
├── cross-references.yaml         # Topic cross-references
├── .refresh-queue               # Stale entry refresh queue
│
├── libraries/                    # Library-based sharding
│   ├── react/
│   │   ├── meta.yaml            # React library metadata
│   │   ├── hooks.md             # React hooks docs
│   │   ├── components.md        # React components docs
│   │   └── state-management.md  # React state docs
│   │
│   ├── fastapi/
│   │   ├── meta.yaml            # FastAPI metadata
│   │   ├── authentication.md    # FastAPI auth docs
│   │   └── routing.md           # FastAPI routing docs
│   │
│   └── [other libraries...]
│
└── topics/                       # Topic-based cross-referencing
    ├── hooks/
    │   └── index.yaml           # Hooks topic index
    └── routing/
        └── index.yaml           # Routing topic index
```

#### 18.2.2 KB Cache File Format

```markdown
# {library} - {topic}

**Source**: {context7_id} (Trust Score: {trust_score})
**Snippets**: {snippet_count} | **Tokens**: {token_count}
**Last Updated**: {last_updated} | **Cache Hits**: {cache_hits}

---

{context7_content}

---

<!-- KB Metadata -->
<!-- Library: {library} -->
<!-- Topic: {topic} -->
<!-- Context7 ID: {context7_id} -->
<!-- Trust Score: {trust_score} -->
<!-- Snippet Count: {snippet_count} -->
<!-- Last Updated: {last_updated} -->
<!-- Cache Hits: {cache_hits} -->
<!-- Token Count: {token_count} -->
```

#### 18.2.3 Fuzzy Matching

- **Confidence Threshold**: 0.7 (configurable)
- **Matching Strategy**:
  - Exact library match (highest priority)
  - Topic similarity (string similarity)
  - Cross-reference lookup
- **Fallback**: Context7 API if no match found

#### 18.2.4 Performance Targets

| Metric | Target | Current (BMAD) |
|--------|--------|----------------|
| **Hit Rate** | >70% | 87%+ |
| **Cached Response Time** | <0.15s | 0.12s avg |
| **Context7 API Time** | <2.0s | 1.5-2.0s |
| **KB Storage Time** | <0.5s | 0.3-0.5s |
| **Metadata Update Time** | <0.1s | <0.1s |

### 18.3 MCP Integration

#### 18.3.1 MCP Tools

**Library Resolution Tool:**
- **Tool Name**: `mcp_Context7_resolve-library-id`
- **Purpose**: Resolve library/package name to Context7-compatible ID
- **Parameters**: `libraryName` (string, required)
- **Returns**: List of matching libraries with Context7 IDs (`/org/project` format)

**Documentation Retrieval Tool:**
- **Tool Name**: `mcp_Context7_get-library-docs`
- **Purpose**: Fetch up-to-date documentation for a library
- **Parameters**:
  - `context7CompatibleLibraryID` (string, required)
  - `topic` (string, optional) - Focus documentation
  - `mode` (string, optional) - "code" (default) or "info"
  - `page` (integer, optional) - Pagination (1-10)
- **Returns**: Documentation content in markdown format

#### 18.3.2 KB-First Workflow (MANDATORY)

```yaml
kb_first_workflow:
  step_1_check_cache:
    action: "read_file"
    path: ".tapps-agents/kb/context7-cache/libraries/{library}/{topic}.md"
    on_hit:
      - extract_metadata_from_comments
      - update_hit_count_in_meta_yaml
      - update_last_accessed_timestamp
      - return_cached_content
      - log_performance: "cache_hit"
    on_miss:
      - proceed_to_fuzzy_match
  
  step_2_fuzzy_match:
    action: "search_kb_index"
    index_file: ".tapps-agents/kb/context7-cache/index.yaml"
    cross_refs_file: ".tapps-agents/kb/context7-cache/cross-references.yaml"
    confidence_threshold: 0.7
    on_match:
      - return_fuzzy_match_with_confidence
      - update_hit_count
    on_no_match:
      - proceed_to_context7_resolution
  
  step_3_resolve_library:
    check_kb_first: ".tapps-agents/kb/context7-cache/libraries/{library}/meta.yaml"
    on_found:
      - use_cached_context7_id
    on_not_found:
      - call_mcp_tool: "mcp_Context7_resolve-library-id"
      - store_result_in_kb
  
  step_4_context7_api:
    condition: "kb_cache_miss AND fuzzy_match_failed"
    tool: "mcp_Context7_get-library-docs"
    on_success:
      - proceed_to_kb_storage
  
  step_5_store_in_kb:
    steps:
      - create_directory: ".tapps-agents/kb/context7-cache/libraries/{library}"
      - write_content: ".tapps-agents/kb/context7-cache/libraries/{library}/{topic}.md"
      - update_metadata: "meta.yaml"
      - update_index: "index.yaml"
      - update_cross_refs: "cross-references.yaml"
```

### 18.4 Auto-Refresh System

#### 18.4.1 Staleness Detection

```yaml
staleness_policies:
  stable:
    max_age_days: 30
    examples: ["react", "pytest", "fastapi", "typescript"]
  
  active:
    max_age_days: 14
    examples: ["vitest", "playwright", "vite"]
  
  critical:
    max_age_days: 7
    examples: ["security-libs", "jwt", "oauth"]
```

#### 18.4.2 Refresh Modes

**Manual Refresh:**
```bash
*context7-kb-refresh                    # Refresh all stale entries
*context7-kb-refresh --check-only       # Check what needs refreshing
*context7-kb-refresh {library}          # Refresh specific library
```

**Automatic Refresh:**
- **Check on First Access**: Session-based staleness check
- **Queue System**: Background refresh queue
- **Process Queue**: `*context7-kb-process-queue` command

#### 18.4.3 Queue Management

```python
# Simple file-based queue
queue_file: ".tapps-agents/kb/context7-cache/.refresh-queue"

# Queue entry format
{library_name},{topic or 'all'},{queued_at_timestamp}

# Processing
- Silent processing on agent startup (if enabled)
- Manual processing via command
- Failed items remain in queue for retry
```

### 18.5 Performance Analytics

#### 18.5.1 Metrics Tracked

| Metric | Description | Target |
|--------|-------------|--------|
| **Hit Rate** | Cache hits / (hits + misses) | >70% |
| **Average Response Time** | Time to return documentation | <0.15s (cached) |
| **Cache Size** | Total KB cache size | <100MB (configurable) |
| **Total Entries** | Number of cached library/topic pairs | Tracked |
| **Top Libraries** | Most frequently accessed | Top 5 |
| **Top Topics** | Most frequently accessed topics | Top 5 |

#### 18.5.2 Status Command

```bash
*context7-kb-status
```

**Output Format:**
```markdown
# Context7 Knowledge Base Status

## Overview
- **Total Entries**: 45
- **Total Size**: 12.3MB / 100MB (12.3%)
- **Hit Rate**: 87.2%
- **Average Response Time**: 0.15s
- **Last Updated**: 2025-12-27T15:01:00Z

## Performance Metrics
- **Cache Hits**: 156
- **Cache Misses**: 23
- **Context7 Calls**: 23
- **Fuzzy Matches**: 12

## Top Libraries
1. **React** - 45 hits, 2.3MB
2. **Express** - 32 hits, 1.8MB
3. **MongoDB** - 28 hits, 1.2MB

## Recommendations
- ✅ **Hit Rate Excellent**: 87.2% exceeds target of 70%
- ✅ **Response Time Good**: 0.15s meets target
- ⚠️ **Size Growth**: Consider cleanup if approaching 80MB
```

### 18.6 Agent Integration

#### 18.6.1 Agent-Specific Configuration

```yaml
context7_agent_limits:
  architect:
    token_limit: 4000
    topics: ["architecture", "design-patterns", "scalability"]
    kb_priority: true
    context7_mandatory: true
  
  implementer:
    token_limit: 3000
    topics: ["hooks", "routing", "authentication", "testing"]
    kb_priority: true
    context7_mandatory: true
  
  tester:
    token_limit: 2500
    topics: ["testing", "security", "performance"]
    kb_priority: true
    context7_mandatory: true
```

#### 18.6.2 Auto-Triggers

Agents automatically use Context7 KB when:
- User mentions a library/framework name
- Discussing implementation patterns
- Making technology recommendations
- Troubleshooting library-specific issues
- User asks "how does [library] work?"

**Proactive Offer Pattern:**
> "Would you like me to check Context7 KB for current [library] best practices?"

#### 18.6.3 Integration with Existing RAG

**Priority Order:**
1. **Context7 KB** (for library/framework questions)
2. **Domain Knowledge Base** (for business domain questions)
3. **Context7 API** (if KB miss)

**Combined Usage:**
- Context7 for technical library documentation
- Domain KB for business logic and patterns
- Both can be used together for comprehensive answers

### 18.7 Configuration Schema

#### 18.7.1 Core Configuration

```yaml
# .tapps-agents/config.yaml

context7:
  enabled: true
  default_token_limit: 3000
  cache_duration: 3600
  integration_level: mandatory  # or "optional"
  usage_requirement: "MANDATORY for all technology decisions"
  bypass_forbidden: true
  
  knowledge_base:
    enabled: true
    location: ".tapps-agents/kb/context7-cache"
    sharding: true
    indexing: true
    cross_references: true
    max_cache_size: "100MB"
    cleanup_interval: 86400  # 24 hours
    hit_rate_threshold: 0.7
    fuzzy_match_threshold: 0.7
    analytics_enabled: true
    
    refresh:
      enabled: true
      default_max_age_days: 30
      check_on_access: true
      auto_queue: true
      notify_stale: true
      auto_process_on_startup: true
      auto_check_on_first_access: true
      
      library_types:
        stable:
          max_age_days: 30
          examples: ["react", "pytest", "fastapi", "typescript"]
        active:
          max_age_days: 14
          examples: ["vitest", "playwright", "vite"]
        critical:
          max_age_days: 7
          examples: ["security-libs", "jwt", "oauth"]
  
  agent_limits:
    architect:
      token_limit: 4000
      topics: ["architecture", "design-patterns", "scalability"]
      kb_priority: true
      context7_mandatory: true
      bypass_forbidden: true
    
    implementer:
      token_limit: 3000
      topics: ["hooks", "routing", "authentication", "testing"]
      kb_priority: true
      context7_mandatory: true
      bypass_forbidden: true
    
    tester:
      token_limit: 2500
      topics: ["testing", "security", "performance"]
      kb_priority: true
      context7_mandatory: true
      bypass_forbidden: true
```

#### 18.7.2 MCP Server Configuration

```yaml
# MCP server configuration (Cursor/Claude Desktop)
mcp_servers:
  context7:
    command: "npx"
    args:
      - "-y"
      - "@context7/mcp-server"
    env:
      CONTEXT7_API_KEY: "${CONTEXT7_API_KEY}"
```

### 18.8 Implementation Phases

**Current Status**: ✅ **Phase 3 Complete** - All phases implemented, testing in progress

#### ✅ Phase 1: Core Integration (Complete)

**Status**: ✅ **Complete** - All deliverables implemented and tested

**Deliverables:**
1. MCP Context7 tool integration
2. Basic KB cache structure
3. KB-first lookup workflow
4. Basic metadata tracking
5. Library resolution caching

**Success Criteria:**
- ✅ KB cache structure created
- ✅ MCP tools integrated
- ✅ KB-first workflow functional
- ✅ Basic caching working
- ✅ Metadata files updated

#### ✅ Phase 2: Intelligence Layer (Complete)

**Status**: ✅ **Complete** - All deliverables implemented and tested

**Deliverables:**
1. Fuzzy matching implementation
2. Auto-refresh system
3. Performance analytics
4. Agent-specific optimizations
5. Status and search commands

**Success Criteria:**
- ✅ Fuzzy matching with 0.7 threshold
- ✅ Staleness detection working
- ✅ Refresh queue functional
- ✅ Analytics dashboard complete
- ✅ Hit rate >70%

#### ✅ Phase 3: Advanced Features (Complete)

**Status**: ✅ **Complete** - All deliverables implemented; test fixtures need minor adjustments

**Deliverables:**
1. Cross-references system
2. Predictive pre-loading
3. Advanced analytics
4. KB cleanup automation
5. Integration with existing RAG

**Success Criteria:**
- ✅ Cross-references functional (CrossReferenceManager implemented)
- ✅ KB cleanup automation working (LRU, size-based, age-based cleanup)
- ✅ Advanced analytics dashboard (Analytics class with comprehensive metrics)
- ✅ Automated cleanup working (KBCleanup with multiple strategies)
- ✅ Agent integration complete (Context7AgentHelper integrated into Architect, Implementer, Tester agents)
- ✅ CLI commands implemented (8 commands: docs, resolve, status, search, refresh, cleanup, rebuild, help)
- ✅ Test suite created (66 tests for Phase 3 components)

**Additional Deliverables Completed:**
- ✅ CrossReferenceManager for topic-based relationships
- ✅ KBCleanup for automated cache management
- ✅ Context7AgentHelper for simplified agent integration
- ✅ Context7Commands for CLI interaction
- ✅ Integration into Architect, Implementer, and Tester agents

### 18.9 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `*context7-docs {library} {topic}` | Get KB-first documentation | `*context7-docs react hooks` |
| `*context7-resolve {library}` | Resolve library to Context7 ID | `*context7-resolve fastapi` |
| `*context7-kb-status` | Show KB statistics and analytics | `*context7-kb-status` |
| `*context7-kb-search {query}` | Search local knowledge base | `*context7-kb-search react` |
| `*context7-kb-test` | Test KB integration functionality | `*context7-kb-test` |
| `*context7-kb-refresh` | Refresh stale cache entries | `*context7-kb-refresh` |
| `*context7-kb-refresh --check-only` | Check what needs refreshing | `*context7-kb-refresh --check-only` |
| `*context7-kb-process-queue` | Process queued refreshes | `*context7-kb-process-queue` |
| `*context7-kb-cleanup` | Clean up old/unused cached docs | `*context7-kb-cleanup` |
| `*context7-kb-rebuild` | Rebuild knowledge base index | `*context7-kb-rebuild` |
| `*context7-help` | Show Context7 usage examples | `*context7-help` |

### 18.10 Integration with Existing Features

#### 18.10.1 Tiered Context Integration

- **Context7 KB** uses Tier 1 caching (fast, minimal tokens)
- **Context7 API** uses Tier 2-3 (when KB miss)
- **Combined**: Context7 docs + Tiered Context = optimal token usage

#### 18.10.2 Code Scoring Integration

- Context7 ensures accurate library API references
- Reduces false positives in security/complexity scoring
- Provides current best practices for code quality

#### 18.10.3 MCP Gateway Integration

- Context7 MCP tools accessible via MCP Gateway
- Unified tool routing and caching
- Consistent with other MCP server integrations

#### 18.10.4 Workflow Integration

- Context7 automatically used in technology selection steps
- Architect agent uses Context7 for design decisions
- Implementer agent uses Context7 for library implementation

### 18.11 Expected Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **API Calls** | 100% external | 13% external | 87% reduction |
| **Response Time** | 1.5-2.0s | 0.12s (cached) | 92% faster |
| **Documentation Accuracy** | Variable | Always current | 100% accuracy |
| **Hallucinated APIs** | Common | Rare | 90% reduction |
| **Cost per Query** | High | Low (cached) | 87% cost savings |

### 18.12 Migration Path

**For Existing Projects:**
1. Enable Context7 in configuration
2. Run `*context7-kb-refresh` to populate initial cache
3. Agents automatically use KB-first approach
4. Monitor `*context7-kb-status` for hit rates
5. Adjust refresh policies as needed

**For New Projects:**
1. Context7 enabled by default
2. KB cache populated on first library question
3. Auto-refresh keeps docs current
4. No manual intervention needed

---

## 19. Phase 6: Modern Quality Analysis Enhancements (2025 Standards)

**Status**: ✅ **COMPLETE** (December 2025) - All High and Medium Priority Improvements Implemented  
**Duration**: Completed in Q4 2025  
**Last Updated**: January 2026  
**Review Document**: See `implementation/PHASE6_STATUS.md` for completion details

**Prerequisites Met:**
- ✅ Phase 5 (Context7 Integration) complete (177/207 tests passing, production-ready)
- ✅ Current code scoring system provides solid foundation
- ✅ Reviewer Agent structure ready for extension
- ✅ Configuration system supports quality tools configuration
- ✅ All dependencies identified with 2025-standard versions

### 19.1 Overview

Phase 6 enhances the code quality analysis system with 2025 industry standards, modern tooling, and comprehensive reporting. This phase aligns TappsCodingAgents with current best practices for Python and TypeScript code analysis, dependency management, and multi-service quality assessment.

**Key Objectives:**
- Integrate modern 2025-standard tools (Ruff, mypy, jscpd)
- Extend quality analysis to TypeScript/JavaScript
- Add comprehensive reporting infrastructure
- Enable multi-service and project-wide analysis
- Integrate dependency security auditing
- Enhance cross-agent quality data sharing

### 19.2 High Priority Improvements

#### 19.2.1 Ruff Integration (Modern Python Linting)

**Agent**: **Reviewer Agent** (Primary), **Improver Agent** (Secondary)  
**Rating**: 5/5  
**Estimated Effort**: 1-2 weeks

**Description:**
Integrate Ruff as the primary Python linter, replacing slower legacy tools. Ruff is 10-100x faster than pylint and combines the functionality of flake8, black, and isort into a single tool.

**2025 Standards:**
- **Ruff Version**: `>=0.8.0,<1.0` (2025 standard)
- **Output Format**: JSON for programmatic parsing
- **Configuration**: `ruff.toml` or `pyproject.toml` support
- **Performance**: Sub-second linting for typical codebases

**Implementation Requirements:**

1. **Scoring Integration** (`tapps_agents/agents/reviewer/scoring.py`)
   - Add `_calculate_linting_score()` method using Ruff
   - Parse Ruff JSON output format
   - Calculate linting score (0-10 scale): `10 - (issues * 0.5)`
   - Support configurable Ruff configuration files

2. **Reviewer Agent Enhancement** (`tapps_agents/agents/reviewer/agent.py`)
   - Add `*lint` command for Ruff-only analysis
   - Include Ruff results in `*review` command output
   - Display Ruff issues in feedback

3. **Improver Agent Integration** (`tapps_agents/agents/improver/agent.py`)
   - Use Ruff results to suggest auto-fixes
   - Execute `ruff check --fix` when appropriate
   - Prioritize Ruff-suggested improvements

4. **Configuration** (`tapps_agents/core/config.py`)
   - Add `ruff_enabled: bool = True` to `QualityToolsConfig`
   - Add `ruff_config: Optional[str]` for custom config path
   - Support per-service Ruff configurations

**Success Criteria:**
- ✅ Ruff integrated into code scoring system
- ✅ Linting score calculated from Ruff JSON output
- ✅ Reviewer Agent `*lint` command functional
- ✅ Improver Agent uses Ruff for auto-fixes
- ✅ Configuration system supports Ruff settings
- ✅ 10-100x performance improvement over pylint
- ✅ Comprehensive test coverage (95%+)

**Dependencies:**
- `ruff>=0.8.0,<1.0` (add to `requirements.txt`)

---

#### 19.2.2 mypy Type Checking Integration

**Agent**: **Reviewer Agent** (Primary), **Improver Agent** (Secondary)  
**Rating**: 5/5  
**Estimated Effort**: 1-2 weeks

**Description:**
Integrate mypy for static type checking, providing type safety scores and identifying type errors in Python code.

**2025 Standards:**
- **mypy Version**: `>=1.13.0,<2.0` (2025 standard)
- **Mode**: Strict type checking enabled
- **Error Codes**: Show error codes for easy fixing
- **Configuration**: `mypy.ini` or `pyproject.toml` support

**Implementation Requirements:**

1. **Scoring Integration** (`tapps_agents/agents/reviewer/scoring.py`)
   - Add `_calculate_type_checking_score()` method
   - Parse mypy output with `--show-error-codes`
   - Calculate type safety score (0-10 scale): `10 - (errors * 0.5)`
   - Support mypy configuration files

2. **Reviewer Agent Enhancement** (`tapps_agents/agents/reviewer/agent.py`)
   - Add `*type-check` command for mypy-only analysis
   - Include type checking results in `*review` command
   - Display type errors with error codes

3. **Improver Agent Integration** (`tapps_agents/agents/improver/agent.py`)
   - Use mypy errors to suggest type annotations
   - Auto-fix simple type issues
   - Prioritize type safety improvements

4. **Configuration** (`tapps_agents/core/config.py`)
   - Add `mypy_enabled: bool = True` to `QualityToolsConfig`
   - Add `mypy_config: Optional[str]` for custom config path
   - Support strict mode configuration

**Success Criteria:**
- ✅ mypy integrated into code scoring system
- ✅ Type checking score calculated from mypy output
- ✅ Reviewer Agent `*type-check` command functional
- ✅ Improver Agent suggests type fixes
- ✅ Error codes displayed for all type errors
- ✅ Configuration system supports mypy settings
- ✅ Comprehensive test coverage (95%+)

**Dependencies:**
- `mypy>=1.13.0,<2.0` (add to `requirements.txt`)

---

#### 19.2.3 Comprehensive Reporting Infrastructure

**Agent**: **Reviewer Agent** (Primary), **Orchestrator Agent** (Secondary), **Documenter Agent** (Secondary)  
**Rating**: 5/5  
**Estimated Effort**: 2-3 weeks

**Description:**
Build a comprehensive reporting system that generates quality analysis reports in multiple formats (JSON, Markdown, HTML) with summary statistics, historical tracking, and trend analysis.

**2025 Standards:**
- **Report Formats**: JSON (CI/CD), Markdown (readable), HTML (interactive)
- **Output Location**: `reports/quality/` directory structure
- **Historical Tracking**: Time-series data for trend analysis
- **Thresholds**: Configurable quality gates per metric

**Implementation Requirements:**

1. **Report Generator** (`tapps_agents/agents/reviewer/report_generator.py`)
   - `generate_summary_report()`: Markdown summary with thresholds
   - `generate_json_report()`: Machine-readable JSON for CI/CD
   - `generate_html_report()`: Interactive HTML dashboard
   - `generate_historical_report()`: Trend analysis over time

2. **Report Structure**:
   ```
   reports/
   ├── quality/
   │   ├── SUMMARY.md                    # Human-readable summary
   │   ├── quality-report.json           # Machine-readable data
   │   ├── quality-dashboard.html        # Interactive dashboard
   │   ├── ruff-report.json              # Ruff linting results
   │   ├── mypy-report.json              # Type checking results
   │   ├── complexity-report.json        # Complexity analysis
   │   └── historical/                   # Time-series data
   │       └── 2025-12-*.json
   ├── duplication/
   │   └── jscpd-report.json            # Duplication analysis
   └── dependencies/
       ├── dependency-tree.txt          # pipdeptree output
       └── security-audit.json          # pip-audit results
   ```

3. **Reviewer Agent Enhancement** (`tapps_agents/agents/reviewer/agent.py`)
   - Add `*report` command to generate all report formats
   - Add `--format` option (json, markdown, html, all)
   - Add `--output-dir` option for custom output location

4. **Orchestrator Agent Integration** (`tapps_agents/agents/orchestrator/agent.py`)
   - Generate workflow-level quality reports
   - Aggregate quality scores across services
   - Create project-wide quality dashboards

5. **Documenter Agent Integration** (`tapps_agents/agents/documenter/agent.py`)
   - Generate quality documentation sections
   - Create quality trend reports
   - Include quality metrics in API documentation

**Success Criteria:**
- ✅ Multi-format reporting (JSON, Markdown, HTML)
- ✅ Summary reports with quality thresholds
- ✅ Historical tracking and trend analysis
- ✅ Interactive HTML dashboards
- ✅ CI/CD integration via JSON reports
- ✅ Comprehensive test coverage (90%+)

**Dependencies:**
- `jinja2>=3.1.0` (for HTML template rendering)
- `plotly>=5.18.0` (optional, for trend visualization)

---

### 19.3 Medium Priority Improvements

#### 19.3.1 Code Duplication Detection

**Agent**: **Reviewer Agent** (Primary), **Improver Agent** (Secondary)  
**Rating**: 4/5  
**Estimated Effort**: 1-2 weeks

**Description:**
Integrate jscpd (JavaScript Copy/Paste Detector) to detect code duplication across Python and TypeScript codebases, identifying opportunities for refactoring and shared utilities.

**2025 Standards:**
- **jscpd Version**: `>=3.5.0` (via npm, Python wrapper)
- **Threshold**: <3% duplication (configurable)
- **Min Lines**: 5 lines minimum for duplicate detection
- **Output Format**: JSON for programmatic parsing

**Implementation Requirements:**

1. **Scoring Integration** (`tapps_agents/agents/reviewer/scoring.py`)
   - Add `_calculate_duplication_score()` method
   - Parse jscpd JSON output
   - Calculate duplication score (0-10 scale): `10 - (duplication_pct / 10)`
   - Support Python and TypeScript analysis

2. **Reviewer Agent Enhancement** (`tapps_agents/agents/reviewer/agent.py`)
   - Add `*duplication` command for duplication analysis
   - Include duplication score in `*review` command
   - Display duplicate code blocks with locations

3. **Improver Agent Integration** (`tapps_agents/agents/improver/agent.py`)
   - Use duplication results to suggest refactoring
   - Identify opportunities for shared utilities
   - Prioritize high-duplication areas for improvement

4. **Configuration** (`tapps_agents/core/config.py`)
   - Add `jscpd_enabled: bool = True` to `QualityToolsConfig`
   - Add `duplication_threshold: float = 3.0` (percentage)
   - Add `min_duplication_lines: int = 5`

**Success Criteria:**
- ✅ jscpd integrated into code scoring system
- ✅ Duplication score calculated from jscpd output
- ✅ Reviewer Agent `*duplication` command functional
- ✅ Improver Agent suggests refactoring opportunities
- ✅ Support for Python and TypeScript
- ✅ Comprehensive test coverage (90%+)

**Dependencies:**
- `jscpd>=3.5.0` (via npm: `npm install -g jscpd`)
- Python wrapper or subprocess integration

---

#### 19.3.2 Multi-Service Analysis

**Agent**: **Reviewer Agent** (Primary), **Orchestrator Agent** (Secondary)  
**Rating**: 4/5  
**Estimated Effort**: 2-3 weeks

**Description:**
Extend Reviewer Agent to analyze entire projects or multiple services in batch, providing service-level aggregation, cross-service comparison, and project-wide quality dashboards.

**2025 Standards:**
- **Service Discovery**: Auto-detect services in `services/` directory
- **Parallel Analysis**: Concurrent analysis for performance
- **Aggregation**: Service-level and project-level metrics
- **Comparison**: Cross-service quality comparison

**Implementation Requirements:**

1. **Service Discovery** (`tapps_agents/agents/reviewer/service_discovery.py`)
   - Auto-detect services in project structure
   - Support common patterns (`services/*/`, `src/*/`, etc.)
   - Filter by service name patterns

2. **Batch Analysis** (`tapps_agents/agents/reviewer/agent.py`)
   - Add `*analyze-project` command
   - Add `*analyze-services` command with service list
   - Parallel analysis using `asyncio.gather()`
   - Progress reporting for large projects

3. **Aggregation** (`tapps_agents/agents/reviewer/aggregator.py`)
   - Service-level quality scores
   - Project-wide quality metrics
   - Cross-service comparison reports
   - Quality trend analysis per service

4. **Orchestrator Agent Integration** (`tapps_agents/agents/orchestrator/agent.py`)
   - Use project-wide analysis for workflow decisions
   - Service dependency quality tracking
   - Quality gate decisions based on service health

**Success Criteria:**
- ✅ Service auto-discovery functional
- ✅ Batch analysis with parallel processing
- ✅ Service-level and project-level aggregation
- ✅ Cross-service comparison reports
- ✅ Integration with Orchestrator Agent
- ✅ Comprehensive test coverage (90%+)

**Dependencies:**
- None (uses existing infrastructure)

---

#### 19.3.3 Dependency Analysis & Security Auditing

**Agent**: **Ops Agent** (Primary), **Reviewer Agent** (Secondary), **Orchestrator Agent** (Secondary)  
**Rating**: 4/5  
**Estimated Effort**: 2-3 weeks

**Description:**
Add comprehensive dependency analysis using pipdeptree (dependency tree visualization) and pip-audit (vulnerability scanning), tracking dependency health, identifying outdated packages, and reporting security vulnerabilities.

**2025 Standards:**
- **pip-audit Version**: `>=2.6.0` (2025 standard)
- **pipdeptree Version**: `>=2.5.0` (2025 standard)
- **Output Format**: JSON for programmatic parsing
- **Security Focus**: CVE tracking, vulnerability severity levels

**Implementation Requirements:**

1. **Dependency Analyzer** (`tapps_agents/agents/ops/dependency_analyzer.py`)
   - `analyze_dependencies()`: Full dependency analysis
   - `get_dependency_tree()`: Visualize dependency tree
   - `run_security_audit()`: Scan for vulnerabilities
   - `check_outdated()`: Identify outdated packages

2. **Ops Agent Enhancement** (`tapps_agents/agents/ops/agent.py`)
   - Add `*audit-dependencies` command
   - Add `*dependency-tree` command
   - Add `*check-vulnerabilities` command
   - Integrate with compliance checking

3. **Reviewer Agent Integration** (`tapps_agents/agents/reviewer/agent.py`)
   - Include dependency health in quality metrics
   - Report outdated/vulnerable packages
   - Enhance security score with dependency audit results

4. **Orchestrator Agent Integration** (`tapps_agents/agents/orchestrator/agent.py`)
   - Use dependency audit results for gate decisions
   - Block deployments with critical vulnerabilities
   - Track dependency health over time

5. **Configuration** (`tapps_agents/core/config.py`)
   - Add `pip_audit_enabled: bool = True` to `QualityToolsConfig`
   - Add `dependency_audit_threshold: str = "high"` (low/medium/high/critical)

**Success Criteria:**
- ✅ Dependency tree visualization functional
- ✅ Security vulnerability scanning working
- ✅ Outdated package detection
- ✅ Integration with Ops Agent compliance checks
- ✅ Reviewer Agent includes dependency health
- ✅ Orchestrator Agent uses audit for gate decisions
- ✅ Comprehensive test coverage (90%+)

**Dependencies:**
- `pip-audit>=2.6.0` (add to `requirements.txt`)
- `pipdeptree>=2.5.0` (add to `requirements.txt`)

---

#### 19.3.4 TypeScript & JavaScript Support

**Agent**: **Reviewer Agent** (Primary), **Implementer Agent** (Secondary), **Tester Agent** (Secondary)  
**Rating**: 4/5  
**Estimated Effort**: 3-4 weeks

**Description:**
Extend the scoring system to support TypeScript and JavaScript files, integrating ESLint for linting, TypeScript compiler (tsc) for type checking, and complexity analysis for frontend code.

**2025 Standards:**
- **TypeScript Version**: `>=5.6.0` (2025 standard)
- **ESLint Version**: `>=9.0.0` (2025 standard)
- **Strict Mode**: TypeScript strict mode enabled
- **ESLint Config**: Modern flat config format (ESLint 9+)

**Implementation Requirements:**

1. **TypeScript Scorer** (`tapps_agents/agents/reviewer/typescript_scorer.py`)
   - `score_file()`: Score TypeScript/JavaScript files
   - `_calculate_complexity()`: Complexity analysis for TS/JS
   - `_run_tsc()`: TypeScript compiler type checking
   - `_run_eslint()`: ESLint linting with complexity rules

2. **Reviewer Agent Enhancement** (`tapps_agents/agents/reviewer/agent.py`)
   - Auto-detect file type (`.ts`, `.tsx`, `.js`, `.jsx`)
   - Route to appropriate scorer (Python or TypeScript)
   - Support TypeScript in `*review` and `*score` commands

3. **Implementer Agent Integration** (`tapps_agents/agents/implementer/agent.py`)
   - Generate TypeScript code with quality checks
   - Ensure type safety during code generation
   - Use ESLint rules for code formatting

4. **Tester Agent Integration** (`tapps_agents/agents/tester/agent.py`)
   - Generate TypeScript tests
   - Use type information for test generation
   - Support Jest, Vitest, and other TS test frameworks

5. **Configuration** (`tapps_agents/core/config.py`)
   - Add `typescript_enabled: bool = True` to `QualityToolsConfig`
   - Add `eslint_config: Optional[str]` for custom ESLint config
   - Add `tsconfig_path: Optional[str]` for TypeScript config

**Success Criteria:**
- ✅ TypeScriptScorer class implemented
- ✅ ESLint integration functional
- ✅ TypeScript compiler type checking working
- ✅ Complexity analysis for TS/JS
- ✅ Implementer Agent generates quality TS code
- ✅ Tester Agent generates TS tests
- ✅ Comprehensive test coverage (90%+)

**Dependencies:**
- `typescript>=5.6.0` (via npm: `npm install -g typescript`)
- ESLint via npm (project-specific)
- Python subprocess integration for npm tools

---

#### 19.3.5 Agent Integration Enhancements

**Agent**: **Orchestrator Agent** (Primary), **Improver Agent** (Secondary), **Ops Agent** (Secondary), **Reviewer Agent** (Secondary), **Planner Agent** (Secondary)  
**Rating**: 4/5  
**Estimated Effort**: 2-3 weeks

**Description:**
Integrate quality analysis results across agents, enabling cross-agent data sharing, automated quality-based decisions, and coordinated quality improvements.

**2025 Standards:**
- **Data Sharing**: JSON-based quality data exchange
- **Event-Driven**: Quality events trigger agent actions
- **Coordination**: Orchestrator manages quality workflows
- **Automation**: Automated quality-based gate decisions

**Implementation Requirements:**

1. **Quality Data Exchange** (`tapps_agents/core/quality_data.py`)
   - `QualityMetrics` Pydantic model for structured data
   - Quality data serialization/deserialization
   - Quality event definitions

2. **Orchestrator Agent Enhancement** (`tapps_agents/agents/orchestrator/agent.py`)
   - Use quality scores for gate decisions
   - Coordinate quality improvements across agents
   - Aggregate quality data from multiple sources
   - Quality-based workflow routing

3. **Improver Agent Integration** (`tapps_agents/agents/improver/agent.py`)
   - Use duplication detection for refactoring suggestions
   - Prioritize improvements based on quality scores
   - Coordinate with Reviewer Agent for validation

4. **Ops Agent Integration** (`tapps_agents/agents/ops/agent.py`)
   - Use security audit results for compliance checks
   - Block deployments with quality issues
   - Track quality metrics for compliance reporting

5. **Planner Agent Integration** (`tapps_agents/agents/planner/agent.py`)
   - Consider quality metrics when planning stories
   - Include quality improvements in story planning
   - Estimate effort based on code quality

**Success Criteria:**
- ✅ Quality data exchange format defined
- ✅ Orchestrator Agent uses quality for gate decisions
- ✅ Improver Agent uses duplication results
- ✅ Ops Agent uses security audit results
- ✅ Planner Agent considers quality metrics
- ✅ Comprehensive test coverage (85%+)

**Dependencies:**
- None (uses existing infrastructure)

---

### 19.4 Configuration Enhancements

#### 19.4.1 Quality Tools Configuration

**Location**: `tapps_agents/core/config.py`  
**Estimated Effort**: 1 week

**Description:**
Extend the configuration system to support per-tool settings, enable/disable flags, custom rule sets, and per-service quality thresholds.

**Implementation Requirements:**

1. **QualityToolsConfig** (`tapps_agents/core/config.py`)
   ```python
   class QualityToolsConfig(BaseModel):
       """Configuration for quality analysis tools"""
       
       # Tool enable/disable flags
       ruff_enabled: bool = Field(default=True, description="Enable Ruff linting")
       mypy_enabled: bool = Field(default=True, description="Enable mypy type checking")
       pylint_enabled: bool = Field(default=False, description="Enable pylint (legacy)")
       jscpd_enabled: bool = Field(default=True, description="Enable duplication detection")
       bandit_enabled: bool = Field(default=True, description="Enable security scanning")
       pip_audit_enabled: bool = Field(default=True, description="Enable dependency security audit")
       typescript_enabled: bool = Field(default=True, description="Enable TypeScript analysis")
       
       # Tool-specific configurations
       ruff_config: Optional[str] = Field(default=None, description="Path to ruff.toml")
       mypy_config: Optional[str] = Field(default=None, description="Path to mypy.ini")
       eslint_config: Optional[str] = Field(default=None, description="Path to ESLint config")
       tsconfig_path: Optional[str] = Field(default=None, description="Path to tsconfig.json")
       
       # Quality thresholds
       duplication_threshold: float = Field(default=3.0, description="Max duplication percentage")
       min_duplication_lines: int = Field(default=5, description="Min lines for duplication")
       dependency_audit_threshold: str = Field(default="high", description="Min severity for blocking")
   ```

2. **Per-Service Configuration** (`tapps_agents/core/config.py`)
   - Support service-specific quality thresholds
   - Override global tool settings per service
   - Service-specific quality gate criteria

**Success Criteria:**
- ✅ QualityToolsConfig model implemented
- ✅ Per-service configuration support
- ✅ Tool enable/disable flags functional
- ✅ Custom config file paths supported
- ✅ Comprehensive test coverage (95%+)

---

### 19.5 Requirements Updates

#### 19.5.1 Dependencies

Update `requirements.txt` with 2025-standard versions:

```python
# Quality Analysis Tools (2025 Standards)
ruff>=0.8.0,<1.0          # Fast Python linter (10-100x faster than pylint)
mypy>=1.13.0,<2.0         # Type checking (strict mode)
pip-audit>=2.6.0          # Security audit for dependencies
pipdeptree>=2.5.0         # Dependency tree visualization

# Reporting
jinja2>=3.1.0             # HTML template rendering
plotly>=5.18.0            # Optional: Trend visualization

# Existing (keep current versions)
radon>=6.0.1              # Complexity analysis
bandit>=1.7.5             # Security analysis
coverage>=7.0.0           # Test coverage analysis
```

#### 19.5.2 npm Dependencies (for TypeScript support)

Create `package.json` or document npm requirements:

```json
{
  "devDependencies": {
    "typescript": ">=5.6.0",
    "eslint": ">=9.0.0",
    "jscpd": ">=3.5.0"
  }
}
```

---

### 19.6 Implementation Phases

**Current Status**: ✅ **Ready to Start** - Phase 5 complete, no blockers. All phases ready to begin implementation.

#### Phase 6.1: High Priority Core (4-5 weeks)

**Deliverables:**
1. Ruff integration (Reviewer Agent)
2. mypy integration (Reviewer Agent)
3. Reporting infrastructure (Reviewer Agent, Orchestrator Agent, Documenter Agent)

**Success Criteria:**
- ✅ Ruff linting functional in Reviewer Agent
- ✅ mypy type checking functional in Reviewer Agent
- ✅ Multi-format reporting (JSON, Markdown, HTML)
- ✅ Summary reports with quality thresholds
- ✅ Comprehensive test coverage (90%+)

#### Phase 6.2: Medium Priority Core (6-8 weeks)

**Deliverables:**
1. Code duplication detection (Reviewer Agent, Improver Agent)
2. Multi-service analysis (Reviewer Agent, Orchestrator Agent)
3. Dependency analysis (Ops Agent, Reviewer Agent, Orchestrator Agent)

**Success Criteria:**
- ✅ jscpd duplication detection functional
- ✅ Multi-service batch analysis working
- ✅ Dependency security auditing integrated
- ✅ Cross-agent quality data sharing
- ✅ Comprehensive test coverage (90%+)

#### Phase 6.3: Language Expansion (3-4 weeks)

**Deliverables:**
1. TypeScript/JavaScript support (Reviewer Agent, Implementer Agent, Tester Agent)
2. Agent integration enhancements (Orchestrator Agent, all secondary agents)

**Success Criteria:**
- ✅ TypeScriptScorer class implemented
- ✅ ESLint and tsc integration functional
- ✅ Cross-agent quality coordination working
- ✅ Comprehensive test coverage (90%+)

---

### 19.7 Expected Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Linting Speed** | 10-30s (pylint) | 0.1-1s (Ruff) | 10-100x faster |
| **Type Safety** | Heuristic only | Static analysis (mypy) | 100% type coverage |
| **Language Support** | Python only | Python + TypeScript | 2x coverage |
| **Reporting** | Basic JSON | Multi-format (JSON/MD/HTML) | 3x formats |
| **Service Analysis** | Single file | Multi-service batch | 10x scale |
| **Dependency Security** | Manual checks | Automated auditing | 100% automation |
| **Code Duplication** | Not detected | Automated detection | New capability |
| **Agent Coordination** | Isolated | Integrated | Cross-agent workflows |

---

### 19.8 Migration Path

**For Existing Projects:**
1. Update `requirements.txt` with new dependencies
2. Install npm packages for TypeScript support (if needed)
3. Configure quality tools in `config.yaml`
4. Run `*analyze-project` to establish baseline
5. Enable quality gates in workflows
6. Monitor quality trends over time

**For New Projects:**
1. Quality tools enabled by default
2. Auto-detection of project structure
3. Multi-language support auto-configured
4. Quality reports generated automatically
5. No manual intervention needed

---

## 20. Appendix

### 20.1 Glossary

| Term | Definition |
|------|------------|
| **MAL** | Model Abstraction Layer - Routes requests to appropriate models |
| **RAG** | Retrieval-Augmented Generation - Enhances LLM with external knowledge |
| **LoRA** | Low-Rank Adaptation - Efficient fine-tuning method |
| **Primary Expert** | Expert with 51% authority for a domain |
| **Workflow Agent** | Agent that executes SDLC tasks |
| **Industry Expert** | Business domain knowledge authority |
| **Agent Skill** | Claude Code format for agent definition |
| **Code Scoring** | Quantitative code quality metrics system |
| **Tiered Context** | Multi-level context caching for token optimization |
| **MCP Gateway** | Unified Model Context Protocol interface layer |
| **Greenfield** | New project workflow (no existing code) |
| **Brownfield** | Existing project workflow (adding to codebase) |
| **Quality Gate** | Automated checkpoint with pass/fail criteria |
| **Context Tier** | Level of context detail (1=core, 2=extended, 3=full) |
| **Star Commands** | Commands prefixed with `*` for namespace separation (`*help`, `*review`) |
| **Activation Instructions** | Standardized startup sequence for agent initialization |
| **Workflow Init** | Auto-detect project type and recommend workflow (`*workflow-init`) |
| **Conditional Steps** | Workflow steps that execute based on conditions |
| **Optional Steps** | Additional workflow steps user can request |
| **Context7** | Real-time library documentation service with KB caching |
| **KB-First** | Check local knowledge base cache before external API calls |
| **Fuzzy Matching** | Find similar topics when exact match not found (0.7 threshold) |
| **Auto-Refresh** | Automatic detection and refresh of stale cached documentation |
| **Hit Rate** | Percentage of cache hits vs total requests (target: >70%) |

### 20.2 Inspired By

| Project | Contribution |
|---------|--------------|
| **BMAD-METHOD** | Star-prefixed commands, activation instructions, scale-adaptive workflows, workflow conditions/notes, agent customization |
| **codefortify** | Code Scoring System, quantitative quality metrics |
| **HomeIQ (BMAD)** | Tiered Context Injection, YAML Workflows, Greenfield/Brownfield, document sharding, Context7 KB integration |
| **LocalMCP** | MCP Gateway architecture, local-first AI patterns |
| **agentforge-mcp** | MCP integration patterns, comprehensive tooling |
| **TappsHA** | Smart suggestions system |
| **AgentForge** | Agent-OS patterns, compliance checking, security |
| **Claude Code Skills** | Agent definition format |

### 20.3 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | Dec 2025 | Initial requirements document |
| 1.1.0-draft | Dec 2025 | Added Enhanced Features: Code Scoring, Tiered Context, MCP Gateway, YAML Workflows, Greenfield/Brownfield |
| 1.2.0-draft | Dec 2025 | Added BMAD-METHOD patterns: Star commands, activation instructions, workflow enhancements, scale-adaptive selection |
| 1.3.0-draft | Dec 2025 | Added Context7 Integration (Enhancement Phase): KB-first caching, MCP integration, auto-refresh, performance analytics |
| 1.4.0-draft | Dec 2025 | Added Phase 6: Modern Quality Analysis Enhancements (2025 Standards): Ruff, mypy, TypeScript support, comprehensive reporting, multi-service analysis |
| 1.5.0-draft | Dec 2025 | Updated Phase 5 status to Complete (177/207 tests passing, production-ready). Updated Phase 6 status to Ready to Start. Verified 2025 standards compliance (Ruff >=0.8.0, mypy >=1.13.0, TypeScript >=5.6.0, ESLint >=9.0.0, pip-audit >=2.6.0, pipdeptree >=2.5.0). See PHASE5_COMPLETION_REVIEW.md and PHASE6_REVIEW.md |

---

## Document Status

**Status**: Draft  
**Next Steps**: Review and iterate on requirements before implementation

---

*End of Document*

