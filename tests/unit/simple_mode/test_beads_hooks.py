"""
Unit tests for tapps_agents.simple_mode.beads_hooks: create_review_issue,
create_test_issue, create_refactor_issue, create_workflow_issue.

Uses mocks for is_available and run_bd; no real bd required.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.simple_mode.beads_hooks import (
    create_refactor_issue,
    create_review_issue,
    create_test_issue,
    create_workflow_issue,
)


def _mock_config(*, enabled: bool = True, hooks_review: bool = False, hooks_test: bool = False,
                 hooks_refactor: bool = False, hooks_workflow: bool = False):
    c = MagicMock()
    c.beads.enabled = enabled
    c.beads.hooks_review = hooks_review
    c.beads.hooks_test = hooks_test
    c.beads.hooks_refactor = hooks_refactor
    c.beads.hooks_workflow = hooks_workflow
    return c


@pytest.mark.unit
class TestCreateReviewIssue:
    def test_returns_none_when_disabled(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=False, hooks_review=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_review_issue(tmp_path, config, "x.py") is None

    def test_returns_none_when_hooks_review_false(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_review=False)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_review_issue(tmp_path, config, "x.py") is None

    def test_returns_none_when_bd_not_available(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_review=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=False):
            assert create_review_issue(tmp_path, config, "x.py") is None

    def test_returns_parsed_id_when_enabled_and_success(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_review=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True), \
             patch("tapps_agents.simple_mode.beads_hooks.run_bd") as m:
            m.return_value = MagicMock(returncode=0, stdout="Created issue: Proj-a1b2c3")
            assert create_review_issue(tmp_path, config, "x.py") == "Proj-a1b2c3"


@pytest.mark.unit
class TestCreateTestIssue:
    def test_returns_none_when_disabled(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=False, hooks_test=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_test_issue(tmp_path, config, "x.py") is None

    def test_returns_none_when_hooks_test_false(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_test=False)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_test_issue(tmp_path, config, "x.py") is None

    def test_returns_none_when_bd_not_available(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_test=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=False):
            assert create_test_issue(tmp_path, config, "x.py") is None

    def test_returns_parsed_id_when_enabled_and_success(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_test=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True), \
             patch("tapps_agents.simple_mode.beads_hooks.run_bd") as m:
            m.return_value = MagicMock(returncode=0, stdout="Created issue: Proj-d4e5f6")
            assert create_test_issue(tmp_path, config, "x.py") == "Proj-d4e5f6"


@pytest.mark.unit
class TestCreateRefactorIssue:
    def test_returns_none_when_disabled(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=False, hooks_refactor=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_refactor_issue(tmp_path, config, "x.py", "desc") is None

    def test_returns_none_when_hooks_refactor_false(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_refactor=False)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_refactor_issue(tmp_path, config, "x.py", "desc") is None

    def test_returns_none_when_bd_not_available(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_refactor=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=False):
            assert create_refactor_issue(tmp_path, config, "x.py", "desc") is None

    def test_returns_parsed_id_when_enabled_and_success(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_refactor=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True), \
             patch("tapps_agents.simple_mode.beads_hooks.run_bd") as m:
            m.return_value = MagicMock(returncode=0, stdout="Created issue: Proj-g7h8i9")
            assert create_refactor_issue(tmp_path, config, "x.py", "modernize") == "Proj-g7h8i9"


@pytest.mark.unit
class TestCreateWorkflowIssue:
    def test_returns_none_when_disabled(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=False, hooks_workflow=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_workflow_issue(tmp_path, config, "rapid", "prompt") is None

    def test_returns_none_when_hooks_workflow_false(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_workflow=False)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True):
            assert create_workflow_issue(tmp_path, config, "rapid", "prompt") is None

    def test_returns_none_when_bd_not_available(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_workflow=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=False):
            assert create_workflow_issue(tmp_path, config, "rapid", "prompt") is None

    def test_returns_parsed_id_when_enabled_and_success(self, tmp_path: Path) -> None:
        config = _mock_config(enabled=True, hooks_workflow=True)
        with patch("tapps_agents.simple_mode.beads_hooks.is_available", return_value=True), \
             patch("tapps_agents.simple_mode.beads_hooks.run_bd") as m:
            m.return_value = MagicMock(returncode=0, stdout="Created issue: Proj-j0k1l2")
            assert create_workflow_issue(tmp_path, config, "rapid", "add auth") == "Proj-j0k1l2"
