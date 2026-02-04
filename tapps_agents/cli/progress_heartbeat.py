"""
Progress Heartbeat - Continuous activity indicator for long-running CLI operations.

Provides a heartbeat mechanism that shows activity even when operations appear stuck,
ensuring users know the system is still working.
"""

import asyncio
import threading
import time
from collections.abc import Callable

from .feedback import FeedbackManager, get_feedback


class ProgressHeartbeat:
    """
    Heartbeat indicator that shows continuous activity during long-running operations.
    
    Automatically starts showing progress updates after a delay, and continues
    updating periodically to indicate the system is still working.
    """
    
    def __init__(
        self,
        message: str = "Working...",
        start_delay: float = 2.0,
        update_interval: float = 1.0,
        feedback_manager: FeedbackManager | None = None,
    ):
        """
        Initialize progress heartbeat.
        
        Args:
            message: Base message to display
            start_delay: Seconds to wait before showing progress (default: 2s)
            update_interval: Seconds between progress updates (default: 1s)
            feedback_manager: Optional FeedbackManager instance
        """
        self.message = message
        self.start_delay = start_delay
        self.update_interval = update_interval
        self.feedback = feedback_manager or get_feedback()
        self._running = False
        self._thread: threading.Thread | None = None
        self._start_time: float | None = None
        self._last_update: float | None = None
        self._update_count = 0
        
    def start(self) -> None:
        """Start the heartbeat indicator."""
        if self._running:
            return
            
        self._running = True
        self._start_time = time.time()
        self._last_update = self._start_time
        self._update_count = 0
        
        # Start heartbeat thread
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the heartbeat indicator."""
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        self._thread = None
        self.feedback.clear_progress()
    
    def update_message(self, message: str) -> None:
        """Update the progress message."""
        self.message = message
    
    def _heartbeat_loop(self) -> None:
        """Main heartbeat loop running in background thread."""
        # Wait for initial delay
        time.sleep(self.start_delay)
        
        if not self._running:
            return
        
        # Start showing progress
        while self._running:
            elapsed = time.time() - (self._start_time or 0)
            
            # Format elapsed time
            if elapsed < 60:
                elapsed_str = f"{int(elapsed)}s"
            elif elapsed < 3600:
                elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
            else:
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                elapsed_str = f"{hours}h {minutes}m"
            
            # Update progress message with elapsed time
            progress_message = f"{self.message} ({elapsed_str})"
            
            # Show progress (indeterminate spinner)
            self.feedback.progress(progress_message, show_progress_bar=False)
            
            # Wait for next update
            time.sleep(self.update_interval)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class AsyncProgressHeartbeat:
    """
    Async version of progress heartbeat for async operations.
    
    Uses asyncio instead of threading for better integration with async code.
    """
    
    def __init__(
        self,
        message: str = "Working...",
        start_delay: float = 2.0,
        update_interval: float = 1.0,
        feedback_manager: FeedbackManager | None = None,
    ):
        """
        Initialize async progress heartbeat.
        
        Args:
            message: Base message to display
            start_delay: Seconds to wait before showing progress (default: 2s)
            update_interval: Seconds between progress updates (default: 1s)
            feedback_manager: Optional FeedbackManager instance
        """
        self.message = message
        self.start_delay = start_delay
        self.update_interval = update_interval
        self.feedback = feedback_manager or get_feedback()
        self._task: asyncio.Task | None = None
        self._running = False
        self._start_time: float | None = None
        
    async def start(self) -> None:
        """Start the heartbeat indicator."""
        if self._running:
            return
            
        self._running = True
        self._start_time = time.time()
        self._task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self) -> None:
        """Stop the heartbeat indicator."""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        self.feedback.clear_progress()
    
    def update_message(self, message: str) -> None:
        """Update the progress message."""
        self.message = message
    
    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop running as async task."""
        # Wait for initial delay
        await asyncio.sleep(self.start_delay)
        
        if not self._running:
            return
        
        # Start showing progress
        while self._running:
            elapsed = time.time() - (self._start_time or 0)
            
            # Format elapsed time
            if elapsed < 60:
                elapsed_str = f"{int(elapsed)}s"
            elif elapsed < 3600:
                elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
            else:
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                elapsed_str = f"{hours}h {minutes}m"
            
            # Update progress message with elapsed time
            progress_message = f"{self.message} ({elapsed_str})"
            
            # Show progress (indeterminate spinner)
            self.feedback.progress(progress_message, show_progress_bar=False)
            
            # Wait for next update
            await asyncio.sleep(self.update_interval)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


def with_progress_heartbeat(
    message: str = "Working...",
    start_delay: float = 2.0,
):
    """
    Decorator to add progress heartbeat to a function.
    
    Usage:
        @with_progress_heartbeat("Processing files...")
        def long_running_function():
            # ... do work ...
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            # Async function
            async def async_wrapper(*args, **kwargs):
                heartbeat = AsyncProgressHeartbeat(message, start_delay)
                try:
                    await heartbeat.start()
                    return await func(*args, **kwargs)
                finally:
                    await heartbeat.stop()
            return async_wrapper
        else:
            # Sync function
            def sync_wrapper(*args, **kwargs):
                heartbeat = ProgressHeartbeat(message, start_delay)
                try:
                    heartbeat.start()
                    return func(*args, **kwargs)
                finally:
                    heartbeat.stop()
            return sync_wrapper
    return decorator

