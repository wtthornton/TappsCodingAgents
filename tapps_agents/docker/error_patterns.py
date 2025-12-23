"""
Error Pattern Database

Stores error → fix mappings for pattern matching and learning.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ErrorFix:
    """Represents an error fix pattern."""

    action: str
    confidence: float
    success_count: int = 0
    failure_count: int = 0
    description: str = ""


@dataclass
class ErrorPattern:
    """Represents an error pattern with potential fixes."""

    pattern: str
    category: str
    fixes: list[ErrorFix] = field(default_factory=list)
    regex_pattern: str = ""


class ErrorPatternDatabase:
    """
    Database of error patterns and their fixes.

    Supports learning from successful fixes to improve confidence scores.
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize error pattern database.

        Args:
            db_path: Path to JSON database file (default: .tapps-agents/error-patterns.json)
        """
        if db_path is None:
            db_path = Path.cwd() / ".tapps-agents" / "error-patterns.json"
        self.db_path = db_path
        self.patterns: dict[str, ErrorPattern] = {}
        self._load_database()

    def _load_database(self) -> None:
        """Load patterns from database file."""
        if not self.db_path.exists():
            self._initialize_default_patterns()
            return

        try:
            with self.db_path.open(encoding="utf-8") as f:
                data = json.load(f)

            for pattern_data in data.get("patterns", []):
                pattern = ErrorPattern(
                    pattern=pattern_data["pattern"],
                    category=pattern_data["category"],
                    regex_pattern=pattern_data.get("regex_pattern", ""),
                )
                for fix_data in pattern_data.get("fixes", []):
                    pattern.fixes.append(
                        ErrorFix(
                            action=fix_data["action"],
                            confidence=fix_data["confidence"],
                            success_count=fix_data.get("success_count", 0),
                            failure_count=fix_data.get("failure_count", 0),
                            description=fix_data.get("description", ""),
                        )
                    )
                self.patterns[pattern.pattern] = pattern
        except Exception as e:
            logger.warning(f"Failed to load error pattern database: {e}")
            self._initialize_default_patterns()

    def _initialize_default_patterns(self) -> None:
        """Initialize with default error patterns."""
        # Dockerfile Python path issue
        self.patterns["ModuleNotFoundError: No module named 'src'"] = ErrorPattern(
            pattern="ModuleNotFoundError: No module named 'src'",
            category="dockerfile_python_path",
            regex_pattern=r"ModuleNotFoundError.*No module named ['\"]src['\"]",
            fixes=[
                ErrorFix(
                    action="move_workdir_before_copy",
                    confidence=0.95,
                    success_count=12,
                    description="Move WORKDIR before COPY commands",
                ),
                ErrorFix(
                    action="use_python_m_uvicorn",
                    confidence=0.90,
                    success_count=8,
                    description="Use 'python -m uvicorn' instead of 'uvicorn'",
                ),
            ],
        )

    def match_error(self, error_message: str) -> ErrorPattern | None:
        """
        Match an error message to a pattern.

        Args:
            error_message: Error message to match

        Returns:
            Matching ErrorPattern or None
        """
        for pattern in self.patterns.values():
            if pattern.regex_pattern:
                import re

                if re.search(pattern.regex_pattern, error_message, re.IGNORECASE):
                    return pattern
            elif pattern.pattern.lower() in error_message.lower():
                return pattern

        return None

    def get_best_fix(self, error_message: str) -> ErrorFix | None:
        """
        Get the best fix for an error.

        Args:
            error_message: Error message

        Returns:
            Best ErrorFix or None
        """
        pattern = self.match_error(error_message)
        if not pattern or not pattern.fixes:
            return None

        # Return fix with highest confidence
        return max(pattern.fixes, key=lambda f: f.confidence)

    def record_success(self, error_message: str, fix_action: str) -> None:
        """
        Record a successful fix.

        Args:
            error_message: Error message that was fixed
            fix_action: Action that fixed it
        """
        pattern = self.match_error(error_message)
        if not pattern:
            return

        for fix in pattern.fixes:
            if fix.action == fix_action:
                fix.success_count += 1
                # Increase confidence slightly
                fix.confidence = min(fix.confidence + 0.01, 1.0)
                self._save_database()
                break

    def record_failure(self, error_message: str, fix_action: str) -> None:
        """
        Record a failed fix attempt.

        Args:
            error_message: Error message
            fix_action: Action that failed
        """
        pattern = self.match_error(error_message)
        if not pattern:
            return

        for fix in pattern.fixes:
            if fix.action == fix_action:
                fix.failure_count += 1
                # Decrease confidence slightly
                fix.confidence = max(fix.confidence - 0.02, 0.0)
                self._save_database()
                break

    def _save_database(self) -> None:
        """Save patterns to database file."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "patterns": [
                {
                    "pattern": p.pattern,
                    "category": p.category,
                    "regex_pattern": p.regex_pattern,
                    "fixes": [
                        {
                            "action": f.action,
                            "confidence": f.confidence,
                            "success_count": f.success_count,
                            "failure_count": f.failure_count,
                            "description": f.description,
                        }
                        for f in p.fixes
                    ],
                }
                for p in self.patterns.values()
            ]
        }

        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

