"""
Command-line interface for TappsCodingAgents
"""

import asyncio
import json
import sys
from pathlib import Path

from .agents.analyst.agent import AnalystAgent
from .agents.architect.agent import ArchitectAgent
from .agents.debugger.agent import DebuggerAgent
from .agents.designer.agent import DesignerAgent
from .agents.documenter.agent import DocumenterAgent
from .agents.enhancer.agent import EnhancerAgent
from .agents.implementer.agent import ImplementerAgent
from .agents.improver.agent import ImproverAgent
from .agents.ops.agent import OpsAgent
from .agents.orchestrator.agent import OrchestratorAgent
from .agents.planner.agent import PlannerAgent
from .agents.reviewer.agent import ReviewerAgent
from .agents.tester.agent import TesterAgent
from .core.doctor import collect_doctor_report
from .core.hardware_profiler import HardwareProfile, HardwareProfiler
from .core.unified_cache_config import UnifiedCacheConfigManager


async def review_command(
    file_path: str, model: str | None = None, output_format: str = "json"
):
    """Review a code file (supports both *review and review commands)"""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    reviewer = ReviewerAgent()
    try:
        # Activate agent (load configs, etc.)
        await reviewer.activate()

        # Execute review command
        result = await reviewer.run(
            "review", file=file_path, model=model or "qwen2.5-coder:7b"
        )

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            # Simple text format
            print(f"Review: {result['file']}")
            if "scoring" in result:
                scores = result["scoring"]
                print("\nScores:")
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Overall: {scores['overall_score']:.1f}/100")
                print(f"\nPassed: {result.get('passed', False)}")

            if "feedback" in result and "summary" in result["feedback"]:
                print(f"\nFeedback:\n{result['feedback']['summary']}")
    finally:
        await reviewer.close()


async def score_command(file_path: str, output_format: str = "json"):
    """Score a code file (supports both *score and score commands)"""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        result = await reviewer.run("score", file=file_path)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Scores for: {result['file']}")
            if "scoring" in result:
                scores = result["scoring"]
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Overall: {scores['overall_score']:.1f}/100")
    finally:
        await reviewer.close()


async def help_command():
    """Show help (supports both *help and help commands)"""
    reviewer = ReviewerAgent()
    await reviewer.activate()
    result = await reviewer.run("help")
    print(result["content"])


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


async def plan_command(description: str, output_format: str = "json"):
    """Create a plan for a feature/requirement"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("plan", description=description)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Plan: {result['description']}")
            print(f"\n{result.get('plan', '')}")
    finally:
        await planner.close()


async def create_story_command(
    description: str,
    epic: str | None = None,
    priority: str = "medium",
    output_format: str = "json",
):
    """Generate a user story from description"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run(
            "create-story", description=description, epic=epic, priority=priority
        )

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Story created: {result['story_id']}")
            print(f"File: {result['story_file']}")
            print(f"\nTitle: {result['metadata']['title']}")
            print(f"Epic: {result['metadata']['epic']}")
            print(f"Priority: {result['metadata']['priority']}")
            print(f"Complexity: {result['metadata']['complexity']}/5")
    finally:
        await planner.close()


async def list_stories_command(
    epic: str | None = None,
    status: str | None = None,
    output_format: str = "json",
):
    """List all stories in the project"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("list-stories", epic=epic, status=status)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Found {result['count']} stories")
            for story in result["stories"]:
                print(f"\n{story['story_id']}: {story['title']}")
                print(
                    f"  Epic: {story['epic']}, Status: {story['status']}, Priority: {story['priority']}"
                )
    finally:
        await planner.close()


async def implement_command(
    specification: str,
    file_path: str,
    context: str | None = None,
    language: str = "python",
    output_format: str = "json",
):
    """Generate and write code to file (with review)"""
    implementer = ImplementerAgent()
    try:
        await implementer.activate()
        result = await implementer.run(
            "implement",
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
        )

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Code implemented: {result['file']}")
            print(f"Approved: {result['approved']}")
            if result.get("backup"):
                print(f"Backup created: {result['backup']}")
    finally:
        await implementer.close()


async def generate_code_command(
    specification: str,
    file_path: str | None = None,
    context: str | None = None,
    language: str = "python",
    output_format: str = "json",
):
    """Generate code from specification (no file write)"""
    implementer = ImplementerAgent()
    try:
        await implementer.activate()
        result = await implementer.run(
            "generate-code",
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
        )

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print("Generated Code:")
            print("-" * 40)
            print(result["code"])
    finally:
        await implementer.close()


async def refactor_command(
    file_path: str, instruction: str, output_format: str = "json"
):
    """Refactor existing code file"""
    implementer = ImplementerAgent()
    try:
        await implementer.activate()
        result = await implementer.run(
            "refactor", file_path=file_path, instruction=instruction
        )

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Refactored: {result['file']}")
            print(f"Approved: {result['approved']}")
            if result.get("backup"):
                print(f"Backup created: {result['backup']}")
    finally:
        await implementer.close()


def _handle_planner_command(args: object) -> None:
    """Handle planner agent commands"""
    command = args.command.lstrip("*") if args.command else None
    if command == "plan":
        asyncio.run(plan_command(args.description, getattr(args, "format", "json")))
    elif command == "create-story":
        asyncio.run(
            create_story_command(
                args.description,
                epic=getattr(args, "epic", None),
                priority=getattr(args, "priority", "medium"),
                output_format=getattr(args, "format", "json"),
            )
        )
    elif command == "list-stories":
        asyncio.run(
            list_stories_command(
                epic=getattr(args, "epic", None),
                status=getattr(args, "status", None),
                output_format=getattr(args, "format", "json"),
            )
        )
    elif command == "help":
        planner = PlannerAgent()
        asyncio.run(planner.activate())
        result = asyncio.run(planner.run("help"))
        print(result["content"])
        asyncio.run(planner.close())
    else:
        planner = PlannerAgent()
        asyncio.run(planner.activate())
        result = asyncio.run(planner.run("help"))
        print(result["content"])
        asyncio.run(planner.close())


def _handle_implementer_command(args: object) -> None:
    """Handle implementer agent commands"""
    command = args.command.lstrip("*") if args.command else None
    if command == "implement":
        asyncio.run(
            implement_command(
                args.specification,
                args.file_path,
                context=getattr(args, "context", None),
                language=getattr(args, "language", "python"),
                output_format=getattr(args, "format", "json"),
            )
        )
    elif command == "generate-code":
        asyncio.run(
            generate_code_command(
                args.specification,
                file_path=getattr(args, "file", None),
                context=getattr(args, "context", None),
                language=getattr(args, "language", "python"),
                output_format=getattr(args, "format", "json"),
            )
        )
    elif command == "refactor":
        asyncio.run(
            refactor_command(
                args.file_path,
                args.instruction,
                output_format=getattr(args, "format", "json"),
            )
        )
    elif command == "help":
        implementer = ImplementerAgent()
        asyncio.run(implementer.activate())
        result = asyncio.run(implementer.run("help"))
        print(result["content"])
        asyncio.run(implementer.close())
    else:
        implementer = ImplementerAgent()
        asyncio.run(implementer.activate())
        result = asyncio.run(implementer.run("help"))
        print(result["content"])
        asyncio.run(implementer.close())


def _handle_tester_command(args: object) -> None:
    """Handle tester agent commands"""
    command = args.command.lstrip("*") if args.command else None
    tester = TesterAgent()
    asyncio.run(tester.activate())
    try:
        if command == "test":
            result = asyncio.run(
                tester.run(
                    "test",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
        elif command == "generate-tests":
            result = asyncio.run(
                tester.run(
                    "generate-tests",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
        elif command == "run-tests":
            result = asyncio.run(
                tester.run(
                    "run-tests",
                    test_path=getattr(args, "test_path", None),
                    coverage=not getattr(args, "no_coverage", False),
                )
            )
        elif command == "help":
            result = asyncio.run(tester.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(tester.run("help"))
            print(result["content"])
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(tester.close())


def _handle_debugger_command(args: object) -> None:
    """Handle debugger agent commands"""
    command = args.command.lstrip("*") if args.command else None
    debugger = DebuggerAgent()
    asyncio.run(debugger.activate())
    try:
        if command == "debug":
            result = asyncio.run(
                debugger.run(
                    "debug",
                    error_message=args.error_message,
                    file=getattr(args, "file", None),
                    line=getattr(args, "line", None),
                    stack_trace=getattr(args, "stack_trace", None),
                )
            )
        elif command == "analyze-error":
            result = asyncio.run(
                debugger.run(
                    "analyze-error",
                    error_message=args.error_message,
                    stack_trace=getattr(args, "stack_trace", None),
                    code_context=getattr(args, "code_context", None),
                )
            )
        elif command == "trace":
            result = asyncio.run(
                debugger.run(
                    "trace",
                    file=args.file,
                    function=getattr(args, "function", None),
                    line=getattr(args, "line", None),
                )
            )
        elif command == "help":
            result = asyncio.run(debugger.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(debugger.run("help"))
            print(result["content"])
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(debugger.close())


def _handle_documenter_command(args: object) -> None:
    """Handle documenter agent commands"""
    command = args.command.lstrip("*") if args.command else None
    documenter = DocumenterAgent()
    asyncio.run(documenter.activate())
    try:
        if command == "document":
            result = asyncio.run(
                documenter.run(
                    "document",
                    file=args.file,
                    output_format=getattr(args, "output_format", "markdown"),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "generate-docs":
            result = asyncio.run(
                documenter.run(
                    "generate-docs",
                    file=args.file,
                    output_format=getattr(args, "output_format", "markdown"),
                )
            )
        elif command == "update-readme":
            result = asyncio.run(
                documenter.run(
                    "update-readme",
                    project_root=getattr(args, "project_root", None),
                    context=getattr(args, "context", None),
                )
            )
        elif command == "update-docstrings":
            result = asyncio.run(
                documenter.run(
                    "update-docstrings",
                    file=args.file,
                    docstring_format=getattr(args, "docstring_format", None),
                    write_file=getattr(args, "write_file", False),
                )
            )
        elif command == "help":
            result = asyncio.run(documenter.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(documenter.run("help"))
            print(result["content"])
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(documenter.close())


def _handle_orchestrator_command(args: object) -> None:
    """Handle orchestrator agent commands"""
    command = args.command.lstrip("*") if args.command else None
    orchestrator = OrchestratorAgent()
    asyncio.run(orchestrator.activate())
    try:
        if command == "workflow-list" or command == "*workflow-list":
            result = asyncio.run(orchestrator.run("*workflow-list"))
        elif command == "workflow-start" or command == "*workflow-start":
            workflow_id = getattr(args, "workflow_id", None)
            if not workflow_id:
                print("Error: workflow_id required", file=sys.stderr)
                sys.exit(1)
            result = asyncio.run(
                orchestrator.run("*workflow-start", workflow_id=workflow_id)
            )
        elif command == "workflow-status" or command == "*workflow-status":
            result = asyncio.run(orchestrator.run("*workflow-status"))
        elif command == "workflow-next" or command == "*workflow-next":
            result = asyncio.run(orchestrator.run("*workflow-next"))
        elif command == "workflow-skip" or command == "*workflow-skip":
            step_id = getattr(args, "step_id", None)
            if not step_id:
                print("Error: step_id required", file=sys.stderr)
                sys.exit(1)
            result = asyncio.run(orchestrator.run("*workflow-skip", step_id=step_id))
        elif command == "workflow-resume" or command == "*workflow-resume":
            result = asyncio.run(orchestrator.run("*workflow-resume"))
        elif command == "gate" or command == "*gate":
            condition = getattr(args, "condition", None)
            scoring_data = getattr(args, "scoring_data", {})
            if isinstance(scoring_data, str):
                scoring_data = json.loads(scoring_data)
            result = asyncio.run(
                orchestrator.run(
                    "*gate", condition=condition, scoring_data=scoring_data
                )
            )
        elif command == "help" or command == "*help":
            result = asyncio.run(orchestrator.run("*help"))
        else:
            result = asyncio.run(orchestrator.run("*help"))
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(orchestrator.close())


def _handle_analyst_command(args: object) -> None:
    """Handle analyst agent commands"""
    command = args.command.lstrip("*") if args.command else None
    analyst = AnalystAgent()
    asyncio.run(analyst.activate())
    try:
        if command == "gather-requirements":
            result = asyncio.run(
                analyst.run(
                    "gather-requirements",
                    description=args.description,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "stakeholder-analysis":
            result = asyncio.run(
                analyst.run(
                    "analyze-stakeholders",
                    description=args.description,
                    stakeholders=getattr(args, "stakeholders", []),
                )
            )
        elif command == "tech-research":
            result = asyncio.run(
                analyst.run(
                    "research-technology",
                    requirement=args.requirement,
                    context=getattr(args, "context", ""),
                    criteria=getattr(args, "criteria", []),
                )
            )
        elif command == "estimate-effort":
            result = asyncio.run(
                analyst.run(
                    "estimate-effort",
                    feature_description=args.feature_description,
                    context=getattr(args, "context", ""),
                )
            )
        elif command == "assess-risk":
            result = asyncio.run(
                analyst.run(
                    "assess-risk",
                    feature_description=args.feature_description,
                    context=getattr(args, "context", ""),
                )
            )
        elif command == "competitive-analysis":
            result = asyncio.run(
                analyst.run(
                    "competitive-analysis",
                    product_description=args.product_description,
                    competitors=getattr(args, "competitors", []),
                )
            )
        elif command == "help":
            result = asyncio.run(analyst.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(analyst.run("help"))
            print(result["content"])
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(analyst.close())


def _handle_architect_command(args: object) -> None:
    """Handle architect agent commands"""
    command = args.command.lstrip("*") if args.command else None
    architect = ArchitectAgent()
    asyncio.run(architect.activate())
    try:
        if command == "design-system":
            result = asyncio.run(
                architect.run(
                    "design-system",
                    requirements=args.requirements,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "architecture-diagram":
            result = asyncio.run(
                architect.run(
                    "create-diagram",
                    architecture_description=args.architecture_description,
                    diagram_type=getattr(args, "diagram_type", "component"),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "tech-selection":
            result = asyncio.run(
                architect.run(
                    "select-technology",
                    component_description=args.component_description,
                    requirements=getattr(args, "requirements", ""),
                    constraints=getattr(args, "constraints", []),
                )
            )
        elif command == "design-security":
            result = asyncio.run(
                architect.run(
                    "design-security",
                    system_description=args.system_description,
                    threat_model=getattr(args, "threat_model", ""),
                )
            )
        elif command == "define-boundaries":
            result = asyncio.run(
                architect.run(
                    "define-boundaries",
                    system_description=args.system_description,
                    context=getattr(args, "context", ""),
                )
            )
        elif command == "help":
            result = asyncio.run(architect.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(architect.run("help"))
            print(result["content"])
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(architect.close())


def _handle_designer_command(args: object) -> None:
    """Handle designer agent commands"""
    command = args.command.lstrip("*") if args.command else None
    designer = DesignerAgent()
    asyncio.run(designer.activate())
    try:
        if command == "design-api":
            result = asyncio.run(
                designer.run(
                    "design-api",
                    requirements=args.requirements,
                    api_type=getattr(args, "api_type", "REST"),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "design-data-model":
            result = asyncio.run(
                designer.run(
                    "design-data-model",
                    requirements=args.requirements,
                    data_source=getattr(args, "data_source", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "design-ui":
            result = asyncio.run(
                designer.run(
                    "design-ui",
                    feature_description=args.feature_description,
                    user_stories=getattr(args, "user_stories", []),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "create-wireframe":
            result = asyncio.run(
                designer.run(
                    "create-wireframe",
                    screen_description=args.screen_description,
                    wireframe_type=getattr(args, "wireframe_type", "page"),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "define-design-system":
            result = asyncio.run(
                designer.run(
                    "define-design-system",
                    project_description=args.project_description,
                    brand_guidelines=getattr(args, "brand_guidelines", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "help":
            result = asyncio.run(designer.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(designer.run("help"))
            print(result["content"])
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
    finally:
        asyncio.run(designer.close())


def _handle_reviewer_command(args: object) -> None:
    """Handle reviewer agent commands"""
    command = args.command.lstrip("*") if args.command else None
    if command == "review":
        asyncio.run(
            review_command(args.file, args.model, getattr(args, "format", "json"))
        )
    elif command == "score":
        asyncio.run(score_command(args.file, getattr(args, "format", "json")))
    elif command == "lint":
        reviewer = ReviewerAgent()
        asyncio.run(reviewer.activate())
        result = asyncio.run(reviewer.run("lint", file=args.file))
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        output_format = getattr(args, "format", "json")
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            if "issues" in result:
                print(f"Linting issues for {args.file}:")
                for issue in result["issues"]:
                    print(
                        f"  {issue.get('code', '')}: {issue.get('message', '')} (line {issue.get('line', '?')})"
                    )
        asyncio.run(reviewer.close())
    elif command == "type-check":
        reviewer = ReviewerAgent()
        asyncio.run(reviewer.activate())
        result = asyncio.run(reviewer.run("type-check", file=args.file))
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        output_format = getattr(args, "format", "json")
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            if "errors" in result:
                print(f"Type checking errors for {args.file}:")
                for error in result["errors"]:
                    print(
                        f"  {error.get('message', '')} (line {error.get('line', '?')})"
                    )
        asyncio.run(reviewer.close())
    elif command == "report":
        reviewer = ReviewerAgent()
        asyncio.run(reviewer.activate())
        formats = getattr(args, "formats", ["all"])
        if "all" in formats:
            format_type = "all"
        else:
            format_type = ",".join(formats)
        result = asyncio.run(
            reviewer.run(
                "report",
                target=args.target,
                format=format_type,
                output_dir=getattr(args, "output_dir", None),
            )
        )
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
        asyncio.run(reviewer.close())
    elif command == "duplication":
        reviewer = ReviewerAgent()
        asyncio.run(reviewer.activate())
        result = asyncio.run(reviewer.run("duplication", file=args.target))
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        output_format = getattr(args, "format", "json")
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            if "duplicates" in result:
                print(f"Code duplication detected in {args.target}:")
                print(f"  Total duplicates: {len(result.get('duplicates', []))}")
        asyncio.run(reviewer.close())
    elif command == "analyze-project":
        reviewer = ReviewerAgent()
        asyncio.run(reviewer.activate())
        result = asyncio.run(
            reviewer.run(
                "analyze-project",
                project_root=getattr(args, "project_root", None),
                include_comparison=not getattr(args, "no_comparison", False),
            )
        )
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        output_format = getattr(args, "format", "json")
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print("Project analysis complete. See JSON output for details.")
        asyncio.run(reviewer.close())
    elif command == "analyze-services":
        reviewer = ReviewerAgent()
        asyncio.run(reviewer.activate())
        services = getattr(args, "services", None)
        result = asyncio.run(
            reviewer.run(
                "analyze-services",
                services=services if services else None,
                project_root=getattr(args, "project_root", None),
                include_comparison=not getattr(args, "no_comparison", False),
            )
        )
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        output_format = getattr(args, "format", "json")
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print("Service analysis complete. See JSON output for details.")
        asyncio.run(reviewer.close())
    elif command == "help":
        asyncio.run(help_command())
    else:
        asyncio.run(help_command())


def main():
    """Main CLI entry point - supports both *command and command formats"""
    import argparse

    parser = argparse.ArgumentParser(
        description="TappsCodingAgents CLI - AI coding agents framework",
        epilog="""Quick shortcuts:
  score <file>          - Score a code file (shortcut for 'reviewer score')
  init                  - Initialize project (Cursor Rules + workflow presets)
  workflow <preset>     - Run preset workflows (rapid, full, fix, quality, hotfix)
  
Examples:
  python -m tapps_agents.cli score example.py
  python -m tapps_agents.cli init
  python -m tapps_agents.cli workflow rapid""",
    )
    subparsers = parser.add_subparsers(dest="agent", help="Agent or command to use")

    # Reviewer agent commands
    reviewer_parser = subparsers.add_parser("reviewer", help="Reviewer Agent commands")
    reviewer_subparsers = reviewer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    review_parser = reviewer_subparsers.add_parser(
        "review", aliases=["*review"], help="Review a code file"
    )
    review_parser.add_argument("file", help="Path to code file")
    review_parser.add_argument(
        "--model", help="LLM model to use", default="qwen2.5-coder:7b"
    )
    review_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    score_parser = reviewer_subparsers.add_parser(
        "score", aliases=["*score"], help="Calculate code scores only"
    )
    score_parser.add_argument("file", help="Path to code file")
    score_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    lint_parser = reviewer_subparsers.add_parser(
        "lint", aliases=["*lint"], help="Run Ruff linting on a file (Phase 6.1)"
    )
    lint_parser.add_argument("file", help="Path to code file")
    lint_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    type_check_parser = reviewer_subparsers.add_parser(
        "type-check",
        aliases=["*type-check"],
        help="Run mypy type checking on a file (Phase 6.2)",
    )
    type_check_parser.add_argument("file", help="Path to code file")
    type_check_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    report_parser = reviewer_subparsers.add_parser(
        "report",
        aliases=["*report"],
        help="Generate quality reports in multiple formats (Phase 6.3)",
    )
    report_parser.add_argument("target", help="File or directory path to analyze")
    report_parser.add_argument(
        "formats",
        nargs="+",
        choices=["json", "markdown", "html", "all"],
        help="Output formats",
    )
    report_parser.add_argument(
        "--output-dir", help="Output directory for reports (default: reports/quality/)"
    )

    duplication_parser = reviewer_subparsers.add_parser(
        "duplication",
        aliases=["*duplication"],
        help="Detect code duplication using jscpd (Phase 6.4)",
    )
    duplication_parser.add_argument("target", help="File or directory path to analyze")
    duplication_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    analyze_project_parser = reviewer_subparsers.add_parser(
        "analyze-project",
        aliases=["*analyze-project"],
        help="Analyze entire project with all services (Phase 6.4.2)",
    )
    analyze_project_parser.add_argument(
        "--project-root", help="Project root directory (default: current directory)"
    )
    analyze_project_parser.add_argument(
        "--no-comparison",
        action="store_true",
        help="Skip comparison with previous analysis",
    )
    analyze_project_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    analyze_services_parser = reviewer_subparsers.add_parser(
        "analyze-services",
        aliases=["*analyze-services"],
        help="Analyze specific services (Phase 6.4.2)",
    )
    analyze_services_parser.add_argument(
        "services",
        nargs="*",
        help="Service names or patterns to analyze (default: all services)",
    )
    analyze_services_parser.add_argument(
        "--project-root", help="Project root directory (default: current directory)"
    )
    analyze_services_parser.add_argument(
        "--no-comparison",
        action="store_true",
        help="Skip comparison with previous analysis",
    )
    analyze_services_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    reviewer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show reviewer commands"
    )

    # Planner agent commands
    planner_parser = subparsers.add_parser("planner", help="Planner Agent commands")
    planner_subparsers = planner_parser.add_subparsers(dest="command", help="Commands")

    plan_parser = planner_subparsers.add_parser(
        "plan", aliases=["*plan"], help="Create a plan for a feature"
    )
    plan_parser.add_argument("description", help="Feature/requirement description")
    plan_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    create_story_parser = planner_subparsers.add_parser(
        "create-story", aliases=["*create-story"], help="Generate a user story"
    )
    create_story_parser.add_argument("description", help="Story description")
    create_story_parser.add_argument("--epic", help="Epic or feature area")
    create_story_parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority",
    )
    create_story_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    list_stories_parser = planner_subparsers.add_parser(
        "list-stories", aliases=["*list-stories"], help="List all stories"
    )
    list_stories_parser.add_argument("--epic", help="Filter by epic")
    list_stories_parser.add_argument("--status", help="Filter by status")
    list_stories_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    planner_subparsers.add_parser(
        "help", aliases=["*help"], help="Show planner commands"
    )

    # Implementer agent commands
    implementer_parser = subparsers.add_parser(
        "implementer", help="Implementer Agent commands"
    )
    implementer_subparsers = implementer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    implement_parser = implementer_subparsers.add_parser(
        "implement", aliases=["*implement"], help="Generate and write code to file"
    )
    implement_parser.add_argument(
        "specification", help="Code specification/description"
    )
    implement_parser.add_argument("file_path", help="Target file path")
    implement_parser.add_argument("--context", help="Additional context")
    implement_parser.add_argument(
        "--language", default="python", help="Programming language"
    )
    implement_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    generate_code_parser = implementer_subparsers.add_parser(
        "generate-code",
        aliases=["*generate-code"],
        help="Generate code (no file write)",
    )
    generate_code_parser.add_argument(
        "specification", help="Code specification/description"
    )
    generate_code_parser.add_argument(
        "--file", help="Optional target file path for context"
    )
    generate_code_parser.add_argument("--context", help="Additional context")
    generate_code_parser.add_argument(
        "--language", default="python", help="Programming language"
    )
    generate_code_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    refactor_parser = implementer_subparsers.add_parser(
        "refactor", aliases=["*refactor"], help="Refactor existing code file"
    )
    refactor_parser.add_argument("file_path", help="Path to file to refactor")
    refactor_parser.add_argument("instruction", help="Refactoring instruction")
    refactor_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    implementer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show implementer commands"
    )

    # Tester agent commands
    tester_parser = subparsers.add_parser("tester", help="Tester Agent commands")
    tester_subparsers = tester_parser.add_subparsers(dest="command", help="Commands")

    test_parser = tester_subparsers.add_parser(
        "test", aliases=["*test"], help="Generate and run tests for a file"
    )
    test_parser.add_argument("file", help="Source code file to test")
    test_parser.add_argument("--test-file", help="Path to write test file")
    test_parser.add_argument(
        "--integration", action="store_true", help="Generate integration tests"
    )

    generate_tests_parser = tester_subparsers.add_parser(
        "generate-tests",
        aliases=["*generate-tests"],
        help="Generate tests without running",
    )
    generate_tests_parser.add_argument("file", help="Source code file to test")
    generate_tests_parser.add_argument("--test-file", help="Path to write test file")
    generate_tests_parser.add_argument(
        "--integration", action="store_true", help="Generate integration tests"
    )

    run_tests_parser = tester_subparsers.add_parser(
        "run-tests", aliases=["*run-tests"], help="Run existing tests"
    )
    run_tests_parser.add_argument(
        "test_path", nargs="?", help="Path to test file or directory (default: tests/)"
    )
    run_tests_parser.add_argument(
        "--no-coverage", action="store_true", help="Don't include coverage report"
    )

    tester_subparsers.add_parser("help", aliases=["*help"], help="Show tester commands")

    # Debugger agent commands
    debugger_parser = subparsers.add_parser("debugger", help="Debugger Agent commands")
    debugger_subparsers = debugger_parser.add_subparsers(
        dest="command", help="Commands"
    )

    debug_parser = debugger_subparsers.add_parser(
        "debug", aliases=["*debug"], help="Debug an error or issue"
    )
    debug_parser.add_argument("error_message", help="Error message to debug")
    debug_parser.add_argument("--file", help="File path where error occurred")
    debug_parser.add_argument(
        "--line", type=int, help="Line number where error occurred"
    )
    debug_parser.add_argument("--stack-trace", help="Stack trace")

    analyze_error_parser = debugger_subparsers.add_parser(
        "analyze-error",
        aliases=["*analyze-error"],
        help="Analyze error message and stack trace",
    )
    analyze_error_parser.add_argument("error_message", help="Error message")
    analyze_error_parser.add_argument("--stack-trace", help="Stack trace")
    analyze_error_parser.add_argument(
        "--code-context", help="Code context around error"
    )

    trace_parser = debugger_subparsers.add_parser(
        "trace", aliases=["*trace"], help="Trace code execution path"
    )
    trace_parser.add_argument("file", help="File path to trace")
    trace_parser.add_argument("--function", help="Function name to trace from")
    trace_parser.add_argument("--line", type=int, help="Line number to trace from")

    debugger_subparsers.add_parser(
        "help", aliases=["*help"], help="Show debugger commands"
    )

    # Documenter agent commands
    documenter_parser = subparsers.add_parser(
        "documenter", help="Documenter Agent commands"
    )
    documenter_subparsers = documenter_parser.add_subparsers(
        dest="command", help="Commands"
    )

    document_parser = documenter_subparsers.add_parser(
        "document", aliases=["*document"], help="Generate documentation for a file"
    )
    document_parser.add_argument("file", help="Source code file path")
    document_parser.add_argument(
        "--output-format", default="markdown", help="Output format (markdown/rst/html)"
    )
    document_parser.add_argument("--output-file", help="Output file path")

    generate_docs_parser = documenter_subparsers.add_parser(
        "generate-docs", aliases=["*generate-docs"], help="Generate API documentation"
    )
    generate_docs_parser.add_argument("file", help="Source code file path")
    generate_docs_parser.add_argument(
        "--output-format", default="markdown", help="Output format"
    )

    update_readme_parser = documenter_subparsers.add_parser(
        "update-readme", aliases=["*update-readme"], help="Generate or update README.md"
    )
    update_readme_parser.add_argument(
        "--project-root", help="Project root directory (default: current directory)"
    )
    update_readme_parser.add_argument("--context", help="Additional context for README")

    update_docstrings_parser = documenter_subparsers.add_parser(
        "update-docstrings",
        aliases=["*update-docstrings"],
        help="Update docstrings in code",
    )
    update_docstrings_parser.add_argument("file", help="Source code file path")
    update_docstrings_parser.add_argument(
        "--docstring-format",
        default="google",
        help="Docstring format (google/numpy/sphinx)",
    )
    update_docstrings_parser.add_argument(
        "--write-file", action="store_true", help="Write updated code back to file"
    )

    documenter_subparsers.add_parser(
        "help", aliases=["*help"], help="Show documenter commands"
    )

    # Analyst agent commands
    analyst_parser = subparsers.add_parser("analyst", help="Analyst Agent commands")
    analyst_subparsers = analyst_parser.add_subparsers(dest="command", help="Commands")

    gather_req_parser = analyst_subparsers.add_parser(
        "gather-requirements",
        aliases=["*gather-requirements"],
        help="Gather requirements for a project",
    )
    gather_req_parser.add_argument("description", help="Requirement description")
    gather_req_parser.add_argument("--context", help="Additional context")
    gather_req_parser.add_argument("--output-file", help="Output file path")

    stakeholder_parser = analyst_subparsers.add_parser(
        "stakeholder-analysis",
        aliases=["*stakeholder-analysis"],
        help="Perform stakeholder analysis",
    )
    stakeholder_parser.add_argument(
        "description", help="Project or feature description"
    )
    stakeholder_parser.add_argument(
        "--stakeholders", nargs="+", help="List of stakeholders"
    )

    tech_research_parser = analyst_subparsers.add_parser(
        "tech-research", aliases=["*tech-research"], help="Perform technology research"
    )
    tech_research_parser.add_argument("requirement", help="Technology requirement")
    tech_research_parser.add_argument("--context", help="Additional context")
    tech_research_parser.add_argument(
        "--criteria", nargs="+", help="Evaluation criteria"
    )

    estimate_parser = analyst_subparsers.add_parser(
        "estimate-effort",
        aliases=["*estimate-effort"],
        help="Estimate effort for tasks",
    )
    estimate_parser.add_argument("feature_description", help="Feature description")
    estimate_parser.add_argument("--context", help="Additional context")

    assess_risk_parser = analyst_subparsers.add_parser(
        "assess-risk", aliases=["*assess-risk"], help="Assess project risks"
    )
    assess_risk_parser.add_argument(
        "feature_description", help="Feature or project description"
    )
    assess_risk_parser.add_argument("--context", help="Additional context")

    competitive_parser = analyst_subparsers.add_parser(
        "competitive-analysis",
        aliases=["*competitive-analysis"],
        help="Perform competitive analysis",
    )
    competitive_parser.add_argument("product_description", help="Product description")
    competitive_parser.add_argument(
        "--competitors", nargs="+", help="List of competitors"
    )

    analyst_subparsers.add_parser(
        "help", aliases=["*help"], help="Show analyst commands"
    )

    # Architect agent commands
    architect_parser = subparsers.add_parser(
        "architect", help="Architect Agent commands"
    )
    architect_subparsers = architect_parser.add_subparsers(
        dest="command", help="Commands"
    )

    design_system_parser = architect_subparsers.add_parser(
        "design-system",
        aliases=["*design-system"],
        help="Design the overall system architecture",
    )
    design_system_parser.add_argument("requirements", help="System requirements")
    design_system_parser.add_argument("--context", help="Additional context")
    design_system_parser.add_argument("--output-file", help="Output file path")

    diagram_parser = architect_subparsers.add_parser(
        "architecture-diagram",
        aliases=["*architecture-diagram"],
        help="Generate architecture diagrams",
    )
    diagram_parser.add_argument(
        "architecture_description", help="Architecture description"
    )
    diagram_parser.add_argument(
        "--diagram-type",
        default="component",
        help="Diagram type (component, sequence, deployment)",
    )
    diagram_parser.add_argument("--output-file", help="Output file path")

    tech_selection_parser = architect_subparsers.add_parser(
        "tech-selection",
        aliases=["*tech-selection"],
        help="Select appropriate technologies",
    )
    tech_selection_parser.add_argument(
        "component_description", help="Component description"
    )
    tech_selection_parser.add_argument("--requirements", help="Requirements")
    tech_selection_parser.add_argument("--constraints", nargs="+", help="Constraints")

    security_design_parser = architect_subparsers.add_parser(
        "security-design",
        aliases=["*security-design"],
        help="Design security aspects of the system",
    )
    security_design_parser.add_argument("system_description", help="System description")
    security_design_parser.add_argument("--threat-model", help="Threat model")

    boundaries_parser = architect_subparsers.add_parser(
        "define-boundaries",
        aliases=["*define-boundaries"],
        help="Define system boundaries and interfaces",
    )
    boundaries_parser.add_argument("system_description", help="System description")
    boundaries_parser.add_argument("--context", help="Additional context")

    architect_subparsers.add_parser(
        "help", aliases=["*help"], help="Show architect commands"
    )

    # Designer agent commands
    designer_parser = subparsers.add_parser("designer", help="Designer Agent commands")
    designer_subparsers = designer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    api_design_parser = designer_subparsers.add_parser(
        "api-design", aliases=["*api-design"], help="Design APIs (REST, GraphQL, gRPC)"
    )
    api_design_parser.add_argument("requirements", help="API requirements")
    api_design_parser.add_argument(
        "--api-type", default="REST", help="API type (REST, GraphQL, gRPC)"
    )
    api_design_parser.add_argument("--output-file", help="Output file path")

    data_model_parser = designer_subparsers.add_parser(
        "data-model-design",
        aliases=["*data-model-design"],
        help="Design data models and schemas",
    )
    data_model_parser.add_argument("requirements", help="Data model requirements")
    data_model_parser.add_argument("--data-source", help="Data source description")
    data_model_parser.add_argument("--output-file", help="Output file path")

    ui_ux_parser = designer_subparsers.add_parser(
        "ui-ux-design",
        aliases=["*ui-ux-design"],
        help="Design user interfaces and experiences",
    )
    ui_ux_parser.add_argument("feature_description", help="Feature description")
    ui_ux_parser.add_argument("--user-stories", nargs="+", help="User stories")
    ui_ux_parser.add_argument("--output-file", help="Output file path")

    wireframes_parser = designer_subparsers.add_parser(
        "wireframes", aliases=["*wireframes"], help="Generate wireframes for UI"
    )
    wireframes_parser.add_argument("screen_description", help="Screen description")
    wireframes_parser.add_argument(
        "--wireframe-type",
        default="page",
        help="Wireframe type (page, component, flow)",
    )
    wireframes_parser.add_argument("--output-file", help="Output file path")

    design_system_designer_parser = designer_subparsers.add_parser(
        "design-system",
        aliases=["*design-system"],
        help="Develop or extend a design system",
    )
    design_system_designer_parser.add_argument(
        "project_description", help="Project description"
    )
    design_system_designer_parser.add_argument(
        "--brand-guidelines", help="Brand guidelines"
    )
    design_system_designer_parser.add_argument("--output-file", help="Output file path")

    designer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show designer commands"
    )

    # Improver agent commands
    improver_parser = subparsers.add_parser("improver", help="Improver Agent commands")
    improver_subparsers = improver_parser.add_subparsers(
        dest="command", help="Commands"
    )

    refactor_improver_parser = improver_subparsers.add_parser(
        "refactor", aliases=["*refactor"], help="Refactor existing code"
    )
    refactor_improver_parser.add_argument("file_path", help="Path to file to refactor")
    refactor_improver_parser.add_argument(
        "--instruction", help="Specific refactoring instructions"
    )

    optimize_parser = improver_subparsers.add_parser(
        "optimize",
        aliases=["*optimize"],
        help="Optimize code for performance or memory",
    )
    optimize_parser.add_argument("file_path", help="Path to file to optimize")
    optimize_parser.add_argument(
        "--type",
        choices=["performance", "memory", "both"],
        default="performance",
        help="Optimization type",
    )

    improve_quality_parser = improver_subparsers.add_parser(
        "improve-quality",
        aliases=["*improve-quality"],
        help="Improve overall code quality",
    )
    improve_quality_parser.add_argument("file_path", help="Path to file to improve")

    improver_subparsers.add_parser(
        "help", aliases=["*help"], help="Show improver commands"
    )

    # Ops agent commands
    ops_parser = subparsers.add_parser("ops", help="Ops Agent commands")
    ops_subparsers = ops_parser.add_subparsers(dest="command", help="Commands")

    security_scan_parser = ops_subparsers.add_parser(
        "security-scan", aliases=["*security-scan"], help="Perform security scanning"
    )
    security_scan_parser.add_argument(
        "--target", help="File or directory to scan (default: project root)"
    )
    security_scan_parser.add_argument(
        "--type",
        default="all",
        help="Scan type (all, sql_injection, xss, secrets, etc.)",
    )

    compliance_check_parser = ops_subparsers.add_parser(
        "compliance-check",
        aliases=["*compliance-check"],
        help="Check compliance with standards",
    )
    compliance_check_parser.add_argument(
        "--type",
        default="general",
        help="Compliance type (general, GDPR, HIPAA, SOC2, all)",
    )

    deploy_parser = ops_subparsers.add_parser(
        "deploy", aliases=["*deploy"], help="Deploy application"
    )
    deploy_parser.add_argument(
        "--target",
        default="local",
        help="Deployment target (local, staging, production)",
    )
    deploy_parser.add_argument("--environment", help="Environment configuration name")

    infrastructure_setup_parser = ops_subparsers.add_parser(
        "infrastructure-setup",
        aliases=["*infrastructure-setup"],
        help="Set up infrastructure",
    )
    infrastructure_setup_parser.add_argument(
        "--type",
        default="docker",
        help="Infrastructure type (docker, kubernetes, terraform)",
    )

    audit_dependencies_parser = ops_subparsers.add_parser(
        "audit-dependencies",
        aliases=["*audit-dependencies"],
        help="Audit dependencies for security vulnerabilities (Phase 6.4.3)",
    )
    audit_dependencies_parser.add_argument(
        "--severity-threshold",
        choices=["low", "medium", "high", "critical"],
        default="high",
        help="Minimum severity threshold to report",
    )
    audit_dependencies_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    ops_subparsers.add_parser("help", aliases=["*help"], help="Show ops commands")

    # Enhancer agent commands
    enhancer_parser = subparsers.add_parser("enhancer", help="Enhancer Agent commands")
    enhancer_subparsers = enhancer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    enhance_parser = enhancer_subparsers.add_parser(
        "enhance", aliases=["*enhance"], help="Full enhancement pipeline"
    )
    enhance_parser.add_argument("prompt", help="Prompt to enhance")
    enhance_parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format",
    )
    enhance_parser.add_argument("--output", help="Output file path")
    enhance_parser.add_argument("--config", help="Enhancement config file path")

    enhance_quick_parser = enhancer_subparsers.add_parser(
        "enhance-quick",
        aliases=["*enhance-quick"],
        help="Quick enhancement (stages 1-3)",
    )
    enhance_quick_parser.add_argument("prompt", help="Prompt to enhance")
    enhance_quick_parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format",
    )
    enhance_quick_parser.add_argument("--output", help="Output file path")

    enhance_stage_parser = enhancer_subparsers.add_parser(
        "enhance-stage",
        aliases=["*enhance-stage"],
        help="Run specific enhancement stage",
    )
    enhance_stage_parser.add_argument(
        "stage", help="Stage to run (analysis, requirements, architecture, etc.)"
    )
    enhance_stage_parser.add_argument("--prompt", help="Prompt to enhance")
    enhance_stage_parser.add_argument("--session-id", help="Session ID to continue")

    enhance_resume_parser = enhancer_subparsers.add_parser(
        "enhance-resume",
        aliases=["*enhance-resume"],
        help="Resume interrupted enhancement",
    )
    enhance_resume_parser.add_argument("session_id", help="Session ID to resume")

    enhancer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show enhancer commands"
    )

    # Orchestrator agent commands
    orchestrator_parser = subparsers.add_parser(
        "orchestrator", help="Orchestrator Agent commands"
    )
    orchestrator_subparsers = orchestrator_parser.add_subparsers(
        dest="command", help="Commands"
    )

    orchestrator_subparsers.add_parser(
        "workflow-list", aliases=["*workflow-list"], help="List available workflows"
    )

    workflow_start_parser = orchestrator_subparsers.add_parser(
        "workflow-start", aliases=["*workflow-start"], help="Start a workflow"
    )
    workflow_start_parser.add_argument("workflow_id", help="Workflow ID to start")

    orchestrator_subparsers.add_parser(
        "workflow-status",
        aliases=["*workflow-status"],
        help="Show current workflow status",
    )

    orchestrator_subparsers.add_parser(
        "workflow-next", aliases=["*workflow-next"], help="Show next step"
    )

    workflow_skip_parser = orchestrator_subparsers.add_parser(
        "workflow-skip", aliases=["*workflow-skip"], help="Skip an optional step"
    )
    workflow_skip_parser.add_argument("step_id", help="Step ID to skip")

    orchestrator_subparsers.add_parser(
        "workflow-resume",
        aliases=["*workflow-resume"],
        help="Resume interrupted workflow",
    )

    gate_parser = orchestrator_subparsers.add_parser(
        "gate", aliases=["*gate"], help="Make a gate decision"
    )
    gate_parser.add_argument("--condition", help="Gate condition")
    gate_parser.add_argument(
        "--scoring-data", help="Scoring data as JSON", default="{}"
    )

    orchestrator_subparsers.add_parser(
        "help", aliases=["*help"], help="Show orchestrator commands"
    )

    # Workflow preset commands
    workflow_parser = subparsers.add_parser(
        "workflow", help="Run preset workflows (short commands)"
    )
    workflow_subparsers = workflow_parser.add_subparsers(
        dest="preset", help="Workflow presets"
    )

    # Common workflow options (apply to all presets)
    common_workflow_args = argparse.ArgumentParser(add_help=False)
    common_workflow_args.add_argument(
        "--file",
        help="Optional target file for workflows (defaults to example_bug.py for hotfix if present)",
    )

    # Short aliases
    workflow_subparsers.add_parser(
        "full",
        help="Full SDLC Pipeline (enterprise, complete lifecycle)",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "rapid",
        help="Rapid Development (feature, sprint work)",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "fix",
        help="Maintenance & Bug Fixing (refactor, technical debt)",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "quality",
        help="Quality Improvement (code review cycle)",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "hotfix",
        help="Quick Fix (urgent, production bugs)",
        parents=[common_workflow_args],
    )

    # Voice-friendly aliases
    workflow_subparsers.add_parser(
        "enterprise",
        help="Full SDLC Pipeline (alias for 'full')",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "feature",
        help="Rapid Development (alias for 'rapid')",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "refactor",
        help="Maintenance & Bug Fixing (alias for 'fix')",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "improve",
        help="Quality Improvement (alias for 'quality')",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "urgent",
        help="Quick Fix (alias for 'hotfix')",
        parents=[common_workflow_args],
    )

    # List command
    workflow_subparsers.add_parser("list", help="List all available workflow presets")

    # Project initialization command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize project: Set up Cursor Rules and workflow presets",
        description="Initialize a new project with TappsCodingAgents configuration. Creates Cursor Rules for natural language workflow commands and copies workflow presets to your project.",
    )
    init_parser.add_argument(
        "--no-rules", action="store_true", help="Skip Cursor Rules setup"
    )
    init_parser.add_argument(
        "--no-presets", action="store_true", help="Skip workflow presets setup"
    )
    init_parser.add_argument(
        "--no-config", action="store_true", help="Skip .tapps-agents/config.yaml setup"
    )
    init_parser.add_argument(
        "--no-skills",
        action="store_true",
        help="Skip installing .claude/skills (Cursor Skills definitions)",
    )
    init_parser.add_argument(
        "--no-background-agents",
        action="store_true",
        help="Skip installing .cursor/background-agents.yaml",
    )

    # Environment diagnostics
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Validate local environment and tools (soft-degrades with warnings by default)",
    )
    doctor_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )
    doctor_parser.add_argument(
        "--config-path", help="Optional explicit path to .tapps-agents/config.yaml"
    )

    # Hardware profile command
    hardware_parser = subparsers.add_parser(
        "hardware-profile",
        aliases=["hardware"],
        help="Check and configure hardware profile (NUC, Development, Workstation, Server)",
        description="Display current hardware metrics and detected profile. Optionally set a specific profile.",
    )
    hardware_parser.add_argument(
        "--set",
        choices=["auto", "nuc", "development", "workstation", "server"],
        help="Set hardware profile (overrides auto-detection)",
    )
    hardware_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )
    hardware_parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Hide detailed resource usage metrics",
    )

    # Quick shortcuts for common commands
    score_parser = subparsers.add_parser(
        "score",
        help="Quick shortcut: Score a code file (same as 'reviewer score')",
        description="Quick shortcut to score code files. Equivalent to 'reviewer score <file>'",
    )
    score_parser.add_argument("file", help="File path to score")
    score_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    # Expert setup wizard commands
    setup_experts_parser = subparsers.add_parser(
        "setup-experts", help="Interactive expert setup wizard"
    )
    setup_experts_subparsers = setup_experts_parser.add_subparsers(
        dest="command", help="Setup commands"
    )

    setup_experts_subparsers.add_parser(
        "init", aliases=["initialize"], help="Initialize project with expert setup"
    )
    setup_experts_subparsers.add_parser("add", help="Add a new expert")
    setup_experts_subparsers.add_parser("remove", help="Remove an expert")
    setup_experts_subparsers.add_parser("list", help="List all experts")

    # Analytics dashboard commands
    analytics_parser = subparsers.add_parser(
        "analytics", help="Analytics dashboard and metrics"
    )
    analytics_subparsers = analytics_parser.add_subparsers(
        dest="command", help="Analytics commands"
    )

    dashboard_parser = analytics_subparsers.add_parser(
        "dashboard", aliases=["show"], help="Show full analytics dashboard"
    )
    dashboard_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    agents_parser = analytics_subparsers.add_parser(
        "agents", help="Show agent performance metrics"
    )
    agents_parser.add_argument("--agent-id", help="Filter by specific agent ID")
    agents_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    workflows_parser = analytics_subparsers.add_parser(
        "workflows", help="Show workflow performance metrics"
    )
    workflows_parser.add_argument(
        "--workflow-id", help="Filter by specific workflow ID"
    )
    workflows_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    trends_parser = analytics_subparsers.add_parser(
        "trends", help="Show historical trends"
    )
    trends_parser.add_argument(
        "--metric-type",
        choices=[
            "agent_duration",
            "workflow_duration",
            "agent_success_rate",
            "workflow_success_rate",
        ],
        default="agent_duration",
        help="Metric type to show",
    )
    trends_parser.add_argument(
        "--days", type=int, default=30, help="Number of days to look back"
    )
    trends_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    system_parser = analytics_subparsers.add_parser("system", help="Show system status")
    system_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    args = parser.parse_args()

    # Handle commands
    if args.agent == "reviewer":
        _handle_reviewer_command(args)
    elif args.agent == "planner":
        _handle_planner_command(args)
    elif args.agent == "implementer":
        _handle_implementer_command(args)
    elif args.agent == "tester":
        _handle_tester_command(args)
    elif args.agent == "debugger":
        _handle_debugger_command(args)
    elif args.agent == "documenter":
        _handle_documenter_command(args)
    elif args.agent == "orchestrator":
        _handle_orchestrator_command(args)
    elif args.agent == "analyst":
        _handle_analyst_command(args)
    elif args.agent == "architect":
        _handle_architect_command(args)
    elif args.agent == "designer":
        _handle_designer_command(args)
    elif args.agent == "improver":
        command = args.command.lstrip("*") if args.command else None
        improver = ImproverAgent()
        asyncio.run(improver.activate())

        if command == "refactor":
            result = asyncio.run(
                improver.run(
                    "refactor",
                    file_path=args.file_path,
                    instruction=getattr(args, "instruction", None),
                )
            )
        elif command == "optimize":
            result = asyncio.run(
                improver.run(
                    "optimize",
                    file_path=args.file_path,
                    optimization_type=getattr(args, "type", "performance"),
                )
            )
        elif command == "improve-quality":
            result = asyncio.run(
                improver.run("improve-quality", file_path=args.file_path)
            )
        elif command == "help":
            result = asyncio.run(improver.run("help"))
            print(json.dumps(result["content"], indent=2))
            asyncio.run(improver.close())
            return
        else:
            result = asyncio.run(improver.run("help"))
            print(json.dumps(result["content"], indent=2))
            asyncio.run(improver.close())
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
        asyncio.run(improver.close())
    elif args.agent == "ops":
        command = args.command.lstrip("*") if args.command else None
        ops = OpsAgent()
        asyncio.run(ops.activate())

        if command == "security-scan":
            result = asyncio.run(
                ops.run(
                    "security-scan",
                    target=getattr(args, "target", None),
                    scan_type=getattr(args, "type", "all"),
                )
            )
        elif command == "compliance-check":
            result = asyncio.run(
                ops.run(
                    "compliance-check", compliance_type=getattr(args, "type", "general")
                )
            )
        elif command == "deploy":
            result = asyncio.run(
                ops.run(
                    "deploy",
                    target=getattr(args, "target", "local"),
                    environment=getattr(args, "environment", None),
                )
            )
        elif command == "infrastructure-setup":
            result = asyncio.run(
                ops.run(
                    "infrastructure-setup",
                    infrastructure_type=getattr(args, "type", "docker"),
                )
            )
        elif command == "audit-dependencies":
            result = asyncio.run(
                ops.run(
                    "audit-dependencies",
                    severity_threshold=getattr(args, "severity_threshold", "high"),
                )
            )
        elif command == "help":
            result = asyncio.run(ops.run("help"))
            print(json.dumps(result["content"], indent=2))
            asyncio.run(ops.close())
            return
        else:
            result = asyncio.run(ops.run("help"))
            print(json.dumps(result["content"], indent=2))
            asyncio.run(ops.close())
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
        asyncio.run(ops.close())
    elif args.agent == "enhancer":
        command = args.command.lstrip("*") if args.command else None
        enhancer = EnhancerAgent()
        asyncio.run(enhancer.activate())

        if command == "enhance" or command == "*enhance":
            result = asyncio.run(
                enhancer.run(
                    "enhance",
                    prompt=args.prompt,
                    output_format=getattr(args, "format", "markdown"),
                    output_file=getattr(args, "output", None),
                    config_path=getattr(args, "config", None),
                )
            )
        elif command == "enhance-quick" or command == "*enhance-quick":
            result = asyncio.run(
                enhancer.run(
                    "enhance-quick",
                    prompt=args.prompt,
                    output_format=getattr(args, "format", "markdown"),
                    output_file=getattr(args, "output", None),
                )
            )
        elif command == "enhance-stage" or command == "*enhance-stage":
            result = asyncio.run(
                enhancer.run(
                    "enhance-stage",
                    stage=args.stage,
                    prompt=getattr(args, "prompt", None),
                    session_id=getattr(args, "session_id", None),
                )
            )
        elif command == "enhance-resume" or command == "*enhance-resume":
            result = asyncio.run(
                enhancer.run("enhance-resume", session_id=args.session_id)
            )
        elif command == "help" or command == "*help":
            result = asyncio.run(enhancer.run("help"))
            print(result["content"])
            asyncio.run(enhancer.close())
            return
        else:
            result = asyncio.run(enhancer.run("help"))
            print(result["content"])
            asyncio.run(enhancer.close())
            return

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        # Format output
        if getattr(args, "format", "markdown") == "json":
            print(json.dumps(result, indent=2))
        else:
            enhanced = result.get("enhanced_prompt", {})
            if isinstance(enhanced, dict):
                print(enhanced.get("enhanced_prompt", json.dumps(enhanced, indent=2)))
            else:
                print(enhanced)

        asyncio.run(enhancer.close())
    elif args.agent == "workflow":
        # Workflow preset execution
        from .workflow.executor import WorkflowExecutor
        from .workflow.preset_loader import PresetLoader

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
            executor = WorkflowExecutor(auto_detect=False)
            target_file = getattr(args, "file", None)
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
    elif args.agent == "score":
        # Quick shortcut for reviewer score
        file_path = getattr(args, "file", None)
        if not file_path:
            print("Error: File path required", file=sys.stderr)
            print("Usage: python -m tapps_agents.cli score <file>", file=sys.stderr)
            sys.exit(1)

        output_format = getattr(args, "format", "text")
        asyncio.run(score_command(file_path, output_format=output_format))
    elif args.agent == "init":
        # Project initialization
        from .core.init_project import init_project

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
        )

        print("Initialization Results:")
        print(f"  Project Root: {results['project_root']}")

        if results["cursor_rules"]:
            print("  Cursor Rules: Created")
            # Find cursor rule files in files_created
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
            # Print a short hint rather than every file path (can be long).
            print("    - .claude/skills/")
        else:
            print("  Cursor Skills: Skipped or already exists")

        if results.get("background_agents"):
            print("  Background Agents: Installed")
            print("    - .cursor/background-agents.yaml")
        else:
            print("  Background Agents: Skipped or already exists")

        print("\nNext Steps:")
        print("  1. Set up experts: python -m tapps_agents.cli setup-experts init")
        print("  2. List workflows: python -m tapps_agents.cli workflow list")
        print("  3. Run a workflow: python -m tapps_agents.cli workflow rapid")
        print("  4. Check environment: python -m tapps_agents.cli doctor")
        print()
    elif args.agent == "doctor":
        config_path = getattr(args, "config_path", None)
        report = collect_doctor_report(
            config_path=Path(config_path) if config_path else None
        )

        if getattr(args, "format", "text") == "json":
            print(json.dumps(report, indent=2))
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
            for f in report.get("findings", []):
                sev = (f.get("severity") or "warn").upper()
                code = f.get("code") or ""
                msg = f.get("message") or ""
                print(f"  [{sev}] {code}: {msg}")
                remediation = f.get("remediation")
                if remediation:
                    print(f"         remediation: {remediation}")
    elif args.agent == "setup-experts":
        # Expert setup wizard
        from .experts.setup_wizard import ExpertSetupWizard

        wizard = ExpertSetupWizard()

        command = getattr(args, "command", None)
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
    elif args.agent == "hardware-profile" or args.agent == "hardware":
        # Hardware profile command
        hardware_profile_command(
            set_profile=getattr(args, "set", None),
            output_format=getattr(args, "format", "text"),
            show_metrics=not getattr(args, "no_metrics", False),
        )
    elif args.agent == "analytics":
        # Analytics dashboard
        from .core.analytics_dashboard import AnalyticsDashboard

        dashboard = AnalyticsDashboard()
        command = getattr(args, "command", "dashboard")

        if command == "dashboard" or command == "show":
            # Show full dashboard
            data = dashboard.get_dashboard_data()
            if getattr(args, "format", "json") == "json":
                print(json.dumps(data, indent=2))
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
                print(json.dumps(metrics, indent=2))
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
                print(json.dumps(metrics, indent=2))
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
                print(json.dumps(trends, indent=2))
            else:
                for trend in trends:
                    print(f"{trend['metric_name']}: {len(trend['values'])} data points")
        elif command == "system":
            # Show system status
            status = dashboard.get_system_status()
            if getattr(args, "format", "json") == "json":
                print(json.dumps(status, indent=2))
            else:
                print(f"System Status (as of {status['timestamp']}):")
                print(f"  Total Agents: {status['total_agents']}")
                print(f"  Active Workflows: {status['active_workflows']}")
                print(f"  Completed Today: {status['completed_workflows_today']}")
                print(f"  Failed Today: {status['failed_workflows_today']}")
    else:
        # Show main help
        parser.print_help()


if __name__ == "__main__":
    # Run startup routines (documentation refresh) before main
    import asyncio

    from .core.startup import startup_routines

    async def startup():
        """Run startup routines in background."""
        try:
            await startup_routines(refresh_docs=True, background_refresh=True)
        except Exception:
            # Don't fail if startup routines fail
            return

    # Start startup routines in background
    asyncio.run(startup())

    main()
