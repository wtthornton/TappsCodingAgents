"""
Quality & Complexity Marathon Runner

Phase 0/1 focus: produce deterministic, checkpointed baseline artifacts without modifying code.

Outputs:
  - reports/baseline/*
  - reports/checkpoints/cp-000-baseline.json
  - coverage.xml (repo root) via pytest-cov

This script is designed to be resumable: if an output file already exists, the step is skipped
unless --force is provided.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class Step:
    name: str
    out_file: Path | None
    command: list[str]
    cwd: Path


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run_step(step: Step, force: bool) -> dict:
    if step.out_file is not None and step.out_file.exists() and not force:
        return {
            "name": step.name,
            "skipped": True,
            "reason": f"exists: {step.out_file.as_posix()}",
        }

    started_at = _utc_now_iso()
    proc = subprocess.run(
        step.command,
        cwd=str(step.cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    ended_at = _utc_now_iso()

    # Write stdout/stderr to a single artifact if requested.
    if step.out_file is not None:
        _ensure_dir(step.out_file.parent)
        stdout_text = proc.stdout or ""
        step.out_file.write_text(stdout_text, encoding="utf-8", errors="replace")
        # Always write stderr alongside (prevents stale *.stderr.txt from older runs).
        (step.out_file.parent / f"{step.out_file.stem}.stderr.txt").write_text(
            proc.stderr or "", encoding="utf-8", errors="replace"
        )

    return {
        "name": step.name,
        "skipped": False,
        "started_at": started_at,
        "ended_at": ended_at,
        "returncode": proc.returncode,
        "command": step.command,
    }


def _which(tool: str) -> str | None:
    # Prefer scripts in the active interpreter's environment.
    exe_dir = Path(sys.executable).resolve().parent
    candidate = exe_dir / (tool + (".exe" if os.name == "nt" else ""))
    if candidate.exists():
        return str(candidate)
    return shutil.which(tool)


def _tool_version(tool: str) -> str | None:
    exe = _which(tool)
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
        out = (proc.stdout or proc.stderr).strip()
        return out if out else None
    except Exception:
        return None


def build_baseline_steps(project_root: Path, reports_dir: Path) -> list[Step]:
    baseline_dir = reports_dir / "baseline"
    _ensure_dir(baseline_dir)

    # NOTE: We intentionally do NOT run formatting that mutates files in baseline.
    return [
        Step(
            name="black_check",
            out_file=baseline_dir / "black_check.txt",
            command=[sys.executable, "-m", "black", "--check", "--diff", "."],
            cwd=project_root,
        ),
        Step(
            name="ruff_check_json",
            out_file=baseline_dir / "ruff.json",
            command=[
                sys.executable,
                "-m",
                "ruff",
                "check",
                ".",
                "--output-format",
                "json",
            ],
            cwd=project_root,
        ),
        Step(
            name="mypy",
            out_file=baseline_dir / "mypy.txt",
            command=[sys.executable, "-m", "mypy", "tapps_agents"],
            cwd=project_root,
        ),
        Step(
            name="pytest_coverage_xml",
            out_file=baseline_dir / "pytest.txt",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--cov=tapps_agents",
                "--cov-report=xml",
            ],
            cwd=project_root,
        ),
        Step(
            name="radon_cc",
            out_file=baseline_dir / "radon_cc.txt",
            command=[sys.executable, "-m", "radon", "cc", "-s", "-a", "tapps_agents"],
            cwd=project_root,
        ),
        Step(
            name="radon_mi",
            out_file=baseline_dir / "radon_mi.txt",
            command=[sys.executable, "-m", "radon", "mi", "-s", "tapps_agents"],
            cwd=project_root,
        ),
        Step(
            name="bandit_json",
            out_file=baseline_dir / "bandit.json",
            command=[
                sys.executable,
                "-m",
                "bandit",
                "-r",
                "tapps_agents",
                "-f",
                "json",
            ],
            cwd=project_root,
        ),
        Step(
            name="pip_audit_json",
            out_file=baseline_dir / "pip_audit.json",
            command=[
                sys.executable,
                "-m",
                "pip_audit",
                "-r",
                "requirements.txt",
                "-f",
                "json",
            ],
            cwd=project_root,
        ),
        Step(
            name="reviewer_report",
            out_file=baseline_dir / "reviewer_report.json",
            command=[
                sys.executable,
                "-m",
                "tapps_agents.cli",
                "reviewer",
                "report",
                "tapps_agents",
                "all",
                "--output-dir",
                "reports/quality",
            ],
            cwd=project_root,
        ),
        Step(
            name="reviewer_analyze_project",
            out_file=baseline_dir / "reviewer_analyze_project.json",
            command=[
                sys.executable,
                "-m",
                "tapps_agents.cli",
                "reviewer",
                "analyze-project",
                "--project-root",
                str(project_root),
                "--no-comparison",
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality & Complexity Marathon Runner (baseline + checkpoints)"
    )
    parser.add_argument("--project-root", default=".", help="Project root (default: .)")
    parser.add_argument(
        "--reports-dir", default="reports", help="Reports directory (default: reports)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-run steps even if outputs exist"
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    reports_dir = (project_root / args.reports_dir).resolve()
    checkpoints_dir = reports_dir / "checkpoints"
    _ensure_dir(reports_dir / "baseline")
    _ensure_dir(checkpoints_dir)
    _ensure_dir(reports_dir / "quality")

    steps = build_baseline_steps(project_root=project_root, reports_dir=reports_dir)

    metadata = {
        "checkpoint_id": "CP-000",
        "kind": "baseline",
        "started_at": _utc_now_iso(),
        "project_root": str(project_root),
        "reports_dir": str(reports_dir),
        "platform": {
            "python": sys.version,
            "os": platform.platform(),
        },
        "tools": {
            "black": _tool_version("black"),
            "ruff": _tool_version("ruff"),
            "mypy": _tool_version("mypy"),
            "pytest": _tool_version("pytest"),
            "radon": _tool_version("radon"),
            "bandit": _tool_version("bandit"),
            "pip-audit": _tool_version("pip-audit"),
        },
        "steps": [],
    }

    any_failures = False
    for step in steps:
        result = _run_step(step, force=args.force)
        metadata["steps"].append(result)
        if not result.get("skipped") and result.get("returncode", 0) != 0:
            any_failures = True

    metadata["ended_at"] = _utc_now_iso()
    checkpoint_path = checkpoints_dir / "cp-000-baseline.json"
    checkpoint_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Non-zero exit if any step failed (useful for CI), but checkpoint is still written for diagnosis/resume.
    return 1 if any_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
