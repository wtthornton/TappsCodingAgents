"""
Tests for `tapps_agents.core.init_project` related to Cursor-first setup.
"""

from pathlib import Path

import pytest

from tapps_agents.core.init_project import init_project


pytestmark = pytest.mark.unit


class TestInitProjectCursorArtifacts:
    def test_init_project_installs_cursor_rules_skills_and_background_agents(self, tmp_path: Path):
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=True,
            include_workflow_presets=False,
            include_config=False,
            include_skills=True,
            include_background_agents=True,
        )

        # Cursor rules
        rules_dir = tmp_path / ".cursor" / "rules"
        assert rules_dir.exists()
        assert (rules_dir / "workflow-presets.mdc").exists()
        assert (rules_dir / "quick-reference.mdc").exists()
        assert (rules_dir / "agent-capabilities.mdc").exists()
        assert (rules_dir / "project-context.mdc").exists()

        # Skills
        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.exists()
        # At least one skill folder should be installed
        assert any(p.is_dir() for p in skills_dir.iterdir())

        # Background agents config
        bg_config = tmp_path / ".cursor" / "background-agents.yaml"
        assert bg_config.exists()

        assert results["cursor_rules"] is True
        assert results["skills"] is True
        assert results["background_agents"] is True


