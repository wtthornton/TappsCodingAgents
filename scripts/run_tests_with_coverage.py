#!/usr/bin/env python3
"""
Test runner with live terminal feedback and code coverage.

This script provides:
- Real-time test progress with colored output
- Live coverage updates during test execution
- Summary reports (terminal, HTML, JSON)
- Parallel execution support
- Configurable verbosity and output formats

Usage:
    python scripts/run_tests_with_coverage.py
    python scripts/run_tests_with_coverage.py --unit
    python scripts/run_tests_with_coverage.py --all --html
    python scripts/run_tests_with_coverage.py --file tests/unit/test_config.py
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(message: str, color: str = Colors.ENDC) -> None:
    """Print colored message."""
    try:
        print(f"{color}{message}{Colors.ENDC}")
    except UnicodeEncodeError:
        # Fallback for Windows terminals that don't support Unicode
        # Remove Unicode characters and print plain text
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(f"{color}{safe_message}{Colors.ENDC}")


def run_tests(
    test_path: str = "tests",
    markers: str | None = None,
    coverage: bool = True,
    parallel: bool = True,
    html_report: bool = False,
    json_report: bool = False,
    verbose: bool = True,
    fail_under: float | None = None,
    specific_file: str | None = None,
    show_progress: bool = True,
) -> int:
    """
    Run tests with coverage and live terminal feedback.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Test path
    if specific_file:
        cmd.append(specific_file)
    else:
        cmd.append(test_path)
    
    # Markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Coverage options
    if coverage:
        cmd.extend(["--cov=tapps_agents", "--cov-report=term"])
        
        # Additional coverage reports
        if html_report:
            cmd.append("--cov-report=html")
        if json_report:
            cmd.append("--cov-report=json")
        
        # Fail under threshold
        if fail_under is not None:
            cmd.extend(["--cov-fail-under", str(fail_under)])
    
    # Progress indicator (pytest-sugar provides better output)
    if show_progress:
        # pytest-sugar adds colored output and progress indicators automatically
        # Just ensure we have good verbosity
        pass
    
    # Print command
    print_colored("=" * 80, Colors.HEADER)
    print_colored("Running Tests with Coverage", Colors.BOLD + Colors.HEADER)
    print_colored("=" * 80, Colors.HEADER)
    print()
    print_colored("Command:", Colors.OKCYAN)
    print(f"  {' '.join(cmd)}")
    print()
    
    # Record start time
    start_time = time.time()
    
    # Run tests
    try:
        print_colored("Starting test execution...", Colors.OKBLUE)
        print()
        
        # Run pytest with real-time output streaming
        # Don't capture stdout/stderr - let pytest print directly to terminal
        # This ensures immediate, unbuffered output especially with pytest-xdist
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered Python output for immediate output
        
        result = subprocess.run(
            cmd,
            cwd=Path.cwd(),
            env=env,
            stdout=None,  # Don't capture - print directly to terminal
            stderr=None,  # Don't capture - print directly to terminal
            check=False,  # Don't raise on failure, we'll handle it
        )
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        
        # Print summary
        print()
        print_colored("=" * 80, Colors.HEADER)
        print_colored("Test Execution Summary", Colors.BOLD + Colors.HEADER)
        print_colored("=" * 80, Colors.HEADER)
        print()
        print_colored(f"Elapsed time: {elapsed:.2f} seconds", Colors.OKCYAN)
        print()
        
        if result.returncode == 0:
            print_colored("[PASS] All tests passed!", Colors.OKGREEN)
        else:
            print_colored(f"[FAIL] Tests failed with exit code {result.returncode}", Colors.FAIL)
        
        # Coverage report locations
        if coverage:
            print()
            print_colored("Coverage Reports:", Colors.OKCYAN)
            if html_report:
                html_path = Path("htmlcov/index.html")
                if html_path.exists():
                    print_colored(f"  [HTML] Report: {html_path.absolute()}", Colors.OKGREEN)
                    print_colored("         Open with: start htmlcov/index.html", Colors.OKBLUE)
            if json_report:
                json_path = Path("coverage.json")
                if json_path.exists():
                    print_colored(f"  [JSON] Report: {json_path.absolute()}", Colors.OKGREEN)
            print_colored("  [TERM] Terminal Report: (shown above)", Colors.OKGREEN)
        
        print()
        print_colored("=" * 80, Colors.HEADER)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print()
        print_colored("\n[WARN] Test execution interrupted by user", Colors.WARNING)
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print_colored(f"\n[ERROR] Error running tests: {e}", Colors.FAIL)
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests with coverage and live terminal feedback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run unit tests with coverage (default)
  python scripts/run_tests_with_coverage.py

  # Run all tests with HTML report
  python scripts/run_tests_with_coverage.py --all --html

  # Run specific test file
  python scripts/run_tests_with_coverage.py --file tests/unit/test_config.py

  # Run without coverage (faster)
  python scripts/run_tests_with_coverage.py --no-coverage

  # Run sequentially (for debugging)
  python scripts/run_tests_with_coverage.py --no-parallel
        """,
    )
    
    # Test selection
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests (default)",
    )
    test_group.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests",
    )
    test_group.add_argument(
        "--e2e",
        action="store_true",
        help="Run only E2E tests",
    )
    test_group.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (unit + integration + e2e)",
    )
    test_group.add_argument(
        "--file",
        type=str,
        metavar="PATH",
        help="Run specific test file",
    )
    
    # Coverage options
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable code coverage (faster execution)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Generate JSON coverage report",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        metavar="PERCENT",
        help="Fail if coverage is below this percentage (default: 75)",
    )
    
    # Execution options
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Run tests sequentially (slower, but better for debugging)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity",
    )
    
    # Path options
    parser.add_argument(
        "--test-path",
        type=str,
        default="tests",
        help="Test directory path (default: tests)",
    )
    
    args = parser.parse_args()
    
    # Determine markers
    markers = None
    if args.unit:
        markers = "unit"
    elif args.integration:
        markers = "integration"
    elif args.e2e:
        markers = "e2e"
    elif args.all:
        markers = ""  # Empty string means all tests
    
    # Determine test path
    test_path = args.test_path
    specific_file = args.file if args.file else None
    
    # Run tests
    return run_tests(
        test_path=test_path,
        markers=markers,
        coverage=not args.no_coverage,
        parallel=not args.no_parallel,
        html_report=args.html,
        json_report=args.json,
        verbose=not args.quiet,
        fail_under=args.fail_under or (75.0 if not args.no_coverage else None),
        specific_file=specific_file,
        show_progress=True,
    )


if __name__ == "__main__":
    sys.exit(main())

