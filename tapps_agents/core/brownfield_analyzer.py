"""
Brownfield System Analyzer

Analyzes existing codebases to detect technologies, frameworks, and domains.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.project_profile import load_project_profile
from ..experts.domain_detector import DomainMapping, DomainStackDetector

logger = logging.getLogger(__name__)


@dataclass
class BrownfieldAnalysisResult:
    """Result of brownfield codebase analysis."""

    project_root: Path
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    domains: list[DomainMapping] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    analysis_metadata: dict[str, Any] = field(default_factory=dict)


class BrownfieldAnalyzer:
    """
    Analyzes brownfield codebase to detect technologies and domains.

    Usage:
        detector = DomainStackDetector(project_root)
        analyzer = BrownfieldAnalyzer(project_root, detector)
        result = await analyzer.analyze()
    """

    # Language detection patterns
    LANGUAGE_PATTERNS = {
        "python": [".py"],
        "typescript": [".ts", ".tsx"],
        "javascript": [".js", ".jsx"],
        "java": [".java"],
        "go": [".go"],
        "rust": [".rs"],
        "ruby": [".rb"],
        "php": [".php"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx"],
        "c": [".c", ".h"],
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "fastapi": ["fastapi", "uvicorn"],
        "django": ["django"],
        "flask": ["flask"],
        "react": ["react", "react-dom"],
        "vue": ["vue"],
        "angular": ["@angular/core"],
        "nextjs": ["next"],
        "spring": ["spring-boot", "spring-core"],
        "express": ["express"],
        "nest": ["@nestjs/core"],
    }

    def __init__(
        self,
        project_root: Path,
        domain_detector: DomainStackDetector | None = None,
    ) -> None:
        """
        Initialize analyzer.

        Args:
            project_root: Root directory of project to analyze
            domain_detector: Optional DomainStackDetector instance
        """
        self.project_root = Path(project_root).resolve()
        self.domain_detector = domain_detector or DomainStackDetector(
            project_root=self.project_root
        )

    async def analyze(self) -> BrownfieldAnalysisResult:
        """
        Perform complete brownfield analysis.

        Returns:
            BrownfieldAnalysisResult with detected languages, frameworks,
            dependencies, and domains
        """
        logger.info(f"Analyzing brownfield project at {self.project_root}")

        # Detect languages
        languages = self.detect_languages()

        # Detect frameworks
        frameworks = self.detect_frameworks()

        # Detect dependencies
        dependencies = self.detect_dependencies()

        # Detect domains using DomainStackDetector
        project_profile = load_project_profile(project_root=self.project_root)
        stack_result = self.domain_detector.detect(project_profile=project_profile)
        domains = stack_result.detected_domains

        # Build metadata
        metadata = {
            "primary_language": stack_result.primary_language,
            "primary_framework": stack_result.primary_framework,
            "build_tools": stack_result.build_tools,
            "ci_tools": stack_result.ci_tools,
            "signal_count": len(stack_result.all_signals),
        }

        result = BrownfieldAnalysisResult(
            project_root=self.project_root,
            languages=languages,
            frameworks=frameworks,
            dependencies=dependencies,
            domains=domains,
            analysis_metadata=metadata,
        )

        logger.info(
            f"Analysis complete: {len(languages)} languages, "
            f"{len(frameworks)} frameworks, {len(dependencies)} dependencies, "
            f"{len(domains)} domains"
        )

        return result

    def detect_languages(self) -> list[str]:
        """
        Detect programming languages from file extensions and content.

        Returns:
            List of detected language names (e.g., ["python", "typescript"])
        """
        languages = set()

        # Scan for files with language extensions
        for lang, extensions in self.LANGUAGE_PATTERNS.items():
            for ext in extensions:
                if list(self.project_root.rglob(f"*{ext}")):
                    languages.add(lang)

        # Also check for language-specific config files
        if (self.project_root / "requirements.txt").exists() or (
            self.project_root / "pyproject.toml"
        ).exists():
            languages.add("python")

        if (self.project_root / "package.json").exists():
            languages.add("javascript")  # Could be JS or TS, check further
            # Check for TypeScript
            if (self.project_root / "tsconfig.json").exists():
                languages.add("typescript")
                languages.discard("javascript")

        if (self.project_root / "go.mod").exists():
            languages.add("go")

        if (self.project_root / "Cargo.toml").exists():
            languages.add("rust")

        if (self.project_root / "pom.xml").exists() or (
            self.project_root / "build.gradle"
        ).exists():
            languages.add("java")

        return sorted(languages)

    def detect_frameworks(self) -> list[str]:
        """
        Detect frameworks from dependency files and code patterns.

        Returns:
            List of detected framework names (e.g., ["fastapi", "react"])
        """
        frameworks = set()
        dependencies = self.detect_dependencies()

        # Check dependencies against framework patterns
        deps_lower = [dep.lower() for dep in dependencies]
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            if any(pattern in dep for dep in deps_lower for pattern in patterns):
                frameworks.add(framework)

        # Also check for framework-specific files
        if (self.project_root / "next.config.js").exists() or (
            self.project_root / "next.config.ts"
        ).exists():
            frameworks.add("nextjs")

        if (self.project_root / "angular.json").exists():
            frameworks.add("angular")

        if (self.project_root / "vue.config.js").exists():
            frameworks.add("vue")

        return sorted(frameworks)

    def detect_dependencies(self) -> list[str]:
        """
        Extract dependencies from package files.

        Supports:
        - Python: requirements.txt, pyproject.toml, setup.py
        - Node.js: package.json
        - Go: go.mod
        - Java: pom.xml, build.gradle

        Returns:
            List of dependency names (e.g., ["fastapi", "pytest", "react"])
        """
        dependencies = set()

        # Python: requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before ==, >=, etc.)
                            dep_name = (
                                line.split("==")[0]
                                .split(">=")[0]
                                .split("<=")[0]
                                .split("~=")[0]
                                .strip()
                            )
                            if dep_name:
                                dependencies.add(dep_name.lower())
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")

        # Python: pyproject.toml
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomli

                with open(pyproject_file, "rb") as f:
                    data = tomli.load(f)
                    deps = data.get("project", {}).get("dependencies", [])
                    for dep in deps:
                        dep_name = (
                            dep.split(">=")[0]
                            .split("==")[0]
                            .split("~=")[0]
                            .strip()
                        )
                        if dep_name:
                            dependencies.add(dep_name.lower())
            except Exception as e:
                logger.debug(f"Failed to parse pyproject.toml: {e}")

        # Node.js: package.json
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }
                    for dep_name in deps.keys():
                        dependencies.add(dep_name.lower())
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")

        # Go: go.mod
        go_mod = self.project_root / "go.mod"
        if go_mod.exists():
            try:
                with open(go_mod, encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("require"):
                            # Simple parsing - could be enhanced
                            parts = line.split()
                            if len(parts) > 1:
                                dep_name = parts[1].split("/")[-1]
                                dependencies.add(dep_name.lower())
            except Exception as e:
                logger.debug(f"Failed to parse go.mod: {e}")

        return sorted(dependencies)
