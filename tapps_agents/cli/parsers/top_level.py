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
        "workflow",
        help="Run preset workflows (short commands) or custom workflow files",
        description="""Execute predefined workflow presets or custom workflow YAML files.
        
Workflows orchestrate multiple agents in sequence to complete complex tasks:
  • Rapid/Feature: Fast development for sprint work and new features
  • Full/Enterprise: Complete SDLC pipeline with all quality gates
  • Fix/Refactor: Maintenance workflows for bug fixes and technical debt
  • Quality/Improve: Code review and quality improvement cycles
  • Hotfix/Urgent: Quick fixes for production-critical issues

You can use preset names (rapid, full, fix, etc.) or provide a path to a custom workflow YAML file.
Each workflow can be run with --auto for fully automated execution or interactively.

Examples:
  tapps-agents workflow rapid --prompt "Add feature"
  tapps-agents workflow workflows/custom/my-workflow.yaml --prompt "Build API"
""",
    )
    workflow_subparsers = workflow_parser.add_subparsers(
        dest="preset",
        help="Workflow preset name or file path (use 'list' to see all available presets)",
    )

    # Common workflow options (apply to all presets)
    common_workflow_args = argparse.ArgumentParser(add_help=False)
    common_workflow_args.add_argument(
        "--file",
        help="Target file or directory path for workflows that operate on existing code (e.g., bug fixes, refactoring). For hotfix workflow, defaults to example_bug.py if present in project root.",
    )
    common_workflow_args.add_argument(
        "--prompt", "-p",
        help="Natural language description of what to build or implement. Required for greenfield workflows (full, rapid, feature). Describes the project, feature, or task in plain English.",
    )
    common_workflow_args.add_argument(
        "--auto",
        action="store_true",
        help="Enable fully automated execution mode. Skips all interactive prompts and uses default decisions. Recommended for CI/CD pipelines and batch processing. Without this flag, workflow will prompt for confirmation at key decision points.",
    )

    # Short aliases
    full_parser = workflow_subparsers.add_parser(
        "full",
        help="Full SDLC Pipeline (enterprise, complete lifecycle)",
        description="""Complete software development lifecycle workflow for enterprise projects.
        
Executes all phases: requirements analysis, architecture design, implementation,
testing, code review, documentation, and deployment planning. Includes all quality
gates and compliance checks. Best for greenfield projects or major features.

Example: tapps-agents workflow full --prompt "Build a microservices e-commerce platform" --auto""",
        parents=[common_workflow_args],
    )
    rapid_parser = workflow_subparsers.add_parser(
        "rapid",
        help="Rapid Development (feature, sprint work)",
        description="""Fast-paced development workflow for sprint work and feature development.
        
Optimized for speed while maintaining code quality. Skips some documentation
and uses lighter review processes. Best for well-understood features and tight deadlines.

Example: tapps-agents workflow rapid --prompt "Add user profile editing" --auto""",
        parents=[common_workflow_args],
    )
    fix_parser = workflow_subparsers.add_parser(
        "fix",
        help="Maintenance & Bug Fixing (refactor, technical debt)",
        description="""Workflow focused on bug fixes, refactoring, and technical debt reduction.
        
Emphasizes code analysis, targeted fixes, and regression testing. Includes
duplication detection and quality improvement steps. Best for maintenance work.

Example: tapps-agents workflow fix --file src/buggy_module.py --auto""",
        parents=[common_workflow_args],
    )
    quality_parser = workflow_subparsers.add_parser(
        "quality",
        help="Quality Improvement (code review cycle)",
        description="""Comprehensive code quality improvement workflow.
        
Runs full code analysis, scoring, linting, type checking, and generates
detailed quality reports. Focuses on improving existing code without adding features.

Example: tapps-agents workflow quality --file src/legacy_code.py --auto""",
        parents=[common_workflow_args],
    )
    # Simple Mode workflow aliases
    new_feature_parser = workflow_subparsers.add_parser(
        "new-feature",
        help="Simple New Feature (build new features quickly)",
        description="""Simplified workflow for building new features with automatic quality checks.
        
Coordinates: Enhancer → Planner → Implementer → Reviewer → Tester
Quality gates: Overall ≥65, Security ≥6.5

Example: tapps-agents workflow new-feature --prompt "Add user authentication" --auto""",
        parents=[common_workflow_args],
    )
    improve_parser = workflow_subparsers.add_parser(
        "improve",
        help="Simple Improve Quality (code quality improvement)",
        description="""Simplified workflow for improving code quality through review and refactoring.
        
Coordinates: Reviewer → Improver → Reviewer → Tester
Quality gates: Overall ≥75, Maintainability ≥8.0

Example: tapps-agents workflow improve --file src/legacy_code.py --auto""",
        parents=[common_workflow_args],
    )
    hotfix_parser = workflow_subparsers.add_parser(
        "hotfix",
        help="Quick Fix (urgent, production bugs)",
        description="""Minimal workflow for urgent production bug fixes.
        
Fastest execution path with essential testing only. Skips documentation and
extensive reviews. Use only for critical production issues requiring immediate fixes.

Example: tapps-agents workflow hotfix --file example_bug.py --auto""",
        parents=[common_workflow_args],
    )

    # Voice-friendly aliases
    workflow_subparsers.add_parser(
        "enterprise",
        help="Full SDLC Pipeline (alias for 'full' workflow)",
        description="Alias for 'full' workflow - executes complete enterprise software development lifecycle pipeline with all quality gates, documentation, and compliance checks. Best for mission-critical projects requiring comprehensive oversight.",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "feature",
        help="Rapid Development (alias for 'rapid' workflow)",
        description="Alias for 'rapid' workflow - optimized for fast feature development in sprint cycles. Maintains code quality while prioritizing speed and delivery. Ideal for well-understood features with clear requirements.",
        parents=[common_workflow_args],
    )
    workflow_subparsers.add_parser(
        "refactor",
        help="Maintenance & Bug Fixing (alias for 'fix' workflow)",
        description="Alias for 'fix' workflow - focused on code maintenance, bug fixes, and technical debt reduction. Emphasizes targeted analysis, safe refactoring, and regression testing. Use for improving existing code without adding new features.",
        parents=[common_workflow_args],
    )
    # Note: "improve" parser already added above (line 145), skipping duplicate
    workflow_subparsers.add_parser(
        "urgent",
        help="Quick Fix (alias for 'hotfix' workflow)",
        description="Alias for 'hotfix' workflow - minimal workflow for urgent production bug fixes requiring immediate resolution. Fastest execution path with essential testing only. Use only for critical production issues that cannot wait for full workflow.",
        parents=[common_workflow_args],
    )

    # List command
    list_parser = workflow_subparsers.add_parser(
        "list",
        help="List all available workflow presets with descriptions",
        description="""Display all available workflow presets with detailed descriptions.
        
Shows both primary names and their aliases, along with:
  • Purpose and use cases for each workflow
  • When to use each workflow type
  • Key differences between workflows
  • Recommended scenarios for each preset

Use this command to discover which workflow best fits your current task.""",
    )
    
    # State management commands (Epic 12)
    state_parser = workflow_subparsers.add_parser(
        "state",
        help="Workflow state management (list, show, cleanup, resume)",
        description="""Manage workflow state persistence and resume capabilities.
        
Workflows can save their state at checkpoints, allowing you to:
  • Resume interrupted workflows from the last checkpoint
  • Inspect workflow state for debugging
  • Clean up old or completed workflow states
  • Track workflow execution history

Use state management to recover from failures or pause/resume long-running workflows.""",
    )
    state_subparsers = state_parser.add_subparsers(
        dest="state_command", help="State management subcommand (list, show, cleanup, resume)", required=True
    )
    
    state_list_parser = state_subparsers.add_parser(
        "list",
        help="List all persisted workflow states with metadata",
        description="Display all saved workflow states with their IDs, timestamps, status, and workflow type. Use --workflow-id to filter by specific workflow.",
    )
    state_list_parser.add_argument(
        "--workflow-id",
        help="Filter results to show only states for a specific workflow ID",
    )
    state_list_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable, 'json' for programmatic use (default: text)",
    )
    
    state_show_parser = state_subparsers.add_parser(
        "show",
        help="Show detailed information about a specific workflow state",
        description="Display complete details of a saved workflow state including all checkpoint data, execution context, and current step information. Useful for debugging or understanding workflow progress.",
    )
    state_show_parser.add_argument(
        "workflow_id",
        help="The workflow ID to inspect (obtain from 'workflow state list')",
    )
    state_show_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable, 'json' for programmatic use (default: text)",
    )
    
    state_cleanup_parser = state_subparsers.add_parser(
        "cleanup",
        help="Remove old or completed workflow states to free up disk space",
        description="""Clean up persisted workflow states based on retention policies.
        
Removes workflow states that are:
  • Older than the retention period
  • Exceed the maximum count per workflow
  • Completed (if --remove-completed is set)
  
Use --dry-run first to preview what will be removed without making changes.""",
    )
    state_cleanup_parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Keep workflow states newer than this many days. States older than this will be removed (default: 30 days)",
    )
    state_cleanup_parser.add_argument(
        "--max-states-per-workflow",
        type=int,
        default=10,
        help="Maximum number of states to keep per workflow. Older states beyond this limit will be removed (default: 10)",
    )
    state_cleanup_parser.add_argument(
        "--remove-completed",
        action="store_true",
        default=True,
        help="Remove states for workflows that have completed successfully (default: True). Set to False to keep completed workflow states for historical reference.",
    )
    state_cleanup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be removed without actually deleting any states. Recommended before running actual cleanup.",
    )
    
    state_resume_parser = workflow_subparsers.add_parser(
        "resume",
        help="Resume a workflow from its last saved checkpoint",
        description="""Resume workflow execution from the last saved checkpoint.
        
Recovers workflow state and continues execution from where it left off. Useful for:
  • Recovering from interruptions or failures
  • Resuming long-running workflows after system restarts
  • Continuing workflows that were manually paused

If --workflow-id is not specified, resumes the most recent workflow. Use --validate to ensure state integrity before resuming.""",
    )
    state_resume_parser.add_argument(
        "--workflow-id",
        help="Specific workflow ID to resume. If not provided, resumes the most recently saved workflow state",
    )
    state_resume_parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate state integrity and dependencies before resuming. Checks that all required files and context are still available (default: True).",
    )
    state_resume_parser.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        help="Skip state validation before resuming. Use only if you're certain the state is valid.",
    )
    state_resume_parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum number of steps to execute during resume (default: 50). Use to limit execution for testing or debugging.",
    )
    
    # Recommend command
    recommend_parser = workflow_subparsers.add_parser(
        "recommend",
        help="Get AI-powered workflow recommendation based on project analysis",
        description="""Analyze your project context and recommend the most appropriate workflow preset.
        
The system examines:
  • Project structure and codebase state
  • Recent changes and git history
  • File types and complexity
  • Existing tests and documentation
  • Project size and maturity

In interactive mode, asks clarifying questions for ambiguous cases. Use --non-interactive for CI/CD or programmatic usage. Use --auto-load to automatically start the recommended workflow after confirmation.""",
    )
    recommend_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode: return structured recommendation without prompting for user input. Recommended for CI/CD pipelines and automated scripts. Uses defaults for ambiguous cases.",
    )
    # Cleanup branches command
    cleanup_branches_parser = workflow_subparsers.add_parser(
        "cleanup-branches",
        help="Clean up orphaned Git branches from workflow worktrees",
        description="Detect and optionally delete orphaned Git branches that were created for workflow worktrees but no longer have associated worktrees.",
    )
    cleanup_branches_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview which branches would be deleted without actually deleting them",
    )
    cleanup_branches_parser.add_argument(
        "--retention-days",
        type=int,
        help="Override retention period (default: from config)",
    )
    cleanup_branches_parser.add_argument(
        "--pattern",
        type=str,
        help="Branch pattern to match (e.g., 'workflow/*' or 'agent/*')",
    )
    cleanup_branches_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    cleanup_branches_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    
    recommend_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable recommendation, 'json' for structured data suitable for programmatic use (default: text)",
    )
    recommend_parser.add_argument(
        "--auto-load",
        action="store_true",
        help="Automatically start the recommended workflow after displaying the recommendation. Prompts for confirmation unless --non-interactive is also set.",
    )

    # Short command for primary use case: create new project from prompt
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new project from description (PRIMARY USE CASE)",
        description="""Create a complete, tested application from a natural language description.
        
This is the PRIMARY USE CASE for TappsCodingAgents. It's a shortcut for
'workflow full --auto --prompt' that executes a fully automated SDLC pipeline.

The workflow will:
  1. Analyze requirements and gather specifications
  2. Design system architecture
  3. Generate implementation code
  4. Create comprehensive tests
  5. Review code quality
  6. Generate documentation
  7. Provide deployment guidance

Example:
  tapps-agents create "Build a REST API for a todo app with user authentication"
  tapps-agents create "Create a React dashboard with data visualization" --workflow rapid""",
    )
    create_parser.add_argument(
        "prompt",
        help="Natural language description of the project or application you want to build. Be as specific as possible about features, technologies, and requirements. Example: 'Build a REST API for a todo app with user authentication using FastAPI and PostgreSQL'",
    )
    create_parser.add_argument(
        "--workflow",
        default="full",
        choices=["full", "rapid", "enterprise", "feature"],
        help="Workflow preset to use: 'full' for complete SDLC (default), 'rapid'/'feature' for faster development, 'enterprise' for full pipeline with extra compliance checks (default: full)",
    )
    create_parser.add_argument(
        "--cursor-mode",
        action="store_true",
        help="(Deprecated) Force Cursor mode for workflow execution. Cursor-first is now the default for workflows unless TAPPS_AGENTS_MODE is explicitly set (e.g., TAPPS_AGENTS_MODE=headless).",
    )

    # Project initialization command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize project: Set up Cursor Rules and workflow presets",
        description="""Initialize a new project with TappsCodingAgents configuration.
        
Sets up all integration components for Cursor AI:
  • Cursor Rules (.cursor/rules/) - Natural language workflow commands and project context
  • Workflow Presets (workflows/presets/) - Reusable workflow definitions
  • Configuration (.tapps-agents/config.yaml) - Project settings
  • Cursor Skills (.claude/skills/) - Agent skill definitions
  • Background Agents (.cursor/background-agents.yaml) - Auto-execution config
  • Context7 Cache - Pre-populated knowledge base cache
  • .cursorignore - Exclude patterns for Cursor indexing

This command is safe to run multiple times - it won't overwrite existing files
unless you use --overwrite flags. Use --no-<component> to skip specific setups.

Upgrade/Reset Mode:
  Use --reset or --upgrade to reset framework-managed files to the latest version
  while preserving user data and customizations. Creates a backup by default.

Examples:
  tapps-agents init                    # Initial setup
  tapps-agents init --reset            # Upgrade/reset framework files
  tapps-agents init --reset --dry-run  # Preview changes without making them
  tapps-agents init --rollback <path>  # Rollback from backup""",
    )
    init_parser.add_argument(
        "--no-rules", action="store_true", help="Skip creating/updating .cursor/rules/ directory with natural language workflow commands and project context"
    )
    init_parser.add_argument(
        "--no-presets", action="store_true", help="Skip creating workflow presets directory (workflows/presets/) with reusable workflow definitions"
    )
    init_parser.add_argument(
        "--no-config", action="store_true", help="Skip creating .tapps-agents/config.yaml configuration file with project settings"
    )
    init_parser.add_argument(
        "--no-skills",
        action="store_true",
        help="Skip installing Cursor Skills definitions in .claude/skills/ directory. Skills enable agent capabilities in Cursor AI.",
    )
    init_parser.add_argument(
        "--background-agents",
        action="store_true",
        help="Install .cursor/background-agents.yaml configuration for automatic workflow execution in Cursor (not installed by default)",
    )
    init_parser.add_argument(
        "--no-background-agents",
        action="store_true",
        help="(Deprecated) Explicitly skip creating .cursor/background-agents.yaml. Background agents are not installed by default, so this flag is no longer needed.",
    )
    init_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip pre-populating Context7 knowledge base cache. Cache speeds up library documentation lookups.",
    )
    # Generate rules command
    generate_rules_parser = subparsers.add_parser(
        "generate-rules",
        help="Generate Cursor Rules documentation from workflow YAML files",
        description="""Generate .cursor/rules/workflow-presets.mdc from workflow YAML definitions.
        
This command automatically generates Cursor Rules documentation by parsing workflow YAML files
and extracting metadata, steps, and quality gates. The generated documentation stays in sync
with workflow definitions, eliminating documentation drift.

Example: tapps-agents generate-rules""",
    )
    generate_rules_parser.add_argument(
        "--output",
        type=str,
        help="Output file path (defaults to .cursor/rules/workflow-presets.mdc)",
    )
    generate_rules_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backing up existing rules file",
    )

    init_parser.add_argument(
        "--no-cursorignore",
        action="store_true",
        help="Skip creating .cursorignore file to exclude patterns from Cursor AI indexing (e.g., node_modules, .git, build artifacts)",
    )
    init_parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset framework-managed files to latest version (upgrade mode). Detects existing installation and resets framework files while preserving user data and customizations.",
    )
    init_parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade installation (alias for --reset). Resets framework-managed files to latest version while preserving user data.",
    )
    init_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup before reset (not recommended). Use with caution as this prevents rollback capability.",
    )
    init_parser.add_argument(
        "--reset-mcp",
        action="store_true",
        help="Also reset .cursor/mcp.json to framework version. By default, MCP config is preserved.",
    )
    init_parser.add_argument(
        "--preserve-custom",
        action="store_true",
        default=True,
        help="Preserve custom Skills, Rules, and presets (default: True). Custom files not in framework whitelist are always preserved.",
    )
    init_parser.add_argument(
        "--rollback",
        type=str,
        metavar="BACKUP_PATH",
        help="Rollback an init reset from a backup. Provide path to backup directory (e.g., .tapps-agents/backups/init-reset-20250116-143022).",
    )
    init_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Automatically answer 'yes' to all confirmation prompts. Useful for CI/CD pipelines.",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be reset without actually making changes. Shows framework files that would be deleted and files that would be preserved.",
    )

    # Environment diagnostics
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Validate local environment and tools",
        description="""Diagnose and validate your local development environment.
        
Checks for:
  • Python version and dependencies
  • Required tools (ruff, mypy, pytest, etc.)
  • Configuration files (.tapps-agents/config.yaml)
  • Cursor integration components
  • Cursor Skills configuration
  • File permissions and directory structure

By default, soft-degrades with warnings for missing optional components.
Use --format json for programmatic checking.

Example: tapps-agents doctor""",
    )
    doctor_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable diagnostics, 'json' for structured data suitable for programmatic checking (default: text)"
    )
    doctor_parser.add_argument(
        "--config-path", help="Explicit path to .tapps-agents/config.yaml file if not in default location. Useful when running doctor from outside project root."
    )

    # Health check command
    health_parser = subparsers.add_parser(
        "health",
        help="Comprehensive health checks for TappsCodingAgents",
        description="""Run comprehensive health checks across all system dimensions.
        
Checks:
  • Environment readiness (Python, tools, config)
  • Execution reliability (workflow success rates, performance)
  • Context7 cache effectiveness (hit rate, response time)
  • Knowledge base population (RAG/KB status)
  • Governance safety (approval queue, filtering)
  • Outcome trends (quality scores, improvements)

Use this to ensure tapps-agents is working at 100% capacity.
Health metrics are stored persistently for trend analysis.

Example: tapps-agents health check""",
    )
    health_subparsers = health_parser.add_subparsers(
        dest="command", help="Health subcommand (check, dashboard, metrics, trends)", required=True
    )

    health_check_parser = health_subparsers.add_parser(
        "check",
        help="Run health checks",
        description="Run all health checks or specific checks. Results are saved to metrics storage for trend analysis.",
    )
    health_check_parser.add_argument(
        "--check",
        choices=["environment", "automation", "execution", "context7_cache", "knowledge_base", "governance", "outcomes"],
        help="Run a specific health check (default: all checks)",
    )
    health_check_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable, 'json' for structured data (default: text)",
    )
    health_check_parser.add_argument(
        "--save",
        action="store_true",
        default=True,
        help="Save results to metrics storage (default: True)",
    )
    health_check_parser.add_argument(
        "--no-save",
        action="store_false",
        dest="save",
        help="Don't save results to metrics storage",
    )

    health_dashboard_parser = health_subparsers.add_parser(
        "dashboard",
        aliases=["show"],
        help="Display health dashboard",
        description="Show comprehensive health dashboard with all checks, overall status, and remediation actions.",
    )
    health_dashboard_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable dashboard, 'json' for structured data (default: text)",
    )

    health_metrics_parser = health_subparsers.add_parser(
        "metrics",
        help="Show stored health metrics",
        description="Display stored health metrics from previous checks. Supports filtering by check name, status, and time range.",
    )
    health_metrics_parser.add_argument(
        "--check-name",
        help="Filter by check name (e.g., 'environment', 'execution')",
    )
    health_metrics_parser.add_argument(
        "--status",
        choices=["healthy", "degraded", "unhealthy"],
        help="Filter by status",
    )
    health_metrics_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )
    health_metrics_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable, 'json' for structured data (default: text)",
    )

    health_trends_parser = health_subparsers.add_parser(
        "trends",
        help="Show health trends over time",
        description="Display health trends for specific checks over time. Helps identify improving or degrading health patterns.",
    )
    health_trends_parser.add_argument(
        "--check-name",
        required=True,
        help="Check name to analyze trends for (e.g., 'environment', 'execution')",
    )
    health_trends_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )
    health_trends_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable trends, 'json' for structured data (default: text)",
    )

    # Install dev tools command
    install_dev_parser = subparsers.add_parser(
        "install-dev",
        help="Install development tools and dependencies required by TappsCodingAgents",
        description="""Install all development dependencies via pip including:
  • ruff - Fast Python linter and formatter
  • mypy - Static type checker
  • pytest - Testing framework
  • pip-audit - Security vulnerability scanner for dependencies
  • pipdeptree - Dependency tree visualization

Automatically detects if you're in a development context (has pyproject.toml) or using the installed package. Use --dry-run to preview what will be installed.""",
    )
    install_dev_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what packages would be installed without actually installing them. Useful for checking compatibility or reviewing dependencies before installation.",
    )

    # Hardware profile command
    hardware_parser = subparsers.add_parser(
        "hardware-profile",
        aliases=["hardware"],
        help="Check and configure hardware profile for performance optimization",
        description="""Display current hardware metrics and detected profile for performance optimization.
        
Hardware profiles help TappsCodingAgents optimize resource usage:
  • NUC - Low-power devices (Intel NUC, small form factor)
  • Development - Standard development machines
  • Workstation - High-performance development workstations
  • Server - Production server environments
  • Auto - Automatically detect based on system resources

Profiles affect model selection, parallel processing, and resource allocation. Use --set to override auto-detection.""",
    )
    hardware_parser.add_argument(
        "--set",
        choices=["auto", "nuc", "development", "workstation", "server"],
        help="Set a specific hardware profile to override auto-detection. Use 'auto' to re-enable automatic detection based on system resources.",
    )
    hardware_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable, 'json' for programmatic use (default: text)"
    )
    hardware_parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Hide detailed resource usage metrics (CPU, memory, disk). Shows only profile information.",
    )

    # Quick shortcuts for common commands
    score_parser = subparsers.add_parser(
        "score",
        help="Quick shortcut: Score a code file (same as 'reviewer score')",
        description="""Quick shortcut to score code files for quality metrics.
        
Equivalent to 'reviewer score <file>'. Calculates objective quality scores
including complexity, security, maintainability, and test coverage metrics.

Returns scores from 0-100 for:
  • Overall Quality Score
  • Complexity Score (lower is better)
  • Security Score
  • Maintainability Score
  • Test Coverage (if tests exist)

Example:
  tapps-agents score src/main.py
  tapps-agents score src/main.py --format json""",
    )
    score_parser.add_argument("file", help="Path to the Python code file to analyze and score. Can be a relative or absolute path.")
    score_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable scores, 'json' for structured data (default: text)"
    )

    # Unified status command
    status_parser = subparsers.add_parser(
        "status",
        help="Unified status command for Background Agents",
        description="""Consolidated status command showing Background Agents activity.
        
Shows:
  • Active worktrees and their status
  • Progress files and execution status
  • Background agent configuration status
  • Recent results
  
Use --detailed for full information, --worktrees-only for worktree info only.

Examples:
  tapps-agents status
  tapps-agents status --detailed
  tapps-agents status --worktrees-only
  tapps-agents status --format json""",
    )
    status_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information including full progress data and workflow state",
    )
    status_parser.add_argument(
        "--worktrees-only",
        action="store_true",
        help="Show only worktree information",
    )
    status_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable, 'json' for structured data (default: text)",
    )

    # Expert setup wizard commands
    setup_experts_parser = subparsers.add_parser(
        "setup-experts", 
        help="Interactive wizard for configuring Industry Experts",
        description="""Configure Industry Experts for domain-specific knowledge and decision-making.
        
Industry Experts provide specialized knowledge in specific domains (e.g., AI frameworks, code quality, architecture, DevOps). They enhance agent decision-making with weighted expertise. Use this wizard to:
  • Initialize expert configuration for your project
  • Add new domain experts
  • Remove experts that are no longer needed
  • List currently configured experts

Experts are configured in .tapps-agents/experts.yaml and can be referenced by agents during execution.""",
    )
    setup_experts_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically answer 'yes' to all confirmation prompts. Useful for Cursor AI integration and CI/CD pipelines where user interaction is not possible.",
    )
    setup_experts_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode: use default values where possible and error if user input is required. Prevents any prompts from appearing.",
    )
    setup_experts_subparsers = setup_experts_parser.add_subparsers(
        dest="command", help="Expert setup subcommand (init, add, remove, list)"
    )

    setup_experts_subparsers.add_parser(
        "init", aliases=["initialize"], help="Initialize project with expert configuration setup", description="Set up initial expert configuration for your project. Creates .tapps-agents/experts.yaml with default or recommended experts based on project analysis."
    )
    setup_experts_subparsers.add_parser("add", help="Add a new Industry Expert to the project", description="Add a new domain expert to your project configuration. Prompts for expert name, domain, knowledge base location, and weight.")
    setup_experts_subparsers.add_parser("remove", help="Remove an expert from the project configuration", description="Remove an Industry Expert from .tapps-agents/experts.yaml. The expert will no longer be consulted by agents.")
    setup_experts_subparsers.add_parser("list", help="List all currently configured experts", description="Display all Industry Experts currently configured in the project, including their domains, weights, and knowledge base locations.")

    # Analytics dashboard commands
    analytics_parser = subparsers.add_parser(
        "analytics", 
        help="Analytics dashboard and performance metrics",
        description="""Access analytics and performance metrics for agents and workflows.
        
Provides insights into:
  • Agent performance (execution time, success rates)
  • Workflow metrics (completion rates, duration)
  • Historical trends and patterns
  • System resource usage

Use analytics to optimize agent selection, identify bottlenecks, and track improvement over time.""",
    )
    analytics_subparsers = analytics_parser.add_subparsers(
        dest="command", help="Analytics subcommand (dashboard, agents, workflows, trends, system)"
    )

    dashboard_parser = analytics_subparsers.add_parser(
        "dashboard", aliases=["show"], help="Display comprehensive analytics dashboard", description="Show a full analytics dashboard with all key metrics including agent performance, workflow statistics, system status, and recent trends. Provides a complete overview of TappsCodingAgents usage and performance."
    )
    dashboard_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable dashboard, 'json' for structured data (default: text)"
    )

    agents_parser = analytics_subparsers.add_parser(
        "agents", help="Display agent performance metrics and statistics", description="Show detailed performance metrics for all agents or a specific agent. Includes execution times, success rates, error counts, and average response quality. Use --agent-id to filter to a specific agent."
    )
    agents_parser.add_argument("--agent-id", help="Filter metrics to show only data for a specific agent (e.g., 'reviewer', 'implementer', 'tester')")
    agents_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable, 'json' for programmatic use (default: text)"
    )

    workflows_parser = analytics_subparsers.add_parser(
        "workflows", help="Display workflow performance metrics and statistics", description="Show detailed performance metrics for all workflows or a specific workflow. Includes completion rates, average duration, success rates, and step-by-step timing. Use --workflow-id to filter to a specific workflow."
    )
    workflows_parser.add_argument(
        "--workflow-id", help="Filter metrics to show only data for a specific workflow ID"
    )
    workflows_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable, 'json' for programmatic use (default: text)"
    )

    trends_parser = analytics_subparsers.add_parser(
        "trends", help="Display historical trends and patterns", description="Show historical trends for selected metrics over time. Helps identify patterns, improvements, or regressions in agent and workflow performance. Use --days to control the time window and --metric-type to select the metric to analyze."
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
        help="Type of metric to analyze: 'agent_duration' for agent execution times, 'workflow_duration' for workflow completion times, 'agent_success_rate' for agent success percentages, 'workflow_success_rate' for workflow completion rates (default: agent_duration)",
    )
    trends_parser.add_argument(
        "--days", type=int, default=30, help="Number of days to look back in history (default: 30 days). Increase for longer-term trends, decrease for recent patterns."
    )
    trends_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable trends, 'json' for structured time-series data (default: text)"
    )

    system_parser = analytics_subparsers.add_parser("system", help="Display system status and resource usage", description="Show current system status including resource usage (CPU, memory, disk), active agents/workflows, configuration status, and health checks. Useful for monitoring and troubleshooting.")
    system_parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format: 'text' for human-readable status, 'json' for structured system data (default: text)"
    )

    # Background Agent configuration commands
    bg_agent_parser = subparsers.add_parser(
        "background-agent-config",
        aliases=["bg-config"],
        help="Manage Background Agent configuration for automatic workflow execution",
        description="""Generate and validate Background Agent configuration files for automatic workflow command execution in Cursor AI.
        
Background Agents enable automatic execution of workflow commands based on triggers (file changes, git commits, etc.). Configuration is stored in .cursor/background-agents.yaml and allows Cursor to automatically run workflows without manual intervention.""",
    )
    bg_agent_subparsers = bg_agent_parser.add_subparsers(
        dest="command", help="Background Agent configuration subcommand (generate, validate)", required=True
    )

    bg_generate_parser = bg_agent_subparsers.add_parser(
        "generate",
        aliases=["gen", "init"],
        help="Generate Background Agent configuration file from template",
        description="""Generate a Background Agent configuration file (.cursor/background-agents.yaml) from template.
        
Creates configuration with:
  • Workflow trigger definitions
  • Auto-execution rules
  • Agent selection criteria
  • Execution conditions

Use --minimal for a basic configuration, or provide --template for a custom template. Use --overwrite to replace existing configuration.""",
    )
    bg_generate_parser.add_argument(
        "--template",
        help="Path to a custom template file. If not provided, uses the framework's default template with comprehensive examples.",
    )
    bg_generate_parser.add_argument(
        "--minimal",
        action="store_true",
        help="Generate a minimal configuration with basic settings only. Useful for simple use cases or as a starting point.",
    )
    bg_generate_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing .cursor/background-agents.yaml file if it exists. Without this flag, the command will fail if the file already exists.",
    )
    bg_generate_parser.add_argument(
        "--config-path",
        help="Custom path for the configuration file. Defaults to .cursor/background-agents.yaml in the project root.",
    )

    bg_validate_parser = bg_agent_subparsers.add_parser(
        "validate",
        aliases=["check"],
        help="Validate Background Agent configuration file for errors",
        description="""Validate the Background Agent configuration file for syntax and schema errors.
        
Checks:
  • YAML syntax correctness
  • Schema compliance
  • Required fields presence
  • Valid workflow references
  • Trigger configuration validity

Use this before committing configuration changes to ensure Cursor can properly load the background agents.""",
    )
    bg_validate_parser.add_argument(
        "--config-path",
        help="Path to the configuration file to validate. Defaults to .cursor/background-agents.yaml in the project root.",
    )
    bg_validate_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable validation results, 'json' for structured error data (default: text)",
    )

    # Governance & Approval Queue command (Story 28.5)
    governance_parser = subparsers.add_parser(
        "governance",
        aliases=["approval"],
        help="Manage governance approval queue for knowledge base entries",
        description="""Manage the approval queue for knowledge entries that require human review before being added to the Knowledge Base.
        
When agents generate knowledge entries (patterns, best practices, solutions), they can be queued for approval to ensure quality and correctness. This command allows you to:
  • List pending approval requests
  • Review detailed information about entries
  • Approve entries for automatic ingestion
  • Reject entries with optional reasons

Use this for quality control and ensuring only validated knowledge enters your project's knowledge base.""",
    )
    governance_subparsers = governance_parser.add_subparsers(
        dest="command", help="Governance subcommand (list, show, approve, reject)"
    )
    
    approval_list_parser = governance_subparsers.add_parser(
        "list",
        aliases=["ls"],
        help="List all pending knowledge entry approval requests",
        description="Display all knowledge entries waiting for approval, including their IDs, types, sources, and submission timestamps. Use this to see what needs review.",
    )
    approval_list_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable list, 'json' for structured data (default: text)",
    )
    
    approval_show_parser = governance_subparsers.add_parser(
        "show",
        help="Display detailed information about a specific approval request",
        description="Show complete details of a knowledge entry approval request including content, metadata, source agent, and context. Use this to review entries before approving or rejecting.",
    )
    approval_show_parser.add_argument(
        "request_id",
        help="The approval request ID to inspect (obtain from 'governance list'). Can be a filename or full path to the request file.",
    )
    
    approval_approve_parser = governance_subparsers.add_parser(
        "approve",
        aliases=["accept"],
        help="Approve a knowledge entry request for ingestion into the KB",
        description="Approve a knowledge entry and optionally automatically ingest it into the Knowledge Base. Approved entries become available to all agents for future reference.",
    )
    approval_approve_parser.add_argument(
        "request_id",
        help="The approval request ID to approve (obtain from 'governance list'). Can be a filename or full path to the request file.",
    )
    approval_approve_parser.add_argument(
        "--auto-ingest",
        action="store_true",
        help="Automatically ingest the approved entry into the Knowledge Base immediately after approval. Without this flag, the entry is marked as approved but not automatically ingested.",
    )
    
    approval_reject_parser = governance_subparsers.add_parser(
        "reject",
        aliases=["deny"],
        help="Reject a knowledge entry request",
        description="Reject a knowledge entry request with an optional reason. Rejected entries are removed from the approval queue and will not be added to the Knowledge Base. Use --reason to document why the entry was rejected.",
    )
    approval_reject_parser.add_argument(
        "request_id",
        help="The approval request ID to reject (obtain from 'governance list'). Can be a filename or full path to the request file.",
    )
    approval_reject_parser.add_argument(
        "--reason",
        help="Reason for rejection (e.g., 'Incorrect information', 'Outdated pattern', 'Not applicable to our project'). Stored for audit purposes.",
    )

    # Auto-execution monitoring commands (Story 7.9)
    auto_exec_parser = subparsers.add_parser(
        "auto-execution",
        aliases=["auto-exec", "ae"],
        help="Monitor and manage Background Agent auto-execution",
        description="""Monitor and manage Background Agent auto-execution status, metrics, and health.
        
Background Agents can automatically execute workflows based on triggers (file changes, git events, etc.). This command provides tools to:
  • Check current execution status
  • View execution history
  • Monitor performance metrics
  • Run health checks
  • Enable/disable debug logging

Use this to troubleshoot auto-execution issues, monitor performance, and ensure Background Agents are functioning correctly.""",
    )
    auto_exec_subparsers = auto_exec_parser.add_subparsers(
        dest="command", help="Auto-execution subcommand (status, history, metrics, health, debug)"
    )

    auto_exec_status_parser = auto_exec_subparsers.add_parser(
        "status",
        help="Display current auto-execution status and active workflows",
        description="Show the current status of Background Agent auto-execution including any workflows currently running, queued executions, and recent activity. Use --workflow-id to filter to a specific workflow.",
    )
    auto_exec_status_parser.add_argument(
        "--workflow-id",
        help="Filter status output to show only information for a specific workflow ID",
    )
    auto_exec_status_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable status, 'json' for structured data (default: text)",
    )

    auto_exec_history_parser = auto_exec_subparsers.add_parser(
        "history",
        help="Display history of auto-executed workflows",
        description="Show a history of workflows that were automatically executed by Background Agents. Includes execution times, outcomes, triggers, and durations. Use --workflow-id to filter to a specific workflow type and --limit to control the number of entries shown.",
    )
    auto_exec_history_parser.add_argument(
        "--workflow-id",
        help="Filter history to show only executions for a specific workflow ID or workflow type",
    )
    auto_exec_history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of execution records to display (default: 20). Increase for longer history, decrease for recent executions only.",
    )
    auto_exec_history_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable history, 'json' for structured data (default: text)",
    )

    auto_exec_metrics_parser = auto_exec_subparsers.add_parser(
        "metrics",
        help="Display auto-execution performance metrics summary",
        description="Show aggregated performance metrics for auto-execution including success rates, average execution times, trigger frequencies, and error rates. Useful for monitoring overall auto-execution health and performance.",
    )
    auto_exec_metrics_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable metrics, 'json' for structured data (default: text)",
    )

    auto_exec_health_parser = auto_exec_subparsers.add_parser(
        "health",
        help="Run health checks on auto-execution system",
        description="Perform comprehensive health checks on the Background Agent auto-execution system including configuration validity, trigger monitoring status, resource availability, and error detection. Use this to diagnose issues with auto-execution.",
    )
    auto_exec_health_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable health report, 'json' for structured health data (default: text)",
    )

    auto_exec_debug_parser = auto_exec_subparsers.add_parser(
        "debug",
        help="Enable, disable, or check debug mode status",
        description="Control debug logging for Background Agent auto-execution. Debug mode provides detailed logging of trigger detection, execution decisions, and workflow launches. Use 'on' to enable, 'off' to disable, or 'status' to check current state.",
    )
    auto_exec_debug_parser.add_argument(
        "action",
        choices=["on", "off", "status"],
        help="Debug action: 'on' to enable detailed debug logging, 'off' to disable, 'status' to check current debug mode state",
    )

    # Customization template generator command
    customize_parser = subparsers.add_parser(
        "customize",
        help="Generate agent customization file templates",
        description="""Generate customization file templates for agents to override default behaviors.
        
Customizations allow you to modify agent behavior without changing the base framework code:
  • Override default prompts and instructions
  • Customize tool selection preferences
  • Adjust model selection criteria
  • Add project-specific guidelines

Customization files are stored in .tapps-agents/customizations/ and take precedence over default agent definitions.""",
    )
    customize_subparsers = customize_parser.add_subparsers(
        dest="command", help="Customization subcommand (init/generate)"
    )

    init_customize_parser = customize_subparsers.add_parser(
        "init",
        aliases=["generate"],
        help="Generate a customization file template for a specific agent",
        description="Create a customization template file for the specified agent. The template includes all customizable aspects with comments explaining each option. Edit the generated file to customize agent behavior for your project.",
    )
    init_customize_parser.add_argument(
        "agent_id",
        help="Agent ID to customize (e.g., 'implementer', 'reviewer', 'tester', 'planner'). Must be a valid agent type from the framework.",
    )
    init_customize_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing customization file if one already exists. Without this flag, the command will fail if a customization file for this agent already exists.",
    )

    # Custom Skill commands
    skill_parser = subparsers.add_parser(
        "skill",
        help="Custom Skill management commands",
        description="""Manage custom Skills for extending framework capabilities.
        
Skills are domain-specific agent extensions that can be used in Cursor AI. They define:
  • Agent capabilities and tools
  • Domain-specific knowledge
  • Custom instructions and prompts
  • Model profiles and configurations

Use this command to validate existing Skills or generate new Skill templates.""",
    )
    skill_subparsers = skill_parser.add_subparsers(
        dest="skill_command",
        help="Skill management subcommand (validate, template)",
    )

    # Skill validation command
    skill_validate_parser = skill_subparsers.add_parser(
        "validate",
        help="Validate custom Skills for correctness and completeness",
        description="""Validate custom Skills for format, schema, and capability correctness.
        
Checks:
  • SKILL.md format and required sections
  • Valid agent type references
  • Tool capability definitions
  • Model profile configurations
  • File structure and organization

Use --skill to validate a specific Skill, or validate all Skills in .claude/skills/ by default. Use --no-warnings to show only errors.""",
    )
    skill_validate_parser.add_argument(
        "--skill",
        help="Path to a specific Skill directory (e.g., .claude/skills/my-skill/) or SKILL.md file to validate. If not provided, validates all Skills in .claude/skills/",
    )
    skill_validate_parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="Show only errors and hide warnings. Useful for strict validation in CI/CD pipelines.",
    )
    skill_validate_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' for human-readable validation results, 'json' for structured error data (default: text)",
    )

    # Custom Skill template generator command (as subcommand)
    skill_template_parser = skill_subparsers.add_parser(
        "template",
        help="Generate a custom Skill template for Cursor AI integration",
        description="""Generate a custom Skill template that can be used in Cursor AI.
        
Skills extend the framework's capabilities with domain-specific agents. The template includes:
  • SKILL.md with agent definition
  • Capability descriptions
  • Tool access configurations
  • Model profile settings
  • Example usage patterns

Use --interactive for guided setup, or provide options directly via command-line arguments.""",
    )
    
    # Also keep the old skill-template command for backward compatibility
    skill_template_legacy_parser = subparsers.add_parser(
        "skill-template",
        help="Generate custom Skill template for Cursor Skills (legacy command, use 'skill template')",
        description="""Generate a custom Skill template that can be used in Cursor AI. Skills extend the framework's capabilities with domain-specific agents.
        
NOTE: This is a legacy command. For new code, use 'skill template' instead. This command is maintained for backward compatibility.""",
    )
    # Copy arguments to legacy parser
    skill_template_legacy_parser.add_argument(
        "skill_name",
        help="Name of the Skill (e.g., 'my-custom-skill', 'data-science-helper'). Must be a valid directory name. Will be created in .claude/skills/",
    )
    skill_template_legacy_parser.add_argument(
        "--type",
        choices=AGENT_TYPES,
        help="Base agent type for template defaults. Determines default capabilities and tool access. Choose from: analyst, architect, debugger, designer, documenter, enhancer, implementer, improver, ops, orchestrator, planner, reviewer, tester",
    )
    skill_template_legacy_parser.add_argument(
        "--description",
        help="Custom description of what the Skill does and when to use it. This appears in Cursor AI's Skill selection interface.",
    )
    skill_template_legacy_parser.add_argument(
        "--tools",
        nargs="+",
        choices=TOOL_OPTIONS,
        help="Space-separated list of tools the Skill can access. Available tools: Read, Write, Edit, Grep, Glob, Bash, CodebaseSearch, Terminal. Omit to use defaults for the agent type.",
    )
    skill_template_legacy_parser.add_argument(
        "--capabilities",
        nargs="+",
        choices=CAPABILITY_CATEGORIES,
        help="Space-separated list of capability categories. Available: code_generation, code_review, testing, documentation, debugging, refactoring, analysis, architecture, design, planning. Omit to use defaults for the agent type.",
    )
    skill_template_legacy_parser.add_argument(
        "--model-profile",
        help="Model profile name to use for this Skill. If not provided, defaults to '{skill_name}_profile'. Model profiles define which LLM models to use and their configurations.",
    )
    skill_template_legacy_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Skill directory and files if they already exist. Without this flag, the command will fail if the Skill already exists.",
    )
    skill_template_legacy_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: prompt for all options with helpful descriptions. Recommended for first-time Skill creation. If not set, uses provided arguments or defaults.",
    )
    
    skill_template_parser.add_argument(
        "skill_name",
        help="Name of the Skill (e.g., 'my-custom-skill', 'data-science-helper'). Must be a valid directory name. Will be created in .claude/skills/",
    )
    skill_template_parser.add_argument(
        "--type",
        choices=AGENT_TYPES,
        help="Base agent type for template defaults. Determines default capabilities and tool access. Choose from: analyst, architect, debugger, designer, documenter, enhancer, implementer, improver, ops, orchestrator, planner, reviewer, tester",
    )
    skill_template_parser.add_argument(
        "--description",
        help="Custom description of what the Skill does and when to use it. This appears in Cursor AI's Skill selection interface.",
    )
    skill_template_parser.add_argument(
        "--tools",
        nargs="+",
        choices=TOOL_OPTIONS,
        help="Space-separated list of tools the Skill can access. Available tools: Read, Write, Edit, Grep, Glob, Bash, CodebaseSearch, Terminal. Omit to use defaults for the agent type.",
    )
    skill_template_parser.add_argument(
        "--capabilities",
        nargs="+",
        choices=CAPABILITY_CATEGORIES,
        help="Space-separated list of capability categories. Available: code_generation, code_review, testing, documentation, debugging, refactoring, analysis, architecture, design, planning. Omit to use defaults for the agent type.",
    )
    skill_template_parser.add_argument(
        "--model-profile",
        help="Model profile name to use for this Skill. If not provided, defaults to '{skill_name}_profile'. Model profiles define which LLM models to use and their configurations.",
    )
    skill_template_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Skill directory and files if they already exist. Without this flag, the command will fail if the Skill already exists.",
    )
    skill_template_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: prompt for all options with helpful descriptions. Recommended for first-time Skill creation. If not set, uses provided arguments or defaults.",
    )

    # Cursor integration verification command
    cursor_parser = subparsers.add_parser(
        "cursor",
        help="Cursor AI integration verification and management",
        description="""Verify and manage Cursor AI integration components.
        
Checks the status of:
  • Cursor Skills (.claude/skills/) - Agent capability definitions
  • Cursor Rules (.cursor/rules/) - Natural language workflow commands and project context
  • Background Agents (.cursor/background-agents.yaml) - Auto-execution configuration
  • Configuration files and directory structure

Use this to ensure all Cursor integration components are properly installed and configured for your project.""",
    )
    cursor_subparsers = cursor_parser.add_subparsers(
        dest="cursor_command",
        help="Cursor integration subcommand (verify/check)",
        required=True,
    )

    cursor_verify_parser = cursor_subparsers.add_parser(
        "verify",
        aliases=["check"],
        help="Verify all Cursor AI integration components are properly configured",
        description="""Verify that all Cursor AI integration components are properly installed and configured.
        
Performs comprehensive checks:
  • Validates Skills directory structure and files
  • Checks Cursor Rules file presence and format
  • Validates Background Agent configuration
  • Verifies required directories exist
  • Checks file permissions and accessibility

Reports any missing components, configuration errors, or issues that would prevent Cursor from using TappsCodingAgents features.""",
    )
    cursor_verify_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format: 'text' for human-readable verification report, 'json' for structured validation data (default: text)",
    )

    # Simple Mode commands
    simple_mode_parser = subparsers.add_parser(
        "simple-mode",
        help="Simple Mode commands (toggle, status)",
        description="""Manage Simple Mode - a simplified interface that hides complexity while showcasing power.

Simple Mode provides intent-based agent orchestration:
  • Build: Create new features (planner → architect → designer → implementer)
  • Review: Code review and quality checks (reviewer → improver)
  • Fix: Debug and fix issues (debugger → implementer → tester)
  • Test: Generate and run tests (tester)

Use natural language commands instead of agent-specific syntax.""",
    )
    simple_mode_subparsers = simple_mode_parser.add_subparsers(
        dest="command",
        help="Simple Mode command",
    )

    # Simple Mode: on/off
    simple_mode_on_parser = simple_mode_subparsers.add_parser(
        "on",
        help="Enable Simple Mode",
    )
    simple_mode_off_parser = simple_mode_subparsers.add_parser(
        "off",
        help="Disable Simple Mode",
    )
    simple_mode_status_parser = simple_mode_subparsers.add_parser(
        "status",
        help="Check Simple Mode status",
    )
    simple_mode_status_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    simple_mode_init_parser = simple_mode_subparsers.add_parser(
        "init",
        help="Initialize Simple Mode with guided onboarding",
        description="""Run the Simple Mode onboarding wizard to get started quickly.

The wizard will:
  • Detect your project type automatically
  • Configure Simple Mode settings
  • Suggest your first command
  • Show a quick demonstration
  • Celebrate your success! 🎉
""",
    )
    simple_mode_configure_parser = simple_mode_subparsers.add_parser(
        "configure",
        aliases=["config"],
        help="Configure Simple Mode settings interactively",
        description="""Run the configuration wizard to customize Simple Mode settings.

The wizard will guide you through:
  • Basic settings (enable/disable, natural language, etc.)
  • Quality thresholds
  • Advanced options
""",
    )
    simple_mode_progress_parser = simple_mode_subparsers.add_parser(
        "progress",
        help="Show your Simple Mode learning progression",
        description="""Display your learning progression, usage statistics, and unlocked features.

Shows:
  • Current level (Beginner, Intermediate, Advanced)
  • Total commands used
  • Commands to next level
  • Features unlocked
  • Usage breakdown by command type
""",
    )
    simple_mode_full_parser = simple_mode_subparsers.add_parser(
        "full",
        help="Run full lifecycle workflow with testing and development loopbacks",
        description="""Execute the complete development lifecycle with automatic quality loopbacks.

This workflow runs the full SDLC pipeline:
  • Requirements gathering
  • Planning and story creation
  • Architecture design
  • API design
  • Implementation
  • Code review with quality gates
  • Test generation and execution
  • Security scanning
  • Documentation generation

Features:
  • Automatic loopbacks if code quality scores aren't good enough
  • Test execution with retry logic
  • Security validation with remediation
  • Final quality review before completion

The workflow will automatically retry and improve code until quality thresholds are met.""",
    )
    simple_mode_full_parser.add_argument(
        "--prompt", "-p",
        help="Natural language description of what to build or implement. Required for greenfield workflows.",
    )
    simple_mode_full_parser.add_argument(
        "--file",
        help="Target file or directory path for workflows that operate on existing code.",
    )
    simple_mode_full_parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable fully automated execution mode. Skips all interactive prompts.",
    )

    # Simple Mode: build
    simple_mode_build_parser = simple_mode_subparsers.add_parser(
        "build",
        help="Build new features with Simple Mode workflow",
        description="""Build new features using the Simple Mode build workflow.

This workflow executes:
  • Step 1: Enhance prompt (requirements analysis)
  • Step 2: Create user stories
  • Step 3: Design architecture
  • Step 4: Design API/data models
  • Step 5: Implement code
  • Step 6: Review code quality
  • Step 7: Generate tests

Use --fast to skip documentation steps (1-4) for faster iteration.""",
    )
    simple_mode_build_parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Natural language description of the feature to build",
    )
    simple_mode_build_parser.add_argument(
        "--file",
        help="Target file path for implementation",
    )
    simple_mode_build_parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip documentation steps (1-4) for 50-70% faster execution",
    )
    simple_mode_build_parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable fully automated execution mode",
    )

    # Simple Mode: resume
    simple_mode_resume_parser = simple_mode_subparsers.add_parser(
        "resume",
        help="Resume a failed or paused workflow",
        description="""Resume a workflow from the last completed step.

Use this command to continue a workflow that was interrupted or failed.
The workflow will resume from the last successfully completed step.""",
    )
    simple_mode_resume_parser.add_argument(
        "workflow_id",
        nargs="?",
        help="Workflow ID to resume (use --list to see available workflows)",
    )
    simple_mode_resume_parser.add_argument(
        "--list",
        action="store_true",
        help="List available workflows that can be resumed",
    )
    simple_mode_resume_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate state before resuming",
    )
