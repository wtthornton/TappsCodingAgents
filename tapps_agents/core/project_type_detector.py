"""
Project Type Detector - Detect project archetype (api-service, web-app, cli-tool, library, microservice)

This module detects project archetypes from repository signals to select appropriate
project-type templates during initialization.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project type archetypes
PROJECT_TYPES = {
    "api-service": {
        "indicators": [
            ("has_api_routes", lambda p: _has_api_indicators(p)),
            ("has_openapi", lambda p: _has_openapi_spec(p)),
            ("has_graphql", lambda p: _has_graphql_schema(p)),
            ("api_focused_structure", lambda p: _has_api_structure(p)),
        ],
        "confidence_weights": [0.3, 0.3, 0.2, 0.2],
    },
    "web-app": {
        "indicators": [
            ("has_frontend", lambda p: _has_frontend_indicators(p)),
            ("has_backend", lambda p: _has_backend_indicators(p)),
            ("has_ui_components", lambda p: _has_ui_components(p)),
            ("fullstack_structure", lambda p: _has_fullstack_structure(p)),
        ],
        "confidence_weights": [0.3, 0.3, 0.2, 0.2],
    },
    "cli-tool": {
        "indicators": [
            ("has_cli_entrypoint", lambda p: _has_cli_entrypoint(p)),
            ("has_setup_py_cli", lambda p: _has_setup_py_cli(p)),
            ("has_click_typer", lambda p: _has_click_or_typer(p)),
            ("cli_focused_structure", lambda p: _has_cli_structure(p)),
        ],
        "confidence_weights": [0.4, 0.2, 0.2, 0.2],
    },
    "library": {
        "indicators": [
            ("has_package_structure", lambda p: _has_package_structure(p)),
            ("has_setup_py_pyproject", lambda p: _has_package_manifest(p)),
            ("minimal_entrypoints", lambda p: _has_minimal_entrypoints(p)),
            ("library_focused", lambda p: _is_library_focused(p)),
        ],
        "confidence_weights": [0.3, 0.3, 0.2, 0.2],
    },
    "microservice": {
        "indicators": [
            ("has_service_boundaries", lambda p: _has_service_boundaries(p)),
            ("has_docker_k8s", lambda p: _has_container_orchestration(p)),
            ("has_service_mesh", lambda p: _has_service_mesh_indicators(p)),
            ("microservice_structure", lambda p: _has_microservice_structure(p)),
        ],
        "confidence_weights": [0.3, 0.3, 0.2, 0.2],
    },
}


def _has_api_indicators(project_root: Path) -> bool:
    """Check for API service indicators."""
    # Check for common API patterns
    api_patterns = [
        "api/",
        "routes/",
        "endpoints/",
        "controllers/",
        "app.py",  # FastAPI/Flask apps
        "main.py",  # FastAPI entrypoint
    ]
    for pattern in api_patterns:
        if (project_root / pattern).exists():
            return True
    
    # Check for API-related files
    api_files = [
        "openapi.yaml",
        "openapi.yml",
        "swagger.yaml",
        "api.yaml",
    ]
    for file in api_files:
        if (project_root / file).exists():
            return True
    
    return False


def _has_openapi_spec(project_root: Path) -> bool:
    """Check for OpenAPI/Swagger specification."""
    openapi_files = [
        "openapi.yaml",
        "openapi.yml",
        "swagger.yaml",
        "swagger.yml",
        "api.yaml",
    ]
    return any((project_root / f).exists() for f in openapi_files)


def _has_graphql_schema(project_root: Path) -> bool:
    """Check for GraphQL schema files."""
    graphql_files = [
        "schema.graphql",
        "schema.gql",
        "graphql/",
    ]
    return any((project_root / f).exists() for f in graphql_files)


def _has_api_structure(project_root: Path) -> bool:
    """Check for API-focused directory structure."""
    api_dirs = ["api/", "routes/", "endpoints/", "controllers/"]
    has_api_dir = any((project_root / d).exists() for d in api_dirs)
    
    # Check if project has API focus (no frontend, minimal UI)
    has_frontend = _has_frontend_indicators(project_root)
    
    return has_api_dir and not has_frontend


def _has_frontend_indicators(project_root: Path) -> bool:
    """Check for frontend indicators."""
    frontend_patterns = [
        "src/",
        "public/",
        "static/",
        "components/",
        "pages/",
        "app/",  # Next.js
        "index.html",
        "package.json",  # Node.js frontend
    ]
    return any((project_root / p).exists() for p in frontend_patterns)


def _has_backend_indicators(project_root: Path) -> bool:
    """Check for backend indicators."""
    backend_patterns = [
        "server/",
        "backend/",
        "api/",
        "app.py",
        "main.py",
        "requirements.txt",
        "pyproject.toml",
    ]
    return any((project_root / p).exists() for p in backend_patterns)


def _has_ui_components(project_root: Path) -> bool:
    """Check for UI component directories."""
    ui_dirs = [
        "components/",
        "src/components/",
        "app/components/",
        "ui/",
    ]
    return any((project_root / d).exists() for d in ui_dirs)


def _has_fullstack_structure(project_root: Path) -> bool:
    """Check for fullstack structure (both frontend and backend)."""
    return _has_frontend_indicators(project_root) and _has_backend_indicators(project_root)


def _has_cli_entrypoint(project_root: Path) -> bool:
    """Check for CLI entrypoint files."""
    cli_files = [
        "cli.py",
        "main.py",  # Common CLI entrypoint
        "command.py",
        "__main__.py",
    ]
    return any((project_root / f).exists() for f in cli_files)


def _has_setup_py_cli(project_root: Path) -> bool:
    """Check for CLI entry points in setup.py or pyproject.toml."""
    setup_py = project_root / "setup.py"
    pyproject_toml = project_root / "pyproject.toml"
    
    if setup_py.exists():
        content = setup_py.read_text(encoding="utf-8")
        if "console_scripts" in content or "entry_points" in content:
            return True
    
    if pyproject_toml.exists():
        try:
            # Try Python 3.11+ tomllib first
            try:
                import tomllib
                with pyproject_toml.open("rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                # Fallback to tomli for older Python
                try:
                    import tomli
                    content = pyproject_toml.read_bytes()
                    data = tomli.loads(content.decode("utf-8"))
                except ImportError:
                    # No TOML parser available, parse as text
                    content = pyproject_toml.read_text(encoding="utf-8")
                    if "console_scripts" in content or "scripts" in content:
                        return True
                    return False
            
            if "project" in data and "scripts" in data["project"]:
                return True
            if "tool" in data and "poetry" in data["tool"]:
                if "scripts" in data["tool"]["poetry"]:
                    return True
        except Exception:
            pass
    
    return False


def _has_click_or_typer(project_root: Path) -> bool:
    """Check for Click or Typer usage (CLI frameworks)."""
    # Check requirements/dependencies
    req_files = [
        project_root / "requirements.txt",
        project_root / "pyproject.toml",
        project_root / "setup.py",
    ]
    
    for req_file in req_files:
        if req_file.exists():
            content = req_file.read_text(encoding="utf-8", errors="ignore")
            if "click" in content.lower() or "typer" in content.lower():
                return True
    
    # Check for Click/Typer imports in code
    for py_file in project_root.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "import click" in content or "import typer" in content:
                return True
        except Exception:
            continue
    
    return False


def _has_cli_structure(project_root: Path) -> bool:
    """Check for CLI-focused structure."""
    has_cli_entry = _has_cli_entrypoint(project_root) or _has_setup_py_cli(project_root)
    has_cli_framework = _has_click_or_typer(project_root)
    no_web_indicators = not _has_frontend_indicators(project_root) and not _has_api_indicators(project_root)
    
    return has_cli_entry and (has_cli_framework or no_web_indicators)


def _has_package_structure(project_root: Path) -> bool:
    """Check for Python package structure."""
    # Look for package directories with __init__.py
    for item in project_root.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            init_file = item / "__init__.py"
            if init_file.exists():
                return True
    return False


def _has_package_manifest(project_root: Path) -> bool:
    """Check for package manifest files."""
    manifest_files = [
        "setup.py",
        "pyproject.toml",
        "setup.cfg",
    ]
    return any((project_root / f).exists() for f in manifest_files)


def _has_minimal_entrypoints(project_root: Path) -> bool:
    """Check for minimal entrypoints (library characteristic)."""
    # Libraries typically have few entrypoints
    entrypoint_files = [
        "main.py",
        "app.py",
        "cli.py",
        "__main__.py",
    ]
    entrypoint_count = sum(1 for f in entrypoint_files if (project_root / f).exists())
    return entrypoint_count <= 1  # Libraries have 0-1 entrypoints


def _is_library_focused(project_root: Path) -> bool:
    """Check if project is library-focused."""
    has_package = _has_package_structure(project_root)
    has_manifest = _has_package_manifest(project_root)
    minimal_entrypoints = _has_minimal_entrypoints(project_root)
    no_web = not _has_frontend_indicators(project_root) and not _has_api_indicators(project_root)
    
    return has_package and has_manifest and (minimal_entrypoints or no_web)


def _has_service_boundaries(project_root: Path) -> bool:
    """Check for microservice boundaries."""
    # Look for service directories or service-focused structure
    service_patterns = [
        "services/",
        "src/services/",
        "microservices/",
    ]
    return any((project_root / p).exists() for p in service_patterns)


def _has_container_orchestration(project_root: Path) -> bool:
    """Check for Docker/Kubernetes files."""
    container_files = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "kubernetes/",
        "k8s/",
        "deployment.yaml",
    ]
    return any((project_root / f).exists() for f in container_files)


def _has_service_mesh_indicators(project_root: Path) -> bool:
    """Check for service mesh indicators."""
    mesh_files = [
        "istio/",
        "linkerd/",
        "consul/",
    ]
    return any((project_root / f).exists() for f in mesh_files)


def _has_microservice_structure(project_root: Path) -> bool:
    """Check for microservice architecture structure."""
    has_services = _has_service_boundaries(project_root)
    has_orchestration = _has_container_orchestration(project_root)
    
    return has_services and has_orchestration


def detect_project_type(
    project_root: Path | None = None,
    tech_stack: dict[str, Any] | None = None,
) -> tuple[str | None, float, str]:
    """
    Detect project archetype from repository signals.
    
    Args:
        project_root: Project root directory
        tech_stack: Detected tech stack (optional, for additional context)
    
    Returns:
        Tuple of (project_type, confidence, reason) where:
        - project_type: Detected type (api-service, web-app, cli-tool, library, microservice) or None
        - confidence: Confidence score (0.0-1.0)
        - reason: Human-readable reason for detection
    """
    if project_root is None:
        project_root = Path.cwd()
    
    if not project_root.exists():
        return (None, 0.0, "Project root does not exist")
    
    # Score each project type
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    
    for project_type, config in PROJECT_TYPES.items():
        score = 0.0
        matched_indicators = []
        weights = config["confidence_weights"]
        
        for i, (indicator_name, check_func) in enumerate(config["indicators"]):
            try:
                if check_func(project_root):
                    weight = weights[i] if i < len(weights) else 0.25
                    score += weight
                    matched_indicators.append(indicator_name)
            except Exception as e:
                logger.debug(f"Error checking indicator {indicator_name} for {project_type}: {e}")
        
        scores[project_type] = score
        reasons[project_type] = matched_indicators
    
    # Find highest scoring type
    if not scores or max(scores.values()) < 0.3:
        return (None, 0.0, "No clear project type detected (confidence too low)")
    
    best_type = max(scores.items(), key=lambda x: x[1])
    project_type, confidence = best_type
    
    # Build reason string
    matched = reasons[project_type]
    reason = f"Detected {project_type} based on indicators: {', '.join(matched)}"
    
    return (project_type, min(1.0, confidence), reason)


def get_project_type_template_path(
    project_type: str,
    templates_dir: Path | None = None,
) -> Path | None:
    """
    Get path to project type template file.
    
    Args:
        project_type: Project type name (e.g., "api-service")
        templates_dir: Directory containing templates (optional)
    
    Returns:
        Path to template file or None if not found
    """
    if templates_dir is None:
        # Default to framework's templates directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        templates_dir = framework_root / "templates" / "project_types"
    
    template_file = templates_dir / f"{project_type}.yaml"
    if template_file.exists():
        return template_file
    
    return None


def get_available_project_types(templates_dir: Path | None = None) -> list[str]:
    """
    Get list of available project type templates.
    
    Args:
        templates_dir: Directory containing templates (optional)
    
    Returns:
        List of project type names
    """
    if templates_dir is None:
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        templates_dir = framework_root / "templates" / "project_types"
    
    if not templates_dir.exists():
        return []
    
    types = []
    for template_file in templates_dir.glob("*.yaml"):
        if template_file.name != "README.md":
            types.append(template_file.stem)
    
    return sorted(types)

