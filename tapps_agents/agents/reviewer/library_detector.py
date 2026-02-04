"""
Library Detector - Detects libraries used in code and dependency files.

Supports:
- Python import statement parsing (AST-based)
- requirements.txt parsing
- pyproject.toml parsing
"""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Standard library modules (Python 3.8+)
STDLIB_MODULES = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii",
    "bisect", "builtins", "bz2", "calendar", "collections", "collections.abc",
    "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal",
    "difflib", "dis", "doctest", "email", "encodings", "enum", "errno",
    "fcntl", "fileinput", "fnmatch", "fractions", "functools", "gc",
    "getopt", "getpass", "gettext", "glob", "graphlib", "grp", "gzip",
    "hashlib", "heapq", "html", "http", "imaplib", "importlib", "inspect",
    "io", "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "msilib", "msvcrt", "multiprocessing",
    "netrc", "nis", "nntplib", "ntpath", "nturl2path", "numbers", "opcode",
    "operator", "optparse", "os", "pathlib", "pdb", "pickle", "pickletools",
    "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath",
    "pprint", "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "runpy", "sched", "secrets", "select", "selectors", "shelve",
    "shlex", "shutil", "signal", "site", "smtplib", "sndhdr", "socket",
    "socketserver", "spwd", "sqlite3", "sre_compile", "sre_constants",
    "sre_parse", "ssl", "stat", "statistics", "string", "stringprep",
    "struct", "subprocess", "sunau", "symbol", "symtable", "sys", "sysconfig",
    "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
    "test", "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "trace", "traceback", "tracemalloc", "tty", "turtle", "types",
    "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv",
    "warnings", "wave", "weakref", "webbrowser", "winreg", "winsound",
    "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport",
    "zlib"
}


class LibraryDetector:
    """
    Detects libraries used in code and dependency files.
    
    Supports:
    - Python import statement parsing (AST-based)
    - requirements.txt parsing
    - pyproject.toml parsing
    """
    
    def __init__(
        self,
        include_stdlib: bool = False,
        detection_depth: str = "both"  # "code", "dependencies", "both"
    ):
        """
        Initialize library detector.
        
        Args:
            include_stdlib: Whether to include standard library modules
            detection_depth: What to detect ("code", "dependencies", "both")
        """
        self.include_stdlib = include_stdlib
        self.detection_depth = detection_depth
    
    def detect_from_code(self, code: str) -> list[str]:
        """
        Detect libraries from Python code using AST parsing.
        
        Args:
            code: Python source code as string
            
        Returns:
            List of library names (deduplicated)
        """
        libraries: set[str] = set()
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        lib_name = alias.name.split('.')[0]
                        if self._should_include(lib_name):
                            libraries.add(lib_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        lib_name = node.module.split('.')[0]
                        if self._should_include(lib_name):
                            libraries.add(lib_name)
        except SyntaxError:
            # Invalid Python code, return empty list
            logger.debug("Failed to parse code for library detection (syntax error)")
        except Exception as e:
            logger.warning(f"Library detection from code failed: {e}")
        
        return sorted(list(libraries))
    
    def detect_from_requirements(self, file_path: Path) -> list[str]:
        """
        Detect libraries from requirements.txt file.
        
        Args:
            file_path: Path to requirements.txt (or project root to search)
            
        Returns:
            List of library names (deduplicated)
        """
        libraries: set[str] = set()
        
        # If file_path is a file, use it directly
        # If it's a directory, look for requirements.txt in it
        if file_path.is_dir():
            req_file = file_path / "requirements.txt"
        else:
            # Look for requirements.txt in parent directory
            req_file = file_path.parent / "requirements.txt"
        
        if not req_file.exists():
            return []
        
        try:
            with open(req_file, encoding="utf-8") as f:
                for line in f:
                    package = self._parse_requirements_line(line)
                    if package and self._should_include(package):
                        libraries.add(package)
        except Exception as e:
            logger.warning(f"Failed to parse requirements.txt: {e}")
        
        return sorted(list(libraries))
    
    def detect_from_pyproject(self, file_path: Path) -> list[str]:
        """
        Detect libraries from pyproject.toml file.
        
        Args:
            file_path: Path to pyproject.toml (or project root to search)
            
        Returns:
            List of library names (deduplicated)
        """
        libraries: set[str] = set()
        
        # If file_path is a file, look for pyproject.toml in parent
        # If it's a directory, look for pyproject.toml in it
        if file_path.is_dir():
            pyproject_file = file_path / "pyproject.toml"
        else:
            pyproject_file = file_path.parent / "pyproject.toml"
        
        if not pyproject_file.exists():
            return []
        
        try:
            # Try to import tomli (Python 3.11+) or tomllib (Python 3.11+)
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                try:
                    import tomli as tomllib  # Fallback to tomli package
                except ImportError:
                    logger.debug("tomli not available, skipping pyproject.toml parsing")
                    return []
            
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)
            
            # Check [project.dependencies]
            if "project" in data and "dependencies" in data["project"]:
                for dep in data["project"]["dependencies"]:
                    package = self._parse_dependency_spec(dep)
                    if package and self._should_include(package):
                        libraries.add(package)
            
            # Check [tool.poetry.dependencies] (Poetry)
            if "tool" in data and "poetry" in data["tool"]:
                if "dependencies" in data["tool"]["poetry"]:
                    for dep_name, _dep_spec in data["tool"]["poetry"]["dependencies"].items():
                        if dep_name != "python" and self._should_include(dep_name):
                            libraries.add(dep_name)
            
        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml: {e}")
        
        return sorted(list(libraries))
    
    def detect_all(self, code: str, file_path: Path) -> list[str]:
        """
        Detect libraries from all sources (code, requirements.txt, pyproject.toml).
        
        Args:
            code: Python source code as string
            file_path: Path to the file being reviewed (used to find dependency files)
            
        Returns:
            List of library names (deduplicated, merged from all sources)
        """
        all_libraries: set[str] = set()
        
        # Detect from code if enabled
        if self.detection_depth in ("code", "both"):
            code_libs = self.detect_from_code(code)
            all_libraries.update(code_libs)
        
        # Detect from dependency files if enabled
        if self.detection_depth in ("dependencies", "both"):
            req_libs = self.detect_from_requirements(file_path)
            all_libraries.update(req_libs)
            
            pyproject_libs = self.detect_from_pyproject(file_path)
            all_libraries.update(pyproject_libs)
        
        return sorted(list(all_libraries))
    
    def _should_include(self, lib_name: str) -> bool:
        """Check if library should be included in results."""
        if not lib_name:
            return False
        
        # Filter out standard library if not including stdlib
        if not self.include_stdlib and lib_name in STDLIB_MODULES:
            return False
        
        # Filter out relative imports
        if lib_name.startswith('.'):
            return False
        
        return True
    
    def _parse_requirements_line(self, line: str) -> str | None:
        """
        Parse a single line from requirements.txt.
        
        Handles:
        - Comments (#)
        - Version specifiers (>=, ==, <=, >, <, ~=)
        - Extras ([extra], [extra1,extra2])
        - URLs and git+ URLs
        """
        # Remove comments and whitespace
        line = line.split('#')[0].strip()
        if not line:
            return None
        
        # Handle URLs (skip)
        if line.startswith(('http://', 'https://', 'git+', 'hg+', 'svn+')):
            return None
        
        # Handle version specifiers: package>=1.0.0, package==1.0.0, etc.
        # Extract just the package name
        package = line.split('>=')[0].split('==')[0].split('<=')[0]
        package = package.split('>')[0].split('<')[0].split('~=')[0]
        package = package.split('!=')[0]
        
        # Handle extras: package[extra], package[extra1,extra2]
        package = package.split('[')[0].strip()
        
        # Handle @ for URLs: package@http://...
        package = package.split('@')[0].strip()
        
        return package if package else None
    
    def _parse_dependency_spec(self, spec: str) -> str | None:
        """
        Parse a dependency specification from pyproject.toml.
        
        Handles:
        - Simple: "package"
        - With version: "package>=1.0.0"
        - With extras: "package[extra]>=1.0.0"
        """
        # Remove whitespace
        spec = spec.strip()
        if not spec:
            return None
        
        # Handle version specifiers
        package = spec.split('>=')[0].split('==')[0].split('<=')[0]
        package = package.split('>')[0].split('<')[0].split('~=')[0]
        package = package.split('!=')[0]
        
        # Handle extras
        package = package.split('[')[0].strip()
        
        return package if package else None
