"""
Unit tests for CLI parsers.

Tests that all parsers can be registered and parse arguments correctly.
"""

import argparse

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
    """Test that all parsers can be registered."""

    def test_analyst_parser_registration(self):
        """Test analyst parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        analyst.add_analyst_parser(subparsers)
        
        # Test that parser exists
        args = parser.parse_args(["analyst", "gather-requirements", "test"])
        assert args.agent == "analyst"
        assert args.command == "gather-requirements"
        assert args.description == "test"

    def test_architect_parser_registration(self):
        """Test architect parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        architect.add_architect_parser(subparsers)
        
        args = parser.parse_args(["architect", "design-system", "requirements"])
        assert args.agent == "architect"
        assert args.command == "design-system"
        assert args.requirements == "requirements"

    def test_debugger_parser_registration(self):
        """Test debugger parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        debugger.add_debugger_parser(subparsers)
        
        args = parser.parse_args(["debugger", "debug", "error message", "--file", "test.py"])
        assert args.agent == "debugger"
        assert args.command == "debug"
        assert args.error_message == "error message"
        assert args.file == "test.py"

    def test_designer_parser_registration(self):
        """Test designer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        designer.add_designer_parser(subparsers)
        
        args = parser.parse_args(["designer", "design-api", "requirements"])
        assert args.agent == "designer"
        assert args.command == "design-api"
        assert args.requirements == "requirements"

    def test_documenter_parser_registration(self):
        """Test documenter parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        documenter.add_documenter_parser(subparsers)
        
        args = parser.parse_args(["documenter", "document", "test.py"])
        assert args.agent == "documenter"
        assert args.command == "document"
        assert args.file == "test.py"

    def test_enhancer_parser_registration(self):
        """Test enhancer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        enhancer.add_enhancer_parser(subparsers)
        
        args = parser.parse_args(["enhancer", "enhance", "test prompt"])
        assert args.agent == "enhancer"
        assert args.command == "enhance"
        assert args.prompt == "test prompt"

    def test_implementer_parser_registration(self):
        """Test implementer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        implementer.add_implementer_parser(subparsers)
        
        args = parser.parse_args(["implementer", "implement", "description", "output.py"])
        assert args.agent == "implementer"
        assert args.command == "implement"
        assert args.description == "description"
        assert args.output_file == "output.py"

    def test_improver_parser_registration(self):
        """Test improver parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        improver.add_improver_parser(subparsers)
        
        args = parser.parse_args(["improver", "refactor", "test.py", "--instruction", "improve"])
        assert args.agent == "improver"
        assert args.command == "refactor"
        assert args.file_path == "test.py"
        assert args.instruction == "improve"

    def test_ops_parser_registration(self):
        """Test ops parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        ops.add_ops_parser(subparsers)
        
        args = parser.parse_args(["ops", "security-scan", "--target", "test.py"])
        assert args.agent == "ops"
        assert args.command == "security-scan"
        assert args.target == "test.py"

    def test_orchestrator_parser_registration(self):
        """Test orchestrator parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        orchestrator.add_orchestrator_parser(subparsers)
        
        args = parser.parse_args(["orchestrator", "workflow-start", "test-workflow"])
        assert args.agent == "orchestrator"
        assert args.command == "workflow-start"
        assert args.workflow_id == "test-workflow"

    def test_planner_parser_registration(self):
        """Test planner parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        planner.add_planner_parser(subparsers)
        
        args = parser.parse_args(["planner", "plan", "test feature"])
        assert args.agent == "planner"
        assert args.command == "plan"
        assert args.description == "test feature"

    def test_reviewer_parser_registration(self):
        """Test reviewer parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        reviewer.add_reviewer_parser(subparsers)
        
        args = parser.parse_args(["reviewer", "score", "test.py"])
        assert args.agent == "reviewer"
        assert args.command == "score"
        assert args.file == "test.py"

    def test_tester_parser_registration(self):
        """Test tester parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        tester.add_tester_parser(subparsers)
        
        args = parser.parse_args(["tester", "test", "test.py"])
        assert args.agent == "tester"
        assert args.command == "test"
        assert args.file == "test.py"


class TestTopLevelParsers:
    """Test top-level command parsers."""

    def test_workflow_parser_registration(self):
        """Test workflow parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        top_level.add_top_level_parsers(subparsers)
        
        args = parser.parse_args(["workflow", "full", "--prompt", "test"])
        assert args.command == "workflow"
        assert args.preset == "full"
        assert args.prompt == "test"

    def test_create_parser_registration(self):
        """Test create parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        top_level.add_top_level_parsers(subparsers)
        
        args = parser.parse_args(["create", "test project"])
        assert args.command == "create"
        assert args.prompt == "test project"

    def test_init_parser_registration(self):
        """Test init parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        top_level.add_top_level_parsers(subparsers)
        
        args = parser.parse_args(["init", "--no-rules"])
        assert args.command == "init"
        assert args.no_rules is True

    def test_doctor_parser_registration(self):
        """Test doctor parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        top_level.add_top_level_parsers(subparsers)
        
        args = parser.parse_args(["doctor", "--format", "json"])
        assert args.command == "doctor"
        assert args.format == "json"

    def test_score_parser_registration(self):
        """Test score parser registration."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        top_level.add_top_level_parsers(subparsers)
        
        args = parser.parse_args(["score", "test.py", "--format", "json"])
        assert args.command == "score"
        assert args.file == "test.py"
        assert args.format == "json"

    def test_workflow_presets(self):
        """Test all workflow preset parsers."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        top_level.add_top_level_parsers(subparsers)
        
        presets = ["full", "rapid", "fix", "quality", "hotfix"]
        for preset in presets:
            args = parser.parse_args(["workflow", preset, "--prompt", "test"])
            assert args.preset == preset
            assert args.prompt == "test"


class TestParserArguments:
    """Test parser argument handling."""

    def test_analyst_gather_requirements_args(self):
        """Test analyst gather-requirements arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        analyst.add_analyst_parser(subparsers)
        
        args = parser.parse_args([
            "analyst", "gather-requirements", "test",
            "--context", "context",
            "--output-file", "output.json"
        ])
        assert args.description == "test"
        assert args.context == "context"
        assert args.output_file == "output.json"

    def test_reviewer_score_args(self):
        """Test reviewer score arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        reviewer.add_reviewer_parser(subparsers)
        
        args = parser.parse_args([
            "reviewer", "score", "test.py",
            "--format", "json"
        ])
        assert args.file == "test.py"
        assert args.format == "json"

    def test_tester_test_args(self):
        """Test tester test arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        tester.add_tester_parser(subparsers)
        
        args = parser.parse_args([
            "tester", "test", "test.py",
            "--test-file", "test_test.py",
            "--integration"
        ])
        assert args.file == "test.py"
        assert args.test_file == "test_test.py"
        assert args.integration is True

    def test_planner_plan_args(self):
        """Test planner plan arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        planner.add_planner_parser(subparsers)
        
        args = parser.parse_args([
            "planner", "plan", "test feature",
            "--epic", "test-epic",
            "--priority", "high"
        ])
        assert args.description == "test feature"
        assert args.epic == "test-epic"
        assert args.priority == "high"

