"""
Knowledge Ingestion Pipeline

Automatically populates project KB from multiple sources:
- Project sources (requirements, architecture docs, ADRs, runbooks, SDLC reports)
- Context7 dependency sources (auto-fetch library docs)
- Operational sources (CI failures, runtime exceptions, monitoring alerts)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .domain_detector import DomainStackDetector
from .governance import GovernanceLayer, GovernancePolicy
from .simple_rag import KnowledgeChunk, SimpleKnowledgeBase
from .vector_rag import VectorKnowledgeBase

if TYPE_CHECKING:
    from ..context7.agent_integration import Context7AgentHelper


@dataclass
class IngestionResult:
    """Result of knowledge ingestion operation."""

    source_type: str  # project, context7, operational
    entries_ingested: int
    entries_failed: int
    errors: list[str] = field(default_factory=list)


@dataclass
class KnowledgeEntry:
    """A knowledge entry to be ingested."""

    title: str
    content: str
    domain: str
    source: str  # Source file or identifier
    source_type: str  # project, context7, operational
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeIngestionPipeline:
    """
    Pipeline for ingesting knowledge from multiple sources.

    Automatically populates project KB from:
    - Project documentation (requirements, architecture, ADRs, runbooks)
    - Context7 library documentation (auto-fetched on dependency detection)
    - Operational sources (CI failures, exceptions, alerts)
    """

    # Project source patterns
    PROJECT_SOURCE_PATTERNS = {
        "requirements": ["requirements*.txt", "requirements*.yaml", "requirements*.yml"],
        "architecture": ["docs/**/architecture*.md", "docs/**/arch*.md", "ARCHITECTURE.md"],
        "adr": ["docs/adr/**/*.md", "docs/decisions/**/*.md", "adr/**/*.md"],
        "runbook": ["docs/runbook*.md", "runbooks/**/*.md", "docs/ops/**/*.md"],
        "sdlc_report": [".tapps-agents/reports/**/*.md", "reports/**/*.md"],
        "lessons_learned": ["docs/lessons*.md", "docs/learnings*.md"],
    }

    def __init__(
        self,
        project_root: Path,
        context7_helper: Context7AgentHelper | None = None,
        governance_policy: GovernancePolicy | None = None,
    ):
        """
        Initialize Knowledge Ingestion Pipeline.

        Args:
            project_root: Project root directory
            context7_helper: Optional Context7 helper for library docs
            governance_policy: Optional governance policy configuration
        """
        self.project_root = project_root
        self.config_dir = project_root / ".tapps-agents"
        self.knowledge_base_dir = self.config_dir / "knowledge"
        self.context7_helper = context7_helper
        self.domain_detector = DomainStackDetector(project_root=project_root)
        
        # Initialize governance layer (Story 28.5)
        if governance_policy is None:
            governance_policy = GovernancePolicy()
        self.governance = GovernanceLayer(policy=governance_policy)

    async def ingest_all_sources(
        self, include_context7: bool = True, include_operational: bool = True
    ) -> dict[str, IngestionResult]:
        """
        Ingest knowledge from all available sources.

        Args:
            include_context7: Whether to ingest Context7 library docs
            include_operational: Whether to ingest operational sources

        Returns:
            Dictionary mapping source types to ingestion results
        """
        results = {}

        # Ingest project sources
        project_result = self.ingest_project_sources()
        results["project"] = project_result

        # Ingest Context7 sources
        if include_context7 and self.context7_helper:
            context7_result = await self.ingest_context7_sources()
            results["context7"] = context7_result

        # Ingest operational sources
        if include_operational:
            operational_result = self.ingest_operational_sources()
            results["operational"] = operational_result

        return results

    def ingest_project_sources(self) -> IngestionResult:
        """Ingest knowledge from project documentation sources."""
        entries_ingested = 0
        entries_failed = 0
        errors = []

        # Detect stack to determine relevant domains
        detection_result = self.domain_detector.detect_stack()
        domains = [dm.domain for dm in detection_result.domains]

        # Ingest each source type
        for source_type, patterns in self.PROJECT_SOURCE_PATTERNS.items():
            try:
                entries = self._ingest_source_type(source_type, patterns, domains)
                entries_ingested += len(entries)
                self._store_knowledge_entries(entries)
            except Exception as e:
                entries_failed += 1
                errors.append(f"{source_type}: {e!s}")

        return IngestionResult(
            source_type="project",
            entries_ingested=entries_ingested,
            entries_failed=entries_failed,
            errors=errors,
        )

    def _ingest_source_type(
        self, source_type: str, patterns: list[str], domains: list[str]
    ) -> list[KnowledgeEntry]:
        """Ingest knowledge from a specific source type."""
        entries = []

        # Find matching files
        for pattern in patterns:
            if "**" in pattern:
                # Recursive glob
                for path in self.project_root.rglob(pattern.replace("**/", "")):
                    if path.is_file():
                        entries.extend(self._parse_source_file(path, source_type, domains))
            else:
                # Simple glob
                for path in self.project_root.glob(pattern):
                    if path.is_file():
                        entries.extend(self._parse_source_file(path, source_type, domains))

        return entries

    def _parse_source_file(
        self, file_path: Path, source_type: str, domains: list[str]
    ) -> list[KnowledgeEntry]:
        """Parse a source file and extract knowledge entries."""
        entries = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Determine domain (use first matching domain or "general")
            domain = domains[0] if domains else "general"

            # Extract title from filename or content
            title = self._extract_title(file_path, content)

            # Create knowledge entry
            entry = KnowledgeEntry(
                title=title,
                content=content,
                domain=domain,
                source=str(file_path.relative_to(self.project_root)),
                source_type="project",
                metadata={
                    "file_type": source_type,
                    "file_path": str(file_path),
                    "ingested_at": datetime.now().isoformat(),
                },
            )

            entries.append(entry)
        except Exception as e:
            # Log error but continue
            print(f"Error parsing {file_path}: {e}")

        return entries

    def _extract_title(self, file_path: Path, content: str) -> str:
        """Extract title from file path or content."""
        # Try to extract from markdown header
        header_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if header_match:
            return header_match.group(1).strip()

        # Use filename as fallback
        return file_path.stem.replace("_", " ").replace("-", " ").title()

    async def ingest_context7_sources(self) -> IngestionResult:
        """Ingest knowledge from Context7 library documentation."""
        if not self.context7_helper:
            return IngestionResult(
                source_type="context7",
                entries_ingested=0,
                entries_failed=0,
                errors=["Context7 helper not available"],
            )

        entries_ingested = 0
        entries_failed = 0
        errors = []

        # Detect dependencies
        detection_result = self.domain_detector.detect_stack()
        dependencies = self._extract_dependencies(detection_result)

        # Fetch Context7 docs for each dependency
        for library in dependencies:
            try:
                # Fetch overview
                overview = await self.context7_helper.get_documentation(library, topic=None)
                if overview:
                    entry = self._create_context7_entry(
                        library, "overview", overview.get("content", "")
                    )
                    self._store_knowledge_entries([entry])
                    entries_ingested += 1

                # Fetch patterns
                patterns = await self.context7_helper.get_documentation(library, topic="patterns")
                if patterns:
                    entry = self._create_context7_entry(
                        library, "patterns", patterns.get("content", "")
                    )
                    self._store_knowledge_entries([entry])
                    entries_ingested += 1

                # Fetch pitfalls
                pitfalls = await self.context7_helper.get_documentation(library, topic="pitfalls")
                if pitfalls:
                    entry = self._create_context7_entry(
                        library, "pitfalls", pitfalls.get("content", "")
                    )
                    self._store_knowledge_entries([entry])
                    entries_ingested += 1

                # Fetch security notes
                security = await self.context7_helper.get_documentation(library, topic="security")
                if security:
                    entry = self._create_context7_entry(
                        library, "security", security.get("content", "")
                    )
                    self._store_knowledge_entries([entry])
                    entries_ingested += 1

            except Exception as e:
                entries_failed += 1
                errors.append(f"{library}: {e!s}")

        return IngestionResult(
            source_type="context7",
            entries_ingested=entries_ingested,
            entries_failed=entries_failed,
            errors=errors,
        )

    def _extract_dependencies(self, detection_result) -> list[str]:
        """Extract library dependencies from detection result."""
        dependencies = []

        # Extract from dependency signals
        for signal in detection_result.signals:
            if signal.signal_type == "dependency":
                # Try to extract library name from signal value
                if isinstance(signal.value, str):
                    # Parse common dependency formats
                    lib_name = signal.value.split("==")[0].split("@")[0].strip()
                    if lib_name:
                        dependencies.append(lib_name)

        return list(set(dependencies))  # Remove duplicates

    def _create_context7_entry(
        self, library: str, topic: str, content: str
    ) -> KnowledgeEntry:
        """Create knowledge entry from Context7 documentation."""
        # Distill Context7 content into project-specific format
        distilled_content = self._distill_context7_content(library, topic, content)

        return KnowledgeEntry(
            title=f"{library} - {topic}",
            content=distilled_content,
            domain=library.lower().replace("-", "_"),
            source=f"context7://{library}/{topic}",
            source_type="context7",
            metadata={
                "library": library,
                "topic": topic,
                "ingested_at": datetime.now().isoformat(),
            },
        )

    def _distill_context7_content(self, library: str, topic: str, content: str) -> str:
        """Distill Context7 content into project-specific knowledge."""
        # Create "how we use X here" format
        distilled = f"# How We Use {library} - {topic}\n\n"
        distilled += f"## Overview\n\n{content}\n\n"
        distilled += "## Project-Specific Notes\n\n"
        distilled += "_Add project-specific patterns and usage here_\n"

        return distilled

    def ingest_operational_sources(self) -> IngestionResult:
        """Ingest knowledge from operational sources (CI failures, exceptions, alerts)."""
        entries_ingested = 0
        entries_failed = 0
        errors = []

        # Look for operational sources
        operational_sources = [
            self.project_root / ".github" / "workflows",
            self.project_root / ".gitlab-ci.yml",
            self.config_dir / "reports",
        ]

        for source_path in operational_sources:
            if not source_path.exists():
                continue

            try:
                entries = self._parse_operational_source(source_path)
                entries_ingested += len(entries)
                self._store_knowledge_entries(entries)
            except Exception as e:
                entries_failed += 1
                errors.append(f"{source_path}: {e!s}")

        return IngestionResult(
            source_type="operational",
            entries_ingested=entries_ingested,
            entries_failed=entries_failed,
            errors=errors,
        )

    def _parse_operational_source(self, source_path: Path) -> list[KnowledgeEntry]:
        """Parse operational source and extract known issues."""
        entries = []

        # This is a simplified implementation
        # In practice, would parse CI logs, exception traces, monitoring alerts
        # and convert to structured KB entries

        return entries

    def _store_knowledge_entries(self, entries: list[KnowledgeEntry]):
        """Store knowledge entries in appropriate KB backends with governance checks."""
        # Group entries by domain
        entries_by_domain: dict[str, list[KnowledgeEntry]] = {}
        for entry in entries:
            if entry.domain not in entries_by_domain:
                entries_by_domain[entry.domain] = []
            entries_by_domain[entry.domain].append(entry)

        # Store in domain-specific knowledge bases
        for domain, domain_entries in entries_by_domain.items():
            domain_kb_dir = self.knowledge_base_dir / domain
            domain_kb_dir.mkdir(parents=True, exist_ok=True)

            # Try VectorKnowledgeBase first, fallback to SimpleKnowledgeBase
            try:
                _kb = VectorKnowledgeBase(knowledge_dir=domain_kb_dir, domain=domain)
            except Exception:
                _kb = SimpleKnowledgeBase(knowledge_dir=domain_kb_dir, domain=domain)

            # Convert entries to knowledge chunks and add with governance checks
            # Note: KB is created but currently using markdown file fallback
            for entry in domain_entries:
                # Apply governance layer (Story 28.5)
                # 1. Filter content for secrets/PII
                filter_result = self.governance.filter_content(entry.content, entry.source)
                
                # 2. Use filtered content if available
                if filter_result.filtered_content:
                    entry.content = filter_result.filtered_content
                
                # 3. Validate entry against governance policies
                is_valid, reason = self.governance.validate_knowledge_entry(entry)
                
                if not is_valid:
                    # Entry failed validation - log and skip
                    print(f"Governance validation failed for {entry.title}: {reason}")
                    continue
                
                # 4. Entry passed all checks - store it
                _chunk = KnowledgeChunk(
                    content=entry.content,
                    metadata={
                        "title": entry.title,
                        "source": entry.source,
                        "source_type": entry.source_type,
                        **entry.metadata,
                    },
                )
                # Add to knowledge base (implementation depends on KB backend)
                # For now, write to markdown files
                # TODO: Use _kb.add_chunk(_chunk) when KB backend is fully implemented
                self._write_knowledge_file(domain_kb_dir, entry)

    def _write_knowledge_file(self, domain_dir: Path, entry: KnowledgeEntry):
        """Write knowledge entry to markdown file."""
        # Sanitize title for filename
        safe_title = re.sub(r"[^\w\s-]", "", entry.title).strip().replace(" ", "_")
        filename = f"{safe_title}.md"

        # Write content
        file_path = domain_dir / filename
        file_path.write_text(entry.content, encoding="utf-8")

