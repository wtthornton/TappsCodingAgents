"""Project Cleanup Agent - Automated project structure analysis and cleanup.

This module provides tools for analyzing project structure, identifying cleanup
opportunities, and safely executing cleanup operations with backups and rollback.

Architecture:
    - ProjectAnalyzer: Scan and analyze project structure
    - CleanupPlanner: Generate cleanup plans with categorization
    - CleanupExecutor: Execute cleanup operations safely
    - CleanupAgent: CLI orchestrator

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
import json
import re
import shutil
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import aiofiles
from difflib import SequenceMatcher
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from git import Repo, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


# =============================================================================
# Data Models (Pydantic)
# =============================================================================

class ActionType(str, Enum):
    """Types of cleanup actions."""
    DELETE = "delete"
    MOVE = "move"
    RENAME = "rename"
    MERGE = "merge"

    def __str__(self) -> str:
        return self.value


class SafetyLevel(str, Enum):
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


class FileCategory(str, Enum):
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
    files: List[Path] = Field(..., description="List of file paths with identical content", min_length=2)
    size: int = Field(..., description="File size in bytes", ge=0)
    recommendation: str = Field(..., description="Recommended action for this group")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def primary_file(self) -> Path:
        """Return the file to keep (first in list)."""
        return self.files[0]

    @property
    def duplicates(self) -> List[Path]:
        """Return files to delete/merge (all except first)."""
        return self.files[1:]

    @property
    def savings(self) -> int:
        """Potential space savings by removing duplicates."""
        return self.size * (len(self.files) - 1)


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


class AnalysisReport(BaseModel):
    """Analysis report of project structure."""
    total_files: int = Field(..., description="Total number of files analyzed", ge=0)
    total_size: int = Field(..., description="Total size of all files in bytes", ge=0)
    duplicates: List[DuplicateGroup] = Field(default_factory=list, description="Groups of duplicate files")
    outdated_files: List[OutdatedFile] = Field(default_factory=list, description="Files not modified recently")
    naming_issues: List[NamingIssue] = Field(default_factory=list, description="Files with naming convention violations")
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


class CleanupAction(BaseModel):
    """Individual cleanup action."""
    action_type: ActionType = Field(..., description="Type of action")
    source_files: List[Path] = Field(..., description="Source file(s) for this action", min_length=1)
    target_path: Optional[Path] = Field(None, description="Target path (for MOVE/RENAME actions)")
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
    actions: List[CleanupAction] = Field(..., description="List of cleanup actions to perform")
    priorities: Dict[str, int] = Field(default_factory=dict, description="Action counts by priority")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Action dependencies")
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
    source_files: List[Path] = Field(..., description="Source file(s)")
    target_path: Optional[Path] = Field(None, description="Target path (if applicable)")
    status: str = Field(..., description="Operation status", pattern="^(SUCCESS|FAILED|SKIPPED)$")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")
    references_updated: int = Field(0, description="Number of cross-references updated", ge=0)
    timestamp: datetime = Field(default_factory=datetime.now, description="When operation was performed")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def succeeded(self) -> bool:
        """Whether operation succeeded."""
        return self.status == "SUCCESS"


class ExecutionReport(BaseModel):
    """Complete execution report."""
    operations: List[OperationResult] = Field(..., description="List of operation results")
    files_modified: int = Field(..., description="Total number of files modified", ge=0)
    files_deleted: int = Field(0, description="Number of files deleted", ge=0)
    files_moved: int = Field(0, description="Number of files moved", ge=0)
    files_renamed: int = Field(0, description="Number of files renamed", ge=0)
    backup_location: Optional[Path] = Field(None, description="Path to backup archive")
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
- **Total:** {self.files_modified}

## Backup
- **Location:** {self.backup_location}
"""


# =============================================================================
# ProjectAnalyzer - Analysis Layer
# =============================================================================

class ProjectAnalyzer:
    """Analyze project structure and identify cleanup opportunities."""

    def __init__(self, project_root: Path):
        """Initialize analyzer.

        Args:
            project_root: Root directory of project to analyze
        """
        self.project_root = project_root.resolve()
        self._validate_path(self.project_root)
        self._repo: Optional['Repo'] = None
        if GIT_AVAILABLE:
            try:
                self._repo = Repo(self.project_root)
            except InvalidGitRepositoryError:
                pass  # Not a git repo, continue without git features

    def _validate_path(self, path: Path) -> None:
        """Validate path is safe and within project."""
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

    async def scan_directory_structure(self, path: Path, pattern: str = "*.md") -> List[Path]:
        """Scan directory for files matching pattern.

        Args:
            path: Directory to scan
            pattern: Glob pattern for files to include

        Returns:
            List of file paths matching pattern
        """
        self._validate_path(path)
        files: List[Path] = []

        def scan_sync(directory: Path) -> List[Path]:
            """Synchronous scan helper."""
            return list(directory.rglob(pattern))

        # Run sync scan in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(None, scan_sync, path)

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

    async def detect_duplicates(self, files: List[Path]) -> List[DuplicateGroup]:
        """Detect duplicate files by content hash.

        Args:
            files: List of files to check

        Returns:
            List of duplicate groups
        """
        hash_map: Dict[str, List[Path]] = {}

        # Calculate hashes concurrently
        tasks = [self.hash_file(f) for f in files]
        hashes = await asyncio.gather(*tasks)

        # Group files by hash
        for file, file_hash in zip(files, hashes):
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

    def analyze_naming_patterns(self, files: List[Path]) -> List[NamingIssue]:
        """Analyze file naming patterns and detect violations.

        Args:
            files: List of files to check

        Returns:
            List of naming issues
        """
        issues = []
        kebab_pattern = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*\.(md|json|yaml|yml|txt)$')

        for file in files:
            name = file.name
            stem = file.stem  # File name without extension

            # Skip if already kebab-case
            if kebab_pattern.match(name):
                continue

            # Detect violation type
            violation = None
            if stem.isupper():
                violation = "UPPERCASE"
            elif '_' in stem:
                violation = "snake_case"
            elif any(c.isupper() for c in stem):
                violation = "MixedCase"

            if violation:
                # Generate kebab-case suggestion
                suggested = name.lower().replace('_', '-').replace(' ', '-')
                suggested = re.sub(r'[^a-z0-9.-]', '', suggested)

                issues.append(NamingIssue(
                    path=file,
                    current_name=name,
                    suggested_name=suggested,
                    pattern_violation=violation
                ))

        return issues

    def detect_outdated_files(self, files: List[Path], age_threshold_days: int = 90) -> List[OutdatedFile]:
        """Detect files that haven't been modified recently.

        Args:
            files: List of files to check
            age_threshold_days: Age threshold in days

        Returns:
            List of outdated files
        """
        outdated = []
        now = datetime.now()

        for file in files:
            # Get last modified time from git if available, else filesystem
            last_modified = self._get_last_modified_date(file)
            age_days = (now - last_modified).days

            if age_days >= age_threshold_days:
                # Count references to this file
                ref_count = self._count_references(file, files)

                # Determine recommendation
                if age_days > 90 and ref_count == 0:
                    category = FileCategory.DELETE
                elif age_days > 90:
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

    def _count_references(self, target_file: Path, all_files: List[Path]) -> int:
        """Count references to target file in other files.

        Args:
            target_file: File to search for
            all_files: List of all files to search in

        Returns:
            Number of references found
        """
        count = 0
        target_name = target_file.name
        target_path_str = str(target_file.relative_to(self.project_root))

        for file in all_files:
            if file == target_file:
                continue

            try:
                content = file.read_text(encoding='utf-8', errors='ignore')

                # Check for references: [text](path), docs/file.md
                if target_name in content or target_path_str in content:
                    count += 1
            except Exception:
                pass  # Skip files that can't be read

        return count

    async def generate_analysis_report(self, scan_path: Path, pattern: str = "*.md") -> AnalysisReport:
        """Generate comprehensive analysis report.

        Args:
            scan_path: Path to scan
            pattern: File pattern to match

        Returns:
            Analysis report
        """
        # Scan files
        files = await self.scan_directory_structure(scan_path, pattern)

        # Calculate total size
        total_size = sum(f.stat().st_size for f in files)

        # Run analysis tasks
        duplicates = await self.detect_duplicates(files)
        naming_issues = self.analyze_naming_patterns(files)
        outdated_files = self.detect_outdated_files(files)

        return AnalysisReport(
            total_files=len(files),
            total_size=total_size,
            duplicates=duplicates,
            outdated_files=outdated_files,
            naming_issues=naming_issues,
            scan_path=scan_path
        )


# =============================================================================
# CleanupPlanner - Planning Layer
# =============================================================================

class CleanupPlanner:
    """Generate cleanup plans with categorization and prioritization."""

    def __init__(self, analysis_report: AnalysisReport):
        """Initialize planner.

        Args:
            analysis_report: Analysis report to plan from
        """
        self.analysis = analysis_report

    def detect_content_similarity(self, file1: Path, file2: Path, threshold: float = 0.8) -> float:
        """Detect content similarity between two files.

        Args:
            file1: First file
            file2: Second file
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            Similarity ratio (0.0-1.0)
        """
        try:
            content1 = file1.read_text(encoding='utf-8', errors='ignore')
            content2 = file2.read_text(encoding='utf-8', errors='ignore')

            return SequenceMatcher(None, content1, content2).ratio()
        except Exception:
            return 0.0

    def categorize_files(self) -> Dict[FileCategory, List[Path]]:
        """Categorize files based on analysis results.

        Returns:
            Dictionary mapping categories to file lists
        """
        categories: Dict[FileCategory, List[Path]] = {
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

        return categories

    def prioritize_actions(self, actions: List[CleanupAction]) -> List[CleanupAction]:
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
        actions: List[CleanupAction] = []

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
        """Update markdown link reference.

        Args:
            match: Regex match object
            old_path: Old file path
            new_path: New file path

        Returns:
            Updated match string
        """
        link_text = match.group(1)
        link_target = match.group(2)

        # Check if link target matches old filename
        if Path(link_target).name == old_path.name or link_target == str(old_path):
            # Update to new filename/path
            new_target = str(new_path) if '/' in link_target else new_path.name
            return f'[{link_text}]({new_target})'

        return match.group(0)  # No change

    def _update_relative_path(self, match, old_path: Path, new_path: Path) -> str:
        """Update relative path reference.

        Args:
            match: Regex match object
            old_path: Old file path
            new_path: New file path

        Returns:
            Updated match string
        """
        prefix = match.group(1) or ''
        path_str = match.group(2)

        # Check if path matches old filename
        if Path(path_str).name == old_path.name or path_str == str(old_path):
            # Preserve relative path structure - use name if path had no directory, else use relative path
            if '/' in path_str:
                # Path had directory structure - try to preserve it
                old_parts = Path(path_str).parts
                new_relative = '/'.join(old_parts[:-1] + (new_path.name,))
                return f'{prefix}{new_relative}'
            else:
                # Simple filename - use new name only
                return f'{prefix}{new_path.name}'

        return match.group(0)  # No change

    def scan_and_update_references(
        self,
        old_path: Path,
        new_path: Path,
        dry_run: bool = False
    ) -> int:
        """Scan all text files and update references.

        Args:
            old_path: Old file path
            new_path: New file path
            dry_run: If True, don't actually modify files

        Returns:
            Number of references updated
        """
        references_updated = 0
        old_name = old_path.name

        # Scan all text files in project
        text_extensions = {'.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.txt', '.rst'}

        for file in self.project_root.rglob('*'):
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

                    def replacer(match):
                        nonlocal file_updated
                        updated = update_func(match, old_path, new_path)
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
        try:
            for file in action.source_files:
                if not dry_run:
                    file.unlink()

            return OperationResult(
                operation_id=f"del-{action.source_files[0].stem}",
                action_type=ActionType.DELETE,
                source_files=action.source_files,
                status="SUCCESS"
            )
        except Exception as e:
            return OperationResult(
                operation_id=f"del-{action.source_files[0].stem}",
                action_type=ActionType.DELETE,
                source_files=action.source_files,
                status="FAILED",
                error_message=str(e)
            )


class RenameStrategy(CleanupStrategy):
    """Strategy for renaming files."""

    def __init__(self, repo: Optional['Repo'] = None, project_root: Optional[Path] = None):
        """Initialize rename strategy.

        Args:
            repo: Git repository for git mv operations
            project_root: Project root for reference updating
        """
        self.repo = repo
        self.reference_updater = ReferenceUpdater(project_root) if project_root else None

    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute rename action."""
        try:
            source = action.source_files[0]
            target = action.target_path
            references_updated = 0

            if not dry_run:
                if self.repo and GIT_AVAILABLE:
                    # Use git mv to preserve history
                    try:
                        self.repo.git.mv(str(source), str(target))
                    except Exception:
                        # Fall back to regular rename
                        source.rename(target)
                else:
                    source.rename(target)

                # Update references in other files
                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=False
                    )
            else:
                # Dry-run: count references that would be updated
                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=True
                    )

            return OperationResult(
                operation_id=f"ren-{source.stem}",
                action_type=ActionType.RENAME,
                source_files=[source],
                target_path=target,
                status="SUCCESS",
                references_updated=references_updated
            )
        except Exception as e:
            return OperationResult(
                operation_id=f"ren-{action.source_files[0].stem}",
                action_type=ActionType.RENAME,
                source_files=action.source_files,
                target_path=action.target_path,
                status="FAILED",
                error_message=str(e)
            )


class MoveStrategy(CleanupStrategy):
    """Strategy for moving files."""

    def __init__(self, repo: Optional['Repo'] = None, project_root: Optional[Path] = None):
        """Initialize move strategy.

        Args:
            repo: Git repository for git mv operations
            project_root: Project root for reference updating
        """
        self.repo = repo
        self.reference_updater = ReferenceUpdater(project_root) if project_root else None

    async def execute(self, action: CleanupAction, dry_run: bool = False) -> OperationResult:
        """Execute move action."""
        try:
            source = action.source_files[0]
            target = action.target_path
            references_updated = 0

            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))

                # Update references in other files
                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=False
                    )
            else:
                # Dry-run: count references that would be updated
                if self.reference_updater:
                    references_updated = self.reference_updater.scan_and_update_references(
                        source, target, dry_run=True
                    )

            return OperationResult(
                operation_id=f"mov-{source.stem}",
                action_type=ActionType.MOVE,
                source_files=[source],
                target_path=target,
                status="SUCCESS",
                references_updated=references_updated
            )
        except Exception as e:
            return OperationResult(
                operation_id=f"mov-{action.source_files[0].stem}",
                action_type=ActionType.MOVE,
                source_files=action.source_files,
                target_path=action.target_path,
                status="FAILED",
                error_message=str(e)
            )


class CleanupExecutor:
    """Execute cleanup operations safely with backups and rollback."""

    def __init__(self, project_root: Path):
        """Initialize executor.

        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root.resolve()
        self.backup_dir = project_root / ".cleanup-backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Initialize strategies
        repo = None
        if GIT_AVAILABLE:
            try:
                repo = Repo(project_root)
            except Exception:
                pass

        self.strategies: Dict[ActionType, CleanupStrategy] = {
            ActionType.DELETE: DeleteStrategy(),
            ActionType.RENAME: RenameStrategy(repo, self.project_root),
            ActionType.MOVE: MoveStrategy(repo, self.project_root)
        }

    def create_backup(self) -> Path:
        """Create timestamped backup of project.

        Returns:
            Path to backup ZIP file
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / f"backup-{timestamp}.zip"

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in self.project_root.rglob("*"):
                if file.is_file() and ".cleanup-backups" not in str(file):
                    arcname = file.relative_to(self.project_root)
                    zipf.write(file, arcname)

        return backup_path

    async def execute_dry_run(self, plan: CleanupPlan) -> ExecutionReport:
        """Execute dry-run (preview changes without modifying files).

        Args:
            plan: Cleanup plan to execute

        Returns:
            Execution report
        """
        return await self.execute_plan(plan, dry_run=True)

    async def execute_plan(self, plan: CleanupPlan, dry_run: bool = False, create_backup: bool = True) -> ExecutionReport:
        """Execute cleanup plan.

        Args:
            plan: Cleanup plan to execute
            dry_run: If True, don't actually modify files
            create_backup: If True, create backup before execution

        Returns:
            Execution report
        """
        started_at = datetime.now()
        operations: List[OperationResult] = []
        backup_location = None

        # Create backup if requested and not dry-run
        if create_backup and not dry_run:
            backup_location = self.create_backup()

        # Execute actions
        for action in plan.actions:
            strategy = self.strategies.get(action.action_type)
            if strategy:
                result = await strategy.execute(action, dry_run=dry_run)
                operations.append(result)

        completed_at = datetime.now()

        # Count file modifications
        files_deleted = sum(1 for op in operations if op.action_type == ActionType.DELETE and op.succeeded)
        files_moved = sum(1 for op in operations if op.action_type == ActionType.MOVE and op.succeeded)
        files_renamed = sum(1 for op in operations if op.action_type == ActionType.RENAME and op.succeeded)
        files_modified = files_deleted + files_moved + files_renamed

        return ExecutionReport(
            operations=operations,
            files_modified=files_modified,
            files_deleted=files_deleted,
            files_moved=files_moved,
            files_renamed=files_renamed,
            backup_location=backup_location,
            started_at=started_at,
            completed_at=completed_at,
            dry_run=dry_run
        )


# =============================================================================
# CleanupAgent - CLI Orchestrator
# =============================================================================

class CleanupAgent:
    """CLI orchestrator for cleanup workflows."""

    def __init__(self, project_root: Path):
        """Initialize cleanup agent.

        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root
        self.analyzer = ProjectAnalyzer(project_root)
        self.executor = CleanupExecutor(project_root)

    async def run_analysis(self, scan_path: Path, pattern: str = "*.md") -> AnalysisReport:
        """Run analysis workflow.

        Args:
            scan_path: Path to scan
            pattern: File pattern

        Returns:
            Analysis report
        """
        return await self.analyzer.generate_analysis_report(scan_path, pattern)

    def run_planning(self, analysis: AnalysisReport) -> CleanupPlan:
        """Run planning workflow.

        Args:
            analysis: Analysis report

        Returns:
            Cleanup plan
        """
        planner = CleanupPlanner(analysis)
        return planner.generate_cleanup_plan()

    async def run_execution(self, plan: CleanupPlan, dry_run: bool = False, create_backup: bool = True) -> ExecutionReport:
        """Run execution workflow.

        Args:
            plan: Cleanup plan
            dry_run: Preview mode
            create_backup: Create backup before execution

        Returns:
            Execution report
        """
        return await self.executor.execute_plan(plan, dry_run=dry_run, create_backup=create_backup)

    async def run_full_cleanup(
        self,
        scan_path: Path,
        pattern: str = "*.md",
        dry_run: bool = False,
        create_backup: bool = True
    ) -> tuple[AnalysisReport, CleanupPlan, ExecutionReport]:
        """Run complete cleanup workflow.

        Args:
            scan_path: Path to scan
            pattern: File pattern
            dry_run: Preview mode
            create_backup: Create backup before execution

        Returns:
            Tuple of (analysis_report, cleanup_plan, execution_report)
        """
        # Step 1: Analysis
        analysis = await self.run_analysis(scan_path, pattern)

        # Step 2: Planning
        plan = self.run_planning(analysis)

        # Step 3: Execution
        execution = await self.run_execution(plan, dry_run=dry_run, create_backup=create_backup)

        return analysis, plan, execution


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
        agent = CleanupAgent(args.path.parent)
        report = await agent.run_analysis(args.path, args.pattern)

        if args.output:
            args.output.write_text(report.model_dump_json(indent=2))
            print(f"Analysis report saved to {args.output}")
        else:
            print(report.to_markdown())

    elif args.command == "plan":
        analysis = AnalysisReport.model_validate_json(args.analysis.read_text())
        agent = CleanupAgent(analysis.scan_path.parent)
        plan = agent.run_planning(analysis)

        if args.output:
            args.output.write_text(plan.model_dump_json(indent=2))
            print(f"Cleanup plan saved to {args.output}")
        else:
            print(plan.to_markdown())

    elif args.command == "execute":
        plan = CleanupPlan.model_validate_json(args.plan.read_text())
        agent = CleanupAgent(Path.cwd())
        report = await agent.run_execution(plan, dry_run=args.dry_run, create_backup=not args.no_backup)

        print(report.to_markdown())

    elif args.command == "run":
        agent = CleanupAgent(args.path.parent)
        analysis, plan, execution = await agent.run_full_cleanup(
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
