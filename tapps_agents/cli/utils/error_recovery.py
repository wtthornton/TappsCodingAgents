"""
Error recovery handler for workflow execution.

Provides recovery options when workflow steps fail.
"""

from collections.abc import Callable
from typing import Any


class ErrorRecoveryHandler:
    """Handles error recovery options for failed workflow steps."""
    
    def __init__(self, interactive: bool = False):
        """
        Initialize error recovery handler.
        
        Args:
            interactive: If True, prompt user for recovery action (default: False)
        """
        self.interactive = interactive
        self.recovery_actions: list[dict[str, Any]] = []
    
    def handle_step_error(
        self,
        step_num: int,
        step_name: str,
        error: Exception,
        retry_callback: Callable[[], Any] | None = None,
        skip_callback: Callable[[], Any] | None = None,
        continue_callback: Callable[[], Any] | None = None,
    ) -> str:
        """
        Handle a step error and determine recovery action.
        
        Args:
            step_num: Step number that failed
            step_name: Name of the step that failed
            error: Exception that occurred
            retry_callback: Optional callback to retry the step
            skip_callback: Optional callback to skip the step
            continue_callback: Optional callback to continue with degraded functionality
            
        Returns:
            Recovery action taken: "retry", "skip", "continue", or "fail"
        """
        error_info = {
            "step_num": step_num,
            "step_name": step_name,
            "error": str(error),
            "error_type": type(error).__name__,
        }
        
        # Determine recovery strategy based on error type
        recovery_action = self._determine_recovery_strategy(error, step_name)
        
        if self.interactive:
            # Interactive mode: prompt user
            recovery_action = self._prompt_recovery_action(step_name, error)
        
        # Execute recovery action
        if recovery_action == "retry" and retry_callback:
            try:
                retry_callback()
                error_info["recovery_action"] = "retry"
                error_info["recovery_success"] = True
                self.recovery_actions.append(error_info)
                return "retry"
            except Exception as retry_error:
                error_info["recovery_action"] = "retry"
                error_info["recovery_success"] = False
                error_info["retry_error"] = str(retry_error)
                self.recovery_actions.append(error_info)
                return "fail"
        
        elif recovery_action == "skip" and skip_callback:
            skip_callback()
            error_info["recovery_action"] = "skip"
            self.recovery_actions.append(error_info)
            return "skip"
        
        elif recovery_action == "continue" and continue_callback:
            continue_callback()
            error_info["recovery_action"] = "continue"
            self.recovery_actions.append(error_info)
            return "continue"
        
        else:
            # No recovery possible or action is "fail"
            error_info["recovery_action"] = "fail"
            self.recovery_actions.append(error_info)
            return "fail"
    
    def _determine_recovery_strategy(self, error: Exception, step_name: str) -> str:
        """
        Determine recovery strategy based on error type and step.
        
        Args:
            error: Exception that occurred
            step_name: Name of the step
            
        Returns:
            Recovery strategy: "retry", "skip", "continue", or "fail"
        """
        type(error).__name__
        error_str = str(error).lower()
        
        # Network/timeout errors: retry
        if "timeout" in error_str or "connection" in error_str or "network" in error_str:
            return "retry"
        
        # Validation errors: skip (non-critical steps)
        if "validation" in error_str or "invalid" in error_str:
            step_lower = step_name.lower()
            # Check if step name contains non-critical keywords
            if any(keyword in step_lower for keyword in ["review", "test", "document"]):
                return "skip"  # Non-critical steps can be skipped
            return "fail"  # Critical steps fail
        
        # File not found: continue (may be created later)
        if "not found" in error_str:
            step_lower = step_name.lower()
            # Check if step name contains non-critical keywords
            if any(keyword in step_lower for keyword in ["document", "test"]):
                return "continue"  # Can continue without these
            return "fail"
        
        # Default: fail for unknown errors
        return "fail"
    
    def _prompt_recovery_action(self, step_name: str, error: Exception) -> str:
        """
        Prompt user for recovery action (interactive mode).
        
        Args:
            step_name: Name of the failed step
            error: Exception that occurred
            
        Returns:
            User-selected recovery action
        """
        print(f"\n{'='*60}")
        print(f"Step Failed: {step_name}")
        print(f"{'='*60}")
        print(f"Error: {error}")
        print("\nRecovery Options:")
        print("  1. Retry step")
        print("  2. Skip step and continue")
        print("  3. Continue with degraded functionality")
        print("  4. Fail workflow")
        
        while True:
            try:
                choice = input("\nSelect recovery action (1-4): ").strip()
                if choice == "1":
                    return "retry"
                elif choice == "2":
                    return "skip"
                elif choice == "3":
                    return "continue"
                elif choice == "4":
                    return "fail"
                else:
                    print("Invalid choice. Please enter 1-4.")
            except (EOFError, KeyboardInterrupt):
                # Non-interactive fallback
                return "fail"
    
    def get_recovery_summary(self) -> dict[str, Any]:
        """
        Get summary of recovery actions taken.
        
        Returns:
            Dictionary with recovery summary statistics
        """
        total = len(self.recovery_actions)
        retries = sum(1 for a in self.recovery_actions if a.get("recovery_action") == "retry")
        skips = sum(1 for a in self.recovery_actions if a.get("recovery_action") == "skip")
        continues = sum(1 for a in self.recovery_actions if a.get("recovery_action") == "continue")
        failures = sum(1 for a in self.recovery_actions if a.get("recovery_action") == "fail")
        
        return {
            "total_recoveries": total,
            "retries": retries,
            "skips": skips,
            "continues": continues,
            "failures": failures,
            "actions": self.recovery_actions,
        }
