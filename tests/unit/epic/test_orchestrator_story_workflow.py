"""
Unit tests for EpicOrchestrator story workflow generation and parsing.

Ensures the YAML format used for epic story workflows is parseable by
WorkflowParser.parse_yaml() so we avoid regressions (e.g. calling
a non-existent parse_workflow method).
"""

import pytest

from tapps_agents.workflow.parser import WorkflowParser

# Minimal workflow YAML in the same format as EpicOrchestrator._create_story_workflow
STORY_WORKFLOW_YAML = """
workflow:
  id: story-2.1
  name: "Story 2.1: Add reviewer quality tools"
  description: "Implement scoring and lint."
  version: "1.0.0"
  type: greenfield
  auto_detect: false
  settings:
    quality_gates: true
    code_scoring: true
    context_tier_default: 2
  steps:
    - id: enhance
      agent: enhancer
      action: enhance
      context_tier: 1
      requires: []
      next: plan
    - id: plan
      agent: planner
      action: plan
      context_tier: 1
      requires: [enhance]
      next: implement
    - id: implement
      agent: implementer
      action: implement
      context_tier: 3
      requires: [plan]
      next: review
    - id: review
      agent: reviewer
      action: review
      context_tier: 2
      requires: [implement]
      next: test
    - id: test
      agent: tester
      action: test
      context_tier: 2
      requires: [implement]
      next: complete
    - id: complete
      agent: orchestrator
      action: finalize
      context_tier: 1
"""


@pytest.mark.unit
class TestEpicOrchestratorStoryWorkflow:
    """Tests for epic story workflow YAML parsing."""

    def test_story_workflow_yaml_parses_with_parse_yaml(self) -> None:
        """Story workflow YAML must parse via WorkflowParser.parse_yaml (not parse_workflow)."""
        workflow = WorkflowParser.parse_yaml(STORY_WORKFLOW_YAML)

        assert workflow.id == "story-2.1"
        assert "2.1" in workflow.name and "Add reviewer quality tools" in workflow.name
        assert len(workflow.steps) >= 5
        step_ids = [s.id for s in workflow.steps]
        assert "enhance" in step_ids
        assert "plan" in step_ids
        assert "implement" in step_ids
        assert "review" in step_ids
        assert "test" in step_ids
