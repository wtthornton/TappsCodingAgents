#!/usr/bin/env python3
"""
Validation script for Windows path handling.

Tests path normalization utilities to ensure they work correctly on Windows
and other platforms. Can be run manually or in CI/CD pipelines.

Usage:
    python scripts/validate_path_handling.py
    python scripts/validate_path_handling.py --verbose
    python scripts/validate_path_handling.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.core.path_normalizer import (
    ensure_relative_path,
    normalize_for_cli,
    normalize_path,
    normalize_project_root,
)


def test_normalize_path(project_root: Path, verbose: bool = False) -> dict[str, any]:
    """Test normalize_path function."""
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Test 1: Relative path unchanged
    try:
        result = normalize_path("src/file.py", project_root)
        assert result == "src/file.py", f"Expected 'src/file.py', got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Relative path unchanged", "status": "PASS"})
        if verbose:
            print("✓ Relative path unchanged")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Relative path unchanged", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Relative path unchanged: {e}")
    
    # Test 2: Absolute path within project
    try:
        test_file = project_root / "src" / "test_file.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()
        
        absolute_path = str(test_file.resolve())
        result = normalize_path(absolute_path, project_root)
        
        assert "src" in result and "test_file.py" in result, f"Expected relative path, got '{result}'"
        assert not Path(result).is_absolute(), f"Result should be relative, got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Absolute path within project", "status": "PASS"})
        if verbose:
            print(f"✓ Absolute path within project: {absolute_path} → {result}")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Absolute path within project", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Absolute path within project: {e}")
    
    # Test 3: Empty path
    try:
        result = normalize_path("", project_root)
        assert result == "", f"Expected empty string, got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Empty path handling", "status": "PASS"})
        if verbose:
            print("✓ Empty path handling")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Empty path handling", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Empty path handling: {e}")
    
    return results


def test_normalize_for_cli(project_root: Path, verbose: bool = False) -> dict[str, any]:
    """Test normalize_for_cli function."""
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Test 1: Relative path
    try:
        result = normalize_for_cli("src/file.py", project_root)
        assert result == "src/file.py", f"Expected 'src/file.py', got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Normalize for CLI - relative path", "status": "PASS"})
        if verbose:
            print("✓ Normalize for CLI - relative path")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Normalize for CLI - relative path", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Normalize for CLI - relative path: {e}")
    
    # Test 2: Absolute path
    try:
        test_file = project_root / "src" / "cli_test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()
        
        absolute_path = str(test_file.resolve())
        result = normalize_for_cli(absolute_path, project_root)
        
        assert "src" in result and "cli_test.py" in result, f"Expected relative path, got '{result}'"
        # On Windows, should use forward slashes
        if sys.platform == "win32":
            assert "\\" not in result or result == absolute_path.replace("\\", "/"), "Should use forward slashes"
        results["passed"] += 1
        results["tests"].append({"name": "Normalize for CLI - absolute path", "status": "PASS"})
        if verbose:
            print(f"✓ Normalize for CLI - absolute path: {absolute_path} → {result}")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Normalize for CLI - absolute path", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Normalize for CLI - absolute path: {e}")
    
    return results


def test_normalize_project_root(verbose: bool = False) -> dict[str, any]:
    """Test normalize_project_root function."""
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Test 1: Absolute path
    try:
        test_root = Path.cwd().resolve()
        result = normalize_project_root(test_root)
        assert result.is_absolute(), f"Result should be absolute, got '{result}'"
        assert result.resolve() == test_root.resolve(), f"Result should match input, got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Normalize project root - absolute path", "status": "PASS"})
        if verbose:
            print(f"✓ Normalize project root - absolute path: {test_root} → {result}")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Normalize project root - absolute path", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Normalize project root - absolute path: {e}")
    
    # Test 2: Relative path
    try:
        result = normalize_project_root(".")
        assert result.is_absolute(), f"Result should be absolute, got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Normalize project root - relative path", "status": "PASS"})
        if verbose:
            print(f"✓ Normalize project root - relative path: . → {result}")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Normalize project root - relative path", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Normalize project root - relative path: {e}")
    
    return results


def test_ensure_relative_path(project_root: Path, verbose: bool = False) -> dict[str, any]:
    """Test ensure_relative_path function."""
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Test 1: Valid relative path
    try:
        result = ensure_relative_path("src/file.py", project_root)
        assert result == "src/file.py", f"Expected 'src/file.py', got '{result}'"
        results["passed"] += 1
        results["tests"].append({"name": "Ensure relative path - valid", "status": "PASS"})
        if verbose:
            print("✓ Ensure relative path - valid")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Ensure relative path - valid", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Ensure relative path - valid: {e}")
    
    # Test 2: Path outside project root (should raise ValueError)
    try:
        outside_path = project_root.parent / "outside" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()
        
        absolute_path = str(outside_path.resolve())
        try:
            ensure_relative_path(absolute_path, project_root)
            # Should not reach here
            results["failed"] += 1
            results["tests"].append({"name": "Ensure relative path - outside project", "status": "FAIL", "error": "Should have raised ValueError"})
            if verbose:
                print("✗ Ensure relative path - outside project: Should have raised ValueError")
        except ValueError:
            # Expected behavior
            results["passed"] += 1
            results["tests"].append({"name": "Ensure relative path - outside project", "status": "PASS"})
            if verbose:
                print("✓ Ensure relative path - outside project: Correctly raised ValueError")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Ensure relative path - outside project", "status": "FAIL", "error": str(e)})
        if verbose:
            print(f"✗ Ensure relative path - outside project: {e}")
    
    return results


def main():
    """Run path handling validation tests."""
    parser = argparse.ArgumentParser(description="Validate path handling on Windows and other platforms")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()
    
    project_root = Path.cwd().resolve()
    
    if args.verbose:
        print("=" * 70)
        print("Path Handling Validation")
        print("=" * 70)
        print(f"Project root: {project_root}")
        print(f"Platform: {sys.platform}")
        print()
    
    # Run all tests
    all_results = {
        "platform": sys.platform,
        "project_root": str(project_root),
        "tests": {
            "normalize_path": test_normalize_path(project_root, args.verbose),
            "normalize_for_cli": test_normalize_for_cli(project_root, args.verbose),
            "normalize_project_root": test_normalize_project_root(args.verbose),
            "ensure_relative_path": test_ensure_relative_path(project_root, args.verbose),
        }
    }
    
    # Calculate totals
    total_passed = sum(r["passed"] for r in all_results["tests"].values())
    total_failed = sum(r["failed"] for r in all_results["tests"].values())
    total_tests = total_passed + total_failed
    
    all_results["summary"] = {
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
    }
    
    # Output results
    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        if args.verbose:
            print()
            print("=" * 70)
        print("Summary:")
        print(f"  Total tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Success rate: {all_results['summary']['success_rate']:.1f}%")
        
        if total_failed > 0:
            print("\nFailed tests:")
            for test_group, results in all_results["tests"].items():
                for test in results["tests"]:
                    if test["status"] == "FAIL":
                        print(f"  - {test_group}.{test['name']}: {test.get('error', 'Unknown error')}")
    
    # Exit with appropriate code
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
