"""
Service Discovery - Auto-detect services in project structure

Phase 6.4.2: Multi-Service Analysis
"""

from typing import List, Optional, Dict
from pathlib import Path
import re


class ServiceDiscovery:
    """
    Discover services in a project structure.
    
    Phase 6.4.2: Multi-Service Analysis
    """
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        service_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize service discovery.
        
        Args:
            project_root: Root directory of the project (default: current directory)
            service_patterns: List of patterns to match service directories
                            (default: ['services/*/', 'src/*/', 'apps/*/'])
            exclude_patterns: List of patterns to exclude (default: ['node_modules', '.git', '__pycache__'])
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).resolve()
        
        if service_patterns is None:
            service_patterns = [
                "services/*/",
                "src/*/",
                "apps/*/",
                "microservices/*/",
                "packages/*/"
            ]
        self.service_patterns = service_patterns
        
        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules",
                ".git",
                "__pycache__",
                ".pytest_cache",
                ".venv",
                "venv",
                "env",
                ".env",
                "dist",
                "build"
            ]
        self.exclude_patterns = exclude_patterns
    
    def discover_services(self) -> List[Dict[str, any]]:
        """
        Discover all services in the project.
        
        Returns:
            List of service dictionaries with:
            - name: Service name (directory name)
            - path: Full path to service directory
            - relative_path: Relative path from project root
        """
        services = []
        
        # Try each service pattern
        for pattern in self.service_patterns:
            # Convert glob pattern to directory structure
            # e.g., "services/*/" -> "services/"
            base_dir = pattern.split('*')[0].rstrip('/')
            base_path = self.project_root / base_dir
            
            if not base_path.exists() or not base_path.is_dir():
                continue
            
            # Find all subdirectories
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue
                
                # Check exclusion patterns
                if self._should_exclude(item):
                    continue
                
                # Check if it looks like a service (has code files)
                if self._is_service_directory(item):
                    service_name = item.name
                    services.append({
                        "name": service_name,
                        "path": str(item),
                        "relative_path": str(item.relative_to(self.project_root)),
                        "pattern": pattern
                    })
        
        # Remove duplicates (services might match multiple patterns)
        seen = set()
        unique_services = []
        for service in services:
            key = service["path"]
            if key not in seen:
                seen.add(key)
                unique_services.append(service)
        
        return sorted(unique_services, key=lambda x: x["name"])
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        path_str = str(path)
        path_name = path.name
        
        # Check exclusion patterns
        for exclude_pattern in self.exclude_patterns:
            if exclude_pattern in path_str or path_name.startswith(exclude_pattern):
                return True
        
        # Exclude hidden directories
        if path_name.startswith('.'):
            return True
        
        return False
    
    def _is_service_directory(self, path: Path) -> bool:
        """
        Check if a directory looks like a service directory.
        
        A service directory should have:
        - Python files (*.py)
        - Or TypeScript files (*.ts, *.tsx)
        - Or JavaScript files (*.js, *.jsx)
        - Or a requirements.txt / package.json
        - Or a Dockerfile / docker-compose.yml
        """
        service_indicators = [
            # Code files
            "*.py",
            "*.ts",
            "*.tsx",
            "*.js",
            "*.jsx",
            # Configuration files
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "Dockerfile",
            "docker-compose.yml",
            "*.yaml",
            "*.yml"
        ]
        
        # Check for service indicators
        for indicator in service_indicators:
            if indicator.startswith("*."):
                # File extension pattern
                extension = indicator[1:]
                matches = list(path.rglob(f"*{extension}"))
                if matches:
                    # Make sure it's not just in a subdirectory like node_modules
                    for match in matches[:5]:  # Check first 5 matches
                        if not self._should_exclude(match.parent):
                            return True
            else:
                # Specific file pattern
                matches = list(path.glob(indicator))
                if matches:
                    return True
        
        return False
    
    def discover_service(self, service_name: str) -> Optional[Dict[str, any]]:
        """
        Discover a specific service by name.
        
        Args:
            service_name: Name of the service to find
            
        Returns:
            Service dictionary if found, None otherwise
        """
        services = self.discover_services()
        for service in services:
            if service["name"] == service_name:
                return service
        return None
    
    def discover_by_pattern(self, pattern: str) -> List[Dict[str, any]]:
        """
        Discover services matching a specific pattern.
        
        Args:
            pattern: Pattern to match service names (supports wildcards)
            
        Returns:
            List of matching services
        """
        services = self.discover_services()
        
        # Convert pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex = re.compile(f"^{regex_pattern}$", re.IGNORECASE)
        
        matching_services = []
        for service in services:
            if regex.match(service["name"]):
                matching_services.append(service)
        
        return matching_services


