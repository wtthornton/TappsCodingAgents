"""
Documenter Agent - Generates documentation
"""

from pathlib import Path
from typing import Any

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

        # Initialize doc generator (no MAL dependency)
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
            ]
        )
        return commands

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute a command."""
        if command == "document":
            return await self.document_command(**kwargs)
        elif command == "generate-docs":
            return await self.generate_docs_command(**kwargs)
        elif command == "update-readme":
            return await self.update_readme_command(**kwargs)
        elif command == "update-docstrings":
            return await self.update_docstrings_command(**kwargs)
        elif command == "generate-project-docs":
            return await self.generate_project_docs_command(**kwargs)
        elif command == "help":
            return await self._help()
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

    async def _help(self) -> dict[str, Any]:
        """Generate help text."""
        help_text = self.format_help()
        help_text += "\n\nExamples:\n"
        help_text += "  *document code.py --output-format markdown\n"
        help_text += "  *generate-docs utils.py\n"
        help_text += "  *update-readme\n"
        help_text += "  *update-docstrings code.py --write-file\n"
        help_text += "  *generate-project-docs --output-dir docs/api\n"
        return {"type": "help", "content": help_text}

    async def close(self):
        """Close agent and clean up resources."""
