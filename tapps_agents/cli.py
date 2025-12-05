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
    """Review a code file"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    reviewer = ReviewerAgent()
    try:
        result = await reviewer.review_file(
            path,
            model=model or "qwen2.5-coder:7b",
            include_scoring=True,
            include_llm_feedback=True
        )
        
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


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TappsCodingAgents CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review a code file")
    review_parser.add_argument("file", help="Path to code file")
    review_parser.add_argument("--model", help="LLM model to use", default="qwen2.5-coder:7b")
    review_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    if args.command == "review":
        asyncio.run(review_command(args.file, args.model, args.format))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

