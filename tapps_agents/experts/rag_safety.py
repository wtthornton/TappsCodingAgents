"""
RAG Safety - Prompt injection defense and untrusted retrieval handling.

Implements 2025 standards for RAG safety:
- Treat retrieved content as untrusted input
- Defend against prompt injection
- Strip/label sources
- Constrain tool usage
- Require citations
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Common prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+(instructions|prompts?|commands?)",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"system\s*:\s*",
    r"<\|(system|user|assistant)\|>",
    r"\[INST\]",
    r"###\s*(system|instruction|prompt)",
    r"---\s*BEGIN\s+(NEW\s+)?(INSTRUCTION|PROMPT|COMMAND)",
    r"---\s*END\s+(INSTRUCTION|PROMPT|COMMAND)",
    r"execute\s+(this|the following|code|command)",
    r"run\s+(this|the following|code|command)",
    r"eval\s*\(",
    r"exec\s*\(",
    r"<script",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
]

# Compile patterns for efficiency
INJECTION_PATTERN = re.compile(
    "|".join(f"({pattern})" for pattern in PROMPT_INJECTION_PATTERNS),
    re.IGNORECASE | re.MULTILINE,
)


class RAGSafetyHandler:
    """
    Handles safety for RAG-retrieved content.

    Features:
    - Prompt injection detection and mitigation
    - Source labeling
    - Content sanitization
    - Citation requirements
    """

    def __init__(
        self,
        enable_injection_detection: bool = True,
        enable_sanitization: bool = True,
        require_citations: bool = True,
    ):
        """
        Initialize safety handler.

        Args:
            enable_injection_detection: Enable prompt injection detection
            enable_sanitization: Enable content sanitization
            require_citations: Require citations for retrieved content
        """
        self.enable_injection_detection = enable_injection_detection
        self.enable_sanitization = enable_sanitization
        self.require_citations = require_citations

    def sanitize_retrieved_content(
        self, content: str, source: str | None = None
    ) -> tuple[str, bool]:
        """
        Sanitize retrieved content and detect prompt injection.

        Args:
            content: Retrieved content text
            source: Source file/path (for labeling)

        Returns:
            Tuple of (sanitized_content, is_safe)
            - sanitized_content: Sanitized version of content
            - is_safe: True if content appears safe, False if injection detected
        """
        if not content:
            return "", True

        is_safe = True

        # Detect prompt injection
        if self.enable_injection_detection:
            if INJECTION_PATTERN.search(content):
                logger.warning(
                    f"Potential prompt injection detected in retrieved content from {source}"
                )
                is_safe = False

                # Remove detected injection patterns
                if self.enable_sanitization:
                    content = INJECTION_PATTERN.sub("", content)

        # Sanitize content
        if self.enable_sanitization:
            # Remove control characters (except newlines and tabs)
            content = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", content)

            # Remove excessive whitespace
            content = re.sub(r"\n{3,}", "\n\n", content)
            content = re.sub(r" {3,}", "  ", content)

        # Label source if provided
        if source and self.require_citations:
            # Add source label at the beginning
            content = f"[Source: {source}]\n{content}"

        return content, is_safe

    def format_retrieved_context(
        self,
        chunks: list[tuple[str, float, str | None]],
        max_length: int = 2000,
        min_similarity: float = 0.7,
    ) -> tuple[str, list[str], bool]:
        """
        Format retrieved chunks into safe context string.

        Args:
            chunks: List of (content, similarity_score, source) tuples
            max_length: Maximum character length
            min_similarity: Minimum similarity threshold

        Returns:
            Tuple of (formatted_context, sources, all_safe)
            - formatted_context: Formatted context string
            - sources: List of source paths
            - all_safe: True if all chunks are safe
        """
        formatted_parts: list[str] = []
        sources: list[str] = []
        all_safe = True
        current_length = 0

        for content, similarity, source in chunks:
            # Filter by similarity threshold
            if similarity < min_similarity:
                continue

            # Sanitize content
            sanitized, is_safe = self.sanitize_retrieved_content(content, source)
            if not is_safe:
                all_safe = False

            # Check length limit
            chunk_text = f"{sanitized}\n---\n"
            if current_length + len(chunk_text) > max_length:
                break

            formatted_parts.append(sanitized)
            if source:
                sources.append(source)
            current_length += len(chunk_text)

        formatted_context = "\n---\n".join(formatted_parts)

        # Add warning if unsafe content detected
        if not all_safe:
            warning = "\n[WARNING: Some retrieved content may contain unsafe patterns. Use with caution.]\n"
            formatted_context = warning + formatted_context

        return formatted_context, sources, all_safe

    def validate_retrieved_content(self, content: str) -> dict[str, Any]:
        """
        Validate retrieved content for safety.

        Args:
            content: Content to validate

        Returns:
            Dictionary with validation results:
            - is_safe: bool
            - has_injection: bool
            - warnings: list[str]
        """
        result = {
            "is_safe": True,
            "has_injection": False,
            "warnings": [],
        }

        if not content:
            return result

        # Check for injection patterns
        if INJECTION_PATTERN.search(content):
            result["has_injection"] = True
            result["is_safe"] = False
            result["warnings"].append("Potential prompt injection detected")

        # Check for suspicious patterns
        suspicious_patterns = [
            (r"<script", "Potential script tag"),
            (r"javascript:", "Potential JavaScript injection"),
            (r"onerror\s*=", "Potential event handler injection"),
            (r"eval\s*\(", "Potential code execution"),
            (r"exec\s*\(", "Potential code execution"),
        ]

        for pattern, warning in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result["warnings"].append(warning)
                if not result["has_injection"]:
                    result["is_safe"] = False

        return result

    def add_citation_headers(self, content: str, sources: list[str]) -> str:
        """
        Add citation headers to content.

        Args:
            content: Content text
            sources: List of source paths

        Returns:
            Content with citation headers
        """
        if not sources:
            return content

        citation_header = "## Citations\n"
        citation_header += "\n".join(f"- {source}" for source in sources)
        citation_header += "\n\n---\n\n"

        return citation_header + content


def create_safety_handler(
    enable_injection_detection: bool = True,
    enable_sanitization: bool = True,
    require_citations: bool = True,
) -> RAGSafetyHandler:
    """
    Factory function to create a safety handler.

    Args:
        enable_injection_detection: Enable prompt injection detection
        enable_sanitization: Enable content sanitization
        require_citations: Require citations

    Returns:
        RAGSafetyHandler instance
    """
    return RAGSafetyHandler(
        enable_injection_detection=enable_injection_detection,
        enable_sanitization=enable_sanitization,
        require_citations=require_citations,
    )
