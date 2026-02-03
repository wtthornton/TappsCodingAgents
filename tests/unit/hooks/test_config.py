"""
Unit tests for tapps_agents.hooks.config: schema, load, validation, error handling.
"""

from pathlib import Path

import pytest
import yaml

from tapps_agents.hooks.config import (
    HOOK_EVENT_TYPES,
    HookDefinition,
    HooksConfig,
    load_hooks_config,
)


@pytest.mark.unit
class TestHookDefinition:
    """Tests for HookDefinition schema."""

    def test_required_name_and_command(self) -> None:
        """name and command are required."""
        HookDefinition(name="h1", command="echo ok")
        with pytest.raises(Exception):
            HookDefinition(name="", command="echo")  # min_length
        with pytest.raises(Exception):
            HookDefinition(name="h", command="")  # min_length

    def test_optional_fields_defaults(self) -> None:
        """enabled defaults True, matcher/file_patterns optional."""
        h = HookDefinition(name="h", command="true")
        assert h.enabled is True
        assert h.matcher is None
        assert h.file_patterns is None
        assert h.fail_on_error is False

    def test_all_fields(self) -> None:
        """All fields (name, command, enabled, matcher, file_patterns) accepted."""
        h = HookDefinition(
            name="Auto-format",
            command="black {file_path}",
            enabled=True,
            matcher="Write|Edit",
            file_patterns=["*.py"],
            fail_on_error=False,
        )
        assert h.name == "Auto-format"
        assert h.command == "black {file_path}"
        assert h.matcher == "Write|Edit"
        assert h.file_patterns == ["*.py"]

    def test_forbid_extra_fields(self) -> None:
        """Extra fields rejected."""
        with pytest.raises(Exception):
            HookDefinition(name="h", command="true", unknown="x")


@pytest.mark.unit
class TestHooksConfig:
    """Tests for HooksConfig schema."""

    def test_empty_hooks_valid(self) -> None:
        """Empty hooks dict is valid."""
        c = HooksConfig(hooks={})
        assert c.hooks == {}

    def test_supported_events_accepted(self) -> None:
        """All 5 supported events are accepted."""
        c = HooksConfig(
            hooks={
                "UserPromptSubmit": [
                    HookDefinition(name="ctx", command="cat x"),
                ],
                "PostToolUse": [
                    HookDefinition(name="fmt", command="black x", matcher="Write"),
                ],
                "SessionStart": [
                    HookDefinition(name="ready", command="bd ready"),
                ],
                "SessionEnd": [
                    HookDefinition(name="save", command="echo done"),
                ],
                "WorkflowComplete": [
                    HookDefinition(name="done", command="echo ok"),
                ],
            }
        )
        assert len(c.hooks) == 5
        assert "UserPromptSubmit" in c.hooks
        assert "WorkflowComplete" in c.hooks

    def test_unsupported_event_rejected(self) -> None:
        """Unsupported event names raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported hook event 'InvalidEvent'"):
            HooksConfig(
                hooks={
                    "InvalidEvent": [
                        HookDefinition(name="x", command="true"),
                    ],
                }
            )


@pytest.mark.unit
class TestLoadHooksConfig:
    """Tests for load_hooks_config."""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """When hooks.yaml is missing, return empty config (safe defaults)."""
        path = tmp_path / ".tapps-agents" / "hooks.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        # No file created - should return empty
        cfg = load_hooks_config(project_root=tmp_path)
        assert cfg.hooks == {}

    def test_load_valid_config(self, tmp_path: Path) -> None:
        """Load valid hooks.yaml."""
        (tmp_path / ".tapps-agents").mkdir(parents=True)
        hooks_file = tmp_path / ".tapps-agents" / "hooks.yaml"
        hooks_file.write_text(
            """
hooks:
  UserPromptSubmit:
    - name: Add context
      command: cat .tapps-agents/context/project.md
      enabled: true
  PostToolUse:
    - name: Auto-format
      command: black {file_path}
      matcher: Write|Edit
      file_patterns: ["*.py"]
      enabled: true
""",
            encoding="utf-8",
        )
        cfg = load_hooks_config(project_root=tmp_path)
        assert "UserPromptSubmit" in cfg.hooks
        assert len(cfg.hooks["UserPromptSubmit"]) == 1
        assert cfg.hooks["UserPromptSubmit"][0].name == "Add context"
        assert "PostToolUse" in cfg.hooks
        assert cfg.hooks["PostToolUse"][0].matcher == "Write|Edit"
        assert cfg.hooks["PostToolUse"][0].file_patterns == ["*.py"]

    def test_invalid_yaml_raises_with_path_hint(self, tmp_path: Path) -> None:
        """Invalid YAML raises yaml.YAMLError with path/line hint."""
        (tmp_path / ".tapps-agents").mkdir(parents=True)
        hooks_file = tmp_path / ".tapps-agents" / "hooks.yaml"
        hooks_file.write_text("hooks:\n  bad: [\n  unfinished", encoding="utf-8")
        with pytest.raises(yaml.YAMLError, match="hooks\\.yaml|Invalid YAML"):
            load_hooks_config(project_root=tmp_path)

    def test_schema_violation_raises_value_error(self, tmp_path: Path) -> None:
        """Schema validation failure raises ValueError with path."""
        (tmp_path / ".tapps-agents").mkdir(parents=True)
        hooks_file = tmp_path / ".tapps-agents" / "hooks.yaml"
        hooks_file.write_text(
            """
hooks:
  UserPromptSubmit:
    - name: x
      command: ""   # empty command invalid
""",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="validation failed|Hooks config"):
            load_hooks_config(project_root=tmp_path)

    def test_explicit_config_path(self, tmp_path: Path) -> None:
        """Explicit config_path is used."""
        custom = tmp_path / "my-hooks.yaml"
        custom.write_text(
            """
hooks:
  SessionStart:
    - name: Init
      command: echo init
      enabled: true
""",
            encoding="utf-8",
        )
        cfg = load_hooks_config(config_path=custom, project_root=tmp_path)
        assert "SessionStart" in cfg.hooks
        assert cfg.hooks["SessionStart"][0].command == "echo init"

    def test_none_yaml_returns_empty(self, tmp_path: Path) -> None:
        """Empty YAML file (None) returns empty config."""
        (tmp_path / ".tapps-agents").mkdir(parents=True)
        (tmp_path / ".tapps-agents" / "hooks.yaml").write_text("", encoding="utf-8")
        cfg = load_hooks_config(project_root=tmp_path)
        assert cfg.hooks == {}


@pytest.mark.unit
class TestHookEventTypes:
    """Tests for HOOK_EVENT_TYPES constant."""

    def test_all_five_events(self) -> None:
        """HOOK_EVENT_TYPES contains exactly the 5 supported events."""
        expected = {
            "UserPromptSubmit",
            "PostToolUse",
            "SessionStart",
            "SessionEnd",
            "WorkflowComplete",
        }
        assert HOOK_EVENT_TYPES == expected
