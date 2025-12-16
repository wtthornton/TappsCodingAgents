"""
Analyst agent parser definitions
"""
import argparse


def add_analyst_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add analyst agent parser and subparsers"""
    analyst_parser = subparsers.add_parser("analyst", help="Analyst Agent commands")
    analyst_subparsers = analyst_parser.add_subparsers(dest="command", help="Commands")

    gather_req_parser = analyst_subparsers.add_parser(
        "gather-requirements",
        aliases=["*gather-requirements"],
        help="Gather requirements for a project",
    )
    gather_req_parser.add_argument("description", help="Requirement description")
    gather_req_parser.add_argument("--context", help="Additional context")
    gather_req_parser.add_argument("--output-file", help="Output file path")

    stakeholder_parser = analyst_subparsers.add_parser(
        "stakeholder-analysis",
        aliases=["*stakeholder-analysis"],
        help="Perform stakeholder analysis",
    )
    stakeholder_parser.add_argument(
        "description", help="Project or feature description"
    )
    stakeholder_parser.add_argument(
        "--stakeholders", nargs="+", help="List of stakeholders"
    )

    tech_research_parser = analyst_subparsers.add_parser(
        "tech-research", aliases=["*tech-research"], help="Perform technology research"
    )
    tech_research_parser.add_argument("requirement", help="Technology requirement")
    tech_research_parser.add_argument("--context", help="Additional context")
    tech_research_parser.add_argument(
        "--criteria", nargs="+", help="Evaluation criteria"
    )

    estimate_parser = analyst_subparsers.add_parser(
        "estimate-effort",
        aliases=["*estimate-effort"],
        help="Estimate effort for tasks",
    )
    estimate_parser.add_argument("feature_description", help="Feature description")
    estimate_parser.add_argument("--context", help="Additional context")

    assess_risk_parser = analyst_subparsers.add_parser(
        "assess-risk", aliases=["*assess-risk"], help="Assess project risks"
    )
    assess_risk_parser.add_argument(
        "feature_description", help="Feature or project description"
    )
    assess_risk_parser.add_argument("--context", help="Additional context")

    competitive_parser = analyst_subparsers.add_parser(
        "competitive-analysis",
        aliases=["*competitive-analysis"],
        help="Perform competitive analysis",
    )
    competitive_parser.add_argument("product_description", help="Product description")
    competitive_parser.add_argument(
        "--competitors", nargs="+", help="List of competitors"
    )

    analyst_subparsers.add_parser(
        "help", aliases=["*help"], help="Show analyst commands"
    )

