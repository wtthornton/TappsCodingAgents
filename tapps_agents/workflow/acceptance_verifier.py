"""
Acceptance Criteria Verifier

Verifies acceptance criteria for story-level workflow steps.
Basic text matching implementation for Phase 3.
"""

from pathlib import Path
from typing import Any

from .models import Artifact


class AcceptanceCriteriaVerifier:
    """Verify acceptance criteria for stories (basic text matching)."""

    def verify(
        self,
        criteria: list[str],
        artifacts: dict[str, Artifact],
        code_files: list[Path] | None = None,
    ) -> dict[str, Any]:
        """
        Verify acceptance criteria against artifacts and code files.

        Args:
            criteria: List of acceptance criteria strings
            artifacts: Dictionary of artifacts created by the step
            code_files: Optional list of code file paths to check

        Returns:
            Dictionary with verification results:
            {
                "all_passed": bool,
                "results": [
                    {
                        "criterion": str,
                        "passed": bool,
                        "evidence": str | None
                    }
                ]
            }
        """
        results = []
        all_passed = True

        for criterion in criteria:
            passed = False
            evidence = None

            # Simple text matching: check if criterion keywords appear in artifacts
            criterion_lower = criterion.lower()

            # Check artifacts
            for artifact_name, artifact in artifacts.items():
                artifact_content = self._get_artifact_content(artifact)
                if artifact_content and self._matches_criterion(
                    criterion_lower, artifact_content
                ):
                    passed = True
                    evidence = f"Found in artifact: {artifact_name}"
                    break

            # Check code files if provided
            if not passed and code_files:
                for code_file in code_files:
                    if code_file.exists():
                        try:
                            content = code_file.read_text(encoding="utf-8")
                            if self._matches_criterion(criterion_lower, content):
                                passed = True
                                evidence = f"Found in code file: {code_file}"
                                break
                        except Exception:
                            # Skip files that can't be read
                            continue

            if not passed:
                all_passed = False

            results.append(
                {
                    "criterion": criterion,
                    "passed": passed,
                    "evidence": evidence,
                }
            )

        return {
            "all_passed": all_passed,
            "results": results,
        }

    def _get_artifact_content(self, artifact: Artifact) -> str | None:
        """Extract text content from artifact for matching."""
        if artifact.path:
            artifact_path = Path(artifact.path)
            if artifact_path.exists():
                try:
                    return artifact_path.read_text(encoding="utf-8")
                except Exception:
                    return None
        return None

    def _matches_criterion(self, criterion: str, content: str) -> bool:
        """
        Simple text matching: check if criterion keywords appear in content.

        This is a basic implementation for Phase 3. Future enhancements could
        use more sophisticated matching (semantic, structured parsing, etc.).
        """
        content_lower = content.lower()

        # Extract key phrases from criterion (simple approach)
        # Look for important keywords (skip common words)
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        criterion_words = [
            word.strip()
            for word in criterion.split()
            if word.strip().lower() not in common_words and len(word.strip()) > 2
        ]

        # Check if at least 50% of key words appear in content
        if not criterion_words:
            # If no keywords, check if criterion phrase appears
            return criterion in content_lower

        matches = sum(1 for word in criterion_words if word in content_lower)
        match_ratio = matches / len(criterion_words) if criterion_words else 0

        # Require at least 50% keyword match or exact phrase match
        return match_ratio >= 0.5 or criterion in content_lower
