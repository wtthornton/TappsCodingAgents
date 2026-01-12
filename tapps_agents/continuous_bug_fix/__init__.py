"""
Continuous Bug Fix module.

Provides automated bug detection, fixing, and commit workflow.
"""

from .bug_finder import BugFinder, BugInfo
from .bug_fix_coordinator import BugFixCoordinator
from .commit_manager import CommitManager
from .continuous_bug_fixer import ContinuousBugFixer

__all__ = [
    "BugFinder",
    "BugInfo",
    "BugFixCoordinator",
    "CommitManager",
    "ContinuousBugFixer",
]
