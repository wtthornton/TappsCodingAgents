---
title: AI Comment Tag Guidelines
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [documentation, ai-assistants, code-comments, standards]
---

# AI Comment Tag Guidelines

This document defines the standard AI comment tags used throughout the TappsCodingAgents codebase to provide context and guidance to AI coding assistants.

## Overview

AI comment tags are special comment annotations that help AI assistants understand:
- **File purpose and constraints** (`@ai-prime-directive`, `@ai-constraints`)
- **Current development context** (`@ai-current-task`)
- **Important permanent context** (`@note`, `@note[date]`)
- **Temporary AI directives** (`@hint`)
- **Protected code sections** (`@ai-dont-touch`)

These tags are designed to be machine-readable while remaining human-readable, enabling both AI assistants and human developers to understand code context and constraints.

## Tag Reference

### `@ai-prime-directive`

**Purpose:** File-level metadata describing the primary purpose and responsibility of a file.

**When to Use:**
- At the top of files that implement core functionality
- When a file has a specific architectural role
- To clarify file purpose when the name alone is insufficient

**Format:**
```python
# @ai-prime-directive: Brief description of file's primary purpose.
# Additional context about the file's role, architecture, or design decisions.
```

**Example:**
```python
# @ai-prime-directive: This file implements the workflow execution engine for YAML-first workflows.
# Workflows are defined in YAML with strict schema enforcement and executed with dependency-based
# parallelism. Do not modify the execution model without updating workflow definitions and tests.
```

**Best Practices:**
- Keep the first line concise (one sentence)
- Add additional context on subsequent lines if needed
- Reference architectural decisions (ADRs) when relevant
- Update when file's primary purpose changes

---

### `@ai-constraints`

**Purpose:** Document constraints, limitations, and requirements that must be maintained.

**When to Use:**
- When code must adhere to specific architectural patterns
- When there are performance requirements
- When backward compatibility must be maintained
- When there are integration constraints

**Format:**
```python
# @ai-constraints:
# - Constraint 1: Description
# - Constraint 2: Description
# - Performance: Specific requirement
```

**Example:**
```python
# @ai-constraints:
# - Must support YAML-first architecture per ADR-004
# - Dependency-based parallelism is automatic - do not add manual parallel_tasks configuration
# - Workflow state persistence must maintain backward compatibility
# - Performance: Workflow parsing must complete in <100ms for typical workflows
```

**Best Practices:**
- Use bullet points for clarity
- Reference ADRs when constraints come from architectural decisions
- Include performance requirements when applicable
- Update when constraints change

---

### `@note` / `@note[date]`

**Purpose:** Permanent important context that should be preserved across refactorings.

**When to Use:**
- To document architectural decisions (reference ADRs)
- To explain non-obvious design choices
- To document important historical context
- To explain workarounds or special handling

**Format:**
```python
# @note[YYYY-MM-DD]: Brief description of important context.
# Additional details if needed.
```

**Example:**
```python
# @note[2025-03-15]: YAML-first workflow architecture per ADR-004.
# YAML is the single source of truth with strict schema enforcement.
# See docs/architecture/decisions/ADR-004-yaml-first-workflows.md
```

**Best Practices:**
- Include date when documenting a specific decision or change
- Reference ADRs for architectural decisions
- Keep notes concise but informative
- Use `@note` (without date) for general context that doesn't have a specific date

**Example without date:**
```python
# @note: Dynamic agent import pattern - allows parallel execution to load agents
# on-demand without circular import issues.
```

---

### `@ai-current-task`

**Purpose:** Document the current development task or context for ongoing work.

**When to Use:**
- During active development of a feature
- When code is in a transitional state
- To guide AI assistants working on incomplete features
- To mark areas that need follow-up work

**Format:**
```python
# @ai-current-task: Brief description of current work.
# Additional context about what's being implemented or fixed.
```

**Example:**
```python
# @ai-current-task: Implementing async workflow execution.
# Currently adding support for async agent handlers. Tests pending.
```

**Best Practices:**
- Remove or update when task is complete
- Include status (e.g., "in progress", "pending tests")
- Reference related issues or PRs when applicable
- Update regularly as work progresses

**Note:** This tag is temporary and should be removed or updated when the task is complete.

---

### `@hint`

**Purpose:** Temporary AI directives for specific development scenarios.

**When to Use:**
- To guide AI assistants during refactoring
- To provide context for specific code sections
- To explain non-obvious patterns
- For temporary development guidance

**Format:**
```python
# @hint: Brief directive for AI assistants.
# Additional context if needed.
```

**Example:**
```python
# @hint: When modifying this function, ensure all error paths return ErrorEnvelope.
# See ErrorEnvelopeBuilder for consistent error formatting.
```

**Best Practices:**
- Keep hints concise and actionable
- Remove when no longer needed
- Use for temporary guidance, not permanent documentation
- Prefer `@note` for permanent context

**Note:** This tag is temporary and should be removed when the guidance is no longer needed.

---

### `@ai-dont-touch`

**Purpose:** Guard sections of code that should not be modified.

**When to Use:**
- For legacy code that must remain unchanged
- For fragile code sections that break easily
- For code that has specific performance characteristics
- For third-party integration points that must remain stable

**Format:**
```python
# @ai-dont-touch: Reason why this code should not be modified.
# Additional context about what would break if modified.
```

**Example:**
```python
# @ai-dont-touch: This function has been optimized for specific performance characteristics.
# Modifying the algorithm will break performance benchmarks. See performance-guide.md.
```

**Best Practices:**
- Always provide a clear reason
- Reference documentation when applicable
- Consider if code can be refactored instead of guarded
- Review periodically to see if guard is still needed

**Warning:** Use sparingly. Overuse of this tag can prevent necessary improvements. Consider refactoring guarded code if it becomes a maintenance burden.

---

## Tag Usage Patterns

### File Header Pattern

For core files, use this pattern at the top:

```python
"""
Module docstring here.
"""

# @ai-prime-directive: Primary purpose of this file.
# Additional context about role and architecture.

# @ai-constraints:
# - Constraint 1: Description
# - Constraint 2: Description

# @note[YYYY-MM-DD]: Important architectural context.
# Reference to ADR or design decision.
```

### Inline Context Pattern

For specific code sections:

```python
def complex_function():
    # @note: This function uses a specific pattern because...
    # @hint: When modifying, ensure X behavior is maintained.
    
    # Implementation here
    pass
```

### Guard Pattern

For protected code:

```python
# @ai-dont-touch: Reason for protection.
# What would break if modified.
def fragile_function():
    # Protected implementation
    pass
```

## When to Use Each Tag

| Scenario | Recommended Tag | Alternative |
|----------|----------------|-------------|
| File purpose/role | `@ai-prime-directive` | Module docstring |
| Architectural constraints | `@ai-constraints` | `@note` with ADR reference |
| Design decisions | `@note[date]` with ADR | Regular comment |
| Ongoing development | `@ai-current-task` | `@todo` (general) |
| Temporary AI guidance | `@hint` | Regular comment |
| Protected code | `@ai-dont-touch` | `@warning` (general) |
| General context | `@note` | Regular comment |

## Tag Maintenance

### Regular Review

- **Quarterly review:** Review all `@ai-dont-touch` tags to see if they're still needed
- **After refactoring:** Update or remove `@ai-current-task` tags
- **After ADR changes:** Update `@ai-constraints` and `@note` tags that reference ADRs
- **After feature completion:** Remove `@hint` tags that are no longer relevant

### Migration Guide

When updating existing code:

1. **Identify existing patterns:**
   - Look for TODO/FIXME comments that should be `@ai-current-task`
   - Find architectural comments that should be `@note[date]` with ADR references
   - Locate "DO NOT MODIFY" comments that should be `@ai-dont-touch`

2. **Update systematically:**
   - Start with core files (`core/`, `workflow/`)
   - Update files as you work on them
   - Don't do a mass update unless necessary

3. **Validate:**
   - Ensure tags are accurate and up-to-date
   - Remove obsolete tags
   - Update references to ADRs

## Examples from Codebase

### Example 1: Core Agent Base

```python
# @ai-prime-directive: This file implements the core agent base class for all workflow agents.
# All agents inherit from AgentBase and implement the instruction-based architecture pattern.

# @ai-constraints:
# - Must implement instruction-based architecture per ADR-001
# - All agents must return Instruction objects, not direct results
# - Agent execution is deterministic based on instructions

# @note[2025-01-15]: Instruction-based architecture per ADR-001.
# See docs/architecture/decisions/ADR-001-instruction-based-architecture.md
```

### Example 2: Workflow Executor

```python
# @ai-prime-directive: This file implements the workflow execution engine for YAML-first workflows.
# Workflows are defined in YAML with strict schema enforcement and executed with dependency-based
# parallelism. Do not modify the execution model without updating workflow definitions and tests.

# @ai-constraints:
# - Must support YAML-first architecture per ADR-004
# - Dependency-based parallelism is automatic - do not add manual parallel_tasks configuration
# - Workflow state persistence must maintain backward compatibility
# - Performance: Workflow parsing must complete in <100ms for typical workflows

# @note[2025-03-15]: YAML-first workflow architecture per ADR-004.
# YAML is the single source of truth with strict schema enforcement.
# See docs/architecture/decisions/ADR-004-yaml-first-workflows.md
```

### Example 3: Inline Note

```python
def load_agent(agent_name: str):
    # @note: Dynamic agent import pattern - allows parallel execution to load agents
    # on-demand without circular import issues.
    module = importlib.import_module(f"tapps_agents.agents.{agent_name}")
    return getattr(module, agent_name.title().replace("_", ""))
```

## Integration with Documentation

### ADR References

When referencing Architectural Decision Records:

```python
# @note[2025-03-15]: YAML-first workflow architecture per ADR-004.
# See docs/architecture/decisions/ADR-004-yaml-first-workflows.md
```

### Documentation Links

Link to relevant documentation:

```python
# @ai-constraints:
# - Performance requirements documented in docs/architecture/performance-guide.md
# - See docs/architecture/testing-strategy.md for test requirements
```

## Best Practices Summary

1. **Be specific:** Provide clear, actionable context
2. **Reference ADRs:** Link to architectural decisions when relevant
3. **Keep updated:** Remove or update temporary tags (`@hint`, `@ai-current-task`)
4. **Use sparingly:** Don't over-tag code; focus on areas that need AI guidance
5. **Maintain consistency:** Follow the patterns established in this document
6. **Review regularly:** Periodically review tags for accuracy and relevance

## Related Documentation

- **[Architecture Decisions](../architecture/decisions/)** - ADRs referenced in tags
- **[Coding Standards](../architecture/coding-standards.md)** - General coding standards
- **[Contributing Guide](../CONTRIBUTING.md)** - Contribution guidelines
- **[AGENTS.md](../AGENTS.md)** - AI agent identity and rules

## Questions or Suggestions?

If you have questions about AI comment tags or suggestions for improvements, please:
1. Review existing patterns in the codebase
2. Check if your use case is covered by existing tags
3. Open an issue or discussion for new tag types
4. Update this document when adding new patterns
