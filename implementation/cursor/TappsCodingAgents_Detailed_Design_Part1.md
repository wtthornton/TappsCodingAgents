# TappsCodingAgents - Detailed Design Document
## Multi-Agent Architecture for Cursor Cloud Agents

**Version:** 2.0  
**Date:** December 14, 2025  
**Author:** Claude (Anthropic)  
**Status:** Recommended Architecture

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Agent Breakdown](#agent-breakdown)
4. [Communication Architecture](#communication-architecture)
5. [Business Expert System](#business-expert-system)
6. [RAG Implementation](#rag-implementation)
7. [Workflow Orchestration](#workflow-orchestration)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Infrastructure Requirements](#infrastructure-requirements)
10. [Success Metrics](#success-metrics)

---

## Executive Summary

### Purpose
This document provides a comprehensive design for restructuring TappsCodingAgents to leverage Cursor's cloud agent capabilities for maximum parallel execution, efficiency, and scalability.

### Key Goals
- **Maximize Parallelization:** Utilize Cursor's 8 parallel agent capacity
- **Optimize Resource Usage:** Offload heavy tasks to cloud agents
- **Maintain Quality:** Comprehensive quality checks and expert consultation
- **Enable Scalability:** Support projects from small to enterprise scale
- **Reduce Human Wait Time:** Parallel execution vs. sequential bottlenecks

### Architecture Highlights
- **11 Specialized Agents** organized into functional groups
- **Hub-and-Spoke + Layered Architecture** combining coordination with expertise
- **Git Worktree Isolation** preventing merge conflicts
- **Context7 RAG** for shared knowledge and library documentation
- **Expert Consultation Framework** with weighted decision-making
- **File-based Communication** with version control and audit trails

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION HUB                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Workflow Orchestration Agent                                 │  │
│  │  - Task routing & dependency management                       │  │
│  │  - Result aggregation & conflict resolution                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────┬────────┬────────┬────────┬────────┬────────┬────────┬─────────┘
     │        │        │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼        ▼        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PARALLEL EXECUTION LAYER                          │
│  Background Agents (Cloud):           Foreground Agents (Local):     │
│  ┌──────────┐ ┌──────────┐           ┌──────────┐ ┌──────────┐    │
│  │ Quality  │ │ Testing  │           │   Code   │ │  Design  │    │
│  │  Agent   │ │  Agent   │           │  Agent   │ │  Agent   │    │
│  └──────────┘ └──────────┘           └──────────┘ └──────────┘    │
│  ┌──────────┐ ┌──────────┐           ┌──────────┐ ┌──────────┐    │
│  │   Docs   │ │ Context  │           │  Review  │ │ Planning │    │
│  │  Agent   │ │  Agent   │           │  Agent   │ │  Agent   │    │
│  └──────────┘ └──────────┘           └──────────┘ └──────────┘    │
│  ┌──────────┐                         ┌──────────┐                  │
│  │   Ops    │                         │ Enhance  │                  │
│  │  Agent   │                         │  Agent   │                  │
│  └──────────┘                         └──────────┘                  │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Context7 RAG (Technical: FastAPI, pytest, etc.)             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Expert RAG (Business: Industry + 16 Built-in Experts)       │  │
│  │  - Weighted decision-making (Primary 51%, Others 49%/(N-1))  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                                │
│  Git Worktrees | MCP Gateway | Cursor Cloud (AWS Firecracker)      │
└─────────────────────────────────────────────────────────────────────┘
```

### Architecture Pattern: Hub-and-Spoke + Layered Specialists

**Why This Pattern:**
1. Matches existing TappsCodingAgents design (13 workflow agents + expert system)
2. Leverages Cursor's native capabilities (8 parallel agents, git worktrees)
3. Scales from small to enterprise projects
4. Separates concerns cleanly (execution vs. knowledge)
5. Enables parallel execution while maintaining coordination

---

## Agent Breakdown

### Summary Table

| # | Agent Name | Type | Execution | Priority | Runtime | Resources |
|---|-----------|------|-----------|----------|---------|-----------|
| 1 | **Orchestration** | Coordination | Always Running | Critical | Continuous | Low |
| 2 | **Quality & Analysis** | Analysis | Background Cloud | Medium | 2-10 min | Med CPU |
| 3 | **Testing & Coverage** | Execution | Background Cloud | High | 5-30 min | Med CPU/Mem |
| 4 | **Documentation** | Creation | Background Cloud | Low | 3-15 min | Low |
| 5 | **Code Generation** | Creation | Foreground | High | 5-20 min | Med |
| 6 | **Design & Architecture** | Planning | Foreground | High | 10-30 min | Med Mem |
| 7 | **Review & Improvement** | Analysis | Foreground | High | 3-15 min | Low CPU |
| 8 | **Operations & Deployment** | Config | Background Cloud | Medium | 5-20 min | Med CPU |
| 9 | **Context & Knowledge** | Support | Background Cloud | Medium | 1-5 min | Med Mem |
| 10 | **Planning & Analysis** | Planning | Foreground | High | 10-30 min | Low CPU |
| 11 | **Enhancement & Prompt** | Optimization | Foreground | Medium | 2-8 min | Med Mem |

### Parallel Execution Groups

**Group A (Simultaneous):**
- Quality Agent
- Testing Agent
- Documentation Agent
- Context Agent

**Group B (After Group A):**
- Review Agent (needs Quality results)
- Code Agent (needs Review approval)

**Group C (Final Stage):**
- Operations Agent (needs tested code)

**Always Running:**
- Orchestration Agent (coordinates all)
- Enhancement Agent (on-demand)

---

## Communication Architecture

### Primary Communication: Git Worktree + JSON Files

**File Structure:**
```
.tapps-agents/
├── state/                      # Shared state between agents
│   ├── quality_results.json
│   ├── test_results.json
│   ├── code_scores.json
│   ├── architecture.json
│   ├── feature_plan.json
│   └── workflow_state.json
├── messages/                   # Agent coordination
│   ├── inbox/                  # Orchestrator → Agents
│   │   ├── quality-001.json
│   │   └── testing-002.json
│   └── outbox/                 # Agents → Orchestrator
│       ├── quality-001.json
│       └── testing-002.json
└── reports/                    # Final outputs
    ├── quality/latest.html
    └── coverage/latest.html
```

**Worktree Strategy:**
```
main
├─→ worktree/orchestrator-main (orchestrator)
├─→ worktree/quality-001 (Quality Agent)
├─→ worktree/testing-002 (Testing Agent)
├─→ worktree/code-003 (Code Agent)
└─→ worktree/docs-004 (Docs Agent)
```

### Secondary Communication: Context7 + Expert RAG

**Context7 Structure:**
```
.tapps-agents/context7/
├── cache/
│   ├── fastapi/
│   │   ├── index.faiss
│   │   └── metadata.json
│   └── pytest/
└── stats/
    └── hit_rate.json
```

**Expert RAG Structure:**
```
.tapps-agents/experts/
├── industry/
│   └── healthcare/
│       ├── expert.yaml
│       ├── knowledge/
│       │   ├── compliance/hipaa.md
│       │   └── standards/hl7_fhir.md
│       └── rag/
│           ├── index.faiss
│           └── metadata.json
└── builtin/
    ├── security/
    └── performance/
```

---

## Business Expert System

### Expert Types

**Industry Experts (N configurable):**
- Business domain knowledge
- Compliance requirements
- Domain-specific patterns
- 1:1 mapping: N domains → N experts
- Weighted: Primary 51%, Others 49%/(N-1)

**Built-in Technical Experts (16 fixed):**
1. Security
2. Performance
3. Testing
4. Data Privacy
5. Accessibility
6. UX
7. Code Quality
8. Software Architecture
9. DevOps
10. Documentation
11. AI Frameworks
12. Observability
13. API Design
14. Cloud Infrastructure
15. Database
16. Agent Learning

### Expert Configuration Example

**`.tapps-agents/experts/industry/healthcare/expert.yaml`**
```yaml
expert:
  name: healthcare
  type: industry
  domain: "Healthcare and Medical Devices"
  primary: true                    # 51% weight
  
  capabilities:
    - hipaa_compliance
    - hl7_fhir_standards
    - patient_data_security
    
  knowledge:
    - file: compliance/hipaa.md
      topic: "HIPAA Security Rule"
      priority: high
      
  rag:
    enabled: true
    chunk_size: 512
    overlap: 50
    similarity_threshold: 0.7
    top_k: 5
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    
  triggers:
    keywords: [hipaa, phi, patient, medical]
    contexts: [healthcare_application, medical_records]
    file_patterns: ["**/patient*.py", "**/medical*.py"]
```

### Expert Consultation Flow

```python
# Design Agent consulting experts
async def design_payment_system(requirements):
    # 1. Identify relevant experts
    experts = [
        healthcare_expert (51% weight),
        fintech_expert (24.5% weight),
        security_expert (12.25% weight),
        performance_expert (12.25% weight)
    ]
    
    # 2. Query each expert in parallel
    recommendations = await asyncio.gather(*[
        expert.consult(requirements)
        for expert in experts
    ])
    
    # 3. Weighted decision
    final = weighted_decision(recommendations)
    
    return generate_architecture(final)
```

### Creating New Experts

**Method 1: CLI**
```bash
tapps-agents expert create \
  --name retail \
  --type industry \
  --primary \
  --capabilities "inventory,pos"
```

**Method 2: Manual YAML**
```bash
mkdir -p .tapps-agents/experts/industry/retail/knowledge
# Create expert.yaml, add knowledge files
tapps-agents rag build --expert retail
```

**Method 3: Interactive Wizard**
```bash
tapps-agents enhance --setup-experts
# Interactive prompts for domain, capabilities, etc.
```

---

## RAG Implementation

### RAG Architecture

**Two RAG Systems:**
1. **Context7 RAG** - Technical knowledge (libraries, patterns)
2. **Expert RAG** - Business knowledge (industry experts)

### Loading Knowledge into RAG

**Method 1: Manual Files**
```bash
# 1. Create knowledge files
mkdir -p .tapps-agents/experts/industry/healthcare/knowledge/compliance
cat > .tapps-agents/experts/industry/healthcare/knowledge/compliance/hipaa.md << 'EOF'
# HIPAA Security Rule
...content...
EOF

# 2. Build RAG index
tapps-agents rag build --expert healthcare
```

**Method 2: CLI Import**
```bash
# From directory
tapps-agents rag import \
  --expert healthcare \
  --source ./docs/ \
  --file-pattern "*.md"

# From URL
tapps-agents rag import \
  --expert healthcare \
  --url https://www.hhs.gov/hipaa/

# From Git repo
tapps-agents rag import \
  --expert healthcare \
  --git-repo https://github.com/HL7/fhir \
  --git-path docs/
```

**Method 3: Programmatic**
```python
from tapps_agents.rag import DocumentLoader, RAGIndexer

loader = DocumentLoader()
indexer = RAGIndexer()

# Load and index
documents = loader.load_directory("./knowledge")
chunks = indexer.chunk_documents(documents, chunk_size=512)
embeddings = indexer.generate_embeddings(chunks)
index = indexer.build_index(embeddings)
indexer.save(index, path="./rag/")
```

### RAG Query Example

```python
from tapps_agents.experts import ExpertRegistry

expert = ExpertRegistry().get("healthcare")

results = expert.retrieve_knowledge(
    query="HIPAA encryption requirements",
    top_k=5
)

# Results:
[
    {
        "content": "HIPAA requires encryption of ePHI...",
        "similarity": 0.89,
        "source": "compliance/hipaa.md"
    },
    ...
]
```

### Context7 Pre-population

```bash
tapps-agents context7 populate \
  --libraries fastapi,pytest,pydantic \
  --force-refresh

# Output:
# ✓ Cache populated: 2,847 chunks
# ✓ Token savings estimate: 92%
```

---

## Workflow Orchestration

### YAML Workflow Example

**`.tapps-agents/workflows/feature-implementation.yaml`**
```yaml
workflow:
  name: feature-implementation
  description: "Complete feature implementation workflow"
  
  steps:
    - name: planning
      agent: planning-agent
      execution: foreground
      timeout: 1800
      
    - name: design
      agent: design-agent
      execution: foreground
      depends_on: [planning]
      
    - name: parallel_development
      type: parallel
      depends_on: [design]
      tasks:
        - name: code
          agent: code-agent
          worktree: code-001
          
        - name: tests
          agent: testing-agent
          worktree: testing-001
          
        - name: docs
          agent: docs-agent
          worktree: docs-001
    
    - name: quality
      agent: quality-agent
      depends_on: [parallel_development.code]
      
    - name: review
      agent: review-agent
      depends_on: [quality, parallel_development.tests]
      
    - name: finalize
      agent: orchestrator
      depends_on: [review]
      actions:
        - merge_worktrees
        - create_pull_request
```

### Workflow Execution

```bash
# Run workflow
tapps-agents workflow run \
  --workflow feature-implementation \
  --input feature_description="User authentication"

# Monitor progress
tapps-agents workflow status --id workflow-12345

# Output:
# ✓ planning (8m 23s)
# ✓ design (15m 45s)
# ⟳ parallel_development (67% complete)
# ⏸ quality (waiting)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Core infrastructure and orchestration

**Tasks:**
1. Git worktree management
2. Orchestrator Agent implementation
3. Communication infrastructure (inbox/outbox)
4. YAML workflow parser

**Deliverables:**
- Working orchestrator with 2-3 agents
- Git worktree automation
- Basic workflow execution

**Success Criteria:**
- 2 agents run in parallel
- Worktrees auto-created/cleaned
- Simple workflow completes end-to-end

---

### Phase 2: Core Agents (Weeks 3-4)

**Goal:** Implement all 11 agents

**Tasks:**
1. Background agents (Quality, Testing, Docs, Ops, Context)
2. Foreground agents (Code, Design, Review, Planning, Enhancement)
3. Cursor integration
4. Agent communication testing

**Deliverables:**
- All 11 agents implemented
- Cursor cloud agents configured
- Parallel execution working

**Success Criteria:**
- 8 agents run in parallel
- Results properly aggregated
- No merge conflicts

---

### Phase 3: Expert System (Weeks 5-6)

**Goal:** Business expert consultation framework

**Tasks:**
1. Expert Registry implementation
2. RAG system (chunking, embeddings, FAISS)
3. Create 2-3 initial industry experts
4. Integrate expert consultation into agents

**Deliverables:**
- Working expert system with RAG
- 2-3 industry experts configured
- Expert consultation in Design/Code agents

**Success Criteria:**
- Experts queryable
- Weighted recommendations work
- Knowledge retrieval < 2s

---

### Phase 4: Context7 Integration (Week 7)

**Goal:** Technical knowledge caching

**Tasks:**
1. Context7 cache implementation
2. Library documentation pre-population
3. Cache warming strategies
4. Integration with all agents

**Deliverables:**
- Context7 operational
- 5+ libraries cached
- 90%+ token savings

**Success Criteria:**
- Cache hit rate > 80%
- Query latency < 1s
- Token usage reduced 90%+

---

### Phase 5: Workflow Engine (Week 8)

**Goal:** YAML-based workflow orchestration

**Tasks:**
1. YAML parser and validator
2. Dependency graph resolver
3. Parallel task execution
4. Workflow state management

**Deliverables:**
- 3-5 standard workflows
- Workflow execution engine
- Progress monitoring

**Success Criteria:**
- Complex workflows execute
- Dependencies respected
- State persists across runs

---

### Phase 6: Quality & Testing (Weeks 9-10)

**Goal:** Comprehensive quality assurance

**Tasks:**
1. Code scoring system (5 metrics)
2. Quality tools integration (Ruff, mypy, Bandit)
3. Test generation and execution
4. Coverage reporting

**Deliverables:**
- Quality Agent fully functional
- Testing Agent operational
- Review Agent with scoring

**Success Criteria:**
- Quality score accurate
- Tests auto-generated
- Coverage > 80% target

---

### Phase 7: Documentation & Polish (Weeks 11-12)

**Goal:** Production-ready system

**Tasks:**
1. Documentation Agent implementation
2. Error handling improvements
3. Logging and monitoring
4. User documentation

**Deliverables:**
- Complete documentation
- Error handling robust
- Monitoring dashboards
- User guides

**Success Criteria:**
- All features documented
- Error recovery works
- Monitoring operational

---

## Infrastructure Requirements

### Hardware Requirements

**Development Machine (Minimum):**
- CPU: 4 cores (Intel i5 or equivalent)
- RAM: 16 GB
- Storage: 50 GB SSD
- Network: Stable internet (for cloud agents)

**Recommended:**
- CPU: 8+ cores (Intel i7/i9 or AMD Ryzen 7/9)
- RAM: 32 GB
- Storage: 256 GB NVMe SSD
- Network: High-speed internet (100+ Mbps)

**For NUC/Low-Power:**
- Follow NUC optimization guide
- Use Background Cloud Agents extensively
- Limit parallel foreground agents to 2-3

### Software Requirements

**Essential:**
- Cursor IDE (latest version)
- Cursor Pro subscription ($20/month for Background Agents)
- Git 2.30+
- Python 3.13+
- Node.js 18+ (for TypeScript projects)

**Optional:**
- Docker (for containerized workflows)
- Redis (for caching)
- PostgreSQL (for analytics)

### Cloud Resources

**Cursor Cloud Agents:**
- Included with Cursor Pro
- AWS Firecracker microVMs
- Ubuntu-based environments
- Automatic resource management

**Estimated Costs:**
- Cursor Pro: $20/month
- No additional cloud costs (handled by Cursor)

---

## Success Metrics

### Performance Metrics

**Time Savings:**
- Target: 60% reduction vs. sequential execution
- Measure: Workflow completion time
- Baseline: Sequential SDLC (planning → design → code → test → review)
- Goal: Parallel execution (planning → design → [code + tests + docs])

**Parallelization Efficiency:**
- Target: 6-8 agents running simultaneously
- Measure: Average concurrent agents
- Goal: Maximize use of Cursor's 8-agent limit

**Cache Hit Rate:**
- Context7: > 80% hit rate
- Expert RAG: > 70% hit rate
- Measure: Query cache hits / total queries

### Quality Metrics

**Code Quality Scores:**
- Overall: > 8.0/10 average
- Security: > 8.5/10 (critical)
- Test Coverage: > 80%

**Expert Consultation:**
- Expert recommendations used: > 90%
- Weighted decision confidence: > 0.75

**Workflow Success Rate:**
- Completed workflows: > 95%
- Failed workflows requiring retry: < 5%

### Developer Experience Metrics

**Developer Satisfaction:**
- Agent usefulness rating: > 4/5
- Time saved perception: > 50%
- Would recommend: > 80%

**Adoption Metrics:**
- Active agents per developer: > 5
- Workflows run per week: > 10
- Background agent usage: > 60%

---

## Conclusion

This detailed design provides a comprehensive roadmap for restructuring TappsCodingAgents to leverage Cursor's cloud agent capabilities. The Hub-and-Spoke + Layered Architecture combines:

1. **Parallel Execution** - 8 agents simultaneously
2. **Expert Consultation** - Weighted domain knowledge
3. **Quality Assurance** - Comprehensive scoring
4. **Workflow Orchestration** - YAML-based automation
5. **Knowledge Management** - Context7 + Expert RAG

**Next Steps:**
1. Review and approve this design
2. Begin Phase 1 implementation
3. Set up development environment
4. Create initial 2-3 agents for proof-of-concept
5. Iterate based on real-world usage

**Expected Outcomes:**
- 60% faster development cycles
- Higher code quality (8.0+ scores)
- Better domain expertise integration
- Scalable from small to enterprise projects

---

*End of Document Part 1*

**See Part 2 for:**
- Detailed agent specifications
- Communication protocol examples
- Expert consultation code samples
- Workflow execution examples
- Troubleshooting guide
