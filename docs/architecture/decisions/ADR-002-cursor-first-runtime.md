---
title: ADR-002: Cursor-First Runtime Policy
version: 1.0.0
status: accepted
last_updated: 2026-01-20
tags: [adr, runtime, cursor, policy]
---

# ADR-002: Cursor-First Runtime Policy

**Status**: Accepted  
**Date**: 2025-01-15  
**Deciders**: TappsCodingAgents Team  
**Tags**: runtime, cursor, policy, execution-mode

## Context

TappsCodingAgents needed to define a clear runtime policy for how the framework operates in different execution contexts. The framework should prioritize Cursor IDE integration while maintaining flexibility for other execution modes.

## Decision

**Cursor-First Runtime Policy:**

- **When running under Cursor** (Skills / Background Agents): The framework runs **tools-only** and prepares instruction objects for Cursor Skills. MAL (Model Abstraction Layer) is **disabled**.
- **When running headlessly**: MAL is optional and can be enabled explicitly, but the primary execution mode is tools-only with instruction preparation.

**Mental Model:**
- **Cursor is the "brain"** (LLM reasoning) - Uses whatever model the developer configured
- **TappsCodingAgents is the "hands"** (deterministic execution) - Runs workflows, quality tools, reporting, worktree isolation, caching, etc.

## Rationale

This policy provides:

1. **Clear Separation**: Framework focuses on deterministic execution, Cursor handles LLM reasoning
2. **Optimal Integration**: Leverages Cursor's native capabilities without duplication
3. **Developer Experience**: No additional LLM setup required when using Cursor
4. **Consistency**: Same execution model whether using Skills or Background Agents
5. **Performance**: Tools-only execution is faster and more reliable than LLM calls

## Consequences

### Positive

- **Simplified Setup**: No LLM configuration needed in Cursor
- **Better Performance**: Tools-only execution is faster
- **Native Integration**: Works seamlessly with Cursor's Skills system
- **Consistent Behavior**: Same execution model across all Cursor integration points
- **Reduced Complexity**: No need to manage LLM providers in framework code

### Negative

- **Cursor Dependency**: Primary execution mode requires Cursor IDE
- **Limited Headless Support**: Headless execution has reduced functionality (though acceptable for secondary use case)
- **Model Selection**: Framework doesn't control model selection (delegated to Cursor)

### Neutral

- **Documentation Requirements**: Need to clearly document runtime policy for developers

## Alternatives Considered

### Alternative 1: Always Use MAL

**Description**: Always use Model Abstraction Layer for LLM operations, even in Cursor

**Pros**:
- Consistent execution model across all contexts
- Framework controls model selection
- Works independently of Cursor

**Cons**:
- Requires API keys or local LLM setup
- Duplicates Cursor's LLM capabilities
- More complex configuration
- Slower execution (LLM calls vs tools-only)

**Why Not Chosen**: The primary use case is Cursor IDE integration, and using Cursor's native LLM capabilities provides better performance and simpler setup.

### Alternative 2: Conditional MAL Usage

**Description**: Use MAL when Cursor is not available, otherwise use Cursor's LLM

**Pros**:
- Supports both Cursor and headless execution
- Flexible execution model

**Cons**:
- More complex implementation
- Two code paths to maintain
- Potential inconsistencies between modes
- Requires detecting Cursor availability

**Why Not Chosen**: The tools-only approach with instruction preparation is sufficient for both Cursor and headless execution. The added complexity of conditional MAL usage doesn't provide sufficient value.

## Related ADRs

- [ADR-001: Instruction-Based Architecture](ADR-001-instruction-based-architecture.md)

## References

- [How It Works Documentation](../HOW_IT_WORKS.md)
- [Architecture Overview](../ARCHITECTURE.md)

---

**Last Updated**: 2026-01-20  
**Maintained By**: TappsCodingAgents Team
