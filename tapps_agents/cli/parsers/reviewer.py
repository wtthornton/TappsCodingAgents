"""
Reviewer agent parser definitions
"""
import argparse


def add_reviewer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add reviewer agent parser and subparsers"""
    reviewer_parser = subparsers.add_parser(
        "reviewer",
        help="Reviewer Agent commands",
        description="""Code review and quality analysis agent.
        
The Reviewer Agent provides comprehensive code quality analysis including:
  • Code scoring (complexity, security, maintainability)
  • Linting with Ruff
  • Type checking with mypy
  • Duplication detection
  • Quality reports in multiple formats
  • Project-wide analysis

Use this agent to assess code quality, identify issues, and generate
detailed quality reports for your codebase.""",
    )
    reviewer_subparsers = reviewer_parser.add_subparsers(
        dest="command", help="Reviewer agent subcommand (use 'help' to see all available commands)"
    )

    review_parser = reviewer_subparsers.add_parser(
        "review",
        aliases=["*review"],
        help="Review a code file with AI analysis",
        description="""Perform comprehensive AI-powered code review.
        
Analyzes code for:
  • Code quality and best practices
  • Potential bugs and security issues
  • Performance optimizations
  • Maintainability concerns
  • Documentation quality
  • Test coverage recommendations

Example:
  tapps-agents reviewer review src/app.py
  tapps-agents reviewer review src/app.py --format text""",
    )
    review_parser.add_argument("file", help="Path to the source code file to review. The file will be analyzed for quality, bugs, security issues, and best practices.")
    # Model parameter removed - all LLM operations handled by Cursor Skills
    review_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' for structured review data with categories and scores (default), 'text' for human-readable review report",
    )

    score_parser = reviewer_subparsers.add_parser(
        "score",
        aliases=["*score"],
        help="Calculate objective code quality scores",
        description="""Calculate objective quality metrics for code files.
        
Returns numerical scores (0-100) for:
  • Overall Quality Score
  • Complexity Score (cyclomatic complexity, lower is better)
  • Security Score (vulnerability detection)
  • Maintainability Score (code structure, documentation)
  • Test Coverage (if tests exist)

This is a fast, objective analysis without AI review. Use 'review' for
detailed AI-powered analysis.

Example:
  tapps-agents reviewer score src/utils.py
  tapps-agents reviewer score src/utils.py --format text""",
    )
    score_parser.add_argument("file", help="Path to the source code file to score. Objective metrics will be calculated without AI analysis.")
    score_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' for structured score data (default), 'text' for human-readable score summary",
    )

    lint_parser = reviewer_subparsers.add_parser(
        "lint",
        aliases=["*lint"],
        help="Run Ruff linting on a file",
        description="""Run Ruff linter to find code style and quality issues.
        
Ruff is a fast Python linter that checks for:
  • PEP 8 style violations
  • Common bugs and errors
  • Unused imports and variables
  • Code complexity issues
  • Best practice violations

Example:
  tapps-agents reviewer lint src/main.py
  tapps-agents reviewer lint src/main.py --format text""",
    )
    lint_parser.add_argument("file", help="Path to the Python source code file to lint. Ruff will analyze the file for style violations and code quality issues.")
    lint_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' for structured lint results (default), 'text' for human-readable lint output",
    )

    type_check_parser = reviewer_subparsers.add_parser(
        "type-check",
        aliases=["*type-check"],
        help="Run mypy type checking on a file",
        description="""Run mypy static type checker to find type errors.
        
Checks for:
  • Type annotation errors
  • Missing type hints
  • Incorrect type usage
  • Type inference issues
  • Import type problems

Requires type annotations in your code. Use --format text for readable output.

Example:
  tapps-agents reviewer type-check src/models.py
  tapps-agents reviewer type-check src/models.py --format text""",
    )
    type_check_parser.add_argument("file", help="Path to the Python source code file to type-check. Requires type annotations in your code for meaningful results.")
    type_check_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' for structured type check results (default), 'text' for human-readable mypy output",
    )

    report_parser = reviewer_subparsers.add_parser(
        "report",
        aliases=["*report"],
        help="Generate comprehensive quality reports",
        description="""Generate detailed quality reports in multiple formats.
        
Creates comprehensive reports including:
  • Code scores and metrics
  • Linting results
  • Type checking results
  • Duplication analysis
  • Security findings
  • Recommendations

Supports multiple output formats: JSON, Markdown, HTML, or all formats.

Example:
  tapps-agents reviewer report src/ --formats json markdown
  tapps-agents reviewer report src/ --formats all --output-dir reports/""",
    )
    report_parser.add_argument("target", help="File or directory path to analyze. Can be a single file, directory, or glob pattern. All Python files in the target will be analyzed.")
    report_parser.add_argument(
        "formats",
        nargs="+",
        choices=["json", "markdown", "html", "all"],
        help="Output formats to generate: 'json' for structured data, 'markdown' for Markdown report, 'html' for HTML report, 'all' for all formats. Can specify multiple formats.",
    )
    report_parser.add_argument(
        "--output-dir", help="Directory path where quality reports will be saved. Defaults to 'reports/quality/' in the project root. Directory will be created if it doesn't exist."
    )

    duplication_parser = reviewer_subparsers.add_parser(
        "duplication",
        aliases=["*duplication"],
        help="Detect code duplication",
        description="""Detect duplicate code blocks using jscpd.
        
Identifies:
  • Exact code duplicates
  • Similar code blocks
  • Duplication percentage
  • Locations of duplicated code

Helps identify refactoring opportunities and maintainability issues.

Example:
  tapps-agents reviewer duplication src/
  tapps-agents reviewer duplication src/utils.py --format text""",
    )
    duplication_parser.add_argument("target", help="File or directory path to analyze for code duplication. Can be a single file, directory, or glob pattern.")
    duplication_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured duplication data (default), 'text' for human-readable duplication report"
    )

    analyze_project_parser = reviewer_subparsers.add_parser(
        "analyze-project",
        aliases=["*analyze-project"],
        help="Analyze entire project with comprehensive metrics",
        description="""Perform comprehensive analysis of the entire project.
        
Runs all analysis services:
  • Code scoring across all files
  • Linting across project
  • Type checking
  • Duplication detection
  • Security scanning
  • Test coverage analysis

Optionally compares with previous analysis to show trends. Use --no-comparison
to skip comparison.

Example:
  tapps-agents reviewer analyze-project
  tapps-agents reviewer analyze-project --project-root /path/to/project --format json""",
    )
    analyze_project_parser.add_argument(
        "--project-root", help="Project root directory to analyze. Defaults to current working directory. All Python files in the project will be analyzed."
    )
    analyze_project_parser.add_argument(
        "--no-comparison",
        action="store_true",
        help="Skip comparison with previous analysis results. By default, compares current analysis with previous run to show trends and improvements.",
    )
    analyze_project_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured analysis data (default), 'text' for human-readable analysis report"
    )

    analyze_services_parser = reviewer_subparsers.add_parser(
        "analyze-services",
        aliases=["*analyze-services"],
        help="Analyze specific services or modules",
        description="""Analyze specific services or modules within a project.
        
Allows targeted analysis of specific parts of your codebase. Useful for
large projects where full analysis is time-consuming.

Specify service names or patterns to analyze. If none specified, analyzes all services.

Example:
  tapps-agents reviewer analyze-services api auth
  tapps-agents reviewer analyze-services --project-root /path/to/project""",
    )
    analyze_services_parser.add_argument(
        "services",
        nargs="*",
        help="Space-separated list of service names or directory patterns to analyze (e.g., 'api', 'auth', 'payment'). If not provided, analyzes all services/modules in the project.",
    )
    analyze_services_parser.add_argument(
        "--project-root", help="Project root directory. Defaults to current working directory. Services are identified relative to this root."
    )
    analyze_services_parser.add_argument(
        "--no-comparison",
        action="store_true",
        help="Skip comparison with previous analysis results. By default, compares current analysis with previous run to show trends.",
    )
    analyze_services_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured analysis data (default), 'text' for human-readable analysis report"
    )

    reviewer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show reviewer commands"
    )

