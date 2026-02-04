"""
Command Registry for TappsCodingAgents.

Provides centralized command registration, alias management, and fuzzy matching
for command discovery and error handling.
"""

from collections import defaultdict
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Any


@dataclass
class CommandDefinition:
    """Definition of a command with aliases and metadata."""

    command: str
    aliases: list[str]
    agent: str
    description: str
    parameters: dict[str, Any] | None = None

    def matches(self, query: str) -> bool:
        """Check if query matches this command or any alias."""
        query_lower = query.lower()
        return (
            self.command.lower() == query_lower
            or query_lower in [alias.lower() for alias in self.aliases]
        )


class CommandRegistry:
    """
    Centralized registry for all agent commands.
    
    Provides:
    - Command registration with aliases
    - Fuzzy matching for typos
    - Command discovery
    - Error message generation with suggestions
    """

    def __init__(self):
        """Initialize empty registry."""
        self._commands: dict[str, list[CommandDefinition]] = defaultdict(list)
        self._all_commands: dict[str, CommandDefinition] = {}  # command -> definition

    def register(
        self,
        command: str,
        agent: str,
        description: str,
        aliases: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a command with optional aliases.
        
        Args:
            command: Primary command name (kebab-case recommended)
            agent: Agent name that provides this command
            description: Human-readable description
            aliases: Optional list of aliases (e.g., ["api-design"] for "design-api")
            parameters: Optional parameter definitions
        """
        definition = CommandDefinition(
            command=command,
            aliases=aliases or [],
            agent=agent,
            description=description,
            parameters=parameters,
        )

        # Store by agent
        self._commands[agent].append(definition)

        # Store by command name (primary)
        self._all_commands[command] = definition

        # Store aliases
        for alias in aliases or []:
            self._all_commands[alias] = definition

    def find(self, query: str, agent: str | None = None) -> CommandDefinition | None:
        """
        Find command by exact match.
        
        Args:
            query: Command name or alias to find
            agent: Optional agent name to limit search
            
        Returns:
            CommandDefinition if found, None otherwise
        """
        query_lower = query.lower()

        if agent:
            # Search within specific agent
            for cmd_def in self._commands.get(agent, []):
                if cmd_def.matches(query):
                    return cmd_def
        else:
            # Search all commands
            if query_lower in self._all_commands:
                return self._all_commands[query_lower]

        return None

    def fuzzy_match(
        self, query: str, agent: str | None = None, limit: int = 3
    ) -> list[CommandDefinition]:
        """
        Find commands using fuzzy matching (for typo correction).
        
        Args:
            query: Command name to match
            agent: Optional agent name to limit search
            limit: Maximum number of suggestions
            
        Returns:
            List of CommandDefinition objects, sorted by similarity
        """
        query_lower = query.lower()

        # Get candidates
        if agent:
            candidates = self._commands.get(agent, [])
        else:
            candidates = list(self._all_commands.values())

        # Build list of all possible matches (command + aliases)
        all_matches: list[tuple[str, CommandDefinition]] = []
        for cmd_def in candidates:
            all_matches.append((cmd_def.command, cmd_def))
            for alias in cmd_def.aliases:
                all_matches.append((alias, cmd_def))

        # Use difflib for fuzzy matching
        match_strings = [match[0] for match in all_matches]
        close_matches = get_close_matches(query_lower, match_strings, n=limit, cutoff=0.6)

        # Convert back to CommandDefinition objects
        result = []
        seen = set()
        for match_str in close_matches:
            for orig_str, cmd_def in all_matches:
                if orig_str.lower() == match_str and cmd_def.command not in seen:
                    result.append(cmd_def)
                    seen.add(cmd_def.command)
                    break

        return result

    def get_commands(self, agent: str | None = None) -> list[CommandDefinition]:
        """
        Get all commands, optionally filtered by agent.
        
        Args:
            agent: Optional agent name to filter
            
        Returns:
            List of CommandDefinition objects
        """
        if agent:
            return self._commands.get(agent, [])
        return list(self._all_commands.values())

    def get_suggestions(
        self, query: str, agent: str | None = None
    ) -> dict[str, Any]:
        """
        Get command suggestions for error messages.
        
        Args:
            query: Unknown command that was queried
            agent: Optional agent name
            
        Returns:
            Dictionary with suggestions and error message
        """
        # Try exact match first
        exact = self.find(query, agent)
        if exact:
            return {
                "found": True,
                "command": exact,
                "message": f"Command '{query}' found. Use: {exact.command}",
            }

        # Try fuzzy match
        fuzzy_matches = self.fuzzy_match(query, agent, limit=3)
        if fuzzy_matches:
            suggestions = [cmd.command for cmd in fuzzy_matches]
            return {
                "found": False,
                "suggestions": suggestions,
                "message": f"Unknown command '{query}'. Did you mean: {', '.join(suggestions)}?",
            }

        # No matches - show available commands
        available = self.get_commands(agent)
        if available:
            available_names = [cmd.command for cmd in available[:5]]
            return {
                "found": False,
                "suggestions": [],
                "available": available_names,
                "message": f"Unknown command '{query}'. Available commands: {', '.join(available_names)}...",
            }

        return {
            "found": False,
            "suggestions": [],
            "message": f"Unknown command '{query}'. No commands available.",
        }


# Global registry instance
_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    """Get or create global command registry."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
        _register_default_commands(_registry)
    return _registry


def _register_default_commands(registry: CommandRegistry) -> None:
    """Register default commands for all agents."""
    # Designer agent commands
    registry.register(
        command="design-api",
        agent="designer",
        description="Design API endpoints and specifications",
        aliases=["api-design", "designapi"],
    )
    registry.register(
        command="design-model",
        agent="designer",
        description="Design data models",
        aliases=["model-design", "designmodel"],
    )

    # Documenter agent commands
    registry.register(
        command="document",
        agent="documenter",
        description="Generate documentation for a file",
        aliases=["doc", "generate-docs"],
    )
    registry.register(
        command="document-api",
        agent="documenter",
        description="Document API endpoints",
        aliases=["api-document", "documentapi", "generate-docs"],
    )

    # Planner agent commands
    registry.register(
        command="plan",
        agent="planner",
        description="Create development plan",
        aliases=["create-plan"],
    )
    registry.register(
        command="create-story",
        agent="planner",
        description="Create user story",
        aliases=["story", "add-story"],
    )

    # Reviewer agent commands
    registry.register(
        command="review",
        agent="reviewer",
        description="Review code with scoring and feedback",
        aliases=["code-review"],
    )
    registry.register(
        command="score",
        agent="reviewer",
        description="Calculate quality scores only",
        aliases=["quality-score"],
    )

    # Implementer agent commands
    registry.register(
        command="implement",
        agent="implementer",
        description="Generate code from specification",
        aliases=["generate-code", "code"],
    )
    registry.register(
        command="refactor",
        agent="implementer",
        description="Refactor existing code",
        aliases=["refactor-code"],
    )

    # Tester agent commands
    registry.register(
        command="test",
        agent="tester",
        description="Generate and run tests",
        aliases=["generate-tests", "run-tests"],
    )

    # Enhancer agent commands
    registry.register(
        command="enhance",
        agent="enhancer",
        description="Full prompt enhancement (7-stage pipeline)",
        aliases=["enhance-prompt"],
    )
    registry.register(
        command="enhance-quick",
        agent="enhancer",
        description="Quick prompt enhancement (stages 1-3)",
        aliases=["quick-enhance"],
    )

    # Add more default commands as needed...
