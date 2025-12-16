"""
Top-level command handlers (create, init, workflow, score, doctor, hardware-profile, analytics, setup-experts)
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


def handle_workflow_command(args: object) -> None:
    """Handle workflow command"""
    from ...workflow.executor import WorkflowExecutor
    from ...workflow.preset_loader import PresetLoader

    loader = PresetLoader()

    preset_name = getattr(args, "preset", None)

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
        
        if tech_stack.get("frameworks"):
            print(f"  Frameworks: {', '.join(tech_stack['frameworks'])}")
        
        if tech_stack.get("package_managers"):
            print(f"  Package Managers: {', '.join(tech_stack['package_managers'])}")
        
        if tech_stack.get("libraries"):
            lib_count = len(tech_stack["libraries"])
            print(f"  Libraries Detected: {lib_count}")
            if lib_count > 0 and lib_count <= 20:
                print(f"    {', '.join(tech_stack['libraries'][:20])}")
            elif lib_count > 20:
                print(f"    {', '.join(tech_stack['libraries'][:20])} ...")
                print(f"    (and {lib_count - 20} more)")
        
        if tech_stack.get("detected_files"):
            print(f"  Detected Files: {', '.join(tech_stack['detected_files'])}")

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

