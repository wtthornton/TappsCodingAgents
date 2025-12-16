"""
Project Initialization Module

Helps initialize a new project with TappsCodingAgents configuration,
Cursor Rules, and workflow presets.
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from .config import get_default_config

try:
    # Python 3.9+: importlib.resources is the canonical way to ship non-code assets.
    from importlib import resources as importlib_resources
    from importlib.resources.abc import Traversable
except Exception:  # pragma: no cover - extremely defensive
    importlib_resources = None  # type: ignore[assignment]
    Traversable = object  # type: ignore[misc,assignment]


def _resource_at(*parts: str) -> "Traversable | None":
    """
    Return a Traversable pointing at packaged resources under `tapps_agents.resources`.

    This enables `tapps-agents init` to work when the framework is installed from PyPI
    (where repo-root dot-directories like `.cursor/` and `.claude/` are not present).
    """
    if importlib_resources is None:
        return None
    try:
        root = importlib_resources.files("tapps_agents.resources")
        node: Traversable = root
        for p in parts:
            node = node / p
        return node
    except Exception:
        return None


def _copy_traversable_tree(src: "Traversable", dest: Path) -> list[str]:
    """
    Recursively copy a Traversable directory tree to a filesystem path.

    Returns a list of created file paths (as strings).
    """
    created: list[str] = []
    dest.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        target = dest / entry.name
        if entry.is_dir():
            created.extend(_copy_traversable_tree(entry, target))
        else:
            if target.exists():
                continue
            target.write_bytes(entry.read_bytes())
            created.append(str(target))
    return created


def init_project_config(project_root: Path | None = None) -> tuple[bool, str | None]:
    """
    Initialize `.tapps-agents/config.yaml` with a canonical default config.

    Returns:
        (created, path)
    """
    if project_root is None:
        project_root = Path.cwd()

    config_dir = project_root / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.yaml"
    if config_file.exists():
        return False, str(config_file)

    default_config = get_default_config()
    config_file.write_text(
        yaml.safe_dump(default_config, sort_keys=False),
        encoding="utf-8",
    )
    return True, str(config_file)


def init_cursor_rules(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Cursor Rules for the project.

    Args:
        project_root: Project root directory (defaults to cwd)
        source_dir: Source directory for rules (defaults to framework's .cursor/rules)

    Returns:
        (success, list of copied rule paths)
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        # Prefer packaged resources (works when installed from PyPI).
        packaged = _resource_at("cursor", "rules")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_rules = packaged
        else:
            packaged_rules = None
            # Fall back to repo-root `.cursor/rules` (works in source checkout).
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / ".cursor" / "rules"
    else:
        packaged_rules = None

    project_rules_dir = project_root / ".cursor" / "rules"
    project_rules_dir.mkdir(parents=True, exist_ok=True)

    # Copy Cursor Rules (workflow-presets, quick-reference, and agent-capabilities)
    rules_to_copy = [
        "workflow-presets.mdc",
        "quick-reference.mdc",
        "agent-capabilities.mdc",
        "project-context.mdc",
        "project-profiling.mdc",
    ]
    copied_rules = []

    for rule_name in rules_to_copy:
        dest_rule = project_rules_dir / rule_name
        if dest_rule.exists():
            continue

        if packaged_rules is not None:
            source_rule = packaged_rules / rule_name
            if source_rule.exists():
                dest_rule.write_bytes(source_rule.read_bytes())
                copied_rules.append(str(dest_rule))
        else:
            source_rule = source_dir / rule_name
            if source_rule.exists():
                shutil.copy2(source_rule, dest_rule)
                copied_rules.append(str(dest_rule))

    if copied_rules:
        return True, copied_rules

    return False, []


def init_workflow_presets(
    project_root: Path | None = None, source_dir: Path | None = None
):
    """
    Initialize workflow presets directory.

    Args:
        project_root: Project root directory (defaults to cwd)
        source_dir: Source directory for presets (defaults to framework's workflows/presets)
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        packaged = _resource_at("workflows", "presets")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_presets = packaged
        else:
            packaged_presets = None
            # Find framework's workflows/presets directory (source checkout).
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / "workflows" / "presets"
    else:
        packaged_presets = None

    project_presets_dir = project_root / "workflows" / "presets"
    project_presets_dir.mkdir(parents=True, exist_ok=True)

    # Copy preset files
    copied = []
    if packaged_presets is not None:
        for preset_file in packaged_presets.iterdir():
            if preset_file.is_dir() or not preset_file.name.endswith(".yaml"):
                continue
            dest_file = project_presets_dir / preset_file.name
            if dest_file.exists():
                continue
            dest_file.write_bytes(preset_file.read_bytes())
            copied.append(preset_file.name)
    else:
        if source_dir.exists():
            for preset_file in source_dir.glob("*.yaml"):
                dest_file = project_presets_dir / preset_file.name
                if not dest_file.exists():
                    shutil.copy2(preset_file, dest_file)
                    copied.append(preset_file.name)

    return len(copied) > 0, copied


def init_claude_skills(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Claude/Cursor Skills directory for a project.

    Copies framework-provided Skills from `.claude/skills/` into the target project.
    This is intentionally model-agnostic: Cursor's configured model is used at runtime.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        packaged = _resource_at("claude", "skills")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_skills = packaged
        else:
            packaged_skills = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / ".claude" / "skills"
    else:
        packaged_skills = None

    project_skills_dir = project_root / ".claude" / "skills"
    project_skills_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    if packaged_skills is not None:
        # Copy each skill folder (idempotent).
        for skill_dir in packaged_skills.iterdir():
            if not skill_dir.is_dir():
                continue
            dest_dir = project_skills_dir / skill_dir.name
            if dest_dir.exists():
                continue
            created = _copy_traversable_tree(skill_dir, dest_dir)
            if created:
                copied.append(str(dest_dir))
    else:
        if source_dir.exists():
            # Copy each skill folder (idempotent).
            for skill_dir in source_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                dest_dir = project_skills_dir / skill_dir.name
                if dest_dir.exists():
                    continue
                shutil.copytree(skill_dir, dest_dir)
                copied.append(str(dest_dir))

    return len(copied) > 0, copied


def init_background_agents_config(
    project_root: Path | None = None, source_file: Path | None = None
):
    """
    Initialize Cursor Background Agents config for a project.

    Copies `.cursor/background-agents.yaml` into the target project if it doesn't exist.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_file is None:
        packaged = _resource_at("cursor", "background-agents.yaml")
        if packaged is not None and packaged.exists() and not packaged.is_dir():
            source_file = None  # type: ignore[assignment]
            packaged_bg = packaged
        else:
            packaged_bg = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_file = framework_root / ".cursor" / "background-agents.yaml"
    else:
        packaged_bg = None

    project_cursor_dir = project_root / ".cursor"
    project_cursor_dir.mkdir(parents=True, exist_ok=True)
    dest_file = project_cursor_dir / "background-agents.yaml"

    if dest_file.exists():
        return False, str(dest_file)

    if packaged_bg is not None:
        dest_file.write_bytes(packaged_bg.read_bytes())
        return True, str(dest_file)

    if source_file.exists():
        shutil.copy2(source_file, dest_file)
        return True, str(dest_file)

    return False, None


def init_cursorignore(project_root: Path | None = None, source_file: Path | None = None):
    """
    Initialize .cursorignore file for a project.

    Copies `.cursorignore` into the target project if it doesn't exist.
    This file helps keep Cursor fast by excluding large/generated artifacts from indexing.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_file is None:
        packaged = _resource_at("cursor", ".cursorignore")
        if packaged is not None and packaged.exists() and not packaged.is_dir():
            source_file = None  # type: ignore[assignment]
            packaged_ignore = packaged
        else:
            packaged_ignore = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_file = framework_root / ".cursorignore"
    else:
        packaged_ignore = None

    dest_file = project_root / ".cursorignore"

    if dest_file.exists():
        return False, str(dest_file)

    if packaged_ignore is not None:
        dest_file.write_bytes(packaged_ignore.read_bytes())
        return True, str(dest_file)

    if source_file and source_file.exists():
        shutil.copy2(source_file, dest_file)
        return True, str(dest_file)

    return False, None


def detect_tech_stack(project_root: Path) -> dict[str, Any]:
    """
    Detect technology stack from project files.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with detected technologies and libraries
    """
    tech_stack: dict[str, Any] = {
        "languages": [],
        "frameworks": [],
        "libraries": set(),
        "package_managers": [],
        "detected_files": [],
    }

    # Python projects
    requirements_txt = project_root / "requirements.txt"
    if requirements_txt.exists():
        tech_stack["package_managers"].append("pip")
        tech_stack["languages"].append("python")
        tech_stack["detected_files"].append("requirements.txt")
        try:
            content = requirements_txt.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("git+") or line.startswith("http"):
                    continue
                match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if match:
                    lib_name = match.group(1).lower().replace("_", "-")
                    tech_stack["libraries"].add(lib_name)
        except Exception:
            pass

    pyproject_toml = project_root / "pyproject.toml"
    if pyproject_toml.exists():
        tech_stack["package_managers"].append("pip")
        tech_stack["languages"].append("python")
        tech_stack["detected_files"].append("pyproject.toml")
        try:
            content = pyproject_toml.read_text(encoding="utf-8")
            # Try to parse as TOML (simple regex-based extraction)
            deps_pattern = r'(?:dependencies|dev-dependencies)\s*=\s*\[(.*?)\]'
            matches = re.findall(deps_pattern, content, re.DOTALL)
            for match in matches:
                pkg_names = re.findall(r'["\']([^"\']+)["\']', match)
                for pkg_name in pkg_names:
                    tech_stack["libraries"].add(pkg_name.lower())
        except Exception:
            pass

    # Node.js/TypeScript projects
    package_json = project_root / "package.json"
    if package_json.exists():
        tech_stack["package_managers"].append("npm")
        tech_stack["languages"].append("javascript")
        tech_stack["detected_files"].append("package.json")
        try:
            with open(package_json, encoding="utf-8") as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}
                for dep_name in all_deps.keys():
                    normalized = dep_name.replace("@types/", "").replace("@", "")
                    tech_stack["libraries"].add(normalized)
        except Exception:
            pass

    # Convert set to sorted list
    tech_stack["libraries"] = sorted(list(tech_stack["libraries"]))

    # Detect frameworks from libraries
    frameworks_map = {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "starlette": "Starlette",
        "react": "React",
        "vue": "Vue.js",
        "angular": "Angular",
        "next": "Next.js",
        "express": "Express",
        "nestjs": "NestJS",
    }

    for lib in tech_stack["libraries"]:
        lib_lower = lib.lower()
        for key, framework in frameworks_map.items():
            if key in lib_lower:
                if framework not in tech_stack["frameworks"]:
                    tech_stack["frameworks"].append(framework)

    return tech_stack


def get_builtin_expert_libraries() -> list[str]:
    """
    Get libraries commonly used by built-in experts that should be pre-populated.

    Returns:
        List of library names used by built-in experts
    """
    expert_libraries = {
        # Security Expert
        "bandit",  # Security linter
        "safety",  # Dependency vulnerability scanner
        "cryptography",  # Cryptographic library
        "pyjwt",  # JWT handling
        "bcrypt",  # Password hashing
        # Performance Expert
        "cprofile",  # Profiling
        "memory-profiler",  # Memory profiling
        "line-profiler",  # Line-by-line profiling
        "cachetools",  # Caching utilities
        "diskcache",  # Disk-based caching
        # Testing Expert
        "pytest",  # Testing framework
        "pytest-cov",  # Coverage plugin
        "pytest-mock",  # Mocking plugin
        "pytest-asyncio",  # Async testing
        "coverage",  # Coverage analysis
        "unittest",  # Standard library testing
        "mock",  # Mocking library
        # Code Quality Expert
        "ruff",  # Fast linter
        "mypy",  # Type checker
        "pylint",  # Linter
        "black",  # Code formatter
        "radon",  # Complexity analysis
        # Database Expert
        "sqlalchemy",  # ORM
        "pymongo",  # MongoDB driver
        "psycopg2",  # PostgreSQL driver
        "redis",  # Redis client
        "sqlite3",  # SQLite (built-in, but docs available)
        # API Design Expert
        "fastapi",  # Web framework
        "flask",  # Web framework
        "django",  # Web framework
        "starlette",  # ASGI framework
        "httpx",  # HTTP client
        "requests",  # HTTP library
        "aiohttp",  # Async HTTP
        # Observability Expert
        "prometheus-client",  # Prometheus metrics
        "opentelemetry",  # Observability framework
        "structlog",  # Structured logging
        "sentry-sdk",  # Error tracking
        # Cloud Infrastructure Expert
        "boto3",  # AWS SDK
        "kubernetes",  # Kubernetes client
        "docker",  # Docker SDK
        # Data Processing (for various experts)
        "pandas",  # Data analysis
        "numpy",  # Numerical computing
        "pydantic",  # Data validation
    }
    return sorted(list(expert_libraries))


def detect_mcp_servers(project_root: Path) -> dict[str, Any]:
    """
    Detect installed and configured EXTERNAL MCP servers.
    
    Note: This only checks for external MCP servers that need installation.
    Built-in MCP servers (Filesystem, Git, Analysis) are always available
    as part of the TappsCodingAgents framework and don't need detection.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with MCP server detection results
    """
    mcp_status: dict[str, Any] = {
        "note": "Checking external MCP servers only. Built-in servers (Filesystem, Git, Analysis) are always available.",
        "required_servers": [],
        "optional_servers": [],
        "detected_servers": [],
        "missing_servers": [],
        "configuration_files": [],
        "setup_instructions": {},
    }

    # Required MCP servers
    required_servers = {
        "Context7": {
            "name": "Context7 MCP Server",
            "package": "@context7/mcp-server",
            "command": "npx",
            "description": "Library documentation resolution and retrieval",
            "required": True,
        }
    }

    # Optional MCP servers
    optional_servers = {
        "Playwright": {
            "name": "Playwright MCP Server",
            "package": "@playwright/mcp-server",
            "command": "npx",
            "description": "Browser automation (optional, Cursor may provide this)",
            "required": False,
        }
    }

    all_servers = {**required_servers, **optional_servers}

    # Check for MCP configuration files
    mcp_config_paths = [
        project_root / ".cursor" / "mcp.json",
        project_root / ".vscode" / "mcp.json",
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / ".config" / "cursor" / "mcp.json",
    ]

    mcp_config = None
    for config_path in mcp_config_paths:
        if config_path.exists():
            mcp_status["configuration_files"].append(str(config_path))
            try:
                with open(config_path, encoding="utf-8") as f:
                    mcp_config = json.load(f)
                    break
            except Exception:
                pass

    # Check for npx (required for Context7 MCP server)
    npx_available = False
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        npx_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check each server
    for server_id, server_info in all_servers.items():
        detected = False
        reason = ""

        # Check if server is in MCP config
        if mcp_config:
            mcp_servers = mcp_config.get("mcpServers", {})
            # Check for exact server ID or name match
            if server_id in mcp_servers or server_info["name"] in mcp_servers:
                detected = True
                reason = "Configured in MCP settings"
            else:
                # Check all configured servers for matches
                for server_name, server_config in mcp_servers.items():
                    # Check for package name in args (npx format)
                    args = server_config.get("args", [])
                    if server_info["package"] in args:
                        detected = True
                        reason = f"Configured as '{server_name}' in MCP settings (npx)"
                        break
                    
                    # Check for URL-based configuration (Context7 can use URL format)
                    if server_id == "Context7":
                        url = server_config.get("url", "")
                        if url and ("context7.com" in url.lower() or "context7" in url.lower()):
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings (URL)"
                            break
                        
                        # Also check for Context7 in server name (case-insensitive)
                        if "context7" in server_name.lower():
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings"
                            break
                        
                        # Check headers for Context7 API key
                        headers = server_config.get("headers", {})
                        if "CONTEXT7_API_KEY" in headers or "context7" in str(headers).lower():
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings (with API key)"
                            break

        # Check environment variables for Context7
        if server_id == "Context7":
            if os.getenv("CONTEXT7_API_KEY"):
                detected = True
                reason = "API key found in environment"
            elif not npx_available:
                reason = "npx not available (required for installation)"

        if detected:
            mcp_status["detected_servers"].append(
                {
                    "id": server_id,
                    "name": server_info["name"],
                    "status": "installed",
                    "reason": reason,
                    "required": server_info["required"],
                }
            )
        else:
            status_entry = {
                "id": server_id,
                "name": server_info["name"],
                "status": "missing",
                "required": server_info["required"],
                "package": server_info["package"],
                "description": server_info["description"],
            }
            mcp_status["missing_servers"].append(status_entry)

            # Generate setup instructions
            if server_id == "Context7":
                mcp_status["setup_instructions"][server_id] = {
                    "method": "npx",
                    "steps": [
                        "1. Install Node.js and npm (if not already installed)",
                        "2. Configure Context7 MCP server in your MCP settings:",
                        "   Location: ~/.cursor/mcp.json or .cursor/mcp.json",
                        "   Configuration:",
                        "   {",
                        '     "mcpServers": {',
                        '       "Context7": {',
                        '         "command": "npx",',
                        '         "args": ["-y", "@context7/mcp-server"],',
                        '         "env": {',
                        '           "CONTEXT7_API_KEY": "your-api-key-here"',
                        "         }",
                        "       }",
                        "     }",
                        "   }",
                        "3. Set CONTEXT7_API_KEY environment variable:",
                        "   export CONTEXT7_API_KEY='your-api-key'",
                        "4. Restart Cursor/VS Code",
                    ],
                    "alternative": "Set CONTEXT7_API_KEY environment variable for direct API access",
                }

    # Categorize servers
    for server in mcp_status["detected_servers"] + mcp_status["missing_servers"]:
        if server["required"]:
            mcp_status["required_servers"].append(server)
        else:
            mcp_status["optional_servers"].append(server)

    return mcp_status


async def pre_populate_context7_cache(
    project_root: Path, libraries: list[str] | None = None
) -> dict[str, Any]:
    """
    Pre-populate Context7 cache with project dependencies.

    Args:
        project_root: Project root directory
        libraries: Optional list of libraries to cache (auto-detected if None)

    Returns:
        Dictionary with pre-population results
    """
    try:
        from tapps_agents.context7.commands import Context7Commands
        from tapps_agents.core.config import load_config

        # Load configuration
        try:
            config = load_config(project_root)
            if not config.context7 or not config.context7.enabled:
                return {
                    "success": False,
                    "error": "Context7 is not enabled in configuration",
                    "cached": 0,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading config: {e}",
                "cached": 0,
            }

        # Initialize Context7 commands
        context7_commands = Context7Commands(project_root=project_root, config=config)

        if not context7_commands.enabled:
            return {
                "success": False,
                "error": "Context7 is not enabled",
                "cached": 0,
            }

        # Auto-detect libraries if not provided
        project_libraries = []
        if libraries is None:
            tech_stack = detect_tech_stack(project_root)
            project_libraries = tech_stack["libraries"]
        else:
            project_libraries = libraries

        # Get built-in expert libraries
        expert_libraries = get_builtin_expert_libraries()

        # Combine project libraries with expert libraries (remove duplicates)
        all_libraries = sorted(list(set(project_libraries + expert_libraries)))

        if not all_libraries:
            return {
                "success": False,
                "error": "No libraries to cache",
                "cached": 0,
            }

        # Common topics to cache for popular libraries
        common_topics_map = {
            "fastapi": ["routing", "dependency-injection", "middleware", "errors"],
            "pytest": ["fixtures", "parametrize", "markers", "async"],
            "sqlalchemy": ["models", "queries", "sessions", "relationships"],
            "django": ["models", "views", "urls", "middleware"],
            "pydantic": ["models", "validation", "serialization"],
        }

        success_count = 0
        fail_count = 0
        errors: list[str] = []

        for library in all_libraries:
            # Cache overview
            result = await context7_commands.cmd_docs(library)
            if result.get("success"):
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"{library}: {result.get('error', 'Unknown error')}")

            # Cache common topics if available
            lib_lower = library.lower()
            topics = None
            for key, topic_list in common_topics_map.items():
                if key in lib_lower:
                    topics = topic_list
                    break

            if topics:
                for topic in topics:
                    result = await context7_commands.cmd_docs(library, topic=topic)
                    if result.get("success"):
                        success_count += 1
                    else:
                        fail_count += 1
                        errors.append(
                            f"{library}/{topic}: {result.get('error', 'Unknown error')}"
                        )

        return {
            "success": success_count > 0,
            "cached": success_count,
            "failed": fail_count,
            "total": len(all_libraries),
            "project_libraries": len(project_libraries),
            "expert_libraries": len(expert_libraries),
            "errors": errors[:10],  # Limit errors shown
        }

    except ImportError:
        return {
            "success": False,
            "error": "Context7 module not available",
            "cached": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error during cache pre-population: {e}",
            "cached": 0,
        }


def init_project(
    project_root: Path | None = None,
    include_cursor_rules: bool = True,
    include_workflow_presets: bool = True,
    include_config: bool = True,
    include_skills: bool = True,
    include_background_agents: bool = True,
    include_cursorignore: bool = True,
    pre_populate_cache: bool = True,
):
    """
    Initialize a new project with TappsCodingAgents setup.

    Args:
        project_root: Project root directory (defaults to cwd)
        include_cursor_rules: Whether to copy Cursor Rules
        include_workflow_presets: Whether to copy workflow presets
        include_config: Whether to create project config
        include_skills: Whether to install Cursor Skills
        include_background_agents: Whether to install Background Agents config
        include_cursorignore: Whether to install .cursorignore file
        pre_populate_cache: Whether to pre-populate Context7 cache with detected tech stack

    Returns:
        Dictionary with initialization results
    """
    if project_root is None:
        project_root = Path.cwd()

    results: dict[str, Any] = {
        "project_root": str(project_root),
        "cursor_rules": False,
        "workflow_presets": False,
        "config": False,
        "skills": False,
        "background_agents": False,
        "cursorignore": False,
        "tech_stack": None,
        "cache_prepopulated": False,
        "files_created": [],
    }

    # Initialize project config
    if include_config:
        success, config_path = init_project_config(project_root)
        results["config"] = success
        if config_path:
            results["files_created"].append(config_path)

    # Initialize Cursor Rules
    if include_cursor_rules:
        success, rule_paths = init_cursor_rules(project_root)
        results["cursor_rules"] = success
        if rule_paths:
            results["files_created"].extend(rule_paths)

    # Initialize workflow presets
    if include_workflow_presets:
        success, preset_files = init_workflow_presets(project_root)
        results["workflow_presets"] = success
        if preset_files:
            results["files_created"].extend(
                [f"workflows/presets/{f}" for f in preset_files]
            )

    # Initialize Skills for Cursor/Claude
    if include_skills:
        success, copied_skills = init_claude_skills(project_root)
        results["skills"] = success
        if copied_skills:
            results["files_created"].extend(copied_skills)

    # Initialize Cursor Background Agents config
    if include_background_agents:
        success, bg_path = init_background_agents_config(project_root)
        results["background_agents"] = success
        if bg_path:
            results["files_created"].append(bg_path)

    # Initialize .cursorignore file
    if include_cursorignore:
        success, ignore_path = init_cursorignore(project_root)
        results["cursorignore"] = success
        if ignore_path:
            results["files_created"].append(ignore_path)

    # Detect tech stack and pre-populate cache for existing projects
    tech_stack = detect_tech_stack(project_root)
    results["tech_stack"] = tech_stack

    # Detect MCP servers
    mcp_status = detect_mcp_servers(project_root)
    results["mcp_servers"] = mcp_status

    # Pre-populate cache with expert libraries even if no project libraries detected
    # Expert libraries should always be cached for built-in experts
    if pre_populate_cache:
        try:
            cache_result = asyncio.run(
                pre_populate_context7_cache(project_root, tech_stack["libraries"])
            )
            results["cache_prepopulated"] = cache_result.get("success", False)
            results["cache_result"] = cache_result
        except Exception as e:
            results["cache_prepopulated"] = False
            results["cache_error"] = str(e)

    # Validate setup
    try:
        from .validate_cursor_setup import validate_cursor_setup

        validation = validate_cursor_setup(project_root)
        results["validation"] = validation
    except Exception as e:
        results["validation_error"] = str(e)

    return results
