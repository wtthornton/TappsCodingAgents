"""
Tests for `tapps_agents.core.init_project` related to Cursor-first setup.
"""

from pathlib import Path

import pytest

from tapps_agents.core.init_project import (
    init_cursor_mcp_config,
    init_experts_scaffold,
    init_project,
)

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

    def test_init_project_does_not_install_background_agents_by_default(self, tmp_path: Path):
        """Test that background agents are NOT installed by default (opt-in behavior)."""
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=True,
            include_workflow_presets=False,
            include_config=False,
            include_skills=True,
            # include_background_agents not specified - should default to False
        )

        # Background agents config should NOT exist
        bg_config = tmp_path / ".cursor" / "background-agents.yaml"
        assert not bg_config.exists(), "Background agents should not be installed by default"

        assert results["background_agents"] is False

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

    def test_init_cursor_mcp_config_creates_mcp_json(self, tmp_path: Path):
        """Test that init_cursor_mcp_config creates .cursor/mcp.json with Context7 config."""
        created, mcp_path = init_cursor_mcp_config(project_root=tmp_path, overwrite=False)
        
        assert created is True
        assert mcp_path is not None
        assert mcp_path.endswith(".cursor/mcp.json")
        
        mcp_file = tmp_path / ".cursor" / "mcp.json"
        assert mcp_file.exists()
        
        # Verify JSON structure
        import json
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
        assert "mcpServers" in config
        assert "Context7" in config["mcpServers"]
        assert config["mcpServers"]["Context7"]["command"] == "npx"
        assert "-y" in config["mcpServers"]["Context7"]["args"]
        assert "@context7/mcp-server" in config["mcpServers"]["Context7"]["args"]
        # Verify environment variable reference (no secrets)
        assert config["mcpServers"]["Context7"]["env"]["CONTEXT7_API_KEY"] == "${CONTEXT7_API_KEY}"

    def test_init_cursor_mcp_config_idempotent(self, tmp_path: Path):
        """Test that init_cursor_mcp_config is idempotent (doesn't overwrite existing file)."""
        # Create config first time
        created1, path1 = init_cursor_mcp_config(project_root=tmp_path, overwrite=False)
        assert created1 is True
        
        # Try to create again (should skip)
        created2, path2 = init_cursor_mcp_config(project_root=tmp_path, overwrite=False)
        assert created2 is False
        assert path1 == path2

    def test_init_cursor_mcp_config_overwrite(self, tmp_path: Path):
        """Test that init_cursor_mcp_config can overwrite existing file when overwrite=True."""
        # Create config first time
        created1, _ = init_cursor_mcp_config(project_root=tmp_path, overwrite=False)
        assert created1 is True
        
        # Overwrite it
        created2, _ = init_cursor_mcp_config(project_root=tmp_path, overwrite=True)
        assert created2 is True

    def test_init_experts_scaffold_creates_files(self, tmp_path: Path):
        """Test that init_experts_scaffold creates all expected files and directories."""
        results = init_experts_scaffold(project_root=tmp_path)
        
        # Check domains.md
        domains_file = tmp_path / ".tapps-agents" / "domains.md"
        assert domains_file.exists()
        assert "domains.md" in results["domains_md"]
        assert str(domains_file) in results["created"]
        
        # Check experts.yaml
        experts_file = tmp_path / ".tapps-agents" / "experts.yaml"
        assert experts_file.exists()
        assert "experts.yaml" in results["experts_yaml"]
        assert str(experts_file) in results["created"]
        
        # Check knowledge directory
        knowledge_dir = tmp_path / ".tapps-agents" / "knowledge"
        assert knowledge_dir.exists()
        assert knowledge_dir.is_dir()
        assert "knowledge" in results["knowledge_dir"]
        
        # Check knowledge README
        knowledge_readme = knowledge_dir / "README.md"
        assert knowledge_readme.exists()
        assert str(knowledge_readme) in results["created"]
        
        # Check general example
        general_example = knowledge_dir / "general" / "project-overview.md"
        assert general_example.exists()
        assert str(general_example) in results["created"]

    def test_init_experts_scaffold_idempotent(self, tmp_path: Path):
        """Test that init_experts_scaffold is idempotent (doesn't recreate existing files)."""
        # Create scaffold first time
        results1 = init_experts_scaffold(project_root=tmp_path)
        created_count1 = len(results1["created"])
        assert created_count1 > 0
        
        # Create again (should not recreate)
        results2 = init_experts_scaffold(project_root=tmp_path)
        created_count2 = len(results2["created"])
        assert created_count2 == 0  # No new files created

    def test_init_project_includes_mcp_config_and_experts_scaffold(self, tmp_path: Path):
        """Test that init_project includes MCP config and experts scaffold in results."""
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=False,
            include_workflow_presets=False,
            include_config=False,
            include_skills=False,
            include_background_agents=False,
            pre_populate_cache=False,
        )
        
        # Check MCP config
        assert "mcp_config" in results
        mcp_config = results["mcp_config"]
        assert "created" in mcp_config
        assert "path" in mcp_config
        if mcp_config["created"]:
            mcp_file = tmp_path / ".cursor" / "mcp.json"
            assert mcp_file.exists()
        
        # Check experts scaffold
        assert "experts_scaffold" in results
        experts_scaffold = results["experts_scaffold"]
        assert "domains_md" in experts_scaffold
        assert "experts_yaml" in experts_scaffold
        assert "knowledge_dir" in experts_scaffold
        
        # Verify files are in files_created
        if mcp_config.get("path"):
            assert mcp_config["path"] in results["files_created"]
        if experts_scaffold.get("created"):
            for file_path in experts_scaffold["created"]:
                assert file_path in results["files_created"]

    def test_cursor_verification_includes_simple_mode_mdc(self, tmp_path: Path):
        """Test that cursor verification includes simple-mode.mdc in expected rules."""
        from tapps_agents.core.cursor_verification import verify_cursor_integration
        
        # Initialize project with cursor rules
        init_project(
            project_root=tmp_path,
            include_cursor_rules=True,
            include_workflow_presets=False,
            include_config=False,
            include_skills=True,
            include_background_agents=False,
            pre_populate_cache=False,
        )
        
        # Verify integration
        is_valid, results = verify_cursor_integration(project_root=tmp_path)
        
        # Check that simple-mode.mdc is in expected rules
        rules_result = results["components"]["rules"]
        assert "simple-mode.mdc" in rules_result["expected_rules"]
        
        # Check if it was found (should be if init copied it)
        rules_dir = tmp_path / ".cursor" / "rules"
        simple_mode_file = rules_dir / "simple-mode.mdc"
        if simple_mode_file.exists():
            assert "simple-mode.mdc" in rules_result["rules_found"]


