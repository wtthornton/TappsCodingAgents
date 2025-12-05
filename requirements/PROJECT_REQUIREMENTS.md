# TappsCodingAgents - Project Requirements Document

**Version:** 1.2.0-draft  
**Date:** December 2025  
**Status:** Design Phase (BMAD-METHOD Patterns Added)

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
18. [Appendix](#18-appendix)

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
                        Read  Write  Edit  Grep  Glob  Bash
─────────────────────────────────────────────────────────────
PLANNING
  analyst                ✅    ❌     ❌    ✅    ✅    ❌
  planner                ✅    ✅     ❌    ✅    ✅    ❌

DESIGN
  architect              ✅    ✅     ❌    ✅    ✅    ❌
  designer               ✅    ✅     ❌    ✅    ✅    ❌

DEVELOPMENT
  implementer            ✅    ✅     ✅    ✅    ✅    ✅
  debugger               ✅    ✅     ✅    ✅    ✅    ✅
  documenter             ✅    ✅     ❌    ✅    ✅    ❌

QUALITY
  reviewer               ✅    ❌     ❌    ✅    ✅    ❌
  improver               ✅    ✅     ✅    ✅    ✅    ❌

TESTING
  tester                 ✅    ✅     ✅    ✅    ✅    ✅

OPERATIONS
  ops                    ✅    ✅     ❌    ✅    ✅    ✅

ORCHESTRATION
  orchestrator           ✅    ❌     ❌    ✅    ✅    ❌
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

### 6.4 Expert Inheritance

```
┌─────────────────────┐
│    base-expert      │
│                     │
│ • Shared knowledge  │
│ • Core capabilities │
│ • Base behaviors    │
└─────────┬───────────┘
          │
          │ extends
          │
    ┌─────┴─────┬─────────────┐
    ▼           ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐
│Expert A│  │Expert B│  │Expert C│
│        │  │        │  │        │
│+Domain │  │+Domain │  │+Domain │
│ RAG    │  │ RAG    │  │ RAG    │
│+Fine-  │  │+Fine-  │  │+Fine-  │
│ tuning │  │ tuning │  │ tuning │
└────────┘  └────────┘  └────────┘
```

### 6.5 Base Expert Definition

```yaml
base-expert:
  shared_knowledge:
    - Project context
    - Coding standards
    - Architecture patterns
    - Business terminology
    
  shared_capabilities:
    - RAG integration
    - Confidence scoring
    - Influence weighting
    - Consultation interface
    
  shared_behaviors:
    - Always cite sources
    - Acknowledge uncertainty
    - Defer to primary expert
    - Provide influence not override
```

### 6.6 Consultation Flow

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
├── knowledge/                          # RAG knowledge base templates
│   └── templates/
│       └── domain-template/
│
├── adapters/                           # Fine-tuning adapter templates
│   └── templates/
│
├── config/                             # Configuration templates
│   ├── rag_config.yaml
│   ├── fine_tuning_config.yaml
│   └── project_config.yaml
│
└── templates/                          # Project templates
    ├── domains.md.template
    └── project-setup.md
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
│   ├── domains.md                      # Business domains (owner-provided)
│   ├── expert_weights.yaml             # Auto-generated weights
│   ├── model_profiles.yaml             # Model configuration
│   └── rag_config.yaml                 # RAG configuration
│
├── knowledge/                          # Project knowledge bases
│   ├── domain-1/
│   │   ├── docs/
│   │   └── patterns/
│   └── domain-2/
│
└── adapters/                           # Project-specific adapters
    ├── domain-1-lora/
    └── domain-2-lora/
```

---

## 14. Configuration Schemas

### 14.1 Project Configuration

```yaml
# project_config.yaml

project:
  name: "Project Name"
  description: "Project description"
  
domains_file: "./domains.md"

model_defaults:
  local_provider: "ollama"
  cloud_provider: "anthropic"
  
workflow_agents:
  enabled: all  # or list specific agents
  
expert_agents:
  auto_generate: true  # Generate from domains.md
  
rag:
  enabled: true
  vector_db: "chromadb"
  
fine_tuning:
  enabled: true
  method: "lora"
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

## 18. Appendix

### 18.1 Glossary

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

### 18.2 Inspired By

| Project | Contribution |
|---------|--------------|
| **BMAD-METHOD** | Star-prefixed commands, activation instructions, scale-adaptive workflows, workflow conditions/notes, agent customization |
| **codefortify** | Code Scoring System, quantitative quality metrics |
| **HomeIQ (BMAD)** | Tiered Context Injection, YAML Workflows, Greenfield/Brownfield, document sharding |
| **LocalMCP** | MCP Gateway architecture, local-first AI patterns |
| **agentforge-mcp** | MCP integration patterns, comprehensive tooling |
| **TappsHA** | Smart suggestions system |
| **AgentForge** | Agent-OS patterns, compliance checking, security |
| **Claude Code Skills** | Agent definition format |

### 18.3 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | Dec 2025 | Initial requirements document |
| 1.1.0-draft | Dec 2025 | Added Enhanced Features: Code Scoring, Tiered Context, MCP Gateway, YAML Workflows, Greenfield/Brownfield |
| 1.2.0-draft | Dec 2025 | Added BMAD-METHOD patterns: Star commands, activation instructions, workflow enhancements, scale-adaptive selection |

---

## Document Status

**Status**: Draft  
**Next Steps**: Review and iterate on requirements before implementation

---

*End of Document*

