# JSON Schemas for TappsCodingAgents Artifacts

This directory contains JSON Schema files generated from Pydantic artifact models.

## Schema Version: 1.0

All schemas in the `1.0/` directory are generated from Pydantic BaseModel classes using Pydantic's `model_json_schema()` method.

## Generated Schemas

### Artifact Models (10)
- `PlanningArtifact.json` - Planning artifact schema
- `DesignArtifact.json` - Design and architecture artifact schema
- `CodeArtifact.json` - Code generation artifact schema
- `ReviewArtifact.json` - Code review artifact schema
- `TestingArtifact.json` - Testing artifact schema
- `QualityArtifact.json` - Quality analysis artifact schema
- `OperationsArtifact.json` - Operations artifact schema
- `EnhancementArtifact.json` - Prompt enhancement artifact schema
- `DocumentationArtifact.json` - Documentation artifact schema
- `ContextArtifact.json` - Context analysis artifact schema

### Nested Models (19+)
- Component, CodeChange, ReviewComment
- TestResult, CoverageSummary, ToolResult
- SecurityIssue, ComplianceCheck, DeploymentStep, InfrastructureFile
- EnhancementStage, DocFileResult
- LibraryCacheEntry, ProjectProfile
- PlanDetails, TaskInputs, TaskResults, RetryPolicy
- Story (unified story model)

## Usage

### Schema Validation

You can use these schemas to validate JSON artifact data:

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

### API Documentation

These schemas can be used to generate API documentation, OpenAPI specifications, or client libraries.

### Schema Index

See `1.0/index.json` for a complete list of all generated schemas with metadata.

## Regenerating Schemas

To regenerate schemas after model changes:

```bash
python scripts/generate_artifact_schemas.py schemas 1.0
```

## Schema Format

All schemas follow JSON Schema Draft 2020-12 format and include:
- `$schema`: JSON Schema version
- `$id`: Unique schema identifier
- `title`: Model class name
- `description`: Model docstring
- `version`: Schema version (1.0)
- Full property definitions with types, constraints, and defaults

## Migration Notes

These schemas are generated from Pydantic v2 BaseModel classes that were migrated from dataclasses in January 2025. The schemas reflect:
- Type-safe enums (ArtifactStatus, Priority, OperationType, etc.)
- Structured metadata models (PlanDetails, TaskInputs, TaskResults)
- Validation constraints (field types, min/max values, etc.)
- Required vs optional fields
