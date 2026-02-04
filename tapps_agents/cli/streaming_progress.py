"""
Streaming Progress - Incremental progress updates for batch operations.

2025 Performance Pattern: Stream results as they're computed, not after completion.
Provides better UX and prevents Cursor timeouts during long-running batch operations.

References:
- docs/PERFORMANCE_OPTIMIZATION_RECOMMENDATIONS_2025.md
- docs/PERFORMANCE_PATTERNS_QUICK_REFERENCE.md
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ProgressUpdate:
    """
    Progress update for streaming operations.
    
    Attributes:
        current: Current item number
        total: Total number of items
        percentage: Completion percentage (0-100)
        current_file: Path of current file being processed
        status: Status string (e.g., "processing", "completed", "failed")
        result: Result data (if completed)
        error: Error message (if failed)
        elapsed_seconds: Elapsed time in seconds
        estimated_remaining: Estimated remaining time in seconds
    """
    current: int
    total: int
    percentage: float
    current_file: str = ""
    status: str = "processing"
    result: dict[str, Any] | None = None
    error: str | None = None
    elapsed_seconds: float = 0.0
    estimated_remaining: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate percentage if not provided."""
        if self.total > 0 and self.percentage == 0.0:
            self.percentage = (self.current / self.total) * 100
    
    def format_progress_bar(self, width: int = 30) -> str:
        """
        Format progress as a text progress bar.
        
        Args:
            width: Width of the progress bar
            
        Returns:
            Formatted progress bar string
        """
        filled = int(self.percentage / 100 * width)
        bar = "=" * filled + "-" * (width - filled)
        return f"[{bar}] {self.percentage:.1f}%"
    
    def format_status(self) -> str:
        """
        Format status line for display.
        
        Returns:
            Formatted status string
        """
        parts = [
            f"{self.current}/{self.total}",
            f"({self.percentage:.1f}%)",
        ]
        
        if self.current_file:
            parts.append(f"- {self.current_file}")
        
        if self.elapsed_seconds > 0:
            parts.append(f"[{self.elapsed_seconds:.1f}s]")
        
        if self.estimated_remaining is not None:
            parts.append(f"~{self.estimated_remaining:.0f}s remaining")
        
        return " ".join(parts)


@dataclass
class FileResult:
    """
    Result for a single file in batch processing.
    
    Attributes:
        file_path: Path to the processed file
        success: Whether processing succeeded
        result: Result data (if successful)
        error: Error message (if failed)
        duration_seconds: Processing time in seconds
    """
    file_path: Path
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file": str(self.file_path),
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


class StreamingBatchProcessor:
    """
    Process files in batch with streaming progress updates.
    
    Features:
    - Bounded concurrency with semaphore
    - Progress callbacks for real-time updates
    - Error handling per file (doesn't stop batch)
    - Time estimation
    
    Example:
        processor = StreamingBatchProcessor(max_workers=4)
        
        async def process_file(file: Path) -> dict:
            result = await some_async_operation(file)
            return result
        
        def on_progress(update: ProgressUpdate):
            print(update.format_status())
        
        results = await processor.process_batch(
            files,
            process_file,
            progress_callback=on_progress
        )
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        progress_interval: float = 0.1,
    ):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum concurrent operations
            progress_interval: Minimum interval between progress callbacks (seconds)
        """
        self.max_workers = max_workers
        self.progress_interval = progress_interval
    
    async def process_batch(
        self,
        files: list[Path],
        process_fn: Callable[[Path], Any],
        *,
        progress_callback: Callable[[ProgressUpdate], None] | None = None,
        result_callback: Callable[[FileResult], None] | None = None,
    ) -> list[FileResult]:
        """
        Process files in batch with streaming progress.
        
        Args:
            files: List of files to process
            process_fn: Async function to process each file
            progress_callback: Optional callback for progress updates
            result_callback: Optional callback for each file result (streaming)
            
        Returns:
            List of FileResult objects
        """
        if not files:
            return []
        
        total = len(files)
        completed = 0
        results: list[FileResult] = []
        semaphore = asyncio.Semaphore(self.max_workers)
        start_time = time.time()
        last_progress_time = 0.0
        results_lock = asyncio.Lock()
        
        async def process_file(file: Path) -> FileResult:
            nonlocal completed, last_progress_time
            
            file_start = time.time()
            
            async with semaphore:
                try:
                    result = await process_fn(file)
                    file_result = FileResult(
                        file_path=file,
                        success=True,
                        result=result,
                        duration_seconds=time.time() - file_start,
                    )
                except Exception as e:
                    file_result = FileResult(
                        file_path=file,
                        success=False,
                        error=str(e),
                        duration_seconds=time.time() - file_start,
                    )
                
                # Update completed count (thread-safe)
                async with results_lock:
                    completed += 1
                    results.append(file_result)
                    current_completed = completed
                
                # Stream result immediately
                if result_callback:
                    try:
                        result_callback(file_result)
                    except Exception:
                        pass  # Don't fail batch on callback error
                
                # Send progress update (rate-limited)
                current_time = time.time()
                if progress_callback and (current_time - last_progress_time >= self.progress_interval):
                    elapsed = current_time - start_time
                    avg_time = elapsed / current_completed if current_completed > 0 else 0
                    remaining = (total - current_completed) * avg_time if avg_time > 0 else None
                    
                    update = ProgressUpdate(
                        current=current_completed,
                        total=total,
                        percentage=(current_completed / total) * 100,
                        current_file=str(file),
                        status="completed" if file_result.success else "failed",
                        result=file_result.result if file_result.success else None,
                        error=file_result.error,
                        elapsed_seconds=elapsed,
                        estimated_remaining=remaining,
                    )
                    
                    try:
                        progress_callback(update)
                    except Exception:
                        pass  # Don't fail batch on callback error
                    
                    last_progress_time = current_time
                
                return file_result
        
        # Initial progress update
        if progress_callback:
            progress_callback(ProgressUpdate(
                current=0,
                total=total,
                percentage=0.0,
                status="starting",
                elapsed_seconds=0.0,
            ))
        
        # Process all files in parallel (bounded)
        tasks = [process_file(file) for file in files]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final progress update
        if progress_callback:
            elapsed = time.time() - start_time
            sum(1 for r in results if r.success)
            progress_callback(ProgressUpdate(
                current=total,
                total=total,
                percentage=100.0,
                status="completed",
                elapsed_seconds=elapsed,
            ))
        
        return results
    
    def aggregate_results(self, results: list[FileResult]) -> dict[str, Any]:
        """
        Aggregate batch results.
        
        Args:
            results: List of FileResult objects
            
        Returns:
            Aggregated results dictionary
        """
        return {
            "total": len(results),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "files": [r.to_dict() for r in results],
            "errors": [
                {"file": str(r.file_path), "error": r.error}
                for r in results if not r.success
            ],
        }


async def process_files_with_streaming(
    files: list[Path],
    process_fn: Callable[[Path], Any],
    max_workers: int = 4,
    progress_callback: Callable[[ProgressUpdate], None] | None = None,
    result_callback: Callable[[FileResult], None] | None = None,
) -> dict[str, Any]:
    """
    Convenience function to process files with streaming progress.
    
    Args:
        files: List of files to process
        process_fn: Async function to process each file
        max_workers: Maximum concurrent operations
        progress_callback: Optional callback for progress updates
        result_callback: Optional callback for each file result (streaming)
        
    Returns:
        Aggregated results dictionary
    """
    processor = StreamingBatchProcessor(max_workers=max_workers)
    results = await processor.process_batch(
        files,
        process_fn,
        progress_callback=progress_callback,
        result_callback=result_callback,
    )
    return processor.aggregate_results(results)
