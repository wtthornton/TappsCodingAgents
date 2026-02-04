"""
Epic Document Parser

Parses Epic PRD markdown documents to extract stories, dependencies, and acceptance criteria.
Supports BMAD-standard Epic format.
"""

import re
from pathlib import Path
from typing import Any

from ..workflow.common_enums import Priority
from .models import AcceptanceCriterion, EpicDocument, Story


class EpicParser:
    """
    Parser for Epic markdown documents.

    Supports parsing Epic documents in the format:
    - Epic Goal
    - Epic Description
    - Stories (numbered X.Y)
    - Dependencies
    - Acceptance Criteria
    - Execution Notes
    - Definition of Done
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize Epic parser.

        Args:
            project_root: Root directory of the project (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()

    def parse(self, epic_path: Path | str) -> EpicDocument:
        """
        Parse an Epic document.

        Args:
            epic_path: Path to Epic markdown file

        Returns:
            Parsed EpicDocument

        Raises:
            FileNotFoundError: If Epic file doesn't exist
            ValueError: If parsing fails
        """
        epic_path = Path(epic_path)
        if not epic_path.is_absolute():
            # Try relative to project root, then docs/prd/
            if (self.project_root / epic_path).exists():
                epic_path = self.project_root / epic_path
            elif (self.project_root / "docs" / "prd" / epic_path.name).exists():
                epic_path = self.project_root / "docs" / "prd" / epic_path.name
            else:
                epic_path = self.project_root / epic_path

        if not epic_path.exists():
            raise FileNotFoundError(f"Epic document not found: {epic_path}")

        content = epic_path.read_text(encoding="utf-8")

        # Extract Epic metadata
        epic_number = self._extract_epic_number(content, epic_path)
        title = self._extract_title(content)
        goal = self._extract_goal(content)
        description = self._extract_description(content)
        priority = self._extract_priority(content)
        timeline = self._extract_timeline(content)
        prerequisites = self._extract_prerequisites(content)
        execution_notes = self._extract_execution_notes(content)
        definition_of_done = self._extract_definition_of_done(content)
        status = self._extract_status(content)

        # Extract stories
        stories = self._extract_stories(content, epic_number)

        return EpicDocument(
            epic_number=epic_number,
            title=title,
            goal=goal,
            description=description,
            stories=stories,
            priority=priority,
            timeline=timeline,
            prerequisites=prerequisites,
            execution_notes=execution_notes,
            definition_of_done=definition_of_done,
            status=status,
            file_path=epic_path,
        )

    def _extract_epic_number(self, content: str, file_path: Path) -> int:
        """Extract Epic number from content or filename."""
        # Try to extract from title: "# Epic 8: ..."
        match = re.search(r"^#\s+Epic\s+(\d+):", content, re.MULTILINE)
        if match:
            return int(match.group(1))

        # Try to extract from filename: "epic-8-*.md"
        match = re.search(r"epic-(\d+)", file_path.name, re.IGNORECASE)
        if match:
            return int(match.group(1))

        raise ValueError(f"Could not extract Epic number from {file_path}")

    def _extract_title(self, content: str) -> str:
        """Extract Epic title from content."""
        # Title is usually in the first heading: "# Epic 8: Title"
        match = re.search(r"^#\s+Epic\s+\d+:\s*(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled Epic"

    def _extract_goal(self, content: str) -> str:
        """Extract Epic Goal section."""
        goal_match = re.search(
            r"##\s+Epic\s+Goal\s*\n\n(.+?)(?=\n##|\Z)", content, re.DOTALL
        )
        if goal_match:
            return goal_match.group(1).strip()
        return ""

    def _extract_description(self, content: str) -> str:
        """Extract Epic Description section."""
        desc_match = re.search(
            r"##\s+Epic\s+Description\s*\n\n(.+?)(?=\n##\s+(?:Stories|Execution|Definition)|\Z)",
            content,
            re.DOTALL,
        )
        if desc_match:
            return desc_match.group(1).strip()
        return ""

    def _extract_priority(self, content: str) -> Priority | None:
        """Extract priority from content."""
        # Look for "Priority: High" or similar patterns
        match = re.search(
            r"(?:Priority|priority):\s*(\w+)", content, re.IGNORECASE | re.MULTILINE
        )
        if not match:
            return None
        priority_str = match.group(1).strip().lower()
        try:
            return Priority(priority_str)
        except ValueError:
            # If priority string doesn't match enum, return None
            return None

    def _extract_timeline(self, content: str) -> str | None:
        """Extract timeline from content."""
        # Look for "Timeline: 1-2 weeks" or similar
        match = re.search(
            r"(?:Timeline|timeline):\s*(.+?)(?:\n|$)", content, re.IGNORECASE | re.MULTILINE
        )
        return match.group(1).strip() if match else None

    def _extract_prerequisites(self, content: str) -> list[str]:
        """Extract prerequisites from Execution Notes."""
        prereq_match = re.search(
            r"###\s+Prerequisites\s*\n\n(.+?)(?=\n###|\Z)", content, re.DOTALL | re.IGNORECASE
        )
        if not prereq_match:
            return []

        prereq_text = prereq_match.group(1)
        # Extract list items
        items = re.findall(r"^[-*]\s*(.+)$", prereq_text, re.MULTILINE)
        return [item.strip() for item in items]

    def _extract_execution_notes(self, content: str) -> dict[str, Any]:
        """Extract execution notes section."""
        notes_match = re.search(
            r"##\s+Execution\s+Notes\s*\n\n(.+?)(?=\n##\s+Definition|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if not notes_match:
            return {}

        notes_text = notes_match.group(1)
        notes: dict[str, Any] = {}

        # Extract subsections
        prereq_match = re.search(
            r"###\s+Prerequisites\s*\n\n(.+?)(?=\n###|\Z)", notes_text, re.DOTALL | re.IGNORECASE
        )
        if prereq_match:
            notes["prerequisites"] = prereq_match.group(1).strip()

        tech_match = re.search(
            r"###\s+Technical\s+Decisions\s+Required\s*\n\n(.+?)(?=\n###|\Z)",
            notes_text,
            re.DOTALL | re.IGNORECASE,
        )
        if tech_match:
            notes["technical_decisions"] = tech_match.group(1).strip()

        risk_match = re.search(
            r"###\s+Risk\s+Mitigation\s*\n\n(.+?)(?=\n###|\Z)",
            notes_text,
            re.DOTALL | re.IGNORECASE,
        )
        if risk_match:
            notes["risk_mitigation"] = risk_match.group(1).strip()

        return notes

    def _extract_definition_of_done(self, content: str) -> list[str]:
        """Extract Definition of Done checklist items."""
        dod_match = re.search(
            r"##\s+Definition\s+of\s+Done\s*\n\n(.+?)(?=\n##\s+Status|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if not dod_match:
            return []

        dod_text = dod_match.group(1)
        # Extract checklist items: "- [ ] ..." or "- [x] ..."
        items = re.findall(r"^[-*]\s*\[[ xX]\]\s*(.+)$", dod_text, re.MULTILINE)
        return [item.strip() for item in items]

    def _extract_status(self, content: str) -> str | None:
        """Extract Epic status."""
        # Look for "## Status: ✅ COMPLETE" or similar
        match = re.search(
            r"##\s+Status:\s*(.+?)(?:\n|$)", content, re.IGNORECASE | re.MULTILINE
        )
        return match.group(1).strip() if match else None

    def _extract_stories(self, content: str, epic_number: int) -> list[Story]:
        """Extract all stories from content."""
        stories: list[Story] = []

        # Find Stories section
        stories_match = re.search(
            r"##\s+Stories\s*\n\n(.+?)(?=\n##\s+(?:Execution|Definition)|\Z)",
            content,
            re.DOTALL,
        )
        if not stories_match:
            return stories

        stories_text = stories_match.group(1)

        # Split by numbered stories: "1. **Story X.Y: Title**" or "**Story X.Y: Title**"
        story_pattern = r"(\d+\.\s*\*\*Story\s+(\d+)\.(\d+):\s*(.+?)\*\*|"
        story_pattern += r"\*\*Story\s+(\d+)\.(\d+):\s*(.+?)\*\*)"
        story_pattern += r"(.+?)(?=\d+\.\s*\*\*Story|\*\*Story|\Z)"

        matches = re.finditer(story_pattern, stories_text, re.DOTALL)

        for match in matches:
            # Handle both patterns; body is always group 8: (alt1|alt2)(.+?)
            if match.group(2):  # Pattern 1: "1. **Story X.Y: Title**"
                story_num = int(match.group(3))
                title = match.group(4).strip()
            else:  # Pattern 2: "**Story X.Y: Title**"
                story_num = int(match.group(6))
                title = match.group(7).strip()
            body = match.group(8)

            # Extract description (everything before acceptance criteria)
            desc_match = re.search(
                r"^(.+?)(?=\n\s*-\s*Acceptance\s+criteria:|\n\s*Acceptance\s+criteria:|\Z)",
                body,
                re.DOTALL | re.IGNORECASE,
            )
            description = desc_match.group(1).strip() if desc_match else body.strip()

            # Extract acceptance criteria
            acceptance_criteria = self._extract_acceptance_criteria(body)

            # Extract dependencies (look for "depends on", "requires", etc.)
            dependencies = self._extract_story_dependencies(body, epic_number, story_num)

            # Extract story points if present
            story_points = self._extract_story_points(body)

            story = Story(
                epic_number=epic_number,
                story_number=story_num,
                title=title,
                description=description,
                acceptance_criteria=acceptance_criteria,
                dependencies=dependencies,
                story_points=story_points,
            )

            stories.append(story)

        return stories

    def _extract_acceptance_criteria(self, story_text: str) -> list[AcceptanceCriterion]:
        """Extract acceptance criteria from story text."""
        criteria: list[AcceptanceCriterion] = []

        # Look for "Acceptance criteria:" or "- Acceptance criteria:"
        ac_match = re.search(
            r"(?:Acceptance\s+criteria|Acceptance\s+Criteria):\s*\n(.+?)(?=\n\s*\d+\.|\Z)",
            story_text,
            re.DOTALL | re.IGNORECASE,
        )
        if not ac_match:
            return criteria

        ac_text = ac_match.group(1)

        # Extract list items (lines starting with "-" or numbered)
        items = re.findall(r"^[-*]\s*(.+)$", ac_text, re.MULTILINE)
        for item in items:
            item = item.strip()
            if item:
                criteria.append(AcceptanceCriterion(description=item))

        return criteria

    def _extract_story_dependencies(
        self, story_text: str, epic_number: int, story_number: int
    ) -> list[str]:
        """Extract story dependencies."""
        dependencies: list[str] = []

        # Look for dependency patterns:
        # - "depends on Story X.Y"
        # - "requires Story X.Y"
        # - "prerequisite: Story X.Y"
        # - "Story X.Y must be completed first"
        patterns = [
            r"depends?\s+on\s+Story\s+(\d+)\.(\d+)",
            r"requires?\s+Story\s+(\d+)\.(\d+)",
            r"prerequisite:?\s+Story\s+(\d+)\.(\d+)",
            r"Story\s+(\d+)\.(\d+)\s+must\s+be\s+completed",
            r"after\s+Story\s+(\d+)\.(\d+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, story_text, re.IGNORECASE)
            for match in matches:
                dep_epic = int(match.group(1))
                dep_story = int(match.group(2))
                dep_id = f"{dep_epic}.{dep_story}"
                if dep_id not in dependencies:
                    dependencies.append(dep_id)

        return dependencies

    def _extract_story_points(self, story_text: str) -> int | None:
        """Extract story points if present."""
        # Look for "Story points: 3" or "Points: 5"
        match = re.search(
            r"(?:Story\s+points?|Points?):\s*(\d+)", story_text, re.IGNORECASE
        )
        return int(match.group(1)) if match else None

    def build_dependency_graph(self, epic: EpicDocument) -> dict[str, list[str]]:
        """
        Build dependency graph for stories.

        Returns:
            Dictionary mapping story_id -> list of dependent story_ids
        """
        graph: dict[str, list[str]] = {}

        for story in epic.stories:
            graph[story.story_id] = story.dependencies.copy()

        return graph

    def topological_sort(self, epic: EpicDocument) -> list[Story]:
        """
        Topologically sort stories by dependencies.

        Returns:
            List of stories in execution order (dependencies first)

        Raises:
            ValueError: If circular dependencies detected
        """
        graph = self.build_dependency_graph(epic)
        story_map = {s.story_id: s for s in epic.stories}

        # Kahn's algorithm: in_degree[story] = number of prerequisites
        # graph[story] = deps means story depends on deps, so edges dep->story
        in_degree: dict[str, int] = {
            s.story_id: len(s.dependencies) for s in epic.stories
        }

        # Reverse graph: for each dep, which stories depend on it
        rev_graph: dict[str, list[str]] = {s.story_id: [] for s in epic.stories}
        for story_id, deps in graph.items():
            for dep in deps:
                if dep in rev_graph:
                    rev_graph[dep].append(story_id)

        # Queue: stories with no prerequisites
        queue: list[str] = [sid for sid, degree in in_degree.items() if degree == 0]
        result: list[Story] = []

        while queue:
            story_id = queue.pop(0)
            result.append(story_map[story_id])

            # Decrement in_degree of stories that depended on this one
            for dependent in rev_graph.get(story_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for circular dependencies
        if len(result) != len(epic.stories):
            remaining = set(s.story_id for s in epic.stories) - set(
                s.story_id for s in result
            )
            raise ValueError(
                f"Circular dependencies detected. Stories involved: {', '.join(remaining)}"
            )

        return result

