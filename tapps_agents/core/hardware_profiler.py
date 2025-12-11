"""
Hardware Profiler - Detects hardware profile and provides optimization settings.
"""

import psutil
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


class HardwareProfile(Enum):
    """Hardware profile types."""
    NUC = "nuc"  # Low resources (≤6 cores, ≤16GB RAM)
    DEVELOPMENT = "development"  # Medium resources (≤12 cores, ≤32GB RAM)
    WORKSTATION = "workstation"  # High resources (>12 cores, >32GB RAM)
    SERVER = "server"  # Variable resources, usually custom
    UNKNOWN = "unknown"  # Could not detect


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
    """Optimized cache settings for hardware profile."""
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
    emergency_cleanup_threshold: float  # Memory usage % to trigger cleanup


class HardwareProfiler:
    """Detects hardware profile and provides optimization settings."""
    
    # Optimization profiles for each hardware type
    OPTIMIZATION_PROFILES = {
        HardwareProfile.NUC: CacheOptimizationProfile(
            profile=HardwareProfile.NUC,
            tier1_ttl=180,  # 3 minutes
            tier2_ttl=60,   # 1 minute
            tier3_ttl=30,   # 30 seconds
            max_in_memory_entries=50,
            hybrid_mode=False,  # File-only for NUC
            compression_enabled=True,
            max_cache_size_mb=100,
            pre_populate=False,
            auto_refresh=False,
            index_on_startup=False,
            max_knowledge_files=100,
            enable_adaptive=True,
            resource_check_interval=30,  # Check every 30 seconds
            emergency_cleanup_threshold=0.75  # 75% memory usage
        ),
        HardwareProfile.DEVELOPMENT: CacheOptimizationProfile(
            profile=HardwareProfile.DEVELOPMENT,
            tier1_ttl=300,  # 5 minutes
            tier2_ttl=120,  # 2 minutes
            tier3_ttl=60,   # 1 minute
            max_in_memory_entries=100,
            hybrid_mode=True,  # Hybrid for development
            compression_enabled=False,
            max_cache_size_mb=200,
            pre_populate=True,
            auto_refresh=True,
            index_on_startup=True,
            max_knowledge_files=500,
            enable_adaptive=True,
            resource_check_interval=60,  # Check every minute
            emergency_cleanup_threshold=0.80  # 80% memory usage
        ),
        HardwareProfile.WORKSTATION: CacheOptimizationProfile(
            profile=HardwareProfile.WORKSTATION,
            tier1_ttl=600,  # 10 minutes
            tier2_ttl=300,  # 5 minutes
            tier3_ttl=120,  # 2 minutes
            max_in_memory_entries=200,
            hybrid_mode=True,  # Aggressive in-memory for workstation
            compression_enabled=False,
            max_cache_size_mb=500,
            pre_populate=True,
            auto_refresh=True,
            index_on_startup=True,
            max_knowledge_files=1000,
            enable_adaptive=True,
            resource_check_interval=120,  # Check every 2 minutes
            emergency_cleanup_threshold=0.85  # 85% memory usage
        ),
        HardwareProfile.SERVER: CacheOptimizationProfile(
            profile=HardwareProfile.SERVER,
            tier1_ttl=300,  # 5 minutes (default)
            tier2_ttl=120,  # 2 minutes
            tier3_ttl=60,   # 1 minute
            max_in_memory_entries=150,
            hybrid_mode=True,
            compression_enabled=False,
            max_cache_size_mb=300,
            pre_populate=True,
            auto_refresh=True,
            index_on_startup=True,
            max_knowledge_files=750,
            enable_adaptive=True,
            resource_check_interval=60,
            emergency_cleanup_threshold=0.80
        )
    }
    
    def __init__(self):
        self._cached_profile: Optional[HardwareProfile] = None
        self._cached_metrics: Optional[HardwareMetrics] = None
    
    def detect_profile(self) -> HardwareProfile:
        """
        Detect hardware profile based on system resources.
        
        Returns:
            Detected hardware profile
        """
        if self._cached_profile:
            return self._cached_profile
        
        metrics = self.get_metrics()
        self._cached_metrics = metrics
        
        # NUC: Low resources
        if metrics.cpu_cores <= 6 and metrics.ram_gb <= 16:
            profile = HardwareProfile.NUC
        # Development: Medium resources
        elif metrics.cpu_cores <= 12 and metrics.ram_gb <= 32:
            profile = HardwareProfile.DEVELOPMENT
        # Workstation: High resources
        elif metrics.cpu_cores > 12 and metrics.ram_gb > 32:
            profile = HardwareProfile.WORKSTATION
        # Server: Variable, usually custom
        else:
            profile = HardwareProfile.SERVER
        
        self._cached_profile = profile
        return profile
    
    def get_metrics(self) -> HardwareMetrics:
        """
        Get current hardware metrics.
        
        Returns:
            HardwareMetrics instance
        """
        if self._cached_metrics:
            return self._cached_metrics
        
        cpu_cores = psutil.cpu_count(logical=True)
        memory = psutil.virtual_memory()
        ram_gb = memory.total / (1024**3)
        
        # Get disk info (use root partition or current working directory)
        try:
            disk = psutil.disk_usage('/')
        except (OSError, PermissionError):
            # Try current directory
            disk = psutil.disk_usage('.')
        
        disk_total_gb = disk.total / (1024**3)
        disk_free_gb = disk.free / (1024**3)
        
        # Try to detect disk type (SSD vs HDD)
        # This is a simplified check - on Windows, we can't easily detect this
        disk_type = "ssd"  # Default assumption (most modern systems use SSD)
        
        # Get CPU architecture
        import platform
        cpu_arch = platform.machine()
        
        metrics = HardwareMetrics(
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            disk_free_gb=disk_free_gb,
            disk_total_gb=disk_total_gb,
            disk_type=disk_type,
            cpu_arch=cpu_arch
        )
        
        self._cached_metrics = metrics
        return metrics
    
    def get_optimization_profile(self, profile: Optional[HardwareProfile] = None) -> CacheOptimizationProfile:
        """
        Get optimization profile for hardware.
        
        Args:
            profile: Optional hardware profile (auto-detects if not provided)
        
        Returns:
            CacheOptimizationProfile instance
        """
        if profile is None:
            profile = self.detect_profile()
        
        return self.OPTIMIZATION_PROFILES.get(
            profile,
            self.OPTIMIZATION_PROFILES[HardwareProfile.DEVELOPMENT]  # Default fallback
        )
    
    def get_current_resource_usage(self) -> dict:
        """
        Get current resource usage metrics.
        
        Returns:
            Dictionary with current CPU, memory, and disk usage
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        try:
            disk = psutil.disk_usage('/')
        except (OSError, PermissionError):
            disk = psutil.disk_usage('.')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024**3)
        }

