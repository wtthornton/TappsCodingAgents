"""
Architect agent parser definitions
"""
import argparse


def add_architect_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add architect agent parser and subparsers"""
    architect_parser = subparsers.add_parser(
        "architect", help="Architect Agent commands"
    )
    architect_subparsers = architect_parser.add_subparsers(
        dest="command", help="Commands"
    )

    design_system_parser = architect_subparsers.add_parser(
        "design-system",
        aliases=["*design-system"],
        help="Design the overall system architecture",
    )
    design_system_parser.add_argument("requirements", help="System requirements")
    design_system_parser.add_argument("--context", help="Additional context")
    design_system_parser.add_argument("--output-file", help="Output file path")

    diagram_parser = architect_subparsers.add_parser(
        "architecture-diagram",
        aliases=["*architecture-diagram"],
        help="Generate architecture diagrams",
    )
    diagram_parser.add_argument(
        "architecture_description", help="Architecture description"
    )
    diagram_parser.add_argument(
        "--diagram-type",
        default="component",
        help="Diagram type (component, sequence, deployment)",
    )
    diagram_parser.add_argument("--output-file", help="Output file path")

    tech_selection_parser = architect_subparsers.add_parser(
        "tech-selection",
        aliases=["*tech-selection"],
        help="Select appropriate technologies",
    )
    tech_selection_parser.add_argument(
        "component_description", help="Component description"
    )
    tech_selection_parser.add_argument("--requirements", help="Requirements")
    tech_selection_parser.add_argument("--constraints", nargs="+", help="Constraints")

    security_design_parser = architect_subparsers.add_parser(
        "design-security",
        aliases=["*design-security"],
        help="Design security aspects of the system",
    )
    security_design_parser.add_argument("system_description", help="System description")
    security_design_parser.add_argument("--threat-model", help="Threat model")

    boundaries_parser = architect_subparsers.add_parser(
        "define-boundaries",
        aliases=["*define-boundaries"],
        help="Define system boundaries and interfaces",
    )
    boundaries_parser.add_argument("system_description", help="System description")
    boundaries_parser.add_argument("--context", help="Additional context")

    architect_subparsers.add_parser(
        "help", aliases=["*help"], help="Show architect commands"
    )

