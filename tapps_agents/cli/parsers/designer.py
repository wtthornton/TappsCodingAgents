"""
Designer agent parser definitions
"""
import argparse


def add_designer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add designer agent parser and subparsers"""
    designer_parser = subparsers.add_parser("designer", help="Designer Agent commands")
    designer_subparsers = designer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    api_design_parser = designer_subparsers.add_parser(
        "api-design", aliases=["*api-design"], help="Design APIs (REST, GraphQL, gRPC)"
    )
    api_design_parser.add_argument("requirements", help="API requirements")
    api_design_parser.add_argument(
        "--api-type", default="REST", help="API type (REST, GraphQL, gRPC)"
    )
    api_design_parser.add_argument("--output-file", help="Output file path")

    data_model_parser = designer_subparsers.add_parser(
        "data-model-design",
        aliases=["*data-model-design"],
        help="Design data models and schemas",
    )
    data_model_parser.add_argument("requirements", help="Data model requirements")
    data_model_parser.add_argument("--data-source", help="Data source description")
    data_model_parser.add_argument("--output-file", help="Output file path")

    ui_ux_parser = designer_subparsers.add_parser(
        "ui-ux-design",
        aliases=["*ui-ux-design"],
        help="Design user interfaces and experiences",
    )
    ui_ux_parser.add_argument("feature_description", help="Feature description")
    ui_ux_parser.add_argument("--user-stories", nargs="+", help="User stories")
    ui_ux_parser.add_argument("--output-file", help="Output file path")

    wireframes_parser = designer_subparsers.add_parser(
        "wireframes", aliases=["*wireframes"], help="Generate wireframes for UI"
    )
    wireframes_parser.add_argument("screen_description", help="Screen description")
    wireframes_parser.add_argument(
        "--wireframe-type",
        default="page",
        help="Wireframe type (page, component, flow)",
    )
    wireframes_parser.add_argument("--output-file", help="Output file path")

    design_system_designer_parser = designer_subparsers.add_parser(
        "design-system",
        aliases=["*design-system"],
        help="Develop or extend a design system",
    )
    design_system_designer_parser.add_argument(
        "project_description", help="Project description"
    )
    design_system_designer_parser.add_argument(
        "--brand-guidelines", help="Brand guidelines"
    )
    design_system_designer_parser.add_argument("--output-file", help="Output file path")

    designer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show designer commands"
    )

