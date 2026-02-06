"""Tech stack detector for TappsCodingAgents.

This module detects the tech stack from project dependencies and code,
including programming languages, libraries, frameworks, and domains.

Module: Phase 1.2 - Tech Stack Detector
From: docs/INIT_AUTOFILL_DETAILED_REQUIREMENTS.md
"""

import ast
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import tomli


@dataclass
class TechStack:
    """Detected tech stack."""
    languages: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    context7_priority: list[str] = field(default_factory=list)


class TechStackDetector:
    """Detects tech stack from project dependencies and code.

    This detector analyzes:
    - Programming languages from file extensions
    - Libraries from dependency files (requirements.txt, pyproject.toml, package.json, etc.)
    - Frameworks from code imports using AST parsing
    - Project domains from dependencies and structure

    Performance target: < 5 seconds for typical projects
    """

    # Language detection by file extension
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".java": "java",
        ".kt": "kotlin",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".swift": "swift",
        ".m": "objective-c",
        ".sh": "shell",
        ".bash": "shell",
        ".sql": "sql",
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Python frameworks
        "flask": "flask",
        "django": "django",
        "fastapi": "fastapi",
        "starlette": "fastapi",
        "pyramid": "pyramid",
        "tornado": "tornado",
        "sanic": "sanic",
        "aiohttp": "aiohttp",
        "bottle": "bottle",
        "cherrypy": "cherrypy",
        # JavaScript/TypeScript frameworks
        "react": "react",
        "vue": "vue",
        "angular": "angular",
        "express": "express",
        "next": "next.js",
        "nuxt": "nuxt.js",
        "svelte": "svelte",
        "nest": "nestjs",
        # Testing frameworks
        "pytest": "pytest",
        "unittest": "unittest",
        "jest": "jest",
        "mocha": "mocha",
        "jasmine": "jasmine",
        # Other frameworks
        "spring": "spring",
        "rails": "rails",
        "laravel": "laravel",
    }

    # Domain detection patterns
    DOMAIN_PATTERNS = {
        "web": ["flask", "django", "fastapi", "express", "react", "vue", "angular", "next.js"],
        "api": ["fastapi", "flask", "express", "django", "aiohttp"],
        "data": ["pandas", "numpy", "polars", "dask", "spark"],
        "ml": ["tensorflow", "pytorch", "scikit-learn", "keras", "transformers"],
        "database": ["sqlalchemy", "psycopg2", "pymongo", "redis", "elasticsearch"],
        "cloud": ["boto3", "google-cloud", "azure", "kubernetes"],
        "testing": ["pytest", "unittest", "jest", "mocha", "selenium"],
        "devops": ["docker", "kubernetes", "terraform", "ansible"],
    }

    def __init__(self, project_root: Path | None = None, max_files: int = 1000):
        """Initialize tech stack detector.

        Args:
            project_root: Root directory of project (defaults to current directory)
            max_files: Maximum number of files to analyze (performance limit)
        """
        self.project_root = project_root or Path.cwd()
        self.max_files = max_files
        self._detected_languages: set[str] = set()
        self._detected_libraries: set[str] = set()
        self._detected_frameworks: set[str] = set()
        self._detected_domains: set[str] = set()

    def detect_all(self) -> TechStack:
        """Detect complete tech stack.

        Returns:
            TechStack: Complete detected tech stack
        """
        # Detect each component
        self.detect_languages()
        self.detect_libraries()
        self.detect_frameworks()
        self.detect_domains()

        # Determine Context7 priority (most important libraries for documentation)
        context7_priority = self._determine_context7_priority()

        return TechStack(
            languages=sorted(self._detected_languages),
            libraries=sorted(self._detected_libraries),
            frameworks=sorted(self._detected_frameworks),
            domains=sorted(self._detected_domains),
            context7_priority=context7_priority
        )

    def detect_languages(self) -> list[str]:
        """Detect programming languages from file extensions.

        Returns:
            List[str]: Detected programming languages
        """
        language_counts: Counter = Counter()
        files_scanned = 0

        # Scan project files
        for ext, language in self.LANGUAGE_EXTENSIONS.items():
            pattern = f"**/*{ext}"
            for file_path in self.project_root.glob(pattern):
                # Skip virtual environments, node_modules, build directories
                if self._should_skip_path(file_path):
                    continue

                language_counts[language] += 1
                files_scanned += 1

                if files_scanned >= self.max_files:
                    break

            if files_scanned >= self.max_files:
                break

        # Keep languages with at least 3 files
        self._detected_languages = {lang for lang, count in language_counts.items() if count >= 3}
        return sorted(self._detected_languages)

    def detect_libraries(self) -> list[str]:
        """Extract libraries from dependency files.

        Parses:
        - requirements.txt
        - pyproject.toml
        - setup.py
        - package.json
        - Gemfile
        - etc.

        Returns:
            List[str]: Detected libraries
        """
        # Python: requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            self._parse_requirements_txt(req_file)

        # Python: pyproject.toml
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            self._parse_pyproject_toml(pyproject_file)

        # Python: setup.py (basic parsing)
        setup_file = self.project_root / "setup.py"
        if setup_file.exists():
            self._parse_setup_py(setup_file)

        # JavaScript: package.json
        package_file = self.project_root / "package.json"
        if package_file.exists():
            self._parse_package_json(package_file)

        return sorted(self._detected_libraries)

    def detect_frameworks(self) -> list[str]:
        """Detect frameworks from code imports using AST parsing.

        For Python files, uses AST to parse import statements.
        For JavaScript/TypeScript, uses regex patterns.

        Returns:
            List[str]: Detected frameworks
        """
        files_analyzed = 0

        # Analyze Python files
        for py_file in self.project_root.glob("**/*.py"):
            if self._should_skip_path(py_file):
                continue

            self._analyze_python_imports(py_file)
            files_analyzed += 1

            if files_analyzed >= self.max_files:
                break

        # Analyze JavaScript/TypeScript files
        for ext in [".js", ".ts", ".jsx", ".tsx"]:
            for js_file in self.project_root.glob(f"**/*{ext}"):
                if self._should_skip_path(js_file):
                    continue

                self._analyze_js_imports(js_file)
                files_analyzed += 1

                if files_analyzed >= self.max_files:
                    break

            if files_analyzed >= self.max_files:
                break

        return sorted(self._detected_frameworks)

    def detect_domains(self) -> list[str]:
        """Infer domains from dependencies and structure.

        Uses domain patterns to map libraries/frameworks to domains.

        Returns:
            List[str]: Detected project domains
        """
        # Map libraries and frameworks to domains
        all_tech = self._detected_libraries | self._detected_frameworks

        for domain, indicators in self.DOMAIN_PATTERNS.items():
            for indicator in indicators:
                if any(indicator in tech.lower() for tech in all_tech):
                    self._detected_domains.add(domain)
                    break

        # Structural heuristics
        if (self.project_root / "tests").exists() or (self.project_root / "test").exists():
            self._detected_domains.add("testing")

        if (self.project_root / "Dockerfile").exists() or (self.project_root / ".dockerignore").exists():
            self._detected_domains.add("devops")

        return sorted(self._detected_domains)

    def generate_tech_stack_yaml(self) -> dict:
        """Generate complete tech-stack.yaml configuration.

        Returns:
            dict: Complete tech-stack.yaml data
        """
        tech_stack = self.detect_all()

        return {
            "version": "1.0",
            "languages": tech_stack.languages,
            "libraries": tech_stack.libraries,
            "frameworks": tech_stack.frameworks,
            "domains": tech_stack.domains,
            "context7_priority": tech_stack.context7_priority,
            "auto_detected": True,
            "detection_timestamp": None,  # Will be filled by caller
        }

    # Private helper methods

    def _should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped during analysis."""
        skip_dirs = {
            ".git", ".venv", "venv", "env", "node_modules",
            "__pycache__", ".pytest_cache", "dist", "build",
            ".tox", ".eggs", "htmlcov", ".mypy_cache",
            ".tapps-agents", "site-packages"
        }

        # Check if any parent directory is in skip list
        return any(part in skip_dirs for part in path.parts)

    def _parse_requirements_txt(self, req_file: Path) -> None:
        """Parse requirements.txt file."""
        try:
            content = req_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Extract package name (before ==, >=, etc.)
                match = re.match(r"^([a-zA-Z0-9\-_]+)", line)
                if match:
                    package = match.group(1).lower()
                    self._detected_libraries.add(package)
        except Exception:
            pass  # Silently fail if parsing fails

    def _parse_pyproject_toml(self, pyproject_file: Path) -> None:
        """Parse pyproject.toml file."""
        try:
            content = pyproject_file.read_bytes()
            data = tomli.loads(content.decode("utf-8"))

            # Check [project.dependencies]
            if "project" in data and "dependencies" in data["project"]:
                for dep in data["project"]["dependencies"]:
                    match = re.match(r"^([a-zA-Z0-9\-_]+)", dep)
                    if match:
                        self._detected_libraries.add(match.group(1).lower())

            # Check [tool.poetry.dependencies]
            if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
                for dep in data["tool"]["poetry"]["dependencies"]:
                    if dep != "python":
                        self._detected_libraries.add(dep.lower())
        except Exception:
            pass

    def _parse_setup_py(self, setup_file: Path) -> None:
        """Parse setup.py file (basic regex-based parsing)."""
        try:
            content = setup_file.read_text(encoding="utf-8")

            # Look for install_requires
            match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if match:
                deps_str = match.group(1)
                # Extract quoted package names
                packages = re.findall(r'["\']([a-zA-Z0-9\-_]+)', deps_str)
                for pkg in packages:
                    self._detected_libraries.add(pkg.lower())
        except Exception:
            pass

    def _parse_package_json(self, package_file: Path) -> None:
        """Parse package.json file."""
        try:
            import json
            content = package_file.read_text(encoding="utf-8")
            data = json.loads(content)

            # Check dependencies and devDependencies
            for dep_type in ["dependencies", "devDependencies"]:
                if dep_type in data:
                    for package in data[dep_type].keys():
                        self._detected_libraries.add(package.lower())
        except Exception:
            pass

    def _analyze_python_imports(self, py_file: Path) -> None:
        """Analyze Python file imports using AST."""
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_framework_pattern(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._check_framework_pattern(node.module.split(".")[0])
        except Exception:
            pass  # Skip files with syntax errors

    def _analyze_js_imports(self, js_file: Path) -> None:
        """Analyze JavaScript/TypeScript imports using regex."""
        try:
            content = js_file.read_text(encoding="utf-8")

            # Match: import ... from 'package'
            imports = re.findall(r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', content)
            # Match: require('package')
            requires = re.findall(r'require\(["\']([^"\']+)["\']\)', content)

            for package in imports + requires:
                # Extract package name (before /)
                pkg_name = package.split("/")[0]
                if not pkg_name.startswith("."):
                    self._check_framework_pattern(pkg_name)
        except Exception:
            pass

    def _check_framework_pattern(self, module_name: str) -> None:
        """Check if module name matches a framework pattern."""
        module_lower = module_name.lower()
        for pattern, framework in self.FRAMEWORK_PATTERNS.items():
            if pattern in module_lower:
                self._detected_frameworks.add(framework)

    def _determine_context7_priority(self) -> list[str]:
        """Determine Context7 priority list (most important libraries).

        Returns libraries in priority order:
        1. Frameworks (highest priority)
        2. Most common libraries
        3. Domain-specific libraries
        """
        priority = []

        # Add frameworks first
        priority.extend(sorted(self._detected_frameworks))

        # Add other libraries (limit to top 20)
        other_libs = sorted(self._detected_libraries - self._detected_frameworks)
        priority.extend(other_libs[:20])

        return priority


def main() -> None:
    """CLI entry point for tech stack detection."""
    import argparse
    from datetime import datetime

    import yaml

    parser = argparse.ArgumentParser(description="Detect project tech stack")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--output", type=Path, help="Output YAML file")
    args = parser.parse_args()

    detector = TechStackDetector(project_root=args.project_root)
    result = detector.generate_tech_stack_yaml()
    result["detection_timestamp"] = datetime.now().isoformat()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False)
        print(f"Tech stack written to {args.output}")
    else:
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
