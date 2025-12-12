"""
AST Parser - Extracts code structure for tiered context.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FunctionInfo:
    """Information about a function."""

    name: str
    line: int
    signature: str
    args: list[str]
    returns: str | None = None
    docstring: str | None = None


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    line: int
    bases: list[str]
    methods: list[str]
    docstring: str | None = None


@dataclass
class ModuleInfo:
    """Information about a module."""

    imports: list[str]
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    constants: list[tuple[str, Any]]
    docstring: str | None = None


class ASTParser:
    """Parses Python code to extract structured information for tiered context."""

    def __init__(self):
        self._cache: dict[str, ModuleInfo] = {}

    def parse_file(self, file_path: Path, use_cache: bool = True) -> ModuleInfo:
        """
        Parse a Python file and extract module information.

        Args:
            file_path: Path to the Python file
            use_cache: Whether to use cached results

        Returns:
            ModuleInfo with extracted structure
        """
        file_str = str(file_path)

        # Check cache
        if use_cache and file_str in self._cache:
            return self._cache[file_str]

        # Read and parse file
        try:
            code = file_path.read_text(encoding="utf-8")
            tree = ast.parse(code, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            # Return empty module info for invalid files
            return ModuleInfo(imports=[], functions=[], classes=[], constants=[])

        # Extract information
        module_info = self._extract_module_info(tree, code)

        # Cache result
        if use_cache:
            self._cache[file_str] = module_info

        return module_info

    def _extract_module_info(self, tree: ast.Module, code: str) -> ModuleInfo:
        """Extract module information from AST."""
        imports: list[str] = []
        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        constants: list[tuple[str, Any]] = []
        docstring: str | None = None

        # Check for module docstring (Python 3.8+ uses ast.Constant)
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant) and isinstance(
                tree.body[0].value.value, str
            ):
                docstring = tree.body[0].value.value

        # Extract from AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
            elif isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, code)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, tree)
                classes.append(class_info)
            elif isinstance(node, ast.Assign):
                # Extract constants (simple assignments)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        try:
                            value = ast.literal_eval(node.value)
                            constants.append((target.id, value))
                        except (ValueError, SyntaxError):
                            pass

        return ModuleInfo(
            imports=imports,
            functions=functions,
            classes=classes,
            constants=constants,
            docstring=docstring,
        )

    def _extract_function_info(self, node: ast.FunctionDef, code: str) -> FunctionInfo:
        """Extract function information from AST node."""
        # Get function signature
        args = [arg.arg for arg in node.args.args]
        signature = f"def {node.name}({', '.join(args)})"

        # Get return type annotation
        returns = None
        if node.returns:
            returns = (
                ast.unparse(node.returns)
                if hasattr(ast, "unparse")
                else str(node.returns)
            )

        # Get docstring
        docstring = ast.get_docstring(node)

        return FunctionInfo(
            name=node.name,
            line=node.lineno,
            signature=signature,
            args=args,
            returns=returns,
            docstring=docstring,
        )

    def _extract_class_info(self, node: ast.ClassDef, tree: ast.AST) -> ClassInfo:
        """Extract class information from AST node."""
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif hasattr(ast, "unparse"):
                bases.append(ast.unparse(base))
            else:
                bases.append(str(base))

        # Get methods
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        # Get docstring
        docstring = ast.get_docstring(node)

        return ClassInfo(
            name=node.name,
            line=node.lineno,
            bases=bases,
            methods=methods,
            docstring=docstring,
        )

    def clear_cache(self):
        """Clear the parser cache."""
        self._cache.clear()

    def get_file_structure(self, file_path: Path) -> dict[str, Any]:
        """
        Get file structure summary (Tier 1 compatible).

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file structure
        """
        module_info = self.parse_file(file_path)

        return {
            "file": str(file_path),
            "imports": module_info.imports,
            "classes": [
                {
                    "name": cls.name,
                    "line": cls.line,
                    "bases": cls.bases,
                    "methods": cls.methods,
                }
                for cls in module_info.classes
            ],
            "functions": [
                {
                    "name": func.name,
                    "line": func.line,
                    "signature": func.signature,
                    "args": func.args,
                    "returns": func.returns,
                }
                for func in module_info.functions
            ],
            "docstring": module_info.docstring,
        }
