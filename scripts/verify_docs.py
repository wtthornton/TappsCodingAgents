#!/usr/bin/env python3
"""
Documentation Verification Script

Validates that referenced files/paths exist and internal Markdown links are valid.
This helps prevent documentation drift and broken references.

Usage:
    python scripts/verify_docs.py
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urlparse


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
        # Only include files in docs/, root, or implementation/ directories
        if any(part in path_str for part in ["/docs/", "\\docs\\", "/implementation/", "\\implementation\\"]) or md_file.parent == root:
            markdown_files.append(md_file)
    
    return sorted(markdown_files)


def extract_markdown_links(content: str, file_path: Path) -> List[Tuple[str, str, int]]:
    """
    Extract Markdown links from content.
    
    Returns:
        List of (link_text, link_target, line_number) tuples
    """
    links = []
    lines = content.splitlines()
    
    # Pattern for markdown links: [text](target) or [text](target "title")
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    for line_num, line in enumerate(lines, start=1):
        for match in link_pattern.finditer(line):
            link_text = match.group(1)
            link_target = match.group(2).split()[0]  # Remove title if present
            links.append((link_text, link_target, line_num))
    
    return links


def extract_file_references(content: str, file_path: Path) -> List[Tuple[str, int]]:
    """
    Extract file/path references from content.
    
    Looks for:
    - Backtick-wrapped paths (e.g., `docs/README.md`)
    - Relative paths in code blocks
    - File references in text
    
    Returns:
        List of (reference, line_number) tuples
    """
    references = []
    lines = content.splitlines()
    
    # Pattern for backtick-wrapped paths
    backtick_pattern = re.compile(r'`([^`]+)`')
    
    # Pattern for relative paths (starts with ./ or ../ or just a path without http/https)
    path_pattern = re.compile(r'([a-zA-Z0-9_\-./]+\.(md|yaml|yml|py|txt|toml|json|mdc))')
    
    for line_num, line in enumerate(lines, start=1):
        # Skip code blocks (between ```)
        if line.strip().startswith("```"):
            continue
        
        # Find backtick-wrapped references
        for match in backtick_pattern.finditer(line):
            ref = match.group(1)
            # Check if it looks like a file path
            if "/" in ref or ref.endswith((".md", ".yaml", ".yml", ".py", ".txt", ".toml", ".json", ".mdc")):
                if not ref.startswith(("http://", "https://", "mailto:")):
                    references.append((ref, line_num))
        
        # Find path-like references (but be conservative)
        for match in path_pattern.finditer(line):
            ref = match.group(1)
            # Only include if it looks like a relative path reference
            if not ref.startswith(("http://", "https://", "mailto:")) and "/" in ref:
                # Skip if it's part of a URL or email
                if "@" not in ref and "://" not in ref:
                    references.append((ref, line_num))
    
    return references


def resolve_link_target(target: str, source_file: Path, repo_root: Path) -> Tuple[Path, str]:
    """
    Resolve a link target to an actual file path.
    
    Returns:
        (resolved_path, anchor) tuple
    """
    # Remove anchor if present
    if "#" in target:
        target, anchor = target.split("#", 1)
    else:
        anchor = ""
    
    # Handle external URLs
    parsed = urlparse(target)
    if parsed.scheme in ("http", "https", "mailto"):
        return None, ""  # External link, skip validation
    
    # Handle absolute paths (from repo root)
    if target.startswith("/"):
        target = target[1:]
        resolved = repo_root / target
    else:
        # Relative path from source file
        resolved = (source_file.parent / target).resolve()
    
    return resolved, anchor


def check_file_exists(file_path: Path, repo_root: Path) -> bool:
    """Check if a file exists relative to the repo root."""
    try:
        # Ensure path is within repo
        resolved = file_path.resolve()
        repo_resolved = repo_root.resolve()
        
        if not str(resolved).startswith(str(repo_resolved)):
            return False  # Outside repo
        
        return resolved.exists()
    except Exception:
        return False


def verify_documentation(repo_root: Path = None) -> Tuple[int, List[str]]:
    """
    Verify documentation files for broken links and references.
    
    Returns:
        (error_count, error_messages) tuple
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    
    errors = []
    markdown_files = find_markdown_files(repo_root)
    
    # Exclude generated HTML docs
    markdown_files = [f for f in markdown_files if "docs/html" not in str(f)]
    
    print(f"Checking {len(markdown_files)} Markdown files...")
    
    for md_file in markdown_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"{md_file}: Failed to read file: {e}")
            continue
        
        # Check links
        links = extract_markdown_links(content, md_file)
        for link_text, link_target, line_num in links:
            resolved, anchor = resolve_link_target(link_target, md_file, repo_root)
            
            if resolved is None:
                continue  # External link, skip
            
            if not check_file_exists(resolved, repo_root):
                errors.append(
                    f"{md_file}:{line_num}: Broken link '{link_text}' -> '{link_target}' "
                    f"(resolved to: {resolved})"
                )
        
        # Check file references (more conservative)
        references = extract_file_references(content, md_file)
        for ref, line_num in references:
            # Only check if it looks like a relative path reference
            if ref.startswith(("./", "../")) or ("/" in ref and not ref.startswith("http")):
                resolved = (md_file.parent / ref).resolve()
                
                # Only report if it's clearly a file reference and doesn't exist
                if resolved.suffix in (".md", ".yaml", ".yml", ".py", ".txt", ".toml", ".json", ".mdc"):
                    if not check_file_exists(resolved, repo_root):
                        # Check if it might be a code reference (like `file.py:123`)
                        if ":" in ref:
                            file_part = ref.split(":")[0]
                            resolved = (md_file.parent / file_part).resolve()
                            if not check_file_exists(resolved, repo_root):
                                errors.append(
                                    f"{md_file}:{line_num}: Possible broken file reference: `{ref}` "
                                    f"(resolved to: {resolved})"
                                )
                        else:
                            errors.append(
                                f"{md_file}:{line_num}: Possible broken file reference: `{ref}` "
                                f"(resolved to: {resolved})"
                            )
    
    return len(errors), errors


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("Documentation Verification")
    print("=" * 60)
    print()
    
    error_count, errors = verify_documentation(repo_root)
    
    if error_count == 0:
        print("[OK] All documentation checks passed!")
        return 0
    else:
        print(f"[ERROR] Found {error_count} documentation issue(s):\n")
        for error in errors:
            print(f"  {error}")
        print()
        print("Note: Some references may be false positives (external URLs, code examples, etc.)")
        print("Review each error and fix or add to exclusion list if needed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

