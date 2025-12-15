from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from tapps_agents.workflow.messaging import (
    FileMessageBus,
    TaskAssignmentMessage,
)

pytestmark = pytest.mark.unit


def test_concurrent_writers_produce_distinct_files(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir()

    bus = FileMessageBus(project_root=project_root)

    def _writer(i: int) -> None:
        msg = TaskAssignmentMessage(
            workflow_id="wf-1",
            task_id=f"t-{i}",
            agent_id="orchestrator",
            assigned_to="agent-a",
            inputs={"i": i},
        )
        bus.send_to_inbox("agent-a", msg)

    threads = [threading.Thread(target=_writer, args=(i,)) for i in range(25)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    inbox_dir = project_root / ".tapps-agents" / "messages" / "inbox" / "agent-a"
    files = list(inbox_dir.glob("*.json"))
    assert len(files) == 25


def test_invalid_json_is_quarantined_to_dlq(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir()

    bus = FileMessageBus(project_root=project_root)
    inbox_dir = project_root / ".tapps-agents" / "messages" / "inbox" / "agent-a"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    bad = inbox_dir / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")

    msgs = bus.poll_inbox("agent-a", max_messages=10)
    assert msgs == []

    dlq_files = list((project_root / ".tapps-agents" / "messages" / "dlq").glob("*.json"))
    assert len(dlq_files) == 1
    assert dlq_files[0].with_suffix(".reason.txt").exists()


def test_schema_invalid_message_is_quarantined_to_dlq(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir()

    bus = FileMessageBus(project_root=project_root)
    inbox_dir = project_root / ".tapps-agents" / "messages" / "inbox" / "agent-a"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Missing required fields like workflow_id/task_id/agent_id
    invalid = {
        "schema_version": "1.0",
        "message_type": "task_assignment",
        "message_id": "m-1",
        "created_at": "2025-12-14T00:00:00Z",
    }
    (inbox_dir / "invalid.json").write_text(json.dumps(invalid), encoding="utf-8")

    msgs = bus.poll_inbox("agent-a", max_messages=10)
    assert msgs == []
    dlq_files = list((project_root / ".tapps-agents" / "messages" / "dlq").glob("*.json"))
    assert len(dlq_files) == 1


def test_idempotency_skips_already_processed_message(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir()

    bus = FileMessageBus(project_root=project_root)

    msg = TaskAssignmentMessage(
        workflow_id="wf-1",
        task_id="t-1",
        agent_id="orchestrator",
        assigned_to="agent-a",
        message_id="fixed-message-id",
    )

    bus.send_to_inbox("agent-a", msg)
    polled = bus.poll_inbox("agent-a", max_messages=10)
    assert len(polled) == 1
    bus.ack("agent-a", polled[0])

    # Replay the same message_id -> should be dropped.
    bus.send_to_inbox("agent-a", msg)
    polled2 = bus.poll_inbox("agent-a", max_messages=10)
    assert polled2 == []
