"""
Analyst agent parser definitions
"""
import argparse


def add_analyst_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add analyst agent parser and subparsers"""
    analyst_parser = subparsers.add_parser(
        "analyst",
        help="Analyst Agent commands",
        description="""Requirements analysis and research agent.
        
The Analyst Agent performs business and technical analysis:
  • Gather and document requirements
  • Stakeholder analysis
  • Technology research and evaluation
  • Effort estimation
  • Risk assessment
  • Competitive analysis

Use this agent at the beginning of projects to understand requirements
and make informed technology decisions.""",
    )
    analyst_subparsers = analyst_parser.add_subparsers(
        dest="command", help="Analyst agent subcommand (use 'help' to see all available commands)"
    )

    gather_req_parser = analyst_subparsers.add_parser(
        "gather-requirements",
        aliases=["*gather-requirements"],
        help="Gather and document requirements for a project",
        description="""Gather comprehensive requirements from a description.
        
Analyzes the description and extracts:
  • Functional requirements
  • Non-functional requirements
  • Constraints and assumptions
  • Success criteria
  • Dependencies

Example:
  tapps-agents analyst gather-requirements "Build a REST API for inventory management"
  tapps-agents analyst gather-requirements "E-commerce platform" --context "Must support 10k users\"""",
    )
    gather_req_parser.add_argument("description", help="Natural language description of the project, feature, or requirement to analyze. Be specific about goals, constraints, and desired outcomes.")
    gather_req_parser.add_argument("--context", help="Additional context, background information, or constraints that should be considered during requirements gathering (e.g., existing systems, technical limitations, business rules)")
    gather_req_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    gather_req_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    gather_req_parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement for this command",
    )
    gather_req_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Force prompt enhancement even if quality is high",
    )
    gather_req_parser.add_argument(
        "--enhance-mode",
        choices=["quick", "full"],
        help="Override enhancement mode: 'quick' for fast 3-stage enhancement, 'full' for complete 7-stage enhancement",
    )
    gather_req_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    stakeholder_parser = analyst_subparsers.add_parser(
        "stakeholder-analysis",
        aliases=["*stakeholder-analysis"],
        help="Perform comprehensive stakeholder analysis for a project or feature",
        description="""Analyze stakeholders and their interests, influence, and requirements.
        
Identifies:
  • Key stakeholders and their roles
  • Stakeholder interests and concerns
  • Influence and power dynamics
  • Communication requirements
  • Conflicting requirements and priorities
  • Stakeholder engagement strategies

Use this at the beginning of projects to understand who is affected and how to manage their expectations.""",
    )
    stakeholder_parser.add_argument(
        "description", help="Description of the project or feature for which to perform stakeholder analysis. Include project scope, goals, and any known stakeholder groups."
    )
    stakeholder_parser.add_argument(
        "--stakeholders", nargs="+", help="Optional list of known stakeholders to include in the analysis (e.g., 'product-owner', 'end-users', 'devops-team'). If not provided, stakeholders will be identified from the project description."
    )
    stakeholder_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    tech_research_parser = analyst_subparsers.add_parser(
        "tech-research",
        aliases=["*tech-research"],
        help="Research and evaluate technologies",
        description="""Research and evaluate technology options for a requirement.
        
Provides:
  • Technology recommendations
  • Pros and cons analysis
  • Comparison with alternatives
  • Implementation considerations
  • Community and ecosystem analysis

Example:
  tapps-agents analyst tech-research "Database for high-traffic web app"
  tapps-agents analyst tech-research "Authentication solution" --criteria security scalability""",
    )
    tech_research_parser.add_argument("requirement", help="Description of the technology need or requirement (e.g., 'database for high-traffic web app', 'authentication solution', 'API framework'). Be specific about use case and constraints.")
    tech_research_parser.add_argument("--context", help="Additional context about the project, existing tech stack, constraints, or specific requirements that should influence technology selection")
    tech_research_parser.add_argument(
        "--criteria", nargs="+", help="Space-separated list of evaluation criteria to prioritize (e.g., 'performance', 'security', 'scalability', 'cost', 'ease-of-use'). If not provided, uses standard criteria."
    )
    tech_research_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    estimate_parser = analyst_subparsers.add_parser(
        "estimate-effort",
        aliases=["*estimate-effort"],
        help="Estimate development effort and complexity for features or tasks",
        description="""Estimate the effort required to implement a feature or complete a task.
        
Provides:
  • Time estimates (hours, days, story points)
  • Complexity assessment
  • Risk factors affecting estimates
  • Breakdown by component or phase
  • Dependencies and prerequisites
  • Resource requirements

Use this for sprint planning, project estimation, and resource allocation.""",
    )
    estimate_parser.add_argument("feature_description", help="Description of the feature, task, or work item to estimate. Include functional requirements, technical complexity, and any known constraints.")
    estimate_parser.add_argument("--context", help="Additional context affecting estimation such as team experience, existing codebase complexity, technical debt, or external dependencies")
    estimate_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    assess_risk_parser = analyst_subparsers.add_parser(
        "assess-risk", 
        aliases=["*assess-risk"], 
        help="Assess risks and potential issues for a project or feature",
        description="""Identify and assess risks that could impact project success.
        
Analyzes:
  • Technical risks (complexity, dependencies, unknowns)
  • Schedule risks (timeline, resource availability)
  • Quality risks (testing, maintainability)
  • Business risks (requirements changes, stakeholder alignment)
  • External risks (dependencies, third-party services)
  • Mitigation strategies and recommendations

Use this early in projects to proactively identify and address potential problems.""",
    )
    assess_risk_parser.add_argument(
        "feature_description", help="Description of the feature or project to assess for risks. Include scope, timeline, team composition, and any known constraints or challenges."
    )
    assess_risk_parser.add_argument("--context", help="Additional context such as project history, team experience, organizational constraints, or external factors that could affect risk assessment")
    assess_risk_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    competitive_parser = analyst_subparsers.add_parser(
        "competitive-analysis",
        aliases=["*competitive-analysis"],
        help="Perform competitive analysis and market research",
        description="""Analyze competitive landscape and market positioning.
        
Provides:
  • Competitor identification and analysis
  • Feature comparison
  • Market positioning
  • Strengths and weaknesses assessment
  • Differentiation opportunities
  • Market gaps and opportunities

Use this for product planning, feature prioritization, and strategic decision-making.""",
    )
    competitive_parser.add_argument("product_description", help="Description of your product, feature, or service to analyze competitively. Include key features, target market, and value proposition.")
    competitive_parser.add_argument(
        "--competitors", nargs="+", help="Optional list of specific competitors to analyze (e.g., 'competitor-a', 'competitor-b'). If not provided, competitors will be identified from the product description and market context."
    )
    competitive_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    analyst_subparsers.add_parser(
        "help", aliases=["*help"], help="Show analyst commands"
    )

