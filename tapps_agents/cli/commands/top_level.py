"""
Top-level command handlers (create, init, workflow, score, doctor, hardware-profile, analytics, setup-experts, customize)
"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.cursor_verification import (
    format_verification_results,
    verify_cursor_integration,
)
from ..base import run_async_command
from ..feedback import get_feedback
from .common import format_json_output
from .reviewer import score_command


def hardware_profile_command(
    set_profile: str | None = None,
    output_format: str = "text",
    show_metrics: bool = True,
):
    """
    Check and optionally set hardware profile.
    
    Args:
        set_profile: Optional profile to set (nuc, development, workstation, server, auto)
        output_format: Output format (json or text)
        show_metrics: Whether to show detailed hardware metrics
    """
    from ...core.hardware_profiler import HardwareProfiler
    from ...core.unified_cache_config import UnifiedCacheConfigManager
    
    profiler = HardwareProfiler()
    config_manager = UnifiedCacheConfigManager()
    
    # Get current hardware metrics
    metrics = profiler.get_metrics()
    detected_profile = profiler.detect_profile()
    current_resource_usage = profiler.get_current_resource_usage()
    
    # Get current configuration
    config = config_manager.load()
    configured_profile = config.hardware_profile
    detected_in_config = config.detected_profile
    
    feedback = get_feedback()
    feedback.format_type = output_format
    operation_desc = f"Setting profile to {set_profile}" if set_profile else "Checking hardware profile"
    feedback.start_operation("Hardware Profile", operation_desc)
    
    # If user wants to set a profile
    if set_profile:
        feedback.running("Validating profile...", step=1, total_steps=3)
        # Validate profile
        valid_profiles = ["auto", "nuc", "development", "workstation", "server"]
        if set_profile.lower() not in valid_profiles:
            feedback.error(
                f"Invalid profile '{set_profile}'",
                error_code="validation_error",
                context={"valid_options": valid_profiles},
                remediation=f"Use one of: {', '.join(valid_profiles)}",
                exit_code=2,
            )
        
        # Update configuration
        config.hardware_profile = set_profile.lower()
        if set_profile.lower() == "auto":
            config.hardware_auto_detect = True
            config.detected_profile = detected_profile.value
        else:
            config.hardware_auto_detect = False
            config.detected_profile = set_profile.lower()
        
        feedback.running("Saving configuration...", step=2, total_steps=3)
        config_manager.save(config)
        feedback.running("Configuration saved", step=3, total_steps=3)
        feedback.clear_progress()
        
        summary = {
            "profile_set": set_profile.lower(),
            "detected_profile": detected_profile.value,
        }
        
        if output_format == "json":
            result = {
                "action": "set",
                "profile_set": set_profile.lower(),
                "detected_profile": detected_profile.value,
                "hardware_metrics": {
                    "cpu_cores": metrics.cpu_cores,
                    "ram_gb": round(metrics.ram_gb, 2),
                    "disk_free_gb": round(metrics.disk_free_gb, 2),
                    "disk_total_gb": round(metrics.disk_total_gb, 2),
                    "disk_type": metrics.disk_type,
                    "cpu_arch": metrics.cpu_arch,
                },
                "current_resource_usage": {
                    "cpu_percent": round(current_resource_usage["cpu_percent"], 1),
                    "memory_percent": round(current_resource_usage["memory_percent"], 1),
                    "memory_used_gb": round(current_resource_usage["memory_used_gb"], 2),
                    "memory_available_gb": round(
                        current_resource_usage["memory_available_gb"], 2
                    ),
                    "disk_percent": round(current_resource_usage["disk_percent"], 1),
                    "disk_free_gb": round(current_resource_usage["disk_free_gb"], 2),
                },
            }
            # Merge summary into result
            if summary:
                result = {**result, "summary": summary}
            feedback.output_result(result, message="Hardware profile set successfully")
        else:
            feedback.success("Hardware profile set successfully")
            print(f"\nHardware profile set to: {set_profile.lower()}")
            if set_profile.lower() == "auto":
                print(f"  Auto-detection enabled (detected: {detected_profile.value})")
            else:
                print(f"  Auto-detection disabled (using: {set_profile.lower()})")
            print(f"\nConfiguration saved to: {config_manager.config_path}")
    else:
        # Just show current status
        feedback.running("Retrieving hardware profile information...", step=1, total_steps=2)
        feedback.running("Collecting hardware metrics...", step=2, total_steps=2)
        feedback.clear_progress()
        if output_format == "json":
            result = {
                "detected_profile": detected_profile.value,
                "configured_profile": configured_profile,
                "auto_detect": config.hardware_auto_detect,
                "hardware_metrics": {
                    "cpu_cores": metrics.cpu_cores,
                    "ram_gb": round(metrics.ram_gb, 2),
                    "disk_free_gb": round(metrics.disk_free_gb, 2),
                    "disk_total_gb": round(metrics.disk_total_gb, 2),
                    "disk_type": metrics.disk_type,
                    "cpu_arch": metrics.cpu_arch,
                },
                "current_resource_usage": {
                    "cpu_percent": round(current_resource_usage["cpu_percent"], 1),
                    "memory_percent": round(current_resource_usage["memory_percent"], 1),
                    "memory_used_gb": round(current_resource_usage["memory_used_gb"], 2),
                    "memory_available_gb": round(
                        current_resource_usage["memory_available_gb"], 2
                    ),
                    "disk_percent": round(current_resource_usage["disk_percent"], 1),
                    "disk_free_gb": round(current_resource_usage["disk_free_gb"], 2),
                },
            }
            feedback.output_result(result, message="Hardware profile information retrieved")
        else:
            feedback.success("Hardware profile information retrieved")
            print("\n" + "=" * 60)
            print("Hardware Profile Information")
            print("=" * 60)
            
            print("\nHardware Metrics:")
            print(f"  CPU Cores: {metrics.cpu_cores}")
            print(f"  RAM: {metrics.ram_gb:.2f} GB")
            print(f"  Disk: {metrics.disk_free_gb:.2f} GB free / {metrics.disk_total_gb:.2f} GB total")
            print(f"  Disk Type: {metrics.disk_type.upper()}")
            print(f"  CPU Architecture: {metrics.cpu_arch}")
            
            if show_metrics:
                print("\nCurrent Resource Usage:")
                print(f"  CPU Usage: {current_resource_usage['cpu_percent']:.1f}%")
                print(f"  Memory Usage: {current_resource_usage['memory_percent']:.1f}%")
                print(f"  Memory Used: {current_resource_usage['memory_used_gb']:.2f} GB")
                print(f"  Memory Available: {current_resource_usage['memory_available_gb']:.2f} GB")
                print(f"  Disk Usage: {current_resource_usage['disk_percent']:.1f}%")
                print(f"  Disk Free: {current_resource_usage['disk_free_gb']:.2f} GB")
            
            print("\nProfile Detection:")
            print(f"  Detected Profile: {detected_profile.value.upper()}")
            print(f"  Configured Profile: {configured_profile}")
            print(f"  Auto-Detect: {'Enabled' if config.hardware_auto_detect else 'Disabled'}")
            
            if detected_in_config and detected_in_config != detected_profile.value:
                print(f"  Note: Previously detected profile was {detected_in_config}")
            
            # Show profile descriptions
            print("\nAvailable Profiles:")
            print("  - NUC: Low resources (<=6 cores, <=16GB RAM)")
            print("  - DEVELOPMENT: Medium resources (<=12 cores, <=32GB RAM)")
            print("  - WORKSTATION: High resources (>12 cores, >32GB RAM)")
            print("  - SERVER: Variable resources, usually custom")
            print("  - AUTO: Automatically detect based on hardware")
            
            print("\nTo set a profile, use:")
            print("  tapps-agents hardware-profile --set <profile>")
            print("  (Valid profiles: auto, nuc, development, workstation, server)")


def handle_create_command(args: object) -> None:
    """Handle create command"""
    import os
    from ...workflow.executor import WorkflowExecutor
    from ...workflow.preset_loader import PresetLoader
    from ...core.unicode_safe import safe_print

    feedback = get_feedback()
    loader = PresetLoader()
    workflow_name = getattr(args, "workflow", "full")
    user_prompt = getattr(args, "prompt", "")
    cursor_mode_flag = getattr(args, "cursor_mode", False)

    if not user_prompt:
        feedback.error(
            "Prompt/description required",
            error_code="validation_error",
            remediation="Usage: tapps-agents create \"Your project description\"",
            exit_code=2,
        )

    # Cursor-first default:
    # - Workflows need Cursor Skills/Background Agents to produce artifacts for LLM-driven steps.
    # - Users can still force headless mode by setting TAPPS_AGENTS_MODE=headless explicitly.
    if cursor_mode_flag:
        os.environ["TAPPS_AGENTS_MODE"] = "cursor"
    elif "TAPPS_AGENTS_MODE" not in os.environ:
        os.environ["TAPPS_AGENTS_MODE"] = "cursor"

    if feedback.verbosity.value != "quiet":
        mode = os.environ.get("TAPPS_AGENTS_MODE", "headless")
        if mode == "cursor":
            safe_print("[OK] Cursor-first mode: workflows use Cursor Skills / Background Agents (or file-based Skill commands).")
            safe_print("     To force local-only execution: set TAPPS_AGENTS_MODE=headless (note: LLM steps won't execute without Cursor Skills).")
        else:
            safe_print("[WARN] Headless mode: local-only execution. LLM-driven workflow steps will not auto-generate artifacts without Cursor Skills.")

    try:
        feedback.start_operation("Create Project", f"Creating project with {workflow_name} workflow")
        feedback.running(f"Loading workflow preset: {workflow_name}...", step=1, total_steps=5)
        workflow = loader.load_preset(workflow_name)
        if not workflow:
            feedback.error(
                f"Workflow preset '{workflow_name}' not found",
                error_code="config_error",
                remediation="Use 'tapps-agents workflow list' to see available presets",
                exit_code=3,
            )

        feedback.running(f"Initializing workflow: {workflow.name}...", step=2, total_steps=5)
        feedback.running("Preparing project structure...", step=3, total_steps=5)
        if feedback.verbosity.value == "verbose":
            print(f"\n{'='*60}")
            print(f"Creating Project: {workflow.name}")
            print(f"{'='*60}")
            print(f"Description: {workflow.description}")
            print(f"Your Prompt: {user_prompt}")
            print(f"Steps: {len(workflow.steps)}")
            print("Mode: Auto (fully automated)")
            print(f"Runtime Mode: {os.environ.get('TAPPS_AGENTS_MODE', 'headless')}")
            print()

        # Execute workflow with auto mode and prompt
        executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
        executor.user_prompt = user_prompt

        # Use heartbeat to show continuous progress
        from ..progress_heartbeat import AsyncProgressHeartbeat
        
        async def execute_with_progress():
            heartbeat = AsyncProgressHeartbeat(
                message=f"Executing workflow: {workflow.name}",
                start_delay=1.0,  # Show progress after 1 second
                update_interval=1.0,  # Update every second
            )
            try:
                await heartbeat.start()
                result = await executor.execute(workflow=workflow, target_file=None)
                return result
            finally:
                await heartbeat.stop()
        
        result = asyncio.run(execute_with_progress())

        if result.status == "completed":
            feedback.success("Project created successfully", summary={"timeline": "project-timeline.md", "status": result.status})
            if feedback.verbosity.value != "quiet":
                print(f"\n{'='*60}")
                print("Project created successfully!")
                print(f"{'='*60}")
                print("Timeline: project-timeline.md")
                print(f"Status: {result.status}")
        elif result.status == "failed":
            feedback.error(
                result.error or "Unknown error",
                error_code="execution_error",
                exit_code=1,
            )
        else:
            feedback.warning(f"Workflow status: {result.status}")

    except Exception as e:
        feedback.error(
            f"Error creating project: {e}",
            error_code="execution_error",
            exit_code=1,
        )


def _is_ambiguous(recommendation) -> bool:
    """Check if recommendation is ambiguous (low confidence or multiple valid options)"""
    # Low confidence threshold
    if recommendation.confidence < 0.7:
        return True
    # Multiple alternative workflows might indicate ambiguity
    if len(recommendation.alternative_workflows) > 3:
        return True
    return False


def _ask_clarifying_questions(recommendation, non_interactive: bool) -> dict[str, str]:
    """Ask clarifying questions for ambiguous cases"""
    answers = {}
    
    if non_interactive:
        return answers
    
    print("\n" + "-" * 60)
    print("Clarifying Questions")
    print("-" * 60)
    
    # Question 1: Project scope
    try:
        print("\n1. What is the scope of your change?")
        print("   [1] Bug fix or small feature (< 5 files)")
        print("   [2] New feature or enhancement (5-20 files)")
        print("   [3] Major feature or refactoring (20+ files)")
        print("   [4] Enterprise/compliance work")
        response = input("   Your choice [1-4]: ").strip()
        if response in ("1", "2", "3", "4"):
            answers["scope"] = response
    except (EOFError, KeyboardInterrupt):
        return answers
    
    # Question 2: Time constraint
    try:
        print("\n2. What is your time constraint?")
        print("   [1] Quick fix needed ASAP")
        print("   [2] Standard development timeline")
        print("   [3] No rush, quality is priority")
        response = input("   Your choice [1-3]: ").strip()
        if response in ("1", "2", "3"):
            answers["time_constraint"] = response
    except (EOFError, KeyboardInterrupt):
        return answers
    
    # Question 3: Documentation needs
    try:
        print("\n3. How much documentation is needed?")
        print("   [1] Minimal (code comments only)")
        print("   [2] Standard (README updates)")
        print("   [3] Comprehensive (full docs, architecture)")
        response = input("   Your choice [1-3]: ").strip()
        if response in ("1", "2", "3"):
            answers["documentation"] = response
    except (EOFError, KeyboardInterrupt):
        return answers
    
    return answers


def _refine_recommendation(recommendation, answers: dict[str, str]) -> None:
    """Refine recommendation based on Q&A answers"""
    # This is a simplified refinement - in a full implementation,
    # we would re-run detection with the answers as context
    # For now, we just note the answers for display
    if answers:
        recommendation.characteristics.indicators["qa_answers"] = answers


def _estimate_time(workflow_file: str | None, track) -> str:
    """Estimate time for workflow (simplified heuristic)"""
    if not workflow_file:
        return "Unknown"
    
    # Simple heuristic based on track
    time_estimates = {
        "quick_flow": "5-15 minutes",
        "bmad_method": "15-30 minutes",
        "enterprise": "30-60 minutes",
    }
    
    track_value = track.value if hasattr(track, "value") else str(track)
    return time_estimates.get(track_value, "15-30 minutes")


def handle_workflow_recommend_command(args: object) -> None:
    """Handle workflow recommend command"""
    from ...workflow.recommender import WorkflowRecommender
    
    non_interactive = getattr(args, "non_interactive", False)
    output_format = getattr(args, "format", "text")
    auto_load = getattr(args, "auto_load", False)
    
    try:
        # Initialize recommender
        recommender = WorkflowRecommender()
        
        # Get initial recommendation
        recommendation = recommender.recommend(auto_load=False)
        
        # Check for ambiguity and ask Q&A if needed (Story 33.2)
        is_ambiguous = _is_ambiguous(recommendation)
        qa_answers = {}
        
        if is_ambiguous and not non_interactive:
            qa_answers = _ask_clarifying_questions(recommendation, non_interactive)
            if qa_answers:
                _refine_recommendation(recommendation, qa_answers)
        
        # Calculate time estimate (Story 33.3)
        time_estimate = _estimate_time(recommendation.workflow_file, recommendation.track)
        
        # Format output
        if output_format == "json":
            result = {
                "workflow_file": recommendation.workflow_file,
                "track": recommendation.track.value,
                "confidence": recommendation.confidence,
                "message": recommendation.message,
                "time_estimate": time_estimate,
                "alternative_workflows": recommendation.alternative_workflows,
                "is_ambiguous": is_ambiguous,
                "qa_answers": qa_answers,
                "characteristics": {
                    "project_type": recommendation.characteristics.project_type.value,
                    "workflow_track": recommendation.characteristics.workflow_track.value,
                    "confidence": recommendation.characteristics.confidence,
                },
            }
            print(json.dumps(result, indent=2))
        else:
            # Text output (Story 33.3: Time estimates & alternatives)
            print("\n" + "=" * 60)
            print("Workflow Recommendation")
            print("=" * 60)
            print()
            
            # Enhanced recommendation message (Story 33.4)
            print(recommendation.message)
            print()
            
            # Time estimate
            print(f"⏱️  Estimated Time: {time_estimate} (approximate)")
            print()
            
            # Alternatives with brief comparison (Story 33.3)
            if recommendation.alternative_workflows:
                print("Alternative Workflows:")
                for alt in recommendation.alternative_workflows[:5]:  # Show top 5
                    print(f"  • {alt}")
                print()
            
            # Confirmation prompt (Story 33.4)
            if not non_interactive:
                try:
                    if auto_load and recommendation.workflow_file:
                        response = input("Load recommended workflow? [y/N]: ").strip().lower()
                    else:
                        response = input("Accept this recommendation? [y/N/o] (o=override): ").strip().lower()
                    
                    if response in ("y", "yes"):
                        if auto_load and recommendation.workflow_file:
                            from ...workflow.executor import WorkflowExecutor
                            executor = WorkflowExecutor(auto_detect=False)
                            workflow_path = Path("workflows") / f"{recommendation.workflow_file}.yaml"
                            if workflow_path.exists():
                                workflow = executor.load_workflow(workflow_path)
                                print(f"\n[OK] Loaded workflow: {workflow.name}")
                            else:
                                print(f"\n[WARN] Workflow file not found: {workflow_path}")
                    elif response == "o":
                        # Override: show available workflows
                        print("\nAvailable workflows:")
                        available = recommender.list_available_workflows()
                        for i, wf in enumerate(available[:10], 1):
                            print(f"  [{i}] {wf['name']} - {wf.get('description', 'No description')}")
                        try:
                            choice = input("\nSelect workflow number: ").strip()
                            idx = int(choice) - 1
                            if 0 <= idx < len(available):
                                selected = available[idx]
                                print(f"\n[OK] Selected: {selected['name']}")
                                if auto_load:
                                    workflow_path = Path("workflows") / selected["file"]
                                    if workflow_path.exists():
                                        from ...workflow.executor import (
                                            WorkflowExecutor,
                                        )
                                        executor = WorkflowExecutor(auto_detect=False)
                                        workflow = executor.load_workflow(workflow_path)
                                        print(f"[OK] Loaded workflow: {workflow.name}")
                        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
                            print("\nInvalid selection or cancelled.")
                except (EOFError, KeyboardInterrupt):
                    print("\nCancelled.")
                    sys.exit(0)
    
    except Exception as e:
        print(f"Error getting workflow recommendation: {e}", file=sys.stderr)
        if output_format == "json":
            print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


def handle_workflow_command(args: object) -> None:
    """Handle workflow command"""
    from ...workflow.executor import WorkflowExecutor
    from ...workflow.preset_loader import PresetLoader
    import os

    feedback = get_feedback()
    preset_name = getattr(args, "preset", None)
    
    # Handle state management subcommands (Epic 12)
    if preset_name == "state":
        state_command = getattr(args, "state_command", None)
        if state_command == "list":
            handle_workflow_state_list_command(args)
            return
        elif state_command == "show":
            handle_workflow_state_show_command(args)
            return
        elif state_command == "cleanup":
            handle_workflow_state_cleanup_command(args)
            return
        else:
            feedback.error(
                "Unknown state command. Use 'list', 'show', or 'cleanup'.",
                error_code="validation_error",
                remediation="Use: tapps-agents workflow state list|show|cleanup",
                exit_code=2,
            )
    
    # Handle resume subcommand (Epic 12)
    if preset_name == "resume":
        handle_workflow_resume_command(args)
        return
    
    # Handle recommend subcommand
    if preset_name == "recommend":
        handle_workflow_recommend_command(args)
        return

    loader = PresetLoader()

    if not preset_name or preset_name == "list":
        # List all presets
        feedback.info("Loading workflow presets...")
        presets = loader.list_presets()
        feedback.clear_progress()
        feedback.success("Workflow presets loaded")
        print("\n" + "=" * 60)
        print("Available Workflow Presets")
        print("=" * 60)
        print()

        if presets:
            for _preset_id, preset_info in presets.items():
                print(f"{preset_info['name']}")
                if preset_info.get("description"):
                    print(f"  Description: {preset_info['description']}")
                aliases = preset_info.get("aliases", [])
                if aliases:
                    # Show primary aliases (first 5)
                    primary_aliases = [
                        a
                        for a in aliases
                        if a
                        in [
                            "full",
                            "rapid",
                            "fix",
                            "quality",
                            "hotfix",
                            "enterprise",
                            "feature",
                            "refactor",
                            "improve",
                            "urgent",
                        ]
                    ]
                    if primary_aliases:
                        print(f"  Quick commands: {', '.join(primary_aliases[:5])}")
                print()
        else:
            print("No presets found. Check workflows/presets/ directory.")
            print()

        print("Usage: python -m tapps_agents.cli workflow <alias>")
        print("\nExamples:")
        print("  python -m tapps_agents.cli workflow rapid")
        print("  python -m tapps_agents.cli workflow full")
        print("  python -m tapps_agents.cli workflow fix")
        print("  python -m tapps_agents.cli workflow enterprise")
        print("  python -m tapps_agents.cli workflow feature")
        return

    # Load and execute preset
    try:
        workflow = loader.load_preset(preset_name)
        if not workflow:
            print(f"Error: Preset '{preset_name}' not found.", file=sys.stderr)
            print(
                f"Available presets: {', '.join(loader.list_presets().keys())}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Cursor-first default for workflow execution.
        # Workflows frequently require Cursor Skills to materialize artifacts for LLM-driven steps.
        # Respect explicit user override via TAPPS_AGENTS_MODE.
        if "TAPPS_AGENTS_MODE" not in os.environ:
            os.environ["TAPPS_AGENTS_MODE"] = "cursor"

        print(f"\n{'='*60}")
        print(f"Starting: {workflow.name}")
        print(f"{'='*60}")
        print(f"Description: {workflow.description}")
        print(f"Steps: {len(workflow.steps)}")
        print()

        # Execute workflow (start + run steps until completion)
        executor = WorkflowExecutor(auto_detect=False, auto_mode=getattr(args, "auto", False))
        target_file = getattr(args, "file", None)
        user_prompt = getattr(args, "prompt", None)
        
        # Store prompt in executor state if provided
        if user_prompt:
            executor.user_prompt = user_prompt
        
        # Check runtime mode and warn user
        from ...core.runtime_mode import is_cursor_mode, detect_runtime_mode
        runtime_mode = detect_runtime_mode()
        
        print("Executing workflow steps...")
        print(f"Runtime mode: {runtime_mode.value}")
        
        from ...core.unicode_safe import safe_print
        if is_cursor_mode():
            safe_print("[OK] Cursor-first mode: workflow will use Cursor Skills / Background Agents (or file-based Skill commands).")
            safe_print("     If auto-execution is disabled, workflow will wait for manual execution.\n")
        else:
            safe_print("[WARN] Headless mode: local-only execution. LLM-driven workflow steps will not auto-generate artifacts without Cursor Skills.")
            safe_print("       To enable Cursor-first mode: unset TAPPS_AGENTS_MODE or set TAPPS_AGENTS_MODE=cursor.\n")
        
        sys.stdout.flush()
        
        result = asyncio.run(
            executor.execute(workflow=workflow, target_file=target_file)
        )
        
        # Print intermediate status
        from ...core.unicode_safe import safe_print
        if result.status == "running":
            safe_print(f"\nWorkflow is still running. Current step: {result.current_step}")
        elif result.status == "completed":
            safe_print(f"\n[OK] Workflow completed! Processed {len(result.completed_steps)} steps.")
        elif result.status == "failed":
            safe_print(f"\n[FAIL] Workflow failed: {result.error}")
        sys.stdout.flush()

        if result.status == "completed":
            print(f"\n{'='*60}")
            print("Workflow completed successfully!")
            print(f"{'='*60}")
        elif result.status == "failed":
            print(f"\nError: {result.error or 'Unknown error'}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\nWorkflow status: {result.status}")

    except Exception as e:
        print(f"Error executing workflow: {e}", file=sys.stderr)
        sys.exit(1)


def handle_score_command(args: object) -> None:
    """Handle score command (quick shortcut)"""
    file_path = getattr(args, "file", None)
    if not file_path:
        print("Error: File path required", file=sys.stderr)
        print("Usage: python -m tapps_agents.cli score <file>", file=sys.stderr)
        sys.exit(1)

    output_format = getattr(args, "format", "text")
    asyncio.run(score_command(file_path, output_format=output_format))


def handle_customize_command(args: object) -> None:
    """Handle customize command"""
    from pathlib import Path

    from ...core.customization_template import generate_customization_template

    command = getattr(args, "command", None)
    if command == "init" or command == "generate":
        agent_id = getattr(args, "agent_id", None)
        if not agent_id:
            print("Error: agent_id is required", file=sys.stderr)
            sys.exit(1)

        overwrite = getattr(args, "overwrite", False)
        project_root = Path.cwd()

        try:
            result = generate_customization_template(
                agent_id, project_root, overwrite=overwrite
            )
            if result["success"]:
                print(f"\n{'='*60}")
                print("Customization Template Generated")
                print(f"{'='*60}")
                print(f"Agent ID: {agent_id}")
                print(f"File: {result['file_path']}")
                print("\nNext steps:")
                print(f"  1. Edit {result['file_path']} to customize your agent")
                print("  2. See docs/CUSTOMIZATION_GUIDE.md for examples")
                print("  3. Customizations are gitignored by default")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error generating template: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Unknown customize command", file=sys.stderr)
        sys.exit(1)


def handle_governance_command(args: object) -> None:
    """Handle governance/approval command (Story 28.5)"""
    import json
    import sys
    from pathlib import Path
    
    command = getattr(args, "command", None)
    if not command:
        print("Error: subcommand is required (list, show, approve, reject)", file=sys.stderr)
        sys.exit(1)
    
    project_root = Path.cwd()
    approval_queue_dir = project_root / ".tapps-agents" / "approval_queue"
    
    if command in ["list", "ls"]:
        # List pending approvals
        format_type = getattr(args, "format", "text")
        
        if not approval_queue_dir.exists():
            if format_type == "json":
                print(json.dumps({"requests": []}))
            else:
                print("No pending approval requests.")
            return
        
        requests = []
        for approval_file in approval_queue_dir.glob("*.json"):
            try:
                data = json.loads(approval_file.read_text(encoding="utf-8"))
                if data.get("status") == "pending":
                    requests.append({
                        "id": approval_file.name,
                        "title": data.get("entry", {}).get("title", "Unknown"),
                        "domain": data.get("entry", {}).get("domain", "unknown"),
                        "queued_at": data.get("queued_at", ""),
                    })
            except Exception:
                continue
        
        if format_type == "json":
            print(json.dumps({"requests": requests}, indent=2))
        else:
            if not requests:
                print("No pending approval requests.")
            else:
                print(f"Pending Approval Requests ({len(requests)}):")
                print()
                for req in requests:
                    print(f"  ID: {req['id']}")
                    print(f"  Title: {req['title']}")
                    print(f"  Domain: {req['domain']}")
                    print(f"  Queued: {req['queued_at']}")
                    print()
    
    elif command == "show":
        # Show approval request details
        request_id = getattr(args, "request_id", None)
        if not request_id:
            print("Error: request_id is required", file=sys.stderr)
            sys.exit(1)
        
        # Find the approval file
        approval_file = approval_queue_dir / request_id
        if not approval_file.exists():
            # Try without extension
            approval_file = approval_queue_dir / f"{request_id}.json"
        
        if not approval_file.exists():
            print(f"Error: Approval request '{request_id}' not found", file=sys.stderr)
            sys.exit(1)
        
        try:
            data = json.loads(approval_file.read_text(encoding="utf-8"))
            print(f"Approval Request: {approval_file.name}")
            print("=" * 60)
            print(f"Title: {data.get('entry', {}).get('title', 'Unknown')}")
            print(f"Domain: {data.get('entry', {}).get('domain', 'unknown')}")
            print(f"Source: {data.get('entry', {}).get('source', 'unknown')}")
            print(f"Source Type: {data.get('entry', {}).get('source_type', 'unknown')}")
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Queued At: {data.get('queued_at', 'unknown')}")
            print()
            print("Content Preview:")
            print("-" * 60)
            print(data.get('content_preview', 'No preview available'))
            print()
            print("Metadata:")
            print(json.dumps(data.get('entry', {}).get('metadata', {}), indent=2))
        except Exception as e:
            print(f"Error reading approval request: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif command in ["approve", "accept"]:
        # Approve a request
        request_id = getattr(args, "request_id", None)
        auto_ingest = getattr(args, "auto_ingest", False)
        
        if not request_id:
            print("Error: request_id is required", file=sys.stderr)
            sys.exit(1)
        
        # Find the approval file
        approval_file = approval_queue_dir / request_id
        if not approval_file.exists():
            approval_file = approval_queue_dir / f"{request_id}.json"
        
        if not approval_file.exists():
            print(f"Error: Approval request '{request_id}' not found", file=sys.stderr)
            sys.exit(1)
        
        try:
            data = json.loads(approval_file.read_text(encoding="utf-8"))
            data["status"] = "approved"
            data["approved_at"] = datetime.now().isoformat()
            approval_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            
            print(f"Approved: {data.get('entry', {}).get('title', 'Unknown')}")
            
            if auto_ingest:
                # TODO: Integrate with knowledge ingestion pipeline to auto-ingest
                print("Note: Auto-ingestion not yet implemented. Manually ingest the approved entry.")
        except Exception as e:
            print(f"Error approving request: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif command in ["reject", "deny"]:
        # Reject a request
        request_id = getattr(args, "request_id", None)
        reason = getattr(args, "reason", None)
        
        if not request_id:
            print("Error: request_id is required", file=sys.stderr)
            sys.exit(1)
        
        # Find the approval file
        approval_file = approval_queue_dir / request_id
        if not approval_file.exists():
            approval_file = approval_queue_dir / f"{request_id}.json"
        
        if not approval_file.exists():
            print(f"Error: Approval request '{request_id}' not found", file=sys.stderr)
            sys.exit(1)
        
        try:
            data = json.loads(approval_file.read_text(encoding="utf-8"))
            data["status"] = "rejected"
            data["rejected_at"] = datetime.now().isoformat()
            if reason:
                data["rejection_reason"] = reason
            approval_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            
            print(f"Rejected: {data.get('entry', {}).get('title', 'Unknown')}")
            if reason:
                print(f"Reason: {reason}")
        except Exception as e:
            print(f"Error rejecting request: {e}", file=sys.stderr)
            sys.exit(1)


def handle_auto_execution_command(args: object) -> None:
    """Handle auto-execution monitoring command (Story 7.9)"""
    import json
    import sys
    from pathlib import Path

    command = getattr(args, "command", None)
    if not command:
        print("Error: subcommand is required (status, history, metrics, health, debug)", file=sys.stderr)
        sys.exit(1)

    project_root = Path.cwd()

    if command == "status":
        # Show current execution status
        from ...workflow.execution_metrics import ExecutionMetricsCollector

        format_type = getattr(args, "format", "text")
        workflow_id = getattr(args, "workflow_id", None)

        collector = ExecutionMetricsCollector(project_root=project_root)
        metrics = collector.get_metrics(workflow_id=workflow_id, limit=10)

        if format_type == "json":
            print(json.dumps([m.to_dict() for m in metrics], indent=2))
        else:
            if not metrics:
                print("No recent executions found.")
            else:
                print("Recent Executions:")
                print("-" * 80)
                for metric in metrics:
                    status_icon = "[OK]" if metric.status == "success" else "[FAIL]"
                    print(f"{status_icon} {metric.workflow_id}/{metric.step_id}")
                    print(f"   Command: {metric.command}")
                    print(f"   Status: {metric.status}")
                    print(f"   Duration: {metric.duration_ms:.0f}ms")
                    if metric.retry_count > 0:
                        print(f"   Retries: {metric.retry_count}")
                    print()

    elif command == "history":
        # Show execution history
        from ...workflow.execution_metrics import ExecutionMetricsCollector

        format_type = getattr(args, "format", "text")
        workflow_id = getattr(args, "workflow_id", None)
        limit = getattr(args, "limit", 20)

        collector = ExecutionMetricsCollector(project_root=project_root)
        metrics = collector.get_metrics(workflow_id=workflow_id, limit=limit)

        if format_type == "json":
            print(json.dumps([m.to_dict() for m in metrics], indent=2))
        else:
            if not metrics:
                print("No execution history found.")
            else:
                print(f"Execution History (showing {len(metrics)} most recent):")
                print("=" * 80)
                for metric in metrics:
                    status_icon = "[OK]" if metric.status == "success" else "[FAIL]"
                    print(f"{status_icon} {metric.started_at}")
                    print(f"   Workflow: {metric.workflow_id}")
                    print(f"   Step: {metric.step_id}")
                    print(f"   Command: {metric.command}")
                    print(f"   Status: {metric.status}")
                    print(f"   Duration: {metric.duration_ms:.0f}ms")
                    if metric.error_message:
                        print(f"   Error: {metric.error_message}")
                    print()

    elif command == "metrics":
        # Show metrics summary
        from ...workflow.execution_metrics import ExecutionMetricsCollector

        format_type = getattr(args, "format", "text")

        collector = ExecutionMetricsCollector(project_root=project_root)
        summary = collector.get_summary()

        if format_type == "json":
            print(json.dumps(summary, indent=2))
        else:
            print("Execution Metrics Summary")
            print("=" * 80)
            print(f"Total Executions: {summary['total_executions']}")
            print(f"Success Rate: {summary['success_rate']:.1%}")
            print(f"Average Duration: {summary['average_duration_ms']:.0f}ms")
            print(f"Total Retries: {summary['total_retries']}")
            if summary.get("by_status"):
                print("\nBy Status:")
                for status, count in summary["by_status"].items():
                    if count > 0:
                        print(f"  {status}: {count}")

    elif command == "health":
        # Run health checks
        from ...workflow.health_checker import HealthChecker

        format_type = getattr(args, "format", "text")

        checker = HealthChecker(project_root=project_root)
        results = checker.check_all()
        overall = checker.get_overall_status()

        if format_type == "json":
            print(json.dumps({
                "overall_status": overall,
                "checks": [
                    {
                        "name": r.name,
                        "status": r.status,
                        "message": r.message,
                        "details": r.details,
                    }
                    for r in results
                ],
            }, indent=2))
        else:
            status_icon = "[OK]" if overall == "healthy" else "[WARN]" if overall == "degraded" else "[FAIL]"
            print(f"{status_icon} Overall Status: {overall.upper()}")
            print("=" * 80)
            for result in results:
                icon = "[OK]" if result.status == "healthy" else "[WARN]" if result.status == "degraded" else "[FAIL]"
                print(f"{icon} {result.name}: {result.status.upper()}")
                print(f"   {result.message}")
                if result.details:
                    for key, value in result.details.items():
                        print(f"   {key}: {value}")
                print()

    elif command == "debug":
        # Enable/disable debug mode
        from ...workflow.auto_execution_config import AutoExecutionConfigManager

        action = getattr(args, "action", "status")
        manager = AutoExecutionConfigManager(project_root=project_root)
        manager.load()  # Load config (may be used in future)

        if action == "on":
            # Enable debug logging
            import logging
            logging.getLogger("tapps_agents.workflow").setLevel(logging.DEBUG)
            print("Debug mode enabled (verbose logging)")
        elif action == "off":
            # Disable debug logging
            import logging
            logging.getLogger("tapps_agents.workflow").setLevel(logging.INFO)
            print("Debug mode disabled")
        else:  # status
            # Show debug status
            import logging
            level = logging.getLogger("tapps_agents.workflow").level
            is_debug = level <= logging.DEBUG
            print(f"Debug mode: {'ON' if is_debug else 'OFF'}")
            print(f"Log level: {logging.getLevelName(level)}")

    else:
        print(f"Error: Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


def handle_background_agent_config_command(args: object) -> None:
    """Handle background-agent-config command"""
    from pathlib import Path

    from ...workflow.background_agent_config import (
        BackgroundAgentConfigGenerator,
        BackgroundAgentConfigValidator,
    )

    command = getattr(args, "command", None)
    if not command:
        print("Error: subcommand is required (generate, validate)", file=sys.stderr)
        sys.exit(1)

    config_path = getattr(args, "config_path", None)
    project_root = Path.cwd()

    if command in ["generate", "gen", "init"]:
        # Generate configuration
        template_path = getattr(args, "template", None)
        minimal = getattr(args, "minimal", False)
        overwrite = getattr(args, "overwrite", False)

        generator = BackgroundAgentConfigGenerator(project_root=project_root)
        if config_path:
            generator.config_path = Path(config_path)

        if minimal:
            result = generator.generate_minimal_config(overwrite=overwrite)
        else:
            template_file = Path(template_path) if template_path else None
            result = generator.generate_from_template(
                template_path=template_file, overwrite=overwrite
            )

        if result["success"]:
            print(f"[OK] Configuration file generated: {result['file_path']}")
            if "template_path" in result:
                print(f"  Template: {result['template_path']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)

    elif command in ["validate", "check"]:
        # Validate configuration
        output_format = getattr(args, "format", "text")

        validator = BackgroundAgentConfigValidator()
        if config_path:
            validator.config_path = Path(config_path)

        is_valid, errors = validator.validate()

        if output_format == "json":
            result = {
                "valid": is_valid,
                "config_path": str(validator.config_path),
                "errors": errors,
            }
            print(json.dumps(result, indent=2))
        else:
            if is_valid:
                print(f"[OK] Configuration file is valid: {validator.config_path}")
            else:
                print(f"[ERROR] Configuration file has errors: {validator.config_path}", file=sys.stderr)
                print("\nErrors:", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                sys.exit(1)


def handle_skill_command(args: object) -> None:
    """Handle skill command (validate, template, etc.)"""
    command = getattr(args, "skill_command", None)
    
    if command == "validate":
        handle_skill_validate_command(args)
    elif command == "template":
        handle_skill_template_command(args)
    else:
        print(f"Error: Unknown skill command: {command}", file=sys.stderr)
        print("Available commands: validate, template", file=sys.stderr)
        sys.exit(1)


def handle_skill_validate_command(args: object) -> None:
    """Handle skill validate command"""
    from pathlib import Path

    from ...core.skill_validator import SkillValidator, ValidationSeverity

    project_root = Path.cwd()
    validator = SkillValidator(project_root=project_root)

    skill_path = getattr(args, "skill", None)
    no_warnings = getattr(args, "no_warnings", False)
    output_format = getattr(args, "format", "text")

    # Validate specific skill or all skills
    if skill_path:
        skill_path = Path(skill_path)
        if not skill_path.is_absolute():
            skill_path = project_root / skill_path
        results = [validator.validate_skill(skill_path)]
    else:
        results = validator.validate_all_skills()

    # Filter warnings if requested
    if no_warnings:
        for result in results:
            result.errors = [e for e in result.errors if e.severity != ValidationSeverity.WARNING]

    # Output results
    if output_format == "json":
        output_json(results)
    else:
        output_text(results)

    # Exit with error code if any validation failed
    if any(not r.is_valid for r in results):
        sys.exit(1)


def output_json(results: list) -> None:
    """Output validation results in JSON format."""
    import json

    output = {
        "valid": all(r.is_valid for r in results),
        "results": [
            {
                "skill_path": str(r.skill_path),
                "skill_name": r.skill_name,
                "is_valid": r.is_valid,
                "errors": [
                    {
                        "severity": e.severity.value,
                        "field": e.field,
                        "message": e.message,
                        "suggestion": e.suggestion,
                        "line_number": e.line_number,
                    }
                    for e in r.errors
                ],
            }
            for r in results
        ],
    }
    print(json.dumps(output, indent=2))


def output_text(results: list) -> None:
    """Output validation results in text format."""
    from ...core.skill_validator import ValidationSeverity

    if not results:
        print("No Skills found to validate.")
        return

    print("\n" + "=" * 60)
    print("Custom Skill Validation Results")
    print("=" * 60)
    print()

    all_valid = True
    for result in results:
        print(f"Skill: {result.skill_name or result.skill_path.name}")
        print(f"Path: {result.skill_path}")
        print()

        if result.is_valid and not result.has_warnings():
            print("  [OK] Valid")
        else:
            all_valid = False
            if result.has_errors():
                print("  [FAIL] Errors found:")
                for error in result.errors:
                    if error.severity == ValidationSeverity.ERROR:
                        print(f"    - {error}")
            if result.has_warnings():
                print("  [WARN] Warnings:")
                for error in result.errors:
                    if error.severity == ValidationSeverity.WARNING:
                        print(f"    - {error}")

        print()

    if all_valid:
        print("[OK] All Skills are valid!")
    else:
        print("[FAIL] Some Skills have validation errors.")


def handle_skill_template_command(args: object) -> None:
    """Handle skill-template command"""
    from pathlib import Path

    from ...core.skill_template import create_skill_file

    skill_name = getattr(args, "skill_name", None)
    if not skill_name:
        print("Error: skill_name is required", file=sys.stderr)
        sys.exit(1)

    # Get options
    agent_type = getattr(args, "type", None)
    description = getattr(args, "description", None)
    tools = getattr(args, "tools", None)
    capabilities = getattr(args, "capabilities", None)
    model_profile = getattr(args, "model_profile", None)
    overwrite = getattr(args, "overwrite", False)
    interactive = getattr(args, "interactive", False)

    project_root = Path.cwd()

    # Interactive mode: prompt for options
    if interactive:
        try:
            print("\n" + "=" * 60)
            print("Custom Skill Template Generator (Interactive Mode)")
            print("=" * 60)
            print()

            # Agent type
            if not agent_type:
                print("Available agent types:")
                from ...core.skill_template import AGENT_TYPES
                agent_types_list = AGENT_TYPES
                for i, at in enumerate(agent_types_list, 1):
                    print(f"  [{i}] {at}")
                print("  [0] Custom (no defaults)")
                try:
                    choice = input("\nSelect agent type (0 for custom): ").strip()
                    if choice and choice != "0":
                        idx = int(choice) - 1
                        if 0 <= idx < len(agent_types_list):
                            agent_type = agent_types_list[idx]
                except (ValueError, IndexError, EOFError, KeyboardInterrupt):
                    pass

            # Description
            if not description:
                try:
                    desc_input = input("\nDescription (press Enter for default): ").strip()
                    if desc_input:
                        description = desc_input
                except (EOFError, KeyboardInterrupt):
                    pass

            # Tools
            if not tools:
                print("\nAvailable tools (space-separated, press Enter for defaults):")
                from ...core.skill_template import TOOL_OPTIONS
                tool_options_list = TOOL_OPTIONS
                print(f"  Options: {', '.join(tool_options_list)}")
                try:
                    tools_input = input("Tools: ").strip()
                    if tools_input:
                        tools = tools_input.split()
                except (EOFError, KeyboardInterrupt):
                    pass

            # Capabilities
            if not capabilities:
                print("\nAvailable capabilities (space-separated, press Enter for defaults):")
                from ...core.skill_template import CAPABILITY_CATEGORIES
                capability_categories_list = CAPABILITY_CATEGORIES
                print(f"  Options: {', '.join(capability_categories_list)}")
                try:
                    caps_input = input("Capabilities: ").strip()
                    if caps_input:
                        capabilities = caps_input.split()
                except (EOFError, KeyboardInterrupt):
                    pass

            # Model profile
            if not model_profile:
                try:
                    profile_input = input(f"\nModel profile (press Enter for '{skill_name}_profile'): ").strip()
                    if profile_input:
                        model_profile = profile_input
                except (EOFError, KeyboardInterrupt):
                    pass

        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            sys.exit(0)

    try:
        result = create_skill_file(
            skill_name=skill_name,
            project_root=project_root,
            agent_type=agent_type,
            description=description,
            allowed_tools=tools,
            capabilities=capabilities,
            model_profile=model_profile,
            overwrite=overwrite,
        )

        if result["success"]:
            print(f"\n{'='*60}")
            print("Custom Skill Template Generated")
            print(f"{'='*60}")
            print(f"Skill Name: {skill_name}")
            print(f"File: {result['file_path']}")
            print(f"Directory: {result['skill_dir']}")
            print("\nNext steps:")
            print(f"  1. Edit {result['file_path']} to customize your Skill")
            print("  2. Add any additional files needed for your Skill")
            print("  3. Test your Skill in Cursor")
            print("  4. See docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md for usage")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error generating Skill template: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _print_init_header() -> None:
    """Print initialization header."""
    print("\n" + "=" * 60)
    print("TappsCodingAgents Project Initialization")
    print("=" * 60)
    print()


def _print_init_results(results: dict[str, Any]) -> None:
    """Print initialization results summary."""
    print("Initialization Results:")
    print(f"  Project Root: {results['project_root']}")

    if results["cursor_rules"]:
        print("  Cursor Rules: Created")
        cursor_rules = [
            f for f in results.get("files_created", []) if ".cursor/rules" in f
        ]
        for rule_file in cursor_rules:
            print(f"    - {rule_file}")
    else:
        print("  Cursor Rules: Skipped or already exists")

    if results["workflow_presets"]:
        print(
            "  Workflow Presets: Created "
            f"{len([f for f in results['files_created'] if f.startswith('workflows/presets/')])} file(s)"
        )
    else:
        print("  Workflow Presets: Skipped or already exists")

    if results.get("config"):
        print("  Project Config: Created")
        print("    - .tapps-agents/config.yaml")
        # Show template application info if available
        if results.get("template_applied"):
            template_name = results.get("template_name")
            template_reason = results.get("template_reason", "")
            if template_name:
                print(f"    - Template applied: {template_name}")
                if template_reason:
                    print(f"      ({template_reason})")
        elif results.get("template_name") is not None:
            # Template was selected but not applied (e.g., file not found)
            template_name = results.get("template_name")
            template_reason = results.get("template_reason", "")
            if template_name:
                print(f"    - Template selected: {template_name} (not applied)")
                if template_reason:
                    print(f"      ({template_reason})")
    else:
        print("  Project Config: Skipped or already exists")

    if results.get("skills"):
        print("  Cursor Skills: Installed")
        print("    - .claude/skills/")
    else:
        print("  Cursor Skills: Skipped or already exists")

    if results.get("background_agents"):
        print("  Background Agents: Installed")
        print("    - .cursor/background-agents.yaml")
    else:
        print("  Background Agents: Skipped or already exists")

    if results.get("cursorignore"):
        print("  .cursorignore: Installed")
        print("    - .cursorignore")
    else:
        print("  .cursorignore: Skipped or already exists")
    
    # Show MCP config
    mcp_config = results.get("mcp_config", {})
    if mcp_config.get("created"):
        print("  MCP Config: Created")
        print(f"    - {mcp_config.get('path', '.cursor/mcp.json')}")
        print("    - Context7 MCP server configured (project-local)")
    elif mcp_config.get("path"):
        print("  MCP Config: Already exists")
        print(f"    - {mcp_config.get('path')}")
    
    # Show experts scaffold
    experts_scaffold = results.get("experts_scaffold", {})
    if experts_scaffold.get("created"):
        print("  Experts Scaffold: Created")
        if experts_scaffold.get("domains_md"):
            print(f"    - {experts_scaffold['domains_md']}")
        if experts_scaffold.get("experts_yaml"):
            print(f"    - {experts_scaffold['experts_yaml']}")
        if experts_scaffold.get("knowledge_dir"):
            print(f"    - {experts_scaffold['knowledge_dir']}/")
        print("    - Built-in technical experts are automatically available")
        print("    - Edit these files to add business-domain experts")
    elif experts_scaffold.get("domains_md"):
        print("  Experts Scaffold: Already exists")


def _print_validation_results(validation: dict[str, Any]) -> None:
    """Print validation results."""
    print("\n" + "=" * 60)
    print("Setup Validation")
    print("=" * 60)
    
    if validation.get("overall_valid"):
        print("  Status: [OK] All validations passed")
    else:
        print("  Status: [X] Some validations failed")
    
    # Show errors
    errors = validation.get("errors", [])
    if errors:
        print("\n  Errors:")
        for error in errors:
            print(f"    [X] {error}")
    
    # Show warnings
    warnings = validation.get("warnings", [])
    if warnings:
        print("\n  Warnings:")
        for warning in warnings:
            print(f"    [!] {warning}")
    
    # Show component summary
    verification_results = validation.get("verification_results", {})
    components = verification_results.get("components", {})
    
    print("\n  Summary:")
    if "skills" in components:
        skills_info = components["skills"]
        skills_found = len(skills_info.get("skills_found", []))
        skills_expected = len(skills_info.get("expected_skills", []))
        print(f"    Skills: {skills_found}/{skills_expected} found")
    
    if "rules" in components:
        rules_info = components["rules"]
        rules_found = len(rules_info.get("rules_found", []))
        rules_expected = len(rules_info.get("expected_rules", []))
        print(f"    Rules: {rules_found}/{rules_expected} found")
    
    if "background_agents" in components:
        bg_info = components["background_agents"]
        agents_count = bg_info.get("agents_count", 0)
        print(f"    Background Agents: {agents_count} configured")


def _print_tech_stack(tech_stack: dict[str, Any]) -> None:
    """Print tech stack detection results."""
    print("\n" + "=" * 60)
    print("Tech Stack Detection")
    print("=" * 60)
    
    if tech_stack.get("languages"):
        print(f"  Languages: {', '.join(tech_stack['languages'])}")
    else:
        print("  Languages: None detected")
    
    if tech_stack.get("frameworks"):
        print(f"  Frameworks: {', '.join(tech_stack['frameworks'])}")
    else:
        print("  Frameworks: None detected")
    
    if tech_stack.get("package_managers"):
        print(f"  Package Managers: {', '.join(tech_stack['package_managers'])}")
    else:
        print("  Package Managers: None detected")
    
    if tech_stack.get("libraries"):
        lib_count = len(tech_stack["libraries"])
        print(f"  Libraries Detected: {lib_count}")
        if lib_count > 0 and lib_count <= 20:
            print(f"    {', '.join(tech_stack['libraries'][:20])}")
        elif lib_count > 20:
            print(f"    {', '.join(tech_stack['libraries'][:20])} ...")
            print(f"    (and {lib_count - 20} more)")
    else:
        print("  Libraries Detected: 0")
        print("    Note: No dependency files (requirements.txt, pyproject.toml, package.json) found")
    
    if tech_stack.get("detected_files"):
        print(f"  Detected Files: {', '.join(tech_stack['detected_files'])}")
    else:
        print("  Detected Files: None")


def _print_cache_results(results: dict[str, Any]) -> None:
    """Print cache pre-population results."""
    print("\n" + "=" * 60)
    print("Context7 Cache Pre-population")
    print("=" * 60)
    
    if results.get("cache_prepopulated"):
        cache_result = results.get("cache_result", {})
        cached = cache_result.get("cached", 0)
        total = cache_result.get("total", 0)
        failed = cache_result.get("failed", 0)
        project_libs = cache_result.get("project_libraries", 0)
        expert_libs = cache_result.get("expert_libraries", 0)
        print("  Status: [OK] Success")
        print(f"  Cached Entries: {cached}")
        print(f"  Total Libraries: {total}")
        if project_libs > 0:
            print(f"    - Project Libraries: {project_libs}")
        if expert_libs > 0:
            print(f"    - Built-in Expert Libraries: {expert_libs}")
        if failed > 0:
            print(f"  Failed: {failed}")
        if cache_result.get("errors"):
            error_count = len(cache_result["errors"])
            print(f"  Errors: {error_count} (showing first 5)")
            for error in cache_result["errors"][:5]:
                print(f"    - {error}")
    else:
        # Show why cache prepopulation failed
        cache_result = results.get("cache_result", {})
        cache_error = results.get("cache_error")
        
        if cache_error:
            print("  Status: [FAILED] Failed")
            print(f"  Error: {cache_error}")
            print("  Note: Exception occurred during cache pre-population.")
            print("        Cache pre-population works best when run from within Cursor where MCP servers are available.")
        elif cache_result:
            error_msg = cache_result.get("error") or cache_result.get("message") or "Unknown error"
            print("  Status: [FAILED] Failed")
            print(f"  Error: {error_msg}")
            if cache_result.get("note"):
                print(f"  Note: {cache_result.get('note')}")
            if cache_result.get("cached") == 0 and cache_result.get("total") == 0:
                if not cache_result.get("note"):
                    print("  Note: Context7 may not be enabled in configuration")
                    print("        Check .tapps-agents/config.yaml and ensure context7.enabled: true")
        else:
            print("  Status: [SKIPPED] Skipped")
            print("  Note: Cache pre-population was not attempted")


def _run_environment_check(project_root: str) -> None:
    """Run and display environment diagnostics."""
    print("\n" + "=" * 60)
    print("Environment Check")
    print("=" * 60)
    print()

    try:
        from ...core.doctor import collect_doctor_report
        
        doctor_report = collect_doctor_report(
            project_root=Path(project_root)
        )
        
        # Count findings by severity
        findings = doctor_report.get("findings", [])
        ok_count = sum(1 for f in findings if f.get("severity") == "ok")
        warn_count = sum(1 for f in findings if f.get("severity") == "warn")
        error_count = sum(1 for f in findings if f.get("severity") == "error")
        
        # Show summary
        print(f"Status: {ok_count} OK, {warn_count} warnings, {error_count} errors")
        print()
        
        # Show critical findings (warnings and errors)
        critical_findings = [f for f in findings if f.get("severity") in ("warn", "error")]
        
        if critical_findings:
            print("Findings requiring attention:")
            for f in critical_findings:
                sev = (f.get("severity") or "warn").upper()
                code = f.get("code", "")
                msg = f.get("message", "")
                print(f"  [{sev}] {code}: {msg}")
                remediation = f.get("remediation")
                if remediation:
                    print(f"         -> {remediation}")
            print()
    except Exception as e:
        print(f"  Note: Could not run environment check: {e}")
        print("  Run 'python -m tapps_agents.cli doctor' manually for details.")
        print()


def _print_reset_results(results: dict[str, Any]) -> None:
    """Print reset mode results."""
    print("\n" + "=" * 60)
    print("Reset Mode Results")
    print("=" * 60)
    
    # Version information
    version_before = results.get("version_before")
    version_after = results.get("version_after")
    if version_before and version_after:
        print(f"\nVersion: {version_before} → {version_after}")
        if version_before != version_after:
            print("  ✅ Framework upgraded")
        else:
            print("  ℹ️  Same version (files reset to latest)")
    elif version_after:
        print(f"\nVersion: {version_after} (installed)")
    
    # Files reset
    files_reset = results.get("files_reset", [])
    if files_reset:
        print(f"\n✅ Reset {len(files_reset)} framework files:")
        for file_path in files_reset[:10]:  # Show first 10
            print(f"  • {file_path}")
        if len(files_reset) > 10:
            print(f"  ... and {len(files_reset) - 10} more")
    
    # Custom files preserved
    custom_skills = results.get("custom_skills_preserved", [])
    custom_rules = results.get("custom_rules_preserved", [])
    custom_presets = results.get("custom_presets_preserved", [])
    
    if custom_skills or custom_rules or custom_presets:
        print("\n✅ Preserved custom files:")
        if custom_skills:
            print(f"  • Custom Skills ({len(custom_skills)}): {', '.join(custom_skills)}")
        if custom_rules:
            print(f"  • Custom Rules ({len(custom_rules)}): {', '.join(custom_rules)}")
        if custom_presets:
            print(f"  • Custom Presets ({len(custom_presets)}): {', '.join(custom_presets)}")
    
    # User files preserved
    files_preserved = results.get("files_preserved", [])
    if files_preserved:
        print(f"\n✅ Preserved {len(files_preserved)} user files")
    
    # Backup information
    backup_path = results.get("backup_path")
    if backup_path:
        print(f"\n💾 Backup created: {backup_path}")
        print("  To rollback: tapps-agents init --rollback " + backup_path)
    else:
        print("\n⚠️  No backup created (--no-backup was used)")


def _print_next_steps() -> None:
    """Print next steps instructions."""
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print()
    
    print("In Cursor Chat (Recommended):")
    print("  • Use Simple Mode for natural language commands:")
    print("    @simple-mode *build \"Add user authentication\"")
    print("    @simple-mode *review src/api.py")
    print("    @simple-mode *fix src/buggy.py \"Fix the error\"")
    print("    @simple-mode *test src/service.py")
    print()
    print("  • Use individual agents:")
    print("    @reviewer *score src/main.py")
    print("    @implementer *implement \"Add feature\" src/feature.py")
    print("    @tester *test src/utils.py")
    print()
    
    print("In Terminal/CI:")
    print("  • Run workflow presets:")
    print("    tapps-agents workflow rapid --prompt \"Add feature\" --auto")
    print("    tapps-agents workflow fix --file src/buggy.py --auto")
    print()
    print("  • Use CLI commands:")
    print("    tapps-agents reviewer review src/")
    print("    tapps-agents score src/main.py")
    print()

    print("  • Progress UI (all commands):")
    print("    tapps-agents doctor --progress rich")
    print("    tapps-agents reviewer score src/ --no-progress")
    print("    (Env: TAPPS_PROGRESS=auto|rich|plain|off, TAPPS_NO_PROGRESS=1)")
    print()
    
    print("Setup & Configuration:")
    print("  • Configure experts: tapps-agents setup-experts add")
    print("    (Built-in technical experts are already available)")
    print("  • Verify setup: tapps-agents cursor verify")
    print("  • Environment check: tapps-agents doctor")
    print()
    
    print("Why Init Matters:")
    print("  • Cursor Skills: Enables @agent-name commands in Cursor chat")
    print("  • Cursor Rules: Provides context to AI about your project")
    print("  • Background Agents: Auto-executes quality checks and workflows")
    print("  • Context7 MCP: Library documentation lookup (configured in .cursor/mcp.json)")
    print("  • Experts + RAG: Business-domain knowledge for better code generation")
    print("    - Built-in technical experts: Auto-loaded from tech stack")
    print("    - Project experts: Configure in .tapps-agents/experts.yaml")
    print("    - Knowledge base: Add files in .tapps-agents/knowledge/<domain>/")
    print()


def handle_init_command(args: object) -> None:
    """Handle init command"""
    # Set up Windows encoding for Unicode support
    import os
    if sys.platform == "win32":
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        if hasattr(sys.stderr, 'reconfigure'):
            try:
                sys.stderr.reconfigure(encoding='utf-8')
            except Exception:
                pass
    
    from pathlib import Path
    from ...core.init_project import (
        detect_existing_installation,
        identify_framework_files,
        init_project,
        rollback_init_reset,
    )

    # Handle rollback
    rollback_path = getattr(args, "rollback", None)
    if rollback_path:
        project_root = Path.cwd()
        backup_path = Path(rollback_path)
        if not backup_path.is_absolute():
            backup_path = project_root / backup_path
        
        if not backup_path.exists():
            print(f"Error: Backup path not found: {backup_path}", file=sys.stderr)
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print("Rolling back init reset")
        print(f"{'='*60}")
        print(f"Backup: {backup_path}")
        print()
        
        result = rollback_init_reset(project_root, backup_path)
        
        if result["success"]:
            print(f"✅ Successfully restored {len(result['restored_files'])} files")
            if result["restored_files"]:
                print("\nRestored files:")
                for file_path in result["restored_files"]:
                    print(f"  - {file_path}")
        else:
            print(f"❌ Rollback failed with {len(result['errors'])} errors", file=sys.stderr)
            for error in result["errors"]:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)
        
        return
    
    # Check for existing installation
    project_root = Path.cwd()
    detection = detect_existing_installation(project_root)
    reset_mode = getattr(args, "reset", False) or getattr(args, "upgrade", False)
    dry_run = getattr(args, "dry_run", False)
    auto_yes = getattr(args, "yes", False)
    
    # If existing installation detected and no reset flag, warn user
    if detection["installed"] and not reset_mode and not dry_run:
        print("\n" + "="*60)
        print("⚠️  Existing Installation Detected")
        print("="*60)
        print("\nFound existing tapps-agents installation:")
        for indicator in detection["indicators"]:
            print(f"  • {indicator}")
        print("\nTo upgrade and reset framework files, use:")
        print("  tapps-agents init --reset")
        print("\nOr to preview changes without making them:")
        print("  tapps-agents init --reset --dry-run")
        print("\nProceeding with normal init (will skip existing files)...")
        print()
    
    # Handle dry-run mode
    if dry_run and reset_mode:
        file_identification = identify_framework_files(project_root)
        framework_files = file_identification.get("framework_files", [])
        custom_skills = file_identification.get("custom_skills", [])
        custom_rules = file_identification.get("custom_rules", [])
        custom_presets = file_identification.get("custom_presets", [])
        
        print("\n" + "="*60)
        print("DRY RUN: Reset Preview")
        print("="*60)
        print(f"\nFramework files that would be reset ({len(framework_files)}):")
        for file_path in framework_files[:20]:  # Show first 20
            # Convert Path to relative string for display
            rel_path = file_path.relative_to(project_root) if isinstance(file_path, Path) else file_path
            print(f"  - {rel_path}")
        if len(framework_files) > 20:
            print(f"  ... and {len(framework_files) - 20} more")
        
        print(f"\nCustom files that would be preserved:")
        if custom_skills:
            print(f"  Custom Skills ({len(custom_skills)}): {', '.join(custom_skills)}")
        if custom_rules:
            print(f"  Custom Rules ({len(custom_rules)}): {', '.join(custom_rules)}")
        if custom_presets:
            print(f"  Custom Presets ({len(custom_presets)}): {', '.join(custom_presets)}")
        
        print("\nUser data that would be preserved:")
        print("  • .tapps-agents/config.yaml (user overrides)")
        print("  • .tapps-agents/experts.yaml")
        print("  • .tapps-agents/domains.md")
        print("  • .tapps-agents/knowledge/")
        print("  • .tapps-agents/worktrees/")
        print("  • .tapps-agents/workflow-state/")
        print("  • .tapps-agents/customizations/")
        print("  • .tapps-agents/reports/")
        
        print("\n⚠️  This is a dry run. No changes were made.")
        print("Run without --dry-run to perform the reset.")
        return
    
    # Confirm reset if not auto-yes
    if reset_mode and not auto_yes and not dry_run:
        file_identification = identify_framework_files(project_root)
        framework_files = file_identification.get("framework_files", [])
        
        print("\n" + "="*60)
        print("⚠️  Reset Mode: Framework Files Will Be Reset")
        print("="*60)
        print(f"\nThis will reset {len(framework_files)} framework-managed files to the latest version.")
        print("\nFramework files to reset:")
        for file_path in framework_files[:10]:  # Show first 10
            # Convert Path to relative string for display
            rel_path = file_path.relative_to(project_root) if isinstance(file_path, Path) else file_path
            print(f"  • {rel_path}")
        if len(framework_files) > 10:
            print(f"  ... and {len(framework_files) - 10} more")
        
        print("\nUser data that will be preserved:")
        print("  • Custom Skills, Rules, and Presets")
        print("  • .tapps-agents/config.yaml (user overrides)")
        print("  • .tapps-agents/experts.yaml, domains.md, knowledge/")
        print("  • Workflow state and worktrees")
        
        try:
            response = input("\nContinue with reset? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                print("Reset cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nReset cancelled.")
            return

    _print_init_header()

    results = init_project(
        include_cursor_rules=not getattr(args, "no_rules", False),
        include_workflow_presets=not getattr(args, "no_presets", False),
        include_config=not getattr(args, "no_config", False),
        include_skills=not getattr(args, "no_skills", False),
        include_background_agents=not getattr(args, "no_background_agents", False),
        include_cursorignore=not getattr(args, "no_cursorignore", False),
        pre_populate_cache=not getattr(args, "no_cache", False),
        reset_mode=reset_mode,
        backup_before_reset=not getattr(args, "no_backup", False),
        reset_mcp=getattr(args, "reset_mcp", False),
        preserve_custom=getattr(args, "preserve_custom", True),
    )

    _print_init_results(results)
    
    # Show reset mode results if applicable
    if results.get("reset_mode"):
        _print_reset_results(results)

    # Show validation results
    if results.get("validation"):
        _print_validation_results(results["validation"])
    
    # Show tech stack detection
    if results.get("tech_stack"):
        _print_tech_stack(results["tech_stack"])

    # Show cache pre-population results
    if results.get("cache_prepopulated") is not None:
        _print_cache_results(results)

    # Run environment diagnostics
    _run_environment_check(results["project_root"])

    _print_next_steps()


def handle_generate_rules_command(args: object) -> None:
    """Handle generate-rules command"""
    from pathlib import Path
    from ...workflow.rules_generator import CursorRulesGenerator

    logger_instance = logging.getLogger(__name__)

    print("Generating Cursor Rules documentation...")
    print()

    project_root = Path.cwd()
    output_path = None
    if hasattr(args, "output") and args.output:
        output_path = Path(args.output)

    try:
        generator = CursorRulesGenerator(project_root=project_root)
        result_path = generator.write(
            output_path=output_path,
            backup=not getattr(args, "no_backup", False),
        )

        print(f"✅ Successfully generated Cursor Rules at: {result_path}")
        print()
        print("The workflow-presets.mdc file has been updated with current workflow definitions.")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure workflow YAML files exist in:")
        print("  - workflows/presets/*.yaml (project-specific)")
        print("  - Framework resources (if installed from PyPI)")
        if logger_instance.isEnabledFor(logging.DEBUG):
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error generating rules: {e}")
        import traceback
        if logger_instance.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        sys.exit(1)


def handle_doctor_command(args: object) -> None:
    """Handle doctor command"""
    from ...core.doctor import collect_doctor_report
    
    config_path = getattr(args, "config_path", None)
    report = collect_doctor_report(
        config_path=Path(config_path) if config_path else None
    )

    if getattr(args, "format", "text") == "json":
        format_json_output(report)
    else:
        policy = report.get("policy", {})
        targets = report.get("targets", {})
        print("\n" + "=" * 60)
        print("TappsCodingAgents Doctor Report")
        print("=" * 60)
        print(
            f"\nTargets: python={targets.get('python')} requires={targets.get('python_requires')}"
        )
        print(
            f"Policy: external_tools_mode={policy.get('external_tools_mode')} mypy_staged={policy.get('mypy_staged')}"
        )
        print("\nFindings:")
        missing_tools = []
        for f in report.get("findings", []):
            sev = (f.get("severity") or "warn").upper()
            code = f.get("code") or ""
            msg = f.get("message") or ""
            print(f"  [{sev}] {code}: {msg}")
            remediation = f.get("remediation")
            if remediation:
                print(f"         remediation: {remediation}")
            # Track missing tools for summary
            if code == "TOOL_MISSING":
                tool_name = msg.replace("Tool not found on PATH: ", "")
                missing_tools.append(tool_name)
        
        # Show helpful summary if tools are missing
        if missing_tools:
            print("\n" + "-" * 60)
            print("💡 Quick Fix: Install all missing development tools with:")
            print("   python -m tapps_agents.cli install-dev")
            print("-" * 60)


def handle_install_dev_command(args: object) -> None:
    """Handle install-dev command"""
    import subprocess  # nosec B404

    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"
    is_dev_context = pyproject_path.exists()
    dry_run = getattr(args, "dry_run", False)

    if is_dev_context:
        install_cmd = ['pip', 'install', '-e', '.[dev]']
        context_note = "development context (found pyproject.toml)"
    else:
        install_cmd = ['pip', 'install', 'tapps-agents[dev]']
        context_note = "installed package context"

    print(f"Detected: {context_note}")
    print(f"Command: {' '.join(install_cmd)}")
    
    if dry_run:
        print("\n[DRY RUN] Would run the above command to install:")
        print("  - ruff (code formatting & linting)")
        print("  - mypy (type checking)")
        print("  - pytest (testing framework)")
        print("  - pip-audit (security auditing)")
        print("  - pipdeptree (dependency analysis)")
        print("\nRun without --dry-run to actually install.")
    else:
        print("\nInstalling development tools...")
        try:
            result = subprocess.run(  # nosec B603
                install_cmd,
                check=False,
                capture_output=False,
            )
            if result.returncode == 0:
                print("\n[OK] Development tools installed successfully!")
                print("Run 'python -m tapps_agents.cli doctor' to verify installation.")
            else:
                print(f"\n[FAIL] Installation failed with exit code {result.returncode}")
                sys.exit(1)
        except Exception as e:
            print(f"\n[FAIL] Error installing development tools: {e}")
            sys.exit(1)


def handle_setup_experts_command(args: object) -> None:
    """Handle setup-experts command"""
    from ...experts.setup_wizard import ExpertSetupWizard, NonInteractiveInputRequired

    wizard = ExpertSetupWizard(
        assume_yes=bool(getattr(args, "yes", False)),
        non_interactive=bool(getattr(args, "non_interactive", False)),
    )

    command = getattr(args, "command", None)
    try:
        if command == "init" or command == "initialize":
            wizard.init_project()
        elif command == "add":
            wizard.add_expert()
        elif command == "remove":
            wizard.remove_expert()
        elif command == "list":
            wizard.list_experts()
        else:
            wizard.run_wizard()
    except NonInteractiveInputRequired as e:
        print(
            "Error: Non-interactive mode requires additional input.\n"
            f"Missing input for: {e.question}\n"
            "Tip: Either run interactively (omit --non-interactive) or provide defaults/flags where supported.",
            file=sys.stderr,
        )
        sys.exit(2)


def handle_analytics_command(args: object) -> None:
    """Handle analytics command"""
    from ...core.analytics_dashboard import AnalyticsDashboard

    dashboard = AnalyticsDashboard()
    command = getattr(args, "command", "dashboard")

    if command == "dashboard" or command == "show":
        # Show full dashboard
        data = dashboard.get_dashboard_data()
        if getattr(args, "format", "json") == "json":
            format_json_output(data)
        else:
            # Text format
            print("\n" + "=" * 60)
            print("Analytics Dashboard")
            print("=" * 60)
            print(f"\nSystem Status (as of {data['timestamp']}):")
            sys_data = data["system"]
            print(f"  Total Agents: {sys_data['total_agents']}")
            print(f"  Active Workflows: {sys_data['active_workflows']}")
            print(f"  Completed Today: {sys_data['completed_workflows_today']}")
            print(f"  Failed Today: {sys_data['failed_workflows_today']}")
            print(
                f"  Avg Workflow Duration: {sys_data['average_workflow_duration']:.2f}s"
            )
            print(f"  CPU Usage: {sys_data['cpu_usage']:.1f}%")
            print(f"  Memory Usage: {sys_data['memory_usage']:.1f}%")
            print(f"  Disk Usage: {sys_data['disk_usage']:.1f}%")

            print("\nAgent Performance (Top 10):")
            for agent in sorted(
                data["agents"], key=lambda x: x["total_executions"], reverse=True
            )[:10]:
                print(
                    f"  {agent['agent_name']}: {agent['total_executions']} executions, "
                    f"{agent['success_rate']*100:.1f}% success, "
                    f"{agent['average_duration']:.2f}s avg"
                )

            print("\nWorkflow Performance:")
            for workflow in sorted(
                data["workflows"], key=lambda x: x["total_executions"], reverse=True
            )[:10]:
                print(
                    f"  {workflow['workflow_name']}: {workflow['total_executions']} executions, "
                    f"{workflow['success_rate']*100:.1f}% success"
                )
    elif command == "agents":
        # Show agent metrics
        agent_id = getattr(args, "agent_id", None)
        metrics = dashboard.get_agent_performance(agent_id=agent_id)
        if getattr(args, "format", "json") == "json":
            format_json_output(metrics)
        else:
            for agent in metrics:
                print(
                    f"{agent['agent_name']}: {agent['total_executions']} executions, "
                    f"{agent['success_rate']*100:.1f}% success"
                )
    elif command == "workflows":
        # Show workflow metrics
        workflow_id = getattr(args, "workflow_id", None)
        metrics = dashboard.get_workflow_performance(workflow_id=workflow_id)
        if getattr(args, "format", "json") == "json":
            format_json_output(metrics)
        else:
            for workflow in metrics:
                print(
                    f"{workflow['workflow_name']}: {workflow['total_executions']} executions, "
                    f"{workflow['success_rate']*100:.1f}% success"
                )
    elif command == "trends":
        # Show trends
        metric_type = getattr(args, "metric_type", "agent_duration")
        days = getattr(args, "days", 30)
        trends = dashboard.get_trends(metric_type, days=days)
        if getattr(args, "format", "json") == "json":
            format_json_output(trends)
        else:
            for trend in trends:
                print(f"{trend['metric_name']}: {len(trend['values'])} data points")
    elif command == "system":
        # Show system status
        status = dashboard.get_system_status()
        if getattr(args, "format", "json") == "json":
            format_json_output(status)
        else:
            print(f"System Status (as of {status['timestamp']}):")
            print(f"  Total Agents: {status['total_agents']}")
            print(f"  Active Workflows: {status['active_workflows']}")
            print(f"  Completed Today: {status['completed_workflows_today']}")
            print(f"  Failed Today: {status['failed_workflows_today']}")


# Epic 12: State Management Commands

def handle_workflow_state_list_command(args: object) -> None:
    """Handle 'workflow state list' command (Epic 12)"""
    import json
    from datetime import datetime
    from pathlib import Path

    from ...workflow.state_manager import AdvancedStateManager

    state_dir = Path.cwd() / ".tapps-agents" / "workflow-state"
    manager = AdvancedStateManager(state_dir)
    
    workflow_id = getattr(args, "workflow_id", None)
    output_format = getattr(args, "format", "text")
    
    states = manager.list_states(workflow_id=workflow_id)
    
    if output_format == "json":
        print(json.dumps(states, indent=2, default=str))
        return
    
    # Text format
    if not states:
        print("No workflow states found.")
        return
    
    print(f"\n{'='*80}")
    print("Workflow States")
    print(f"{'='*80}\n")
    
    for state in states:
        workflow_id_val = state.get("workflow_id", "unknown")
        saved_at = state.get("saved_at", "")
        status = state.get("status", "unknown")
        current_step = state.get("current_step", "N/A")
        
        # Format saved_at
        if isinstance(saved_at, str):
            try:
                saved_at_dt = datetime.fromisoformat(saved_at)
                saved_at_str = saved_at_dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                saved_at_str = saved_at
        else:
            saved_at_str = str(saved_at)
        
        print(f"Workflow ID: {workflow_id_val}")
        print(f"  Status: {status}")
        print(f"  Current Step: {current_step}")
        print(f"  Saved At: {saved_at_str}")
        print()


def handle_workflow_state_show_command(args: object) -> None:
    """Handle 'workflow state show' command (Epic 12)"""
    import json
    from pathlib import Path

    from ...workflow.state_manager import AdvancedStateManager

    workflow_id = getattr(args, "workflow_id", None)
    if not workflow_id:
        print("Error: workflow_id is required", file=sys.stderr)
        sys.exit(1)
    
    output_format = getattr(args, "format", "text")
    
    state_dir = Path.cwd() / ".tapps-agents" / "workflow-state"
    manager = AdvancedStateManager(state_dir)
    
    try:
        state, metadata = manager.load_state(workflow_id=workflow_id, validate=False)
        
        if output_format == "json":
            result = {
                "workflow_id": state.workflow_id,
                "status": state.status,
                "current_step": state.current_step,
                "completed_steps": state.completed_steps,
                "skipped_steps": state.skipped_steps,
                "metadata": metadata.to_dict() if hasattr(metadata, "to_dict") else str(metadata),
            }
            print(json.dumps(result, indent=2, default=str))
            return
        
        # Text format
        print(f"\n{'='*80}")
        print(f"Workflow State: {workflow_id}")
        print(f"{'='*80}\n")
        print(f"Status: {state.status}")
        print(f"Current Step: {state.current_step or 'N/A'}")
        print(f"Completed Steps: {len(state.completed_steps)}")
        print(f"Skipped Steps: {len(state.skipped_steps)}")
        if state.error:
            print(f"Error: {state.error}")
        print()
        
    except Exception as e:
        print(f"Error loading state: {e}", file=sys.stderr)
        sys.exit(1)


def handle_workflow_state_cleanup_command(args: object) -> None:
    """Handle 'workflow state cleanup' command (Epic 12)"""
    from pathlib import Path

    from ...workflow.state_manager import AdvancedStateManager

    state_dir = Path.cwd() / ".tapps-agents" / "workflow-state"
    manager = AdvancedStateManager(state_dir)
    
    retention_days = getattr(args, "retention_days", 30)
    max_states = getattr(args, "max_states_per_workflow", 10)
    remove_completed = getattr(args, "remove_completed", True)
    dry_run = getattr(args, "dry_run", False)
    
    if dry_run:
        print("DRY RUN: Would clean up states with the following settings:")
        print(f"  Retention: {retention_days} days")
        print(f"  Max states per workflow: {max_states}")
        print(f"  Remove completed: {remove_completed}")
        print()
        # TODO: Implement dry-run preview
        print("Dry-run preview not yet implemented. Use without --dry-run to perform cleanup.")
        return
    
    try:
        result = manager.cleanup_old_states(
            retention_days=retention_days,
            max_states_per_workflow=max_states,
            remove_completed=remove_completed,
        )
        
        print(f"\n{'='*80}")
        print("State Cleanup Complete")
        print(f"{'='*80}\n")
        print(f"Removed: {result['removed_count']} states")
        print(f"Freed: {result['removed_size_mb']} MB")
        print(f"Workflows cleaned: {result['workflows_cleaned']}")
        print()
        
    except Exception as e:
        print(f"Error during cleanup: {e}", file=sys.stderr)
        sys.exit(1)


def handle_workflow_resume_command(args: object) -> None:
    """Handle 'workflow resume' command (Epic 12)"""
    from pathlib import Path

    from ...workflow.executor import WorkflowExecutor

    workflow_id = getattr(args, "workflow_id", None)
    validate = getattr(args, "validate", True)
    max_steps = getattr(args, "max_steps", 50)
    
    executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
    
    try:
        # Load state
        if workflow_id:
            # Load specific workflow state
            state_dir = Path.cwd() / ".tapps-agents" / "workflow-state"
            from ...workflow.state_manager import AdvancedStateManager
            manager = AdvancedStateManager(state_dir)
            state, metadata = manager.load_state(workflow_id=workflow_id, validate=validate)
            executor.state = state
            # Load workflow from metadata
            if metadata.workflow_path:
                from ...workflow.parser import WorkflowParser
                parser = WorkflowParser()
                executor.workflow = parser.parse_file(Path(metadata.workflow_path))
        else:
            # Load last state
            executor.state = executor.load_last_state(validate=validate)
            # Load workflow from state variables
            workflow_path = executor.state.variables.get("_workflow_path")
            if workflow_path:
                from ...workflow.parser import WorkflowParser
                parser = WorkflowParser()
                executor.workflow = parser.parse_file(Path(workflow_path))
        
        if not executor.state or not executor.workflow:
            print("Error: Could not load workflow state or workflow definition", file=sys.stderr)
            sys.exit(1)
        
        # Validate state status
        if executor.state.status == "completed":
            print(f"\n{'='*60}")
            print(f"Workflow: {executor.workflow.name}")
            print(f"{'='*60}")
            print(f"Workflow ID: {executor.state.workflow_id}")
            print("Status: Already completed")
            print(f"{'='*60}")
            return
        
        if executor.state.status == "failed":
            print(f"\nWarning: Workflow previously failed. Resuming from failure point.", file=sys.stderr)
            print(f"Previous error: {executor.state.error or 'Unknown error'}", file=sys.stderr)
            # Reset status to running to allow resume
            executor.state.status = "running"
        
        # Resume paused workflow if needed
        if executor.state.status == "paused":
            executor.resume_workflow()
        
        print(f"\n{'='*60}")
        print(f"Resuming: {executor.workflow.name}")
        print(f"{'='*60}")
        print(f"Workflow ID: {executor.state.workflow_id}")
        print(f"Status: {executor.state.status}")
        print(f"Current Step: {executor.state.current_step or 'N/A'}")
        print(f"Completed Steps: {len(executor.state.completed_steps)}")
        print()
        
        # Get target file from state if available
        target_file = executor.state.variables.get("target_file")
        if target_file:
            # Convert to relative path if absolute
            target_path = Path(target_file)
            if target_path.is_absolute():
                # Try to make it relative to project root
                try:
                    target_file = str(target_path.relative_to(Path.cwd()))
                except ValueError:
                    # Keep absolute if can't make relative
                    target_file = str(target_path)
        
        # Resume execution - use execute() method, not run()
        # Use run_async_command helper for proper event loop management
        final_state = run_async_command(executor.execute(
            workflow=None,  # Already loaded
            target_file=target_file,
            max_steps=max_steps,
        ))
        
        # Handle final state
        if final_state.status == "completed":
            print(f"\n{'='*60}")
            print("Workflow completed successfully!")
            print(f"{'='*60}")
            print(f"Total steps completed: {len(final_state.completed_steps)}")
        elif final_state.status == "failed":
            print(f"\n{'='*60}")
            print("Workflow failed")
            print(f"{'='*60}")
            print(f"Error: {final_state.error or 'Unknown error'}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\n{'='*60}")
            print(f"Workflow status: {final_state.status}")
            print(f"{'='*60}")
            print(f"Current step: {final_state.current_step or 'N/A'}")
            print(f"Completed steps: {len(final_state.completed_steps)}")
            print("\nWorkflow can be resumed again with: tapps-agents workflow resume")
            
    except FileNotFoundError as e:
        print(f"Error: No workflow state found to resume", file=sys.stderr)
        if workflow_id:
            print(f"  Workflow ID: {workflow_id}", file=sys.stderr)
        print(f"  Details: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid workflow state or configuration", file=sys.stderr)
        print(f"  Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error resuming workflow: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_cursor_command(args: object) -> None:
    """Handle cursor verification command"""
    cursor_command = getattr(args, "cursor_command", None)
    output_format = getattr(args, "format", "text")
    
    if cursor_command == "verify" or cursor_command == "check":
        try:
            is_valid, results = verify_cursor_integration()
            output = format_verification_results(results, format=output_format)
            print(output)
            
            # Exit with error code if invalid
            if not is_valid:
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying Cursor integration: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"Unknown cursor command: {cursor_command}", file=sys.stderr)
        sys.exit(1)

