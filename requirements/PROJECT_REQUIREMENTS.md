# TappsCodingAgents - Project Requirements Document

**Version:** 1.0.0-draft  
**Date:** December 2025  
**Status:** Design Phase

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
16. [Appendix](#16-appendix)

---

## 1. Executive Summary

### 1.1 What is TappsCodingAgents?

TappsCodingAgents is a **specification framework** for defining, configuring, and orchestrating coding agents. It provides:

- A standardized way to define agent capabilities and behaviors
- Support for business domain experts with weighted decision-making
- Hybrid model routing (local + cloud)
- Optional MCP (Model Context Protocol) integration
- RAG and fine-tuning capabilities for domain specialization

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
│  • N experts for N domains      │   │  • 18 fixed agents              │
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
| **Execution Layer** | Workflow Agents | SDLC task execution | 18 (fixed) |

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
| **Count** | N (based on domains) | 18 (fixed) |

---

## 5. Workflow Agents

### 5.1 Agent Inventory (18 Agents)

#### Planning Phase (3 Agents)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **analyst** | Requirements gathering + technical research | Read, Grep, Glob |
| **planner** | Create user stories + task breakdown | Read, Write, Grep, Glob |
| **estimator** | Estimate effort, complexity, risk | Read, Grep, Glob |

#### Design Phase (3 Agents)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **architect** | System + security architecture design | Read, Write, Grep, Glob |
| **designer** | API contracts + data models | Read, Write, Grep, Glob |
| **ui-designer** | UI/UX specifications + wireframes | Read, Write, Grep, Glob |

#### Development Phase (4 Agents)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **implementer** | Write production code | Read, Write, Edit, Grep, Glob, Bash |
| **refactorer** | Improve existing code structure | Read, Write, Edit, Grep, Glob |
| **debugger** | Investigate and fix bugs | Read, Write, Edit, Grep, Glob, Bash |
| **documenter** | Write documentation | Read, Write, Grep, Glob |

#### Quality Phase (3 Agents)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **reviewer** | Code review (read-only feedback) | Read, Grep, Glob |
| **analyzer** | Metrics, style, complexity analysis | Read, Grep, Glob |
| **enhancer** | Autonomous code improvement | Read, Write, Edit, Grep, Glob |

#### Testing Phase (2 Agents)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **test-writer** | Write unit + integration tests | Read, Write, Grep, Glob, Bash |
| **test-fixer** | Fix failing tests | Read, Write, Edit, Grep, Glob, Bash |

#### Security & Ops Phase (2 Agents)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **security-auditor** | Vulnerability scanning + compliance | Read, Grep, Glob |
| **deployment-engineer** | Deploy + infrastructure | Read, Write, Grep, Glob, Bash |

#### Orchestration (1 Agent)

| Agent | Purpose | Permissions |
|-------|---------|-------------|
| **orchestrator** | Coordinate workflows + gate decisions | Read, Grep, Glob |

### 5.2 Permission Matrix

```
                        Read  Write  Edit  Grep  Glob  Bash
─────────────────────────────────────────────────────────────
PLANNING
  analyst                ✅    ❌     ❌    ✅    ✅    ❌
  planner                ✅    ✅     ❌    ✅    ✅    ❌
  estimator              ✅    ❌     ❌    ✅    ✅    ❌

DESIGN
  architect              ✅    ✅     ❌    ✅    ✅    ❌
  designer               ✅    ✅     ❌    ✅    ✅    ❌
  ui-designer            ✅    ✅     ❌    ✅    ✅    ❌

DEVELOPMENT
  implementer            ✅    ✅     ✅    ✅    ✅    ✅
  refactorer             ✅    ✅     ✅    ✅    ✅    ❌
  debugger               ✅    ✅     ✅    ✅    ✅    ✅
  documenter             ✅    ✅     ❌    ✅    ✅    ❌

QUALITY
  reviewer               ✅    ❌     ❌    ✅    ✅    ❌
  analyzer               ✅    ❌     ❌    ✅    ✅    ❌
  enhancer               ✅    ✅     ✅    ✅    ✅    ❌

TESTING
  test-writer            ✅    ✅     ❌    ✅    ✅    ✅
  test-fixer             ✅    ✅     ✅    ✅    ✅    ✅

SECURITY & OPS
  security-auditor       ✅    ❌     ❌    ✅    ✅    ❌
  deployment-engineer    ✅    ✅     ❌    ✅    ✅    ✅

ORCHESTRATION
  orchestrator           ✅    ❌     ❌    ✅    ✅    ❌
```

### 5.3 Permission Summary

| Permission Type | Agents with Access | Count |
|-----------------|-------------------|-------|
| **Write + Edit** | implementer, refactorer, debugger, enhancer, test-fixer | 5 |
| **Write only** | planner, architect, designer, ui-designer, documenter, test-writer, deployment-engineer | 7 |
| **Read-only** | analyst, estimator, reviewer, analyzer, security-auditor, orchestrator | 6 |
| **Bash** | implementer, debugger, test-writer, test-fixer, deployment-engineer | 5 |

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
| **planner** | Breaking down domain-specific stories |
| **architect** | Designing domain-appropriate systems |
| **designer** | Creating domain-specific APIs/schemas |
| **implementer** | Writing domain-specific code |
| **reviewer** | Validating domain correctness |
| **debugger** | Diagnosing domain-specific issues |
| **test-writer** | Creating domain-appropriate tests |

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
| reviewer | local:qwen2.5-coder-14b | cloud:claude-sonnet-4 |
| debugger | local:deepseek-coder-6.7b | cloud:claude-sonnet-4 |
| test-writer | local:qwen2.5-coder-14b | cloud:claude-sonnet-4 |
| analyzer | local:qwen2.5-coder-7b | cloud:claude-sonnet-4 |
| documenter | local:qwen2.5-coder-7b | cloud:claude-sonnet-4 |

#### Cloud-Preferred Agents (Complex Tasks)

| Agent | Primary Model | Fallback |
|-------|---------------|----------|
| architect | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| designer | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| planner | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| orchestrator | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |
| enhancer | cloud:claude-sonnet-4 | local:qwen2.5-coder-14b |

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
│   │   ├── analyst/SKILL.md
│   │   ├── planner/SKILL.md
│   │   └── estimator/SKILL.md
│   │
│   ├── design/
│   │   ├── architect/SKILL.md
│   │   ├── designer/SKILL.md
│   │   └── ui-designer/SKILL.md
│   │
│   ├── development/
│   │   ├── implementer/SKILL.md
│   │   ├── refactorer/SKILL.md
│   │   ├── debugger/SKILL.md
│   │   └── documenter/SKILL.md
│   │
│   ├── quality/
│   │   ├── reviewer/SKILL.md
│   │   ├── analyzer/SKILL.md
│   │   └── enhancer/SKILL.md
│   │
│   ├── testing/
│   │   ├── test-writer/SKILL.md
│   │   └── test-fixer/SKILL.md
│   │
│   ├── security-ops/
│   │   ├── security-auditor/SKILL.md
│   │   └── deployment-engineer/SKILL.md
│   │
│   ├── orchestration/
│   │   └── orchestrator/SKILL.md
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

### 15.1 Feature Development Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   planner   │───▶│  architect  │───▶│  designer   │
│ (stories)   │    │ (design)    │    │ (contracts) │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                    ┌─────┴─────┐
                    ▼           ▼
              ┌──────────┐ ┌──────────┐
              │ expert(s)│ │ expert(s)│
              │ consult  │ │ consult  │
              └──────────┘ └──────────┘
                    │
                    ▼
            ┌─────────────┐
            │ implementer │
            │ (code)      │
            └──────┬──────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  reviewer   │ │ test-writer │ │ documenter  │
└─────────────┘ └─────────────┘ └─────────────┘
        │                 │
        └────────┬────────┘
                 ▼
         ┌─────────────┐
         │ orchestrator│
         │ (gate)      │
         └─────────────┘
```

### 15.2 Bug Fix Workflow

```
debugger → implementer → reviewer → test-fixer → orchestrator (gate)
```

### 15.3 Code Quality Improvement Workflow

```
analyzer → reviewer → enhancer → reviewer → orchestrator (gate)
           ↑                          │
           └──────────────────────────┘
              (loop until gate passes)
```

### 15.4 Security Review Workflow

```
security-auditor → expert (security domain) → implementer (fixes) → security-auditor (re-scan)
```

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|------|------------|
| **MAL** | Model Abstraction Layer - Routes requests to appropriate models |
| **RAG** | Retrieval-Augmented Generation - Enhances LLM with external knowledge |
| **LoRA** | Low-Rank Adaptation - Efficient fine-tuning method |
| **Primary Expert** | Expert with 51% authority for a domain |
| **Workflow Agent** | Agent that executes SDLC tasks |
| **Industry Expert** | Business domain knowledge authority |
| **Agent Skill** | Claude Code format for agent definition |

### 16.2 Inspired By

| Project | Contribution |
|---------|--------------|
| CodeFortify | Multi-agent architecture, quality scoring, self-improvement |
| AgentForge | Agent-OS patterns, compliance checking, security |
| TappMCP-Bridge | MCP integration patterns |
| Claude Code Skills | Agent definition format |

### 16.3 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | Dec 2025 | Initial requirements document |

---

## Document Status

**Status**: Draft  
**Next Steps**: Review and iterate on requirements before implementation

---

*End of Document*

