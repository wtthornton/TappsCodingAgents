"""
Cleanup tool for TappsCodingAgents artifacts and data.

Epic 7 / Story 7.5: Operational Runbooks & Data Hygiene
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import ProjectConfig, load_config


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

    def cleanup_workflow_docs(
        self,
        keep_latest: int = 5,
        retention_days: int = 30,
        archive_dir: Path | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Clean up old workflow documentation directories.

        Args:
            keep_latest: Number of most recent workflows to keep visible (default: 5)
            retention_days: Archive workflows older than this many days (default: 30)
            archive_dir: Directory for archived workflows. If None, archival disabled.
            dry_run: If True, preview changes without making them (default: False)

        Returns:
            Dictionary with cleanup results:
            {
                "archived": int,
                "kept": int,
                "total_size_mb": float,
                "archived_workflows": list[str],
                "kept_workflows": list[str],
                "dry_run": bool,
                "errors": list[str],
            }
        """
        import sys
        import shutil
        import logging

        logger = logging.getLogger(__name__)

        workflow_base_dir = self.project_root / "docs" / "workflows" / "simple-mode"
        if not workflow_base_dir.exists():
            return {
                "archived": 0,
                "kept": 0,
                "total_size_mb": 0.0,
                "archived_workflows": [],
                "kept_workflows": [],
                "dry_run": dry_run,
                "errors": [],
            }

        # Get all workflow directories
        workflow_dirs = []
        for item in workflow_base_dir.iterdir():
            if item.is_dir() and item.name not in ["latest"]:
                # Check if it's a workflow directory (has step files or matches pattern)
                step_files = list(item.glob("step*.md"))
                if step_files or ("-" in item.name and len(item.name.split("-")) >= 2):
                    try:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        workflow_dirs.append((item, mtime))
                    except Exception as e:
                        logger.warning(f"Error getting mtime for {item}: {e}")

        # Sort by modification time (newest first)
        workflow_dirs.sort(key=lambda x: x[1], reverse=True)

        # Keep latest N workflows
        kept_workflows = workflow_dirs[:keep_latest]
        workflows_to_process = workflow_dirs[keep_latest:]

        # Process workflows for archival
        archived_count = 0
        archived_workflows = []
        kept_workflow_names = [w[0].name for w in kept_workflows]
        total_size = 0
        errors = []

        if archive_dir and retention_days > 0:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            archive_path = self.project_root / archive_dir if isinstance(archive_dir, Path) else self.project_root / Path(archive_dir)

            for workflow_dir, mtime in workflows_to_process:
                if mtime < cutoff_date:
                    try:
                        # Calculate size
                        size = sum(
                            f.stat().st_size
                            for f in workflow_dir[0].rglob("*")
                            if f.is_file()
                        )
                        total_size += size

                        if dry_run:
                            print(f"Would archive: {workflow_dir[0].name} ({size / 1024 / 1024:.2f} MB)")
                        else:
                            # Archive workflow (Windows-compatible)
                            dest_dir = archive_path / workflow_dir[0].name
                            archive_path.mkdir(parents=True, exist_ok=True)

                            if sys.platform == "win32":
                                # Windows: Copy then delete
                                shutil.copytree(workflow_dir[0], dest_dir, dirs_exist_ok=True)
                                shutil.rmtree(workflow_dir[0])
                            else:
                                # Unix: Move
                                shutil.move(str(workflow_dir[0]), str(dest_dir))

                            print(f"Archived: {workflow_dir[0].name}")
                        archived_count += 1
                        archived_workflows.append(workflow_dir[0].name)
                    except Exception as e:
                        error_msg = f"Failed to archive {workflow_dir[0].name}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)

        return {
            "archived": archived_count,
            "kept": len(kept_workflows),
            "total_size_mb": total_size / 1024 / 1024,
            "archived_workflows": archived_workflows,
            "kept_workflows": kept_workflow_names,
            "dry_run": dry_run,
            "errors": errors,
        }

    def cleanup_all(
        self,
        worktree_days: int = 7,
        analytics_days: int = 90,
        cache_days: int = 30,
        workflow_keep_latest: int | None = None,
        workflow_retention_days: int | None = None,
        workflow_archive: bool | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Clean up all artifacts.

        Args:
            worktree_days: Days to retain worktrees
            analytics_days: Days to retain analytics
            cache_days: Days to retain cache
            workflow_keep_latest: Keep N most recent workflows (None = use config)
            workflow_retention_days: Archive workflows older than N days (None = use config)
            workflow_archive: Enable archival (None = use config)
            dry_run: If True, only report what would be removed

        Returns:
            Dictionary with cleanup results
        """
        results = {
            "worktrees": self.cleanup_worktrees(worktree_days, dry_run),
            "analytics": self.cleanup_analytics(analytics_days, dry_run),
            "cache": self.cleanup_cache(cache_days, dry_run),
        }

        # Workflow docs cleanup
        workflow_config = self.config.cleanup.workflow_docs
        if workflow_config.enabled:
            keep_latest = workflow_keep_latest or workflow_config.keep_latest
            retention_days = workflow_retention_days or workflow_config.retention_days
            archive_enabled = workflow_archive if workflow_archive is not None else workflow_config.archive_enabled
            archive_dir = workflow_config.archive_dir if archive_enabled else None

            results["workflow_docs"] = self.cleanup_workflow_docs(
                keep_latest=keep_latest,
                retention_days=retention_days,
                archive_dir=archive_dir,
                dry_run=dry_run,
            )
        else:
            results["workflow_docs"] = {
                "archived": 0,
                "kept": 0,
                "total_size_mb": 0.0,
                "archived_workflows": [],
                "kept_workflows": [],
                "dry_run": dry_run,
                "errors": [],
            }

        total_removed = sum(r.get("removed", 0) for r in results.values() if isinstance(r, dict))
        total_size = sum(
            r.get("total_size", 0) if isinstance(r, dict) and "total_size" in r
            else r.get("total_size_mb", 0) * 1024 * 1024 if isinstance(r, dict) and "total_size_mb" in r
            else 0
            for r in results.values()
        )

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
