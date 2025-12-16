"""
Reviewer agent parser definitions
"""
import argparse


def add_reviewer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add reviewer agent parser and subparsers"""
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

