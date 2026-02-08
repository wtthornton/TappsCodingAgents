"""
Epic Evaluator - Quality scoring for Epic documents (markdown).

Evaluates epic structure, story breakdown, and dependencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EpicQualityScore:
    """Epic document quality score."""

    overview_score: float = 0.0  # 0-100: Has overview, goal, success metrics
    story_breakdown_score: float = 0.0  # 0-100: Has story list or phase breakdown
    dependency_score: float = 0.0  # 0-100: Dependencies or ordering present
    acceptance_criteria_score: float = 0.0  # 0-100: Stories have acceptance criteria
    overall: float = 0.0  # Weighted average
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class EpicEvaluator:
    """Evaluates Epic document quality (structure, story breakdown, dependencies)."""

    OVERVIEW_WEIGHT = 0.25
    STORY_WEIGHT = 0.30
    DEPENDENCY_WEIGHT = 0.25
    ACCEPTANCE_WEIGHT = 0.20

    OVERVIEW_HEADINGS = re.compile(
        r"^##?\s+(Epic\s+Overview|Goal|Overview|Problem|Success\s+Metrics)",
        re.MULTILINE | re.IGNORECASE,
    )
    STORY_HEADINGS = re.compile(
        r"^##?\s+(Stories?|Story\s+Summary|Phase\s+\d|Epic\s+Stories)",
        re.MULTILINE | re.IGNORECASE,
    )
    STORY_TABLE_OR_LIST = re.compile(
        r"^\s*\|.*\|.*\||^\s*-\s+.*(?:points?|story)",
        re.MULTILINE | re.IGNORECASE,
    )
    DEPENDENCY_PATTERNS = re.compile(
        r"(?:dependencies?|depends?\s+on|RP-\d+|ENH-\d+)\s*[:\|]",
        re.MULTILINE | re.IGNORECASE,
    )
    ACCEPTANCE_PATTERN = re.compile(
        r"Acceptance\s+Criteria|acceptance_criteria",
        re.IGNORECASE,
    )
    STORY_ID = re.compile(r"(?:^|\s)([A-Z]{2,}-\d+)\s*[:\|]?", re.MULTILINE)

    def evaluate(self, epic_content: str | Path) -> EpicQualityScore:
        """
        Evaluate epic document quality.

        Args:
            epic_content: Epic markdown as string or path to file.

        Returns:
            EpicQualityScore with overview, story_breakdown, dependency, overall, issues, recommendations.
        """
        if isinstance(epic_content, Path):
            text = epic_content.read_text(encoding="utf-8", errors="replace")
        else:
            text = epic_content

        score = EpicQualityScore()

        score.overview_score = self._score_overview(text)
        score.story_breakdown_score = self._score_story_breakdown(text)
        score.dependency_score = self._score_dependencies(text)
        score.acceptance_criteria_score = self._score_acceptance_criteria(text)

        score.overall = (
            score.overview_score * self.OVERVIEW_WEIGHT
            + score.story_breakdown_score * self.STORY_WEIGHT
            + score.dependency_score * self.DEPENDENCY_WEIGHT
            + score.acceptance_criteria_score * self.ACCEPTANCE_WEIGHT
        )

        score.issues = self._identify_issues(text, score)
        score.recommendations = self._recommendations(score)

        return score

    def _score_overview(self, text: str) -> float:
        """Score 0-100: has overview, goal, success metrics."""
        matches = self.OVERVIEW_HEADINGS.findall(text)
        seen = set(m.lower() for m in matches)
        points = 0.0
        if any("overview" in s or "goal" in s for s in seen):
            points += 40.0
        if any("goal" in s for s in seen):
            points += 20.0
        if any("success" in s or "metric" in s for s in seen):
            points += 25.0
        if any("problem" in s for s in seen):
            points += 15.0
        return min(100.0, points)

    def _score_story_breakdown(self, text: str) -> float:
        """Score 0-100: has story list or phase breakdown."""
        story_matches = self.STORY_HEADINGS.findall(text)
        table_or_list = len(self.STORY_TABLE_OR_LIST.findall(text))
        story_ids = self.STORY_ID.findall(text)
        points = 0.0
        if story_matches:
            points += 40.0
        if table_or_list >= 3:
            points += 30.0
        if len(set(story_ids)) >= 2:
            points += 30.0
        return min(100.0, points)

    def _score_dependencies(self, text: str) -> float:
        """Score 0-100: dependencies or ordering present."""
        dep_matches = self.DEPENDENCY_PATTERNS.findall(text)
        story_ids = self.STORY_ID.findall(text)
        if not story_ids:
            return 0.0
        points = min(50.0, len(dep_matches) * 15.0)
        if "Dependencies" in text or "dependencies" in text:
            points += 50.0
        return min(100.0, points)

    def _score_acceptance_criteria(self, text: str) -> float:
        """Score 0-100: stories have acceptance criteria."""
        ac_matches = self.ACCEPTANCE_PATTERN.findall(text)
        story_count = len(set(self.STORY_ID.findall(text)))
        if story_count == 0:
            return 50.0  # No stories to judge
        ratio = len(ac_matches) / max(1, story_count)
        return min(100.0, ratio * 100.0)

    def _identify_issues(self, text: str, score: EpicQualityScore) -> list[str]:
        """Identify issues from scores."""
        issues = []
        if score.overview_score < 50:
            issues.append("Epic overview or goal section is missing or weak.")
        if score.story_breakdown_score < 50:
            issues.append("Story breakdown or phase list is missing or unclear.")
        if score.dependency_score < 40:
            issues.append("Story dependencies or ordering are not clearly indicated.")
        if score.acceptance_criteria_score < 60:
            issues.append("Some stories may be missing acceptance criteria.")
        return issues

    def _recommendations(self, score: EpicQualityScore) -> list[str]:
        """Generate recommendations."""
        recs = []
        if score.overview_score < 70:
            recs.append("Add a clear Epic Overview with Goal and Success Metrics.")
        if score.story_breakdown_score < 70:
            recs.append("Add a Story Summary table and phase-wise story list.")
        if score.dependency_score < 60:
            recs.append("Document story dependencies (e.g. RP-002 depends on RP-001).")
        if score.acceptance_criteria_score < 80:
            recs.append("Ensure every story has 3-5 acceptance criteria.")
        return recs


@dataclass
class ImplementationPlanQualityScore:
    """Implementation plan document quality score."""

    phase_score: float = 0.0  # 0-100: Phases/sections defined
    task_score: float = 0.0  # 0-100: Tasks have checkboxes or acceptance criteria
    completion_score: float = 0.0  # 0-100: Completion checklist exists
    overall: float = 0.0
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class ImplementationPlanEvaluator:
    """Evaluates implementation plan documents (phases, tasks, completion criteria)."""

    PHASE_HEADING = re.compile(r"^##\s+Phase\s+\d+|^##\s+\d+\.\s+", re.MULTILINE | re.IGNORECASE)
    CHECKBOX = re.compile(r"^\s*-\s+\[\s*[x ]?\s*\]", re.MULTILINE)
    ACCEPTANCE = re.compile(r"Acceptance|acceptance_criteria|\*\*Acceptance", re.IGNORECASE)
    COMPLETION = re.compile(r"Completion\s+checklist|Definition\s+of\s+done|Verification", re.MULTILINE | re.IGNORECASE)

    def evaluate(self, content: str | Path) -> ImplementationPlanQualityScore:
        """Evaluate implementation plan. Returns phase_score, task_score, completion_score, overall, issues, recommendations."""
        text = Path(content).read_text(encoding="utf-8", errors="replace") if isinstance(content, Path) else content
        score = ImplementationPlanQualityScore()
        score.phase_score = self._score_phases(text)
        score.task_score = self._score_tasks(text)
        score.completion_score = self._score_completion(text)
        score.overall = (score.phase_score * 0.4 + score.task_score * 0.35 + score.completion_score * 0.25)
        score.issues = self._issues(text, score)
        score.recommendations = self._recs(score)
        return score

    def _score_phases(self, text: str) -> float:
        phases = self.PHASE_HEADING.findall(text)
        return min(100.0, 20.0 * max(0, len(phases)))

    def _score_tasks(self, text: str) -> float:
        checkboxes = len(self.CHECKBOX.findall(text))
        acceptance = len(self.ACCEPTANCE.findall(text))
        return min(100.0, checkboxes * 2.0 + acceptance * 15.0)

    def _score_completion(self, text: str) -> float:
        m = self.COMPLETION.findall(text)
        return 100.0 if m else 0.0

    def _issues(self, text: str, score: ImplementationPlanQualityScore) -> list[str]:
        issues = []
        if score.phase_score < 40:
            issues.append("Few or no Phase sections defined.")
        if score.task_score < 50:
            issues.append("Tasks lack checkboxes or acceptance criteria.")
        if score.completion_score < 100:
            issues.append("Completion checklist or verification section missing.")
        return issues

    def _recs(self, score: ImplementationPlanQualityScore) -> list[str]:
        recs = []
        if score.phase_score < 70:
            recs.append("Define phases with ## Phase N headings.")
        if score.task_score < 70:
            recs.append("Use - [ ] task items and Acceptance criteria per task.")
        if score.completion_score < 100:
            recs.append("Add a Completion checklist or Definition of done section.")
        return recs
