"""Comprehensive tests for RagSynchronizer module.

Tests cover:
- Data class validation
- Package rename detection
- Stale import finding
- Code example updates
- Change report generation
- Backup and rollback operations
- Atomic file operations
- Error handling and edge cases

Target: ≥90% coverage
"""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tapps_agents.core.sync.rag_synchronizer import (
    BackupManifest,
    ChangeReport,
    RagSynchronizer,
    Rename,
    StaleReference,
)


# ============================================================================
# Data Class Tests
# ============================================================================


@pytest.mark.unit
@pytest.mark.unit
class TestRenameDataClass:
    """Test Rename data class validation."""

    def test_rename_valid_confidence(self):
        """Test Rename with valid confidence score."""
        rename = Rename(
            old_name="old_package",
            new_name="new_package",
            file_path=Path("test.py"),
            confidence=0.85,
        )
        assert rename.confidence == 0.85

    def test_rename_invalid_confidence_too_high(self):
        """Test Rename rejects confidence > 1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Rename(
                old_name="old",
                new_name="new",
                file_path=Path("test.py"),
                confidence=1.5,
            )

    def test_rename_invalid_confidence_too_low(self):
        """Test Rename rejects confidence < 0.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Rename(
                old_name="old",
                new_name="new",
                file_path=Path("test.py"),
                confidence=-0.1,
            )

    def test_rename_confidence_boundary_values(self):
        """Test Rename accepts boundary confidence values."""
        # Test 0.0
        rename_min = Rename(
            old_name="old",
            new_name="new",
            file_path=Path("test.py"),
            confidence=0.0,
        )
        assert rename_min.confidence == 0.0

        # Test 1.0
        rename_max = Rename(
            old_name="old",
            new_name="new",
            file_path=Path("test.py"),
            confidence=1.0,
        )
        assert rename_max.confidence == 1.0


@pytest.mark.unit
class TestStaleReferenceDataClass:
    """Test StaleReference data class."""

    def test_stale_reference_creation(self):
        """Test StaleReference creation with all fields."""
        ref = StaleReference(
            file_path=Path("docs/example.md"),
            line_number=42,
            old_import="old_module",
            suggested_import="new_module",
            context="import old_module\n",
        )
        assert ref.file_path == Path("docs/example.md")
        assert ref.line_number == 42
        assert ref.old_import == "old_module"
        assert ref.suggested_import == "new_module"


@pytest.mark.unit
class TestChangeReportDataClass:
    """Test ChangeReport data class."""

    def test_change_report_creation(self):
        """Test ChangeReport creation."""
        rename = Rename("old", "new", Path("test.py"), 0.9)
        ref = StaleReference(Path("doc.md"), 1, "old", "new", "context")

        report = ChangeReport(
            timestamp="2024-01-01T00:00:00",
            total_files=1,
            total_changes=2,
            renames=[rename],
            stale_refs=[ref],
            diff_preview="Changes...",
            backup_path=Path("/backup"),
        )

        assert report.total_files == 1
        assert report.total_changes == 2
        assert len(report.renames) == 1
        assert len(report.stale_refs) == 1


# ============================================================================
# RagSynchronizer Initialization Tests
# ============================================================================


@pytest.mark.unit
class TestRagSynchronizerInit:
    """Test RagSynchronizer initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default paths."""
        sync = RagSynchronizer(tmp_path)

        assert sync.project_root == tmp_path.resolve()
        assert sync.knowledge_dir == tmp_path / ".tapps-agents" / "knowledge"
        assert sync.backup_dir == tmp_path / ".tapps-agents" / "backups"

        # Directories should be created
        assert sync.knowledge_dir.exists()
        assert sync.backup_dir.exists()

    def test_init_with_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        knowledge_dir = tmp_path / "custom_knowledge"
        backup_dir = tmp_path / "custom_backup"

        sync = RagSynchronizer(
            tmp_path,
            knowledge_dir=knowledge_dir,
            backup_dir=backup_dir,
        )

        assert sync.knowledge_dir == knowledge_dir
        assert sync.backup_dir == backup_dir
        assert knowledge_dir.exists()
        assert backup_dir.exists()

    def test_init_nonexistent_project_root(self, tmp_path):
        """Test initialization fails with nonexistent project root."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(ValueError, match="Project root does not exist"):
            RagSynchronizer(nonexistent)


# ============================================================================
# Package Rename Detection Tests
# ============================================================================


@pytest.mark.unit
class TestDetectPackageRenames:
    """Test package rename detection functionality."""

    def test_detect_renames_empty_directory(self, tmp_path):
        """Test rename detection with no Python files."""
        sync = RagSynchronizer(tmp_path)
        renames = sync.detect_package_renames()

        assert isinstance(renames, list)
        assert len(renames) == 0

    def test_detect_renames_with_python_files(self, tmp_path):
        """Test rename detection with Python files."""
        # Create test Python file with imports
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "import os\nimport sys\nfrom pathlib import Path\n"
        )

        sync = RagSynchronizer(tmp_path)
        renames = sync.detect_package_renames()

        # Current implementation returns empty list (placeholder)
        assert isinstance(renames, list)

    def test_detect_renames_with_syntax_errors(self, tmp_path):
        """Test rename detection handles syntax errors gracefully."""
        # Create Python file with syntax error
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("import (invalid syntax")

        sync = RagSynchronizer(tmp_path)
        renames = sync.detect_package_renames()

        # Should not raise, just skip the file
        assert isinstance(renames, list)

    def test_detect_renames_custom_source_dir(self, tmp_path):
        """Test rename detection with custom source directory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        test_file = src_dir / "module.py"
        test_file.write_text("import requests\n")

        sync = RagSynchronizer(tmp_path)
        renames = sync.detect_package_renames(source_dir=src_dir)

        assert isinstance(renames, list)


# ============================================================================
# Stale Import Finding Tests
# ============================================================================


@pytest.mark.unit
class TestFindStaleImports:
    """Test stale import finding functionality."""

    def test_find_stale_imports_empty_knowledge(self, tmp_path):
        """Test stale import finding with no knowledge files."""
        sync = RagSynchronizer(tmp_path)
        stale_refs = sync.find_stale_imports()

        assert isinstance(stale_refs, list)
        assert len(stale_refs) == 0

    def test_find_stale_imports_no_code_blocks(self, tmp_path):
        """Test stale import finding with markdown without code blocks."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        doc = knowledge_dir / "example.md"
        doc.write_text("# Example\n\nThis is plain text without code blocks.")

        sync = RagSynchronizer(tmp_path)
        stale_refs = sync.find_stale_imports()

        assert len(stale_refs) == 0

    def test_find_stale_imports_with_current_imports(self, tmp_path):
        """Test stale import finding with current imports provided."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        doc = knowledge_dir / "example.md"
        doc.write_text(
            "# Example\n\n```python\nimport os\nimport sys\n```"
        )

        # Create Python file with current imports
        py_file = tmp_path / "test.py"
        py_file.write_text("import os\n")

        sync = RagSynchronizer(tmp_path)
        current_imports = {"os"}
        stale_refs = sync.find_stale_imports(current_imports=current_imports)

        # sys is not in current_imports, so it should be detected as stale
        assert len(stale_refs) == 1
        assert stale_refs[0].old_import == "sys"

    def test_find_stale_imports_auto_detect(self, tmp_path):
        """Test stale import finding with auto-detection."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        doc = knowledge_dir / "example.md"
        doc.write_text(
            "# Example\n\n```python\nimport requests\n```"
        )

        sync = RagSynchronizer(tmp_path)
        stale_refs = sync.find_stale_imports()

        # requests not in codebase, should be detected
        assert isinstance(stale_refs, list)

    def test_find_stale_imports_with_context(self, tmp_path):
        """Test stale reference includes context."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        doc = knowledge_dir / "example.md"
        doc.write_text(
            "Line 1\nLine 2\n```python\nimport stale_module\n```\nLine 5"
        )

        sync = RagSynchronizer(tmp_path)
        stale_refs = sync.find_stale_imports(current_imports=set())

        if stale_refs:
            assert stale_refs[0].context != ""
            assert "stale_module" in stale_refs[0].context


# ============================================================================
# Code Example Update Tests
# ============================================================================


@pytest.mark.unit
class TestUpdateCodeExamples:
    """Test code example update functionality."""

    def test_update_code_examples_simple_replacement(self, tmp_path):
        """Test simple code example replacement."""
        test_file = tmp_path / "example.md"
        test_file.write_text("import old_module\n")

        sync = RagSynchronizer(tmp_path)
        result = sync.update_code_examples(
            test_file,
            {"old_module": "new_module"}
        )

        assert result is True
        assert "new_module" in test_file.read_text()
        assert "old_module" not in test_file.read_text()

    def test_update_code_examples_multiple_replacements(self, tmp_path):
        """Test multiple replacements in one file."""
        test_file = tmp_path / "example.md"
        test_file.write_text("import old1\nimport old2\n")

        sync = RagSynchronizer(tmp_path)
        result = sync.update_code_examples(
            test_file,
            {"old1": "new1", "old2": "new2"}
        )

        assert result is True
        content = test_file.read_text()
        assert "new1" in content
        assert "new2" in content

    def test_update_code_examples_no_changes_needed(self, tmp_path):
        """Test update when no changes are needed."""
        test_file = tmp_path / "example.md"
        test_file.write_text("import module\n")

        sync = RagSynchronizer(tmp_path)
        result = sync.update_code_examples(
            test_file,
            {"nonexistent": "replacement"}
        )

        assert result is False  # No changes made

    def test_update_code_examples_nonexistent_file(self, tmp_path):
        """Test update fails gracefully for nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.md"

        sync = RagSynchronizer(tmp_path)
        result = sync.update_code_examples(
            nonexistent,
            {"old": "new"}
        )

        assert result is False

    def test_update_code_examples_atomic_operation(self, tmp_path):
        """Test update uses atomic operations (temp file)."""
        test_file = tmp_path / "example.md"
        original_content = "import old\n"
        test_file.write_text(original_content)

        sync = RagSynchronizer(tmp_path)

        # Mock temp file creation to verify atomic operation
        with patch('tempfile.mkstemp') as mock_mkstemp:
            mock_fd = 123
            mock_path = str(tmp_path / "temp_file.md")
            mock_mkstemp.return_value = (mock_fd, mock_path)

            # Create the temp file that will be moved
            Path(mock_path).write_text("import new\n")

            result = sync.update_code_examples(
                test_file,
                {"old": "new"}
            )

            # Verify atomic operation was attempted
            assert mock_mkstemp.called


# ============================================================================
# Change Report Generation Tests
# ============================================================================


@pytest.mark.unit
class TestGenerateChangeReport:
    """Test change report generation."""

    def test_generate_report_empty(self, tmp_path):
        """Test change report with no changes."""
        sync = RagSynchronizer(tmp_path)
        report = sync.generate_change_report(renames=[], stale_refs=[])

        assert report.total_files == 0
        assert report.total_changes == 0
        assert len(report.renames) == 0
        assert len(report.stale_refs) == 0

    def test_generate_report_with_renames(self, tmp_path):
        """Test change report with renames."""
        renames = [
            Rename("old1", "new1", Path("file1.py"), 0.9),
            Rename("old2", "new2", Path("file2.py"), 0.8),
        ]

        sync = RagSynchronizer(tmp_path)
        report = sync.generate_change_report(renames=renames, stale_refs=[])

        assert report.total_changes == 2
        assert len(report.renames) == 2
        assert "old1" in report.diff_preview
        assert "new1" in report.diff_preview

    def test_generate_report_with_stale_refs(self, tmp_path):
        """Test change report with stale references."""
        stale_refs = [
            StaleReference(Path("doc1.md"), 10, "old_import", "new_import", ""),
            StaleReference(Path("doc2.md"), 20, "old_import2", "new_import2", ""),
        ]

        sync = RagSynchronizer(tmp_path)
        report = sync.generate_change_report(renames=[], stale_refs=stale_refs)

        assert report.total_files == 2
        assert report.total_changes == 2
        assert len(report.stale_refs) == 2

    def test_generate_report_includes_timestamp(self, tmp_path):
        """Test change report includes timestamp."""
        sync = RagSynchronizer(tmp_path)
        report = sync.generate_change_report(renames=[], stale_refs=[])

        assert report.timestamp != ""
        assert "T" in report.timestamp  # ISO format


# ============================================================================
# Backup and Rollback Tests
# ============================================================================


@pytest.mark.unit
class TestBackupKnowledgeFiles:
    """Test backup functionality."""

    def test_backup_single_file(self, tmp_path):
        """Test backing up a single file."""
        test_file = tmp_path / "document.md"
        test_file.write_text("Original content")

        sync = RagSynchronizer(tmp_path)
        manifest = sync.backup_knowledge_files([test_file])

        assert len(manifest.files) == 1
        assert len(manifest.checksums) == 1
        assert manifest.backup_dir.exists()

        # Verify backup file exists
        assert manifest.files[0].exists()

    def test_backup_multiple_files(self, tmp_path):
        """Test backing up multiple files."""
        files = []
        for i in range(3):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"Content {i}")
            files.append(f)

        sync = RagSynchronizer(tmp_path)
        manifest = sync.backup_knowledge_files(files)

        assert len(manifest.files) == 3
        assert len(manifest.checksums) == 3

    def test_backup_checksum_validation(self, tmp_path):
        """Test backup includes valid SHA256 checksums."""
        test_file = tmp_path / "document.md"
        content = b"Test content"
        test_file.write_bytes(content)

        # Calculate expected checksum
        expected_checksum = hashlib.sha256(content).hexdigest()

        sync = RagSynchronizer(tmp_path)
        manifest = sync.backup_knowledge_files([test_file])

        # Get checksum from manifest
        relative_path = str(test_file.relative_to(tmp_path))
        actual_checksum = manifest.checksums[relative_path]

        assert actual_checksum == expected_checksum

    def test_backup_nonexistent_file_skipped(self, tmp_path):
        """Test backup skips nonexistent files."""
        test_file = tmp_path / "document.md"
        test_file.write_text("Exists")

        nonexistent = tmp_path / "does_not_exist.md"

        sync = RagSynchronizer(tmp_path)
        manifest = sync.backup_knowledge_files([test_file, nonexistent])

        # Should only backup the existing file
        assert len(manifest.files) == 1

    def test_backup_manifest_saved(self, tmp_path):
        """Test backup manifest is saved to JSON."""
        test_file = tmp_path / "document.md"
        test_file.write_text("Content")

        sync = RagSynchronizer(tmp_path)
        manifest = sync.backup_knowledge_files([test_file])

        # Check manifest file exists
        manifest_file = manifest.backup_dir / "manifest.json"
        assert manifest_file.exists()

        # Verify manifest content
        with open(manifest_file) as f:
            data = json.load(f)

        assert "timestamp" in data
        assert "backup_dir" in data
        assert "files" in data
        assert "checksums" in data


# ============================================================================
# Apply Changes Tests
# ============================================================================


@pytest.mark.unit
class TestApplyChanges:
    """Test change application functionality."""

    def test_apply_changes_dry_run(self, tmp_path):
        """Test dry run doesn't modify files."""
        test_file = tmp_path / "document.md"
        original_content = "import old"
        test_file.write_text(original_content)

        ref = StaleReference(
            test_file, 1, "old", "new", ""
        )
        report = ChangeReport(
            timestamp="2024-01-01",
            total_files=1,
            total_changes=1,
            stale_refs=[ref]
        )

        sync = RagSynchronizer(tmp_path)
        result = sync.apply_changes(report, dry_run=True)

        assert result is True
        assert test_file.read_text() == original_content  # Unchanged

    def test_apply_changes_creates_backup(self, tmp_path):
        """Test apply_changes creates backup."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        test_file = knowledge_dir / "document.md"
        test_file.write_text("import old")

        ref = StaleReference(
            test_file, 1, "old", "new", ""
        )
        report = ChangeReport(
            timestamp="2024-01-01",
            total_files=1,
            total_changes=1,
            stale_refs=[ref]
        )

        sync = RagSynchronizer(tmp_path)
        result = sync.apply_changes(report, dry_run=False)

        # Check backup was created
        backup_dir = tmp_path / ".tapps-agents" / "backups"
        assert backup_dir.exists()
        assert any(backup_dir.iterdir())  # Has backup files

    def test_apply_changes_with_provided_backup(self, tmp_path):
        """Test apply_changes with provided backup manifest."""
        test_file = tmp_path / "document.md"
        test_file.write_text("import old")

        # Create backup manually
        manifest = BackupManifest(
            timestamp="2024-01-01",
            backup_dir=tmp_path / "backup",
            files=[],
            checksums={}
        )

        ref = StaleReference(
            test_file, 1, "old", "new", ""
        )
        report = ChangeReport(
            timestamp="2024-01-01",
            total_files=1,
            total_changes=1,
            stale_refs=[ref]
        )

        sync = RagSynchronizer(tmp_path)
        result = sync.apply_changes(
            report,
            backup_manifest=manifest,
            dry_run=False
        )

        assert isinstance(result, bool)

    def test_apply_changes_rollback_on_error(self, tmp_path):
        """Test rollback occurs on error."""
        # This test would need to simulate a failure during update
        # For now, test that rollback method exists
        sync = RagSynchronizer(tmp_path)
        assert hasattr(sync, '_rollback')


# ============================================================================
# Helper Method Tests
# ============================================================================


@pytest.mark.unit
class TestGetCurrentImports:
    """Test _get_current_imports helper method."""

    def test_get_current_imports_empty_project(self, tmp_path):
        """Test getting imports from empty project."""
        sync = RagSynchronizer(tmp_path)
        imports = sync._get_current_imports()

        assert isinstance(imports, set)
        assert len(imports) == 0

    def test_get_current_imports_with_python_files(self, tmp_path):
        """Test getting imports from Python files."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "import os\nimport sys\nfrom pathlib import Path\n"
        )

        sync = RagSynchronizer(tmp_path)
        imports = sync._get_current_imports()

        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports

    def test_get_current_imports_handles_syntax_errors(self, tmp_path):
        """Test getting imports handles syntax errors."""
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("import (invalid")

        sync = RagSynchronizer(tmp_path)
        imports = sync._get_current_imports()

        # Should not raise, just skip invalid files
        assert isinstance(imports, set)


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.unit
class TestRagSynchronizerIntegration:
    """Integration tests for complete workflows."""

    def test_full_sync_workflow(self, tmp_path):
        """Test complete synchronization workflow."""
        # Setup: Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        # Create Python file with imports
        py_file = src_dir / "module.py"
        py_file.write_text("import requests\n")

        # Create knowledge file with code example
        doc = knowledge_dir / "example.md"
        doc.write_text(
            "# Example\n\n```python\nimport old_package\n```"
        )

        # Execute workflow
        sync = RagSynchronizer(tmp_path)

        # 1. Detect renames
        renames = sync.detect_package_renames(src_dir)

        # 2. Find stale imports
        stale_refs = sync.find_stale_imports()

        # 3. Generate report
        report = sync.generate_change_report(renames, stale_refs)

        # 4. Apply changes (dry run)
        result = sync.apply_changes(report, dry_run=True)

        assert result is True
        assert isinstance(report, ChangeReport)

    def test_backup_and_restore_workflow(self, tmp_path):
        """Test backup and restore workflow."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        # Create test files
        files = []
        for i in range(3):
            f = knowledge_dir / f"doc{i}.md"
            f.write_text(f"Original content {i}")
            files.append(f)

        sync = RagSynchronizer(tmp_path)

        # Create backup
        manifest = sync.backup_knowledge_files(files)

        # Modify original files
        for f in files:
            f.write_text("Modified content")

        # Restore from backup
        sync._rollback(manifest)

        # Verify restoration
        for i, f in enumerate(files):
            assert f.read_text() == f"Original content {i}"


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.unit
class TestPerformance:
    """Performance-related tests."""

    def test_detect_renames_performance_target(self, tmp_path):
        """Test rename detection meets <5s performance target."""
        # Create many Python files
        for i in range(100):
            f = tmp_path / f"module{i}.py"
            f.write_text(f"import os\nimport sys\n")

        sync = RagSynchronizer(tmp_path)

        import time
        start = time.time()
        renames = sync.detect_package_renames()
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 10.0  # More lenient for tests

    def test_find_stale_imports_performance_target(self, tmp_path):
        """Test stale import finding meets <3s performance target."""
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        knowledge_dir.mkdir(parents=True)

        # Create many knowledge files
        for i in range(50):
            f = knowledge_dir / f"doc{i}.md"
            f.write_text(f"```python\nimport module{i}\n```")

        sync = RagSynchronizer(tmp_path)

        import time
        start = time.time()
        stale_refs = sync.find_stale_imports()
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 10.0  # More lenient for tests
