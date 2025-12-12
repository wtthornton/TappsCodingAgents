# Expert Framework Enhancement - Quick Reference

**Quick Start Guide for Implementation**

> **Status Note (2025-12-11):** This file is a historical snapshot.  
> **Canonical status:** See `implementation/IMPLEMENTATION_STATUS.md`.

## Implementation Phases Summary

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 1** | 2 weeks | Foundation + Security | Built-in registry, Security expert, Knowledge base |
| **Phase 2** | 2 weeks | Performance + Testing | Performance expert, Testing expert, Knowledge bases |
| **Phase 3** | 1.5 weeks | Data Privacy | Data Privacy expert, Compliance knowledge |
| **Phase 4** | 1.5 weeks | Accessibility + UX | Accessibility expert, UX expert, Knowledge bases |
| **Phase 5** | 2 weeks | Integration + Testing | Enhanced registry, Comprehensive tests |
| **Phase 6** | 1 week | Documentation + Release | Docs, Migration guide, Release |

**Total: 11 weeks (~3 months)**

## New Experts Overview

| Expert | Domain | Priority | Knowledge Files | Agent Usage |
|--------|--------|----------|-----------------|-------------|
| **Security** | `security` | 🔴 High | 8 files | Architect, Implementer, Reviewer, Ops |
| **Performance** | `performance-optimization` | 🔴 High | 8 files | Architect, Implementer, Reviewer, Debugger |
| **Testing** | `testing-strategies` | 🔴 High | 8 files | Tester, Planner, Reviewer |
| **Data Privacy** | `data-privacy-compliance` | 🟡 Medium | 10 files | Architect, Implementer, Ops, Designer |
| **Accessibility** | `accessibility` | 🟡 Medium | 9 files | Designer, Implementer, Reviewer |
| **UX** | `user-experience` | 🟡 Medium | 8 files | Designer, Architect, Analyst |

## Key Files to Create/Modify

### New Files
```
tapps_agents/experts/
├── builtin_registry.py          # Built-in expert registry
└── knowledge/                    # Built-in knowledge bases
    ├── security/
    ├── performance/
    ├── testing/
    ├── data-privacy/
    ├── accessibility/
    └── user-experience/
```

### Modified Files
```
tapps_agents/experts/
├── expert_registry.py            # Add built-in expert loading
└── base_expert.py                # Add built-in knowledge base support

tapps_agents/agents/
├── architect/agent.py            # Security, Performance, UX integration
├── implementer/agent.py          # Security, Performance integration
├── reviewer/agent.py             # Security, Performance, Testing, Accessibility
├── tester/agent.py               # Testing expert integration
├── designer/agent.py             # Accessibility, UX, Data Privacy integration
├── ops/agent.py                  # Security, Data Privacy integration
└── ... (all other agents)
```

## Architecture Pattern

```python
# Built-in experts (immutable, framework-controlled)
BuiltinExpertRegistry.get_builtin_experts()
  ↓
ExpertRegistry._load_builtin_experts()
  ↓
BaseExpert with built-in knowledge base path

# Customer experts (configurable)
ExpertRegistry.from_config_file(experts.yaml)
  ↓
BaseExpert with customer knowledge base path

# Weighted consultation
ExpertRegistry.consult(query, domain, prioritize_builtin=True/False)
  ↓
51% customer expert (business domains)
49% built-in expert (technical domains)
```

## Knowledge Base Structure

Each expert needs 8-10 markdown files:

```
knowledge/{domain}/
├── overview.md                   # Domain overview
├── patterns.md                   # Common patterns
├── best-practices.md             # Best practices
├── anti-patterns.md              # Anti-patterns
├── {specific-topic-1}.md        # Topic-specific knowledge
├── {specific-topic-2}.md
└── ...
```

## Agent Integration Pattern

```python
# Standard pattern for all agents
async def _method_with_expert(self, ...):
    # Consult expert
    if self.expert_registry:
        consultation = await self.expert_registry.consult(
            query=f"Question about: {context}",
            domain="security",  # or appropriate domain
            include_all=True,
            prioritize_builtin=True  # for technical domains
        )
        expert_guidance = consultation.weighted_answer
    else:
        expert_guidance = ""
    
    # Use expert guidance in prompt
    prompt = f"""
    {expert_guidance}
    
    {original_prompt}
    """
    
    # Continue with implementation
```

## Testing Checklist

For each expert:
- [ ] Unit tests for expert consultation
- [ ] Knowledge base loading tests
- [ ] Integration tests with agents
- [ ] Weighted consultation tests
- [ ] Error handling tests

## Documentation Checklist

- [ ] Built-in experts guide
- [ ] Knowledge base guide
- [ ] Agent integration examples
- [ ] API documentation updates
- [ ] Migration guide
- [ ] Changelog

## Quick Start Commands

```bash
# Phase 1: Create built-in registry
touch tapps_agents/experts/builtin_registry.py

# Phase 1: Create security knowledge base
mkdir -p tapps_agents/experts/knowledge/security

# Phase 1: Create security knowledge files
touch tapps_agents/experts/knowledge/security/{owasp-top10,threat-modeling,secure-coding}.md

# Run tests
pytest tests/unit/experts/
pytest tests/integration/test_security_expert_integration.py
```

## Success Metrics

- ✅ All 6 experts implemented
- ✅ 8+ knowledge files per expert
- ✅ All 12 agents integrated
- ✅ 90%+ test coverage
- ✅ Expert consultation <2s
- ✅ Zero breaking changes

---

**See full plan:** `implementation/EXPERT_FRAMEWORK_ENHANCEMENT_PLAN_2025.md`

