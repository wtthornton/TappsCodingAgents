"""
E2E Test Runner Script

Comprehensive E2E test runner with support for different test categories,
markers, and CI/CD-friendly options.

Usage:
    # Run all E2E tests
    python scripts/run_e2e_tests.py

    # Run smoke tests only (fast, no external services)
    python scripts/run_e2e_tests.py --smoke

    # Run specific category
    python scripts/run_e2e_tests.py --workflow
    python scripts/run_e2e_tests.py --scenario
    python scripts/run_e2e_tests.py --cli
    python scripts/run_e2e_tests.py --agents
    python scripts/run_e2e_tests.py --learning

    # Run with real services (requires LLM/Context7)
    python scripts/run_e2e_tests.py --with-llm
    python scripts/run_e2e_tests.py --with-context7

    # CI/CD mode (JSON output, exit codes)
    python scripts/run_e2e_tests.py --ci --output results.json
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent


def build_pytest_command(
    categories: list[str],
    markers: list[str],
    verbose: bool,
    ci_mode: bool,
    output_file: Path | None = None,
) -> list[str]:
    """Build pytest command with appropriate markers and options."""
    cmd = ["python", "-m", "pytest", "tests/e2e/"]
    
    # Build marker expression
    marker_parts = []
    
    if categories:
        # Convert categories to markers
        category_to_marker = {
            "smoke": "e2e_smoke",
            "workflow": "e2e_workflow",
            "scenario": "e2e_scenario",
            "cli": "e2e_cli",
            "agents": "e2e",
            "learning": "e2e_workflow",  # Learning tests use e2e_workflow marker
        }
        
        category_markers = [category_to_marker.get(cat, cat) for cat in categories]
        if len(category_markers) == 1:
            marker_parts.append(category_markers[0])
        else:
            marker_parts.append(f"({' or '.join(category_markers)})")
    
    # Add service requirement markers
    if markers:
        marker_parts.extend(markers)
    
    # Combine markers
    if marker_parts:
        marker_expr = " and ".join(marker_parts)
        cmd.extend(["-m", marker_expr])
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    if ci_mode:
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "-ra",  # Show extra test summary info
        ])
    
    # Output file handling (pytest JSON report)
    if output_file:
        cmd.extend(["--json-report", "--json-report-file", str(output_file)])
    
    return cmd


def get_test_counts(categories: list[str], markers: list[str]) -> dict[str, int]:
    """Get test counts for given categories and markers (dry run)."""
    cmd = build_pytest_command(categories, markers, verbose=False, ci_mode=False)
    cmd.extend(["--collect-only", "-q"])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=project_root,
        )
        
        # Count tests from output
        output = result.stdout + result.stderr
        test_count = output.count(" <")  # Rough count from pytest output
        
        return {"estimated_tests": test_count}
    except Exception as e:
        return {"estimated_tests": 0, "error": str(e)}


def run_tests(
    categories: list[str],
    markers: list[str],
    verbose: bool,
    ci_mode: bool,
    output_file: Path | None = None,
) -> dict[str, Any]:
    """Run E2E tests and return results."""
    cmd = build_pytest_command(categories, markers, verbose, ci_mode, output_file)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            encoding="utf-8",
            errors="replace",
        )
        
        duration = time.time() - start_time
        exit_code = result.returncode
        
        return {
            "status": "PASS" if exit_code == 0 else "FAIL",
            "exit_code": exit_code,
            "duration_seconds": round(duration, 2),
            "command": " ".join(cmd),
            "categories": categories,
            "markers": markers,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "exit_code": 1,
            "error": str(e),
            "command": " ".join(cmd),
        }


def print_summary(results: dict[str, Any]) -> None:
    """Print test execution summary."""
    print("=" * 80)
    print("E2E Test Execution Summary")
    print("=" * 80)
    print()
    
    print(f"Status: {results['status']}")
    print(f"Exit Code: {results['exit_code']}")
    
    if "duration_seconds" in results:
        print(f"Duration: {results['duration_seconds']}s")
    
    if results.get("categories"):
        print(f"Categories: {', '.join(results['categories'])}")
    
    if results.get("markers"):
        print(f"Markers: {', '.join(results['markers'])}")
    
    print()
    print(f"Command: {results.get('command', 'N/A')}")
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run E2E test suite with various options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all E2E tests
  python scripts/run_e2e_tests.py

  # Run smoke tests only (fast, < 30 seconds)
  python scripts/run_e2e_tests.py --smoke

  # Run workflow tests
  python scripts/run_e2e_tests.py --workflow

  # Run with real LLM service
  python scripts/run_e2e_tests.py --with-llm

  # CI/CD mode with JSON output
  python scripts/run_e2e_tests.py --ci --output results.json
        """,
    )
    
    # Category selection (mutually exclusive groups)
    category_group = parser.add_mutually_exclusive_group()
    category_group.add_argument(
        "--smoke",
        action="store_const",
        const=["smoke"],
        dest="categories",
        help="Run smoke tests only (fast, no external services)",
    )
    category_group.add_argument(
        "--workflow",
        action="store_const",
        const=["workflow"],
        dest="categories",
        help="Run workflow tests",
    )
    category_group.add_argument(
        "--scenario",
        action="store_const",
        const=["scenario"],
        dest="categories",
        help="Run scenario tests",
    )
    category_group.add_argument(
        "--cli",
        action="store_const",
        const=["cli"],
        dest="categories",
        help="Run CLI tests",
    )
    category_group.add_argument(
        "--agents",
        action="store_const",
        const=["agents"],
        dest="categories",
        help="Run agent behavior tests",
    )
    category_group.add_argument(
        "--learning",
        action="store_const",
        const=["learning"],
        dest="categories",
        help="Run learning system tests",
    )
    category_group.add_argument(
        "--all",
        action="store_const",
        const=["smoke", "workflow", "scenario", "cli", "agents", "learning"],
        dest="categories",
        help="Run all test categories (default)",
    )
    
    # Service requirements
    parser.add_argument(
        "--with-llm",
        action="append_const",
        const="requires_llm",
        dest="markers",
        help="Include tests that require LLM services",
    )
    parser.add_argument(
        "--with-context7",
        action="append_const",
        const="requires_context7",
        dest="markers",
        help="Include tests that require Context7",
    )
    
    # Options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD mode (strict markers, JSON report)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output JSON report file (requires pytest-json-report plugin)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing",
    )
    
    args = parser.parse_args()
    
    # Default to all categories if none specified
    categories = args.categories or ["smoke", "workflow", "scenario", "cli", "agents", "learning"]
    markers = args.markers or []
    
    # Dry run
    if args.dry_run:
        counts = get_test_counts(categories, markers)
        print("Dry Run - Would execute:")
        print(f"  Categories: {', '.join(categories)}")
        if markers:
            print(f"  Markers: {', '.join(markers)}")
        print(f"  Estimated tests: {counts.get('estimated_tests', 'unknown')}")
        print()
        cmd = build_pytest_command(categories, markers, args.verbose, args.ci, args.output)
        print(f"Command: {' '.join(cmd)}")
        return 0
    
    # Run tests
    results = run_tests(categories, markers, args.verbose, args.ci, args.output)
    
    # Print summary
    print_summary(results)
    
    # Save results if CI mode
    if args.ci and args.output:
        results_file = args.output.parent / f"{args.output.stem}_metadata.json"
        results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Results metadata saved to: {results_file}")
    
    return results["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
