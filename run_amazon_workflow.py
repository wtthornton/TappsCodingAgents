"""Execute full SDLC workflow for Amazon HTML page creation."""
import asyncio
import sys
import logging
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

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

