"""
Service Discovery - Auto-detect services in project structure

Phase 6.4.2: Multi-Service Analysis
Phase 4.1: Enhanced with prioritization, dependency analysis, and language grouping
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ...core.language_detector import Language, LanguageDetector

logger = logging.getLogger(__name__)


class Priority(str, Enum):
    """Service priority levels for phased review."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Service:
    """
    Service model with enhanced metadata.

    Phase 4.1: Service Discovery Enhancement
    """

    name: str
    path: Path
    relative_path: str
    language: Language = Language.UNKNOWN
    priority: Priority = Priority.MEDIUM
    dependencies: list[str] = field(default_factory=list)
    file_count: int = 0
    pattern: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert Service to dictionary."""
        return {
            "name": self.name,
            "path": str(self.path),
            "relative_path": self.relative_path,
            "language": self.language.value,
            "priority": self.priority.value,  # Convert enum to string
            "dependencies": self.dependencies,
            "file_count": self.file_count,
            "pattern": self.pattern,
        }


class ServiceDiscovery:
    """
    Discover services in a project structure.

    Phase 6.4.2: Multi-Service Analysis
    """

    def __init__(
        self,
        project_root: Path | None = None,
        service_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ):
        """
        Initialize service discovery.

        Args:
            project_root: Root directory of the project (default: current directory)
            service_patterns: List of patterns to match service directories
                            (default: ['services/*/', 'src/*/', 'apps/*/'])
            exclude_patterns: List of patterns to exclude (default: ['node_modules', '.git', '__pycache__'])
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).resolve()

        if service_patterns is None:
            service_patterns = [
                "services/*/",
                "src/*/",
                "apps/*/",
                "microservices/*/",
                "packages/*/",
                # Treat the main Python package as a first-class service root for project analysis.
                "tapps_agents/",
            ]
        self.service_patterns = service_patterns

        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules",
                ".git",
                "__pycache__",
                ".pytest_cache",
                ".venv",
                "venv",
                "env",
                ".env",
                "dist",
                "build",
            ]
        self.exclude_patterns = exclude_patterns
        self.language_detector = LanguageDetector()

    def discover_services_enhanced(self) -> list[Service]:
        """
        Discover all services with enhanced metadata.

        Phase 4.1: Enhanced service discovery with language detection, priority, and dependencies.

        Returns:
            List of Service objects with language, priority, and dependencies
        """
        # Get basic service discovery
        basic_services = self.discover_services()

        # Convert to Service objects with enhanced metadata
        services = []
        for service_dict in basic_services:
            service_path = Path(service_dict["path"])

            # Detect language
            language = self._detect_service_language(service_path)

            # Count files
            file_count = self._count_service_files(service_path)

            # Detect dependencies
            dependencies = self._detect_dependencies(service_path)

            # Determine priority
            priority = self._determine_priority(
                service_dict["name"], dependencies, file_count
            )

            service = Service(
                name=service_dict["name"],
                path=service_path,
                relative_path=service_dict["relative_path"],
                language=language,
                priority=priority,
                dependencies=dependencies,
                file_count=file_count,
                pattern=service_dict.get("pattern", ""),
            )
            services.append(service)

        return services

    def _detect_service_language(self, service_path: Path) -> Language:
        """Detect the primary language of a service."""
        # Try to detect from common config files
        if (service_path / "package.json").exists():
            try:
                with (service_path / "package.json").open(encoding="utf-8") as f:
                    package_data = json.load(f)
                    if package_data.get("dependencies", {}).get("react"):
                        return Language.REACT
                    return Language.TYPESCRIPT
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Failed to parse package.json for language detection in {service_path.name}: {e}")

        if (service_path / "requirements.txt").exists() or (
            service_path / "pyproject.toml"
        ).exists():
            return Language.PYTHON

        # Detect from file extensions in service directory
        code_files = []
        for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]:
            code_files.extend(list(service_path.rglob(f"*{ext}"))[:10])

        if not code_files:
            return Language.UNKNOWN

        # Use LanguageDetector on a sample file
        sample_file = code_files[0]
        result = self.language_detector.detect_language(sample_file)
        return result.language

    def _count_service_files(self, service_path: Path) -> int:
        """Count code files in service directory."""
        count = 0
        code_extensions = [".py", ".ts", ".tsx", ".js", ".jsx"]
        for ext in code_extensions:
            count += len(list(service_path.rglob(f"*{ext}")))
        return count

    def _detect_dependencies(self, service_path: Path) -> list[str]:
        """
        Detect service dependencies from config files.

        Phase 4.1: Dependency Analysis
        """
        dependencies = []

        # Check package.json (Node.js/TypeScript/React)
        package_json = service_path / "package.json"
        if package_json.exists():
            try:
                with package_json.open(encoding="utf-8") as f:
                    package_data = json.load(f)
                    # Get both dependencies and devDependencies
                    deps = package_data.get("dependencies", {})
                    deps.update(package_data.get("devDependencies", {}))
                    dependencies.extend(list(deps.keys()))
            except (json.JSONDecodeError, Exception):
                pass

        # Check requirements.txt (Python)
        requirements_txt = service_path / "requirements.txt"
        if requirements_txt.exists():
            try:
                with requirements_txt.open(encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before ==, >=, etc.)
                            package_name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            if package_name:
                                dependencies.append(package_name)
            except Exception as e:
                logger.debug(f"Failed to parse requirements.txt for service {service_path.name}: {e}")

        # Check pyproject.toml (Python)
        pyproject_toml = service_path / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                import tomllib  # Python 3.11+

                with pyproject_toml.open("rb") as f:
                    pyproject_data = tomllib.load(f)
                    project_deps = pyproject_data.get("project", {}).get(
                        "dependencies", []
                    )
                    for dep in project_deps:
                        # Extract package name (before version specifiers)
                        package_name = dep.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        if package_name:
                            dependencies.append(package_name)
            except ImportError:
                # Fallback for Python < 3.11 (could use tomli)
                pass
            except Exception as e:
                logger.debug(f"Failed to parse requirements.txt for service {service_path.name}: {e}")

        return sorted(set(dependencies))

    def _determine_priority(
        self, service_name: str, dependencies: list[str], file_count: int
    ) -> Priority:
        """
        Determine service priority based on name patterns, dependencies, and file count.

        Phase 4.1: Prioritization Logic
        """
        service_name_lower = service_name.lower()

        # Critical priority patterns
        critical_patterns = [
            "auth",
            "security",
            "api",
            "gateway",
            "core",
            "base",
            "common",
        ]
        if any(pattern in service_name_lower for pattern in critical_patterns):
            return Priority.CRITICAL

        # High priority: many dependencies or high file count
        if len(dependencies) > 20 or file_count > 100:
            return Priority.HIGH

        # High priority patterns
        high_patterns = ["service", "server", "backend", "frontend", "client"]
        if any(pattern in service_name_lower for pattern in high_patterns):
            return Priority.HIGH

        # Low priority: minimal dependencies and low file count
        if len(dependencies) < 3 and file_count < 10:
            return Priority.LOW

        # Default to medium
        return Priority.MEDIUM

    def prioritize_services(self, services: list[Service]) -> list[Service]:
        """
        Prioritize services: critical → high → medium → low.

        Phase 4.1: Service Prioritization
        """
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }

        def priority_key(service: Service) -> tuple[int, str]:
            return (priority_order.get(service.priority, 99), service.name)

        return sorted(services, key=priority_key)

    def group_by_language(self, services: list[Service]) -> dict[Language, list[Service]]:
        """
        Group services by detected primary language.

        Phase 4.1: Language Grouping
        """
        grouped: dict[Language, list[Service]] = {}
        for service in services:
            if service.language not in grouped:
                grouped[service.language] = []
            grouped[service.language].append(service)
        return grouped

    def discover_services_with_priority(
        self, prioritize: bool = True, group_by_language: bool = False
    ) -> list[Service] | dict[Language, list[Service]]:
        """
        Discover services with prioritization and optional language grouping.

        Phase 4.1: Enhanced Service Discovery

        Args:
            prioritize: Whether to prioritize services (critical → high → medium → low)
            group_by_language: Whether to group services by language

        Returns:
            List of prioritized Service objects, or dict grouped by language
        """
        services = self.discover_services_enhanced()

        if prioritize:
            services = self.prioritize_services(services)

        if group_by_language:
            return self.group_by_language(services)

        return services

    def discover_services(self) -> list[dict[str, Any]]:
        """
        Discover all services in the project.

        Returns:
            List of service dictionaries with:
            - name: Service name (directory name)
            - path: Full path to service directory
            - relative_path: Relative path from project root
        """
        services: list[dict[str, Any]] = []

        # Try each service pattern
        for pattern in self.service_patterns:
            # If the pattern points directly at a service root (no wildcard), include that directory itself.
            # This lets us analyze mono-package repos like `tapps_agents/` as a single “service”.
            if "*" not in pattern and "?" not in pattern:
                base_dir = pattern.rstrip("/").rstrip("\\")
                candidate = self.project_root / base_dir
                if (
                    candidate.exists()
                    and candidate.is_dir()
                    and not self._should_exclude(candidate)
                ):
                    if self._is_service_directory(candidate):
                        services.append(
                            {
                                "name": candidate.name,
                                "path": str(candidate),
                                "relative_path": str(
                                    candidate.relative_to(self.project_root)
                                ),
                                "pattern": pattern,
                            }
                        )
                continue

            # Convert glob pattern to directory structure
            # e.g., "services/*/" -> "services/"
            base_dir = pattern.split("*")[0].rstrip("/")
            base_path = self.project_root / base_dir

            if not base_path.exists() or not base_path.is_dir():
                continue

            # Find all subdirectories
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue

                # Check exclusion patterns
                if self._should_exclude(item):
                    continue

                # Check if it looks like a service (has code files)
                if self._is_service_directory(item):
                    service_name = item.name
                    services.append(
                        {
                            "name": service_name,
                            "path": str(item),
                            "relative_path": str(item.relative_to(self.project_root)),
                            "pattern": pattern,
                        }
                    )

        # Remove duplicates (services might match multiple patterns)
        seen = set()
        unique_services = []
        for service in services:
            key = service["path"]
            if key not in seen:
                seen.add(key)
                unique_services.append(service)

        return sorted(unique_services, key=lambda x: x["name"])

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        path_str = str(path)
        path_name = path.name

        # Check exclusion patterns
        for exclude_pattern in self.exclude_patterns:
            if exclude_pattern in path_str or path_name.startswith(exclude_pattern):
                return True

        # Exclude hidden directories
        if path_name.startswith("."):
            return True

        return False

    def _is_service_directory(self, path: Path) -> bool:
        """
        Check if a directory looks like a service directory.

        A service directory should have:
        - Python files (*.py)
        - Or TypeScript files (*.ts, *.tsx)
        - Or JavaScript files (*.js, *.jsx)
        - Or a requirements.txt / package.json
        - Or a Dockerfile / docker-compose.yml
        """
        service_indicators = [
            # Code files
            "*.py",
            "*.ts",
            "*.tsx",
            "*.js",
            "*.jsx",
            # Configuration files
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "Dockerfile",
            "docker-compose.yml",
            "*.yaml",
            "*.yml",
        ]

        # Check for service indicators
        for indicator in service_indicators:
            if indicator.startswith("*."):
                # File extension pattern
                extension = indicator[1:]
                matches = list(path.rglob(f"*{extension}"))
                if matches:
                    # Make sure it's not just in a subdirectory like node_modules
                    for match in matches[:5]:  # Check first 5 matches
                        if not self._should_exclude(match.parent):
                            return True
            else:
                # Specific file pattern
                matches = list(path.glob(indicator))
                if matches:
                    return True

        return False

    def discover_service(self, service_name: str) -> dict[str, Any] | None:
        """
        Discover a specific service by name.

        Args:
            service_name: Name of the service to find

        Returns:
            Service dictionary if found, None otherwise
        """
        services = self.discover_services()
        for service in services:
            if service["name"] == service_name:
                return service
        return None

    def discover_by_pattern(self, pattern: str) -> list[dict[str, Any]]:
        """
        Discover services matching a specific pattern.

        Args:
            pattern: Pattern to match service names (supports wildcards)

        Returns:
            List of matching services
        """
        services = self.discover_services()

        # Convert pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        regex = re.compile(f"^{regex_pattern}$", re.IGNORECASE)

        matching_services = []
        for service in services:
            if regex.match(service["name"]):
                matching_services.append(service)

        return matching_services
