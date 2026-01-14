"""
Base Agent Class - Common functionality for all agents
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .config import ProjectConfig, load_config
from .error_envelope import ErrorEnvelope


class BaseAgent(ABC):
    """
    Base class for all agents.

    Provides common functionality:
    - Activation instructions
    - Command discovery
    - Configuration loading
    - Help system

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    All agents MUST maintain 100% accuracy:
    - NEVER make up, invent, or fabricate information
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    - Check actual return values, not just that functions were called
    """

    def __init__(
        self, agent_id: str, agent_name: str, config: ProjectConfig | None = None
    ):
        """
        Initialize a base agent instance.
        
        Args:
            agent_id: Unique identifier for the agent (e.g., "reviewer", "planner")
            agent_name: Human-readable name for the agent (e.g., "Code Reviewer")
            config: Optional project configuration. If None, will be loaded during activation.
            
        Note:
            Most agent attributes are initialized to None and populated during the
            activate() method. This allows for lazy initialization and proper error handling.
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.config = config  # ProjectConfig instance
        self.domain_config: str | None = None
        self.customizations: Any | None = None
        self.role_file: Any | None = None  # Agent role file data
        self.context_manager: Any | None = None
        self.mcp_gateway: Any | None = None
        self._unified_cache: Any | None = None  # Optional unified cache instance
        self._project_root: Path | None = None  # Cached project root
        self._cached_commands: list[dict[str, str]] | None = None  # Cached command list

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """
        Follow activation instructions sequence.

        This method initializes the agent by loading all necessary configuration
        and context. It follows the BMAD-METHOD pattern for agent activation.

        BMAD-METHOD pattern:
        1. Read agent definition
        2. Load project config
        3. Load domain config
        4. Load role file (optional)
        5. Load customizations
        6. Greet user
        7. Run *help
        8. Wait for commands
        
        Args:
            project_root: Optional project root path. If None, will be detected
                automatically from the current working directory or config.
            offline_mode: If True, skip network-dependent initialization
                (expert support, Context7 helpers, MCP gateway). Defaults to False.
                
        Raises:
            FileNotFoundError: If required configuration files are missing
            ValueError: If configuration is invalid
        """
        if project_root is None:
            project_root = Path.cwd()

        # Store project root for path validation
        self._project_root = project_root

        # Step 3: Load project configuration (offline operation)
        # If config not already loaded, load it now
        if self.config is None:
            try:
                self.config = load_config(
                    project_root / ".tapps-agents" / "config.yaml"
                )
            except (ValueError, FileNotFoundError):
                # Use defaults if config file is invalid or missing
                self.config = load_config()  # Returns defaults

        # Step 4: Load domain configuration (offline operation)
        domains_path = project_root / ".tapps-agents" / "domains.md"
        if domains_path.exists():
            try:
                self.domain_config = domains_path.read_text(encoding="utf-8")
            except OSError:
                self.domain_config = None

        # Step 5: Load role file (if available) (offline operation)
        from .role_loader import load_role_file

        self.role_file = load_role_file(self.agent_id, project_root)

        # Step 5b: Load user role template (if available) (offline operation)
        from .role_template_loader import get_role_from_config

        user_role_id = get_role_from_config(project_root)
        self.user_role_template = None
        if user_role_id:
            from .role_template_loader import load_role_template
            self.user_role_template = load_role_template(user_role_id, project_root)

        # Step 6: Load customizations (offline operation)
        # Customizations can override role file and role template
        from .customization_loader import load_customization

        self.customizations = load_customization(self.agent_id, project_root)
        
        # Network-dependent initialization is deferred to agent subclasses
        # or mixins (e.g., ExpertSupportMixin) when offline_mode=False
        # They should check offline_mode before making network calls

    def get_commands(self) -> list[dict[str, str]]:
        """
        Return list of available commands for this agent.
        
        Results are cached after first call to improve performance. Subclasses
        should override _compute_commands() to provide agent-specific commands.

        Returns:
            List of command dictionaries, each containing:
                - command (str): Command identifier (e.g., "*review", "*help")
                - description (str): Human-readable command description

        Format:
        [
            {"command": "*review", "description": "Review code file"},
            {"command": "*score", "description": "Calculate scores only"},
            ...
        ]
        
        Note:
            This method caches results after the first call. If commands need
            to be recomputed, clear the cache by setting self._cached_commands = None.
        """
        if self._cached_commands is None:
            self._cached_commands = self._compute_commands()
        return self._cached_commands

    def _compute_commands(self) -> list[dict[str, str]]:
        """
        Compute the list of available commands for this agent.
        
        This is the internal method that subclasses should override to provide
        their command list. The base implementation returns just the help command.

        Returns:
            List of command dictionaries. See get_commands() for format details.
        """
        return [
            {"command": "*help", "description": "Show available commands"},
        ]

    def format_help(self) -> str:
        """
        Format help output with numbered command list.

        BMAD-METHOD pattern: Show numbered list for easy selection.
        
        Returns:
            Formatted help text as a string, with commands numbered and
            formatted for easy reading.
            
        Note:
            Uses cached command list from get_commands() for optimal performance.
        """
        commands = self.get_commands()

        lines = [
            f"{self.agent_name} - Available Commands",
            "=" * 50,
            "",
            "Type the command number or command name:",
            "",
        ]

        # Optimize string building with list comprehension
        lines.extend(
            f"{i}. {cmd['command']:<20} - {cmd['description']}"
            for i, cmd in enumerate(commands, 1)
        )

        lines.extend(
            [
                "",
                "Examples:",
                f"  Type '1' or '{commands[0]['command']}' to get help" if commands else "  Use *help to see available commands",
                "",
            ]
        )

        return "\n".join(lines)

    @abstractmethod
    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute agent command"""
        pass

    def format_result(
        self,
        result: dict[str, Any],
        command: str,
        output_format: str = "text",
        output_file: str | Path | None = None,
    ) -> str | Path:
        """
        Format agent result in specified format and optionally save to file.
        
        Args:
            result: Agent result dictionary
            command: Command that was executed
            output_format: Desired output format (json, text, markdown, yaml)
            output_file: Optional path to save output file
            
        Returns:
            Formatted output string, or Path if output_file was provided
        """
        from .output_formatter import OutputFormatter

        formatted = OutputFormatter.format_output(
            result=result,
            agent_name=self.agent_name,
            command=command,
            output_format=output_format,
        )

        if output_file:
            return OutputFormatter.save_output(
                result=result,
                agent_name=self.agent_name,
                command=command,
                output_file=output_file,
                output_format=output_format,
            )

        return formatted

    def wrap_instruction_result(
        self,
        instruction: Any,
        auto_execute: bool = False,
        include_directive: bool = True,
    ) -> dict[str, Any]:
        """
        Wrap instruction object in result with execution directive.
        
        Args:
            instruction: Instruction object (CodeGenerationInstruction, etc.)
            auto_execute: If True, include auto-execution flag
            include_directive: If True, include _cursor_execution_directive
            
        Returns:
            Result dictionary with instruction and execution directive
        """
        result = {
            "success": True,
            "type": "instruction",
            "instruction": instruction.to_dict(),
            "description": instruction.get_description(),
            "skill_command": instruction.to_skill_command(),
            "cli_command": instruction.to_cli_command(),
        }

        if include_directive:
            directive = instruction.to_execution_directive()
            if auto_execute:
                directive["_cursor_execution_directive"]["auto_execute"] = True
            result.update(directive)

        return result

    def parse_command(self, user_input: str) -> tuple[str, dict[str, str]]:
        """
        Parse user input to extract command and arguments.

        Supports:
        - "*review file.py" -> ("review", {"file": "file.py"})
        - "1" -> (command from numbered list)
        - "review file.py" -> ("review", {"file": "file.py"})
        """
        user_input = user_input.strip()
        
        # Handle empty input
        if not user_input:
            return "", {}

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
            if not parts or not parts[0]:
                return "", {}
            command = parts[0]
            args_str = parts[1] if len(parts) > 1 else ""
        else:
            parts = user_input.split(maxsplit=1)
            if not parts or not parts[0]:
                return "", {}
            command = parts[0]
            args_str = parts[1] if len(parts) > 1 else ""

        # Parse arguments (simple space-separated for now)
        args = {}
        if args_str:
            # For commands that take file arguments
            file_commands = ["review", "score", "plan", "implement", "test"]
            if command in file_commands:
                args["file"] = args_str.strip()
            # Could also handle other argument patterns here

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
        Validate file path for security and size using centralized path validator.

        This method uses root-based validation to ensure paths are within
        allowed boundaries (project root and .tapps-agents/).

        Args:
            file_path: Path to validate
            max_file_size: Maximum file size in bytes (default: 10MB)

        Raises:
            ValueError: If path validation fails (renamed from PathValidationError for backward compatibility)
            FileNotFoundError: If file doesn't exist
        """
        from .path_validator import PathValidationError, PathValidator

        # Use cached project root or let validator auto-detect
        project_root = self._project_root

        # Create validator with project root
        validator = PathValidator(project_root)

        try:
            # Validate path (will raise PathValidationError or FileNotFoundError)
            validator.validate_read_path(file_path, max_file_size=max_file_size)
        except PathValidationError as e:
            # Convert to ValueError for backward compatibility
            raise ValueError(str(e)) from e

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

    async def close(self) -> None:
        """
        Cleanup resources. Override in subclasses if needed.
        
        This default implementation provides a no-op cleanup. Subclasses should
        override this method to clean up specific resources like:
        - Database connections
        - File handles
        - Network connections
        - Cache instances
        - Background tasks
        
        Examples:
            async def close(self) -> None:
                await super().close()  # Call parent cleanup
                if self.dependency_analyzer:
                    await self.dependency_analyzer.close()
                if self.cache:
                    self.cache.clear()
        """
        # Default implementation - override in subclasses for specific cleanup
        pass

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
            dependency_name: Name of the optional dependency (e.g., "Context7")
            workflow_id: Optional workflow ID for correlation
            step_id: Optional step ID for correlation

        Returns:
            Error result dictionary with recoverable=True
        """
        from .exceptions import Context7UnavailableError

        # Create a user-friendly message
        if isinstance(error, Context7UnavailableError):
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

    async def _auto_fetch_context7_docs(
        self,
        code: str | None = None,
        prompt: str | None = None,
        error_message: str | None = None,
        language: str = "python",
    ) -> dict[str, dict[str, Any]]:
        """
        Automatically detect libraries and fetch Context7 documentation.
        Called before any agent operation that might benefit from library docs.
        
        This is a universal hook that all agents can use to automatically
        fetch Context7 documentation without manual intervention.

        Args:
            code: Optional code content to analyze
            prompt: Optional prompt text to analyze
            error_message: Optional error message or stack trace
            language: Programming language (default: "python")

        Returns:
            Dictionary mapping library names to their documentation dictionaries,
            or empty dict if Context7 is disabled or no libraries detected.
            Format: {library_name: {content: str, source: str, ...}, ...}
        """
        # Get Context7 helper if available
        context7_helper = getattr(self, "context7", None)
        if not context7_helper:
            # Try to get it via the helper function
            from ..context7.agent_integration import get_context7_helper
            context7_helper = get_context7_helper(self, self.config, self._project_root)
            if context7_helper:
                # Cache it for future use
                self.context7 = context7_helper

        if not context7_helper or not context7_helper.enabled:
            return {}

        # Detect libraries from all available sources (including error messages)
        all_detected = context7_helper.detect_libraries(
            code=code, prompt=prompt, error_message=error_message, language=language
        )

        # Filter: Only fetch docs for libraries that are likely relevant
        # Priority: Project deps > Explicit mentions > Well-known libraries
        project_libs = set(context7_helper.detect_libraries(
            code=None, prompt=None, error_message=None
        ))
        
        filtered_libraries = []
        prompt_lower = (prompt or "").lower()
        
        for lib in all_detected:
            # Always include if it's in project dependencies
            if lib in project_libs:
                filtered_libraries.append(lib)
            # Include if explicitly mentioned or well-known
            elif (context7_helper.is_well_known_library(lib) or
                  any(keyword in prompt_lower for keyword in [
                      f"{lib} library", f"{lib} framework", f"using {lib}"
                  ])):
                filtered_libraries.append(lib)

        # Deduplicate
        filtered_libraries = list(set(filtered_libraries))

        # Fetch documentation for filtered libraries only
        if filtered_libraries:
            return await context7_helper.get_documentation_for_libraries(
                libraries=filtered_libraries,
                topic=None,
                use_fuzzy_match=True,
            )

        return {}