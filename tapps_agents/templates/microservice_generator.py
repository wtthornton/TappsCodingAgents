"""
Microservice Template Generator

Generates complete microservice structure with Docker, tests, and health checks.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MicroserviceGenerator:
    """
    Generates microservice templates for FastAPI/Flask services.

    Creates:
    - Service structure (src/, tests/, Dockerfile, requirements.txt)
    - Docker Compose integration
    - Health check endpoints
    - Logging configuration
    - API router structure
    - Test scaffolding
    - README with service docs
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize microservice generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()

    def generate(
        self,
        service_name: str,
        port: int = 8000,
        service_type: str = "fastapi",
        features: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate microservice structure.

        Args:
            service_name: Name of the service
            port: Port number for the service
            service_type: Type of service (fastapi, flask, homeiq)
            features: Optional list of features (validation, normalization, etc.)

        Returns:
            Generation results
        """
        features = features or []
        service_path = self.project_root / "services" / service_name

        # Create directory structure
        service_path.mkdir(parents=True, exist_ok=True)
        (service_path / "src" / service_name.replace("-", "_")).mkdir(
            parents=True, exist_ok=True
        )
        (service_path / "tests").mkdir(parents=True, exist_ok=True)

        results: dict[str, Any] = {
            "service_name": service_name,
            "service_path": str(service_path),
            "files_created": [],
        }

        # Generate files based on service type
        if service_type == "fastapi":
            self._generate_fastapi_service(service_path, service_name, port, features, results)
        elif service_type == "flask":
            self._generate_flask_service(service_path, service_name, port, features, results)
        elif service_type == "homeiq":
            self._generate_homeiq_service(service_path, service_name, port, features, results)

        return results

    def _generate_fastapi_service(
        self,
        service_path: Path,
        service_name: str,
        port: int,
        features: list[str],
        results: dict[str, Any],
    ) -> None:
        """Generate FastAPI service files."""
        module_name = service_name.replace("-", "_")

        # Generate main.py
        main_content = f'''"""
{service_name} - FastAPI Service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{service_name}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "service": "{service_name}"}}

@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "{service_name} is running"}}
'''
        main_file = service_path / "src" / module_name / "main.py"
        main_file.write_text(main_content, encoding="utf-8")
        results["files_created"].append(str(main_file))

        # Generate Dockerfile
        dockerfile_content = f'''FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE {port}

CMD ["python", "-m", "uvicorn", "{module_name}.main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''
        dockerfile = service_path / "Dockerfile"
        dockerfile.write_text(dockerfile_content, encoding="utf-8")
        results["files_created"].append(str(dockerfile))

        # Generate requirements.txt
        requirements_content = "fastapi==0.104.1\nuvicorn[standard]==0.24.0\npydantic==2.5.0\n"
        requirements = service_path / "requirements.txt"
        requirements.write_text(requirements_content, encoding="utf-8")
        results["files_created"].append(str(requirements))

        # Generate test file
        test_content = f'''"""
Tests for {service_name}
"""

import pytest
from fastapi.testclient import TestClient
from {module_name}.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
'''
        test_file = service_path / "tests" / f"test_{module_name}.py"
        test_file.write_text(test_content, encoding="utf-8")
        results["files_created"].append(str(test_file))

    def _generate_flask_service(
        self,
        service_path: Path,
        service_name: str,
        port: int,
        features: list[str],
        results: dict[str, Any],
    ) -> None:
        """Generate Flask service files."""
        module_name = service_name.replace("-", "_")

        # Generate app.py
        app_content = f'''"""
{service_name} - Flask Service
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({{"status": "healthy", "service": "{service_name}"}})

@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({{"message": "{service_name} is running"}})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port={port})
'''
        app_file = service_path / "src" / module_name / "app.py"
        app_file.write_text(app_content, encoding="utf-8")
        results["files_created"].append(str(app_file))

        # Generate Dockerfile
        dockerfile_content = f'''FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE {port}

CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "--port", "{port}"]
'''
        dockerfile = service_path / "Dockerfile"
        dockerfile.write_text(dockerfile_content, encoding="utf-8")
        results["files_created"].append(str(dockerfile))

        # Generate requirements.txt
        requirements_content = "flask==3.0.0\n"
        requirements = service_path / "requirements.txt"
        requirements.write_text(requirements_content, encoding="utf-8")
        results["files_created"].append(str(requirements))

    def _generate_homeiq_service(
        self,
        service_path: Path,
        service_name: str,
        port: int,
        features: list[str],
        results: dict[str, Any],
    ) -> None:
        """Generate HomeIQ-specific service files."""
        # HomeIQ services use FastAPI with specific patterns
        self._generate_fastapi_service(service_path, service_name, port, features, results)

        # Add HomeIQ-specific configurations
        module_name = service_name.replace("-", "_")

        # Generate config.py with InfluxDB support
        config_content = '''"""
Configuration for HomeIQ service.
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    influxdb_url: str = "http://influxdb:8086"
    influxdb_token: str = ""
    influxdb_org: str = "homeiq"
    influxdb_bucket: str = "metrics"
    
    class Config:
        env_file = ".env"

settings = Settings()
'''
        config_file = service_path / "src" / module_name / "config.py"
        config_file.write_text(config_content, encoding="utf-8")
        results["files_created"].append(str(config_file))

