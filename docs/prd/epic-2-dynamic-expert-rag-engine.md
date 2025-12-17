# Epic 2: Dynamic Expert & RAG Engine

## Epic Goal

Create an always-on Dynamic Knowledge/Expert Orchestrator that automatically detects project domains, creates and curates experts/knowledge for the current project, and continuously enriches agents with the best available, project-relevant information. This engine enables automatic expert creation, auto-filling RAG from multiple sources, and quality improvement through observability.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has built-in technical experts, config-defined experts (`.tapps-agents/experts.yaml`), RAG backends (VectorKnowledgeBase/SimpleKnowledgeBase), Context7 KB cache integration, and Unified Cache
- **Technology stack**: Python 3.13+, existing expert registry (`ExpertRegistry.from_config_file`), RAG backends, Context7 helper, Unified Cache
- **Integration points**: 
  - Existing expert registry and built-in expert system
  - RAG backends (VectorKnowledgeBase with FAISS, SimpleKnowledgeBase fallback)
  - Context7 KB cache and helper utilities
  - Unified Cache (tiered context + Context7 KB + RAG knowledge)
  - Project profile system (`.tapps-agents/project-profile.yaml`)

### Enhancement Details

- **What's being added/changed**: 
  - Expert Engine runtime component that orchestrates expert consultation and knowledge retrieval
  - Domain/Stack Detector that maps repo signals to expert domains
  - Expert Synthesizer that automatically creates/updates `.tapps-agents/domains.md` and `.tapps-agents/experts.yaml`
  - Knowledge Ingestion pipeline that populates project KB from multiple sources
  - Governance layer (do-not-index filters, prompt-injection handling, retention policies, approval mode)
  - Observability and quality improvement loop (metrics, KB maintenance job)

- **How it integrates**: 
  - Expert Engine integrates with existing expert registry and RAG backends
  - Domain detector uses project profile and repo signals (already available)
  - Expert Synthesizer writes to existing expert config format
  - Knowledge Ingestion uses existing RAG backends and Context7 KB cache
  - Governance layer protects existing knowledge stores
  - Observability extends existing metrics infrastructure

- **Success criteria**: 
  - Expert Engine automatically detects relevant domains and routes to appropriate experts
  - Expert Synthesizer successfully creates project-specific experts from signals
  - Knowledge Ingestion populates KB from project sources, Context7, and operational sources
  - Governance prevents secrets/PII from entering KB
  - Observability metrics enable quality improvement
  - KB maintenance job identifies and improves weak areas

## Stories

1. **Story 2.1: Expert Engine Runtime Component**
   - Implement Expert Engine orchestrator that detects domain knowledge needs
   - Create expert routing plan generation (which domains to consult for each step)
   - Implement knowledge retrieval plan (what to fetch from Context7 vs local KB)
   - Add controlled knowledge writes (new KB entries for project)
   - Create metrics collection (cache hit rate, retrieval quality, confidence trends)
   - Acceptance criteria: Engine detects knowledge needs, routes to correct experts, retrieves from appropriate sources, writes knowledge safely, collects metrics

2. **Story 2.2: Domain/Stack Detector**
   - Implement detector that maps repo signals to expert domains
   - Add detection for: dependency manifests, config files, build tooling, service boundaries, file extensions, directory structure, CI workflow files
   - Create domain mapping logic (repo signals → technical domains: security/performance/testing/observability/etc.)
   - Integrate with project profile system
   - Acceptance criteria: Detector correctly identifies project stack, maps to appropriate domains, integrates with project profile

3. **Story 2.3: Expert Synthesizer (Automatic Expert Creation)**
   - Implement automatic creation of config-only experts (`.tapps-agents/experts.yaml`)
   - Create knowledge skeleton generator (`.tapps-agents/knowledge/<domain>/` with overview.md, glossary.md, decisions.md, pitfalls.md, constraints.md)
   - Add automatic detection of technical experts (framework-controlled) vs project/business experts (project-controlled)
   - Implement expert creation from signals (not manual wizards)
   - Acceptance criteria: Synthesizer creates experts from signals, generates knowledge skeletons, distinguishes technical vs project experts, writes valid config files

4. **Story 2.4: Knowledge Ingestion Pipeline**
   - Implement ingestion from project sources (requirements, architecture docs, ADRs, runbooks, prior SDLC reports, lessons learned)
   - Add Context7 integration for dependency sources (auto-fetch when library detected: overview + patterns + pitfalls + security notes)
   - Implement operational source ingestion (CI failures, runtime exceptions, monitoring alerts → known issues KB entries)
   - Create knowledge distillation (Context7 docs → project KB as "how we use X here" notes)
   - Acceptance criteria: Pipeline ingests from all sources, Context7 integration works, operational sources converted to KB entries, knowledge properly structured

5. **Story 2.5: Governance & Safety Layer**
   - Implement do-not-index filters (secrets, tokens, credentials, PII)
   - Add prompt-injection handling (retrieved text treated as untrusted, labeled with sources)
   - Create retention & scope policies (project-local KB remains local, avoid committing runtime state)
   - Implement human approval mode (optional: new experts/KB entries require approval before writing)
   - Acceptance criteria: Filters prevent secrets/PII indexing, prompt-injection handled safely, retention policies enforced, approval mode works when enabled

6. **Story 2.6: Observability & Quality Improvement Loop**
   - Extend metrics: expert consultation (confidence, agreement_level, rag_quality, threshold meet rate), Context7 KB (hit rate, latency), RAG KB (retrieval hit rate, top low-quality queries)
   - Implement scheduled KB maintenance job
   - Add weak area identification (low rag_quality detection)
   - Create KB addition proposals (templates to improve retrieval)
   - Acceptance criteria: All metrics collected, maintenance job runs, weak areas identified, improvement proposals generated

## Compatibility Requirements

- [ ] Existing expert registry and config format remain compatible
- [ ] RAG backends continue to work with enhanced ingestion
- [ ] Context7 KB cache integration enhanced, not replaced
- [ ] Unified Cache interface remains compatible
- [ ] Project profile format unchanged
- [ ] Existing expert consultations continue to work

## Risk Mitigation

- **Primary Risk**: Auto-created experts may be low quality or incorrect
  - **Mitigation**: Human approval mode, quality metrics, KB maintenance job identifies issues
- **Primary Risk**: Knowledge ingestion may include sensitive data
  - **Mitigation**: Governance layer with do-not-index filters, approval mode, retention policies
- **Primary Risk**: Expert Engine may over-consult experts, causing performance issues
  - **Mitigation**: Caching, metrics monitoring, configurable consultation thresholds
- **Primary Risk**: RAG quality may degrade over time
  - **Mitigation**: Observability metrics, maintenance job, quality improvement proposals
- **Rollback Plan**: 
  - Disable Expert Engine (fall back to manual expert selection)
  - Disable automatic expert creation (use manual config only)
  - Disable knowledge ingestion (use manual KB population)
  - Clear KB and rebuild from approved sources only

## Definition of Done

- [x] Story 28.1: Expert Engine Runtime Component - Core implementation complete
- [x] Story 28.2: Domain/Stack Detector - Core implementation complete
- [x] Story 28.3: Expert Synthesizer - Core implementation complete
- [x] Story 28.4: Knowledge Ingestion Pipeline - Core implementation complete
- [x] Story 28.5: Governance & Safety Layer - Core implementation complete
- [x] Story 28.6: Observability & Quality Improvement Loop - Core implementation complete
- [ ] Story 28.3: Expert Synthesizer - Not started
- [ ] Story 28.4: Knowledge Ingestion Pipeline - Not started
- [ ] Story 28.5: Governance & Safety Layer - Not started
- [ ] Story 28.6: Observability & Quality Improvement Loop - Not started
- [ ] All stories completed with acceptance criteria met
- [ ] Expert Engine automatically detects domains and routes appropriately
- [ ] Expert Synthesizer creates valid experts from repo signals
- [ ] Knowledge Ingestion populates KB from all sources successfully
- [ ] Governance layer prevents secrets/PII from entering KB
- [ ] Observability metrics collected and accessible
- [ ] KB maintenance job identifies and improves weak areas
- [ ] Comprehensive test coverage for all new components
- [ ] Documentation updated (Expert Engine guide, KB ingestion guide, governance guide)
- [ ] No regression in existing expert/RAG functionality
- [ ] Example projects demonstrate automatic expert creation and KB population

## Implementation Status

**Last Updated:** 2025-01-XX

**Overall Status:** Not Started - All stories are in Draft status

**Story Status:**
- Story 28.1 (Expert Engine Runtime Component): Draft - Not implemented
- Story 28.2 (Domain/Stack Detector): Draft - Not implemented
- Story 28.3 (Expert Synthesizer): Draft - Not implemented
- Story 28.4 (Knowledge Ingestion Pipeline): Draft - Not implemented
- Story 28.5 (Governance & Safety Layer): Draft - Not implemented
- Story 28.6 (Observability & Quality Improvement Loop): Draft - Not implemented

**Existing Infrastructure:**
- ExpertRegistry exists (`tapps_agents/experts/expert_registry.py`) with consultation capabilities
- Expert consultation integrated into WorkflowExecutor (`consult_experts_for_step`, `consult_experts` methods)
- DomainConfigParser exists for parsing `.tapps-agents/domains.md` files
- Built-in experts exist via BuiltinExpertRegistry
- RAG backends exist (VectorKnowledgeBase/SimpleKnowledgeBase)
- Context7 KB cache integration exists
- Unified Cache exists

**Missing Components:**
- No Expert Engine runtime component that automatically orchestrates expert consultation
- No domain/stack detector that maps repo signals to expert domains
- No expert synthesizer for automatic expert creation
- No knowledge ingestion pipeline for automatic KB population
- No governance layer for safety and security
- No observability metrics or quality improvement loop

**Notes:**
- Existing expert infrastructure provides foundation but lacks automatic orchestration
- Expert consultation is manual (requires explicit expert IDs in workflow steps)
- No automatic expert creation or knowledge population
- No governance or safety layer for KB operations

