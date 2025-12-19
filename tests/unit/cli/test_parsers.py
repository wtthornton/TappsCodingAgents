"""
Comprehensive unit tests for CLI parsers.

Tests all parser modules to ensure they:
- Register correctly
- Parse arguments correctly
- Handle edge cases
- Support aliases
"""

import argparse
from unittest.mock import patch

import pytest

from tapps_agents.cli.parsers import (
    analyst,
    architect,
    debugger,
    designer,
    documenter,
    enhancer,
    implementer,
    improver,
    ops,
    orchestrator,
    planner,
    reviewer,
    tester,
    top_level,
)

pytestmark = pytest.mark.unit


class TestParserRegistration:
    """Tests for parser registration."""

    def test_all_parsers_register(self):
        """Test that all parsers can be registered without errors."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")

        # Should not raise any errors
        reviewer.add_reviewer_parser(subparsers)
        planner.add_planner_parser(subparsers)
        implementer.add_implementer_parser(subparsers)
        tester.add_tester_parser(subparsers)
        debugger.add_debugger_parser(subparsers)
        documenter.add_documenter_parser(subparsers)
        orchestrator.add_orchestrator_parser(subparsers)
        analyst.add_analyst_parser(subparsers)
        architect.add_architect_parser(subparsers)
        designer.add_designer_parser(subparsers)
        improver.add_improver_parser(subparsers)
        ops.add_ops_parser(subparsers)
        enhancer.add_enhancer_parser(subparsers)
        top_level.add_top_level_parsers(subparsers)

        # Verify parsers were added
        assert "reviewer" in subparsers.choices
        assert "planner" in subparsers.choices
        assert "implementer" in subparsers.choices
        assert "tester" in subparsers.choices
        assert "workflow" in subparsers.choices
        assert "init" in subparsers.choices


class TestReviewerParser:
    """Tests for reviewer parser."""

    def test_reviewer_parser_registration(self):
        """Test reviewer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        args = parser.parse_args(["reviewer", "review", "test.py"])
        assert args.agent == "reviewer"
        assert args.command == "review"
        assert args.file == "test.py"

    def test_reviewer_parser_aliases(self):
        """Test reviewer parser supports star aliases."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        # Test star alias
        args = parser.parse_args(["reviewer", "*review", "test.py"])
        assert args.command == "review"

        args = parser.parse_args(["reviewer", "*score", "test.py"])
        assert args.command == "score"

    def test_reviewer_parser_format_options(self):
        """Test reviewer parser format options."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        args = parser.parse_args(["reviewer", "review", "test.py", "--format", "text"])
        assert args.format == "text"

        args = parser.parse_args(["reviewer", "review", "test.py", "--format", "json"])
        assert args.format == "json"

    def test_reviewer_parser_all_commands(self):
        """Test all reviewer commands are registered."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        reviewer_parser = subparsers.choices["reviewer"]
        reviewer_subparsers = reviewer_parser._subparsers._group_actions[0]

        expected_commands = ["review", "score", "lint", "type-check", "report", "duplication", "analyze-project", "analyze-services", "help"]
        for cmd in expected_commands:
            assert cmd in reviewer_subparsers.choices or f"*{cmd}" in reviewer_subparsers.choices


class TestTopLevelParser:
    """Tests for top-level parser."""

    def test_workflow_parser_registration(self):
        """Test workflow parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        args = parser.parse_args(["workflow", "rapid", "--prompt", "test"])
        assert args.agent == "workflow"
        assert args.preset == "rapid"
        assert args.prompt == "test"

    def test_workflow_parser_aliases(self):
        """Test workflow parser aliases."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        # Test aliases
        args = parser.parse_args(["workflow", "enterprise", "--prompt", "test"])
        assert args.preset == "enterprise"

        args = parser.parse_args(["workflow", "feature", "--prompt", "test"])
        assert args.preset == "feature"

        args = parser.parse_args(["workflow", "refactor", "--file", "test.py"])
        assert args.preset == "refactor"

    def test_workflow_parser_auto_flag(self):
        """Test workflow parser --auto flag."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        args = parser.parse_args(["workflow", "rapid", "--prompt", "test", "--auto"])
        assert args.auto is True

        args = parser.parse_args(["workflow", "rapid", "--prompt", "test"])
        assert args.auto is False

    def test_workflow_state_commands(self):
        """Test workflow state management commands."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        args = parser.parse_args(["workflow", "state", "list"])
        assert args.agent == "workflow"
        assert args.preset == "state"
        assert args.state_command == "list"

        args = parser.parse_args(["workflow", "state", "show", "workflow-123"])
        assert args.state_command == "show"
        assert args.workflow_id == "workflow-123"

    def test_init_parser(self):
        """Test init parser."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        args = parser.parse_args(["init"])
        assert args.agent == "init"

    def test_score_parser(self):
        """Test score parser."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        args = parser.parse_args(["score", "test.py"])
        assert args.agent == "score"
        assert args.file == "test.py"

    def test_doctor_parser(self):
        """Test doctor parser."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        top_level.add_top_level_parsers(subparsers)

        args = parser.parse_args(["doctor"])
        assert args.agent == "doctor"

        args = parser.parse_args(["doctor", "--format", "json"])
        assert args.format == "json"


class TestPlannerParser:
    """Tests for planner parser."""

    def test_planner_parser_registration(self):
        """Test planner parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        planner.add_planner_parser(subparsers)

        args = parser.parse_args(["planner", "create-story", "--title", "Test"])
        assert args.agent == "planner"
        assert args.command == "create-story"
        assert args.title == "Test"


class TestImplementerParser:
    """Tests for implementer parser."""

    def test_implementer_parser_registration(self):
        """Test implementer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        implementer.add_implementer_parser(subparsers)

        args = parser.parse_args(["implementer", "implement", "--description", "test"])
        assert args.agent == "implementer"
        assert args.command == "implement"
        assert args.description == "test"


class TestTesterParser:
    """Tests for tester parser."""

    def test_tester_parser_registration(self):
        """Test tester parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        tester.add_tester_parser(subparsers)

        args = parser.parse_args(["tester", "test", "test.py"])
        assert args.agent == "tester"
        assert args.command == "test"
        assert args.file == "test.py"


class TestOtherAgentParsers:
    """Tests for other agent parsers."""

    def test_debugger_parser_registration(self):
        """Test debugger parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        debugger.add_debugger_parser(subparsers)

        args = parser.parse_args(["debugger", "analyze", "--error", "test"])
        assert args.agent == "debugger"

    def test_analyst_parser_registration(self):
        """Test analyst parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        analyst.add_analyst_parser(subparsers)

        args = parser.parse_args(["analyst", "analyze", "--requirements", "test"])
        assert args.agent == "analyst"

    def test_architect_parser_registration(self):
        """Test architect parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        architect.add_architect_parser(subparsers)

        args = parser.parse_args(["architect", "design", "--system", "test"])
        assert args.agent == "architect"

    def test_designer_parser_registration(self):
        """Test designer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        designer.add_designer_parser(subparsers)

        args = parser.parse_args(["designer", "design", "--api", "test"])
        assert args.agent == "designer"

    def test_documenter_parser_registration(self):
        """Test documenter parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        documenter.add_documenter_parser(subparsers)

        args = parser.parse_args(["documenter", "document", "--target", "test"])
        assert args.agent == "documenter"

    def test_enhancer_parser_registration(self):
        """Test enhancer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        enhancer.add_enhancer_parser(subparsers)

        args = parser.parse_args(["enhancer", "enhance", "--prompt", "test"])
        assert args.agent == "enhancer"

    def test_improver_parser_registration(self):
        """Test improver parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        improver.add_improver_parser(subparsers)

        args = parser.parse_args(["improver", "improve", "--file", "test.py"])
        assert args.agent == "improver"

    def test_ops_parser_registration(self):
        """Test ops parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        ops.add_ops_parser(subparsers)

        args = parser.parse_args(["ops", "scan", "--target", "test"])
        assert args.agent == "ops"

    def test_orchestrator_parser_registration(self):
        """Test orchestrator parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        orchestrator.add_orchestrator_parser(subparsers)

        args = parser.parse_args(["orchestrator", "run", "--workflow", "test"])
        assert args.agent == "orchestrator"


class TestParserErrorHandling:
    """Tests for parser error handling."""

    def test_invalid_command_raises_error(self):
        """Test that invalid commands raise SystemExit."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        with pytest.raises(SystemExit):
            parser.parse_args(["reviewer", "invalid-command"])

    def test_missing_required_argument_raises_error(self):
        """Test that missing required arguments raise SystemExit."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        with pytest.raises(SystemExit):
            parser.parse_args(["reviewer", "review"])

    def test_invalid_format_raises_error(self):
        """Test that invalid format choices raise SystemExit."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        reviewer.add_reviewer_parser(subparsers)

        with pytest.raises(SystemExit):
            parser.parse_args(["reviewer", "review", "test.py", "--format", "invalid"])

