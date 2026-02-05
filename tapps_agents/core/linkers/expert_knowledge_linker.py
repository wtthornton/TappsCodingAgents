"""Expert-Knowledge Linker Module.

Links knowledge files to appropriate experts and identifies orphan knowledge files.

This module follows modular design principles:
- Small, focused functions (< 100 lines)
- Clear separation of concerns
- Single responsibility principle
- Easy to test and maintain

Phase: 3.2 - Expert-Knowledge Linking
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


@dataclass
class OrphanFile:
    """Represents an orphan knowledge file not linked to any expert."""

    filepath: Path
    domain: Optional[str] = None
    topic: Optional[str] = None
    suggested_experts: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class LinkingResult:
    """Results from expert-knowledge linking analysis."""

    total_knowledge_files: int = 0
    linked_files: int = 0
    orphan_files: List[OrphanFile] = field(default_factory=list)
    experts_analyzed: int = 0
    suggestions: Dict[str, List[str]] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class ExpertKnowledgeLinker:
    """Links knowledge files to experts and finds orphans.

    This class provides modular functionality for:
    1. Loading expert configurations
    2. Scanning knowledge base files
    3. Finding orphan files (not linked to any expert)
    4. Suggesting knowledge_files additions

    Design: Each method has a single responsibility and is < 100 lines.
    """

    def __init__(
        self,
        project_root: Path,
        knowledge_base_dir: Optional[Path] = None,
        experts_file: Optional[Path] = None,
    ):
        """Initialize the expert-knowledge linker.

        Args:
            project_root: Project root directory
            knowledge_base_dir: Knowledge base directory (defaults to .tapps-agents/knowledge)
            experts_file: Experts configuration file (defaults to .tapps-agents/experts.yaml)
        """
        self.project_root = Path(project_root)
        self.knowledge_base_dir = knowledge_base_dir or self.project_root / ".tapps-agents" / "knowledge"
        self.experts_file = experts_file or self.project_root / ".tapps-agents" / "experts.yaml"

        self.experts: Dict[str, Dict] = {}
        self.linked_files: Set[Path] = set()

    def load_experts(self) -> Dict[str, Dict]:
        """Load expert configurations from experts.yaml.

        Returns:
            Dictionary mapping expert IDs to expert configurations

        Raises:
            FileNotFoundError: If experts.yaml doesn't exist
            ValueError: If experts.yaml is invalid
        """
        if not self.experts_file.exists():
            raise FileNotFoundError(f"Experts file not found: {self.experts_file}")

        try:
            with open(self.experts_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            experts_list = data.get('experts', [])
            if not isinstance(experts_list, list):
                raise ValueError("'experts' must be a list in experts.yaml")

            # Create mapping of expert_id -> expert_config
            experts_map = {}
            for expert in experts_list:
                if isinstance(expert, dict) and 'expert_id' in expert:
                    expert_id = expert['expert_id']
                    experts_map[expert_id] = expert

            self.experts = experts_map
            return experts_map

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in experts file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load experts: {e}")

    def get_linked_knowledge_files(self) -> Set[Path]:
        """Get all knowledge files currently linked to experts.

        Returns:
            Set of knowledge file paths that are referenced by experts
        """
        linked = set()

        for expert in self.experts.values():
            knowledge_files = expert.get('knowledge_files', [])

            for kf_path in knowledge_files:
                # Resolve relative to project root
                if not isinstance(kf_path, (str, Path)):
                    continue

                full_path = self.project_root / kf_path

                # Normalize path
                try:
                    normalized = full_path.resolve()
                    if normalized.exists():
                        linked.add(normalized)
                except (OSError, ValueError):
                    # Skip invalid paths
                    continue

        self.linked_files = linked
        return linked

    def scan_knowledge_base(self) -> List[Path]:
        """Scan knowledge base directory for all markdown files.

        Returns:
            List of knowledge file paths found
        """
        if not self.knowledge_base_dir.exists():
            logger.warning(f"Knowledge base directory not found: {self.knowledge_base_dir}")
            return []

        # Find all markdown files, excluding README.md
        markdown_files = []
        for md_file in self.knowledge_base_dir.rglob("*.md"):
            if md_file.name.lower() != "readme.md":
                markdown_files.append(md_file.resolve())

        return markdown_files

    def find_orphan_files(self) -> List[OrphanFile]:
        """Find knowledge files not linked to any expert.

        Returns:
            List of OrphanFile objects representing unlinked knowledge files
        """
        all_knowledge_files = self.scan_knowledge_base()
        linked_files = self.get_linked_knowledge_files()

        orphans = []

        for kf_path in all_knowledge_files:
            if kf_path not in linked_files:
                # Extract domain and topic from path
                domain, topic = self._extract_domain_topic(kf_path)

                # Suggest potential experts
                suggested_experts = self._suggest_experts_for_file(kf_path, domain, topic)

                orphan = OrphanFile(
                    filepath=kf_path,
                    domain=domain,
                    topic=topic,
                    suggested_experts=suggested_experts,
                    reason="Not referenced by any expert's knowledge_files"
                )
                orphans.append(orphan)

        return orphans

    def _extract_domain_topic(self, filepath: Path) -> tuple[Optional[str], Optional[str]]:
        """Extract domain and topic from knowledge file path.

        Args:
            filepath: Path to knowledge file

        Returns:
            Tuple of (domain, topic) extracted from path structure
        """
        try:
            relative = filepath.relative_to(self.knowledge_base_dir)
            parts = list(relative.parts)

            # Domain is the first directory level
            domain = parts[0] if len(parts) > 1 else None

            # Topic is the filename without extension
            topic = filepath.stem if filepath.stem else None

            return domain, topic

        except (ValueError, IndexError):
            return None, None

    def _suggest_experts_for_file(
        self,
        filepath: Path,
        domain: Optional[str],
        topic: Optional[str]
    ) -> List[str]:
        """Suggest experts that might match this knowledge file.

        Args:
            filepath: Path to knowledge file
            domain: Extracted domain
            topic: Extracted topic

        Returns:
            List of expert IDs that might be relevant for this file
        """
        suggestions = []

        if not domain and not topic:
            return suggestions

        # Match by domain
        for expert_id, expert_config in self.experts.items():
            primary_domain = expert_config.get('primary_domain', '')
            expert_name = expert_config.get('expert_name', '')

            # Exact domain match
            if domain and domain.lower() == primary_domain.lower():
                suggestions.append(expert_id)
                continue

            # Topic in expert name
            if topic and topic.lower() in expert_name.lower():
                suggestions.append(expert_id)
                continue

            # Domain in expert name
            if domain and domain.lower() in expert_name.lower():
                suggestions.append(expert_id)

        return suggestions

    def suggest_knowledge_file_additions(self) -> Dict[str, List[str]]:
        """Suggest knowledge_files to add to each expert.

        Returns:
            Dictionary mapping expert_id to list of suggested knowledge file paths
        """
        orphans = self.find_orphan_files()
        suggestions: Dict[str, List[str]] = {}

        for orphan in orphans:
            for expert_id in orphan.suggested_experts:
                if expert_id not in suggestions:
                    suggestions[expert_id] = []

                # Convert to relative path from project root
                try:
                    relative_path = orphan.filepath.relative_to(self.project_root)
                    suggestions[expert_id].append(str(relative_path))
                except ValueError:
                    # If path is not relative to project root, use absolute
                    suggestions[expert_id].append(str(orphan.filepath))

        return suggestions

    def analyze(self) -> LinkingResult:
        """Perform complete expert-knowledge linking analysis.

        Returns:
            LinkingResult with analysis results
        """
        try:
            # Load experts
            self.load_experts()

            # Scan knowledge base
            all_files = self.scan_knowledge_base()

            # Get linked files
            linked_files = self.get_linked_knowledge_files()

            # Find orphans
            orphans = self.find_orphan_files()

            # Generate suggestions
            suggestions = self.suggest_knowledge_file_additions()

            return LinkingResult(
                total_knowledge_files=len(all_files),
                linked_files=len(linked_files),
                orphan_files=orphans,
                experts_analyzed=len(self.experts),
                suggestions=suggestions,
                success=True,
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return LinkingResult(
                success=False,
                error=str(e),
            )


def main():
    """CLI entry point for expert-knowledge linker."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Link knowledge files to experts and find orphans"
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Create linker
    linker = ExpertKnowledgeLinker(args.project_root)

    # Run analysis
    result = linker.analyze()

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.format == "json":
        import json
        output = {
            "total_knowledge_files": result.total_knowledge_files,
            "linked_files": result.linked_files,
            "orphan_count": len(result.orphan_files),
            "orphan_files": [
                {
                    "filepath": str(o.filepath),
                    "domain": o.domain,
                    "topic": o.topic,
                    "suggested_experts": o.suggested_experts,
                    "reason": o.reason,
                }
                for o in result.orphan_files
            ],
            "suggestions": result.suggestions,
        }
        print(json.dumps(output, indent=2))
    else:
        # Text format
        print(f"\n=== Expert-Knowledge Linking Analysis ===")
        print(f"Total knowledge files: {result.total_knowledge_files}")
        print(f"Linked files: {result.linked_files}")
        print(f"Orphan files: {len(result.orphan_files)}")
        print(f"Experts analyzed: {result.experts_analyzed}")

        if result.orphan_files:
            print(f"\n--- Orphan Knowledge Files ---")
            for orphan in result.orphan_files:
                print(f"\n{orphan.filepath}")
                print(f"  Domain: {orphan.domain or 'Unknown'}")
                print(f"  Topic: {orphan.topic or 'Unknown'}")
                if orphan.suggested_experts:
                    print(f"  Suggested experts: {', '.join(orphan.suggested_experts)}")
                else:
                    print(f"  No expert suggestions")

        if result.suggestions:
            print(f"\n--- Suggestions for Experts ---")
            for expert_id, files in result.suggestions.items():
                print(f"\n{expert_id}:")
                for filepath in files:
                    print(f"  + {filepath}")


if __name__ == "__main__":
    main()
