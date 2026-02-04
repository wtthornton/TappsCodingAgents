"""
Tests for Knowledge Base Freshness Tracking.
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tapps_agents.experts.knowledge_freshness import (
    KnowledgeFreshnessTracker,
    get_freshness_tracker,
)

pytestmark = pytest.mark.unit


class TestKnowledgeFreshnessTracker:
    """Test knowledge base freshness tracking."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        yield knowledge_dir

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def temp_metadata_file(self):
        """Create temporary metadata file."""
        temp_dir = Path(tempfile.mkdtemp())
        metadata_file = temp_dir / "knowledge_metadata.json"

        yield metadata_file

        shutil.rmtree(temp_dir)

    def test_tracker_creation(self, temp_metadata_file):
        """Test creating freshness tracker."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        assert tracker.metadata_file == temp_metadata_file
        assert len(tracker.metadata) == 0

    def test_update_file_metadata(self, temp_knowledge_dir, temp_metadata_file):
        """Test updating file metadata."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        test_file = temp_knowledge_dir / "test.md"
        test_file.write_text("# Test\nContent", encoding="utf-8")

        tracker.update_file_metadata(
            test_file,
            version="1.0.0",
            author="Test Author",
            tags=["tag1", "tag2"],
            description="Test description",
        )

        metadata = tracker.get_file_metadata(test_file)
        assert metadata is not None
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert "tag1" in metadata.tags
        assert metadata.description == "Test description"

    def test_mark_deprecated(self, temp_knowledge_dir, temp_metadata_file):
        """Test marking file as deprecated."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        test_file = temp_knowledge_dir / "old.md"
        test_file.write_text("# Old\nContent", encoding="utf-8")

        tracker.update_file_metadata(test_file)
        tracker.mark_deprecated(test_file, replacement_file=temp_knowledge_dir / "new.md")

        metadata = tracker.get_file_metadata(test_file)
        assert metadata is not None
        assert metadata.deprecated
        assert metadata.replacement_file == str(temp_knowledge_dir / "new.md")
        assert metadata.deprecation_date is not None

    def test_get_stale_files(self, temp_knowledge_dir, temp_metadata_file):
        """Test getting stale files."""
        import os
        import time

        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        # Create old file
        old_file = temp_knowledge_dir / "old.md"
        old_file.write_text("# Old\nContent", encoding="utf-8")

        # Set file mtime to 400 days ago
        old_time = time.time() - (400 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        # Update metadata with old timestamp
        old_date = datetime.now() - timedelta(days=400)
        tracker.update_file_metadata(old_file)
        if old_file in tracker.metadata:
            tracker.metadata[str(old_file)].last_updated = old_date.isoformat()

        stale_files = tracker.get_stale_files(temp_knowledge_dir, max_age_days=365)

        # Should find old file
        assert len(stale_files) > 0
        assert any(str(f) == str(old_file) for f, _ in stale_files)

    def test_get_deprecated_files(self, temp_knowledge_dir, temp_metadata_file):
        """Test getting deprecated files."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        deprecated_file = temp_knowledge_dir / "deprecated.md"
        deprecated_file.write_text("# Deprecated\nContent", encoding="utf-8")

        tracker.update_file_metadata(deprecated_file)
        tracker.mark_deprecated(deprecated_file)

        deprecated_files = tracker.get_deprecated_files(temp_knowledge_dir)

        # Should find deprecated file
        assert len(deprecated_files) > 0
        assert any(str(f) == str(deprecated_file) for f, _ in deprecated_files)

    def test_scan_and_update(self, temp_knowledge_dir, temp_metadata_file):
        """Test scanning and updating metadata."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        # Create files
        (temp_knowledge_dir / "file1.md").write_text("# File 1\nContent", encoding="utf-8")
        (temp_knowledge_dir / "file2.md").write_text("# File 2\nContent", encoding="utf-8")

        scan_results = tracker.scan_and_update(temp_knowledge_dir)

        assert scan_results["scanned"] == 2
        assert scan_results["new_files"] == 2
        assert scan_results["total_tracked"] == 2

    def test_get_summary(self, temp_knowledge_dir, temp_metadata_file):
        """Test getting freshness summary."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        # Create and track files
        (temp_knowledge_dir / "file1.md").write_text("# File 1\nContent", encoding="utf-8")
        tracker.scan_and_update(temp_knowledge_dir)

        summary = tracker.get_summary(temp_knowledge_dir)

        assert summary["total_files"] >= 1
        assert summary["tracked_files"] >= 1
        assert summary["coverage"] > 0
        assert "deprecated_files" in summary
        assert "stale_files" in summary

    def test_global_tracker(self, temp_metadata_file):
        """Test global tracker instance."""
        tracker1 = get_freshness_tracker(metadata_file=temp_metadata_file)
        tracker2 = get_freshness_tracker(metadata_file=temp_metadata_file)

        # Should return same instance when same file
        assert tracker1 is tracker2

    def test_persist_metadata(self, temp_knowledge_dir, temp_metadata_file):
        """Test metadata persistence to file."""
        tracker = KnowledgeFreshnessTracker(temp_metadata_file)

        test_file = temp_knowledge_dir / "test.md"
        test_file.write_text("# Test\nContent", encoding="utf-8")

        tracker.update_file_metadata(test_file, version="1.0.0")

        # Metadata should be persisted
        assert temp_metadata_file.exists()

        # Create new tracker and load
        tracker2 = KnowledgeFreshnessTracker(temp_metadata_file)
        metadata = tracker2.get_file_metadata(test_file)

        assert metadata is not None
        assert metadata.version == "1.0.0"
