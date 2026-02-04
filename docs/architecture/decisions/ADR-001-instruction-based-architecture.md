---
title: ADR-001: Instruction-Based Architecture
version: 1.0.0
status: accepted
last_updated: 2026-01-20
tags: [adr, architecture, instruction-based, cursor]
---

# ADR-001: Instruction-Based Architecture

**Status**: Accepted  
**Date**: 2025-01-15  
**Deciders**: TappsCodingAgents Team  
**Tags**: architecture, instruction-based, cursor, llm-integration

## Context

TappsCodingAgents needed a way to integrate with LLMs without requiring local LLM installations or API keys. The framework should work seamlessly with Cursor IDE, which already provides LLM capabilities through its Skills system. Additionally, we wanted to separate the "brain" (LLM reasoning) from the "hands" (deterministic execution).

## Decision

Agents prepare structured instruction objects (defined in `tapps_agents/core/instructions.py`) instead of calling LLMs directly. These instruction objects are executed via Cursor Skills, which use the developer's configured model.

**Instruction Models:**
- `CodeGenerationInstruction` - For code generation and refactoring
- `TestGenerationInstruction` - For test generation
- `DocumentationInstruction` - For documentation generation
- `ErrorAnalysisInstruction` - For error analysis and debugging
- `GenericInstruction` - For other agent operations

**Runtime Model:**
- All agents prepare instruction objects instead of calling LLMs directly
- Instructions are executed by Cursor Skills, which use the developer's configured model
- No local LLM or API keys required - Cursor handles all LLM operations

## Rationale

This architecture provides several key benefits:

1. **Separation of Concerns**: Framework focuses on deterministic execution (workflows, quality tools, reporting), while Cursor handles LLM reasoning
2. **Model Agnostic**: Works with any model the developer configures in Cursor (Auto or pinned)
3. **No API Keys Required**: Developers don't need to manage LLM API keys or local LLM installations
4. **Consistent Interface**: All agents use the same instruction-based interface, making the system more maintainable
5. **Testability**: Instruction objects can be validated and tested without requiring LLM calls

## Consequences

### Positive

- **Simplified Setup**: No need to configure LLM providers or API keys
- **Model Flexibility**: Developers can use any model configured in Cursor
- **Better Separation**: Clear boundary between framework logic and LLM operations
- **Easier Testing**: Instruction objects can be validated independently
- **Cursor Integration**: Native integration with Cursor's Skills system

### Negative

- **Cursor Dependency**: Framework requires Cursor IDE for LLM operations (though CLI mode exists for headless execution)
- **Instruction Overhead**: Additional layer of abstraction between agents and LLM execution
- **Limited Headless Support**: Headless execution requires alternative approaches (though this is acceptable for the primary use case)

### Neutral

- **Learning Curve**: Developers need to understand instruction-based model (though it's well-documented)

## Alternatives Considered

### Alternative 1: Direct LLM Calls

**Description**: Agents call LLMs directly using a model abstraction layer (MAL)

**Pros**:
- More direct control over LLM interactions
- Works independently of Cursor
- Can support multiple LLM providers

**Cons**:
- Requires API keys or local LLM setup
- More complex configuration
- Duplicates functionality that Cursor already provides
- Less integrated with Cursor's native capabilities

**Why Not Chosen**: The primary use case is Cursor IDE integration, and direct LLM calls would require additional setup and maintenance. The instruction-based approach provides better separation of concerns and integrates seamlessly with Cursor.

### Alternative 2: Hybrid Approach

**Description**: Support both instruction-based (Cursor) and direct LLM calls (headless)

**Pros**:
- Flexibility for different execution modes
- Supports both Cursor and headless use cases

**Cons**:
- More complex implementation
- Two code paths to maintain
- Potential inconsistencies between modes

**Why Not Chosen**: The instruction-based approach is sufficient for the primary use case (Cursor IDE), and headless execution can use alternative approaches when needed. The added complexity of supporting both modes doesn't provide sufficient value.

## Related ADRs

- [ADR-002: Equal Platform Support Policy](ADR-002-equal-platform-support.md)

## References

- [How It Works Documentation](../HOW_IT_WORKS.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [Instruction Models](../tapps_agents/core/instructions.py)

---

**Last Updated**: 2026-01-20  
**Maintained By**: TappsCodingAgents Team
