"""
Simple Mode command handlers.
"""

import sys
import yaml
from pathlib import Path

from ...core.config import ProjectConfig, load_config, save_config
from ...simple_mode.error_handling import SimpleModeErrorHandler
from ...simple_mode.learning_progression import LearningProgressionTracker
from ...simple_mode.onboarding import OnboardingWizard
from ...simple_mode.zero_config import ZeroConfigMode
from ...workflow.executor import WorkflowExecutor
from ...workflow.preset_loader import PresetLoader
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
    elif command == "full":
        handle_simple_mode_full(args)
    else:
        feedback = get_feedback()
        feedback.error(
            "Invalid simple-mode command",
            error_code="invalid_command",
            context={"command": command},
            remediation="Use: on, off, status, init, configure, progress, or full",
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
    feedback.running("Loading configuration...", step=2, total_steps=3)
    config = load_config(config_path)
    config.simple_mode.enabled = True

    # Save config
    feedback.running("Saving configuration...", step=3, total_steps=3)
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
    feedback.start_operation("Disable Simple Mode", "Disabling Simple Mode in configuration")

    # Find config file
    feedback.running("Locating configuration file...", step=1, total_steps=3)
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

    feedback.start_operation("Simple Mode Status", "Checking Simple Mode configuration status")
    feedback.running("Loading configuration...", step=1, total_steps=2)

    # Find config file
    config_path = find_config_file()
    if not config_path:
        # No config file - use defaults
        config = ProjectConfig()
    else:
        feedback.running("Loading configuration...", step=2, total_steps=2)
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


def handle_simple_mode_full(args: object) -> None:
    """Handle simple-mode full command - runs full lifecycle workflow with testing and loopbacks."""
    feedback = get_feedback()
    feedback.start_operation("Starting Simple Full Lifecycle Workflow")
    
    # Load the simple-full workflow preset
    loader = PresetLoader()
    workflow = loader.load_preset("simple-full")
    
    if not workflow:
        feedback.error(
            "Workflow not found",
            error_code="workflow_not_found",
            context={"preset": "simple-full"},
            remediation="Ensure simple-full.yaml exists in workflows/presets/",
            exit_code=1,
        )
        return
    
    print(f"\n{'='*60}")
    print(f"Starting: {workflow.name}")
    print(f"{'='*60}")
    print(f"Description: {workflow.description}")
    print(f"Steps: {len(workflow.steps)}")
    print("\nThis workflow includes:")
    print("  • Full SDLC lifecycle (requirements -> implementation -> testing)")
    print("  • Automatic quality gates with scoring")
    print("  • Development loopbacks if scores aren't good enough")
    print("  • Test execution and validation")
    print("  • Security scanning")
    print("  • Documentation generation")
    print()
    
    # Get optional arguments
    target_file = getattr(args, "file", None)
    user_prompt = getattr(args, "prompt", None)
    auto_mode = getattr(args, "auto", False)
    
    # Execute workflow
    executor = WorkflowExecutor(auto_detect=False, auto_mode=auto_mode)
    
    if user_prompt:
        executor.user_prompt = user_prompt
    
    # Check runtime mode
    from ...core.runtime_mode import is_cursor_mode, detect_runtime_mode
    runtime_mode = detect_runtime_mode()
    
    print("Executing workflow steps...")
    print(f"Runtime mode: {runtime_mode.value}")
    
    from ...core.unicode_safe import safe_print
    if is_cursor_mode():
        safe_print("WARNING: Running in Cursor mode - workflow will use Background Agents")
        safe_print("   If auto-execution is disabled, workflow will wait for manual execution")
        safe_print("   To force headless mode: set TAPPS_AGENTS_MODE=headless\n")
    else:
        safe_print("[OK] Running in headless mode - direct execution with terminal output\n")
    
    sys.stdout.flush()
    
    try:
        import asyncio
        state = asyncio.run(executor.execute(workflow=workflow, target_file=target_file))
        
        if state.status == "completed":
            feedback.success("Simple Full Lifecycle Workflow completed successfully")
            print("\n✅ Workflow completed successfully!")
            print(f"\nWorkflow ID: {state.workflow_id}")
            print(f"Steps completed: {len(state.completed_steps)}/{len(workflow.steps)}")
        else:
            feedback.error(
                "Workflow execution failed",
                error_code="workflow_execution_failed",
                context={"status": state.status, "error": state.error if hasattr(state, 'error') else "Unknown error"},
                exit_code=1,
            )
    except Exception as e:
        feedback.error(
            "Workflow execution error",
            error_code="workflow_execution_error",
            context={"error": str(e)},
            exit_code=1,
        )

