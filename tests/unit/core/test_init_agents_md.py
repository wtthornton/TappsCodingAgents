"""Tests for init_agents_md (AGENTS.md open-format scaffold)."""

from pathlib import Path

import pytest

from tapps_agents.core.init_project import (
    _agents_md_placeholders,
    init_agents_md,
)

pytestmark = pytest.mark.unit


class TestAgentsMdPlaceholders:
    def test_placeholders_python_default(self, tmp_path: Path) -> None:
        placeholders = _agents_md_placeholders(tmp_path, {"languages": ["python"]})
        assert placeholders["PROJECT_NAME"] == tmp_path.name
        assert "pytest" in placeholders["TEST_CMD"]
        assert "pip" in placeholders["INSTALL_CMD"]

    def test_placeholders_node_pnpm(self, tmp_path: Path) -> None:
        placeholders = _agents_md_placeholders(
            tmp_path, {"languages": ["javascript"], "frameworks": []}
        )
        assert "pnpm" in placeholders["INSTALL_CMD"]
        assert "pnpm" in placeholders["TEST_CMD"]

    def test_placeholders_none_tech_stack(self, tmp_path: Path) -> None:
        placeholders = _agents_md_placeholders(tmp_path, None)
        assert placeholders["PROJECT_NAME"] == tmp_path.name
        assert "pip" in placeholders["INSTALL_CMD"]


class TestInitAgentsMd:
    def test_creates_agents_md_when_missing(self, tmp_path: Path) -> None:
        ok, pth = init_agents_md(tmp_path, tech_stack={"languages": ["python"]})
        assert ok is True
        assert pth is not None
        agents_md = tmp_path / "AGENTS.md"
        assert agents_md.exists()
        content = agents_md.read_text(encoding="utf-8")
        assert "AGENTS.md" in content
        assert "pytest" in content
        assert "Setup commands" in content

    def test_overwrites_existing_always(self, tmp_path: Path) -> None:
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Custom AGENTS.md\n", encoding="utf-8")
        ok, pth = init_agents_md(tmp_path, tech_stack={"languages": ["python"]})
        assert ok is True
        content = agents_md.read_text(encoding="utf-8")
        assert "Setup commands" in content
        assert "pytest" in content
        assert "# Custom AGENTS.md" not in content or "Custom" not in content.strip()

    def test_second_call_overwrites(self, tmp_path: Path) -> None:
        ok1, _ = init_agents_md(tmp_path, tech_stack={"languages": ["python"]})
        assert ok1 is True
        (tmp_path / "AGENTS.md").write_text("# First content\n", encoding="utf-8")
        ok2, _ = init_agents_md(tmp_path, tech_stack={"languages": ["python"]})
        assert ok2 is True
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "Setup commands" in content
        assert "First content" not in content

    def test_tech_stack_summary_in_rendered_file(self, tmp_path: Path) -> None:
        ok, _ = init_agents_md(
            tmp_path,
            tech_stack={"languages": ["python"], "frameworks": ["FastAPI"]},
        )
        assert ok is True
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "python" in content
        assert "FastAPI" in content
        assert "Tech stack (detected):" in content
