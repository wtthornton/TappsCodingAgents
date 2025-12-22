"""
Feedback Generator - Language-aware code review feedback generation

Phase 1.3: LLM Feedback Generation Fix
"""

from typing import Any

from pydantic import BaseModel, Field

from ...core.error_envelope import ErrorEnvelope
from ...core.language_detector import Language


class FeedbackResult(BaseModel):
    """
    Structured feedback result with validation.
    
    Phase 1.3: LLM Feedback Generation Fix
    """

    feedback: str = Field(
        description="Generated feedback text", min_length=50
    )  # Minimum 50 chars
    language: Language = Field(description="Detected language")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in feedback quality (0.0-1.0)"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="List of specific improvement suggestions"
    )


class FeedbackGenerationError(Exception):
    """Raised when feedback generation fails or produces invalid feedback."""

    pass


class FeedbackGenerator:
    """
    Generate language-aware code review feedback with validation.
    
    Phase 1.3: LLM Feedback Generation Fix
    """

    @staticmethod
    def generate_prompt(
        code: str,
        language: Language,
        scores: dict[str, Any] | None = None,
        expert_guidance: dict[str, Any] | None = None,
        code_preview_limit: int = 2000,
    ) -> str:
        """
        Generate language-aware prompt for feedback generation.
        
        Args:
            code: Code content to review
            language: Detected programming language
            scores: Optional code quality scores
            expert_guidance: Optional expert consultation results
            code_preview_limit: Maximum characters of code to include in prompt
            
        Returns:
            Generated prompt string
        """
        # Determine code block syntax based on language
        code_block_lang = FeedbackGenerator._get_code_block_language(language)
        
        prompt_parts = [
            "Review this code and provide detailed feedback:",
            "",
            "Code:",
            f"```{code_block_lang}",
            code[:code_preview_limit],
            "```",
        ]

        # Add language-specific guidance
        lang_guidance = FeedbackGenerator._get_language_guidance(language)
        if lang_guidance:
            prompt_parts.extend(["", lang_guidance])

        # Add expert guidance if available
        if expert_guidance:
            prompt_parts.append("\nExpert Guidance:")
            if "security" in expert_guidance:
                prompt_parts.append(
                    f"\nSecurity Expert:\n{expert_guidance['security'][:500]}..."
                )
            if "performance" in expert_guidance:
                prompt_parts.append(
                    f"\nPerformance Expert:\n{expert_guidance['performance'][:300]}..."
                )
            if "code_quality" in expert_guidance:
                prompt_parts.append(
                    f"\nCode Quality Expert:\n{expert_guidance['code_quality'][:300]}..."
                )
            prompt_parts.append("")

        if scores:
            prompt_parts.extend(
                [
                    "",
                    "Code Quality Scores:",
                    f"- Complexity: {scores.get('complexity_score', 0):.1f}/10",
                    f"- Security: {scores.get('security_score', 0):.1f}/10",
                    f"- Maintainability: {scores.get('maintainability_score', 0):.1f}/10",
                    f"- Test Coverage: {scores.get('test_coverage_score', 0):.1f}/10",
                    f"- Performance: {scores.get('performance_score', 0):.1f}/10",
                    f"- Overall Score: {scores.get('overall_score', 0):.1f}/100",
                ]
            )

        # Add language-specific feedback requirements
        feedback_requirements = FeedbackGenerator._get_feedback_requirements(language)
        prompt_parts.extend(["", "Provide detailed feedback:", ""])
        prompt_parts.extend(feedback_requirements)

        return "\n".join(prompt_parts)

    @staticmethod
    def _get_code_block_language(language: Language) -> str:
        """Get code block language identifier for markdown."""
        language_map = {
            Language.PYTHON: "python",
            Language.TYPESCRIPT: "typescript",
            Language.JAVASCRIPT: "javascript",
            Language.REACT: "tsx",  # Use tsx for React files
            Language.JAVA: "java",
            Language.CPP: "cpp",
            Language.C: "c",
            Language.RUST: "rust",
            Language.GO: "go",
            Language.RUBY: "ruby",
            Language.PHP: "php",
            Language.SWIFT: "swift",
            Language.KOTLIN: "kotlin",
            Language.HTML: "html",
            Language.CSS: "css",
            Language.SHELL: "bash",
            Language.POWERSHELL: "powershell",
            Language.DOCKERFILE: "dockerfile",
            Language.YAML: "yaml",
            Language.JSON: "json",
            Language.XML: "xml",
            Language.MARKDOWN: "markdown",
        }
        return language_map.get(language, "text")

    @staticmethod
    def _get_language_guidance(language: Language) -> str | None:
        """Get language-specific review guidance."""
        guidance_map = {
            Language.PYTHON: (
                "Focus on Python best practices:\n"
                "- PEP 8 style compliance\n"
                "- Type hints (Python 3.9+)\n"
                "- Error handling patterns\n"
                "- Docstring quality\n"
                "- Import organization"
            ),
            Language.TYPESCRIPT: (
                "Focus on TypeScript best practices:\n"
                "- Type safety and strict typing\n"
                "- Interface and type definitions\n"
                "- Error handling patterns\n"
                "- Code organization (exports/imports)\n"
                "- ESLint/TSLint compliance"
            ),
            Language.JAVASCRIPT: (
                "Focus on JavaScript best practices:\n"
                "- ES6+ features usage\n"
                "- Code organization\n"
                "- Error handling\n"
                "- ESLint compliance\n"
                "- Performance considerations"
            ),
            Language.REACT: (
                "Focus on React best practices:\n"
                "- React hooks usage (Rules of Hooks)\n"
                "- Component prop type safety\n"
                "- Performance optimization (memoization, re-renders)\n"
                "- JSX patterns and accessibility\n"
                "- State management patterns"
            ),
        }
        return guidance_map.get(language)

    @staticmethod
    def _get_feedback_requirements(language: Language) -> list[str]:
        """Get language-specific feedback requirements."""
        base_requirements = [
            "1. What the code does (brief summary)",
            "2. Potential issues or improvements",
            "3. Security concerns (if any)",
            "4. Style/best practices recommendations",
        ]

        # Add language-specific requirements
        if language == Language.PYTHON:
            base_requirements.extend(
                [
                    "5. Type hint usage and improvements",
                    "6. Error handling improvements",
                    "7. Documentation quality (docstrings)",
                ]
            )
        elif language in [Language.TYPESCRIPT, Language.REACT]:
            base_requirements.extend(
                [
                    "5. Type safety improvements",
                    "6. Code organization and structure",
                    "7. React patterns (if React code)",
                ]
            )
        elif language == Language.JAVASCRIPT:
            base_requirements.extend(
                [
                    "5. Modern JavaScript features usage",
                    "6. Code organization",
                    "7. Performance considerations",
                ]
            )

        return base_requirements

    @staticmethod
    def validate_feedback(
        feedback_text: str, minimum_length: int = 50
    ) -> FeedbackResult:
        """
        Validate feedback text and create structured result.
        
        Args:
            feedback_text: Generated feedback text
            minimum_length: Minimum required length in characters
            
        Returns:
            FeedbackResult with validated feedback
            
        Raises:
            FeedbackGenerationError: If feedback is invalid
        """
        if not feedback_text or not feedback_text.strip():
            envelope = ErrorEnvelope(
                code="empty_feedback",
                message="Generated feedback is empty",
                category="validation",
                agent="reviewer",
                recoverable=True,
            )
            raise FeedbackGenerationError(envelope.to_user_message())

        feedback_text = feedback_text.strip()

        if len(feedback_text) < minimum_length:
            envelope = ErrorEnvelope(
                code="feedback_too_short",
                message=f"Generated feedback is too short (minimum {minimum_length} characters, got {len(feedback_text)})",
                category="validation",
                agent="reviewer",
                recoverable=True,
                details={"length": len(feedback_text), "minimum": minimum_length},
            )
            raise FeedbackGenerationError(envelope.to_user_message())

        # Extract suggestions (basic heuristic - look for numbered lists or bullet points)
        suggestions = FeedbackGenerator._extract_suggestions(feedback_text)

        # Calculate confidence based on feedback characteristics
        confidence = FeedbackGenerator._calculate_confidence(feedback_text)

        # Note: Language is not determined here - it should be passed in from context
        # For now, we'll use UNKNOWN as a placeholder
        # In practice, this should be determined from the review context
        return FeedbackResult(
            feedback=feedback_text,
            language=Language.UNKNOWN,  # Should be set from context
            confidence=confidence,
            suggestions=suggestions,
        )

    @staticmethod
    def _extract_suggestions(feedback_text: str) -> list[str]:
        """Extract improvement suggestions from feedback text."""
        import re

        suggestions = []

        # Look for numbered lists (1. ..., 2. ..., etc.)
        numbered_pattern = r"\d+\.\s+([^\n]+)"
        numbered_matches = re.findall(numbered_pattern, feedback_text)
        suggestions.extend([match.strip() for match in numbered_matches])

        # Look for bullet points (- ..., * ..., • ...)
        bullet_pattern = r"[-*•]\s+([^\n]+)"
        bullet_matches = re.findall(bullet_pattern, feedback_text)
        suggestions.extend([match.strip() for match in bullet_matches])

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen:
                seen.add(suggestion.lower())
                unique_suggestions.append(suggestion)

        return unique_suggestions[:10]  # Limit to top 10

    @staticmethod
    def _calculate_confidence(feedback_text: str) -> float:
        """
        Calculate confidence score based on feedback characteristics.
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence
        confidence = 0.5

        # Increase confidence if feedback contains specific indicators
        if len(feedback_text) > 200:
            confidence += 0.1
        if len(feedback_text) > 500:
            confidence += 0.1

        # Check for structured content (numbered lists, bullet points)
        import re

        if re.search(r"\d+\.\s+", feedback_text):
            confidence += 0.1  # Has numbered list
        if re.search(r"[-*•]\s+", feedback_text):
            confidence += 0.1  # Has bullet points

        # Check for keywords indicating detailed analysis
        analysis_keywords = [
            "recommend",
            "suggest",
            "improve",
            "consider",
            "issue",
            "problem",
            "better",
            "optimize",
        ]
        keyword_count = sum(
            1 for keyword in analysis_keywords if keyword.lower() in feedback_text.lower()
        )
        confidence += min(keyword_count * 0.05, 0.2)  # Up to 0.2 for keywords

        return min(confidence, 1.0)  # Cap at 1.0

