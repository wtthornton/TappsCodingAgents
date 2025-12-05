"""
Command-line interface for TappsCodingAgents
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .agents.reviewer.agent import ReviewerAgent
from .agents.planner.agent import PlannerAgent


async def review_command(file_path: str, model: Optional[str] = None, output_format: str = "json"):
    """Review a code file (supports both *review and review commands)"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    reviewer = ReviewerAgent()
    try:
        # Activate agent (load configs, etc.)
        await reviewer.activate()
        
        # Execute review command
        result = await reviewer.run("review", file=file_path, model=model or "qwen2.5-coder:7b")
        
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            # Simple text format
            print(f"Review: {result['file']}")
            if "scoring" in result:
                scores = result["scoring"]
                print(f"\nScores:")
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Overall: {scores['overall_score']:.1f}/100")
                print(f"\nPassed: {result.get('passed', False)}")
            
            if "feedback" in result and "summary" in result["feedback"]:
                print(f"\nFeedback:\n{result['feedback']['summary']}")
    finally:
        await reviewer.close()


async def score_command(file_path: str, output_format: str = "json"):
    """Score a code file (supports both *score and score commands)"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        result = await reviewer.run("score", file=file_path)
        
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Scores for: {result['file']}")
            if "scoring" in result:
                scores = result["scoring"]
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Overall: {scores['overall_score']:.1f}/100")
    finally:
        await reviewer.close()


async def help_command():
    """Show help (supports both *help and help commands)"""
    reviewer = ReviewerAgent()
    await reviewer.activate()
    result = await reviewer.run("help")
    print(result["content"])


async def plan_command(description: str, output_format: str = "json"):
    """Create a plan for a feature/requirement"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("plan", description=description)
        
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Plan: {result['description']}")
            print(f"\n{result.get('plan', '')}")
    finally:
        await planner.close()


async def create_story_command(description: str, epic: Optional[str] = None, priority: str = "medium", output_format: str = "json"):
    """Generate a user story from description"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("create-story", description=description, epic=epic, priority=priority)
        
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Story created: {result['story_id']}")
            print(f"File: {result['story_file']}")
            print(f"\nTitle: {result['metadata']['title']}")
            print(f"Epic: {result['metadata']['epic']}")
            print(f"Priority: {result['metadata']['priority']}")
            print(f"Complexity: {result['metadata']['complexity']}/5")
    finally:
        await planner.close()


async def list_stories_command(epic: Optional[str] = None, status: Optional[str] = None, output_format: str = "json"):
    """List all stories in the project"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("list-stories", epic=epic, status=status)
        
        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Found {result['count']} stories")
            for story in result['stories']:
                print(f"\n{story['story_id']}: {story['title']}")
                print(f"  Epic: {story['epic']}, Status: {story['status']}, Priority: {story['priority']}")
    finally:
        await planner.close()


def main():
    """Main CLI entry point - supports both *command and command formats"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TappsCodingAgents CLI")
    subparsers = parser.add_subparsers(dest="agent", help="Agent to use")
    
    # Reviewer agent commands
    reviewer_parser = subparsers.add_parser("reviewer", help="Reviewer Agent commands")
    reviewer_subparsers = reviewer_parser.add_subparsers(dest="command", help="Commands")
    
    review_parser = reviewer_subparsers.add_parser("review", aliases=["*review"], help="Review a code file")
    review_parser.add_argument("file", help="Path to code file")
    review_parser.add_argument("--model", help="LLM model to use", default="qwen2.5-coder:7b")
    review_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    score_parser = reviewer_subparsers.add_parser("score", aliases=["*score"], help="Calculate code scores only")
    score_parser.add_argument("file", help="Path to code file")
    score_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    reviewer_help_parser = reviewer_subparsers.add_parser("help", aliases=["*help"], help="Show reviewer commands")
    
    # Planner agent commands
    planner_parser = subparsers.add_parser("planner", help="Planner Agent commands")
    planner_subparsers = planner_parser.add_subparsers(dest="command", help="Commands")
    
    plan_parser = planner_subparsers.add_parser("plan", aliases=["*plan"], help="Create a plan for a feature")
    plan_parser.add_argument("description", help="Feature/requirement description")
    plan_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    create_story_parser = planner_subparsers.add_parser("create-story", aliases=["*create-story"], help="Generate a user story")
    create_story_parser.add_argument("description", help="Story description")
    create_story_parser.add_argument("--epic", help="Epic or feature area")
    create_story_parser.add_argument("--priority", choices=["high", "medium", "low"], default="medium", help="Priority")
    create_story_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    list_stories_parser = planner_subparsers.add_parser("list-stories", aliases=["*list-stories"], help="List all stories")
    list_stories_parser.add_argument("--epic", help="Filter by epic")
    list_stories_parser.add_argument("--status", help="Filter by status")
    list_stories_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    planner_help_parser = planner_subparsers.add_parser("help", aliases=["*help"], help="Show planner commands")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.agent == "reviewer":
        command = args.command.lstrip("*") if args.command else None
        if command == "review":
            asyncio.run(review_command(args.file, args.model, getattr(args, "format", "json")))
        elif command == "score":
            asyncio.run(score_command(args.file, getattr(args, "format", "json")))
        elif command == "help":
            asyncio.run(help_command())
        else:
            asyncio.run(help_command())
    elif args.agent == "planner":
        command = args.command.lstrip("*") if args.command else None
        if command == "plan":
            asyncio.run(plan_command(args.description, getattr(args, "format", "json")))
        elif command == "create-story":
            asyncio.run(create_story_command(
                args.description,
                epic=getattr(args, "epic", None),
                priority=getattr(args, "priority", "medium"),
                output_format=getattr(args, "format", "json")
            ))
        elif command == "list-stories":
            asyncio.run(list_stories_command(
                epic=getattr(args, "epic", None),
                status=getattr(args, "status", None),
                output_format=getattr(args, "format", "json")
            ))
        elif command == "help":
            planner = PlannerAgent()
            asyncio.run(planner.activate())
            result = asyncio.run(planner.run("help"))
            print(result["content"])
            asyncio.run(planner.close())
        else:
            # Show planner help by default
            planner = PlannerAgent()
            asyncio.run(planner.activate())
            result = asyncio.run(planner.run("help"))
            print(result["content"])
            asyncio.run(planner.close())
    else:
        # Show main help
        parser.print_help()


if __name__ == "__main__":
    main()

