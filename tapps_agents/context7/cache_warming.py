"""
Cache Warming Strategies for Context7 KB cache.

Implements automatic cache warming based on project dependencies and usage patterns.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache_structure import CacheStructure
from .kb_cache import KBCache
from .lookup import KBLookup
from .metadata import MetadataManager
from .staleness_policies import StalenessPolicyManager

logger = logging.getLogger(__name__)


@dataclass
class WarmingStrategy:
    """Strategy for cache warming."""

    name: str
    priority: int  # 1-10, higher = more urgent
    libraries: list[str]
    topics: list[str] = None  # None means all common topics
    auto_detect: bool = True  # Whether to auto-detect from project


class CacheWarmer:
    """Manages cache warming strategies."""

    def __init__(
        self,
        kb_cache: KBCache,
        kb_lookup: KBLookup,
        cache_structure: CacheStructure,
        metadata_manager: MetadataManager,
        project_root: Path | None = None,
    ):
        """
        Initialize cache warmer.

        Args:
            kb_cache: KBCache instance
            kb_lookup: KBLookup instance
            cache_structure: CacheStructure instance
            metadata_manager: MetadataManager instance
            project_root: Optional project root path
        """
        self.kb_cache = kb_cache
        self.kb_lookup = kb_lookup
        self.cache_structure = cache_structure
        self.metadata_manager = metadata_manager
        self.project_root = project_root or Path.cwd()
        self.policy_manager = StalenessPolicyManager()

    def detect_project_libraries(self) -> list[str]:
        """
        Detect libraries from project dependencies.

        Returns:
            List of library names detected from project files
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
                    # Extract common library names
                    for dep_name in all_deps.keys():
                        # Normalize names (e.g., @types/react -> react)
                        normalized = dep_name.replace("@types/", "").replace("@", "")
                        libraries.add(normalized)
            except Exception:
                logger.debug("Failed to parse package.json", exc_info=True)

        # Check requirements.txt or pyproject.toml (Python projects)
        requirements_txt = self.project_root / "requirements.txt"
        if requirements_txt.exists():
            try:
                with open(requirements_txt, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before == or other specifiers)
                            pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                            libraries.add(pkg_name.lower())
            except Exception:
                logger.debug("Failed to parse requirements.txt", exc_info=True)

        pyproject_toml = self.project_root / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                with open(pyproject_toml, encoding="utf-8") as f:
                    content = f.read()
                    # Simple regex-like extraction (for basic cases)
                    import re
                    # Match dependencies in [project.dependencies] or [tool.poetry.dependencies]
                    deps_pattern = r'(?:dependencies|dev-dependencies)\s*=\s*\[(.*?)\]'
                    matches = re.findall(deps_pattern, content, re.DOTALL)
                    for match in matches:
                        # Extract quoted strings
                        pkg_names = re.findall(r'["\']([^"\']+)["\']', match)
                        for pkg_name in pkg_names:
                            libraries.add(pkg_name.lower())
            except Exception:
                logger.debug("Failed to parse pyproject.toml", exc_info=True)

        return sorted(list(libraries))

    def get_common_topics(self, library: str) -> list[str]:
        """
        Get common topics for a library based on library type.

        Args:
            library: Library name

        Returns:
            List of common topic names
        """
        library_lower = library.lower()

        # Framework-specific topics
        if "react" in library_lower:
            return ["overview", "hooks", "components", "routing"]
        elif "fastapi" in library_lower or "flask" in library_lower or "django" in library_lower:
            return ["overview", "routing", "middleware", "authentication"]
        elif "pytest" in library_lower or "jest" in library_lower or "vitest" in library_lower:
            return ["overview", "fixtures", "mocking", "async"]
        elif "typescript" in library_lower:
            return ["overview", "types", "interfaces", "generics"]
        elif "playwright" in library_lower or "selenium" in library_lower:
            return ["overview", "selectors", "waiting", "screenshots"]
        elif "sqlalchemy" in library_lower or "prisma" in library_lower:
            return ["overview", "models", "queries", "migrations"]
        else:
            # Default topics for any library
            return ["overview"]

    async def warm_cache(
        self,
        libraries: list[str] | None = None,
        topics: list[str] | None = None,
        priority: int = 5,
        auto_detect: bool = True,
    ) -> dict[str, Any]:
        """
        Warm cache with specified libraries and topics.

        Args:
            libraries: Optional list of library names (auto-detected if None and auto_detect=True)
            topics: Optional list of topics (auto-detected if None)
            priority: Priority for warming (1-10)
            auto_detect: Whether to auto-detect libraries from project

        Returns:
            Dictionary with warming result
        """
        if libraries is None:
            if auto_detect:
                libraries = self.detect_project_libraries()
            else:
                libraries = []

        if not libraries:
            return {
                "success": False,
                "error": "No libraries specified or detected",
                "warmed": 0,
            }

        warmed = 0
        errors: list[str] = []

        for library in libraries:
            # Get topics for this library
            lib_topics = topics or self.get_common_topics(library)

            for topic in lib_topics:
                # Skip if already cached and not stale
                if self.kb_cache.exists(library, topic):
                    entry = self.kb_cache.get(library, topic)
                    if entry and entry.cached_at:
                        # Check if stale
                        is_stale = self.policy_manager.is_entry_stale(
                            library, entry.cached_at
                        )
                        if not is_stale:
                            continue  # Skip non-stale entries

                try:
                    # Perform lookup (will cache if successful)
                    result = await self.kb_lookup.lookup(
                        library=library, topic=topic, use_fuzzy_match=False
                    )
                    if result.success:
                        warmed += 1
                    else:
                        errors.append(f"{library}/{topic}: {result.error}")
                except Exception as e:
                    errors.append(f"{library}/{topic}: {str(e)}")

        return {
            "success": warmed > 0,
            "warmed": warmed,
            "total_requested": len(libraries) * len(topics or ["overview"]),
            "errors": errors,
            "libraries": libraries,
        }

    def get_warming_recommendations(self) -> list[dict[str, Any]]:
        """
        Get cache warming recommendations based on project and usage.

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Detect project libraries
        detected = self.detect_project_libraries()
        if detected:
            recommendations.append(
                {
                    "type": "project_dependencies",
                    "libraries": detected,
                    "priority": 8,
                    "reason": "Detected from project dependencies",
                }
            )

        # Check cache statistics for frequently accessed libraries
        from .analytics import Analytics

        analytics = Analytics(self.cache_structure, self.metadata_manager)
        top_libraries = analytics.get_top_libraries(limit=5)
        if top_libraries:
            recommendations.append(
                {
                    "type": "frequently_accessed",
                    "libraries": [lib.library for lib in top_libraries],
                    "priority": 7,
                    "reason": "Frequently accessed libraries",
                }
            )

        # Check for stale entries that should be refreshed
        index = self.metadata_manager.load_cache_index()
        stale_libraries = []
        for library_name, library_data in index.libraries.items():
            topics = library_data.get("topics", {})
            for _topic_name, topic_data in topics.items():
                last_updated = topic_data.get("last_updated") or topic_data.get(
                    "cached_at"
                )
                if last_updated:
                    is_stale = self.policy_manager.is_entry_stale(
                        library_name, last_updated
                    )
                    if is_stale:
                        stale_libraries.append(library_name)
                        break  # Only add library once

        if stale_libraries:
            recommendations.append(
                {
                    "type": "stale_entries",
                    "libraries": stale_libraries,
                    "priority": 6,
                    "reason": "Libraries with stale entries",
                }
            )

        return recommendations
