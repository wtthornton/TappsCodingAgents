"""
E2E tests for cursor verify and cursor check commands.

Validates Cursor integration verification (Skills, Rules, .cursorignore).
"""

import json
import pytest
import shutil
from pathlib import Path

from tests.e2e.cli.test_base import CLICommandTestBase


def _run_init(base: "CLICommandTestBase") -> None:
    """Run init --yes --no-cache in test project."""
    base.run_command(
        ["python", "-m", "tapps_agents.cli", "init", "--yes", "--no-cache"],
        expect_success=False,
    )


@pytest.mark.e2e_cli
class TestCursorVerifyAfterInit(CLICommandTestBase):
    """Cursor verify/check with valid installation."""

    def test_cursor_verify_after_init_succeeds(self):
        """cursor verify after init reports valid installation."""
        _run_init(self)
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "cursor", "verify"],
            expect_success=True,
        )
        assert result.exit_code == 0
        assert "skills" in result.stdout.lower() or "rules" in result.stdout.lower() or "valid" in result.stdout.lower()

    def test_cursor_check_alias(self):
        """cursor check is alias for cursor verify."""
        _run_init(self)
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "cursor", "check"],
            expect_success=True,
        )
        assert result.exit_code == 0

    def test_cursor_verify_format_json(self):
        """cursor verify --format json outputs valid JSON."""
        _run_init(self)
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "cursor", "verify", "--format", "json"],
            expect_success=True,
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "components" in data or "valid" in data or "errors" in data


@pytest.mark.e2e_cli
class TestCursorVerifyMissingComponents(CLICommandTestBase):
    """Cursor verify when components are missing."""

    def test_cursor_verify_missing_skills_fails(self):
        """cursor verify fails when .claude/skills is missing."""
        _run_init(self)
        skills_dir = self.test_project / ".claude" / "skills"
        if not skills_dir.exists():
            pytest.skip("Init did not create .claude/skills")
        shutil.rmtree(skills_dir)
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "cursor", "verify"],
            expect_success=False,
        )
        assert result.exit_code == 1
        assert "skill" in result.stdout.lower() or "error" in result.stdout.lower() or "valid" in result.stdout.lower()

    def test_cursor_verify_missing_rules_fails(self):
        """cursor verify fails when .cursor/rules is missing."""
        _run_init(self)
        rules_dir = self.test_project / ".cursor" / "rules"
        if not rules_dir.exists():
            pytest.skip("Init did not create .cursor/rules")
        shutil.rmtree(rules_dir)
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "cursor", "verify"],
            expect_success=False,
        )
        assert result.exit_code == 1
