"""
Environment "doctor" checks for TappsCodingAgents.

This module validates the current environment against the canonical project config
(.tapps-agents/config.yaml) and produces warnings when tools/versions are missing
or mismatched. Per project policy, the default behavior is soft-degrade (warn/skip).
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ProjectConfig, load_config


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
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    # Some tools print version to stderr (e.g., older node/npm)
    return out if out else (err if err else None)


def collect_doctor_report(
    *,
    project_root: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
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

    typescript_enabled = bool(
        config.quality_tools and config.quality_tools.typescript_enabled
    )

    for tool, argv in tool_cmds.items():
        # Only require node/npm/npx when TS tooling is enabled.
        if tool in {"node", "npm", "npx"} and not typescript_enabled:
            continue

        exe = argv[0]
        if shutil.which(exe) is None:
            findings.append(
                DoctorFinding(
                    severity="warn" if soft_degrade else "error",
                    code="TOOL_MISSING",
                    message=f"Tool not found on PATH: {exe}",
                    remediation="Install the tool or disable the feature in .tapps-agents/config.yaml.",
                )
            )
            continue

        version_out = _run_version_cmd(argv)
        if version_out is None:
            findings.append(
                DoctorFinding(
                    severity="warn" if soft_degrade else "error",
                    code="TOOL_VERSION_UNKNOWN",
                    message=f"Could not determine version for: {exe}",
                )
            )
        else:
            findings.append(
                DoctorFinding(
                    severity="ok",
                    code="TOOL_VERSION",
                    message=f"{exe}: {version_out}",
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


