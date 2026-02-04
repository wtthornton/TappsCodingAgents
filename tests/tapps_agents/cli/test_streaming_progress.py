"""
Tests for StreamingBatchProcessor - streaming_progress.py

Tests for streaming progress updates during batch operations.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from tapps_agents.cli.streaming_progress import (
    FileResult,
    ProgressUpdate,
    StreamingBatchProcessor,
    process_files_with_streaming,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_files(temp_dir):
    """Create temporary files for testing."""
    files = []
    for i in range(5):
        file_path = temp_dir / f"file_{i}.txt"
        file_path.write_text(f"Content {i}\n")
        files.append(file_path)
    return files


class TestProgressUpdate:
    """Tests for ProgressUpdate dataclass."""

    def test_init_calculates_percentage(self):
        """Test that percentage is calculated from current/total."""
        update = ProgressUpdate(current=5, total=10, percentage=0.0)
        assert update.percentage == 50.0

    def test_format_progress_bar(self):
        """Test progress bar formatting."""
        update = ProgressUpdate(current=5, total=10, percentage=50.0)
        bar = update.format_progress_bar(width=20)
        
        assert "[" in bar
        assert "]" in bar
        assert "50.0%" in bar
        assert "=" in bar
        assert "-" in bar

    def test_format_progress_bar_empty(self):
        """Test progress bar at 0%."""
        update = ProgressUpdate(current=0, total=10, percentage=0.0)
        bar = update.format_progress_bar(width=10)
        assert "----------" in bar

    def test_format_progress_bar_full(self):
        """Test progress bar at 100%."""
        update = ProgressUpdate(current=10, total=10, percentage=100.0)
        bar = update.format_progress_bar(width=10)
        assert "==========" in bar

    def test_format_status(self):
        """Test status line formatting."""
        update = ProgressUpdate(
            current=5,
            total=10,
            percentage=50.0,
            current_file="test.py",
            elapsed_seconds=5.0,
            estimated_remaining=5.0,
        )
        status = update.format_status()
        
        assert "5/10" in status
        assert "50.0%" in status
        assert "test.py" in status
        assert "5.0s" in status
        assert "5s remaining" in status


class TestFileResult:
    """Tests for FileResult dataclass."""

    def test_to_dict_success(self, temp_dir):
        """Test converting successful result to dict."""
        result = FileResult(
            file_path=temp_dir / "test.py",
            success=True,
            result={"score": 85.0},
            duration_seconds=1.5,
        )
        d = result.to_dict()
        
        assert "test.py" in d["file"]
        assert d["success"] is True
        assert d["result"]["score"] == 85.0
        assert d["error"] is None
        assert d["duration_seconds"] == 1.5

    def test_to_dict_failure(self, temp_dir):
        """Test converting failed result to dict."""
        result = FileResult(
            file_path=temp_dir / "test.py",
            success=False,
            error="Test error",
            duration_seconds=0.5,
        )
        d = result.to_dict()
        
        assert d["success"] is False
        assert d["error"] == "Test error"
        assert d["result"] is None


class TestStreamingBatchProcessor:
    """Tests for StreamingBatchProcessor class."""

    def test_init_defaults(self):
        """Test default initialization."""
        processor = StreamingBatchProcessor()
        assert processor.max_workers == 4
        assert processor.progress_interval == 0.1

    def test_init_custom(self):
        """Test custom initialization."""
        processor = StreamingBatchProcessor(max_workers=8, progress_interval=0.5)
        assert processor.max_workers == 8
        assert processor.progress_interval == 0.5

    @pytest.mark.asyncio
    async def test_process_batch_empty(self):
        """Test processing empty file list."""
        processor = StreamingBatchProcessor()
        
        async def process_fn(file: Path) -> dict:
            return {"processed": True}
        
        results = await processor.process_batch([], process_fn)
        assert results == []

    @pytest.mark.asyncio
    async def test_process_batch_success(self, temp_files):
        """Test successful batch processing."""
        processor = StreamingBatchProcessor(max_workers=2)
        
        async def process_fn(file: Path) -> dict:
            return {"file": str(file), "processed": True}
        
        results = await processor.process_batch(temp_files, process_fn)
        
        assert len(results) == 5
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_process_batch_with_failures(self, temp_files):
        """Test batch processing with some failures."""
        processor = StreamingBatchProcessor(max_workers=2)
        
        async def process_fn(file: Path) -> dict:
            if "file_2" in str(file):
                raise ValueError("Test error")
            return {"processed": True}
        
        results = await processor.process_batch(temp_files, process_fn)
        
        assert len(results) == 5
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        assert successful == 4
        assert failed == 1

    @pytest.mark.asyncio
    async def test_process_batch_with_progress_callback(self, temp_files):
        """Test batch processing with progress callback."""
        processor = StreamingBatchProcessor(max_workers=2)
        progress_updates = []
        
        async def process_fn(file: Path) -> dict:
            await asyncio.sleep(0.01)  # Small delay
            return {"processed": True}
        
        def on_progress(update: ProgressUpdate):
            progress_updates.append(update)
        
        results = await processor.process_batch(
            temp_files,
            process_fn,
            progress_callback=on_progress,
        )
        
        assert len(results) == 5
        assert len(progress_updates) > 0
        # First update should be "starting"
        assert progress_updates[0].status == "starting"
        # Last update should be "completed"
        assert progress_updates[-1].status == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_with_result_callback(self, temp_files):
        """Test batch processing with result callback."""
        processor = StreamingBatchProcessor(max_workers=2)
        streamed_results = []
        
        async def process_fn(file: Path) -> dict:
            return {"file": str(file)}
        
        def on_result(result: FileResult):
            streamed_results.append(result)
        
        results = await processor.process_batch(
            temp_files,
            process_fn,
            result_callback=on_result,
        )
        
        assert len(results) == 5
        assert len(streamed_results) == 5

    def test_aggregate_results(self, temp_files):
        """Test result aggregation."""
        processor = StreamingBatchProcessor()
        
        results = [
            FileResult(file_path=temp_files[0], success=True, result={"score": 85}),
            FileResult(file_path=temp_files[1], success=True, result={"score": 90}),
            FileResult(file_path=temp_files[2], success=False, error="Test error"),
        ]
        
        aggregated = processor.aggregate_results(results)
        
        assert aggregated["total"] == 3
        assert aggregated["successful"] == 2
        assert aggregated["failed"] == 1
        assert len(aggregated["files"]) == 3
        assert len(aggregated["errors"]) == 1


class TestConvenienceFunction:
    """Tests for process_files_with_streaming convenience function."""

    @pytest.mark.asyncio
    async def test_process_files_with_streaming(self, temp_files):
        """Test convenience function."""
        async def process_fn(file: Path) -> dict:
            return {"processed": True}
        
        result = await process_files_with_streaming(
            temp_files,
            process_fn,
            max_workers=2,
        )
        
        assert result["total"] == 5
        assert result["successful"] == 5
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_process_files_with_callbacks(self, temp_files):
        """Test convenience function with callbacks."""
        progress_count = 0
        result_count = 0
        
        async def process_fn(file: Path) -> dict:
            await asyncio.sleep(0.01)
            return {"processed": True}
        
        def on_progress(update: ProgressUpdate):
            nonlocal progress_count
            progress_count += 1
        
        def on_result(result: FileResult):
            nonlocal result_count
            result_count += 1
        
        result = await process_files_with_streaming(
            temp_files,
            process_fn,
            max_workers=2,
            progress_callback=on_progress,
            result_callback=on_result,
        )
        
        assert result["successful"] == 5
        assert progress_count > 0
        assert result_count == 5
