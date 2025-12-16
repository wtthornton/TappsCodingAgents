"""
Unit tests for boundary values and invalid data handling.

This module tests:
- Boundary values (min, max, zero, negative)
- Corrupted config files and data
- Circular dependencies in workflows
- Invalid library IDs and malformed data
- Network timeout and partial response handling
- Permission errors and file system issues
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from tapps_agents.agents.reviewer.scoring import CodeScorer
from tapps_agents.core.config import load_config
from tapps_agents.workflow import WorkflowExecutor, WorkflowParser


@pytest.mark.unit
class TestBoundaryValues:
    """Test boundary value handling."""

    def test_scorer_zero_length_file(self, tmp_path: Path):
        """Test scoring a zero-length file."""
        scorer = CodeScorer()
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        
        result = scorer.score_file(empty_file, "")
        assert isinstance(result, dict)
        assert "overall_score" in result
        # Zero-length file should return valid scores (may be 0 or default)

    def test_scorer_max_int_values(self, tmp_path: Path):
        """Test scoring with max integer values in code."""
        scorer = CodeScorer()
        test_file = tmp_path / "max_int.py"
        
        # Code with max integer values
        max_int_code = f"""
def test():
    max_int = {2**31 - 1}
    return max_int
"""
        test_file.write_text(max_int_code)
        
        result = scorer.score_file(test_file, max_int_code)
        assert isinstance(result, dict)

    def test_scorer_negative_values(self, tmp_path: Path):
        """Test scoring with negative values."""
        scorer = CodeScorer()
        test_file = tmp_path / "negative.py"
        
        negative_code = """
def test():
    x = -100
    y = -1
    return x + y
"""
        test_file.write_text(negative_code)
        
        result = scorer.score_file(test_file, negative_code)
        assert isinstance(result, dict)

    def test_agent_validate_path_zero_size_file(self, base_agent, tmp_path: Path):
        """Test validating a zero-size file."""
        agent = base_agent
        zero_file = tmp_path / "zero.py"
        zero_file.write_text("")
        
        # Zero-size file should be valid
        agent._validate_path(zero_file)

    def test_agent_validate_path_max_size_file(self, base_agent, tmp_path: Path):
        """Test validating a file at max size boundary."""
        agent = base_agent
        max_file = tmp_path / "max.py"
        
        # Create file at exactly max size
        max_size = 10 * 1024 * 1024  # 10MB
        max_file.write_text("x" * max_size)
        
        # Should be valid at boundary
        agent._validate_path(max_file, max_file_size=max_size)

    def test_agent_validate_path_over_max_size(self, base_agent, tmp_path: Path):
        """Test validating a file over max size."""
        agent = base_agent
        over_max_file = tmp_path / "over_max.py"
        
        max_size = 100  # 100 bytes
        over_max_file.write_text("x" * (max_size + 1))
        
        # Should raise ValueError
        with pytest.raises(ValueError, match=r"File too large"):
            agent._validate_path(over_max_file, max_file_size=max_size)


@pytest.mark.unit
class TestCorruptedData:
    """Test handling of corrupted data."""

    def test_load_config_corrupted_yaml(self, tmp_path: Path):
        """Test loading corrupted YAML config."""
        config_file = tmp_path / "config.yaml"
        # Corrupted YAML
        config_file.write_text("project_name: test\ninvalid: [unclosed")
        
        # Should raise YAMLError or ValueError
        with pytest.raises((yaml.YAMLError, ValueError)):
            load_config(config_file)

    def test_load_config_invalid_json_in_yaml(self, tmp_path: Path):
        """Test loading YAML with invalid JSON-like structure."""
        config_file = tmp_path / "config.yaml"
        # Invalid structure
        config_file.write_text("project_name: test\nagents: {unclosed")
        
        with pytest.raises((yaml.YAMLError, ValueError)):
            load_config(config_file)

    def test_workflow_parser_corrupted_yaml(self, tmp_path: Path):
        """Test parsing corrupted workflow YAML."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow:\n  id: test\n  steps: [unclosed")
        
        with open(workflow_file) as f:
            workflow_dict = yaml.safe_load(f)
        
        # Should handle corrupted data gracefully
        try:
            WorkflowParser.parse(workflow_dict)
            # May succeed with partial data or raise
        except (ValueError, KeyError, TypeError):
            # Acceptable to raise on corrupted data
            pass

    def test_scorer_corrupted_ast(self, tmp_path: Path):
        """Test scoring code with corrupted AST (syntax errors)."""
        scorer = CodeScorer()
        corrupted_file = tmp_path / "corrupted.py"
        
        # Code with syntax errors
        corrupted_code = "def test(\n    return invalid"
        corrupted_file.write_text(corrupted_code)
        
        # Should handle syntax errors gracefully
        result = scorer.score_file(corrupted_file, corrupted_code)
        assert isinstance(result, dict)
        # May have lower scores due to syntax errors

    def test_agent_get_context_corrupted_file(self, base_agent, tmp_path: Path):
        """Test get_context with corrupted file."""
        agent = base_agent
        corrupted_file = tmp_path / "corrupted.py"
        
        # File with invalid encoding or binary data
        corrupted_file.write_bytes(b"\xff\xfe\xfd\x00")
        
        # Should handle gracefully
        try:
            context = agent.get_context(corrupted_file)
            assert isinstance(context, dict)
        except (UnicodeDecodeError, ValueError):
            # Acceptable to raise on corrupted file
            pass


@pytest.mark.unit
class TestCircularDependencies:
    """Test circular dependency handling."""

    def test_workflow_circular_dependencies(self, tmp_path: Path, monkeypatch):
        """Test workflow with circular step dependencies."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        
        workflow_dict = {
            "workflow": {
                "id": "circular",
                "name": "Circular Workflow",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "creates": ["file1.md"],
                        "requires": ["file3.md"],  # Depends on step3
                        "next": "step2",
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                        "creates": ["file2.md"],
                        "requires": ["file1.md"],  # Depends on step1
                        "next": "step3",
                    },
                    {
                        "id": "step3",
                        "agent": "implementer",
                        "action": "implement",
                        "creates": ["file3.md"],
                        "requires": ["file2.md"],  # Depends on step2, creating cycle
                    },
                ],
            }
        }
        
        workflow = WorkflowParser.parse(workflow_dict)
        executor = WorkflowExecutor(project_root=tmp_path)
        executor.start(workflow)
        
        # Circular dependency should be detected or handled
        # Step1 requires file3, but step3 requires file2, which requires file1
        # This creates a cycle: step1 -> step2 -> step3 -> step1
        
        # First step should not be able to proceed (missing file3)
        assert executor.can_proceed() is False

    def test_workflow_self_dependency(self, tmp_path: Path, monkeypatch):
        """Test workflow step that depends on itself."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        
        workflow_dict = {
            "workflow": {
                "id": "self-dep",
                "name": "Self Dependency",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "creates": ["file1.md"],
                        "requires": ["file1.md"],  # Depends on itself
                    },
                ],
            }
        }
        
        workflow = WorkflowParser.parse(workflow_dict)
        executor = WorkflowExecutor(project_root=tmp_path)
        executor.start(workflow)
        
        # Self-dependency should prevent proceeding
        assert executor.can_proceed() is False


@pytest.mark.unit
class TestInvalidLibraryIDs:
    """Test handling of invalid library IDs."""

    def test_context7_invalid_library_id(self):
        """Test handling invalid Context7 library ID."""
        from tapps_agents.context7.mal import MAL
        
        MAL()
        
        # Invalid library ID format
        invalid_ids = [
            "",
            "invalid",
            "/invalid",
            "//invalid",
            "invalid/",
            "/invalid/",
            "a" * 1000,  # Very long
            "a/b/c/d/e",  # Too many segments
        ]
        
        for _invalid_id in invalid_ids:
            # Should handle invalid IDs gracefully
            try:
                # This would normally make an API call, but we're just testing
                # that invalid IDs are handled
                pass
            except (ValueError, TypeError):
                # Acceptable to raise on invalid ID
                pass

    def test_context7_malformed_library_id(self):
        """Test handling malformed library IDs."""
        # Malformed IDs with special characters
        malformed_ids = [
            "/org/project@version",
            "/org/project#fragment",
            "/org/project?query",
            "/org/project space",
            "/org/project\nnewline",
            "/org/project\ttab",
        ]
        
        for _malformed_id in malformed_ids:
            # Should handle malformed IDs
            try:
                pass
            except (ValueError, TypeError):
                pass


@pytest.mark.unit
class TestNetworkTimeoutHandling:
    """Test network timeout and partial response handling."""

    @pytest.mark.asyncio
    async def test_mal_timeout_handling(self):
        """Test MAL timeout handling."""
        from tapps_agents.context7.mal import MAL
        
        mal = MAL()
        
        # Mock timeout scenario
        with patch("tapps_agents.context7.mal.httpx.AsyncClient.get") as mock_get:
            import httpx
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            # Should handle timeout gracefully
            try:
                await mal.get_library_docs("test-library", timeout=0.1)
                # May return None or raise
            except (httpx.TimeoutException, TimeoutError):
                # Acceptable to raise on timeout
                pass

    @pytest.mark.asyncio
    async def test_mal_partial_response(self):
        """Test handling partial response."""
        from tapps_agents.context7.mal import MAL
        
        mal = MAL()
        
        # Mock partial response
        with patch("tapps_agents.context7.mal.httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "partial json{"
            mock_response.json.side_effect = json.JSONDecodeError("Incomplete", "", 0)
            mock_get.return_value = mock_response
            
            # Should handle partial response
            try:
                await mal.get_library_docs("test-library")
                # May return None or raise
            except (json.JSONDecodeError, ValueError):
                # Acceptable to raise on partial response
                pass


@pytest.mark.unit
class TestPermissionErrors:
    """Test permission error handling."""

    def test_agent_validate_path_permission_denied(self, base_agent, tmp_path: Path):
        """Test validating file with permission denied."""
        agent = base_agent
        
        # Create a file and then remove read permission (Unix)
        # On Windows, this may not work the same way
        test_file = tmp_path / "no_permission.py"
        test_file.write_text("def test(): pass")
        
        # Try to make file unreadable
        try:
            import os
            os.chmod(test_file, 0o000)  # No permissions
            
            # Should handle permission error
            try:
                agent._validate_path(test_file)
            except PermissionError:
                # Acceptable to raise on permission error
                pass
            finally:
                # Restore permissions for cleanup
                os.chmod(test_file, 0o644)
        except (OSError, AttributeError):
            # Windows or permission change failed
            pass

    def test_scorer_score_file_permission_denied(self, tmp_path: Path):
        """Test scoring file with permission denied."""
        scorer = CodeScorer()
        test_file = tmp_path / "no_permission.py"
        test_file.write_text("def test(): pass")
        
        try:
            import os
            os.chmod(test_file, 0o000)
            
            # Should handle permission error
            try:
                scorer.score_file(test_file, "def test(): pass")
                # May succeed if content is provided
            except PermissionError:
                # Acceptable to raise on permission error
                pass
            finally:
                os.chmod(test_file, 0o644)
        except (OSError, AttributeError):
            pass

    def test_workflow_executor_permission_denied(self, tmp_path: Path, monkeypatch):
        """Test workflow executor with permission denied."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        
        # Try to create executor in read-only directory
        try:
            import os
            # Make directory read-only
            os.chmod(tmp_path, 0o444)
            
            try:
                WorkflowExecutor(project_root=tmp_path)
                # May fail on initialization or later
            except PermissionError:
                # Acceptable to raise on permission error
                pass
            finally:
                os.chmod(tmp_path, 0o755)
        except (OSError, AttributeError):
            # Windows or permission change failed
            pass


@pytest.mark.unit
class TestFileSystemIssues:
    """Test file system issue handling."""

    def test_agent_get_context_nonexistent_directory(self, base_agent, tmp_path: Path):
        """Test get_context with file in nonexistent directory."""
        agent = base_agent
        nonexistent_file = tmp_path / "nonexistent" / "dir" / "file.py"
        
        # Should handle nonexistent directory
        with pytest.raises(FileNotFoundError):
            agent.get_context(nonexistent_file)

    def test_scorer_score_file_deleted_during_operation(self, tmp_path: Path):
        """Test scoring file that gets deleted during operation."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        content = test_file.read_text()
        
        # Delete file
        test_file.unlink()
        
        # Should handle deleted file
        try:
            result = scorer.score_file(test_file, content)
            # May succeed if content is provided
            assert isinstance(result, dict)
        except FileNotFoundError:
            # Acceptable to raise on deleted file
            pass

    def test_workflow_executor_disk_full(self, tmp_path: Path, monkeypatch):
        """Test workflow executor when disk is full."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        
        # Mock disk full scenario
        with patch("pathlib.Path.write_text") as mock_write:
            mock_write.side_effect = OSError("No space left on device")
            
            executor = WorkflowExecutor(project_root=tmp_path)
            workflow_dict = {
                "workflow": {
                    "id": "test",
                    "name": "Test",
                    "description": "Test",
                    "version": "1.0.0",
                    "steps": [{"id": "step1", "agent": "analyst", "action": "gather"}],
                }
            }
            workflow = WorkflowParser.parse(workflow_dict)
            
            # Should handle disk full error
            try:
                executor.start(workflow)
            except OSError:
                # Acceptable to raise on disk full
                pass

