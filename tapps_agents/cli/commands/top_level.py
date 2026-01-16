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
    # - Workflows need Cursor Skills to produce artifacts for LLM-driven steps.
    # - Users can still force headless mode by setting TAPPS_AGENTS_MODE=headless explicitly.
    if cursor_mode_flag:
        os.environ["TAPPS_AGENTS_MODE"] = "cursor"
    elif "TAPPS_AGENTS_MODE" not in os.environ:
        os.environ["TAPPS_AGENTS_MODE"] = "cursor"

    if feedback.verbosity.value != "quiet":
        mode = os.environ.get("TAPPS_AGENTS_MODE", "headless")
        if mode == "cursor":
            safe_print("[OK] Cursor-first mode: workflows use Cursor Skills (or file-based Skill commands).")
            safe_print("     To force local-only execution: set TAPPS_AGENTS_MODE=headless (note: LLM steps won't execute without Cursor Skills).")
        else:
            safe_print("[WARN] Headless mode: local-only execution. LLM-driven workflow steps will not auto-generate artifacts without Cursor Skills.")

    try:
        # Check if workflow_name is actually a file path
        is_file_path = (
            "/" in workflow_name
            or "\\" in workflow_name
            or workflow_name.endswith(".yaml")
            or workflow_name.endswith(".yml")
        )
        
        # Validate input
        if not workflow_name or not isinstance(workflow_name, str):
            feedback.error(
                "Workflow name or file path required",
                error_code="validation_error",
                exit_code=3,
            )
            return

        if is_file_path:
            # Load workflow from file path
            workflow_file_path = Path(workflow_name)
            if not workflow_file_path.is_absolute():
                workflow_file_path = (Path.cwd() / workflow_file_path).resolve()
            else:
                workflow_file_path = workflow_file_path.resolve()
            
            if not workflow_file_path.exists():
                feedback.error(
                    f"Workflow file not found: {workflow_name}",
                    error_code="file_not_found",
                    remediation="Check that the file path is correct and the file exists",
                    exit_code=3,
                )
                return
            
            if not workflow_file_path.is_file():
                feedback.error(
                    f"Path is not a file: {workflow_name}",
                    error_code="validation_error",
                    remediation="Provide a path to a workflow YAML file",
                    exit_code=3,
                )
                return
            
            feedback.start_operation("Create Project", f"Creating project with workflow from {workflow_name}")
            feedback.running(f"Loading workflow from file: {workflow_name}...", step=1, total_steps=5)
            try:
                from ...workflow.executor import WorkflowExecutor
                executor = WorkflowExecutor(auto_detect=False)
                workflow = executor.load_workflow(workflow_file_path)
            except Exception as e:
                feedback.error(
                    f"Failed to load workflow from file: {str(e)}",
                    error_code="workflow_load_error",
                    context={"file": str(workflow_file_path)},
                    exit_code=3,
                )
                return
        else:
            # Load workflow preset
            feedback.start_operation("Create Project", f"Creating project with {workflow_name} workflow")
            feedback.running(f"Loading workflow preset: {workflow_name}...", step=1, total_steps=5)
            workflow = loader.load_preset(workflow_name)
            if not workflow:
                feedback.error(
                    f"Workflow preset '{workflow_name}' not found",
                    error_code="config_error",
                    remediation="Use 'tapps-agents workflow list' to see available presets, or provide a file path",
                    exit_code=3,
                )
                return

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


def _handle_workflow_dry_run(workflow: Any, args: object, feedback: Any) -> None:
    """
    Handle workflow dry-run validation (Issue fix: No pre-flight checks).
    
    Validates workflow without executing, showing what would happen.
    """
    from ...core.config import load_config
    from ...core.runtime_mode import detect_runtime_mode
    from ...core.unicode_safe import safe_print
    
    print(f"\n{'='*60}")
    print(f"DRY RUN: {workflow.name}")
    print(f"{'='*60}")
    print(f"Description: {workflow.description}")
    print()
    
    # Check runtime mode
    runtime_mode = detect_runtime_mode()
    cli_mode = getattr(args, "cli_mode", False)
    cursor_mode = getattr(args, "cursor_mode", False)
    
    print("📋 Configuration:")
    print(f"   Runtime mode: {runtime_mode.value}")
    if cli_mode:
        print("   Mode override: --cli-mode (headless execution)")
    elif cursor_mode:
        print("   Mode override: --cursor-mode (Cursor Skills)")
    
    # Check target file
    target_file = getattr(args, "file", None)
    user_prompt = getattr(args, "prompt", None)
    
    print()
    print("📁 Inputs:")
    if target_file:
        target_path = Path(target_file)
        if target_path.exists():
            safe_print(f"   [OK] Target file exists: {target_file}")
        else:
            safe_print(f"   [WARN] Target file not found: {target_file}")
    else:
        print("   Target file: Not specified")
    
    if user_prompt:
        print(f"   Prompt: {user_prompt[:50]}..." if len(user_prompt) > 50 else f"   Prompt: {user_prompt}")
    else:
        print("   Prompt: Not specified")
    
    # Check artifact paths
    config = load_config()
    artifact_config = config.workflow.artifacts
    artifact_dir = artifact_config.get_artifact_dir()
    
    print()
    print("📂 Artifact Paths:")
    print(f"   Base directory: {artifact_config.base_dir}")
    print(f"   Simple Mode subdir: {artifact_config.simple_mode_subdir}")
    print(f"   Full path: {artifact_dir}")
    
    artifact_path = Path(artifact_dir)
    if artifact_path.exists():
        existing_files = list(artifact_path.glob("*.md"))
        if existing_files:
            safe_print(f"   [WARN] Existing artifacts found: {len(existing_files)} files")
            for f in existing_files[:3]:
                print(f"      - {f.name}")
            if len(existing_files) > 3:
                print(f"      ... and {len(existing_files) - 3} more")
        else:
            safe_print("   [OK] No existing artifacts")
    else:
        safe_print("   [OK] Directory will be created")
    
    # List workflow steps
    print()
    print(f"📝 Workflow Steps ({len(workflow.steps)} total):")
    
    continue_from = getattr(args, "continue_from", None)
    skip_steps_str = getattr(args, "skip_steps", None)
    skip_steps = skip_steps_str.split(",") if skip_steps_str else []
    
    found_continue_from = False
    for i, step in enumerate(workflow.steps, 1):
        step_id = step.id
        agent = step.agent or "unknown"
        action = step.action or "execute"
        
        status = ""
        if continue_from and not found_continue_from:
            if step_id == continue_from:
                found_continue_from = True
                status = " [RESUME FROM HERE]"
            else:
                status = " [SKIP - before continue point]"
        elif step_id in skip_steps:
            status = " [SKIP - user requested]"
        
        print(f"   {i}. {step_id}: @{agent} *{action}{status}")
    
    if continue_from and not found_continue_from:
        safe_print(f"\n   [FAIL] Step '{continue_from}' not found in workflow!")
        print(f"   Available steps: {', '.join(s.id for s in workflow.steps)}")
    
    # Environment check
    print()
    print("🔧 Environment:")
    try:
        from ...core.doctor import collect_doctor_report
        report = collect_doctor_report()
        findings = report.get("findings", [])
        errors = [f for f in findings if f.get("severity") == "error"]
        warnings = [f for f in findings if f.get("severity") == "warn"]
        
        if errors:
            safe_print(f"   [FAIL] {len(errors)} error(s) found")
            for err in errors[:2]:
                print(f"      - {err.get('message', 'Unknown error')}")
        elif warnings:
            safe_print(f"   [WARN] {len(warnings)} warning(s) found")
        else:
            safe_print("   [OK] Environment ready")
    except Exception as e:
        safe_print(f"   [WARN] Could not check environment: {e}")
    
    # Summary
    print()
    print("="*60)
    print("DRY RUN COMPLETE")
    print("="*60)
    print()
    print("To execute this workflow, remove --dry-run flag:")
    
    cmd_parts = ["tapps-agents", "workflow", getattr(args, "preset", "rapid")]
    if user_prompt:
        cmd_parts.extend(["--prompt", f'"{user_prompt}"'])
    if target_file:
        cmd_parts.extend(["--file", target_file])
    if getattr(args, "auto", False):
        cmd_parts.append("--auto")
    if continue_from:
        cmd_parts.extend(["--continue-from", continue_from])
    if skip_steps:
        cmd_parts.extend(["--skip-steps", ",".join(skip_steps)])
    
    print(f"  {' '.join(cmd_parts)}")


def _extract_files_changed_from_state(state: Any) -> list[str]:
    """Extract list of file paths from workflow state artifacts."""
    files_changed = []
    if state and hasattr(state, "artifacts"):
        for artifact in state.artifacts.values():
            if hasattr(artifact, "path") and artifact.path:
                files_changed.append(artifact.path)
    return files_changed


def _extract_story_info_from_workflow(workflow: Any, state: Any) -> tuple[str | None, str | None]:
    """Extract story information from workflow steps and state."""
    story_title = None
    story_id = None
    
    if workflow and hasattr(workflow, "steps") and state:
        # Get current step
        current_step_id = state.current_step if hasattr(state, "current_step") else None
        if current_step_id:
            # Find current step
            for step in workflow.steps:
                if step.id == current_step_id:
                    # Check metadata for story information
                    if hasattr(step, "metadata") and step.metadata:
                        story_id = step.metadata.get("story_id")
                        story_title = step.metadata.get("story_title")
                    # Fallback to step ID/action if no story metadata
                    if not story_title:
                        story_title = f"{step.agent}/{step.action}" if hasattr(step, "agent") else step.id
                    break
    
    return story_title, story_id


def _extract_learnings_from_state(state: Any) -> list[str]:
    """Extract learnings from workflow state (from variables or step executions)."""
    learnings = []
    
    if state:
        # Check state variables for learnings
        if hasattr(state, "variables") and state.variables:
            state_learnings = state.variables.get("learnings", [])
            if isinstance(state_learnings, list):
                learnings.extend(state_learnings)
        
        # Extract learnings from step execution metadata if available
        if hasattr(state, "step_executions"):
            for step_exec in state.step_executions:
                if hasattr(step_exec, "metadata") and step_exec.metadata:
                    step_learnings = step_exec.metadata.get("learnings", [])
                    if isinstance(step_learnings, list):
                        learnings.extend(step_learnings)
    
    return learnings


def _handle_autonomous_workflow_execution(
    workflow: Any,
    args: object,
    executor: Any,
    user_prompt: str | None,
    target_file: str | None,
) -> None:
    """Handle autonomous execution loop (2025 architecture)."""
    from datetime import datetime
    from pathlib import Path
    from ...workflow.parser import WorkflowParser
    from ...workflow.progress_logger import ProgressLogger
    from ...core.unicode_safe import safe_print
    
    autonomous = getattr(args, "autonomous", False)
    max_iterations = getattr(args, "max_iterations", 10)
    
    if not autonomous:
        return  # Fall through to normal execution
    
    # Initialize progress logger
    project_root = Path.cwd()
    progress_file = project_root / ".tapps-agents" / "progress.txt"
    progress_logger = ProgressLogger(progress_file)
    
    iteration = 1
    start_time = datetime.now()
    final_state = None
    
    while iteration <= max_iterations:
        safe_print(f"\nIteration {iteration}/{max_iterations}: ", end="")
        
        if iteration == 1:
            # First iteration: start new workflow
            executor.user_prompt = user_prompt  # Store prompt
            safe_print("Starting workflow execution...")
            final_state = asyncio.run(executor.execute(workflow=workflow, target_file=target_file))
            # State is already saved by execute(), autonomous variables will be set in next iteration if needed
        else:
            # Subsequent iterations: resume workflow (like resume command)
            try:
                safe_print("Resuming workflow execution...")
                executor.state = executor.load_last_state()
                # Load workflow from state (like resume command)
                # load_last_state() already attempts to reload workflow if path is available
                # If workflow is still None, try loading from state variables
                if not executor.workflow:
                    workflow_path = executor.state.variables.get("_workflow_path")
                    if workflow_path:
                        parser = WorkflowParser()
                        executor.workflow = parser.parse_file(Path(workflow_path))
                # Reset status if failed (allow retry, like resume command)
                if executor.state.status == "failed":
                    executor.state.status = "running"
                executor.state.variables["autonomous_iteration"] = iteration
                executor.save_state()  # Persist variables before execute
                final_state = asyncio.run(executor.execute(workflow=None, target_file=target_file))
            except FileNotFoundError:
                safe_print("[FAIL] No workflow state found to resume")
                break
            except ValueError as e:
                # Handle case where workflow can't be loaded (e.g., preset without path)
                safe_print(f"[FAIL] Cannot resume workflow: {e}")
                break
        
        # Log iteration to progress.txt (Phase 3)
        if final_state:
            # Extract information for logging
            files_changed = _extract_files_changed_from_state(final_state)
            learnings = _extract_learnings_from_state(final_state)
            
            # Get workflow for story extraction (try executor.workflow, fallback to passed workflow)
            workflow_for_story = workflow
            if hasattr(executor, "workflow") and executor.workflow:
                workflow_for_story = executor.workflow
            
            story_title, story_id = _extract_story_info_from_workflow(
                workflow_for_story,
                final_state
            )
            thread_id = final_state.workflow_id if hasattr(final_state, "workflow_id") else None
            
            # Log to progress.txt
            progress_logger.log_iteration(
                iteration=iteration,
                story_title=story_title,
                files_changed=files_changed if files_changed else None,
                learnings=learnings if learnings else None,
                thread_id=thread_id,
                status=final_state.status,
            )
        
        # Check status and decide next action
        if final_state.status == "completed":
            safe_print(f"[OK] Workflow completed successfully")
            break
        elif final_state.status == "failed":
            safe_print(f"[FAIL] Workflow failed: {final_state.error}")
            # Phase 1: retry if iterations remain (can enhance with smart retry logic later)
        elif final_state.status == "running":
            safe_print(f"[INFO] Workflow interrupted, will resume next iteration")
        
        iteration += 1
    
    # Print final summary (ensure final_state exists)
    if final_state:
        elapsed = (datetime.now() - start_time).total_seconds()
        _print_autonomous_summary(iteration - 1, max_iterations, final_state, elapsed)


def _print_autonomous_summary(
    iteration: int,
    max_iterations: int,
    final_state: Any,
    elapsed: float,
) -> None:
    """Print autonomous execution summary."""
    from ...core.unicode_safe import safe_print
    
    safe_print(f"\n{'='*60}")
    safe_print("Autonomous Execution Summary")
    safe_print(f"{'='*60}")
    safe_print(f"Iterations: {iteration}/{max_iterations}")
    safe_print(f"Final Status: {final_state.status}")
    safe_print(f"Completed Steps: {len(final_state.completed_steps)}")
    safe_print(f"Total Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    
    if final_state.status == "completed":
        safe_print("[OK] Workflow completed successfully!")
    elif final_state.status == "failed":
        safe_print(f"[FAIL] Workflow failed: {final_state.error}")
    elif iteration >= max_iterations:
        safe_print(f"[WARN] Max iterations ({max_iterations}) reached before completion")
        safe_print(f"Current step: {final_state.current_step or 'N/A'}")
        safe_print("Use 'tapps-agents workflow resume' to continue")
    
    safe_print(f"{'='*60}\n")


def handle_workflow_command(args: object) -> None:
    """Handle workflow command"""
    from ...workflow.executor import WorkflowExecutor
    from ...workflow.preset_loader import PresetLoader
    from ...core.runtime_mode import is_cursor_mode, detect_runtime_mode
    from ...core.unicode_safe import safe_print
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
    
    # Handle cleanup-branches subcommand
    if preset_name == "cleanup-branches":
        handle_workflow_cleanup_branches_command(args)
        return

    # ROOT CAUSE FIX: Prevent CLI workflow commands in Cursor mode
    # This prevents failed attempts and provides clear guidance to use @simple-mode commands
    runtime_mode = detect_runtime_mode()
    cli_mode_override = getattr(args, "cli_mode", False)
    
    # If in Cursor mode and not explicitly overridden, prevent CLI workflow execution
    # State management, resume, recommend, and cleanup-branches subcommands are allowed
    if is_cursor_mode() and not cli_mode_override and preset_name and preset_name not in ["list", None]:
        safe_print("\n" + "=" * 60)
        safe_print("⚠️  CLI Workflow Commands Not Recommended in Cursor Mode")
        safe_print("=" * 60)
        safe_print("")
        safe_print("You're running in Cursor mode, but attempting to use CLI workflow commands.")
        safe_print("CLI workflow commands may fail due to dependency issues in Cursor mode.")
        safe_print("")
        safe_print("✅ Instead, use @simple-mode commands in Cursor chat:")
        safe_print("")
        safe_print("   @simple-mode *build 'description'")
        safe_print("   @simple-mode *review <file>")
        safe_print("   @simple-mode *fix <file> 'description'")
        safe_print("   @simple-mode *test <file>")
        safe_print("   @simple-mode *full 'description'")
        safe_print("")
        safe_print("💡 To force CLI execution (not recommended), use: --cli-mode")
        safe_print("")
        safe_print("=" * 60)
        sys.exit(1)

    loader = PresetLoader()

    try:
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

            print("Usage: python -m tapps_agents.cli workflow <preset>|<file_path>")
            print("\nExamples:")
            print("  # Using preset names:")
            print("  python -m tapps_agents.cli workflow rapid")
            print("  python -m tapps_agents.cli workflow full")
            print("  python -m tapps_agents.cli workflow fix")
            print("  python -m tapps_agents.cli workflow enterprise")
            print("  python -m tapps_agents.cli workflow feature")
            print("\n  # Using file paths:")
            print("  python -m tapps_agents.cli workflow workflows/custom/my-workflow.yaml")
            print("  python -m tapps_agents.cli workflow ./workflows/example-feature-development.yaml")
            return

        # Validate input
        if not preset_name or not isinstance(preset_name, str):
            feedback.error(
                "Workflow preset name or file path required",
                error_code="validation_error",
                exit_code=1,
            )
            return

        # Check if preset_name is actually a file path
        # File paths typically contain '/' or '\' or end with '.yaml' or '.yml'
        workflow_file_path: Path | None = None
        is_file_path = (
            "/" in preset_name
            or "\\" in preset_name
            or preset_name.endswith(".yaml")
            or preset_name.endswith(".yml")
        )
        
        if is_file_path:
            # Try to load as file path
            workflow_file_path = Path(preset_name)
            if not workflow_file_path.is_absolute():
                workflow_file_path = (Path.cwd() / workflow_file_path).resolve()
            else:
                workflow_file_path = workflow_file_path.resolve()
            
            if not workflow_file_path.exists():
                feedback.error(
                    f"Workflow file not found: {preset_name}",
                    error_code="file_not_found",
                    remediation="Check that the file path is correct and the file exists",
                    exit_code=1,
                )
                return
            
            if not workflow_file_path.is_file():
                feedback.error(
                    f"Path is not a file: {preset_name}",
                    error_code="validation_error",
                    remediation="Provide a path to a workflow YAML file",
                    exit_code=1,
                )
                return
            
            # Load workflow from file
            try:
                executor = WorkflowExecutor(auto_detect=False)
                workflow = executor.load_workflow(workflow_file_path)
            except Exception as e:
                feedback.error(
                    f"Failed to load workflow from file: {str(e)}",
                    error_code="workflow_load_error",
                    context={"file": str(workflow_file_path)},
                    exit_code=1,
                )
                return
        else:
            # Load and execute preset
            try:
                workflow = loader.load_preset(preset_name)
                if not workflow:
                    print(f"Error: Preset '{preset_name}' not found.", file=sys.stderr)
                    print(
                        f"Available presets: {', '.join(loader.list_presets().keys())}",
                        file=sys.stderr,
                    )
                    print(
                        "\nTip: You can also provide a file path (e.g., 'workflows/custom/my-workflow.yaml')",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            except Exception as e:
                feedback.error(
                    f"Failed to load preset: {str(e)}",
                    error_code="preset_load_error",
                    context={"preset": preset_name},
                    exit_code=1,
                )
                return

        # Handle explicit mode flags (Issue fix: CLI/Cursor mode confusion)
        cli_mode = getattr(args, "cli_mode", False)
        cursor_mode = getattr(args, "cursor_mode", False)
        
        if cli_mode and cursor_mode:
            feedback.error(
                "Cannot specify both --cli-mode and --cursor-mode",
                error_code="validation_error",
                remediation="Choose one: --cli-mode for headless execution, --cursor-mode for Cursor Skills",
                exit_code=2,
            )
            return
        
        # Set mode based on explicit flags
        if cli_mode:
            os.environ["TAPPS_AGENTS_MODE"] = "headless"
        elif cursor_mode:
            os.environ["TAPPS_AGENTS_MODE"] = "cursor"
        elif "TAPPS_AGENTS_MODE" not in os.environ:
            # Cursor-first default for workflow execution.
            # Workflows frequently require Cursor Skills to materialize artifacts for LLM-driven steps.
            os.environ["TAPPS_AGENTS_MODE"] = "cursor"
        
        # Handle dry-run validation (Issue fix: No pre-flight checks)
        dry_run = getattr(args, "dry_run", False)
        if dry_run:
            _handle_workflow_dry_run(workflow, args, feedback)
            return
        
        # Handle continue-from flag (Issue fix: All-or-nothing execution)
        continue_from = getattr(args, "continue_from", None)
        skip_steps_str = getattr(args, "skip_steps", None)
        skip_steps = skip_steps_str.split(",") if skip_steps_str else []
        print_paths = getattr(args, "print_paths", True)

        # Execute workflow (start + run steps until completion)
        executor = WorkflowExecutor(auto_detect=False, auto_mode=getattr(args, "auto", False))
        target_file = getattr(args, "file", None)
        user_prompt = getattr(args, "prompt", None)
        
        # Store prompt in executor state if provided
        if user_prompt:
            executor.user_prompt = user_prompt
        
        # Store new flags in executor for step handling
        executor.continue_from = continue_from
        executor.skip_steps = skip_steps
        executor.print_paths = print_paths
        
        # Handle autonomous execution mode (Phase 1: Autonomous Execution Loop)
        autonomous = getattr(args, "autonomous", False)
        if autonomous:
            _handle_autonomous_workflow_execution(
                workflow=workflow,
                args=args,
                executor=executor,
                user_prompt=user_prompt,
                target_file=target_file,
            )
            return
        
        print(f"\n{'='*60}")
        print(f"Starting: {workflow.name}")
        print(f"{'='*60}")
        print(f"Description: {workflow.description}")
        print(f"Steps: {len(workflow.steps)}")
        if continue_from:
            print(f"Continuing from: {continue_from}")
        if skip_steps:
            print(f"Skipping steps: {', '.join(skip_steps)}")
        print()
        
        # Check runtime mode and warn user
        from ...core.runtime_mode import is_cursor_mode, detect_runtime_mode
        runtime_mode = detect_runtime_mode()
        
        print("Executing workflow steps...")
        print(f"Runtime mode: {runtime_mode.value}")
        
        from ...core.unicode_safe import safe_print
        if is_cursor_mode():
            safe_print("[OK] Cursor-first mode: workflow will use Cursor Skills (or file-based Skill commands).")
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


def handle_status_command(args: object) -> None:
    """Handle the unified status command."""
    from .status import handle_status_command as status_handler

    detailed = getattr(args, "detailed", False)
    worktrees_only = getattr(args, "worktrees_only", False)
    format = getattr(args, "format", "text")

    status_handler(detailed=detailed, worktrees_only=worktrees_only, format=format)


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

    # Background Agents removed - no longer displayed

    if results.get("cursorignore"):
        print("  .cursorignore: Installed")
        print("    - .cursorignore")
    else:
        print("  .cursorignore: Skipped or already exists")
    
    # Show MCP config (will be shown in dedicated section)
    # MCP status is now shown in _print_mcp_status() function
    
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


def _print_mcp_status(results: dict[str, Any]) -> None:
    """Print MCP configuration status."""
    from ...core.unicode_safe import safe_print
    
    mcp_config = results.get("mcp_config", {})
    if not mcp_config:
        return
    
    print("\n" + "=" * 60)
    print("MCP Configuration Status")
    print("=" * 60)
    
    # Show config file status
    if mcp_config.get("created"):
        safe_print("  [OK] MCP Config: Created")
        print(f"    - {mcp_config.get('path', '.cursor/mcp.json')}")
        print("    - Context7 MCP server configured (project-local)")
    elif mcp_config.get("path"):
        print("  MCP Config: Already exists")
        print(f"    - {mcp_config.get('path')}")
    
    # Show validation status
    mcp_validation = mcp_config.get("validation")
    if mcp_validation:
        if not mcp_validation.get("valid", True):
            safe_print("\n  [ERROR] MCP Configuration Issues:")
            for issue in mcp_validation.get("issues", []):
                print(f"    - {issue}")
        if mcp_validation.get("warnings"):
            safe_print("\n  [WARN] Warnings:")
            for warning in mcp_validation.get("warnings", []):
                print(f"    - {warning}")
        if mcp_validation.get("recommendations"):
            safe_print("\n  [INFO] Recommendations:")
            for rec in mcp_validation.get("recommendations", []):
                print(f"    - {rec}")
    
    # Show npx availability
    npx_available = mcp_config.get("npx_available", True)
    npx_error = mcp_config.get("npx_error")
    if not npx_available:
        safe_print("\n  [WARN] npx not available:")
        print(f"    - {npx_error}")
        print("    - Install Node.js: https://nodejs.org/")
        print("    - MCP servers that use npx will not work without Node.js")
    
    # Show overall status
    if mcp_validation and mcp_validation.get("valid", True) and npx_available:
        safe_print("\n  [OK] MCP configuration is ready!")
    elif mcp_validation and not mcp_validation.get("valid", True):
        safe_print("\n  [ERROR] MCP configuration has issues that need to be fixed.")
    else:
        safe_print("\n  [WARN] MCP configuration may have issues.")


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
            # Check if this is an import error (non-critical Context7 MCP server issue)
            is_import_error = (
                "import error" in cache_error.lower() or 
                "attempted relative import" in cache_error.lower()
            )
            
            if is_import_error:
                print("  Status: [WARN] Pre-population failed (non-critical)")
                print(f"  Error: {cache_error}")
                print("  Note: This is a known issue with Context7 MCP server library resolution.")
                print("        Context7 will continue to work normally via on-demand lookups.")
                print("        To skip pre-population in future runs, use: --no-cache")
            else:
                print("  Status: [FAILED] Failed")
                print(f"  Error: {cache_error}")
                print("  Note: Exception occurred during cache pre-population.")
                print("        Cache pre-population works best when run from within Cursor where MCP servers are available.")
        elif cache_result:
            error_msg = cache_result.get("error") or cache_result.get("message") or "Unknown error"
            
            # Check if this is an import error (non-critical Context7 MCP server issue)
            is_import_error = (
                "import error" in error_msg.lower() or 
                "attempted relative import" in error_msg.lower() or
                "MCP server import issue" in error_msg
            )
            
            if is_import_error:
                print("  Status: [WARN] Pre-population failed (non-critical)")
                print(f"  Error: {error_msg}")
                print("  Note: This is a known issue with Context7 MCP server library resolution.")
                print("        Context7 will continue to work normally via on-demand lookups.")
                print("        To skip pre-population in future runs, use: --no-cache")
            else:
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
    print("Next Steps - START HERE")
    print("=" * 60)
    print()
    
    # Prominent Simple Mode section
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  RECOMMENDED: Use @simple-mode for ALL development tasks ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print("In Cursor Chat, type:")
    print()
    print("  @simple-mode *build \"<describe your feature>\"")
    print()
    print("This orchestrates a complete 7-step workflow:")
    print("  1. @enhancer  → Enhanced requirements with analysis")
    print("  2. @planner   → User stories with acceptance criteria")
    print("  3. @architect → System architecture design")
    print("  4. @designer  → Component/API specifications")
    print("  5. @implementer → Code implementation")
    print("  6. @reviewer  → Quality review (auto-loops if score < 70)")
    print("  7. @tester    → Test generation and validation")
    print()
    print("More Simple Mode commands:")
    print("  @simple-mode *review src/file.py      # Code quality review")
    print("  @simple-mode *fix src/file.py \"error\" # Fix bugs with debugging")
    print("  @simple-mode *test src/file.py        # Generate tests")
    print("  @simple-mode *refactor src/file.py    # Refactor code")
    print()
    print("-" * 60)
    print()
    
    print("Individual Agent Commands (Advanced):")
    print("  Use these only when you need a specific agent directly:")
    print("    @reviewer *score src/main.py")
    print("    @implementer *implement \"Add feature\" src/feature.py")
    print("    @tester *test src/utils.py")
    print()
    
    print("Terminal/CI Commands:")
    print("  • Workflow presets:")
    print("    tapps-agents workflow rapid --prompt \"Add feature\" --auto")
    print("    tapps-agents workflow fix --file src/buggy.py --auto")
    print()
    print("  • Direct commands:")
    print("    tapps-agents reviewer review src/")
    print("    tapps-agents score src/main.py")
    print()

    print("Setup & Configuration:")
    print("  • Verify setup: tapps-agents cursor verify")
    print("  • Environment check: tapps-agents doctor")
    print("  • Configure experts: tapps-agents setup-experts add")
    print()
    
    print("Why Simple Mode Produces Better Results:")
    print("  • Workflow orchestration → quality gates with automatic loopbacks")
    print("  • Requirements analysis → prevents scope creep")
    print("  • Architecture design → better structure")
    print("  • Documentation artifacts → full traceability")
    print("  • Test generation → comprehensive coverage")
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
        include_cursorignore=not getattr(args, "no_cursorignore", False),
        pre_populate_cache=not getattr(args, "no_cache", False),
        reset_mode=reset_mode,
        backup_before_reset=not getattr(args, "no_backup", False),
        reset_mcp=getattr(args, "reset_mcp", False),
        preserve_custom=getattr(args, "preserve_custom", True),
    )
    
    # Offer interactive Context7 setup if API key is missing
    mcp_config = results.get("mcp_config", {})
    mcp_validation = mcp_config.get("validation")
    if mcp_validation and not mcp_validation.get("valid", True):
        # Check if the issue is missing API key
        issues = mcp_validation.get("issues", [])
        api_key_missing = any("CONTEXT7_API_KEY" in issue for issue in issues)
        
        if api_key_missing and not getattr(args, "yes", False):
            from ...core.mcp_setup import offer_context7_setup
            offer_context7_setup(results["project_root"], interactive=True)

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
    
    # Show MCP status
    if results.get("mcp_config"):
        _print_mcp_status(results)

    # Update .cursorignore patterns if cursorignore was created/updated
    if results.get("cursorignore") or not getattr(args, "no_cursorignore", False):
        cursorignore_update = _update_cursorignore_patterns(results["project_root"])
        if cursorignore_update["updated"]:
            print("\n✅ Updated .cursorignore with TappsCodingAgents patterns:")
            for pattern in cursorignore_update["patterns_added"]:
                print(f"   - {pattern}")

    # Run environment diagnostics
    _run_environment_check(results["project_root"])

    _print_next_steps()


def _update_cursorignore_patterns(project_root: Path | str) -> dict[str, Any]:
    """
    Update .cursorignore with TappsCodingAgents patterns.
    
    Args:
        project_root: Project root directory (Path or string)
        
    Returns:
        Dictionary with update results:
        {
            "updated": bool,
            "patterns_added": list[str],
            "patterns_existing": list[str],
        }
    """
    # Convert string to Path if needed
    if isinstance(project_root, str):
        project_root = Path(project_root)
    cursorignore_path = project_root / ".cursorignore"
    
    # Patterns to add
    patterns_to_add = [
        ".tapps-agents/backups/",
        ".tapps-agents/archives/",
        ".tapps-agents/artifacts/",
    ]
    
    # Read existing file
    existing_content = ""
    if cursorignore_path.exists():
        existing_content = cursorignore_path.read_text(encoding="utf-8")
    
    # Check which patterns are missing
    missing_patterns = [
        p for p in patterns_to_add
        if p not in existing_content
    ]
    
    if not missing_patterns:
        return {
            "updated": False,
            "patterns_added": [],
            "patterns_existing": patterns_to_add,
        }
    
    # Append missing patterns
    new_content = existing_content
    if new_content and not new_content.endswith("\n"):
        new_content += "\n"
    
    new_content += "\n# TappsCodingAgents generated artifacts (auto-added)\n"
    for pattern in missing_patterns:
        new_content += f"{pattern}\n"
    
    cursorignore_path.write_text(new_content, encoding="utf-8")
    
    return {
        "updated": True,
        "patterns_added": missing_patterns,
        "patterns_existing": [p for p in patterns_to_add if p not in missing_patterns],
    }


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
    from ..feedback import get_feedback
    
    config_path = getattr(args, "config_path", None)
    full_mode = getattr(args, "full", False)
    output_format = getattr(args, "format", "text")
    
    feedback = get_feedback()
    feedback.format_type = output_format
    
    # Collect doctor report
    report = collect_doctor_report(
        config_path=Path(config_path) if config_path else None
    )

    # If --full flag, also run health checks
    health_results = None
    if full_mode:
        feedback.start_operation("Doctor", "Running comprehensive diagnostics (doctor + health checks)")
        feedback.running("Running health checks...", step=1, total_steps=2)
        
        try:
            from ...health.checks.context7_cache import Context7CacheHealthCheck
            from ...health.registry import HealthCheckRegistry
            from ...health.orchestrator import HealthOrchestrator
            from ...health.collector import HealthMetricsCollector
            
            project_root = Path.cwd()
            registry = HealthCheckRegistry()
            registry.register(Context7CacheHealthCheck(project_root=project_root))
            
            metrics_collector = HealthMetricsCollector(project_root=project_root)
            orchestrator = HealthOrchestrator(
                registry=registry, metrics_collector=metrics_collector, project_root=project_root
            )
            
            health_results = orchestrator.run_all_checks()
            feedback.running("Health checks completed", step=2, total_steps=2)
        except Exception as e:
            feedback.warning(f"Could not run health checks: {e}")
            health_results = None
        
        feedback.clear_progress()

    if output_format == "json":
        result = report.copy()
        if health_results:
            result["health_checks"] = {
                "results": [
                    {
                        "name": r.name,
                        "status": r.status,
                        "score": r.score,
                        "message": r.message,
                        "details": r.details,
                    }
                    for r in health_results.values()
                ]
            }
        format_json_output(result)
    else:
        policy = report.get("policy", {})
        targets = report.get("targets", {})
        print("\n" + "=" * 60)
        print("TappsCodingAgents Doctor Report" + (" (Full Diagnostics)" if full_mode else ""))
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
        
        # Show health check results if --full
        if full_mode and health_results:
            print("\n" + "=" * 60)
            print("Health Check Results")
            print("=" * 60)
            for result in health_results.values():
                status_symbol = "✅" if result.status == "healthy" else "⚠️" if result.status == "degraded" else "❌"
                print(f"\n{status_symbol} {result.name}: {result.status} (score: {result.score:.1f}/100)")
                print(f"   {result.message}")
                if result.details:
                    key_metrics = []
                    for key, value in result.details.items():
                        if isinstance(value, (int, float)) and key in ["hit_rate", "avg_response_time_ms", "total_entries"]:
                            if key == "hit_rate":
                                key_metrics.append(f"{key}: {value:.1f}%")
                            elif key == "avg_response_time_ms":
                                key_metrics.append(f"{key}: {value:.0f}ms")
                            else:
                                key_metrics.append(f"{key}: {value}")
                    if key_metrics:
                        print(f"   Metrics: {' | '.join(key_metrics)}")
                if result.remediation:
                    if isinstance(result.remediation, list) and result.remediation:
                        print(f"   Remediation: {result.remediation[0]}")
                    elif isinstance(result.remediation, str):
                        print(f"   Remediation: {result.remediation}")


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


def handle_cleanup_workflow_docs_command(args: object) -> None:
    """Handle 'cleanup workflow-docs' command"""
    from ...core.cleanup_tool import CleanupTool

    tool = CleanupTool()

    # Get config values or use command-line overrides
    config = tool.config.cleanup.workflow_docs
    keep_latest = getattr(args, "keep_latest", None) or config.keep_latest
    retention_days = getattr(args, "retention_days", None) or config.retention_days
    
    # Handle archive flag
    archive_enabled = config.archive_enabled
    if getattr(args, "archive", False):
        archive_enabled = True
    elif getattr(args, "no_archive", False):
        archive_enabled = False
    
    archive_dir = config.archive_dir if archive_enabled else None
    dry_run = getattr(args, "dry_run", False)

    if dry_run:
        print("DRY RUN: Would clean up workflow documentation with the following settings:")
        print(f"  Keep latest: {keep_latest} workflows")
        print(f"  Retention: {retention_days} days")
        print(f"  Archive enabled: {archive_enabled}")
        if archive_dir:
            print(f"  Archive directory: {archive_dir}")
        print()

    try:
        results = tool.cleanup_workflow_docs(
            keep_latest=keep_latest,
            retention_days=retention_days,
            archive_dir=archive_dir,
            dry_run=dry_run,
        )

        print(f"\n{'='*80}")
        print("Workflow Documentation Cleanup Complete")
        print(f"{'='*80}\n")
        print(f"Kept: {results['kept']} workflows visible")
        print(f"Archived: {results['archived']} workflows ({results['total_size_mb']:.2f} MB)")
        
        if results['archived_workflows']:
            print("\nArchived workflows:")
            for workflow_id in results['archived_workflows'][:10]:  # Show first 10
                print(f"  - {workflow_id}")
            if len(results['archived_workflows']) > 10:
                print(f"  ... and {len(results['archived_workflows']) - 10} more")
        
        if results['kept_workflows']:
            print("\nKept workflows:")
            for workflow_id in results['kept_workflows'][:10]:  # Show first 10
                print(f"  - {workflow_id}")
            if len(results['kept_workflows']) > 10:
                print(f"  ... and {len(results['kept_workflows']) - 10} more")
        
        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"  ⚠️  {error}")
        
        if dry_run:
            print("\n⚠️  This was a dry run. Run without --dry-run to perform actual cleanup.")
        
        print()
        
    except Exception as e:
        print(f"Error during cleanup: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
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


def handle_workflow_cleanup_branches_command(args: object) -> None:
    """Handle 'workflow cleanup-branches' command"""
    import asyncio
    from pathlib import Path
    
    from ...workflow.branch_cleanup import BranchCleanupService
    
    dry_run = getattr(args, "dry_run", False)
    retention_days = getattr(args, "retention_days", None)
    pattern = getattr(args, "pattern", None)
    force = getattr(args, "force", False)
    output_format = getattr(args, "format", "text")
    
    feedback = get_feedback()
    feedback.format_type = output_format
    operation_desc = "Previewing branch cleanup" if dry_run else "Cleaning up orphaned branches"
    feedback.start_operation("Branch Cleanup", operation_desc)
    
    try:
        project_root = Path.cwd()
        service = BranchCleanupService(project_root=project_root)
        
        # Build patterns dict if pattern provided
        patterns = None
        if pattern:
            patterns = {"custom": pattern}
        
        # Confirm unless dry-run or force
        if not dry_run and not force:
            feedback.running("Detecting orphaned branches...", step=1, total_steps=3)
            # Pre-scan to show what would be deleted
            orphaned = asyncio.run(service.detect_orphaned_branches(patterns=patterns))
            
            if orphaned:
                print(f"\n{'='*60}")
                print("Orphaned Branches Found:")
                print(f"{'='*60}")
                for branch in orphaned:
                    age_str = f" ({branch.metadata.age_days:.1f} days old)" if branch.metadata.age_days else ""
                    print(f"  • {branch.branch_name}{age_str}")
                    print(f"    Reason: {branch.reason}")
                print(f"{'='*60}")
                print(f"\nTotal: {len(orphaned)} branches")
                response = input("\nDelete these branches? (yes/no): ").strip().lower()
                if response not in ["yes", "y"]:
                    print("Cancelled.")
                    return
            else:
                print("\nNo orphaned branches found.")
                return
        
        feedback.running("Running cleanup...", step=2, total_steps=3)
        
        # Run cleanup
        report = asyncio.run(
            service.cleanup_orphaned_branches(
                dry_run=dry_run,
                patterns=patterns,
                max_age_days=retention_days,
            )
        )
        
        feedback.running("Cleanup complete", step=3, total_steps=3)
        feedback.clear_progress()
        
        # Display results
        if output_format == "json":
            import json
            result = {
                "total_branches_scanned": report.total_branches_scanned,
                "orphaned_branches_found": report.orphaned_branches_found,
                "branches_deleted": report.branches_deleted,
                "branches_failed": report.branches_failed,
                "dry_run": report.dry_run,
                "branches": [
                    {
                        "branch_name": b.branch_name,
                        "reason": b.reason,
                        "age_days": b.metadata.age_days,
                    }
                    for b in report.branches
                ],
                "errors": report.errors,
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*60}")
            print("Branch Cleanup Results")
            print(f"{'='*60}")
            print(f"Total branches scanned: {report.total_branches_scanned}")
            print(f"Orphaned branches found: {report.orphaned_branches_found}")
            if dry_run:
                print(f"Branches that would be deleted: {report.branches_deleted}")
            else:
                print(f"Branches deleted: {report.branches_deleted}")
                if report.branches_failed > 0:
                    print(f"Branches failed: {report.branches_failed}")
            print(f"{'='*60}")
            
            if report.branches:
                print("\nBranches:")
                for branch in report.branches:
                    age_str = f" ({branch.metadata.age_days:.1f} days old)" if branch.metadata.age_days else ""
                    status = "[DRY RUN]" if dry_run else "[DELETED]"
                    print(f"  {status} {branch.branch_name}{age_str}")
                    print(f"    Reason: {branch.reason}")
            
            if report.errors:
                print("\nErrors:")
                for error in report.errors:
                    print(f"  • {error}")
        
        feedback.success("Branch cleanup completed")
        
    except Exception as e:
        feedback.error(
            f"Error during branch cleanup: {e}",
            error_code="cleanup_error",
            exit_code=1,
        )
        import traceback
        traceback.print_exc()


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


def handle_continuous_bug_fix_command(args: object) -> None:
    """Handle continuous-bug-fix command"""
    import asyncio
    from ...continuous_bug_fix.continuous_bug_fixer import ContinuousBugFixer
    from ...core.config import load_config

    feedback = get_feedback()
    output_format = getattr(args, "format", "text")
    feedback.format_type = output_format

    # Parse arguments
    test_path = getattr(args, "test_path", None)
    max_iterations = getattr(args, "max_iterations", 10)
    commit_strategy = getattr(args, "commit_strategy", "one-per-bug")
    auto_commit = not getattr(args, "no_commit", False)
    proactive = getattr(args, "proactive", False)
    target_path = getattr(args, "target_path", None)
    max_bugs = getattr(args, "max_bugs", 20)

    # Load config
    config = load_config()

    # Override config with CLI args if defaults used
    continuous_config = getattr(config, "continuous_bug_fix", None)
    if test_path is None and continuous_config:
        test_path = continuous_config.test_path
    if max_iterations == 10 and continuous_config:
        max_iterations = continuous_config.max_iterations
    if commit_strategy == "one-per-bug" and continuous_config:
        commit_strategy = continuous_config.commit_strategy
    if auto_commit and continuous_config:
        auto_commit = continuous_config.auto_commit

    mode_str = "proactive bug discovery" if proactive else "test-based bug finding"
    feedback.start_operation(
        "Continuous Bug Fix",
        f"Running {mode_str} and fixing (max {max_iterations} iterations)...",
    )

    # Execute
    fixer = ContinuousBugFixer(config=config)

    try:
        result = asyncio.run(
            fixer.execute(
                test_path=test_path,
                max_iterations=max_iterations,
                commit_strategy=commit_strategy,
                auto_commit=auto_commit,
                proactive=proactive,
                target_path=target_path,
                max_bugs=max_bugs,
            )
        )

        feedback.clear_progress()

        # Format and output result
        if output_format == "json":
            feedback.output_result(result)
        else:
            _format_continuous_bug_fix_text_output(result, feedback)

    except KeyboardInterrupt:
        feedback.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        feedback.error(f"Error: {e}", exit_code=1)


def handle_brownfield_command(args: object) -> None:
    """Handle brownfield review command."""
    import logging

    from ...core.brownfield_review import BrownfieldReviewOrchestrator
    from ...context7.agent_integration import get_context7_helper
    from ...core.config import load_config

    logger = logging.getLogger(__name__)
    feedback = get_feedback()
    feedback.format_type = getattr(args, "format", "text")

    brownfield_command = getattr(args, "brownfield_command", None)
    if brownfield_command != "review":
        feedback.error(
            f"Unknown brownfield command: {brownfield_command}",
            exit_code=1,
        )
        return

    # Get arguments
    auto = getattr(args, "auto", False)
    dry_run = getattr(args, "dry_run", False)
    include_context7 = not getattr(args, "no_context7", False)
    output_dir = getattr(args, "output_dir", None)
    resume = getattr(args, "resume", False)
    resume_from = getattr(args, "resume_from", None)

    project_root = Path.cwd()
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = project_root / ".tapps-agents" / "brownfield-review"

    # Initialize Context7 helper if available
    config = load_config()
    context7_helper = None
    if include_context7:
        try:
            context7_helper = get_context7_helper(None, config, project_root)
        except Exception as e:
            logger.warning(f"Context7 helper not available: {e}")

    # Initialize orchestrator
    orchestrator = BrownfieldReviewOrchestrator(
        project_root=project_root,
        context7_helper=context7_helper,
        dry_run=dry_run,
    )

    feedback.start_operation(
        "Brownfield Review",
        "Analyzing codebase and creating experts...",
    )

    try:
        # Run review
        result = asyncio.run(
            orchestrator.review(
                auto=auto,
                include_context7=include_context7,
                resume=resume,
                resume_from=resume_from,
            )
        )

        feedback.clear_progress()

        # Save report
        output_dir.mkdir(parents=True, exist_ok=True)
        report_file = output_dir / "review-report.md"
        report_file.write_text(result.report, encoding="utf-8")

        # Output result
        if feedback.format_type == "json":
            import json

            result_dict = {
                "analysis": {
                    "languages": result.analysis.languages,
                    "frameworks": result.analysis.frameworks,
                    "dependencies": result.analysis.dependencies,
                    "domains": [
                        {
                            "domain": d.domain,
                            "confidence": d.confidence,
                        }
                        for d in result.analysis.domains
                    ],
                },
                "experts_created": len(result.experts_created),
                "rag_results": {
                    k: {
                        "entries_ingested": v.entries_ingested,
                        "entries_failed": v.entries_failed,
                    }
                    for k, v in result.rag_results.items()
                },
                "errors": result.errors,
                "warnings": result.warnings,
                "execution_time": result.execution_time,
                "dry_run": result.dry_run,
                "report_file": str(report_file),
            }
            feedback.output_result(result_dict)
        else:
            print("\n" + "=" * 80)
            print("Brownfield Review Complete")
            print("=" * 80)
            print()
            print(result.report)
            print()
            print(f"📄 Full report saved to: {report_file}")

    except KeyboardInterrupt:
        feedback.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        feedback.error(f"Brownfield review failed: {e}", exit_code=1)


def _format_continuous_bug_fix_text_output(result: dict[str, Any], feedback: Any) -> None:
    """Format continuous bug fix results as text"""
    print("\n" + "=" * 80)
    print("Continuous Bug Fix Results")
    print("=" * 80)
    print()

    print(f"Iterations Run: {result.get('iterations', 0)}")
    print(f"Bugs Found: {result.get('bugs_found', 0)}")
    print(f"Bugs Fixed: {result.get('bugs_fixed', 0)}")
    print(f"Bugs Failed: {result.get('bugs_failed', 0)}")
    print(f"Bugs Skipped: {result.get('bugs_skipped', 0)}")
    print()

    summary = result.get("summary", {})
    if summary:
        print("Summary:")
        print(f"  Fix Rate: {summary.get('fix_rate', 0) * 100:.1f}%")
        print(f"  Total Bugs Found: {summary.get('total_bugs_found', 0)}")
        print(f"  Total Bugs Fixed: {summary.get('total_bugs_fixed', 0)}")
        print(f"  Total Bugs Failed: {summary.get('total_bugs_failed', 0)}")
        print()

    results = result.get("results", [])
    if results:
        print("Iteration Details:")
        for iteration_result in results:
            iteration = iteration_result.get("iteration", 0)
            bugs_found = iteration_result.get("bugs_found", 0)
            bugs_fixed = iteration_result.get("bugs_fixed", 0)
            bugs_failed = iteration_result.get("bugs_failed", 0)
            print(
                f"  Iteration {iteration}: Found {bugs_found}, Fixed {bugs_fixed}, Failed {bugs_failed}"
            )
        print()

    if result.get("success"):
        print("[OK] Continuous bug fix completed successfully")
    else:
        print("[WARN] Continuous bug fix completed with some failures")


def handle_knowledge_command(args: object) -> None:
    """Handle knowledge base management commands."""
    from .knowledge import KnowledgeCommand
    from ..feedback import get_feedback
    
    feedback = get_feedback()
    command = getattr(args, "knowledge_command", None)
    output_format = getattr(args, "format", "text")
    feedback.format_type = output_format
    
    knowledge_cmd = KnowledgeCommand()
    
    if command == "validate":
        knowledge_dir = getattr(args, "knowledge_dir", None)
        result = knowledge_cmd.validate(knowledge_dir=knowledge_dir)
        
        if output_format == "json":
            format_json_output(result)
        else:
            summary = result["summary"]
            print("\n" + "=" * 70)
            print("Knowledge Base Validation Results")
            print("=" * 70)
            print(f"\nTotal Files: {summary['total_files']}")
            print(f"Valid Files: {summary['valid_files']}")
            print(f"Invalid Files: {summary['invalid_files']}")
            print(f"Total Issues: {summary['total_issues']}")
            print(f"\nIssues by Severity:")
            for severity, count in summary["issues_by_severity"].items():
                print(f"  {severity.capitalize()}: {count}")
            
            # Show files with issues
            files_with_issues = [r for r in result["results"] if r["issues"]]
            if files_with_issues:
                print(f"\nFiles with Issues ({len(files_with_issues)}):")
                for file_result in files_with_issues[:10]:  # Limit to 10
                    print(f"\n  {file_result['file']}:")
                    for issue in file_result["issues"][:5]:  # Limit to 5 issues per file
                        line_info = f" (line {issue['line']})" if issue["line"] else ""
                        print(f"    [{issue['severity'].upper()}] {issue['message']}{line_info}")
    
    elif command == "metrics":
        result = knowledge_cmd.metrics()
        
        if output_format == "json":
            format_json_output(result)
        else:
            metrics = result["metrics"]
            print("\n" + "=" * 70)
            print("RAG Performance Metrics")
            print("=" * 70)
            print(f"\nTotal Queries: {metrics['total_queries']}")
            print(f"Average Latency: {metrics['avg_latency_ms']} ms")
            print(f"Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")
            print(f"Average Results: {metrics['avg_results']:.1f}")
            print(f"Average Similarity: {metrics['avg_similarity']:.3f}")
            print(f"\nBackend Usage:")
            for backend, count in metrics["backend_usage"].items():
                print(f"  {backend}: {count}")
            print(f"\nSimilarity Distribution:")
            for level, count in metrics["similarity_distribution"].items():
                print(f"  {level}: {count}")
            
            if result["recent_queries"]:
                print(f"\nRecent Queries (last {len(result['recent_queries'])}):")
                for q in result["recent_queries"][:5]:
                    print(f"  [{q['timestamp']}] {q['expert_id']}: {q['query'][:50]}...")
    
    elif command == "freshness":
        knowledge_dir = getattr(args, "knowledge_dir", None)
        scan = getattr(args, "scan", False)
        result = knowledge_cmd.freshness(knowledge_dir=knowledge_dir, scan=scan)
        
        if output_format == "json":
            format_json_output(result)
        else:
            summary = result["summary"]
            print("\n" + "=" * 70)
            print("Knowledge Base Freshness")
            print("=" * 70)
            print(f"\nTotal Files: {summary['total_files']}")
            print(f"Tracked Files: {summary['tracked_files']}")
            print(f"Coverage: {summary['coverage']:.1f}%")
            print(f"Deprecated Files: {summary['deprecated_files']}")
            print(f"Stale Files (>365 days): {summary['stale_files']}")
            
            if result.get("scan_results"):
                scan_res = result["scan_results"]
                print(f"\nScan Results:")
                print(f"  Scanned: {scan_res['scanned']}")
                print(f"  Updated: {scan_res['updated']}")
                print(f"  New Files: {scan_res['new_files']}")
            
            if result.get("stale_files"):
                print(f"\nStale Files (showing first 10):")
                for stale in result["stale_files"]:
                    print(f"  {stale['file']}: last updated {stale['last_updated']}")
            
            if result.get("deprecated_files"):
                print(f"\nDeprecated Files:")
                for dep in result["deprecated_files"]:
                    print(f"  {dep['file']}: deprecated {dep['deprecation_date']}")
                    if dep.get("replacement"):
                        print(f"    -> Replacement: {dep['replacement']}")
    
    else:
        print(f"Unknown knowledge command: {command}", file=sys.stderr)
        sys.exit(1)
