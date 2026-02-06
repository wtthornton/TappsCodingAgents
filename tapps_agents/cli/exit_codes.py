"""CLI exit codes for TappsCodingAgents.

Provides semantic exit codes instead of raw integers.
"""

from enum import IntEnum


class ExitCode(IntEnum):
    """Standard CLI exit codes."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    QUALITY_GATE_FAILED = 3
    TIMEOUT = 4
    KEYBOARD_INTERRUPT = 130
