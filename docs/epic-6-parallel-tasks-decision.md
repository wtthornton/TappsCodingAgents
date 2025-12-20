# Parallel Tasks Decision Document
## Epic 6: YAML Schema Enforcement

**Date**: 2025-01-XX  
**Decision**: Remove `parallel_tasks` from YAML (Option A)

---

## Context

Two workflow files (`multi-agent-review-and-test.yaml` and `multi-agent-refactor.yaml`) defined `parallel_tasks` sections that were never parsed or executed by the workflow engine. This created "YAML theater" - features documented in YAML but not actually implemented.

## Options Considered

### Option A: Remove `parallel_tasks` from YAML (SELECTED)
- **Pros**:
  - Dependency-based parallelism already works well and is simpler
  - No additional code complexity
  - Aligns with "don't over-engineer" principle
  - All workflows can use the same execution model
- **Cons**:
  - Need to rewrite 2 workflow files to use standard `steps`
  - Lose explicit parallel task syntax (but functionality preserved)

### Option B: Implement `parallel_tasks` support
- **Pros**:
  - Preserves existing YAML structure
  - Provides explicit parallel task syntax
- **Cons**:
  - Significant implementation effort (parser + executor changes)
  - Adds complexity for minimal benefit
  - Dependency-based parallelism already handles the use cases

## Decision

**Selected Option A**: Remove `parallel_tasks` and convert workflows to use standard `steps` with dependency-based parallelism.

## Rationale

1. **Dependency-based parallelism is sufficient**: The workflow executor already automatically runs independent steps in parallel (up to 8 concurrent steps by default). This handles all the use cases that `parallel_tasks` was intended for.

2. **Simplicity**: Using a single execution model (`steps`) is simpler than maintaining two parallel execution mechanisms.

3. **No functionality loss**: The converted workflows achieve the same parallel execution behavior using dependency-based parallelism.

4. **Alignment with architecture**: The architecture documentation already recommends dependency-based parallelism as the primary mechanism.

## Implementation

1. ✅ Converted `multi-agent-review-and-test.yaml` to use standard `steps`
2. ✅ Converted `multi-agent-refactor.yaml` to use standard `steps`
3. ✅ Removed `parallel_execution` flag (no longer needed)
4. ✅ Removed unsupported settings fields (`max_parallel_agents`, `use_worktrees`, etc.)

## Impact

- **Workflow files affected**: 2 files converted
- **Breaking changes**: None (these workflows weren't working before anyway)
- **Functionality**: Preserved (parallel execution still works via dependencies)

## Migration Notes

For workflows that used `parallel_tasks`:
- Convert `parallel_tasks` to standard `steps`
- Steps with no `requires` dependencies will run in parallel automatically
- Use `requires` to create dependencies between steps
- All steps are automatically executed in parallel when dependencies are met

