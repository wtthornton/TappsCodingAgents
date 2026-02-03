"""
Hook system for TappsCodingAgents.

Provides event-driven automation: UserPromptSubmit, PostToolUse, SessionStart,
SessionEnd, WorkflowComplete. Configuration via .tapps-agents/hooks.yaml.
"""

from .config import HookDefinition, HooksConfig, load_hooks_config
from .executor import HookResult, run_hook
from .events import (
    HookEventType,
    PostToolUseEvent,
    SessionEndEvent,
    SessionStartEvent,
    UserPromptSubmitEvent,
    WorkflowCompleteEvent,
)
from .manager import HookManager

__all__ = [
    "HookDefinition",
    "HookManager",
    "HooksConfig",
    "HookResult",
    "load_hooks_config",
    "run_hook",
    "HookEventType",
    "PostToolUseEvent",
    "SessionEndEvent",
    "SessionStartEvent",
    "UserPromptSubmitEvent",
    "WorkflowCompleteEvent",
]
