"""
TappsCodingAgents - Specification framework for coding agents.

This package provides a comprehensive framework for building and orchestrating
AI-powered coding agents. It includes workflow execution, agent capabilities,
quality assessment, and integration with Cursor IDE.

Main Components:
    - Core: Base agent classes, context management, caching, and learning systems
    - Agents: Specialized workflow agents (reviewer, implementer, tester, etc.)
    - Workflow: Workflow execution engine, orchestration, and state management
    - CLI: Command-line interface for agent operations

Example:
    ```python
    from tapps_agents import BaseAgent
    from tapps_agents.core import ContextManager
    
    # Create agent instance
    agent = BaseAgent(name="my_agent")
    
    # Use context manager
    context = ContextManager()
    ```
"""

__version__: str = "3.5.11"

# Also expose as _version_ for compatibility with some import mechanisms
# This helps with editable installs where __version__ might not be importable
_version_: str = __version__
