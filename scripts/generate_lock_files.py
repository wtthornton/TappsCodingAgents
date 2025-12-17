#!/usr/bin/env python3
"""
Generate lock files for reproducible builds.

This script generates pinned dependency lock files from pyproject.toml using pip-tools.
Lock files ensure reproducible builds by pinning exact versions of all dependencies
and their transitive dependencies.

Usage:
    python scripts/generate_lock_files.py

This will generate:
    - requirements-lock.txt (runtime dependencies)
    - requirements-dev-lock.txt (runtime + dev dependencies)

Lock files should be committed to version control for reproducibility.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n{description}...")
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(
            f"ERROR: pip-compile not found. Install with: pip install pip-tools",
            file=sys.stderr,
        )
        return False


def main() -> int:
    """Generate lock files from pyproject.toml."""
    project_root = Path(__file__).parent.parent
    pyproject_toml = project_root / "pyproject.toml"

    if not pyproject_toml.exists():
        print(f"ERROR: {pyproject_toml} not found", file=sys.stderr)
        return 1

    print("Generating lock files from pyproject.toml...")
    print(f"Project root: {project_root}")

    # Generate runtime lock file
    runtime_lock = project_root / "requirements-lock.txt"
    runtime_success = run_command(
        [
            "pip-compile",
            "--output-file",
            str(runtime_lock),
            "--resolver",
            "backtracking",
            str(pyproject_toml),
        ],
        f"Generating {runtime_lock.name} (runtime dependencies)",
    )

    # Generate dev lock file (runtime + dev)
    dev_lock = project_root / "requirements-dev-lock.txt"
    dev_success = run_command(
        [
            "pip-compile",
            "--output-file",
            str(dev_lock),
            "--resolver",
            "backtracking",
            "--extra",
            "dev",
            str(pyproject_toml),
        ],
        f"Generating {dev_lock.name} (runtime + dev dependencies)",
    )

    if runtime_success and dev_success:
        print("\n[OK] Lock files generated successfully!")
        print(f"\nGenerated files:")
        print(f"  - {runtime_lock.name} (runtime dependencies)")
        print(f"  - {dev_lock.name} (runtime + dev dependencies)")
        print("\nNote: Lock files should be committed to version control for reproducibility.")
        return 0
    else:
        print("\n[FAIL] Failed to generate lock files!", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

