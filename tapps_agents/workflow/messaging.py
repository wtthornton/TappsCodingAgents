"""
File-based messaging infrastructure for orchestrator <-> agents coordination.

Epic 1 / Story 1.2 requirements:
- Durable inbox/outbox under .tapps-agents/messages/
- Versioned, validated JSON message contracts
- Atomic writes (write-then-rename)
- Consumer idempotency (message_id)
- DLQ/quarantine with reason + minimal replay support
- Windows + POSIX friendly filenames
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

SCHEMA_VERSION: str = "1.0"


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _safe_component(value: str, *, max_len: int = 64) -> str:
    value = (value or "").strip()
    if not value:
        return "x"
    value = value.replace("\\", "-").replace("/", "-")
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        value = "x"
    if len(value) > max_len:
        value = value[:max_len]
    return value


def _format_ts_for_filename(dt: datetime) -> str:
    # Windows-safe, stable, sortable, no ":".
    dt = dt.astimezone(UTC)
    return dt.strftime("%Y%m%dT%H%M%S") + f"_{dt.microsecond // 1000:03d}Z"


class BaseMessage(BaseModel):
    schema_version: str = Field(default=SCHEMA_VERSION)
    message_type: str

    workflow_id: str
    task_id: str
    agent_id: str

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utcnow)

    # Optional: help consumers be idempotent across retries.
    idempotency_key: str | None = None

    # Freeform metadata (kept small; avoid secrets).
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }


class TaskAssignmentMessage(BaseMessage):
    message_type: Literal["task_assignment"] = "task_assignment"
    assigned_to: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    inputs: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = None
    retry_policy: dict[str, Any] = Field(default_factory=dict)


class StatusUpdateMessage(BaseMessage):
    message_type: Literal["status_update"] = "status_update"
    status: Literal["queued", "in_progress", "blocked", "failed", "completed"]
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    current_step: str | None = None


class TaskCompleteMessage(BaseMessage):
    message_type: Literal["task_complete"] = "task_complete"
    status: Literal["completed", "failed"]
    results: dict[str, Any] = Field(default_factory=dict)


type Message = TaskAssignmentMessage | StatusUpdateMessage | TaskCompleteMessage


def parse_message(data: dict[str, Any]) -> Message:
    msg_type = data.get("message_type")
    if msg_type == "task_assignment":
        return TaskAssignmentMessage.model_validate(data)
    if msg_type == "status_update":
        return StatusUpdateMessage.model_validate(data)
    if msg_type == "task_complete":
        return TaskCompleteMessage.model_validate(data)
    raise ValueError(f"Unknown message_type: {msg_type!r}")


@dataclass(frozen=True)
class MessagePaths:
    root: Path
    inbox: Path
    outbox: Path
    dlq: Path
    locks: Path
    processed: Path
    tmp: Path


class FileMessageBus:
    """
    File-based inbox/outbox message bus.

    Layout (default):
      .tapps-agents/messages/
        inbox/{agent_id}/
        outbox/{agent_id}/
        dlq/
        locks/{agent_id}/
        processed/{agent_id}.jsonl
        tmp/
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        root = self.project_root / ".tapps-agents" / "messages"
        self.paths = MessagePaths(
            root=root,
            inbox=root / "inbox",
            outbox=root / "outbox",
            dlq=root / "dlq",
            locks=root / "locks",
            processed=root / "processed",
            tmp=root / "tmp",
        )
        for p in [
            self.paths.root,
            self.paths.inbox,
            self.paths.outbox,
            self.paths.dlq,
            self.paths.locks,
            self.paths.processed,
            self.paths.tmp,
        ]:
            p.mkdir(parents=True, exist_ok=True)

        self._processed_cache: dict[str, set[str]] = {}
        self._processed_lock = threading.Lock()

    def _agent_dir(self, base: Path, agent_id: str) -> Path:
        d = base / _safe_component(agent_id, max_len=64)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _processed_index_path(self, agent_id: str) -> Path:
        return self.paths.processed / f"{_safe_component(agent_id)}.jsonl"

    def _is_processed(self, agent_id: str, message_id: str) -> bool:
        safe_agent = _safe_component(agent_id)
        with self._processed_lock:
            cache = self._processed_cache.get(safe_agent)
            if cache is None:
                cache = set()
                idx = self._processed_index_path(agent_id)
                if idx.exists():
                    for line in idx.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line:
                            cache.add(line)
                self._processed_cache[safe_agent] = cache
            return message_id in cache

    def _mark_processed(self, agent_id: str, message_id: str) -> None:
        safe_agent = _safe_component(agent_id)
        idx = self._processed_index_path(agent_id)
        idx.parent.mkdir(parents=True, exist_ok=True)
        # Append is safe enough for this index; we keep it simple.
        with idx.open("a", encoding="utf-8") as f:
            f.write(message_id + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        with self._processed_lock:
            self._processed_cache.setdefault(safe_agent, set()).add(message_id)

    def _atomic_write_json(self, target: Path, data: dict[str, Any]) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_name = f"{target.name}.{uuid.uuid4().hex}.tmp"
        tmp_path = self.paths.tmp / tmp_name
        payload = json.dumps(data, indent=2, sort_keys=True, default=str)
        with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        os.replace(tmp_path, target)  # atomic on Windows + POSIX

    def _message_filename(self, msg: Message) -> str:
        ts = _format_ts_for_filename(msg.created_at)
        return f"{ts}_{msg.message_id}_{msg.message_type}.json"

    def send_to_inbox(self, agent_id: str, msg: Message) -> Path:
        inbox_dir = self._agent_dir(self.paths.inbox, agent_id)
        path = inbox_dir / self._message_filename(msg)
        self._atomic_write_json(path, msg.model_dump(mode="json"))
        return path

    def send_to_outbox(self, agent_id: str, msg: Message) -> Path:
        outbox_dir = self._agent_dir(self.paths.outbox, agent_id)
        path = outbox_dir / self._message_filename(msg)
        self._atomic_write_json(path, msg.model_dump(mode="json"))
        return path

    def _quarantine(self, src: Path, *, reason: str) -> None:
        self.paths.dlq.mkdir(parents=True, exist_ok=True)
        safe = _safe_component(src.stem, max_len=80)
        dst = self.paths.dlq / f"{safe}.{uuid.uuid4().hex}.json"
        try:
            os.replace(src, dst)
        except FileNotFoundError:
            return

        reason_path = dst.with_suffix(".reason.txt")
        reason_path.write_text(reason + "\n", encoding="utf-8")

    def poll_inbox(self, agent_id: str, *, max_messages: int = 10) -> list[Message]:
        """
        Poll and claim up to max_messages for an agent from its inbox.

        Claiming is done via atomic rename into locks/{agent_id}/ to prevent double-consumption.
        """
        inbox_dir = self._agent_dir(self.paths.inbox, agent_id)
        lock_dir = self._agent_dir(self.paths.locks, agent_id)

        msgs: list[Message] = []
        for msg_file in sorted(inbox_dir.glob("*.json")):
            if len(msgs) >= max_messages:
                break

            claimed = lock_dir / msg_file.name
            try:
                os.replace(msg_file, claimed)
            except FileNotFoundError:
                continue
            except OSError:
                # Another consumer likely claimed it
                continue

            try:
                raw = claimed.read_text(encoding="utf-8")
                data = json.loads(raw)
                msg = parse_message(data)
                if self._is_processed(agent_id, msg.message_id):
                    # Already processed: drop it.
                    claimed.unlink(missing_ok=True)
                    continue
                msgs.append(msg)
                # Keep claimed file until ack; caller can ack/fail.
            except json.JSONDecodeError as e:
                self._quarantine(claimed, reason=f"Invalid JSON: {e}")
            except (ValidationError, ValueError) as e:
                self._quarantine(claimed, reason=f"Schema validation failed: {e}")
            except Exception as e:
                self._quarantine(claimed, reason=f"Unhandled read/parse error: {e}")

        return msgs

    def ack(self, agent_id: str, msg: Message) -> None:
        """Mark message processed and remove its claimed file if present."""
        self._mark_processed(agent_id, msg.message_id)

        lock_dir = self._agent_dir(self.paths.locks, agent_id)
        pattern = f"*_{msg.message_id}_{msg.message_type}.json"
        for p in lock_dir.glob(pattern):
            p.unlink(missing_ok=True)

    def fail(self, agent_id: str, msg: Message, *, reason: str) -> None:
        """Send the claimed file to DLQ with a reason."""
        lock_dir = self._agent_dir(self.paths.locks, agent_id)
        pattern = f"*_{msg.message_id}_{msg.message_type}.json"
        for p in lock_dir.glob(pattern):
            self._quarantine(p, reason=reason)

    def replay_dlq(self, *, agent_id: str | None = None, limit: int = 100) -> int:
        """
        Minimal replay: move DLQ messages back into an agent inbox.

        If agent_id is None, replay is not attempted (returns 0). This is intentional:
        DLQ messages often need human routing decisions.
        """
        if not agent_id:
            return 0

        inbox_dir = self._agent_dir(self.paths.inbox, agent_id)
        moved = 0
        for f in sorted(self.paths.dlq.glob("*.json")):
            if moved >= limit:
                break
            dst = inbox_dir / f.name
            try:
                os.replace(f, dst)
            except OSError:
                continue
            moved += 1
        return moved
