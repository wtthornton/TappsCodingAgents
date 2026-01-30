# Project Cleanup Agent - Data Models Specification

**Version:** 1.0
**Created:** 2026-01-29
**Framework:** Pydantic v2.x

---

## Overview

This document defines the Pydantic data models for the Project Cleanup Agent. All models support JSON schema export, validation, and serialization.

---

## Enumerations

### ActionType

Defines the types of cleanup actions that can be performed.

```python
from enum import Enum

class ActionType(str, Enum):
    """Types of cleanup actions."""

    DELETE = "delete"      # Remove file permanently
    MOVE = "move"          # Move file to different location (e.g., archive)
    RENAME = "rename"      # Rename file (enforce naming conventions)
    MERGE = "merge"        # Merge similar files into one

    def __str__(self) -> str:
        return self.value
```

**Usage Examples:**
- `DELETE`: Remove duplicate files, obsolete documentation
- `MOVE`: Archive old implementation docs to `docs/archive/`
- `RENAME`: Convert `UPPERCASE.md` to `kebab-case.md`
- `MERGE`: Combine similar workflow documentation files

---

### SafetyLevel

Risk assessment for cleanup actions.

```python
class SafetyLevel(str, Enum):
    """Safety level for cleanup actions."""

    SAFE = "safe"            # Low risk, reversible, no dependencies
    MODERATE = "moderate"    # Medium risk, may have dependencies
    RISKY = "risky"          # High risk, critical file or many dependencies

    def __str__(self) -> str:
        return self.value

    @property
    def requires_confirmation(self) -> bool:
        """Whether this safety level requires user confirmation."""
        return self in (SafetyLevel.MODERATE, SafetyLevel.RISKY)
```

**Risk Assessment Criteria:**
- **SAFE**: Duplicate files (non-primary), files with no references
- **MODERATE**: Files with 1-5 references, recent files (<30 days)
- **RISKY**: Core documentation, files with >5 references, git-tracked files

---

### FileCategory

File categorization for cleanup planning.

```python
class FileCategory(str, Enum):
    """File categories for cleanup."""

    KEEP = "keep"          # Essential files to keep
    ARCHIVE = "archive"    # Move to archive directory
    DELETE = "delete"      # Remove permanently
    MERGE = "merge"        # Merge with other files
    RENAME = "rename"      # Rename for consistency

    def __str__(self) -> str:
        return self.value
```

---

## Core Data Models

### 1. DuplicateGroup

Represents a group of duplicate files with identical content.

```python
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

class DuplicateGroup(BaseModel):
    """Group of files with identical content."""

    hash: str = Field(
        ...,
        description="SHA256 hash of file content",
        min_length=64,
        max_length=64
    )

    files: list[Path] = Field(
        ...,
        description="List of file paths with identical content",
        min_length=2
    )

    size: int = Field(
        ...,
        description="File size in bytes",
        ge=0
    )

    recommendation: str = Field(
        ...,
        description="Recommended action for this group"
    )

    @field_validator('files')
    @classmethod
    def validate_files_exist(cls, v: list[Path]) -> list[Path]:
        """Validate that all files exist."""
        for file in v:
            if not file.exists():
                raise ValueError(f"File does not exist: {file}")
        return v

    @property
    def primary_file(self) -> Path:
        """Return the file to keep (first in list)."""
        return self.files[0]

    @property
    def duplicates(self) -> list[Path]:
        """Return files to delete/merge (all except first)."""
        return self.files[1:]

    @property
    def savings(self) -> int:
        """Potential space savings by removing duplicates."""
        return self.size * (len(self.files) - 1)

    class Config:
        json_schema_extra = {
            "example": {
                "hash": "a" * 64,
                "files": ["docs/file1.md", "docs/file2.md"],
                "size": 1024,
                "recommendation": "Keep docs/file1.md, delete docs/file2.md"
            }
        }
```

---

### 2. OutdatedFile

Represents a file that hasn't been modified recently.

```python
from datetime import datetime

class OutdatedFile(BaseModel):
    """File that hasn't been modified recently."""

    path: Path = Field(..., description="File path")

    last_modified: datetime = Field(
        ...,
        description="Last modification date from git history"
    )

    age_days: int = Field(
        ...,
        description="Age in days since last modification",
        ge=0
    )

    reference_count: int = Field(
        0,
        description="Number of references to this file",
        ge=0
    )

    recommendation: FileCategory = Field(
        ...,
        description="Recommended category for this file"
    )

    @property
    def is_obsolete(self) -> bool:
        """File is obsolete if >90 days old with no references."""
        return self.age_days > 90 and self.reference_count == 0

    class Config:
        json_schema_extra = {
            "example": {
                "path": "docs/OLD_FEATURE.md",
                "last_modified": "2023-10-01T00:00:00Z",
                "age_days": 120,
                "reference_count": 0,
                "recommendation": "archive"
            }
        }
```

---

### 3. NamingIssue

Represents a file with naming convention violation.

```python
class NamingIssue(BaseModel):
    """File with naming convention violation."""

    path: Path = Field(..., description="File path")

    current_name: str = Field(..., description="Current filename")

    suggested_name: str = Field(..., description="Suggested filename (kebab-case)")

    pattern_violation: str = Field(
        ...,
        description="Naming pattern violated (e.g., 'UPPERCASE', 'snake_case')"
    )

    @field_validator('suggested_name')
    @classmethod
    def validate_kebab_case(cls, v: str) -> str:
        """Validate suggested name is kebab-case."""
        if not v.replace('-', '').replace('.', '').isalnum():
            raise ValueError("Suggested name must be kebab-case")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "path": "docs/UPPERCASE_FILE.md",
                "current_name": "UPPERCASE_FILE.md",
                "suggested_name": "uppercase-file.md",
                "pattern_violation": "UPPERCASE"
            }
        }
```

---

### 4. AnalysisReport

Comprehensive analysis report of project structure.

```python
class AnalysisReport(BaseModel):
    """Analysis report of project structure."""

    total_files: int = Field(
        ...,
        description="Total number of files analyzed",
        ge=0
    )

    total_size: int = Field(
        ...,
        description="Total size of all files in bytes",
        ge=0
    )

    duplicates: list[DuplicateGroup] = Field(
        default_factory=list,
        description="Groups of duplicate files"
    )

    outdated_files: list[OutdatedFile] = Field(
        default_factory=list,
        description="Files not modified recently"
    )

    naming_issues: list[NamingIssue] = Field(
        default_factory=list,
        description="Files with naming convention violations"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )

    scan_path: Path = Field(
        ...,
        description="Root path that was analyzed"
    )

    @property
    def duplicate_count(self) -> int:
        """Total number of duplicate files."""
        return sum(len(group.duplicates) for group in self.duplicates)

    @property
    def potential_savings(self) -> int:
        """Total potential space savings from removing duplicates."""
        return sum(group.savings for group in self.duplicates)

    @property
    def obsolete_file_count(self) -> int:
        """Number of obsolete files (>90 days, no refs)."""
        return sum(1 for f in self.outdated_files if f.is_obsolete)

    def to_markdown(self) -> str:
        """Generate markdown report."""
        return f"""# Analysis Report

**Analyzed:** {self.timestamp.isoformat()}
**Path:** {self.scan_path}
**Total Files:** {self.total_files}
**Total Size:** {self.total_size / 1024 / 1024:.2f} MB

## Duplicates
- **Groups:** {len(self.duplicates)}
- **Files:** {self.duplicate_count}
- **Potential Savings:** {self.potential_savings / 1024:.2f} KB

## Outdated Files
- **Total:** {len(self.outdated_files)}
- **Obsolete:** {self.obsolete_file_count}

## Naming Issues
- **Total:** {len(self.naming_issues)}
"""

    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 229,
                "total_size": 3145728,
                "duplicates": [],
                "outdated_files": [],
                "naming_issues": [],
                "timestamp": "2026-01-29T12:00:00Z",
                "scan_path": "docs/"
            }
        }
```

---

### 5. CleanupAction

Individual cleanup action to be performed.

```python
class CleanupAction(BaseModel):
    """Individual cleanup action."""

    action_type: ActionType = Field(..., description="Type of action")

    source_files: list[Path] = Field(
        ...,
        description="Source file(s) for this action",
        min_length=1
    )

    target_path: Path | None = Field(
        None,
        description="Target path (for MOVE/RENAME actions)"
    )

    rationale: str = Field(
        ...,
        description="Explanation for this action",
        min_length=10
    )

    priority: int = Field(
        ...,
        description="Priority level (1=low, 2=medium, 3=high)",
        ge=1,
        le=3
    )

    safety_level: SafetyLevel = Field(
        ...,
        description="Risk assessment for this action"
    )

    estimated_savings: int = Field(
        0,
        description="Estimated space savings in bytes",
        ge=0
    )

    @field_validator('target_path')
    @classmethod
    def validate_target_required(cls, v: Path | None, info) -> Path | None:
        """Validate target path is provided for MOVE/RENAME actions."""
        action_type = info.data.get('action_type')
        if action_type in (ActionType.MOVE, ActionType.RENAME) and v is None:
            raise ValueError(f"target_path required for {action_type} action")
        return v

    @property
    def requires_confirmation(self) -> bool:
        """Whether this action requires user confirmation."""
        return self.safety_level.requires_confirmation

    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "delete",
                "source_files": ["docs/duplicate.md"],
                "target_path": None,
                "rationale": "Duplicate of docs/original.md with identical content",
                "priority": 2,
                "safety_level": "safe",
                "estimated_savings": 1024
            }
        }
```

---

### 6. CleanupPlan

Complete cleanup plan with prioritized actions.

```python
from typing import Dict

class CleanupPlan(BaseModel):
    """Complete cleanup plan with prioritized actions."""

    actions: list[CleanupAction] = Field(
        ...,
        description="List of cleanup actions to perform"
    )

    priorities: Dict[str, int] = Field(
        default_factory=dict,
        description="Action counts by priority (high/medium/low)"
    )

    dependencies: Dict[str, list[str]] = Field(
        default_factory=dict,
        description="Action dependencies (action_id -> [dependent_action_ids])"
    )

    estimated_savings: int = Field(
        ...,
        description="Total estimated space savings in bytes",
        ge=0
    )

    estimated_file_reduction: float = Field(
        ...,
        description="Estimated file reduction percentage",
        ge=0.0,
        le=100.0
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When plan was created"
    )

    @property
    def high_priority_count(self) -> int:
        """Number of high priority actions."""
        return sum(1 for a in self.actions if a.priority == 3)

    @property
    def medium_priority_count(self) -> int:
        """Number of medium priority actions."""
        return sum(1 for a in self.actions if a.priority == 2)

    @property
    def low_priority_count(self) -> int:
        """Number of low priority actions."""
        return sum(1 for a in self.actions if a.priority == 1)

    @property
    def risky_action_count(self) -> int:
        """Number of risky actions."""
        return sum(1 for a in self.actions if a.safety_level == SafetyLevel.RISKY)

    def get_actions_by_priority(self, priority: int) -> list[CleanupAction]:
        """Get actions by priority level."""
        return [a for a in self.actions if a.priority == priority]

    def to_markdown(self) -> str:
        """Generate markdown summary of plan."""
        return f"""# Cleanup Plan

**Created:** {self.created_at.isoformat()}
**Total Actions:** {len(self.actions)}
**Estimated Savings:** {self.estimated_savings / 1024 / 1024:.2f} MB
**File Reduction:** {self.estimated_file_reduction:.1f}%

## Actions by Priority
- **High:** {self.high_priority_count}
- **Medium:** {self.medium_priority_count}
- **Low:** {self.low_priority_count}

## Safety Assessment
- **Risky Actions:** {self.risky_action_count}
"""

    class Config:
        json_schema_extra = {
            "example": {
                "actions": [],
                "priorities": {"high": 5, "medium": 10, "low": 15},
                "dependencies": {},
                "estimated_savings": 1572864,
                "estimated_file_reduction": 45.0,
                "created_at": "2026-01-29T12:00:00Z"
            }
        }
```

---

### 7. OperationResult

Result of a single cleanup operation.

```python
class OperationResult(BaseModel):
    """Result of a single cleanup operation."""

    operation_id: str = Field(..., description="Unique operation ID")

    action_type: ActionType = Field(..., description="Type of action performed")

    source_files: list[Path] = Field(..., description="Source file(s)")

    target_path: Path | None = Field(None, description="Target path (if applicable)")

    status: str = Field(
        ...,
        description="Operation status",
        pattern="^(SUCCESS|FAILED|SKIPPED)$"
    )

    error_message: str | None = Field(
        None,
        description="Error message if operation failed"
    )

    references_updated: int = Field(
        0,
        description="Number of cross-references updated",
        ge=0
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When operation was performed"
    )

    @property
    def succeeded(self) -> bool:
        """Whether operation succeeded."""
        return self.status == "SUCCESS"

    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "op-001",
                "action_type": "rename",
                "source_files": ["docs/UPPERCASE.md"],
                "target_path": "docs/kebab-case.md",
                "status": "SUCCESS",
                "error_message": None,
                "references_updated": 3,
                "timestamp": "2026-01-29T12:00:00Z"
            }
        }
```

---

### 8. ExecutionReport

Complete execution report for cleanup operations.

```python
class ExecutionReport(BaseModel):
    """Complete execution report."""

    operations: list[OperationResult] = Field(
        ...,
        description="List of operation results"
    )

    files_modified: int = Field(
        ...,
        description="Total number of files modified",
        ge=0
    )

    files_deleted: int = Field(
        0,
        description="Number of files deleted",
        ge=0
    )

    files_moved: int = Field(
        0,
        description="Number of files moved",
        ge=0
    )

    files_renamed: int = Field(
        0,
        description="Number of files renamed",
        ge=0
    )

    backup_location: Path | None = Field(
        None,
        description="Path to backup archive"
    )

    started_at: datetime = Field(..., description="Execution start time")

    completed_at: datetime = Field(..., description="Execution completion time")

    dry_run: bool = Field(
        False,
        description="Whether this was a dry-run (no actual changes)"
    )

    @property
    def success_count(self) -> int:
        """Number of successful operations."""
        return sum(1 for op in self.operations if op.succeeded)

    @property
    def failure_count(self) -> int:
        """Number of failed operations."""
        return sum(1 for op in self.operations if op.status == "FAILED")

    @property
    def duration_seconds(self) -> float:
        """Execution duration in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    def to_markdown(self) -> str:
        """Generate markdown execution report."""
        return f"""# Execution Report

**Started:** {self.started_at.isoformat()}
**Completed:** {self.completed_at.isoformat()}
**Duration:** {self.duration_seconds:.2f}s
**Dry Run:** {self.dry_run}

## Results
- **Total Operations:** {len(self.operations)}
- **Successful:** {self.success_count}
- **Failed:** {self.failure_count}

## Files Modified
- **Deleted:** {self.files_deleted}
- **Moved:** {self.files_moved}
- **Renamed:** {self.files_renamed}
- **Total:** {self.files_modified}

## Backup
- **Location:** {self.backup_location}
"""

    class Config:
        json_schema_extra = {
            "example": {
                "operations": [],
                "files_modified": 30,
                "files_deleted": 10,
                "files_moved": 15,
                "files_renamed": 5,
                "backup_location": ".cleanup-backups/backup-20260129.zip",
                "started_at": "2026-01-29T12:00:00Z",
                "completed_at": "2026-01-29T12:00:30Z",
                "dry_run": False
            }
        }
```

---

## JSON Schema Export

All models can export JSON schemas for API documentation and validation:

```python
# Export individual model schema
schema = AnalysisReport.model_json_schema()

# Export all schemas
from pathlib import Path
import json

def export_all_schemas(output_dir: Path) -> None:
    """Export all model schemas to JSON files."""
    models = [
        AnalysisReport,
        CleanupPlan,
        CleanupAction,
        ExecutionReport,
        DuplicateGroup,
        OutdatedFile,
        NamingIssue,
        OperationResult
    ]

    for model in models:
        schema = model.model_json_schema()
        output_file = output_dir / f"{model.__name__}_schema.json"
        output_file.write_text(json.dumps(schema, indent=2))
```

---

## Usage Examples

### Creating an Analysis Report

```python
from pathlib import Path
from datetime import datetime

# Create analysis report
report = AnalysisReport(
    total_files=229,
    total_size=3145728,
    duplicates=[
        DuplicateGroup(
            hash="a" * 64,
            files=[Path("docs/file1.md"), Path("docs/file2.md")],
            size=1024,
            recommendation="Keep file1.md, delete file2.md"
        )
    ],
    outdated_files=[],
    naming_issues=[],
    scan_path=Path("docs/")
)

# Export to JSON
json_data = report.model_dump_json(indent=2)

# Export to dict
dict_data = report.model_dump()

# Generate markdown
markdown = report.to_markdown()
```

### Creating a Cleanup Plan

```python
# Create cleanup plan
plan = CleanupPlan(
    actions=[
        CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[Path("docs/duplicate.md")],
            rationale="Duplicate content",
            priority=2,
            safety_level=SafetyLevel.SAFE,
            estimated_savings=1024
        )
    ],
    estimated_savings=1024,
    estimated_file_reduction=45.0
)

# Save to file
Path("cleanup-plan.json").write_text(plan.model_dump_json(indent=2))

# Load from file
loaded_plan = CleanupPlan.model_validate_json(
    Path("cleanup-plan.json").read_text()
)
```

---

## Validation Examples

```python
from pydantic import ValidationError

# Valid action
action = CleanupAction(
    action_type=ActionType.RENAME,
    source_files=[Path("docs/OLD.md")],
    target_path=Path("docs/new.md"),
    rationale="Enforce naming convention",
    priority=2,
    safety_level=SafetyLevel.MODERATE
)

# Invalid action (missing target_path for RENAME)
try:
    invalid_action = CleanupAction(
        action_type=ActionType.RENAME,
        source_files=[Path("docs/OLD.md")],
        target_path=None,  # Error: required for RENAME
        rationale="Test",
        priority=2,
        safety_level=SafetyLevel.SAFE
    )
except ValidationError as e:
    print(e)
```

---

**End of Data Models Specification**
