# Pydantic Migration Guide

**Date**: January 2025  
**Version**: 1.0  
**Status**: Migration Complete ✅

This guide documents the migration of TappsCodingAgents artifact models from Python dataclasses to Pydantic v2 BaseModel classes.

## Overview

All workflow artifact models have been migrated from dataclasses to Pydantic BaseModel for:
- **Type safety**: Runtime validation and type checking
- **Better serialization**: Built-in JSON schema generation
- **Structured data**: TypedDict and structured models for metadata, plans, inputs, and results
- **Enum safety**: Type-safe Python Enums instead of string literals

## What Changed

### 1. Artifact Models (All Migrated to Pydantic)

All 10 artifact types now use Pydantic BaseModel:
- `PlanningArtifact` - User stories and planning data
- `DesignArtifact` - Architecture and component design
- `CodeArtifact` - Code generation artifacts
- `ReviewArtifact` - Code review results
- `TestingArtifact` - Test results and coverage
- `QualityArtifact` - Quality analysis results
- `OperationsArtifact` - Security, compliance, and deployment artifacts
- `EnhancementArtifact` - Prompt enhancement artifacts
- `DocumentationArtifact` - Documentation generation artifacts
- `ContextArtifact` - Context analysis artifacts

### 2. Enum Types (Type-Safe)

All string-based enums replaced with type-safe Python Enums:
- `Priority` - Priority levels (HIGH, MEDIUM, LOW)
- `ArtifactStatus` - Artifact execution status (PENDING, RUNNING, COMPLETED, etc.)
- `RiskLevel` - Risk levels (LOW, MEDIUM, HIGH)
- `OperationType` - Operation types (CREATE, UPDATE, DELETE, etc.)
- `StoryStatus` - Story status (NOT_STARTED, IN_PROGRESS, DONE, etc.)

**Location**: `tapps_agents/workflow/common_enums.py`

### 3. Structured Metadata Models

Unstructured fields replaced with typed models:
- `ArtifactMetadata` (TypedDict) - Flexible metadata structure
- `PlanDetails` (BaseModel) - Structured plan information
- `TaskInputs` (BaseModel) - Task input parameters
- `TaskResults` (BaseModel) - Task output results
- `RetryPolicy` (BaseModel) - Retry configuration

**Location**: `tapps_agents/workflow/metadata_models.py`

### 4. Unified Story Model

Created unified `Story` model combining features from:
- Legacy `UserStory` (PlanningArtifact)
- `Epic.Story` (Epic models)

**Location**: `tapps_agents/workflow/story_models.py`

### 5. Epic Models

Epic models migrated to Pydantic:
- `AcceptanceCriterion` - Story acceptance criteria
- `Story` - Epic story model (with Priority enum)
- `EpicDocument` - Epic document model

**Location**: `tapps_agents/epic/models.py`

## Backward Compatibility

The migration maintains full backward compatibility:

### Loading Artifacts

All artifact models have a `from_dict()` method that handles both:
- **Old format**: Dataclass-based artifacts (legacy)
- **New format**: Pydantic-based artifacts (current)

```python
from tapps_agents.workflow.planning_artifact import PlanningArtifact
from tapps_agents.workflow.artifact_helper import load_artifact

# Automatically handles both formats
artifact = load_artifact("planning.json", PlanningArtifact)
```

### Enum Compatibility

Pydantic `str` Enums automatically serialize/deserialize as strings:
- ✅ Compare with strings: `if artifact.status == "completed":`
- ✅ Serialize to JSON as strings
- ✅ Deserialize from JSON strings automatically

### Attribute Access

Pydantic models support attribute access like dataclasses:
- ✅ `artifact.status` (same as dataclass)
- ✅ `artifact.user_stories` (same as dataclass)
- ✅ Type hints work correctly

## Migration for Users

### For Code Using Artifacts

**No changes required** - All existing code continues to work:

```python
# This code works with both old and new artifacts
from tapps_agents.workflow.planning_artifact import PlanningArtifact

artifact = PlanningArtifact.from_dict(data)  # Handles both formats
print(artifact.status)  # Attribute access works
print(artifact.user_stories)  # Same as before
```

### For Code Creating Artifacts

**Recommended**: Use Pydantic models directly:

```python
from tapps_agents.workflow.planning_artifact import PlanningArtifact
from tapps_agents.workflow.common_enums import ArtifactStatus, Priority

# Create artifact with Pydantic model (recommended)
artifact = PlanningArtifact(
    artifact_type="planning",
    status=ArtifactStatus.COMPLETED,  # Use enum, not string
    user_stories=[...],
    metadata={"key": "value"},  # Dict works, but consider ArtifactMetadata
)
```

**Enum Usage**:
```python
from tapps_agents.workflow.common_enums import Priority, ArtifactStatus

# Type-safe enums
priority = Priority.HIGH  # Not "high" string
status = ArtifactStatus.COMPLETED  # Not "completed" string

# But they still serialize to strings in JSON
assert str(priority) == "high"
assert status == "completed"  # Also compares with strings
```

### For Code Using Epic Models

**No changes required** - Epic models support attribute access:

```python
from tapps_agents.epic.models import EpicDocument, Story
from tapps_agents.workflow.common_enums import Priority, StoryStatus

epic = EpicDocument(
    epic_number=1,
    title="Test Epic",
    goal="Goal",
    description="Description",
    priority=Priority.HIGH,  # Use enum
)

story = Story(
    epic_number=1,
    story_number=1,
    title="Story",
    description="Description",
    status=StoryStatus.NOT_STARTED,  # Use enum
    priority=Priority.MEDIUM,  # Use enum
)
```

## JSON Schemas

JSON Schema files are available for all artifact models:

**Location**: `schemas/1.0/`

**Usage**:
```python
import json
import jsonschema

# Load schema
with open("schemas/1.0/PlanningArtifact.json") as f:
    schema = json.load(f)

# Validate artifact data
with open("artifact.json") as f:
    artifact_data = json.load(f)

jsonschema.validate(instance=artifact_data, schema=schema)
```

See `schemas/README.md` for complete schema documentation.

## Benefits of Migration

1. **Type Safety**: Runtime validation catches errors early
2. **Better IDE Support**: Type hints and autocomplete work correctly
3. **JSON Schemas**: Automatic schema generation for API documentation
4. **Structured Data**: TypedDict and structured models prevent errors
5. **Enum Safety**: Type-safe enums prevent typos and invalid values
6. **Validation**: Pydantic validates data on creation
7. **Serialization**: Built-in JSON serialization with type checking

## Migration Status

✅ **Complete**: All artifacts migrated  
✅ **Tests Pass**: All existing tests pass without modification  
✅ **Backward Compatible**: Old artifacts can be loaded  
✅ **JSON Schemas**: Generated for all models  
✅ **Documentation**: This guide

## Technical Details

### Model Configuration

All Pydantic models use strict validation:
```python
model_config = {"extra": "forbid"}  # Reject unknown fields
```

### Enum Serialization

All enums are `str` Enums for JSON compatibility:
```python
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### Backward Compatibility Methods

All artifacts have `from_dict()` methods:
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Artifact":
    # Handles both old dataclass format and new Pydantic format
    ...
```

## Related Documentation

- **Status Document**: `docs/IMPLEMENTATION/pydantic_migration_status.md`
- **JSON Schemas**: `schemas/README.md`
- **API Reference**: `docs/API.md`
- **Architecture**: `docs/ARCHITECTURE.md`

## Support

If you encounter issues with the migration:
1. Check backward compatibility - use `from_dict()` for loading artifacts
2. Verify enum usage - use enum classes, not strings (but strings work too)
3. Check type hints - Pydantic models support all dataclass patterns
4. Review JSON schemas - validate your artifact data structure

## Conclusion

The migration to Pydantic provides better type safety, validation, and developer experience while maintaining full backward compatibility. All existing code continues to work, and new code can take advantage of Pydantic's features.
