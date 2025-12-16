#!/usr/bin/env python3
"""
Dependency Drift Validation Script

Validates that dependency sources are consistent with pyproject.toml (the authoritative source).

This script ensures:
1. setup.py does not define dependencies (they should come from pyproject.toml)
2. requirements.txt (if present) matches the expected dependency set from pyproject.toml

Exit codes:
  0: All checks passed
  1: Drift detected or validation failed
"""

import ast
import sys
from pathlib import Path
from typing import Any

# Use tomllib for Python 3.11+, tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib  # type: ignore
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        print("ERROR: Need tomli package for Python < 3.11", file=sys.stderr)
        print("Install with: pip install tomli", file=sys.stderr)
        sys.exit(1)


def read_pyproject_toml(project_root: Path) -> dict[str, Any]:
    """Read and parse pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"ERROR: {pyproject_path} not found", file=sys.stderr)
        sys.exit(1)

    with pyproject_path.open("rb") as f:
        return tomllib.load(f)  # type: ignore


def get_dependencies_from_pyproject(pyproject: dict[str, Any]) -> tuple[list[str], dict[str, list[str]]]:
    """Extract dependencies and optional dependencies from pyproject.toml."""
    project = pyproject.get("project", {})
    dependencies = project.get("dependencies", [])
    optional_deps = project.get("optional-dependencies", {})
    return dependencies, optional_deps


def check_setup_py(project_root: Path) -> tuple[bool, str]:
    """
    Check that setup.py doesn't define install_requires.

    Returns:
        (is_valid, message)
    """
    setup_py_path = project_root / "setup.py"
    if not setup_py_path.exists():
        return True, "setup.py not found (OK - not required)"

    try:
        with setup_py_path.open(encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(setup_py_path))
    except Exception as e:
        return False, f"Failed to parse setup.py: {e}"

    # Check for install_requires in setup() call
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setup":
            for keyword in node.keywords:
                if keyword.arg == "install_requires":
                    # Check if it's an empty list or None (which is OK)
                    if isinstance(keyword.value, (ast.List, ast.Tuple)):
                        if len(keyword.value.elts) == 0:
                            return True, "setup.py has empty install_requires (OK)"
                    elif isinstance(keyword.value, ast.Constant) and keyword.value.value is None:
                        return True, "setup.py has None install_requires (OK)"
                    # If it has actual dependencies, that's a problem
                    return False, (
                        "setup.py defines install_requires. "
                        "Dependencies must come from pyproject.toml only. "
                        "See docs/DEPENDENCY_POLICY.md"
                    )

    return True, "setup.py does not define install_requires (OK)"


def normalize_dependency_spec(dep: str) -> str:
    """Normalize a dependency spec for comparison (remove version constraints, normalize whitespace)."""
    # Remove comments
    dep = dep.split("#")[0].strip()
    if not dep:
        return ""
    # Extract package name (before any version specifier)
    parts = dep.replace(">=", " ").replace("<=", " ").replace("==", " ").replace("!=", " ").replace(">", " ").replace("<", " ").replace("~=", " ").split()
    if parts:
        return parts[0].lower()
    return dep.lower()


def check_requirements_txt(project_root: Path, expected_deps: list[str], optional_deps: dict[str, list[str]]) -> tuple[bool, str]:
    """
    Check that requirements.txt (if present) matches pyproject.toml dependencies.

    Returns:
        (is_valid, message)
    """
    requirements_path = project_root / "requirements.txt"
    if not requirements_path.exists():
        return True, "requirements.txt not found (OK - optional convenience file)"

    # Read requirements.txt
    with requirements_path.open(encoding="utf-8") as f:
        req_lines = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

    # Build expected set (runtime + dev, as requirements.txt typically includes both)
    expected_set = {normalize_dependency_spec(dep) for dep in expected_deps}
    dev_deps = optional_deps.get("dev", [])
    expected_set.update({normalize_dependency_spec(dep) for dep in dev_deps})

    # Build actual set from requirements.txt
    actual_set = {normalize_dependency_spec(dep) for dep in req_lines}

    # Check for missing dependencies
    missing = expected_set - actual_set
    extra = actual_set - expected_set

    if missing or extra:
        msg_parts = ["requirements.txt does not match pyproject.toml:"]
        if missing:
            msg_parts.append(f"  Missing from requirements.txt: {sorted(missing)}")
        if extra:
            msg_parts.append(f"  Extra in requirements.txt: {sorted(extra)}")
        msg_parts.append("  Note: requirements.txt is a convenience file and should match pyproject.toml")
        msg_parts.append("  See docs/DEPENDENCY_POLICY.md")
        return False, "\n".join(msg_parts)

    return True, "requirements.txt matches pyproject.toml (OK)"


def main() -> int:
    """Main validation function."""
    project_root = Path(__file__).parent.parent

    print("Validating dependency consistency...")
    print(f"Project root: {project_root}")

    # Read pyproject.toml
    try:
        pyproject = read_pyproject_toml(project_root)
    except Exception as e:
        print(f"ERROR: Failed to read pyproject.toml: {e}", file=sys.stderr)
        return 1

    dependencies, optional_deps = get_dependencies_from_pyproject(pyproject)
    print(f"Found {len(dependencies)} runtime dependencies in pyproject.toml")
    print(f"Found {len(optional_deps)} optional dependency groups")

    # Check setup.py
    print("\nChecking setup.py...")
    setup_valid, setup_msg = check_setup_py(project_root)
    print(f"  {setup_msg}")
    if not setup_valid:
        print("  [FAIL] FAILED", file=sys.stderr)

    # Check requirements.txt
    print("\nChecking requirements.txt...")
    req_valid, req_msg = check_requirements_txt(project_root, dependencies, optional_deps)
    print(f"  {req_msg}")
    if not req_valid:
        print("  [FAIL] FAILED", file=sys.stderr)

    # Summary
    if setup_valid and req_valid:
        print("\n[OK] All dependency checks passed!")
        return 0
    else:
        print("\n[FAIL] Dependency drift detected!", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

