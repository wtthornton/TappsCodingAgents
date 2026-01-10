#!/usr/bin/env python3
"""Update the improver agent help message."""

import sys
from pathlib import Path

def main():
    file_path = Path("tapps_agents/agents/improver/agent.py")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    content = file_path.read_text(encoding="utf-8")
    
    # Replace the help message
    old = '''        help_message = {
            "*refactor [file_path] [instruction]": "Refactor existing code to improve structure and maintainability",
            "*optimize [file_path] [type]": "Optimize code for performance, memory, or both (type: performance|memory|both)",
            "*improve-quality [file_path]": "Improve overall code quality (best practices, patterns, documentation)",
            "*help": "Show this help message",
        }'''
    
    new = '''        help_message = {
            "*refactor [file_path] [instruction]": "Refactor existing code to improve structure and maintainability",
            "*optimize [file_path] [type]": "Optimize code for performance, memory, or both (type: performance|memory|both)",
            "*improve-quality [file_path] [--auto-apply] [--preview]": "Improve code quality (--auto-apply: apply, --preview: diff)",
            "*help": "Show this help message",
        }'''
    
    if old in content:
        content = content.replace(old, new)
        file_path.write_text(content, encoding="utf-8")
        print("Updated help message successfully")
    else:
        print("Old string not found - help message may already be updated")

if __name__ == "__main__":
    main()
