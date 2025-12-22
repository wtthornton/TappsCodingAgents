"""Shared utilities for agent lifecycle management."""
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def safe_close_agent(agent: Any) -> None:
    """
    Safely close an agent, handling cases where close() may not exist.
    
    Args:
        agent: Agent instance to close
    """
    if not agent:
        return
    
    try:
        if hasattr(agent, 'close') and callable(agent.close):
            if asyncio.iscoroutinefunction(agent.close):
                await agent.close()
            else:
                agent.close()
    except Exception as e:
        # Log but don't fail - cleanup errors shouldn't break commands
        logger.debug(f"Error during agent cleanup: {e}", exc_info=True)


def safe_close_agent_sync(agent: Any) -> None:
    """
    Synchronous version of safe_close_agent for use in sync contexts.
    
    Args:
        agent: Agent instance to close
    """
    if not agent:
        return
    
    try:
        if hasattr(agent, 'close') and callable(agent.close):
            if asyncio.iscoroutinefunction(agent.close):
                asyncio.run(agent.close())
            else:
                agent.close()
    except Exception as e:
        logger.debug(f"Error during agent cleanup: {e}", exc_info=True)

