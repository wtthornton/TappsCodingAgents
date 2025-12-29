"""
Library Detection Utility - Detect libraries from code, imports, and project files.

This module provides comprehensive library detection capabilities for Option 3
quality uplift enhancements (C1-C3, D1-D2, E2).
"""

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LibraryDetector:
    """
    Detect libraries from various sources:
    - Code content (import statements)
    - Project files (package.json, requirements.txt, pyproject.toml)
    - Prompt text (library mentions)
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize library detector.

        Args:
            project_root: Optional project root directory
        """
        self.project_root = project_root or Path.cwd()

    def detect_from_code(self, code: str, language: str = "python") -> list[str]:
        """
        Detect libraries from code content (import statements).

        Args:
            code: Code content to analyze
            language: Programming language ("python", "typescript", "javascript")

        Returns:
            List of detected library names
        """
        libraries = set()

        if language == "python":
            libraries.update(self._detect_python_imports(code))
        elif language in ("typescript", "javascript"):
            libraries.update(self._detect_js_imports(code))
        else:
            # Try both methods
            libraries.update(self._detect_python_imports(code))
            libraries.update(self._detect_js_imports(code))

        return sorted(list(libraries))

    def _detect_python_imports(self, code: str) -> set[str]:
        """Detect Python imports from code."""
        libraries = set()

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Extract top-level package name
                        lib_name = alias.name.split(".")[0]
                        # Filter out standard library
                        if not self._is_stdlib(lib_name):
                            libraries.add(lib_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Extract top-level package name
                        lib_name = node.module.split(".")[0]
                        if not self._is_stdlib(lib_name):
                            libraries.add(lib_name)
        except SyntaxError:
            # Fallback to regex for invalid syntax
            libraries.update(self._detect_imports_regex(code, "python"))

        return libraries

    def _detect_js_imports(self, code: str) -> set[str]:
        """Detect JavaScript/TypeScript imports from code."""
        libraries = set()

        # ES6 import patterns
        import_pattern = r"import\s+(?:(?:\*\s+as\s+\w+)|(?:\{[^}]*\})|(?:\w+))\s+from\s+['\"]([^'\"]+)['\"]"
        matches = re.findall(import_pattern, code)
        for match in matches:
            # Extract package name (before /)
            lib_name = match.split("/")[0].replace("@", "")
            if not self._is_stdlib(lib_name):
                libraries.add(lib_name)

        # require() patterns
        require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        matches = re.findall(require_pattern, code)
        for match in matches:
            lib_name = match.split("/")[0].replace("@", "")
            if not self._is_stdlib(lib_name):
                libraries.add(lib_name)

        return libraries

    def _detect_imports_regex(self, code: str, language: str) -> set[str]:
        """Fallback regex-based import detection."""
        libraries = set()

        if language == "python":
            # Python import patterns
            patterns = [
                r"^import\s+(\w+)",
                r"^from\s+(\w+)",
                r"import\s+(\w+)",
                r"from\s+(\w+)",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, code, re.MULTILINE)
                for match in matches:
                    lib_name = match.split(".")[0]
                    if not self._is_stdlib(lib_name):
                        libraries.add(lib_name)

        return libraries

    def _is_stdlib(self, lib_name: str) -> bool:
        """Check if library is Python standard library."""
        # Common standard library modules
        stdlib_modules = {
            "os",
            "sys",
            "json",
            "re",
            "pathlib",
            "typing",
            "collections",
            "itertools",
            "functools",
            "datetime",
            "time",
            "logging",
            "asyncio",
            "threading",
            "multiprocessing",
            "subprocess",
            "urllib",
            "http",
            "email",
            "html",
            "xml",
            "sqlite3",
            "csv",
            "io",
            "pickle",
            "base64",
            "hashlib",
            "secrets",
            "random",
            "math",
            "statistics",
            "decimal",
            "fractions",
            "array",
            "queue",
            "heapq",
            "bisect",
            "copy",
            "gc",
            "weakref",
            "types",
            "inspect",
            "traceback",
            "warnings",
            "contextlib",
            "abc",
            "atexit",
            "argparse",
            "getopt",
            "shutil",
            "tempfile",
            "glob",
            "fnmatch",
            "linecache",
            "shlex",
            "textwrap",
            "unicodedata",
            "stringprep",
            "readline",
            "rlcompleter",
            "struct",
            "codecs",
            "encodings",
            "locale",
            "gettext",
            "platform",
            "errno",
            "ctypes",
            "msilib",
            "winreg",
            "winsound",
            "posix",
            "pwd",
            "spwd",
            "grp",
            "crypt",
            "termios",
            "tty",
            "pty",
            "fcntl",
            "pipes",
            "resource",
            "nis",
            "syslog",
            "optparse",
            "imp",
            "importlib",
            "pkgutil",
            "modulefinder",
            "runpy",
            "parser",
            "ast",
            "symtable",
            "symbol",
            "token",
            "tokenize",
            "keyword",
            "tabnanny",
            "py_compile",
            "compileall",
            "dis",
            "pickletools",
            "formatter",
            "msvcrt",
            "winreg",
            "winsound",
            "posixpath",
            "ntpath",
            "genericpath",
            "nt",
            "posix",
            "pwd",
            "spwd",
            "grp",
            "crypt",
            "termios",
            "tty",
            "pty",
            "fcntl",
            "pipes",
            "resource",
            "nis",
            "syslog",
            "optparse",
            "imp",
            "importlib",
            "pkgutil",
            "modulefinder",
            "runpy",
            "parser",
            "ast",
            "symtable",
            "symbol",
            "token",
            "tokenize",
            "keyword",
            "tabnanny",
            "py_compile",
            "compileall",
            "dis",
            "pickletools",
            "formatter",
        }
        return lib_name.lower() in stdlib_modules

    def detect_from_project_files(self) -> list[str]:
        """
        Detect libraries from project dependency files.

        Returns:
            List of detected library names
        """
        libraries = set()

        # Check package.json (Node.js/TypeScript projects)
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    all_deps = {**deps, **dev_deps}
                    for dep_name in all_deps.keys():
                        # Normalize names (e.g., @types/react -> react)
                        normalized = dep_name.replace("@types/", "").replace("@", "")
                        libraries.add(normalized)
            except Exception as e:
                logger.debug(f"Failed to parse package.json: {e}")

        # Check requirements.txt (Python projects)
        requirements_txt = self.project_root / "requirements.txt"
        if requirements_txt.exists():
            try:
                with open(requirements_txt, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before == or other specifiers)
                            pkg_name = (
                                line.split("==")[0]
                                .split(">=")[0]
                                .split("<=")[0]
                                .split(">")[0]
                                .split("<")[0]
                                .strip()
                            )
                            libraries.add(pkg_name.lower())
            except Exception as e:
                logger.debug(f"Failed to parse requirements.txt: {e}")

        # Check pyproject.toml (Python projects)
        pyproject_toml = self.project_root / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                content = pyproject_toml.read_text(encoding="utf-8")
                # Simple regex-based extraction (could use tomli for better parsing)
                deps_pattern = r"dependencies\s*=\s*\[(.*?)\]"
                matches = re.findall(deps_pattern, content, re.DOTALL)
                for match in matches:
                    # Extract quoted package names
                    pkg_pattern = r"['\"]([^'\"]+)['\"]"
                    pkgs = re.findall(pkg_pattern, match)
                    for pkg in pkgs:
                        pkg_name = pkg.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        libraries.add(pkg_name.lower())
            except Exception as e:
                logger.debug(f"Failed to parse pyproject.toml: {e}")

        return sorted(list(libraries))

    def detect_from_prompt(self, prompt: str) -> list[str]:
        """
        Detect libraries mentioned in prompt text.

        Args:
            prompt: Prompt text to analyze

        Returns:
            List of detected library names
        """
        libraries = set()

        # Common library/framework keywords
        library_keywords = [
            "react",
            "vue",
            "angular",
            "fastapi",
            "django",
            "flask",
            "pytest",
            "jest",
            "vitest",
            "typescript",
            "javascript",
            "node",
            "express",
            "nextjs",
            "nuxt",
            "svelte",
            "tailwind",
            "bootstrap",
            "material-ui",
            "antd",
            "sqlalchemy",
            "prisma",
            "mongoose",
            "sequelize",
            "redis",
            "postgresql",
            "mongodb",
            "mysql",
            "sqlite",
            "pandas",
            "numpy",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "playwright",
            "selenium",
            "cypress",
            "pytest-playwright",
        ]

        prompt_lower = prompt.lower()
        for keyword in library_keywords:
            if keyword in prompt_lower:
                libraries.add(keyword)

        # Pattern-based detection
        # "using X library" or "with X framework"
        patterns = [
            r"using\s+(\w+)\s+library",
            r"with\s+(\w+)\s+framework",
            r"(\w+)\s+library",
            r"(\w+)\s+framework",
            r"(\w+)\s+package",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, prompt_lower, re.IGNORECASE)
            for match in matches:
                if not self._is_stdlib(match):
                    libraries.add(match)

        return sorted(list(libraries))

    def detect_from_error(self, error_message: str) -> list[str]:
        """
        Detect libraries from error messages and stack traces.
        
        Examples:
        - "FastAPI HTTPException" → ["fastapi"]
        - "pytest.raises" → ["pytest"]
        - "sqlalchemy.exc.IntegrityError" → ["sqlalchemy"]
        
        Args:
            error_message: Error message or stack trace to analyze
            
        Returns:
            List of detected library names
        """
        libraries = set()
        
        # Pattern matching for common error formats
        patterns = [
            r"(\w+)\.(HTTPException|ValidationError|NotFound|APIRouter|FastAPI)",  # FastAPI, Pydantic
            r"(\w+)\.(raises|fixture|mark)",  # pytest
            r"(\w+)\.(exc\.|orm\.)",  # SQLAlchemy
            r"from\s+(\w+)\s+import",  # Import statements in tracebacks
            r"(\w+)\.(core\.exceptions|db\.)",  # Django
            r"(\w+)\.(models\.|admin\.)",  # Django models/admin
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            for match in matches:
                lib_name = match[0] if isinstance(match, tuple) else match
                if not self._is_stdlib(lib_name):
                    libraries.add(lib_name.lower())
        
        # Known library error patterns
        library_errors = {
            "fastapi": ["HTTPException", "APIRouter", "FastAPI", "fastapi"],
            "pytest": ["pytest.raises", "pytest.fixture", "pytest.mark", "pytest"],
            "sqlalchemy": ["sqlalchemy.exc", "sqlalchemy.orm", "sqlalchemy"],
            "django": ["django.core.exceptions", "django.db", "django"],
            "flask": ["flask", "Flask", "flask.Flask"],
            "pydantic": ["pydantic", "ValidationError", "BaseModel"],
            "requests": ["requests", "requests.exceptions"],
            "httpx": ["httpx", "httpx.exceptions"],
            "aiohttp": ["aiohttp", "aiohttp.exceptions"],
        }
        
        error_lower = error_message.lower()
        for lib, keywords in library_errors.items():
            if any(keyword.lower() in error_lower for keyword in keywords):
                libraries.add(lib)
        
        return sorted(list(libraries))

    def detect_all(
        self,
        code: str | None = None,
        prompt: str | None = None,
        error_message: str | None = None,
        language: str = "python",
    ) -> list[str]:
        """
        Detect libraries from all available sources.

        Args:
            code: Optional code content
            prompt: Optional prompt text
            error_message: Optional error message or stack trace
            language: Programming language

        Returns:
            Combined list of detected library names (deduplicated)
        """
        libraries = set()

        # From project files
        libraries.update(self.detect_from_project_files())

        # From code
        if code:
            libraries.update(self.detect_from_code(code, language))

        # From prompt
        if prompt:
            libraries.update(self.detect_from_prompt(prompt))

        # From error messages (NEW)
        if error_message:
            libraries.update(self.detect_from_error(error_message))

        return sorted(list(libraries))

