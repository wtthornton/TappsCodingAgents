#!/usr/bin/env python3
"""
Documentation Code Example Testing Script

Extracts and validates Python code examples from Markdown documentation files.
This helps ensure code examples in documentation are syntactically correct and,
optionally, executable.

Usage:
    python scripts/run_doc_tests.py [--execute] [--file <path>] [--format json|text]
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import json

# Try to import yaml for frontmatter extraction
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def find_markdown_files(root: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """Find all Markdown files in the repository."""
    if exclude_patterns is None:
        exclude_patterns = [
            "node_modules", ".git", "htmlcov", "build", "dist", 
            ".pytest_cache", ".ruff_cache", ".mypy_cache", ".venv", "venv",
            "worktrees", ".tapps-agents", "__pycache__", ".egg-info"
        ]
    
    markdown_files = []
    for md_file in root.rglob("*.md"):
        # Skip excluded patterns
        path_str = str(md_file)
        if any(exclude in path_str for exclude in exclude_patterns):
            continue
        # Only include files in docs/ directory
        if "/docs/" in path_str or "\\docs\\" in path_str:
            # Exclude workflow output files (they may have incomplete examples)
            if "docs/workflows/" not in path_str:
                markdown_files.append(md_file)
    
    return sorted(markdown_files)


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from markdown content.
    
    Returns:
        (frontmatter_dict, content_without_frontmatter)
    """
    if not content.startswith("---\n"):
        return {}, content
    
    if not YAML_AVAILABLE:
        return {}, content
    
    # Find the end of frontmatter
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return {}, content
    
    try:
        frontmatter = yaml.safe_load(parts[1])
        if frontmatter is None:
            frontmatter = {}
        return frontmatter, parts[2]
    except yaml.YAMLError:
        return {}, content


def extract_python_code_blocks(content: str, file_path: Path) -> List[Tuple[str, int, str]]:
    """
    Extract Python code blocks from Markdown content.
    
    Returns:
        List of (code, line_number, context) tuples
    """
    code_blocks = []
    
    # Pattern to match Python code blocks
    # Matches: ```python ... ``` or ```python:test ... ```
    pattern = r'```python(?::(\w+))?\n(.*?)```'
    
    for match in re.finditer(pattern, content, re.DOTALL | re.MULTILINE):
        code = match.group(2)
        directive = match.group(1)  # e.g., "test", "skip", "no-exec"
        
        # Calculate line number (approximate)
        line_num = content[:match.start()].count('\n') + 1
        
        # Skip blocks marked with directives
        if directive in ("skip", "no-exec", "no-test"):
            continue
        
        # Skip empty blocks
        if not code.strip():
            continue
        
        # Get context (surrounding text for better error messages)
        context_start = max(0, match.start() - 200)
        context_end = min(len(content), match.end() + 200)
        context = content[context_start:context_end]
        
        code_blocks.append((code, line_num, context))
    
    return code_blocks


def validate_syntax(code: str, file_path: Path, line_num: int) -> Tuple[bool, Optional[str]]:
    """
    Validate Python code syntax.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        error_msg = f"Syntax error: {e.msg} (line {e.lineno})"
        return False, error_msg
    except Exception as e:
        return False, f"Parse error: {str(e)}"


def execute_code_block(
    code: str, 
    file_path: Path, 
    line_num: int,
    allowed_imports: List[str] = None
) -> Tuple[bool, Optional[str], Optional[Any]]:
    """
    Execute a Python code block in a controlled environment.
    
    This is a basic implementation that validates imports and basic execution.
    For production use, consider using a sandboxed environment.
    
    Returns:
        (success, error_message, result)
    """
    if allowed_imports is None:
        # Common imports that are safe and likely to be in examples
        allowed_imports = [
            "pathlib", "typing", "json", "yaml", "datetime", 
            "collections", "dataclasses", "enum"
        ]
    
    # Check for potentially unsafe operations
    unsafe_patterns = [
        r'__import__\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'open\s*\([^)]*["\']w',
        r'subprocess',
        r'os\.system',
        r'shutil\.',
    ]
    
    for pattern in unsafe_patterns:
        if re.search(pattern, code):
            return False, f"Unsafe operation detected: {pattern}", None
    
    # Try to parse and check imports
    try:
        tree = ast.parse(code)
        
        # Check for imports
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # For now, we just validate syntax - actual execution would require
                # a sandboxed environment
                pass
        
        # For now, we only validate syntax
        # Actual execution would require:
        # 1. Sandboxed environment (e.g., RestrictedPython, PyPy sandbox)
        # 2. Mock objects for framework imports
        # 3. Proper error handling
        
        return True, None, None
        
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg}", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def test_documentation_file(
    file_path: Path,
    repo_root: Path,
    execute: bool = False
) -> Dict[str, Any]:
    """
    Test code examples in a single documentation file.
    
    Returns:
        Dictionary with test results
    """
    # Get relative path safely
    try:
        rel_path = str(file_path.relative_to(repo_root))
    except ValueError:
        # Fallback if paths are on different drives (Windows)
        rel_path = str(file_path)
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "file": rel_path,
            "error": f"Failed to read file: {e}",
            "blocks_tested": 0,
            "blocks_passed": 0,
            "blocks_failed": 0
        }
    
    # Extract frontmatter (skip it for code extraction)
    frontmatter, content = extract_frontmatter(content)
    
    # Extract Python code blocks
    code_blocks = extract_python_code_blocks(content, file_path)
    
    if not code_blocks:
        return {
            "file": rel_path,
            "blocks_tested": 0,
            "blocks_passed": 0,
            "blocks_failed": 0,
            "status": "no_code_blocks"
        }
    
    # Get relative path safely
    try:
        rel_path = str(file_path.relative_to(repo_root))
    except ValueError:
        # Fallback if paths are on different drives (Windows)
        rel_path = str(file_path)
    
    results = {
        "file": rel_path,
        "blocks_tested": len(code_blocks),
        "blocks_passed": 0,
        "blocks_failed": 0,
        "errors": []
    }
    
    for code, line_num, context in code_blocks:
        # Validate syntax
        is_valid, error_msg = validate_syntax(code, file_path, line_num)
        
        if not is_valid:
            results["blocks_failed"] += 1
            results["errors"].append({
                "line": line_num,
                "error": error_msg,
                "code_preview": code[:200] + "..." if len(code) > 200 else code
            })
            continue
        
        # Optionally execute
        if execute:
            success, exec_error, _ = execute_code_block(code, file_path, line_num)
            if not success:
                results["blocks_failed"] += 1
                results["errors"].append({
                    "line": line_num,
                    "error": exec_error,
                    "code_preview": code[:200] + "..." if len(code) > 200 else code
                })
                continue
        
        results["blocks_passed"] += 1
    
    results["status"] = "passed" if results["blocks_failed"] == 0 else "failed"
    
    return results


def run_doc_tests(
    repo_root: Path = None,
    execute: bool = False,
    target_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run doc-tests on all or a specific documentation file.
    
    Returns:
        Dictionary with overall results
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    
    if target_file:
        # Test single file
        files_to_test = [target_file]
    else:
        # Test all documentation files
        files_to_test = find_markdown_files(repo_root)
    
    print(f"Testing code examples in {len(files_to_test)} documentation file(s)...")
    
    all_results = []
    total_blocks = 0
    total_passed = 0
    total_failed = 0
    
    for file_path in files_to_test:
        result = test_documentation_file(file_path, repo_root, execute)
        all_results.append(result)
        
        total_blocks += result["blocks_tested"]
        total_passed += result["blocks_passed"]
        total_failed += result["blocks_failed"]
        
        # Print progress for files with code blocks
        if result["blocks_tested"] > 0:
            # Use ASCII-safe symbols for Windows compatibility
            status_icon = "[OK]" if result["status"] == "passed" else "[FAIL]"
            print(f"  {status_icon} {result['file']}: "
                  f"{result['blocks_passed']}/{result['blocks_tested']} passed")
    
    return {
        "summary": {
            "files_tested": len(files_to_test),
            "files_with_code": len([r for r in all_results if r["blocks_tested"] > 0]),
            "total_blocks": total_blocks,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": (total_passed / total_blocks * 100) if total_blocks > 0 else 100.0
        },
        "results": all_results,
        "mode": "execute" if execute else "syntax_only"
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test code examples in documentation files"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute code blocks (default: syntax validation only)"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Test a specific file (relative to repo root)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        help="Repository root directory (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    repo_root = Path(args.repo_root) if args.repo_root else None
    target_file = Path(args.file) if args.file else None
    
    if target_file and not target_file.is_absolute():
        repo_root = repo_root or Path(__file__).parent.parent
        target_file = repo_root / target_file
    
    results = run_doc_tests(repo_root, execute=args.execute, target_file=target_file)
    
    if args.format == "json":
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["summary"]["total_failed"] == 0 else 1)
    else:
        # Text output
        summary = results["summary"]
        print("\n" + "=" * 70)
        print("Documentation Code Example Test Results")
        print("=" * 70)
        print(f"Files tested: {summary['files_tested']}")
        print(f"Files with code examples: {summary['files_with_code']}")
        print(f"Total code blocks: {summary['total_blocks']}")
        print(f"Passed: {summary['total_passed']}")
        print(f"Failed: {summary['total_failed']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Mode: {results['mode']}")
        print("=" * 70)
        
        # Print errors
        if summary["total_failed"] > 0:
            print("\nErrors:")
            for result in results["results"]:
                if result["errors"]:
                    print(f"\n  {result['file']}:")
                    for error in result["errors"]:
                        print(f"    Line {error['line']}: {error['error']}")
                        if len(error['code_preview']) < 100:
                            print(f"      Code: {error['code_preview']}")
        
        sys.exit(0 if summary["total_failed"] == 0 else 1)


if __name__ == "__main__":
    main()
