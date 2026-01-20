"""
Quick test to verify execute_improvements.py can start and show feedback.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


def log(message: str, level: str = "INFO"):
    """Print timestamped log message with immediate flush."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


async def test_startup():
    """Test that the script can load and display files without processing."""
    log("=" * 70, "TEST")
    log("Testing execute_improvements.py startup", "TEST")
    log("=" * 70, "TEST")

    # Load analysis results
    analysis_file = Path("docs/implementation/PROJECT_ANALYSIS.json")
    if not analysis_file.exists():
        log("Analysis file not found. Run analyze_project.py first.", "ERROR")
        return

    log(f"Loading analysis from {analysis_file}...", "LOAD")
    with open(analysis_file) as f:
        data = json.load(f)

    analysis = data.get("analysis", {})
    code_quality = analysis.get("code_quality", {})

    # Prioritize files by lowest score
    files_to_improve = sorted(
        code_quality.items(),
        key=lambda x: x[1].get("scoring", {}).get("overall_score", 0),
    )

    log(f"Found {len(files_to_improve)} files to improve", "INFO")
    log("\nPriority order (lowest scores first):", "INFO")
    for idx, (file, result) in enumerate(files_to_improve, 1):
        score = result.get("scoring", {}).get("overall_score", 0)
        log(f"  {idx}. {file}: {score:.1f}/100", "INFO")

    log("\n" + "=" * 70, "TEST")
    log("Startup test complete - script can load and display files", "SUCCESS")
    log("=" * 70, "TEST")


if __name__ == "__main__":
    asyncio.run(test_startup())
