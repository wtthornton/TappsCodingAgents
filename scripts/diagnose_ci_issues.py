#!/usr/bin/env python3
"""
CI/CD Diagnostic Script

This script helps diagnose issues that might cause GitHub Actions workflows to fail.
Run this locally before pushing to identify potential problems.

Windows Compatibility:
- Sets UTF-8 encoding for console output (Windows uses CP1252 by default)
- Uses ASCII-safe symbols for cross-platform compatibility
- All file I/O operations specify encoding="utf-8"
- Subprocess calls specify encoding="utf-8" with errors="replace"

Reference: Python 3.10 Documentation - Windows Encoding
https://docs.python.org/3.10/library/sys.html
"""

import os
import subprocess
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
# Windows uses CP1252 by default, which cannot handle Unicode emojis
# This setup ensures scripts work on Windows, Linux, and macOS
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        # Python 3.7+ - reconfigure stdout/stderr to UTF-8
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 - environment variable only
        pass

# Color codes for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# ASCII-safe symbols for Windows compatibility
SUCCESS_SYMBOL = "[OK]"
ERROR_SYMBOL = "[FAIL]"
WARNING_SYMBOL = "[WARN]"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    try:
        print(f"{GREEN}{SUCCESS_SYMBOL} {text}{RESET}")
    except UnicodeEncodeError:
        print(f"[OK] {text}")


def print_error(text: str) -> None:
    """Print error message."""
    try:
        print(f"{RED}{ERROR_SYMBOL} {text}{RESET}")
    except UnicodeEncodeError:
        print(f"[FAIL] {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    try:
        print(f"{YELLOW}{WARNING_SYMBOL} {text}{RESET}")
    except UnicodeEncodeError:
        print(f"[WARN] {text}")


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        # Always specify encoding for subprocess output (Windows compatibility)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Replace invalid characters instead of failing
            check=False,
            timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 300 seconds"
    except Exception as e:
        return False, str(e)


def check_python_version() -> bool:
    """Check Python version compatibility."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 12:
        print_success(f"Python {version.major}.{version.minor} is compatible")
        return True
    else:
        print_error(
            f"Python {version.major}.{version.minor} may not be compatible (need 3.12+)"
        )
        return False


def check_pytest_markers() -> bool:
    """Check pytest marker configuration."""
    print_header("Checking Pytest Markers")

    # Read pytest.ini
    pytest_ini = Path("pytest.ini")
    if not pytest_ini.exists():
        print_error("pytest.ini not found")
        return False

    # Always specify encoding for file I/O (Windows compatibility)
    content = pytest_ini.read_text(encoding="utf-8")

    # Check for required markers
    required_markers = [
        "requires_llm",
        "requires_context7",
        "unit",
        "integration",
        "e2e",
        "e2e_smoke",
        "e2e_workflow",
        "e2e_scenario",
        "e2e_cli",
    ]

    missing = []
    for marker in required_markers:
        if marker not in content:
            missing.append(marker)

    if missing:
        print_error(f"Missing markers in pytest.ini: {', '.join(missing)}")
        return False
    else:
        print_success("All required markers found in pytest.ini")
        return True


def check_linting() -> bool:
    """Check linting."""
    print_header("Checking Linting (Ruff)")

    success, output = run_command(["ruff", "check", "."], "Ruff linting")

    if success:
        print_success("Linting passed")
        return True
    else:
        print_error("Linting failed")
        print(output[:500])  # Print first 500 chars
        return False


def check_formatting() -> bool:
    """Check code formatting."""
    print_header("Checking Code Formatting (Ruff)")

    success, output = run_command(
        ["ruff", "format", "--check", "."], "Ruff format check"
    )

    if success:
        print_success("Formatting check passed")
        return True
    else:
        print_error("Formatting check failed")
        print(output[:500])
        return False


def check_type_checking() -> bool:
    """Check type checking."""
    print_header("Checking Type Checking (Mypy)")

    success, output = run_command(
        [
            "python",
            "-m",
            "mypy",
            "tapps_agents/core",
            "tapps_agents/workflow",
            "tapps_agents/context7",
        ],
        "Mypy type checking",
    )

    if success:
        print_success("Type checking passed")
        return True
    else:
        print_error("Type checking failed")
        print(output[:1000])  # Print first 1000 chars
        return False


def check_dependency_validation() -> bool:
    """Check dependency validation."""
    print_header("Checking Dependency Validation")

    script = Path("scripts/validate_dependencies.py")
    if not script.exists():
        print_error("validate_dependencies.py not found")
        return False

    success, output = run_command(["python", str(script)], "Dependency validation")

    if success:
        print_success("Dependency validation passed")
        return True
    else:
        print_error("Dependency validation failed")
        print(output)
        return False


def check_test_markers() -> bool:
    """Check that test marker expressions work."""
    print_header("Checking Test Marker Expressions")

    marker_expressions = [
        "unit or e2e_smoke",
        "unit or integration or e2e_workflow",
        "e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)",
    ]

    all_passed = True
    for expr in marker_expressions:
        success, output = run_command(
            ["pytest", "-m", expr, "--collect-only", "-q"], f"Marker expression: {expr}"
        )

        if success:
            print_success(f"Marker expression '{expr}' works")
        else:
            print_error(f"Marker expression '{expr}' failed")
            print(output[:300])
            all_passed = False

    return all_passed


def check_test_coverage() -> bool:
    """Check test coverage."""
    print_header("Checking Test Coverage")

    success, output = run_command(
        [
            "pytest",
            "tests/",
            "--cov=tapps_agents",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "-q",
        ],
        "Test coverage",
    )

    if success:
        # Try to extract coverage percentage
        if "TOTAL" in output:
            lines = output.split("\n")
            for line in lines:
                if "TOTAL" in line:
                    print(f"Coverage report:\n{line}")
                    break

        print_success("Tests passed")
        return True
    else:
        print_error("Tests failed or coverage below threshold")
        print(output[:1000])
        return False


def check_workflow_files() -> bool:
    """Check workflow files exist and are valid YAML."""
    print_header("Checking Workflow Files")

    workflows = [
        ".github/workflows/ci.yml",
        ".github/workflows/e2e.yml",
        ".github/workflows/release.yml",
    ]

    all_valid = True
    for workflow in workflows:
        path = Path(workflow)
        if not path.exists():
            print_error(f"Workflow file not found: {workflow}")
            all_valid = False
        else:
            # Basic YAML check (try to parse)
            try:
                import yaml

                # Always specify encoding for file I/O (Windows compatibility)
                with path.open(encoding="utf-8") as f:
                    yaml.safe_load(f)
                print_success(f"Workflow file valid: {workflow}")
            except Exception as e:
                print_error(f"Workflow file invalid: {workflow} - {e}")
                all_valid = False

    return all_valid


def main() -> int:
    """Run all diagnostic checks."""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}GitHub Actions CI/CD Diagnostic Tool{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    checks = [
        ("Python Version", check_python_version),
        ("Pytest Markers", check_pytest_markers),
        ("Workflow Files", check_workflow_files),
        ("Dependency Validation", check_dependency_validation),
        ("Linting", check_linting),
        ("Formatting", check_formatting),
        ("Type Checking", check_type_checking),
        ("Test Markers", check_test_markers),
        ("Test Coverage", check_test_coverage),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} check failed with exception: {e}")
            results.append((name, False))

    # Summary
    print_header("Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print(f"\n{BLUE}Results: {passed}/{total} checks passed{RESET}\n")

    if passed == total:
        print_success("All checks passed! Ready for CI/CD.")
        return 0
    else:
        print_error(f"{total - passed} check(s) failed. Fix issues before pushing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
