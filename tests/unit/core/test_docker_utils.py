"""
Unit tests for Docker utility functions.

Tests the safe Docker command execution utilities that avoid
PowerShell table format parsing issues.
"""

import json
from unittest.mock import MagicMock, patch

from tapps_agents.core.docker_utils import (
    get_container_status,
    run_docker_ps_json,
    run_docker_ps_native,
    run_docker_ps_simple,
)


class TestRunDockerPsJson:
    """Tests for run_docker_ps_json function."""

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_success(self, mock_subprocess):
        """Test successful JSON format parsing."""
        # Mock Docker output with JSON format (one JSON object per line)
        mock_output = json.dumps({"Names": "container1", "Status": "Up 2 hours", "ID": "abc123"}) + "\n"
        mock_output += json.dumps({"Names": "container2", "Status": "Up 1 day", "ID": "def456"}) + "\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_json()
        
        assert len(containers) == 2
        assert containers[0]["Names"] == "container1"
        assert containers[0]["Status"] == "Up 2 hours"
        assert containers[1]["Names"] == "container2"
        assert containers[1]["Status"] == "Up 1 day"
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == ["docker", "ps", "--format", "json"]

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_with_limit(self, mock_subprocess):
        """Test JSON format with limit parameter."""
        # Create 5 containers
        mock_output = "\n".join([
            json.dumps({"Names": f"container{i}", "Status": "Up", "ID": f"id{i}"})
            for i in range(5)
        ]) + "\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_json(limit=3)
        
        assert len(containers) == 3
        assert containers[0]["Names"] == "container0"
        assert containers[2]["Names"] == "container2"

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_empty_output(self, mock_subprocess):
        """Test handling of empty Docker output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_json()
        
        assert containers == []

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_docker_error(self, mock_subprocess):
        """Test handling of Docker command errors."""
        mock_result = MagicMock()
        mock_result.returncode = 1  # Docker error
        mock_result.stdout = "Error: Cannot connect to Docker daemon"
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_json()
        
        assert containers == []

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_invalid_json(self, mock_subprocess):
        """Test handling of invalid JSON lines."""
        mock_output = json.dumps({"Names": "container1", "Status": "Up"}) + "\n"
        mock_output += "invalid json line\n"  # Invalid JSON
        mock_output += json.dumps({"Names": "container2", "Status": "Up"}) + "\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_json()
        
        # Should skip invalid JSON and return valid ones
        assert len(containers) == 2
        assert containers[0]["Names"] == "container1"
        assert containers[1]["Names"] == "container2"

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_docker_not_installed(self, mock_subprocess):
        """Test handling when Docker is not installed."""
        mock_subprocess.side_effect = FileNotFoundError("docker: command not found")
        
        containers = run_docker_ps_json()
        
        assert containers == []

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_json_timeout(self, mock_subprocess):
        """Test handling of command timeout."""
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired(["docker", "ps"], 30)
        
        containers = run_docker_ps_json()
        
        assert containers == []


class TestRunDockerPsSimple:
    """Tests for run_docker_ps_simple function."""

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_simple_success(self, mock_subprocess):
        """Test successful simple format parsing."""
        # Simple format: Names\tStatus (no table header)
        mock_output = "container1\tUp 2 hours\n"
        mock_output += "container2\tUp 1 day\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_simple()
        
        assert len(containers) == 2
        assert containers[0]["Names"] == "container1"
        assert containers[0]["Status"] == "Up 2 hours"
        assert containers[1]["Names"] == "container2"
        assert containers[1]["Status"] == "Up 1 day"
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"]

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_simple_with_limit(self, mock_subprocess):
        """Test simple format with limit parameter."""
        mock_output = "\n".join([
            f"container{i}\tUp {i} hours"
            for i in range(5)
        ]) + "\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_simple(limit=3)
        
        assert len(containers) == 3
        assert containers[0]["Names"] == "container0"
        assert containers[2]["Names"] == "container2"

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_simple_empty_output(self, mock_subprocess):
        """Test handling of empty output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_simple()
        
        assert containers == []

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_simple_malformed_line(self, mock_subprocess):
        """Test handling of lines without tabs."""
        mock_output = "container1\tUp 2 hours\n"
        mock_output += "container2_no_tab\n"  # Missing tab
        mock_output += "container3\tUp 1 day\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        containers = run_docker_ps_simple()
        
        # Should only return properly formatted lines
        assert len(containers) == 2
        assert containers[0]["Names"] == "container1"
        assert containers[1]["Names"] == "container3"


class TestRunDockerPsNative:
    """Tests for run_docker_ps_native function."""

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_native_success(self, mock_subprocess):
        """Test successful native output."""
        mock_output = "CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS   NAMES\n"
        mock_output += "abc123         image1    cmd1      2h ago    Up 2h     80/tcp  container1\n"
        mock_output += "def456         image2    cmd2      1d ago    Up 1d     443/tcp container2\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        output = run_docker_ps_native()
        
        assert "container1" in output
        assert "container2" in output
        assert "CONTAINER ID" in output
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == ["docker", "ps"]

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_native_with_limit(self, mock_subprocess):
        """Test native output with line limit."""
        mock_output = "HEADER\n"
        mock_output += "\n".join([f"line{i}" for i in range(10)]) + "\n"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        output = run_docker_ps_native(limit=3)
        
        lines = output.split("\n")
        assert len(lines) == 3  # HEADER + 2 data lines

    @patch("tapps_agents.core.docker_utils.subprocess.run")
    def test_run_docker_ps_native_empty_output(self, mock_subprocess):
        """Test handling of empty output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        output = run_docker_ps_native()
        
        assert output == ""


class TestGetContainerStatus:
    """Tests for get_container_status function."""

    @patch("tapps_agents.core.docker_utils.run_docker_ps_json")
    def test_get_container_status_all(self, mock_run_docker_ps_json):
        """Test getting status of all containers."""
        mock_containers = [
            {"Names": "/container1", "Status": "Up 2 hours", "State": "running"},
            {"Names": "/container2", "Status": "Exited", "State": "exited"},
        ]
        mock_run_docker_ps_json.return_value = mock_containers
        
        result = get_container_status()
        
        assert result["total"] == 2
        assert len(result["containers"]) == 2
        assert result["containers"] == mock_containers

    @patch("tapps_agents.core.docker_utils.run_docker_ps_json")
    def test_get_container_status_found(self, mock_run_docker_ps_json):
        """Test finding a specific container."""
        mock_containers = [
            {"Names": "/my-container", "Status": "Up 2 hours", "State": "running"},
            {"Names": "/other-container", "Status": "Exited", "State": "exited"},
        ]
        mock_run_docker_ps_json.return_value = mock_containers
        
        result = get_container_status("my-container")
        
        assert result["found"] is True
        assert result["running"] is True
        assert result["container"]["Names"] == "/my-container"

    @patch("tapps_agents.core.docker_utils.run_docker_ps_json")
    def test_get_container_status_not_found(self, mock_run_docker_ps_json):
        """Test when container is not found."""
        mock_containers = [
            {"Names": "/other-container", "Status": "Up", "State": "running"},
        ]
        mock_run_docker_ps_json.return_value = mock_containers
        
        result = get_container_status("my-container")
        
        assert result["found"] is False
        assert result["running"] is False
        assert result["container"] is None

    @patch("tapps_agents.core.docker_utils.run_docker_ps_json")
    def test_get_container_status_without_leading_slash(self, mock_run_docker_ps_json):
        """Test finding container with or without leading slash."""
        mock_containers = [
            {"Names": "/my-container", "Status": "Up", "State": "running"},
        ]
        mock_run_docker_ps_json.return_value = mock_containers
        
        # Should find container even if name doesn't have leading slash
        result = get_container_status("my-container")
        
        assert result["found"] is True
        assert result["running"] is True

    @patch("tapps_agents.core.docker_utils.run_docker_ps_json")
    def test_get_container_status_exited(self, mock_run_docker_ps_json):
        """Test container that has exited."""
        mock_containers = [
            {"Names": "/my-container", "Status": "Exited (0) 2 hours ago", "State": "exited"},
        ]
        mock_run_docker_ps_json.return_value = mock_containers
        
        result = get_container_status("my-container")
        
        assert result["found"] is True
        assert result["running"] is False
        assert result["container"]["State"] == "exited"

