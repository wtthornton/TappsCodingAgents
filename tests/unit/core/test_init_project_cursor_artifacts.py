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

    def test_init_project_with_empty_project_detects_no_tech_stack(self, tmp_path: Path):
        """Test that init_project handles empty projects (no dependency files) correctly."""
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=False,
            include_workflow_presets=False,
            include_config=True,
            include_skills=False,
            include_background_agents=False,
            pre_populate_cache=False,  # Disable cache to focus on tech stack detection
        )

        # Tech stack should be detected but empty
        assert "tech_stack" in results
        tech_stack = results["tech_stack"]
        assert tech_stack is not None
        assert tech_stack["languages"] == []
        assert tech_stack["frameworks"] == []
        assert tech_stack["libraries"] == []
        assert tech_stack["package_managers"] == []
        assert tech_stack["detected_files"] == []

    def test_init_project_cache_prepopulation_with_empty_project_libraries(
        self, tmp_path: Path, monkeypatch
    ):
        """
        Test that cache prepopulation attempts even when project libraries are empty.
        
        This test verifies the fix for the bug where expert libraries weren't cached
        when project libraries were empty.
        """
        # Mock the cache prepopulation to avoid actual Context7 calls
        cache_prepop_called = False
        cache_prepop_libraries = None

        async def mock_pre_populate_context7_cache(project_root, libraries):
            nonlocal cache_prepop_called, cache_prepop_libraries
            cache_prepop_called = True
            cache_prepop_libraries = libraries
            # Return a mock result indicating expert libraries would be cached
            return {
                "success": True,
                "cached": 50,
                "failed": 0,
                "total": 50,
                "project_libraries": 0,
                "expert_libraries": 50,
            }

        # Patch the function
        monkeypatch.setattr(
            "tapps_agents.core.init_project.pre_populate_context7_cache",
            mock_pre_populate_context7_cache,
        )

        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=False,
            include_workflow_presets=False,
            include_config=True,
            include_skills=False,
            include_background_agents=False,
            pre_populate_cache=True,
        )

        # Verify cache prepopulation was attempted even with empty project libraries
        assert cache_prepop_called, "Cache prepopulation should be called even with empty project"
        assert cache_prepop_libraries == [], "Should pass empty list for project libraries"
        assert results["cache_prepopulated"] is True
        assert results["cache_result"]["expert_libraries"] == 50

    def test_init_project_with_requirements_txt_detects_tech_stack(self, tmp_path: Path):
        """Test that init_project detects tech stack from requirements.txt."""
        # Create a requirements.txt file
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("fastapi>=0.100.0\npytest>=7.0.0\nsqlalchemy>=2.0.0\n")

        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=False,
            include_workflow_presets=False,
            include_config=True,
            include_skills=False,
            include_background_agents=False,
            pre_populate_cache=False,
        )

        # Tech stack should be detected
        assert "tech_stack" in results
        tech_stack = results["tech_stack"]
        assert "python" in tech_stack["languages"]
        assert "pip" in tech_stack["package_managers"]
        assert "requirements.txt" in tech_stack["detected_files"]
        assert len(tech_stack["libraries"]) >= 3
        assert "fastapi" in tech_stack["libraries"]
        assert "pytest" in tech_stack["libraries"]
        assert "sqlalchemy" in tech_stack["libraries"]


