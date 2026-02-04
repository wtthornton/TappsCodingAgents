"""
Unit tests for command classification system.
"""

from tapps_agents.cli.command_classifier import (
    CommandClassifier,
    CommandNetworkRequirement,
)


def test_offline_commands():
    """Test that offline commands are correctly classified."""
    assert (
        CommandClassifier.get_network_requirement("reviewer", "help")
        == CommandNetworkRequirement.OFFLINE
    )
    assert (
        CommandClassifier.get_network_requirement("reviewer", "score")
        == CommandNetworkRequirement.OFFLINE
    )
    assert (
        CommandClassifier.get_network_requirement("reviewer", "lint")
        == CommandNetworkRequirement.OFFLINE
    )
    assert (
        CommandClassifier.get_network_requirement("reviewer", "type-check")
        == CommandNetworkRequirement.OFFLINE
    )
    assert (
        CommandClassifier.get_network_requirement("simple-mode", "status")
        == CommandNetworkRequirement.OFFLINE
    )
    assert (
        CommandClassifier.get_network_requirement("doctor", None)
        == CommandNetworkRequirement.OFFLINE
    )


def test_network_optional_commands():
    """Test that network-optional commands are correctly classified."""
    assert (
        CommandClassifier.get_network_requirement("reviewer", "review")
        == CommandNetworkRequirement.OPTIONAL
    )
    assert (
        CommandClassifier.get_network_requirement("reviewer", "docs")
        == CommandNetworkRequirement.OPTIONAL
    )


def test_network_required_commands():
    """Test that network-required commands are correctly classified."""
    assert (
        CommandClassifier.get_network_requirement("implementer", "implement")
        == CommandNetworkRequirement.REQUIRED
    )
    assert (
        CommandClassifier.get_network_requirement("planner", "plan")
        == CommandNetworkRequirement.REQUIRED
    )
    assert (
        CommandClassifier.get_network_requirement("architect", "design")
        == CommandNetworkRequirement.REQUIRED
    )
    assert (
        CommandClassifier.get_network_requirement("designer", "design-api")
        == CommandNetworkRequirement.REQUIRED
    )
    assert (
        CommandClassifier.get_network_requirement("enhancer", "enhance")
        == CommandNetworkRequirement.REQUIRED
    )
    assert (
        CommandClassifier.get_network_requirement("tester", "test")
        == CommandNetworkRequirement.REQUIRED
    )


def test_case_insensitive():
    """Test that command classification is case-insensitive."""
    assert (
        CommandClassifier.get_network_requirement("REVIEWER", "HELP")
        == CommandNetworkRequirement.OFFLINE
    )
    assert (
        CommandClassifier.get_network_requirement("Reviewer", "Score")
        == CommandNetworkRequirement.OFFLINE
    )


def test_default_network_required():
    """Test that unknown commands default to network required (fail-safe)."""
    assert (
        CommandClassifier.get_network_requirement("unknown-agent", "unknown-command")
        == CommandNetworkRequirement.REQUIRED
    )

