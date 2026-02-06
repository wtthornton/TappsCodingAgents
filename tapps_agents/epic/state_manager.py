"""
Epic State Manager

Manages Epic execution state persistence, resume, memory (JSONL), and session handoff.

Phase 1.1: Progress persistence + resume
Phase 4.1: Epic memory (JSONL append-only)
Phase 4.2: Session handoff file
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EpicStateManager:
    """
    Manages Epic execution state for persistence, resume, and status queries.

    State files:
    - {epic_id}.json          — primary state (stories, scores, timestamps)
    - {epic_id}-memory.jsonl   — append-only per-story summaries
    - {epic_id}-handoff.md     — session handoff context
    """

    SCHEMA_VERSION = 1

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.state_dir = self.project_root / ".tapps-agents" / "epic-state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # ── State file paths ─────────────────────────────────────────────

    def _state_path(self, epic_id: str, run_id: str | None = None) -> Path:
        if run_id:
            return self.state_dir / f"{epic_id}-{run_id}.json"
        return self.state_dir / f"{epic_id}.json"

    def _memory_path(self, epic_id: str) -> Path:
        return self.state_dir / f"{epic_id}-memory.jsonl"

    def _handoff_path(self, epic_id: str) -> Path:
        return self.state_dir / f"{epic_id}-handoff.md"

    # ── Content checksum ─────────────────────────────────────────────

    @staticmethod
    def compute_checksum(content: str) -> str:
        return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"

    # ── Load / Save state ────────────────────────────────────────────

    def load_state(self, epic_id: str, run_id: str | None = None) -> dict[str, Any] | None:
        """Load epic state from JSON. Returns None if no state file exists."""
        path = self._state_path(epic_id, run_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            logger.info("Loaded epic state from %s", path)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load epic state %s: %s", path, exc)
            return None

    def save_state(self, state: dict[str, Any], run_id: str | None = None) -> Path:
        """
        Atomically save epic state to JSON.

        Uses write-to-tmp + rename for crash safety.
        """
        epic_id = state.get("epic_id", "unknown")
        state.setdefault("schema_version", self.SCHEMA_VERSION)
        state["updated_at"] = datetime.now().isoformat()

        path = self._state_path(epic_id, run_id)
        tmp_path = path.with_suffix(".json.tmp")
        try:
            tmp_path.write_text(
                json.dumps(state, indent=2, default=str),
                encoding="utf-8",
            )
            # Atomic rename (on Windows, remove target first)
            if os.name == "nt" and path.exists():
                path.unlink()
            tmp_path.rename(path)
            logger.debug("Saved epic state to %s", path)
        except OSError:
            # Fallback: direct write
            path.write_text(
                json.dumps(state, indent=2, default=str),
                encoding="utf-8",
            )
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        return path

    def create_initial_state(
        self,
        epic_id: str,
        epic_title: str,
        epic_path: str,
        epic_content: str,
        stories: list[dict[str, Any]],
        execution_order: list[str],
    ) -> dict[str, Any]:
        """Create a new epic state dict."""
        return {
            "schema_version": self.SCHEMA_VERSION,
            "epic_id": epic_id,
            "epic_content_checksum": self.compute_checksum(epic_content),
            "epic_path": str(epic_path),
            "epic_title": epic_title,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stories": stories,
            "execution_order": execution_order,
        }

    def update_story_state(
        self,
        state: dict[str, Any],
        story_id: str,
        status: str,
        quality_scores: dict[str, Any] | None = None,
        artifacts: list[str] | None = None,
        retry_count: int = 0,
        workflow_id: str | None = None,
    ) -> dict[str, Any]:
        """Update a single story's state within the epic state dict."""
        for story in state.get("stories", []):
            if story.get("story_id") == story_id:
                story["status"] = status
                if status == "done":
                    story["completed_at"] = datetime.now().isoformat()
                if quality_scores is not None:
                    story["quality_scores"] = quality_scores
                if artifacts is not None:
                    story["artifacts"] = artifacts
                story["retry_count"] = retry_count
                if workflow_id:
                    story["workflow_id"] = workflow_id
                break
        return state

    def get_completed_story_ids(self, state: dict[str, Any]) -> set[str]:
        """Return set of story IDs that are already 'done'."""
        return {
            s["story_id"]
            for s in state.get("stories", [])
            if s.get("status") == "done"
        }

    def check_content_drift(self, state: dict[str, Any], epic_content: str) -> bool:
        """Return True if epic content has changed since state was saved."""
        saved = state.get("epic_content_checksum", "")
        current = self.compute_checksum(epic_content)
        return saved != current

    # ── Epic Memory (JSONL) ──────────────────────────────────────────

    def append_memory(
        self,
        epic_id: str,
        story_id: str,
        title: str,
        files_changed: list[str] | None = None,
        summary: str = "",
        quality_scores: dict[str, Any] | None = None,
    ) -> None:
        """Append a per-story summary to the JSONL memory file."""
        path = self._memory_path(epic_id)
        entry = {
            "story_id": story_id,
            "title": title,
            "files_changed": files_changed or [],
            "summary": summary,
            "quality_scores": quality_scores or {},
            "timestamp": datetime.now().isoformat(),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def load_memory(self, epic_id: str, last_k: int = 5) -> list[dict[str, Any]]:
        """Load last K memory entries for prior-work context."""
        path = self._memory_path(epic_id)
        if not path.exists():
            return []
        entries: list[dict[str, Any]] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Error reading epic memory %s: %s", path, exc)
        return entries[-last_k:] if last_k else entries

    def build_prior_work_context(self, epic_id: str, last_k: int = 5) -> str:
        """Build a text summary of prior work for injection into implementer context."""
        entries = self.load_memory(epic_id, last_k)
        if not entries:
            return ""
        parts: list[str] = []
        for e in entries:
            files = ", ".join(e.get("files_changed", [])[:5])
            summary = e.get("summary", "")
            parts.append(f"- Story {e.get('story_id', '?')}: {summary} (files: {files})")
        return "\n".join(parts)

    # ── Session Handoff ──────────────────────────────────────────────

    def write_handoff(
        self,
        epic_id: str,
        state: dict[str, Any],
        decisions: str = "",
    ) -> Path:
        """Write a markdown handoff file for session continuity."""
        path = self._handoff_path(epic_id)
        stories = state.get("stories", [])
        done = [s for s in stories if s.get("status") == "done"]
        pending = [s for s in stories if s.get("status") not in ("done", "failed")]
        failed = [s for s in stories if s.get("status") == "failed"]

        last_done = done[-1] if done else None
        next_pending = pending[0] if pending else None

        lines = [
            f"# Epic {epic_id} Session Handoff",
            f"",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Epic:** {state.get('epic_title', epic_id)}",
            f"**Progress:** {len(done)}/{len(stories)} stories complete",
            f"",
        ]

        if last_done:
            files = ", ".join(last_done.get("artifacts", [])[:5]) or "none"
            lines.extend([
                f"## Last Completed",
                f"- Story {last_done.get('story_id', '?')}: {last_done.get('title', '')}",
                f"- Files: {files}",
                f"",
            ])

        if next_pending:
            lines.extend([
                f"## Next Up",
                f"- Story {next_pending.get('story_id', '?')}: {next_pending.get('title', '')}",
                f"",
            ])

        if failed:
            lines.append("## Failed Stories")
            for s in failed:
                lines.append(f"- Story {s.get('story_id', '?')}: {s.get('title', '')}")
            lines.append("")

        # Collect changed files from memory
        memory = self.load_memory(epic_id, last_k=10)
        all_files: list[str] = []
        for entry in memory:
            all_files.extend(entry.get("files_changed", []))
        if all_files:
            unique_files = sorted(set(all_files))[:20]
            lines.extend([
                "## Key Files Changed",
                *[f"- {f}" for f in unique_files],
                "",
            ])

        if decisions:
            lines.extend([
                "## Decisions",
                decisions,
                "",
            ])

        content = "\n".join(lines)
        path.write_text(content, encoding="utf-8")
        logger.info("Wrote handoff to %s", path)
        return path

    # ── Listing and Cleanup ──────────────────────────────────────────

    def list_epic_states(self) -> list[dict[str, Any]]:
        """List all persisted epic states with summary info."""
        results: list[dict[str, Any]] = []
        if not self.state_dir.exists():
            return results
        for f in sorted(self.state_dir.glob("*.json")):
            if f.name.endswith(".tmp"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                stories = data.get("stories", [])
                done = sum(1 for s in stories if s.get("status") == "done")
                total = len(stories)
                pct = (done / total * 100) if total else 0.0
                results.append({
                    "epic_id": data.get("epic_id", f.stem),
                    "epic_title": data.get("epic_title", ""),
                    "completion": f"{pct:.0f}%",
                    "done": done,
                    "total": total,
                    "updated_at": data.get("updated_at", ""),
                    "file": str(f),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return results

    def cleanup_states(
        self,
        retention_days: int = 30,
        remove_completed: bool = False,
        archive: bool = False,
        dry_run: bool = False,
    ) -> list[dict[str, str]]:
        """
        Clean up old epic state files.

        Returns list of actions taken (or would-take for dry_run).
        """
        actions: list[dict[str, str]] = []
        cutoff = time.time() - (retention_days * 86400)
        archive_dir = self.state_dir.parent / "archives" / "epic-state"

        patterns = ["*.json", "*-memory.jsonl", "*-handoff.md"]
        for pattern in patterns:
            for f in self.state_dir.glob(pattern):
                if f.name.endswith(".tmp"):
                    continue
                mtime = f.stat().st_mtime
                should_remove = mtime < cutoff

                if remove_completed and f.suffix == ".json":
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        stories = data.get("stories", [])
                        all_done = all(s.get("status") == "done" for s in stories) if stories else False
                        should_remove = should_remove or all_done
                    except (json.JSONDecodeError, OSError):
                        pass

                if not should_remove:
                    continue

                action_type = "archive" if archive else "delete"
                actions.append({"file": str(f), "action": action_type})

                if not dry_run:
                    if archive:
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        dest = archive_dir / f.name
                        f.rename(dest)
                    else:
                        f.unlink()

        return actions
