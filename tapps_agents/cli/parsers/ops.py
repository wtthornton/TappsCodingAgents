"""
Ops agent parser definitions
"""
import argparse


def add_ops_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add ops agent parser and subparsers"""
    ops_parser = subparsers.add_parser(
        "ops",
        help="Ops Agent commands",
        description="""DevOps and operations agent.
        
The Ops Agent handles deployment and operations tasks:
  • Security scanning
  • Compliance checking (GDPR, HIPAA, SOC2)
  • Deployment automation
  • Infrastructure setup
  • Dependency auditing

Use this agent for security, compliance, and deployment tasks.""",
    )
    ops_subparsers = ops_parser.add_subparsers(
        dest="command", help="Ops agent subcommand (use 'help' to see all available commands)"
    )

    security_scan_parser = ops_subparsers.add_parser(
        "security-scan",
        aliases=["*security-scan"],
        help="Perform security vulnerability scanning",
        description="""Scan code for security vulnerabilities.
        
Detects:
  • SQL injection vulnerabilities
  • XSS (Cross-Site Scripting) issues
  • Secret keys and credentials
  • Insecure dependencies
  • Authentication/authorization flaws
  • Input validation issues

Example:
  tapps-agents ops security-scan
  tapps-agents ops security-scan --target src/api/ --type sql_injection""",
    )
    security_scan_parser.add_argument(
        "--target", help="File or directory path to scan for security vulnerabilities. Defaults to project root if not specified. Can be a specific file, directory, or pattern."
    )
    security_scan_parser.add_argument(
        "--type",
        default="all",
        help="Type of security scan to perform: 'all' for comprehensive scan (default), 'sql_injection' for SQL injection vulnerabilities, 'xss' for cross-site scripting, 'secrets' for exposed credentials, or other specific vulnerability types",
    )
    security_scan_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    compliance_check_parser = ops_subparsers.add_parser(
        "compliance-check",
        aliases=["*compliance-check"],
        help="Check compliance with regulatory standards",
        description="""Check code and configuration for regulatory compliance.
        
Validates compliance with:
  • GDPR (General Data Protection Regulation)
  • HIPAA (Health Insurance Portability)
  • SOC 2 (Service Organization Control)
  • General security best practices

Example:
  tapps-agents ops compliance-check --type GDPR
  tapps-agents ops compliance-check --type all""",
    )
    compliance_check_parser.add_argument(
        "--type",
        default="general",
        help="Compliance standard to check: 'general' for general security best practices (default), 'GDPR' for General Data Protection Regulation, 'HIPAA' for Health Insurance Portability, 'SOC2' for Service Organization Control, 'all' for comprehensive compliance check",
    )
    compliance_check_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    deploy_parser = ops_subparsers.add_parser(
        "deploy", 
        aliases=["*deploy"], 
        help="Deploy application to specified environment",
        description="""Deploy application to a target environment.
        
Handles:
  • Environment configuration
  • Dependency installation
  • Service startup
  • Health checks
  • Rollback procedures

Use this to automate deployment processes. Ensure deployment configurations are properly set up before use.""",
    )
    deploy_parser.add_argument(
        "--target",
        default="local",
        help="Deployment target environment: 'local' for local development (default), 'staging' for staging environment, 'production' for production deployment",
    )
    deploy_parser.add_argument("--environment", help="Name of a specific environment configuration to use. Overrides --target if a matching configuration exists.")

    infrastructure_setup_parser = ops_subparsers.add_parser(
        "infrastructure-setup",
        aliases=["*infrastructure-setup"],
        help="Set up infrastructure configuration and deployment files",
        description="""Generate infrastructure setup files and configurations.
        
Creates configuration for:
  • Docker containers and docker-compose
  • Kubernetes deployments and services
  • Terraform infrastructure as code
  • CI/CD pipeline configurations

Use this to bootstrap infrastructure setup for your project.""",
    )
    infrastructure_setup_parser.add_argument(
        "--type",
        default="docker",
        help="Infrastructure type to set up: 'docker' for Docker and docker-compose (default), 'kubernetes' for K8s manifests, 'terraform' for Terraform configurations",
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
        help="Minimum vulnerability severity to report: 'low' for all vulnerabilities, 'medium' for medium and above, 'high' for high and critical (default), 'critical' for critical only",
    )
    audit_dependencies_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    audit_dependencies_parser.add_argument(
        "--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured vulnerability data (default), 'text' for human-readable report, 'markdown' for markdown format"
    )
    audit_dependencies_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    ops_subparsers.add_parser("help", aliases=["*help"], help="Show ops commands")

