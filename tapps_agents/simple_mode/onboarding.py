"""
Guided Onboarding Wizard for Simple Mode.

Provides an interactive onboarding experience for new users, including:
- Project type detection
- First command suggestions
- Live demonstration
- Success celebration
"""

import sys
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig, load_config, save_config
from ..core.project_type_detector import detect_project_type
from ..cli.feedback import get_feedback


class OnboardingWizard:
    """Interactive onboarding wizard for Simple Mode."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.feedback = get_feedback()
        self.config_path = self._find_config_file()

    def _find_config_file(self) -> Path | None:
        """Find .tapps-agents/config.yaml in current or parent directories."""
        current = self.project_root
        for parent in [current] + list(current.parents):
            candidate = parent / ".tapps-agents" / "config.yaml"
            if candidate.exists():
                return candidate
        # Return default path if not found
        return self.project_root / ".tapps-agents" / "config.yaml"

    def run(self) -> None:
        """Run the complete onboarding wizard."""
        self.feedback.start_operation("Simple Mode Onboarding")
        
        try:
            self._welcome()
            self._detect_project()
            self._configure_simple_mode()
            self._suggest_first_command()
            self._show_demo()
            self._celebrate_success()
        except KeyboardInterrupt:
            self.feedback.warning("\n\nOnboarding cancelled by user.")
            sys.exit(0)
        except Exception as e:
            self.feedback.error(
                f"Onboarding failed: {e}",
                error_code="onboarding_error",
                exit_code=1,
            )

    def _welcome(self) -> None:
        """Display welcome message."""
        print("\n" + "=" * 70)
        print(" " * 15 + "Welcome to Simple Mode!")
        print("=" * 70)
        print("\nSimple Mode makes TappsCodingAgents easy to use by:")
        print("  • Understanding natural language commands")
        print("  • Automatically selecting the right agents")
        print("  • Hiding complexity while showcasing power")
        print("\nLet's get you started in just a few steps...\n")

    def _detect_project(self) -> None:
        """Detect project type and display results."""
        self.feedback.info("Step 1: Detecting your project type...")
        
        project_type, confidence, reason = detect_project_type(self.project_root)
        
        if project_type:
            print(f"\n✓ Detected project type: {project_type}")
            print(f"  Confidence: {int(confidence * 100)}%")
            print(f"  Reason: {reason}")
            
            # Store project type for later use
            self.project_type = project_type
            self.project_confidence = confidence
        else:
            print("\n⚠ Could not automatically detect project type.")
            print("  Don't worry! Simple Mode will still work great.")
            self.project_type = None
            self.project_confidence = 0.0
        
        print()

    def _configure_simple_mode(self) -> None:
        """Configure Simple Mode settings."""
        self.feedback.info("Step 2: Configuring Simple Mode...")
        
        # Load or create config
        if self.config_path.exists():
            config = load_config(self.config_path)
        else:
            config = ProjectConfig()
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Enable Simple Mode
        config.simple_mode.enabled = True
        config.simple_mode.auto_detect = True
        config.simple_mode.natural_language = True
        config.simple_mode.show_advanced = False
        
        # Save config
        save_config(self.config_path, config)
        
        print("\n✓ Simple Mode enabled and configured!")
        print(f"  Config saved to: {self.config_path}")
        print()

    def _suggest_first_command(self) -> None:
        """Suggest appropriate first command based on project type."""
        self.feedback.info("Step 3: Suggested first command...")
        
        suggestions = self._get_command_suggestions()
        
        print("\n" + "=" * 70)
        print("Ready to get started? Here are some great first commands:")
        print("=" * 70)
        
        for i, (action, example, description) in enumerate(suggestions, 1):
            print(f"\n{i}. {action.upper()}: {example}")
            print(f"   {description}")
        
        print("\n" + "-" * 70)
        print("💡 Tip: You can use these commands in Cursor chat or CLI:")
        print("   • In Cursor: Just type naturally, like 'Build a user API'")
        print("   • In CLI: tapps-agents simple-mode on (already enabled!)")
        print("-" * 70)
        print()

    def _get_command_suggestions(self) -> list[tuple[str, str, str]]:
        """Get command suggestions based on project type."""
        base_suggestions = [
            (
                "Build",
                "Build a new feature or module",
                "Create new code with automatic planning and implementation",
            ),
            (
                "Review",
                "Review existing code for quality",
                "Check code quality, security, and best practices",
            ),
            (
                "Fix",
                "Fix issues in your code",
                "Debug and resolve problems automatically",
            ),
            (
                "Test",
                "Generate tests for your code",
                "Create comprehensive test coverage",
            ),
        ]
        
        # Customize suggestions based on project type
        if self.project_type == "api-service":
            return [
                (
                    "Build",
                    "Build a new API endpoint",
                    "Create REST endpoints with automatic validation and documentation",
                ),
                (
                    "Review",
                    "Review API security and best practices",
                    "Check for security vulnerabilities and API design issues",
                ),
            ] + base_suggestions[2:]
        elif self.project_type == "web-app":
            return [
                (
                    "Build",
                    "Build a new component or feature",
                    "Create UI components or backend features with full integration",
                ),
                (
                    "Review",
                    "Review code quality and performance",
                    "Check for performance issues and code quality problems",
                ),
            ] + base_suggestions[2:]
        elif self.project_type == "cli-tool":
            return [
                (
                    "Build",
                    "Build a new CLI command",
                    "Create new commands with argument parsing and help text",
                ),
                (
                    "Review",
                    "Review CLI usability and error handling",
                    "Check for user experience issues and error handling",
                ),
            ] + base_suggestions[2:]
        else:
            return base_suggestions

    def _show_demo(self) -> None:
        """Show a live demonstration (simulated)."""
        self.feedback.info("Step 4: Quick demonstration...")
        
        print("\n" + "=" * 70)
        print("Here's how Simple Mode works:")
        print("=" * 70)
        
        demo_examples = [
            ("User says:", "Build a user authentication module"),
            ("Simple Mode:", "✓ Detected: BUILD intent"),
            ("", "  → Planning user stories..."),
            ("", "  → Designing architecture..."),
            ("", "  → Generating code..."),
            ("", "✓ Complete! Created 3 files"),
            ("", ""),
            ("User says:", "Review the security of auth.py"),
            ("Simple Mode:", "✓ Detected: REVIEW intent"),
            ("", "  → Analyzing code quality..."),
            ("", "  → Checking security..."),
            ("", "✓ Review complete! Found 2 issues"),
        ]
        
        for prompt, response in demo_examples:
            if prompt:
                print(f"\n{prompt:20} {response}")
            else:
                print(f"{'':20} {response}")
        
        print("\n" + "-" * 70)
        print("That's it! Simple Mode handles all the complexity for you.")
        print("-" * 70)
        print()

    def _celebrate_success(self) -> None:
        """Display success message and next steps."""
        self.feedback.success("Onboarding complete!")
        
        print("\n" + "=" * 70)
        print(" " * 20 + "🎉 You're all set!")
        print("=" * 70)
        print("\nSimple Mode is now enabled and ready to use!")
        print("\nNext steps:")
        print("  1. Try a command in Cursor chat (e.g., 'Build a new feature')")
        print("  2. Or use the CLI: tapps-agents simple-mode status")
        print("  3. Check out examples: docs/SIMPLE_MODE_GUIDE.md")
        print("\n" + "=" * 70)
        print("\nHappy coding! 🚀\n")

