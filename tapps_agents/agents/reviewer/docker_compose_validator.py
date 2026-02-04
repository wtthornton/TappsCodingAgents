"""
Docker Compose Validator - Validates Docker Compose configurations

Phase 3.3: Microservices & FastAPI Patterns for HomeIQ
"""

from pathlib import Path
from typing import Any

import yaml


class DockerComposeValidator:
    """
    Validates Docker Compose configurations for microservice patterns.
    
    Checks for:
    - Service dependencies
    - Health checks
    - Networking patterns
    - Resource limits
    - Volume management
    """

    def __init__(self):
        """Initialize Docker Compose validator."""
        pass

    def validate_compose_file(self, compose_file: Path) -> dict[str, Any]:
        """
        Validate Docker Compose file.
        
        Args:
            compose_file: Path to docker-compose.yml file
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": list[str],
                "suggestions": list[str],
                "service_dependencies": dict,
                "health_checks": dict
            }
        """
        issues = []
        suggestions = []
        service_dependencies = {}
        health_checks = {}
        
        try:
            with open(compose_file, encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Failed to parse YAML: {e}"],
                "suggestions": [],
                "service_dependencies": {},
                "health_checks": {}
            }
        
        if not compose_data or 'services' not in compose_data:
            issues.append("No services defined in docker-compose.yml")
            return {
                "valid": False,
                "issues": issues,
                "suggestions": suggestions,
                "service_dependencies": {},
                "health_checks": {}
            }
        
        services = compose_data.get('services', {})
        
        # Check each service
        for service_name, service_config in services.items():
            # Check for health checks
            if 'healthcheck' not in service_config:
                issues.append(f"Service '{service_name}' missing health check")
                suggestions.append(
                    f"Add healthcheck to '{service_name}' for better service discovery"
                )
            else:
                health_checks[service_name] = service_config['healthcheck']
            
            # Check for dependencies
            if 'depends_on' in service_config:
                service_dependencies[service_name] = service_config['depends_on']
            else:
                suggestions.append(
                    f"Service '{service_name}' has no dependencies - consider adding depends_on"
                )
            
            # Check for resource limits
            if 'deploy' not in service_config or 'resources' not in service_config.get('deploy', {}):
                suggestions.append(
                    f"Service '{service_name}' missing resource limits - add deploy.resources"
                )
            
            # Check for environment variables
            if 'environment' not in service_config and 'env_file' not in service_config:
                suggestions.append(
                    f"Service '{service_name}' missing environment configuration"
                )
            
            # Check for networks
            if 'networks' not in service_config:
                suggestions.append(
                    f"Service '{service_name}' not explicitly assigned to network"
                )
        
        # Check for networks definition
        if 'networks' not in compose_data:
            suggestions.append("Consider defining explicit networks for service isolation")
        
        # Check for volumes definition
        if 'volumes' not in compose_data:
            suggestions.append("Consider defining named volumes for data persistence")
        
        # Check for version
        if 'version' not in compose_data:
            suggestions.append("Specify docker-compose version (e.g., '3.8')")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "service_dependencies": service_dependencies,
            "health_checks": health_checks
        }

    def review_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Review a file for Docker Compose patterns.
        
        Args:
            file_path: Path to the file
            code: File content (not used for YAML files)
            
        Returns:
            Dictionary with review results:
            {
                "is_compose_file": bool,
                "validation": dict
            }
        """
        results = {
            "is_compose_file": False,
            "validation": {}
        }
        
        # Check if file is docker-compose.yml
        if file_path.name in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']:
            results["is_compose_file"] = True
            validation = self.validate_compose_file(file_path)
            results["validation"] = validation
        
        return results

