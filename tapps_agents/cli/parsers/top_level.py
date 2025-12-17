"""
Top-level command parser definitions
"""
import argparse

# Constants for skill-template command
AGENT_TYPES = [
    "analyst",
    "architect",
    "debugger",
    "designer",
    "documenter",
    "enhancer",
    "implementer",
    "improver",
    "ops",
    "orchestrator",
    "planner",
    "reviewer",
    "tester",
]

TOOL_OPTIONS = [
    "Read",
    "Write",
    "Edit",
    "Grep",
    "Glob",
    "Bash",
    "CodebaseSearch",
    "Terminal",
]

CAPABILITY_CATEGORIES = [
    "code_generation",
    "code_review",
    "testing",
    "documentation",
    "debugging",
    "refactoring",
    "analysis",
    "architecture",
    "design",
    "planning",
]


def add_top_level_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add all top-level command parsers"""
    
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
    common_workflow_args.add_argument(
        "--prompt", "-p",
        help="User prompt/description for the project (for greenfield workflows)",
    )
    common_workflow_args.add_argument(
        "--auto",
        action="store_true",
        help="Auto mode: no prompts, fully automated execution",
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
    
    # State management commands (Epic 12)
    state_parser = workflow_subparsers.add_parser(
        "state",
        help="Workflow state management (list, show, cleanup, resume)",
        description="Manage workflow state persistence and resume capabilities.",
    )
    state_subparsers = state_parser.add_subparsers(
        dest="state_command", help="State management commands", required=True
    )
    
    state_list_parser = state_subparsers.add_parser(
        "list",
        help="List all persisted workflow states",
    )
    state_list_parser.add_argument(
        "--workflow-id",
        help="Filter by specific workflow ID",
    )
    state_list_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    
    state_show_parser = state_subparsers.add_parser(
        "show",
        help="Show details of a specific workflow state",
    )
    state_show_parser.add_argument(
        "workflow_id",
        help="Workflow ID to show",
    )
    state_show_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    
    state_cleanup_parser = state_subparsers.add_parser(
        "cleanup",
        help="Clean up old workflow states",
    )
    state_cleanup_parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Keep states newer than this many days (default: 30)",
    )
    state_cleanup_parser.add_argument(
        "--max-states-per-workflow",
        type=int,
        default=10,
        help="Maximum states to keep per workflow (default: 10)",
    )
    state_cleanup_parser.add_argument(
        "--remove-completed",
        action="store_true",
        default=True,
        help="Remove states for completed workflows (default: True)",
    )
    state_cleanup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )
    
    state_resume_parser = workflow_subparsers.add_parser(
        "resume",
        help="Resume a workflow from last checkpoint",
        description="Resume workflow execution from the last saved checkpoint.",
    )
    state_resume_parser.add_argument(
        "--workflow-id",
        help="Specific workflow ID to resume (defaults to last workflow)",
    )
    state_resume_parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate state integrity before resuming (default: True)",
    )
    
    # Recommend command
    recommend_parser = workflow_subparsers.add_parser(
        "recommend",
        help="Get interactive workflow recommendation based on project analysis",
        description="Analyze the project and recommend the most appropriate workflow. "
        "Supports interactive mode with Q&A for ambiguous cases, or non-interactive mode for programmatic usage.",
    )
    recommend_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode: return structured output without prompts",
    )
    recommend_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    recommend_parser.add_argument(
        "--auto-load",
        action="store_true",
        help="Automatically load the recommended workflow after confirmation",
    )

    # Short command for primary use case: create new project from prompt
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new project from description (shortcut for 'workflow full --auto --prompt')",
        description="Primary use case: Create a complete, tested application from a description. "
        "This is a shortcut for 'workflow full --auto --prompt'. "
        "Executes fully automated with timeline tracking.",
    )
    create_parser.add_argument(
        "prompt",
        help="Project description/prompt (what you want to build)",
    )
    create_parser.add_argument(
        "--workflow",
        default="full",
        choices=["full", "rapid", "enterprise", "feature"],
        help="Workflow preset to use (default: full)",
    )

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
    init_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip Context7 cache pre-population",
    )
    init_parser.add_argument(
        "--no-cursorignore",
        action="store_true",
        help="Skip installing .cursorignore file",
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

    # Install dev tools command
    install_dev_parser = subparsers.add_parser(
        "install-dev",
        help="Install development tools (ruff, mypy, pytest, pip-audit, pipdeptree)",
        description="Install all development dependencies via pip. Detects if you're in a development context (has pyproject.toml) or using the installed package.",
    )
    install_dev_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be installed without actually installing",
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
    setup_experts_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Assume 'yes' to all prompts (useful for Cursor/CI)",
    )
    setup_experts_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt for input; use defaults where possible and error if input is required",
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

    # Customization template generator command
    customize_parser = subparsers.add_parser(
        "customize",
        help="Generate agent customization file templates",
        description="Generate customization file templates for agents. Customizations allow you to override agent behaviors without modifying base agent definitions.",
    )
    customize_subparsers = customize_parser.add_subparsers(
        dest="command", help="Customization commands"
    )

    init_customize_parser = customize_subparsers.add_parser(
        "init",
        aliases=["generate"],
        help="Generate customization file template for an agent",
    )
    init_customize_parser.add_argument(
        "agent_id",
        help="Agent ID (e.g., 'dev', 'implementer', 'reviewer', 'tester')",
    )
    init_customize_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing customization file if it exists",
    )

    # Custom Skill template generator command
    skill_template_parser = subparsers.add_parser(
        "skill-template",
        help="Generate custom Skill template for Cursor Skills",
        description="Generate a custom Skill template that can be used in Cursor. Skills extend the framework's capabilities with domain-specific agents.",
    )
    skill_template_parser.add_argument(
        "skill_name",
        help="Name of the Skill (e.g., 'my-custom-skill')",
    )
    skill_template_parser.add_argument(
        "--type",
        choices=AGENT_TYPES,
        help="Agent type for template defaults (analyst, architect, implementer, etc.)",
    )
    skill_template_parser.add_argument(
        "--description",
        help="Custom description for the Skill",
    )
    skill_template_parser.add_argument(
        "--tools",
        nargs="+",
        choices=TOOL_OPTIONS,
        help="Allowed tools (space-separated list)",
    )
    skill_template_parser.add_argument(
        "--capabilities",
        nargs="+",
        choices=CAPABILITY_CATEGORIES,
        help="Capabilities (space-separated list)",
    )
    skill_template_parser.add_argument(
        "--model-profile",
        help="Model profile name (defaults to {skill_name}_profile)",
    )
    skill_template_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Skill file if it exists",
    )
    skill_template_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: prompt for all options",
    )

