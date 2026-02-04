"""
Hook configuration schema and loader.

Loads and validates .tapps-agents/hooks.yaml with event definitions,
matchers, and commands. Supported events: UserPromptSubmit, PostToolUse,
SessionStart, SessionEnd, WorkflowComplete.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

# Supported hook event types
HOOK_EVENT_TYPES = frozenset({
    "UserPromptSubmit",
    "PostToolUse",
    "SessionStart",
    "SessionEnd",
    "WorkflowComplete",
})


class HookDefinition(BaseModel):
    """Single hook definition within an event."""

    name: str = Field(..., min_length=1, description="Hook display name")
    command: str = Field(..., min_length=1, description="Shell command to execute")
    enabled: bool = Field(default=True, description="Whether hook is enabled")
    matcher: str | None = Field(
        default=None,
        description="Tool name matcher for PostToolUse (e.g. 'Write|Edit')",
    )
    file_patterns: list[str] | None = Field(
        default=None,
        description="Glob patterns for file filtering (e.g. ['*.py'])",
    )
    fail_on_error: bool = Field(
        default=False,
        description="If true, non-zero exit fails workflow",
    )

    model_config = {"extra": "forbid"}


class HooksConfig(BaseModel):
    """
    Root schema for hooks.yaml.

    Top-level key is 'hooks'. Each event maps to a list of HookDefinition.
    """

    hooks: dict[str, list[HookDefinition]] = Field(
        default_factory=dict,
        description="Event name -> list of hook definitions",
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_event_names(self) -> HooksConfig:
        """Ensure only supported event names are used."""
        for event_name in self.hooks:
            if event_name not in HOOK_EVENT_TYPES:
                raise ValueError(
                    f"Unsupported hook event '{event_name}'. "
                    f"Supported: {', '.join(sorted(HOOK_EVENT_TYPES))}"
                )
        return self


def load_hooks_config(
    config_path: Path | str | None = None,
    project_root: Path | None = None,
) -> HooksConfig:
    """
    Load and validate hooks.yaml.

    Args:
        config_path: Explicit path to hooks.yaml. If None, uses
            project_root/.tapps-agents/hooks.yaml.
        project_root: Project root (default: cwd). Used when config_path is None.

    Returns:
        Validated HooksConfig. Returns empty config (all events empty) when
        file is missing (safe defaults).

    Raises:
        FileNotFoundError: If config_path is given and file doesn't exist.
        yaml.YAMLError: On YAML parse errors (includes path/line in message).
        ValueError: On schema validation failures.
    """
    project_root = project_root or Path.cwd()
    if config_path is None:
        config_path = project_root / ".tapps-agents" / "hooks.yaml"
    else:
        config_path = Path(config_path)
        if not config_path.is_absolute():
            config_path = project_root / config_path

    if not config_path.exists():
        return HooksConfig(hooks={})

    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError as e:
        raise FileNotFoundError(
            f"Cannot read hooks config from {config_path}: {e}"
        ) from e

    try:
        raw = yaml.safe_load(content)
    except yaml.YAMLError as e:
        path_hint = str(config_path)
        if hasattr(e, "problem_mark") and e.problem_mark:
            line = e.problem_mark.line + 1
            col = e.problem_mark.column + 1
            path_hint = f"{config_path}:{line}:{col}"
        raise yaml.YAMLError(f"Invalid YAML in {path_hint}: {e}") from e

    if raw is None:
        return HooksConfig(hooks={})

    if not isinstance(raw, dict):
        raise ValueError(
            f"hooks.yaml must be a YAML object (dict), got {type(raw).__name__} "
            f"at {config_path}"
        )

    if "hooks" not in raw:
        return HooksConfig(hooks={})

    try:
        return HooksConfig.model_validate(raw)
    except Exception as e:
        raise ValueError(
            f"Hooks config validation failed at {config_path}: {e}"
        ) from e
