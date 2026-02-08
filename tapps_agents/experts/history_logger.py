"""
Expert Consultation History Logger

Tracks expert consultations to JSONL file for debugging and transparency.
Users can see which experts were consulted, when, and why.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ConsultationEntry:
    """Single expert consultation history entry."""

    timestamp: datetime
    expert_id: str
    domain: str
    consulted: bool  # True if consulted, False if skipped
    confidence: float
    reasoning: str  # Why consulted or not consulted
    context_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "expert_id": self.expert_id,
            "domain": self.domain,
            "consulted": self.consulted,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "context_summary": self.context_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsultationEntry:
        """Create from dictionary (JSON deserialization)."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expert_id=data["expert_id"],
            domain=data["domain"],
            consulted=data["consulted"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            context_summary=data.get("context_summary"),
        )


class HistoryLogger:
    """
    Log expert consultations to JSONL file.

    JSONL format allows easy streaming, rotation, and analysis.
    """

    def __init__(self, history_file: Path | None = None):
        """
        Initialize history logger.

        Args:
            history_file: Path to history file. If None, uses default
                         .tapps-agents/expert-history.jsonl
        """
        if history_file is None:
            history_file = Path.cwd() / ".tapps-agents" / "expert-history.jsonl"

        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def log_consultation(
        self,
        expert_id: str,
        domain: str,
        consulted: bool,
        confidence: float,
        reasoning: str,
        context_summary: str | None = None,
    ):
        """
        Log expert consultation.

        Args:
            expert_id: Expert ID
            domain: Domain that triggered consultation
            consulted: True if consulted, False if skipped
            confidence: Confidence score
            reasoning: Why consulted or not consulted
            context_summary: Optional context summary
        """
        entry = ConsultationEntry(
            timestamp=datetime.now(),
            expert_id=expert_id,
            domain=domain,
            consulted=consulted,
            confidence=confidence,
            reasoning=reasoning,
            context_summary=context_summary,
        )

        self._append_entry(entry)

    def _append_entry(self, entry: ConsultationEntry):
        """Append entry to JSONL file."""
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def get_recent(self, limit: int = 10) -> list[ConsultationEntry]:
        """
        Get recent consultation entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent entries, newest first
        """
        if not self.history_file.exists():
            return []

        entries = []
        with open(self.history_file, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entry = ConsultationEntry.from_dict(data)
                    entries.append(entry)
                except Exception:
                    continue  # Skip malformed entries

        # Return newest first
        entries.reverse()
        return entries[:limit]

    def get_by_expert(self, expert_id: str, limit: int = 10) -> list[ConsultationEntry]:
        """
        Get consultation history for specific expert.

        Args:
            expert_id: Expert ID
            limit: Maximum number of entries to return

        Returns:
            List of entries for expert, newest first
        """
        if not self.history_file.exists():
            return []

        entries = []
        with open(self.history_file, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data["expert_id"] == expert_id:
                        entry = ConsultationEntry.from_dict(data)
                        entries.append(entry)
                except Exception:
                    continue

        entries.reverse()
        return entries[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get consultation statistics.

        Returns:
            Dictionary with consultation statistics
        """
        if not self.history_file.exists():
            return {
                "total_consultations": 0,
                "consulted_count": 0,
                "skipped_count": 0,
                "experts": {},
            }

        total = 0
        consulted = 0
        skipped = 0
        expert_counts: dict[str, int] = {}

        with open(self.history_file, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    total += 1

                    if data["consulted"]:
                        consulted += 1
                    else:
                        skipped += 1

                    expert_id = data["expert_id"]
                    expert_counts[expert_id] = expert_counts.get(expert_id, 0) + 1
                except Exception:
                    continue

        return {
            "total_consultations": total,
            "consulted_count": consulted,
            "skipped_count": skipped,
            "experts": expert_counts,
        }

    def export_to_json(self, output_file: Path):
        """
        Export history to JSON file (not JSONL).

        Args:
            output_file: Path to output JSON file
        """
        if not self.history_file.exists():
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            return

        entries = []
        with open(self.history_file, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entries.append(data)
                except Exception:
                    continue

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)

    def rotate(self, keep_recent: int = 1000):
        """
        Rotate history file, keeping only recent entries.

        Args:
            keep_recent: Number of recent entries to keep
        """
        if not self.history_file.exists():
            return

        entries = self.get_recent(limit=keep_recent)

        # Write to temporary file
        temp_file = self.history_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            for entry in reversed(entries):  # Reverse to restore chronological order
                f.write(json.dumps(entry.to_dict()) + "\n")

        # Replace original file
        temp_file.replace(self.history_file)


class HistoryFormatter:
    """Format consultation history for display."""

    @staticmethod
    def format_entry(entry: ConsultationEntry) -> str:
        """Format single entry for display."""
        status = "✅ CONSULTED" if entry.consulted else "⏭️  SKIPPED"
        return f"""
[{entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")}] {status}
Expert: {entry.expert_id}
Domain: {entry.domain}
Confidence: {entry.confidence:.2f}
Reasoning: {entry.reasoning}
""".strip()

    @staticmethod
    def format_list(entries: list[ConsultationEntry]) -> str:
        """Format list of entries for display."""
        if not entries:
            return "No consultation history found."

        lines = ["=" * 70]
        lines.append("EXPERT CONSULTATION HISTORY")
        lines.append("=" * 70)

        for entry in entries:
            lines.append("")
            lines.append(HistoryFormatter.format_entry(entry))
            lines.append("-" * 70)

        return "\n".join(lines)

    @staticmethod
    def format_statistics(stats: dict[str, Any]) -> str:
        """Format statistics for display."""
        lines = ["=" * 70]
        lines.append("EXPERT CONSULTATION STATISTICS")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Total Consultations: {stats['total_consultations']}")
        lines.append(f"Consulted: {stats['consulted_count']}")
        lines.append(f"Skipped: {stats['skipped_count']}")
        lines.append("")
        lines.append("By Expert:")
        lines.append("-" * 70)

        # Sort experts by consultation count
        experts = sorted(
            stats["experts"].items(), key=lambda x: x[1], reverse=True
        )
        for expert_id, count in experts:
            lines.append(f"  {expert_id}: {count}")

        lines.append("=" * 70)

        return "\n".join(lines)
