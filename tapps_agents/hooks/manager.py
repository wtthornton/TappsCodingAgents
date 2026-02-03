"""
Hook manager: lifecycle, registration by event, and triggering.

Loads hooks from config, runs them via the executor with payload-derived env,
and supports PostToolUse filtering by matcher and file_patterns.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any, Protocol

from .config import HookDefinition, HooksConfig, load_hooks_config
from .executor import HookResult, run_hook


class _PayloadProtocol(Protocol):
    """Payload must provide to_env() for hook execution."""

    def to_env(self) -> dict[str, str]: ...
    def to_dict(self) -> dict[str, Any]: ...


def _tool_matches(hook: HookDefinition, tool_name: str) -> bool:
    """True if hook has no matcher or tool_name matches the matcher regex."""
    if not hook.matcher:
        return True
    try:
        return re.search(hook.matcher, tool_name) is not None
    except re.error:
        return False


def _file_matches(hook: HookDefinition, file_path: str | None) -> bool:
    """True if hook has no file_patterns or file_path matches any pattern."""
    if not hook.file_patterns or not file_path:
        return True
    name = Path(file_path).name
    for pattern in hook.file_patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def _filter_post_tool_use(
    hooks: list[HookDefinition],
    tool_name: str,
    file_path: str | None,
) -> list[HookDefinition]:
    """Filter PostToolUse hooks by matcher and file_patterns."""
    return [
        h
        for h in hooks
        if _tool_matches(h, tool_name) and _file_matches(h, file_path)
    ]


class HookManager:
    """
    Loads and triggers hooks by event type.

    Hooks are loaded from .tapps-agents/hooks.yaml (or explicit path).
    Trigger invokes all enabled hooks for the event with payload-derived env.
    """

    def __init__(
        self,
        config: HooksConfig | None = None,
        *,
        config_path: Path | str | None = None,
        project_root: Path | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        """
        Initialize manager from config or load from path.

        Args:
            config: Pre-loaded config. If None, loads from config_path/project_root.
            config_path: Path to hooks.yaml (used when config is None).
            project_root: Project root for loading config and running hooks.
            timeout_seconds: Override default hook timeout.
        """
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._timeout_seconds = timeout_seconds
        if config is not None:
            self._config = config
        else:
            self._config = load_hooks_config(
                config_path=config_path,
                project_root=self._project_root,
            )

    def _get_hooks_for_event(self, event_name: str) -> list[HookDefinition]:
        """Return enabled hooks for the event."""
        hooks = self._config.hooks.get(event_name, [])
        return [h for h in hooks if h.enabled]

    def trigger(
        self,
        event_name: str,
        payload: _PayloadProtocol,
        *,
        tool_name: str | None = None,
        file_path: str | None = None,
    ) -> list[HookResult]:
        """
        Run all hooks registered for the event with payload env.

        For PostToolUse, only hooks matching tool_name and file_path (matcher
        and file_patterns) are run.

        Args:
            event_name: One of UserPromptSubmit, PostToolUse, SessionStart,
                SessionEnd, WorkflowComplete.
            payload: Event payload with to_env() returning TAPPS_* dict.
            tool_name: For PostToolUse, the tool that was used (e.g. Write, Edit).
            file_path: For PostToolUse, the affected file path.

        Returns:
            List of HookResult in execution order. Caller can check fail_on_error
            and result.success to decide whether to fail the workflow.
        """
        hooks = self._get_hooks_for_event(event_name)
        if event_name == "PostToolUse" and (tool_name is not None or file_path is not None):
            hooks = _filter_post_tool_use(hooks, tool_name or "", file_path)
        env = payload.to_env()
        results: list[HookResult] = []
        for hook in hooks:
            result = run_hook(
                hook,
                env,
                timeout_seconds=self._timeout_seconds,
                project_root=self._project_root,
            )
            results.append(result)
            if hook.fail_on_error and not result.success:
                raise RuntimeError(
                    f"Hook {hook.name} failed (fail_on_error=True): "
                    f"returncode={result.returncode}, stderr={result.stderr[:200]!r}"
                )
        return results
