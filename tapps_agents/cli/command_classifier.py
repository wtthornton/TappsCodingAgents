"""
Command classification system for determining network requirements.

This module classifies commands into three categories:
- OFFLINE: Never requires network access
- OPTIONAL: Works offline with reduced functionality
- REQUIRED: Must have network access to function
"""
from enum import Enum


class CommandNetworkRequirement(Enum):
    """Network requirement levels for commands."""
    
    OFFLINE = "offline"  # Never needs network
    OPTIONAL = "optional"  # Works offline with degraded functionality
    REQUIRED = "required"  # Must have network


class CommandClassifier:
    """Classifies commands by network requirement."""
    
    # Commands that NEVER need network
    OFFLINE_COMMANDS = {
        # Reviewer agent offline commands
        ("reviewer", "help"),
        ("reviewer", "score"),
        ("reviewer", "lint"),
        ("reviewer", "type-check"),
        
        # Simple mode offline commands
        ("simple-mode", "status"),
        
        # Top-level commands
        ("doctor", None),
        ("help", None),
        ("version", None),
        
        # Add other offline commands here
    }
    
    # Commands that work offline with reduced functionality
    OPTIONAL_COMMANDS = {
        ("reviewer", "review"),  # Can work without LLM feedback
        ("reviewer", "docs"),  # Can use cached docs
        # Add network-optional commands here
    }
    
    @staticmethod
    def get_network_requirement(agent: str, command: str | None) -> CommandNetworkRequirement:
        """Determine network requirement for a command.
        
        Args:
            agent: Agent name (e.g., "reviewer", "simple-mode", "doctor")
            command: Command name (e.g., "score", "review") or None for top-level
            
        Returns:
            CommandNetworkRequirement enum value
        """
        # Normalize inputs
        agent_key = agent.lower() if agent else None
        command_key = command.lower() if command else None
        key = (agent_key, command_key)
        
        if key in CommandClassifier.OFFLINE_COMMANDS:
            return CommandNetworkRequirement.OFFLINE
        elif key in CommandClassifier.OPTIONAL_COMMANDS:
            return CommandNetworkRequirement.OPTIONAL
        else:
            # Default: assume network required
            return CommandNetworkRequirement.REQUIRED

