"""Quick test for context manager"""

from pathlib import Path

from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.tiered_context import ContextTier

agent = BaseAgent("test", "Test")
context = agent.get_context(Path("tapps_agents/core/agent_base.py"), ContextTier.TIER1)
print(f"Context retrieved: {len(context)} keys, tier: {context.get('tier')}")
print(f"Token estimate: {context.get('token_estimate', 0)}")
