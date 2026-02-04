"""
Visual Feedback for Simple Mode.

Provides user-friendly progress reporting, results formatting with visual indicators,
and before/after comparisons for Simple Mode operations.
"""

from dataclasses import dataclass
from typing import Any

from ..cli.feedback import get_feedback


@dataclass
class OperationResult:
    """Represents the result of a Simple Mode operation."""

    action: str  # build, review, fix, test
    status: str  # success, failed, partial
    files_created: list[str] | None = None
    files_modified: list[str] | None = None
    issues_found: int = 0
    issues_fixed: int = 0
    score_before: float | None = None
    score_after: float | None = None
    duration_seconds: float | None = None
    message: str = ""


class SimpleModeVisualFeedback:
    """Provides visual feedback for Simple Mode operations."""

    def __init__(self):
        self.feedback = get_feedback()

    def show_operation_start(self, action: str, description: str) -> None:
        """Display the start of an operation."""
        action_display = {
            "build": "🔨 Building",
            "review": "🔍 Reviewing",
            "fix": "🔧 Fixing",
            "test": "🧪 Testing",
        }.get(action.lower(), "⚙️ Processing")

        self.feedback.start_operation(f"{action_display} {description}")

    def show_progress(self, step: str, current: int, total: int | None = None) -> None:
        """Show progress for a multi-step operation."""
        if total:
            percentage = int((current / total) * 100)
            message = f"{step} ({current}/{total})"
            self.feedback.progress(message, percentage=percentage, show_progress_bar=True)
        else:
            self.feedback.progress(step)

    def show_agent_activity(self, agent_name: str, activity: str) -> None:
        """Show what a specific agent is doing."""
        self.feedback.info(f"[{agent_name}] {activity}")

    def format_result(self, result: OperationResult) -> None:
        """Format and display the final result of an operation."""
        self.feedback.clear_progress()

        if result.status == "success":
            self._format_success_result(result)
        elif result.status == "failed":
            self._format_failed_result(result)
        else:
            self._format_partial_result(result)

    def _format_success_result(self, result: OperationResult) -> None:
        """Format a successful operation result."""
        action_display = {
            "build": "Build",
            "review": "Review",
            "fix": "Fix",
            "test": "Test",
        }.get(result.action.lower(), "Operation")

        print("\n" + "=" * 70)
        print(f"✅ {action_display} completed successfully!")
        print("=" * 70)

        if result.files_created:
            print(f"\n📁 Created {len(result.files_created)} file(s):")
            for file in result.files_created:
                print(f"   • {file}")

        if result.files_modified:
            print(f"\n📝 Modified {len(result.files_modified)} file(s):")
            for file in result.files_modified:
                print(f"   • {file}")

        if result.issues_fixed > 0:
            print(f"\n🔧 Fixed {result.issues_fixed} issue(s)")

        if result.score_before is not None and result.score_after is not None:
            self._show_score_comparison(result.score_before, result.score_after)

        if result.duration_seconds:
            print(f"\n⏱️  Duration: {result.duration_seconds:.1f}s")

        if result.message:
            print(f"\n💡 {result.message}")

        print()

    def _format_failed_result(self, result: OperationResult) -> None:
        """Format a failed operation result."""
        action_display = {
            "build": "Build",
            "review": "Review",
            "fix": "Fix",
            "test": "Test",
        }.get(result.action.lower(), "Operation")

        print("\n" + "=" * 70)
        print(f"❌ {action_display} failed")
        print("=" * 70)

        if result.message:
            print(f"\n{result.message}")

        print("\n💡 Try:")
        print("   • Check the error message above")
        print("   • Verify your project configuration")
        print("   • Run 'tapps-agents simple-mode status' to check settings")
        print()

    def _format_partial_result(self, result: OperationResult) -> None:
        """Format a partially successful operation result."""
        action_display = {
            "build": "Build",
            "review": "Review",
            "fix": "Fix",
            "test": "Test",
        }.get(result.action.lower(), "Operation")

        print("\n" + "=" * 70)
        print(f"⚠️  {action_display} completed with warnings")
        print("=" * 70)

        if result.message:
            print(f"\n{result.message}")

        if result.issues_found > 0:
            print(f"\n⚠️  Found {result.issues_found} issue(s) that need attention")

        print()

    def _show_score_comparison(self, before: float, after: float) -> None:
        """Show a before/after score comparison."""
        improvement = after - before
        improvement_pct = (improvement / before * 100) if before > 0 else 0

        print("\n📊 Code Quality Score:")
        print(f"   Before: {before:.1f}/100")
        print(f"   After:  {after:.1f}/100")

        if improvement > 0:
            print(f"   Improvement: +{improvement:.1f} (+{improvement_pct:.1f}%) ✅")
        elif improvement < 0:
            print(f"   Change: {improvement:.1f} ({improvement_pct:.1f}%) ⚠️")
        else:
            print("   No change")

    def show_before_after_comparison(
        self,
        file_path: str,
        before_content: str | None = None,
        after_content: str | None = None,
        changes_summary: str | None = None,
    ) -> None:
        """Show a before/after comparison for file changes."""
        print("\n" + "-" * 70)
        print(f"📄 Changes to: {file_path}")
        print("-" * 70)

        if changes_summary:
            print(f"\n{changes_summary}")
        elif before_content and after_content:
            # Show a simple diff summary
            before_lines = len(before_content.splitlines())
            after_lines = len(after_content.splitlines())
            lines_changed = abs(after_lines - before_lines)

            if after_lines > before_lines:
                print(f"\n➕ Added {lines_changed} line(s)")
            elif after_lines < before_lines:
                print(f"\n➖ Removed {lines_changed} line(s)")
            else:
                print("\n📝 Modified (same line count)")

        print()

    def show_issues_list(self, issues: list[dict[str, Any]]) -> None:
        """Display a formatted list of issues."""
        if not issues:
            return

        print("\n" + "-" * 70)
        print("📋 Issues Found:")
        print("-" * 70)

        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "unknown").upper()
            severity_icon = {
                "HIGH": "🔴",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "CRITICAL": "🔴",
            }.get(severity, "⚪")

            print(f"\n{i}. {severity_icon} [{severity}] {issue.get('title', 'Issue')}")
            if issue.get("file"):
                print(f"   File: {issue['file']}")
            if issue.get("line"):
                print(f"   Line: {issue['line']}")
            if issue.get("message"):
                print(f"   {issue['message']}")

        print()

    def show_summary_stats(self, stats: dict[str, Any]) -> None:
        """Display summary statistics."""
        print("\n" + "=" * 70)
        print("📊 Summary")
        print("=" * 70)

        for key, value in stats.items():
            if isinstance(value, (int, float)):
                print(f"   {key.replace('_', ' ').title()}: {value}")
            else:
                print(f"   {key.replace('_', ' ').title()}: {value}")

        print()

