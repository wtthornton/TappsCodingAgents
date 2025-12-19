"""
Document Generator - Prepares documentation generation instructions for Cursor Skills
"""

import ast
from pathlib import Path
from typing import Any

from ...core.instructions import DocumentationInstruction


class DocGenerator:
    """Prepares documentation generation instructions for Cursor Skills execution."""

    def __init__(self):
        """Initialize document generator."""
        pass

    def prepare_api_docs(
        self, file_path: Path, output_format: str = "markdown"
    ) -> DocumentationInstruction:
        """
        Prepare API documentation generation instruction for Cursor Skills.

        Args:
            file_path: Path to the source code file
            output_format: Output format (markdown/rst/html)

        Returns:
            DocumentationInstruction object for Cursor Skills execution
        """
        return DocumentationInstruction(
            target_file=str(file_path),
            output_dir=None,
            docstring_format="google",
            include_examples=True,
        )

    def prepare_readme(
        self, project_root: Path, context: str | None = None
    ) -> DocumentationInstruction:
        """
        Prepare README generation instruction for Cursor Skills.

        Args:
            project_root: Project root directory
            context: Optional additional context

        Returns:
            DocumentationInstruction object for Cursor Skills execution
        """
        readme_path = project_root / "README.md"
        return DocumentationInstruction(
            target_file=str(readme_path),
            output_dir=str(project_root),
            docstring_format="markdown",
            include_examples=True,
        )

    def prepare_docstring_update(
        self, file_path: Path, docstring_format: str = "google"
    ) -> DocumentationInstruction:
        """
        Prepare docstring update instruction for Cursor Skills.

        Args:
            file_path: Path to the source code file
            docstring_format: Docstring format (google/numpy/sphinx)

        Returns:
            DocumentationInstruction object for Cursor Skills execution
        """
        return DocumentationInstruction(
            target_file=str(file_path),
            output_dir=None,
            docstring_format=docstring_format,
            include_examples=True,
        )

    def _analyze_code_structure(self, code: str) -> dict[str, Any]:
        """Analyze code structure to extract functions, classes, etc."""
        functions: list[dict[str, Any]] = []
        classes: list[dict[str, Any]] = []
        modules: list[str] = []

        structure: dict[str, Any] = {
            "file_name": "",
            "functions": functions,
            "classes": classes,
            "modules": modules,
            "has_docstrings": False,
        }

        try:
            tree = ast.parse(code)

            # Check for module docstring
            if tree.body and isinstance(tree.body[0], ast.Expr):
                if isinstance(tree.body[0].value, ast.Constant) and isinstance(
                    tree.body[0].value.value, str
                ):
                    structure["has_docstrings"] = True

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    has_doc = ast.get_docstring(node) is not None
                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "args": args,
                            "has_docstring": has_doc,
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    methods = [
                        n.name for n in node.body if isinstance(n, ast.FunctionDef)
                    ]
                    has_doc = ast.get_docstring(node) is not None
                    classes.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "methods": methods,
                            "has_docstring": has_doc,
                        }
                    )
        except SyntaxError:
            pass

        return structure

    def _analyze_project_structure(self, project_root: Path) -> dict[str, Any]:
        """Analyze project structure."""
        python_files: list[str] = []
        directories: list[str] = []
        info: dict[str, Any] = {
            "name": project_root.name,
            "has_readme": (project_root / "README.md").exists(),
            "has_requirements": (project_root / "requirements.txt").exists(),
            "has_setup": (project_root / "setup.py").exists(),
            "python_files": python_files,
            "directories": directories,
        }

        # Find Python files
        for py_file in project_root.rglob("*.py"):
            if "test" not in str(py_file) and "__pycache__" not in str(py_file):
                python_files.append(str(py_file.relative_to(project_root)))

        # Find directories
        for dir_path in project_root.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith("."):
                directories.append(dir_path.name)

        return info

    def _build_api_docs_prompt(
        self, code: str, structure: dict[str, Any], output_format: str
    ) -> str:
        """Build prompt for API documentation generation."""
        prompt_parts = [
            f"Generate {output_format.upper()} API documentation for the following Python code.",
            "",
            "Code structure:",
            f"- Functions: {len(structure['functions'])}",
            f"- Classes: {len(structure['classes'])}",
            "",
            "Code:",
            "```python",
            code[:5000],  # Limit code size
            "```",
            "",
            f"Generate comprehensive API documentation in {output_format} format:",
            "- Document all public functions and classes",
            "- Include parameter descriptions",
            "- Include return value descriptions",
            "- Include usage examples if relevant",
            "- Use clear section headers",
            "",
        ]

        if output_format == "markdown":
            prompt_parts.append(
                "Format as Markdown with headers (##), code blocks, and lists."
            )
        elif output_format == "rst":
            prompt_parts.append("Format as reStructuredText with proper directives.")

        return "\n".join(prompt_parts)

    def _build_readme_prompt(
        self, project_info: dict[str, Any], context: str | None
    ) -> str:
        """Build prompt for README generation."""
        prompt_parts = [
            f"Generate a comprehensive README.md for the project: {project_info['name']}",
            "",
            "Project structure:",
            f"- Python files: {len(project_info['python_files'])}",
            f"- Directories: {', '.join(project_info['directories'][:10])}",
            "",
        ]

        if context:
            prompt_parts.append("Additional context:")
            prompt_parts.append(context)
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "Generate a README.md with:",
                "1. Project title and description",
                "2. Installation instructions",
                "3. Usage examples",
                "4. API overview (if applicable)",
                "5. Contributing guidelines",
                "6. License information (if known)",
                "",
                "Use Markdown format with proper headers, code blocks, and lists.",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_docstring_prompt(
        self, code: str, structure: dict[str, Any], docstring_format: str
    ) -> str:
        """Build prompt for docstring generation."""
        functions_without_docs = [
            f["name"] for f in structure["functions"] if not f["has_docstring"]
        ]
        classes_without_docs = [
            c["name"] for c in structure["classes"] if not c["has_docstring"]
        ]

        prompt_parts = [
            f"Add or update docstrings to the following Python code using {docstring_format} format.",
            "",
            "Functions needing docstrings:",
            ", ".join(functions_without_docs) if functions_without_docs else "None",
            "",
            "Classes needing docstrings:",
            ", ".join(classes_without_docs) if classes_without_docs else "None",
            "",
            "Code:",
            "```python",
            code[:5000],  # Limit code size
            "```",
            "",
            "Requirements:",
            f"- Use {docstring_format} docstring format",
            "- Include parameter descriptions with types",
            "- Include return value descriptions",
            "- Include brief summary",
            "- Include examples if complex",
            "",
            "Return the complete updated code with docstrings:",
        ]

        return "\n".join(prompt_parts)

    async def generate_project_api_docs(
        self,
        project_root: Path,
        output_dir: Path,
        output_format: str = "markdown",
        include_modules: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate project-level API documentation for multiple modules.

        Args:
            project_root: Root directory of the project
            output_dir: Directory to write documentation files
            output_format: Output format (markdown/rst/html)
            include_modules: Optional list of module paths to include (relative to project_root)

        Returns:
            Dictionary with generation results including index path and generated files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine which modules to document
        if include_modules:
            module_paths = [project_root / mod for mod in include_modules]
        else:
            # Default: document key agents and workflow engine modules
            module_paths = self._find_key_modules(project_root)

        generated_files: list[str] = []
        module_docs: dict[str, str] = {}

        # Generate docs for each module
        for module_path in module_paths:
            if not module_path.exists() or not module_path.is_file():
                continue

            # Skip test files and private modules
            if "test" in str(module_path) or "__pycache__" in str(module_path):
                continue

            try:
                # Generate documentation for this module
                docs = await self.generate_api_docs(module_path, output_format)

                # Determine output filename
                rel_path = module_path.relative_to(project_root)
                # Convert path to safe filename (e.g., tapps_agents/agents/reviewer/agent.py -> agents_reviewer_agent.md)
                safe_name = str(rel_path).replace("/", "_").replace("\\", "_").replace(".py", "")
                output_file = output_dir / f"{safe_name}.md"

                # Write documentation
                output_file.write_text(docs, encoding="utf-8")
                generated_files.append(str(output_file))
                module_docs[str(rel_path)] = str(output_file)

            except Exception as e:
                # Log error but continue with other modules
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to generate docs for {module_path}: {e}")

        # Generate index page
        index_content = self._generate_index_page(module_docs, output_format)
        index_path = output_dir / f"index.{'md' if output_format == 'markdown' else output_format}"
        index_path.write_text(index_content, encoding="utf-8")

        return {
            "index_file": str(index_path),
            "generated_files": generated_files,
            "module_count": len(generated_files),
        }

    def _find_key_modules(self, project_root: Path) -> list[Path]:
        """
        Find key modules to document (agents + workflow engine).

        Args:
            project_root: Project root directory

        Returns:
            List of module paths to document
        """
        modules: list[Path] = []

        # Find agent modules
        agents_dir = project_root / "tapps_agents" / "agents"
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir() and not agent_dir.name.startswith("_"):
                    agent_file = agent_dir / "agent.py"
                    if agent_file.exists():
                        modules.append(agent_file)

        # Find workflow engine modules
        workflow_dir = project_root / "tapps_agents" / "workflow"
        if workflow_dir.exists():
            key_workflow_files = [
                "executor.py",
                "parser.py",
                "state_manager.py",
                "models.py",
                "recommender.py",
            ]
            for filename in key_workflow_files:
                workflow_file = workflow_dir / filename
                if workflow_file.exists():
                    modules.append(workflow_file)

        # Find core modules
        core_dir = project_root / "tapps_agents" / "core"
        if core_dir.exists():
            key_core_files = [
                "agent_base.py",
                "config.py",
                "exceptions.py",
            ]
            for filename in key_core_files:
                core_file = core_dir / filename
                if core_file.exists():
                    modules.append(core_file)

        return modules

    def _generate_index_page(
        self, module_docs: dict[str, str], output_format: str
    ) -> str:
        """
        Generate index page linking to all module documentation.

        Args:
            module_docs: Dictionary mapping module paths to documentation file paths
            output_format: Output format (markdown/rst/html)

        Returns:
            Index page content
        """
        if output_format == "markdown":
            lines = [
                "# API Documentation Index",
                "",
                "This directory contains automatically generated API documentation for the TappsCodingAgents project.",
                "",
                "## Modules",
                "",
            ]

            # Group by category
            agents: list[tuple[str, str]] = []
            workflow: list[tuple[str, str]] = []
            core: list[tuple[str, str]] = []
            other: list[tuple[str, str]] = []

            for module_path, doc_file in module_docs.items():
                doc_filename = Path(doc_file).name
                if "agents" in module_path:
                    agents.append((module_path, doc_filename))
                elif "workflow" in module_path:
                    workflow.append((module_path, doc_filename))
                elif "core" in module_path:
                    core.append((module_path, doc_filename))
                else:
                    other.append((module_path, doc_filename))

            if agents:
                lines.append("### Agents")
                lines.append("")
                for module_path, doc_filename in sorted(agents):
                    agent_name = Path(module_path).stem
                    lines.append(f"- [{agent_name}]({doc_filename}) - `{module_path}`")
                lines.append("")

            if workflow:
                lines.append("### Workflow Engine")
                lines.append("")
                for module_path, doc_filename in sorted(workflow):
                    module_name = Path(module_path).stem
                    lines.append(f"- [{module_name}]({doc_filename}) - `{module_path}`")
                lines.append("")

            if core:
                lines.append("### Core")
                lines.append("")
                for module_path, doc_filename in sorted(core):
                    module_name = Path(module_path).stem
                    lines.append(f"- [{module_name}]({doc_filename}) - `{module_path}`")
                lines.append("")

            if other:
                lines.append("### Other")
                lines.append("")
                for module_path, doc_filename in sorted(other):
                    module_name = Path(module_path).stem
                    lines.append(f"- [{module_name}]({doc_filename}) - `{module_path}`")
                lines.append("")

            lines.append("---")
            lines.append("")
            lines.append("*Generated automatically by TappsCodingAgents Documenter Agent*")

            return "\n".join(lines)
        else:
            # For other formats, return a simple text index
            lines = ["API Documentation Index", "", "Generated modules:"]
            for module_path, doc_file in sorted(module_docs.items()):
                lines.append(f"  - {module_path} -> {doc_file}")
            return "\n".join(lines)
