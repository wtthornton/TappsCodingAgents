"""Execute full SDLC workflow for Amazon HTML page creation."""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Windows compatibility: Set UTF-8 encoding for console output
if sys.platform == "win32":
    # Set environment variable for subprocess calls
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout/stderr if available (Python 3.7+)
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Ignore if reconfigure fails

# Force headless mode to see terminal output and run fully automated
# This bypasses Cursor mode which uses Background Agents and manual execution
os.environ["TAPPS_AGENTS_MODE"] = "headless"

# Add the project root to the path (script lives in scripts/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.preset_loader import PresetLoader

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


async def main():
    """Execute the full SDLC workflow."""
    # Load the full SDLC preset
    loader = PresetLoader()
    workflow = loader.load_preset("full")
    
    if not workflow:
        print("Error: Could not load 'full' preset", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Starting: {workflow.name}")
    print(f"{'='*60}")
    print(f"Description: {workflow.description}")
    print(f"Steps: {len(workflow.steps)}")
    print()
    
    # Create executor with auto mode
    executor = WorkflowExecutor(
        auto_detect=False,
        auto_mode=True,
        project_root=Path.cwd()
    )
    
    # Set the user prompt
    executor.user_prompt = (
        "Create an amazon HTML page the highlights all the 2025 advanced features. "
        "Make it modern and dark, but eye catching"
    )
    
    # Execute the workflow
    try:
        print("Executing workflow...")
        print("=" * 60)
        result = await executor.execute(workflow=workflow)
        
        if result.status == "completed":
            print(f"\n{'='*60}")
            print("Workflow completed successfully!")
            print(f"{'='*60}")
            print(f"\nArtifacts created:")
            for name, artifact in result.artifacts.items():
                print(f"  - {name}: {artifact.path}")
        elif result.status == "failed":
            print(f"\nError: {result.error or 'Unknown error'}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\nWorkflow status: {result.status}")
            
    except Exception as e:
        print(f"Error executing workflow: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

