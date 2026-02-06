"""
Comprehensive unit tests for project_cleanup_agent utility module.

Tests cover all 13 enhancements:
  #1  Targeted backup (only affected files)
  #2  Excluded directories filtering
  #3  MergeStrategy implementation
  #4  Config wiring (constructor params)
  #5  Naming exclusion list
  #6  Reference index (O(n) indexing)
  #7  Near-duplicate detection
  #8  asyncio.to_thread (modernized async)
  #9  Unique operation IDs
  #10 Log skipped actions / SKIPPED status
  #11 Progress callbacks
  #12 (This file)
  #13 CleanupOrchestrator rename + backward compat alias
"""

import asyncio
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.utils.project_cleanup_agent import (
    EXCLUDED_DIRS,
    ActionType,
    AnalysisReport,
    CleanupAction,
    CleanupAgent,
    CleanupExecutor,
    CleanupOrchestrator,
    CleanupPlan,
    CleanupPlanner,
    DeleteStrategy,
    DuplicateGroup,
    ExecutionReport,
    FileCategory,
    MergeStrategy,
    MoveStrategy,
    NamingIssue,
    NearDuplicatePair,
    OperationResult,
    OutdatedFile,
    ProjectAnalyzer,
    ReferenceUpdater,
    RenameStrategy,
    SafetyLevel,
    _is_excluded,
    _make_operation_id,
)

pytestmark = pytest.mark.unit


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory with docs structure."""
    docs = tmp_path / "docs"
    docs.mkdir()
    return tmp_path


@pytest.fixture
def populated_project(temp_project):
    """Project with several files for analysis."""
    docs = temp_project / "docs"
    (docs / "readme.md").write_text("# Readme\nMain documentation", encoding="utf-8")
    (docs / "guide.md").write_text("# Guide\nSome guide content", encoding="utf-8")
    (docs / "duplicate1.md").write_text("# Identical\nSame content exactly", encoding="utf-8")
    (docs / "duplicate2.md").write_text("# Identical\nSame content exactly", encoding="utf-8")
    (docs / "MixedCase.md").write_text("# Mixed\nMixed case file", encoding="utf-8")
    (docs / "snake_case.md").write_text("# Snake\nSnake case file", encoding="utf-8")
    return temp_project


@pytest.fixture
def analyzer(temp_project):
    """ProjectAnalyzer for temp project."""
    return ProjectAnalyzer(temp_project)


@pytest.fixture
def populated_analyzer(populated_project):
    """ProjectAnalyzer for populated project."""
    return ProjectAnalyzer(populated_project)


# =============================================================================
# Enhancement #2: EXCLUDED_DIRS and _is_excluded()
# =============================================================================


class TestExcludedDirs:
    """Tests for excluded directories filtering."""

    def test_excluded_dirs_is_frozenset(self):
        assert isinstance(EXCLUDED_DIRS, frozenset)

    def test_excluded_dirs_contains_common_dirs(self):
        for d in [".git", "node_modules", ".venv", "__pycache__", ".tapps-agents"]:
            assert d in EXCLUDED_DIRS

    def test_is_excluded_matches_git(self):
        assert _is_excluded(Path("project/.git/config"))

    def test_is_excluded_matches_node_modules(self):
        assert _is_excluded(Path("project/node_modules/pkg/index.js"))

    def test_is_excluded_matches_pycache(self):
        assert _is_excluded(Path("src/__pycache__/mod.pyc"))

    def test_is_excluded_does_not_match_normal(self):
        assert not _is_excluded(Path("src/main.py"))

    def test_is_excluded_does_not_match_docs(self):
        assert not _is_excluded(Path("docs/guide.md"))


# =============================================================================
# Enhancement #9: Unique operation IDs
# =============================================================================


class TestMakeOperationId:
    """Tests for _make_operation_id."""

    def test_includes_prefix(self):
        op_id = _make_operation_id("del")
        assert op_id.startswith("del-")

    def test_unique_ids(self):
        ids = {_make_operation_id("test") for _ in range(100)}
        assert len(ids) == 100

    def test_format(self):
        op_id = _make_operation_id("mrg")
        prefix, suffix = op_id.split("-", 1)
        assert prefix == "mrg"
        assert len(suffix) == 8  # uuid4 hex[:8]


# =============================================================================
# Data Model Tests
# =============================================================================


class TestNearDuplicatePair:
    """Tests for NearDuplicatePair model."""

    def test_valid_pair(self, tmp_path):
        pair = NearDuplicatePair(
            file1=tmp_path / "a.md",
            file2=tmp_path / "b.md",
            similarity=0.85,
        )
        assert pair.similarity == 0.85

    def test_similarity_bounds(self):
        with pytest.raises(Exception):
            NearDuplicatePair(file1=Path("a"), file2=Path("b"), similarity=1.5)
        with pytest.raises(Exception):
            NearDuplicatePair(file1=Path("a"), file2=Path("b"), similarity=-0.1)


class TestExecutionReportMergedField:
    """Test that ExecutionReport includes files_merged."""

    def test_files_merged_default(self):
        report = ExecutionReport(
            operations=[],
            files_modified=0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )
        assert report.files_merged == 0

    def test_files_merged_set(self):
        report = ExecutionReport(
            operations=[],
            files_modified=3,
            files_merged=2,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )
        assert report.files_merged == 2

    def test_to_markdown_includes_merged(self):
        report = ExecutionReport(
            operations=[],
            files_modified=1,
            files_merged=1,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )
        md = report.to_markdown()
        assert "Merged" in md


class TestOperationResultSkipped:
    """Test SKIPPED status on OperationResult."""

    def test_skipped_status_valid(self):
        result = OperationResult(
            operation_id="skip-abc",
            action_type=ActionType.DELETE,
            source_files=[Path("a.md")],
            status="SKIPPED",
            error_message="No strategy",
        )
        assert result.status == "SKIPPED"
        assert not result.succeeded


# =============================================================================
# Enhancement #4: Config wiring (ProjectAnalyzer)
# =============================================================================


class TestProjectAnalyzerConfig:
    """Tests for ProjectAnalyzer config wiring."""

    def test_default_age_threshold(self, temp_project):
        analyzer = ProjectAnalyzer(temp_project)
        assert analyzer.age_threshold_days == 90

    def test_custom_age_threshold(self, temp_project):
        analyzer = ProjectAnalyzer(temp_project, age_threshold_days=30)
        assert analyzer.age_threshold_days == 30

    def test_default_exclude_names(self, temp_project):
        analyzer = ProjectAnalyzer(temp_project)
        assert analyzer.exclude_names == set()

    def test_custom_exclude_names(self, temp_project):
        analyzer = ProjectAnalyzer(temp_project, exclude_names=["README.md", "LICENSE"])
        assert analyzer.exclude_names == {"README.md", "LICENSE"}


# =============================================================================
# Enhancement #5: Naming exclusion list
# =============================================================================


class TestNamingExclusionList:
    """Tests for naming exclusion list in analyze_naming_patterns."""

    def test_excluded_names_skipped(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        readme = docs / "README.md"
        readme.write_text("# README", encoding="utf-8")

        analyzer = ProjectAnalyzer(temp_project, exclude_names=["README.md"])
        issues = analyzer.analyze_naming_patterns([readme])
        assert len(issues) == 0

    def test_non_excluded_names_flagged(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        mixed = docs / "MixedCase.md"
        mixed.write_text("# Mixed", encoding="utf-8")

        analyzer = ProjectAnalyzer(temp_project, exclude_names=["README.md"])
        issues = analyzer.analyze_naming_patterns([mixed])
        assert len(issues) == 1
        assert issues[0].pattern_violation == "MixedCase"

    def test_multiple_excluded_names(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        files = []
        for name in ["README.md", "CHANGELOG.md", "AGENTS.md", "normal.md"]:
            f = docs / name
            f.write_text(f"# {name}", encoding="utf-8")
            files.append(f)

        analyzer = ProjectAnalyzer(
            temp_project,
            exclude_names=["README.md", "CHANGELOG.md", "AGENTS.md"],
        )
        issues = analyzer.analyze_naming_patterns(files)
        # Only "normal.md" remains — it's already kebab-case, so 0 issues
        assert len(issues) == 0


# =============================================================================
# Enhancement #6: Reference index
# =============================================================================


class TestReferenceIndex:
    """Tests for _build_reference_index and _count_references_indexed."""

    def test_build_reference_index_basic(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        a = docs / "a.md"
        b = docs / "b.md"
        a.write_text("See b.md for details", encoding="utf-8")
        b.write_text("Main content", encoding="utf-8")

        analyzer = ProjectAnalyzer(temp_project)
        index = analyzer._build_reference_index([a, b])

        # a.md references b.md, so b.md's name should have a referring file
        assert a in index.get("b.md", set())

    def test_count_references_indexed(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        a = docs / "a.md"
        b = docs / "b.md"
        c = docs / "c.md"
        a.write_text("See b.md for details", encoding="utf-8")
        b.write_text("Main content", encoding="utf-8")
        c.write_text("Also see b.md", encoding="utf-8")

        analyzer = ProjectAnalyzer(temp_project)
        count = analyzer._count_references_indexed(b, [a, b, c])
        assert count == 2

    def test_no_self_references(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        a = docs / "a.md"
        a.write_text("This is a.md itself", encoding="utf-8")

        analyzer = ProjectAnalyzer(temp_project)
        count = analyzer._count_references_indexed(a, [a])
        assert count == 0

    def test_index_lazy_initialized(self, temp_project):
        analyzer = ProjectAnalyzer(temp_project)
        assert analyzer._reference_index is None


# =============================================================================
# Enhancement #8: asyncio.to_thread (scan_directory_structure)
# =============================================================================


class TestAsyncScanning:
    """Tests for async scanning with asyncio.to_thread."""

    @pytest.mark.asyncio
    async def test_scan_directory_finds_files(self, populated_project):
        analyzer = ProjectAnalyzer(populated_project)
        docs = populated_project / "docs"
        files = await analyzer.scan_directory_structure(docs, "*.md")
        assert len(files) >= 4  # readme, guide, duplicate1, duplicate2, MixedCase, snake_case

    @pytest.mark.asyncio
    async def test_scan_empty_directory(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        analyzer = ProjectAnalyzer(temp_project)
        files = await analyzer.scan_directory_structure(docs, "*.md")
        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_scan_respects_pattern(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "test.md").write_text("md", encoding="utf-8")
        (docs / "test.txt").write_text("txt", encoding="utf-8")

        analyzer = ProjectAnalyzer(temp_project)
        md_files = await analyzer.scan_directory_structure(docs, "*.md")
        assert len(md_files) == 1
        assert md_files[0].name == "test.md"


# =============================================================================
# Enhancement #11: Progress callbacks
# =============================================================================


class TestProgressCallbacks:
    """Tests for progress callback support."""

    @pytest.mark.asyncio
    async def test_analysis_progress_callback(self, populated_project):
        progress_calls = []

        def on_progress(step: str, current: int, total: int):
            progress_calls.append((step, current, total))

        analyzer = ProjectAnalyzer(populated_project)
        docs = populated_project / "docs"
        await analyzer.generate_analysis_report(docs, "*.md", progress_callback=on_progress)

        assert len(progress_calls) == 4
        steps = [c[0] for c in progress_calls]
        assert "Scanning files" in steps
        assert "Detecting duplicates" in steps
        assert "Analyzing naming patterns" in steps
        assert "Detecting outdated files" in steps

    @pytest.mark.asyncio
    async def test_analysis_no_callback(self, populated_project):
        """Ensure no errors when callback is None."""
        analyzer = ProjectAnalyzer(populated_project)
        docs = populated_project / "docs"
        report = await analyzer.generate_analysis_report(docs, "*.md", progress_callback=None)
        assert report.total_files >= 1

    @pytest.mark.asyncio
    async def test_executor_progress_callback(self, temp_project):
        progress_calls = []

        def on_progress(step: str, current: int, total: int):
            progress_calls.append((step, current, total))

        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        f = docs / "test.md"
        f.write_text("content", encoding="utf-8")

        plan = CleanupPlan(
            actions=[
                CleanupAction(
                    action_type=ActionType.DELETE,
                    source_files=[f],
                    rationale="Test deletion for progress callback",
                    priority=1,
                    safety_level=SafetyLevel.SAFE,
                ),
            ],
            estimated_savings=0,
            estimated_file_reduction=0.0,
        )

        executor = CleanupExecutor(temp_project)
        await executor.execute_plan(plan, dry_run=True, create_backup=False, progress_callback=on_progress)

        assert len(progress_calls) == 1
        assert "delete" in progress_calls[0][0].lower()


# =============================================================================
# Enhancement #3: MergeStrategy
# =============================================================================


class TestMergeStrategy:
    """Tests for the MergeStrategy implementation."""

    @pytest.mark.asyncio
    async def test_merge_combines_content(self, tmp_path):
        f1 = tmp_path / "part1.md"
        f2 = tmp_path / "part2.md"
        f1.write_text("# Part 1\nContent A", encoding="utf-8")
        f2.write_text("# Part 2\nContent B", encoding="utf-8")

        action = CleanupAction(
            action_type=ActionType.MERGE,
            source_files=[f1, f2],
            target_path=f1,
            rationale="Merge near-duplicates into one file",
            priority=1,
            safety_level=SafetyLevel.RISKY,
        )

        strategy = MergeStrategy()
        result = await strategy.execute(action, dry_run=False)

        assert result.succeeded
        merged = f1.read_text(encoding="utf-8")
        assert "Part 1" in merged
        assert "Part 2" in merged
        assert not f2.exists()  # Secondary file deleted

    @pytest.mark.asyncio
    async def test_merge_dry_run(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("A", encoding="utf-8")
        f2.write_text("B", encoding="utf-8")

        action = CleanupAction(
            action_type=ActionType.MERGE,
            source_files=[f1, f2],
            target_path=f1,
            rationale="Dry run merge test for near-duplicates",
            priority=1,
            safety_level=SafetyLevel.RISKY,
        )

        strategy = MergeStrategy()
        result = await strategy.execute(action, dry_run=True)

        assert result.succeeded
        # Files should be unchanged
        assert f1.read_text(encoding="utf-8") == "A"
        assert f2.exists()

    @pytest.mark.asyncio
    async def test_merge_operation_id_prefix(self, tmp_path):
        f1 = tmp_path / "x.md"
        f1.write_text("x", encoding="utf-8")

        action = CleanupAction(
            action_type=ActionType.MERGE,
            source_files=[f1],
            target_path=f1,
            rationale="Test merge operation ID prefix",
            priority=1,
            safety_level=SafetyLevel.RISKY,
        )

        strategy = MergeStrategy()
        result = await strategy.execute(action, dry_run=True)
        assert result.operation_id.startswith("mrg-")

    @pytest.mark.asyncio
    async def test_merge_error_handling(self, tmp_path):
        """Merge with a non-existent source should handle gracefully."""
        f1 = tmp_path / "exists.md"
        f1.write_text("content", encoding="utf-8")
        f2 = tmp_path / "missing.md"  # Does not exist

        action = CleanupAction(
            action_type=ActionType.MERGE,
            source_files=[f1, f2],
            target_path=f1,
            rationale="Test merge with missing source file",
            priority=1,
            safety_level=SafetyLevel.RISKY,
        )

        strategy = MergeStrategy()
        result = await strategy.execute(action, dry_run=False)
        # Should succeed (only reads existing files)
        assert result.succeeded


# =============================================================================
# Enhancement #1: Targeted backup
# =============================================================================


class TestTargetedBackup:
    """Tests for targeted backup (only plan-affected files)."""

    def test_backup_only_affected_files(self, temp_project):
        docs = temp_project / "docs"
        docs.mkdir(exist_ok=True)
        f1 = docs / "target.md"
        f2 = docs / "unaffected.md"
        f1.write_text("will be backed up", encoding="utf-8")
        f2.write_text("should NOT be in backup", encoding="utf-8")

        plan = CleanupPlan(
            actions=[
                CleanupAction(
                    action_type=ActionType.DELETE,
                    source_files=[f1],
                    rationale="Delete target file for targeted backup test",
                    priority=1,
                    safety_level=SafetyLevel.SAFE,
                ),
            ],
            estimated_savings=100,
            estimated_file_reduction=50.0,
        )

        executor = CleanupExecutor(temp_project)
        backup_path = executor.create_backup(plan)

        assert backup_path.exists()
        with zipfile.ZipFile(backup_path, "r") as zf:
            names = zf.namelist()
            # target.md should be in backup
            assert any("target.md" in n for n in names)
            # unaffected.md should NOT be in backup
            assert not any("unaffected.md" in n for n in names)

    def test_backup_empty_plan(self, temp_project):
        plan = CleanupPlan(
            actions=[],
            estimated_savings=0,
            estimated_file_reduction=0.0,
        )

        executor = CleanupExecutor(temp_project)
        backup_path = executor.create_backup(plan)

        assert backup_path.exists()
        with zipfile.ZipFile(backup_path, "r") as zf:
            assert len(zf.namelist()) == 0

    def test_backup_none_plan(self, temp_project):
        executor = CleanupExecutor(temp_project)
        backup_path = executor.create_backup(None)

        assert backup_path.exists()
        with zipfile.ZipFile(backup_path, "r") as zf:
            assert len(zf.namelist()) == 0

    def test_backup_dir_configurable(self, temp_project):
        custom_dir = ".custom-backups"
        executor = CleanupExecutor(temp_project, backup_dir=custom_dir)
        assert (temp_project / custom_dir).exists()

    def test_backup_default_dir(self, temp_project):
        executor = CleanupExecutor(temp_project)
        assert (temp_project / ".tapps-agents" / "cleanup-backups").exists()

    def test_backup_skips_excluded_dirs(self, temp_project):
        """Files in excluded directories should not be backed up."""
        git_dir = temp_project / ".git"
        git_dir.mkdir(exist_ok=True)
        git_file = git_dir / "config"
        git_file.write_text("git config", encoding="utf-8")

        plan = CleanupPlan(
            actions=[
                CleanupAction(
                    action_type=ActionType.DELETE,
                    source_files=[git_file],
                    rationale="Test that excluded dir files are skipped in backup",
                    priority=1,
                    safety_level=SafetyLevel.SAFE,
                ),
            ],
            estimated_savings=0,
            estimated_file_reduction=0.0,
        )

        executor = CleanupExecutor(temp_project)
        backup_path = executor.create_backup(plan)

        with zipfile.ZipFile(backup_path, "r") as zf:
            assert len(zf.namelist()) == 0


# =============================================================================
# Enhancement #10: Skipped actions logging
# =============================================================================


class TestSkippedActions:
    """Tests for logging and SKIPPED status on missing strategies."""

    @pytest.mark.asyncio
    async def test_missing_strategy_produces_skipped(self, temp_project):
        executor = CleanupExecutor(temp_project)
        # Remove the DELETE strategy to simulate missing strategy
        del executor.strategies[ActionType.DELETE]

        plan = CleanupPlan(
            actions=[
                CleanupAction(
                    action_type=ActionType.DELETE,
                    source_files=[temp_project / "nonexistent.md"],
                    rationale="Test that missing strategy produces SKIPPED result",
                    priority=1,
                    safety_level=SafetyLevel.SAFE,
                ),
            ],
            estimated_savings=0,
            estimated_file_reduction=0.0,
        )

        report = await executor.execute_plan(plan, dry_run=True, create_backup=False)
        assert len(report.operations) == 1
        assert report.operations[0].status == "SKIPPED"
        assert "No strategy" in report.operations[0].error_message


# =============================================================================
# Strategy Tests (Delete, Rename, Move)
# =============================================================================


class TestDeleteStrategy:
    """Tests for DeleteStrategy."""

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, tmp_path):
        f = tmp_path / "delete_me.md"
        f.write_text("content", encoding="utf-8")

        action = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[f],
            rationale="Test delete strategy removes file",
            priority=1,
            safety_level=SafetyLevel.SAFE,
        )

        result = await DeleteStrategy().execute(action, dry_run=False)
        assert result.succeeded
        assert not f.exists()

    @pytest.mark.asyncio
    async def test_delete_dry_run(self, tmp_path):
        f = tmp_path / "keep_me.md"
        f.write_text("content", encoding="utf-8")

        action = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[f],
            rationale="Test delete dry run preserves file",
            priority=1,
            safety_level=SafetyLevel.SAFE,
        )

        result = await DeleteStrategy().execute(action, dry_run=True)
        assert result.succeeded
        assert f.exists()

    @pytest.mark.asyncio
    async def test_delete_operation_id(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("x", encoding="utf-8")
        action = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[f],
            rationale="Test delete operation ID prefix",
            priority=1,
            safety_level=SafetyLevel.SAFE,
        )
        result = await DeleteStrategy().execute(action, dry_run=True)
        assert result.operation_id.startswith("del-")


class TestRenameStrategy:
    """Tests for RenameStrategy."""

    @pytest.mark.asyncio
    async def test_rename_file(self, tmp_path):
        f = tmp_path / "OldName.md"
        f.write_text("content", encoding="utf-8")
        new_path = tmp_path / "new-name.md"

        action = CleanupAction(
            action_type=ActionType.RENAME,
            source_files=[f],
            target_path=new_path,
            rationale="Test rename strategy renames file",
            priority=2,
            safety_level=SafetyLevel.MODERATE,
        )

        strategy = RenameStrategy(project_root=tmp_path)
        result = await strategy.execute(action, dry_run=False)
        assert result.succeeded
        assert new_path.exists()
        assert not f.exists()

    @pytest.mark.asyncio
    async def test_rename_dry_run(self, tmp_path):
        f = tmp_path / "Original.md"
        f.write_text("content", encoding="utf-8")
        new_path = tmp_path / "renamed.md"

        action = CleanupAction(
            action_type=ActionType.RENAME,
            source_files=[f],
            target_path=new_path,
            rationale="Test rename dry run preserves file",
            priority=2,
            safety_level=SafetyLevel.MODERATE,
        )

        strategy = RenameStrategy(project_root=tmp_path)
        result = await strategy.execute(action, dry_run=True)
        assert result.succeeded
        assert f.exists()
        assert not new_path.exists()

    @pytest.mark.asyncio
    async def test_rename_operation_id(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("x", encoding="utf-8")
        action = CleanupAction(
            action_type=ActionType.RENAME,
            source_files=[f],
            target_path=tmp_path / "new.md",
            rationale="Test rename operation ID prefix",
            priority=2,
            safety_level=SafetyLevel.MODERATE,
        )
        result = await RenameStrategy(project_root=tmp_path).execute(action, dry_run=True)
        assert result.operation_id.startswith("ren-")


class TestMoveStrategy:
    """Tests for MoveStrategy."""

    @pytest.mark.asyncio
    async def test_move_file(self, tmp_path):
        src = tmp_path / "source.md"
        src.write_text("content", encoding="utf-8")
        target_dir = tmp_path / "archive"
        target = target_dir / "source.md"

        action = CleanupAction(
            action_type=ActionType.MOVE,
            source_files=[src],
            target_path=target,
            rationale="Test move strategy moves file to archive",
            priority=1,
            safety_level=SafetyLevel.MODERATE,
        )

        strategy = MoveStrategy(project_root=tmp_path)
        result = await strategy.execute(action, dry_run=False)
        assert result.succeeded
        assert target.exists()
        assert not src.exists()

    @pytest.mark.asyncio
    async def test_move_creates_parent_dirs(self, tmp_path):
        src = tmp_path / "file.md"
        src.write_text("content", encoding="utf-8")
        target = tmp_path / "deep" / "nested" / "dir" / "file.md"

        action = CleanupAction(
            action_type=ActionType.MOVE,
            source_files=[src],
            target_path=target,
            rationale="Test move creates parent directories",
            priority=1,
            safety_level=SafetyLevel.MODERATE,
        )

        strategy = MoveStrategy(project_root=tmp_path)
        result = await strategy.execute(action, dry_run=False)
        assert result.succeeded
        assert target.exists()

    @pytest.mark.asyncio
    async def test_move_operation_id(self, tmp_path):
        src = tmp_path / "test.md"
        src.write_text("x", encoding="utf-8")
        action = CleanupAction(
            action_type=ActionType.MOVE,
            source_files=[src],
            target_path=tmp_path / "moved.md",
            rationale="Test move operation ID prefix format",
            priority=1,
            safety_level=SafetyLevel.MODERATE,
        )
        result = await MoveStrategy(project_root=tmp_path).execute(action, dry_run=True)
        assert result.operation_id.startswith("mov-")


# =============================================================================
# ReferenceUpdater tests
# =============================================================================


class TestReferenceUpdater:
    """Tests for ReferenceUpdater cross-reference scanning."""

    def test_updates_markdown_links(self, tmp_path):
        target = tmp_path / "old-name.md"
        target.write_text("content", encoding="utf-8")
        referring = tmp_path / "index.md"
        referring.write_text("See [details](old-name.md) for more", encoding="utf-8")

        updater = ReferenceUpdater(tmp_path)
        count = updater.scan_and_update_references(
            Path("old-name.md"),
            Path("new-name.md"),
            dry_run=False,
        )

        updated_content = referring.read_text(encoding="utf-8")
        assert "new-name.md" in updated_content
        assert count == 1

    def test_dry_run_does_not_modify(self, tmp_path):
        target = tmp_path / "old.md"
        target.write_text("content", encoding="utf-8")
        referring = tmp_path / "ref.md"
        referring.write_text("[link](old.md)", encoding="utf-8")

        updater = ReferenceUpdater(tmp_path)
        count = updater.scan_and_update_references(
            Path("old.md"),
            Path("new.md"),
            dry_run=True,
        )

        assert count == 1
        assert "old.md" in referring.read_text(encoding="utf-8")

    def test_skips_excluded_directories(self, tmp_path):
        """Reference updater should skip EXCLUDED_DIRS."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        git_file = git_dir / "description"
        git_file.write_text("See old.md", encoding="utf-8")

        updater = ReferenceUpdater(tmp_path)
        count = updater.scan_and_update_references(
            Path("old.md"),
            Path("new.md"),
            dry_run=False,
        )

        # .git should be skipped
        assert count == 0
        assert "old.md" in git_file.read_text(encoding="utf-8")


# =============================================================================
# Enhancement #7: Near-duplicate detection
# =============================================================================


class TestNearDuplicateDetection:
    """Tests for near-duplicate detection in CleanupPlanner."""

    def test_detects_similar_files(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("# Title\n\nThis is some shared content that is almost the same", encoding="utf-8")
        f2.write_text("# Title\n\nThis is some shared content that is nearly the same", encoding="utf-8")

        report = AnalysisReport(
            total_files=2,
            total_size=200,
            duplicates=[],
            scan_path=tmp_path,
        )

        planner = CleanupPlanner(report, similarity_threshold=0.7)
        pairs = planner.detect_near_duplicates([f1, f2])

        assert len(pairs) >= 1
        assert pairs[0].similarity >= 0.7

    def test_skips_exact_duplicates(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        content = "Identical content"
        f1.write_text(content, encoding="utf-8")
        f2.write_text(content, encoding="utf-8")

        report = AnalysisReport(
            total_files=2,
            total_size=200,
            duplicates=[],
            scan_path=tmp_path,
        )

        planner = CleanupPlanner(report, similarity_threshold=0.8)
        pairs = planner.detect_near_duplicates([f1, f2])

        # similarity == 1.0 is filtered out (exact duplicates handled separately)
        assert all(p.similarity < 1.0 for p in pairs)

    def test_skips_when_too_many_files(self, tmp_path):
        """Should skip when more than 200 candidate files."""
        report = AnalysisReport(
            total_files=300,
            total_size=30000,
            duplicates=[],
            scan_path=tmp_path,
        )

        # Create 201 tiny files
        files = []
        for i in range(201):
            f = tmp_path / f"file{i}.md"
            f.write_text(f"content {i}", encoding="utf-8")
            files.append(f)

        planner = CleanupPlanner(report, similarity_threshold=0.8)
        pairs = planner.detect_near_duplicates(files)
        assert len(pairs) == 0

    def test_plan_includes_merge_actions_for_near_duplicates(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("shared content A", encoding="utf-8")
        f2.write_text("shared content B", encoding="utf-8")

        report = AnalysisReport(
            total_files=2,
            total_size=200,
            duplicates=[],
            near_duplicates=[
                NearDuplicatePair(file1=f1, file2=f2, similarity=0.85),
            ],
            scan_path=tmp_path,
        )

        planner = CleanupPlanner(report, similarity_threshold=0.8)
        plan = planner.generate_cleanup_plan()

        merge_actions = [a for a in plan.actions if a.action_type == ActionType.MERGE]
        assert len(merge_actions) == 1
        assert merge_actions[0].target_path == f1


# =============================================================================
# CleanupPlanner categorize_files and prioritize_actions
# =============================================================================


class TestCleanupPlanner:
    """Tests for CleanupPlanner categorization and prioritization."""

    def test_categorize_duplicates(self, tmp_path):
        f1 = tmp_path / "keep.md"
        f2 = tmp_path / "delete.md"
        f1.write_text("x", encoding="utf-8")
        f2.write_text("x", encoding="utf-8")

        report = AnalysisReport(
            total_files=2,
            total_size=2,
            duplicates=[
                DuplicateGroup(
                    hash="a" * 64,
                    files=[f1, f2],
                    size=1,
                    recommendation="Keep keep.md",
                ),
            ],
            scan_path=tmp_path,
        )

        planner = CleanupPlanner(report)
        categories = planner.categorize_files()
        assert f1 in categories[FileCategory.KEEP]
        assert f2 in categories[FileCategory.DELETE]

    def test_categorize_naming_issues(self, tmp_path):
        f = tmp_path / "BadName.md"
        f.write_text("x", encoding="utf-8")

        report = AnalysisReport(
            total_files=1,
            total_size=1,
            naming_issues=[
                NamingIssue(
                    path=f,
                    current_name="BadName.md",
                    suggested_name="bad-name.md",
                    pattern_violation="MixedCase",
                ),
            ],
            scan_path=tmp_path,
        )

        planner = CleanupPlanner(report)
        categories = planner.categorize_files()
        assert f in categories[FileCategory.RENAME]

    def test_categorize_near_duplicates_as_merge(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"

        report = AnalysisReport(
            total_files=2,
            total_size=200,
            near_duplicates=[
                NearDuplicatePair(file1=f1, file2=f2, similarity=0.9),
            ],
            scan_path=tmp_path,
        )

        planner = CleanupPlanner(report)
        categories = planner.categorize_files()
        assert f2 in categories[FileCategory.MERGE]

    def test_prioritize_high_first(self):
        a1 = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[Path("a")],
            rationale="Low priority safe deletion action",
            priority=1,
            safety_level=SafetyLevel.SAFE,
        )
        a2 = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[Path("b")],
            rationale="High priority safe deletion action",
            priority=3,
            safety_level=SafetyLevel.SAFE,
        )

        report = AnalysisReport(total_files=0, total_size=0, scan_path=Path("."))
        planner = CleanupPlanner(report)
        result = planner.prioritize_actions([a1, a2])
        assert result[0].priority == 3

    def test_prioritize_safe_before_risky(self):
        a1 = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[Path("a")],
            rationale="Same priority risky deletion action",
            priority=2,
            safety_level=SafetyLevel.RISKY,
        )
        a2 = CleanupAction(
            action_type=ActionType.DELETE,
            source_files=[Path("b")],
            rationale="Same priority safe deletion action",
            priority=2,
            safety_level=SafetyLevel.SAFE,
        )

        report = AnalysisReport(total_files=0, total_size=0, scan_path=Path("."))
        planner = CleanupPlanner(report)
        result = planner.prioritize_actions([a1, a2])
        assert result[0].safety_level == SafetyLevel.SAFE


# =============================================================================
# Enhancement #13: CleanupOrchestrator rename + backward compat
# =============================================================================


class TestCleanupOrchestratorRename:
    """Tests for CleanupOrchestrator rename and backward compat alias."""

    def test_cleanup_agent_is_alias(self):
        assert CleanupAgent is CleanupOrchestrator

    def test_orchestrator_init(self, temp_project):
        orch = CleanupOrchestrator(temp_project)
        assert orch.project_root == temp_project

    def test_orchestrator_config_params(self, temp_project):
        orch = CleanupOrchestrator(
            temp_project,
            backup_dir=".custom-backups",
            age_threshold_days=60,
            similarity_threshold=0.9,
            exclude_names=["README.md"],
        )
        assert orch.analyzer.age_threshold_days == 60
        assert orch.analyzer.exclude_names == {"README.md"}
        assert orch.similarity_threshold == 0.9

    @pytest.mark.asyncio
    async def test_orchestrator_run_analysis(self, populated_project):
        docs = populated_project / "docs"
        orch = CleanupOrchestrator(populated_project)
        report = await orch.run_analysis(docs, "*.md")
        assert report.total_files >= 1

    def test_orchestrator_run_planning(self, populated_project):
        report = AnalysisReport(
            total_files=1,
            total_size=100,
            scan_path=populated_project / "docs",
        )
        orch = CleanupOrchestrator(populated_project)
        plan = orch.run_planning(report)
        assert isinstance(plan, CleanupPlan)

    @pytest.mark.asyncio
    async def test_orchestrator_full_cleanup(self, populated_project):
        docs = populated_project / "docs"
        orch = CleanupOrchestrator(populated_project)
        analysis, plan, execution = await orch.run_full_cleanup(
            docs, "*.md", dry_run=True, create_backup=False,
        )
        assert isinstance(analysis, AnalysisReport)
        assert isinstance(plan, CleanupPlan)
        assert isinstance(execution, ExecutionReport)
        assert execution.dry_run is True


# =============================================================================
# Integration: executor registers MergeStrategy
# =============================================================================


class TestExecutorStrategyRegistration:
    """Test that CleanupExecutor registers all strategies including MERGE."""

    def test_all_strategies_registered(self, temp_project):
        executor = CleanupExecutor(temp_project)
        assert ActionType.DELETE in executor.strategies
        assert ActionType.RENAME in executor.strategies
        assert ActionType.MOVE in executor.strategies
        assert ActionType.MERGE in executor.strategies
        assert isinstance(executor.strategies[ActionType.MERGE], MergeStrategy)

    @pytest.mark.asyncio
    async def test_execute_plan_counts_merged(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("content A", encoding="utf-8")
        f2.write_text("content B", encoding="utf-8")

        plan = CleanupPlan(
            actions=[
                CleanupAction(
                    action_type=ActionType.MERGE,
                    source_files=[f1, f2],
                    target_path=f1,
                    rationale="Merge two files for count verification",
                    priority=1,
                    safety_level=SafetyLevel.RISKY,
                ),
            ],
            estimated_savings=100,
            estimated_file_reduction=50.0,
        )

        executor = CleanupExecutor(tmp_path)
        report = await executor.execute_plan(plan, dry_run=False, create_backup=False)
        assert report.files_merged == 1
        assert report.files_modified == 1


# =============================================================================
# Duplicate detection
# =============================================================================


class TestDuplicateDetection:
    """Tests for duplicate file detection."""

    @pytest.mark.asyncio
    async def test_detect_duplicates(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f3 = tmp_path / "c.md"
        content = "identical content for duplicate detection"
        f1.write_text(content, encoding="utf-8")
        f2.write_text(content, encoding="utf-8")
        f3.write_text("different content", encoding="utf-8")

        analyzer = ProjectAnalyzer(tmp_path)
        groups = await analyzer.detect_duplicates([f1, f2, f3])

        assert len(groups) == 1
        assert len(groups[0].files) == 2
        assert groups[0].savings > 0

    @pytest.mark.asyncio
    async def test_no_duplicates(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("unique content 1", encoding="utf-8")
        f2.write_text("unique content 2", encoding="utf-8")

        analyzer = ProjectAnalyzer(tmp_path)
        groups = await analyzer.detect_duplicates([f1, f2])
        assert len(groups) == 0
