"""
Sync epic execution status from report JSON back into the epic markdown file.

Updates each story block with **Execution status:** done | failed so the .md
reflects the last run. Run after epic execution or when you have a report file.
"""

import json
import re
from pathlib import Path


def update_epic_markdown_from_report(
    epic_path: Path | str,
    report_path: Path | None = None,
    project_root: Path | None = None,
) -> None:
    """
    Update the epic markdown file with execution status from the report JSON.

    For each story in the report, adds or replaces a line
    "**Execution status:** done" or "**Execution status:** failed"
    in the corresponding story block.

    Args:
        epic_path: Path to the epic .md file.
        report_path: Path to epic-N-report.json. If None, uses same directory
            as epic_path and filename epic-{N}-report.json (N from epic content).
        project_root: Project root for resolving relative epic_path. Defaults to cwd.

    Raises:
        FileNotFoundError: If epic or report file is missing.
        ValueError: If report format is invalid or epic number cannot be determined.
    """
    root = Path(project_root or Path.cwd())
    epic_path = Path(epic_path)
    if not epic_path.is_absolute():
        for base in [root, root / "stories", root / "docs" / "prd"]:
            candidate = base / epic_path.name if epic_path.parent.name else base / epic_path
            if candidate.exists():
                epic_path = candidate
                break
        else:
            epic_path = root / epic_path

    if not epic_path.exists():
        raise FileNotFoundError(f"Epic file not found: {epic_path}")

    content = epic_path.read_text(encoding="utf-8")

    # Determine epic number from content
    epic_num_match = re.search(r"^#\s+Epic\s+(\d+):", content, re.MULTILINE)
    if not epic_num_match:
        epic_num_match = re.search(r"epic-(\d+)", epic_path.name, re.IGNORECASE)
    if not epic_num_match:
        raise ValueError(f"Could not determine epic number from {epic_path}")
    epic_number = int(epic_num_match.group(1))

    if report_path is None:
        report_path = epic_path.parent / f"epic-{epic_number}-report.json"
    else:
        report_path = Path(report_path)
    if not report_path.is_absolute():
        report_path = root / report_path

    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    stories = report.get("stories") or []
    if not stories:
        return

    # Build map story_id -> status (done | failed | in_progress)
    status_by_id: dict[str, str] = {}
    for s in stories:
        sid = s.get("story_id")
        if sid:
            status_by_id[sid] = (s.get("status") or "unknown").lower()

    # For each story id, find the story block and add/replace **Execution status:**
    def replace_or_add_status(match: re.Match[str]) -> str:
        story_id = match.group(2)  # e.g. "2.1"
        title_line = match.group(1)
        rest = match.group(3)
        status = status_by_id.get(story_id, "not run")
        status_line = f"   **Execution status:** {status}\n"
        existing = re.search(r"^(\s*\*\*Execution status:\*\*\s*)[^\n]*\n", rest, re.MULTILINE)
        if existing:
            rest = rest[: existing.start()] + status_line.strip() + "\n" + rest[existing.end() :]
        else:
            rest = status_line + rest
        return title_line + rest

    pattern = re.compile(
        r"^(\d+\.\s*\*\*Story\s+(\d+\.\d+):[^*]*\*\*[^\n]*\n)(.*?)(?=^\d+\.\s*\*\*Story\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    new_content = pattern.sub(
        lambda m: replace_or_add_status(m) if m.group(2) in status_by_id else m.group(0),
        content,
    )

    if new_content != content:
        epic_path.write_text(new_content, encoding="utf-8")
