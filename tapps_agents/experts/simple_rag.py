"""
Simple File-Based RAG System for Industry Experts

Provides knowledge retrieval from markdown files in a knowledge/ directory
using keyword search and context extraction. No vector DB required.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass
from collections import defaultdict


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
    
    def __init__(self, knowledge_dir: Path, domain: Optional[str] = None):
        """
        Initialize knowledge base.
        
        Args:
            knowledge_dir: Directory containing knowledge files (markdown)
            domain: Optional domain filter (only load files matching domain)
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.domain = domain
        self.files: Dict[Path, str] = {}  # Cache of loaded files
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
                if self.domain.lower() not in md_file.stem.lower() and \
                   self.domain.lower() not in str(md_file).lower():
                    continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                self.files[md_file] = content
            except Exception:
                # Skip files that can't be read
                continue
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        context_lines: int = 10
    ) -> List[KnowledgeChunk]:
        """
        Search knowledge base for relevant chunks.
        
        Args:
            query: Search query (keywords)
            max_results: Maximum number of chunks to return
            context_lines: Number of lines of context around matches
        
        Returns:
            List of KnowledgeChunk objects sorted by relevance
        """
        query_lower = query.lower()
        query_keywords = set(word.lower() for word in query_lower.split() if len(word) > 2)
        
        chunks: List[KnowledgeChunk] = []
        
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
        self,
        file_path: Path,
        content: str,
        query_keywords: set,
        context_lines: int
    ) -> List[KnowledgeChunk]:
        """
        Extract relevant chunks from a file based on keyword matches.
        
        Uses markdown-aware chunking (respects headers, paragraphs).
        """
        lines = content.split('\n')
        chunks: List[KnowledgeChunk] = []
        
        # Score each line by keyword matches
        line_scores: Dict[int, float] = {}
        for i, line in enumerate(lines):
            line_lower = line.lower()
            score = sum(1.0 for keyword in query_keywords if keyword in line_lower)
            # Boost score for headers (marked by #)
            if line.strip().startswith('#'):
                score *= 1.5
            if score > 0:
                line_scores[i] = score
        
        if not line_scores:
            return chunks  # No matches
        
        # Group consecutive high-scoring lines into chunks
        current_chunk_start: Optional[int] = None
        current_chunk_lines: List[int] = []
        
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
                        file_path, lines, current_chunk_start,
                        current_chunk_lines[-1], context_lines, query_keywords
                    )
                    if chunk:
                        chunks.append(chunk)
                
                current_chunk_start = i
                current_chunk_lines = [i]
        
        # Add final chunk
        if current_chunk_start is not None:
            chunk = self._create_chunk_from_lines(
                file_path, lines, current_chunk_start,
                current_chunk_lines[-1], context_lines, query_keywords
            )
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_from_lines(
        self,
        file_path: Path,
        lines: List[str],
        start_line: int,
        end_line: int,
        context_lines: int,
        query_keywords: set
    ) -> Optional[KnowledgeChunk]:
        """Create a KnowledgeChunk from line range with context."""
        # Expand range with context
        actual_start = max(0, start_line - context_lines)
        actual_end = min(len(lines), end_line + context_lines)
        
        # Try to align to markdown boundaries (headers)
        for i in range(actual_start, start_line):
            if lines[i].strip().startswith('#'):
                actual_start = i
                break
        
        # Extract chunk content
        chunk_lines = lines[actual_start:actual_end]
        content = '\n'.join(chunk_lines).strip()
        
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
            score=score
        )
    
    def get_context(
        self,
        query: str,
        max_length: int = 2000
    ) -> str:
        """
        Get formatted context string for a query.
        
        Args:
            query: Search query
            max_length: Maximum character length of context
        
        Returns:
            Formatted context string with sources
        """
        chunks = self.search(query, max_results=5)
        
        if not chunks:
            return "No relevant knowledge found in knowledge base."
        
        context_parts = []
        current_length = 0
        
        for chunk in chunks:
            chunk_text = f"[From: {chunk.source_file.name}]\n{chunk.content}\n"
            
            if current_length + len(chunk_text) > max_length:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n---\n".join(context_parts)
    
    def get_sources(
        self,
        query: str,
        max_results: int = 5
    ) -> List[str]:
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
    
    def list_all_files(self) -> List[str]:
        """List all knowledge files in the knowledge base."""
        return [str(f.relative_to(self.knowledge_dir)) if self.knowledge_dir in f.parents else str(f)
                for f in self.files.keys()]

