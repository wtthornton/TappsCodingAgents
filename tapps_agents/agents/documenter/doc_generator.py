"""
Document Generator - Generates documentation from code
"""

import ast
from pathlib import Path
from typing import Any

from ...core.mal import MAL


class DocGenerator:
    """Generates documentation from code analysis using LLM."""

    def __init__(self, mal: MAL):
        self.mal = mal

    async def generate_api_docs(
        self, file_path: Path, output_format: str = "markdown"
    ) -> str:
        """
        Generate API documentation for a file.

        Args:
            file_path: Path to the source code file
            output_format: Output format (markdown/rst/html)

        Returns:
            Generated documentation as string
        """
        code = file_path.read_text(encoding="utf-8")

        # Analyze code structure
        structure = self._analyze_code_structure(code)

        # Build prompt for API docs
        prompt = self._build_api_docs_prompt(code, structure, output_format)

        # Generate documentation
        docs = await self.mal.generate(prompt)

        return docs

    async def generate_readme(
        self, project_root: Path, context: str | None = None
    ) -> str:
        """
        Generate README.md for a project.

        Args:
            project_root: Project root directory
            context: Optional additional context

        Returns:
            Generated README content
        """
        # Analyze project structure
        project_info = self._analyze_project_structure(project_root)

        # Build prompt for README
        prompt = self._build_readme_prompt(project_info, context)

        # Generate README
        readme = await self.mal.generate(prompt)

        return readme

    async def update_docstrings(
        self, file_path: Path, docstring_format: str = "google"
    ) -> str:
        """
        Update or add docstrings to code.

        Args:
            file_path: Path to the source code file
            docstring_format: Docstring format (google/numpy/sphinx)

        Returns:
            Updated code with docstrings
        """
        code = file_path.read_text(encoding="utf-8")

        # Analyze code structure
        structure = self._analyze_code_structure(code)

        # Build prompt for docstring generation
        prompt = self._build_docstring_prompt(code, structure, docstring_format)

        # Generate updated code
        updated_code = await self.mal.generate(prompt)

        return updated_code

    def _analyze_code_structure(self, code: str) -> dict[str, Any]:
        """Analyze code structure to extract functions, classes, etc."""
        structure = {
            "file_name": "",
            "functions": [],
            "classes": [],
            "modules": [],
            "has_docstrings": False,
        }

        try:
            tree = ast.parse(code)

            # Check for module docstring
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Str)
            ):
                structure["has_docstrings"] = True

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    has_doc = ast.get_docstring(node) is not None
                    structure["functions"].append(
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
                    structure["classes"].append(
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
        info = {
            "name": project_root.name,
            "has_readme": (project_root / "README.md").exists(),
            "has_requirements": (project_root / "requirements.txt").exists(),
            "has_setup": (project_root / "setup.py").exists(),
            "python_files": [],
            "directories": [],
        }

        # Find Python files
        for py_file in project_root.rglob("*.py"):
            if "test" not in str(py_file) and "__pycache__" not in str(py_file):
                info["python_files"].append(str(py_file.relative_to(project_root)))

        # Find directories
        for dir_path in project_root.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith("."):
                info["directories"].append(dir_path.name)

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
