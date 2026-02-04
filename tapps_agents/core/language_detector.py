"""
Language Detection System - Detect programming languages from files and projects

Phase 1.1: Multi-Language Support Engine
"""

from __future__ import annotations

import json
import logging
import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Language(StrEnum):
    """Supported programming languages."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    REACT = "react"  # .tsx, .jsx files
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    RUST = "rust"
    GO = "go"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    HTML = "html"
    CSS = "css"
    SHELL = "shell"
    POWERSHELL = "powershell"
    DOCKERFILE = "dockerfile"
    XML = "xml"
    UNKNOWN = "unknown"


class LanguageDetectionResult(BaseModel):
    """Result of language detection."""

    language: Language
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence (0.0-1.0)")
    method: str = Field(description="Detection method used")
    project_language: Language | None = Field(
        default=None, description="Primary language detected at project level"
    )


class LanguageDetector:
    """
    Detect programming language from file path, content, and project configuration.

    Uses multiple detection strategies:
    1. File extension (fastest, most reliable)
    2. Content-based analysis (fallback for ambiguous cases)
    3. Project-level configuration (package.json, tsconfig.json, pyproject.toml)
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize language detector.

        Args:
            project_root: Root directory of the project for project-level detection
        """
        self.project_root = project_root or Path.cwd()
        self._cache: dict[str, LanguageDetectionResult] = {}
        self._project_language: Language | None = None

    def detect_language(
        self, file_path: Path, content: str | None = None
    ) -> LanguageDetectionResult:
        """
        Detect language for a file.

        Args:
            file_path: Path to the file
            content: Optional file content for content-based detection

        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Strategy 1: File extension (most reliable)
        extension_result = self._detect_from_extension(file_path)
        if extension_result.confidence >= 0.9:
            self._cache[cache_key] = extension_result
            return extension_result

        # Strategy 2: Content-based detection (if content provided)
        if content:
            content_result = self._detect_from_content(content, file_path)
            if content_result.confidence > extension_result.confidence:
                self._cache[cache_key] = content_result
                return content_result

        # Strategy 3: Project-level configuration
        project_result = self._detect_from_project(file_path)
        if project_result and project_result.confidence > extension_result.confidence:
            self._cache[cache_key] = project_result
            return project_result

        # Return extension result (fallback)
        self._cache[cache_key] = extension_result
        return extension_result

    def _detect_from_extension(self, file_path: Path) -> LanguageDetectionResult:
        """Detect language from file extension."""
        suffix = file_path.suffix.lower()

        # Extension mapping
        extension_map: dict[str, Language] = {
            ".py": Language.PYTHON,
            ".ts": Language.TYPESCRIPT,
            ".tsx": Language.REACT,  # React TypeScript
            ".js": Language.JAVASCRIPT,
            ".jsx": Language.REACT,  # React JavaScript
            ".java": Language.JAVA,
            ".cpp": Language.CPP,
            ".cc": Language.CPP,
            ".cxx": Language.CPP,
            ".c": Language.C,
            ".rs": Language.RUST,
            ".go": Language.GO,
            ".rb": Language.RUBY,
            ".php": Language.PHP,
            ".swift": Language.SWIFT,
            ".kt": Language.KOTLIN,
            ".md": Language.MARKDOWN,
            ".yaml": Language.YAML,
            ".yml": Language.YAML,
            ".json": Language.JSON,
            ".xml": Language.XML,
            ".html": Language.HTML,
            ".htm": Language.HTML,
            ".css": Language.CSS,
            ".sh": Language.SHELL,
            ".bash": Language.SHELL,
            ".zsh": Language.SHELL,
            ".ps1": Language.POWERSHELL,
            ".psm1": Language.POWERSHELL,
            ".dockerfile": Language.DOCKERFILE,
        }

        language = extension_map.get(suffix, Language.UNKNOWN)
        confidence = 1.0 if language != Language.UNKNOWN else 0.0

        return LanguageDetectionResult(
            language=language,
            confidence=confidence,
            method="extension",
            project_language=self._get_project_language(),
        )

    def _detect_from_content(self, content: str, file_path: Path) -> LanguageDetectionResult:
        """Detect language from file content (fallback method)."""
        content.lower()

        # TypeScript/JavaScript patterns
        if re.search(r"\b(import|export)\s+.*from\s+['\"]", content):
            # Check for TypeScript-specific patterns
            if re.search(r":\s*(string|number|boolean|object|any|void)", content):
                return LanguageDetectionResult(
                    language=Language.TYPESCRIPT,
                    confidence=0.8,
                    method="content",
                    project_language=self._get_project_language(),
                )
            # Check for React patterns
            if re.search(r"import.*from\s+['\"]react['\"]", content) or re.search(
                r"<[A-Z]\w+", content
            ):
                if file_path.suffix.lower() in [".tsx", ".jsx"]:
                    return LanguageDetectionResult(
                        language=Language.REACT,
                        confidence=0.9,
                        method="content",
                        project_language=self._get_project_language(),
                    )
            return LanguageDetectionResult(
                language=Language.JAVASCRIPT,
                confidence=0.7,
                method="content",
                project_language=self._get_project_language(),
            )

        # Python patterns
        if re.search(r"\b(def|class|import|from)\s+\w+", content):
            return LanguageDetectionResult(
                language=Language.PYTHON,
                confidence=0.8,
                method="content",
                project_language=self._get_project_language(),
            )

        # YAML patterns
        if content.strip().startswith("---") or re.search(r"^\s*\w+:\s", content, re.MULTILINE):
            return LanguageDetectionResult(
                language=Language.YAML,
                confidence=0.7,
                method="content",
                project_language=self._get_project_language(),
            )

        # Default to unknown
        return LanguageDetectionResult(
            language=Language.UNKNOWN,
            confidence=0.0,
            method="content",
            project_language=self._get_project_language(),
        )

    def _detect_from_project(self, file_path: Path) -> LanguageDetectionResult | None:
        """Detect language from project configuration files."""
        project_lang = self._get_project_language()
        if project_lang and project_lang != Language.UNKNOWN:
            # Use project language with medium confidence
            return LanguageDetectionResult(
                language=project_lang,
                confidence=0.6,
                method="project",
                project_language=project_lang,
            )
        return None

    def _get_project_language(self) -> Language | None:
        """Detect primary language from project configuration files."""
        if self._project_language is not None:
            return self._project_language

        # Check for package.json (TypeScript/JavaScript project)
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    # Check for TypeScript
                    if (self.project_root / "tsconfig.json").exists():
                        self._project_language = Language.TYPESCRIPT
                        return Language.TYPESCRIPT
                    # Check for React
                    deps = data.get("dependencies", {}) | data.get("devDependencies", {})
                    if "react" in deps:
                        self._project_language = Language.REACT
                        return Language.REACT
                    self._project_language = Language.JAVASCRIPT
                    return Language.JAVASCRIPT
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Failed to parse package.json for language detection: {e}")

        # Check for pyproject.toml or setup.py (Python project)
        if (
            (self.project_root / "pyproject.toml").exists()
            or (self.project_root / "setup.py").exists()
            or (self.project_root / "requirements.txt").exists()
        ):
            self._project_language = Language.PYTHON
            return Language.PYTHON

        # Check for tsconfig.json (TypeScript project)
        if (self.project_root / "tsconfig.json").exists():
            self._project_language = Language.TYPESCRIPT
            return Language.TYPESCRIPT

        self._project_language = Language.UNKNOWN
        return Language.UNKNOWN

    def detect_primary_language(self) -> Language:
        """
        Detect the primary language of the project.

        Returns:
            Primary language detected from project configuration
        """
        return self._get_project_language() or Language.UNKNOWN

    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self._cache.clear()
        self._project_language = None

