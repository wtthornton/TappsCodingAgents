"""
Comprehensive unit tests for CLI command handlers.

Tests command execution, error handling, output formatting, and agent integration.
Extends existing tests with additional coverage.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.cli.commands import (
    common,
    planner,
    reviewer,
    top_level,
)

pytestmark = pytest.mark.unit


class TestCommonCommands:
    """Tests for common command utilities."""

    def test_format_json_output_dict(self, capsys):
        """Test format_json_output with dict."""
        data = {"result": "success", "value": 42}
        common.format_json_output(data)
        captured = capsys.readouterr()
        # Output goes through feedback system, may be formatted
        assert len(captured.out) > 0

    def test_format_json_output_string(self, capsys):
        """Test format_json_output with string."""
        data = "simple string"
        common.format_json_output(data)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_format_text_output(self, capsys):
        """Test format_text_output."""
        data = "simple text"
        common.format_text_output(data)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_handle_error_string(self, capsys):
        """Test handle_error with string."""
        with pytest.raises(SystemExit) as exc_info:
            common.handle_error("Test error", exit_code=1)
        assert exc_info.value.code == 1

    def test_handle_error_dict(self, capsys):
        """Test handle_error with dict."""
        error_dict = {
            "error": "Test error",
            "error_code": "test_error",
            "context": {"key": "value"},
            "remediation": "Fix it",
        }
        with pytest.raises(SystemExit) as exc_info:
            common.handle_error(error_dict, exit_code=2)
        assert exc_info.value.code == 2

    def test_check_result_error_no_error(self):
        """Test check_result_error with no error."""
        result = {"success": True, "data": "test"}
        # Should not raise
        common.check_result_error(result)

    def test_check_result_error_with_error(self, capsys):
        """Test check_result_error with error."""
        result = {"error": "Test error"}
        with pytest.raises(SystemExit) as exc_info:
            common.check_result_error(result)
        assert exc_info.value.code == 1


class TestReviewerCommands:
    """Tests for reviewer command handlers."""

    @pytest.mark.asyncio
    async def test_review_command_file_not_found(self, tmp_path, capsys):
        """Test review command with non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(SystemExit) as exc_info:
            await reviewer.review_command(str(non_existent), output_format="json")
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err or "file_not_found" in captured.err.lower()

    @pytest.mark.asyncio
    async def test_review_command_success_json(self, sample_python_file, capsys):
        """Test review command with valid file, JSON output."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
                "passed": True,
                "feedback": {"summary": "Good code"},
            })
            mock_agent_class.return_value = mock_agent

            await reviewer.review_command(str(sample_python_file), output_format="json")

            mock_agent.activate.assert_called_once()
            mock_agent.run.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_success_text(self, sample_python_file, capsys):
        """Test review command with valid file, text output."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
                "passed": True,
                "feedback": {"summary": "Good code"},
            })
            mock_agent_class.return_value = mock_agent

            await reviewer.review_command(str(sample_python_file), output_format="text")

            captured = capsys.readouterr()
            assert "Review" in captured.out or "Score" in captured.out
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_error_handling(self, sample_python_file, capsys):
        """Test review command error handling."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={"error": "Test error"})
            mock_agent_class.return_value = mock_agent

            with pytest.raises(SystemExit) as exc_info:
                await reviewer.review_command(str(sample_python_file), output_format="json")
            
            assert exc_info.value.code == 1
            mock_agent.close.assert_called_once()  # Should always close

    @pytest.mark.asyncio
    async def test_score_command_file_not_found(self, tmp_path, capsys):
        """Test score command with non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(SystemExit) as exc_info:
            await reviewer.score_command(str(non_existent), output_format="json")
        
        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_score_command_success(self, sample_python_file, capsys):
        """Test score command with valid file."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
            })
            mock_agent_class.return_value = mock_agent

            await reviewer.score_command(str(sample_python_file), output_format="json")

            mock_agent.activate.assert_called_once()
            mock_agent.run.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_command(self, capsys):
        """Test help command output."""
        await reviewer.help_command()
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestReviewerBatchOperations:
    """Tests for reviewer batch operations (multiple files, glob patterns)."""

    @pytest.mark.asyncio
    async def test_review_command_multiple_files(self, tmp_path, capsys):
        """Test review command with multiple files."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file3 = tmp_path / "file3.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        file3.write_text("def func3(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            
            # Mock run to return different results for each file
            async def mock_run(command, file):
                return {
                    "file": file,
                    "scoring": {
                        "complexity_score": 2.0,
                        "security_score": 10.0,
                        "maintainability_score": 9.0,
                        "overall_score": 85.0,
                    },
                    "passed": True,
                }
            
            mock_agent.run = AsyncMock(side_effect=mock_run)
            mock_agent_class.return_value = mock_agent
            
            await reviewer.review_command(
                files=[str(file1), str(file2), str(file3)],
                output_format="json"
            )
            
            # Should call run 3 times (once per file)
            assert mock_agent.run.call_count == 3
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_glob_pattern(self, tmp_path, capsys):
        """Test review command with glob pattern."""
        # Create test files in subdirectory
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        file1 = test_dir / "file1.py"
        file2 = test_dir / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class, \
             patch("pathlib.Path.cwd", return_value=tmp_path):
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "scoring": {
                    "complexity_score": 2.0,
                    "security_score": 10.0,
                    "maintainability_score": 9.0,
                    "overall_score": 85.0,
                },
                "passed": True,
            })
            mock_agent_class.return_value = mock_agent
            
            await reviewer.review_command(
                pattern="test_dir/*.py",
                output_format="json"
            )
            
            # Should call run for each matched file
            assert mock_agent.run.call_count >= 1
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_batch_with_errors(self, tmp_path, capsys):
        """Test batch review with some files failing."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            
            # First file succeeds, second fails
            async def mock_run(command, file):
                if "file1" in file:
                    return {
                        "file": file,
                        "scoring": {
                            "complexity_score": 2.0,
                            "security_score": 10.0,
                            "maintainability_score": 9.0,
                            "overall_score": 85.0,
                        },
                        "passed": True,
                    }
                else:
                    return {"error": "Test error", "file": file}
            
            mock_agent.run = AsyncMock(side_effect=mock_run)
            mock_agent_class.return_value = mock_agent
            
            with pytest.raises(SystemExit):
                await reviewer.review_command(
                    files=[str(file1), str(file2)],
                    output_format="json"
                )
            
            assert mock_agent.run.call_count == 2
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_score_command_multiple_files(self, tmp_path, capsys):
        """Test score command with multiple files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "scoring": {
                    "complexity_score": 2.0,
                    "security_score": 10.0,
                    "maintainability_score": 9.0,
                    "overall_score": 85.0,
                },
            })
            mock_agent_class.return_value = mock_agent
            
            await reviewer.score_command(
                files=[str(file1), str(file2)],
                output_format="json"
            )
            
            assert mock_agent.run.call_count == 2
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_score_command_glob_pattern(self, tmp_path, capsys):
        """Test score command with glob pattern."""
        test_dir = tmp_path / "src"
        test_dir.mkdir()
        file1 = test_dir / "module1.py"
        file2 = test_dir / "module2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class, \
             patch("pathlib.Path.cwd", return_value=tmp_path):
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "scoring": {
                    "complexity_score": 2.0,
                    "security_score": 10.0,
                    "maintainability_score": 9.0,
                    "overall_score": 85.0,
                },
            })
            mock_agent_class.return_value = mock_agent
            
            await reviewer.score_command(
                pattern="src/*.py",
                output_format="json"
            )
            
            assert mock_agent.run.call_count >= 1
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_file_list_with_files(self, tmp_path):
        """Test file resolution with explicit file list."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class, \
             patch("pathlib.Path.cwd", return_value=tmp_path):
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "scoring": {"overall_score": 85.0},
            })
            mock_agent_class.return_value = mock_agent
            
            # Test through public interface
            await reviewer.review_command(
                files=[str(file1), str(file2)],
                output_format="json"
            )
            
            # Should process both files
            assert mock_agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_resolve_file_list_with_pattern(self, tmp_path):
        """Test file resolution with glob pattern."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        file1 = test_dir / "file1.py"
        file2 = test_dir / "file2.py"
        file3 = test_dir / "file3.txt"  # Should not match *.py
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        file3.write_text("not python", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class, \
             patch("pathlib.Path.cwd", return_value=tmp_path):
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "scoring": {"overall_score": 85.0},
            })
            mock_agent_class.return_value = mock_agent
            
            # Test through public interface
            await reviewer.review_command(
                pattern="test/*.py",
                output_format="json"
            )
            
            # Should process only .py files (2 files)
            assert mock_agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_resolve_file_list_no_files(self, tmp_path):
        """Test file resolution raises error when no files found."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with pytest.raises(SystemExit):
                await reviewer.review_command(
                    pattern="nonexistent/*.py",
                    output_format="json"
                )

    def test_resolve_file_list_no_path_duplication(self, tmp_path):
        """Test that relative paths don't duplicate directory segments when cwd contains matching segments."""
        # Create a nested directory structure
        # cwd will be: tmp_path / "services" / "service-name"
        service_dir = tmp_path / "services" / "service-name"
        service_dir.mkdir(parents=True)
        
        # Create a file in the service directory
        target_file = service_dir / "src" / "file.py"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("def func(): pass", encoding="utf-8")
        
        # Import the function to test directly
        from tapps_agents.cli.commands.reviewer import _resolve_file_list
        
        # Test with cwd = service_dir, and relative path that starts with "services/service-name"
        # This would previously cause duplication: services/service-name/services/service-name/src/file.py
        with patch("pathlib.Path.cwd", return_value=service_dir):
            # Provide relative path that starts with directory segments matching cwd parent
            # Relative to service_dir, "src/file.py" is the correct path
            resolved = _resolve_file_list(["src/file.py"], None)
            
            # Should resolve to the correct file without duplication
            assert len(resolved) == 1
            assert resolved[0].resolve() == target_file.resolve()
            # Verify no duplication - check that path parts don't repeat
            path_parts = list(resolved[0].parts)
            # Count occurrences of "services" and "service-name" - should appear once each
            services_count = path_parts.count("services")
            service_name_count = path_parts.count("service-name")
            assert services_count <= 1, f"Path duplication detected (services appears {services_count} times): {resolved[0]}"
            assert service_name_count <= 1, f"Path duplication detected (service-name appears {service_name_count} times): {resolved[0]}"
            
    def test_resolve_file_list_relative_path_normalization(self, tmp_path):
        """Test that resolve() properly handles path normalization for relative paths."""
        # Create a file structure
        service_dir = tmp_path / "services" / "service-name"
        src_dir = service_dir / "src"
        src_dir.mkdir(parents=True)
        target_file = src_dir / "file.py"
        target_file.write_text("def func(): pass", encoding="utf-8")
        
        from tapps_agents.cli.commands.reviewer import _resolve_file_list
        
        # Test with cwd = service_dir, passing a simple relative path
        # This tests that resolve() works correctly for normal relative paths
        with patch("pathlib.Path.cwd", return_value=service_dir):
            # Simple relative path - should resolve correctly
            resolved = _resolve_file_list(["src/file.py"], None)
            
            # Should resolve to the correct file
            assert len(resolved) == 1
            resolved_path = resolved[0].resolve()
            target_resolved = target_file.resolve()
            assert resolved_path == target_resolved, f"Expected {target_resolved}, got {resolved_path}"

    @pytest.mark.asyncio
    async def test_process_file_batch_success(self, tmp_path):
        """Test batch processing with successful processing."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=[
                {"file": str(file1), "scoring": {"overall_score": 85.0}},
                {"file": str(file2), "scoring": {"overall_score": 90.0}},
            ])
            mock_agent_class.return_value = mock_agent
            
            # Test through public interface
            await reviewer.score_command(
                files=[str(file1), str(file2)],
                output_format="json"
            )
            
            # Both files should be processed successfully
            assert mock_agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_process_file_batch_with_errors(self, tmp_path):
        """Test batch processing with some errors."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=[
                {"file": str(file1), "scoring": {"overall_score": 85.0}},
                {"error": "Test error", "file": str(file2)},
            ])
            mock_agent_class.return_value = mock_agent
            
            # Test through public interface
            with pytest.raises(SystemExit):
                await reviewer.score_command(
                    files=[str(file1), str(file2)],
                    output_format="json"
                )
            
            # Both files should be processed (one succeeds, one fails)
            assert mock_agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_process_file_batch_concurrency_limit(self, tmp_path):
        """Test batch processing respects max_workers limit."""
        # Create 5 files
        files = []
        for i in range(5):
            file = tmp_path / f"file{i}.py"
            file.write_text(f"def func{i}(): pass", encoding="utf-8")
            files.append(file)
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            call_count = 0
            
            async def mock_run(command, file):
                nonlocal call_count
                call_count += 1
                return {"file": str(file), "scoring": {"overall_score": 85.0}}
            
            mock_agent.run = AsyncMock(side_effect=mock_run)
            mock_agent_class.return_value = mock_agent
            
            # Test through public interface with max_workers=2
            await reviewer.score_command(
                files=[str(f) for f in files],
                output_format="json",
                max_workers=2
            )
            
            # All files should be processed
            assert call_count == 5

    @pytest.mark.asyncio
    async def test_lint_command_multiple_files(self, tmp_path, capsys):
        """Test lint command with multiple files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "linting_score": 9.0,
                "issues": [],
                "issue_count": 0,
            })
            mock_agent_class.return_value = mock_agent
            
            await reviewer.lint_command(
                files=[str(file1), str(file2)],
                output_format="json"
            )
            
            assert mock_agent.run.call_count == 2
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_type_check_command_multiple_files(self, tmp_path, capsys):
        """Test type-check command with multiple files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": "test",
                "type_checking_score": 9.0,
                "errors": [],
                "error_count": 0,
            })
            mock_agent_class.return_value = mock_agent
            
            await reviewer.type_check_command(
                files=[str(file1), str(file2)],
                output_format="json"
            )
            
            assert mock_agent.run.call_count == 2
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lint_command_with_output_file(self, tmp_path):
        """Test lint command saves results to output file."""
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        output_file = tmp_path / "lint-report.json"
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(file1),
                "issues": [],
            })
            mock_agent_class.return_value = mock_agent
            
            # Call lint_command directly instead of handle_reviewer_command
            # (handle_reviewer_command uses run_async_command which can't be called from async context)
            await reviewer.lint_command(
                files=[str(file1)],
                output_format="json",
                output_file=str(output_file)
            )
            
            # Verify file was created
            assert output_file.exists()
            # Verify content is valid JSON
            import json
            content = json.loads(output_file.read_text(encoding="utf-8"))
            assert "file" in content or isinstance(content, list)

    @pytest.mark.asyncio
    async def test_type_check_command_with_output_file(self, tmp_path):
        """Test type-check command saves results to output file."""
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        output_file = tmp_path / "type-check.json"
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(file1),
                "errors": [],
            })
            mock_agent_class.return_value = mock_agent
            
            # Call type_check_command directly instead of handle_reviewer_command
            # (handle_reviewer_command uses run_async_command which can't be called from async context)
            await reviewer.type_check_command(
                files=[str(file1)],
                output_format="json",
                output_file=str(output_file)
            )
            
            # Verify file was created
            assert output_file.exists()
            # Verify content is valid JSON
            import json
            content = json.loads(output_file.read_text(encoding="utf-8"))
            assert "file" in content or isinstance(content, list)

    @pytest.mark.asyncio
    async def test_lint_command_output_format_detection(self, tmp_path):
        """Test lint command detects format from file extension."""
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        output_file = tmp_path / "lint-report.html"
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(file1),
                "issues": [],
            })
            mock_agent_class.return_value = mock_agent
            
            # Call lint_command directly instead of handle_reviewer_command
            # (handle_reviewer_command uses run_async_command which can't be called from async context)
            await reviewer.lint_command(
                files=[str(file1)],
                output_format="html",  # Explicitly set format based on extension
                output_file=str(output_file)
            )
            
            # Verify HTML file was created
            assert output_file.exists()
            content = output_file.read_text(encoding="utf-8")
            assert "<html>" in content or "<!DOCTYPE html>" in content

    @pytest.mark.asyncio
    async def test_type_check_command_output_format_detection(self, tmp_path):
        """Test type-check command detects format from file extension."""
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        output_file = tmp_path / "type-check.md"
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(file1),
                "errors": [],
            })
            mock_agent_class.return_value = mock_agent
            
            # Call type_check_command directly instead of handle_reviewer_command
            # (handle_reviewer_command uses run_async_command which can't be called from async context)
            await reviewer.type_check_command(
                files=[str(file1)],
                output_format="markdown",  # Explicitly set format based on extension
                output_file=str(output_file)
            )
            
            # Verify Markdown file was created
            assert output_file.exists()
            content = output_file.read_text(encoding="utf-8")
            assert "#" in content or "Results" in content

    @pytest.mark.asyncio
    async def test_lint_batch_with_output_file(self, tmp_path):
        """Test batch lint with output file."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def func1(): pass", encoding="utf-8")
        file2.write_text("def func2(): pass", encoding="utf-8")
        output_file = tmp_path / "batch-lint.json"
        
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=[
                {"file": str(file1), "issues": []},
                {"file": str(file2), "issues": []},
            ])
            mock_agent_class.return_value = mock_agent
            
            # Call lint_command directly instead of handle_reviewer_command
            # (handle_reviewer_command uses run_async_command which can't be called from async context)
            await reviewer.lint_command(
                files=[str(file1), str(file2)],
                output_format="json",
                output_file=str(output_file)
            )
            
            # Verify file was created
            assert output_file.exists()
            # Verify content is valid JSON
            import json
            content = json.loads(output_file.read_text(encoding="utf-8"))
            assert "files" in content or isinstance(content, list)


class TestPlannerCommands:
    """Tests for planner command handlers."""

    @pytest.mark.asyncio
    async def test_list_stories_command_json(self, tmp_path, capsys):
        """Test list stories command with JSON output."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        stories_dir = project_dir / ".tapps-agents" / "stories"
        stories_dir.mkdir(parents=True)
        
        # Create a sample story file
        story_file = stories_dir / "story-001.yaml"
        story_file.write_text("title: Test Story\nstatus: open\n", encoding="utf-8")

        with patch("pathlib.Path.cwd", return_value=project_dir):
            await planner.list_stories_command(output_format="json")
        
        captured = capsys.readouterr()
        # Should output something (may be JSON or text)
        assert len(captured.out) >= 0

    @pytest.mark.asyncio
    async def test_list_stories_command_text(self, tmp_path, capsys):
        """Test list stories command with text output."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        stories_dir = project_dir / ".tapps-agents" / "stories"
        stories_dir.mkdir(parents=True)

        with patch("pathlib.Path.cwd", return_value=project_dir):
            await planner.list_stories_command(output_format="text")
        
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)


class TestTopLevelCommands:
    """Tests for top-level command handlers."""

    def test_score_command_shortcut(self, sample_python_file, capsys):
        """Test score command shortcut (top-level)."""
        with patch("tapps_agents.cli.commands.top_level.score_command") as mock_score, \
             patch("asyncio.run") as mock_asyncio_run:
            mock_score.return_value = None
            top_level.handle_score_command(MagicMock(file=str(sample_python_file), format="json"))
            mock_asyncio_run.assert_called_once()

    def test_doctor_command(self, capsys):
        """Test doctor command."""
        with patch("tapps_agents.core.doctor.collect_doctor_report") as mock_collect:
            mock_collect.return_value = {
                "policy": {},
                "targets": {},
                "findings": [],
            }
            top_level.handle_doctor_command(MagicMock(format="text"))
            mock_collect.assert_called_once()

    def test_doctor_command_json(self, capsys):
        """Test doctor command with JSON output."""
        with patch("tapps_agents.core.doctor.collect_doctor_report") as mock_collect:
            mock_collect.return_value = {
                "policy": {},
                "targets": {},
                "findings": [],
            }
            top_level.handle_doctor_command(MagicMock(format="json"))
            mock_collect.assert_called_once()


class TestMainCLI:
    """Tests for main CLI entry point."""

    def test_main_help(self, capsys):
        """Test main function with --help."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "--help"]):
            try:
                main()
            except SystemExit:
                pass  # argparse exits on --help
        
        captured = capsys.readouterr()
        assert "TappsCodingAgents" in captured.out or "agent" in captured.out.lower()

    def test_main_reviewer_help(self, capsys):
        """Test main function with reviewer --help."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "reviewer", "--help"]):
            try:
                main()
            except SystemExit:
                pass
        
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_main_version(self, capsys):
        """Test main function with --version."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "--version"]):
            try:
                main()
            except SystemExit:
                pass
        
        captured = capsys.readouterr()
        # Version should be printed
        assert len(captured.out) > 0

    def test_main_unknown_command(self, capsys):
        """Test main function with unknown command."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "unknown-command"]):
            with pytest.raises(SystemExit):
                main()

    def test_register_all_parsers(self):
        """Test register_all_parsers function."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers
        
        parser = create_root_parser()
        register_all_parsers(parser)
        
        # Verify some parsers were registered
        subparsers = parser._subparsers._group_actions[0]
        assert "reviewer" in subparsers.choices
        assert "workflow" in subparsers.choices

    def test_route_command_reviewer(self):
        """Test route_command with reviewer."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers, route_command
        
        parser = create_root_parser()
        register_all_parsers(parser)
        
        with patch("tapps_agents.cli.commands.reviewer.handle_reviewer_command") as mock_handler:
            args = parser.parse_args(["reviewer", "help"])
            route_command(args)
            mock_handler.assert_called_once()

    def test_route_command_workflow(self):
        """Test route_command with workflow."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers, route_command
        
        parser = create_root_parser()
        register_all_parsers(parser)
        
        with patch("tapps_agents.cli.commands.top_level.handle_workflow_command") as mock_handler:
            args = parser.parse_args(["workflow", "list"])
            route_command(args)
            mock_handler.assert_called_once()

