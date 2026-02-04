"""
Intelligent Cache Pre-warming - Predictive cache population based on project dependencies.

2025 Architecture Pattern:
- Detect project dependencies from requirements.txt, pyproject.toml, package.json
- Prioritize by usage frequency and relevance
- Background pre-warming (non-blocking)
- Adaptive learning from usage patterns
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent_integration import Context7AgentHelper

logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Information about a detected dependency."""
    
    name: str
    version: str | None = None
    source: str = "unknown"  # "requirements.txt", "pyproject.toml", "package.json"
    is_dev_dependency: bool = False
    priority: int = 5  # 1 = highest, 10 = lowest
    
    def __hash__(self):
        return hash(self.name.lower())
    
    def __eq__(self, other):
        if isinstance(other, DependencyInfo):
            return self.name.lower() == other.name.lower()
        return False


@dataclass
class PrewarmResult:
    """Result of cache pre-warming operation."""
    
    total_libraries: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0  # Already cached
    duration_seconds: float = 0.0
    libraries: dict[str, str] = field(default_factory=dict)  # name -> status


class DependencyDetector:
    """
    Detects project dependencies from various package managers.
    
    Supports:
    - Python: requirements.txt, pyproject.toml, setup.py, Pipfile
    - JavaScript/Node: package.json
    - Multiple languages in monorepos
    """
    
    # Built-in expert libraries that Context7 likely has docs for
    EXPERT_LIBRARIES = {
        # Python
        "fastapi", "django", "flask", "pydantic", "sqlalchemy", "pytest",
        "requests", "httpx", "aiohttp", "click", "typer", "numpy", "pandas",
        "openai", "anthropic", "langchain", "celery", "redis", "dramatiq",
        "alembic", "asyncpg", "psycopg2", "boto3", "pillow", "jinja2",
        "marshmallow", "attrs", "structlog", "loguru", "rich", "playwright", "selenium", "beautifulsoup4", "scrapy", "lxml",
        # JavaScript/TypeScript
        "react", "vue", "angular", "svelte", "nextjs", "nuxt", "express",
        "nest", "fastify", "koa", "axios", "fetch", "lodash", "moment",
        "dayjs", "date-fns", "zod", "yup", "joi", "jest", "vitest",
        "mocha", "chai", "cypress", "puppeteer", "webpack",
        "vite", "rollup", "esbuild", "tailwindcss", "styled-components",
        "emotion", "prisma", "typeorm", "sequelize", "mongoose", "graphql",
    }
    
    # Priority mapping (lower = higher priority)
    PRIORITY_MAP = {
        "fastapi": 1, "django": 1, "flask": 1, "react": 1, "vue": 1,
        "pydantic": 2, "sqlalchemy": 2, "pytest": 2, "express": 2,
        "requests": 3, "httpx": 3, "axios": 3, "jest": 3,
    }
    
    def __init__(self, project_root: Path):
        """Initialize dependency detector."""
        self.project_root = project_root
    
    def detect_all(self) -> list[DependencyInfo]:
        """
        Detect all dependencies from project files.
        
        Returns:
            List of DependencyInfo sorted by priority
        """
        dependencies: set[DependencyInfo] = set()
        
        # Python dependencies
        dependencies.update(self._detect_requirements_txt())
        dependencies.update(self._detect_pyproject_toml())
        dependencies.update(self._detect_pipfile())
        
        # JavaScript dependencies
        dependencies.update(self._detect_package_json())
        
        # Sort by priority
        return sorted(dependencies, key=lambda d: d.priority)
    
    def _detect_requirements_txt(self) -> set[DependencyInfo]:
        """Detect dependencies from requirements.txt files."""
        dependencies: set[DependencyInfo] = set()
        
        # Check multiple possible locations
        req_files = [
            self.project_root / "requirements.txt",
            self.project_root / "requirements" / "base.txt",
            self.project_root / "requirements" / "prod.txt",
            self.project_root / "requirements" / "dev.txt",
        ]
        
        for req_file in req_files:
            if req_file.exists():
                try:
                    content = req_file.read_text(encoding="utf-8")
                    is_dev = "dev" in req_file.name
                    
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith("-"):
                            continue
                        
                        # Parse package name (before ==, >=, etc.)
                        match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                        if match:
                            name = match.group(1).lower()
                            version_match = re.search(r"[=<>!]+(.+)", line)
                            version = version_match.group(1) if version_match else None
                            
                            # Only include if it's an expert library
                            if name in self.EXPERT_LIBRARIES:
                                dependencies.add(DependencyInfo(
                                    name=name,
                                    version=version,
                                    source=str(req_file.name),
                                    is_dev_dependency=is_dev,
                                    priority=self.PRIORITY_MAP.get(name, 5),
                                ))
                except Exception as e:
                    logger.debug(f"Failed to parse {req_file}: {e}")
        
        return dependencies
    
    def _detect_pyproject_toml(self) -> set[DependencyInfo]:
        """Detect dependencies from pyproject.toml."""
        dependencies: set[DependencyInfo] = set()
        pyproject_file = self.project_root / "pyproject.toml"
        
        if not pyproject_file.exists():
            return dependencies
        
        try:
            import tomllib
            content = pyproject_file.read_text(encoding="utf-8")
            data = tomllib.loads(content)
            
            # Poetry dependencies
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                
                # Main dependencies
                for dep in poetry.get("dependencies", {}).keys():
                    name = dep.lower()
                    if name in self.EXPERT_LIBRARIES:
                        dependencies.add(DependencyInfo(
                            name=name,
                            source="pyproject.toml (poetry)",
                            priority=self.PRIORITY_MAP.get(name, 5),
                        ))
                
                # Dev dependencies
                for dep in poetry.get("group", {}).get("dev", {}).get("dependencies", {}).keys():
                    name = dep.lower()
                    if name in self.EXPERT_LIBRARIES:
                        dependencies.add(DependencyInfo(
                            name=name,
                            source="pyproject.toml (poetry)",
                            is_dev_dependency=True,
                            priority=self.PRIORITY_MAP.get(name, 5),
                        ))
            
            # PEP 621 dependencies
            if "project" in data:
                project = data["project"]
                
                for dep in project.get("dependencies", []):
                    # Parse package name
                    match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                    if match:
                        name = match.group(1).lower()
                        if name in self.EXPERT_LIBRARIES:
                            dependencies.add(DependencyInfo(
                                name=name,
                                source="pyproject.toml (PEP 621)",
                                priority=self.PRIORITY_MAP.get(name, 5),
                            ))
                
                # Optional/dev dependencies
                for dep_list in project.get("optional-dependencies", {}).values():
                    for dep in dep_list:
                        match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                        if match:
                            name = match.group(1).lower()
                            if name in self.EXPERT_LIBRARIES:
                                dependencies.add(DependencyInfo(
                                    name=name,
                                    source="pyproject.toml (PEP 621)",
                                    is_dev_dependency=True,
                                    priority=self.PRIORITY_MAP.get(name, 5),
                                ))
                                
        except Exception as e:
            logger.debug(f"Failed to parse pyproject.toml: {e}")
        
        return dependencies
    
    def _detect_pipfile(self) -> set[DependencyInfo]:
        """Detect dependencies from Pipfile."""
        dependencies: set[DependencyInfo] = set()
        pipfile = self.project_root / "Pipfile"
        
        if not pipfile.exists():
            return dependencies
        
        try:
            import tomllib
            content = pipfile.read_text(encoding="utf-8")
            data = tomllib.loads(content)
            
            for dep in data.get("packages", {}).keys():
                name = dep.lower()
                if name in self.EXPERT_LIBRARIES:
                    dependencies.add(DependencyInfo(
                        name=name,
                        source="Pipfile",
                        priority=self.PRIORITY_MAP.get(name, 5),
                    ))
            
            for dep in data.get("dev-packages", {}).keys():
                name = dep.lower()
                if name in self.EXPERT_LIBRARIES:
                    dependencies.add(DependencyInfo(
                        name=name,
                        source="Pipfile",
                        is_dev_dependency=True,
                        priority=self.PRIORITY_MAP.get(name, 5),
                    ))
                    
        except Exception as e:
            logger.debug(f"Failed to parse Pipfile: {e}")
        
        return dependencies
    
    def _detect_package_json(self) -> set[DependencyInfo]:
        """Detect dependencies from package.json."""
        dependencies: set[DependencyInfo] = set()
        package_json = self.project_root / "package.json"
        
        if not package_json.exists():
            return dependencies
        
        try:
            import json
            content = package_json.read_text(encoding="utf-8")
            data = json.loads(content)
            
            for dep in data.get("dependencies", {}).keys():
                name = dep.lower().lstrip("@").replace("/", "-")
                if name in self.EXPERT_LIBRARIES:
                    dependencies.add(DependencyInfo(
                        name=name,
                        source="package.json",
                        priority=self.PRIORITY_MAP.get(name, 5),
                    ))
            
            for dep in data.get("devDependencies", {}).keys():
                name = dep.lower().lstrip("@").replace("/", "-")
                if name in self.EXPERT_LIBRARIES:
                    dependencies.add(DependencyInfo(
                        name=name,
                        source="package.json",
                        is_dev_dependency=True,
                        priority=self.PRIORITY_MAP.get(name, 5),
                    ))
                    
        except Exception as e:
            logger.debug(f"Failed to parse package.json: {e}")
        
        return dependencies


class CachePrewarmer:
    """
    Intelligent cache pre-warmer for Context7 documentation.
    
    Features:
    - Detects project dependencies automatically
    - Prioritizes by usage frequency
    - Background pre-warming (non-blocking)
    - Respects rate limits and circuit breaker
    """
    
    def __init__(
        self,
        context7_helper: Context7AgentHelper,
        project_root: Path | None = None,
        max_concurrent: int = 3,
        per_library_timeout: float = 10.0,
    ):
        """
        Initialize cache pre-warmer.
        
        Args:
            context7_helper: Context7AgentHelper instance
            project_root: Project root path
            max_concurrent: Maximum concurrent pre-warm operations
            per_library_timeout: Timeout per library in seconds
        """
        self.helper = context7_helper
        self.project_root = project_root or context7_helper.project_root
        self.max_concurrent = max_concurrent
        self.per_library_timeout = per_library_timeout
        self.detector = DependencyDetector(self.project_root)
    
    async def prewarm(
        self,
        max_libraries: int = 20,
        skip_cached: bool = True,
        priority_filter: int | None = None,
    ) -> PrewarmResult:
        """
        Pre-warm cache with project dependencies.
        
        Args:
            max_libraries: Maximum number of libraries to pre-warm
            skip_cached: Skip libraries that are already cached
            priority_filter: Only pre-warm libraries with priority <= this value
            
        Returns:
            PrewarmResult with statistics
        """
        start_time = datetime.now(UTC)
        result = PrewarmResult()
        
        # Detect dependencies
        dependencies = self.detector.detect_all()
        
        # Filter by priority
        if priority_filter is not None:
            dependencies = [d for d in dependencies if d.priority <= priority_filter]
        
        # Limit to max_libraries
        dependencies = dependencies[:max_libraries]
        result.total_libraries = len(dependencies)
        
        if not dependencies:
            logger.info("No libraries detected for pre-warming")
            return result
        
        logger.info(f"Pre-warming cache with {len(dependencies)} libraries")
        
        # Pre-warm in parallel with bounded concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def prewarm_one(dep: DependencyInfo) -> tuple[str, str]:
            """Pre-warm single library."""
            async with semaphore:
                # Check if already cached
                if skip_cached and self.helper.is_library_cached(dep.name):
                    return (dep.name, "skipped")
                
                try:
                    doc = await asyncio.wait_for(
                        self.helper.get_documentation(dep.name, topic="overview"),
                        timeout=self.per_library_timeout,
                    )
                    if doc:
                        return (dep.name, "success")
                    else:
                        return (dep.name, "not_found")
                except TimeoutError:
                    return (dep.name, "timeout")
                except Exception as e:
                    logger.debug(f"Pre-warm failed for {dep.name}: {e}")
                    return (dep.name, "error")
        
        # Execute all pre-warms
        tasks = [prewarm_one(dep) for dep in dependencies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for item in results:
            if isinstance(item, Exception):
                result.failed += 1
                result.libraries["unknown"] = f"error: {item}"
            elif isinstance(item, tuple):
                name, status = item
                result.libraries[name] = status
                if status == "success":
                    result.successful += 1
                elif status == "skipped":
                    result.skipped += 1
                else:
                    result.failed += 1
        
        result.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()
        
        logger.info(
            f"Pre-warm completed: {result.successful} success, "
            f"{result.skipped} skipped, {result.failed} failed "
            f"({result.duration_seconds:.1f}s)"
        )
        
        return result
    
    async def prewarm_background(
        self,
        max_libraries: int = 10,
        delay_seconds: float = 1.0,
    ) -> asyncio.Task:
        """
        Start background pre-warming (non-blocking).
        
        Args:
            max_libraries: Maximum libraries to pre-warm
            delay_seconds: Initial delay before starting
            
        Returns:
            asyncio.Task that can be cancelled
        """
        async def _background_prewarm():
            await asyncio.sleep(delay_seconds)
            await self.prewarm(max_libraries=max_libraries, skip_cached=True)
        
        return asyncio.create_task(_background_prewarm())


async def prewarm_on_init(
    context7_helper: Context7AgentHelper,
    project_root: Path | None = None,
    max_libraries: int = 10,
) -> PrewarmResult | None:
    """
    Pre-warm cache during initialization (convenience function).
    
    This is called during `tapps-agents init` to populate cache with
    project dependencies.
    
    Args:
        context7_helper: Context7AgentHelper instance
        project_root: Project root path
        max_libraries: Maximum libraries to pre-warm
        
    Returns:
        PrewarmResult or None if Context7 is disabled
    """
    if not context7_helper.enabled:
        return None
    
    prewarmer = CachePrewarmer(
        context7_helper=context7_helper,
        project_root=project_root,
        max_concurrent=3,
        per_library_timeout=10.0,
    )
    
    return await prewarmer.prewarm(
        max_libraries=max_libraries,
        skip_cached=True,
        priority_filter=5,  # Only high-priority libraries
    )
