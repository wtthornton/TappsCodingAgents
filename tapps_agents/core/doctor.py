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
