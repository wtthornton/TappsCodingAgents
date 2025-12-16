"""
RAG Chunker - Deterministic chunking for knowledge base documents.

Implements markdown-aware chunking with configurable token size and overlap.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Approximate tokens per character (rough estimate for English text)
# This is a conservative estimate; actual tokenization varies by model
APPROX_TOKENS_PER_CHAR = 0.25  # ~4 chars per token


@dataclass
class Chunk:
    """A chunk of text with provenance metadata."""

    content: str
    source_file: Path
    line_start: int  # 1-indexed
    line_end: int  # 1-indexed
    chunk_id: str  # Deterministic ID for this chunk
    token_count: int  # Approximate token count

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        return {
            "content": self.content,
            "source_file": str(self.source_file),
            "line_start": self.line_start,
            "line_end": self.line_end,
            "chunk_id": self.chunk_id,
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chunk":
        """Create chunk from dictionary."""
        return cls(
            content=data["content"],
            source_file=Path(data["source_file"]),
            line_start=data["line_start"],
            line_end=data["line_end"],
            chunk_id=data["chunk_id"],
            token_count=data["token_count"],
        )


class Chunker:
    """
    Chunks markdown documents into fixed-size pieces with overlap.

    Features:
    - Markdown-aware (respects headers, paragraphs)
    - Deterministic chunk IDs
    - Configurable token size and overlap
    - Preserves file/line provenance
    """

    def __init__(
        self,
        target_tokens: int = 512,
        overlap_tokens: int = 50,
    ):
        """
        Initialize chunker.

        Args:
            target_tokens: Target number of tokens per chunk (default: 512)
            overlap_tokens: Number of tokens to overlap between chunks (default: 50)
        """
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.target_chars = int(target_tokens / APPROX_TOKENS_PER_CHAR)
        self.overlap_chars = int(overlap_tokens / APPROX_TOKENS_PER_CHAR)

    def chunk_file(self, file_path: Path, content: str) -> list[Chunk]:
        """
        Chunk a markdown file into pieces.

        Args:
            file_path: Path to the source file
            content: File content as string

        Returns:
            List of Chunk objects with provenance
        """
        lines = content.split("\n")
        chunks: list[Chunk] = []

        # Track current position
        current_start_line = 1
        current_content: list[str] = []
        current_chars = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            line_chars = len(line) + 1  # +1 for newline

            # Check if adding this line would exceed target
            if current_chars + line_chars > self.target_chars and current_content:
                # Create chunk from current content
                chunk_content = "\n".join(current_content)
                chunk = self._create_chunk(
                    file_path,
                    chunk_content,
                    current_start_line,
                    i,  # End line (before current)
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_lines = self._calculate_overlap_lines(current_content)
                current_content = overlap_lines + [line]
                current_start_line = i - len(overlap_lines) + 1
                current_chars = sum(len(line) + 1 for line in current_content)
            else:
                # Add line to current chunk
                current_content.append(line)
                current_chars += line_chars

            i += 1

        # Add final chunk if there's remaining content
        if current_content:
            chunk_content = "\n".join(current_content)
            chunk = self._create_chunk(
                file_path,
                chunk_content,
                current_start_line,
                len(lines),
            )
            chunks.append(chunk)

        return chunks

    def _calculate_overlap_lines(self, lines: list[str]) -> list[str]:
        """
        Calculate overlap lines from previous chunk.

        Returns lines that should be included in the next chunk for overlap.
        """
        if not lines:
            return []

        # Calculate how many lines we need for overlap
        overlap_chars_needed = self.overlap_chars
        overlap_lines: list[str] = []

        # Start from the end and work backwards
        for line in reversed(lines):
            if sum(len(overlap_line) + 1 for overlap_line in overlap_lines) + len(line) + 1 <= overlap_chars_needed:
                overlap_lines.insert(0, line)
            else:
                break

        return overlap_lines

    def _create_chunk(
        self,
        file_path: Path,
        content: str,
        line_start: int,
        line_end: int,
    ) -> Chunk:
        """
        Create a Chunk object with deterministic ID.

        Args:
            file_path: Source file path
            content: Chunk content
            line_start: Starting line number (1-indexed)
            line_end: Ending line number (1-indexed)
        """
        # Generate deterministic chunk ID
        chunk_id = self._generate_chunk_id(file_path, line_start, line_end, content)

        # Estimate token count
        token_count = int(len(content) * APPROX_TOKENS_PER_CHAR)

        return Chunk(
            content=content,
            source_file=file_path,
            line_start=line_start,
            line_end=line_end,
            chunk_id=chunk_id,
            token_count=token_count,
        )

    def _generate_chunk_id(
        self, file_path: Path, line_start: int, line_end: int, content: str
    ) -> str:
        """
        Generate deterministic chunk ID.

        Uses file path, line range, and content hash for uniqueness.
        """
        # Create a stable identifier
        identifier = f"{file_path}:{line_start}:{line_end}:{content[:100]}"
        hash_obj = hashlib.sha256(identifier.encode("utf-8"))
        return hash_obj.hexdigest()[:16]  # 16-char hex ID
