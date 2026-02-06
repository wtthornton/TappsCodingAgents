#!/usr/bin/env python3
"""
Validate that root directory follows project structure standards.
Run this in CI/CD or as a pre-commit hook.
"""

import sys
from pathlib import Path

# Allowed files in root
ALLOWED_ROOT_FILES = {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "requirements.txt",
    "pytest.ini",
    "MANIFEST.in",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".cursorignore",
    ".github",  # Directory
}

# Patterns that should NOT be in root (move to docs/archive or docs/releases)
FORBIDDEN_PATTERNS = [
    "test_*.py",  # Test files
    "*-report.md",  # Report files
    "*-summary.md",  # Summary files
    "*-analysis.md",  # Analysis files
    "debug-*.md",  # Debug files
    "*CLEANUP*.md",  # Cleanup summaries -> docs/archive/
    "RELEASE_NOTES*.md",  # Release notes -> docs/releases/
]


def validate_root_structure(project_root: Path) -> tuple[bool, list[str]]:
    """Validate root directory structure."""
    errors = []
    warnings = []
    
    root_files = {f.name for f in project_root.iterdir() if f.is_file()}
    {f.name for f in project_root.iterdir() if f.is_dir()}
    
    # Check for test files
    test_files = [f for f in root_files if f.startswith("test_") and f.endswith(".py")]
    if test_files:
        errors.append(f"Test files in root (move to tests/): {', '.join(test_files)}")
    
    # Check for forbidden markdown patterns
    for pattern in FORBIDDEN_PATTERNS:
        pattern_base = pattern.replace("*", "").replace(".py", "").replace(".md", "")
        matching = [f for f in root_files if pattern_base in f and (f.endswith(".md") or f.endswith(".py"))]
        if matching:
            warnings.append(f"Files matching '{pattern}' in root: {', '.join(matching)}")
    
    # Check for Python scripts in root
    python_scripts = [f for f in root_files if f.endswith(".py")]
    if python_scripts:
        warnings.append(f"Python scripts in root (consider moving to scripts/): {', '.join(python_scripts)}")
    
    # Check for PowerShell scripts
    ps_scripts = [f for f in root_files if f.endswith(".ps1")]
    if ps_scripts:
        warnings.append(f"PowerShell scripts in root (consider moving to scripts/): {', '.join(ps_scripts)}")
    
    return len(errors) == 0, errors + warnings


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    is_valid, messages = validate_root_structure(project_root)
    
    if messages:
        for msg in messages:
            if "ERROR" in msg or "error" in msg.lower() or "Test files" in msg:
                print(f"[ERROR] {msg}", file=sys.stderr)
            else:
                print(f"[WARNING] {msg}", file=sys.stderr)
    
    if not is_valid:
        print("\n[ERROR] Root directory structure validation failed!", file=sys.stderr)
        sys.exit(1)
    elif messages:
        print("\n[WARNING] Root directory structure has warnings (see above)", file=sys.stderr)
        sys.exit(0)
    else:
        print("[OK] Root directory structure is valid!", file=sys.stdout)
        sys.exit(0)

