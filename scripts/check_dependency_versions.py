#!/usr/bin/env python3
"""
Check Dependency Versions Script

Compares current dependency versions in pyproject.toml against latest stable
versions available on PyPI. Provides a report of packages that need upgrading.
"""

import re
import subprocess
import sys

# Use tomllib for Python 3.11+, tomli for older versions
import tomllib
from pathlib import Path
from typing import Any


def get_latest_version(package: str) -> tuple[str | None, str | None]:
    """
    Get the latest version of a package from PyPI.
    Returns (latest_version, error_message)
    """
    try:
        result = subprocess.run(
            ["pip", "index", "versions", package],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        
        if result.returncode != 0:
            return None, result.stderr.strip()
        
        # Parse output: "package (current_version)\nAvailable versions: ..."
        # First line contains the current/latest version
        lines = result.stdout.strip().split("\n")
        if not lines:
            return None, "No output from pip index"
        
        # Extract version from first line: "package (version)"
        match = re.search(r"\(([\d.]+(?:[a-z0-9]+)?)\)", lines[0])
        if match:
            return match.group(1), None
        
        # Try to parse from "Available versions: x.y.z, ..."
        if "Available versions:" in result.stdout:
            versions_line = [l for l in lines if "Available versions:" in l]
            if versions_line:
                versions_text = versions_line[0].split("Available versions:")[-1].strip()
                # First version is usually the latest
                versions = [v.strip() for v in versions_text.split(",")]
                if versions:
                    return versions[0], None
        
        return None, "Could not parse version from pip output"
    
    except subprocess.TimeoutExpired:
        return None, "Timeout checking PyPI"
    except Exception as e:
        return None, str(e)


def parse_version_spec(spec: str) -> tuple[str, str]:
    """
    Parse a version spec like ">=2.12.0" or ">=0.14.10,<1.0"
    Returns (package_name, version_spec)
    """
    # Remove whitespace and split package name from version
    spec = spec.strip()
    
    # Handle operators: >=, <=, <, >, ==, ~=, !=
    match = re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)\s*([>=<!~=].*)?$", spec)
    if match:
        package = match.group(1)
        version = match.group(2) if match.group(2) else ""
        # Clean up version spec (remove brackets from extras)
        package = package.split("[")[0]
        return package.strip(), version.strip()
    
    # Fallback: treat as package name only
    return spec, ""


def extract_min_version(version_spec: str) -> str | None:
    """
    Extract the minimum version from a version spec.
    For ">=2.12.0", returns "2.12.0"
    For ">=0.14.10,<1.0", returns "0.14.10"
    """
    if not version_spec:
        return None
    
    # Find first >= or == operator
    match = re.search(r"(?:>=|==)\s*([\d.]+(?:[a-z0-9]+)?)", version_spec)
    if match:
        return match.group(1)
    
    return None


def read_pyproject_toml(project_root: Path) -> dict[str, Any]:
    """Read and parse pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"ERROR: {pyproject_path} not found", file=sys.stderr)
        sys.exit(1)
    
    with pyproject_path.open("rb") as f:
        return tomllib.load(f)  # type: ignore


def compare_versions(current: str, latest: str) -> tuple[bool, str]:
    """
    Compare two version strings.
    Returns (needs_upgrade, reason)
    """
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        
        # Pad to same length
        max_len = max(len(current_parts), len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))
        
        for c, l in zip(current_parts, latest_parts, strict=False):
            if l > c:
                return True, "Newer version available"
            elif c > l:
                return False, "Current is newer (unlikely, check manually)"
        
        return False, "Versions match"
    
    except ValueError:
        # Handle pre-release versions, etc.
        if latest > current:
            return True, "Newer version available (contains non-numeric parts)"
        return False, "Could not compare (contains non-numeric parts)"


def main() -> int:
    """Main function."""
    project_root = Path(__file__).parent.parent
    
    print("Checking dependency versions against PyPI...")
    print(f"Project root: {project_root}\n")
    
    # Read pyproject.toml
    try:
        pyproject = read_pyproject_toml(project_root)
    except Exception as e:
        print(f"ERROR: Failed to read pyproject.toml: {e}", file=sys.stderr)
        return 1
    
    # Collect all dependencies
    dependencies: list[tuple[str, str, str]] = []  # (package, version_spec, category)
    
    # Runtime dependencies
    if "project" in pyproject and "dependencies" in pyproject["project"]:
        for dep in pyproject["project"]["dependencies"]:
            pkg, spec = parse_version_spec(dep)
            dependencies.append((pkg, spec, "runtime"))
    
    # Dev dependencies
    if "project" in pyproject and "optional-dependencies" in pyproject["project"]:
        for group, deps in pyproject["project"]["optional-dependencies"].items():
            for dep in deps:
                pkg, spec = parse_version_spec(dep)
                dependencies.append((pkg, spec, f"dev[{group}]"))
    
    print(f"Found {len(dependencies)} dependencies to check\n")
    
    # Check each dependency
    upgrade_needed: list[dict[str, Any]] = []
    up_to_date: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    
    for package, version_spec, category in dependencies:
        print(f"Checking {package}...", end=" ", flush=True)
        
        latest_version, error = get_latest_version(package)
        
        if error:
            print(f"[ERROR: {error}]")
            errors.append({
                "package": package,
                "category": category,
                "error": error,
            })
            continue
        
        if not latest_version:
            print("[ERROR: No version found]")
            errors.append({
                "package": package,
                "category": category,
                "error": "No version found",
            })
            continue
        
        current_min = extract_min_version(version_spec)
        
        if current_min:
            needs_upgrade, reason = compare_versions(current_min, latest_version)
            
            if needs_upgrade:
                print(f"[UPGRADE NEEDED: {current_min} -> {latest_version}]")
                upgrade_needed.append({
                    "package": package,
                    "category": category,
                    "current_min": current_min,
                    "latest": latest_version,
                    "version_spec": version_spec,
                })
            else:
                print(f"[OK: {latest_version}]")
                up_to_date.append({
                    "package": package,
                    "category": category,
                    "version": latest_version,
                })
        else:
            print(f"[INFO: Latest is {latest_version}, no minimum specified]")
            up_to_date.append({
                "package": package,
                "category": category,
                "version": latest_version,
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total dependencies checked: {len(dependencies)}")
    print(f"Up to date: {len(up_to_date)}")
    print(f"Upgrade needed: {len(upgrade_needed)}")
    print(f"Errors: {len(errors)}")
    
    if upgrade_needed:
        print("\n" + "=" * 80)
        print("PACKAGES NEEDING UPGRADE")
        print("=" * 80)
        print(f"{'Package':<30} {'Category':<20} {'Current Min':<15} {'Latest':<15} {'Priority'}")
        print("-" * 95)
        
        # Sort by priority (runtime first, then by version gap)
        upgrade_needed.sort(key=lambda x: (
            0 if x["category"] == "runtime" else 1,
            x["package"],
        ))
        
        for item in upgrade_needed:
            # Determine priority based on version gap
            current_parts = [int(x) for x in item["current_min"].split(".")]
            latest_parts = [int(x) for x in item["latest"].split(".")]
            major_gap = latest_parts[0] - current_parts[0] if len(latest_parts) > 0 and len(current_parts) > 0 else 0
            
            if major_gap > 0:
                priority = "HIGH (major version)"
            elif latest_parts[1] - current_parts[1] > 2 if len(latest_parts) > 1 and len(current_parts) > 1 else False:
                priority = "MEDIUM (minor version)"
            else:
                priority = "LOW (patch version)"
            
            print(f"{item['package']:<30} {item['category']:<20} {item['current_min']:<15} {item['latest']:<15} {priority}")
    
    if errors:
        print("\n" + "=" * 80)
        print("ERRORS")
        print("=" * 80)
        for item in errors:
            print(f"{item['package']} ({item['category']}): {item['error']}")
    
    # Print recommended updates
    if upgrade_needed:
        print("\n" + "=" * 80)
        print("RECOMMENDED UPDATES")
        print("=" * 80)
        print("\nUpdate pyproject.toml with these versions:\n")
        
        for item in upgrade_needed:
            current_spec = item["version_spec"]
            # Try to preserve the version spec format but update minimum
            if current_spec.startswith(">="):
                # Update minimum version
                new_spec = re.sub(r">=\s*[\d.]+", f">={item['latest']}", current_spec)
                print(f"  {item['package']}: {current_spec} -> {new_spec}")
            elif current_spec.startswith("=="):
                # Update exact version
                new_spec = f"=={item['latest']}"
                print(f"  {item['package']}: {current_spec} -> {new_spec}")
            else:
                # Add minimum version
                print(f"  {item['package']}: {current_spec} -> >={item['latest']}")
    
    return 0 if not upgrade_needed else 1


if __name__ == "__main__":
    sys.exit(main())
