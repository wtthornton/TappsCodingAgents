"""
Session Handoff Artifact (PROJECT_STATE / Handoff Doc).

At end of a workflow or at checkpoints, write a structured handoff: what was done,
what was decided, what is next. New sessions can load this to reduce cold start.
Plan Phase 2.1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SessionHandoff:
    """Structured handoff for cross-session context."""

    workflow_id: str
    session_ended_at: str  # ISO timestamp
    summary: str
    done: list[str]  # completed step ids or summaries
    decisions: list[dict[str, Any]]  # {decision, rationale?, step_id?}
    next_steps: list[str]
    artifact_paths: list[str] = ()
    bd_ready_hint: str | None = None  # e.g. "Run `bd ready`"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionHandoff:
        return cls(
            workflow_id=data["workflow_id"],
            session_ended_at=data["session_ended_at"],
            summary=data["summary"],
            done=list(data.get("done") or []),
            decisions=list(data.get("decisions") or []),
            next_steps=list(data.get("next_steps") or []),
            artifact_paths=list(data.get("artifact_paths") or []),
            bd_ready_hint=data.get("bd_ready_hint"),
        )


def write_handoff(
    project_root: Path,
    handoff: SessionHandoff,
    path: Path | None = None,
) -> Path:
    """
    Write SessionHandoff to disk (YAML frontmatter + markdown body).

    Args:
        project_root: Project root directory
        handoff: SessionHandoff instance
        path: Override path; if None, uses
              .tapps-agents/workflow-state/{workflow_id}/SESSION_HANDOFF.md

    Returns:
        Path to the written file
    """
    project_root = Path(project_root)
    if path is None:
        base = project_root / ".tapps-agents" / "workflow-state" / handoff.workflow_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "SESSION_HANDOFF.md"

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # YAML frontmatter
    fm = {
        "workflow_id": handoff.workflow_id,
        "session_ended_at": handoff.session_ended_at,
        "summary": handoff.summary,
        "done": handoff.done,
        "decisions": handoff.decisions,
        "next_steps": handoff.next_steps,
        "artifact_paths": handoff.artifact_paths,
        "bd_ready_hint": handoff.bd_ready_hint,
    }
    fm_str = yaml.safe_dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Markdown body for human readability
    lines = [
        f"# Session Handoff: {handoff.workflow_id}",
        "",
        f"**Ended:** {handoff.session_ended_at}",
        "",
        "## Summary",
        handoff.summary,
        "",
        "## Done",
    ]
    for d in handoff.done:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("## Next steps")
    for n in handoff.next_steps:
        lines.append(f"- {n}")
    if handoff.artifact_paths:
        lines.append("")
        lines.append("## Artifacts")
        for a in handoff.artifact_paths:
            lines.append(f"- {a}")
    if handoff.bd_ready_hint:
        lines.append("")
        lines.append("## Hint")
        lines.append(handoff.bd_ready_hint)

    body = "\n".join(lines)
    content = f"---\n{fm_str}---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")
    return path


def load_handoff(
    project_root: Path,
    workflow_id: str | None = None,
) -> SessionHandoff | None:
    """
    Load SessionHandoff from disk.

    Args:
        project_root: Project root directory
        workflow_id: If None, load the latest (most recent SESSION_HANDOFF in
                     .tapps-agents/workflow-state/*/SESSION_HANDOFF.md)

    Returns:
        SessionHandoff or None if not found
    """
    project_root = Path(project_root)
    base = project_root / ".tapps-agents" / "workflow-state"
    if not base.exists():
        return None

    if workflow_id:
        p = base / workflow_id / "SESSION_HANDOFF.md"
        if not p.exists():
            # .json fallback
            p2 = base / workflow_id / "SESSION_HANDOFF.json"
            if p2.exists():
                import json
                data = json.loads(p2.read_text(encoding="utf-8"))
                return SessionHandoff.from_dict(data)
            return None
        path = p
    else:
        # Latest: find most recent by mtime
        best: Path | None = None
        best_mtime: float = 0
        for d in base.iterdir():
            if d.is_dir():
                f = d / "SESSION_HANDOFF.md"
                if f.exists():
                    m = f.stat().st_mtime
                    if m > best_mtime:
                        best_mtime = m
                        best = f
        if best is None:
            return None
        path = best

    text = path.read_text(encoding="utf-8")
    # Parse YAML frontmatter
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        return None
    return SessionHandoff.from_dict(fm)
