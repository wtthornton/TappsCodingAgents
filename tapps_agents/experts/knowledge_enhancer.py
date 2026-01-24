"""
Knowledge Enhancer

Automatically enhances expert knowledge bases based on usage patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeGap:
    """Identified knowledge gap."""

    expert_id: str
    domain: str
    query: str
    confidence: float
    gap_type: str  # "low_confidence", "missing_pattern", "outdated"
    suggested_content: str | None = None


@dataclass
class KnowledgeUpdate:
    """Knowledge base update."""

    expert_id: str
    file_path: Path
    content: str
    update_type: str  # "new_file", "append", "replace_section"
    confidence: float


class KnowledgeEnhancer:
    """
    Enhances expert knowledge based on usage patterns.
    
    Identifies gaps from low-confidence consultations and successful
    patterns, then generates knowledge updates.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize knowledge enhancer.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.knowledge_base_dir = self.project_root / ".tapps-agents" / "knowledge"

    async def enhance_knowledge(
        self,
        expert_id: str,
        gaps: list[KnowledgeGap],
        successful_patterns: list[dict] | None = None,
    ) -> list[KnowledgeUpdate]:
        """
        Enhance knowledge base for an expert.

        Args:
            expert_id: Expert identifier
            gaps: List of identified knowledge gaps
            successful_patterns: List of successful patterns to incorporate

        Returns:
            List of KnowledgeUpdate objects
        """
        updates = []

        # Get expert domain
        domain = self._get_expert_domain(expert_id)
        if not domain:
            logger.warning(f"Could not determine domain for expert {expert_id}")
            return updates

        knowledge_dir = self.knowledge_base_dir / domain
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Process gaps
        for gap in gaps:
            if gap.expert_id != expert_id:
                continue

            update = await self._process_gap(gap, knowledge_dir)
            if update:
                updates.append(update)

        # Process successful patterns
        if successful_patterns:
            pattern_updates = await self._process_successful_patterns(
                expert_id, domain, successful_patterns, knowledge_dir
            )
            updates.extend(pattern_updates)

        # Validate updates
        validated_updates = [
            update for update in updates if self._validate_update(update)
        ]

        return validated_updates

    async def _process_gap(
        self, gap: KnowledgeGap, knowledge_dir: Path
    ) -> KnowledgeUpdate | None:
        """Process a knowledge gap and generate update."""
        # Determine update type based on gap type
        if gap.gap_type == "low_confidence":
            # Create or update a knowledge file with this query/pattern
            filename = self._generate_filename_from_query(gap.query)
            file_path = knowledge_dir / filename

            content = self._generate_content_from_gap(gap)

            return KnowledgeUpdate(
                expert_id=gap.expert_id,
                file_path=file_path,
                content=content,
                update_type="new_file" if not file_path.exists() else "append",
                confidence=1.0 - gap.confidence,  # Higher gap = higher confidence in need
            )

        return None

    async def _process_successful_patterns(
        self,
        expert_id: str,
        domain: str,
        patterns: list[dict],
        knowledge_dir: Path,
    ) -> list[KnowledgeUpdate]:
        """Process successful patterns and generate updates."""
        updates = []

        # Group patterns by topic
        pattern_groups: dict[str, list[dict]] = {}
        for pattern in patterns:
            topic = pattern.get("topic", "general")
            if topic not in pattern_groups:
                pattern_groups[topic] = []
            pattern_groups[topic].append(pattern)

        # Create/update knowledge files for each topic
        for topic, topic_patterns in pattern_groups.items():
            filename = f"{topic}-patterns.md"
            file_path = knowledge_dir / filename

            content = self._generate_content_from_patterns(topic, topic_patterns)

            updates.append(
                KnowledgeUpdate(
                    expert_id=expert_id,
                    file_path=file_path,
                    content=content,
                    update_type="new_file" if not file_path.exists() else "append",
                    confidence=0.8,  # High confidence for successful patterns
                )
            )

        return updates

    def _get_expert_domain(self, expert_id: str) -> str | None:
        """Get primary domain for expert."""
        experts_file = self.project_root / ".tapps-agents" / "experts.yaml"
        if not experts_file.exists():
            return None

        try:
            import yaml

            with open(experts_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                experts = data.get("experts", [])
                for expert in experts:
                    if expert.get("expert_id") == expert_id:
                        return expert.get("primary_domain")
        except Exception:
            pass

        return None

    def _generate_filename_from_query(self, query: str) -> str:
        """Generate filename from query text."""
        # Extract key terms and create filename
        words = query.lower().split()[:3]  # First 3 words
        filename = "-".join(words) + ".md"
        # Sanitize filename
        filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
        return filename

    def _generate_content_from_gap(self, gap: KnowledgeGap) -> str:
        """Generate knowledge content from gap."""
        return f"""# Knowledge Gap: {gap.query}

**Domain:** {gap.domain}
**Confidence Gap:** {1.0 - gap.confidence:.0%}
**Type:** {gap.gap_type}

## Query

{gap.query}

## Suggested Content

{gap.suggested_content or "Content to be populated based on successful patterns"}

## Notes

This knowledge was auto-generated to address a confidence gap.
Consider reviewing and enhancing with domain-specific expertise.
"""

    def _generate_content_from_patterns(
        self, topic: str, patterns: list[dict]
    ) -> str:
        """Generate knowledge content from successful patterns."""
        lines = [f"# {topic.title()} Patterns", "", "**Auto-generated from successful patterns**", ""]

        for i, pattern in enumerate(patterns, 1):
            lines.append(f"## Pattern {i}")
            lines.append("")
            if "description" in pattern:
                lines.append(pattern["description"])
            if "code" in pattern:
                lines.append("```python")
                lines.append(pattern["code"])
                lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def _validate_update(self, update: KnowledgeUpdate) -> bool:
        """Validate knowledge update before applying."""
        # Check file path is within knowledge base
        try:
            update.file_path.resolve().relative_to(self.knowledge_base_dir.resolve())
        except ValueError:
            logger.warning(f"Invalid file path: {update.file_path}")
            return False

        # Check content is not empty
        if not update.content or not update.content.strip():
            logger.warning("Empty content in update")
            return False

        return True

    def apply_update(self, update: KnowledgeUpdate) -> bool:
        """
        Apply knowledge update to file system.

        Args:
            update: KnowledgeUpdate to apply

        Returns:
            True if successful, False otherwise
        """
        if not self._validate_update(update):
            return False

        try:
            if update.update_type == "new_file":
                update.file_path.write_text(update.content, encoding="utf-8")
            elif update.update_type == "append":
                with open(update.file_path, "a", encoding="utf-8") as f:
                    f.write("\n\n" + update.content)
            elif update.update_type == "replace_section":
                # More complex - would need to parse and replace specific sections
                logger.warning("replace_section not yet implemented")
                return False

            logger.info(f"Applied knowledge update: {update.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            return False
