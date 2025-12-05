"""
Base Agent Class - Common functionality for all agents
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml

from .config import ProjectConfig, load_config


class BaseAgent(ABC):
    """
    Base class for all agents.
    
    Provides common functionality:
    - Activation instructions
    - Command discovery
    - Configuration loading
    - Help system
    """
    
    def __init__(self, agent_id: str, agent_name: str, config: Optional[ProjectConfig] = None):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.config = config  # ProjectConfig instance
        self.domain_config = None
        self.customizations = None
        
    async def activate(self, project_root: Optional[Path] = None):
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
                self.config = load_config(project_root / ".tapps-agents" / "config.yaml")
            except (ValueError, FileNotFoundError):
                # Use defaults if config file is invalid or missing
                self.config = load_config()  # Returns defaults
        
        # Step 4: Load domain configuration
        domains_path = project_root / ".tapps-agents" / "domains.md"
        if domains_path.exists():
            try:
                self.domain_config = domains_path.read_text(encoding='utf-8')
            except IOError:
                self.domain_config = None
        
        # Step 5: Load customizations
        custom_path = project_root / ".tapps-agents" / "customizations" / f"{self.agent_id}-custom.yaml"
        if custom_path.exists():
            try:
                with open(custom_path, encoding='utf-8') as f:
                    self.customizations = yaml.safe_load(f)
            except (yaml.YAMLError, IOError):
                self.customizations = None
    
    def get_commands(self) -> List[Dict[str, str]]:
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
        
        lines.extend([
            "",
            "Examples:",
            f"  Type '1' or '{commands[0]['command']}' to get help",
            "",
        ])
        
        return "\n".join(lines)
    
    @abstractmethod
    async def run(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute agent command"""
        pass
    
    def parse_command(self, user_input: str) -> Tuple[str, Dict[str, str]]:
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

