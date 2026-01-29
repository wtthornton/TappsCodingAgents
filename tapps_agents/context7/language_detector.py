"""
Language Detection for Context7 Cache

Detects primary programming language from project structure to prevent
wrong-language examples in Context7 cache (e.g., Go instead of Python).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

LanguageType = Literal["python", "javascript", "typescript", "ruby", "go", "rust", "java", "csharp", "unknown"]


class LanguageDetector:
    """
    Detect project language from files and configuration.

    Priority order:
    1. pyproject.toml → Python
    2. package.json → JavaScript/TypeScript
    3. Gemfile → Ruby
    4. go.mod → Go
    5. Cargo.toml → Rust
    6. pom.xml → Java
    7. *.csproj → C#
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize language detector.

        Args:
            project_root: Project root directory. If None, uses current working directory.
        """
        self.project_root = project_root or Path.cwd()

    def detect_from_project(self, project_path: Path | None = None) -> LanguageType:
        """
        Detect primary language from project structure.

        Args:
            project_path: Path to project root. If None, uses self.project_root.

        Returns:
            Detected language: "python" | "javascript" | "typescript" | "ruby" |
                              "go" | "rust" | "java" | "csharp" | "unknown"
        """
        path = project_path or self.project_root

        # Priority 1: Python (pyproject.toml or setup.py)
        if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
            return "python"

        # Priority 2: JavaScript/TypeScript (package.json)
        if (path / "package.json").exists():
            # Check if TypeScript
            if (path / "tsconfig.json").exists() or self._has_typescript_files(path):
                return "typescript"
            return "javascript"

        # Priority 3: Ruby (Gemfile)
        if (path / "Gemfile").exists():
            return "ruby"

        # Priority 4: Go (go.mod)
        if (path / "go.mod").exists():
            return "go"

        # Priority 5: Rust (Cargo.toml)
        if (path / "Cargo.toml").exists():
            return "rust"

        # Priority 6: Java (pom.xml or build.gradle)
        if (path / "pom.xml").exists() or (path / "build.gradle").exists():
            return "java"

        # Priority 7: C# (*.csproj files)
        if list(path.glob("*.csproj")):
            return "csharp"

        # Fallback: Check for common file extensions
        return self._detect_from_file_extensions(path)

    def _has_typescript_files(self, path: Path) -> bool:
        """Check if project has TypeScript files."""
        # Check common src directories
        for src_dir in ["src", "lib", "app"]:
            src_path = path / src_dir
            if src_path.exists() and list(src_path.glob("**/*.ts")):
                return True
        return False

    def _detect_from_file_extensions(self, path: Path) -> LanguageType:
        """
        Fallback detection from file extensions.

        Counts files by extension and returns most common language.
        """
        extension_counts: dict[LanguageType, int] = {
            "python": 0,
            "javascript": 0,
            "typescript": 0,
            "ruby": 0,
            "go": 0,
            "rust": 0,
            "java": 0,
            "csharp": 0,
        }

        # Count files in common source directories
        for src_dir in ["src", "lib", "app", "pkg", "internal"]:
            src_path = path / src_dir
            if not src_path.exists():
                continue

            # Count Python files
            extension_counts["python"] += len(list(src_path.glob("**/*.py")))

            # Count JavaScript/TypeScript files
            extension_counts["javascript"] += len(list(src_path.glob("**/*.js")))
            extension_counts["javascript"] += len(list(src_path.glob("**/*.jsx")))
            extension_counts["typescript"] += len(list(src_path.glob("**/*.ts")))
            extension_counts["typescript"] += len(list(src_path.glob("**/*.tsx")))

            # Count Ruby files
            extension_counts["ruby"] += len(list(src_path.glob("**/*.rb")))

            # Count Go files
            extension_counts["go"] += len(list(src_path.glob("**/*.go")))

            # Count Rust files
            extension_counts["rust"] += len(list(src_path.glob("**/*.rs")))

            # Count Java files
            extension_counts["java"] += len(list(src_path.glob("**/*.java")))

            # Count C# files
            extension_counts["csharp"] += len(list(src_path.glob("**/*.cs")))

        # Return language with most files
        max_count = max(extension_counts.values())
        if max_count == 0:
            return "unknown"

        for lang, count in extension_counts.items():
            if count == max_count:
                return lang

        return "unknown"

    def detect_with_confidence(self, project_path: Path | None = None) -> tuple[LanguageType, float]:
        """
        Detect language with confidence score.

        Args:
            project_path: Path to project root. If None, uses self.project_root.

        Returns:
            Tuple of (language, confidence) where confidence is 0.0-1.0
        """
        path = project_path or self.project_root

        # High confidence (0.95): Project config file exists
        if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
            return ("python", 0.95)

        if (path / "package.json").exists():
            if (path / "tsconfig.json").exists():
                return ("typescript", 0.95)
            return ("javascript", 0.95)

        if (path / "Gemfile").exists():
            return ("ruby", 0.95)

        if (path / "go.mod").exists():
            return ("go", 0.95)

        if (path / "Cargo.toml").exists():
            return ("rust", 0.95)

        if (path / "pom.xml").exists() or (path / "build.gradle").exists():
            return ("java", 0.95)

        if list(path.glob("*.csproj")):
            return ("csharp", 0.95)

        # Medium confidence (0.7): Based on file extensions
        lang = self._detect_from_file_extensions(path)
        if lang != "unknown":
            return (lang, 0.7)

        # Low confidence (0.3): Unknown
        return ("unknown", 0.3)


def get_language_from_config(config_path: Path) -> LanguageType | None:
    """
    Get language from .tapps-agents/config.yaml if specified.

    Args:
        config_path: Path to config.yaml

    Returns:
        Language if specified in config, None otherwise
    """
    try:
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        if config and "context7" in config and "language" in config["context7"]:
            return config["context7"]["language"]
    except Exception:
        pass

    return None
