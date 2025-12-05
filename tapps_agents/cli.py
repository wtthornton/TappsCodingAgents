"""
Command-line interface for TappsCodingAgents
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .agents.reviewer.agent import ReviewerAgent


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


def main():
    """Main CLI entry point - supports both *command and command formats"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TappsCodingAgents CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Review command (supports both *review and review)
    review_parser = subparsers.add_parser("review", aliases=["*review"], help="Review a code file")
    review_parser.add_argument("file", help="Path to code file")
    review_parser.add_argument("--model", help="LLM model to use", default="qwen2.5-coder:7b")
    review_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    # Score command (supports both *score and score)
    score_parser = subparsers.add_parser("score", aliases=["*score"], help="Calculate code scores only")
    score_parser.add_argument("file", help="Path to code file")
    score_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    # Help command (supports both *help and help)
    help_parser = subparsers.add_parser("help", aliases=["*help"], help="Show available commands")
    
    args = parser.parse_args()
    
    # Handle commands (with or without * prefix)
    command = args.command.lstrip("*") if args.command else None
    
    if command == "review":
        asyncio.run(review_command(args.file, args.model, args.format))
    elif command == "score":
        asyncio.run(score_command(args.file, args.format))
    elif command == "help":
        asyncio.run(help_command())
    else:
        # Show help by default
        asyncio.run(help_command())


if __name__ == "__main__":
    main()

