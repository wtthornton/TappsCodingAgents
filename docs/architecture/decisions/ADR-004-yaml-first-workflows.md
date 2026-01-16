---
title: ADR-004: YAML-First Workflow Architecture
version: 1.0.0
status: accepted
last_updated: 2026-01-20
tags: [adr, architecture, workflows, yaml]
---

# ADR-004: YAML-First Workflow Architecture

**Status**: Accepted  
**Date**: 2025-03-15  
**Deciders**: TappsCodingAgents Team  
**Tags**: architecture, workflows, yaml, schema-enforcement

## Context

TappsCodingAgents needed a way to define workflows that is both human-readable and machine-executable. Workflows should be easy to create, validate, and maintain while supporting complex execution patterns like parallel steps and conditional logic.

## Decision

**YAML-First Workflow Architecture:**

- **YAML is the single source of truth** - All workflow definitions in YAML with strict schema enforcement
- **Strict schema validation** - Parser rejects unknown fields (Epic 6)
- **Auto-generated artifacts**:
  - **Task Manifests** (Epic 7): Auto-generated from workflow YAML + state
  - **Cursor Rules Documentation** (Epic 8): Auto-generated from workflow YAML
- **Dependency-based parallelism** - Automatic parallel execution based on step dependencies (no `parallel_tasks` field needed)

**Key Components:**
- Workflow parsing: `tapps_agents/workflow/parser.py` - YAML parsing with strict schema enforcement
- Parallel execution: `tapps_agents/workflow/parallel_executor.py` - Executes independent steps in parallel (up to 8 concurrent)
- Task manifest generation: `tapps_agents/workflow/manifest.py` - Auto-generated task checklists
- Cursor Rules generation: `tapps_agents/workflow/rules_generator.py` - Auto-generated Cursor Rules docs

## Rationale

This architecture provides:

1. **Human-Readable**: YAML is easy to read and write, making workflows accessible to non-developers
2. **Machine-Executable**: Strict schema validation ensures workflows are valid before execution
3. **Version Control Friendly**: YAML files work well with Git and can be reviewed in PRs
4. **Auto-Generated Artifacts**: Task manifests and documentation are automatically generated, reducing maintenance
5. **Dependency-Based Parallelism**: Automatic parallel execution based on dependencies, no manual configuration needed
6. **Single Source of Truth**: YAML defines everything, reducing duplication and inconsistencies

## Consequences

### Positive

- **Human-Readable**: Easy to understand and modify workflows
- **Strict Validation**: Schema enforcement catches errors early
- **Auto-Generated Docs**: Task manifests and Cursor Rules docs are always up-to-date
- **Automatic Parallelism**: No need to manually configure parallel execution
- **Version Control**: YAML files work well with Git workflows
- **Reduced Duplication**: Single source of truth eliminates inconsistencies

### Negative

- **YAML Complexity**: Complex workflows can become verbose
- **Schema Learning Curve**: Developers need to learn workflow schema
- **Limited Expressiveness**: YAML may not support all possible workflow patterns (though sufficient for most cases)
- **Parser Dependency**: Requires robust YAML parser with schema validation

### Neutral

- **Tooling Requirements**: Need YAML schema validation tools
- **Documentation**: Need comprehensive workflow schema documentation

## Alternatives Considered

### Alternative 1: Code-Based Workflows

**Description**: Define workflows in Python code

**Pros**:
- Full programming language expressiveness
- Type checking and IDE support
- Can use complex logic and conditionals

**Cons**:
- Less accessible to non-developers
- Harder to version control and review
- More complex to maintain
- Requires code changes for workflow modifications

**Why Not Chosen**: YAML provides better accessibility and maintainability. Code-based workflows would require developers to modify Python code for every workflow change, which is less flexible than YAML files.

### Alternative 2: JSON Workflows

**Description**: Use JSON instead of YAML for workflow definitions

**Pros**:
- Machine-readable format
- Wide tool support
- No parsing ambiguity

**Cons**:
- Less human-readable (no comments, verbose syntax)
- Harder to write and maintain
- No multi-line string support

**Why Not Chosen**: YAML is more human-readable and easier to write, which is important for workflow definitions that may be created or modified by non-developers.

### Alternative 3: Hybrid Approach

**Description**: Use YAML for structure, Python for complex logic

**Pros**:
- Combines readability of YAML with expressiveness of Python
- Flexible for complex workflows

**Cons**:
- More complex implementation
- Two languages to maintain
- Potential inconsistencies between YAML and Python

**Why Not Chosen**: Pure YAML approach is sufficient for most workflows. Complex logic can be handled through step dependencies and conditional execution, which are supported in YAML.

## Related ADRs

- [ADR-001: Instruction-Based Architecture](ADR-001-instruction-based-architecture.md)

## References

- [YAML Workflow Architecture Design](../YAML_WORKFLOW_ARCHITECTURE_DESIGN.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [Workflow Selection Guide](../WORKFLOW_SELECTION_GUIDE.md)

---

**Last Updated**: 2026-01-20  
**Maintained By**: TappsCodingAgents Team
