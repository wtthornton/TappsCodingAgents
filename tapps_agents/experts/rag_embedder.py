"""
RAG Embedder - Interface and implementation for generating embeddings.

Supports multiple embedding backends with a common interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

# Try to import sentence-transformers (optional dependency)
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore


class Embedder(ABC):
    """Abstract interface for embedding generation."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        pass

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """
        Get the dimension of embeddings produced by this embedder.

        Returns:
            Embedding dimension (number of floats per embedding)
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name/identifier of the embedding model.

        Returns:
            Model name string
        """
        pass


class SentenceTransformerEmbedder(Embedder):
    """
    Embedder using sentence-transformers library.

    This is the default embedder for FAISS-based RAG.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence-transformers embedder.

        Args:
            model_name: Name of the sentence-transformers model
                       (default: "all-MiniLM-L6-v2" - fast, good quality)

        Raises:
            ImportError: If sentence-transformers is not installed
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )

        try:
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            # Get embedding dimension by encoding a dummy text
            dummy_embedding = self.model.encode(["test"], convert_to_numpy=False)[0]
            self._embedding_dim = len(dummy_embedding)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize sentence-transformers model '{model_name}': {e}"
            ) from e

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []

        try:
            # Encode texts to embeddings
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True,  # Normalize for cosine similarity
            )

            # Convert numpy arrays to lists
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self._embedding_dim

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name


def create_embedder(model_name: str | None = None) -> Embedder | None:
    """
    Factory function to create an embedder.

    Args:
        model_name: Optional model name (default: "all-MiniLM-L6-v2")

    Returns:
        Embedder instance if dependencies are available, None otherwise
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.warning(
            "sentence-transformers not available. "
            "Vector RAG will fall back to SimpleKnowledgeBase."
        )
        return None

    try:
        return SentenceTransformerEmbedder(model_name=model_name or "all-MiniLM-L6-v2")
    except Exception as e:
        logger.warning(f"Failed to create embedder: {e}. Falling back to SimpleKnowledgeBase.")
        return None
