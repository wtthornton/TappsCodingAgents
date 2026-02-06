"""RAG Synchronizer Module.

Synchronizes RAG knowledge files when code changes (package renames, API changes).

This module follows modular design principles:
- Small, focused functions (< 100 lines)
- Clear separation of concerns
- Single responsibility principle
- Comprehensive error handling and logging
- Atomic file operations with rollback support

Phase: 4 - Knowledge Synchronization
"""

import ast
import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Rename:
    """Represents a package/module rename detection."""

    old_name: str
    new_name: str
    file_path: Path
    confidence: float  # 0.0-1.0

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class StaleReference:
    """Represents an outdated import/reference in knowledge files."""

    file_path: Path
    line_number: int
    old_import: str
    suggested_import: str
    context: str  # Surrounding lines for context


@dataclass
class ChangeReport:
    """Comprehensive report of changes to be applied."""

    timestamp: str
    total_files: int
    total_changes: int
    renames: list[Rename] = field(default_factory=list)
    stale_refs: list[StaleReference] = field(default_factory=list)
    diff_preview: str = ""
    backup_path: Path | None = None


@dataclass
class BackupManifest:
    """Backup manifest with file checksums."""

    timestamp: str
    backup_dir: Path
    files: list[Path] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)  # file -> SHA256


class RagSynchronizer:
    """Synchronizes RAG knowledge files with codebase changes.

    This class provides modular functionality for:
    1. Detecting package renames via AST analysis
    2. Finding stale imports in knowledge files
    3. Updating code examples in knowledge files
    4. Generating detailed change reports with diffs
    5. Backing up files with SHA256 checksums
    6. Applying changes atomically with rollback support

    Design: Each method has a single responsibility and is < 100 lines.
    """

    def __init__(
        self,
        project_root: Path,
        knowledge_dir: Path | None = None,
        backup_dir: Path | None = None,
    ):
        """Initialize the RAG synchronizer.

        Args:
            project_root: Project root directory
            knowledge_dir: Knowledge base directory (defaults to .tapps-agents/knowledge)
            backup_dir: Backup directory (defaults to .tapps-agents/backups)
        """
        self.project_root = Path(project_root).resolve()
        self.knowledge_dir = knowledge_dir or self.project_root / ".tapps-agents" / "knowledge"
        self.backup_dir = backup_dir or self.project_root / ".tapps-agents" / "backups"

        # Validate paths
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")

        # Create directories if needed
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def detect_package_renames(self, source_dir: Path | None = None) -> list[Rename]:
        """Detect package/module renames in codebase using AST analysis.

        Args:
            source_dir: Source directory to scan (defaults to project root)

        Returns:
            List of detected Rename objects with confidence scores

        Performance Target: <5 seconds for typical projects
        """
        source_dir = source_dir or self.project_root
        renames: list[Rename] = []

        try:
            # Find all Python files
            python_files = list(source_dir.rglob("*.py"))

            # Track import patterns
            import_patterns: dict[str, set[Path]] = {}

            for py_file in python_files:
                try:
                    with open(py_file, encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=str(py_file))

                    # Extract import statements
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_name = alias.name
                                if import_name not in import_patterns:
                                    import_patterns[import_name] = set()
                                import_patterns[import_name].add(py_file)

                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                if node.module not in import_patterns:
                                    import_patterns[node.module] = set()
                                import_patterns[node.module].add(py_file)

                except (SyntaxError, UnicodeDecodeError) as e:
                    logger.debug(f"Skipping file {py_file}: {e}")
                    continue

            # Detect potential renames (simple heuristic: similar names, different usage)
            # This is a placeholder - real implementation would use git history
            # For now, we'll return empty list (to be enhanced with git integration)
            logger.info(f"Analyzed {len(python_files)} Python files, found {len(import_patterns)} unique imports")

        except Exception as e:
            logger.error(f"Failed to detect package renames: {e}")

        return renames

    def find_stale_imports(self, current_imports: set[str] | None = None) -> list[StaleReference]:
        """Find outdated imports in knowledge files.

        Args:
            current_imports: Set of current valid imports (auto-detected if None)

        Returns:
            List of StaleReference objects for outdated imports

        Performance Target: <3 seconds for typical knowledge bases
        """
        stale_refs: list[StaleReference] = []

        try:
            # Auto-detect current imports if not provided
            if current_imports is None:
                current_imports = self._get_current_imports()

            # Scan knowledge files
            md_files = list(self.knowledge_dir.rglob("*.md"))

            # Pattern to match Python imports in code blocks
            import_pattern = re.compile(r'^(?:from|import)\s+([\w.]+)', re.MULTILINE)

            for md_file in md_files:
                try:
                    with open(md_file, encoding='utf-8') as f:
                        lines = f.readlines()

                    in_code_block = False
                    for line_num, line in enumerate(lines, start=1):
                        # Track code blocks
                        if line.strip().startswith('```'):
                            in_code_block = not in_code_block
                            continue

                        # Only check imports in code blocks
                        if in_code_block:
                            match = import_pattern.search(line)
                            if match:
                                import_name = match.group(1)
                                # Check if import is stale (not in current imports)
                                if import_name not in current_imports:
                                    # Get context (3 lines before and after)
                                    context_start = max(0, line_num - 4)
                                    context_end = min(len(lines), line_num + 3)
                                    context = ''.join(lines[context_start:context_end])

                                    stale_ref = StaleReference(
                                        file_path=md_file,
                                        line_number=line_num,
                                        old_import=import_name,
                                        suggested_import="",  # To be filled by suggestion logic
                                        context=context,
                                    )
                                    stale_refs.append(stale_ref)

                except (OSError, UnicodeDecodeError) as e:
                    logger.warning(f"Skipping file {md_file}: {e}")
                    continue

            logger.info(f"Scanned {len(md_files)} knowledge files, found {len(stale_refs)} stale references")

        except Exception as e:
            logger.error(f"Failed to find stale imports: {e}")

        return stale_refs

    def _get_current_imports(self) -> set[str]:
        """Get set of current valid imports from codebase.

        Returns:
            Set of import names currently in use
        """
        current_imports: set[str] = set()

        try:
            python_files = list(self.project_root.rglob("*.py"))

            for py_file in python_files:
                try:
                    with open(py_file, encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=str(py_file))

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                current_imports.add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                current_imports.add(node.module)

                except (SyntaxError, UnicodeDecodeError):
                    continue

        except Exception as e:
            logger.error(f"Failed to get current imports: {e}")

        return current_imports

    def update_code_examples(
        self,
        file_path: Path,
        replacements: dict[str, str],
    ) -> bool:
        """Update code examples in a knowledge file with regex replacement.

        Args:
            file_path: Path to knowledge file to update
            replacements: Dictionary mapping old patterns to new patterns

        Returns:
            True if file was modified, False otherwise
        """
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False

        try:
            # Read original content
            with open(file_path, encoding='utf-8') as f:
                original_content = f.read()

            # Apply replacements
            modified_content = original_content
            for old_pattern, new_pattern in replacements.items():
                modified_content = re.sub(
                    re.escape(old_pattern),
                    new_pattern,
                    modified_content,
                    flags=re.MULTILINE
                )

            # Check if content changed
            if modified_content == original_content:
                logger.debug(f"No changes needed for {file_path}")
                return False

            # Write to temporary file first (atomic operation)
            temp_fd, temp_path = tempfile.mkstemp(suffix='.md', text=True)
            try:
                # Close the file descriptor first (important for Windows)
                os.close(temp_fd)

                # Write content
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)

                # Atomic rename
                shutil.move(temp_path, file_path)
                logger.info(f"Updated code examples in {file_path}")
                return True

            finally:
                # Clean up temp file if it still exists
                if Path(temp_path).exists():
                    Path(temp_path).unlink()

        except Exception as e:
            logger.error(f"Failed to update code examples in {file_path}: {e}")
            return False

    def generate_change_report(
        self,
        renames: list[Rename],
        stale_refs: list[StaleReference],
    ) -> ChangeReport:
        """Generate detailed change report with diff view.

        Args:
            renames: List of detected renames
            stale_refs: List of stale references

        Returns:
            ChangeReport object with comprehensive change summary
        """
        timestamp = datetime.now().isoformat()

        # Calculate totals
        affected_files = set()
        for stale_ref in stale_refs:
            affected_files.add(stale_ref.file_path)

        total_files = len(affected_files)
        total_changes = len(renames) + len(stale_refs)

        # Generate diff preview
        diff_lines = []
        diff_lines.append("=" * 80)
        diff_lines.append(f"Change Report - {timestamp}")
        diff_lines.append("=" * 80)
        diff_lines.append("")

        if renames:
            diff_lines.append(f"Package Renames ({len(renames)}):")
            for rename in renames:
                diff_lines.append(f"  - {rename.old_name} → {rename.new_name} (confidence: {rename.confidence:.2f})")
            diff_lines.append("")

        if stale_refs:
            diff_lines.append(f"Stale References ({len(stale_refs)}):")
            for ref in stale_refs:
                diff_lines.append(f"  - {ref.file_path}:{ref.line_number}")
                diff_lines.append(f"    Old: {ref.old_import}")
                if ref.suggested_import:
                    diff_lines.append(f"    Suggested: {ref.suggested_import}")
            diff_lines.append("")

        diff_preview = '\n'.join(diff_lines)

        report = ChangeReport(
            timestamp=timestamp,
            total_files=total_files,
            total_changes=total_changes,
            renames=renames,
            stale_refs=stale_refs,
            diff_preview=diff_preview,
        )

        return report

    def backup_knowledge_files(self, files: list[Path]) -> BackupManifest:
        """Backup knowledge files with SHA256 checksums.

        Args:
            files: List of files to backup

        Returns:
            BackupManifest with backup metadata and checksums
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir(parents=True, exist_ok=True)

        checksums: dict[str, str] = {}
        backed_up_files: list[Path] = []

        try:
            for file_path in files:
                if not file_path.exists():
                    logger.warning(f"File does not exist, skipping: {file_path}")
                    continue

                # Calculate SHA256 checksum
                sha256 = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        sha256.update(chunk)
                checksum = sha256.hexdigest()

                # Backup file
                relative_path = file_path.relative_to(self.project_root)
                backup_file = backup_subdir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(file_path, backup_file)

                checksums[str(relative_path)] = checksum
                backed_up_files.append(backup_file)

            # Save manifest
            manifest_path = backup_subdir / "manifest.json"
            manifest_data = {
                "timestamp": timestamp,
                "backup_dir": str(backup_subdir),
                "files": [str(f) for f in backed_up_files],
                "checksums": checksums,
            }
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2)

            logger.info(f"Backed up {len(backed_up_files)} files to {backup_subdir}")

            return BackupManifest(
                timestamp=timestamp,
                backup_dir=backup_subdir,
                files=backed_up_files,
                checksums=checksums,
            )

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def apply_changes(
        self,
        changes: ChangeReport,
        backup_manifest: BackupManifest | None = None,
        dry_run: bool = False,
    ) -> bool:
        """Apply changes atomically with rollback support.

        Args:
            changes: ChangeReport with changes to apply
            backup_manifest: Backup manifest for rollback (if None, creates new backup)
            dry_run: If True, only simulate changes without applying

        Returns:
            True if changes applied successfully, False otherwise
        """
        if dry_run:
            logger.info("DRY RUN: Simulating changes without applying")
            logger.info(changes.diff_preview)
            return True

        try:
            # Create backup if not provided
            if backup_manifest is None:
                affected_files = set()
                for stale_ref in changes.stale_refs:
                    affected_files.add(stale_ref.file_path)

                backup_manifest = self.backup_knowledge_files(list(affected_files))

            # Apply stale reference updates
            replacements_by_file: dict[Path, dict[str, str]] = {}

            for stale_ref in changes.stale_refs:
                if stale_ref.file_path not in replacements_by_file:
                    replacements_by_file[stale_ref.file_path] = {}

                replacements_by_file[stale_ref.file_path][stale_ref.old_import] = (
                    stale_ref.suggested_import or stale_ref.old_import
                )

            # Apply updates to each file
            success = True
            for file_path, replacements in replacements_by_file.items():
                if not self.update_code_examples(file_path, replacements):
                    logger.warning(f"Failed to update {file_path}")
                    success = False

            if not success:
                # Rollback on failure
                logger.error("Changes failed, rolling back...")
                self._rollback(backup_manifest)
                return False

            logger.info(f"Successfully applied {changes.total_changes} changes to {changes.total_files} files")
            return True

        except Exception as e:
            logger.error(f"Failed to apply changes: {e}")
            if backup_manifest:
                logger.error("Rolling back changes...")
                self._rollback(backup_manifest)
            return False

    def _rollback(self, backup_manifest: BackupManifest) -> None:
        """Rollback changes from backup.

        Args:
            backup_manifest: Backup manifest to restore from
        """
        try:
            for backed_up_file in backup_manifest.files:
                relative_path = backed_up_file.relative_to(backup_manifest.backup_dir)
                original_file = self.project_root / relative_path

                # Restore file
                shutil.copy2(backed_up_file, original_file)

                # Verify checksum
                sha256 = hashlib.sha256()
                with open(original_file, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        sha256.update(chunk)
                checksum = sha256.hexdigest()

                expected_checksum = backup_manifest.checksums.get(str(relative_path))
                if checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {original_file}, rollback may be incomplete")

            logger.info(f"Rolled back {len(backup_manifest.files)} files from backup")

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
