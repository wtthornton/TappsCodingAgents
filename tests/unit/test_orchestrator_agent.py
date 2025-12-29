"""
Unit tests for Orchestrator Agent.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.agents.orchestrator.agent import OrchestratorAgent


@pytest.mark.unit
class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent."""

    @pytest.fixture
    def orchestrator(self):
        """Create an OrchestratorAgent instance."""
        return OrchestratorAgent()

    @pytest.fixture
    def sample_workflow_file(self, tmp_path: Path):
        """Create a sample workflow file."""
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        workflow_file = workflows_dir / "test-workflow.yaml"
        workflow_content = {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "description": "A test workflow",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "requires": [],
                    }
                ],
            }
        }

        with open(workflow_file, "w", encoding="utf-8") as f:
            yaml.dump(workflow_content, f)

        return workflow_file

    @pytest.mark.asyncio
    async def test_list_workflows_no_directory(self, orchestrator, tmp_path: Path):
        """Test listing workflows when workflows directory doesn't exist."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run("*workflow-list")

            assert "workflows" in result
            assert result["workflows"] == []
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_list_workflows_with_files(
        self, orchestrator, sample_workflow_file, tmp_path: Path
    ):
        """Test listing workflows when workflow files exist."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run("*workflow-list")

            assert "workflows" in result
            assert len(result["workflows"]) > 0
            assert any(w["id"] == "test-workflow" for w in result["workflows"])
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_list_workflows_in_subdirectories(
        self, orchestrator, tmp_path: Path
    ):
        """Test listing workflows when workflow files exist in subdirectories."""
        import os

        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        # Create workflow in root
        root_workflow = workflows_dir / "root-workflow.yaml"
        root_workflow.write_text(
            yaml.dump(
                {
                    "workflow": {
                        "id": "root-workflow",
                        "name": "Root Workflow",
                        "description": "A workflow in root",
                        "version": "1.0.0",
                        "type": "greenfield",
                        "steps": [
                            {
                                "id": "step1",
                                "agent": "analyst",
                                "action": "gather",
                                "requires": [],
                            }
                        ],
                    }
                }
            )
        )

        # Create workflow in subdirectory
        custom_dir = workflows_dir / "custom"
        custom_dir.mkdir()
        custom_workflow = custom_dir / "custom-workflow.yaml"
        custom_workflow.write_text(
            yaml.dump(
                {
                    "workflow": {
                        "id": "custom-workflow",
                        "name": "Custom Workflow",
                        "description": "A workflow in custom subdirectory",
                        "version": "1.0.0",
                        "type": "greenfield",
                        "steps": [
                            {
                                "id": "step1",
                                "agent": "analyst",
                                "action": "gather",
                                "requires": [],
                            }
                        ],
                    }
                }
            )
        )

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run("*workflow-list")

            assert "workflows" in result
            assert len(result["workflows"]) == 2
            workflow_ids = [w["id"] for w in result["workflows"]]
            assert "root-workflow" in workflow_ids
            assert "custom-workflow" in workflow_ids
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_start_workflow_in_subdirectory(
        self, orchestrator, tmp_path: Path, monkeypatch
    ):
        """Test starting a workflow that exists in a subdirectory."""
        import os

        workflows_dir = tmp_path / "workflows"
        custom_dir = workflows_dir / "custom"
        custom_dir.mkdir(parents=True)

        workflow_file = custom_dir / "subdir-workflow.yaml"
        workflow_file.write_text(
            yaml.dump(
                {
                    "workflow": {
                        "id": "subdir-workflow",
                        "name": "Subdirectory Workflow",
                        "description": "A workflow in a subdirectory",
                        "version": "1.0.0",
                        "type": "greenfield",
                        "steps": [
                            {
                                "id": "step1",
                                "agent": "analyst",
                                "action": "gather",
                                "requires": [],
                            }
                        ],
                    }
                }
            )
        )

        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run(
                "*workflow-start", workflow_id="subdir-workflow"
            )

            assert "success" in result
            assert result["success"] is True
            assert result["workflow_id"] == "subdir-workflow"
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_start_workflow(
        self, orchestrator, sample_workflow_file, tmp_path: Path, monkeypatch
    ):
        """Test starting a workflow."""
        import os

        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run(
                "*workflow-start", workflow_id="test-workflow"
            )

            assert "success" in result
            assert result["success"] is True
            assert result["workflow_id"] == "test-workflow"
            assert result["status"] == "running"
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_start_workflow_not_found(self, orchestrator, tmp_path: Path):
        """Test starting a workflow that doesn't exist."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run(
                "*workflow-start", workflow_id="nonexistent"
            )

            assert "error" in result
            assert "not found" in result["error"].lower()
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_get_workflow_status_no_workflow(self, orchestrator, tmp_path: Path):
        """Test getting status when no workflow is active."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run("*workflow-status")

            # Executor returns {"status": "not_started"} when no workflow is active
            assert "status" in result
            assert result["status"] == "not_started"
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_get_workflow_status_active(
        self, orchestrator, sample_workflow_file, tmp_path: Path, monkeypatch
    ):
        """Test getting status of active workflow."""
        import os

        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            # Start workflow first
            await orchestrator.run("*workflow-start", workflow_id="test-workflow")
            # Get status
            result = await orchestrator.run("*workflow-status")

            assert "workflow_id" in result
            assert result["workflow_id"] == "test-workflow"
            assert "status" in result
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_get_next_step(
        self, orchestrator, sample_workflow_file, tmp_path: Path
    ):
        """Test getting next step."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            await orchestrator.run("*workflow-start", workflow_id="test-workflow")
            result = await orchestrator.run("*workflow-next")

            # Should return message that there's no next step (single step workflow)
            assert "message" in result or "next_step" in result
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_make_gate_decision_default(self, orchestrator):
        """Test making gate decision with default condition."""
        await orchestrator.activate()

        scoring_data = {"passed": True, "overall_score": 85}

        result = await orchestrator.run(
            "*gate", condition=None, scoring_data=scoring_data
        )

        assert "passed" in result
        assert result["passed"] is True
        assert result["overall_score"] == 85

    @pytest.mark.asyncio
    async def test_make_gate_decision_with_condition(self, orchestrator):
        """Test making gate decision with condition."""
        await orchestrator.activate()

        scoring_data = {"passed": True, "overall_score": 85}

        result = await orchestrator.run(
            "*gate", condition="scoring.passed == true", scoring_data=scoring_data
        )

        assert "passed" in result
        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_make_gate_decision_failed(self, orchestrator):
        """Test making gate decision when scoring fails."""
        await orchestrator.activate()

        scoring_data = {"passed": False, "overall_score": 50}

        result = await orchestrator.run(
            "*gate", condition=None, scoring_data=scoring_data
        )

        assert "passed" in result
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_help(self, orchestrator):
        """Test help command."""
        await orchestrator.activate()
        result = await orchestrator.run("*help")

        assert "commands" in result
        # Help returns commands as dict with descriptions
        assert "*workflow-list" in result["commands"]
        # Check that workflow-start is in the commands (may be with {workflow_id} suffix)
        assert any("*workflow-start" in cmd for cmd in result["commands"].keys())

    @pytest.mark.asyncio
    async def test_execute_workflow_from_file(
        self, orchestrator, sample_workflow_file, tmp_path: Path, monkeypatch
    ):
        """Test executing a workflow from a file path."""
        import os

        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            # Use relative path
            relative_path = str(sample_workflow_file.relative_to(tmp_path))
            result = await orchestrator.run("*workflow", workflow_file=relative_path)

            assert "success" in result
            assert result["success"] is True
            assert result["workflow_id"] == "test-workflow"
            assert result["workflow_file"] == str(sample_workflow_file)
            assert result["status"] == "running"
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_execute_workflow_from_file_absolute_path(
        self, orchestrator, sample_workflow_file, tmp_path: Path, monkeypatch
    ):
        """Test executing a workflow from an absolute file path."""
        import os

        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            # Use absolute path
            result = await orchestrator.run("*workflow", workflow_file=str(sample_workflow_file))

            assert "success" in result
            assert result["success"] is True
            assert result["workflow_id"] == "test-workflow"
            assert result["workflow_file"] == str(sample_workflow_file)
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_execute_workflow_from_file_subdirectory(
        self, orchestrator, tmp_path: Path, monkeypatch
    ):
        """Test executing a workflow from a file in a subdirectory."""
        import os

        workflows_dir = tmp_path / "workflows"
        custom_dir = workflows_dir / "custom"
        custom_dir.mkdir(parents=True)

        workflow_file = custom_dir / "subdir-workflow.yaml"
        workflow_file.write_text(
            yaml.dump(
                {
                    "workflow": {
                        "id": "subdir-workflow",
                        "name": "Subdirectory Workflow",
                        "description": "A workflow in a subdirectory",
                        "version": "1.0.0",
                        "type": "greenfield",
                        "steps": [
                            {
                                "id": "step1",
                                "agent": "analyst",
                                "action": "gather",
                                "requires": [],
                            }
                        ],
                    }
                }
            )
        )

        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            # Use relative path with subdirectory
            relative_path = str(workflow_file.relative_to(tmp_path))
            result = await orchestrator.run("*workflow", workflow_file=relative_path)

            assert "success" in result
            assert result["success"] is True
            assert result["workflow_id"] == "subdir-workflow"
            assert result["workflow_file"] == str(workflow_file)
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_execute_workflow_from_file_not_found(self, orchestrator, tmp_path: Path):
        """Test executing a workflow from a non-existent file."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run(
                "*workflow", workflow_file="workflows/nonexistent.yaml"
            )

            assert "error" in result
            assert "not found" in result["error"].lower()
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_execute_workflow_from_file_no_file_param(self, orchestrator, tmp_path: Path):
        """Test executing workflow command without file parameter."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            await orchestrator.activate(project_root=tmp_path)
            result = await orchestrator.run("*workflow")

            assert "error" in result
            assert "workflow_file required" in result["error"]
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_unknown_command(self, orchestrator):
        """Test unknown command."""
        await orchestrator.activate()
        result = await orchestrator.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]
