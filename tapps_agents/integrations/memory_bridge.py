"""
Memory Bridge - Ingest Clawdbot workspace files into TappsCodingAgents knowledge base.

This module bridges Clawdbot's workspace files (MEMORY.md, USER.md, daily notes)
into the TappsCodingAgents expert knowledge system, creating a "user preferences"
domain that persists learned patterns.

Features:
- Ingests MEMORY.md, USER.md, SOUL.md, AGENTS.md
- Ingests daily notes from memory/*.md
- Creates "user-preferences" domain with extracted patterns
- Updates automatically when files change

Usage:
    from tapps_agents.integrations.memory_bridge import MemoryBridge
    
    bridge = MemoryBridge(
        workspace_root="/path/to/clawd",
        project_root="/path/to/project"
    )
    
    # Sync all workspace files to knowledge base
    await bridge.sync_all()
    
    # Query user preferences
    results = await bridge.query_preferences("How does the user prefer error handling?")
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceFile:
    """A workspace file to be ingested."""
    path: Path
    category: str  # identity, preferences, context, daily
    last_hash: str | None = None


@dataclass 
class IngestResult:
    """Result of ingesting workspace files."""
    files_processed: int
    files_updated: int
    patterns_extracted: int
    knowledge_entries_created: int
    errors: list[str]


class MemoryBridge:
    """
    Bridge between Clawdbot workspace files and TappsCodingAgents knowledge base.
    
    Creates a "user-preferences" domain that learns from:
    - MEMORY.md: Long-term memories and lessons
    - USER.md: User information and context
    - SOUL.md: Persona and behavior guidelines
    - AGENTS.md: Workspace conventions
    - memory/*.md: Daily notes and context
    """
    
    # Files to track in workspace
    WORKSPACE_FILES = {
        "MEMORY.md": "preferences",
        "USER.md": "identity", 
        "SOUL.md": "identity",
        "AGENTS.md": "context",
        "TOOLS.md": "context",
        "IDENTITY.md": "identity",
    }
    
    # Patterns to extract from files
    PREFERENCE_PATTERNS = [
        r"(?:prefers?|likes?|wants?|should|always|never|don't)\s+(.+?)(?:\.|$)",
        r"(?:important|note|remember|key):\s*(.+?)(?:\.|$)",
        r"##\s*(?:Preferences|Rules|Guidelines|Conventions)\s*\n([\s\S]*?)(?=\n##|\Z)",
    ]
    
    def __init__(
        self,
        workspace_root: Path | str | None = None,
        project_root: Path | str | None = None,
    ):
        """
        Initialize Memory Bridge.
        
        Args:
            workspace_root: Root of Clawdbot workspace (where MEMORY.md lives)
            project_root: Root of project with .tapps-agents/ directory
        """
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.project_root = Path(project_root) if project_root else self.workspace_root
        
        self.config_dir = self.project_root / ".tapps-agents"
        self.knowledge_dir = self.config_dir / "knowledge" / "user-preferences"
        self.state_file = self.config_dir / "memory_bridge_state.json"
        
        # Ensure directories exist
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Load state (tracks file hashes to detect changes)
        self._state = self._load_state()
    
    def _load_state(self) -> dict[str, Any]:
        """Load bridge state from disk."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Error loading state: {e}")
        return {"file_hashes": {}, "last_sync": None}
    
    def _save_state(self) -> None:
        """Save bridge state to disk."""
        self._state["last_sync"] = datetime.now().isoformat()
        self.state_file.write_text(
            json.dumps(self._state, indent=2),
            encoding="utf-8"
        )
    
    def _get_file_hash(self, path: Path) -> str:
        """Get hash of file contents."""
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8", errors="ignore")
        return hashlib.md5(content.encode()).hexdigest()
    
    def _file_changed(self, path: Path) -> bool:
        """Check if file has changed since last sync."""
        current_hash = self._get_file_hash(path)
        stored_hash = self._state["file_hashes"].get(str(path), "")
        return current_hash != stored_hash
    
    async def sync_all(self, force: bool = False) -> IngestResult:
        """
        Sync all workspace files to knowledge base.
        
        Args:
            force: If True, re-process all files even if unchanged
            
        Returns:
            IngestResult with processing statistics
        """
        result = IngestResult(
            files_processed=0,
            files_updated=0,
            patterns_extracted=0,
            knowledge_entries_created=0,
            errors=[]
        )
        
        # Process static workspace files
        for filename, category in self.WORKSPACE_FILES.items():
            file_path = self.workspace_root / filename
            if file_path.exists():
                try:
                    if force or self._file_changed(file_path):
                        entries = await self._ingest_file(file_path, category)
                        result.knowledge_entries_created += entries
                        result.files_updated += 1
                        
                        # Update hash
                        self._state["file_hashes"][str(file_path)] = self._get_file_hash(file_path)
                    
                    result.files_processed += 1
                except Exception as e:
                    result.errors.append(f"Error processing {filename}: {e}")
                    logger.error(f"Error processing {filename}: {e}")
        
        # Process daily notes
        memory_dir = self.workspace_root / "memory"
        if memory_dir.exists():
            for note_file in memory_dir.glob("*.md"):
                try:
                    if force or self._file_changed(note_file):
                        entries = await self._ingest_file(note_file, "daily")
                        result.knowledge_entries_created += entries
                        result.files_updated += 1
                        
                        self._state["file_hashes"][str(note_file)] = self._get_file_hash(note_file)
                    
                    result.files_processed += 1
                except Exception as e:
                    result.errors.append(f"Error processing {note_file.name}: {e}")
        
        # Extract patterns from all ingested content
        patterns = self._extract_patterns()
        result.patterns_extracted = len(patterns)
        
        # Create summary knowledge file
        await self._create_summary(patterns)
        
        # Save state
        self._save_state()
        
        return result
    
    async def _ingest_file(self, path: Path, category: str) -> int:
        """
        Ingest a single file into knowledge base.
        
        Returns number of knowledge entries created.
        """
        content = path.read_text(encoding="utf-8", errors="ignore")
        
        # Create knowledge file for this source
        kb_filename = f"{category}_{path.stem}.md"
        kb_path = self.knowledge_dir / kb_filename
        
        # Format for knowledge base
        knowledge_content = f"""# {path.name} (auto-ingested)

**Source:** {path}
**Category:** {category}
**Last Updated:** {datetime.now().isoformat()}

---

{content}
"""
        
        kb_path.write_text(knowledge_content, encoding="utf-8")
        logger.info(f"Ingested {path.name} → {kb_filename}")
        
        return 1
    
    def _extract_patterns(self) -> list[str]:
        """Extract preference patterns from all knowledge files."""
        patterns = []
        
        for kb_file in self.knowledge_dir.glob("*.md"):
            content = kb_file.read_text(encoding="utf-8", errors="ignore")
            
            for pattern in self.PREFERENCE_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if isinstance(match, str) and len(match.strip()) > 10:
                        patterns.append(match.strip())
        
        # Deduplicate
        return list(set(patterns))
    
    async def _create_summary(self, patterns: list[str]) -> None:
        """Create a summary knowledge file with extracted patterns."""
        summary_path = self.knowledge_dir / "_summary.md"
        
        content = f"""# User Preferences Summary

**Auto-generated:** {datetime.now().isoformat()}
**Patterns Extracted:** {len(patterns)}

This file summarizes preferences and patterns extracted from the Clawdbot workspace.

## Extracted Patterns

"""
        
        for i, pattern in enumerate(patterns[:50], 1):  # Limit to 50
            content += f"{i}. {pattern}\n"
        
        content += """

## Usage

When consulting this domain, consider:
- Code style preferences
- Communication preferences  
- Project conventions
- Personal context

This knowledge is automatically updated when workspace files change.
"""
        
        summary_path.write_text(content, encoding="utf-8")
    
    async def query_preferences(self, question: str, top_k: int = 3) -> list[dict[str, Any]]:
        """
        Query the user preferences knowledge base.
        
        Args:
            question: Question to search for
            top_k: Number of results to return
            
        Returns:
            List of relevant knowledge chunks
        """
        from ..experts.simple_rag import SimpleKnowledgeBase
        
        if not self.knowledge_dir.exists():
            return []
        
        kb = SimpleKnowledgeBase(self.knowledge_dir)
        chunks = kb.search(question, max_results=top_k)
        
        return [
            {
                "content": chunk.content,
                "source": chunk.source,
                "score": getattr(chunk, "score", 0.0)
            }
            for chunk in chunks
        ]
    
    def get_user_context(self) -> dict[str, Any]:
        """
        Get structured user context from workspace files.
        
        Returns:
            Dictionary with user info, preferences, etc.
        """
        context = {
            "user": {},
            "preferences": [],
            "conventions": [],
            "identity": {}
        }
        
        # Parse USER.md
        user_file = self.workspace_root / "USER.md"
        if user_file.exists():
            content = user_file.read_text(encoding="utf-8", errors="ignore")
            
            # Extract key-value pairs (handles "- **Key:** Value" format)
            for line in content.split("\n"):
                if "**" in line and line.strip().startswith("- **"):
                    match = re.match(r"-\s*\*\*([^*]+)\*\*:?\s*(.+)", line)
                    if match:
                        key = match.group(1).rstrip(":").lower().replace(" ", "_")
                        value = match.group(2).strip()
                        context["user"][key] = value
        
        # Parse IDENTITY.md
        identity_file = self.workspace_root / "IDENTITY.md"
        if identity_file.exists():
            content = identity_file.read_text(encoding="utf-8", errors="ignore")
            
            for line in content.split("\n"):
                if "**" in line and line.strip().startswith("- **"):
                    match = re.match(r"-\s*\*\*([^*]+)\*\*:?\s*(.+)", line)
                    if match:
                        key = match.group(1).rstrip(":").lower().replace(" ", "_")
                        value = match.group(2).strip()
                        context["identity"][key] = value
        
        return context
