"""
Integration tests for offline command execution.
"""
import os
from unittest.mock import patch

import pytest

from tapps_agents.cli.command_classifier import CommandNetworkRequirement
from tapps_agents.cli.network_detection import NetworkDetector


@pytest.fixture
def mock_offline_network():
    """Mock network to be unavailable."""
    with patch.object(NetworkDetector, "is_network_available", return_value=False):
        yield


@pytest.fixture
def offline_env():
    """Set offline environment variable."""
    old_value = os.getenv("TAPPS_AGENTS_OFFLINE", "0")
    os.environ["TAPPS_AGENTS_OFFLINE"] = "1"
    yield
    os.environ["TAPPS_AGENTS_OFFLINE"] = old_value


def test_offline_commands_classified_correctly():
    """Test that offline commands are correctly identified."""
    from tapps_agents.cli.command_classifier import CommandClassifier
    
    offline_commands = [
        ("reviewer", "help"),
        ("reviewer", "score"),
        ("reviewer", "lint"),
        ("reviewer", "type-check"),
        ("simple-mode", "status"),
        ("doctor", None),
    ]
    
    for agent, command in offline_commands:
        requirement = CommandClassifier.get_network_requirement(agent, command)
        assert (
            requirement == CommandNetworkRequirement.OFFLINE
        ), f"{agent} {command} should be offline"


def test_offline_mode_environment_variable():
    """Test that offline mode is enabled via environment variable."""
    from tapps_agents.cli.commands.common import should_use_offline_mode
    
    with patch.dict(os.environ, {"TAPPS_AGENTS_OFFLINE": "1"}):
        assert should_use_offline_mode(CommandNetworkRequirement.OFFLINE) is True
        assert should_use_offline_mode(CommandNetworkRequirement.OPTIONAL) is True
        assert should_use_offline_mode(CommandNetworkRequirement.REQUIRED) is True


def test_optional_command_falls_back_to_offline(mock_offline_network):
    """Test that optional commands use offline mode when network unavailable."""
    from tapps_agents.cli.commands.common import should_use_offline_mode
    
    assert should_use_offline_mode(CommandNetworkRequirement.OPTIONAL) is True


def test_optional_command_uses_network_when_available():
    """Test that optional commands use network when available."""
    from tapps_agents.cli.commands.common import should_use_offline_mode
    
    with patch.object(NetworkDetector, "is_network_available", return_value=True):
        assert should_use_offline_mode(CommandNetworkRequirement.OPTIONAL) is False


def test_offline_commands_never_require_network():
    """Test that offline commands always use offline mode."""
    from tapps_agents.cli.commands.common import should_use_offline_mode
    
    # Even if network is available, offline commands should use offline mode
    with patch.object(NetworkDetector, "is_network_available", return_value=True):
        assert should_use_offline_mode(CommandNetworkRequirement.OFFLINE) is True

