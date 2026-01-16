---
title: ADR-003: Expert System Design
version: 1.0.0
status: accepted
last_updated: 2026-01-20
tags: [adr, architecture, expert-system, knowledge]
---

# ADR-003: Expert System Design

**Status**: Accepted  
**Date**: 2025-02-01  
**Deciders**: TappsCodingAgents Team  
**Tags**: architecture, expert-system, knowledge, two-layer-model

## Context

TappsCodingAgents needed a way to provide domain-specific knowledge to agents without hardcoding all possible domains. The system should support both framework-provided technical expertise and project-defined business domain knowledge.

## Decision

**Two-Layer Expert System:**

1. **Built-in Experts** (16): Framework-provided technical domains
   - Security, Performance, Testing, Data Privacy, Accessibility, UX
   - Code Quality, Software Architecture, DevOps, Documentation
   - AI Frameworks, Observability, API Design, Cloud Infrastructure
   - Database, Agent Learning
   - 100+ knowledge files across domains

2. **Industry Experts** (project-defined): Configured in `.tapps-agents/experts.yaml`
   - Optional file-based knowledge base under `.tapps-agents/knowledge/<domain>/*.md`
   - Custom domain expertise for specific projects
   - Weighted decision-making with confidence calculation

**Architecture:**
- Experts live under `tapps_agents/experts/`
- Expert registry for lookup and consultation
- RAG integration (file-based and vector-based)
- Expert consultation integrated into 6 agents: Architect, Implementer, Reviewer, Tester, Designer, Ops

## Rationale

This design provides:

1. **Extensibility**: Projects can add custom domain experts without modifying framework code
2. **Separation of Concerns**: Framework provides technical expertise, projects provide business expertise
3. **Weighted Decision-Making**: Experts provide weighted recommendations with confidence scores
4. **RAG Integration**: Supports both simple file-based and advanced vector-based RAG
5. **Flexibility**: Configuration-only experts (no code classes required)

## Consequences

### Positive

- **Extensible**: Easy to add new experts without code changes
- **Separation**: Clear boundary between framework and project expertise
- **Weighted Decisions**: Confidence-based expert recommendations
- **RAG Support**: Both simple and advanced knowledge retrieval
- **Configuration-Only**: Experts can be defined purely in YAML

### Negative

- **Complexity**: Two-layer system requires understanding of both built-in and industry experts
- **Knowledge Management**: Projects need to maintain their own knowledge bases
- **Expert Selection**: Need to determine which experts to consult for each task

### Neutral

- **Learning Curve**: Developers need to understand expert system architecture
- **Documentation**: Need comprehensive documentation for expert configuration

## Alternatives Considered

### Alternative 1: Single-Layer Built-in Experts Only

**Description**: Only provide framework-built-in experts, no project-defined experts

**Pros**:
- Simpler architecture
- No knowledge base management required
- Easier to understand

**Cons**:
- No way to add project-specific domain knowledge
- Limited to technical domains
- Less flexible for diverse projects

**Why Not Chosen**: Projects need domain-specific expertise (e.g., healthcare, finance, e-commerce) that can't be provided by framework-built-in experts. The two-layer system provides necessary flexibility.

### Alternative 2: Fully Dynamic Expert Creation

**Description**: Automatically create experts from project documentation and code

**Pros**:
- Automatic expert creation
- No manual configuration
- Always up-to-date with project

**Cons**:
- More complex implementation
- Quality control challenges
- Potential for incorrect expert creation
- Requires sophisticated NLP/AI for expert synthesis

**Why Not Chosen**: While this is planned for future (Dynamic Expert & RAG Engine - Epic 2), the current two-layer system provides a good balance of flexibility and control. Automatic expert creation can be added as an enhancement.

## Related ADRs

- [ADR-001: Instruction-Based Architecture](ADR-001-instruction-based-architecture.md)

## References

- [Architecture Overview](../ARCHITECTURE.md)
- [Expert Configuration Guide](../EXPERT_CONFIG_GUIDE.md)
- [Built-in Experts Guide](../BUILTIN_EXPERTS_GUIDE.md)

---

**Last Updated**: 2026-01-20  
**Maintained By**: TappsCodingAgents Team
