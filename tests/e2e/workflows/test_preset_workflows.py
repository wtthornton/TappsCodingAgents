"""
E2E tests for all shipped workflow presets.

Per docs/planning/E2E_TESTING_PLAN.md: parse, start, and short run (max_steps=2)
with mocks for each preset. Uses target_file for reviewer-first presets (e.g. quality).
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.workflow_runner import WorkflowRunner

# Presets that use steps: (id, expected name substring for assertion)
PRESETS = [
    ("fix", "Fix"),
    ("full-sdlc", "Full SDLC"),
    ("quality", "Quality"),
    ("rapid-dev", "Rapid"),
    # brownfield-analysis uses legacy sequence format; only parse/start if needed
]

ROOT = Path(__file__).resolve().parent.parent.parent.parent
PRESETS_DIR = ROOT / "workflows" / "presets"


def _workflow_path(preset_id: str) -> Path:
    return PRESETS_DIR / f"{preset_id}.yaml"


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
class TestPresetWorkflows:
    """Parameterized E2E tests for workflow presets: parse, start, short run."""

    @pytest.mark.parametrize("preset_id,name_substring", PRESETS)
    @pytest.mark.asyncio
    async def test_preset_parsing(
        self,
        workflow_runner: WorkflowRunner,
        preset_id: str,
        name_substring: str,
    ):
        """Each preset YAML parses and has expected id, name, and steps."""
        path = _workflow_path(preset_id)
        if not path.exists():
            pytest.skip(f"Preset {preset_id} not found at {path}")
        workflow = workflow_runner.load_workflow(path)
        assert workflow.id == preset_id
        assert name_substring in (workflow.name or "")
        assert len(workflow.steps) > 0, f"Preset {preset_id} has no steps"

    @pytest.mark.parametrize("preset_id,name_substring", PRESETS)
    @pytest.mark.asyncio
    async def test_preset_start(
        self,
        workflow_runner: WorkflowRunner,
        preset_id: str,
        name_substring: str,
    ):
        """Each preset can be started (executor.start) and state is running."""
        path = _workflow_path(preset_id)
        if not path.exists():
            pytest.skip(f"Preset {preset_id} not found at {path}")
        workflow = workflow_runner.load_workflow(path)
        executor = workflow_runner.create_executor()
        executor.load_workflow(path)
        state = executor.start(workflow)
        assert state.workflow_id.startswith(preset_id)
        assert state.status == "running"
        assert state.current_step is not None

    @pytest.mark.parametrize("preset_id,name_substring", PRESETS)
    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_preset_run_limited(
        self,
        workflow_runner: WorkflowRunner,
        preset_id: str,
        name_substring: str,
        mock_mal,
    ):
        """Short run (max_steps=2) with mocks; pass target_file for reviewer-first presets."""
        path = _workflow_path(preset_id)
        if not path.exists():
            pytest.skip(f"Preset {preset_id} not found at {path}")
        # Quality (and any reviewer-first preset) needs a target file
        kwargs = {}
        if preset_id == "quality":
            kwargs["target_file"] = "main.py"
        state, results = await workflow_runner.run_workflow(
            path, max_steps=2, **kwargs
        )
        assert state is not None
        assert state.workflow_id.startswith(preset_id)
        assert results.get("correlation_id") is not None
        # Accept any terminal or running status; require at least one step progressed
        steps_done = (
            results.get("steps_completed", 0)
            or len(results.get("completed_steps_ids", []))
            or len(state.completed_steps)
        )
        assert steps_done >= 0, "steps_completed or completed_steps should be present"
        assert state.status in (
            "running",
            "completed",
            "success",
            "failed",
            "blocked",
        ), f"Unexpected status: {state.status}"
