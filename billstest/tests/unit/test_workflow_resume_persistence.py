from pathlib import Path

import pytest

from tapps_agents.workflow.executor import WorkflowExecutor

pytestmark = pytest.mark.unit


def test_workflow_executor_persists_and_resumes_last_state(tmp_path: Path) -> None:
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    wf_file = workflows_dir / "test.yaml"
    wf_file.write_text(
        (
            "workflow:\n"
            "  id: test-workflow\n"
            "  name: Test Workflow\n"
            "  description: test\n"
            "  version: 1.0.0\n"
            "  type: greenfield\n"
            "  steps:\n"
            "    - id: s1\n"
            "      agent: reviewer\n"
            "      action: review\n"
            "      next: s2\n"
            "    - id: s2\n"
            "      agent: implementer\n"
            "      action: implement\n"
        ),
        encoding="utf-8",
    )

    ex1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
    ex1.load_workflow(wf_file)
    state1 = ex1.start()
    assert state1.current_step == "s1"

    ex1.mark_step_complete(step_id="s1")

    ex2 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
    state2 = ex2.load_last_state()

    assert state2.workflow_id == "test-workflow"
    assert state2.current_step == "s2"
    assert "s1" in state2.completed_steps
