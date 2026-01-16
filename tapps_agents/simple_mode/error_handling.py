"""
Error Handling for Simple Mode.

Provides friendly error messages, automatic recovery strategies, and help suggestions
to make Simple Mode more user-friendly when things go wrong.
"""

from pathlib import Path
from typing import Any

from ..cli.feedback import get_feedback
from ..core.unicode_safe import safe_print


class SimpleModeErrorHandler:
    """Handles errors in Simple Mode with friendly messages and recovery suggestions."""

    ERROR_TEMPLATES = {
        "config_not_found": {
            "message": "Simple Mode configuration not found",
            "suggestion": "Run 'tapps-agents simple-mode init' to set up Simple Mode",
            "recovery": "auto_init",
        },
        "intent_parsing_failed": {
            "message": "Could not understand your command",
            "suggestion": "Try using keywords like 'build', 'review', 'fix', or 'test'",
            "recovery": "suggest_alternatives",
        },
        "file_not_found": {
            "message": "File or directory not found",
            "suggestion": "Check that the file path is correct and the file exists",
            "recovery": "check_path",
        },
        "workflow_failed": {
            "message": "Workflow execution failed",
            "suggestion": "Check the error details above and try again",
            "recovery": "retry_with_details",
        },
        "agent_unavailable": {
            "message": "Required agent is not available",
            "suggestion": "Verify your project configuration and agent setup",
            "recovery": "check_config",
        },
        "permission_denied": {
            "message": "Permission denied",
            "suggestion": "Check file permissions and try again",
            "recovery": "check_permissions",
        },
        "invalid_config": {
            "message": "Invalid configuration",
            "suggestion": "Run 'tapps-agents simple-mode configure' to fix settings",
            "recovery": "run_config_wizard",
        },
        "path_validation_error": {
            "message": "Path validation failed - Windows absolute path detected",
            "suggestion": "Use relative paths or run from project root",
            "recovery": "normalize_path",
        },
        "windows_path_error": {
            "message": "Windows absolute path detected",
            "suggestion": "Convert to relative path or use Cursor Skills",
            "recovery": "suggest_cursor_skills",
        },
    }

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.feedback = get_feedback()

    def handle_error(
        self,
        error_code: str,
        error_message: str | None = None,
        context: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """
        Handle an error with friendly messaging and recovery suggestions.

        Args:
            error_code: Error code identifier
            error_message: Optional custom error message
            context: Additional context about the error
            original_exception: Original exception if available
        """
        template = self.ERROR_TEMPLATES.get(error_code, {})
        
        message = error_message or template.get("message", "An error occurred")
        suggestion = template.get("suggestion", "Please check the error and try again")
        recovery = template.get("recovery", "none")

        # Display friendly error message (using safe_print for Windows Unicode compatibility)
        safe_print("\n" + "=" * 70)
        safe_print("❌ Error")
        safe_print("=" * 70)
        safe_print(f"\n{message}")

        if context:
            safe_print("\nDetails:")
            for key, value in context.items():
                safe_print(f"  • {key}: {value}")

        if original_exception:
            safe_print(f"\nTechnical details: {str(original_exception)}")

        safe_print(f"\n💡 {suggestion}")

        # Attempt automatic recovery if possible
        if recovery != "none":
            self._attempt_recovery(recovery, error_code, context)

        safe_print("=" * 70)
        safe_print()

    def _attempt_recovery(
        self, recovery_strategy: str, error_code: str, context: dict[str, Any] | None
    ) -> None:
        """Attempt automatic recovery based on strategy."""
        if recovery_strategy == "auto_init":
            safe_print("\n🔄 Attempting automatic recovery...")
            safe_print("   Would you like to run the setup wizard? (This is a placeholder)")
            # In a real implementation, this could prompt the user or auto-run init

        elif recovery_strategy == "suggest_alternatives":
            safe_print("\n💡 Common command patterns:")
            safe_print("   • Build: 'build a user API', 'create a new feature'")
            safe_print("   • Review: 'review my code', 'check quality of auth.py'")
            safe_print("   • Fix: 'fix the error', 'debug the issue'")
            safe_print("   • Test: 'add tests', 'generate tests for service.py'")

        elif recovery_strategy == "check_path":
            if context and "file_path" in context:
                file_path = Path(context["file_path"])
                if not file_path.is_absolute():
                    # Try relative to project root
                    abs_path = self.project_root / file_path
                    if abs_path.exists():
                        safe_print(f"\n💡 Found file at: {abs_path}")
                    else:
                        safe_print(f"\n💡 Searched for: {abs_path} (not found)")

        elif recovery_strategy == "retry_with_details":
            safe_print("\n💡 Try running with more details:")
            safe_print("   • Check the workflow logs in .tapps-agents/workflow-state/")
            safe_print("   • Run 'tapps-agents simple-mode status' to verify configuration")

        elif recovery_strategy == "check_config":
            safe_print("\n💡 Configuration check:")
            safe_print("   • Run 'tapps-agents simple-mode status'")
            safe_print("   • Verify agents are properly installed")

        elif recovery_strategy == "check_permissions":
            if context and "file_path" in context:
                file_path = Path(context["file_path"])
                if file_path.exists():
                    safe_print(f"\n💡 File exists but may not be readable/writable")
                    safe_print(f"   Path: {file_path}")
                    safe_print(f"   Try: chmod +rw {file_path}")

        elif recovery_strategy == "run_config_wizard":
            safe_print("\n💡 Run the configuration wizard:")
            safe_print("   tapps-agents simple-mode configure")

        elif recovery_strategy == "normalize_path":
            safe_print("\n💡 Path normalization suggestions:")
            safe_print("   • Use relative paths: 'src/file.py' instead of 'c:/project/src/file.py'")
            safe_print("   • Run commands from project root directory")
            safe_print("   • Paths are automatically normalized - try again")
            if context and "received_path" in context:
                safe_print(f"\n   Received: {context['received_path']}")
            if context and "project_root" in context:
                safe_print(f"   Project root: {context['project_root']}")

        elif recovery_strategy == "suggest_cursor_skills":
            safe_print("\n💡 Alternative execution methods:")
            safe_print("   • Use Cursor Skills directly: @simple-mode *build 'description'")
            safe_print("   • Use relative paths in CLI commands")
            safe_print("   • Path normalization is automatic - the error should be resolved")

    def format_friendly_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> str:
        """
        Format an exception into a friendly error message.

        Args:
            error: The exception that occurred
            context: Additional context

        Returns:
            Friendly error message string
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Map common exceptions to friendly messages
        friendly_messages = {
            "FileNotFoundError": "File not found",
            "PermissionError": "Permission denied",
            "ValueError": "Invalid value or configuration",
            "KeyError": "Missing required configuration",
            "AttributeError": "Configuration error",
        }

        friendly_type = friendly_messages.get(error_type, "An error occurred")

        message = f"{friendly_type}: {error_message}"

        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            message += f" (Context: {context_str})"

        return message

    def get_help_suggestions(self, error_code: str) -> list[str]:
        """
        Get help suggestions for a specific error code.

        Args:
            error_code: Error code identifier

        Returns:
            List of help suggestion strings
        """
        suggestions = {
            "config_not_found": [
                "Run 'tapps-agents simple-mode init' to set up Simple Mode",
                "Check that you're in a project directory",
                "Verify .tapps-agents/config.yaml exists",
            ],
            "intent_parsing_failed": [
                "Use explicit keywords: build, review, fix, test",
                "Be more specific about what you want to do",
                "Check command variations in docs/SIMPLE_MODE_GUIDE.md",
            ],
            "file_not_found": [
                "Verify the file path is correct",
                "Check that you're in the right directory",
                "Use absolute paths if relative paths don't work",
            ],
            "workflow_failed": [
                "Check workflow logs for details",
                "Verify all required agents are available",
                "Try a simpler command first",
            ],
            "path_validation_error": [
                "Use relative paths instead of absolute paths",
                "Run commands from project root directory",
                "Paths are automatically normalized - try again",
            ],
            "windows_path_error": [
                "Use Cursor Skills: @simple-mode *build 'description'",
                "Use relative paths in CLI commands",
                "Path normalization handles this automatically",
            ],
        }

        return suggestions.get(error_code, ["Check the error message and try again"])

