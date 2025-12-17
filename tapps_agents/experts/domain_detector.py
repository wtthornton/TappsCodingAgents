"""
Domain/Stack Detector

Maps repo signals to expert domains automatically.
Detects technical stack and maps to appropriate expert domains.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..core.project_profile import ProjectProfile, load_project_profile


@dataclass
class RepoSignal:
    """A signal detected from the repository."""

    signal_type: str  # dependency, config, build, service, file_structure, ci
    source: str  # File path or pattern
    value: Any  # Detected value
    confidence: float = 1.0


@dataclass
class DomainMapping:
    """Mapping of detected domains with confidence scores."""

    domain: str
    confidence: float
    signals: list[RepoSignal] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class StackDetectionResult:
    """Result of stack detection."""

    detected_domains: list[DomainMapping]
    primary_language: str | None = None
    primary_framework: str | None = None
    build_tools: list[str] = field(default_factory=list)
    ci_tools: list[str] = field(default_factory=list)
    all_signals: list[RepoSignal] = field(default_factory=list)


class DomainStackDetector:
    """
    Detects project stack and maps to expert domains.

    Analyzes repo signals (dependencies, configs, build tools, etc.)
    and maps them to appropriate expert domains.
    """

    # Domain mapping rules: signal pattern -> expert domain
    DOMAIN_MAPPINGS = {
        # Language domains
        "python": ["testing", "api-design-integration", "database-data-management"],
        "typescript": ["testing", "api-design-integration", "user-experience"],
        "javascript": ["testing", "api-design-integration", "user-experience"],
        "java": ["testing", "api-design-integration", "database-data-management"],
        "go": ["testing", "api-design-integration", "cloud-infrastructure"],
        "rust": ["testing", "api-design-integration", "performance"],
        # Framework domains
        "react": ["user-experience", "testing", "api-design-integration"],
        "vue": ["user-experience", "testing", "api-design-integration"],
        "angular": ["user-experience", "testing", "api-design-integration"],
        "nextjs": ["user-experience", "testing", "api-design-integration", "cloud-infrastructure"],
        "django": ["api-design-integration", "database-data-management", "testing"],
        "flask": ["api-design-integration", "testing"],
        "fastapi": ["api-design-integration", "testing", "performance"],
        "spring": ["api-design-integration", "database-data-management", "testing"],
        # Infrastructure domains
        "docker": ["cloud-infrastructure", "observability-monitoring"],
        "kubernetes": ["cloud-infrastructure", "observability-monitoring"],
        "aws": ["cloud-infrastructure", "observability-monitoring"],
        "azure": ["cloud-infrastructure", "observability-monitoring"],
        "gcp": ["cloud-infrastructure", "observability-monitoring"],
        # Database domains
        "postgresql": ["database-data-management", "performance"],
        "mysql": ["database-data-management", "performance"],
        "mongodb": ["database-data-management", "nosql-patterns"],
        "redis": ["database-data-management", "performance", "caching"],
        # Security domains
        "security": ["security", "data-privacy-compliance"],
        "oauth": ["security", "api-design-integration"],
        "jwt": ["security", "api-design-integration"],
        # Testing domains
        "pytest": ["testing"],
        "jest": ["testing"],
        "junit": ["testing"],
        "cypress": ["testing", "user-experience"],
        # Performance domains
        "performance": ["performance", "observability-monitoring"],
        "caching": ["performance", "caching"],
    }

    def __init__(self, project_root: Path | None = None):
        """
        Initialize domain stack detector.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()

    def detect(self, project_profile: ProjectProfile | None = None) -> StackDetectionResult:
        """
        Detect stack and map to expert domains.

        Args:
            project_profile: Optional project profile for hints

        Returns:
            StackDetectionResult with detected domains and signals
        """
        all_signals: list[RepoSignal] = []
        detected_domains: dict[str, DomainMapping] = {}

        # Collect signals from various sources
        all_signals.extend(self._detect_dependency_manifests())
        all_signals.extend(self._detect_config_files())
        all_signals.extend(self._detect_build_tooling())
        all_signals.extend(self._detect_service_boundaries())
        all_signals.extend(self._detect_file_structure())
        all_signals.extend(self._detect_ci_workflows())

        # Map signals to domains
        for signal in all_signals:
            domains = self._map_signal_to_domains(signal)
            for domain_name, confidence in domains.items():
                if domain_name not in detected_domains:
                    detected_domains[domain_name] = DomainMapping(
                        domain=domain_name,
                        confidence=confidence,
                        signals=[],
                        reasoning="",
                    )
                detected_domains[domain_name].signals.append(signal)
                # Update confidence (use max)
                detected_domains[domain_name].confidence = max(
                    detected_domains[domain_name].confidence, confidence
                )

        # Generate reasoning for each domain
        for domain_mapping in detected_domains.values():
            signal_types = [s.signal_type for s in domain_mapping.signals]
            domain_mapping.reasoning = (
                f"Detected via {', '.join(set(signal_types))} signals "
                f"({len(domain_mapping.signals)} total)"
            )

        # Sort by confidence
        sorted_domains = sorted(
            detected_domains.values(), key=lambda d: d.confidence, reverse=True
        )

        # Extract primary language and framework
        primary_language = self._extract_primary_language(all_signals)
        primary_framework = self._extract_primary_framework(all_signals)
        build_tools = self._extract_build_tools(all_signals)
        ci_tools = self._extract_ci_tools(all_signals)

        return StackDetectionResult(
            detected_domains=sorted_domains,
            primary_language=primary_language,
            primary_framework=primary_framework,
            build_tools=build_tools,
            ci_tools=ci_tools,
            all_signals=all_signals,
        )

    def _detect_dependency_manifests(self) -> list[RepoSignal]:
        """Detect dependencies from package manifests."""
        signals = []

        # Python
        if (self.project_root / "requirements.txt").exists():
            try:
                with open(self.project_root / "requirements.txt") as f:
                    deps = [line.strip().split("==")[0].lower() for line in f if line.strip()]
                    for dep in deps:
                        signals.append(
                            RepoSignal(
                                signal_type="dependency",
                                source="requirements.txt",
                                value=dep,
                                confidence=1.0,
                            )
                        )
            except Exception:
                pass

        if (self.project_root / "pyproject.toml").exists():
            try:
                import tomli

                with open(self.project_root / "pyproject.toml", "rb") as f:
                    data = tomli.load(f)
                    deps = data.get("project", {}).get("dependencies", [])
                    for dep in deps:
                        dep_name = dep.split(">=")[0].split("==")[0].split("~=")[0].lower()
                        signals.append(
                            RepoSignal(
                                signal_type="dependency",
                                source="pyproject.toml",
                                value=dep_name,
                                confidence=1.0,
                            )
                        )
            except Exception:
                pass

        # Node.js
        if (self.project_root / "package.json").exists():
            try:
                with open(self.project_root / "package.json") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for dep_name in deps.keys():
                        signals.append(
                            RepoSignal(
                                signal_type="dependency",
                                source="package.json",
                                value=dep_name.lower(),
                                confidence=1.0,
                            )
                        )
            except Exception:
                pass

        return signals

    def _detect_config_files(self) -> list[RepoSignal]:
        """Detect stack from config files."""
        signals = []

        # Docker
        if (self.project_root / "Dockerfile").exists():
            signals.append(
                RepoSignal(
                    signal_type="config",
                    source="Dockerfile",
                    value="docker",
                    confidence=1.0,
                )
            )

        # Kubernetes
        if (self.project_root / "k8s").exists() or (self.project_root / "kubernetes").exists():
            signals.append(
                RepoSignal(
                    signal_type="config",
                    source="k8s/kubernetes",
                    value="kubernetes",
                    confidence=1.0,
                )
            )

        # Environment files
        env_files = list(self.project_root.glob(".env*"))
        if env_files:
            signals.append(
                RepoSignal(
                    signal_type="config",
                    source=".env",
                    value="configuration",
                    confidence=0.8,
                )
            )

        return signals

    def _detect_build_tooling(self) -> list[RepoSignal]:
        """Detect build tools."""
        signals = []

        # Makefile
        if (self.project_root / "Makefile").exists():
            signals.append(
                RepoSignal(
                    signal_type="build",
                    source="Makefile",
                    value="make",
                    confidence=1.0,
                )
            )

        # Webpack
        if (self.project_root / "webpack.config.js").exists():
            signals.append(
                RepoSignal(
                    signal_type="build",
                    source="webpack.config.js",
                    value="webpack",
                    confidence=1.0,
                )
            )

        # Vite
        if (self.project_root / "vite.config.js").exists() or (
            self.project_root / "vite.config.ts"
        ).exists():
            signals.append(
                RepoSignal(
                    signal_type="build",
                    source="vite.config.*",
                    value="vite",
                    confidence=1.0,
                )
            )

        return signals

    def _detect_service_boundaries(self) -> list[RepoSignal]:
        """Detect service boundaries (microservices, APIs)."""
        signals = []

        # Check for API-related directories
        if (self.project_root / "api").exists() or (self.project_root / "apis").exists():
            signals.append(
                RepoSignal(
                    signal_type="service",
                    source="api/",
                    value="api-design-integration",
                    confidence=0.9,
                )
            )

        # Check for services directory
        if (self.project_root / "services").exists():
            signals.append(
                RepoSignal(
                    signal_type="service",
                    source="services/",
                    value="api-design-integration",
                    confidence=0.8,
                )
            )

        return signals

    def _detect_file_structure(self) -> list[RepoSignal]:
        """Detect stack from file extensions and directory structure."""
        signals = []

        # Count file types
        py_files = list(self.project_root.rglob("*.py"))
        ts_files = list(self.project_root.rglob("*.ts"))
        js_files = list(self.project_root.rglob("*.js"))
        java_files = list(self.project_root.rglob("*.java"))
        go_files = list(self.project_root.rglob("*.go"))
        rs_files = list(self.project_root.rglob("*.rs"))

        if py_files:
            signals.append(
                RepoSignal(
                    signal_type="file_structure",
                    source="*.py",
                    value="python",
                    confidence=min(1.0, len(py_files) / 10.0),
                )
            )
        if ts_files:
            signals.append(
                RepoSignal(
                    signal_type="file_structure",
                    source="*.ts",
                    value="typescript",
                    confidence=min(1.0, len(ts_files) / 10.0),
                )
            )
        if js_files and not ts_files:  # Only if not TypeScript
            signals.append(
                RepoSignal(
                    signal_type="file_structure",
                    source="*.js",
                    value="javascript",
                    confidence=min(1.0, len(js_files) / 10.0),
                )
            )
        if java_files:
            signals.append(
                RepoSignal(
                    signal_type="file_structure",
                    source="*.java",
                    value="java",
                    confidence=min(1.0, len(java_files) / 10.0),
                )
            )
        if go_files:
            signals.append(
                RepoSignal(
                    signal_type="file_structure",
                    source="*.go",
                    value="go",
                    confidence=min(1.0, len(go_files) / 10.0),
                )
            )
        if rs_files:
            signals.append(
                RepoSignal(
                    signal_type="file_structure",
                    source="*.rs",
                    value="rust",
                    confidence=min(1.0, len(rs_files) / 10.0),
                )
            )

        return signals

    def _detect_ci_workflows(self) -> list[RepoSignal]:
        """Detect CI/CD workflows."""
        signals = []

        # GitHub Actions
        github_actions = self.project_root / ".github" / "workflows"
        if github_actions.exists():
            signals.append(
                RepoSignal(
                    signal_type="ci",
                    source=".github/workflows",
                    value="github-actions",
                    confidence=1.0,
                )
            )

        # GitLab CI
        if (self.project_root / ".gitlab-ci.yml").exists():
            signals.append(
                RepoSignal(
                    signal_type="ci",
                    source=".gitlab-ci.yml",
                    value="gitlab-ci",
                    confidence=1.0,
                )
            )

        return signals

    def _map_signal_to_domains(self, signal: RepoSignal) -> dict[str, float]:
        """Map a signal to expert domains."""
        domains: dict[str, float] = {}
        value_lower = str(signal.value).lower()

        # Direct domain matches
        if value_lower in self.DOMAIN_MAPPINGS:
            for domain in self.DOMAIN_MAPPINGS[value_lower]:
                domains[domain] = signal.confidence

        # Pattern matching for dependencies
        if signal.signal_type == "dependency":
            # Framework detection
            if "react" in value_lower:
                domains["user-experience"] = signal.confidence
                domains["testing"] = signal.confidence * 0.8
            elif "vue" in value_lower:
                domains["user-experience"] = signal.confidence
                domains["testing"] = signal.confidence * 0.8
            elif "angular" in value_lower:
                domains["user-experience"] = signal.confidence
                domains["testing"] = signal.confidence * 0.8
            elif "django" in value_lower:
                domains["api-design-integration"] = signal.confidence
                domains["database-data-management"] = signal.confidence * 0.8
            elif "flask" in value_lower:
                domains["api-design-integration"] = signal.confidence
            elif "fastapi" in value_lower:
                domains["api-design-integration"] = signal.confidence
                domains["performance"] = signal.confidence * 0.8
            elif "spring" in value_lower:
                domains["api-design-integration"] = signal.confidence
                domains["database-data-management"] = signal.confidence * 0.8

            # Database detection
            if any(db in value_lower for db in ["postgres", "psycopg", "pg"]):
                domains["database-data-management"] = signal.confidence
            elif "mysql" in value_lower or "mariadb" in value_lower:
                domains["database-data-management"] = signal.confidence
            elif "mongodb" in value_lower or "pymongo" in value_lower:
                domains["database-data-management"] = signal.confidence
            elif "redis" in value_lower:
                domains["database-data-management"] = signal.confidence
                domains["performance"] = signal.confidence * 0.8

            # Testing framework detection
            if "pytest" in value_lower:
                domains["testing"] = signal.confidence
            elif "jest" in value_lower:
                domains["testing"] = signal.confidence
            elif "junit" in value_lower:
                domains["testing"] = signal.confidence
            elif "cypress" in value_lower:
                domains["testing"] = signal.confidence
                domains["user-experience"] = signal.confidence * 0.7

            # Security detection
            if any(sec in value_lower for sec in ["oauth", "jwt", "auth", "security"]):
                domains["security"] = signal.confidence

        return domains

    def _extract_primary_language(self, signals: list[RepoSignal]) -> str | None:
        """Extract primary programming language from signals."""
        language_signals = [s for s in signals if s.signal_type == "file_structure"]
        if language_signals:
            # Return most common language
            languages = [s.value for s in language_signals]
            return max(set(languages), key=languages.count)
        return None

    def _extract_primary_framework(self, signals: list[RepoSignal]) -> str | None:
        """Extract primary framework from signals."""
        framework_keywords = [
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "fastapi",
            "spring",
            "nextjs",
        ]
        for signal in signals:
            if signal.signal_type == "dependency":
                value_lower = str(signal.value).lower()
                for framework in framework_keywords:
                    if framework in value_lower:
                        return framework
        return None

    def _extract_build_tools(self, signals: list[RepoSignal]) -> list[str]:
        """Extract build tools from signals."""
        build_tools = []
        for signal in signals:
            if signal.signal_type == "build":
                build_tools.append(str(signal.value))
        return list(set(build_tools))

    def _extract_ci_tools(self, signals: list[RepoSignal]) -> list[str]:
        """Extract CI tools from signals."""
        ci_tools = []
        for signal in signals:
            if signal.signal_type == "ci":
                ci_tools.append(str(signal.value))
        return list(set(ci_tools))

