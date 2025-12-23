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

Supports batch processing: specify multiple files or use --pattern for glob patterns.

Example:
  tapps-agents reviewer review src/app.py
  tapps-agents reviewer review src/app.py --format text
  tapps-agents reviewer review file1.py file2.py file3.py
  tapps-agents reviewer review --pattern "**/*.py" --max-workers 8""",
    )
    review_parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to source code file(s) to review. Supports multiple files, directories (auto-discovers code files), or glob patterns. If not provided and --pattern is not used, the command will error.",
    )
    review_parser.add_argument(
        "--pattern",
        help="Glob pattern to match files (e.g., '**/*.py'). Overrides file arguments. Files are resolved relative to current working directory.",
    )
    review_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of concurrent file operations (default: 4). Use 1 for sequential processing.",
    )
    # Model parameter removed - all LLM operations handled by Cursor Skills
    review_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown", "html"],
        default="json",
        help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for Markdown, 'html' for HTML report",
    )
    review_parser.add_argument(
        "--output",
        help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.",
    )
    review_parser.add_argument(
        "--fail-under",
        type=float,
        help="Exit with code 1 if the overall score is below this threshold (0-100). Useful for CI.",
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

Supports batch processing: specify multiple files or use --pattern for glob patterns.

Example:
  tapps-agents reviewer score src/utils.py
  tapps-agents reviewer score src/utils.py --format text
  tapps-agents reviewer score file1.py file2.py file3.py
  tapps-agents reviewer score --pattern "**/*.py" --max-workers 8""",
    )
    score_parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to source code file(s) to score. Supports multiple files, directories (auto-discovers code files), or glob patterns. If not provided and --pattern is not used, the command will error.",
    )
    score_parser.add_argument(
        "--pattern",
        help="Glob pattern to match files (e.g., '**/*.py'). Overrides file arguments. Files are resolved relative to current working directory.",
    )
    score_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of concurrent file operations (default: 4). Use 1 for sequential processing.",
    )
    score_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown", "html"],
        default="json",
        help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for Markdown, 'html' for HTML report",
    )
    score_parser.add_argument(
        "--output",
        help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.",
    )
    score_parser.add_argument(
        "--fail-under",
        type=float,
        help="Exit with code 1 if the overall score is below this threshold (0-100). Useful for CI.",
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

Supports batch processing: specify multiple files or use --pattern for glob patterns.

Example:
  tapps-agents reviewer lint src/main.py
  tapps-agents reviewer lint src/main.py --format text
  tapps-agents reviewer lint src/main.py --output lint-report.json
  tapps-agents reviewer lint file1.py file2.py file3.py
  tapps-agents reviewer lint --pattern "**/*.py" --max-workers 8""",
    )
    lint_parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to source code file(s) to lint. Supports multiple files, directories (auto-discovers code files), or glob patterns. If not provided and --pattern is not used, the command will error.",
    )
    lint_parser.add_argument(
        "--pattern",
        help="Glob pattern to match files (e.g., '**/*.py'). Overrides file arguments. Files are resolved relative to current working directory.",
    )
    lint_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of concurrent file operations (default: 4). Use 1 for sequential processing.",
    )
    lint_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown", "html"],
        default="json",
        help="Output format: 'json' for structured lint results (default), 'text' for human-readable output, 'markdown' for Markdown, 'html' for HTML report",
    )
    lint_parser.add_argument(
        "--output",
        help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.",
    )
    lint_parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 1 if any lint issues are found (or any files fail in batch mode). Useful for CI.",
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

Supports batch processing: specify multiple files or use --pattern for glob patterns.

Example:
  tapps-agents reviewer type-check src/models.py
  tapps-agents reviewer type-check src/models.py --format text
  tapps-agents reviewer type-check src/models.py --output type-check.json
  tapps-agents reviewer type-check file1.py file2.py file3.py
  tapps-agents reviewer type-check --pattern "**/*.py" --max-workers 8""",
    )
    type_check_parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to source code file(s) to type-check. Supports multiple files, directories (auto-discovers code files), or glob patterns. If not provided and --pattern is not used, the command will error.",
    )
    type_check_parser.add_argument(
        "--pattern",
        help="Glob pattern to match files (e.g., '**/*.py'). Overrides file arguments. Files are resolved relative to current working directory.",
    )
    type_check_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of concurrent file operations (default: 4). Use 1 for sequential processing.",
    )
    type_check_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown", "html"],
        default="json",
        help="Output format: 'json' for structured results (default), 'text' for human-readable output, 'markdown' for Markdown, 'html' for HTML report",
    )
    type_check_parser.add_argument(
        "--output",
        help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.",
    )
    type_check_parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 1 if any type-check errors are found (or any files fail in batch mode). Useful for CI.",
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

    docs_parser = reviewer_subparsers.add_parser(
        "docs",
        aliases=["*docs"],
        help="Get library documentation from Context7",
        description="""Get up-to-date library documentation from Context7.

Retrieves documentation for a library using KB-first lookup with automatic fallback.
The documentation is cached locally for fast subsequent lookups.

Example:
  tapps-agents reviewer docs react
  tapps-agents reviewer docs fastapi routing
  tapps-agents reviewer docs react hooks --mode code --page 2
  tapps-agents reviewer docs react --format markdown""",
    )
    docs_parser.add_argument(
        "library",
        help="Library name (e.g., 'react', 'fastapi', 'pytest')",
    )
    docs_parser.add_argument(
        "topic",
        nargs="?",
        default=None,
        help="Optional topic name (e.g., 'hooks', 'routing', 'fixtures'). Defaults to 'overview' if not specified.",
    )
    docs_parser.add_argument(
        "--mode",
        choices=["code", "info"],
        default="code",
        help="Documentation mode: 'code' for API references and code examples (default), 'info' for conceptual guides",
    )
    docs_parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number for pagination (default: 1). Use if documentation is paginated.",
    )
    docs_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="json",
        help="Output format: 'json' for structured data (default), 'text' for plain text, 'markdown' for Markdown",
    )
    docs_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache and fetch fresh documentation from Context7 API",
    )

    reviewer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show reviewer commands"
    )

