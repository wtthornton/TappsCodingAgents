"""
Ops agent parser definitions
"""
import argparse


def add_ops_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add ops agent parser and subparsers"""
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

