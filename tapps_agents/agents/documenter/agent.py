"""
Documenter Agent - Generates documentation
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

from ...core.mal import MAL
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config, DocumenterAgentConfig
from .doc_generator import DocGenerator


class DocumenterAgent(BaseAgent):
    """
    Documenter Agent - Documentation generation.
    
    Permissions: Read, Write, Grep, Glob
    """
    
    def __init__(self, mal: Optional[MAL] = None, config: Optional[ProjectConfig] = None):
        super().__init__(agent_id="documenter", agent_name="Documenter Agent", config=config)
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config
        
        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )
        
        # Initialize doc generator
        self.doc_generator = DocGenerator(self.mal)
        
        # Get documenter config
        documenter_config = config.agents.documenter if config and config.agents else None
        self.docs_dir = Path(documenter_config.docs_dir) if documenter_config and documenter_config.docs_dir else Path("docs")
        self.include_examples = documenter_config.include_examples if documenter_config else True
        self.docstring_format = documenter_config.docstring_format if documenter_config else "google"
        
        # Ensure docs directory exists
        self.docs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Return list of available commands."""
        commands = super().get_commands()
        commands.extend([
            {"command": "*document", "description": "Generate documentation for a file"},
            {"command": "*generate-docs", "description": "Generate API documentation"},
            {"command": "*update-readme", "description": "Generate or update README.md"},
            {"command": "*update-docstrings", "description": "Update docstrings in code"}
        ])
        return commands
    
    async def run(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command."""
        if command == "document":
            return await self.document_command(**kwargs)
        elif command == "generate-docs":
            return await self.generate_docs_command(**kwargs)
        elif command == "update-readme":
            return await self.update_readme_command(**kwargs)
        elif command == "update-docstrings":
            return await self.update_docstrings_command(**kwargs)
        elif command == "help":
            return await self._help()
        else:
            return {"error": f"Unknown command: {command}"}
    
    async def document_command(
        self,
        file: str,
        output_format: str = "markdown",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
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
        
        # Generate API docs
        docs = await self.doc_generator.generate_api_docs(file_path, output_format)
        
        # Determine output file
        if output_file:
            output_path = Path(output_file)
        else:
            # Auto-generate output path
            output_path = self.docs_dir / f"{file_path.stem}_api.{'md' if output_format == 'markdown' else output_format}"
        
        # Write documentation
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(docs, encoding='utf-8')
        
        return {
            "type": "document",
            "file": str(file_path),
            "output_file": str(output_path),
            "format": output_format,
            "documentation": docs[:500] + "..." if len(docs) > 500 else docs  # Preview
        }
    
    async def generate_docs_command(
        self,
        file: Optional[str] = None,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
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
            docs = await self.doc_generator.generate_api_docs(file_path, output_format)
            
            return {
                "type": "api_docs",
                "file": str(file_path),
                "format": output_format,
                "documentation": docs
            }
        else:
            return {"error": "File path required"}
    
    async def update_readme_command(
        self,
        project_root: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
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
        
        # Generate README
        readme = await self.doc_generator.generate_readme(root_path, context)
        
        # Write README
        readme_path = root_path / "README.md"
        readme_path.write_text(readme, encoding='utf-8')
        
        return {
            "type": "readme",
            "project_root": str(root_path),
            "readme_file": str(readme_path),
            "readme": readme[:500] + "..." if len(readme) > 500 else readme  # Preview
        }
    
    async def update_docstrings_command(
        self,
        file: str,
        docstring_format: Optional[str] = None,
        write_file: bool = False
    ) -> Dict[str, Any]:
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
        
        # Generate updated code with docstrings
        updated_code = await self.doc_generator.update_docstrings(file_path, format_to_use)
        
        # Write back to file if requested
        if write_file:
            file_path.write_text(updated_code, encoding='utf-8')
        
        return {
            "type": "docstrings",
            "file": str(file_path),
            "format": format_to_use,
            "updated_code": updated_code[:1000] + "..." if len(updated_code) > 1000 else updated_code,  # Preview
            "written": write_file
        }
    
    async def _help(self) -> Dict[str, Any]:
        """Generate help text."""
        help_text = self.format_help()
        help_text += "\n\nExamples:\n"
        help_text += "  *document code.py --output-format markdown\n"
        help_text += "  *generate-docs utils.py\n"
        help_text += "  *update-readme\n"
        help_text += "  *update-docstrings code.py --write-file\n"
        return {"type": "help", "content": help_text}
    
    async def close(self):
        """Close agent and clean up resources."""
        if self.mal:
            await self.mal.close()

