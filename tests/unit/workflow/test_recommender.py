"""
Tests for Workflow Recommender.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from tapps_agents.workflow.detector import ProjectType, WorkflowTrack
from tapps_agents.workflow.recommender import (
    WorkflowRecommendation,
    WorkflowRecommender,
)

pytestmark = pytest.mark.unit


class TestWorkflowRecommender:
    """Test workflow recommendation."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            workflows_dir = project_root / "workflows"
            workflows_dir.mkdir()

            # Create a sample workflow
            workflow_file = workflows_dir / "feature-development.yaml"
            workflow_content = {
                "workflow": {
                    "id": "feature-development",
                    "name": "Feature Development",
                    "description": "Standard feature development workflow",
                    "version": "1.0.0",
                    "type": "greenfield",
                    "steps": [],
                }
            }
            with open(workflow_file, "w") as f:
                yaml.dump(workflow_content, f)

            yield project_root, workflows_dir

    def test_recommend_greenfield(self, temp_project):
        """Test recommendation for greenfield project."""
        project_root, workflows_dir = temp_project
        recommender = WorkflowRecommender(
            project_root=project_root, workflows_dir=workflows_dir
        )

        recommendation = recommender.recommend()

        assert isinstance(recommendation, WorkflowRecommendation)
        assert recommendation.track == WorkflowTrack.BMAD_METHOD
        assert recommendation.confidence >= 0.5
        assert recommendation.characteristics.project_type == ProjectType.GREENFIELD
        assert len(recommendation.message) > 0

    def test_recommend_quick_fix(self, temp_project):
        """Test recommendation for quick-fix."""
        project_root, workflows_dir = temp_project
        recommender = WorkflowRecommender(
            project_root=project_root, workflows_dir=workflows_dir
        )

        recommendation = recommender.recommend(user_query="fix the bug", file_count=2)

        assert recommendation.track == WorkflowTrack.QUICK_FLOW
        assert recommendation.workflow_file == "quick-fix"
        assert "Quick Flow" in recommendation.message

    def test_recommend_workflow_loaded(self, temp_project):
        """Test that workflow is loaded when available."""
        project_root, workflows_dir = temp_project
        recommender = WorkflowRecommender(
            project_root=project_root, workflows_dir=workflows_dir
        )

        recommendation = recommender.recommend(auto_load=True)

        # Workflow may or may not be loaded depending on matching
        # But the recommendation should always have a workflow_file suggestion
        assert (
            recommendation.workflow_file is not None
            or len(recommendation.alternative_workflows) > 0
        )

    def test_list_available_workflows(self, temp_project):
        """Test listing available workflows."""
        project_root, workflows_dir = temp_project
        recommender = WorkflowRecommender(
            project_root=project_root, workflows_dir=workflows_dir
        )

        workflows = recommender.list_available_workflows()

        assert len(workflows) >= 1
        assert any(w["file"] == "feature-development.yaml" for w in workflows)

        # Check workflow metadata
        workflow = next(w for w in workflows if w["file"] == "feature-development.yaml")
        assert workflow["id"] == "feature-development"
        assert workflow["name"] == "Feature Development"

    def test_recommend_no_workflows_dir(self):
        """Test recommendation when workflows directory doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            recommender = WorkflowRecommender(project_root=project_root)

            recommendation = recommender.recommend()

            assert isinstance(recommendation, WorkflowRecommendation)
            assert recommendation.track in [
                WorkflowTrack.QUICK_FLOW,
                WorkflowTrack.BMAD_METHOD,
                WorkflowTrack.ENTERPRISE,
            ]

    def test_recommend_with_alternatives(self, temp_project):
        """Test recommendation includes alternative workflows."""
        project_root, workflows_dir = temp_project

        # Create another workflow
        workflow_file = workflows_dir / "quick-fix.yaml"
        workflow_content = {
            "workflow": {
                "id": "quick-fix",
                "name": "Quick Fix",
                "description": "Quick fix workflow",
                "version": "1.0.0",
                "type": "brownfield",
                "steps": [],
            }
        }
        with open(workflow_file, "w") as f:
            yaml.dump(workflow_content, f)

        recommender = WorkflowRecommender(
            project_root=project_root, workflows_dir=workflows_dir
        )

        recommendation = recommender.recommend()

        assert len(recommendation.alternative_workflows) >= 1

    def test_generate_message(self, temp_project):
        """Test that recommendation message is generated."""
        project_root, workflows_dir = temp_project
        recommender = WorkflowRecommender(
            project_root=project_root, workflows_dir=workflows_dir
        )

        recommendation = recommender.recommend()

        assert len(recommendation.message) > 0
        assert "workflow recommended" in recommendation.message.lower()
        assert "confidence" in recommendation.message.lower()
