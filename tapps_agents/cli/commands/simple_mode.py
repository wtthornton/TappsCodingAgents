"""
Simple Mode command handlers.
"""

import yaml
from pathlib import Path

from ...core.config import ProjectConfig, load_config, save_config
from ...simple_mode.error_handling import SimpleModeErrorHandler
from ...simple_mode.learning_progression import LearningProgressionTracker
from ...simple_mode.onboarding import OnboardingWizard
from ...simple_mode.zero_config import ZeroConfigMode
from ..feedback import get_feedback


def handle_simple_mode_command(args: object) -> None:
    """Handle simple-mode command."""
    command = getattr(args, "command", None)

    if command == "on":
        handle_simple_mode_on()
    elif command == "off":
        handle_simple_mode_off()
    elif command == "status":
        handle_simple_mode_status(args)
    elif command == "init":
        handle_simple_mode_init()
    elif command == "configure" or command == "config":
        handle_simple_mode_configure()
    elif command == "progress":
        handle_simple_mode_progress()
    else:
        feedback = get_feedback()
        feedback.error(
            "Invalid simple-mode command",
            error_code="invalid_command",
            context={"command": command},
            remediation="Use: on, off, status, init, configure, or progress",
            exit_code=2,
        )


def handle_simple_mode_on() -> None:
    """Enable Simple Mode."""
    feedback = get_feedback()
    error_handler = SimpleModeErrorHandler()
    feedback.start_operation("Enabling Simple Mode")

    # Find config file
    config_path = find_config_file()
    if not config_path:
        error_handler.handle_error(
            "config_not_found",
            error_message="No config file found",
            context={"suggestion": "Run 'tapps-agents init' first"},
        )
        feedback.error(
            "No config file found",
            error_code="config_not_found",
            remediation="Run 'tapps-agents init' first",
            exit_code=2,
        )

    # Load config
    config = load_config(config_path)
    config.simple_mode.enabled = True

    # Save config
    save_config(config_path, config)

    feedback.clear_progress()
    feedback.success("Simple Mode enabled")
    print("\nSimple Mode is now enabled.")
    print("You can use natural language commands like:")
    print("  • 'Build a user authentication feature'")
    print("  • 'Review my authentication code'")
    print("  • 'Fix the error in auth.py'")
    print("  • 'Add tests for service.py'")


def handle_simple_mode_off() -> None:
    """Disable Simple Mode."""
    feedback = get_feedback()
    error_handler = SimpleModeErrorHandler()
    feedback.start_operation("Disabling Simple Mode")

    # Find config file
    config_path = find_config_file()
    if not config_path:
        error_handler.handle_error(
            "config_not_found",
            error_message="No config file found",
            context={"suggestion": "Run 'tapps-agents init' first"},
        )
        feedback.error(
            "No config file found",
            error_code="config_not_found",
            remediation="Run 'tapps-agents init' first",
            exit_code=2,
        )

    # Load config
    config = load_config(config_path)
    config.simple_mode.enabled = False

    # Save config
    save_config(config_path, config)

    feedback.clear_progress()
    feedback.success("Simple Mode disabled")
    print("\nSimple Mode is now disabled.")
    print("You can use agent-specific commands like:")
    print("  • @reviewer *review")
    print("  • @implementer *implement")
    print("  • @tester *test")


def handle_simple_mode_status(args: object) -> None:
    """Check Simple Mode status."""
    feedback = get_feedback()
    output_format = getattr(args, "format", "text")
    feedback.format_type = output_format

    feedback.start_operation("Checking Simple Mode status")

    # Find config file
    config_path = find_config_file()
    if not config_path:
        # No config file - use defaults
        config = ProjectConfig()
    else:
        config = load_config(config_path)

    feedback.clear_progress()

    status = {
        "enabled": config.simple_mode.enabled,
        "auto_detect": config.simple_mode.auto_detect,
        "show_advanced": config.simple_mode.show_advanced,
        "natural_language": config.simple_mode.natural_language,
        "config_file": str(config_path) if config_path else None,
    }

    if output_format == "json":
        feedback.output_result(status, message="Simple Mode status retrieved")
    else:
        feedback.success("Simple Mode status retrieved")
        print("\n" + "=" * 60)
        print("Simple Mode Status")
        print("=" * 60)
        print(f"\nEnabled: {'Yes' if status['enabled'] else 'No'}")
        print(f"Auto-detect: {'Yes' if status['auto_detect'] else 'No'}")
        print(f"Show advanced: {'Yes' if status['show_advanced'] else 'No'}")
        print(f"Natural language: {'Yes' if status['natural_language'] else 'No'}")
        if status["config_file"]:
            print(f"\nConfig file: {status['config_file']}")


def find_config_file() -> Path | None:
    """Find .tapps-agents/config.yaml in current or parent directories."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        candidate = parent / ".tapps-agents" / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def handle_simple_mode_init() -> None:
    """Run the Simple Mode onboarding wizard."""
    wizard = OnboardingWizard()
    wizard.run()


def handle_simple_mode_configure() -> None:
    """Run the Simple Mode configuration wizard."""
    zero_config = ZeroConfigMode()
    zero_config.run_configuration_wizard()


def handle_simple_mode_progress() -> None:
    """Show Simple Mode learning progression."""
    tracker = LearningProgressionTracker()
    tracker.show_progression_indicator()

