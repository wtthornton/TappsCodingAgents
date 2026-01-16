"""
Simple File-Based RAG System for Industry Experts

Provides knowledge retrieval from markdown files in a knowledge/ directory
using keyword search and context extraction. No vector DB required.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge from a knowledge base file."""

    content: str
    source_file: Path
    line_start: int
    line_end: int
    score: float = 0.0  # Relevance score (0.0-1.0)


class SimpleKnowledgeBase:
    """
    Simple file-based knowledge base for RAG.

    Features:
    - Keyword search in markdown files
    - Context extraction around matches
    - File-based storage (no vector DB)
    - Markdown-aware chunking
    """

    def __init__(self, knowledge_dir: Path, domain: str | None = None):
        """
        Initialize knowledge base.

        Args:
            knowledge_dir: Directory containing knowledge files (markdown)
            domain: Optional domain filter (only load files matching domain)
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.domain = domain
        self.files: dict[Path, str] = {}  # Cache of loaded files
        self._load_knowledge_files()

    def _load_knowledge_files(self):
        """Load all markdown files from knowledge directory."""
        if not self.knowledge_dir.exists():
            return  # No knowledge base directory

        # Load .md files
        for md_file in self.knowledge_dir.rglob("*.md"):
            # Filter by domain if specified
            if self.domain:
                # Check if file path or name contains domain
                if (
                    self.domain.lower() not in md_file.stem.lower()
                    and self.domain.lower() not in str(md_file).lower()
                ):
                    continue

            try:
                content = md_file.read_text(encoding="utf-8")
                self.files[md_file] = content
            except Exception:
                # Skip files that can't be read
                logger.debug("Failed to read knowledge file %s", md_file, exc_info=True)
                continue  # nosec B112 - best-effort load

    def _normalize_query(self, query: str) -> set[str]:
        """
        Normalize query by removing stop words, stemming, and extracting keywords.
        
        Args:
            query: Raw query string
            
        Returns:
            Set of normalized keywords
        """
        # Common stop words (technical domain focused)
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "what", "how", "why", "when", "where", "which", "who"
        }
        
        # Normalize: lowercase, remove punctuation, split
        query_lower = query.lower()
        # Remove punctuation except hyphens (for compound terms)
        query_clean = re.sub(r'[^\w\s-]', ' ', query_lower)
        words = query_clean.split()
        
        # Filter: remove stop words and short words
        keywords = {
            word.lower() for word in words 
            if len(word) > 2 and word.lower() not in stop_words
        }
        
        return keywords

    def search(
        self, query: str, max_results: int = 5, context_lines: int = 10
    ) -> list[KnowledgeChunk]:
        """
        Search knowledge base for relevant chunks.

        Args:
            query: Search query (keywords)
            max_results: Maximum number of chunks to return
            context_lines: Number of lines of context around matches

        Returns:
            List of KnowledgeChunk objects sorted by relevance
        """
        query_keywords = self._normalize_query(query)

        chunks: list[KnowledgeChunk] = []

        for file_path, content in self.files.items():
            file_chunks = self._extract_relevant_chunks(
                file_path, content, query_keywords, context_lines
            )
            chunks.extend(file_chunks)

        # Sort by score (highest first)
        chunks.sort(key=lambda c: c.score, reverse=True)

        # Return top results
        return chunks[:max_results]

    def _extract_relevant_chunks(
        self, file_path: Path, content: str, query_keywords: set, context_lines: int
    ) -> list[KnowledgeChunk]:
        """
        Extract relevant chunks from a file based on keyword matches.

        Uses markdown-aware chunking (respects headers, paragraphs).
        """
        lines = content.split("\n")
        chunks: list[KnowledgeChunk] = []

        # Score each line by keyword matches with improved scoring
        line_scores: dict[int, float] = {}
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Base score: count keyword matches
            base_score = sum(1.0 for keyword in query_keywords if keyword in line_lower)
            
            # Boost for exact phrase matches (consecutive keywords)
            if len(query_keywords) > 1:
                query_phrase = " ".join(sorted(query_keywords))
                if query_phrase in line_lower or any(
                    keyword1 in line_lower and keyword2 in line_lower
                    for keyword1 in query_keywords
                    for keyword2 in query_keywords
                    if keyword1 != keyword2
                ):
                    base_score *= 1.3
            
            # Boost score for headers (marked by #)
            header_boost = 1.0
            if line.strip().startswith("#"):
                # H1 gets highest boost, H2 less, etc.
                header_level = len(line) - len(line.lstrip("#"))
                header_boost = 2.0 - (header_level * 0.2)
            
            # Boost for code blocks (examples are valuable)
            if line.strip().startswith("```"):
                base_score *= 1.4
            
            # Boost for lines with lists (structured information)
            if line.strip().startswith("- ") or line.strip().startswith("* "):
                base_score *= 1.2
            
            score = base_score * header_boost
            
            if score > 0:
                line_scores[i] = score

        if not line_scores:
            return chunks  # No matches

        # Group consecutive high-scoring lines into chunks
        current_chunk_start: int | None = None
        current_chunk_lines: list[int] = []

        for i in sorted(line_scores.keys()):
            if current_chunk_start is None:
                current_chunk_start = i
                current_chunk_lines = [i]
            elif i - current_chunk_lines[-1] <= context_lines:
                # Within context distance, add to current chunk
                current_chunk_lines.append(i)
            else:
                # New chunk needed
                if current_chunk_start is not None:
                    chunk = self._create_chunk_from_lines(
                        file_path,
                        lines,
                        current_chunk_start,
                        current_chunk_lines[-1],
                        context_lines,
                        query_keywords,
                    )
                    if chunk:
                        chunks.append(chunk)

                current_chunk_start = i
                current_chunk_lines = [i]

        # Add final chunk
        if current_chunk_start is not None:
            chunk = self._create_chunk_from_lines(
                file_path,
                lines,
                current_chunk_start,
                current_chunk_lines[-1],
                context_lines,
                query_keywords,
            )
            if chunk:
                chunks.append(chunk)

        return chunks

    def _create_chunk_from_lines(
        self,
        file_path: Path,
        lines: list[str],
        start_line: int,
        end_line: int,
        context_lines: int,
        query_keywords: set,
    ) -> KnowledgeChunk | None:
        """Create a KnowledgeChunk from line range with context."""
        # Expand range with context
        actual_start = max(0, start_line - context_lines)
        actual_end = min(len(lines), end_line + context_lines)

        # Try to align to markdown boundaries (headers)
        for i in range(actual_start, start_line):
            if lines[i].strip().startswith("#"):
                actual_start = i
                break

        # Extract chunk content
        chunk_lines = lines[actual_start:actual_end]
        content = "\n".join(chunk_lines).strip()

        if not content:
            return None

        # Calculate relevance score
        content_lower = content.lower()
        matches = sum(1.0 for keyword in query_keywords if keyword in content_lower)
        score = matches / len(query_keywords) if query_keywords else 0.0

        return KnowledgeChunk(
            content=content,
            source_file=file_path,
            line_start=actual_start + 1,  # 1-indexed
            line_end=actual_end,
            score=score,
        )

    def get_context(self, query: str, max_length: int = 2000) -> str:
        """
        Get formatted context string for a query with deduplication and prioritization.

        Args:
            query: Search query
            max_length: Maximum character length of context

        Returns:
            Formatted context string with sources
        """
        chunks = self.search(query, max_results=10)  # Get more chunks for better selection

        if not chunks:
            return "No relevant knowledge found in knowledge base."

        # Deduplicate: Remove chunks with very similar content
        unique_chunks = self._deduplicate_chunks(chunks)
        
        # Prioritize: Sort by score, then by source file importance
        prioritized_chunks = self._prioritize_chunks(unique_chunks)

        context_parts = []
        current_length = 0
        seen_sources = set()

        for chunk in prioritized_chunks:
            # Skip if we've seen this source file (avoid redundancy)
            source_key = str(chunk.source_file)
            if source_key in seen_sources:
                # Only allow multiple chunks from same file if they're significantly different
                continue
            
            chunk_text = f"[From: {chunk.source_file.name}] (score: {chunk.score:.2f})\n{chunk.content}\n"

            if current_length + len(chunk_text) > max_length:
                # Try to include partial chunk if it fits
                remaining = max_length - current_length
                if remaining > 200:  # Only include if meaningful portion remains
                    chunk_text = chunk_text[:remaining] + "..."
                    context_parts.append(chunk_text)
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)
            seen_sources.add(source_key)

        if not context_parts:
            return "No relevant knowledge found in knowledge base."

        return "\n---\n".join(context_parts)

    def _deduplicate_chunks(self, chunks: list[KnowledgeChunk], similarity_threshold: float = 0.8) -> list[KnowledgeChunk]:
        """
        Remove duplicate or very similar chunks.
        
        Args:
            chunks: List of chunks to deduplicate
            similarity_threshold: Threshold for considering chunks similar (0.0-1.0)
            
        Returns:
            Deduplicated list of chunks
        """
        if not chunks:
            return chunks
            
        unique_chunks: list[KnowledgeChunk] = [chunks[0]]
        
        for chunk in chunks[1:]:
            is_duplicate = False
            chunk_content = chunk.content.lower().strip()
            
            for existing_chunk in unique_chunks:
                existing_content = existing_chunk.content.lower().strip()
                
                # Simple similarity check: check if one content is mostly contained in the other
                if len(chunk_content) > 0 and len(existing_content) > 0:
                    if chunk_content in existing_content or existing_content in chunk_content:
                        is_duplicate = True
                        break
                    # Check word overlap (simple Jaccard similarity)
                    chunk_words = set(chunk_content.split())
                    existing_words = set(existing_content.split())
                    if chunk_words and existing_words:
                        overlap = len(chunk_words & existing_words)
                        union = len(chunk_words | existing_words)
                        similarity = overlap / union if union > 0 else 0.0
                        if similarity > similarity_threshold:
                            is_duplicate = True
                            break
            
            if not is_duplicate:
                unique_chunks.append(chunk)
        
        return unique_chunks

    def _prioritize_chunks(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        """
        Prioritize chunks by score and source importance.
        
        Args:
            chunks: List of chunks to prioritize
            
        Returns:
            Prioritized list of chunks (sorted by importance)
        """
        # Sort by score (already done in search), but also consider:
        # - Chunks from files with better names (containing keywords)
        # - Higher-scoring chunks first
        # - Shorter chunks (more focused) get slight boost
        
        def priority_key(chunk: KnowledgeChunk) -> tuple:
            # Primary: score (higher is better, so negate)
            # Secondary: prefer shorter, focused chunks (but not too short)
            content_length = len(chunk.content)
            length_score = 1.0 / max(content_length / 500, 1.0)  # Prefer 200-500 char chunks
            
            return (-chunk.score, -length_score)
        
        return sorted(chunks, key=priority_key)

    def get_sources(self, query: str, max_results: int = 5) -> list[str]:
        """
        Get source file paths for a query.

        Args:
            query: Search query
            max_results: Maximum number of sources to return

        Returns:
            List of source file paths (relative to knowledge_dir)
        """
        chunks = self.search(query, max_results=max_results)

        # Get unique source files
        sources = set()
        for chunk in chunks:
            # Return relative path from knowledge_dir
            try:
                rel_path = chunk.source_file.relative_to(self.knowledge_dir)
                sources.add(str(rel_path))
            except ValueError:
                # File not in knowledge_dir, use absolute path
                sources.add(str(chunk.source_file))

        return list(sources)

    def list_all_files(self) -> list[str]:
        """List all knowledge files in the knowledge base."""
        return [
            (
                str(f.relative_to(self.knowledge_dir))
                if self.knowledge_dir in f.parents
                else str(f)
            )
            for f in self.files.keys()
        ]
