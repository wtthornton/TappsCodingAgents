"""
Documenter Agent - Generates documentation
"""

from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from .doc_generator import DocGenerator


class DocumenterAgent(BaseAgent):
    """
    Documenter Agent - Documentation generation.

    Permissions: Read, Write, Grep, Glob

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="documenter", agent_name="Documenter Agent", config=config
        )
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Initialize doc generator
        self.doc_generator = DocGenerator()

        # Get documenter config
        documenter_config = (
            config.agents.documenter if config and config.agents else None
        )
        self.docs_dir = (
            Path(documenter_config.docs_dir)
            if documenter_config and documenter_config.docs_dir
            else Path("docs")
        )
        self.include_examples = (
            documenter_config.include_examples if documenter_config else True
        )
        self.docstring_format = (
            documenter_config.docstring_format if documenter_config else "google"
        )

        # Initialize Context7 helper (Enhancement: Universal Context7 integration)
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

        # Ensure docs directory exists
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def get_commands(self) -> list[dict[str, str]]:
        """Return list of available commands."""
        commands = super().get_commands()
        commands.extend(
            [
                {
                    "command": "*document",
                    "description": "Generate documentation for a file",
                },
                {
                    "command": "*document-api",
                    "description": "Document API endpoints (alias for generate-docs)",
                },
                {
                    "command": "*generate-docs",
                    "description": "Generate API documentation",
                },
                {
                    "command": "*update-readme",
                    "description": "Generate or update README.md",
                },
                {
                    "command": "*update-docstrings",
                    "description": "Update docstrings in code",
                },
                {
                    "command": "*generate-project-docs",
                    "description": "Generate project-level API documentation for all agents and workflow engine",
                },
                {
                    "command": "*update-project-docs-for-new-agent",
                    "description": "Update all project documentation files for a newly created agent",
                },
            ]
        )
        return commands

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute a command."""
        if command == "document":
            return await self.document_command(**kwargs)
        elif command == "document-api":
            # Backward-compatible alias used by docs and CLI help.
            return await self.generate_docs_command(**kwargs)
        elif command == "generate-docs":
            return await self.generate_docs_command(**kwargs)
        elif command == "update-readme":
            return await self.update_readme_command(**kwargs)
        elif command == "update-docstrings":
            return await self.update_docstrings_command(**kwargs)
        elif command == "generate-project-docs":
            return await self.generate_project_docs_command(**kwargs)
        elif command == "update-project-docs-for-new-agent":
            return await self.update_project_docs_for_new_agent_command(**kwargs)
        elif command == "help":
            return self._help()
        else:
            return {"error": f"Unknown command: {command}"}

    async def document_command(
        self,
        file: str,
        output_format: str = "markdown",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate documentation for a file.

        Args:
            file: Source code file path
            output_format: Output format (markdown/rst/html)
            output_file: Optional output file path
        """
        file_path = Path(file)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        self._validate_path(file_path)

        # Prepare API docs instruction
        instruction = self.doc_generator.prepare_api_docs(file_path, output_format)

        # Determine output file
        if output_file:
            output_path = Path(output_file)
        else:
            # Auto-generate output path
            output_path = (
                self.docs_dir
                / f"{file_path.stem}_api.{'md' if output_format == 'markdown' else output_format}"
            )

        return {
            "type": "document",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "file": str(file_path),
            "output_file": str(output_path),
            "format": output_format,
        }

    async def generate_docs_command(
        self, file: str | None = None, output_format: str = "markdown"
    ) -> dict[str, Any]:
        """
        Generate API documentation.

        Args:
            file: Optional source file (defaults to all Python files)
            output_format: Output format
        """
        if file:
            file_path = Path(file)
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}

            self._validate_path(file_path)
            instruction = self.doc_generator.prepare_api_docs(file_path, output_format)

            return {
                "type": "api_docs",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "file": str(file_path),
                "format": output_format,
            }
        else:
            return {"error": "File path required"}

    async def update_readme_command(
        self, project_root: str | None = None, context: str | None = None
    ) -> dict[str, Any]:
        """
        Generate or update README.md.

        Args:
            project_root: Project root directory (default: current directory)
            context: Optional additional context
        """
        if project_root:
            root_path = Path(project_root)
        else:
            root_path = Path.cwd()

        if not root_path.exists():
            return {"error": f"Directory not found: {root_path}"}

        # Prepare README instruction
        instruction = self.doc_generator.prepare_readme(root_path, context)

        readme_path = root_path / "README.md"

        return {
            "type": "readme",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "project_root": str(root_path),
            "readme_file": str(readme_path),
        }

    async def update_docstrings_command(
        self,
        file: str,
        docstring_format: str | None = None,
        write_file: bool = False,
    ) -> dict[str, Any]:
        """
        Update or add docstrings to code.

        Args:
            file: Source code file path
            docstring_format: Docstring format (default: config value)
            write_file: Whether to write updated code back to file
        """
        file_path = Path(file)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        self._validate_path(file_path)

        format_to_use = docstring_format or self.docstring_format

        # Prepare docstring update instruction
        instruction = self.doc_generator.prepare_docstring_update(
            file_path, format_to_use
        )

        return {
            "type": "docstrings",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "file": str(file_path),
            "format": format_to_use,
            "written": write_file,
        }

    async def generate_project_docs_command(
        self,
        project_root: str | None = None,
        output_dir: str | None = None,
        output_format: str = "markdown",
        include_modules: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate project-level API documentation.

        Args:
            project_root: Project root directory (default: current directory)
            output_dir: Output directory for docs (default: docs/api/)
            output_format: Output format (markdown/rst/html)
            include_modules: Optional list of module paths to include (relative to project_root)

        Returns:
            Dictionary with generation results
        """
        if project_root:
            root_path = Path(project_root)
        else:
            root_path = Path.cwd()

        if not root_path.exists():
            return {"error": f"Directory not found: {root_path}"}

        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
            # Validate output path is within project or allowed location
            self._validate_path(output_path)
        else:
            # Default to docs/api/ under project root
            output_path = root_path / "docs" / "api"

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        # Prepare project documentation instruction
        # For project docs, we'll create a single instruction for the project root
        instruction = self.doc_generator.prepare_api_docs(
            root_path / "README.md" if (root_path / "README.md").exists() else root_path / "__init__.py",
            output_format
        )
        instruction.output_dir = str(output_path)

        return {
            "type": "project_docs",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "project_root": str(root_path),
            "output_dir": str(output_path),
            "format": output_format,
        }

    async def update_project_docs_for_new_agent_command(
        self,
        agent_name: str,
        agent_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update all project documentation files for a newly created agent.
        
        This method updates:
        - README.md (agent count, agent list)
        - docs/API.md (agent subcommands, API docs)
        - docs/ARCHITECTURE.md (agent list)
        - .cursor/rules/agent-capabilities.mdc (agent section)
        
        Args:
            agent_name: Name of the new agent (e.g., "evaluator")
            agent_info: Optional dictionary with agent metadata
            
        Returns:
            Dictionary with update results for each file
        """
        agent_info = agent_info or {}
        results = {
            "agent_name": agent_name,
            "readme_updated": False,
            "api_updated": False,
            "architecture_updated": False,
            "capabilities_updated": False,
            "errors": [],
        }
        
        try:
            # Get project root from activated state or use current directory
            # BaseAgent stores project_root after activate() is called
            project_root = getattr(self, 'project_root', None) or Path.cwd()
            
            # Update README.md
            readme_path = project_root / "README.md"
            if readme_path.exists():
                try:
                    readme_content = readme_path.read_text(encoding="utf-8")
                    
                    # Update agent count (find pattern like "Workflow Agents (13)" or "13 (fixed)")
                    import re
                    # Pattern 1: "Workflow Agents (13)"
                    pattern1 = r"Workflow Agents\s*\((\d+)\)"
                    match1 = re.search(pattern1, readme_content)
                    if match1:
                        current_count = int(match1.group(1))
                        new_count = current_count + 1
                        readme_content = re.sub(
                            pattern1,
                            f"Workflow Agents ({new_count})",
                            readme_content
                        )
                    
                    # Pattern 2: "13 (fixed)" in table
                    pattern2 = r"(\d+)\s*\(fixed\)"
                    match2 = re.search(pattern2, readme_content)
                    if match2:
                        current_count = int(match2.group(1))
                        new_count = current_count + 1
                        readme_content = re.sub(
                            pattern2,
                            f"{new_count} (fixed)",
                            readme_content,
                            count=1
                        )
                    
                    # Add agent to agent list if not present
                    agent_name.title()
                    if f"- **Evaluation**: {agent_name}" not in readme_content and \
                       "- evaluator" not in readme_content.lower():
                        # Find the last agent in the list and add after it
                        # Look for pattern like "- **Enhancement**: enhancer"
                        last_agent_pattern = r"(- \*\*[^\*]+\*\*: [^\n]+)"
                        matches = list(re.finditer(last_agent_pattern, readme_content))
                        if matches:
                            last_match = matches[-1]
                            insert_pos = last_match.end()
                            new_line = f"\n- **Evaluation**: {agent_name} ✅ (Framework Effectiveness Analysis & Continuous Improvement)"
                            readme_content = readme_content[:insert_pos] + new_line + readme_content[insert_pos:]
                    
                    readme_path.write_text(readme_content, encoding="utf-8")
                    results["readme_updated"] = True
                except Exception as e:
                    results["errors"].append(f"README.md update failed: {e}")
            
            # Update API.md
            api_path = project_root / "docs" / "API.md"
            if api_path.exists():
                try:
                    api_content = api_path.read_text(encoding="utf-8")
                    
                    # Add agent to subcommands list
                    if f"`{agent_name}`" not in api_content:
                        # Find the agent subcommands line
                        subcommands_pattern = r"(\*\*Agent subcommands\*\*: `[^`]+`)"
                        match = re.search(subcommands_pattern, api_content)
                        if match:
                            subcommands_text = match.group(1)
                            # Add agent name before the closing backtick
                            new_subcommands = subcommands_text[:-1] + f", `{agent_name}`" + subcommands_text[-1]
                            api_content = api_content.replace(subcommands_text, new_subcommands)
                    
                    api_path.write_text(api_content, encoding="utf-8")
                    results["api_updated"] = True
                except Exception as e:
                    results["errors"].append(f"API.md update failed: {e}")
            
            # Update ARCHITECTURE.md
            arch_path = project_root / "docs" / "ARCHITECTURE.md"
            if arch_path.exists():
                try:
                    arch_content = arch_path.read_text(encoding="utf-8")
                    
                    # Update agent count
                    arch_pattern = r"fixed set of (\d+) SDLC-oriented agents"
                    arch_match = re.search(arch_pattern, arch_content)
                    if arch_match:
                        current_count = int(arch_match.group(1))
                        new_count = current_count + 1
                        arch_content = re.sub(
                            arch_pattern,
                            f"fixed set of {new_count} SDLC-oriented agents",
                            arch_content
                        )
                    
                    # Add agent to agent list
                    if f"- {agent_name}" not in arch_content:
                        # Find the agents list section
                        agents_list_pattern = r"(Agents:\s*\n\s*- [^\n]+\n(?:\s+- [^\n]+\n)*)"
                        agents_match = re.search(agents_list_pattern, arch_content)
                        if agents_match:
                            agents_list = agents_match.group(1)
                            # Add new agent at the end
                            new_agent_line = f"- {agent_name}\n"
                            arch_content = arch_content.replace(agents_list, agents_list + new_agent_line)
                    
                    arch_path.write_text(arch_content, encoding="utf-8")
                    results["architecture_updated"] = True
                except Exception as e:
                    results["errors"].append(f"ARCHITECTURE.md update failed: {e}")
            
            # Update agent-capabilities.mdc
            capabilities_path = project_root / ".cursor" / "rules" / "agent-capabilities.mdc"
            if capabilities_path.exists():
                try:
                    capabilities_content = capabilities_path.read_text(encoding="utf-8")
                    
                    # Update agent count
                    cap_pattern = r"(\d+) specialized workflow agents"
                    cap_match = re.search(cap_pattern, capabilities_content)
                    if cap_match:
                        current_count = int(cap_match.group(1))
                        new_count = current_count + 1
                        capabilities_content = re.sub(
                            cap_pattern,
                            f"{new_count} specialized workflow agents",
                            capabilities_content
                        )
                    
                    # Add agent to agent list if not present
                    if f"- **Evaluation**: {agent_name}" not in capabilities_content:
                        # Find the last agent in the list
                        last_agent_pattern = r"(- \*\*[^\*]+\*\*: [^\n]+)"
                        matches = list(re.finditer(last_agent_pattern, capabilities_content))
                        if matches:
                            last_match = matches[-1]
                            insert_pos = last_match.end()
                            new_line = f"\n- **Evaluation**: {agent_name}"
                            capabilities_content = capabilities_content[:insert_pos] + new_line + capabilities_content[insert_pos:]
                    
                    capabilities_path.write_text(capabilities_content, encoding="utf-8")
                    results["capabilities_updated"] = True
                except Exception as e:
                    results["errors"].append(f"agent-capabilities.mdc update failed: {e}")
            
        except Exception as e:
            results["errors"].append(f"Documentation update failed: {e}")
        
        results["success"] = len(results["errors"]) == 0
        return results

    def _help(self) -> dict[str, Any]:
        """
        Return help information for Documenter Agent.
        
        Returns standardized help format with commands and usage examples.
        
        Returns:
            dict: Help information with standardized format:
                - type (str): Always "help"
                - content (str): Formatted help text containing:
                    - Available commands (from format_help())
                    - Usage examples for document, generate-docs, update-readme,
                      update-docstrings, and generate-project-docs commands
                      
        Note:
            This method is synchronous as it performs no I/O operations.
            Called via agent.run("help") which handles async context.
            Uses BaseAgent.format_help() which caches command list for performance.
        """
        # Optimize string building by using list and join
        examples = [
            "  *document code.py --output-format markdown",
            "  *generate-docs utils.py",
            "  *update-readme",
            "  *update-docstrings code.py --write-file",
            "  *generate-project-docs --output-dir docs/api",
        ]
        help_text = "\n".join([self.format_help(), "\nExamples:", *examples])
        return {"type": "help", "content": help_text}

    async def close(self):
        """Close agent and clean up resources."""
