"""Unit tests for init hook helpers (init_hooks_minimal, init_hooks_and_context)."""
from pathlib import Path

import pytest

from tapps_agents.core.init_project import init_hooks_and_context, init_hooks_minimal


@pytest.mark.unit
def test_init_hooks_minimal_creates_file(tmp_path: Path) -> None:
    """init_hooks_minimal creates .tapps-agents/hooks.yaml with hooks: {} when missing."""
    created, path = init_hooks_minimal(tmp_path)
    assert created is True
    assert path is not None
    hooks_file = tmp_path / ".tapps-agents" / "hooks.yaml"
    assert hooks_file.exists()
    assert hooks_file.read_text().strip() == "hooks: {}"


@pytest.mark.unit
def test_init_hooks_minimal_does_not_overwrite(tmp_path: Path) -> None:
    """init_hooks_minimal does not overwrite existing hooks.yaml."""
    config_dir = tmp_path / ".tapps-agents"
    config_dir.mkdir(parents=True)
    hooks_file = config_dir / "hooks.yaml"
    hooks_file.write_text("hooks:\n  PostToolUse: []\n", encoding="utf-8")
    created, path = init_hooks_minimal(tmp_path)
    assert created is False
    assert path == str(hooks_file)
    assert "PostToolUse" in hooks_file.read_text()


@pytest.mark.unit
def test_init_hooks_and_context_creates_hooks_yaml_and_context(tmp_path: Path) -> None:
    """init_hooks_and_context creates hooks.yaml from templates and .tapps-agents/context/."""
    hooks_created, hooks_path, context_created, files_created = init_hooks_and_context(tmp_path)
    assert hooks_created is True
    assert hooks_path is not None
    assert context_created is True
    assert ".tapps-agents/hooks.yaml" in files_created
    assert ".tapps-agents/context/README.md" in files_created

    hooks_file = tmp_path / ".tapps-agents" / "hooks.yaml"
    assert hooks_file.exists()
    content = hooks_file.read_text()
    assert "hooks:" in content
    # All hooks from templates should be present and disabled
    assert "enabled: false" in content or "enabled: False" in content
    # At least one event from templates (e.g. PostToolUse, SessionStart)
    assert "PostToolUse" in content or "SessionStart" in content or "WorkflowComplete" in content

    context_readme = tmp_path / ".tapps-agents" / "context" / "README.md"
    assert context_readme.exists()
    assert "Project context" in context_readme.read_text()


@pytest.mark.unit
def test_init_hooks_and_context_context_readme_not_overwritten(tmp_path: Path) -> None:
    """init_hooks_and_context does not overwrite existing context/README.md."""
    context_dir = tmp_path / ".tapps-agents" / "context"
    context_dir.mkdir(parents=True)
    readme = context_dir / "README.md"
    readme.write_text("Custom existing readme", encoding="utf-8")
    _, _, context_created, files_created = init_hooks_and_context(tmp_path)
    assert context_created is False
    assert ".tapps-agents/context/README.md" not in files_created
    assert readme.read_text() == "Custom existing readme"


@pytest.mark.unit
def test_init_hooks_and_context_hooks_yaml_has_all_hooks_disabled(tmp_path: Path) -> None:
    """Hooks written by init_hooks_and_context have enabled: false."""
    init_hooks_and_context(tmp_path)
    import yaml
    hooks_file = tmp_path / ".tapps-agents" / "hooks.yaml"
    data = yaml.safe_load(hooks_file.read_text())
    assert "hooks" in data
    for _event_name, hook_list in data["hooks"].items():
        for hook in hook_list:
            assert hook.get("enabled") is False, f"Hook {hook.get('name')} should be disabled"
