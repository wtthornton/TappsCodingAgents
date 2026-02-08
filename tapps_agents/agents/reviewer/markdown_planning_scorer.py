"""
Markdown Planning Document Scorer.

Scores PRDs, implementation plans, epics, and story documents (markdown)
on structure, completeness, traceability, and format.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ...core.language_detector import Language
from .scoring import BaseScorer


class MarkdownPlanningScorer(BaseScorer):
    """
    Scores markdown planning documents (PRDs, implementation plans, epics, stories).

    Categories (0-100):
    - structure_score: Has Purpose, Scope, Goals, Phase sections
    - completeness_score: Few TBD/placeholder/TODO
    - traceability_score: Links between requirements/stories/phases
    - format_score: Headings, lists, tables
    """

    # Section headings that indicate good structure
    STRUCTURE_HEADINGS = re.compile(
        r"^##\s+(Purpose|Scope|Goals?|Phase\s+\d|Overview|Table of contents|References?)",
        re.MULTILINE | re.IGNORECASE,
    )
    # Task/checkbox patterns
    CHECKBOX = re.compile(r"^\s*-\s+\[[\sx]\]", re.MULTILINE)
    TBD_TODO = re.compile(r"\b(TBD|TODO|FIXME|XXX)\b", re.IGNORECASE)
    # Markdown links [text](path)
    LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    # Headings (## or ###)
    HEADING = re.compile(r"^#{2,6}\s+.+", re.MULTILINE)
    # List items
    LIST_ITEM = re.compile(r"^\s*[-*]\s+", re.MULTILINE)
    # Table row (|---|---|)
    TABLE_ROW = re.compile(r"^\s*\|.+\|", re.MULTILINE)

    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Score a markdown planning document.

        Returns dict with: overall_score, structure_score, completeness_score,
        traceability_score, format_score, metrics (issues, strengths).
        """
        structure_score = self._score_structure(code)
        completeness_score = self._score_completeness(code)
        traceability_score = self._score_traceability(code)
        format_score = self._score_format(code)

        # Weighted overall (0-100)
        overall = (
            structure_score * 0.30
            + completeness_score * 0.25
            + traceability_score * 0.25
            + format_score * 0.20
        )

        issues: list[str] = []
        strengths: list[str] = []

        if structure_score < 50:
            issues.append("Missing standard sections (Purpose, Scope, Goals, Phase)")
        else:
            strengths.append("Document has clear structure")

        tbd_count = len(self.TBD_TODO.findall(code))
        if tbd_count > 5:
            issues.append(f"Many placeholders (TBD/TODO): {tbd_count}")
        elif tbd_count == 0 and len(code) > 500:
            strengths.append("No TBD/TODO placeholders")

        if traceability_score < 40:
            issues.append("Few or no links between sections")
        elif traceability_score >= 70:
            strengths.append("Good traceability with links")

        metrics: dict[str, Any] = {
            "issues": issues,
            "strengths": strengths,
            "language": Language.MARKDOWN.value,
        }

        return {
            "overall_score": round(overall, 1),
            "structure_score": round(structure_score, 1),
            "completeness_score": round(completeness_score, 1),
            "traceability_score": round(traceability_score, 1),
            "format_score": round(format_score, 1),
            # Map to reviewer 7-category names where expected (optional)
            "complexity_score": min(10.0, structure_score / 10.0),
            "security_score": 5.0,
            "maintainability_score": min(10.0, completeness_score / 10.0),
            "test_coverage_score": 0.0,
            "performance_score": 5.0,
            "metrics": metrics,
        }

    def _score_structure(self, code: str) -> float:
        """Score 0-100: presence of Purpose, Scope, Goals, Phase sections."""
        matches = self.STRUCTURE_HEADINGS.findall(code)
        if not matches:
            return 0.0
        # Normalize to unique section types
        seen = set(m.lower() for m in matches)
        points = 0.0
        if any("purpose" in s for s in seen):
            points += 25.0
        if any("scope" in s for s in seen):
            points += 25.0
        if any("goal" in s for s in seen):
            points += 20.0
        if any("phase" in s for s in seen):
            points += 20.0
        if any("overview" in s or "table of contents" in s or "references" in s for s in seen):
            points += 10.0
        return min(100.0, points)

    def _score_completeness(self, code: str) -> float:
        """Score 0-100: few TBD/TODO/placeholder; has checkboxes or acceptance criteria."""
        tbd_count = len(self.TBD_TODO.findall(code))
        word_count = max(1, len(code.split()))
        # Penalize by TBD density (e.g. 1 per 200 words = small penalty)
        tbd_penalty = min(80.0, tbd_count * (200.0 / max(1, word_count / 50)))
        base = 100.0 - tbd_penalty
        # Bonus for task/acceptance structure
        checkboxes = len(self.CHECKBOX.findall(code))
        if checkboxes >= 3:
            base = min(100.0, base + 10.0)
        return max(0.0, base)

    def _score_traceability(self, code: str) -> float:
        """Score 0-100: links between sections, requirements, stories."""
        links = self.LINK.findall(code)
        if not links:
            return 0.0
        # More internal links (to .md or #) = better traceability
        internal = sum(1 for _text, path in links if path.endswith(".md") or path.startswith("#"))
        total = len(links)
        if total == 0:
            return 0.0
        ratio = internal / total
        count_score = min(50.0, total * 5.0)  # cap at 50 for count
        internal_score = ratio * 50.0  # up to 50 for internal ratio
        return min(100.0, count_score + internal_score)

    def _score_format(self, code: str) -> float:
        """Score 0-100: headings, lists, tables."""
        headings = len(self.HEADING.findall(code))
        list_items = len(self.LIST_ITEM.findall(code))
        table_rows = len(self.TABLE_ROW.findall(code))
        points = 0.0
        points += min(40.0, headings * 5.0)
        points += min(30.0, list_items * 0.5)
        points += min(30.0, table_rows * 3.0)
        return min(100.0, points)
