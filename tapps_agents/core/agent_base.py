"""
Base Agent Class - Common functionality for all agents
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig, load_config
from .error_envelope import create_error_result, ErrorEnvelopeBuilder


class BaseAgent(ABC):
    """
    Base class for all agents.

    Provides common functionality:
    - Activation instructions
    - Command discovery
    - Configuration loading
    - Help system
    """

    def __init__(
        self, agent_id: str, agent_name: str, config: ProjectConfig | None = None
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.config = config  # ProjectConfig instance
        self.domain_config: str | None = None
        self.customizations: Any | None = None
        self.context_manager: Any | None = None
        self.mcp_gateway: Any | None = None
        self._unified_cache: Any | None = None  # Optional unified cache instance

    async def activate(self, project_root: Path | None = None):
        """
        Follow activation instructions sequence.

        BMAD-METHOD pattern:
        1. Read agent definition
        2. Load project config
        3. Load domain config
        4. Load customizations
        5. Greet user
        6. Run *help
        7. Wait for commands
        """
        if project_root is None:
            project_root = Path.cwd()

        # Step 3: Load project configuration
        # If config not already loaded, load it now
        if self.config is None:
            try:
                self.config = load_config(
                    project_root / ".tapps-agents" / "config.yaml"
                )
            except (ValueError, FileNotFoundError):
                # Use defaults if config file is invalid or missing
                self.config = load_config()  # Returns defaults

        # Step 4: Load domain configuration
        domains_path = project_root / ".tapps-agents" / "domains.md"
        if domains_path.exists():
            try:
                self.domain_config = domains_path.read_text(encoding="utf-8")
            except OSError:
                self.domain_config = None

        # Step 5: Load customizations
        custom_path = (
            project_root
            / ".tapps-agents"
            / "customizations"
            / f"{self.agent_id}-custom.yaml"
        )
        if custom_path.exists():
            try:
                with open(custom_path, encoding="utf-8") as f:
                    self.customizations = yaml.safe_load(f)
            except (OSError, yaml.YAMLError):
                self.customizations = None

    def get_commands(self) -> list[dict[str, str]]:
        """
        Return list of available commands for this agent.

        Format:
        [
            {"command": "*review", "description": "Review code file"},
            {"command": "*score", "description": "Calculate scores only"},
            ...
        ]
        """
        return [
            {"command": "*help", "description": "Show available commands"},
        ]

    def format_help(self) -> str:
        """
        Format help output with numbered command list.

        BMAD-METHOD pattern: Show numbered list for easy selection.
        """
        commands = self.get_commands()

        lines = [
            f"{self.agent_name} - Available Commands",
            "=" * 50,
            "",
            "Type the command number or command name:",
            "",
        ]

        for i, cmd in enumerate(commands, 1):
            lines.append(f"{i}. {cmd['command']:<20} - {cmd['description']}")

        lines.extend(
            [
                "",
                "Examples:",
                f"  Type '1' or '{commands[0]['command']}' to get help",
                "",
            ]
        )

        return "\n".join(lines)

    @abstractmethod
    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute agent command"""
        pass

    def parse_command(self, user_input: str) -> tuple[str, dict[str, str]]:
        """
        Parse user input to extract command and arguments.

        Supports:
        - "*review file.py" -> ("review", {"file": "file.py"})
        - "1" -> (command from numbered list)
        - "review file.py" -> ("review", {"file": "file.py"})
        """
        user_input = user_input.strip()

        # Handle numbered command
        if user_input.isdigit():
            commands = self.get_commands()
            idx = int(user_input) - 1
            if 0 <= idx < len(commands):
                command_str = commands[idx]["command"]
                # Remove * prefix for processing
                return command_str.lstrip("*"), {}

        # Handle star-prefixed command
        if user_input.startswith("*"):
            parts = user_input[1:].split(maxsplit=1)
            command = parts[0]
            args_str = parts[1] if len(parts) > 1 else ""
        else:
            parts = user_input.split(maxsplit=1)
            command = parts[0]
            args_str = parts[1] if len(parts) > 1 else ""

        # Parse arguments (simple space-separated for now)
        args = {}
        if args_str:
            # For commands like "review file.py", treat first arg as file
            if command in ["review", "score"]:
                args["file"] = args_str.strip()

        return command, args

    def get_context(
        self, file_path: Path, tier: Any | None = None, include_related: bool = False
    ) -> dict[str, Any]:
        """
        Get tiered context for a file.

        Args:
            file_path: Path to the file
            tier: Context tier level (default: TIER1)
            include_related: Whether to include related files

        Returns:
            Dictionary with tiered context
        """
        from .context_manager import ContextManager
        from .tiered_context import ContextTier

        if tier is None:
            tier = ContextTier.TIER1

        if self.context_manager is None:
            self.context_manager = ContextManager()

        return self.context_manager.get_context(file_path, tier, include_related)

    def get_context_text(
        self, file_path: Path, tier: Any | None = None, format: str = "text"
    ) -> str:
        """
        Get tiered context as formatted text.

        Args:
            file_path: Path to the file
            tier: Context tier level
            format: Output format (text/markdown/json)

        Returns:
            Formatted context string
        """
        from .context_manager import ContextManager
        from .tiered_context import ContextTier

        if tier is None:
            tier = ContextTier.TIER1

        if self.context_manager is None:
            self.context_manager = ContextManager()

        return self.context_manager.get_context_text(file_path, tier, format)

    def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """
        Call a tool through the MCP Gateway.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool result dictionary
        """
        if self.mcp_gateway is None:
            from tapps_agents.mcp import (
                AnalysisMCPServer,
                FilesystemMCPServer,
                GitMCPServer,
                MCPGateway,
            )

            self.mcp_gateway = MCPGateway()
            # Register default servers
            FilesystemMCPServer(self.mcp_gateway.registry)
            GitMCPServer(self.mcp_gateway.registry)
            AnalysisMCPServer(self.mcp_gateway.registry)

        return self.mcp_gateway.call_tool(tool_name, **kwargs)

    def _validate_path(
        self, file_path: Path, max_file_size: int = 10 * 1024 * 1024
    ) -> None:
        """
        Validate file path for security and size.
        Raises ValueError for invalid paths or FileNotFoundError if file doesn't exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = file_path.stat().st_size
        if file_size > max_file_size:
            raise ValueError(
                f"File too large: {file_size} bytes (max {max_file_size} bytes)"
            )

        # Resolve path to check for path traversal
        resolved_path = file_path.resolve()

        # Allow test files in temp directories
        if "pytest" in str(resolved_path) and "tmp_path" in str(resolved_path):
            return

        # Basic path traversal check (more robust checks might involve comparing against project root)
        if ".." in str(file_path) and not resolved_path.exists():
            raise ValueError(f"Path traversal detected: {file_path}")

        # Additional check: ensure path doesn't contain suspicious patterns
        suspicious_patterns = ["%2e%2e", "%2f", "%5c"]  # URL-encoded traversal attempts
        if any(pattern in str(file_path).lower() for pattern in suspicious_patterns):
            raise ValueError(f"Suspicious path detected: {file_path}")

    def get_unified_cache(self):
        """
        Get or create unified cache instance (optional enhancement).

        This provides access to the unified cache interface which includes:
        - Tiered Context Cache
        - Context7 KB Cache
        - RAG Knowledge Base

        Returns:
            UnifiedCache instance (lazy initialization)

        Note: This is an optional enhancement. Existing code using
        context_manager continues to work unchanged. The unified cache
        will use the existing context_manager if available, or create
        a new one if not.
        """
        if self._unified_cache is None:
            from .cache_router import CacheType
            from .unified_cache import create_unified_cache

            # Use existing context_manager if available for backward compatibility
            self._unified_cache = create_unified_cache(
                context_manager=self.context_manager
            )
            # If we didn't have a context_manager, use the one from unified cache
            if self.context_manager is None:
                # Access the context_manager from the TieredContextAdapter
                tiered_adapter = self._unified_cache.router.get_adapter(
                    CacheType.TIERED_CONTEXT
                )
                if tiered_adapter:
                    self.context_manager = tiered_adapter.context_manager

        return self._unified_cache

    def handle_optional_dependency_error(
        self,
        error: Exception,
        dependency_name: str,
        workflow_id: str | None = None,
        step_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle errors from optional dependencies gracefully.

        This method creates a structured error result that indicates
        the dependency is optional and the operation can continue without it.

        Args:
            error: Exception that occurred
            dependency_name: Name of the optional dependency (e.g., "Context7", "MAL")
            workflow_id: Optional workflow ID for correlation
            step_id: Optional step ID for correlation

        Returns:
            Error result dictionary with recoverable=True
        """
        from .exceptions import Context7UnavailableError, MALDisabledInCursorModeError

        # Create a user-friendly message
        if isinstance(error, (Context7UnavailableError, MALDisabledInCursorModeError)):
            message = f"{dependency_name} is not available: {str(error)}"
        else:
            message = f"{dependency_name} operation failed: {str(error)}"

        envelope = ErrorEnvelope(
            code=f"{dependency_name.lower()}_unavailable",
            message=message,
            category="external_dependency",
            workflow_id=workflow_id,
            step_id=step_id,
            agent=self.agent_id,
            recoverable=True,
        )

        result = envelope.to_dict()
        result["success"] = False
        result["optional_dependency"] = True
        return result
