"""Project Overview Generator Module.

Generates comprehensive project overview from project metadata and architecture.

This module follows modular design principles:
- Small, focused functions (< 100 lines)
- Clear separation of concerns
- Single responsibility principle
- Comprehensive error handling and logging

Phase: 4 - Knowledge Synchronization
"""

import json
import logging
import tomllib  # type: ignore
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ArchitectureType(Enum):
    """Architecture pattern types."""

    LAYERED = "layered"
    MVC = "mvc"
    CLEAN = "clean"
    HEXAGONAL = "hexagonal"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    CQRS = "cqrs"
    EVENT_DRIVEN = "event-driven"
    UNKNOWN = "unknown"


@dataclass
class ProjectMetadata:
    """Project metadata extracted from configuration files."""

    name: str
    version: str
    description: str = ""
    authors: list[str] = field(default_factory=list)
    license: str = ""
    dependencies: dict[str, str] = field(default_factory=dict)
    python_version: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'authors': self.authors,
            'license': self.license,
            'dependencies': self.dependencies,
            'python_version': self.python_version,
        }


@dataclass
class ArchitecturePattern:
    """Detected architecture pattern with confidence."""

    pattern: ArchitectureType
    confidence: float  # 0.0-1.0
    indicators: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class ComponentMap:
    """Component map with dependencies."""

    components: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    mermaid_diagram: str = ""


class ProjectOverviewGenerator:
    """Generates comprehensive project overview from metadata and architecture.

    This class provides modular functionality for:
    1. Extracting project metadata from pyproject.toml/package.json
    2. Detecting architecture patterns from directory structure
    3. Generating component maps with Mermaid diagrams
    4. Creating comprehensive markdown overview
    5. Incrementally updating overview when structure changes

    Design: Each method has a single responsibility and is < 100 lines.
    """

    def __init__(
        self,
        project_root: Path,
        output_file: Path | None = None,
    ):
        """Initialize the project overview generator.

        Args:
            project_root: Project root directory
            output_file: Output file for overview (defaults to PROJECT_OVERVIEW.md)
        """
        self.project_root = Path(project_root).resolve()
        self.output_file = output_file or self.project_root / "PROJECT_OVERVIEW.md"

        # Validate paths
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")

    def extract_project_metadata(self) -> ProjectMetadata:
        """Extract project metadata from pyproject.toml or package.json.

        Returns:
            ProjectMetadata object with extracted information

        Raises:
            FileNotFoundError: If neither pyproject.toml nor package.json exists
            ValueError: If file parsing fails
        """
        # Try pyproject.toml first (Python projects)
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            return self._extract_from_pyproject(pyproject_path)

        # Try package.json (Node.js projects)
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            return self._extract_from_package_json(package_json_path)

        raise FileNotFoundError(
            f"Neither pyproject.toml nor package.json found in {self.project_root}"
        )

    def _extract_from_pyproject(self, pyproject_path: Path) -> ProjectMetadata:
        """Extract metadata from pyproject.toml.

        Args:
            pyproject_path: Path to pyproject.toml

        Returns:
            ProjectMetadata object
        """
        if tomllib is None:
            raise ImportError(
                "tomllib/tomli not available. Install tomli for Python < 3.11: pip install tomli"
            )

        try:
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)

            # Extract from [project] or [tool.poetry] sections
            project_data = data.get('project', {})
            poetry_data = data.get('tool', {}).get('poetry', {})

            # Prefer [project] over [tool.poetry]
            name = project_data.get('name') or poetry_data.get('name', 'unknown')
            version = project_data.get('version') or poetry_data.get('version', '0.0.0')
            description = project_data.get('description') or poetry_data.get('description', '')

            # Extract authors
            authors = []
            project_authors = project_data.get('authors', [])
            if isinstance(project_authors, list):
                authors = [str(a) for a in project_authors]
            poetry_authors = poetry_data.get('authors', [])
            if not authors and isinstance(poetry_authors, list):
                authors = [str(a) for a in poetry_authors]

            # Extract license
            license_info = project_data.get('license', {})
            if isinstance(license_info, dict):
                license_str = license_info.get('text', '')
            else:
                license_str = str(license_info) if license_info else ''

            if not license_str:
                license_str = str(poetry_data.get('license', ''))

            # Extract dependencies
            dependencies = {}
            deps = project_data.get('dependencies', {})
            if isinstance(deps, dict):
                dependencies = {k: str(v) for k, v in deps.items()}

            poetry_deps = poetry_data.get('dependencies', {})
            if not dependencies and isinstance(poetry_deps, dict):
                dependencies = {k: str(v) for k, v in poetry_deps.items()}

            # Extract Python version
            python_version = ""
            requires_python = project_data.get('requires-python', '')
            if requires_python:
                python_version = str(requires_python)
            elif 'python' in dependencies:
                python_version = dependencies['python']

            return ProjectMetadata(
                name=name,
                version=version,
                description=description,
                authors=authors,
                license=license_str,
                dependencies=dependencies,
                python_version=python_version,
            )

        except Exception as e:
            logger.error(f"Failed to parse pyproject.toml: {e}")
            raise ValueError(f"Invalid pyproject.toml: {e}") from e

    def _extract_from_package_json(self, package_json_path: Path) -> ProjectMetadata:
        """Extract metadata from package.json.

        Args:
            package_json_path: Path to package.json

        Returns:
            ProjectMetadata object
        """
        try:
            with open(package_json_path, encoding='utf-8') as f:
                data = json.load(f)

            name = data.get('name', 'unknown')
            version = data.get('version', '0.0.0')
            description = data.get('description', '')

            # Extract authors
            authors = []
            author = data.get('author')
            if author:
                authors = [str(author)]
            contributors = data.get('contributors', [])
            if isinstance(contributors, list):
                authors.extend([str(c) for c in contributors])

            # Extract license
            license_str = str(data.get('license', ''))

            # Extract dependencies
            dependencies = data.get('dependencies', {})
            if not isinstance(dependencies, dict):
                dependencies = {}

            return ProjectMetadata(
                name=name,
                version=version,
                description=description,
                authors=authors,
                license=license_str,
                dependencies=dependencies,
            )

        except Exception as e:
            logger.error(f"Failed to parse package.json: {e}")
            raise ValueError(f"Invalid package.json: {e}") from e

    def detect_architecture_patterns(self) -> list[ArchitecturePattern]:
        """Detect architecture patterns from directory structure.

        Returns:
            List of detected ArchitecturePattern objects with confidence scores
        """
        patterns: list[ArchitecturePattern] = []

        # Check for common directory patterns
        dirs = set()
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dirs.add(item.name.lower())

        # MVC pattern detection
        mvc_indicators = {'models', 'views', 'controllers'}
        mvc_matches = mvc_indicators.intersection(dirs)
        if mvc_matches:
            confidence = len(mvc_matches) / len(mvc_indicators)
            patterns.append(ArchitecturePattern(
                pattern=ArchitectureType.MVC,
                confidence=confidence,
                indicators=list(mvc_matches),
            ))

        # Layered architecture detection
        layered_indicators = {'presentation', 'business', 'data', 'domain', 'application'}
        layered_matches = layered_indicators.intersection(dirs)
        if layered_matches:
            confidence = len(layered_matches) / len(layered_indicators)
            patterns.append(ArchitecturePattern(
                pattern=ArchitectureType.LAYERED,
                confidence=confidence,
                indicators=list(layered_matches),
            ))

        # Clean/Hexagonal architecture detection
        clean_indicators = {'domain', 'application', 'infrastructure', 'interfaces'}
        clean_matches = clean_indicators.intersection(dirs)
        if clean_matches:
            confidence = len(clean_matches) / len(clean_indicators)
            patterns.append(ArchitecturePattern(
                pattern=ArchitectureType.CLEAN,
                confidence=confidence,
                indicators=list(clean_matches),
            ))

        # Microservices pattern detection
        microservices_indicators = {'services', 'api-gateway', 'gateway'}
        microservices_matches = microservices_indicators.intersection(dirs)
        if microservices_matches or len([d for d in dirs if 'service' in d]) >= 2:
            service_dirs = [d for d in dirs if 'service' in d]
            confidence = 0.8 if microservices_matches else 0.5
            patterns.append(ArchitecturePattern(
                pattern=ArchitectureType.MICROSERVICES,
                confidence=confidence,
                indicators=list(microservices_matches) + service_dirs,
            ))

        # CQRS pattern detection
        cqrs_indicators = {'commands', 'queries'}
        cqrs_matches = cqrs_indicators.intersection(dirs)
        if len(cqrs_matches) == 2:
            patterns.append(ArchitecturePattern(
                pattern=ArchitectureType.CQRS,
                confidence=1.0,
                indicators=list(cqrs_matches),
            ))

        # If no patterns detected, mark as unknown
        if not patterns:
            patterns.append(ArchitecturePattern(
                pattern=ArchitectureType.UNKNOWN,
                confidence=1.0,
                indicators=['No clear architecture pattern detected'],
            ))

        # Sort by confidence (highest first)
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        logger.info(f"Detected {len(patterns)} architecture patterns")
        return patterns

    def generate_component_map(self) -> ComponentMap:
        """Generate component map with Mermaid diagram.

        Returns:
            ComponentMap object with components, dependencies, and Mermaid diagram
        """
        components = []
        dependencies: dict[str, list[str]] = {}

        # Scan for major components (top-level directories)
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                components.append(item.name)
                dependencies[item.name] = []

        # Generate Mermaid diagram
        mermaid_lines = ['graph TD']

        for component in components:
            # Sanitize component name for Mermaid (replace hyphens/spaces)
            safe_name = component.replace('-', '_').replace(' ', '_')
            mermaid_lines.append(f'    {safe_name}[{component}]')

        # Add dependencies (if detected)
        for component, deps in dependencies.items():
            safe_name = component.replace('-', '_').replace(' ', '_')
            for dep in deps:
                safe_dep = dep.replace('-', '_').replace(' ', '_')
                mermaid_lines.append(f'    {safe_name} --> {safe_dep}')

        mermaid_diagram = '\n'.join(mermaid_lines)

        logger.info(f"Generated component map with {len(components)} components")

        return ComponentMap(
            components=components,
            dependencies=dependencies,
            mermaid_diagram=mermaid_diagram,
        )

    def generate_overview(self) -> str:
        """Generate comprehensive project overview markdown.

        Returns:
            Markdown-formatted project overview
        """
        try:
            # Extract metadata
            metadata = self.extract_project_metadata()

            # Detect architecture
            patterns = self.detect_architecture_patterns()

            # Generate component map
            component_map = self.generate_component_map()

            # Build markdown
            overview_lines = []
            overview_lines.append(f"# {metadata.name}")
            overview_lines.append("")
            overview_lines.append(f"**Version:** {metadata.version}")
            overview_lines.append("")

            if metadata.description:
                overview_lines.append("## Description")
                overview_lines.append("")
                overview_lines.append(metadata.description)
                overview_lines.append("")

            if metadata.authors:
                overview_lines.append("## Authors")
                overview_lines.append("")
                for author in metadata.authors:
                    overview_lines.append(f"- {author}")
                overview_lines.append("")

            if metadata.license:
                overview_lines.append(f"**License:** {metadata.license}")
                overview_lines.append("")

            # Architecture section
            overview_lines.append("## Architecture")
            overview_lines.append("")

            if patterns:
                primary_pattern = patterns[0]
                overview_lines.append(f"**Primary Pattern:** {primary_pattern.pattern.value.title()}")
                overview_lines.append(f"**Confidence:** {primary_pattern.confidence:.0%}")
                overview_lines.append("")

                if primary_pattern.indicators:
                    overview_lines.append("**Indicators:**")
                    for indicator in primary_pattern.indicators:
                        overview_lines.append(f"- {indicator}")
                    overview_lines.append("")

                # Other detected patterns
                if len(patterns) > 1:
                    overview_lines.append("**Other Patterns Detected:**")
                    for pattern in patterns[1:]:
                        overview_lines.append(
                            f"- {pattern.pattern.value.title()} "
                            f"({pattern.confidence:.0%} confidence)"
                        )
                    overview_lines.append("")

            # Component map section
            overview_lines.append("## Components")
            overview_lines.append("")

            if component_map.components:
                overview_lines.append("```mermaid")
                overview_lines.append(component_map.mermaid_diagram)
                overview_lines.append("```")
                overview_lines.append("")

                overview_lines.append("**Components:**")
                for component in component_map.components:
                    overview_lines.append(f"- `{component}`")
                overview_lines.append("")

            # Dependencies section
            if metadata.dependencies:
                overview_lines.append("## Dependencies")
                overview_lines.append("")

                if metadata.python_version:
                    overview_lines.append(f"**Python Version:** {metadata.python_version}")
                    overview_lines.append("")

                overview_lines.append("**Key Dependencies:**")
                for dep, version in list(metadata.dependencies.items())[:10]:  # Limit to 10
                    overview_lines.append(f"- {dep}: {version}")
                overview_lines.append("")

            # Footer
            overview_lines.append("---")
            overview_lines.append("")
            overview_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

            overview = '\n'.join(overview_lines)

            logger.info(f"Generated overview with {len(overview_lines)} lines")
            return overview

        except Exception as e:
            logger.error(f"Failed to generate overview: {e}")
            raise

    def update_overview(self, force: bool = False) -> bool:
        """Update project overview (incremental update when structure changes).

        Args:
            force: Force update even if file is recent

        Returns:
            True if overview was updated, False if no update needed
        """
        try:
            # Check if update is needed
            if not force and self.output_file.exists():
                # Get file modification time
                file_mtime = self.output_file.stat().st_mtime

                # Check if any relevant files changed since last update
                pyproject_path = self.project_root / "pyproject.toml"
                package_json_path = self.project_root / "package.json"

                config_mtime = 0
                if pyproject_path.exists():
                    config_mtime = max(config_mtime, pyproject_path.stat().st_mtime)
                if package_json_path.exists():
                    config_mtime = max(config_mtime, package_json_path.stat().st_mtime)

                # If config unchanged, skip update
                if config_mtime > 0 and file_mtime > config_mtime:
                    logger.debug("Overview is up-to-date, skipping update")
                    return False

            # Generate new overview
            overview = self.generate_overview()

            # Write to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(overview)

            logger.info(f"Updated overview: {self.output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to update overview: {e}")
            return False
