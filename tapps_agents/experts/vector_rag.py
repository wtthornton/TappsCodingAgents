"""
Vector RAG - FAISS-based semantic search for expert knowledge bases.

Provides semantic search capabilities with automatic fallback to SimpleKnowledgeBase
when vector dependencies are unavailable.
"""

import logging
import time
from pathlib import Path

from .rag_chunker import Chunk, Chunker
from .rag_embedder import Embedder, create_embedder
from .rag_index import VectorIndex
from .rag_safety import create_safety_handler
from .simple_rag import KnowledgeChunk, SimpleKnowledgeBase

logger = logging.getLogger(__name__)

# Try to check if FAISS is available
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class VectorKnowledgeBase:
    """
    FAISS-based vector knowledge base for semantic search.

    Features:
    - Semantic similarity search using embeddings
    - Automatic index building and caching
    - Fallback to SimpleKnowledgeBase if dependencies unavailable
    - Time-bounded queries (<2s target)
    """

    def __init__(
        self,
        knowledge_dir: Path,
        domain: str | None = None,
        chunk_size: int = 512,
        overlap: int = 50,
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.7,
        index_dir: Path | None = None,
    ):
        """
        Initialize vector knowledge base.

        Args:
            knowledge_dir: Directory containing knowledge files (markdown)
            domain: Optional domain filter
            chunk_size: Target tokens per chunk (default: 512)
            overlap: Overlap tokens between chunks (default: 50)
            embedding_model: Sentence-transformers model name
            similarity_threshold: Minimum similarity for results (0.0-1.0)
            index_dir: Optional custom index directory (default: .tapps-agents/rag_index/<domain>)
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.domain = domain
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold

        # Determine index directory
        if index_dir:
            self.index_dir = Path(index_dir)
        else:
            # Default: .tapps-agents/rag_index/<domain> or .tapps-agents/rag_index/general
            base_dir = self.knowledge_dir.parent / ".tapps-agents" / "rag_index"
            self.index_dir = base_dir / (domain or "general")

        # Initialize components
        self.chunker = Chunker(target_tokens=chunk_size, overlap_tokens=overlap)
        self.embedder: Embedder | None = None
        self.index: VectorIndex | None = None
        self.fallback_kb: SimpleKnowledgeBase | None = None

        # Track backend selection
        self._backend_type: str | None = None
        self._initialized = False

        # Initialize safety handler
        self.safety_handler = create_safety_handler(
            enable_injection_detection=True,
            enable_sanitization=True,
            require_citations=True,
        )

    def _initialize(self) -> None:
        """Initialize vector backend or fallback."""
        if self._initialized:
            return

        # Try to initialize vector backend
        if FAISS_AVAILABLE:
            try:
                self.embedder = create_embedder(model_name=self.embedding_model)
                if self.embedder:
                    self._backend_type = "vector"
                    self._build_or_load_index()
                    logger.info(f"Vector RAG initialized: {self.embedding_model}")
                    self._initialized = True
                    return
            except Exception as e:
                logger.warning(f"Failed to initialize vector RAG: {e}. Falling back to SimpleKnowledgeBase.")

        # Fallback to SimpleKnowledgeBase
        self.fallback_kb = SimpleKnowledgeBase(self.knowledge_dir, domain=self.domain)
        self._backend_type = "simple"
        logger.info("Using SimpleKnowledgeBase fallback (vector dependencies unavailable)")
        self._initialized = True

    def _build_or_load_index(self) -> None:
        """Build new index or load existing one."""
        if not self.embedder:
            return

        # Check if index exists and is valid
        if self._index_exists() and self._index_is_valid():
            try:
                self.index = VectorIndex.load(self.index_dir, embedder=self.embedder)
                logger.info(f"Loaded existing index from {self.index_dir}")
                return
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}. Rebuilding...")

        # Build new index
        self._build_index()

    def _index_exists(self) -> bool:
        """Check if index files exist."""
        return (
            (self.index_dir / "index.faiss").exists()
            and (self.index_dir / "chunks.json").exists()
            and (self.index_dir / "metadata.json").exists()
        )

    def _index_is_valid(self) -> bool:
        """Check if existing index is valid (matches current sources)."""
        try:
            import json

            metadata_path = self.index_dir / "metadata.json"
            if not metadata_path.exists():
                return False

            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)

            # Check schema version
            if metadata.get("schema_version") != "1.0":
                return False

            # TODO: Could check source fingerprint for more validation
            return True
        except Exception:
            return False

    def _build_index(self) -> None:
        """Build FAISS index from knowledge files."""
        if not self.embedder:
            return

        logger.info(f"Building vector index from {self.knowledge_dir}...")
        start_time = time.time()

        # Load and chunk all markdown files
        all_chunks: list[Chunk] = []
        for md_file in self.knowledge_dir.rglob("*.md"):
            # Filter by domain if specified
            if self.domain:
                if (
                    self.domain.lower() not in md_file.stem.lower()
                    and self.domain.lower() not in str(md_file).lower()
                ):
                    continue

            try:
                content = md_file.read_text(encoding="utf-8")
                file_chunks = self.chunker.chunk_file(md_file, content)
                all_chunks.extend(file_chunks)
            except Exception as e:
                logger.warning(f"Failed to process {md_file}: {e}")
                continue

        if not all_chunks:
            logger.warning(f"No chunks found in {self.knowledge_dir}")
            return

        # Build index
        self.index = VectorIndex(embedder=self.embedder)
        self.index.build(
            all_chunks,
            chunk_params={
                "target_tokens": self.chunk_size,
                "overlap_tokens": self.overlap,
            },
        )

        # Save index
        self.index.save(self.index_dir)

        elapsed = time.time() - start_time
        logger.info(f"Index built in {elapsed:.2f}s: {len(all_chunks)} chunks")

    def search(
        self, query: str, max_results: int = 5, context_lines: int = 10
    ) -> list[KnowledgeChunk]:
        """
        Search knowledge base for relevant chunks.

        Args:
            query: Search query
            max_results: Maximum number of results
            context_lines: Unused (kept for compatibility with SimpleKnowledgeBase API)

        Returns:
            List of KnowledgeChunk objects (compatible with SimpleKnowledgeBase format)
        """
        self._initialize()

        # Use fallback if vector backend not available
        if self._backend_type == "simple" and self.fallback_kb:
            return self.fallback_kb.search(query, max_results=max_results, context_lines=context_lines)

        # Use vector search
        if not self.index:
            logger.warning("Index not available, falling back to SimpleKnowledgeBase")
            if not self.fallback_kb:
                self.fallback_kb = SimpleKnowledgeBase(self.knowledge_dir, domain=self.domain)
            return self.fallback_kb.search(query, max_results=max_results, context_lines=context_lines)

        # Perform semantic search with timeout
        start_time = time.time()
        try:
            results = self.index.search(
                query_text=query,
                top_k=max_results,
                similarity_threshold=self.similarity_threshold,
            )

            # Convert to KnowledgeChunk format with safety sanitization
            knowledge_chunks: list[KnowledgeChunk] = []
            for chunk, similarity in results:
                # Sanitize retrieved content
                sanitized_content, is_safe = self.safety_handler.sanitize_retrieved_content(
                    chunk.content, str(chunk.source_file)
                )

                # Log warning if unsafe content detected
                if not is_safe:
                    logger.warning(
                        f"Unsafe content detected in chunk from {chunk.source_file}. "
                        "Content has been sanitized."
                    )

                knowledge_chunk = KnowledgeChunk(
                    content=sanitized_content,
                    source_file=chunk.source_file,
                    line_start=chunk.line_start,
                    line_end=chunk.line_end,
                    score=similarity,  # Use similarity as score
                )
                knowledge_chunks.append(knowledge_chunk)

            elapsed = time.time() - start_time
            if elapsed > 2.0:
                logger.warning(f"Query took {elapsed:.2f}s (target: <2s)")

            return knowledge_chunks
        except Exception as e:
            logger.error(f"Vector search failed: {e}. Falling back to SimpleKnowledgeBase.", exc_info=True)
            if not self.fallback_kb:
                self.fallback_kb = SimpleKnowledgeBase(self.knowledge_dir, domain=self.domain)
            return self.fallback_kb.search(query, max_results=max_results, context_lines=context_lines)

    def get_context(self, query: str, max_length: int = 2000) -> str:
        """
        Get formatted context string for a query with safety handling.

        Args:
            query: Search query
            max_length: Maximum character length of context

        Returns:
            Formatted context string with sources and safety labels
        """
        chunks = self.search(query, max_results=5)

        if not chunks:
            return "No relevant knowledge found in knowledge base."

        # Format with safety handler
        chunk_tuples = [
            (chunk.content, chunk.score, str(chunk.source_file)) for chunk in chunks
        ]
        formatted_context, sources, all_safe = self.safety_handler.format_retrieved_context(
            chunk_tuples, max_length=max_length, min_similarity=self.similarity_threshold
        )

        # Add citations if required
        if self.safety_handler.require_citations and sources:
            formatted_context = self.safety_handler.add_citation_headers(
                formatted_context, sources
            )

        return formatted_context

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
            try:
                rel_path = chunk.source_file.relative_to(self.knowledge_dir)
                sources.add(str(rel_path))
            except ValueError:
                sources.add(str(chunk.source_file))

        return list(sources)

    def list_all_files(self) -> list[str]:
        """List all knowledge files in the knowledge base."""
        self._initialize()

        if self._backend_type == "simple" and self.fallback_kb:
            return self.fallback_kb.list_all_files()

        # For vector backend, list from knowledge_dir
        return [
            (
                str(f.relative_to(self.knowledge_dir))
                if self.knowledge_dir in f.parents
                else str(f)
            )
            for f in self.knowledge_dir.rglob("*.md")
        ]

    def get_backend_type(self) -> str:
        """Get the backend type being used ('vector' or 'simple')."""
        self._initialize()
        return self._backend_type or "unknown"
