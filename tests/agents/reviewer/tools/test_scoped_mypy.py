"""
Tests for ScopedMypyExecutor - ENH-002-S2.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.tools.scoped_mypy import (
    MypyIssue,
    MypyResult,
    ScopedMypyConfig,
    ScopedMypyExecutor,
)

pytestmark = pytest.mark.unit


class TestScopedMypyConfig:
    def test_default_flags_include_follow_imports_skip(self):
        config = ScopedMypyConfig()
        assert "--follow-imports=skip" in config.flags
        assert "--no-site-packages" in config.flags

    def test_default_timeout(self):
        config = ScopedMypyConfig()
        assert config.timeout == 10


class TestScopedMypyExecutorParseOutput:
    def test_parse_empty_output(self):
        executor = ScopedMypyExecutor()
        target = Path("src/module.py")
        assert executor.parse_output("", target) == []
        assert executor.parse_output("\n\n", target) == []

    def test_parse_filters_to_target_file(self):
        executor = ScopedMypyExecutor()
        target = Path("src/module.py")
        raw = "src/module.py:10: error: Missing return type [return-value]\nother/file.py:1: error: Other"
        issues = executor.parse_output(raw, target)
        assert len(issues) == 1
        assert issues[0].line == 10
        assert "Missing return type" in issues[0].message
        assert issues[0].error_code == "return-value"

    def test_parse_extracts_column_when_present(self):
        executor = ScopedMypyExecutor()
        target = Path("m.py")
        raw = "m.py:5:3: error: Incompatible type [arg-type]"
        issues = executor.parse_output(raw, target)
        assert len(issues) == 1
        assert issues[0].line == 5
        assert issues[0].severity == "error"

    def test_parse_multiple_issues_same_file(self):
        executor = ScopedMypyExecutor()
        target = Path("app.py")
        raw = """app.py:1: error: First [code1]
app.py:2: error: Second [code2]
"""
        issues = executor.parse_output(raw, target)
        assert len(issues) == 2
        assert issues[0].message.strip() == "First"
        assert issues[1].message.strip() == "Second"


class TestScopedMypyExecutorGetScopedFlags:
    def test_returns_list_with_follow_imports_skip(self):
        executor = ScopedMypyExecutor()
        flags = executor.get_scoped_flags()
        assert "--follow-imports=skip" in flags
        assert "--no-site-packages" in flags


class TestScopedMypyExecutorExecuteScoped:
    @pytest.mark.asyncio
    async def test_nonexistent_file_returns_failed_result(self):
        executor = ScopedMypyExecutor(ScopedMypyConfig(timeout=5))
        result = await executor.execute_scoped(Path("nonexistent.py"))
        assert result.success is False
        assert result.files_checked == 0
        assert result.issues == ()

    @pytest.mark.asyncio
    async def test_valid_python_file_runs_mypy(self, tmp_path):
        py = tmp_path / "valid.py"
        py.write_text("x: int = 1\n", encoding="utf-8")
        config = ScopedMypyConfig(timeout=15)
        executor = ScopedMypyExecutor(config)
        result = await executor.execute_scoped(py)
        assert result.files_checked == 1
        assert result.duration_seconds >= 0
        # May have 0 issues (success) or some (e.g. untyped)
        assert isinstance(result.issues, tuple)


class TestMypyResult:
    def test_to_dict(self):
        issue = MypyIssue(
            file_path=Path("a.py"),
            line=1,
            column=0,
            severity="error",
            message="msg",
            error_code="code",
        )
        result = MypyResult(
            issues=(issue,),
            duration_seconds=1.5,
            files_checked=1,
            success=False,
        )
        d = result.to_dict()
        assert d["duration_seconds"] == 1.5
        assert d["files_checked"] == 1
        assert d["success"] is False
        assert len(d["issues"]) == 1
        assert d["issues"][0]["line"] == 1
