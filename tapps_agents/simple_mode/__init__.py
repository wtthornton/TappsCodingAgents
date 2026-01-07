"""
Simple Mode - Simplified interface for TappsCodingAgents.

Provides intent-based agent orchestration that hides complexity while
showcasing the power of the framework.

2025 Enhancements:
- StreamingWorkflowExecutor: Progressive streaming with checkpoints
- StreamEvent: Typed events for workflow progress
- Cursor-native response formatting
"""

from .intent_parser import Intent, IntentParser, IntentType
from .nl_handler import SimpleModeHandler
from .streaming import (
    StreamEvent,
    StreamEventType,
    StreamingWorkflowExecutor,
    create_streaming_response,
    format_streaming_response,
)

__all__ = [
    "Intent",
    "IntentParser",
    "IntentType",
    "SimpleModeHandler",
    # 2025: Streaming responses
    "StreamingWorkflowExecutor",
    "StreamEvent",
    "StreamEventType",
    "create_streaming_response",
    "format_streaming_response",
]

