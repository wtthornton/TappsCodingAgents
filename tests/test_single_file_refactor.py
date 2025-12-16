"""
Test refactoring a single file to diagnose LLM call issues.
"""

import asyncio
from datetime import datetime
from pathlib import Path


def log(message: str, level: str = "INFO"):
    """Print timestamped log message with immediate flush."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


async def test_single_file():
    """Test refactoring a single small file."""
    log("=" * 70, "TEST")
    log("Testing single file refactoring", "TEST")
    log("=" * 70, "TEST")

    # Use a small file for testing
    test_file = "tapps_agents/core/agent_base.py"

    if not Path(test_file).exists():
        log(f"Test file not found: {test_file}", "ERROR")
        return

    log(f"Target file: {test_file}", "INFO")
    log("Loading configuration...", "SETUP")

    from tapps_agents.agents.implementer.agent import ImplementerAgent
    from tapps_agents.core.config import load_config

    config = load_config()
    if config.mal:
        config.mal.use_streaming = True
        config.mal.read_timeout = 600.0

    log("Initializing Implementer Agent...", "SETUP")
    implementer = ImplementerAgent(config=config)

    project_root = Path.cwd()
    log("Activating agent...", "SETUP")
    await implementer.activate(project_root=project_root)
    implementer.project_root = project_root

    instruction = """Improve code quality:
1. Add type hints where missing
2. Improve code structure
3. Follow PEP 8 guidelines
"""

    log("Sending refactoring request to LLM...", "LLM")
    log("This may take 2-5 minutes for this file", "INFO")
    log("Starting LLM call NOW...", "LLM")

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

        result = await asyncio.wait_for(
            implementer.run("refactor", file_path=test_file, instruction=instruction),
            timeout=600.0,
        )

        # Cancel heartbeat
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        elapsed = heartbeat_count[0] * 30
        if "error" in result:
            log(f"Refactoring failed: {result['error']} (took ~{elapsed}s)", "ERROR")
        else:
            log(f"Refactoring completed successfully! (took ~{elapsed}s)", "SUCCESS")
            log(f"Result keys: {list(result.keys())}", "INFO")

    except TimeoutError:
        if heartbeat_task:
            heartbeat_task.cancel()
        log("LLM call timed out after 10 minutes", "ERROR")
    except Exception as e:
        if heartbeat_task:
            heartbeat_task.cancel()
        log(f"Error: {e}", "ERROR")
        import traceback

        log(f"Traceback:\n{traceback.format_exc()}", "ERROR")

    log("=" * 70, "TEST")
    log("Test complete", "TEST")
    log("=" * 70, "TEST")


if __name__ == "__main__":
    asyncio.run(test_single_file())
