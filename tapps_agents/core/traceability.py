"""
Traceability Matrix - Links requirements, stories, design, and implementation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class TraceabilityLink:
    """A link between artifacts in the traceability matrix."""

    source_type: str  # "requirement", "story", "design", "implementation"
    source_id: str
    target_type: str
    target_id: str
    link_type: str = "implements"  # "implements", "validates", "depends_on", "refines"
    confidence: float = 1.0  # 0.0-1.0: How certain is this link?


@dataclass
class TraceabilityMatrix:
    """Traceability matrix tracking links between artifacts."""

    links: list[TraceabilityLink] = field(default_factory=list)
    requirements: dict[str, dict[str, Any]] = field(default_factory=dict)
    stories: dict[str, dict[str, Any]] = field(default_factory=dict)
    designs: dict[str, dict[str, Any]] = field(default_factory=dict)
    implementations: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_requirement(self, req_id: str, requirement: dict[str, Any]):
        """Add a requirement to the matrix."""
        self.requirements[req_id] = requirement

    def add_story(self, story_id: str, story: dict[str, Any]):
        """Add a story to the matrix."""
        self.stories[story_id] = story

    def add_design(self, design_id: str, design: dict[str, Any]):
        """Add a design artifact to the matrix."""
        self.designs[design_id] = design

    def add_implementation(self, impl_id: str, implementation: dict[str, Any]):
        """Add an implementation artifact to the matrix."""
        self.implementations[impl_id] = implementation

    def link(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        link_type: str = "implements",
        confidence: float = 1.0,
    ):
        """Create a link between artifacts."""
        link = TraceabilityLink(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            link_type=link_type,
            confidence=confidence,
        )
        self.links.append(link)

    def get_links_from(self, source_type: str, source_id: str) -> list[TraceabilityLink]:
        """Get all links from a source artifact."""
        return [link for link in self.links if link.source_type == source_type and link.source_id == source_id]

    def get_links_to(self, target_type: str, target_id: str) -> list[TraceabilityLink]:
        """Get all links to a target artifact."""
        return [link for link in self.links if link.target_type == target_type and link.target_id == target_id]

    def get_trace_path(self, source_type: str, source_id: str, target_type: str) -> list[TraceabilityLink]:
        """Get trace path from source to target (may be multi-hop)."""
        # Simple implementation: direct links only
        # TODO: Implement multi-hop path finding if needed
        return [
            link
            for link in self.links
            if link.source_type == source_type
            and link.source_id == source_id
            and link.target_type == target_type
        ]

    def find_unlinked_requirements(self) -> list[str]:
        """Find requirements that are not linked to any stories."""
        linked_req_ids = {link.source_id for link in self.links if link.source_type == "requirement"}
        all_req_ids = set(self.requirements.keys())
        return list(all_req_ids - linked_req_ids)

    def find_unlinked_stories(self) -> list[str]:
        """Find stories that are not linked to requirements or designs."""
        linked_story_ids = {link.source_id for link in self.links if link.source_type == "story"}
        linked_story_ids.update({link.target_id for link in self.links if link.target_type == "story"})
        all_story_ids = set(self.stories.keys())
        return list(all_story_ids - linked_story_ids)

    def generate_report(self) -> dict[str, Any]:
        """Generate traceability report."""
        report = {
            "summary": {
                "requirements_count": len(self.requirements),
                "stories_count": len(self.stories),
                "designs_count": len(self.designs),
                "implementations_count": len(self.implementations),
                "links_count": len(self.links),
            },
            "coverage": {
                "requirements_linked": len(self.find_unlinked_requirements()) == 0,
                "stories_linked": len(self.find_unlinked_stories()) == 0,
                "unlinked_requirements": self.find_unlinked_requirements(),
                "unlinked_stories": self.find_unlinked_stories(),
            },
            "links_by_type": {},
        }

        # Count links by type
        for link in self.links:
            link_type = link.link_type
            report["links_by_type"][link_type] = report["links_by_type"].get(link_type, 0) + 1

        return report

    def save(self, file_path: Path):
        """Save traceability matrix to file."""
        data = {
            "requirements": self.requirements,
            "stories": self.stories,
            "designs": self.designs,
            "implementations": self.implementations,
            "links": [
                {
                    "source_type": link.source_type,
                    "source_id": link.source_id,
                    "target_type": link.target_type,
                    "target_id": link.target_id,
                    "link_type": link.link_type,
                    "confidence": link.confidence,
                }
                for link in self.links
            ],
        }

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, file_path: Path) -> "TraceabilityMatrix":
        """Load traceability matrix from file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        matrix = cls()
        matrix.requirements = data.get("requirements", {})
        matrix.stories = data.get("stories", {})
        matrix.designs = data.get("designs", {})
        matrix.implementations = data.get("implementations", {})

        for link_data in data.get("links", []):
            matrix.link(
                source_type=link_data["source_type"],
                source_id=link_data["source_id"],
                target_type=link_data["target_type"],
                target_id=link_data["target_id"],
                link_type=link_data.get("link_type", "implements"),
                confidence=link_data.get("confidence", 1.0),
            )

        return matrix


class TraceabilityManager:
    """Manages traceability across the project."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.matrix_file = self.project_root / ".tapps-agents" / "traceability.yaml"
        self.matrix: TraceabilityMatrix | None = None

    def get_matrix(self) -> TraceabilityMatrix:
        """Get or create traceability matrix."""
        if self.matrix is None:
            if self.matrix_file.exists():
                try:
                    self.matrix = TraceabilityMatrix.load(self.matrix_file)
                except Exception as e:
                    logger.warning(f"Failed to load traceability matrix: {e}. Creating new one.")
                    self.matrix = TraceabilityMatrix()
            else:
                self.matrix = TraceabilityMatrix()

        return self.matrix

    def save_matrix(self):
        """Save traceability matrix to file."""
        if self.matrix:
            self.matrix.save(self.matrix_file)

    def link_requirement_to_story(self, req_id: str, story_id: str, confidence: float = 1.0):
        """Link a requirement to a story."""
        matrix = self.get_matrix()
        matrix.link("requirement", req_id, "story", story_id, "implements", confidence)
        self.save_matrix()

    def link_story_to_design(self, story_id: str, design_id: str, confidence: float = 1.0):
        """Link a story to a design."""
        matrix = self.get_matrix()
        matrix.link("story", story_id, "design", design_id, "implements", confidence)
        self.save_matrix()

    def link_design_to_implementation(self, design_id: str, impl_id: str, confidence: float = 1.0):
        """Link a design to an implementation."""
        matrix = self.get_matrix()
        matrix.link("design", design_id, "implementation", impl_id, "implements", confidence)
        self.save_matrix()

    def get_requirement_trace(self, req_id: str) -> dict[str, Any]:
        """Get full trace for a requirement (requirement → story → design → implementation)."""
        matrix = self.get_matrix()
        trace = {
            "requirement_id": req_id,
            "stories": [],
            "designs": [],
            "implementations": [],
        }

        # Find linked stories
        story_links = matrix.get_links_from("requirement", req_id)
        for link in story_links:
            if link.target_type == "story":
                trace["stories"].append(link.target_id)

                # Find designs linked to these stories
                design_links = matrix.get_links_from("story", link.target_id)
                for design_link in design_links:
                    if design_link.target_type == "design":
                        trace["designs"].append(design_link.target_id)

                        # Find implementations linked to these designs
                        impl_links = matrix.get_links_from("design", design_link.target_id)
                        for impl_link in impl_links:
                            if impl_link.target_type == "implementation":
                                trace["implementations"].append(impl_link.target_id)

        return trace
