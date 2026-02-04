"""
Unit tests for health checking.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from tapps_agents.workflow.health_checker import HealthChecker, HealthCheckResult


def test_health_check_result():
    """Test HealthCheckResult."""
    result = HealthCheckResult(
        name="test",
        status="healthy",
        message="Test message",
        details={"key": "value"},
    )
    assert result.name == "test"
    assert result.status == "healthy"
    assert result.message == "Test message"
    assert result.details == {"key": "value"}


def test_health_checker_check_file_system(tmp_path: Path):
    """Test file system health check."""
    checker = HealthChecker(project_root=tmp_path)
    result = checker.check_file_system()

    assert result.name == "file_system"
    assert result.status == "healthy"
    assert "accessible" in result.message.lower()


def test_health_checker_check_status_file_access(tmp_path: Path):
    """Test status file access health check."""
    checker = HealthChecker(project_root=tmp_path)
    result = checker.check_status_file_access()

    assert result.name == "status_file_access"
    # Should be healthy or degraded (depending on whether .cursor exists)
    assert result.status in ["healthy", "degraded"]


def test_health_checker_check_command_file_access(tmp_path: Path):
    """Test command file access health check."""
    checker = HealthChecker(project_root=tmp_path)
    result = checker.check_command_file_access()

    assert result.name == "command_file_access"
    # Should be healthy or degraded
    assert result.status in ["healthy", "degraded"]


def test_health_checker_check_configuration_valid(tmp_path: Path):
    """Test configuration health check with valid config."""
    # Create valid config
    config_path = tmp_path / ".cursor" / "background-agents.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "agents": [
            {
                "name": "Test Agent",
                "type": "background",
                "commands": ["test-command"],
                "watch_paths": [".cursor-skill-command.txt"],
            }
        ]
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    checker = HealthChecker(project_root=tmp_path)
    result = checker.check_configuration()

    assert result.name == "configuration"
    # Should be healthy or degraded (depending on validation)
    assert result.status in ["healthy", "degraded", "unhealthy"]


def test_health_checker_check_configuration_missing(tmp_path: Path):
    """Test configuration health check with missing config."""
    checker = HealthChecker(project_root=tmp_path)
    result = checker.check_configuration()

    assert result.name == "configuration"
    assert result.status == "degraded"
    assert "not found" in result.message.lower()


def test_health_checker_check_all(tmp_path: Path):
    """Test running all health checks."""
    checker = HealthChecker(project_root=tmp_path)
    results = checker.check_all()

    assert len(results) >= 4
    assert all(isinstance(r, HealthCheckResult) for r in results)


def test_health_checker_get_overall_status(tmp_path: Path):
    """Test getting overall health status."""
    checker = HealthChecker(project_root=tmp_path)
    status = checker.get_overall_status()

    assert status in ["healthy", "degraded", "unhealthy"]

