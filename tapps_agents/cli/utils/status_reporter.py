"""
Status reporter for workflow execution.

Provides real-time status updates, progress indicators, and execution summaries.
SIMPLE_MODE_FEEDBACK_REVIEW: includes elapsed time and estimated remaining (informational only).
"""

import sys
import time
from typing import Any


def _format_elapsed(seconds: float) -> str:
    """Format seconds as e.g. 2m 30s or 45s."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}m {s}s" if s else f"{m}m"


class StatusReporter:
    """Provides real-time status reporting for workflow execution."""
    
    def __init__(self, total_steps: int = 0):
        """
        Initialize status reporter.
        
        Args:
            total_steps: Total number of steps in workflow (0 = unknown)
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.step_times: list[tuple[int, str, float]] = []  # (step_num, step_name, duration or start_time)
        self.step_status: dict[int, str] = {}  # step_num -> status ("success", "failed", "skipped")
    
    def _elapsed(self) -> float:
        return time.time() - self.start_time

    def _estimated_remaining(self, last_completed_step: int) -> str | None:
        """Estimate remaining time from completed step durations (SIMPLE_MODE_FEEDBACK_REVIEW)."""
        if self.total_steps <= 0 or last_completed_step >= self.total_steps:
            return None
        # Only use entries that have been updated to duration (seconds), not start_time (timestamp)
        completed_durations = [
            t[2] for t in self.step_times
            if isinstance(t[2], (int, float)) and 0 < t[2] < 3600
        ]
        if not completed_durations:
            return None
        avg = sum(completed_durations) / len(completed_durations)
        remaining_steps = self.total_steps - last_completed_step
        est_sec = avg * remaining_steps
        return f"~{_format_elapsed(est_sec)} remaining"
    
    def start_step(self, step_num: int, step_name: str) -> None:
        """
        Start a workflow step.
        
        Args:
            step_num: Step number (1-based)
            step_name: Name of the step
        """
        self.current_step = step_num
        step_start_time = time.time()
        self.step_times.append((step_num, step_name, step_start_time))
        
        elapsed_str = _format_elapsed(self._elapsed())
        if self.total_steps > 0:
            print(f"\n[{step_num}/{self.total_steps}] {step_name}... (elapsed: {elapsed_str})", end="", flush=True, file=sys.stderr)
        else:
            print(f"\n[Step {step_num}] {step_name}... (elapsed: {elapsed_str})", end="", flush=True, file=sys.stderr)
    
    def complete_step(self, step_num: int, step_name: str, status: str = "success") -> None:
        """
        Complete a workflow step.
        
        Args:
            step_num: Step number (1-based)
            step_name: Name of the step
            status: Step status ("success", "failed", "skipped")
        """
        # Find the step start time
        step_duration = 0.0
        for i, (num, name, start_time) in enumerate(self.step_times):
            if num == step_num and name == step_name:
                step_duration = time.time() - start_time
                # Update with duration
                self.step_times[i] = (num, name, step_duration)
                break
        
        self.step_status[step_num] = status
        
        status_icon = "[OK]" if status == "success" else "[FAIL]" if status == "failed" else "[SKIP]"
        duration_str = f"({step_duration:.1f}s)" if step_duration > 0 else ""
        elapsed_str = _format_elapsed(self._elapsed())
        eta = self._estimated_remaining(step_num) if self.total_steps > 0 else None
        eta_str = f", {eta}" if eta else ""
        step_progress = f"Step {step_num}/{self.total_steps} complete" if self.total_steps > 0 else f"Step {step_num} complete"
        print(f" {status_icon} {duration_str} | {step_progress}, elapsed: {elapsed_str}{eta_str}", file=sys.stderr)
        sys.stderr.flush()
    
    def print_summary(self) -> None:
        """Print execution summary."""
        total_duration = time.time() - self.start_time
        
        print("\n" + "=" * 60, file=sys.stderr)
        print("Execution Summary", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        if self.total_steps > 0:
            completed = sum(1 for s in self.step_status.values() if s == "success")
            print(f"Steps Executed: {completed}/{self.total_steps}", file=sys.stderr)
        
        print(f"Total Time: {total_duration:.1f}s", file=sys.stderr)
        
        if self.step_times:
            print("\nStep Details:", file=sys.stderr)
            for step_num, step_name, duration in self.step_times:
                if isinstance(duration, float):
                    status = self.step_status.get(step_num, "unknown")
                    icon = "[OK]" if status == "success" else "[FAIL]" if status == "failed" else "[SKIP]"
                    print(f"  {icon} Step {step_num}: {step_name} ({duration:.1f}s)", file=sys.stderr)
        
        sys.stderr.flush()
