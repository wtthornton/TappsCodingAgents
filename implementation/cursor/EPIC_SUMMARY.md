# TappsCodingAgents Migration to 11-Agent Architecture - Epic Summary

**Version:** 1.1  
**Date:** December 14, 2025  
**Status:** Draft for Review

---

## Overview

This document provides a high-level summary of all epics required to migrate TappsCodingAgents from its current architecture to the new 11-agent hub-and-spoke architecture leveraging Cursor's cloud agent capabilities.

## 2025 Standards Baseline (applies to all epics)

- **Python baseline**: Python **3.13+** with modern typing and structured concurrency (`asyncio.TaskGroup`).
- **Project/tooling**: `pyproject.toml` as the source of truth; **ruff** for lint+format; **pytest** for tests; keep CI fast and reproducible (optionally via modern env tooling such as `uv`).
- **Contracts**: agent messaging and artifacts are **versioned** and **schema-validated** (avoid implicit JSON drift).
- **Reliability**: file-based messaging uses atomic writes, idempotent handlers, retries/backoff, and dead-letter/quarantine handling.
- **Observability**: structured logs with correlation IDs; trace context propagation; metrics for latency/success/retries/cache/token usage.
- **Security hygiene**: secret/PII redaction in logs/artifacts; dependency and secret scanning gates; no credential material in repo.

## Epic List

### Epic 1: Foundation & Orchestration Infrastructure
**Goal:** Establish core infrastructure for the new architecture, including git worktree management, orchestration agent, and file-based communication system.

**Key Deliverables:**
- Git worktree management system
- Workflow Orchestration Agent
- File-based inbox/outbox messaging (versioned, durable, dead-letter capable)
- YAML workflow parser
- Basic conflict resolution

**Estimated Duration:** 2 weeks (Phase 1)

---

### Epic 2: Core Agent Implementation
**Goal:** Implement all 11 specialized agents (5 background cloud + 5 foreground + 1 orchestrator) with Cursor cloud integration, enabling parallel execution.

**Key Deliverables:**
- 5 Background Cloud Agents (Quality, Testing, Docs, Ops, Context)
- 5 Foreground Agents (Code, Design, Review, Planning, Enhancement)
- Cursor cloud agent configuration
- Parallel execution (up to 8 agents)
- Agent contract tests / compatibility harness

**Estimated Duration:** 2 weeks (Phase 2)

---

### Epic 3: Expert Consultation Framework & RAG System
**Goal:** Implement business expert consultation framework with RAG system, enabling weighted decision-making from industry and technical experts.

**Key Deliverables:**
- Expert Registry system
- RAG system (chunking, embeddings, FAISS)
- Weighted decision-making (Primary 51%, Others 49%/(N-1))
- Expert consultation integration
- 2-3 initial industry experts

**Estimated Duration:** 2 weeks (Phase 3)

---

### Epic 4: Context7 RAG Integration & Cache Management
**Goal:** Integrate Context7 RAG system for technical knowledge caching, enabling 90%+ token savings on library documentation queries.

**Key Deliverables:**
- Context7 cache pre-population
- Library documentation caching (5+ libraries)
- Cache warming strategies
- Agent integration for library docs
- Cache statistics and monitoring

**Estimated Duration:** 1 week (Phase 4)

---

### Epic 5: YAML Workflow Orchestration Engine
**Goal:** Implement comprehensive YAML-based workflow orchestration engine with dependency resolution, parallel task execution, and workflow state management.

**Key Deliverables:**
- YAML workflow parser and validator
- Dependency graph resolver
- Parallel task execution engine
- Workflow state persistence
- 3-5 standard workflow templates

**Estimated Duration:** 1 week (Phase 5)

---

### Epic 6: Comprehensive Quality Assurance & Testing
**Goal:** Implement comprehensive quality assurance system with 5-metric code scoring, automated test generation, and coverage analysis.

**Key Deliverables:**
- 5-metric code scoring system
- Automated test generation (unit, integration, E2E)
- Coverage analysis and reporting
- Quality gates and thresholds
- Review Agent integration

**Estimated Duration:** 2 weeks (Phase 6)

---

### Epic 7: Documentation, Error Handling & Production Readiness
**Goal:** Complete production-ready system with comprehensive documentation, robust error handling, logging, and monitoring.

**Key Deliverables:**
- Comprehensive API documentation
- User guides and tutorials
- Robust error handling
- Structured logging + monitoring (correlation IDs, trace context, key metrics)
- Production deployment guides

**Estimated Duration:** 2 weeks (Phase 7)

---

## Epic Dependencies

```
Epic 1 (Foundation)
  └─> Epic 2 (Core Agents) - Requires orchestration infrastructure
      ├─> Epic 3 (Expert System) - Agents need expert consultation
      ├─> Epic 4 (Context7) - Agents need library docs
      └─> Epic 5 (Workflow Engine) - Uses agents from Epic 2
          └─> Epic 6 (Quality & Testing) - Workflows need quality gates
              └─> Epic 7 (Documentation & Polish) - Final production readiness
```

## Total Timeline

**Estimated Total Duration:** 12 weeks (aligned with design document roadmap)

- **Weeks 1-2:** Epic 1 (Foundation)
- **Weeks 3-4:** Epic 2 (Core Agents)
- **Weeks 5-6:** Epic 3 (Expert System)
- **Week 7:** Epic 4 (Context7)
- **Week 8:** Epic 5 (Workflow Engine)
- **Weeks 9-10:** Epic 6 (Quality & Testing)
- **Weeks 11-12:** Epic 7 (Documentation & Polish)

## Success Metrics

- **Performance:** 60% reduction in workflow completion time vs. sequential
- **Quality:** Code quality scores > 8.0/10 average
- **Coverage:** Test coverage > 80%
- **Efficiency:** 6-8 agents running simultaneously
- **Cache:** Context7 cache hit rate > 80%, 90%+ token savings
- **Expert System:** Knowledge retrieval < 2s

## Risk Assessment

**High Risk Areas:**
- Epic 1: Git worktree operations could corrupt repository
- Epic 2: Parallel execution could cause merge conflicts
- Epic 3: RAG system latency could block agents

**Mitigation Strategies:**
- Comprehensive testing at each epic
- Feature flags for gradual rollout
- Rollback plans for each epic
- Incremental integration with existing system

## Next Steps

1. Review and approve epic structure
2. Begin Epic 1 implementation
3. Set up development environment
4. Create proof-of-concept with 2-3 agents
5. Iterate based on real-world usage

---

**Epic Documents:**
- [Epic 1: Foundation & Orchestration Infrastructure](./EPIC_01_Foundation.md)
- [Epic 2: Core Agent Implementation](./EPIC_02_Core_Agents.md)
- [Epic 3: Expert Consultation Framework & RAG System](./EPIC_03_Expert_System.md)
- [Epic 4: Context7 RAG Integration & Cache Management](./EPIC_04_Context7_Integration.md)
- [Epic 5: YAML Workflow Orchestration Engine](./EPIC_05_Workflow_Engine.md)
- [Epic 6: Comprehensive Quality Assurance & Testing](./EPIC_06_Quality_Testing.md)
- [Epic 7: Documentation, Error Handling & Production Readiness](./EPIC_07_Documentation_Polish.md)
