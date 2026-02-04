"""Simple Mode workflows for specialized task execution."""

from .quick_wins_workflow import QuickWin, QuickWinsResult, QuickWinsWorkflow
from .validation_workflow import ValidationResult, ValidationWorkflow

__all__ = [
    "ValidationWorkflow",
    "ValidationResult",
    "QuickWinsWorkflow",
    "QuickWin",
    "QuickWinsResult",
]
