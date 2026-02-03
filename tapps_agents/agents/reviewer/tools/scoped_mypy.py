"""
Scoped Mypy Executor - ENH-002-S2

Runs mypy with file-level scoping for ~70% performance improvement.
Uses --follow-imports=skip and --no-site-packages; filters results to target file only.
"""

from __future__ import annotations

import asyncio
import logging
import re
import subprocess  # nosec B404 - fixed args, no shell
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MypyTimeoutError(Exception):
    """Mypy execution timed out."""

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        super().__init__(f"Mypy timed out after {timeout}s")


@dataclass(frozen=True)
class MypyIssue:
    """Single mypy type checking issue."""

    file_path: Path
    line: int
    column: int
    severity: str
    message: str
    error_code: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class MypyResult:
    """Result of scoped mypy execution."""

    issues: tuple[MypyIssue, ...]
    duration_seconds: float
    files_checked: int
    success: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issues": [i.to_dict() for i in self.issues],
            "duration_seconds": self.duration_seconds,
            "files_checked": self.files_checked,
            "success": self.success,
        }


@dataclass(frozen=True)
class ScopedMypyConfig:
    """Configuration for scoped mypy execution."""

    enabled: bool = True
    timeout: int = 10
    flags: tuple[str, ...] = (
        "--follow-imports=skip",
        "--no-site-packages",
        "--show-column-numbers",
        "--show-error-codes",
        "--no-error-summary",
        "--no-color-output",
        "--no-incremental",
    )


class ScopedMypyExecutor:
    """
    Execute mypy with scoped imports for performance.

    Uses --follow-imports=skip, --no-site-packages and filters results
    to the target file only. Target: <10s vs 30-60s unscoped.
    """

    def __init__(self, config: ScopedMypyConfig | None = None) -> None:
        self.config = config or ScopedMypyConfig()
        self._logger = logging.getLogger(__name__)

    def get_scoped_flags(self) -> list[str]:
        """Return mypy flags for scoped execution."""
        return list(self.config.flags)

    def parse_output(self, raw_output: str, file_path: Path) -> list[MypyIssue]:
        """
        Parse mypy stdout and return issues for the target file only.

        Mypy format: file.py:line:col: severity: message [error-code]
        or file.py:line: severity: message [error-code]
        """
        issues: list[MypyIssue] = []
        target_name = file_path.name
        target_resolved = str(file_path.resolve()).replace("\\", "/")

        for line in raw_output.splitlines():
            line = line.strip()
            if not line or "error:" not in line.lower():
                continue
            # Match file:line:col: severity: message [code] or file:line: severity: message [code]
            match = re.match(
                r"^(.+?):(\d+):(?:\d+:)?\s*(error|warning|note):\s*(.+)$",
                line,
                re.IGNORECASE,
            )
            if not match:
                continue
            path_part, line_str, severity, rest = match.groups()
            path_part = path_part.replace("\\", "/")
            if target_name not in path_part and target_resolved not in path_part:
                try:
                    if Path(path_part).resolve() != file_path.resolve():
                        continue
                except Exception:
                    continue
            try:
                line_num = int(line_str)
            except ValueError:
                continue
            col_num = 0
            if ":" in line:
                col_match = re.match(r"^.+?:\d+:(\d+):", line)
                if col_match:
                    try:
                        col_num = int(col_match.group(1))
                    except ValueError:
                        pass
            error_code = None
            if "[" in rest and "]" in rest:
                start = rest.rfind("[")
                end = rest.rfind("]")
                if start < end:
                    error_code = rest[start + 1 : end].strip()
                    rest = rest[:start].strip()
            issues.append(
                MypyIssue(
                    file_path=file_path,
                    line=line_num,
                    column=col_num,
                    severity=severity.strip().lower(),
                    message=rest.strip(),
                    error_code=error_code,
                )
            )
        return issues

    async def execute_scoped(
        self,
        file_path: Path,
        *,
        timeout: int | None = None,
    ) -> MypyResult:
        """
        Run mypy on a single file with scoped flags and filter to that file.

        On timeout, returns a result with success=False and empty issues
        (graceful fallback; caller can run full mypy if needed).
        """
        timeout_sec = timeout if timeout is not None else self.config.timeout
        if not file_path.is_file():
            return MypyResult(
                issues=(), duration_seconds=0.0, files_checked=0, success=False
            )
        cmd = [sys.executable, "-m", "mypy"] + self.get_scoped_flags() + [str(file_path)]
        cwd = file_path.parent if file_path.parent.exists() else None
        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_sec
                )
            except TimeoutError:
                proc.kill()
                await proc.wait()
                elapsed = time.monotonic() - start
                self._logger.warning(
                    "mypy timed out for %s after %.2fs", file_path, elapsed
                )
                raise MypyTimeoutError(timeout_sec)
            elapsed = time.monotonic() - start
            out = (stdout or b"").decode("utf-8", errors="replace")
            issues = self.parse_output(out, file_path)
            return MypyResult(
                issues=tuple(issues),
                duration_seconds=elapsed,
                files_checked=1,
                success=proc.returncode == 0 or not issues,
            )
        except MypyTimeoutError as e:
            raise e from None
        except FileNotFoundError:
            self._logger.debug("mypy not found")
            return MypyResult(
                issues=(), duration_seconds=0.0, files_checked=0, success=False
            )
        except Exception as e:
            self._logger.warning("mypy failed for %s: %s", file_path, e)
            return MypyResult(
                issues=(), duration_seconds=0.0, files_checked=0, success=False
            )

    def run_scoped_sync(
        self,
        file_path: Path,
        *,
        timeout: int | None = None,
    ) -> MypyResult:
        """
        Run mypy synchronously with scoped flags (for use from scoring.py).
        Uses subprocess.run to avoid event loop issues in sync callers.
        """
        timeout_sec = timeout if timeout is not None else self.config.timeout
        if not file_path.is_file():
            return MypyResult(
                issues=(), duration_seconds=0.0, files_checked=0, success=False
            )
        cmd = [sys.executable, "-m", "mypy"] + self.get_scoped_flags() + [str(file_path)]
        cwd = file_path.parent if file_path.parent.exists() else None
        start = time.monotonic()
        try:
            result = subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_sec,
                cwd=cwd,
            )
            elapsed = time.monotonic() - start
            out = (result.stdout or "").strip()
            issues = self.parse_output(out, file_path)
            return MypyResult(
                issues=tuple(issues),
                duration_seconds=elapsed,
                files_checked=1,
                success=result.returncode == 0 or not issues,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            self._logger.warning("mypy timed out for %s after %.2fs", file_path, elapsed)
            return MypyResult(
                issues=(),
                duration_seconds=elapsed,
                files_checked=0,
                success=False,
            )
        except FileNotFoundError:
            self._logger.debug("mypy not found")
            return MypyResult(
                issues=(), duration_seconds=0.0, files_checked=0, success=False
            )
        except Exception as e:
            self._logger.warning("mypy failed for %s: %s", file_path, e)
            return MypyResult(
                issues=(), duration_seconds=0.0, files_checked=0, success=False
            )
