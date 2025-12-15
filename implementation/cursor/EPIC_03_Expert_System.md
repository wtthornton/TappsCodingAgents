# Epic 3: Expert Consultation Framework & RAG System

## Epic Goal

Implement the business expert consultation framework with RAG (Retrieval-Augmented Generation) system, enabling weighted decision-making from industry and technical experts. This epic adds domain expertise capabilities to the Design and Code agents.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Basic expert profile system exists (`tapps_agents/experts/`)
- **Technology stack**: Python, existing expert profiles, potential RAG libraries
- **Integration points**: 
  - Expert profile system
  - Design & Architecture Agent
  - Code Generation Agent
  - Context7 integration points

### Enhancement Details

- **What's being added/changed**: 
  - Expert Registry with industry and built-in experts
  - RAG system for expert knowledge (chunking, embeddings, FAISS) with governance and evaluation
  - Weighted decision-making (Primary 51%, Others 49%/(N-1))
  - Expert consultation integration in Design/Code agents
  - Knowledge base loading and indexing

- **How it integrates**: 
  - Expert Registry extends existing expert profiles
  - RAG queries integrated into agent decision-making
  - Expert recommendations influence architecture and code
  - Knowledge bases stored in `.tapps-agents/experts/`

- **2025 standards / guardrails**:
  - **RAG safety**: retrieved content is treated as untrusted input; defend against prompt injection (strip/label sources, constrain tool usage, require citations).
  - **Measurable quality**: add retrieval evaluation (golden Q/A sets) and track precision/latency regressions.
  - **Data governance**: explicit allowlist of indexed content, retention policy, and “do-not-index” patterns (secrets/PII).
  - **Resilience**: hard timeouts + graceful degradation (expert-free mode) with clear user-facing notes.

- **Success criteria**: 
  - Expert system queryable and functional
  - Weighted recommendations work correctly
  - Knowledge retrieval < 2s
  - 2-3 industry experts configured

## Stories

1. **Story 3.1: Expert Registry & Configuration System**
   - Implement Expert Registry class
   - Create expert YAML configuration format
   - Add expert discovery and loading

2. **Story 3.2: RAG System Core (Chunking & Embeddings)**
   - Implement document chunking (512 tokens, 50 overlap)
   - Add embedding generation (sentence-transformers)
   - Create FAISS index builder

3. **Story 3.3: RAG Query & Retrieval System**
   - Implement semantic search queries
   - Add similarity threshold filtering
   - Create knowledge retrieval API

4. **Story 3.4: Weighted Decision-Making Engine**
   - Implement weighted recommendation combination
   - Add primary expert (51%) weighting
   - Create recommendation merging logic

5. **Story 3.5: Expert Consultation Integration**
   - Integrate expert consultation into Design Agent
   - Add expert queries to Code Agent
   - Create 2-3 initial industry expert configurations

6. **Story 3.6: Retrieval Quality Evaluation & Safety Hardening**
   - Create a small evaluation set (questions + expected snippets/answers) for expert KBs
   - Add metrics: latency, hit rate, and basic relevance scoring; fail CI on major regressions
   - Add prompt-injection defensive patterns and “untrusted retrieval” handling

## Compatibility Requirements

- [x] Existing expert profiles remain functional
- [x] Expert system optional (agents work without experts)
- [x] No breaking changes to agent interfaces
- [x] RAG system doesn't impact agent performance significantly (fallback to SimpleKnowledgeBase when FAISS unavailable)

## Risk Mitigation

- **Primary Risk**: RAG system adds latency or fails, blocking agents
- **Mitigation**: 
  - RAG queries are async and non-blocking
  - Fallback to no-expert mode if RAG fails
  - Timeout mechanisms for slow queries
- **Rollback Plan**: 
  - Disable expert consultation feature flag
  - Agents continue without expert recommendations
  - Existing functionality unaffected

## Definition of Done

- [x] Expert Registry operational
- [x] RAG system functional with FAISS indexing
- [x] Weighted decision-making works correctly
- [x] Expert consultation integrated into Design/Code agents
- [x] 2-3 industry experts configured and queryable
- [x] Knowledge retrieval < 2s average (with timeout monitoring)
- [x] Documentation updated
- [x] No regression in existing features
- [x] Safety hardening implemented (prompt injection defense)
- [x] Evaluation system implemented (metrics, golden Q/A sets)

## Integration Verification

- **IV1**: Design Agent successfully consults experts
- **IV2**: Expert recommendations influence architecture decisions
- **IV3**: RAG queries don't block agent execution
- **IV4**: Expert system performance acceptable (<2s queries)
