"""
Environment "doctor" checks for TappsCodingAgents.

This module validates the current environment against the canonical project config
(.tapps-agents/config.yaml) and produces warnings when tools/versions are missing
or mismatched. Per project policy, the default behavior is soft-degrade (warn/skip).
"""

from __future__ import annotations

import platform
import shutil
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    if config.context7.knowledge_base:
        cache_root = project_root / config.context7.knowledge_base.location
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
    tool_cmds: dict[str, list[str]] = {
        "ruff": ["ruff", "--version"],
        "mypy": ["mypy", "--version"],
        "pytest": ["pytest", "--version"],
        "pip-audit": ["pip-audit", "--version"],
        "pipdeptree": ["pipdeptree", "--version"],
        # Node ecosystem (optional, but enabled by default via QualityToolsConfig.typescript_enabled)
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "npx": ["npx", "--version"],
    }
    
    # Python tools that can be checked via 'python -m' as fallback
    python_tools = {"ruff", "mypy", "pytest", "pip-audit", "pipdeptree"}

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
        
        # Check Background Agents
        bg_agents_result = verification_results.get("components", {}).get("background_agents", {})
        if bg_agents_result.get("valid"):
            agents_count = bg_agents_result.get("agents_count", 0)
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="BACKGROUND_AGENTS",
                    message=f"Background Agents: {agents_count} agents configured",
                )
            )
        else:
            findings.append(
                DoctorFinding(
                    severity="warn",
                    code="BACKGROUND_AGENTS",
                    message="Background Agents: Config not found or invalid",
                    remediation=(
                        "Run 'tapps-agents init' to install Background Agents configuration.\n"
                        "Background Agents enable automatic workflow execution in Cursor."
                    ),
                )
            )
        
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
