"""
Modern 2025 pytest plugin with Rich visual progress indicators.

Provides:
- Real-time progress bars
- Emoji indicators for test status
- Color-coded output
- Test suite progress tracking
- Modern visual feedback
"""

import os
import sys
from typing import Any

import pytest
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 - use environment variable only
        pass


def safe_emoji(emoji: str, fallback: str) -> str:
    """Return emoji if encoding supports it, otherwise fallback."""
    if sys.platform == "win32":
        try:
            # Test if emoji can be encoded
            emoji.encode(sys.stdout.encoding or "utf-8")
            return emoji
        except (UnicodeEncodeError, AttributeError):
            return fallback
    return emoji


class RichProgressReporter:
    """Rich-based progress reporter for pytest."""

    def __init__(self):
        self.console = Console()
        self.progress = None
        self.live = None
        self.test_count = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0
        self.current_test = ""
        self.test_results = []
        self.session_start_time = None
        self.main_task = None

    def start_session(self, session: pytest.Session) -> None:
        """Called after the Session object has been created."""
        import time

        self.session_start_time = time.time()
        self.test_count = len(session.items)

        # Print header immediately (before progress bar)
        self.console.print()
        rocket = safe_emoji("🚀", "[START]")
        self.console.print(
            Panel(
                f"[bold green]{rocket} Starting Test Suite[/bold green]\n"
                f"[dim]Total tests: {self.test_count}[/dim]",
                border_style="green",
            )
        )
        self.console.print()

        # Create progress bar
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        # Start live display
        test_emoji = safe_emoji("🧪", "[TEST]")
        self.live = Live(
            Panel(
                self.progress,
                title=f"[bold cyan]{test_emoji} Test Suite Progress[/bold cyan]",
                border_style="cyan",
            ),
            console=self.console,
            refresh_per_second=10,
            screen=False,  # Don't clear screen
        )
        self.live.start()

        # Add main progress task
        self.main_task = self.progress.add_task(
            f"[cyan]Running {self.test_count} tests...", total=self.test_count
        )

    def log_test_start(self, nodeid: str, location: tuple) -> None:
        """Called at the start of running a test."""
        # Extract test name
        test_name = nodeid.split("::")[-1]
        class_name = nodeid.split("::")[-2] if "::" in nodeid else ""
        if class_name:
            self.current_test = f"{class_name}::{test_name}"
        else:
            self.current_test = test_name

        # Update progress description
        if self.progress:
            self.progress.update(
                self.main_task,
                description=f"[cyan]Running:[/cyan] [yellow]{self.current_test[:60]}...[/yellow]"
                if len(self.current_test) > 60
                else f"[cyan]Running:[/cyan] [yellow]{self.current_test}[/yellow]",
            )

    def log_test_finish(self, nodeid: str, location: tuple) -> None:
        """Called at the end of running a test."""
        # Advance progress
        if self.progress:
            self.progress.advance(self.main_task)

    def log_test_report(self, report: pytest.TestReport) -> None:
        """Process a test report."""
        if report.when == "call":  # Only count actual test execution
            status_emoji = {
                "passed": safe_emoji("✅", "[OK]"),
                "failed": safe_emoji("❌", "[FAIL]"),
                "skipped": safe_emoji("⏭️", "[SKIP]"),
                "error": safe_emoji("💥", "[ERROR]"),
            }

            status_color = {
                "passed": "green",
                "failed": "red",
                "skipped": "yellow",
                "error": "red",
            }

            emoji = status_emoji.get(report.outcome, safe_emoji("❓", "[?]"))
            color = status_color.get(report.outcome, "white")

            # Store result
            self.test_results.append(
                {
                    "name": self.current_test,
                    "outcome": report.outcome,
                    "emoji": emoji,
                    "duration": report.duration or 0,
                }
            )

            # Update counters
            if report.outcome == "passed":
                self.passed += 1
            elif report.outcome == "failed":
                self.failed += 1
            elif report.outcome == "skipped":
                self.skipped += 1
            elif report.outcome == "error":
                self.errors += 1

            # Print result
            duration_str = f"{report.duration:.2f}s" if report.duration else "0.00s"
            status_text = Text(f"{emoji} {self.current_test[:50]}", style=color)
            if len(self.current_test) > 50:
                status_text.append("...", style="dim")

            # Show in console (non-blocking)
            self.console.print(f"{emoji} [{color}]{self.current_test[:70]}[/{color}] [dim]{duration_str}[/dim]")

    def finish_session(self, session: pytest.Session, exitstatus: int) -> None:
        """Called after whole test run finished."""
        import time

        if self.live:
            self.live.stop()

        if self.progress:
            self.progress.stop()

        # Calculate totals
        total = self.passed + self.failed + self.skipped + self.errors
        duration = time.time() - (self.session_start_time or time.time())

        # Create summary
        self.console.print()
        chart_emoji = safe_emoji("📊", "[SUMMARY]")
        self.console.print(
            Panel(
                f"[bold cyan]{chart_emoji} Test Suite Summary[/bold cyan]",
                border_style="cyan",
            )
        )

        # Summary table
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold", justify="right")
        summary.add_column(style="", justify="left")

        summary.add_row(safe_emoji("✅", "[OK]"), f"[green]Passed:[/green] {self.passed}")
        summary.add_row(safe_emoji("❌", "[FAIL]"), f"[red]Failed:[/red] {self.failed}")
        summary.add_row(safe_emoji("⏭️", "[SKIP]"), f"[yellow]Skipped:[/yellow] {self.skipped}")
        summary.add_row(safe_emoji("💥", "[ERROR]"), f"[red]Errors:[/red] {self.errors}")
        summary.add_row("", "")
        summary.add_row(safe_emoji("📈", "[TOTAL]"), f"[cyan]Total:[/cyan] {total}")
        summary.add_row(safe_emoji("⏱️", "[TIME]"), f"[cyan]Duration:[/cyan] {duration:.2f}s")

        self.console.print(summary)

        # Show failed tests if any
        if self.failed > 0 or self.errors > 0:
            self.console.print()
            fail_emoji = safe_emoji("❌", "[FAIL]")
            self.console.print(
                Panel(
                    f"[bold red]{fail_emoji} Failed Tests[/bold red]",
                    border_style="red",
                )
            )
            failed_tests = [
                r for r in self.test_results if r["outcome"] in ("failed", "error")
            ]
            for test in failed_tests[:10]:  # Show first 10
                self.console.print(f"  {test['emoji']} [red]{test['name']}[/red]")

            if len(failed_tests) > 10:
                self.console.print(f"  [dim]... and {len(failed_tests) - 10} more[/dim]")

        # Final status
        self.console.print()
        if exitstatus == 0:
            success_emoji = safe_emoji("✨", "[SUCCESS]")
            self.console.print(
                Panel(
                    f"[bold green]{success_emoji} All tests passed![/bold green]",
                    border_style="green",
                )
            )
        else:
            error_emoji = safe_emoji("💥", "[ERROR]")
            self.console.print(
                Panel(
                    f"[bold red]{error_emoji} Test suite failed with {self.failed + self.errors} error(s)[/bold red]",
                    border_style="red",
                )
            )
        self.console.print()


# Global reporter instance
_reporter: RichProgressReporter | None = None


def pytest_configure(config: pytest.Config) -> None:
    """Register the plugin."""
    global _reporter
    
    # Only use rich reporter if not in quiet mode and not in parallel worker mode
    # --quiet is a count option, so it returns an int (0, 1, 2, etc.)
    quiet_count = config.getoption("--quiet", default=0)
    tb_option = config.getoption("--tb", default="short")
    
    # Check if we're in a worker process (pytest-xdist)
    # workerinput is only present in worker processes, not the main process
    is_worker = hasattr(config, 'workerinput')
    
    # Create and store reporter if not quiet, traceback not disabled, and not a worker
    # Rich visualization should only run in the main process
    if quiet_count == 0 and tb_option != "no" and not is_worker:
        _reporter = RichProgressReporter()


# Module-level hooks that delegate to the reporter
def pytest_sessionstart(session: pytest.Session) -> None:
    """Called after the Session object has been created."""
    if _reporter:
        _reporter.start_session(session)


def pytest_runtest_logstart(nodeid: str, location: tuple) -> None:
    """Called at the start of running a test."""
    if _reporter:
        _reporter.log_test_start(nodeid, location)


def pytest_runtest_logfinish(nodeid: str, location: tuple) -> None:
    """Called at the end of running a test."""
    if _reporter:
        _reporter.log_test_finish(nodeid, location)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Process a test report."""
    if _reporter:
        _reporter.log_test_report(report)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Called after whole test run finished."""
    if _reporter:
        _reporter.finish_session(session, exitstatus)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify test items after collection."""
    pass

