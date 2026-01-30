"""Simple Mode workflows for specialized task execution."""

from .validation_workflow import ValidationWorkflow, ValidationResult
from .quick_wins_workflow import QuickWinsWorkflow, QuickWin, QuickWinsResult

__all__ = [
    "ValidationWorkflow",
    "ValidationResult",
    "QuickWinsWorkflow",
    "QuickWin",
    "QuickWinsResult",
]
