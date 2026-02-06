"""
Environment "doctor" checks for TappsCodingAgents.

This module validates the current environment against the canonical project config
(.tapps-agents/config.yaml) and produces warnings when tools/versions are missing
or mismatched. Per project policy, the default behavior is soft-degrade (warn/skip).
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig, load_config
from .subprocess_utils import wrap_windows_cmd_shim


@dataclass(frozen=True)
class DoctorFinding:
    severity: str  # "ok" | "warn" | "error"
    code: str
    message: str
    remediation: str | None = None


def _parse_version_tuple(version: str) -> tuple[int, ...] | None:
    parts: list[int] = []
    for piece in version.strip().split("."):
        if not piece:
            continue
        if not piece.isdigit():
            return None
        parts.append(int(piece))
    return tuple(parts) if parts else None


def _run_version_cmd(argv: list[str]) -> str | None:
    argv = wrap_windows_cmd_shim(argv)

    try:
        proc = subprocess.run(  # nosec B603
            argv,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,  # Add timeout to prevent hanging
        )
    except (subprocess.TimeoutExpired, Exception):
        return None
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    # Some tools print version to stderr (e.g., older node/npm)
    return out if out else (err if err else None)


def _check_tool_via_python_m(module_name: str) -> tuple[bool, str | None]:
    """
    Check if a tool is available via 'python -m <module_name>'.
    
    Returns:
        (is_available, version_output)
    """
    try:
        proc = subprocess.run(  # nosec B603
            [sys.executable, "-m", module_name, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if proc.returncode == 0:
            out = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            version = out if out else (err if err else None)
            return True, version
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return False, None


def _get_python_module_name(tool_name: str) -> str:
    """
    Map command-line tool names to their Python module names.
    
    Examples:
        pip-audit -> pip_audit
        pipdeptree -> pipdeptree
        ruff -> ruff
    """
    # Map of command names to module names
    module_map = {
        "pip-audit": "pip_audit",
        "pipdeptree": "pipdeptree",
    }
    return module_map.get(tool_name, tool_name.replace("-", "_"))


def _validate_background_agents_yaml(project_root: Path) -> DoctorFinding | None:
    """
    Validate background-agents.yaml file if it exists.
    
    Note: Background Agents were removed from the framework, but users may
    still have manual configurations. This function provides optional validation
    for those files without requiring framework support.
    
    Args:
        project_root: Project root directory
        
    Returns:
        DoctorFinding with validation status, or None if file doesn't exist
    """
    bg_agents_file = project_root / ".cursor" / "background-agents.yaml"
    
    if not bg_agents_file.exists():
        # File doesn't exist - this is fine, Background Agents are optional
        return None
    
    # File exists - validate YAML syntax
    try:
        content = bg_agents_file.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        
        # Basic structure validation
        if not isinstance(data, dict):
            return DoctorFinding(
                severity="warn",
                code="BACKGROUND_AGENTS",
                message="Background Agents: Config file exists but has invalid structure",
                remediation=(
                    "The .cursor/background-agents.yaml file exists but is not a valid YAML dictionary.\n"
                    "Background Agents are optional and not part of the framework.\n"
                    "If you're not using Background Agents, you can safely ignore this warning."
                ),
            )
        
        # Count agents if present
        agents = data.get("agents", [])
        if isinstance(agents, list):
            agents_count = len(agents)
            return DoctorFinding(
                severity="ok",
                code="BACKGROUND_AGENTS",
                message=f"Background Agents: Config file found with {agents_count} agent(s) (optional, not framework-managed)",
            )
        else:
            return DoctorFinding(
                severity="ok",
                code="BACKGROUND_AGENTS",
                message="Background Agents: Config file found (optional, not framework-managed)",
            )
            
    except yaml.YAMLError as e:
        return DoctorFinding(
            severity="warn",
            code="BACKGROUND_AGENTS",
            message="Background Agents: Config file has invalid YAML syntax",
            remediation=(
                f"YAML parsing error: {e}\n"
                "Background Agents are optional and not part of the framework.\n"
                "If you're not using Background Agents, you can safely ignore this warning."
            ),
        )
    except Exception as e:
        return DoctorFinding(
            severity="warn",
            code="BACKGROUND_AGENTS",
            message="Background Agents: Error reading config file",
            remediation=(
                f"Error: {e}\n"
                "Background Agents are optional and not part of the framework.\n"
                "If you're not using Background Agents, you can safely ignore this warning."
            ),
        )


def _check_context7_cache_status(
    config: ProjectConfig, project_root: Path
) -> DoctorFinding | None:
    """
    Check basic Context7 cache status for doctor command.
    
    Provides lightweight status checks:
    - Context7 enabled in config
    - Cache directory accessible
    - Cache populated (entry count)
    
    Detailed metrics remain in health check system.
    
    Args:
        config: Project configuration
        project_root: Project root directory
        
    Returns:
        DoctorFinding with cache status, or None if Context7 not available
    """
    # Check if Context7 is enabled
    if not (config.context7 and config.context7.enabled):
        return DoctorFinding(
            severity="ok",
            code="CONTEXT7_CACHE",
            message="Context7: Disabled (optional feature)",
        )
    
    # Try to import Context7 components (optional dependency)
    try:
        from ..context7.analytics import Analytics
        from ..context7.cache_structure import CacheStructure
        from ..context7.metadata import MetadataManager
    except ImportError:
        # Context7 not available - skip check
        return None
    
    # Determine cache root
    # Defensive: if knowledge_base.location is not a string (e.g. MagicMock in tests),
    # use default to avoid creating directories with mock reprs (e.g. "MagicMock/").
    if config.context7.knowledge_base:
        loc = getattr(config.context7.knowledge_base, "location", None)
        cache_root = (
            project_root / loc
            if isinstance(loc, str)
            else project_root / ".tapps-agents" / "kb" / "context7-cache"
        )
    else:
        cache_root = project_root / ".tapps-agents" / "kb" / "context7-cache"
    
    # Check cache directory existence and accessibility
    cache_exists = cache_root.exists()
    cache_writable = False
    if cache_exists:
        try:
            test_file = cache_root / ".doctor_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            cache_writable = True
        except Exception:
            cache_writable = False
    
    if not cache_exists or not cache_writable:
        return DoctorFinding(
            severity="warn",
            code="CONTEXT7_CACHE",
            message=f"Context7 Cache: Directory not accessible ({cache_root.name})",
            remediation=(
                f"Create cache directory: mkdir -p {cache_root}\n"
                f"Or fix permissions if directory exists."
            ),
        )
    
    # Get cache entry count (lightweight check)
    try:
        cache_structure = CacheStructure(cache_root)
        metadata_manager = MetadataManager(cache_structure)
        analytics = Analytics(cache_structure, metadata_manager)
        cache_metrics = analytics.get_cache_metrics()
        
        if cache_metrics.total_entries == 0:
            return DoctorFinding(
                severity="warn",
                code="CONTEXT7_CACHE",
                message="Context7 Cache: Empty (0 entries)",
                remediation=(
                    "Cache is empty. Run cache pre-population:\n"
                    "  python scripts/prepopulate_context7_cache.py\n"
                    "Or wait for automatic cache population during agent execution."
                ),
            )
        else:
            return DoctorFinding(
                severity="ok",
                code="CONTEXT7_CACHE",
                message=f"Context7 Cache: {cache_metrics.total_entries} entries, {cache_metrics.total_libraries} libraries",
            )
    except Exception:
        # If we can't get metrics, at least report directory is accessible
        return DoctorFinding(
            severity="warn",
            code="CONTEXT7_CACHE",
            message="Context7 Cache: Accessible but metrics unavailable",
            remediation="Check cache directory permissions and structure.",
        )


def _check_claude_code_integration(project_root: Path) -> list[DoctorFinding]:
    """
    Check Claude Code CLI integration status (informational, non-blocking).

    Validates:
    - .claude/settings.json exists and contains valid JSON
    - Permissions include tapps-agents commands
    - TAPPS_AGENTS_MODE environment variable is set
    - .claude/agents/ directory exists with subagent files
    - Claude Code CLI is installed (shutil.which("claude"))

    Args:
        project_root: Project root directory

    Returns:
        List of DoctorFinding objects with Claude Code status
    """
    import os

    findings: list[DoctorFinding] = []

    # 1. Check Claude Code CLI installation
    claude_on_path = shutil.which("claude") is not None
    if claude_on_path:
        version_out = _run_version_cmd(["claude", "--version"])
        version_info = f" ({version_out})" if version_out else ""
        findings.append(
            DoctorFinding(
                severity="ok",
                code="CLAUDE_CODE_CLI",
                message=f"Claude Code CLI: Installed{version_info}",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="CLAUDE_CODE_CLI",
                message="Claude Code CLI: Not found on PATH (optional)",
                remediation=(
                    "Install Claude Code CLI for terminal-based AI development.\n"
                    "See https://docs.anthropic.com/en/docs/claude-code for installation instructions."
                ),
            )
        )

    # 2. Check .claude/settings.json exists and is valid JSON
    settings_file = project_root / ".claude" / "settings.json"
    settings_local_file = project_root / ".claude" / "settings.local.json"
    settings_data: dict | None = None

    if settings_file.exists():
        try:
            content = settings_file.read_text(encoding="utf-8")
            settings_data = json.loads(content)
            if not isinstance(settings_data, dict):
                findings.append(
                    DoctorFinding(
                        severity="warn",
                        code="CLAUDE_CODE_SETTINGS",
                        message="Claude Code Settings: .claude/settings.json exists but root is not a JSON object",
                        remediation=(
                            "The .claude/settings.json file should contain a JSON object at the root level.\n"
                            "Example: {\"permissions\": {\"allow\": []}}"
                        ),
                    )
                )
                settings_data = None
            else:
                findings.append(
                    DoctorFinding(
                        severity="ok",
                        code="CLAUDE_CODE_SETTINGS",
                        message="Claude Code Settings: .claude/settings.json found (valid JSON)",
                    )
                )
        except json.JSONDecodeError as e:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CLAUDE_CODE_SETTINGS",
                    message="Claude Code Settings: .claude/settings.json has invalid JSON",
                    remediation=f"JSON parse error: {e}\nFix the JSON syntax in .claude/settings.json.",
                )
            )
        except Exception as e:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CLAUDE_CODE_SETTINGS",
                    message=f"Claude Code Settings: Error reading .claude/settings.json ({e})",
                )
            )
    elif settings_local_file.exists():
        # settings.local.json exists but settings.json does not
        findings.append(
            DoctorFinding(
                severity="ok",
                code="CLAUDE_CODE_SETTINGS",
                message="Claude Code Settings: .claude/settings.local.json found (no shared settings.json)",
                remediation=(
                    "Only .claude/settings.local.json exists (git-ignored, machine-specific).\n"
                    "Create .claude/settings.json for shared team settings if needed."
                ),
            )
        )
        # Try to load local settings for permissions check
        try:
            content = settings_local_file.read_text(encoding="utf-8")
            settings_data = json.loads(content)
            if not isinstance(settings_data, dict):
                settings_data = None
        except Exception:
            settings_data = None
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="CLAUDE_CODE_SETTINGS",
                message="Claude Code Settings: No .claude/settings.json found (optional)",
                remediation=(
                    "Create .claude/settings.json to configure Claude Code permissions and behavior.\n"
                    "Example: {\"permissions\": {\"allow\": [\"Bash(tapps-agents:*)\"]}}"
                ),
            )
        )

    # 3. Check permissions include tapps-agents commands
    if settings_data is not None:
        permissions = settings_data.get("permissions", {})
        allow_list = permissions.get("allow", [])
        if isinstance(allow_list, list):
            tapps_commands = [
                entry for entry in allow_list
                if isinstance(entry, str) and "tapps-agents" in entry
            ]
            if tapps_commands:
                findings.append(
                    DoctorFinding(
                        severity="ok",
                        code="CLAUDE_CODE_PERMISSIONS",
                        message=f"Claude Code Permissions: {len(tapps_commands)} tapps-agents permission(s) configured",
                    )
                )
            else:
                findings.append(
                    DoctorFinding(
                        severity="warn",
                        code="CLAUDE_CODE_PERMISSIONS",
                        message="Claude Code Permissions: No tapps-agents commands in allow list",
                        remediation=(
                            "Add tapps-agents commands to .claude/settings.json permissions.allow:\n"
                            '  "Bash(tapps-agents:*)" - allows all tapps-agents CLI commands\n'
                            '  "Bash(tapps-agents simple-mode:*)" - allows simple-mode commands\n'
                            "This lets Claude Code run tapps-agents workflows without manual approval."
                        ),
                    )
                )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CLAUDE_CODE_PERMISSIONS",
                    message="Claude Code Permissions: permissions.allow is not a list",
                    remediation=(
                        "The permissions.allow field should be a list of permission strings.\n"
                        'Example: {"permissions": {"allow": ["Bash(tapps-agents:*)"]}}'
                    ),
                )
            )
    # If settings_data is None, we already reported the settings file issue above

    # 4. Check TAPPS_AGENTS_MODE environment variable
    tapps_mode = os.environ.get("TAPPS_AGENTS_MODE")
    if tapps_mode:
        findings.append(
            DoctorFinding(
                severity="ok",
                code="CLAUDE_CODE_ENV",
                message=f"Claude Code Env: TAPPS_AGENTS_MODE={tapps_mode}",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="CLAUDE_CODE_ENV",
                message="Claude Code Env: TAPPS_AGENTS_MODE not set (optional)",
                remediation=(
                    "Set TAPPS_AGENTS_MODE environment variable to configure agent behavior.\n"
                    "Common values: 'cli' (for Claude Code CLI), 'cursor' (for Cursor IDE).\n"
                    "Set in shell profile or .env file."
                ),
            )
        )

    # 5. Check .claude/agents/ directory with subagent files
    agents_dir = project_root / ".claude" / "agents"
    if agents_dir.exists() and agents_dir.is_dir():
        agent_files = list(agents_dir.glob("*.md"))
        if agent_files:
            agent_names = [f.stem for f in agent_files]
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="CLAUDE_CODE_AGENTS",
                    message=f"Claude Code Agents: {len(agent_files)} subagent(s) found ({', '.join(agent_names)})",
                )
            )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CLAUDE_CODE_AGENTS",
                    message="Claude Code Agents: .claude/agents/ exists but no .md agent files found",
                    remediation=(
                        "Add subagent definition files (.md) to .claude/agents/.\n"
                        "Run 'tapps-agents init' to generate default subagent definitions."
                    ),
                )
            )
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="CLAUDE_CODE_AGENTS",
                message="Claude Code Agents: .claude/agents/ directory not found (optional)",
                remediation=(
                    "Create .claude/agents/ with subagent .md files for Claude Code team workflows.\n"
                    "Run 'tapps-agents init' to set up Claude Code integration files."
                ),
            )
        )

    return findings


def collect_doctor_report(
    *,
    project_root: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """
    Collect a comprehensive environment health check report.
    
    This function validates the current environment against the project's
    canonical configuration, checking for:
    - Required tools and their versions
    - Python version compatibility
    - Configuration file presence
    - Tool availability on PATH or via python -m
    
    Args:
        project_root: Root directory of the project. If None, uses current directory.
        config_path: Path to config file. If None, uses default location.
        
    Returns:
        Dictionary containing:
        - "findings": List of DoctorFinding objects
        - "summary": Summary statistics (ok, warn, error counts)
        - "config": Configuration that was checked against
        
    Example:
        >>> report = collect_doctor_report()
        >>> print(f"Found {len(report['findings'])} issues")
    """
    config: ProjectConfig = load_config(config_path)
    policy_mode = (config.tooling.policy.external_tools_mode or "soft").lower()
    soft_degrade = policy_mode != "hard"

    findings: list[DoctorFinding] = []

    # --- Runtime target checks ---
    target_python = config.tooling.targets.python
    running_python = ".".join(map(str, sys.version_info[:3]))
    target_tuple = _parse_version_tuple(target_python)
    running_tuple = tuple(sys.version_info[:3])

    if target_tuple is not None and running_tuple < target_tuple[:3]:
        findings.append(
            DoctorFinding(
                severity="warn" if soft_degrade else "error",
                code="PYTHON_VERSION_TOO_OLD",
                message=(
                    f"Running Python {running_python}, but project targets {target_python}."
                ),
                remediation=f"Install Python {target_python} (or newer) and recreate your venv.",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                severity="ok",
                code="PYTHON_VERSION",
                message=f"Python runtime: {running_python} (target: {target_python})",
            )
        )

    findings.append(
        DoctorFinding(
            severity="ok",
            code="PLATFORM",
            message=f"Platform: {platform.system()} {platform.release()} ({platform.machine()})",
        )
    )

    # --- External tool checks (soft degrade by default) ---
    # These are CLI tools used by reviewers/quality workflows; missing ones should warn.
    # Note: Ruff replaced Black for formatting (CI uses ruff format --check)
    tool_cmds: dict[str, list[str]] = {
        # Code quality tools (Ruff handles both lint and format)
        "ruff": ["ruff", "--version"],
        "mypy": ["mypy", "--version"],
        "pytest": ["pytest", "--version"],
        # Security & dependency tools
        "pip-audit": ["pip-audit", "--version"],
        "pipdeptree": ["pipdeptree", "--version"],
        # Version control (required for workflows, releases, git operations)
        "git": ["git", "--version"],
        # GitHub CLI (optional, used for releases)
        "gh": ["gh", "--version"],
        # Node ecosystem (optional, but enabled by default via QualityToolsConfig.typescript_enabled)
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "npx": ["npx", "--version"],
    }
    
    # Python tools that can be checked via 'python -m' as fallback
    python_tools = {"ruff", "mypy", "pytest", "pip-audit", "pipdeptree", "coverage", "build"}

    typescript_enabled = bool(
        config.quality_tools and config.quality_tools.typescript_enabled
    )

    for tool, argv in tool_cmds.items():
        # Only require node/npm/npx when TS tooling is enabled.
        if tool in {"node", "npm", "npx"} and not typescript_enabled:
            continue

        exe = argv[0]
        found_on_path = shutil.which(exe) is not None
        found_via_python_m = False
        version_out = None
        detection_method = None
        
        # Try PATH first
        if found_on_path:
            version_out = _run_version_cmd(argv)
            if version_out:
                detection_method = "PATH"
        
        # If not found on PATH (or version check failed) and it's a Python tool, try python -m
        if (not found_on_path or not version_out) and tool in python_tools:
            module_name = _get_python_module_name(tool)
            found_via_python_m, python_m_version = _check_tool_via_python_m(module_name)
            if found_via_python_m and python_m_version:
                version_out = python_m_version
                detection_method = "python -m"
        
        # Report findings
        if not found_on_path and not found_via_python_m:
            # Determine installation command based on context
            root = project_root or Path.cwd()
            pyproject_path = root / "pyproject.toml"
            is_dev_context = pyproject_path.exists()
            
            if tool in python_tools:
                module_name = _get_python_module_name(tool)
                if is_dev_context:
                    # In development context (has pyproject.toml)
                    install_cmd = 'pip install -e ".[dev]"'
                    remediation_msg = (
                        f"Install dev dependencies: {install_cmd}\n"
                        f"         Or install individually: pip install {exe}\n"
                        f"         Or disable the feature in .tapps-agents/config.yaml.\n"
                        f"         If installed, verify with: python -m {module_name} --version"
                    )
                else:
                    # Using installed package
                    install_cmd = "pip install tapps-agents[dev]"
                    remediation_msg = (
                        f"Install dev dependencies: {install_cmd}\n"
                        f"         Or install individually: pip install {exe}\n"
                        f"         Or disable the feature in .tapps-agents/config.yaml.\n"
                        f"         If installed, verify with: python -m {module_name} --version"
                    )
            else:
                remediation_msg = "Install the tool or disable the feature in .tapps-agents/config.yaml."
            
            findings.append(
                DoctorFinding(
                    severity="warn" if soft_degrade else "error",
                    code="TOOL_MISSING",
                    message=f"Tool not found on PATH: {exe}",
                    remediation=remediation_msg,
                )
            )
        elif version_out is None:
            findings.append(
                DoctorFinding(
                    severity="warn" if soft_degrade else "error",
                    code="TOOL_VERSION_UNKNOWN",
                    message=f"Could not determine version for: {exe}",
                )
            )
        else:
            # Tool found - report with detection method
            method_note = f" (via {detection_method})" if detection_method and detection_method != "PATH" else ""
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="TOOL_VERSION",
                    message=f"{exe}: {version_out}{method_note}",
                )
            )

    # --- Project root / config discovery note ---
    root = project_root or Path.cwd()
    findings.append(
        DoctorFinding(
            severity="ok",
            code="PROJECT_ROOT",
            message=f"Project root: {root}",
        )
    )

    # --- Skills & Agents (plan 1.2) ---
    try:
        from .skill_agent_registry import get_registry

        reg = get_registry(root)
        skills = reg.list_skills()
        n = len(skills)
        k = sum(1 for e in skills if e.has_workflow_handler)
        L = sum(1 for e in skills if e.is_orchestrator)
        findings.append(
            DoctorFinding(
                severity="ok",
                code="SKILLS_AGENTS",
                message=f"Skills & Agents: {n} skills ({k} with workflow handlers, {L} orchestrators)",
            )
        )
        no_path = reg.skills_with_no_execution_path()
        if no_path:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="SKILLS_AGENTS",
                    message=(
                        f"Some skills have no direct execution path: {', '.join(no_path)}. "
                        "They are invoked via @simple-mode, orchestrators, or external tools—this is expected."
                    ),
                    remediation="Use @simple-mode *build, *fix, *review, etc., or see .cursor/rules/agent-capabilities.mdc.",
                )
            )
        # Plan 2.2: tool scoping documentation
        if any(e.allowed_tools for e in skills):
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="SKILLS_AGENTS",
                    message="Skills declare allowed-tools; ensure Cursor/IDE is configured to respect tool scoping.",
                )
            )
    except Exception as e:  # pylint: disable=broad-except
        findings.append(
            DoctorFinding(
                severity="warn",
                code="SKILLS_AGENTS",
                message=f"Skills & Agents: Could not load registry: {e}",
            )
        )

    # --- MCP Server checks ---
    from .init_project import detect_mcp_servers
    try:
        mcp_status = detect_mcp_servers(root)
        
        # Check Context7 MCP
        context7_detected = any(
            s.get("id") == "Context7" and s.get("status") == "installed"
            for s in mcp_status.get("detected_servers", [])
        )
        if context7_detected:
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="MCP_CONTEXT7",
                    message="Context7 MCP: Configured",
                )
            )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="MCP_CONTEXT7",
                    message="Context7 MCP: Not configured (optional but recommended)",
                    remediation=(
                        "Configure Context7 MCP in .cursor/mcp.json for library documentation lookup.\n"
                        "Run 'tapps-agents init' to set up MCP configuration."
                    ),
                )
            )
        
        # Check Playwright MCP and capabilities
        playwright_detected = any(
            s.get("id") == "Playwright" and s.get("status") == "installed"
            for s in mcp_status.get("detected_servers", [])
        )
        if playwright_detected:
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="MCP_PLAYWRIGHT",
                    message=(
                        "Playwright MCP: Configured\n"
                        "  ✓ Browser automation available\n"
                        "  ✓ Accessibility testing (WCAG 2.2) available\n"
                        "  ✓ Performance monitoring (Core Web Vitals) available\n"
                        "  ✓ Network request analysis available"
                    ),
                )
            )
        else:
            # Check if Python Playwright is installed as fallback
            playwright_python_available = False
            try:
                import playwright  # noqa: F401
                playwright_python_available = True
            except ImportError:
                pass
            
            # Note: Cursor may provide Playwright MCP natively (not in config files)
            # If it's enabled in Cursor settings, it should work even if not detected here
            findings.append(
                DoctorFinding(
                    severity="ok" if playwright_python_available else "warn",
                    code="MCP_PLAYWRIGHT",
                    message=(
                        "Playwright MCP: Not detected in config files (optional)"
                        + (" - Python Playwright package available" if playwright_python_available else "")
                        + "\nNote: Cursor may provide Playwright MCP natively. If enabled in Cursor settings, it should work."
                    ),
                    remediation=(
                        "Playwright MCP is optional. If it's enabled in Cursor settings (Tools & MCP), it should work.\n"
                        "If not enabled, you can:\n"
                        "1. Enable it in Cursor settings (Tools & MCP), or\n"
                        "2. Configure Playwright MCP in .cursor/mcp.json:\n"
                        '   {"mcpServers": {"Playwright": {"command": "npx", "args": ["-y", "@playwright/mcp-server"]}}}, or\n'
                        "3. Install Python Playwright: pip install playwright && python -m playwright install"
                    ) if not playwright_python_available else None,
                )
            )

        # Optional: MCP count / context guidance (>10 enabled may reduce context)
        mcp_path = root / ".cursor" / "mcp.json"
        if mcp_path.exists():
            try:
                with open(mcp_path, encoding="utf-8-sig") as f:
                    mcp_cfg = json.load(f)
                servers = mcp_cfg.get("mcpServers") or {}
                n = len(servers) if isinstance(servers, dict) else 0
                if n > 10:
                    findings.append(
                        DoctorFinding(
                            severity="warn",
                            code="MCP_CONTEXT_GUIDANCE",
                            message=f"MCP/context: {n} MCP servers configured (>{10} may reduce effective context)",
                            remediation=(
                                "Consider enabling <10 MCPs per project and using disabledMcpServers or "
                                "project MCP config to disable unused ones. See .cursor/rules/performance.mdc."
                            ),
                        )
                    )
            except Exception:
                pass
    except Exception:
        # If MCP detection fails, don't fail the entire doctor report
        findings.append(
            DoctorFinding(
                severity="warn",
                code="MCP_DETECTION_ERROR",
                message="Could not detect MCP servers (check .cursor/mcp.json manually)",
            )
        )

    # --- Cursor Integration checks (what init creates) ---
    try:
        from .cursor_verification import verify_cursor_integration
        
        is_valid, verification_results = verify_cursor_integration(root)
        
        # Check Cursor Rules
        rules_result = verification_results.get("components", {}).get("rules", {})
        if rules_result.get("valid"):
            rules_found = len(rules_result.get("rules_found", []))
            expected = len(rules_result.get("expected_rules", []))
            if rules_found == expected:
                findings.append(
                    DoctorFinding(
                        severity="ok",
                        code="CURSOR_RULES",
                        message=f"Cursor Rules: {rules_found}/{expected} rules found",
                    )
                )
            else:
                findings.append(
                    DoctorFinding(
                        severity="warn",
                        code="CURSOR_RULES",
                        message=f"Cursor Rules: {rules_found}/{expected} rules found (missing {expected - rules_found})",
                        remediation=(
                            "Run 'tapps-agents init' to install missing Cursor Rules.\n"
                            "Missing rules are required for Cursor AI integration."
                        ),
                    )
                )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CURSOR_RULES",
                    message="Cursor Rules: Not found or incomplete",
                    remediation=(
                        "Run 'tapps-agents init' to install Cursor Rules.\n"
                        "Cursor Rules provide context to Cursor AI about workflow presets and agent capabilities."
                    ),
                )
            )
        
        # Check Skills
        skills_result = verification_results.get("components", {}).get("skills", {})
        if skills_result.get("valid"):
            skills_found = len(skills_result.get("skills_found", []))
            expected = len(skills_result.get("expected_skills", []))
            if skills_found == expected:
                findings.append(
                    DoctorFinding(
                        severity="ok",
                        code="CURSOR_SKILLS",
                        message=f"Cursor Skills: {skills_found}/{expected} skills found",
                    )
                )
            else:
                findings.append(
                    DoctorFinding(
                        severity="warn",
                        code="CURSOR_SKILLS",
                        message=f"Cursor Skills: {skills_found}/{expected} skills found (missing {expected - skills_found})",
                        remediation=(
                            "Run 'tapps-agents init' to install missing Cursor Skills.\n"
                            "Skills enable @agent-name commands in Cursor chat."
                        ),
                    )
                )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CURSOR_SKILLS",
                    message="Cursor Skills: Not found or incomplete",
                    remediation=(
                        "Run 'tapps-agents init' to install Cursor Skills.\n"
                        "Skills enable @agent-name commands (e.g., @reviewer, @implementer) in Cursor chat."
                    ),
                )
            )
        
        # Check Background Agents (optional - not framework-managed)
        # Note: Background Agents were removed from the framework, but users may
        # still have manual configurations. We validate the YAML file if it exists.
        bg_agents_finding = _validate_background_agents_yaml(root)
        if bg_agents_finding:
            findings.append(bg_agents_finding)
        
        # Check .cursorignore
        cursorignore_result = verification_results.get("components", {}).get("cursorignore", {})
        if cursorignore_result.get("valid"):
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="CURSORIGNORE",
                    message=".cursorignore: Found (recommended for performance)",
                )
            )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="CURSORIGNORE",
                    message=".cursorignore: Not found (optional but recommended)",
                    remediation=(
                        "Run 'tapps-agents init' to create .cursorignore.\n"
                        ".cursorignore excludes large/generated files from Cursor indexing for better performance."
                    ),
                )
            )
        
    except Exception as e:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="CURSOR_INTEGRATION_CHECK_ERROR",
                message=f"Could not verify Cursor integration: {e}",
                remediation="Run 'tapps-agents init' to set up Cursor integration components.",
            )
        )
    
    # --- Workflow Presets check ---
    from .init_project import FRAMEWORK_WORKFLOW_PRESETS
    
    presets_dir = root / "workflows" / "presets"
    if presets_dir.exists():
        preset_files = list(presets_dir.glob("*.yaml"))
        framework_presets_found = [
            p.name for p in preset_files if p.name in FRAMEWORK_WORKFLOW_PRESETS
        ]
        expected_count = len(FRAMEWORK_WORKFLOW_PRESETS)
        found_count = len(framework_presets_found)
        
        if found_count == expected_count:
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="WORKFLOW_PRESETS",
                    message=f"Workflow Presets: {found_count}/{expected_count} presets found",
                )
            )
        else:
            missing = expected_count - found_count
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="WORKFLOW_PRESETS",
                    message=f"Workflow Presets: {found_count}/{expected_count} presets found (missing {missing})",
                    remediation=(
                        "Run 'tapps-agents init' to install missing workflow presets.\n"
                        "Workflow presets define reusable workflows (full, rapid, fix, quality, hotfix)."
                    ),
                )
            )
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="WORKFLOW_PRESETS",
                message="Workflow Presets: Directory not found",
                remediation=(
                    "Run 'tapps-agents init' to install workflow presets.\n"
                    "Workflow presets define reusable workflows for common development tasks."
                ),
            )
        )
    
    # --- Config file check ---
    config_file = root / ".tapps-agents" / "config.yaml"
    if config_file.exists():
        findings.append(
            DoctorFinding(
                severity="ok",
                code="PROJECT_CONFIG",
                message="Project Config: .tapps-agents/config.yaml found",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="PROJECT_CONFIG",
                message="Project Config: .tapps-agents/config.yaml not found",
                remediation=(
                    "Run 'tapps-agents init' to create project configuration.\n"
                    "Config file contains project settings, quality thresholds, and tool configurations."
                ),
            )
        )

    # --- Context7 Cache Status check ---
    cache_status_finding = _check_context7_cache_status(config, root)
    if cache_status_finding:
        findings.append(cache_status_finding)

    # --- Sessions folder check (.tapps-agents/sessions) ---
    sessions_dir = root / ".tapps-agents" / "sessions"
    if sessions_dir.exists() and sessions_dir.is_dir():
        try:
            files = list(sessions_dir.glob("*.json"))
            count = len(files)
            total_bytes = sum(f.stat().st_size for f in files if f.is_file())
            total_mb = total_bytes / (1024 * 1024)
            # Suggest cleanup when > 100 files or > 1 MB
            if count > 100 or total_mb > 1.0:
                findings.append(
                    DoctorFinding(
                        severity="warn",
                        code="SESSIONS",
                        message=f"Sessions folder: {count} files ({total_mb:.2f} MB). Consider pruning.",
                        remediation="Run 'tapps-agents cleanup sessions' to remove old enhancer/agent sessions (use --dry-run to preview). See docs/reviews/SESSIONS_FOLDER_REVIEW.md.",
                    )
                )
            else:
                findings.append(
                    DoctorFinding(
                        severity="ok",
                        code="SESSIONS",
                        message=f"Sessions folder: {count} files ({total_mb:.2f} MB).",
                        remediation=None,
                    )
                )
        except OSError:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="SESSIONS",
                    message="Sessions folder: could not read.",
                    remediation="Check .tapps-agents/sessions permissions.",
                )
            )

    # --- Beads (bd) status check (required by default) ---
    try:
        from ..beads import is_available, is_ready, resolve_bd_path, run_bd

        b = config.beads
        beads_required = getattr(b, "required", False)
        cfg = "enabled={}, required={}, sync_epic={}, hooks_simple_mode={}, hooks_workflow={}, hooks_review={}, hooks_test={}, hooks_refactor={}".format(
            getattr(b, "enabled", False),
            beads_required,
            getattr(b, "sync_epic", False),
            getattr(b, "hooks_simple_mode", False),
            getattr(b, "hooks_workflow", False),
            getattr(b, "hooks_review", False),
            getattr(b, "hooks_test", False),
            getattr(b, "hooks_refactor", False),
        )
        if is_available(root):
            runnable = False
            try:
                for args in (["--version"], ["--help"], []):
                    r = run_bd(root, args, capture_output=True)
                    if r.returncode == 0:
                        runnable = True
                        break
            except Exception:
                pass
            ready = is_ready(root)
            if runnable:
                if ready:
                    msg = f"Beads (bd): Available (ready). {cfg}"
                else:
                    msg = f"Beads (bd): Available (run `bd init` or `bd init --stealth`). {cfg}"
                    if beads_required:
                        findings.append(
                            DoctorFinding(
                                severity="fail",
                                code="BEADS",
                                message="Beads (bd): Required but not initialized. " + msg,
                                remediation="Run 'bd init' or 'bd init --stealth', then 'bd doctor --fix'. Or set beads.required: false. See docs/BEADS_INTEGRATION.md.",
                            )
                        )
                if ready or (not beads_required and not ready):
                    rem_parts = []
                    if not getattr(b, "enabled", False):
                        rem_parts.append(
                            "To use Beads with tapps-agents, set beads.enabled: true in .tapps-agents/config.yaml. See docs/BEADS_INTEGRATION.md."
                        )
                    rem_parts.append(
                        "Run bd doctor for Beads-specific checks; bd doctor --fix to fix."
                    )
                    resolved = resolve_bd_path(root)
                    from_tools_bd = False
                    if resolved:
                        try:
                            from_tools_bd = (root / "tools" / "bd").resolve() == Path(resolved).resolve().parent
                        except Exception:
                            from_tools_bd = "tools" in resolved and "bd" in resolved
                    if from_tools_bd and not shutil.which("bd"):
                        set_bd = root / "scripts" / "set_bd_path.ps1"
                        if set_bd.exists():
                            rem_parts.append(
                                "To run bd in terminal: . .\\scripts\\set_bd_path.ps1 (Windows) or . ./scripts/set_bd_path.ps1 (Unix). Or .\\scripts\\set_bd_path.ps1 -Persist to add to User PATH."
                            )
                        else:
                            rem_parts.append(
                                "Add tools/bd to PATH to run bd in terminal. See tools/README.md and docs/BEADS_INTEGRATION.md."
                            )
                    rem = "\n".join(rem_parts) if rem_parts else None
                    findings.append(DoctorFinding(severity="ok", code="BEADS", message=msg, remediation=rem))
            else:
                msg = f"Beads (bd): Available but bd did not run. {cfg}"
                rem = "The bd binary was found but bd --version/--help failed. Reinstall bd or check dependencies. See docs/BEADS_INTEGRATION.md."
                findings.append(DoctorFinding(severity="warn", code="BEADS", message=msg, remediation=rem))
        else:
            if getattr(b, "enabled", False):
                is_required = getattr(b, "required", False)
                findings.append(
                    DoctorFinding(
                        severity="fail" if is_required else "warn",
                        code="BEADS",
                        message="Beads (bd): Not found"
                        + (" (required)" if is_required else ""),
                        remediation="beads.enabled is true"
                        + (" and beads.required is true" if is_required else "")
                        + " but bd was not found. Install bd to tools/bd or PATH, run 'bd init', or set beads.required: false (or beads.enabled: false). See docs/BEADS_INTEGRATION.md.",
                    )
                )
            else:
                findings.append(
                    DoctorFinding(
                        severity="ok",
                        code="BEADS",
                        message="Beads (bd): Not found (Beads disabled in config). See docs/BEADS_INTEGRATION.md.",
                    )
                )
    except Exception:
        findings.append(
            DoctorFinding(
                severity="ok",
                code="BEADS",
                message="Beads (bd): Not checked (error or Beads disabled). See docs/BEADS_INTEGRATION.md.",
            )
        )

    # --- Build tool check (via python -m) ---
    build_available, build_version = _check_tool_via_python_m("build")
    if build_available:
        findings.append(
            DoctorFinding(
                severity="ok",
                code="BUILD_TOOL",
                message=f"Build tool: {build_version or 'available'} (via python -m build)",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                severity="warn",
                code="BUILD_TOOL",
                message="Build tool: Not available (optional, used for package building)",
                remediation=(
                    "Install build tool: pip install build\n"
                    "Required for creating distribution packages (sdist, wheel)."
                ),
            )
        )

    # --- Python package importability checks (core dependencies) ---
    # Check if critical Python packages can be imported
    critical_packages = [
        ("pydantic", "Core framework dependency"),
        ("httpx", "HTTP client for API calls"),
        ("yaml", "YAML parsing (PyYAML)"),
        ("rich", "CLI progress bars and formatting"),
    ]
    
    for package_name, description in critical_packages:
        try:
            __import__(package_name)
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="PYTHON_PACKAGE",
                    message=f"Python package: {package_name} (importable)",
                )
            )
        except ImportError:
            findings.append(
                DoctorFinding(
                    severity="error" if not soft_degrade else "warn",
                    code="PYTHON_PACKAGE_MISSING",
                    message=f"Python package not importable: {package_name} ({description})",
                    remediation=(
                        f"Install missing package: pip install {package_name}\n"
                        f"Or reinstall tapps-agents: pip install --upgrade tapps-agents"
                    ),
                )
            )
    
    # --- Optional Python packages (used by reviewer agent) ---
    optional_packages = [
        ("radon", "Code complexity analysis (used by reviewer agent)"),
        ("bandit", "Security scanning (used by reviewer agent)"),
        ("coverage", "Test coverage analysis (used by reviewer agent)"),
    ]
    
    for package_name, description in optional_packages:
        try:
            __import__(package_name)
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="PYTHON_PACKAGE_OPTIONAL",
                    message=f"Optional package: {package_name} (available)",
                )
            )
        except ImportError:
            # These are optional - reviewer agent has fallbacks
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="PYTHON_PACKAGE_OPTIONAL_MISSING",
                    message=f"Optional package not available: {package_name} ({description})",
                    remediation=(
                        f"Install for enhanced features: pip install {package_name}\n"
                        f"Reviewer agent will use fallback methods if not available."
                    ),
                )
            )
    
    # --- Git repository check ---
    try:
        git_root = subprocess.run(  # nosec B603
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if git_root.returncode == 0:
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="GIT_REPOSITORY",
                    message=f"Git repository: {git_root.stdout.strip()}",
                )
            )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="GIT_REPOSITORY",
                    message="Not in a Git repository (optional but recommended)",
                    remediation=(
                        "Initialize Git repository: git init\n"
                        "Git is used for workflow state management, releases, and version control."
                    ),
                )
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Git not available or error - already reported in tool checks above
        pass
    
    # --- Claude Code Integration checks (informational) ---
    findings.extend(_check_claude_code_integration(root))

    # --- Write permissions check ---
    try:
        test_file = root / ".tapps-agents" / ".doctor_write_test"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        findings.append(
            DoctorFinding(
                severity="ok",
                code="WRITE_PERMISSIONS",
                message="Project directory: Writable",
            )
        )
    except (PermissionError, OSError) as e:
        findings.append(
            DoctorFinding(
                severity="error" if not soft_degrade else "warn",
                code="WRITE_PERMISSIONS",
                message=f"Project directory: Not writable ({e})",
                remediation=(
                    "Fix write permissions on project directory.\n"
                    "TappsCodingAgents needs write access for:\n"
                    "  - Workflow state files\n"
                    "  - Cache directories\n"
                    "  - Generated documentation\n"
                    "  - Configuration files"
                ),
            )
        )
    except Exception:
        # Other errors (e.g., directory doesn't exist yet) - not critical
        pass

    return {
        "policy": {
            "external_tools_mode": policy_mode,
            "soft_degrade": soft_degrade,
            "mypy_staged": config.tooling.policy.mypy_staged,
            "mypy_stage_paths": config.tooling.policy.mypy_stage_paths,
        },
        "targets": {
            "python": target_python,
            "python_requires": config.tooling.targets.python_requires,
            "os_targets": config.tooling.targets.os_targets,
            "node": config.tooling.targets.node,
        },
        "features": {
            "context7_enabled": bool(config.context7 and config.context7.enabled),
            "typescript_enabled": typescript_enabled,
        },
        "findings": [
            {
                "severity": f.severity,
                "code": f.code,
                "message": f.message,
                "remediation": f.remediation,
            }
            for f in findings
        ],
    }
