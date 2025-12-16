"""Test refactor functionality directly"""

import asyncio
from pathlib import Path

from tapps_agents.agents.implementer.agent import ImplementerAgent
from tapps_agents.core.config import load_config


async def test_refactor():
    """Test refactor on a small file"""
    print("Testing refactor functionality...")

    config = load_config()
    print(f"MAL Config: {config.mal}")
    print(f"Ollama URL: {config.mal.ollama_url}")
    print(f"Default Model: {config.mal.default_model}")

    agent = ImplementerAgent(config=config)
    try:
        project_root = Path.cwd()
        await agent.activate(project_root=project_root)
        agent.project_root = project_root

        # Test on a small file
        test_file = "test_refactor.py"  # This file itself
        print(f"\nRefactoring {test_file}...")

        result = await agent.run(
            "refactor",
            file_path=test_file,
            instruction="Add type hints to all functions",
        )

        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            import traceback

            traceback.print_exc()
        else:
            print("\n✅ Success!")
            print(f"Result keys: {list(result.keys())}")

        return result
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
    finally:
        if hasattr(agent, "mal") and hasattr(agent.mal, "client"):
            await agent.mal.client.aclose()


if __name__ == "__main__":
    asyncio.run(test_refactor())
