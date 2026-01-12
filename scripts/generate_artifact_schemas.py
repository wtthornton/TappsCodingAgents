"""
Generate JSON Schemas for all Pydantic artifact models.

Generates JSON Schema files for all workflow artifacts using Pydantic's
model_json_schema() method. Schemas are exported to schemas/v1.0/ directory.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import os

    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Import all artifact models
from tapps_agents.workflow.code_artifact import CodeArtifact, CodeChange
from tapps_agents.workflow.context_artifact import (
    ContextArtifact,
    LibraryCacheEntry,
    ProjectProfile,
)
from tapps_agents.workflow.design_artifact import Component, DesignArtifact
from tapps_agents.workflow.docs_artifact import DocFileResult, DocumentationArtifact
from tapps_agents.workflow.enhancement_artifact import (
    EnhancementArtifact,
    EnhancementStage,
)
from tapps_agents.workflow.ops_artifact import (
    ComplianceCheck,
    DeploymentStep,
    InfrastructureFile,
    OperationsArtifact,
    SecurityIssue,
)
from tapps_agents.workflow.planning_artifact import PlanningArtifact
from tapps_agents.workflow.quality_artifact import QualityArtifact, ToolResult
from tapps_agents.workflow.review_artifact import ReviewArtifact, ReviewComment
from tapps_agents.workflow.testing_artifact import (
    CoverageSummary,
    TestingArtifact,
    TestResult,
)
from tapps_agents.epic.models import AcceptanceCriterion, EpicDocument, Story
from tapps_agents.workflow.metadata_models import (
    PlanDetails,
    RetryPolicy,
    TaskInputs,
    TaskResults,
)
from tapps_agents.workflow.story_models import Story as UnifiedStory


def generate_schema_file(
    model_class: type[Any], output_dir: Path, schema_version: str = "1.0"
) -> Path:
    """
    Generate JSON schema file for a Pydantic model.

    Args:
        model_class: Pydantic model class
        output_dir: Directory to write schema file
        schema_version: Schema version (default: "1.0")

    Returns:
        Path to generated schema file

    Raises:
        AttributeError: If model_class is not a Pydantic BaseModel
    """
    # Check if model has model_json_schema method (Pydantic BaseModel)
    if not hasattr(model_class, "model_json_schema"):
        raise AttributeError(f"{model_class.__name__} is not a Pydantic BaseModel")

    # Generate JSON schema using Pydantic's model_json_schema()
    schema = model_class.model_json_schema(
        mode="serialization",
        by_alias=False,
    )

    # Add schema metadata
    schema_with_metadata = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://tapps-coding-agents.com/schemas/{schema_version}/{model_class.__name__}.json",
        "title": model_class.__name__,
        "description": model_class.__doc__ or f"JSON Schema for {model_class.__name__}",
        "version": schema_version,
        **schema,
    }

    # Write schema file
    output_dir.mkdir(parents=True, exist_ok=True)
    schema_file = output_dir / f"{model_class.__name__}.json"
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(schema_with_metadata, f, indent=2, ensure_ascii=False)

    return schema_file


def generate_all_schemas(output_base: Path = Path("schemas"), schema_version: str = "1.0") -> dict[str, Path]:
    """
    Generate JSON schemas for all artifact models.

    Args:
        output_base: Base directory for schema files (default: "schemas")
        schema_version: Schema version (default: "1.0")

    Returns:
        Dictionary mapping model names to schema file paths
    """
    output_dir = output_base / schema_version
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files: dict[str, Path] = {}

    # Artifact models (main artifacts)
    artifact_models = [
        PlanningArtifact,
        DesignArtifact,
        CodeArtifact,
        ReviewArtifact,
        TestingArtifact,
        QualityArtifact,
        OperationsArtifact,
        EnhancementArtifact,
        DocumentationArtifact,
        ContextArtifact,
    ]

    # Nested models (components of artifacts)
    nested_models = [
        # Planning
        # (UserStory is legacy, skipped)
        # Design
        Component,
        # Code
        CodeChange,
        # Review
        ReviewComment,
        # Testing
        TestResult,
        CoverageSummary,
        # Quality
        ToolResult,
        # Operations
        SecurityIssue,
        ComplianceCheck,
        DeploymentStep,
        InfrastructureFile,
        # Enhancement
        EnhancementStage,
        # Documentation
        DocFileResult,
        # Context
        LibraryCacheEntry,
        ProjectProfile,
        # Epic
        AcceptanceCriterion,
        Story,
        EpicDocument,
        # Metadata models
        PlanDetails,
        TaskInputs,
        TaskResults,
        RetryPolicy,
        # Story models
        UnifiedStory,
    ]

    # Generate schemas for main artifacts
    print(f"Generating schemas for {len(artifact_models)} artifact models...")
    for model in artifact_models:
        schema_file = generate_schema_file(model, output_dir, schema_version)
        generated_files[model.__name__] = schema_file
        print(f"  [OK] Generated: {schema_file.name}")

    # Generate schemas for nested models
    print(f"\nGenerating schemas for {len(nested_models)} nested models...")
    for model in nested_models:
        try:
            schema_file = generate_schema_file(model, output_dir, schema_version)
            generated_files[model.__name__] = schema_file
            print(f"  [OK] Generated: {schema_file.name}")
        except AttributeError as e:
            print(f"  [SKIP] {model.__name__}: {e}")
        except Exception as e:
            print(f"  [ERROR] {model.__name__}: {e}")

    # Create index file listing all schemas
    index_file = output_dir / "index.json"
    index_data = {
        "schema_version": schema_version,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "schemas": {
            name: {
                "file": str(path.relative_to(output_base)),
                "model": name,
            }
            for name, path in generated_files.items()
        },
        "artifact_models": [m.__name__ for m in artifact_models],
        "nested_models": [m.__name__ for m in nested_models],
    }

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Generated {len(generated_files)} schema files")
    print(f"[OK] Created index: {index_file}")
    print(f"\nAll schemas written to: {output_dir}")

    return generated_files


if __name__ == "__main__":
    import sys

    output_base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("schemas")
    schema_version = sys.argv[2] if len(sys.argv) > 2 else "1.0"

    try:
        generated = generate_all_schemas(output_base, schema_version)
        print(f"\n[OK] Successfully generated {len(generated)} JSON schema files")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error generating schemas: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
