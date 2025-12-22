"""
Architect agent parser definitions
"""
import argparse


def add_architect_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add architect agent parser and subparsers"""
    architect_parser = subparsers.add_parser(
        "architect",
        help="Architect Agent commands",
        description="""System architecture and design agent.
        
The Architect Agent designs system architecture:
  • System architecture design
  • Architecture diagrams (component, sequence, deployment)
  • Technology selection
  • Security architecture
  • System boundaries and interfaces

Use this agent to design scalable, maintainable system architectures
with appropriate technology choices.""",
    )
    architect_subparsers = architect_parser.add_subparsers(
        dest="command", help="Architect agent subcommand (use 'help' to see all available commands)"
    )

    design_system_parser = architect_subparsers.add_parser(
        "design-system",
        aliases=["*design-system"],
        help="Design the overall system architecture",
        description="""Design comprehensive system architecture from requirements.
        
Creates architecture including:
  • System components and modules
  • Component interactions
  • Data flow
  • Technology stack
  • Scalability considerations
  • Deployment architecture

Example:
  tapps-agents architect design-system "Microservices e-commerce platform"
  tapps-agents architect design-system "Real-time chat application" --output-file architecture.md""",
    )
    design_system_parser.add_argument("requirements", help="System requirements description including functional requirements, non-functional requirements, constraints, and goals. Be comprehensive for best results.")
    design_system_parser.add_argument("--context", help="Additional context such as existing systems, technical constraints, organizational standards, or integration requirements")
    design_system_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    design_system_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    design_system_parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement for this command",
    )
    design_system_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Force prompt enhancement even if quality is high",
    )
    design_system_parser.add_argument(
        "--enhance-mode",
        choices=["quick", "full"],
        help="Override enhancement mode: 'quick' for fast 3-stage enhancement, 'full' for complete 7-stage enhancement",
    )

    diagram_parser = architect_subparsers.add_parser(
        "architecture-diagram",
        aliases=["*architecture-diagram"],
        help="Generate architecture diagrams in various formats",
        description="""Generate visual architecture diagrams from system descriptions.
        
Creates diagrams showing:
  • Component diagrams - System components and their relationships
  • Sequence diagrams - Interaction flows and message passing
  • Deployment diagrams - Infrastructure and deployment architecture

Diagrams are generated in text format (Mermaid, PlantUML) that can be rendered in documentation or converted to images.""",
    )
    diagram_parser.add_argument(
        "architecture_description", help="Description of the system architecture to diagram. Include components, interactions, deployment structure, or sequence flows depending on diagram type."
    )
    diagram_parser.add_argument(
        "--diagram-type",
        default="component",
        help="Type of diagram to generate: 'component' for system structure (default), 'sequence' for interaction flows, 'deployment' for infrastructure layout",
    )
    diagram_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    diagram_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    tech_selection_parser = architect_subparsers.add_parser(
        "tech-selection",
        aliases=["*tech-selection"],
        help="Select appropriate technologies for system components",
        description="""Recommend technology choices based on requirements and constraints.
        
Evaluates:
  • Technology options and alternatives
  • Pros and cons of each option
  • Fit with requirements and constraints
  • Integration with existing stack
  • Community support and maturity
  • Performance and scalability characteristics

Use this when making technology decisions for new components or system parts.""",
    )
    tech_selection_parser.add_argument(
        "component_description", help="Description of the component or system part requiring technology selection. Include purpose, expected load, integration needs, and any specific requirements."
    )
    tech_selection_parser.add_argument("--requirements", help="Specific requirements that technologies must meet (e.g., 'must support horizontal scaling', 'must integrate with PostgreSQL', 'must support real-time updates')")
    tech_selection_parser.add_argument("--constraints", nargs="+", help="Space-separated list of constraints (e.g., 'budget-limited', 'must-use-existing-infrastructure', 'compliance-required'). These will influence technology recommendations.")

    security_design_parser = architect_subparsers.add_parser(
        "design-security",
        aliases=["*design-security"],
        help="Design security architecture and controls for the system",
        description="""Design comprehensive security architecture for a system.
        
Covers:
  • Authentication and authorization strategies
  • Data encryption and protection
  • Network security and boundaries
  • Threat mitigation strategies
  • Security monitoring and logging
  • Compliance considerations
  • Security best practices

Use this to ensure systems are designed with security as a foundational concern.""",
    )
    security_design_parser.add_argument("system_description", help="Description of the system requiring security design. Include system components, data types, user roles, and any specific security requirements or compliance needs.")
    security_design_parser.add_argument("--threat-model", help="Optional threat model description or known threats to address. If not provided, a threat model will be developed based on the system description.")

    boundaries_parser = architect_subparsers.add_parser(
        "define-boundaries",
        aliases=["*define-boundaries"],
        help="Define system boundaries, interfaces, and integration points",
        description="""Define clear system boundaries and interfaces.
        
Identifies:
  • System boundaries and scope
  • External interfaces and APIs
  • Integration points with other systems
  • Data flow across boundaries
  • Interface contracts and protocols
  • Dependency relationships

Use this to establish clear system boundaries and integration contracts, especially in microservices or distributed systems.""",
    )
    boundaries_parser.add_argument("system_description", help="Description of the system for which to define boundaries. Include system purpose, known external systems, and integration requirements.")
    boundaries_parser.add_argument("--context", help="Additional context such as existing systems, organizational boundaries, or architectural constraints that should influence boundary definition")

    architect_subparsers.add_parser(
        "help", aliases=["*help"], help="Show architect commands"
    )

