# YAML Structure Audit Report
## Epic 6: YAML Schema Enforcement

**Date**: 2025-01-XX  
**Purpose**: Catalog all YAML structures used in workflow files and identify drift between YAML definitions and execution

---

## Summary

- **Total Workflow Files**: 10
- **Files with `parallel_tasks`**: 2 (not parsed/executed)
- **Files with `schema_version`**: 1
- **Files using standard `steps`**: 10

---

## Structures Found in YAML Files

### 1. Workflow-Level Fields

| Field | Used In | Parsed? | Executed? | Notes |
|-------|---------|---------|-----------|-------|
| `id` | All (10) | ✅ | ✅ | Required, validated |
| `name` | All (10) | ✅ | ✅ | Parsed to Workflow.name |
| `description` | All (10) | ✅ | ✅ | Parsed to Workflow.description |
| `version` | All (10) | ✅ | ✅ | Parsed to Workflow.version |
| `type` | All (10) | ✅ | ✅ | Parsed to WorkflowType enum |
| `schema_version` | 1 file | ✅ | ✅ | Validated but not used for migration |
| `settings` | All (10) | ✅ | ✅ | Parsed to WorkflowSettings |
| `steps` | All (10) | ✅ | ✅ | Fully parsed and executed |
| `parallel_execution` | 2 files | ❌ | ❌ | **DRIFT: Exists in YAML, ignored by parser** |
| `parallel_tasks` | 2 files | ❌ | ❌ | **DRIFT: Exists in YAML, ignored by parser** |
| `auto_detect` | 3 files | ❌ | ❌ | **DRIFT: Exists in YAML, not in WorkflowSettings model** |
| `metadata` | 0 files | ✅ | ✅ | Supported but not used in any workflow |

### 2. Step-Level Fields

| Field | Used In | Parsed? | Executed? | Notes |
|-------|---------|---------|-----------|-------|
| `id` | All steps | ✅ | ✅ | Required, validated |
| `agent` | All steps | ✅ | ✅ | Required, validated |
| `action` | All steps | ✅ | ✅ | Required, validated |
| `context_tier` | Most steps | ✅ | ✅ | Defaults to 2 |
| `creates` | Most steps | ✅ | ✅ | Used for dependency tracking |
| `requires` | Most steps | ✅ | ✅ | Used for dependency tracking |
| `consults` | Some steps | ✅ | ✅ | Parsed but usage unclear |
| `condition` | Some steps | ✅ | ✅ | Validated (required/optional/conditional) |
| `next` | Some steps | ✅ | ✅ | Validated for step references |
| `gate` | Some steps | ✅ | ✅ | Validated, used for routing |
| `optional_steps` | Some steps | ✅ | ✅ | Validated for step references |
| `notes` | Some steps | ✅ | ✅ | Parsed to metadata |
| `repeats` | Some steps | ✅ | ✅ | Parsed, boolean |
| `scoring` | Some steps | ✅ | ✅ | Parsed to metadata |
| `metadata` | Some steps | ✅ | ✅ | Parsed to step metadata |

### 3. Settings Fields

| Field | Used In | Parsed? | Executed? | Notes |
|-------|---------|---------|-----------|-------|
| `quality_gates` | Most files | ✅ | ✅ | Parsed to WorkflowSettings |
| `code_scoring` | Most files | ✅ | ✅ | Parsed to WorkflowSettings |
| `context_tier_default` | Most files | ✅ | ✅ | Parsed to WorkflowSettings |
| `auto_detect` | 3 files | ❌ | ❌ | **DRIFT: Exists in YAML, not in WorkflowSettings** |
| `max_parallel_agents` | 2 files | ❌ | ❌ | **DRIFT: In parallel_tasks workflows, not parsed** |
| `use_worktrees` | 2 files | ❌ | ❌ | **DRIFT: In parallel_tasks workflows, not parsed** |
| `aggregate_results` | 2 files | ❌ | ❌ | **DRIFT: In parallel_tasks workflows, not parsed** |
| `performance_monitoring` | 2 files | ❌ | ❌ | **DRIFT: In parallel_tasks workflows, not parsed** |

### 4. Gate Fields

| Field | Used In | Parsed? | Executed? | Notes |
|-------|---------|---------|-----------|-------|
| `condition` | Some gates | ✅ | ✅ | Validated |
| `on_pass` | Some gates | ✅ | ✅ | Validated for step references |
| `on_fail` | Some gates | ✅ | ✅ | Validated for step references |

---

## Critical Drift Issues

### Issue 1: `parallel_tasks` Section (HIGH PRIORITY)
- **Files Affected**: `multi-agent-review-and-test.yaml`, `multi-agent-refactor.yaml`
- **Status**: Defined in YAML but **NOT parsed** by `WorkflowParser`
- **Impact**: These workflows define parallel tasks that are completely ignored
- **Decision Needed**: Remove from YAML or implement parser/executor support

### Issue 2: `parallel_execution` Flag (MEDIUM PRIORITY)
- **Files Affected**: Same 2 files as above
- **Status**: Defined in YAML but **NOT parsed**
- **Impact**: Flag is ignored, no effect on execution
- **Decision Needed**: Remove or implement

### Issue 3: Settings Fields Not in Model (LOW PRIORITY)
- **Fields**: `max_parallel_agents`, `use_worktrees`, `aggregate_results`, `performance_monitoring`
- **Status**: In YAML but not in `WorkflowSettings` model
- **Impact**: Settings are ignored
- **Decision Needed**: Add to model or remove from YAML

### Issue 4: `auto_detect` at Workflow Level (LOW PRIORITY)
- **Files Affected**: 3 preset workflows
- **Status**: In YAML but not in `WorkflowSettings` model
- **Impact**: Setting is ignored
- **Decision Needed**: Add to model or remove from YAML

---

## Files with Drift

1. **workflows/multi-agent-review-and-test.yaml**
   - Has `parallel_execution: true`
   - Has `parallel_tasks` section (7 tasks)
   - Has unsupported settings fields

2. **workflows/multi-agent-refactor.yaml**
   - Has `parallel_execution: true`
   - Has `parallel_tasks` section (6 tasks)
   - Has unsupported settings fields

3. **workflows/presets/rapid-dev.yaml**
   - Has `auto_detect: true` at workflow level (not in settings)

4. **workflows/presets/quality.yaml**
   - Has `auto_detect: true` at workflow level (not in settings)

5. **workflows/presets/full-sdlc.yaml**
   - Has `auto_detect: true` at workflow level (not in settings)

---

## Recommendations

1. **Remove `parallel_tasks` and `parallel_execution`** - Dependency-based parallelism already works well and is simpler
2. **Add `auto_detect` to WorkflowSettings model** - Used in 3 preset workflows
3. **Remove unsupported settings fields** from parallel workflows or add to model if needed
4. **Implement strict schema validation** - Fail fast on unknown fields
5. **Add schema versioning** - Support migration between versions

---

## Next Steps

1. ✅ Complete audit (this document)
2. ⏳ Make architectural decision on `parallel_tasks`
3. ⏳ Implement strict schema enforcement
4. ⏳ Add schema versioning support
5. ⏳ Clean up YAML files to remove unsupported fields
6. ⏳ Update documentation

