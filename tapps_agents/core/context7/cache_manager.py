"""Context7 Cache Manager for TappsCodingAgents.

This module manages Context7 cache population and synchronization,
integrating with tech stack detection to automatically populate
library documentation cache.

Module: Phase 2.1 - Context7 Cache Manager
From: docs/INIT_AUTOFILL_DETAILED_REQUIREMENTS.md
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from tapps_agents.context7.commands import Context7Commands
from tapps_agents.core.config import load_config


@dataclass
class FetchResult:
    """Result of a library fetch operation."""
    library: str
    success: bool
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class QueueStatus:
    """Status of the fetch queue."""
    total_queued: int = 0
    in_progress: int = 0
    completed: int = 0
    failed: int = 0
    pending_libraries: list[str] = field(default_factory=list)


class Context7CacheManager:
    """Manages Context7 cache population and synchronization.

    This manager provides a high-level API for:
    - Checking if libraries are cached
    - Queuing libraries for async fetching
    - Fetching multiple libraries with priority ordering
    - Tracking fetch queue status

    Performance target: < 1 second per library fetch
    """

    def __init__(
        self,
        project_root: Path | None = None,
        config = None,
        context7_commands: Context7Commands | None = None,
    ):
        """Initialize Context7 cache manager.

        Args:
            project_root: Root directory of project (defaults to current directory)
            config: Optional ProjectConfig instance
            context7_commands: Optional Context7Commands instance (creates if not provided)
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config(self.project_root)

        # Initialize Context7Commands
        if context7_commands:
            self.context7_commands = context7_commands
        else:
            self.context7_commands = Context7Commands(
                project_root=self.project_root,
                config=self.config
            )

        # Check if Context7 is enabled
        self.enabled = self.context7_commands.enabled

        if not self.enabled:
            # Set minimal attributes for disabled state
            self.kb_cache = None
            self.refresh_queue = None
            self._fetch_results: dict[str, FetchResult] = {}
            return

        # Get references to Context7 components
        self.kb_cache = self.context7_commands.kb_cache
        self.refresh_queue = self.context7_commands.refresh_queue

        # Track fetch results
        self._fetch_results: dict[str, FetchResult] = {}

    def check_library_cached(self, library: str, topic: str = "overview") -> bool:
        """Check if library is in Context7 cache.

        Args:
            library: Library name
            topic: Topic name (default: "overview")

        Returns:
            True if library/topic is cached, False otherwise
        """
        if not self.enabled or self.kb_cache is None:
            return False

        return self.kb_cache.exists(library, topic)

    def queue_library_fetch(
        self,
        library: str,
        topic: str | None = None,
        priority: int = 5,
        reason: str = "auto-population"
    ) -> None:
        """Queue library for Context7 fetch.

        Args:
            library: Library name
            topic: Optional topic name (None = entire library)
            priority: Priority 1-10 (higher = more urgent)
            reason: Reason for fetch (for logging/debugging)
        """
        if not self.enabled or self.refresh_queue is None:
            return

        # Add task to refresh queue
        self.refresh_queue.add_task(
            library=library,
            topic=topic,
            priority=priority,
            reason=reason
        )

    async def fetch_libraries_async(
        self,
        libraries: list[str],
        topics: list[str] | None = None,
        force: bool = False,
        max_concurrent: int = 5
    ) -> dict[str, bool]:
        """Fetch multiple libraries asynchronously.

        Args:
            libraries: List of library names to fetch
            topics: Optional list of topics (defaults to ["overview"])
            force: Whether to force refresh even if cached
            max_concurrent: Maximum concurrent fetches

        Returns:
            Dictionary mapping library names to success status
        """
        if not self.enabled:
            return {lib: False for lib in libraries}

        # Default topics if not provided
        if topics is None:
            topics = ["overview"]

        # Create semaphore for concurrent limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_library(library: str) -> tuple[str, bool]:
            """Fetch a single library with concurrency control."""
            async with semaphore:
                import time
                start_time = time.time()

                try:
                    # Use Context7Commands populate method
                    result = await self.context7_commands.cmd_populate(
                        libraries=[library],
                        topics=topics,
                        force=force
                    )

                    duration_ms = (time.time() - start_time) * 1000
                    success = result.get("success", False)

                    # Record result
                    self._fetch_results[library] = FetchResult(
                        library=library,
                        success=success,
                        error=None if success else result.get("error", "Unknown error"),
                        duration_ms=duration_ms
                    )

                    return (library, success)

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self._fetch_results[library] = FetchResult(
                        library=library,
                        success=False,
                        error=str(e),
                        duration_ms=duration_ms
                    )
                    return (library, False)

        # Fetch all libraries concurrently
        tasks = [fetch_library(lib) for lib in libraries]
        results = await asyncio.gather(*tasks)

        return {lib: success for lib, success in results}

    def get_fetch_queue_status(self) -> dict:
        """Get status of current fetch queue.

        Returns:
            Dictionary with queue status information
        """
        if not self.enabled or self.refresh_queue is None:
            return {
                "enabled": False,
                "total_queued": 0,
                "pending_libraries": []
            }

        # Get queue size
        queue_size = self.refresh_queue.size()

        # Get pending tasks
        pending_libraries = []
        for task in self.refresh_queue.tasks:
            pending_libraries.append(task.library)

        # Get fetch results summary
        total_fetched = len(self._fetch_results)
        successful_fetches = sum(
            1 for result in self._fetch_results.values()
            if result.success
        )
        failed_fetches = total_fetched - successful_fetches

        # Calculate average fetch time
        avg_fetch_time_ms = 0.0
        if total_fetched > 0:
            avg_fetch_time_ms = sum(
                result.duration_ms for result in self._fetch_results.values()
            ) / total_fetched

        return {
            "enabled": True,
            "total_queued": queue_size,
            "pending_libraries": pending_libraries,
            "fetch_statistics": {
                "total_fetched": total_fetched,
                "successful": successful_fetches,
                "failed": failed_fetches,
                "avg_fetch_time_ms": avg_fetch_time_ms
            },
            "recent_results": {
                lib: {
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                    "error": result.error
                }
                for lib, result in list(self._fetch_results.items())[-10:]
            }
        }

    async def scan_and_populate_from_tech_stack(
        self,
        tech_stack_file: Path | None = None,
        skip_cached: bool = True,
        max_concurrent: int = 5
    ) -> dict:
        """Scan tech-stack.yaml and populate missing libraries.

        Args:
            tech_stack_file: Path to tech-stack.yaml (defaults to .tapps-agents/tech-stack.yaml)
            skip_cached: Whether to skip already-cached libraries
            max_concurrent: Maximum concurrent fetches

        Returns:
            Dictionary with scan and populate results
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Context7 is not enabled"
            }

        # Determine tech-stack.yaml path
        if tech_stack_file is None:
            tech_stack_file = self.project_root / ".tapps-agents" / "tech-stack.yaml"

        if not tech_stack_file.exists():
            return {
                "success": False,
                "error": f"tech-stack.yaml not found: {tech_stack_file}"
            }

        # Load tech-stack.yaml
        try:
            with open(tech_stack_file, encoding="utf-8") as f:
                tech_stack_data = yaml.safe_load(f) or {}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load tech-stack.yaml: {e}"
            }

        # Extract libraries from tech-stack.yaml
        libraries_to_populate = set()

        # Add libraries from 'libraries' key
        if "libraries" in tech_stack_data:
            libraries_to_populate.update(tech_stack_data["libraries"])

        # Add libraries from 'frameworks' key
        if "frameworks" in tech_stack_data:
            libraries_to_populate.update(tech_stack_data["frameworks"])

        # Add libraries from 'context7_priority' key (highest priority)
        if "context7_priority" in tech_stack_data:
            libraries_to_populate.update(tech_stack_data["context7_priority"])

        # Filter out already-cached libraries if skip_cached=True
        if skip_cached:
            uncached_libraries = [
                lib for lib in libraries_to_populate
                if not self.check_library_cached(lib)
            ]
        else:
            uncached_libraries = list(libraries_to_populate)

        # Fetch libraries asynchronously
        if uncached_libraries:
            fetch_results = await self.fetch_libraries_async(
                libraries=uncached_libraries,
                max_concurrent=max_concurrent
            )
        else:
            fetch_results = {}

        return {
            "success": True,
            "total_libraries": len(libraries_to_populate),
            "already_cached": len(libraries_to_populate) - len(uncached_libraries),
            "fetched": len(uncached_libraries),
            "fetch_results": fetch_results,
            "successful_fetches": sum(1 for success in fetch_results.values() if success),
            "failed_fetches": sum(1 for success in fetch_results.values() if not success)
        }


async def main() -> None:
    """CLI entry point for Context7 cache management."""
    import argparse

    from tapps_agents.core.unicode_safe import safe_print, setup_windows_encoding

    setup_windows_encoding()

    parser = argparse.ArgumentParser(description="Manage Context7 cache population")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--scan", action="store_true", help="Scan tech-stack.yaml and populate")
    parser.add_argument("--status", action="store_true", help="Show queue status")
    parser.add_argument("--libraries", nargs="+", help="Libraries to fetch")
    parser.add_argument("--force", action="store_true", help="Force refresh even if cached")
    args = parser.parse_args()

    # Initialize cache manager
    cache_manager = Context7CacheManager(project_root=args.project_root)

    if not cache_manager.enabled:
        safe_print("[ERROR] Context7 is not enabled")
        return

    # Handle commands
    if args.status:
        status = cache_manager.get_fetch_queue_status()
        safe_print("\n=== Context7 Cache Queue Status ===")
        safe_print(f"Total Queued: {status['total_queued']}")
        safe_print(f"Pending Libraries: {', '.join(status['pending_libraries']) if status['pending_libraries'] else 'None'}")

        if status.get("fetch_statistics"):
            stats = status["fetch_statistics"]
            safe_print("\nFetch Statistics:")
            safe_print(f"  Total Fetched: {stats['total_fetched']}")
            safe_print(f"  Successful: {stats['successful']}")
            safe_print(f"  Failed: {stats['failed']}")
            safe_print(f"  Avg Time: {stats['avg_fetch_time_ms']:.1f}ms")

    elif args.scan:
        safe_print("[SCAN] Scanning tech-stack.yaml and populating cache...")
        result = await cache_manager.scan_and_populate_from_tech_stack()

        if result["success"]:
            safe_print("\n[OK] Cache population complete!")
            safe_print(f"  Total Libraries: {result['total_libraries']}")
            safe_print(f"  Already Cached: {result['already_cached']}")
            safe_print(f"  Fetched: {result['fetched']}")
            safe_print(f"  Successful: {result['successful_fetches']}")
            safe_print(f"  Failed: {result['failed_fetches']}")
        else:
            safe_print(f"\n[ERROR] {result['error']}")

    elif args.libraries:
        safe_print(f"[FETCH] Fetching libraries: {', '.join(args.libraries)}...")
        results = await cache_manager.fetch_libraries_async(
            libraries=args.libraries,
            force=args.force
        )

        safe_print("\n=== Fetch Results ===")
        for lib, success in results.items():
            status_str = "[OK]" if success else "[FAIL]"
            safe_print(f"{status_str} {lib}")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
