#!/usr/bin/env python3
"""
Coverage tracking script for trend analysis.

This script:
- Extracts coverage metrics from coverage.json
- Tracks trends over time
- Generates reports
- Compares against baseline (75%)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def load_coverage_json(coverage_file: Path) -> dict[str, Any]:
    """Load coverage data from JSON file."""
    if not coverage_file.exists():
        print(f"Error: Coverage file not found: {coverage_file}", file=sys.stderr)
        sys.exit(1)

    with open(coverage_file) as f:
        return json.load(f)


def extract_coverage_metrics(coverage_data: dict[str, Any]) -> dict[str, float]:
    """Extract coverage metrics from coverage data."""
    totals = coverage_data.get("totals", {})
    return {
        "lines": totals.get("percent_covered", 0.0),
        "statements": totals.get("percent_covered", 0.0),
        "branches": totals.get("percent_covered_branches", 0.0),
        "functions": totals.get("percent_covered_functions", 0.0),
    }


def get_module_coverage(coverage_data: dict[str, Any]) -> dict[str, float]:
    """Get per-module coverage."""
    module_coverage = {}
    files = coverage_data.get("files", {})

    for file_path, file_data in files.items():
        # Extract module name from path
        if "tapps_agents" in file_path:
            parts = Path(file_path).parts
            try:
                idx = parts.index("tapps_agents")
                module = ".".join(parts[idx:])
            except ValueError:
                module = Path(file_path).stem
        else:
            module = Path(file_path).stem

        totals = file_data.get("summary", {})
        module_coverage[module] = totals.get("percent_covered", 0.0)

    return module_coverage


def generate_report(
    metrics: dict[str, float],
    module_coverage: dict[str, float],
    baseline: float = 75.0,
) -> str:
    """Generate a coverage report."""
    lines = []
    lines.append("=" * 80)
    lines.append("Coverage Report")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Overall metrics
    lines.append("Overall Coverage:")
    lines.append(f"  Lines:       {metrics['lines']:.2f}%")
    lines.append(f"  Statements:  {metrics['statements']:.2f}%")
    lines.append(f"  Branches:    {metrics['branches']:.2f}%")
    lines.append(f"  Functions:   {metrics['functions']:.2f}%")
    lines.append("")

    # Baseline comparison
    main_coverage = metrics["lines"]
    lines.append(f"Baseline Threshold: {baseline}%")
    if main_coverage >= baseline:
        lines.append(f"✅ Coverage meets threshold ({main_coverage:.2f}% >= {baseline}%)")
    else:
        diff = baseline - main_coverage
        lines.append(
            f"⚠️  Coverage below threshold ({main_coverage:.2f}% < {baseline}%)"
        )
        lines.append(f"   Need to increase coverage by {diff:.2f}%")
    lines.append("")

    # Module coverage (sorted by coverage, lowest first)
    lines.append("Module Coverage (lowest first):")
    sorted_modules = sorted(module_coverage.items(), key=lambda x: x[1])
    for module, coverage in sorted_modules[:20]:  # Show bottom 20
        status = "✅" if coverage >= baseline else "⚠️"
        lines.append(f"  {status} {module}: {coverage:.2f}%")

    if len(sorted_modules) > 20:
        lines.append(f"  ... and {len(sorted_modules) - 20} more modules")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Track and report code coverage")
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=Path("coverage.json"),
        help="Path to coverage.json file",
    )
    parser.add_argument(
        "--baseline",
        type=float,
        default=75.0,
        help="Baseline coverage threshold (default: 75.0%%)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for report (default: stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output metrics as JSON",
    )

    args = parser.parse_args()

    # Load coverage data
    coverage_data = load_coverage_json(args.coverage_file)

    # Extract metrics
    metrics = extract_coverage_metrics(coverage_data)
    module_coverage = get_module_coverage(coverage_data)

    # Generate report
    if args.json:
        output = json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "module_coverage": module_coverage,
                "baseline": args.baseline,
                "meets_baseline": metrics["lines"] >= args.baseline,
            },
            indent=2,
        )
    else:
        output = generate_report(metrics, module_coverage, args.baseline)

    # Write output
    if args.output:
        args.output.write_text(output)
        print(f"Report written to: {args.output}")
    else:
        print(output)

    # Exit with error if below baseline
    if metrics["lines"] < args.baseline:
        sys.exit(1)


if __name__ == "__main__":
    main()

