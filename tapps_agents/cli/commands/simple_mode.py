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
    elif command == "build":
        handle_simple_mode_build(args)
    elif command == "resume":
        handle_simple_mode_resume(args)
    elif command == "enhance":
        handle_simple_mode_enhance(args)
    elif command == "breakdown":
        handle_simple_mode_breakdown(args)
    elif command == "todo":
        handle_simple_mode_todo(args)
    else:
        feedback = get_feedback()
        available_commands = ["on", "off", "status", "init", "configure", "progress", "full", "build", "resume", "enhance", "breakdown", "todo"]
        command_list = ", ".join(available_commands)
        feedback.error(
            f"Invalid simple-mode command: {command or '(none provided)'}",
            error_code="invalid_command",
            context={"command": command, "available_commands": available_commands},
            remediation=f"Use one of: {command_list}",
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


def handle_simple_mode_todo(args: object) -> None:
    """Handle simple-mode todo - forwards to bd. §3.5."""
    from ...beads import is_available, run_bd

    root = Path.cwd()
    if not is_available(root):
        get_feedback().error(
            "bd not found. Install to tools/bd or add bd to PATH. See docs/BEADS_INTEGRATION.md.",
            error_code="bd_not_found",
            exit_code=1,
        )
        return
    bd_args = list(getattr(args, "args", None) or [])
    r = run_bd(root, bd_args, capture_output=False)
    sys.exit(r.returncode if r.returncode is not None else 0)


def handle_simple_mode_enhance(args: object) -> None:
    """Handle simple-mode enhance - @simple-mode *enhance. §3.4."""
    feedback = get_feedback()
    prompt = getattr(args, "prompt", None) or ""
    if not str(prompt).strip():
        feedback.error("Prompt required", error_code="prompt_required", remediation='Use: tapps-agents simple-mode enhance --prompt "your prompt"', exit_code=2)
        return
    feedback.start_operation("Enhance prompt")
    from ...simple_mode.intent_parser import Intent, IntentType
    from ...simple_mode.orchestrators.enhance_orchestrator import EnhanceOrchestrator
    from ...core.config import load_config
    import asyncio

    config = load_config()
    intent = Intent(type=IntentType.ENHANCE, confidence=1.0, parameters={"prompt": str(prompt).strip(), "quick": getattr(args, "quick", False)}, original_input=prompt)
    orch = EnhanceOrchestrator(project_root=Path.cwd(), config=config)
    try:
        r = asyncio.run(orch.execute(intent, intent.parameters))
        feedback.clear_progress()
        if r.get("success"):
            feedback.success("Enhancement complete")
            print(r.get("enhanced_prompt", str(r)))
        else:
            feedback.error(r.get("error", "Unknown error"), error_code="enhance_failed", exit_code=1)
    except Exception as e:
        feedback.error(str(e), error_code="enhance_error", exit_code=1)


def handle_simple_mode_breakdown(args: object) -> None:
    """Handle simple-mode breakdown - @simple-mode *breakdown. §3.4."""
    feedback = get_feedback()
    prompt = getattr(args, "prompt", None) or ""
    if not str(prompt).strip():
        feedback.error("Prompt required", error_code="prompt_required", remediation='Use: tapps-agents simple-mode breakdown --prompt "your goal"', exit_code=2)
        return
    feedback.start_operation("Breakdown tasks")
    from ...simple_mode.intent_parser import Intent, IntentType
    from ...simple_mode.orchestrators.breakdown_orchestrator import BreakdownOrchestrator
    from ...core.config import load_config
    import asyncio

    config = load_config()
    intent = Intent(type=IntentType.BREAKDOWN, confidence=1.0, parameters={"prompt": str(prompt).strip()}, original_input=prompt)
    orch = BreakdownOrchestrator(project_root=Path.cwd(), config=config)
    try:
        r = asyncio.run(orch.execute(intent, intent.parameters))
        feedback.clear_progress()
        if r.get("success"):
            feedback.success("Breakdown complete")
            print(r.get("plan", r))
        else:
            feedback.error(r.get("error", "Unknown error"), error_code="breakdown_failed", exit_code=1)
    except Exception as e:
        feedback.error(str(e), error_code="breakdown_error", exit_code=1)


def handle_simple_mode_resume(args: object) -> None:
    """Handle simple-mode resume command."""
    feedback = get_feedback()
    feedback.start_operation("Resuming Workflow")

    from ...simple_mode.orchestrators.resume_orchestrator import ResumeOrchestrator
    from ...simple_mode.intent_parser import IntentParser

    # Check for --list flag
    list_workflows = getattr(args, "list", False)
    if list_workflows:
        orchestrator = ResumeOrchestrator(project_root=Path.cwd())
        workflows = orchestrator.list_available_workflows()

        if not workflows:
            feedback.success("No workflows available to resume")
            print("\nNo workflows found with checkpoints.")
            return

        feedback.success(f"Found {len(workflows)} workflow(s) available to resume")
        print(f"\n{'='*60}")
        print("Available Workflows to Resume")
        print(f"{'='*60}\n")

        for wf in workflows:
            print(f"Workflow ID: {wf['workflow_id']}")
            print(f"  Last Step: {wf['last_step']} (Step {wf['last_step_number']})")
            print(f"  Completed: {wf['completed_at']}")
            print()

        return

    # Get workflow_id
    workflow_id = getattr(args, "workflow_id", None)
    if not workflow_id:
        feedback.error(
            "Workflow ID required",
            error_code="workflow_id_required",
            remediation="Provide workflow_id or use --list to see available workflows",
            exit_code=2,
        )
        return

    # Validate if requested
    validate = getattr(args, "validate", False)
    if validate:
        feedback.running("Validating workflow state...", step=1, total_steps=2)

    # Resume workflow
    feedback.running(f"Resuming workflow: {workflow_id}...", step=2, total_steps=2)

    try:
        orchestrator = ResumeOrchestrator(project_root=Path.cwd())
        parser = IntentParser()
        intent = parser.parse(f"resume {workflow_id}")

        import asyncio

        result = asyncio.run(orchestrator.execute(intent, {"workflow_id": workflow_id}))

        feedback.clear_progress()
        feedback.success(f"Workflow {workflow_id} ready to resume")

        print(f"\n{'='*60}")
        print(f"Resume Workflow: {workflow_id}")
        print(f"{'='*60}")
        print(f"Resume from: Step {result['resume_step']}")
        print(f"Completed steps: {', '.join(map(str, result['completed_steps']))}")
        print(f"Last checkpoint: {result['checkpoint']['step_name']}")
        print(f"\n{result['message']}")
        print("\nNote: Resume execution logic will be integrated with BuildOrchestrator")

    except Exception as e:
        feedback.clear_progress()
        feedback.error(
            f"Failed to resume workflow: {e}",
            error_code="resume_failed",
            context={"workflow_id": workflow_id},
            remediation="Check that workflow_id exists and checkpoints are valid",
            exit_code=1,
        )


def handle_simple_mode_build(args: object) -> None:
    """Handle simple-mode build command - runs build workflow for new features."""
    feedback = get_feedback()
    feedback.start_operation("Starting Simple Mode Build Workflow")
    
    # Validate arguments before execution
    from ..validators.command_validator import CommandValidator
    from ..utils.error_formatter import ErrorFormatter
    
    validator = CommandValidator()
    validation_result = validator.validate_build_command(args)
    
    if not validation_result.valid:
        formatter = ErrorFormatter()
        error_msg = formatter.format_validation_error(validation_result)
        feedback.error(
            "Command validation failed",
            error_code="validation_error",
            context={"errors": validation_result.errors},
            remediation=validation_result.suggestions[0] if validation_result.suggestions else "Check command arguments",
            exit_code=2,
        )
        # Print detailed error message
        print("\n" + error_msg, file=sys.stderr)
        return
    
    # Get arguments (validated)
    user_prompt = getattr(args, "prompt", None)
    target_file = getattr(args, "file", None)
    fast_mode = getattr(args, "fast", False)
    preset_arg = getattr(args, "preset", None)
    auto_mode = getattr(args, "auto", False)

    # Auto-suggest preset from scope when neither --fast nor --preset set (SIMPLE_MODE_FEEDBACK_REVIEW)
    if not fast_mode and preset_arg is None and user_prompt:
        from ...simple_mode.workflow_suggester import WorkflowSuggester
        suggester = WorkflowSuggester()
        suggested = suggester.suggest_build_preset(user_prompt)
        if suggested == "minimal":
            fast_mode = True
            preset_arg = "minimal"
        else:
            preset_arg = suggested
        # Log without prompting user
        if preset_arg:
            feedback.info(f"Preset auto-selected from scope: {preset_arg}")

    # Explicit --preset overrides: minimal => fast_mode
    if preset_arg == "minimal" and not getattr(args, "fast", False):
        fast_mode = True

    print(f"\n{'='*60}")
    print("Simple Mode Build Workflow")
    print(f"{'='*60}")
    print(f"Feature: {user_prompt}")
    if fast_mode:
        print("Mode: Fast (skipping documentation steps 1-4)")
    else:
        print("Mode: Complete (all 7 steps)")
    print()
    
    # Load config
    from ...core.config import load_config
    from ...core.path_normalizer import normalize_for_cli, normalize_project_root
    from ...core.runtime_mode import detect_runtime_mode, is_cursor_mode
    from ...simple_mode.intent_parser import Intent, IntentParser, IntentType
    from ...simple_mode.orchestrators.build_orchestrator import BuildOrchestrator
    
    config = load_config()
    project_root = normalize_project_root(Path.cwd())
    
    # Normalize target file path if provided
    if target_file:
        try:
            target_file = normalize_for_cli(target_file, project_root)
        except Exception as e:
            feedback.warning(f"Path normalization warning: {e}. Using path as-is.")
            # Continue with original path - let workflow executor handle it
    
    # Create intent
    parser = IntentParser()
    intent = Intent(
        type=IntentType.BUILD,
        confidence=1.0,
        parameters={"description": user_prompt, "file": target_file},
        original_input=user_prompt,
    )
    
    # Initialize orchestrator
    orchestrator = BuildOrchestrator(
        project_root=project_root,
        config=config,
    )
    
    # Check runtime mode
    runtime_mode = detect_runtime_mode()
    feedback.clear_progress()
    
    # Workflow preview (if not auto mode)
    if not auto_mode:
        print("\n" + "=" * 60)
        print("Workflow Preview")
        print("=" * 60)
        print(f"Feature: {user_prompt}")
        print(f"Mode: {'Fast' if fast_mode else 'Complete'} ({'4' if fast_mode else '7'} steps)")
        print("\nSteps to Execute:")
        if fast_mode:
            steps = [
                (5, "Implement code", "~5s"),
                (6, "Review code quality", "~2s"),
                (7, "Generate tests", "~2s"),
            ]
        else:
            steps = [
                (1, "Enhance prompt (requirements analysis)", "~2s"),
                (2, "Create user stories", "~2s"),
                (3, "Design architecture", "~3s"),
                (4, "Design API/data models", "~3s"),
                (5, "Implement code", "~5s"),
                (6, "Review code quality", "~2s"),
                (7, "Generate tests", "~2s"),
            ]
        for step_num, step_name, est_time in steps:
            print(f"  {step_num}. {step_name:<45} {est_time}")
        total_est = sum(float(s[2].replace("~", "").replace("s", "")) for s in steps)
        print(f"\nEstimated Total Time: ~{total_est:.0f}s")
        print(f"Configuration: automation.level=2, fast_mode={str(fast_mode).lower()}")
        print("\n" + "=" * 60)
        sys.stdout.flush()
    
    print("\nExecuting build workflow...")
    print(f"Runtime mode: {runtime_mode.value}")
    print(f"Auto-execution: {'enabled' if auto_mode else 'disabled'}")
    
    from ...core.unicode_safe import safe_print
    if is_cursor_mode():
        safe_print("[OK] Running in Cursor mode - using direct execution\n")
    else:
        safe_print("[OK] Running in headless mode - direct execution with terminal output\n")
    
    sys.stdout.flush()
    
    # Initialize status reporter
    from ..utils.status_reporter import StatusReporter
    total_steps = 4 if fast_mode else 7
    status_reporter = StatusReporter(total_steps=total_steps)
    
    # Define callbacks for real-time status reporting
    def on_step_start(step_num: int, step_name: str) -> None:
        """Callback when a step starts."""
        status_reporter.start_step(step_num, step_name)
    
    def on_step_complete(step_num: int, step_name: str, status: str) -> None:
        """Callback when a step completes."""
        status_reporter.complete_step(step_num, step_name, status)
    
    def on_step_error(step_num: int, step_name: str, error: Exception) -> None:
        """Callback when a step errors."""
        status_reporter.complete_step(step_num, step_name, "failed")
    
    try:
        import asyncio
        
        result = asyncio.run(
            orchestrator.execute(
                intent=intent,
                parameters=intent.parameters,
                fast_mode=fast_mode,
                on_step_start=on_step_start,
                on_step_complete=on_step_complete,
                on_step_error=on_step_error,
            )
        )
        
        # Print execution summary
        status_reporter.print_summary()
        
        if result.get("success", False):
            feedback.success("Simple Mode Build Workflow completed successfully")
            print("\n✅ Build workflow completed successfully!")
            if "workflow_id" in result:
                print(f"\nWorkflow ID: {result['workflow_id']}")
            if "steps_executed" in result:
                print(f"Steps executed: {len(result['steps_executed'])}")
        else:
            feedback.error(
                "Build workflow execution failed",
                error_code="build_workflow_failed",
                context={"error": result.get("error", "Unknown error")},
                exit_code=1,
            )
    except Exception as e:
        feedback.error(
            "Build workflow execution error",
            error_code="build_workflow_error",
            context={"error": str(e)},
            exit_code=1,
        )


def handle_simple_mode_full(args: object) -> None:
    """Handle simple-mode full command - runs the Full SDLC workflow (requirements -> security -> docs)."""
    feedback = get_feedback()
    feedback.start_operation("Starting Full SDLC Workflow")
    
    # Load the full SDLC workflow preset (matches docs: @simple-mode *full)
    loader = PresetLoader()
    workflow = loader.load_preset("full-sdlc")
    
    if not workflow:
        feedback.error(
            "Workflow not found",
            error_code="workflow_not_found",
            context={"preset": "full-sdlc"},
            remediation="Ensure full-sdlc.yaml exists in workflows/presets/",
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
    
    # Execute with auto_mode
    executor = WorkflowExecutor(auto_detect=False, auto_mode=auto_mode)
    
    if user_prompt:
        executor.user_prompt = user_prompt
    
    # Check runtime mode
    from ...core.runtime_mode import is_cursor_mode, detect_runtime_mode
    runtime_mode = detect_runtime_mode()
    
    # Stop spinner before async execution (spinner may interfere with async)
    feedback.clear_progress()
    
    print("Executing workflow steps...")
    print(f"Runtime mode: {runtime_mode.value}")
    print(f"Auto-execution: {'enabled' if auto_mode else 'disabled'}")
    
    from ...core.unicode_safe import safe_print
    if is_cursor_mode():
        safe_print("[OK] Running in Cursor mode - using direct execution and Cursor Skills\n")
    else:
        safe_print("[OK] Running in headless mode - direct execution with terminal output\n")
    
    sys.stdout.flush()
    
    try:
        import asyncio
        state = asyncio.run(executor.execute(workflow=workflow, target_file=target_file))
        
        if state.status == "completed":
            feedback.success("Full SDLC Workflow completed successfully")
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
    except TimeoutError as e:
        feedback.error(
            "Workflow timeout",
            error_code="workflow_timeout",
            context={"error": str(e)},
            remediation="Increase timeout in config (workflow.timeout_seconds) or check for blocking operations",
            exit_code=1,
        )
    except Exception as e:
        feedback.error(
            "Workflow execution error",
            error_code="workflow_execution_error",
            context={"error": str(e)},
            exit_code=1,
        )

