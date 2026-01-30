# Reference Updating Data Models

**Document:** Data Model Specifications for Reference Updating System
**Version:** 1.0
**Date:** 2026-01-29
**Status:** Design Phase

---

## Overview

This document specifies the Pydantic v2 data models for the reference updating system. These models extend the existing `OperationResult` model to provide detailed information about reference updates during file rename/move operations.

**Design Principles:**
1. **Backward Compatible:** Works with existing `OperationResult.references_updated` field
2. **Pydantic v2:** Uses `ConfigDict` for configuration
3. **JSON Serializable:** All models support JSON export for reporting
4. **Detailed Tracking:** Provides file-level and pattern-level details

---

## Model Hierarchy

```
OperationResult (existing)
├── references_updated: int (existing field)
└── reference_details: Optional[ReferenceUpdateResult] (new optional field)

ReferenceUpdateResult (new)
├── files_updated: int
├── patterns_matched: Dict[str, int]
└── file_details: List[FileUpdateDetail]

FileUpdateDetail (new)
├── file_path: Path
├── matches: List[PatternMatch]
└── updated: bool

PatternMatch (new)
├── pattern_name: str
├── line_number: int
├── old_text: str
└── new_text: str
```

---

## Data Models

### 1. ReferenceUpdateResult

**Purpose:** Detailed results of reference updating operation

```python
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field


class ReferenceUpdateResult(BaseModel):
    """Detailed results of reference updating operation.

    This model provides comprehensive information about reference updates,
    including which files were updated, which patterns matched, and detailed
    match information for each file.

    Attributes:
        files_updated: Number of files that had references updated
        patterns_matched: Count of matches per pattern type (e.g., {"markdown": 5, "relative": 3})
        file_details: Optional detailed results per file (for dry-run or debugging)
    """

    files_updated: int = Field(
        ...,
        description="Number of files with updated references",
        ge=0
    )

    patterns_matched: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of matches per pattern type (e.g., markdown, relative)"
    )

    file_details: List['FileUpdateDetail'] = Field(
        default_factory=list,
        description="Detailed results per file (optional, for dry-run or debugging)"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "files_updated": 3,
                "patterns_matched": {
                    "markdown_link": 5,
                    "relative_path": 2
                },
                "file_details": []
            }
        }
    )

    @property
    def total_references(self) -> int:
        """Total number of references updated across all patterns."""
        return sum(self.patterns_matched.values())

    @property
    def pattern_summary(self) -> str:
        """Human-readable summary of patterns matched."""
        if not self.patterns_matched:
            return "No patterns matched"

        parts = [f"{count} {name}" for name, count in self.patterns_matched.items()]
        return ", ".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "files_updated": self.files_updated,
            "total_references": self.total_references,
            "patterns_matched": self.patterns_matched,
            "pattern_summary": self.pattern_summary,
            "file_details": [detail.to_dict() for detail in self.file_details]
        }
```

**Validation Rules:**
- `files_updated` must be ≥ 0
- `patterns_matched` keys must be valid pattern names
- `file_details` can be empty (optional detailed tracking)

**Usage Example:**
```python
result = ReferenceUpdateResult(
    files_updated=3,
    patterns_matched={
        "markdown_link": 5,
        "relative_path": 2
    },
    file_details=[]  # Optional, populate for dry-run
)

print(f"Updated {result.total_references} references in {result.files_updated} files")
print(f"Patterns: {result.pattern_summary}")
```

---

### 2. FileUpdateDetail

**Purpose:** Detailed information about updates in a single file

```python
class FileUpdateDetail(BaseModel):
    """Details of reference updates in a single file.

    This model tracks all pattern matches and replacements in a specific file.
    Useful for dry-run preview and debugging.

    Attributes:
        file_path: Path to the file that was scanned
        matches: List of pattern matches found in this file
        updated: Whether the file was actually modified (False in dry-run)
    """

    file_path: Path = Field(
        ...,
        description="Path to file that was scanned"
    )

    matches: List['PatternMatch'] = Field(
        default_factory=list,
        description="List of pattern matches found in this file"
    )

    updated: bool = Field(
        False,
        description="Whether file was actually modified (False in dry-run)"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "file_path": "docs/README.md",
                "matches": [
                    {
                        "pattern_name": "markdown_link",
                        "line_number": 42,
                        "old_text": "[link](old-name.md)",
                        "new_text": "[link](new-name.md)"
                    }
                ],
                "updated": True
            }
        }
    )

    @property
    def match_count(self) -> int:
        """Number of matches in this file."""
        return len(self.matches)

    @property
    def relative_path(self) -> Path:
        """Relative path from project root (if available)."""
        # This would be set by the scanner based on project_root
        return self.file_path

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": str(self.file_path),
            "match_count": self.match_count,
            "matches": [match.to_dict() for match in self.matches],
            "updated": self.updated
        }
```

**Validation Rules:**
- `file_path` must be a valid Path object
- `matches` must be a list of PatternMatch objects
- `updated` is a boolean flag

**Usage Example:**
```python
detail = FileUpdateDetail(
    file_path=Path("docs/README.md"),
    matches=[
        PatternMatch(
            pattern_name="markdown_link",
            line_number=42,
            old_text="[link](old-name.md)",
            new_text="[link](new-name.md)"
        )
    ],
    updated=True
)

print(f"{detail.file_path}: {detail.match_count} matches")
```

---

### 3. PatternMatch

**Purpose:** Single pattern match and replacement in a file

```python
class PatternMatch(BaseModel):
    """Single pattern match and replacement in a file.

    This model represents one detected reference that was (or will be) updated.
    Provides line-level detail for precise tracking and debugging.

    Attributes:
        pattern_name: Name of the pattern that matched (e.g., "markdown_link")
        line_number: Line number where the match occurred
        old_text: Original text that was matched
        new_text: Replacement text
    """

    pattern_name: str = Field(
        ...,
        description="Name of pattern that matched (e.g., markdown_link)",
        min_length=1
    )

    line_number: int = Field(
        ...,
        description="Line number where match occurred (1-indexed)",
        ge=1
    )

    old_text: str = Field(
        ...,
        description="Original text that was matched",
        min_length=1
    )

    new_text: str = Field(
        ...,
        description="Replacement text",
        min_length=1
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern_name": "markdown_link",
                "line_number": 42,
                "old_text": "[link](old-name.md)",
                "new_text": "[link](new-name.md)"
            }
        }
    )

    @property
    def changed(self) -> bool:
        """Whether the text actually changed."""
        return self.old_text != self.new_text

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern_name": self.pattern_name,
            "line_number": self.line_number,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "changed": self.changed
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"Line {self.line_number} ({self.pattern_name}): {self.old_text} → {self.new_text}"
```

**Validation Rules:**
- `pattern_name` must be non-empty string
- `line_number` must be ≥ 1 (1-indexed)
- `old_text` and `new_text` must be non-empty strings

**Usage Example:**
```python
match = PatternMatch(
    pattern_name="markdown_link",
    line_number=42,
    old_text="[link](old-name.md)",
    new_text="[link](new-name.md)"
)

print(str(match))
# Output: Line 42 (markdown_link): [link](old-name.md) → [link](new-name.md)
```

---

## Integration with Existing Models

### Enhanced OperationResult (Optional)

**Option 1: Keep Current (Minimal Change)**
```python
class OperationResult(BaseModel):
    """Result of a single cleanup operation."""
    # ... existing fields ...
    references_updated: int = Field(0, description="Number of cross-references updated", ge=0)
    # No changes needed - continue using simple count
```

**Option 2: Add Optional Details (Recommended for Dry-Run)**
```python
class OperationResult(BaseModel):
    """Result of a single cleanup operation."""
    # ... existing fields ...
    references_updated: int = Field(0, description="Number of cross-references updated", ge=0)
    reference_details: Optional[ReferenceUpdateResult] = Field(
        None,
        description="Detailed reference update information (optional, for dry-run/debug)"
    )
```

**Backward Compatibility:**
- Existing code using `references_updated` continues to work
- New code can optionally populate `reference_details` for dry-run
- No breaking changes to existing API

---

## JSON Schema Export

All models support automatic JSON schema generation:

```python
# Export JSON schema
schema = ReferenceUpdateResult.model_json_schema()

# Example schema output:
{
    "type": "object",
    "properties": {
        "files_updated": {
            "type": "integer",
            "minimum": 0,
            "description": "Number of files with updated references"
        },
        "patterns_matched": {
            "type": "object",
            "additionalProperties": {"type": "integer"}
        },
        "file_details": {
            "type": "array",
            "items": {"$ref": "#/$defs/FileUpdateDetail"}
        }
    },
    "required": ["files_updated"]
}
```

---

## Usage Examples

### Example 1: Simple Count (Current Usage)

```python
# RenameStrategy.execute() - current usage
result = OperationResult(
    operation_id="ren-001",
    action_type=ActionType.RENAME,
    source_files=[old_path],
    target_path=new_path,
    status="SUCCESS",
    references_updated=3  # Simple count
)
```

### Example 2: Detailed Tracking (Dry-Run)

```python
# ReferenceUpdater.scan_and_update_references() - enhanced usage
update_result = ReferenceUpdateResult(
    files_updated=3,
    patterns_matched={
        "markdown_link": 5,
        "relative_path": 2
    },
    file_details=[
        FileUpdateDetail(
            file_path=Path("docs/README.md"),
            matches=[
                PatternMatch(
                    pattern_name="markdown_link",
                    line_number=42,
                    old_text="[link](old-name.md)",
                    new_text="[link](new-name.md)"
                )
            ],
            updated=True
        )
    ]
)

# Use in OperationResult (optional)
result = OperationResult(
    operation_id="ren-001",
    action_type=ActionType.RENAME,
    source_files=[old_path],
    target_path=new_path,
    status="SUCCESS",
    references_updated=update_result.files_updated,
    reference_details=update_result  # Optional detailed tracking
)
```

### Example 3: Dry-Run Preview

```python
# Generate dry-run report
def generate_dry_run_report(result: ReferenceUpdateResult) -> str:
    """Generate human-readable dry-run report."""

    report = f"Reference Update Preview\n"
    report += f"========================\n\n"
    report += f"Files to update: {result.files_updated}\n"
    report += f"Total references: {result.total_references}\n"
    report += f"Patterns: {result.pattern_summary}\n\n"

    if result.file_details:
        report += "File Details:\n"
        for detail in result.file_details:
            report += f"\n{detail.file_path} ({detail.match_count} matches):\n"
            for match in detail.matches:
                report += f"  {match}\n"

    return report
```

---

## Comparison with Manual Implementation

### Current Manual Implementation

**Returns:** `int` (count of files updated)

```python
def scan_and_update_references(self, old_path, new_path, dry_run=False) -> int:
    """Scan all text files and update references.

    Returns:
        Number of references updated
    """
    references_updated = 0
    # ... scanning logic ...
    return references_updated
```

**Pros:**
- ✅ Simple
- ✅ Works well for current use case
- ✅ Minimal overhead

**Cons:**
- ⚠️ No detailed information for dry-run preview
- ⚠️ Can't see which patterns matched
- ⚠️ No file-level details

### Proposed Enhancement

**Returns:** `ReferenceUpdateResult` (detailed results)

```python
def scan_and_update_references(
    self,
    old_path: Path,
    new_path: Path,
    dry_run: bool = False
) -> ReferenceUpdateResult:
    """Scan all text files and update references.

    Returns:
        Detailed reference update results
    """
    result = ReferenceUpdateResult(
        files_updated=0,
        patterns_matched={},
        file_details=[] if dry_run else []  # Populate for dry-run
    )
    # ... scanning logic ...
    return result
```

**Pros:**
- ✅ Detailed information for dry-run
- ✅ Pattern-level tracking
- ✅ File-level details
- ✅ Better debugging

**Cons:**
- ⚠️ Slightly more complex
- ⚠️ More memory if tracking all details

**Recommendation:**
- Keep simple `int` return for normal execution
- Add optional `ReferenceUpdateResult` for dry-run mode
- Provide backward-compatible upgrade path

---

## Migration Strategy

### Phase 1: Add Models (No Breaking Changes)

```python
# Add new models to project_cleanup_agent.py
class ReferenceUpdateResult(BaseModel):
    ...

class FileUpdateDetail(BaseModel):
    ...

class PatternMatch(BaseModel):
    ...
```

### Phase 2: Enhance ReferenceUpdater (Backward Compatible)

```python
class ReferenceUpdater:
    def scan_and_update_references(
        self,
        old_path: Path,
        new_path: Path,
        dry_run: bool = False,
        detailed: bool = False  # New optional flag
    ) -> Union[int, ReferenceUpdateResult]:
        """Scan and update references.

        Args:
            detailed: If True, return ReferenceUpdateResult; if False, return int
        """
        if detailed:
            return ReferenceUpdateResult(...)
        else:
            return references_updated  # Simple count (backward compatible)
```

### Phase 3: Update Strategies (Optional)

```python
class RenameStrategy:
    async def execute(self, action, dry_run=False):
        # ...
        if dry_run:
            # Use detailed mode for dry-run preview
            result = self.reference_updater.scan_and_update_references(
                source, target, dry_run=True, detailed=True
            )
            return OperationResult(
                ...,
                references_updated=result.files_updated,
                reference_details=result
            )
        else:
            # Use simple mode for normal execution
            refs_updated = self.reference_updater.scan_and_update_references(
                source, target, dry_run=False, detailed=False
            )
            return OperationResult(
                ...,
                references_updated=refs_updated
            )
```

---

## Testing Strategy

### Model Validation Tests

```python
def test_reference_update_result_validation():
    """Test ReferenceUpdateResult validation."""

    # Valid model
    result = ReferenceUpdateResult(
        files_updated=3,
        patterns_matched={"markdown": 5}
    )
    assert result.files_updated == 3
    assert result.total_references == 5

    # Invalid: negative files_updated
    with pytest.raises(ValidationError):
        ReferenceUpdateResult(files_updated=-1)

def test_pattern_match_validation():
    """Test PatternMatch validation."""

    # Valid model
    match = PatternMatch(
        pattern_name="markdown",
        line_number=42,
        old_text="old",
        new_text="new"
    )
    assert match.changed is True

    # Invalid: line_number < 1
    with pytest.raises(ValidationError):
        PatternMatch(
            pattern_name="markdown",
            line_number=0,
            old_text="old",
            new_text="new"
        )
```

### JSON Serialization Tests

```python
def test_json_serialization():
    """Test JSON serialization."""

    result = ReferenceUpdateResult(
        files_updated=2,
        patterns_matched={"markdown": 3, "relative": 1},
        file_details=[
            FileUpdateDetail(
                file_path=Path("test.md"),
                matches=[
                    PatternMatch(
                        pattern_name="markdown",
                        line_number=1,
                        old_text="old",
                        new_text="new"
                    )
                ],
                updated=True
            )
        ]
    )

    # Export to JSON
    json_data = result.model_dump_json()

    # Reimport from JSON
    result2 = ReferenceUpdateResult.model_validate_json(json_data)

    assert result.files_updated == result2.files_updated
```

---

## Summary

**Data Models Designed:**
1. ✅ ReferenceUpdateResult - Detailed reference update results
2. ✅ FileUpdateDetail - Per-file update information
3. ✅ PatternMatch - Single pattern match and replacement

**Key Features:**
- Pydantic v2 with ConfigDict
- JSON serialization support
- Backward compatible with existing `OperationResult`
- Optional detailed tracking for dry-run mode
- Comprehensive validation rules

**Recommendation:**
- Implement models as optional enhancement
- Keep simple `int` return for normal execution
- Use detailed `ReferenceUpdateResult` for dry-run preview
- No breaking changes to existing API

---

**End of Data Model Specifications**
