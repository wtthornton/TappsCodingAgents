"""
Status reporter for workflow execution.

Provides real-time status updates, progress indicators, and execution summaries.
"""

import sys
import time
from typing import Any


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
        self.step_times: list[tuple[int, str, float]] = []  # (step_num, step_name, duration)
        self.step_status: dict[int, str] = {}  # step_num -> status ("success", "failed", "skipped")
    
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
        
        if self.total_steps > 0:
            print(f"\n[{step_num}/{self.total_steps}] {step_name}...", end="", flush=True, file=sys.stderr)
        else:
            print(f"\n[Step {step_num}] {step_name}...", end="", flush=True, file=sys.stderr)
    
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
        
        print(f" {status_icon} {duration_str}", file=sys.stderr)
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
