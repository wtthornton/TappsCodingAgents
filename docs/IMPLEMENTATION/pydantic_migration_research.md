# Pydantic Migration Research - Context7 Findings

**Date**: January 2025  
**Research Method**: Context7 MCP + Pydantic v2 Best Practices  
**Status**: Applied to Migration ✅

This document captures the research findings and best practices applied during the migration from dataclasses to Pydantic v2 BaseModel.

## Research Objectives

1. Current Pydantic v2 best practices for data validation
2. TypedDict patterns for flexible metadata structures
3. Enum integration patterns with Pydantic
4. Backward compatibility strategies
5. Schema generation and validation approaches

## Key Findings

### 1. Pydantic v2 BaseModel Best Practices

**Strict Validation with `extra="forbid"`**:
```python
from pydantic import BaseModel

class MyModel(BaseModel):
    model_config = {"extra": "forbid"}  # Reject unknown fields
```

**Rationale**: 
- Prevents typos and unexpected fields from being silently ignored
- Ensures data integrity and catches errors early
- Recommended for production code where data structure is well-defined

**Applied To**: All artifact models and nested models

### 2. TypedDict for Flexible Metadata

**Pattern**: Use `TypedDict` with `total=False` for optional metadata fields:

```python
from typing import TypedDict

class ArtifactMetadata(TypedDict, total=False):
    agent_version: str
    execution_context: str
    custom_tags: list[str]
    related_artifacts: list[str]
    workflow_id: str
    step_id: str
    agent_id: str
    execution_mode: str
```

**Rationale**:
- Allows partial metadata structures (some fields may be missing)
- Maintains type hints for known fields
- Flexible enough for varying metadata needs
- Can be used in Pydantic models via `Field(..., json_schema_extra={...})` or as separate TypedDict

**Applied To**: `ArtifactMetadata` in `metadata_models.py`

### 3. Enum Integration Patterns

**Pattern**: Use `str` Enum for JSON compatibility:

```python
from enum import Enum

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

**Benefits**:
- Serializes to JSON strings automatically
- Can compare with strings: `if priority == "high":`
- Type-safe in Python code: `Priority.HIGH`
- IDE autocomplete works correctly

**Rationale**:
- Pydantic automatically handles `str` Enum serialization/deserialization
- Maintains backward compatibility with string-based JSON
- Provides type safety in Python code

**Applied To**: 
- `Priority`, `ArtifactStatus`, `RiskLevel`, `OperationType`, `StoryStatus` in `common_enums.py`

### 4. Structured Models for Unstructured Fields

**Pattern**: Replace unstructured `dict[str, Any]` fields with typed BaseModel classes:

```python
from pydantic import BaseModel, Field

class PlanDetails(BaseModel):
    summary: str
    estimated_duration_hours: float | None = None
    key_risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}
```

**Rationale**:
- Type safety for nested structures
- Validation of nested data
- Better IDE support and autocomplete
- Prevents invalid data structures
- Self-documenting code

**Applied To**:
- `PlanDetails` - Structured plan information
- `TaskInputs` - Task input parameters
- `TaskResults` - Task output results
- `RetryPolicy` - Retry configuration

### 5. Backward Compatibility Strategy

**Pattern**: Use `from_dict()` class methods that handle both formats:

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Artifact":
    """
    Load artifact from dictionary.
    Handles both old dataclass format and new Pydantic format.
    """
    # Try Pydantic validation first (new format)
    try:
        return cls.model_validate(data)
    except ValidationError:
        # Fall back to legacy format handling
        return cls._from_dict_legacy(data)
```

**Rationale**:
- Smooth migration path for existing code
- No breaking changes for artifact loading
- Gradual transition period
- Existing artifacts continue to work

**Applied To**: All artifact models have `from_dict()` methods

### 6. Default Values and Optional Fields

**Pattern**: Use `Field(default_factory=list)` for mutable defaults:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    items: list[str] = Field(default_factory=list)  # ✅ Correct
    # items: list[str] = []  # ❌ Wrong - mutable default
```

**Rationale**:
- Prevents shared mutable defaults (common Python gotcha)
- Each instance gets its own list/dict
- Pydantic best practice for collections

**Applied To**: All list and dict fields with defaults

### 7. Optional Fields with Union Types

**Pattern**: Use `|` syntax for optional fields (Python 3.10+):

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    optional_str: str | None = None  # ✅ Python 3.10+ syntax
    # optional_str: Optional[str] = None  # ✅ Also works
```

**Rationale**:
- Modern Python syntax (PEP 604)
- Cleaner and more readable
- Pydantic supports both styles

**Applied To**: All optional fields in artifact models

### 8. JSON Schema Generation

**Pattern**: Use Pydantic's built-in `model_json_schema()`:

```python
from pydantic import BaseModel

schema = MyModel.model_json_schema(
    mode="serialization",
    by_alias=False,
)
```

**Rationale**:
- Automatic schema generation from models
- Always in sync with model definitions
- No manual schema maintenance
- Supports JSON Schema Draft 2020-12

**Applied To**: Schema generation script in `scripts/generate_artifact_schemas.py`

### 9. Field Validation and Constraints

**Pattern**: Use Pydantic validators and Field constraints:

```python
from pydantic import BaseModel, Field

class RetryPolicy(BaseModel):
    max_retries: int = Field(default=0, ge=0)  # Greater than or equal to 0
    backoff_seconds: int = Field(default=60, ge=0)
    backoff_multiplier: float = Field(default=2.0, gt=0)  # Greater than 0
    max_backoff_seconds: int | None = Field(default=None, ge=0)
```

**Rationale**:
- Runtime validation of constraints
- Prevents invalid values (negative numbers, etc.)
- Self-documenting constraints
- Error messages indicate what went wrong

**Applied To**: `RetryPolicy` and numeric fields with constraints

### 10. Path Handling

**Pattern**: Use `pathlib.Path` with Pydantic:

```python
from pathlib import Path
from pydantic import BaseModel

class MyModel(BaseModel):
    file_path: Path | None = None
```

**Rationale**:
- Pydantic automatically serializes Path to string in JSON
- Deserializes string back to Path object
- Cross-platform path handling
- Type-safe path operations

**Applied To**: `EpicDocument`, `Story` models with `file_path` fields

## Migration Decisions

### Decision 1: Keep Legacy UserStory Dataclass

**Decision**: Keep `UserStory` dataclass for backward compatibility

**Rationale**:
- Existing code may reference `UserStory`
- Migration period requires gradual transition
- Can be removed in future major version
- No breaking changes

**Location**: `tapps_agents/workflow/planning_artifact.py`

### Decision 2: Unified Story Model

**Decision**: Create unified `Story` model in `story_models.py`

**Rationale**:
- Consolidates `UserStory` and `Epic.Story` features
- Single source of truth for story structure
- Migration methods provided: `from_user_story()`, `from_epic_story()`
- Epic.Story kept for backward compatibility

**Location**: `tapps_agents/workflow/story_models.py`

### Decision 3: Move StoryStatus to common_enums

**Decision**: Move `StoryStatus` enum to `common_enums.py`

**Rationale**:
- Resolves circular import issues
- Centralized enum definitions
- Reusable across modules
- Better organization

**Location**: `tapps_agents/workflow/common_enums.py`

### Decision 4: Enum Serialization Strategy

**Decision**: Use `str` Enum (not `IntEnum` or plain `Enum`)

**Rationale**:
- JSON compatibility (serializes to strings)
- String comparison works: `if status == "completed":`
- Type safety in Python code
- Backward compatible with existing JSON

**Applied To**: All enums in `common_enums.py`

## Testing Approach

### Backward Compatibility Testing

**Strategy**: Ensure existing tests continue to pass without modification

**Rationale**:
- Pydantic models support attribute access like dataclasses
- `from_dict()` methods handle legacy format
- Enum comparisons work with strings
- No breaking changes for consumers

**Result**: ✅ All existing tests pass without modification

### Validation Testing

**Strategy**: Test Pydantic validation catches invalid data

**Examples**:
- Unknown fields rejected (`extra="forbid"`)
- Invalid enum values rejected
- Type mismatches caught
- Constraint violations detected

## Performance Considerations

### Serialization Performance

**Finding**: Pydantic serialization is comparable to dataclass + `asdict()`

**Considerations**:
- JSON serialization: `model_dump(mode="json")` is optimized
- Schema generation: One-time cost, cached by Pydantic
- Validation: Small overhead, but catches errors early

**Conclusion**: Performance impact is negligible, benefits outweigh costs

### Memory Usage

**Finding**: Pydantic models have similar memory footprint to dataclasses

**Considerations**:
- Field definitions stored in `model_fields`
- Validation metadata minimal
- No significant memory overhead

**Conclusion**: Memory usage is acceptable

## Lessons Learned

### 1. Circular Import Resolution

**Issue**: Circular import when Epic models imported StoryStatus from story_models

**Solution**: Move shared enums to `common_enums.py`

**Lesson**: Centralize shared types/enums to avoid circular dependencies

### 2. Enum Comparison Behavior

**Finding**: `str` Enums compare correctly with strings in Python

**Example**:
```python
status = ArtifactStatus.COMPLETED
assert status == "completed"  # ✅ Works
assert status == ArtifactStatus.COMPLETED  # ✅ Works
```

**Lesson**: `str` Enum provides flexibility while maintaining type safety

### 3. Backward Compatibility Strategy

**Finding**: `from_dict()` method pattern works well for migration

**Lesson**: Class methods for alternative constructors provide clean migration path

### 4. TypedDict vs BaseModel

**Decision**: Use TypedDict for metadata, BaseModel for structured data

**Rationale**:
- TypedDict: Flexible, optional fields (metadata)
- BaseModel: Strict validation, required fields (structured data)

**Lesson**: Choose the right tool for the job

## References

- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Python TypedDict Documentation](https://docs.python.org/3/library/typing.html#typing.TypedDict)
- [Python Enum Documentation](https://docs.python.org/3/library/enum.html)
- [JSON Schema Specification](https://json-schema.org/)

## Applied Best Practices Summary

✅ **Strict Validation**: `model_config = {"extra": "forbid"}` on all models  
✅ **TypedDict for Metadata**: Flexible but typed metadata structures  
✅ **str Enum**: Type-safe enums that serialize to JSON strings  
✅ **Structured Models**: Replace unstructured dicts with typed BaseModel  
✅ **Mutable Defaults**: Use `Field(default_factory=list)`  
✅ **Optional Syntax**: Use `|` for optional types (Python 3.10+)  
✅ **Backward Compatibility**: `from_dict()` methods handle legacy format  
✅ **JSON Schema Generation**: Use `model_json_schema()` for schemas  
✅ **Field Constraints**: Use `Field(ge=0, gt=0)` for validation  
✅ **Path Handling**: Use `pathlib.Path` with Pydantic  

## Conclusion

The migration successfully applied Pydantic v2 best practices while maintaining full backward compatibility. The research findings guided key decisions around validation, enum handling, structured data models, and migration strategy. All artifacts now benefit from type safety, runtime validation, and automatic JSON schema generation.
