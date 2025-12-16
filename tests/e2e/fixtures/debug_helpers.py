"""Debug helpers for E2E tests."""
import json
from typing import Any, Dict


def print_test_context(agent, command: str, response: Dict[str, Any]) -> None:
    """Print test context for debugging."""
    print("\n" + "="*80)
    print(f"Agent: {agent.__class__.__name__}")
    print(f"Command: {command}")
    print(f"Response Type: {type(response)}")
    if isinstance(response, dict):
        print(f"Response Keys: {list(response.keys())}")
        print(f"Response:\n{json.dumps(response, indent=2, default=str)}")
    else:
        print(f"Response: {response}")
    print("="*80 + "\n")

