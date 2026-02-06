# Phase 4: Knowledge Synchronization API Reference

This document provides comprehensive API documentation for the Phase 4 Knowledge Synchronization modules in TappsCodingAgents.

## Table of Contents

1. [Module Overview](#module-overview)
2. [RagSynchronizer API](#ragsynchronizer-api)
3. [ProjectOverviewGenerator API](#projectoverviewgenerator-api)
4. [CLI Commands](#cli-commands)
5. [Usage Examples](#usage-examples)

---

## Module Overview

### Purpose

The Phase 4 Knowledge Synchronization system provides automated tools for keeping RAG (Retrieval-Augmented Generation) knowledge files synchronized with codebase changes. This includes:

- **Detecting package renames** using AST analysis
- **Finding stale imports** in documentation and knowledge files
- **Updating code examples** atomically with rollback support
- **Generating project overviews** with architecture detection
- **Creating component maps** with Mermaid diagrams

### Design Principles

All modules follow these design principles:

- **Small, focused functions** (< 100 lines each)
- **Clear separation of concerns**
- **Single responsibility principle**
- **Comprehensive error handling and logging**
- **Atomic file operations with rollback support**
- **Performance targets** for typical project sizes

### File Locations

| Module | Location |
|--------|----------|
| RagSynchronizer | `tapps_agents/core/sync/rag_synchronizer.py` |
| ProjectOverviewGenerator | `tapps_agents/core/generators/project_overview_generator.py` |
| CLI Commands | `tapps_agents/cli/commands/rag.py` |

---

## RagSynchronizer API

### Module: `tapps_agents.core.sync.rag_synchronizer`

The RagSynchronizer class synchronizes RAG knowledge files with codebase changes, detecting package renames and updating stale references.

### Data Classes

#### `Rename`

Represents a detected package/module rename.

```python
@dataclass
class Rename:
    old_name: str        # Original package/module name
    new_name: str        # New package/module name
    file_path: Path      # File where rename was detected
    confidence: float    # Confidence score (0.0-1.0)
```

**Validation:**
- `confidence` must be between 0.0 and 1.0 (inclusive)
- Raises `ValueError` if confidence is out of range

**Example:**
```python
from tapps_agents.core.sync.rag_synchronizer import Rename
from pathlib import Path

rename = Rename(
    old_name="old_package",
    new_name="new_package",
    file_path=Path("src/module.py"),
    confidence=0.85
)
```

---

#### `StaleReference`

Represents an outdated import/reference found in knowledge files.

```python
@dataclass
class StaleReference:
    file_path: Path       # Path to the knowledge file
    line_number: int      # Line number where stale import appears
    old_import: str       # The outdated import statement
    suggested_import: str # Suggested replacement import
    context: str          # Surrounding lines for context
```

**Example:**
```python
from tapps_agents.core.sync.rag_synchronizer import StaleReference
from pathlib import Path

ref = StaleReference(
    file_path=Path("docs/example.md"),
    line_number=42,
    old_import="old_module",
    suggested_import="new_module",
    context="```python\nimport old_module\n```"
)
```

---

#### `ChangeReport`

Comprehensive report of changes to be applied.

```python
@dataclass
class ChangeReport:
    timestamp: str                    # ISO format timestamp
    total_files: int                  # Number of files affected
    total_changes: int                # Total number of changes
    renames: list[Rename]             # List of detected renames
    stale_refs: list[StaleReference]  # List of stale references
    diff_preview: str                 # Human-readable diff preview
    backup_path: Path | None          # Path to backup (if created)
```

**Example:**
```python
from tapps_agents.core.sync.rag_synchronizer import ChangeReport, Rename, StaleReference

report = ChangeReport(
    timestamp="2024-01-15T10:30:00",
    total_files=5,
    total_changes=12,
    renames=[rename1, rename2],
    stale_refs=[ref1, ref2, ref3],
    diff_preview="Changes summary...",
    backup_path=Path(".tapps-agents/backups/backup_20240115_103000")
)
```

---

#### `BackupManifest`

Backup manifest with file checksums for integrity verification.

```python
@dataclass
class BackupManifest:
    timestamp: str                    # Backup timestamp (YYYYMMDD_HHMMSS)
    backup_dir: Path                  # Directory containing backups
    files: list[Path]                 # List of backed up files
    checksums: dict[str, str]         # Mapping of relative path -> SHA256 checksum
```

**Example:**
```python
from tapps_agents.core.sync.rag_synchronizer import BackupManifest

manifest = BackupManifest(
    timestamp="20240115_103000",
    backup_dir=Path(".tapps-agents/backups/backup_20240115_103000"),
    files=[Path("doc1.md"), Path("doc2.md")],
    checksums={
        "doc1.md": "abc123...",
        "doc2.md": "def456..."
    }
)
```

---

### Class: `RagSynchronizer`

#### Constructor

```python
def __init__(
    self,
    project_root: Path,
    knowledge_dir: Path | None = None,
    backup_dir: Path | None = None,
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_root` | `Path` | Required | Project root directory |
| `knowledge_dir` | `Path \| None` | `.tapps-agents/knowledge` | Knowledge base directory |
| `backup_dir` | `Path \| None` | `.tapps-agents/backups` | Backup storage directory |

**Raises:**
- `ValueError` if `project_root` does not exist

**Example:**
```python
from tapps_agents.core.sync.rag_synchronizer import RagSynchronizer
from pathlib import Path

# Default paths
sync = RagSynchronizer(Path("/path/to/project"))

# Custom paths
sync = RagSynchronizer(
    project_root=Path("/path/to/project"),
    knowledge_dir=Path("/path/to/project/docs/knowledge"),
    backup_dir=Path("/path/to/project/.backups")
)
```

---

#### Method: `detect_package_renames`

Detect package/module renames in codebase using AST analysis.

```python
def detect_package_renames(
    self,
    source_dir: Path | None = None
) -> list[Rename]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_dir` | `Path \| None` | `project_root` | Source directory to scan |

**Returns:** `list[Rename]` - List of detected rename objects with confidence scores

**Performance Target:** < 5 seconds for typical projects

**Example:**
```python
sync = RagSynchronizer(Path("/path/to/project"))
renames = sync.detect_package_renames()

# Scan specific directory
renames = sync.detect_package_renames(source_dir=Path("/path/to/project/src"))

for rename in renames:
    print(f"{rename.old_name} -> {rename.new_name} (confidence: {rename.confidence:.2f})")
```

---

#### Method: `find_stale_imports`

Find outdated imports in knowledge files.

```python
def find_stale_imports(
    self,
    current_imports: set[str] | None = None
) -> list[StaleReference]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `current_imports` | `set[str] \| None` | Auto-detected | Set of current valid imports |

**Returns:** `list[StaleReference]` - List of stale reference objects

**Performance Target:** < 3 seconds for typical knowledge bases

**Example:**
```python
sync = RagSynchronizer(Path("/path/to/project"))

# Auto-detect current imports from codebase
stale_refs = sync.find_stale_imports()

# Provide explicit set of current imports
current = {"os", "sys", "pathlib", "requests"}
stale_refs = sync.find_stale_imports(current_imports=current)

for ref in stale_refs:
    print(f"{ref.file_path}:{ref.line_number} - {ref.old_import}")
```

---

#### Method: `update_code_examples`

Update code examples in a knowledge file with regex replacement.

```python
def update_code_examples(
    self,
    file_path: Path,
    replacements: dict[str, str],
) -> bool
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | `Path` | Path to knowledge file to update |
| `replacements` | `dict[str, str]` | Dictionary mapping old patterns to new patterns |

**Returns:** `bool` - `True` if file was modified, `False` otherwise

**Features:**
- Atomic file operations (writes to temp file first)
- Graceful handling of non-existent files

**Example:**
```python
sync = RagSynchronizer(Path("/path/to/project"))

replacements = {
    "old_package": "new_package",
    "deprecated_function": "new_function"
}

modified = sync.update_code_examples(
    file_path=Path("docs/example.md"),
    replacements=replacements
)

if modified:
    print("File was updated")
else:
    print("No changes needed")
```

---

#### Method: `generate_change_report`

Generate detailed change report with diff view.

```python
def generate_change_report(
    self,
    renames: list[Rename],
    stale_refs: list[StaleReference],
) -> ChangeReport
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `renames` | `list[Rename]` | List of detected renames |
| `stale_refs` | `list[StaleReference]` | List of stale references |

**Returns:** `ChangeReport` - Comprehensive change summary

**Example:**
```python
sync = RagSynchronizer(Path("/path/to/project"))

renames = sync.detect_package_renames()
stale_refs = sync.find_stale_imports()

report = sync.generate_change_report(renames, stale_refs)

print(f"Files affected: {report.total_files}")
print(f"Total changes: {report.total_changes}")
print(report.diff_preview)
```

---

#### Method: `backup_knowledge_files`

Backup knowledge files with SHA256 checksums.

```python
def backup_knowledge_files(
    self,
    files: list[Path]
) -> BackupManifest
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `files` | `list[Path]` | List of files to backup |

**Returns:** `BackupManifest` - Backup metadata with checksums

**Features:**
- Creates timestamped backup directory
- Calculates SHA256 checksums for integrity verification
- Saves JSON manifest file
- Skips non-existent files with warning

**Example:**
```python
sync = RagSynchronizer(Path("/path/to/project"))

files_to_backup = [
    Path("docs/api.md"),
    Path("docs/guide.md"),
    Path("docs/examples.md")
]

manifest = sync.backup_knowledge_files(files_to_backup)

print(f"Backup created at: {manifest.backup_dir}")
print(f"Files backed up: {len(manifest.files)}")
print(f"Checksums: {manifest.checksums}")
```

---

#### Method: `apply_changes`

Apply changes atomically with rollback support.

```python
def apply_changes(
    self,
    changes: ChangeReport,
    backup_manifest: BackupManifest | None = None,
    dry_run: bool = False,
) -> bool
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `changes` | `ChangeReport` | Required | Changes to apply |
| `backup_manifest` | `BackupManifest \| None` | Auto-created | Backup for rollback |
| `dry_run` | `bool` | `False` | Simulate without applying |

**Returns:** `bool` - `True` if changes applied successfully

**Features:**
- Creates automatic backup if not provided
- Atomic operations with rollback on failure
- Dry run mode for preview

**Example:**
```python
sync = RagSynchronizer(Path("/path/to/project"))

# Generate report
renames = sync.detect_package_renames()
stale_refs = sync.find_stale_imports()
report = sync.generate_change_report(renames, stale_refs)

# Preview changes (dry run)
sync.apply_changes(report, dry_run=True)

# Apply changes with automatic backup
success = sync.apply_changes(report, dry_run=False)

if success:
    print("Changes applied successfully")
else:
    print("Changes failed, rollback performed")
```

---

## ProjectOverviewGenerator API

### Module: `tapps_agents.core.generators.project_overview_generator`

The ProjectOverviewGenerator class generates comprehensive project overviews from metadata and architecture analysis.

### Enums

#### `ArchitectureType`

Architecture pattern types that can be detected.

```python
class ArchitectureType(Enum):
    LAYERED = "layered"
    MVC = "mvc"
    CLEAN = "clean"
    HEXAGONAL = "hexagonal"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    CQRS = "cqrs"
    EVENT_DRIVEN = "event-driven"
    UNKNOWN = "unknown"
```

---

### Data Classes

#### `ProjectMetadata`

Project metadata extracted from configuration files.

```python
@dataclass
class ProjectMetadata:
    name: str                          # Project name
    version: str                       # Version string
    description: str = ""              # Project description
    authors: list[str] = []            # List of authors
    license: str = ""                  # License identifier
    dependencies: dict[str, str] = {}  # Package -> version mapping
    python_version: str = ""           # Required Python version
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `dict` | Convert to dictionary for serialization |

**Example:**
```python
from tapps_agents.core.generators.project_overview_generator import ProjectMetadata

metadata = ProjectMetadata(
    name="my-project",
    version="1.0.0",
    description="A sample project",
    authors=["Alice", "Bob"],
    license="MIT",
    dependencies={"requests": ">=2.28.0", "click": ">=8.0.0"},
    python_version=">=3.10"
)

# Convert to dictionary
data = metadata.to_dict()
```

---

#### `ArchitecturePattern`

Detected architecture pattern with confidence score.

```python
@dataclass
class ArchitecturePattern:
    pattern: ArchitectureType  # Detected pattern type
    confidence: float          # Confidence score (0.0-1.0)
    indicators: list[str] = [] # Directories/files that indicate this pattern
```

**Validation:**
- `confidence` must be between 0.0 and 1.0 (inclusive)
- Raises `ValueError` if confidence is out of range

**Example:**
```python
from tapps_agents.core.generators.project_overview_generator import (
    ArchitecturePattern,
    ArchitectureType
)

pattern = ArchitecturePattern(
    pattern=ArchitectureType.MVC,
    confidence=1.0,
    indicators=["models", "views", "controllers"]
)
```

---

#### `ComponentMap`

Component map with dependencies and Mermaid diagram.

```python
@dataclass
class ComponentMap:
    components: list[str] = []              # List of component names
    dependencies: dict[str, list[str]] = {} # Component -> dependencies mapping
    mermaid_diagram: str = ""               # Generated Mermaid diagram
```

**Example:**
```python
from tapps_agents.core.generators.project_overview_generator import ComponentMap

component_map = ComponentMap(
    components=["api", "core", "utils"],
    dependencies={"api": ["core"], "core": ["utils"]},
    mermaid_diagram="graph TD\n    api --> core\n    core --> utils"
)
```

---

### Class: `ProjectOverviewGenerator`

#### Constructor

```python
def __init__(
    self,
    project_root: Path,
    output_file: Path | None = None,
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_root` | `Path` | Required | Project root directory |
| `output_file` | `Path \| None` | `PROJECT_OVERVIEW.md` | Output file path |

**Raises:**
- `ValueError` if `project_root` does not exist

**Example:**
```python
from tapps_agents.core.generators.project_overview_generator import ProjectOverviewGenerator
from pathlib import Path

# Default output file
generator = ProjectOverviewGenerator(Path("/path/to/project"))

# Custom output file
generator = ProjectOverviewGenerator(
    project_root=Path("/path/to/project"),
    output_file=Path("/path/to/project/docs/OVERVIEW.md")
)
```

---

#### Method: `extract_project_metadata`

Extract project metadata from pyproject.toml or package.json.

```python
def extract_project_metadata(self) -> ProjectMetadata
```

**Returns:** `ProjectMetadata` - Extracted project information

**Raises:**
- `FileNotFoundError` if neither pyproject.toml nor package.json exists
- `ValueError` if file parsing fails

**Supported Files:**
- `pyproject.toml` (Python projects) - Supports `[project]` and `[tool.poetry]` sections
- `package.json` (Node.js projects)

**Priority:** `pyproject.toml` is preferred over `package.json` if both exist.

**Example:**
```python
generator = ProjectOverviewGenerator(Path("/path/to/project"))
metadata = generator.extract_project_metadata()

print(f"Project: {metadata.name} v{metadata.version}")
print(f"Description: {metadata.description}")
print(f"Authors: {', '.join(metadata.authors)}")
```

---

#### Method: `detect_architecture_patterns`

Detect architecture patterns from directory structure.

```python
def detect_architecture_patterns(self) -> list[ArchitecturePattern]
```

**Returns:** `list[ArchitecturePattern]` - Detected patterns sorted by confidence (highest first)

**Detection Rules:**

| Pattern | Indicators |
|---------|------------|
| MVC | `models`, `views`, `controllers` |
| Layered | `presentation`, `business`, `data`, `domain`, `application` |
| Clean/Hexagonal | `domain`, `application`, `infrastructure`, `interfaces` |
| Microservices | `services`, `api-gateway`, `gateway`, multiple `*-service` dirs |
| CQRS | `commands`, `queries` |

**Example:**
```python
generator = ProjectOverviewGenerator(Path("/path/to/project"))
patterns = generator.detect_architecture_patterns()

for pattern in patterns:
    print(f"{pattern.pattern.value}: {pattern.confidence:.0%}")
    print(f"  Indicators: {', '.join(pattern.indicators)}")
```

---

#### Method: `generate_component_map`

Generate component map with Mermaid diagram.

```python
def generate_component_map(self) -> ComponentMap
```

**Returns:** `ComponentMap` - Components, dependencies, and Mermaid diagram

**Features:**
- Scans top-level directories as components
- Ignores hidden directories (`.git`, `.vscode`, etc.)
- Ignores underscore-prefixed directories (`__pycache__`, `_private`)
- Generates Mermaid `graph TD` diagram
- Sanitizes names for Mermaid (replaces hyphens with underscores)

**Example:**
```python
generator = ProjectOverviewGenerator(Path("/path/to/project"))
component_map = generator.generate_component_map()

print(f"Components: {', '.join(component_map.components)}")
print("\nMermaid Diagram:")
print(component_map.mermaid_diagram)
```

---

#### Method: `generate_overview`

Generate comprehensive project overview in Markdown format.

```python
def generate_overview(self) -> str
```

**Returns:** `str` - Markdown-formatted project overview

**Sections Generated:**
1. Title (project name)
2. Version
3. Description (if available)
4. Authors (if available)
5. License (if available)
6. Architecture (primary pattern, confidence, indicators, other patterns)
7. Components (Mermaid diagram, component list)
8. Dependencies (Python version, key dependencies)
9. Footer with generation timestamp

**Example:**
```python
generator = ProjectOverviewGenerator(Path("/path/to/project"))
overview = generator.generate_overview()

print(overview)
# Or save to file manually
with open("OVERVIEW.md", "w") as f:
    f.write(overview)
```

---

#### Method: `update_overview`

Update project overview with incremental change detection.

```python
def update_overview(self, force: bool = False) -> bool
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force` | `bool` | `False` | Force update even if file is recent |

**Returns:** `bool` - `True` if overview was updated, `False` if no update needed

**Smart Update Logic:**
- Skips update if overview file is newer than config files
- Detects changes to `pyproject.toml` or `package.json`
- Force flag bypasses freshness check

**Example:**
```python
generator = ProjectOverviewGenerator(Path("/path/to/project"))

# Only update if config changed
updated = generator.update_overview()
if updated:
    print("Overview updated")
else:
    print("Overview is up-to-date")

# Force regeneration
generator.update_overview(force=True)
```

---

## CLI Commands

### Module: `tapps_agents.cli.commands.rag`

The `RagCommand` class provides CLI commands for RAG knowledge synchronization.

### Class: `RagCommand`

#### Constructor

```python
def __init__(self, project_root: Optional[Path] = None)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_root` | `Path \| None` | Current directory | Project root directory |

---

### Command: `sync`

Synchronize RAG knowledge files with codebase changes.

```python
def sync(
    self,
    dry_run: bool = False,
    auto_apply: bool = False,
    report_only: bool = False,
) -> dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dry_run` | `bool` | `False` | Simulate changes without applying |
| `auto_apply` | `bool` | `False` | Apply changes without confirmation |
| `report_only` | `bool` | `False` | Only generate and display report |

**Returns:** `dict` with keys:
- `status`: One of `"report_generated"`, `"no_changes"`, `"dry_run_success"`, `"dry_run_failed"`, `"changes_applied"`, `"changes_failed"`, `"confirmation_required"`, `"error"`
- `report`: Change report details (when applicable)
- `message`: Human-readable message (when applicable)
- `error`: Error message (when status is `"error"`)

**Example:**
```python
from tapps_agents.cli.commands.rag import RagCommand
from pathlib import Path

cmd = RagCommand(Path("/path/to/project"))

# Generate report only
result = cmd.sync(report_only=True)
print(result["report"]["diff_preview"])

# Dry run
result = cmd.sync(dry_run=True)

# Auto-apply changes
result = cmd.sync(auto_apply=True)
if result["status"] == "changes_applied":
    print("Changes applied successfully")
```

---

### Command: `generate_overview`

Generate project overview from metadata and architecture.

```python
def generate_overview(
    self,
    output_file: Optional[Path] = None,
    force: bool = False,
) -> dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_file` | `Path \| None` | `PROJECT_OVERVIEW.md` | Output file path |
| `force` | `bool` | `False` | Force regeneration |

**Returns:** `dict` with keys:
- `status`: `"success"` or `"error"`
- `updated`: Whether file was updated
- `output_file`: Path to generated file
- `overview_length`: Length of generated content
- `error`: Error message (when status is `"error"`)

**Example:**
```python
cmd = RagCommand(Path("/path/to/project"))

# Generate with defaults
result = cmd.generate_overview()
print(f"Generated: {result['output_file']}")

# Force regeneration to custom file
result = cmd.generate_overview(
    output_file=Path("docs/OVERVIEW.md"),
    force=True
)
```

---

### Command: `detect_architecture`

Detect architecture patterns from directory structure.

```python
def detect_architecture(self) -> dict
```

**Returns:** `dict` with keys:
- `status`: `"success"` or `"error"`
- `patterns`: List of detected patterns with confidence and indicators
- `error`: Error message (when status is `"error"`)

**Example:**
```python
cmd = RagCommand(Path("/path/to/project"))
result = cmd.detect_architecture()

if result["status"] == "success":
    for pattern in result["patterns"]:
        print(f"{pattern['pattern']}: {pattern['confidence']:.0%}")
        print(f"  Indicators: {pattern['indicators']}")
```

---

### Command: `extract_metadata`

Extract project metadata from configuration files.

```python
def extract_metadata(self) -> dict
```

**Returns:** `dict` with keys:
- `status`: `"success"` or `"error"`
- `metadata`: Project metadata dictionary
- `error`: Error message (when status is `"error"`)

**Example:**
```python
cmd = RagCommand(Path("/path/to/project"))
result = cmd.extract_metadata()

if result["status"] == "success":
    meta = result["metadata"]
    print(f"Project: {meta['name']} v{meta['version']}")
    print(f"Description: {meta['description']}")
    print(f"Dependencies: {len(meta['dependencies'])} packages")
```

---

## Usage Examples

### Complete Synchronization Workflow

```python
from pathlib import Path
from tapps_agents.core.sync.rag_synchronizer import RagSynchronizer

# Initialize synchronizer
project_root = Path("/path/to/project")
sync = RagSynchronizer(project_root)

# Step 1: Detect package renames
print("Detecting package renames...")
renames = sync.detect_package_renames()
print(f"Found {len(renames)} renames")

# Step 2: Find stale imports in knowledge files
print("Finding stale imports...")
stale_refs = sync.find_stale_imports()
print(f"Found {len(stale_refs)} stale references")

# Step 3: Generate change report
report = sync.generate_change_report(renames, stale_refs)
print(f"\nChange Report:")
print(f"  Files affected: {report.total_files}")
print(f"  Total changes: {report.total_changes}")
print(report.diff_preview)

# Step 4: Preview changes (dry run)
print("\nPreviewing changes...")
sync.apply_changes(report, dry_run=True)

# Step 5: Apply changes with backup
if report.total_changes > 0:
    confirm = input("Apply changes? [y/N]: ")
    if confirm.lower() == 'y':
        success = sync.apply_changes(report)
        if success:
            print("Changes applied successfully!")
        else:
            print("Changes failed, rollback performed")
```

### Generate Project Overview

```python
from pathlib import Path
from tapps_agents.core.generators.project_overview_generator import ProjectOverviewGenerator

# Initialize generator
project_root = Path("/path/to/project")
generator = ProjectOverviewGenerator(project_root)

# Extract and display metadata
metadata = generator.extract_project_metadata()
print(f"Project: {metadata.name}")
print(f"Version: {metadata.version}")
print(f"Description: {metadata.description}")

# Detect architecture
patterns = generator.detect_architecture_patterns()
primary = patterns[0]
print(f"\nArchitecture: {primary.pattern.value.title()}")
print(f"Confidence: {primary.confidence:.0%}")
print(f"Indicators: {', '.join(primary.indicators)}")

# Generate component map
component_map = generator.generate_component_map()
print(f"\nComponents: {', '.join(component_map.components)}")

# Generate and save overview
updated = generator.update_overview()
if updated:
    print(f"\nOverview saved to: {generator.output_file}")
```

### CLI Usage from Python

```python
from pathlib import Path
from tapps_agents.cli.commands.rag import RagCommand

cmd = RagCommand(Path("/path/to/project"))

# Extract metadata
meta_result = cmd.extract_metadata()
if meta_result["status"] == "success":
    print(f"Project: {meta_result['metadata']['name']}")

# Detect architecture
arch_result = cmd.detect_architecture()
if arch_result["status"] == "success":
    for p in arch_result["patterns"]:
        print(f"Pattern: {p['pattern']} ({p['confidence']:.0%})")

# Generate overview
overview_result = cmd.generate_overview(force=True)
if overview_result["status"] == "success":
    print(f"Overview: {overview_result['output_file']}")

# Sync knowledge files
sync_result = cmd.sync(report_only=True)
if sync_result["status"] == "report_generated":
    print(sync_result["report"]["diff_preview"])
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| `detect_package_renames` | < 5 seconds | For typical projects |
| `find_stale_imports` | < 3 seconds | For typical knowledge bases |
| `generate_component_map` | < 2 seconds | For 100+ directories |
| `generate_overview` | < 3 seconds | Full generation |

---

## Error Handling

All methods include comprehensive error handling:

- **File operations**: Gracefully handle missing files, permission errors
- **Parsing errors**: Catch and report invalid TOML/JSON
- **Path validation**: Validate paths exist before operations
- **Atomic operations**: Use temp files and rollback on failure
- **Logging**: All errors logged with appropriate levels

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [knowledge-base-guide.md](knowledge-base-guide.md) - Knowledge base organization
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration reference

---

*Generated for TappsCodingAgents Phase 4 - Knowledge Synchronization*
