"""
Trace Manager for Playwright - Generate and manage trace files for debugging.

Enables automatic trace file generation on test failures and provides
trace viewer integration for enhanced debugging.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TraceManager:
    """
    Manage Playwright trace files for test debugging.

    Generates trace files on test failures and provides trace viewer links.
    """

    def __init__(self, trace_dir: Path | None = None):
        """
        Initialize trace manager.

        Args:
            trace_dir: Directory to save trace files (default: .tapps-agents/traces/)
        """
        if trace_dir is None:
            trace_dir = Path(".tapps-agents") / "traces"
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

        self.current_trace_path: Path | None = None
        self.trace_enabled = False

    def start_tracing(
        self,
        context: Any,
        test_name: str | None = None,
        screenshots: bool = True,
        snapshots: bool = True,
        sources: bool = True,
    ) -> Path:
        """
        Start tracing for a test.

        Args:
            context: Playwright BrowserContext
            test_name: Optional test name for trace file naming
            screenshots: Capture screenshots
            snapshots: Capture DOM snapshots
            sources: Capture source files

        Returns:
            Path where trace will be saved
        """
        import time

        if test_name is None:
            test_name = f"test_{int(time.time())}"

        # Create trace filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_filename = f"{test_name}_{timestamp}.zip"
        trace_path = self.trace_dir / trace_filename

        # Start tracing (for Python Playwright)
        try:
            if hasattr(context, "tracing"):
                context.tracing.start(
                    screenshots=screenshots,
                    snapshots=snapshots,
                    sources=sources,
                )
                self.trace_enabled = True
                self.current_trace_path = trace_path
                logger.info(f"Started tracing: {trace_path}")
        except AttributeError:
            # MCP mode - tracing handled by MCP server
            logger.info(f"Tracing will be handled by MCP server: {trace_path}")
            self.current_trace_path = trace_path

        return trace_path

    def stop_tracing(self, context: Any | None = None) -> Path | None:
        """
        Stop tracing and save trace file.

        Args:
            context: Playwright BrowserContext (for Python Playwright)

        Returns:
            Path to saved trace file or None
        """
        if self.current_trace_path is None:
            return None

        try:
            # Stop tracing (for Python Playwright)
            if context and hasattr(context, "tracing"):
                context.tracing.stop(path=str(self.current_trace_path))
                logger.info(f"Trace saved: {self.current_trace_path}")
            else:
                # MCP mode - create placeholder or use MCP trace
                logger.info(f"Trace path ready: {self.current_trace_path}")

            trace_path = self.current_trace_path
            self.current_trace_path = None
            self.trace_enabled = False

            return trace_path
        except Exception as e:
            logger.error(f"Failed to save trace: {e}")
            return None

    def generate_trace_viewer_link(self, trace_path: Path) -> str:
        """
        Generate trace viewer link or command.

        Args:
            trace_path: Path to trace file

        Returns:
            Trace viewer link or command
        """
        if not trace_path.exists():
            return f"Trace file not found: {trace_path}"

        # Generate Playwright trace viewer command
        command = f"npx playwright show-trace {trace_path}"
        link = f"file://{trace_path.absolute()}"

        return f"""
Trace file: {trace_path}
View trace: {command}
Or open: {link}
"""

    def create_trace_report(
        self,
        test_name: str,
        trace_path: Path | None,
        error: str | None = None,
        screenshot_path: Path | None = None,
    ) -> dict[str, Any]:
        """
        Create trace report for test failure.

        Args:
            test_name: Name of the test
            trace_path: Path to trace file
            error: Error message
            screenshot_path: Optional screenshot path

        Returns:
            Trace report dictionary
        """
        report = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "trace_available": trace_path is not None and trace_path.exists(),
            "trace_path": str(trace_path) if trace_path else None,
            "error": error,
            "screenshot_path": str(screenshot_path) if screenshot_path else None,
        }

        if trace_path and trace_path.exists():
            report["trace_viewer_command"] = f"npx playwright show-trace {trace_path}"
            report["trace_viewer_link"] = f"file://{trace_path.absolute()}"

        return report

    def cleanup_old_traces(self, max_age_days: int = 7, max_traces: int = 50):
        """
        Clean up old trace files.

        Args:
            max_age_days: Maximum age in days
            max_traces: Maximum number of traces to keep
        """
        import time

        traces = sorted(
            self.trace_dir.glob("*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Remove old traces
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        removed = 0
        for trace in traces:
            if trace.stat().st_mtime < cutoff_time:
                trace.unlink()
                removed += 1

        # Keep only max_traces most recent
        if len(traces) > max_traces:
            for trace in traces[max_traces:]:
                trace.unlink()
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old trace files")

    def list_traces(self) -> list[dict[str, Any]]:
        """
        List all available trace files.

        Returns:
            List of trace metadata dictionaries
        """
        traces = []
        for trace_file in sorted(
            self.trace_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            stat = trace_file.stat()
            traces.append(
                {
                    "filename": trace_file.name,
                    "path": str(trace_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "viewer_command": f"npx playwright show-trace {trace_file}",
                }
            )

        return traces
