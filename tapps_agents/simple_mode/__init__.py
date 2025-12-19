"""
Simple Mode - Simplified interface for TappsCodingAgents.

Provides intent-based agent orchestration that hides complexity while
showcasing the power of the framework.
"""

from .intent_parser import Intent, IntentParser, IntentType
from .nl_handler import SimpleModeHandler

__all__ = [
    "Intent",
    "IntentParser",
    "IntentType",
    "SimpleModeHandler",
]

