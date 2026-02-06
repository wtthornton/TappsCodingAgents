"""
Continuous Bug Fix module.

Provides automated bug detection, fixing, and commit workflow.
"""

from .bug_finder import BugFinder, BugInfo
from .bug_fix_coordinator import BugFixCoordinator
from .commit_manager import CommitManager
from .continuous_bug_fixer import ContinuousBugFixer
from .proactive_bug_finder import ProactiveBugFinder

__all__ = [
    "BugFinder",
    "BugFixCoordinator",
    "BugInfo",
    "CommitManager",
    "ContinuousBugFixer",
    "ProactiveBugFinder",
]
