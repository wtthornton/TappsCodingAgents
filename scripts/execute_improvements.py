"""
Execute improvements to TappsCodingAgents based on analysis.
Uses Implementer and Improver agents to fix identified issues.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from tapps_agents.agents.implementer.agent import ImplementerAgent
from tapps_agents.agents.reviewer.agent import ReviewerAgent


def log(message: str, level: str = "INFO"):
    """Print timestamped log message with immediate flush."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


async def improve_file(
    file_path: str, issues: dict[str, Any], file_index: int, total_files: int
) -> dict[str, Any]:
    """Improve a specific file based on identified issues."""
    log(f"Processing file {file_index}/{total_files}: {file_path}", "IMPROVE")

    # Load config first to ensure MAL is properly configured
    from tapps_agents.core.config import load_config

    config = load_config()

    # Enable streaming and configure timeouts for large files
    if config.mal:
        config.mal.use_streaming = True
        config.mal.read_timeout = 600.0  # 10 minutes for large files
        config.mal.streaming_threshold = 5000  # Auto-stream for large prompts

    log("Initializing Implementer Agent...", "SETUP")
    implementer = ImplementerAgent(config=config)
    try:
        # Activate with project root and set it explicitly
        project_root = Path.cwd()
        log("Activating agent with project context...", "SETUP")
        await implementer.activate(project_root=project_root)
        implementer.project_root = project_root  # Ensure it's set

        # Create improvement instruction
        instruction = f"""Refactor and improve code quality based on these scores:
- Maintainability: {issues.get('maintainability_score', 0):.1f}/10 (target: 8.0+)
- Overall Score: {issues.get('overall_score', 0):.1f}/100 (target: 70+)

Focus on:
1. Improving maintainability (code organization, function length, complexity)
2. Adding type hints where missing
3. Improving code structure and readability
4. Following PEP 8 style guidelines
5. Breaking down large functions into smaller, focused functions
6. Improving error handling
"""

        log(
            "Sending refactoring request to LLM (this may take a few minutes for large files)...",
            "LLM",
        )
        log("Streaming enabled - responses will be processed incrementally", "INFO")
        log("Note: Large files may take 2-5 minutes to process", "INFO")
        log("Starting LLM call now...", "LLM")

        # Create a heartbeat task to show progress
        heartbeat_task = None
        heartbeat_count = [0]

        async def heartbeat():
            """Print heartbeat every 30 seconds during LLM processing."""
            while True:
                await asyncio.sleep(30)
                heartbeat_count[0] += 1
                elapsed = heartbeat_count[0] * 30
                log(f"Still processing... ({elapsed}s elapsed)", "HEARTBEAT")

        try:
            # Start heartbeat
            heartbeat_task = asyncio.create_task(heartbeat())

            # Add timeout wrapper
            result = await asyncio.wait_for(
                implementer.run(
                    "refactor",  # Command without star prefix
                    file_path=file_path,
                    instruction=instruction,
                ),
                timeout=600.0,  # 10 minute timeout
            )

            # Cancel heartbeat
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            elapsed = heartbeat_count[0] * 30
            log(
                f"Refactoring request completed successfully (took ~{elapsed}s)",
                "SUCCESS",
            )
        except TimeoutError:
            if heartbeat_task:
                heartbeat_task.cancel()
            log("LLM call timed out after 10 minutes", "ERROR")
            return {"error": "LLM call timed out after 10 minutes"}
        except Exception as e:
            if heartbeat_task:
                heartbeat_task.cancel()
            log(f"LLM call failed: {e}", "ERROR")
            raise
        return result
    except Exception as e:
        log(f"Error during refactoring: {e}", "ERROR")
        import traceback

        log(f"Traceback: {traceback.format_exc()}", "ERROR")
        return {"error": str(e)}


async def verify_improvement(file_path: str) -> dict[str, Any]:
    """Verify that improvements increased the score."""
    log(f"Verifying improvements for {file_path}...", "VERIFY")

    reviewer = ReviewerAgent()
    try:
        log("Initializing Reviewer Agent...", "VERIFY")
        await reviewer.activate()
        log("Scoring improved code...", "VERIFY")
        result = await reviewer.run("score", file=file_path)
        log("Verification complete", "VERIFY")
        return result
    except Exception as e:
        log(f"Verification error: {e}", "ERROR")
        return {"error": str(e)}


async def main():
    """Execute improvements based on analysis."""
    log("=" * 70, "START")
    log("TappsCodingAgents Improvement Execution", "START")
    log("=" * 70, "START")

    # Load analysis results
    analysis_file = Path("implementation/PROJECT_ANALYSIS.json")
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

    # Auto-proceed (user requested automatic execution)
    log("\n" + "=" * 70, "INFO")
    log("Proceeding with automatic improvements...", "INFO")
    log("=" * 70, "INFO")

    # Execute improvements
    results = []
    total_files = len(files_to_improve)

    for idx, (file_path, file_data) in enumerate(files_to_improve, 1):
        scoring = file_data.get("scoring", {})
        old_score = scoring.get("overall_score", 0)

        log("\n" + "=" * 70, "FILE")
        log(f"File {idx}/{total_files}: {file_path}", "FILE")
        log(f"Current Score: {old_score:.1f}/100", "FILE")
        log("=" * 70, "FILE")

        # Improve
        improvement = await improve_file(file_path, scoring, idx, total_files)

        if "error" in improvement:
            log(
                f"Improvement failed: {improvement.get('error', 'Unknown error')}",
                "ERROR",
            )
            results.append(
                {
                    "file": file_path,
                    "status": "failed",
                    "error": improvement.get("error", "Unknown error"),
                }
            )
            continue

        # Verify
        log("Improvement successful, verifying score...", "INFO")
        verification = await verify_improvement(file_path)

        if "scoring" in verification:
            new_score = verification["scoring"].get("overall_score", 0)
            improvement_amount = new_score - old_score

            log(f"New Score: {new_score:.1f}/100", "SUCCESS")
            log(f"Improvement: {improvement_amount:+.1f} points", "SUCCESS")

            results.append(
                {
                    "file": file_path,
                    "old_score": old_score,
                    "new_score": new_score,
                    "improvement": improvement_amount,
                    "status": "success" if new_score > old_score else "no_change",
                }
            )
        else:
            log(
                f"Verification failed: {verification.get('error', 'Unknown error')}",
                "ERROR",
            )
            results.append(
                {
                    "file": file_path,
                    "status": "verification_failed",
                    "error": verification.get("error", "Unknown error"),
                }
            )

    # Save results
    results_file = Path("implementation/IMPROVEMENT_RESULTS.json")
    results_file.parent.mkdir(exist_ok=True)
    log(f"Saving results to {results_file}...", "SAVE")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    log("\n" + "=" * 70, "SUMMARY")
    log("IMPROVEMENT SUMMARY", "SUMMARY")
    log("=" * 70, "SUMMARY")

    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "failed"]
    no_change = [r for r in results if r.get("status") == "no_change"]
    total_improvement = sum(r.get("improvement", 0) for r in successful)

    log(f"Successfully improved: {len(successful)}/{len(results)} files", "SUCCESS")
    log(f"Failed: {len(failed)} files", "INFO" if not failed else "WARNING")
    log(f"No change: {len(no_change)} files", "INFO")
    log(f"Total score improvement: {total_improvement:+.1f} points", "SUCCESS")

    if successful:
        log("\nTop improvements:", "INFO")
        for result in sorted(
            successful, key=lambda x: x.get("improvement", 0), reverse=True
        )[:5]:
            log(f"  {result['file']}: {result['improvement']:+.1f} points", "INFO")

    if failed:
        log("\nFailed files:", "WARNING")
        for result in failed:
            log(
                f"  {result['file']}: {result.get('error', 'Unknown error')}", "WARNING"
            )

    log(f"\nFull results saved to: {results_file}", "SAVE")
    log("=" * 70, "COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
