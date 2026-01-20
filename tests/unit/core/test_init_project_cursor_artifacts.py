"""
Tests for `tapps_agents.core.init_project` related to Cursor-first setup.
"""

from pathlib import Path

import pytest

from tapps_agents.core.init_project import (
    detect_mcp_servers,
    init_cursor_mcp_config,
    init_experts_scaffold,
    init_project,
    normalize_config_encoding,
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
            pre_populate_cache=False,  # Disable cache to avoid HTTP timeouts
            # Note: include_background_agents parameter was removed - background agents are no longer installed
        )

        # Cursor rules
        rules_dir = tmp_path / ".cursor" / "rules"
        assert rules_dir.exists()
        assert (rules_dir / "workflow-presets.mdc").exists()
        assert (rules_dir / "quick-reference.mdc").exists()
        assert (rules_dir / "agent-capabilities.mdc").exists()
        assert (rules_dir / "when-to-use.mdc").exists()
        assert (rules_dir / "project-context.mdc").exists()

        # Skills
        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.exists()
        # At least one skill folder should be installed
        assert any(p.is_dir() for p in skills_dir.iterdir())

        # Background agents config - no longer installed (feature removed)
        bg_config = tmp_path / ".cursor" / "background-agents.yaml"
        # Note: Background agents feature was removed, so this file should not exist
        # The test name is kept for historical reference but behavior has changed

        assert results["cursor_rules"] is True
        assert results["skills"] is True
        # Note: background_agents key is no longer in results (feature was removed)

    def test_init_project_does_not_install_background_agents_by_default(self, tmp_path: Path):
        """Test that background agents are NOT installed by default (opt-in behavior)."""
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=True,
            include_workflow_presets=False,
            include_config=False,
            include_skills=True,
            pre_populate_cache=False,  # Disable cache to avoid HTTP timeouts
            # include_background_agents not specified - should default to False
        )

        # Background agents config should NOT exist
        bg_config = tmp_path / ".cursor" / "background-agents.yaml"
        assert not bg_config.exists(), "Background agents should not be installed by default"
        
        # Note: background_agents key is no longer in results (feature was removed)
        # The test just verifies the file doesn't exist, which is the important check

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

    def test_init_project_cache_deferred_when_pre_populate_cache_true(
        self, tmp_path: Path
    ):
        """
        Test that with pre_populate_cache=True, init_project defers cache to CLI
        by setting cache_requested and cache_libraries (does not run cache itself).
        Cache runs later in the CLI after core init output.
        """
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=False,
            include_workflow_presets=False,
            include_config=True,
            include_skills=False,
            pre_populate_cache=True,
        )

        # Deferred: init_project does not run cache, only requests it
        assert results.get("cache_requested") is True
        assert results.get("cache_libraries") == []
        assert "cache_result" not in results or results.get("cache_result") is None
        # cache_prepopulated remains default until CLI runs cache
        assert results.get("cache_prepopulated") is False

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


class TestBOMHandling:
    """Tests for UTF-8 BOM handling (Windows compatibility)."""

    def test_normalize_config_encoding_removes_bom(self, tmp_path: Path):
        """Test that normalize_config_encoding removes UTF-8 BOM from files."""
        config_file = tmp_path / "config.json"
        # Write file with UTF-8 BOM
        content = '{"test": "value"}'
        config_file.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
        
        # Verify BOM is present
        raw_bytes = config_file.read_bytes()
        assert raw_bytes.startswith(b"\xef\xbb\xbf"), "BOM should be present initially"
        
        # Normalize encoding
        normalized, message = normalize_config_encoding(config_file)
        
        assert normalized is True
        assert message is not None
        assert "BOM" in message
        
        # Verify BOM is removed
        raw_bytes_after = config_file.read_bytes()
        assert not raw_bytes_after.startswith(b"\xef\xbb\xbf"), "BOM should be removed"
        # Content should be preserved
        assert config_file.read_text(encoding="utf-8") == content

    def test_normalize_config_encoding_no_op_without_bom(self, tmp_path: Path):
        """Test that normalize_config_encoding does nothing if no BOM present."""
        config_file = tmp_path / "config.json"
        content = '{"test": "value"}'
        config_file.write_text(content, encoding="utf-8")
        
        # Normalize encoding
        normalized, message = normalize_config_encoding(config_file)
        
        assert normalized is False
        assert message is None
        # Content should be unchanged
        assert config_file.read_text(encoding="utf-8") == content

    def test_detect_mcp_servers_handles_bom_in_mcp_json(self, tmp_path: Path):
        """Test that detect_mcp_servers handles mcp.json with UTF-8 BOM."""
        import json
        
        # Create .cursor directory
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mcp.json with Context7 config and UTF-8 BOM
        mcp_config = {
            "mcpServers": {
                "Context7": {
                    "command": "npx",
                    "args": ["-y", "@context7/mcp-server"],
                    "env": {"CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"}
                }
            }
        }
        mcp_file = cursor_dir / "mcp.json"
        json_content = json.dumps(mcp_config, indent=2)
        # Write with UTF-8 BOM
        mcp_file.write_bytes(b"\xef\xbb\xbf" + json_content.encode("utf-8"))
        
        # Should detect Context7 despite BOM
        mcp_status = detect_mcp_servers(tmp_path)
        
        detected_ids = [s.get("id") for s in mcp_status.get("detected_servers", [])]
        assert "Context7" in detected_ids, "Context7 should be detected despite BOM in mcp.json"

    def test_detect_mcp_servers_detects_playwright_mcp_variant(self, tmp_path: Path):
        """Test that detect_mcp_servers detects @playwright/mcp package variant."""
        import json
        
        # Create .cursor directory
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mcp.json with Playwright using @playwright/mcp (not @playwright/mcp-server)
        mcp_config = {
            "mcpServers": {
                "Playwright": {
                    "command": "npx",
                    "args": ["-y", "@playwright/mcp@0.0.35"]
                }
            }
        }
        mcp_file = cursor_dir / "mcp.json"
        mcp_file.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
        
        # Should detect Playwright
        mcp_status = detect_mcp_servers(tmp_path)
        
        detected_ids = [s.get("id") for s in mcp_status.get("detected_servers", [])]
        assert "Playwright" in detected_ids, "Playwright should be detected with @playwright/mcp variant"

    def test_init_project_normalizes_encoding(self, tmp_path: Path):
        """Test that init_project normalizes encoding of config files."""
        import json
        
        # Create existing mcp.json with BOM
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        mcp_file = cursor_dir / "mcp.json"
        mcp_config = {"mcpServers": {"Test": {}}}
        mcp_file.write_bytes(b"\xef\xbb\xbf" + json.dumps(mcp_config).encode("utf-8"))
        
        # Run init (with most options disabled for speed)
        results = init_project(
            project_root=tmp_path,
            include_cursor_rules=False,
            include_workflow_presets=False,
            include_config=True,
            include_skills=False,
            include_cursorignore=False,
            pre_populate_cache=False,
        )
        
        # Check encoding was normalized
        assert "mcp_encoding_normalized" in results, "MCP encoding should be normalized"
        
        # Verify BOM is removed from mcp.json
        raw_bytes = mcp_file.read_bytes()
        assert not raw_bytes.startswith(b"\xef\xbb\xbf"), "BOM should be removed from mcp.json"
