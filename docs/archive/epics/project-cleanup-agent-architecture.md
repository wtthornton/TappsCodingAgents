# Project Cleanup Agent - System Architecture

**Version:** 1.0
**Created:** 2026-01-29
**Architecture Pattern:** Layered Architecture with Strategy, Command, and Observer patterns

---

## Architecture Overview

The Project Cleanup Agent is designed as a modular, layered system for automated project structure analysis and cleanup. The architecture emphasizes **safety**, **modularity**, and **reversibility** for file operations.

### Architecture Pattern

**Primary Pattern:** Layered Architecture (3 layers)
- **Presentation Layer:** CLI interface (CleanupAgent + Rich console)
- **Business Logic Layer:** Analysis and planning (ProjectAnalyzer, CleanupPlanner)
- **Data Access Layer:** File operations (CleanupExecutor + GitPython)

**Supporting Patterns:**
- **Strategy Pattern:** Pluggable cleanup strategies (DeleteStrategy, MergeStrategy, RenameStrategy)
- **Command Pattern:** Reversible operations with rollback support
- **Observer Pattern:** Progress notifications and event logging

---

## System Components

### 1. ProjectAnalyzer (Analysis Layer)

**Responsibility:** Analyze project structure and identify cleanup opportunities

**Key Functions:**
- `scan_directory_structure(path: Path) -> DirectoryTree`
- `detect_duplicates(files: List[Path]) -> List[DuplicateGroup]`
- `analyze_naming_patterns(files: List[Path]) -> NamingAnalysis`
- `detect_outdated_files(files: List[Path]) -> List[OutdatedFile]`
- `generate_analysis_report() -> AnalysisReport`

**Dependencies:**
- `pathlib` - Cross-platform path operations
- `hashlib` - Content-based duplicate detection (SHA256)
- `GitPython` - Git history analysis for file age
- `aiofiles` - Async file I/O for performance

**Data Structures:**
```python
@dataclass
class AnalysisReport:
    total_files: int
    total_size: int
    duplicates: List[DuplicateGroup]
    outdated_files: List[OutdatedFile]
    naming_issues: List[NamingIssue]
    recommendations: List[Recommendation]

@dataclass
class DuplicateGroup:
    hash: str
    files: List[Path]
    size: int
    recommendation: str  # "Keep first, delete/merge others"
```

**Performance:**
- Async file scanning for parallel I/O
- Stream-based hashing (no full file load)
- Target: 229 files in < 10 seconds

---

### 2. CleanupPlanner (Planning Layer)

**Responsibility:** Categorize files and generate actionable cleanup plans

**Key Functions:**
- `categorize_files(analysis: AnalysisReport) -> FileCategorization`
- `detect_content_similarity(files: List[Path]) -> SimilarityMatrix`
- `build_dependency_map(files: List[Path]) -> DependencyGraph`
- `prioritize_actions(actions: List[Action]) -> PrioritizedPlan`
- `generate_cleanup_plan() -> CleanupPlan`

**Dependencies:**
- `difflib` - Text similarity analysis (SequenceMatcher)
- `networkx` (optional) - Dependency graph analysis
- `pydantic` - Data validation for plans

**File Categorization Rules:**
```
KEEP:     Referenced files, core docs, recent files (<30 days)
ARCHIVE:  Old implementation docs (*_IMPLEMENTATION.md, *_COMPLETE.md)
DELETE:   Duplicates (non-primary), unused files (>90 days, no refs)
MERGE:    Similar content (≥80% similarity)
RENAME:   Naming convention violations
```

**Data Structures:**
```python
@dataclass
class CleanupPlan:
    actions: List[CleanupAction]
    priorities: Dict[str, int]  # high=3, medium=2, low=1
    dependencies: DependencyGraph
    estimated_savings: int  # bytes
    estimated_file_reduction: float  # percentage

@dataclass
class CleanupAction:
    action_type: ActionType  # DELETE, MOVE, RENAME, MERGE
    source_files: List[Path]
    target_path: Optional[Path]
    rationale: str
    priority: int
    safety_level: SafetyLevel  # SAFE, MODERATE, RISKY
```

**Dependency Detection:**
- Regex patterns for markdown links: `[text](path)`, `docs/file.md`
- Cross-reference scanning in all text files
- Git submodule detection

---

### 3. CleanupExecutor (Execution Layer)

**Responsibility:** Execute cleanup operations safely with backups and rollback

**Key Functions:**
- `execute_dry_run(plan: CleanupPlan) -> ExecutionPreview`
- `create_backup(timestamp: str) -> Path`
- `execute_action(action: CleanupAction) -> ActionResult`
- `update_references(old_path: Path, new_path: Path) -> int`
- `rollback_from_backup(backup_path: Path) -> bool`

**Dependencies:**
- `shutil` - File operations (copy, move, remove)
- `zipfile` - Backup creation
- `GitPython` - Git operations (git mv for renames)

**Safety Mechanisms:**
1. **Dry-run Mode:** Preview all changes before execution
2. **Backups:** Timestamped ZIP archives before destructive ops
3. **Transaction Log:** JSON log of all operations for rollback
4. **Path Validation:** Prevent operations outside project directory
5. **Git Integration:** Use `git mv` to preserve file history

**Operation Types:**

```python
class DeleteStrategy:
    """Strategy for safe file deletion"""
    def execute(self, file: Path) -> None:
        self.backup(file)
        self.log_transaction("DELETE", file)
        file.unlink()

class RenameStrategy:
    """Strategy for git-aware file renaming"""
    def execute(self, old: Path, new: Path) -> None:
        if self.is_git_tracked(old):
            self.git_mv(old, new)  # Preserve history
        else:
            old.rename(new)
        self.update_all_references(old, new)

class MergeStrategy:
    """Strategy for merging similar files"""
    def execute(self, sources: List[Path], target: Path) -> None:
        merged_content = self.merge_content(sources)
        self.backup(sources)
        target.write_text(merged_content)
        for source in sources[1:]:  # Keep first, delete others
            source.unlink()
```

**Transaction Log Format:**
```json
{
  "timestamp": "2026-01-29T12:00:00Z",
  "backup_path": ".cleanup-backups/backup-20260129-120000.zip",
  "operations": [
    {
      "type": "DELETE",
      "source": "docs/OLD_FILE.md",
      "timestamp": "2026-01-29T12:00:05Z",
      "status": "SUCCESS"
    },
    {
      "type": "RENAME",
      "source": "docs/UPPERCASE.md",
      "target": "docs/lowercase.md",
      "references_updated": 5,
      "timestamp": "2026-01-29T12:00:10Z",
      "status": "SUCCESS"
    }
  ]
}
```

---

### 4. CleanupAgent (Orchestrator + CLI)

**Responsibility:** Orchestrate workflow and provide CLI interface

**Key Functions:**
- `run_analysis(path: Path) -> AnalysisReport`
- `run_planning(analysis: AnalysisReport) -> CleanupPlan`
- `run_execution(plan: CleanupPlan, dry_run: bool) -> ExecutionReport`
- `run_full_cleanup(path: Path, interactive: bool) -> FinalReport`

**CLI Commands:**
```bash
# Analyze project structure
cleanup-agent analyze --path ./docs --output analysis.json

# Generate cleanup plan
cleanup-agent plan --analysis analysis.json --output plan.json

# Execute cleanup (dry-run by default)
cleanup-agent execute --plan plan.json --dry-run

# Full automated workflow
cleanup-agent run --path ./docs --backup --interactive

# Rollback from backup
cleanup-agent rollback --backup .cleanup-backups/backup-20260129.zip
```

**Progress Notifications (Observer Pattern):**
```python
class ProgressObserver(ABC):
    @abstractmethod
    def on_start(self, total: int) -> None: ...

    @abstractmethod
    def on_progress(self, current: int, total: int) -> None: ...

    @abstractmethod
    def on_complete(self, results: Any) -> None: ...

class RichConsoleObserver(ProgressObserver):
    """Rich console progress display"""
    def on_progress(self, current: int, total: int) -> None:
        self.progress.update(self.task, completed=current, total=total)
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CleanupAgent (CLI)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   analyze   │  │    plan     │  │   execute   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ ProjectAnalyzer │ │ CleanupPlanner  │ │ CleanupExecutor │
│                 │ │                 │ │                 │
│ • scan_dirs     │ │ • categorize    │ │ • dry_run       │
│ • detect_dups   │ │ • similarity    │ │ • backup        │
│ • naming_check  │ │ • dependencies  │ │ • execute       │
│ • git_history   │ │ • prioritize    │ │ • update_refs   │
│ • gen_report    │ │ • gen_plan      │ │ • rollback      │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    File System Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ pathlib  │  │ hashlib  │  │ difflib  │  │GitPython │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram: Full Cleanup Workflow

```
User         CleanupAgent    Analyzer       Planner       Executor
 │               │              │              │              │
 │─run cleanup──>│              │              │              │
 │               │──analyze────>│              │              │
 │               │              │──scan dirs───>│              │
 │               │              │──detect dups─>│              │
 │               │              │<─report──────│              │
 │               │<─analysis────│              │              │
 │               │                             │              │
 │               │──plan──────────────────────>│              │
 │               │                             │──categorize──>│
 │               │                             │──dependencies>│
 │               │                             │<─plan────────│
 │               │<─cleanup plan───────────────│              │
 │               │                                            │
 │<─review plan──│                                            │
 │──approve─────>│                                            │
 │               │──execute───────────────────────────────────>│
 │               │                                            │──create backup──>
 │               │                                            │──execute actions>
 │               │                                            │──update refs────>
 │               │                                            │<─report─────────│
 │               │<─execution report──────────────────────────│
 │<─final report─│
```

---

## Data Flow Diagram

```
┌──────────────┐
│ Project Dirs │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│   ProjectAnalyzer       │
│ • File scanning         │
│ • Hash calculation      │
│ • Git history lookup    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   AnalysisReport        │
│ • Duplicates            │
│ • Outdated files        │
│ • Naming issues         │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   CleanupPlanner        │
│ • Categorization        │
│ • Similarity detection  │
│ • Dependency mapping    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   CleanupPlan           │
│ • Actions (prioritized) │
│ • Dependencies          │
│ • Impact estimate       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   CleanupExecutor       │
│ • Backup creation       │
│ • Action execution      │
│ • Reference updates     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   ExecutionReport       │
│ • Operations performed  │
│ • Files modified        │
│ • Backup location       │
└─────────────────────────┘
```

---

## Technology Stack

### Core Dependencies

| Technology | Purpose | Justification |
|-----------|---------|---------------|
| **pathlib** | Path operations | Standard library, cross-platform, type-safe |
| **hashlib** | Duplicate detection | SHA256 hashing, fast, secure |
| **difflib** | Similarity analysis | Standard library, good for text comparison |
| **GitPython** | Git operations | Preserve history with git mv, file age detection |
| **Rich** | Console output | Beautiful progress bars, color-coded output |
| **Pydantic** | Data validation | Type-safe data models, JSON export |
| **aiofiles** | Async file I/O | Performance for scanning large directories |

### Development Dependencies

| Technology | Purpose |
|-----------|---------|
| **pytest** | Unit testing framework |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reporting |
| **mypy** | Static type checking |
| **ruff** | Linting and formatting |

---

## Security Architecture

### Threats & Mitigations

| Threat | Impact | Mitigation |
|--------|--------|------------|
| **Path Traversal** | High | Validate all paths with `Path.resolve()`, check `.is_relative_to()` |
| **Data Loss** | Critical | Mandatory backups, dry-run default, transaction log |
| **Git History Loss** | High | Use `git mv` instead of OS rename |
| **Unauthorized File Access** | Medium | Permission checks before operations |
| **Malicious File Patterns** | Medium | Sanitize regex patterns, validate user inputs |

### Security Controls

1. **Path Validation:**
   ```python
   def validate_path(path: Path, project_root: Path) -> Path:
       resolved = path.resolve()
       if not resolved.is_relative_to(project_root):
           raise SecurityError("Path outside project directory")
       return resolved
   ```

2. **Secure Backups:**
   - Backups stored in `.cleanup-backups/` (git-ignored)
   - Timestamped archives: `backup-YYYYMMDD-HHMMSS.zip`
   - Permission check (no world-writable)

3. **Audit Logging:**
   - All operations logged to `.cleanup-log.json`
   - Includes: timestamp, operation, source, target, status
   - Immutable append-only log

---

## Performance Optimization

### Strategies

1. **Async File Operations:**
   ```python
   async def scan_directory(path: Path) -> List[Path]:
       tasks = [aiofiles.os.scandir(str(path))]
       results = await asyncio.gather(*tasks)
       return list(itertools.chain(*results))
   ```

2. **Stream-Based Hashing:**
   ```python
   def hash_file(path: Path, chunk_size: int = 8192) -> str:
       sha256 = hashlib.sha256()
       with path.open('rb') as f:
           for chunk in iter(lambda: f.read(chunk_size), b''):
               sha256.update(chunk)
       return sha256.hexdigest()
   ```

3. **Parallel Processing:**
   - Use `ProcessPoolExecutor` for CPU-bound tasks (hashing)
   - Use `ThreadPoolExecutor` for I/O-bound tasks (file reading)

### Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Analyze 229 files | < 10s | TBD |
| Generate plan | < 5s | TBD |
| Execute cleanup | < 30s | TBD |
| Memory usage | < 100MB | TBD |

---

## Error Handling & Resilience

### Error Handling Strategy

1. **Graceful Degradation:**
   - Permission errors → Skip file with warning
   - Git errors → Fall back to OS operations
   - Similarity detection errors → Skip comparison

2. **Transaction Rollback:**
   ```python
   try:
       for action in plan.actions:
           result = executor.execute(action)
           transaction_log.append(result)
   except Exception as e:
       logger.error(f"Execution failed: {e}")
       executor.rollback_from_log(transaction_log)
       raise
   ```

3. **Validation at Boundaries:**
   - Input validation (CLI arguments)
   - File path validation
   - Plan validation before execution

---

## Testing Strategy

### Test Pyramid

1. **Unit Tests (70%):**
   - Test each component in isolation
   - Mock file system operations
   - Test edge cases (empty dirs, symlinks, permission errors)

2. **Integration Tests (20%):**
   - Test component interactions
   - Use fixture directories with known structure
   - Verify end-to-end workflows

3. **Performance Tests (10%):**
   - Benchmark with 1000+ files
   - Memory profiling
   - Async operation verification

### Test Coverage Targets

- **Overall:** ≥ 75%
- **Critical Paths:** 100% (backup, rollback, path validation)
- **Edge Cases:** Symlinks, permissions, git operations

---

## Deployment & Usage

### Installation

```bash
# Install from source
pip install -e .

# Or as standalone tool
pip install tapps-agents[cleanup]
```

### Usage Examples

```bash
# Full analysis report
cleanup-agent analyze --path ./docs --output analysis.json --format markdown

# Generate plan with interactive review
cleanup-agent plan --analysis analysis.json --interactive

# Dry-run execution (preview only)
cleanup-agent execute --plan plan.json --dry-run

# Full automated cleanup with backup
cleanup-agent run --path ./docs --backup --auto-approve

# Rollback if needed
cleanup-agent rollback --backup .cleanup-backups/backup-20260129.zip
```

---

## Future Enhancements

1. **Machine Learning Similarity:** Use ML models for better content similarity
2. **Incremental Cleanup:** Track changes and only analyze new/modified files
3. **Web UI:** Visual interface for reviewing plans
4. **CI/CD Integration:** Automated cleanup on PR merges
5. **Cloud Storage:** Backup to S3/GCS for safety

---

**End of Architecture Document**
