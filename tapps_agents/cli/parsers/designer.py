"""
Designer agent parser definitions
"""
import argparse


def add_designer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add designer agent parser and subparsers"""
    designer_parser = subparsers.add_parser(
        "designer",
        help="Designer Agent commands",
        description="""API, data model, and UI/UX design agent.
        
The Designer Agent creates design specifications:
  • API design (REST, GraphQL, gRPC)
  • Data model and schema design
  • UI/UX design specifications
  • Wireframes
  • Design systems

Use this agent to design interfaces, APIs, and user experiences before implementation.""",
    )
    designer_subparsers = designer_parser.add_subparsers(
        dest="command", help="Designer agent subcommand (use 'help' to see all available commands)"
    )

    api_design_parser = designer_subparsers.add_parser(
        "api-design",
        aliases=["*api-design"],
        help="Design APIs (REST, GraphQL, gRPC)",
        description="""Design API specifications for REST, GraphQL, or gRPC.
        
Creates comprehensive API designs including:
  • Endpoints and routes
  • Request/response schemas
  • Authentication and authorization
  • Error handling
  • Versioning strategy
  • Documentation structure

Example:
  tapps-agents designer api-design "User management API with CRUD operations"
  tapps-agents designer api-design "Product catalog API" --api-type GraphQL --output-file api-spec.yaml""",
    )
    api_design_parser.add_argument("requirements", help="API requirements description including endpoints needed, data models, authentication requirements, and use cases. Be specific about functionality and constraints.")
    api_design_parser.add_argument(
        "--api-type", default="REST", help="API type to design: 'REST' for RESTful APIs (default), 'GraphQL' for GraphQL APIs, 'gRPC' for gRPC services"
    )
    api_design_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    api_design_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    api_design_parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement for this command",
    )
    api_design_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Force prompt enhancement even if quality is high",
    )
    api_design_parser.add_argument(
        "--enhance-mode",
        choices=["quick", "full"],
        help="Override enhancement mode: 'quick' for fast 3-stage enhancement, 'full' for complete 7-stage enhancement",
    )
    api_design_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    data_model_parser = designer_subparsers.add_parser(
        "data-model-design",
        aliases=["*data-model-design"],
        help="Design data models, schemas, and database structures",
        description="""Design comprehensive data models and database schemas.
        
Creates:
  • Entity definitions and relationships
  • Field types and constraints
  • Primary and foreign keys
  • Indexes and optimization
  • Validation rules
  • Migration considerations

Use this to design database schemas, ORM models, or data structures before implementation.""",
    )
    data_model_parser.add_argument("requirements", help="Data model requirements description including entities, relationships, data types, constraints, and use cases. Describe what data needs to be stored and how it relates.")
    data_model_parser.add_argument("--data-source", help="Description of the data source or database system (e.g., 'PostgreSQL', 'MongoDB', 'in-memory'). Influences schema design and optimization strategies.")
    data_model_parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement for this command",
    )
    data_model_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Force prompt enhancement even if quality is high",
    )
    data_model_parser.add_argument(
        "--enhance-mode",
        choices=["quick", "full"],
        help="Override enhancement mode: 'quick' for fast 3-stage enhancement, 'full' for complete 7-stage enhancement",
    )
    data_model_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    data_model_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    ui_ux_parser = designer_subparsers.add_parser(
        "ui-ux-design",
        aliases=["*ui-ux-design"],
        help="Design user interfaces and user experiences",
        description="""Design user interfaces and user experience specifications.
        
Creates:
  • UI component specifications
  • User flow diagrams
  • Interaction patterns
  • Accessibility considerations
  • Responsive design guidelines
  • User experience principles

Use this to design interfaces before implementation, ensuring good UX and accessibility.""",
    )
    ui_ux_parser.add_argument("feature_description", help="Description of the feature or interface to design. Include user goals, functionality, and any design constraints or brand guidelines.")
    ui_ux_parser.add_argument("--user-stories", nargs="+", help="Space-separated list of user stories that inform the design (e.g., 'As a user, I want to login so that I can access my account'). Helps ensure design meets user needs.")
    ui_ux_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    ui_ux_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    wireframes_parser = designer_subparsers.add_parser(
        "wireframes", 
        aliases=["*wireframes"], 
        help="Generate wireframes for user interface design",
        description="""Generate wireframe specifications for UI screens and components.
        
Creates:
  • Layout structure and positioning
  • Component placement
  • Navigation elements
  • Content hierarchy
  • Interactive elements
  • Responsive breakpoints

Wireframes are provided in text format (ASCII art or structured descriptions) that can be used as blueprints for implementation.""",
    )
    wireframes_parser.add_argument("screen_description", help="Description of the screen, page, or component to wireframe. Include purpose, key elements, user actions, and layout requirements.")
    wireframes_parser.add_argument(
        "--wireframe-type",
        default="page",
        help="Type of wireframe to generate: 'page' for full page layouts (default), 'component' for individual UI components, 'flow' for multi-screen user flows",
    )
    wireframes_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    wireframes_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    design_system_designer_parser = designer_subparsers.add_parser(
        "design-system",
        aliases=["*design-system"],
        help="Develop or extend a design system for consistent UI/UX",
        description="""Create or extend a comprehensive design system.
        
Develops:
  • Component library specifications
  • Design tokens (colors, typography, spacing)
  • Style guidelines
  • Usage patterns and best practices
  • Accessibility standards
  • Responsive design rules

Use this to establish or extend a design system that ensures consistency across your application.""",
    )
    design_system_designer_parser.add_argument(
        "project_description", help="Description of the project or application for which to develop the design system. Include project goals, target users, and any existing design elements."
    )
    design_system_designer_parser.add_argument(
        "--brand-guidelines", help="Brand guidelines, color schemes, typography preferences, or existing brand assets that should be incorporated into the design system"
    )
    design_system_designer_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    design_system_designer_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")

    designer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show designer commands"
    )

