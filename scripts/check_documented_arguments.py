#!/usr/bin/env python3
"""
Utility script to detect documented but missing arguments in CLI parsers.

This script scans documentation files for argument usage patterns and
verifies they exist in the actual parser definitions.

Usage:
    python scripts/check_documented_arguments.py
    python scripts/check_documented_arguments.py --fix  # Auto-fix simple cases
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.cli.parsers import (
    improver,
    tester,
)


def extract_arguments_from_docs(doc_path: Path) -> dict[str, list[str]]:
    """
    Extract argument usage from documentation files.
    
    Returns:
        Dictionary mapping command paths to lists of argument names
        Example: {"improver improve-quality": ["--focus", "--format"]}
    """
    if not doc_path.exists():
        return {}
    
    content = doc_path.read_text(encoding="utf-8")
    
    # Pattern to match command lines with arguments
    # Matches: tapps-agents <agent> <command> <args> [--arg value]
    pattern = r"tapps-agents\s+(\w+)\s+([\w-]+)([^\n]*)"
    matches = re.finditer(pattern, content)
    
    results: dict[str, list[str]] = {}
    
    for match in matches:
        agent = match.group(1)
        command = match.group(2)
        args_str = match.group(3)
        
        # Extract argument names (--arg or -arg)
        arg_pattern = r"--(\w+(?:-\w+)*)"
        args_found = re.findall(arg_pattern, args_str)
        
        command_path = f"{agent} {command}"
        if command_path not in results:
            results[command_path] = []
        results[command_path].extend([f"--{arg}" for arg in args_found])
    
    # Deduplicate
    for key in results:
        results[key] = list(set(results[key]))
    
    return results


def check_parser_has_argument(
    agent: str, command: str, arg_name: str
) -> tuple[bool, str]:
    """
    Check if a parser has a specific argument.
    
    Returns:
        Tuple of (exists, error_message)
    """
    try:
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        
        # Import and register the parser
        if agent == "improver":
            improver.add_improver_parser(subparsers)
        elif agent == "tester":
            tester.add_tester_parser(subparsers)
        else:
            return False, f"Unknown agent: {agent}"
        
        # Navigate to the command parser
        agent_parser = subparsers.choices[agent]
        agent_subparsers = agent_parser._subparsers._group_actions[0]
        
        if command not in agent_subparsers.choices:
            return False, f"Command '{command}' not found"
        
        command_parser = agent_subparsers.choices[command]
        
        # Check if argument exists by inspecting parser actions
        arg_name_clean = arg_name.replace("--", "")
        attr_name = arg_name_clean.replace("-", "_")
        
        # Check all actions in the parser
        for action in command_parser._actions:
            if hasattr(action, "dest") and action.dest == attr_name:
                return True, ""
            if hasattr(action, "option_strings") and arg_name in action.option_strings:
                return True, ""
        
        return False, f"Argument '{arg_name}' not found in parser"
    except Exception as e:
        return False, f"Error setting up parser: {e}"


def scan_documentation() -> dict[str, Any]:
    """Scan all documentation files for argument usage."""
    docs_dir = project_root / "docs"
    issues: list[dict[str, Any]] = []
    
    # Scan markdown files
    for doc_file in docs_dir.rglob("*.md"):
        doc_args = extract_arguments_from_docs(doc_file)
        
        for command_path, args in doc_args.items():
            parts = command_path.split()
            if len(parts) < 2:
                continue
            
            agent = parts[0]
            command = parts[1]
            
            for arg in args:
                exists, error = check_parser_has_argument(agent, command, arg)
                if not exists:
                    issues.append({
                        "file": str(doc_file.relative_to(project_root)),
                        "agent": agent,
                        "command": command,
                        "argument": arg,
                        "error": error,
                    })
    
    return {"issues": issues, "total": len(issues)}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check for documented but missing CLI arguments"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix simple cases (not implemented yet)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print("Scanning documentation for argument usage...")
    result = scan_documentation()
    
    if result["total"] == 0:
        print("[OK] No issues found! All documented arguments exist in parsers.")
        return 0
    
    print(f"\n[ERROR] Found {result['total']} issue(s):\n")
    
    for issue in result["issues"]:
        print(f"  File: {issue['file']}")
        print(f"  Command: {issue['agent']} {issue['command']}")
        print(f"  Missing Argument: {issue['argument']}")
        print(f"  Error: {issue['error']}")
        print()
    
    if args.fix:
        print("[WARNING] Auto-fix not yet implemented. Please fix manually.")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())

