"""
Top-level command handlers (create, init, workflow, score, doctor, hardware-profile, analytics, setup-experts, customize)
"""
import asyncio
import json
import sys
from pathlib import Path

from .reviewer import score_command
from .common import format_json_output


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
    
    # If user wants to set a profile
    if set_profile:
        # Validate profile
        valid_profiles = ["auto", "nuc", "development", "workstation", "server"]
        if set_profile.lower() not in valid_profiles:
            print(
                f"Error: Invalid profile '{set_profile}'. "
                f"Valid options: {', '.join(valid_profiles)}",
                file=sys.stderr,
            )
            sys.exit(1)
        
        # Update configuration
        config.hardware_profile = set_profile.lower()
        if set_profile.lower() == "auto":
            config.hardware_auto_detect = True
            config.detected_profile = detected_profile.value
        else:
            config.hardware_auto_detect = False
            config.detected_profile = set_profile.lower()
        
        config_manager.save(config)
        
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
            print(json.dumps(result, indent=2))
        else:
            print(f"\nHardware profile set to: {set_profile.lower()}")
            if set_profile.lower() == "auto":
                print(f"  Auto-detection enabled (detected: {detected_profile.value})")
            else:
                print(f"  Auto-detection disabled (using: {set_profile.lower()})")
            print(f"\nConfiguration saved to: {config_manager.config_path}")
    else:
        # Just show current status
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
            print(json.dumps(result, indent=2))
        else:
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
    from ...workflow.executor import WorkflowExecutor
    from ...workflow.preset_loader import PresetLoader

    loader = PresetLoader()
    workflow_name = getattr(args, "workflow", "full")
    user_prompt = getattr(args, "prompt", "")

    if not user_prompt:
        print("Error: Prompt/description required", file=sys.stderr)
        print("Usage: python -m tapps_agents.cli create \"Your project description\"", file=sys.stderr)
        sys.exit(1)

    try:
        workflow = loader.load_preset(workflow_name)
        if not workflow:
            print(f"Error: Workflow preset '{workflow_name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"Creating Project: {workflow.name}")
        print(f"{'='*60}")
        print(f"Description: {workflow.description}")
        print(f"Your Prompt: {user_prompt}")
        print(f"Steps: {len(workflow.steps)}")
        print("Mode: Auto (fully automated)")
        print()

        # Execute workflow with auto mode and prompt
        executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
        executor.user_prompt = user_prompt

        result = asyncio.run(executor.execute(workflow=workflow, target_file=None))

        if result.status == "completed":
            print(f"\n{'='*60}")
            print("Project created successfully!")
            print(f"{'='*60}")
            print("Timeline: project-timeline.md")
            print(f"Status: {result.status}")
        elif result.status == "failed":
            print(f"\nError: {result.error or 'Unknown error'}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\nWorkflow status: {result.status}")

    except Exception as e:
        print(f"Error creating project: {e}", file=sys.stderr)
        sys.exit(1)


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
                                print(f"\n✅ Loaded workflow: {workflow.name}")
                            else:
                                print(f"\n⚠️  Workflow file not found: {workflow_path}")
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
                                print(f"\n✅ Selected: {selected['name']}")
                                if auto_load:
                                    workflow_path = Path("workflows") / selected["file"]
                                    if workflow_path.exists():
                                        from ...workflow.executor import WorkflowExecutor
                                        executor = WorkflowExecutor(auto_detect=False)
                                        workflow = executor.load_workflow(workflow_path)
                                        print(f"✅ Loaded workflow: {workflow.name}")
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
    from ...workflow.state_manager import AdvancedStateManager
    from pathlib import Path
    import json

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
            print("Error: Unknown state command. Use 'list', 'show', or 'cleanup'.", file=sys.stderr)
            sys.exit(1)
    
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
        presets = loader.list_presets()
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
        
        result = asyncio.run(
            executor.execute(workflow=workflow, target_file=target_file)
        )

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


def handle_init_command(args: object) -> None:
    """Handle init command"""
    from ...core.init_project import init_project

    print("\n" + "=" * 60)
    print("TappsCodingAgents Project Initialization")
    print("=" * 60)
    print()

    results = init_project(
        include_cursor_rules=not getattr(args, "no_rules", False),
        include_workflow_presets=not getattr(args, "no_presets", False),
        include_config=not getattr(args, "no_config", False),
        include_skills=not getattr(args, "no_skills", False),
        include_background_agents=not getattr(args, "no_background_agents", False),
        include_cursorignore=not getattr(args, "no_cursorignore", False),
        pre_populate_cache=not getattr(args, "no_cache", False),
    )

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

    # Show validation results
    if results.get("validation"):
        validation = results["validation"]
        print("\n" + "=" * 60)
        print("Setup Validation")
        print("=" * 60)
        
        if validation.get("overall_valid"):
            print("  Status: ✓ All validations passed")
        else:
            print("  Status: ✗ Some validations failed")
        
        if validation.get("all_errors"):
            print("\n  Errors:")
            for error in validation["all_errors"]:
                print(f"    ✗ {error}")
        
        if validation.get("all_warnings"):
            print("\n  Warnings:")
            for warning in validation["all_warnings"]:
                print(f"    ⚠ {warning}")
        
        # Show summary
        cursor_rules = validation.get("cursor_rules", {})
        claude_skills = validation.get("claude_skills", {})
        bg_agents = validation.get("background_agents", {})
        
        print("\n  Summary:")
        print(f"    Cursor Rules: {len(cursor_rules.get('rules_found', []))} found")
        print(f"    Claude Skills: {len(claude_skills.get('skills_found', []))} found")
        print(f"    Background Agents: {'✓' if bg_agents.get('valid') else '✗'}")
    
    # Show tech stack detection
    if results.get("tech_stack"):
        tech_stack = results["tech_stack"]
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

    # Show cache pre-population results
    if results.get("cache_prepopulated") is not None:
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
            print(f"  Status: ✅ Success")
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
                print(f"  Status: ❌ Failed")
                print(f"  Error: {cache_error}")
            elif cache_result:
                error_msg = cache_result.get("error", "Unknown error")
                print(f"  Status: ❌ Failed")
                print(f"  Error: {error_msg}")
                if cache_result.get("cached") == 0 and cache_result.get("total") == 0:
                    print("  Note: Context7 may not be enabled in configuration")
                    print("        Check .tapps-agents/config.yaml and ensure context7.enabled: true")
            else:
                print(f"  Status: ⚠️  Skipped")
                print("  Note: Cache pre-population was not attempted")

    # Run environment diagnostics
    print("\n" + "=" * 60)
    print("Environment Check")
    print("=" * 60)
    print()

    try:
        from ...core.doctor import collect_doctor_report
        
        doctor_report = collect_doctor_report(
            project_root=Path(results["project_root"])
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

    print("Next Steps:")
    print("  1. Set up experts: python -m tapps_agents.cli setup-experts init")
    print("  2. List workflows: python -m tapps_agents.cli workflow list")
    print("  3. Run a workflow: python -m tapps_agents.cli workflow rapid")
    print("  4. Full environment check: python -m tapps_agents.cli doctor")
    print()


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
                print("\n✅ Development tools installed successfully!")
                print("Run 'python -m tapps_agents.cli doctor' to verify installation.")
            else:
                print(f"\n❌ Installation failed with exit code {result.returncode}")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error installing development tools: {e}")
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
    from ...workflow.state_manager import AdvancedStateManager
    from pathlib import Path
    import json
    from datetime import datetime

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
    from ...workflow.state_manager import AdvancedStateManager
    from pathlib import Path
    import json

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
    from ...workflow.state_manager import AdvancedStateManager
    from pathlib import Path

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
    from ...workflow.executor import WorkflowExecutor
    from pathlib import Path

    workflow_id = getattr(args, "workflow_id", None)
    validate = getattr(args, "validate", True)
    
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
        
        print(f"\n{'='*60}")
        print(f"Resuming: {executor.workflow.name}")
        print(f"{'='*60}")
        print(f"Workflow ID: {executor.state.workflow_id}")
        print(f"Status: {executor.state.status}")
        print(f"Current Step: {executor.state.current_step or 'N/A'}")
        print()
        
        # Resume execution
        result = asyncio.run(executor.run())
        
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
        print(f"Error resuming workflow: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

