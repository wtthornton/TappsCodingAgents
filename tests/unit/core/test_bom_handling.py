"""
Tests for UTF-8 BOM handling (Windows compatibility).

These tests verify fixes for:
- Issue #1: UTF-8 BOM handling in MCP config parsing
- Issue #2: Playwright MCP package name detection
- Issue #4: init --reset should normalize BOM files
"""

from pathlib import Path

import pytest

from tapps_agents.core.init_project import (
    detect_mcp_servers,
    init_project,
    normalize_config_encoding,
)

pytestmark = pytest.mark.unit


class TestNormalizeConfigEncoding:
    """Tests for normalize_config_encoding function."""

    def test_removes_bom_from_file(self, tmp_path: Path):
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

    def test_no_op_without_bom(self, tmp_path: Path):
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

    def test_handles_nonexistent_file(self, tmp_path: Path):
        """Test that normalize_config_encoding handles nonexistent files."""
        config_file = tmp_path / "nonexistent.json"
        
        normalized, message = normalize_config_encoding(config_file)
        
        assert normalized is False
        assert message is None


class TestDetectMCPServersWithBOM:
    """Tests for detect_mcp_servers handling of UTF-8 BOM."""

    def test_handles_bom_in_mcp_json(self, tmp_path: Path):
        """Test that detect_mcp_servers handles mcp.json with UTF-8 BOM (Issue #1)."""
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


class TestPlaywrightPackageVariants:
    """Tests for Playwright MCP package name detection (Issue #2)."""

    def test_detects_playwright_mcp_variant(self, tmp_path: Path):
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

    def test_detects_playwright_mcp_server_variant(self, tmp_path: Path):
        """Test that detect_mcp_servers detects @playwright/mcp-server package variant."""
        import json
        
        # Create .cursor directory
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mcp.json with Playwright using @playwright/mcp-server
        mcp_config = {
            "mcpServers": {
                "Playwright": {
                    "command": "npx",
                    "args": ["-y", "@playwright/mcp-server"]
                }
            }
        }
        mcp_file = cursor_dir / "mcp.json"
        mcp_file.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
        
        # Should detect Playwright
        mcp_status = detect_mcp_servers(tmp_path)
        
        detected_ids = [s.get("id") for s in mcp_status.get("detected_servers", [])]
        assert "Playwright" in detected_ids, "Playwright should be detected with @playwright/mcp-server variant"


class TestInitProjectBOMNormalization:
    """Tests for init_project BOM normalization (Issue #4)."""

    def test_normalizes_mcp_encoding(self, tmp_path: Path):
        """Test that init_project normalizes encoding of mcp.json."""
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
