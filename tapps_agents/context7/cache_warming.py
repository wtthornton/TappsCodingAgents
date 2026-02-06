"""
Cache Warming Strategies for Context7 KB cache.

Implements automatic cache warming based on project dependencies and usage patterns.

2025 Enhancement: Predictive pre-warming with priority-based library detection.
- Detects project dependencies (requirements.txt, pyproject.toml, package.json)
- Prioritizes commonly used libraries
- Background async warming (non-blocking)
- Integrates with `tapps-agents init` for immediate cache population
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cache_structure import CacheStructure
from .kb_cache import KBCache
from .lookup import KBLookup
from .metadata import MetadataManager
from .staleness_policies import StalenessPolicyManager

logger = logging.getLogger(__name__)


# Well-known libraries that Context7 has high-quality documentation for
# Priority: 1 = most important, 3 = least important
WELL_KNOWN_LIBRARIES: dict[str, int] = {
    # Python Web Frameworks (Priority 1)
    "fastapi": 1,
    "django": 1,
    "flask": 1,
    "starlette": 2,
    "aiohttp": 2,
    # Python Data/ML (Priority 1)
    "pydantic": 1,
    "sqlalchemy": 1,
    "numpy": 1,
    "pandas": 1,
    # Python Testing (Priority 1)
    "pytest": 1,
    "unittest": 2,
    # Python HTTP (Priority 2)
    "requests": 2,
    "httpx": 2,
    "urllib3": 3,
    # Python Async (Priority 2)
    "asyncio": 2,
    "aiofiles": 3,
    # Python CLI/Utils (Priority 2)
    "click": 2,
    "typer": 2,
    "rich": 2,
    "pyyaml": 2,
    # JavaScript/TypeScript (Priority 1)
    "react": 1,
    "vue": 1,
    "angular": 1,
    "nextjs": 1,
    "express": 1,
    "typescript": 1,
    # JavaScript Testing (Priority 1)
    "jest": 1,
    "vitest": 1,
    "playwright": 1,
    "cypress": 2,
    # JavaScript Utils (Priority 2)
    "axios": 2,
    "lodash": 2,
    "dayjs": 3,
    "moment": 3,
    # AI/ML (Priority 1)
    "openai": 1,
    "anthropic": 1,
    "langchain": 1,
    "llamaindex": 2,
    # Infrastructure (Priority 2)
    "docker": 2,
    "kubernetes": 2,
    "terraform": 2,
}


@dataclass
class WarmingStrategy:
    """Strategy for cache warming."""

    name: str
    priority: int  # 1-10, higher = more urgent
    libraries: list[str]
    topics: list[str] | None = None  # None means all common topics
    auto_detect: bool = True  # Whether to auto-detect from project


@dataclass
class WarmingResult:
    """Result of cache warming operation."""

    success: bool
    warmed: int
    skipped: int
    failed: int
    total_requested: int
    duration_ms: float
    libraries_warmed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


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
                    for dep_name in all_deps:
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
                    errors.append(f"{library}/{topic}: {e!s}")

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

    def get_prioritized_libraries(self, max_count: int = 20) -> list[str]:
        """
        Get prioritized list of libraries for pre-warming.

        Combines:
        1. Project dependencies (detected from files)
        2. Well-known libraries (from WELL_KNOWN_LIBRARIES)

        Sorted by priority (project deps first, then by well-known priority).

        Args:
            max_count: Maximum number of libraries to return

        Returns:
            List of library names sorted by priority
        """
        # Detect project libraries
        detected = set(self.detect_project_libraries())

        # Score libraries: project deps get +10, well-known get their priority
        scored: list[tuple[str, int]] = []

        for lib in detected:
            lib_lower = lib.lower()
            well_known_priority = WELL_KNOWN_LIBRARIES.get(lib_lower, 3)
            # Project deps get +10 bonus
            score = 10 + (4 - well_known_priority)  # Invert so priority 1 = highest
            scored.append((lib_lower, score))

        # Add well-known libraries not in project (lower priority)
        for lib, priority in WELL_KNOWN_LIBRARIES.items():
            if lib not in detected:
                score = 4 - priority  # priority 1 = score 3, priority 3 = score 1
                scored.append((lib, score))

        # Sort by score (descending) and take top N
        scored.sort(key=lambda x: x[1], reverse=True)
        return [lib for lib, _ in scored[:max_count]]

    async def warm_cache_predictive(
        self,
        max_libraries: int = 20,
        max_concurrency: int = 5,
        per_library_timeout: float = 5.0,
        on_progress: Any | None = None,
    ) -> WarmingResult:
        """
        Predictive cache warming with bounded parallelism.

        2025 Architecture:
        - Detects project dependencies automatically
        - Prioritizes well-known libraries
        - Uses circuit breaker for resilience
        - Bounded concurrency (default: 5 parallel)
        - Per-library timeout (default: 5s)

        Args:
            max_libraries: Maximum number of libraries to warm (default: 20)
            max_concurrency: Maximum concurrent lookups (default: 5)
            per_library_timeout: Timeout per library in seconds (default: 5.0)
            on_progress: Optional callback(library, status, current, total)

        Returns:
            WarmingResult with statistics
        """
        import time

        from .circuit_breaker import get_parallel_executor

        start_time = time.time()

        # Get prioritized libraries
        libraries = self.get_prioritized_libraries(max_count=max_libraries)

        if not libraries:
            return WarmingResult(
                success=False,
                warmed=0,
                skipped=0,
                failed=0,
                total_requested=0,
                duration_ms=0,
                errors=["No libraries detected for warming"],
            )

        # Get parallel executor with circuit breaker
        executor = get_parallel_executor(max_concurrency=max_concurrency)

        warmed = 0
        skipped = 0
        failed = 0
        errors: list[str] = []
        libraries_warmed: list[str] = []

        async def warm_library(lib: str) -> tuple[str, str, str | None]:
            """Warm a single library. Returns (library, status, error)."""
            topic = "overview"

            # Check if already cached and not stale
            if self.kb_cache.exists(lib, topic):
                entry = self.kb_cache.get(lib, topic)
                if entry and entry.cached_at:
                    is_stale = self.policy_manager.is_entry_stale(lib, entry.cached_at)
                    if not is_stale:
                        return (lib, "skipped", None)

            try:
                result = await asyncio.wait_for(
                    self.kb_lookup.lookup(library=lib, topic=topic, use_fuzzy_match=False),
                    timeout=per_library_timeout,
                )
                if result.success:
                    return (lib, "warmed", None)
                else:
                    return (lib, "failed", result.error)
            except TimeoutError:
                return (lib, "failed", f"Timeout after {per_library_timeout}s")
            except Exception as e:
                return (lib, "failed", str(e))

        # Execute warming in parallel
        results = await executor.execute_all(
            items=libraries,
            func=warm_library,
            fallback=None,
        )

        # Process results
        for i, result in enumerate(results):
            library = libraries[i]

            # Report progress
            if on_progress:
                try:
                    on_progress(library, "processing", i + 1, len(libraries))
                except Exception:
                    pass

            if result is None:
                failed += 1
                errors.append(f"{library}: Circuit breaker open")
                continue

            if isinstance(result, tuple) and len(result) == 3:
                lib, status, error = result
                if status == "warmed":
                    warmed += 1
                    libraries_warmed.append(lib)
                elif status == "skipped":
                    skipped += 1
                else:
                    failed += 1
                    if error:
                        errors.append(f"{lib}: {error}")
            else:
                failed += 1
                errors.append(f"{library}: Unexpected result format")

        duration_ms = (time.time() - start_time) * 1000

        return WarmingResult(
            success=warmed > 0,
            warmed=warmed,
            skipped=skipped,
            failed=failed,
            total_requested=len(libraries),
            duration_ms=duration_ms,
            libraries_warmed=libraries_warmed,
            errors=errors[:10],  # Limit errors to 10
        )


async def run_predictive_warming(
    project_root: Path | None = None,
    max_libraries: int = 20,
    max_concurrency: int = 5,
    on_progress: Any | None = None,
) -> WarmingResult:
    """
    Convenience function to run predictive cache warming.

    Can be called during `tapps-agents init` or manually.

    Args:
        project_root: Project root path (default: cwd)
        max_libraries: Maximum libraries to warm (default: 20)
        max_concurrency: Max concurrent lookups (default: 5)
        on_progress: Optional progress callback

    Returns:
        WarmingResult with statistics
    """
    if project_root is None:
        project_root = Path.cwd()

    try:
        # Initialize components
        cache_root = project_root / ".tapps-agents" / "kb" / "context7-cache"
        cache_structure = CacheStructure(cache_root)
        cache_structure.initialize()

        metadata_manager = MetadataManager(cache_structure)
        kb_cache = KBCache(cache_root, metadata_manager)

        # Initialize KB lookup (with MCP gateway if available)
        from ..mcp.gateway import MCPGateway
        
        try:
            mcp_gateway = MCPGateway()
        except Exception:
            mcp_gateway = None

        kb_lookup = KBLookup(kb_cache=kb_cache, mcp_gateway=mcp_gateway)

        # Create warmer and run
        warmer = CacheWarmer(
            kb_cache=kb_cache,
            kb_lookup=kb_lookup,
            cache_structure=cache_structure,
            metadata_manager=metadata_manager,
            project_root=project_root,
        )

        return await warmer.warm_cache_predictive(
            max_libraries=max_libraries,
            max_concurrency=max_concurrency,
            on_progress=on_progress,
        )

    except Exception as e:
        logger.warning(f"Predictive warming failed: {e}")
        return WarmingResult(
            success=False,
            warmed=0,
            skipped=0,
            failed=0,
            total_requested=0,
            duration_ms=0,
            errors=[str(e)],
        )
