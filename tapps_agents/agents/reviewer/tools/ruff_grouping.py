"""
Ruff Output Grouping - ENH-002-S3

Parses Ruff JSON output and groups issues by error code for cleaner reports.
Sorts by severity (error > warning > info), then by count.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class RuffParsingError(Exception):
    """Ruff output parsing failed."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Ruff parsing failed: {reason}")


@dataclass(frozen=True)
class RuffIssue:
    """Single Ruff linting issue."""

    code: str
    message: str
    line: int
    column: int
    severity: str
    fixable: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "fixable": self.fixable,
        }


@dataclass(frozen=True)
class GroupedRuffIssues:
    """Grouped Ruff issues by error code."""

    groups: dict[str, tuple[RuffIssue, ...]]
    total_issues: int
    unique_codes: int
    severity_summary: dict[str, int]
    fixable_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "groups": {
                code: [i.to_dict() for i in issues]
                for code, issues in self.groups.items()
            },
            "total_issues": self.total_issues,
            "unique_codes": self.unique_codes,
            "severity_summary": self.severity_summary,
            "fixable_count": self.fixable_count,
        }


@dataclass(frozen=True)
class RuffGroupingConfig:
    """Configuration for Ruff grouping."""

    enabled: bool = True
    sort_by: str = "severity"
    include_fix_suggestions: bool = True
    max_issues_per_group: int = 10


def _severity_order(severity: str) -> int:
    """Lower = higher priority (error=0, warning=1, info=2)."""
    order = {"error": 0, "warning": 1, "info": 2, "fatal": 0}
    return order.get(severity.lower(), 1)


class RuffGroupingParser:
    """
    Parse Ruff JSON and group issues by error code.

    Sorts groups by severity then count; supports markdown, HTML, JSON output.
    """

    def __init__(self, config: RuffGroupingConfig | None = None) -> None:
        self.config = config or RuffGroupingConfig()

    def parse_and_group(self, ruff_json: str) -> GroupedRuffIssues:
        """
        Parse Ruff JSON output and group by error code.

        Ruff JSON is a list of diagnostics; each has "code" (dict with "name"),
        "message", "location" (row, column), "fix" (optional).
        """
        try:
            data = json.loads(ruff_json) if ruff_json.strip() else []
        except json.JSONDecodeError as e:
            raise RuffParsingError(str(e)) from e
        if not isinstance(data, list):
            raise RuffParsingError("Expected a JSON array of diagnostics")

        issues: list[RuffIssue] = []
        for diag in data:
            if not isinstance(diag, dict):
                continue
            code_info = diag.get("code")
            if isinstance(code_info, dict):
                code = code_info.get("name") or code_info.get("code") or "unknown"
            else:
                code = str(code_info) if code_info else "unknown"
            message = diag.get("message", "")
            loc = diag.get("location", {}) or {}
            row = int(loc.get("row", 0)) if isinstance(loc, dict) else 0
            col = int(loc.get("column", 0)) if isinstance(loc, dict) else 0
            fix = diag.get("fix")
            fixable = fix is not None and fix != {}
            severity = "error"
            if isinstance(code_info, dict):
                severity = (code_info.get("severity") or "error").lower()
            if code.startswith("E") or code.startswith("F"):
                severity = "error"
            elif code.startswith("W"):
                severity = "warning"
            elif code.startswith("I"):
                severity = "info"
            issues.append(
                RuffIssue(
                    code=code,
                    message=message,
                    line=row,
                    column=col,
                    severity=severity,
                    fixable=fixable,
                )
            )

        groups: dict[str, list[RuffIssue]] = {}
        severity_summary: dict[str, int] = {}
        fixable_count = 0
        for i in issues:
            groups.setdefault(i.code, []).append(i)
            severity_summary[i.severity] = severity_summary.get(i.severity, 0) + 1
            if i.fixable:
                fixable_count += 1

        return GroupedRuffIssues(
            groups={k: tuple(v) for k, v in groups.items()},
            total_issues=len(issues),
            unique_codes=len(groups),
            severity_summary=severity_summary,
            fixable_count=fixable_count,
        )

    def sort_groups(
        self,
        groups: dict[str, tuple[RuffIssue, ...]],
        by: str = "severity",
    ) -> list[tuple[str, tuple[RuffIssue, ...]]]:
        """
        Sort groups by severity (error > warning > info), then count, then code.
        """
        items = list(groups.items())
        if by == "code":
            return sorted(items, key=lambda x: x[0])
        if by == "count":
            return sorted(items, key=lambda x: -len(x[1]))
        # severity: worst severity first, then by count descending
        def key(item: tuple[str, tuple[RuffIssue, ...]]) -> tuple[int, int, str]:
            code, iss = item
            min_sev = min(_severity_order(i.severity) for i in iss)
            return (min_sev, -len(iss), code)

        return sorted(items, key=key)

    def render_grouped(
        self,
        grouped: GroupedRuffIssues,
        format: str = "markdown",
    ) -> str:
        """Render grouped issues as markdown, HTML, or JSON."""
        sorted_pairs = self.sort_groups(grouped.groups, by=self.config.sort_by)
        if format == "json":
            return json.dumps(grouped.to_dict(), indent=2)
        if format == "markdown":
            return self._render_markdown(sorted_pairs, grouped)
        if format == "html":
            return self._render_html(sorted_pairs, grouped)
        return self._render_markdown(sorted_pairs, grouped)

    def _render_markdown(
        self,
        sorted_pairs: list[tuple[str, tuple[RuffIssue, ...]]],
        grouped: GroupedRuffIssues,
    ) -> str:
        lines = [
            "### Issues by Code",
            "",
            f"Total: {grouped.total_issues} issues in {grouped.unique_codes} categories.",
        ]
        if self.config.include_fix_suggestions and grouped.fixable_count:
            lines.append(f"*{grouped.fixable_count} auto-fixable*")
            lines.append("")
        max_per = self.config.max_issues_per_group
        for code, iss in sorted_pairs:
            fixable = sum(1 for i in iss if i.fixable)
            sev = iss[0].severity if iss else "error"
            lines.append(f"#### {code} ({len(iss)} issues, {sev})")
            if self.config.include_fix_suggestions and fixable:
                lines.append(f"*{fixable} auto-fixable*")
            for i in iss[:max_per]:
                lines.append(f"- Line {i.line}: {i.message}")
            if len(iss) > max_per:
                lines.append(f"- ... and {len(iss) - max_per} more")
            lines.append("")
        return "\n".join(lines).strip()

    def _render_html(
        self,
        sorted_pairs: list[tuple[str, tuple[RuffIssue, ...]]],
        grouped: GroupedRuffIssues,
    ) -> str:
        lines = [
            "<div class='ruff-grouped'>",
            f"<p>Total: {grouped.total_issues} issues in {grouped.unique_codes} categories.</p>",
        ]
        for code, iss in sorted_pairs:
            fixable = sum(1 for i in iss if i.fixable)
            sev = iss[0].severity if iss else "error"
            lines.append(f"<details><summary>{code} ({len(iss)} issues, {sev})")
            if fixable:
                lines.append(f" — {fixable} auto-fixable")
            lines.append("</summary><ul>")
            for i in iss[: self.config.max_issues_per_group]:
                lines.append(f"<li>Line {i.line}: {i.message}</li>")
            if len(iss) > self.config.max_issues_per_group:
                lines.append(f"<li>... and {len(iss) - self.config.max_issues_per_group} more</li>")
            lines.append("</ul></details>")
        lines.append("</div>")
        return "\n".join(lines)
