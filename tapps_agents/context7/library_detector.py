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
        # Detect internal project modules to filter them out
        self._internal_modules = self._detect_internal_modules()

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
                        # Filter out standard library and internal modules
                        if not self._is_stdlib(lib_name) and not self._is_internal_module(lib_name):
                            libraries.add(lib_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Extract top-level package name
                        lib_name = node.module.split(".")[0]
                        # Filter out standard library and internal modules
                        if not self._is_stdlib(lib_name) and not self._is_internal_module(lib_name):
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
            if not self._is_stdlib(lib_name) and not self._is_internal_module(lib_name):
                libraries.add(lib_name)

        # require() patterns
        require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        matches = re.findall(require_pattern, code)
        for match in matches:
            lib_name = match.split("/")[0].replace("@", "")
            if not self._is_stdlib(lib_name) and not self._is_internal_module(lib_name):
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
                    if not self._is_stdlib(lib_name) and not self._is_internal_module(lib_name):
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

    def _detect_internal_modules(self) -> set[str]:
        """
        Detect internal project modules to filter them out from library detection.
        
        Returns:
            Set of internal module names (e.g., 'tapps_agents', 'core', 'mcp', etc.)
        """
        internal_modules = set()
        
        # Check for tapps_agents package structure
        tapps_agents_dir = self.project_root / "tapps_agents"
        if tapps_agents_dir.exists():
            # Add top-level package name
            internal_modules.add("tapps_agents")
            
            # Add subdirectories that are internal modules
            for item in tapps_agents_dir.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    internal_modules.add(item.name)
        
        # Common internal module patterns
        internal_modules.update({
            "core", "mcp", "security", "uuid",  # Common internal modules
            "agents", "context7", "experts", "workflow", "cli",  # Framework modules
        })
        
        return internal_modules

    def _is_internal_module(self, lib_name: str) -> bool:
        """
        Check if library is an internal project module.
        
        Args:
            lib_name: Library name to check
            
        Returns:
            True if it's an internal module, False otherwise
        """
        return lib_name.lower() in self._internal_modules

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

    def _normalize_library_name(self, lib_name: str) -> str:
        """
        Normalize library name for Context7 lookup.
        
        Normalizations:
        - Strip submodule paths (e.g., "playwright/test" → "playwright")
        - Remove scoped package prefixes (e.g., "@types/react" → "react")
        - Convert to lowercase
        - Remove version suffixes
        
        Args:
            lib_name: Raw library name
            
        Returns:
            Normalized library name
        """
        if not lib_name:
            return ""
        
        # Remove scoped package prefixes
        normalized = lib_name.replace("@types/", "").replace("@", "")
        
        # Split on path separators and take first part (base package name)
        # Examples: "playwright/test" → "playwright", "numpy/core" → "numpy"
        if "/" in normalized:
            normalized = normalized.split("/")[0]
        elif "." in normalized and not normalized.startswith("."):
            # For Python-style imports like "django.contrib.auth", take first part
            # But preserve names like ".env" (relative imports)
            parts = normalized.split(".")
            if len(parts) > 1 and parts[0]:
                normalized = parts[0]
        
        # Remove version suffixes and special characters
        # Examples: "react@18.0.0" → "react", "vue@next" → "vue"
        normalized = re.sub(r'[@~^<=>].*$', '', normalized)
        
        # Convert to lowercase
        normalized = normalized.lower().strip()
        
        return normalized
    
    def _is_valid_library_name(self, lib_name: str) -> bool:
        """
        Validate if a library name is valid for Context7 lookup.
        
        Args:
            lib_name: Library name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not lib_name or len(lib_name) < 1:
            return False
        
        # Filter out standard library modules
        if self._is_stdlib(lib_name):
            return False
        
        # Filter out names with invalid characters for package names
        # Allow: alphanumeric, hyphens, underscores
        # Disallow: slashes (should be normalized), dots (submodules), special chars
        if re.search(r'[^a-z0-9_-]', lib_name.lower()):
            # Allow dots only if it's a known scoped package pattern
            if "/" in lib_name or lib_name.count(".") > 1:
                return False
        
        # Filter out very short names (likely false positives)
        if len(lib_name) < 2:
            return False
        
        # Filter out common false positives (generic directory/structure names)
        # 
        # Research findings (verified with Context7 MCP):
        # - Context7 uses partial/fuzzy matching, so generic names match many libraries
        # - Names like "test" match "GoogleTest", "Jest" but not a library literally called "test"
        # - These are typically project structure directories, not installed packages
        # - We filter them when detected from CODE (local dirs), but keep if in project files (real deps)
        #
        # Names we DO filter (verified as directory names, not exact library matches):
        # - "test", "tests", "testing" → matches test frameworks but not "test" itself
        # - "utils", "util" → matches sqlite-utils, etc. but not "utils" itself  
        # - "lib", "libs" → matches libSQL, libzip but not "lib" itself
        # - "src", "dist", "build" → standard build directories
        # - "main", "index" → common entry point files
        # - "views", "controllers", "routes", "handlers", "middleware" → MVC structure dirs
        # - "types", "constants", "exceptions", "errors" → common code organization dirs
        #
        # Names we DON'T filter (verified as valid libraries in Context7):
        # - "config", "models", "services" → valid library names (node-config, Foundation Models, etc.)
        # - "settings" → valid (pydantic-settings, typed-settings)
        # - "app", "server", "client", "api", "web" → can be valid libraries (Appwrite, webpack, etc.)
        #
        false_positives = {
            # Testing directories (not libraries)
            "test", "tests", "testing",
            # Utility directories (not the "utils" library itself)
            "utils", "util", "helpers", "helper",
            # Build/structure directories
            "lib", "libs", "src", "dist", "build",
            # Entry point files
            "main", "index",
            # MVC/structure directories
            "views", "view", "controllers", "controller", "routes", "route",
            "handlers", "handler", "middleware", "middlewares",
            # Code organization directories
            "types", "type", "constants", "constant", "exceptions", "exception",
            "errors", "error",
        }
        # Note: We intentionally DON'T filter "config", "models", "services", "settings",
        # "app", "server", "client", "api", "web" because Context7 has valid libraries
        # with these exact names. If detected from local directories, Context7 lookup
        # will fail gracefully (debug log only). Project file detection will catch real deps.
        if lib_name.lower() in false_positives:
            return False
        
        return True

    def detect_all(
        self,
        code: str | None = None,
        prompt: str | None = None,
        error_message: str | None = None,
        language: str = "python",
    ) -> list[str]:
        """
        Detect libraries from all available sources.
        
        Automatically normalizes and validates library names before returning.

        Args:
            code: Optional code content
            prompt: Optional prompt text
            error_message: Optional error message or stack trace
            language: Programming language

        Returns:
            Combined list of detected library names (deduplicated and normalized)
        """
        # Priority 1: Project files (most reliable - these are installed dependencies)
        project_libraries = set(self.detect_from_project_files())
        
        # Priority 2-4: Other sources (may include local directories)
        other_libraries = set()

        # From code (may include local directories, so we check against project files)
        if code:
            code_libs = self.detect_from_code(code, language)
            for lib in code_libs:
                # Only include code-detected libraries if they're also in project files
                # This filters out local directory imports like "from config import ..."
                # UNLESS they're also actual dependencies
                normalized = self._normalize_library_name(lib)
                if normalized and normalized in project_libraries:
                    other_libraries.add(normalized)
                # But if it's a well-known library, include it anyway
                # (prompt/error detection will handle explicit mentions)
                elif normalized and self._is_well_known_library(normalized):
                    other_libraries.add(normalized)

        # From prompt (explicit mentions - higher confidence)
        if prompt:
            other_libraries.update(self.detect_from_prompt(prompt))

        # From error messages (explicit mentions - higher confidence)
        if error_message:
            other_libraries.update(self.detect_from_error(error_message))

        # Combine: project libraries + other sources
        all_libraries = project_libraries | other_libraries

        # Normalize and validate all detected library names
        normalized_libraries = set()
        for lib in all_libraries:
            normalized = self._normalize_library_name(lib)
            if normalized and self._is_valid_library_name(normalized):
                normalized_libraries.add(normalized)

        return sorted(list(normalized_libraries))
    
    def _is_well_known_library(self, lib_name: str) -> bool:
        """
        Check if a library name is a well-known library (not a local directory).
        
        Args:
            lib_name: Library name to check
            
        Returns:
            True if it's a well-known library name
        """
        well_known = {
            # Python
            "fastapi", "django", "flask", "pydantic", "sqlalchemy", "pytest",
            "requests", "httpx", "aiohttp", "click", "typer", "numpy", "pandas",
            "openai", "anthropic", "yaml", "pyyaml", "pydantic", "marshmallow",
            # JavaScript/TypeScript
            "react", "vue", "angular", "express", "nextjs", "nuxt", "svelte",
            "typescript", "jest", "vitest", "playwright", "cypress", "selenium",
            "axios", "lodash", "moment", "dayjs",
            # Node.js
            "node", "npm", "yarn", "pnpm",
            # Testing
            "playwright", "puppeteer", "selenium", "cypress", "jest", "mocha",
            # Config/Infra - These ARE valid libraries in Context7
            "config", "dotenv", "env",
        }
        return lib_name.lower() in well_known

