"""
Cleanup tool for TappsCodingAgents artifacts and data.

Epic 7 / Story 7.5: Operational Runbooks & Data Hygiene
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import load_config, ProjectConfig


class CleanupTool:
    """Tool for cleaning up TappsCodingAgents artifacts and data."""

    def __init__(self, project_root: Path | None = None, config: ProjectConfig | None = None):
        """
        Initialize cleanup tool.

        Args:
            project_root: Project root directory
            config: Optional project config
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()
        self.tapps_agents_dir = self.project_root / ".tapps-agents"

    def cleanup_worktrees(
        self, days: int = 7, dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Clean up old worktrees.

        Args:
            days: Remove worktrees older than this many days
            dry_run: If True, only report what would be removed

        Returns:
            Dictionary with cleanup results
        """
        worktrees_dir = self.tapps_agents_dir / "worktrees"
        if not worktrees_dir.exists():
            return {"removed": 0, "total_size": 0, "dry_run": dry_run}

        cutoff = datetime.now() - timedelta(days=days)
        removed_count = 0
        total_size = 0

        for worktree in worktrees_dir.iterdir():
            if worktree.is_dir():
                try:
                    mtime = datetime.fromtimestamp(worktree.stat().st_mtime)
                    if mtime < cutoff:
                        # Calculate size
                        size = sum(
                            f.stat().st_size
                            for f in worktree.rglob("*")
                            if f.is_file()
                        )
                        total_size += size

                        if dry_run:
                            print(f"Would remove: {worktree} ({size / 1024 / 1024:.2f} MB)")
                        else:
                            import shutil
                            shutil.rmtree(worktree)
                            print(f"Removed: {worktree}")
                        removed_count += 1
                except Exception as e:
                    print(f"Error processing {worktree}: {e}")

        return {
            "removed": removed_count,
            "total_size": total_size,
            "dry_run": dry_run,
        }

    def cleanup_analytics(
        self, days: int = 90, dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Clean up old analytics history files.

        Args:
            days: Remove files older than this many days
            dry_run: If True, only report what would be removed

        Returns:
            Dictionary with cleanup results
        """
        analytics_dir = self.tapps_agents_dir / "analytics" / "history"
        if not analytics_dir.exists():
            return {"removed": 0, "total_size": 0, "dry_run": dry_run}

        cutoff = datetime.now() - timedelta(days=days)
        removed_count = 0
        total_size = 0

        for log_file in analytics_dir.glob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    size = log_file.stat().st_size
                    total_size += size

                    if dry_run:
                        print(f"Would remove: {log_file} ({size / 1024:.2f} KB)")
                    else:
                        log_file.unlink()
                        print(f"Removed: {log_file}")
                    removed_count += 1
            except Exception as e:
                print(f"Error processing {log_file}: {e}")

        return {
            "removed": removed_count,
            "total_size": total_size,
            "dry_run": dry_run,
        }

    def cleanup_cache(
        self, days: int = 30, dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Clean up old cache entries.

        Args:
            days: Remove cache entries older than this many days
            dry_run: If True, only report what would be removed

        Returns:
            Dictionary with cleanup results
        """
        cache_dir = self.tapps_agents_dir / "cache"
        if not cache_dir.exists():
            return {"removed": 0, "total_size": 0, "dry_run": dry_run}

        cutoff = datetime.now() - timedelta(days=days)
        removed_count = 0
        total_size = 0

        for cache_file in cache_dir.rglob("*"):
            if cache_file.is_file():
                try:
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if mtime < cutoff:
                        size = cache_file.stat().st_size
                        total_size += size

                        if dry_run:
                            print(f"Would remove: {cache_file} ({size / 1024:.2f} KB)")
                        else:
                            cache_file.unlink()
                            print(f"Removed: {cache_file}")
                        removed_count += 1
                except Exception as e:
                    print(f"Error processing {cache_file}: {e}")

        return {
            "removed": removed_count,
            "total_size": total_size,
            "dry_run": dry_run,
        }

    def cleanup_all(
        self,
        worktree_days: int = 7,
        analytics_days: int = 90,
        cache_days: int = 30,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Clean up all artifacts.

        Args:
            worktree_days: Days to retain worktrees
            analytics_days: Days to retain analytics
            cache_days: Days to retain cache
            dry_run: If True, only report what would be removed

        Returns:
            Dictionary with cleanup results
        """
        results = {
            "worktrees": self.cleanup_worktrees(worktree_days, dry_run),
            "analytics": self.cleanup_analytics(analytics_days, dry_run),
            "cache": self.cleanup_cache(cache_days, dry_run),
        }

        total_removed = sum(r["removed"] for r in results.values())
        total_size = sum(r["total_size"] for r in results.values())

        results["summary"] = {
            "total_removed": total_removed,
            "total_size_mb": total_size / 1024 / 1024,
            "dry_run": dry_run,
        }

        return results


def main():
    """CLI entry point for cleanup tool."""
    parser = argparse.ArgumentParser(
        description="Cleanup TappsCodingAgents artifacts and data"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )
    parser.add_argument(
        "--worktree-days",
        type=int,
        default=7,
        help="Days to retain worktrees (default: 7)",
    )
    parser.add_argument(
        "--analytics-days",
        type=int,
        default=90,
        help="Days to retain analytics (default: 90)",
    )
    parser.add_argument(
        "--cache-days",
        type=int,
        default=30,
        help="Days to retain cache (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without removing files",
    )
    parser.add_argument(
        "--worktrees-only",
        action="store_true",
        help="Only clean up worktrees",
    )
    parser.add_argument(
        "--analytics-only",
        action="store_true",
        help="Only clean up analytics",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Only clean up cache",
    )

    args = parser.parse_args()

    tool = CleanupTool(project_root=args.project_root)

    if args.worktrees_only:
        results = tool.cleanup_worktrees(args.worktree_days, args.dry_run)
    elif args.analytics_only:
        results = tool.cleanup_analytics(args.analytics_days, args.dry_run)
    elif args.cache_only:
        results = tool.cleanup_cache(args.cache_days, args.dry_run)
    else:
        results = tool.cleanup_all(
            args.worktree_days,
            args.analytics_days,
            args.cache_days,
            args.dry_run,
        )

    if args.dry_run:
        print("\n=== Dry Run Complete ===")
        print("Run without --dry-run to perform actual cleanup")
    else:
        print("\n=== Cleanup Complete ===")

    if "summary" in results:
        summary = results["summary"]
        print(f"Total items removed: {summary['total_removed']}")
        print(f"Total size freed: {summary['total_size_mb']:.2f} MB")


if __name__ == "__main__":
    main()
