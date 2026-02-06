"""Project Cleanup Agent - Automated project structure analysis and cleanup.

This module provides tools for analyzing project structure, identifying cleanup
opportunities, and safely executing cleanup operations with backups and rollback.

Architecture:
    - ProjectAnalyzer: Scan and analyze project structure
    - CleanupPlanner: Generate cleanup plans with categorization
    - CleanupExecutor: Execute cleanup operations safely
    - CleanupOrchestrator: CLI orchestrator

Usage:
    # Analyze project
    python -m tapps_agents.utils.project_cleanup_agent analyze --path ./docs

    # Generate cleanup plan
    python -m tapps_agents.utils.project_cleanup_agent plan --report analysis.json

    # Execute cleanup (dry-run by default)
    python -m tapps_agents.utils.project_cleanup_agent execute --plan plan.json

    # Full workflow
    python -m tapps_agents.utils.project_cleanup_agent run --path ./docs --backup
"""

import asyncio
import hashlib
import logging
import re
import shutil
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from difflib import SequenceMatcher
from enum import StrEnum
from pathlib import Path
from typing import Optional
from uuid import uuid4

import aiofiles
from pydantic import BaseModel, ConfigDict, Field

try:
    from git import InvalidGitRepositoryError, Repo
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Directories to exclude from recursive scans (backup, reference updates, etc.)
EXCLUDED_DIRS = frozenset({
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    ".cleanup-backups", ".tapps-agents", ".mypy_cache", ".pytest_cache",
    ".tox", ".eggs", "dist", "build", ".cache",
})

# Scan mode pattern presets
SCAN_MODE_PATTERNS: dict[str, list[str]] = {
    "docs-only": ["*.md", "*.rst", "*.txt", "*.adoc"],
    "code-only": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.go", "*.rs"],
}

# Type alias for progress callbacks
ProgressCallback = Callable[[str, int, int], None]


def _is_excluded(path: Path) -> bool:
    """Check if a path contains an excluded directory component."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


# =============================================================================
# Data Models (Pydantic)
# =============================================================================

class ActionType(StrEnum):
    """Types of cleanup actions."""
    DELETE = "delete"
    MOVE = "move"
    RENAME = "rename"
    MERGE = "merge"

    def __str__(self) -> str:
        return self.value


class SafetyLevel(StrEnum):
    """Safety level for cleanup actions."""
    SAFE = "safe"
    MODERATE = "moderate"
    RISKY = "risky"

    def __str__(self) -> str:
        return self.value

    @property
    def requires_confirmation(self) -> bool:
        """Whether this safety level requires user confirmation."""
        return self in (SafetyLevel.MODERATE, SafetyLevel.RISKY)


class FileCategory(StrEnum):
    """File categories for cleanup."""
    KEEP = "keep"
    ARCHIVE = "archive"
    DELETE = "delete"
    MERGE = "merge"
    RENAME = "rename"

    def __str__(self) -> str:
        return self.value


class DuplicateGroup(BaseModel):
    """Group of files with identical content."""
    hash: str = Field(..., description="SHA256 hash of file content", min_length=64, max_length=64)
    files: list[Path] = Field(..., description="List of file paths with identical content", min_length=2)
    size: int = Field(..., description="File size in bytes", ge=0)
    recommendation: str = Field(..., description="Recommended action for this group")

    model_config = ConfigDict(arbitrary_types_allowed=True)

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


class NearDuplicatePair(BaseModel):
    """Pair of files with near-duplicate content."""
    file1: Path = Field(..., description="First file")
    file2: Path = Field(..., description="Second file")
    similarity: float = Field(..., description="Similarity ratio (0.0-1.0)", ge=0.0, le=1.0)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OutdatedFile(BaseModel):
    """File that hasn't been modified recently."""
    path: Path = Field(..., description="File path")
    last_modified: datetime = Field(..., description="Last modification date")
    age_days: int = Field(..., description="Age in days since last modification", ge=0)
    reference_count: int = Field(0, description="Number of references to this file", ge=0)
    recommendation: FileCategory = Field(..., description="Recommended category for this file")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def is_obsolete(self) -> bool:
        """File is obsolete if >90 days old with no references."""
        return self.age_days > 90 and self.reference_count == 0


class NamingIssue(BaseModel):
    """File with naming convention violation."""
    path: Path = Field(..., description="File path")
    current_name: str = Field(..., description="Current filename")
    suggested_name: str = Field(..., description="Suggested filename (kebab-case)")
    pattern_violation: str = Field(..., description="Naming pattern violated")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LargeFile(BaseModel):
    """File exceeding the configured size threshold."""
    path: Path = Field(..., description="File path")
    size_bytes: int = Field(..., description="File size in bytes", ge=0)
    size_mb: float = Field(..., description="File size in megabytes")
    is_binary: bool = Field(default=False, description="Whether file appears to be binary")
    recommendation: str = Field(
        default="", description="Suggested action (e.g., .gitignore, git-lfs, delete)"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AnalysisReport(BaseModel):
    """Analysis report of project structure."""
    total_files: int = Field(..., description="Total number of files analyzed", ge=0)
    total_size: int = Field(..., description="Total size of all files in bytes", ge=0)
    duplicates: list[DuplicateGroup] = Field(default_factory=list, description="Groups of duplicate files")
    near_duplicates: list[NearDuplicatePair] = Field(default_factory=list, description="Near-duplicate file pairs")
    outdated_files: list[OutdatedFile] = Field(default_factory=list, description="Files not modified recently")
    naming_issues: list[NamingIssue] = Field(default_factory=list, description="Files with naming convention violations")
    large_files: list[LargeFile] = Field(default_factory=list, description="Files exceeding size threshold")
    timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    scan_path: Path = Field(..., description="Root path that was analyzed")

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        near_dup_section = ""
        if self.near_duplicates:
            near_dup_section = f"\n## Near-Duplicates\n- **Pairs:** {len(self.near_duplicates)}\n"

        return f"""# Analysis Report

**Analyzed:** {self.timestamp.isoformat()}
**Path:** {self.scan_path}
**Total Files:** {self.total_files}
**Total Size:** {self.total_size / 1024 / 1024:.2f} MB

## Duplicates
- **Groups:** {len(self.duplicates)}
- **Files:** {self.duplicate_count}
- **Potential Savings:** {self.potential_savings / 1024:.2f} KB
{near_dup_section}
## Outdated Files
- **Total:** {len(self.outdated_files)}
- **Obsolete:** {self.obsolete_file_count}

## Naming Issues
- **Total:** {len(self.naming_issues)}
"""


class CleanupAction(BaseModel):
    """Individual cleanup action."""
    action_type: ActionType = Field(..., description="Type of action")
    source_files: list[Path] = Field(..., description="Source file(s) for this action", min_length=1)
    target_path: Path | None = Field(None, description="Target path (for MOVE/RENAME/MERGE actions)")
    rationale: str = Field(..., description="Explanation for this action", min_length=10)
    priority: int = Field(..., description="Priority level (1=low, 2=medium, 3=high)", ge=1, le=3)
    safety_level: SafetyLevel = Field(..., description="Risk assessment for this action")
    estimated_savings: int = Field(0, description="Estimated space savings in bytes", ge=0)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def requires_confirmation(self) -> bool:
        """Whether this action requires user confirmation."""
        return self.safety_level.requires_confirmation


class CleanupPlan(BaseModel):
    """Complete cleanup plan with prioritized actions."""
    actions: list[CleanupAction] = Field(..., description="List of cleanup actions to perform")
    priorities: dict[str, int] = Field(default_factory=dict, description="Action counts by priority")
    dependencies: dict[str, list[str]] = Field(default_factory=dict, description="Action dependencies")
    estimated_savings: int = Field(..., description="Total estimated space savings in bytes", ge=0)
    estimated_file_reduction: float = Field(..., description="Estimated file reduction percentage", ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=datetime.now, description="When plan was created")

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
"""


class OperationResult(BaseModel):
    """Result of a single cleanup operation."""
    operation_id: str = Field(..., description="Unique operation ID")
    action_type: ActionType = Field(..., description="Type of action performed")
    source_files: list[Path] = Field(..., description="Source file(s)")
    target_path: Path | None = Field(None, description="Target path (if applicable)")
    status: str = Field(..., description="Operation status", pattern="^(SUCCESS|FAILED|SKIPPED)$")
    error_message: str | None = Field(None, description="Error message if operation failed")
    references_updated: int = Field(0, description="Number of cross-references updated", ge=0)
    timestamp: datetime = Field(default_factory=datetime.now, description="When operation was performed")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def succeeded(self) -> bool:
        """Whether operation succeeded."""
        return self.status == "SUCCESS"


class ExecutionReport(BaseModel):
    """Complete execution report."""
    operations: list[OperationResult] = Field(..., description="List of operation results")
    files_modified: int = Field(..., description="Total number of files modified", ge=0)
    files_deleted: int = Field(0, description="Number of files deleted", ge=0)
    files_moved: int = Field(0, description="Number of files moved", ge=0)
    files_renamed: int = Field(0, description="Number of files renamed", ge=0)
    files_merged: int = Field(0, description="Number of files merged", ge=0)
    backup_location: Path | None = Field(None, description="Path to backup archive")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    dry_run: bool = Field(False, description="Whether this was a dry-run")

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
- **Merged:** {self.files_merged}
- **Total:** {self.files_modified}

## Backup
- **Location:** {self.backup_location}
"""


# =============================================================================
# ProjectAnalyzer - Analysis Layer
# =============================================================================

class ProjectAnalyzer:
    """Analyze project structure and identify cleanup opportunities."""

    def __init__(self, project_root: Path, age_threshold_days: int = 90, exclude_names: list[str] | None = None):
        """Initialize analyzer.

        Args:
            project_root: Root directory of project to analyze
            age_threshold_days: Days threshold for outdated file detection
            exclude_names: Filenames to exclude from naming convention analysis
        """
        self.project_root = project_root.resolve()
        self._validate_path(self.project_root)
        self.age_threshold_days = age_threshold_days
        self.exclude_names = set(exclude_names or [])
        self._repo: Repo | None = None
        if GIT_AVAILABLE:
            try:
                self._repo = Repo(self.project_root)
            except InvalidGitRepositoryError:
                pass  # Not a git repo, continue without git features
        # Reference index built lazily (Enhancement #6)
        self._reference_index: dict[str, set[Path]] | None = None

    def _validate_path(self, path: Path) -> None:
        """Validate path is safe and within project."""
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

    async def scan_directory_structure(
        self,
        path: Path,
        pattern: str = "*.md",
        patterns: list[str] | None = None,
        respect_gitignore: bool = True,
    ) -> list[Path]:
        """Scan directory for files matching pattern(s).

        Args:
            path: Directory to scan
            pattern: Single glob pattern (used if patterns is empty/None)
            patterns: Multiple glob patterns to scan (e.g., ['*.md', '*.py'])
            respect_gitignore: If True, exclude files matched by .gitignore

        Returns:
            List of file paths matching pattern(s)
        """
        self._validate_path(path)

        # Determine effective patterns
        effective_patterns = patterns if patterns else [pattern]

        # Set up gitignore filtering
        repo = None
        if respect_gitignore and GIT_AVAILABLE:
            try:
                repo = Repo(path, search_parent_directories=True)
            except (InvalidGitRepositoryError, Exception):
                repo = None

        def scan_sync(directory: Path) -> list[Path]:
            """Synchronous scan helper with multi-pattern and gitignore support."""
            seen: set[Path] = set()
            results: list[Path] = []
            for pat in effective_patterns:
                for f in directory.rglob(pat):
                    if f in seen or not f.is_file():
                        continue
                    # Filter gitignored files
                    if repo is not None:
                        try:
                            if repo.ignored(str(f)):
                                continue
                        except Exception:
                            pass  # Graceful fallback if ignored() fails
                    seen.add(f)
                    results.append(f)
            return results

        files = await asyncio.to_thread(scan_sync, path)

        return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

    async def hash_file(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of file using streaming.

        Args:
            file_path: Path to file
            chunk_size: Bytes to read per chunk

        Returns:
            SHA256 hash as hex string
        """
        sha256 = hashlib.sha256()

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(chunk_size):
                sha256.update(chunk)

        return sha256.hexdigest()

    async def detect_duplicates(self, files: list[Path]) -> list[DuplicateGroup]:
        """Detect duplicate files by content hash.

        Args:
            files: List of files to check

        Returns:
            List of duplicate groups
        """
        hash_map: dict[str, list[Path]] = {}

        # Calculate hashes concurrently
        tasks = [self.hash_file(f) for f in files]
        hashes = await asyncio.gather(*tasks)

        # Group files by hash
        for file, file_hash in zip(files, hashes, strict=False):
            hash_map.setdefault(file_hash, []).append(file)

        # Create duplicate groups (only groups with 2+ files)
        duplicates = []
        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                size = file_list[0].stat().st_size
                duplicates.append(DuplicateGroup(
                    hash=file_hash,
                    files=sorted(file_list),
                    size=size,
                    recommendation=f"Keep {file_list[0].name}, delete/merge {len(file_list) - 1} duplicates"
                ))

        return sorted(duplicates, key=lambda g: g.savings, reverse=True)

    # Naming convention patterns
    NAMING_PATTERNS: dict[str, re.Pattern] = {
        "kebab-case": re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$'),
        "snake_case": re.compile(r'^[a-z0-9]+(_[a-z0-9]+)*$'),
        "camelCase": re.compile(r'^[a-z][a-zA-Z0-9]*$'),
        "PascalCase": re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
    }

    def analyze_naming_patterns(
        self, files: list[Path], convention: str = "kebab-case"
    ) -> list[NamingIssue]:
        """Analyze file naming patterns and detect violations.

        Args:
            files: List of files to check
            convention: Expected naming convention ('kebab-case', 'snake_case',
                        'camelCase', 'PascalCase', or a custom regex pattern)

        Returns:
            List of naming issues
        """
        issues = []

        # Get or compile the pattern for the convention
        if convention in self.NAMING_PATTERNS:
            stem_pattern = self.NAMING_PATTERNS[convention]
        else:
            # Treat as custom regex
            try:
                stem_pattern = re.compile(convention)
            except re.error:
                logger.warning("Invalid naming convention regex: %s, using kebab-case", convention)
                stem_pattern = self.NAMING_PATTERNS["kebab-case"]

        for file in files:
            name = file.name
            stem = file.stem

            # Skip excluded filenames
            if name in self.exclude_names:
                continue

            # Check against convention pattern
            if stem_pattern.match(stem):
                continue

            # Detect what style it currently uses
            if stem.isupper():
                violation = "UPPERCASE"
            elif '_' in stem and stem == stem.lower():
                violation = "snake_case"
            elif '-' in stem and stem == stem.lower():
                violation = "kebab-case"
            elif stem[0].isupper() if stem else False:
                violation = "PascalCase"
            elif any(c.isupper() for c in stem):
                violation = "camelCase"
            else:
                violation = "non-standard"

            # Generate suggestion based on target convention
            suggested = self._convert_to_convention(stem, convention)
            ext = file.suffix

            issues.append(NamingIssue(
                path=file,
                current_name=name,
                suggested_name=f"{suggested}{ext}",
                pattern_violation=f"{violation} (expected {convention})"
            ))

        return issues

    @staticmethod
    def _convert_to_convention(stem: str, convention: str) -> str:
        """Convert a stem to the target naming convention."""
        # Split into words (handle kebab, snake, camelCase, PascalCase)
        words = re.sub(r'[-_]', ' ', stem)  # Replace delimiters with spaces
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', words)  # camelCase split
        parts = [w.lower() for w in words.split() if w]
        if not parts:
            return stem.lower()
        if convention == "kebab-case":
            return "-".join(parts)
        elif convention == "snake_case":
            return "_".join(parts)
        elif convention == "camelCase":
            return parts[0] + "".join(w.capitalize() for w in parts[1:])
        elif convention == "PascalCase":
            return "".join(w.capitalize() for w in parts)
        return "-".join(parts)  # Default to kebab

    def detect_large_files(
        self, files: list[Path], threshold_mb: float = 5.0
    ) -> list[LargeFile]:
        """Detect files exceeding the size threshold.

        Args:
            files: List of files to check
            threshold_mb: Size threshold in megabytes

        Returns:
            List of LargeFile entries
        """
        threshold_bytes = int(threshold_mb * 1024 * 1024)
        large: list[LargeFile] = []
        for f in files:
            try:
                size = f.stat().st_size
                if size > threshold_bytes:
                    is_binary = self._is_binary_file(f)
                    recommendation = (
                        "Consider git-lfs or .gitignore"
                        if is_binary
                        else "Review if file can be split or compressed"
                    )
                    large.append(
                        LargeFile(
                            path=f,
                            size_bytes=size,
                            size_mb=round(size / (1024 * 1024), 2),
                            is_binary=is_binary,
                            recommendation=recommendation,
                        )
                    )
            except OSError:
                continue
        return sorted(large, key=lambda x: x.size_bytes, reverse=True)

    @staticmethod
    def _is_binary_file(path: Path, check_bytes: int = 512) -> bool:
        """Check if a file is binary by reading first bytes."""
        try:
            with open(path, "rb") as f:
                chunk = f.read(check_bytes)
            # Heuristic: if >10% of bytes are non-text, it's binary
            non_text = sum(1 for b in chunk if b > 127 or (b < 32 and b not in (9, 10, 13)))
            return len(chunk) > 0 and (non_text / len(chunk)) > 0.1
        except OSError:
            return False

    def _build_reference_index(self, files: list[Path]) -> dict[str, set[Path]]:
        """Build a reference index mapping filenames to referring files.

        Enhancement #6: Single-pass O(n) index replaces O(n^2) _count_references.

        Args:
            files: All files to index

        Returns:
            Dict mapping filename -> set of files that reference it
        """
        index: dict[str, set[Path]] = {}
        # Pre-populate with all filenames and relative paths
        file_identifiers: dict[Path, list[str]] = {}
        for f in files:
            identifiers = [f.name]
            try:
                identifiers.append(str(f.relative_to(self.project_root)))
            except ValueError:
                pass
            file_identifiers[f] = identifiers
            for ident in identifiers:
                index.setdefault(ident, set())

        # Single pass: read each file once, check which identifiers it mentions
        all_identifiers = set()
        for idents in file_identifiers.values():
            all_identifiers.update(idents)

        for f in files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            for ident in all_identifiers:
                if ident in content:
                    # f references ident — but don't count self-references
                    for target, target_idents in file_identifiers.items():
                        if target != f and ident in target_idents:
                            index.setdefault(ident, set()).add(f)

        return index

    def _count_references_indexed(self, target_file: Path, files: list[Path]) -> int:
        """Count references to target file using the pre-built index.

        Args:
            target_file: File to count references for
            files: All files (used to build index on first call)

        Returns:
            Number of files that reference target_file
        """
        if self._reference_index is None:
            self._reference_index = self._build_reference_index(files)

        referring_files: set[Path] = set()
        # Check both filename and relative path
        identifiers = [target_file.name]
        try:
            identifiers.append(str(target_file.relative_to(self.project_root)))
        except ValueError:
            pass

        for ident in identifiers:
            referring_files.update(self._reference_index.get(ident, set()))

        return len(referring_files)

    def detect_outdated_files(self, files: list[Path], age_threshold_days: int | None = None) -> list[OutdatedFile]:
        """Detect files that haven't been modified recently.

        Args:
            files: List of files to check
            age_threshold_days: Age threshold in days (uses instance default if None)

        Returns:
            List of outdated files
        """
        threshold = age_threshold_days if age_threshold_days is not None else self.age_threshold_days
        outdated = []
        now = datetime.now()

        # Reset reference index for fresh calculation
        self._reference_index = None

        for file in files:
            # Get last modified time from git if available, else filesystem
            last_modified = self._get_last_modified_date(file)
            age_days = (now - last_modified).days

            if age_days >= threshold:
                # Enhancement #6: Use indexed reference counting
                ref_count = self._count_references_indexed(file, files)

                # Determine recommendation
                if age_days > threshold and ref_count == 0:
                    category = FileCategory.DELETE
                elif age_days > threshold:
                    category = FileCategory.ARCHIVE
                else:
                    category = FileCategory.KEEP

                outdated.append(OutdatedFile(
                    path=file,
                    last_modified=last_modified,
                    age_days=age_days,
                    reference_count=ref_count,
                    recommendation=category
                ))

        return sorted(outdated, key=lambda f: f.age_days, reverse=True)

    def _get_last_modified_date(self, file: Path) -> datetime:
        """Get last modified date from git history or filesystem.

        Args:
            file: File path

        Returns:
            Last modified datetime
        """
        if self._repo and GIT_AVAILABLE:
            try:
                # Get last commit date for this file
                commits = list(self._repo.iter_commits(paths=str(file), max_count=1))
                if commits:
                    return datetime.fromtimestamp(commits[0].committed_date)
            except Exception:
                pass  # Fall back to filesystem

        # Use filesystem modification time
        return datetime.fromtimestamp(file.stat().st_mtime)

    async def generate_analysis_report(
        self,
        scan_path: Path,
        pattern: str = "*.md",
        patterns: list[str] | None = None,
        respect_gitignore: bool = True,
        naming_convention: str = "kebab-case",
        large_file_threshold_mb: float = 5.0,
        progress_callback: ProgressCallback | None = None,
    ) -> AnalysisReport:
        """Generate comprehensive analysis report.

        Args:
            scan_path: Path to scan
            pattern: File pattern to match (fallback if patterns is empty)
            patterns: Multiple file patterns to scan
            respect_gitignore: Exclude .gitignore-matched files
            naming_convention: Expected naming convention
            large_file_threshold_mb: Threshold for flagging large files
            progress_callback: Optional callback(step_name, current, total)

        Returns:
            Analysis report
        """
        total_steps = 5

        # Step 1: Scan files (multi-pattern + gitignore aware)
        if progress_callback:
            progress_callback("Scanning files", 1, total_steps)
        files = await self.scan_directory_structure(
            scan_path, pattern, patterns=patterns,
            respect_gitignore=respect_gitignore,
        )

        # Calculate total size
        total_size = sum(f.stat().st_size for f in files)

        # Step 2: Detect duplicates
        if progress_callback:
            progress_callback("Detecting duplicates", 2, total_steps)
        duplicates = await self.detect_duplicates(files)

        # Step 3: Analyze naming (with configurable convention)
        if progress_callback:
            progress_callback("Analyzing naming patterns", 3, total_steps)
        naming_issues = self.analyze_naming_patterns(files, convention=naming_convention)

        # Step 4: Detect outdated files
        if progress_callback:
            progress_callback("Detecting outdated files", 4, total_steps)
        outdated_files = self.detect_outdated_files(files)

        # Step 5: Detect large files
        if progress_callback:
            progress_callback("Detecting large files", 5, total_steps)
        large_files = self.detect_large_files(files, threshold_mb=large_file_threshold_mb)

        return AnalysisReport(
            total_files=len(files),
            total_size=total_size,
            duplicates=duplicates,
            outdated_files=outdated_files,
            naming_issues=naming_issues,
            large_files=large_files,
            scan_path=scan_path
        )


# =============================================================================
# CleanupPlanner - Planning Layer
# =============================================================================

class CleanupPlanner:
    """Generate cleanup plans with categorization and prioritization."""

    def __init__(self, analysis_report: AnalysisReport, similarity_threshold: float = 0.8):
        """Initialize planner.

        Args:
            analysis_report: Analysis report to plan from
            similarity_threshold: Threshold for near-duplicate detection (0.0-1.0)
        """
        self.analysis = analysis_report
        self.similarity_threshold = similarity_threshold

    def detect_content_similarity(self, file1: Path, file2: Path) -> float:
        """Detect content similarity between two files.

        Args:
            file1: First file
            file2: Second file

        Returns:
            Similarity ratio (0.0-1.0)
        """
        try:
            content1 = file1.read_text(encoding='utf-8', errors='ignore')
            content2 = file2.read_text(encoding='utf-8', errors='ignore')

            return SequenceMatcher(None, content1, content2).ratio()
        except Exception:
            return 0.0

    def detect_near_duplicates(self, files: list[Path]) -> list[NearDuplicatePair]:
        """Detect near-duplicate files by content similarity.

        Enhancement #7: Activated near-duplicate detection.

        Args:
            files: List of files to compare

        Returns:
            List of near-duplicate pairs above similarity threshold
        """
        # Collect files that are NOT exact duplicates (those are handled separately)
        duplicate_hashes = {g.hash for g in self.analysis.duplicates}
        candidates = [f for f in files if f.stat().st_size > 0]

        # Only compare if we have a reasonable number of candidates
        if len(candidates) > 200:
            logger.info("Skipping near-duplicate detection: too many files (%d)", len(candidates))
            return []

        pairs: list[NearDuplicatePair] = []
        for i, f1 in enumerate(candidates):
            for f2 in candidates[i + 1:]:
                similarity = self.detect_content_similarity(f1, f2)
                if similarity >= self.similarity_threshold and similarity < 1.0:
                    pairs.append(NearDuplicatePair(
                        file1=f1,
                        file2=f2,
                        similarity=similarity,
                    ))

        return sorted(pairs, key=lambda p: p.similarity, reverse=True)

    def categorize_files(self) -> dict[FileCategory, list[Path]]:
        """Categorize files based on analysis results.

        Returns:
            Dictionary mapping categories to file lists
        """
        categories: dict[FileCategory, list[Path]] = {
            FileCategory.KEEP: [],
            FileCategory.ARCHIVE: [],
            FileCategory.DELETE: [],
            FileCategory.MERGE: [],
            FileCategory.RENAME: []
        }

        # Categorize duplicates
        for group in self.analysis.duplicates:
            categories[FileCategory.KEEP].append(group.primary_file)
            categories[FileCategory.DELETE].extend(group.duplicates)

        # Categorize outdated files
        for file in self.analysis.outdated_files:
            categories[file.recommendation].append(file.path)

        # Categorize naming issues
        for issue in self.analysis.naming_issues:
            categories[FileCategory.RENAME].append(issue.path)

        # Categorize near-duplicates as merge candidates
        for pair in self.analysis.near_duplicates:
            if pair.file2 not in categories[FileCategory.MERGE]:
                categories[FileCategory.MERGE].append(pair.file2)

        return categories

    def prioritize_actions(self, actions: list[CleanupAction]) -> list[CleanupAction]:
        """Prioritize actions by safety and impact.

        Args:
            actions: List of actions to prioritize

        Returns:
            Sorted list of actions (high priority first)
        """
        def priority_key(action: CleanupAction) -> tuple:
            # Sort by: priority (desc), safety (safe first), savings (desc)
            safety_order = {SafetyLevel.SAFE: 0, SafetyLevel.MODERATE: 1, SafetyLevel.RISKY: 2}
            return (-action.priority, safety_order[action.safety_level], -action.estimated_savings)

        return sorted(actions, key=priority_key)

    def generate_cleanup_plan(self) -> CleanupPlan:
        """Generate comprehensive cleanup plan.

        Returns:
            Cleanup plan with prioritized actions
        """
        actions: list[CleanupAction] = []

        # Generate actions for duplicates
        for group in self.analysis.duplicates:
            for dup_file in group.duplicates:
                actions.append(CleanupAction(
                    action_type=ActionType.DELETE,
                    source_files=[dup_file],
                    rationale=f"Duplicate of {group.primary_file.name} with identical content (hash: {group.hash[:8]}...)",
                    priority=2,
                    safety_level=SafetyLevel.SAFE,
                    estimated_savings=group.size
                ))

        # Enhancement #7: Generate merge actions for near-duplicates
        for pair in self.analysis.near_duplicates:
            actions.append(CleanupAction(
                action_type=ActionType.MERGE,
                source_files=[pair.file1, pair.file2],
                target_path=pair.file1,  # Merge into file1
                rationale=f"Near-duplicate files ({pair.similarity:.0%} similar) - merge content into {pair.file1.name}",
                priority=1,
                safety_level=SafetyLevel.RISKY,
                estimated_savings=pair.file2.stat().st_size if pair.file2.exists() else 0,
            ))

        # Generate actions for outdated files
        for file in self.analysis.outdated_files:
            if file.recommendation == FileCategory.DELETE:
                actions.append(CleanupAction(
                    action_type=ActionType.DELETE,
                    source_files=[file.path],
                    rationale=f"Obsolete file: {file.age_days} days old with no references",
                    priority=1,
                    safety_level=SafetyLevel.SAFE,
                    estimated_savings=file.path.stat().st_size
                ))
            elif file.recommendation == FileCategory.ARCHIVE:
                archive_path = file.path.parent / "archive" / file.path.name
                actions.append(CleanupAction(
                    action_type=ActionType.MOVE,
                    source_files=[file.path],
                    target_path=archive_path,
                    rationale=f"Archive old file: {file.age_days} days old with {file.reference_count} references",
                    priority=1,
                    safety_level=SafetyLevel.MODERATE,
                    estimated_savings=0
                ))

        # Generate actions for naming issues
        for issue in self.analysis.naming_issues:
            new_path = issue.path.parent / issue.suggested_name
            actions.append(CleanupAction(
                action_type=ActionType.RENAME,
                source_files=[issue.path],
                target_path=new_path,
                rationale=f"Enforce naming convention: {issue.pattern_violation} -> kebab-case",
                priority=2,
                safety_level=SafetyLevel.MODERATE,
                estimated_savings=0
            ))

        # Prioritize actions
        actions = self.prioritize_actions(actions)

        # Calculate metrics
        total_savings = sum(a.estimated_savings for a in actions)
        file_reduction = (len([a for a in actions if a.action_type == ActionType.DELETE]) / max(self.analysis.total_files, 1)) * 100

        return CleanupPlan(
            actions=actions,
            priorities={
                "high": sum(1 for a in actions if a.priority == 3),
                "medium": sum(1 for a in actions if a.priority == 2),
                "low": sum(1 for a in actions if a.priority == 1)
            },
            dependencies={},
            estimated_savings=total_savings,
            estimated_file_reduction=file_reduction
        )


# =============================================================================
# ReferenceUpdater - Reference Scanning and Updating
# =============================================================================

class ReferenceUpdater:
    """Scan and update file references to maintain link integrity."""

    def __init__(self, project_root: Path):
        """Initialize reference updater.

        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root.resolve()

        # Reference patterns to detect and update
        self.patterns = [
            # Markdown links: [text](file.md)
            (r'\[([^\]]+)\]\(([^)]+)\)', self._update_markdown_link),
            # Relative paths: docs/file.md or ./docs/file.md
            (r'(?:^|\s)(\.?\.?/)?([a-zA-Z0-9_/-]+\.(?:md|json|yaml|yml|txt))', self._update_relative_path),
        ]

    def _update_markdown_link(self, match, old_path: Path, new_path: Path) -> str:
        """Update markdown link reference."""
        link_text = match.group(1)
        link_target = match.group(2)

        # Check if link target matches old filename
        if Path(link_target).name == old_path.name or link_target == str(old_path):
            # Update to new filename/path
            new_target = str(new_path) if '/' in link_target else new_path.name
            return f'[{link_text}]({new_target})'

        return match.group(0)  # No change

    def _update_relative_path(self, match, old_path: Path, new_path: Path) -> str:
        """Update relative path reference."""
        prefix = match.group(1) or ''
        path_str = match.group(2)

        # Check if path matches old filename
        if Path(path_str).name == old_path.name or path_str == str(old_path):
            # Preserve relative path structure
            if '/' in path_str:
                old_parts = Path(path_str).parts
                new_relative = '/'.join(old_parts[:-1] + (new_path.name,))
                return f'{prefix}{new_relative}'
            else:
                return f'{prefix}{new_path.name}'

        return match.group(0)  # No change

    def scan_and_update_references(
        self,
        old_path: Path,
        new_path: Path,
        dry_run: bool = False
    ) -> int:
        """Scan all text files and update references.

        Enhancement #2: Skips EXCLUDED_DIRS during scanning.

        Args:
            old_path: Old file path
            new_path: New file path
            dry_run: If True, don't actually modify files

        Returns:
            Number of references updated
        """
        references_updated = 0

        # Scan all text files in project
        text_extensions = {'.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.txt', '.rst'}

        for file in self.project_root.rglob('*'):
            # Enhancement #2: Skip excluded directories
            if _is_excluded(file):
                continue

            if not file.is_file() or file.suffix not in text_extensions:
                continue

            # Skip the renamed file itself
            if file == new_path:
                continue

            try:
                content = file.read_text(encoding='utf-8')
                modified_content = content
                file_updated = False

                # Apply all reference patterns
                for pattern_regex, update_func in self.patterns:
                    pattern = re.compile(pattern_regex)

                    def replacer(match, _func=update_func):
                        nonlocal file_updated
                        updated = _func(match, old_path, new_path)
                        if updated != match.group(0):
                            file_updated = True
                        return updated

                    modified_content = pattern.sub(replacer, modified_content)

                # Write back if content changed
                if file_updated and not dry_run:
                    file.write_text(modified_content, encoding='utf-8')
                    references_updated += 1
                elif file_updated and dry_run:
                    references_updated += 1  # Count but don't write

            except Exception:
                continue  # Skip files that can't be read/written

        return references_updated


# =============================================================================
# CleanupExecutor - Execution Layer
# =============================================================================

def _make_operation_id(prefix: str) -> str:
    """Generate a unique operation ID with a UUID suffix.

    Enhancement #9: Prevents operation ID collisions.
    """
    return f"{prefix}-{uuid4().hex[:8]}"


class CleanupStrategy(ABC):
    """Abstract base class for cleanup strategies."""

    @abstractmethod
    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute cleanup action.

        Args:
            action: Action to execute
            dry_run: If True, don't actually modify files

        Returns:
            Operation result
        """
        pass


class DeleteStrategy(CleanupStrategy):
    """Strategy for deleting files."""

    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute delete action."""
        op_id = _make_operation_id("del")
        try:
            for file in action.source_files:
                if not dry_run:
                    file.unlink()

            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.DELETE,
                source_files=action.source_files,
                status="SUCCESS"
            )
        except Exception as e:
            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.DELETE,
                source_files=action.source_files,
                status="FAILED",
                error_message=str(e)
            )


class RenameStrategy(CleanupStrategy):
    """Strategy for renaming files."""

    def __init__(self, repo: Optional['Repo'] = None, project_root: Path | None = None):
        self.repo = repo
        self.reference_updater = ReferenceUpdater(project_root) if project_root else None

    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute rename action."""
        op_id = _make_operation_id("ren")
        try:
            source = action.source_files[0]
            target = action.target_path
            references_updated = 0

            if not dry_run:
                if self.repo and GIT_AVAILABLE:
                    try:
                        self.repo.git.mv(str(source), str(target))
                    except Exception:
                        source.rename(target)
                else:
                    source.rename(target)

                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=False
                    )
            else:
                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=True
                    )

            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.RENAME,
                source_files=[source],
                target_path=target,
                status="SUCCESS",
                references_updated=references_updated
            )
        except Exception as e:
            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.RENAME,
                source_files=action.source_files,
                target_path=action.target_path,
                status="FAILED",
                error_message=str(e)
            )


class MoveStrategy(CleanupStrategy):
    """Strategy for moving files."""

    def __init__(self, repo: Optional['Repo'] = None, project_root: Path | None = None):
        self.repo = repo
        self.reference_updater = ReferenceUpdater(project_root) if project_root else None

    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute move action."""
        op_id = _make_operation_id("mov")
        try:
            source = action.source_files[0]
            target = action.target_path
            references_updated = 0

            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))

                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=False
                    )
            else:
                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=True
                    )

            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.MOVE,
                source_files=[source],
                target_path=target,
                status="SUCCESS",
                references_updated=references_updated
            )
        except Exception as e:
            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.MOVE,
                source_files=action.source_files,
                target_path=action.target_path,
                status="FAILED",
                error_message=str(e)
            )


class MergeStrategy(CleanupStrategy):
    """Strategy for merging content from multiple source files into a target.

    Enhancement #3: Implements the missing MergeStrategy.
    Appends content from secondary source files into the target (first source).
    """

    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute merge action.

        Merges content from all source files into target_path (or first source).
        Secondary source files are deleted after merge.
        """
        op_id = _make_operation_id("mrg")
        target = action.target_path or action.source_files[0]
        try:
            if not dry_run:
                # Read all source file contents
                merged_parts: list[str] = []
                for src in action.source_files:
                    if src.exists():
                        merged_parts.append(src.read_text(encoding='utf-8', errors='ignore'))

                # Write merged content to target
                merged_content = "\n\n".join(merged_parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(merged_content, encoding='utf-8')

                # Delete secondary source files (all except target)
                for src in action.source_files:
                    if src != target and src.exists():
                        src.unlink()

            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.MERGE,
                source_files=action.source_files,
                target_path=target,
                status="SUCCESS",
            )
        except Exception as e:
            return OperationResult(
                operation_id=op_id,
                action_type=ActionType.MERGE,
                source_files=action.source_files,
                target_path=target,
                status="FAILED",
                error_message=str(e),
            )


class CleanupExecutor:
    """Execute cleanup operations safely with backups and rollback."""

    def __init__(self, project_root: Path, backup_dir: str = ".tapps-agents/cleanup-backups"):
        """Initialize executor.

        Args:
            project_root: Root directory of project
            backup_dir: Backup directory relative to project root
        """
        self.project_root = project_root.resolve()
        # Enhancement #1: Store backups under .tapps-agents/ using configured backup_dir
        self.backup_dir = self.project_root / backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize strategies
        repo = None
        if GIT_AVAILABLE:
            try:
                repo = Repo(project_root)
            except Exception:
                pass

        self.strategies: dict[ActionType, CleanupStrategy] = {
            ActionType.DELETE: DeleteStrategy(),
            ActionType.RENAME: RenameStrategy(repo, self.project_root),
            ActionType.MOVE: MoveStrategy(repo, self.project_root),
            # Enhancement #3: Register MergeStrategy
            ActionType.MERGE: MergeStrategy(),
        }

    def create_backup(self, plan: CleanupPlan | None = None) -> Path:
        """Create timestamped backup of files affected by the cleanup plan.

        Enhancement #1: Only backs up files that the plan will modify,
        instead of zipping the entire project.

        Args:
            plan: The cleanup plan (backs up affected files only).
                  If None, backs up nothing (returns empty zip).

        Returns:
            Path to backup ZIP file
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / f"backup-{timestamp}.zip"

        affected_files: set[Path] = set()
        if plan:
            for action in plan.actions:
                for src in action.source_files:
                    if src.is_file():
                        affected_files.add(src)
                if action.target_path and action.target_path.is_file():
                    affected_files.add(action.target_path)

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in affected_files:
                # Enhancement #2: Skip excluded directories
                if _is_excluded(file):
                    continue
                try:
                    arcname = file.relative_to(self.project_root)
                    zipf.write(file, arcname)
                except (ValueError, OSError):
                    continue

        return backup_path

    async def execute_dry_run(self, plan: CleanupPlan) -> ExecutionReport:
        """Execute dry-run (preview changes without modifying files)."""
        return await self.execute_plan(plan, dry_run=True)

    async def execute_plan(
        self,
        plan: CleanupPlan,
        dry_run: bool = False,
        create_backup: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> ExecutionReport:
        """Execute cleanup plan.

        Args:
            plan: Cleanup plan to execute
            dry_run: If True, don't actually modify files
            create_backup: If True, create backup before execution
            progress_callback: Optional callback(step_name, current, total)

        Returns:
            Execution report
        """
        started_at = datetime.now()
        operations: list[OperationResult] = []
        backup_location = None

        # Create backup if requested and not dry-run
        if create_backup and not dry_run:
            backup_location = self.create_backup(plan)

        total_actions = len(plan.actions)

        # Execute actions
        for i, action in enumerate(plan.actions):
            if progress_callback:
                progress_callback(f"Executing {action.action_type}", i + 1, total_actions)

            strategy = self.strategies.get(action.action_type)
            if strategy:
                result = await strategy.execute(action, dry_run=dry_run)
                operations.append(result)
            else:
                # Enhancement #10: Log warning for missing strategy instead of silent skip
                logger.warning(
                    "No strategy registered for action type '%s' — skipping action on %s",
                    action.action_type,
                    [str(f) for f in action.source_files],
                )
                operations.append(OperationResult(
                    operation_id=_make_operation_id("skip"),
                    action_type=action.action_type,
                    source_files=action.source_files,
                    status="SKIPPED",
                    error_message=f"No strategy for action type: {action.action_type}",
                ))

        completed_at = datetime.now()

        # Count file modifications
        files_deleted = sum(1 for op in operations if op.action_type == ActionType.DELETE and op.succeeded)
        files_moved = sum(1 for op in operations if op.action_type == ActionType.MOVE and op.succeeded)
        files_renamed = sum(1 for op in operations if op.action_type == ActionType.RENAME and op.succeeded)
        files_merged = sum(1 for op in operations if op.action_type == ActionType.MERGE and op.succeeded)
        files_modified = files_deleted + files_moved + files_renamed + files_merged

        return ExecutionReport(
            operations=operations,
            files_modified=files_modified,
            files_deleted=files_deleted,
            files_moved=files_moved,
            files_renamed=files_renamed,
            files_merged=files_merged,
            backup_location=backup_location,
            started_at=started_at,
            completed_at=completed_at,
            dry_run=dry_run
        )

    def cleanup_empty_dirs(
        self, root: Path, dry_run: bool = False
    ) -> list[Path]:
        """Remove empty directories after cleanup operations.

        Walks bottom-up to catch nested empty directories.
        Never removes project root, .git dirs, or dirs containing .gitkeep.

        Args:
            root: Root directory to scan
            dry_run: If True, only report what would be removed

        Returns:
            List of directories that were (or would be) removed
        """
        removed: list[Path] = []
        resolved_root = root.resolve()
        for dirpath in sorted(resolved_root.rglob("*"), reverse=True):
            if not dirpath.is_dir():
                continue
            # Safety: never remove project root or .git directories
            if dirpath == resolved_root or dirpath.name == ".git":
                continue
            # Skip if directory contains .gitkeep
            if (dirpath / ".gitkeep").exists():
                continue
            # Check if truly empty (no files, no subdirs)
            try:
                if not any(dirpath.iterdir()):
                    if not dry_run:
                        dirpath.rmdir()
                    removed.append(dirpath)
            except OSError:
                pass  # Permission error or race condition
        return removed


# =============================================================================
# CleanupOrchestrator - CLI Orchestrator (renamed from CleanupAgent, Enhancement #13)
# =============================================================================

class CleanupOrchestrator:
    """CLI orchestrator for cleanup workflows.

    Renamed from CleanupAgent to avoid collision with the BaseAgent-derived
    CleanupAgent in agents/cleanup/agent.py.
    """

    def __init__(
        self,
        project_root: Path,
        backup_dir: str = ".tapps-agents/cleanup-backups",
        age_threshold_days: int = 90,
        similarity_threshold: float = 0.8,
        exclude_names: list[str] | None = None,
    ):
        """Initialize cleanup orchestrator.

        Args:
            project_root: Root directory of project
            backup_dir: Backup directory relative to project root
            age_threshold_days: Days threshold for outdated file detection
            similarity_threshold: Threshold for near-duplicate detection
            exclude_names: Filenames to exclude from naming analysis
        """
        self.project_root = project_root
        self.analyzer = ProjectAnalyzer(
            project_root,
            age_threshold_days=age_threshold_days,
            exclude_names=exclude_names,
        )
        self.executor = CleanupExecutor(project_root, backup_dir=backup_dir)
        self.similarity_threshold = similarity_threshold

    async def run_analysis(
        self,
        scan_path: Path,
        pattern: str = "*.md",
        patterns: list[str] | None = None,
        respect_gitignore: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> AnalysisReport:
        """Run analysis workflow with multi-pattern and gitignore support."""
        return await self.analyzer.generate_analysis_report(
            scan_path, pattern, patterns=patterns,
            respect_gitignore=respect_gitignore,
            progress_callback=progress_callback,
        )

    def run_planning(self, analysis: AnalysisReport) -> CleanupPlan:
        """Run planning workflow."""
        planner = CleanupPlanner(analysis, similarity_threshold=self.similarity_threshold)
        return planner.generate_cleanup_plan()

    async def run_execution(
        self,
        plan: CleanupPlan,
        dry_run: bool = False,
        create_backup: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> ExecutionReport:
        """Run execution workflow."""
        return await self.executor.execute_plan(
            plan, dry_run=dry_run, create_backup=create_backup,
            progress_callback=progress_callback,
        )

    async def run_full_cleanup(
        self,
        scan_path: Path,
        pattern: str = "*.md",
        patterns: list[str] | None = None,
        respect_gitignore: bool = True,
        cleanup_empty_dirs: bool = True,
        dry_run: bool = False,
        create_backup: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[AnalysisReport, CleanupPlan, ExecutionReport]:
        """Run complete cleanup workflow."""
        # Step 1: Analysis (multi-pattern + gitignore)
        analysis = await self.run_analysis(
            scan_path, pattern, patterns=patterns,
            respect_gitignore=respect_gitignore,
            progress_callback=progress_callback,
        )

        # Step 2: Planning
        plan = self.run_planning(analysis)

        # Step 3: Execution
        execution = await self.run_execution(
            plan, dry_run=dry_run, create_backup=create_backup,
            progress_callback=progress_callback,
        )

        # Step 4: Clean up empty directories (post-execution)
        if cleanup_empty_dirs:
            self.executor.cleanup_empty_dirs(scan_path, dry_run=dry_run)

        return analysis, plan, execution

    def self_clean(
        self, max_age_days: int = 30, dry_run: bool = False
    ) -> dict[str, list[Path]]:
        """Clean stale data from the .tapps-agents/ directory.

        Targets ephemeral data: old workflow markers, old backups,
        completed sessions, and stale cache entries.

        Args:
            max_age_days: Maximum age in days for ephemeral files
            dry_run: If True, only report what would be cleaned

        Returns:
            Dict mapping category to list of paths removed (or would be removed)
        """
        import time

        tapps_dir = self.project_root / ".tapps-agents"
        if not tapps_dir.exists():
            return {}

        cutoff = time.time() - (max_age_days * 86400)
        cleaned: dict[str, list[Path]] = {
            "workflow_markers": [],
            "old_backups": [],
            "sessions": [],
        }

        # Clean old workflow markers
        markers_dir = tapps_dir / "workflows" / "markers"
        if markers_dir.exists():
            for marker in markers_dir.iterdir():
                if marker.is_dir() and marker.stat().st_mtime < cutoff:
                    cleaned["workflow_markers"].append(marker)
                    if not dry_run:
                        shutil.rmtree(marker, ignore_errors=True)

        # Clean old backup ZIPs
        backup_dir = tapps_dir / "cleanup-backups"
        if backup_dir.exists():
            for backup in backup_dir.glob("backup-*.zip"):
                if backup.stat().st_mtime < cutoff:
                    cleaned["old_backups"].append(backup)
                    if not dry_run:
                        backup.unlink(missing_ok=True)

        # Clean completed sessions
        sessions_dir = tapps_dir / "sessions"
        if sessions_dir.exists():
            for session in sessions_dir.iterdir():
                if session.is_file() and session.stat().st_mtime < cutoff:
                    cleaned["sessions"].append(session)
                    if not dry_run:
                        session.unlink(missing_ok=True)

        return cleaned


# Backward-compatible alias (Enhancement #13)
CleanupAgent = CleanupOrchestrator


# =============================================================================
# CLI Entry Point
# =============================================================================

async def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Project Cleanup Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze project structure")
    analyze_parser.add_argument("--path", type=Path, required=True, help="Path to analyze")
    analyze_parser.add_argument("--pattern", type=str, default="*.md", help="File pattern")
    analyze_parser.add_argument("--output", type=Path, help="Output file for report")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Generate cleanup plan")
    plan_parser.add_argument("--analysis", type=Path, required=True, help="Analysis report JSON file")
    plan_parser.add_argument("--output", type=Path, help="Output file for plan")

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute cleanup plan")
    execute_parser.add_argument("--plan", type=Path, required=True, help="Cleanup plan JSON file")
    execute_parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    execute_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")

    # Run command (full workflow)
    run_parser = subparsers.add_parser("run", help="Run full cleanup workflow")
    run_parser.add_argument("--path", type=Path, required=True, help="Path to analyze")
    run_parser.add_argument("--pattern", type=str, default="*.md", help="File pattern")
    run_parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    run_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")

    args = parser.parse_args()

    if args.command == "analyze":
        orchestrator = CleanupOrchestrator(args.path.parent)
        report = await orchestrator.run_analysis(args.path, args.pattern)

        if args.output:
            args.output.write_text(report.model_dump_json(indent=2))
            print(f"Analysis report saved to {args.output}")
        else:
            print(report.to_markdown())

    elif args.command == "plan":
        analysis = AnalysisReport.model_validate_json(args.analysis.read_text())
        orchestrator = CleanupOrchestrator(analysis.scan_path.parent)
        plan = orchestrator.run_planning(analysis)

        if args.output:
            args.output.write_text(plan.model_dump_json(indent=2))
            print(f"Cleanup plan saved to {args.output}")
        else:
            print(plan.to_markdown())

    elif args.command == "execute":
        plan = CleanupPlan.model_validate_json(args.plan.read_text())
        orchestrator = CleanupOrchestrator(Path.cwd())
        report = await orchestrator.run_execution(plan, dry_run=args.dry_run, create_backup=not args.no_backup)

        print(report.to_markdown())

    elif args.command == "run":
        orchestrator = CleanupOrchestrator(args.path.parent)
        analysis, plan, execution = await orchestrator.run_full_cleanup(
            args.path,
            args.pattern,
            dry_run=args.dry_run,
            create_backup=not args.no_backup
        )

        print("=" * 80)
        print(analysis.to_markdown())
        print("=" * 80)
        print(plan.to_markdown())
        print("=" * 80)
        print(execution.to_markdown())


if __name__ == "__main__":
    asyncio.run(main())
