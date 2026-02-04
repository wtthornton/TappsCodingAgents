"""
Artifact Context Builder - Token-aware artifact injection with budgeting.

Manages workflow artifact context with token budgets and priority ordering
to prevent context window overflow when injecting prior step documentation.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArtifactEntry:
    """Single artifact entry with metadata."""

    key: str
    content: str
    token_estimate: int
    priority: int


class ArtifactContextBuilder:
    """
    Builds context from workflow artifacts with token budget enforcement.

    Fills artifacts in priority order (spec → user_stories → architecture → api_design)
    and applies token budgets to prevent context overflow. When over budget, either
    truncates content to fit or uses template summaries.

    Example:
        >>> artifacts = [
        ...     ("specification", "Enhanced prompt content...", 1),
        ...     ("user_stories", "User stories content...", 2),
        ...     ("architecture", "Architecture content...", 3),
        ...     ("api_design", "API design content...", 4),
        ... ]
        >>> builder = ArtifactContextBuilder(token_budget=4000)
        >>> result = builder.build_context(artifacts)
        >>> # Returns dict with full content or summaries based on budget
    """

    def __init__(
        self,
        token_budget: int = 4000,
        use_tiktoken: bool = True,
        summarization_enabled: bool = False,
    ):
        """
        Initialize ArtifactContextBuilder.

        Args:
            token_budget: Maximum tokens for all artifacts combined
            use_tiktoken: Try to use tiktoken for accurate estimation (fallback to chars/4)
            summarization_enabled: Use template summaries when over budget (default: truncate)
        """
        self.token_budget = token_budget
        self.use_tiktoken = use_tiktoken
        self.summarization_enabled = summarization_enabled
        self._tiktoken_encoder = None

        # Try to load tiktoken if requested
        if use_tiktoken:
            try:
                import tiktoken
                self._tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
                logger.debug("Using tiktoken for token estimation")
            except ImportError:
                logger.debug("tiktoken not available, falling back to chars/4 estimation")

        # Template summaries for each artifact type
        self._summary_templates = {
            "specification": "Enhanced prompt (summary)",
            "user_stories": "User stories: {count} items",
            "architecture": "Architecture: {summary}",
            "api_design": "API design: {count} endpoints",
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        if self._tiktoken_encoder:
            try:
                return len(self._tiktoken_encoder.encode(text))
            except Exception as e:
                logger.warning(f"tiktoken encoding failed, falling back to chars/4: {e}")

        # Fallback: chars/4 with small safety margin
        return int(len(text) / 4 * 1.1)  # 10% safety margin

    def _extract_summary_info(self, key: str, content: str) -> dict[str, Any]:
        """
        Extract summary information from content.

        Args:
            key: Artifact key
            content: Artifact content

        Returns:
            Dictionary with summary info (count, summary text, etc.)
        """
        info: dict[str, Any] = {}

        if key == "user_stories":
            # Count user stories (look for "US-" or "Story" or numbered lists)
            story_matches = re.findall(r'(?:US-\d+|Story \d+|^\d+\.)', content, re.MULTILINE)
            info["count"] = len(story_matches) if story_matches else 1

        elif key == "api_design":
            # Count API endpoints (look for HTTP methods or endpoint patterns)
            endpoint_matches = re.findall(
                r'(?:GET|POST|PUT|DELETE|PATCH)\s+/|endpoint\s*:|route\s*:',
                content,
                re.IGNORECASE
            )
            info["count"] = len(endpoint_matches) if endpoint_matches else 1

        elif key == "architecture":
            # Extract first sentence or first line as summary
            lines = content.strip().split('\n')
            first_line = lines[0] if lines else "Component architecture"
            # Clean markdown and limit length
            summary = re.sub(r'[#*_`]', '', first_line)[:100]
            info["summary"] = summary or "System architecture"

        return info

    def _generate_summary(self, key: str, content: str) -> str:
        """
        Generate template summary for artifact.

        Args:
            key: Artifact key
            content: Original content

        Returns:
            Template summary string
        """
        template = self._summary_templates.get(key, f"{key} (summary)")

        # Extract info for template formatting
        info = self._extract_summary_info(key, content)

        try:
            return template.format(**info)
        except (KeyError, ValueError):
            # Fallback if template formatting fails
            return template

    def build_context(
        self,
        artifacts: list[tuple[str, str, int]] | list[tuple[str, str]],
    ) -> dict[str, str]:
        """
        Build context from ordered artifacts with token budget enforcement.

        Args:
            artifacts: List of (key, content, priority) or (key, content) tuples.
                      If priority not provided, uses order in list (1, 2, 3, ...).
                      Priority 1 = highest priority (filled first)

        Returns:
            Dictionary mapping keys to content (full or summary/truncated)

        Example:
            >>> artifacts = [
            ...     ("specification", "Long spec...", 1),
            ...     ("user_stories", "Stories...", 2),
            ...     ("architecture", "Arch...", 3),
            ...     ("api_design", "API...", 4),
            ... ]
            >>> result = builder.build_context(artifacts)
            >>> # Result contains full content up to budget, then summaries
        """
        if not artifacts:
            return {}

        # Normalize to include priority
        normalized_artifacts: list[ArtifactEntry] = []
        for i, artifact in enumerate(artifacts):
            if len(artifact) == 2:
                key, content = artifact
                priority = i + 1  # Use order as priority
            else:
                key, content, priority = artifact

            token_estimate = self.estimate_tokens(content)
            normalized_artifacts.append(
                ArtifactEntry(
                    key=key,
                    content=content,
                    token_estimate=token_estimate,
                    priority=priority,
                )
            )

        # Sort by priority (lower priority number = higher priority)
        normalized_artifacts.sort(key=lambda x: x.priority)

        # Build context respecting budget
        result: dict[str, str] = {}
        tokens_used = 0

        for entry in normalized_artifacts:
            remaining_budget = self.token_budget - tokens_used

            if remaining_budget <= 0:
                # Budget exhausted - use summary if enabled
                if self.summarization_enabled:
                    summary = self._generate_summary(entry.key, entry.content)
                    result[entry.key] = summary
                    tokens_used += self.estimate_tokens(summary)
                    logger.debug(
                        f"Budget exhausted for '{entry.key}', using summary "
                        f"({self.estimate_tokens(summary)} tokens)"
                    )
                else:
                    # Skip artifact entirely
                    logger.debug(f"Budget exhausted, skipping '{entry.key}'")
                continue

            if entry.token_estimate <= remaining_budget:
                # Fits in budget - use full content
                result[entry.key] = entry.content
                tokens_used += entry.token_estimate
                logger.debug(
                    f"Added '{entry.key}' ({entry.token_estimate} tokens, "
                    f"{tokens_used}/{self.token_budget} used)"
                )
            else:
                # Doesn't fit - truncate or summarize
                if self.summarization_enabled:
                    # Use summary
                    summary = self._generate_summary(entry.key, entry.content)
                    summary_tokens = self.estimate_tokens(summary)

                    if summary_tokens <= remaining_budget:
                        result[entry.key] = summary
                        tokens_used += summary_tokens
                        logger.debug(
                            f"'{entry.key}' over budget ({entry.token_estimate} tokens), "
                            f"using summary ({summary_tokens} tokens)"
                        )
                    else:
                        # Even summary doesn't fit - skip
                        logger.debug(
                            f"'{entry.key}' summary too large ({summary_tokens} tokens), skipping"
                        )
                else:
                    # Truncate to fit remaining budget
                    # Estimate characters for remaining tokens (inverse of estimation)
                    if self._tiktoken_encoder:
                        # With tiktoken, we need to truncate and re-encode iteratively
                        # For simplicity, use chars/4 estimate to get approximate length
                        target_chars = int(remaining_budget * 4 / 1.1)
                    else:
                        target_chars = int(remaining_budget * 4 / 1.1)

                    truncated = entry.content[:target_chars]
                    # Clean up - don't truncate mid-sentence if possible
                    last_period = truncated.rfind('.')
                    if last_period > target_chars * 0.7:  # Within last 30%
                        truncated = truncated[:last_period + 1]

                    truncated += "\n\n[Content truncated to fit token budget]"

                    result[entry.key] = truncated
                    truncated_tokens = self.estimate_tokens(truncated)
                    tokens_used += truncated_tokens
                    logger.debug(
                        f"Truncated '{entry.key}' from {entry.token_estimate} "
                        f"to {truncated_tokens} tokens"
                    )

        logger.info(
            f"Built context with {len(result)}/{len(normalized_artifacts)} artifacts, "
            f"{tokens_used}/{self.token_budget} tokens used"
        )

        return result
