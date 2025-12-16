"""
RAG Index - FAISS-based vector index for semantic search.

Provides indexing and querying capabilities for knowledge base chunks.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import FAISS (optional dependency)
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None  # type: ignore

from .rag_chunker import Chunk
from .rag_embedder import Embedder

# Schema version for index metadata
INDEX_SCHEMA_VERSION = "1.0"


@dataclass
class IndexMetadata:
    """Metadata for a FAISS index."""

    schema_version: str = INDEX_SCHEMA_VERSION
    model_name: str = ""
    embedding_dim: int = 0
    chunk_count: int = 0
    chunk_params: dict[str, Any] = field(default_factory=dict)
    source_files: list[str] = field(default_factory=list)
    source_fingerprint: str = ""  # Hash of source file set

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "schema_version": self.schema_version,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "chunk_count": self.chunk_count,
            "chunk_params": self.chunk_params,
            "source_files": self.source_files,
            "source_fingerprint": self.source_fingerprint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexMetadata":
        """Create metadata from dictionary."""
        return cls(
            schema_version=data.get("schema_version", INDEX_SCHEMA_VERSION),
            model_name=data.get("model_name", ""),
            embedding_dim=data.get("embedding_dim", 0),
            chunk_count=data.get("chunk_count", 0),
            chunk_params=data.get("chunk_params", {}),
            source_files=data.get("source_files", []),
            source_fingerprint=data.get("source_fingerprint", ""),
        )


class VectorIndex:
    """
    FAISS-based vector index for semantic search.

    Provides:
    - Index building from chunks and embeddings
    - Persistent storage to disk
    - Loading from disk
    - Semantic similarity search
    """

    def __init__(self, embedder: Embedder | None = None):
        """
        Initialize vector index.

        Args:
            embedder: Embedder instance (required for building new indexes)
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS is not installed. "
                "Install it with: pip install faiss-cpu (or faiss-gpu)"
            )

        self.embedder = embedder
        self.index: Any | None = None  # FAISS index
        self.chunks: list[Chunk] = []
        self.metadata: IndexMetadata | None = None

    def build(
        self,
        chunks: list[Chunk],
        chunk_params: dict[str, Any] | None = None,
    ) -> None:
        """
        Build index from chunks.

        Args:
            chunks: List of chunks to index
            chunk_params: Optional parameters used for chunking (for metadata)
        """
        if not self.embedder:
            raise ValueError("Embedder is required for building index")

        if not chunks:
            raise ValueError("Cannot build index from empty chunk list")

        logger.info(f"Building FAISS index from {len(chunks)} chunks...")

        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed(texts)

        if not embeddings:
            raise ValueError("Failed to generate embeddings")

        embedding_dim = len(embeddings[0])
        num_chunks = len(embeddings)

        # Create FAISS index (L2 distance index, normalized for cosine similarity)
        # Since embeddings are normalized, L2 distance = 2 - 2*cosine_similarity
        self.index = faiss.IndexFlatL2(embedding_dim)

        # Convert embeddings to numpy array
        import numpy as np

        embeddings_array = np.array(embeddings, dtype="float32")
        self.index.add(embeddings_array)

        # Store chunks and metadata
        self.chunks = chunks
        self.metadata = IndexMetadata(
            model_name=self.embedder.get_model_name(),
            embedding_dim=embedding_dim,
            chunk_count=num_chunks,
            chunk_params=chunk_params or {},
            source_files=list(set(str(c.source_file) for c in chunks)),
            source_fingerprint=self._calculate_source_fingerprint(chunks),
        )

        logger.info(f"Index built successfully: {num_chunks} chunks, dim={embedding_dim}")

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[tuple[Chunk, float]]:
        """
        Search index for similar chunks.

        Args:
            query_text: Query text to search for
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of (Chunk, similarity_score) tuples, sorted by similarity (highest first)
        """
        if not self.index or not self.embedder:
            raise ValueError("Index not built or embedder not available")

        if not self.chunks:
            return []

        # Generate embedding for query
        query_embeddings = self.embedder.embed([query_text])
        if not query_embeddings:
            return []

        import numpy as np

        query_vector = np.array([query_embeddings[0]], dtype="float32")

        # Search index
        k = min(top_k, len(self.chunks))
        distances, indices = self.index.search(query_vector, k)

        # Convert distances to similarity scores
        # For normalized embeddings with L2 distance:
        # similarity = 1 - (distance^2 / 2)
        # This approximates cosine similarity
        results: list[tuple[Chunk, float]] = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self.chunks):  # Invalid index
                continue

            # Convert L2 distance to similarity (0.0-1.0)
            # For normalized vectors: distance^2 = 2 - 2*cosine_similarity
            # So: cosine_similarity = 1 - (distance^2 / 2)
            similarity = max(0.0, min(1.0, 1.0 - (float(distance) ** 2 / 2.0)))

            # Filter by threshold
            if similarity >= similarity_threshold:
                chunk = self.chunks[int(idx)]
                results.append((chunk, similarity))

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def save(self, index_dir: Path) -> None:
        """
        Save index to disk.

        Args:
            index_dir: Directory to save index files
        """
        if not self.index or not self.metadata:
            raise ValueError("Index not built, cannot save")

        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = index_dir / "index.faiss"
        faiss.write_index(self.index, str(index_path))

        # Save chunks as JSON
        chunks_path = index_dir / "chunks.json"
        chunks_data = [chunk.to_dict() for chunk in self.chunks]
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # Save metadata
        metadata_path = index_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

        logger.info(f"Index saved to {index_dir}")

    @classmethod
    def load(cls, index_dir: Path, embedder: Embedder | None = None) -> "VectorIndex":
        """
        Load index from disk.

        Args:
            index_dir: Directory containing index files
            embedder: Optional embedder (required for querying after load)

        Returns:
            Loaded VectorIndex instance
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is not installed")

        index_dir = Path(index_dir)
        if not index_dir.exists():
            raise FileNotFoundError(f"Index directory not found: {index_dir}")

        # Load FAISS index
        index_path = index_dir / "index.faiss"
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")

        index = faiss.read_index(str(index_path))

        # Load chunks
        chunks_path = index_dir / "chunks.json"
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

        with open(chunks_path, encoding="utf-8") as f:
            chunks_data = json.load(f)

        from .rag_chunker import Chunk

        chunks = [Chunk.from_dict(data) for data in chunks_data]

        # Load metadata
        metadata_path = index_dir / "metadata.json"
        metadata = None
        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata_data = json.load(f)
                metadata = IndexMetadata.from_dict(metadata_data)

        # Create instance
        instance = cls(embedder=embedder)
        instance.index = index
        instance.chunks = chunks
        instance.metadata = metadata

        logger.info(f"Index loaded from {index_dir}: {len(chunks)} chunks")

        return instance

    def _calculate_source_fingerprint(self, chunks: list[Chunk]) -> str:
        """Calculate fingerprint of source files."""
        import hashlib

        source_files = sorted(set(str(c.source_file) for c in chunks))
        fingerprint_str = "|".join(source_files)
        return hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()[:16]
