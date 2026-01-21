"""
Hardware Profiler - Workstation-like defaults for optimization settings.

Hardware taxonomy (NUC, development, workstation, server, auto) has been removed.
All callers receive workstation-like behavior via detect_profile() and
get_optimization_profile(). Kept for API compatibility.
"""

from dataclasses import dataclass
from enum import Enum

import psutil


class HardwareProfile(Enum):
    """Hardware profile types. Only WORKSTATION is used; others retained for compatibility."""

    NUC = "nuc"
    DEVELOPMENT = "development"
    WORKSTATION = "workstation"
    SERVER = "server"
    UNKNOWN = "unknown"


@dataclass
class HardwareMetrics:
    """Hardware resource metrics."""

    cpu_cores: int
    ram_gb: float
    disk_free_gb: float
    disk_total_gb: float
    disk_type: str  # "ssd" or "hdd"
    cpu_arch: str


@dataclass
class CacheOptimizationProfile:
    """Optimized cache settings (workstation-like)."""

    profile: HardwareProfile

    # Tiered Context Cache
    tier1_ttl: int
    tier2_ttl: int
    tier3_ttl: int
    max_in_memory_entries: int
    hybrid_mode: bool
    compression_enabled: bool

    # Context7 KB Cache
    max_cache_size_mb: int
    pre_populate: bool
    auto_refresh: bool

    # RAG Knowledge Base
    index_on_startup: bool
    max_knowledge_files: int

    # Adaptive Settings
    enable_adaptive: bool
    resource_check_interval: int
    emergency_cleanup_threshold: float


# Single workstation-like profile used for all callers.
_WORKSTATION_PROFILE = CacheOptimizationProfile(
    profile=HardwareProfile.WORKSTATION,
    tier1_ttl=600,
    tier2_ttl=300,
    tier3_ttl=120,
    max_in_memory_entries=200,
    hybrid_mode=True,
    compression_enabled=False,
    max_cache_size_mb=500,
    pre_populate=True,
    auto_refresh=True,
    index_on_startup=True,
    max_knowledge_files=1000,
    enable_adaptive=True,
    resource_check_interval=120,
    emergency_cleanup_threshold=0.85,
)


class HardwareProfiler:
    """Provides workstation-like optimization settings. Taxonomy detection removed."""

    def __init__(self):
        self._cached_metrics: HardwareMetrics | None = None

    def detect_profile(self) -> HardwareProfile:
        """Always returns WORKSTATION. Kept for API compatibility."""
        return HardwareProfile.WORKSTATION

    def get_metrics(self) -> HardwareMetrics:
        """Get current hardware metrics."""
        if self._cached_metrics:
            return self._cached_metrics

        cpu_cores = psutil.cpu_count(logical=True) or 1
        memory = psutil.virtual_memory()
        ram_gb = memory.total / (1024**3)

        try:
            disk = psutil.disk_usage("/")
        except (OSError, PermissionError):
            disk = psutil.disk_usage(".")

        disk_total_gb = disk.total / (1024**3)
        disk_free_gb = disk.free / (1024**3)
        disk_type = "ssd"

        import platform

        cpu_arch = platform.machine()

        self._cached_metrics = HardwareMetrics(
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            disk_free_gb=disk_free_gb,
            disk_total_gb=disk_total_gb,
            disk_type=disk_type,
            cpu_arch=cpu_arch,
        )
        return self._cached_metrics

    def get_optimization_profile(
        self, profile: HardwareProfile | None = None
    ) -> CacheOptimizationProfile:
        """Always returns workstation-like profile. profile argument ignored."""
        return _WORKSTATION_PROFILE

    def get_current_resource_usage(self) -> dict:
        """Get current resource usage metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        try:
            disk = psutil.disk_usage("/")
        except (OSError, PermissionError):
            disk = psutil.disk_usage(".")

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024**3),
        }
