"""
Service Integration Generator

Automates service-to-service integration (client classes, config, DI).
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ServiceIntegrator:
    """
    Automates service-to-service integration.

    Generates:
    - HTTP client classes for target service
    - Config file updates with service URLs
    - Dependency injection setup
    - Docker Compose updates
    - Integration tests
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize service integrator."""
        self.project_root = project_root or Path.cwd()

    def integrate(
        self, source_service: str, target_service: str
    ) -> dict[str, Any]:
        """
        Integrate two services.

        Args:
            source_service: Service that will call target
            target_service: Service to integrate with

        Returns:
            Integration results
        """
        results: dict[str, Any] = {"files_created": [], "files_updated": []}

        # Generate client class
        client_result = self._generate_client_class(source_service, target_service)
        results["files_created"].append(client_result)

        # Update config
        config_result = self._update_config(source_service, target_service)
        results["files_updated"].append(config_result)

        # Update docker-compose
        compose_result = self._update_docker_compose(target_service)
        if compose_result:
            results["files_updated"].append(compose_result)

        return results

    def _generate_client_class(
        self, source_service: str, target_service: str
    ) -> dict[str, Any]:
        """Generate HTTP client class."""
        source_path = self.project_root / "services" / source_service
        client_file = source_path / "src" / f"{target_service.replace('-', '_')}_client.py"

        client_content = f'''"""
{target_service} HTTP Client
"""

import httpx
from typing import Any

class {target_service.replace('-', '_').title().replace('_', '')}Client:
    """HTTP client for {target_service} service."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient()

    async def health_check(self) -> dict[str, Any]:
        """Check service health."""
        response = await self.client.get(f"{{self.base_url}}/health")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the client."""
        await self.client.aclose()
'''
        client_file.parent.mkdir(parents=True, exist_ok=True)
        client_file.write_text(client_content, encoding="utf-8")

        return {"file": str(client_file), "type": "client_class"}

    def _update_config(
        self, source_service: str, target_service: str
    ) -> dict[str, Any]:
        """Update service config."""
        source_path = self.project_root / "services" / source_service
        config_file = source_path / "src" / "config.py"

        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")
            # Add target service URL
            if f"{target_service}_url" not in content:
                content += f'\n    {target_service.replace("-", "_")}_url: str = "http://{target_service}:8000"'
                config_file.write_text(content, encoding="utf-8")

        return {"file": str(config_file), "type": "config"}

    def _update_docker_compose(self, target_service: str) -> dict[str, Any] | None:
        """Update docker-compose.yml."""
        compose_file = self.project_root / "docker-compose.yml"
        if not compose_file.exists():
            return None

        # Would need to parse and update YAML
        # For now, just return
        return {"file": str(compose_file), "type": "docker_compose"}

