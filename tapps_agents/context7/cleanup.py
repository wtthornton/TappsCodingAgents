"""
KB Cleanup Automation - Automated cleanup of old/unused Context7 KB entries.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from .analytics import Analytics
from .cache_structure import CacheStructure
from .metadata import MetadataManager
from .staleness_policies import StalenessPolicyManager


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    entries_removed: int
    libraries_removed: int
    bytes_freed: int
    reason: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "entries_removed": self.entries_removed,
            "libraries_removed": self.libraries_removed,
            "bytes_freed": self.bytes_freed,
            "reason": self.reason,
            "details": self.details,
        }


class KBCleanup:
    """
    Manages automated cleanup of Context7 KB cache.
    Supports LRU eviction, size-based cleanup, and staleness-based removal.
    """

    def __init__(
        self,
        cache_structure: CacheStructure,
        metadata_manager: MetadataManager,
        staleness_policy_manager: StalenessPolicyManager,
        analytics_manager: Analytics | None = None,
        max_cache_size_bytes: int = 100 * 1024 * 1024,  # 100MB default
        max_age_days: int = 90,  # 90 days default
        min_access_days: int = 30,  # Consider unused if not accessed in 30 days
    ):
        """
        Initialize KB cleanup manager.

        Args:
            cache_structure: CacheStructure instance
            metadata_manager: MetadataManager instance
            staleness_policy_manager: StalenessPolicyManager instance
            analytics_manager: Optional AnalyticsManager instance
            max_cache_size_bytes: Maximum cache size in bytes (default: 100MB)
            max_age_days: Maximum age in days before considering for removal (default: 90)
            min_access_days: Minimum days since last access before considering unused (default: 30)
        """
        self.cache_structure = cache_structure
        self.metadata_manager = metadata_manager
        self.staleness_policy_manager = staleness_policy_manager
        self.analytics_manager = analytics_manager
        self.max_cache_size_bytes = max_cache_size_bytes
        self.max_age_days = max_age_days
        self.min_access_days = min_access_days

    def get_cache_size(self) -> int:
        """
        Calculate total cache size in bytes.

        Returns:
            Total size in bytes
        """
        total_size = 0
        for file_path in self.cache_structure.cache_root.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    def get_entry_access_info(self) -> list[tuple[str, str, datetime, int]]:
        """
        Get access information for all cached entries.

        Returns:
            List of tuples: (library, topic, last_accessed, size_bytes)
        """
        entries = []
        cache_index = self.metadata_manager.load_cache_index()

        for library_name, library_data in cache_index.libraries.items():
            topics = library_data.get("topics", {})
            for topic_name, topic_data in topics.items():
                last_accessed_str = topic_data.get("last_accessed")
                if last_accessed_str:
                    try:
                        last_accessed = datetime.fromisoformat(
                            last_accessed_str.replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                    except (ValueError, TypeError):
                        last_accessed = datetime.now(UTC) - timedelta(days=365)
                else:
                    last_accessed = datetime.now(UTC) - timedelta(days=365)

                # Get file size
                doc_file = self.cache_structure.get_library_doc_file(
                    library_name, topic_name
                )
                size_bytes = doc_file.stat().st_size if doc_file.exists() else 0

                entries.append((library_name, topic_name, last_accessed, size_bytes))

        return entries

    def cleanup_by_size(
        self, target_size_bytes: int | None = None, preserve_recent: bool = True
    ) -> CleanupResult:
        """
        Clean up cache to reduce size below target.
        Uses LRU (Least Recently Used) eviction.

        Args:
            target_size_bytes: Target size in bytes (defaults to max_cache_size_bytes)
            preserve_recent: Whether to preserve recently accessed entries

        Returns:
            CleanupResult
        """
        if target_size_bytes is None:
            target_size_bytes = self.max_cache_size_bytes

        current_size = self.get_cache_size()
        if current_size <= target_size_bytes:
            return CleanupResult(
                entries_removed=0,
                libraries_removed=0,
                bytes_freed=0,
                reason="cache_size_ok",
                details=[f"Current size {current_size} <= target {target_size_bytes}"],
            )

        bytes_to_free = current_size - target_size_bytes

        # Get all entries sorted by last access (oldest first)
        entries = self.get_entry_access_info()

        # Sort by last accessed (oldest first), then by size (largest first for efficiency)
        if preserve_recent:
            # Only consider entries not accessed in min_access_days
            cutoff_date = datetime.now(UTC) - timedelta(days=self.min_access_days)
            entries = [e for e in entries if e[2] < cutoff_date]

        entries.sort(
            key=lambda x: (x[2], -x[3])
        )  # Oldest first, largest first for same age

        removed_entries = 0
        bytes_freed = 0
        libraries_removed = set()
        details = []

        for library, topic, _, _size_bytes in entries:
            if bytes_freed >= bytes_to_free:
                break

            # Remove entry
            doc_file = self.cache_structure.get_library_doc_file(library, topic)
            if doc_file.exists():
                file_size = doc_file.stat().st_size
                doc_file.unlink()
                bytes_freed += file_size
                removed_entries += 1
                libraries_removed.add(library)
                details.append(f"Removed {library}/{topic} ({file_size} bytes)")

                # Update cache index
                self.metadata_manager.remove_from_cache_index(library, topic)

        # Remove empty library directories
        for library in libraries_removed:
            lib_dir = self.cache_structure.get_library_dir(library)
            if lib_dir.exists():
                # Check if directory is empty (except meta.yaml)
                remaining_files = [
                    f for f in lib_dir.iterdir() if f.name != "meta.yaml"
                ]
                if not remaining_files:
                    # Remove meta.yaml and directory
                    meta_file = self.cache_structure.get_library_meta_file(library)
                    if meta_file.exists():
                        meta_file.unlink()
                    lib_dir.rmdir()
                    details.append(f"Removed empty library directory: {library}")

        return CleanupResult(
            entries_removed=removed_entries,
            libraries_removed=len(libraries_removed),
            bytes_freed=bytes_freed,
            reason="size_cleanup",
            details=details,
        )

    def cleanup_by_age(
        self, max_age_days: int | None = None, ignore_staleness_policy: bool = False
    ) -> CleanupResult:
        """
        Clean up entries older than max_age_days.

        Args:
            max_age_days: Maximum age in days (defaults to self.max_age_days)
            ignore_staleness_policy: If True, ignore staleness policies and use max_age_days

        Returns:
            CleanupResult
        """
        if max_age_days is None:
            max_age_days = self.max_age_days

        cutoff_date = datetime.now(UTC) - timedelta(days=max_age_days)
        entries = self.get_entry_access_info()

        removed_entries = 0
        bytes_freed = 0
        libraries_removed = set()
        details = []

        for library, topic, last_accessed, _ in entries:
            # Check age
            if ignore_staleness_policy:
                is_too_old = last_accessed < cutoff_date
            else:
                # Use staleness policy
                library_metadata = self.metadata_manager.load_library_metadata(library)
                if library_metadata and library_metadata.last_updated:
                    try:
                        is_too_old = self.staleness_policy_manager.check_staleness(
                            library, topic, library_metadata.last_updated
                        )
                        # Also check if accessed date is too old
                        if not is_too_old:
                            is_too_old = last_accessed < cutoff_date
                    except (ValueError, TypeError):
                        is_too_old = last_accessed < cutoff_date
                else:
                    is_too_old = last_accessed < cutoff_date

            if is_too_old:
                doc_file = self.cache_structure.get_library_doc_file(library, topic)
                if doc_file.exists():
                    file_size = doc_file.stat().st_size
                    doc_file.unlink()
                    bytes_freed += file_size
                    removed_entries += 1
                    libraries_removed.add(library)
                    details.append(
                        f"Removed old entry {library}/{topic} (last accessed: {last_accessed.date()})"
                    )

                    # Update cache index
                    self.metadata_manager.remove_from_cache_index(library, topic)

        # Remove empty library directories
        for library in libraries_removed:
            lib_dir = self.cache_structure.get_library_dir(library)
            if lib_dir.exists():
                remaining_files = [
                    f for f in lib_dir.iterdir() if f.name != "meta.yaml"
                ]
                if not remaining_files:
                    meta_file = self.cache_structure.get_library_meta_file(library)
                    if meta_file.exists():
                        meta_file.unlink()
                    lib_dir.rmdir()
                    details.append(f"Removed empty library directory: {library}")

        return CleanupResult(
            entries_removed=removed_entries,
            libraries_removed=len(libraries_removed),
            bytes_freed=bytes_freed,
            reason="age_cleanup",
            details=details,
        )

    def cleanup_unused(self, min_access_days: int | None = None) -> CleanupResult:
        """
        Clean up entries that haven't been accessed recently.

        Args:
            min_access_days: Minimum days since last access (defaults to self.min_access_days)

        Returns:
            CleanupResult
        """
        if min_access_days is None:
            min_access_days = self.min_access_days

        cutoff_date = datetime.now(UTC) - timedelta(days=min_access_days)
        entries = self.get_entry_access_info()

        removed_entries = 0
        bytes_freed = 0
        libraries_removed = set()
        details = []

        for library, topic, last_accessed, _ in entries:
            if last_accessed < cutoff_date:
                doc_file = self.cache_structure.get_library_doc_file(library, topic)
                if doc_file.exists():
                    file_size = doc_file.stat().st_size
                    doc_file.unlink()
                    bytes_freed += file_size
                    removed_entries += 1
                    libraries_removed.add(library)
                    details.append(
                        f"Removed unused entry {library}/{topic} (last accessed: {last_accessed.date()})"
                    )

                    # Update cache index
                    self.metadata_manager.remove_from_cache_index(library, topic)

        # Remove empty library directories
        for library in libraries_removed:
            lib_dir = self.cache_structure.get_library_dir(library)
            if lib_dir.exists():
                remaining_files = [
                    f for f in lib_dir.iterdir() if f.name != "meta.yaml"
                ]
                if not remaining_files:
                    meta_file = self.cache_structure.get_library_meta_file(library)
                    if meta_file.exists():
                        meta_file.unlink()
                    lib_dir.rmdir()
                    details.append(f"Removed empty library directory: {library}")

        return CleanupResult(
            entries_removed=removed_entries,
            libraries_removed=len(libraries_removed),
            bytes_freed=bytes_freed,
            reason="unused_cleanup",
            details=details,
        )

    def cleanup_all(
        self,
        target_size_bytes: int | None = None,
        max_age_days: int | None = None,
        min_access_days: int | None = None,
    ) -> CleanupResult:
        """
        Perform comprehensive cleanup using all strategies.

        Args:
            target_size_bytes: Target size for size-based cleanup
            max_age_days: Maximum age for age-based cleanup
            min_access_days: Minimum access days for unused cleanup

        Returns:
            Combined CleanupResult
        """
        results = []

        # 1. Clean up by age first (oldest entries)
        age_result = self.cleanup_by_age(max_age_days=max_age_days)
        results.append(age_result)

        # 2. Clean up unused entries
        unused_result = self.cleanup_unused(min_access_days=min_access_days)
        results.append(unused_result)

        # 3. Clean up by size if still over limit
        size_result = self.cleanup_by_size(target_size_bytes=target_size_bytes)
        results.append(size_result)

        # Combine results
        total_entries_removed = sum(r.entries_removed for r in results)
        total_libraries_removed = len(
            set(
                lib
                for r in results
                for detail in r.details
                if "Removed empty library directory:" in detail
                for lib in [detail.split(":")[-1].strip()]
            )
        )
        total_bytes_freed = sum(r.bytes_freed for r in results)
        all_details = [detail for r in results for detail in r.details]

        combined_result = CleanupResult(
            entries_removed=total_entries_removed,
            libraries_removed=total_libraries_removed,
            bytes_freed=total_bytes_freed,
            reason="comprehensive_cleanup",
            details=all_details,
        )

        return combined_result

    def get_cleanup_recommendations(self) -> dict:
        """
        Get recommendations for cleanup operations.

        Returns:
            Dictionary with cleanup recommendations
        """
        current_size = self.get_cache_size()
        entries = self.get_entry_access_info()

        recs: list[dict[str, Any]] = []
        recommendations: dict[str, Any] = {
            "current_size_bytes": current_size,
            "current_size_mb": current_size / (1024 * 1024),
            "max_size_bytes": self.max_cache_size_bytes,
            "max_size_mb": self.max_cache_size_bytes / (1024 * 1024),
            "over_size_limit": current_size > self.max_cache_size_bytes,
            "total_entries": len(entries),
            "recommendations": recs,
        }

        # Check size
        if current_size > self.max_cache_size_bytes:
            bytes_to_free = current_size - self.max_cache_size_bytes
            recs.append(
                {
                    "type": "size_cleanup",
                    "priority": "high",
                    "description": f"Cache is {bytes_to_free / (1024 * 1024):.2f} MB over limit",
                    "bytes_to_free": bytes_to_free,
                }
            )

        # Check for old entries
        cutoff_date = datetime.now(UTC) - timedelta(days=self.max_age_days)
        old_entries = [e for e in entries if e[2] < cutoff_date]
        if old_entries:
            recs.append(
                {
                    "type": "age_cleanup",
                    "priority": "medium",
                    "description": f"{len(old_entries)} entries older than {self.max_age_days} days",
                    "entries_to_remove": len(old_entries),
                }
            )

        # Check for unused entries
        access_cutoff = datetime.now(UTC) - timedelta(days=self.min_access_days)
        unused_entries = [e for e in entries if e[2] < access_cutoff]
        if unused_entries:
            recs.append(
                {
                    "type": "unused_cleanup",
                    "priority": "low",
                    "description": f"{len(unused_entries)} entries not accessed in {self.min_access_days} days",
                    "entries_to_remove": len(unused_entries),
                }
            )

        return recommendations
