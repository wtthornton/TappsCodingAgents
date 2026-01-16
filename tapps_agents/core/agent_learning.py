"""
Agent Learning System

Enables agents to learn from past tasks and improve over time.
"""

# @ai-prime-directive: This file implements the Agent Learning System for pattern extraction, prompt optimization,
# and feedback analysis. The system enables agents to learn from past tasks and improve over time through
# meta-learning, pattern recognition, and adaptive learning strategies.

# @ai-constraints:
# - Learning intensity must adapt to hardware profile (NUC, Desktop, Server)
# - Pattern extraction must include security scanning before pattern acceptance
# - Anti-pattern extraction must learn from negative feedback and failures
# - Prompt optimization must respect hardware constraints and token budgets
# - Meta-learning must track learning effectiveness and adjust strategies accordingly
# - Performance: Learning operations should not significantly impact agent response times

# @note[2025-01-15]: Agent learning is an advanced feature that improves agent performance over time.
# The system uses meta-learning to adapt learning strategies based on effectiveness tracking.
# See docs/architecture/decisions/ for related architectural decisions.

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .best_practice_consultant import BestPracticeConsultant
from .capability_registry import CapabilityRegistry, LearningIntensity
from .hardware_profiler import HardwareProfile, HardwareProfiler
from .learning_confidence import LearningConfidenceCalculator
from .learning_dashboard import LearningDashboard
from .learning_decision import LearningDecisionEngine
from .learning_explainability import (
    DecisionReasoningLogger,
    LearningImpactReporter,
    PatternSelectionExplainer,
)
from .meta_learning import (
    AdaptiveLearningRate,
    LearningEffectivenessTracker,
    LearningSelfAssessor,
    LearningStrategy,
    LearningStrategySelector,
)
from .security_scanner import SecurityScanner
from .task_memory import TaskMemorySystem, TaskOutcome

logger = logging.getLogger(__name__)


@dataclass
class CodePattern:
    """Represents a learned code pattern."""

    pattern_id: str
    pattern_type: str  # "function", "class", "import", "structure"
    code_snippet: str
    context: str
    quality_score: float
    usage_count: int
    success_rate: float
    learned_from: list[str]  # Task IDs where this pattern was successful
    metadata: dict[str, Any] = field(default_factory=dict)
    security_score: float = 0.0  # Security score (0-10, higher is better)
    is_anti_pattern: bool = False  # True if this is an anti-pattern to avoid
    failure_reasons: list[str] = field(default_factory=list)  # Reasons for failure
    rejection_count: int = 0  # Number of times this pattern was rejected


@dataclass
class PromptVariant:
    """Represents a prompt variation for A/B testing."""

    variant_id: str
    prompt_template: str
    modifications: list[str]  # List of modifications made
    test_count: int
    success_count: int
    average_quality: float
    created_at: datetime
    last_tested: datetime | None = None


class PatternExtractor:
    """Extracts patterns from successful code outputs."""

    def __init__(
        self,
        min_quality_threshold: float = 0.7,
        security_scanner: SecurityScanner | None = None,
        security_threshold: float = 7.0,
    ):
        """
        Initialize pattern extractor.

        Args:
            min_quality_threshold: Minimum quality score to extract patterns
            security_scanner: Optional security scanner instance
            security_threshold: Minimum security score to extract patterns (default: 7.0)
        """
        self.min_quality_threshold = min_quality_threshold
        self.security_scanner = security_scanner or SecurityScanner()
        self.security_threshold = security_threshold
        self.patterns: dict[str, CodePattern] = {}

    def extract_patterns(
        self,
        code: str,
        quality_score: float,
        task_id: str,
        pattern_types: list[str] | None = None,
    ) -> list[CodePattern]:
        """
        Extract patterns from code.

        Args:
            code: Source code
            quality_score: Quality score of the code
            task_id: Task identifier
            pattern_types: Optional list of pattern types to extract

        Returns:
            List of extracted patterns
        """
        if quality_score < self.min_quality_threshold:
            return []

        # Security check before extraction
        security_result = self.security_scanner.scan_code(code=code)
        security_score = security_result["security_score"]
        vulnerabilities = security_result["vulnerabilities"]
        is_safe = security_result.get("is_safe", True)

        # Only extract if security score meets threshold
        # Check both score >= threshold AND is_safe flag
        if security_score < self.security_threshold or not is_safe:
            logger.debug(
                f"Skipping pattern extraction: security score {security_score:.2f} "
                f"below threshold {self.security_threshold:.2f} or is_safe={is_safe}"
            )
            return []

        patterns = []

        # Extract function patterns
        if not pattern_types or "function" in pattern_types:
            func_patterns = self._extract_function_patterns(
                code, quality_score, task_id
            )
            patterns.extend(func_patterns)

        # Extract class patterns
        if not pattern_types or "class" in pattern_types:
            class_patterns = self._extract_class_patterns(code, quality_score, task_id)
            patterns.extend(class_patterns)

        # Extract import patterns
        if not pattern_types or "import" in pattern_types:
            import_patterns = self._extract_import_patterns(
                code, quality_score, task_id
            )
            patterns.extend(import_patterns)

        # Extract structural patterns
        if not pattern_types or "structure" in pattern_types:
            struct_patterns = self._extract_structural_patterns(
                code, quality_score, task_id
            )
            patterns.extend(struct_patterns)

        return patterns

    def _extract_function_patterns(
        self, code: str, quality_score: float, task_id: str
    ) -> list[CodePattern]:
        """Extract function patterns."""
        patterns = []

        # Match function definitions - more flexible pattern that handles docstrings and type hints
        # Find all function definitions, then extract their bodies
        # Pattern matches: def function_name(...) with optional type hints, handling multiline signatures
        func_def_pattern = r"def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?:"
        func_matches = list(re.finditer(func_def_pattern, code, re.MULTILINE | re.DOTALL))
        
        for i, match in enumerate(func_matches):
            func_name = match.group(1)
            start_pos = match.end()
            
            # Find the end of this function (next function def or end of code)
            if i + 1 < len(func_matches):
                end_pos = func_matches[i + 1].start()
            else:
                end_pos = len(code)
            
            func_body = code[start_pos:end_pos].strip()
            
            # Skip if function body is empty
            if not func_body:
                continue

            # Get security score for this pattern
            pattern_code = f"def {func_name}(...):\n{func_body[:200]}"
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            pattern = CodePattern(
                pattern_id=f"func_{func_name}_{hash(func_body) % 10000}",
                pattern_type="function",
                code_snippet=pattern_code,
                context=f"Function: {func_name}",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            patterns.append(pattern)

        return patterns

    def _extract_class_patterns(
        self, code: str, quality_score: float, task_id: str
    ) -> list[CodePattern]:
        """Extract class patterns."""
        patterns = []

        # Match class definitions
        class_pattern = r"class\s+(\w+)(?:\([^)]+\))?:\s*\n((?:\s{4}.*\n?)*)"
        matches = re.finditer(class_pattern, code, re.MULTILINE)

        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)

            # Get security score for this pattern
            pattern_code = f"class {class_name}:\n{class_body[:200]}"
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            pattern = CodePattern(
                pattern_id=f"class_{class_name}_{hash(class_body) % 10000}",
                pattern_type="class",
                code_snippet=pattern_code,
                context=f"Class: {class_name}",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            patterns.append(pattern)

        return patterns

    def _extract_import_patterns(
        self, code: str, quality_score: float, task_id: str
    ) -> list[CodePattern]:
        """Extract import patterns."""
        patterns = []

        # Match import statements
        import_pattern = r"^(?:from\s+[\w.]+|import\s+[\w.,\s]+)"
        matches = re.finditer(import_pattern, code, re.MULTILINE)

        imports = []
        for match in matches:
            imports.append(match.group(0).strip())

        if imports:
            # Get security score for this pattern
            pattern_code = "\n".join(imports[:10])
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            pattern = CodePattern(
                pattern_id=f"imports_{hash(''.join(imports)) % 10000}",
                pattern_type="import",
                code_snippet=pattern_code,
                context="Import statements",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            patterns.append(pattern)

        return patterns

    def _extract_structural_patterns(
        self, code: str, quality_score: float, task_id: str
    ) -> list[CodePattern]:
        """Extract structural patterns (decorators, context managers, etc.)."""
        patterns = []

        # Match decorators
        decorator_pattern = r"@\w+(?:\([^)]*\))?"
        decorators = re.findall(decorator_pattern, code)

        if decorators:
            # Get security score for this pattern
            pattern_code = "\n".join(decorators[:5])
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            pattern = CodePattern(
                pattern_id=f"decorators_{hash(''.join(decorators)) % 10000}",
                pattern_type="structure",
                code_snippet=pattern_code,
                context="Decorators",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            patterns.append(pattern)

        return patterns

    def get_patterns_for_context(
        self,
        context: str,
        pattern_type: str | None = None,
        limit: int = 5,
        exclude_anti_patterns: bool = True,
    ) -> list[CodePattern]:
        """
        Get relevant patterns for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results
            exclude_anti_patterns: If True, exclude anti-patterns (default: True)

        Returns:
            List of relevant patterns
        """
        candidates = list(self.patterns.values())

        # Filter out anti-patterns if requested
        if exclude_anti_patterns:
            candidates = [p for p in candidates if not p.is_anti_pattern]

        if pattern_type:
            candidates = [p for p in candidates if p.pattern_type == pattern_type]

        # Sort by security score, quality, and usage
        candidates.sort(
            key=lambda p: (p.security_score, p.quality_score, p.usage_count),
            reverse=True,
        )

        return candidates[:limit]


class AntiPatternExtractor:
    """Extracts anti-patterns from failed tasks and low-quality code."""

    def __init__(
        self,
        max_quality_threshold: float = 0.7,
        security_scanner: SecurityScanner | None = None,
    ):
        """
        Initialize anti-pattern extractor.

        Args:
            max_quality_threshold: Maximum quality score to extract anti-patterns
            security_scanner: Optional security scanner instance
        """
        self.max_quality_threshold = max_quality_threshold
        self.security_scanner = security_scanner or SecurityScanner()
        self.anti_patterns: dict[str, CodePattern] = {}

    def extract_anti_patterns(
        self,
        code: str,
        quality_score: float,
        task_id: str,
        failure_reasons: list[str] | None = None,
        pattern_types: list[str] | None = None,
    ) -> list[CodePattern]:
        """
        Extract anti-patterns from failed or low-quality code.

        Args:
            code: Source code
            quality_score: Quality score of the code
            task_id: Task identifier
            failure_reasons: Optional list of failure reasons
            pattern_types: Optional list of pattern types to extract

        Returns:
            List of extracted anti-patterns
        """
        # Only extract if quality is below threshold
        if quality_score >= self.max_quality_threshold:
            return []

        failure_reasons = failure_reasons or []
        anti_patterns = []

        # Extract function anti-patterns
        if not pattern_types or "function" in pattern_types:
            func_patterns = self._extract_function_anti_patterns(
                code, quality_score, task_id, failure_reasons
            )
            anti_patterns.extend(func_patterns)

        # Extract class anti-patterns
        if not pattern_types or "class" in pattern_types:
            class_patterns = self._extract_class_anti_patterns(
                code, quality_score, task_id, failure_reasons
            )
            anti_patterns.extend(class_patterns)

        # Extract import anti-patterns
        if not pattern_types or "import" in pattern_types:
            import_patterns = self._extract_import_anti_patterns(
                code, quality_score, task_id, failure_reasons
            )
            anti_patterns.extend(import_patterns)

        # Extract structural anti-patterns
        if not pattern_types or "structure" in pattern_types:
            struct_patterns = self._extract_structural_anti_patterns(
                code, quality_score, task_id, failure_reasons
            )
            anti_patterns.extend(struct_patterns)

        return anti_patterns

    def _extract_function_anti_patterns(
        self,
        code: str,
        quality_score: float,
        task_id: str,
        failure_reasons: list[str],
    ) -> list[CodePattern]:
        """Extract function anti-patterns."""
        anti_patterns = []

        # Match function definitions
        func_pattern = r"def\s+(\w+)\s*\([^)]*\):\s*\n((?:\s{4}.*\n?)*)"
        matches = list(re.finditer(func_pattern, code, re.MULTILINE))

        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2)

            # Get security score for this pattern
            pattern_code = f"def {func_name}(...):\n{func_body[:200]}"
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            anti_pattern = CodePattern(
                pattern_id=f"anti_func_{func_name}_{hash(func_body) % 10000}",
                pattern_type="function",
                code_snippet=pattern_code,
                context=f"Anti-pattern Function: {func_name}",
                quality_score=quality_score,
                usage_count=1,
                success_rate=0.0,  # Anti-patterns have 0 success rate
                learned_from=[task_id],
                security_score=pattern_security_score,
                is_anti_pattern=True,
                failure_reasons=failure_reasons.copy(),
                rejection_count=0,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            anti_patterns.append(anti_pattern)

        return anti_patterns

    def _extract_class_anti_patterns(
        self,
        code: str,
        quality_score: float,
        task_id: str,
        failure_reasons: list[str],
    ) -> list[CodePattern]:
        """Extract class anti-patterns."""
        anti_patterns = []

        # Match class definitions
        class_pattern = r"class\s+(\w+)(?:\([^)]+\))?:\s*\n((?:\s{4}.*\n?)*)"
        matches = re.finditer(class_pattern, code, re.MULTILINE)

        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)

            # Get security score for this pattern
            pattern_code = f"class {class_name}:\n{class_body[:200]}"
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            anti_pattern = CodePattern(
                pattern_id=f"anti_class_{class_name}_{hash(class_body) % 10000}",
                pattern_type="class",
                code_snippet=pattern_code,
                context=f"Anti-pattern Class: {class_name}",
                quality_score=quality_score,
                usage_count=1,
                success_rate=0.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                is_anti_pattern=True,
                failure_reasons=failure_reasons.copy(),
                rejection_count=0,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            anti_patterns.append(anti_pattern)

        return anti_patterns

    def _extract_import_anti_patterns(
        self,
        code: str,
        quality_score: float,
        task_id: str,
        failure_reasons: list[str],
    ) -> list[CodePattern]:
        """Extract import anti-patterns."""
        anti_patterns = []

        # Match import statements
        import_pattern = r"^(?:from\s+[\w.]+|import\s+[\w.,\s]+)"
        matches = re.finditer(import_pattern, code, re.MULTILINE)

        imports = []
        for match in matches:
            imports.append(match.group(0).strip())

        if imports:
            # Get security score for this pattern
            pattern_code = "\n".join(imports[:10])
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            anti_pattern = CodePattern(
                pattern_id=f"anti_imports_{hash(''.join(imports)) % 10000}",
                pattern_type="import",
                code_snippet=pattern_code,
                context="Anti-pattern Import statements",
                quality_score=quality_score,
                usage_count=1,
                success_rate=0.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                is_anti_pattern=True,
                failure_reasons=failure_reasons.copy(),
                rejection_count=0,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            anti_patterns.append(anti_pattern)

        return anti_patterns

    def _extract_structural_anti_patterns(
        self,
        code: str,
        quality_score: float,
        task_id: str,
        failure_reasons: list[str],
    ) -> list[CodePattern]:
        """Extract structural anti-patterns."""
        anti_patterns = []

        # Match decorators
        decorator_pattern = r"@\w+(?:\([^)]*\))?"
        decorators = re.findall(decorator_pattern, code)

        if decorators:
            # Get security score for this pattern
            pattern_code = "\n".join(decorators[:5])
            pattern_security = self.security_scanner.scan_code(code=pattern_code)
            pattern_security_score = pattern_security["security_score"]
            pattern_vulnerabilities = pattern_security["vulnerabilities"]

            anti_pattern = CodePattern(
                pattern_id=f"anti_decorators_{hash(''.join(decorators)) % 10000}",
                pattern_type="structure",
                code_snippet=pattern_code,
                context="Anti-pattern Decorators",
                quality_score=quality_score,
                usage_count=1,
                success_rate=0.0,
                learned_from=[task_id],
                security_score=pattern_security_score,
                is_anti_pattern=True,
                failure_reasons=failure_reasons.copy(),
                rejection_count=0,
                metadata={"vulnerabilities": pattern_vulnerabilities},
            )
            anti_patterns.append(anti_pattern)

        return anti_patterns

    def extract_from_failure(
        self,
        code: str,
        task_id: str,
        failure_reasons: list[str],
        quality_score: float = 0.0,
    ) -> list[CodePattern]:
        """
        Extract anti-patterns from a failed task.

        Args:
            code: Source code from failed task
            task_id: Task identifier
            failure_reasons: List of failure reasons
            quality_score: Quality score (default: 0.0 for failures)

        Returns:
            List of extracted anti-patterns
        """
        return self.extract_anti_patterns(
            code=code,
            quality_score=quality_score,
            task_id=task_id,
            failure_reasons=failure_reasons,
        )

    def extract_from_rejection(
        self,
        code: str,
        task_id: str,
        rejection_reason: str,
        quality_score: float = 0.5,
    ) -> list[CodePattern]:
        """
        Extract anti-patterns from user rejection.

        Args:
            code: Rejected code
            task_id: Task identifier
            rejection_reason: Reason for rejection
            quality_score: Quality score

        Returns:
            List of extracted anti-patterns
        """
        return self.extract_anti_patterns(
            code=code,
            quality_score=quality_score,
            task_id=task_id,
            failure_reasons=[f"User rejection: {rejection_reason}"],
        )

    def get_anti_patterns_for_context(
        self, context: str, pattern_type: str | None = None, limit: int = 5
    ) -> list[CodePattern]:
        """
        Get anti-patterns to avoid for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results

        Returns:
            List of anti-patterns to avoid
        """
        candidates = [p for p in self.anti_patterns.values() if p.is_anti_pattern]

        if pattern_type:
            candidates = [p for p in candidates if p.pattern_type == pattern_type]

        # Sort by rejection count and quality (low quality = more important to avoid)
        candidates.sort(
            key=lambda p: (p.rejection_count, -p.quality_score), reverse=True
        )

        return candidates[:limit]


class PromptOptimizer:
    """Optimizes agent prompts based on outcomes."""

    def __init__(self, hardware_profile: HardwareProfile):
        """
        Initialize prompt optimizer.

        Args:
            hardware_profile: Hardware profile for optimization
        """
        self.hardware_profile = hardware_profile
        self.variants: dict[str, PromptVariant] = {}
        self.base_prompt: str | None = None

    def create_variant(
        self,
        base_prompt: str,
        modifications: list[str],
        variant_id: str | None = None,
    ) -> PromptVariant:
        """
        Create a prompt variant for A/B testing.

        Args:
            base_prompt: Base prompt template
            modifications: List of modifications to apply
            variant_id: Optional variant identifier

        Returns:
            PromptVariant instance
        """
        if variant_id is None:
            variant_id = f"variant_{hash(''.join(modifications)) % 10000}"

        # Apply modifications (simplified - in production would be more sophisticated)
        modified_prompt = base_prompt
        for mod in modifications:
            if mod.startswith("add:"):
                modified_prompt += f"\n{mod[4:]}"
            elif mod.startswith("prepend:"):
                modified_prompt = f"{mod[8:]}\n{modified_prompt}"

        variant = PromptVariant(
            variant_id=variant_id,
            prompt_template=modified_prompt,
            modifications=modifications,
            test_count=0,
            success_count=0,
            average_quality=0.0,
            created_at=datetime.now(UTC),
        )

        self.variants[variant_id] = variant
        return variant

    def record_test_result(self, variant_id: str, success: bool, quality_score: float):
        """
        Record A/B test result for a variant.

        Args:
            variant_id: Variant identifier
            success: Whether test succeeded
            quality_score: Quality score
        """
        if variant_id not in self.variants:
            logger.warning(f"Variant {variant_id} not found")
            return

        variant = self.variants[variant_id]
        variant.test_count += 1
        if success:
            variant.success_count += 1

        # Update average quality (exponential moving average)
        alpha = 0.1
        variant.average_quality = (
            alpha * quality_score + (1 - alpha) * variant.average_quality
        )
        variant.last_tested = datetime.now(UTC)

    def get_best_variant(self, min_tests: int = 5) -> PromptVariant | None:
        """
        Get the best performing variant.

        Args:
            min_tests: Minimum test count to consider

        Returns:
            Best PromptVariant if found, None otherwise
        """
        candidates = [v for v in self.variants.values() if v.test_count >= min_tests]

        if not candidates:
            return None

        # Sort by success rate and average quality
        candidates.sort(
            key=lambda v: (v.success_count / v.test_count, v.average_quality),
            reverse=True,
        )

        return candidates[0]

    def optimize_for_hardware(self, prompt: str) -> str:
        """
        Optimize prompt for hardware profile.

        Args:
            prompt: Original prompt

        Returns:
            Optimized prompt
        """
        if self.hardware_profile == HardwareProfile.NUC:
            # Shorter prompts for NUC
            # Remove verbose instructions, keep essentials
            lines = prompt.split("\n")
            essential_lines = [
                line
                for line in lines
                if not line.strip().startswith("#") or "TODO" in line
            ]
            return "\n".join(essential_lines[:50])  # Limit to 50 lines
        else:
            # Full prompts for workstation
            return prompt


class NegativeFeedbackHandler:
    """Handles negative feedback, rejections, and corrections."""

    def __init__(self, anti_pattern_extractor: AntiPatternExtractor | None = None):
        """
        Initialize negative feedback handler.

        Args:
            anti_pattern_extractor: Optional anti-pattern extractor instance
        """
        self.anti_pattern_extractor = anti_pattern_extractor or AntiPatternExtractor()
        self.rejections: list[dict[str, Any]] = []
        self.corrections: list[dict[str, Any]] = []

    def record_rejection(
        self,
        code: str,
        task_id: str,
        reason: str,
        quality_score: float = 0.5,
    ) -> list[CodePattern]:
        """
        Record user rejection and extract anti-patterns.

        Args:
            code: Rejected code
            task_id: Task identifier
            reason: Reason for rejection
            quality_score: Quality score

        Returns:
            List of extracted anti-patterns
        """
        rejection = {
            "task_id": task_id,
            "reason": reason,
            "quality_score": quality_score,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.rejections.append(rejection)

        # Extract anti-patterns from rejected code
        anti_patterns = self.anti_pattern_extractor.extract_from_rejection(
            code=code,
            task_id=task_id,
            rejection_reason=reason,
            quality_score=quality_score,
        )

        # Update rejection counts for existing anti-patterns
        for anti_pattern in anti_patterns:
            if anti_pattern.pattern_id in self.anti_pattern_extractor.anti_patterns:
                existing = self.anti_pattern_extractor.anti_patterns[
                    anti_pattern.pattern_id
                ]
                existing.rejection_count += 1
                if reason not in existing.failure_reasons:
                    existing.failure_reasons.append(reason)
            else:
                # New anti-pattern from rejection should have rejection_count=1
                anti_pattern.rejection_count = 1
                self.anti_pattern_extractor.anti_patterns[
                    anti_pattern.pattern_id
                ] = anti_pattern

        return anti_patterns

    def record_correction(
        self,
        original_code: str,
        corrected_code: str,
        task_id: str,
        correction_reason: str,
    ) -> tuple[list[CodePattern], list[CodePattern]]:
        """
        Record user correction and extract both anti-patterns and patterns.

        Args:
            original_code: Original (incorrect) code
            corrected_code: Corrected code
            task_id: Task identifier
            correction_reason: Reason for correction

        Returns:
            Tuple of (anti-patterns from original, patterns from corrected)
        """
        correction = {
            "task_id": task_id,
            "reason": correction_reason,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.corrections.append(correction)

        # Extract anti-patterns from original code
        anti_patterns = self.anti_pattern_extractor.extract_from_rejection(
            code=original_code,
            task_id=task_id,
            rejection_reason=f"Correction: {correction_reason}",
            quality_score=0.3,  # Low quality for incorrect code
        )

        # Extract patterns from corrected code (using PatternExtractor logic)
        # Note: This would require access to PatternExtractor, but for now
        # we'll just return the anti-patterns
        return anti_patterns, []

    def extract_anti_patterns_from_feedback(
        self, code: str, task_id: str, feedback: str
    ) -> list[CodePattern]:
        """
        Extract anti-patterns from feedback text.

        Args:
            code: Code that received feedback
            task_id: Task identifier
            feedback: Feedback text

        Returns:
            List of extracted anti-patterns
        """
        return self.anti_pattern_extractor.extract_from_rejection(
            code=code,
            task_id=task_id,
            rejection_reason=feedback,
            quality_score=0.4,
        )

    def get_anti_patterns_for_context(
        self, context: str, pattern_type: str | None = None, limit: int = 5
    ) -> list[CodePattern]:
        """
        Get anti-patterns to avoid for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results

        Returns:
            List of anti-patterns to avoid
        """
        return self.anti_pattern_extractor.get_anti_patterns_for_context(
            context=context, pattern_type=pattern_type, limit=limit
        )


class FailureModeAnalyzer:
    """Analyzes failure patterns and categorizes failures."""

    def __init__(self):
        """Initialize failure mode analyzer."""
        self.failure_modes: dict[str, dict[str, Any]] = {}

    def analyze_failure(
        self,
        code: str,
        task_id: str,
        failure_reasons: list[str],
        quality_scores: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a single failure.

        Args:
            code: Failed code
            task_id: Task identifier
            failure_reasons: List of failure reasons
            quality_scores: Optional quality scores

        Returns:
            Analysis result with failure mode and suggestions
        """
        failure_mode = self.identify_failure_mode(failure_reasons, quality_scores)

        # Track failure mode statistics
        if failure_mode not in self.failure_modes:
            self.failure_modes[failure_mode] = {
                "count": 0,
                "reasons": [],
                "task_ids": [],
            }

        self.failure_modes[failure_mode]["count"] += 1
        self.failure_modes[failure_mode]["reasons"].extend(failure_reasons)
        self.failure_modes[failure_mode]["task_ids"].append(task_id)

        # Generate prevention suggestions
        suggestions = self.suggest_prevention(failure_mode, failure_reasons)

        return {
            "failure_mode": failure_mode,
            "failure_reasons": failure_reasons,
            "suggestions": suggestions,
            "task_id": task_id,
        }

    def identify_failure_mode(
        self,
        failure_reasons: list[str],
        quality_scores: dict[str, float] | None = None,
    ) -> str:
        """
        Categorize failure into a failure mode.

        Args:
            failure_reasons: List of failure reasons
            quality_scores: Optional quality scores

        Returns:
            Failure mode category
        """
        reasons_str = " ".join(failure_reasons).lower()

        # Categorize based on keywords and quality scores
        if any(
            keyword in reasons_str
            for keyword in ["syntax", "parse", "indentation", "syntaxerror"]
        ):
            return "syntax_error"
        elif any(
            keyword in reasons_str
            for keyword in ["security", "vulnerability", "insecure", "bandit"]
        ):
            return "security_issue"
        elif any(
            keyword in reasons_str
            for keyword in ["timeout", "slow", "performance", "efficiency"]
        ):
            return "performance_issue"
        elif any(
            keyword in reasons_str
            for keyword in ["logic", "incorrect", "wrong", "bug", "error"]
        ):
            return "logic_error"
        elif quality_scores:
            # Check quality scores
            if quality_scores.get("security_score", 10.0) < 5.0:
                return "security_issue"
            elif quality_scores.get("complexity_score", 0.0) > 8.0:
                return "complexity_issue"
            elif quality_scores.get("maintainability_score", 10.0) < 5.0:
                return "maintainability_issue"
            else:
                return "quality_issue"
        else:
            return "unknown_failure"

    def get_common_failure_modes(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get most common failure modes.

        Args:
            limit: Maximum results

        Returns:
            List of failure mode statistics
        """
        modes = sorted(
            self.failure_modes.items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )
        return [
            {
                "mode": mode,
                "count": stats["count"],
                "reasons": list(set(stats["reasons"]))[:5],  # Unique reasons, limit 5
            }
            for mode, stats in modes[:limit]
        ]

    def suggest_prevention(
        self, failure_mode: str, failure_reasons: list[str]
    ) -> list[str]:
        """
        Suggest how to prevent this type of failure.

        Args:
            failure_mode: Failure mode category
            failure_reasons: List of failure reasons

        Returns:
            List of prevention suggestions
        """
        suggestions = []

        if failure_mode == "syntax_error":
            suggestions.append(
                "Use syntax checking tools (e.g., Ruff, pylint) before code execution"
            )
            suggestions.append("Review Python syntax rules and indentation")
        elif failure_mode == "security_issue":
            suggestions.append("Run security scanning (Bandit) before learning patterns")
            suggestions.append("Review security best practices for the language")
            suggestions.append("Avoid insecure patterns (eval, exec, shell=True)")
        elif failure_mode == "performance_issue":
            suggestions.append("Profile code to identify bottlenecks")
            suggestions.append("Review algorithm complexity and optimization opportunities")
            suggestions.append("Consider caching or lazy evaluation")
        elif failure_mode == "logic_error":
            suggestions.append("Add unit tests to catch logic errors early")
            suggestions.append("Use type checking (mypy) to catch type-related issues")
            suggestions.append("Review code logic and edge cases")
        elif failure_mode == "complexity_issue":
            suggestions.append("Refactor complex code into smaller functions")
            suggestions.append("Reduce nesting depth and cyclomatic complexity")
            suggestions.append("Use design patterns to simplify code structure")
        elif failure_mode == "maintainability_issue":
            suggestions.append("Improve code documentation and naming")
            suggestions.append("Follow consistent coding style")
            suggestions.append("Reduce code duplication")
        else:
            suggestions.append("Review failure reasons and improve code quality")
            suggestions.append("Add more comprehensive testing")

        return suggestions


class FeedbackAnalyzer:
    """Analyzes feedback from code scoring system and user input."""

    def __init__(self):
        """Initialize feedback analyzer."""
        self.feedback_history: list[dict[str, Any]] = []

    def analyze_code_scores(
        self, scores: dict[str, float], threshold: float = 0.7
    ) -> dict[str, Any]:
        """
        Analyze code scoring results.

        Args:
            scores: Dictionary of metric scores
            threshold: Quality threshold

        Returns:
            Analysis results
        """
        overall_score = scores.get("overall_score", 0.0)
        metrics_obj: object = scores.get("metrics", {})
        metrics: dict[str, float] = {}
        if isinstance(metrics_obj, dict):
            for metric, score in metrics_obj.items():
                if isinstance(score, (int, float)):
                    metrics[str(metric)] = float(score)

        # Identify weak areas
        weak_areas = [metric for metric, score in metrics.items() if score < threshold]

        # Calculate improvement potential
        improvement_potential = {}
        for metric, score in metrics.items():
            if score < threshold:
                improvement_potential[metric] = threshold - score

        analysis = {
            "overall_score": overall_score,
            "weak_areas": weak_areas,
            "improvement_potential": improvement_potential,
            "meets_threshold": overall_score >= threshold,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.feedback_history.append(analysis)
        return analysis

    def correlate_prompt_changes(
        self, prompt_variants: list[str], quality_scores: list[float]
    ) -> dict[str, float]:
        """
        Correlate prompt changes with quality improvements.

        Args:
            prompt_variants: List of prompt variant identifiers
            quality_scores: Corresponding quality scores

        Returns:
            Dictionary mapping variants to quality scores
        """
        correlations = {}
        for variant, score in zip(prompt_variants, quality_scores, strict=False):
            correlations[variant] = score

        return correlations

    def get_improvement_suggestions(self, analysis: dict[str, Any]) -> list[str]:
        """
        Get improvement suggestions based on analysis.

        Args:
            analysis: Analysis results

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        weak_areas = analysis.get("weak_areas", [])
        improvement_potential = analysis.get("improvement_potential", {})

        for area in weak_areas:
            potential = improvement_potential.get(area, 0.0)
            if potential > 0.1:
                suggestions.append(
                    f"Focus on improving {area} (potential: {potential:.2f})"
                )

        if not suggestions:
            suggestions.append("Code quality is good, maintain current patterns")

        return suggestions


class AgentLearner:
    """
    Core learning engine for agents.

    Integrates pattern extraction, prompt optimization, and feedback analysis.
    """

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        expert_registry: Any,  # ExpertRegistry (required)
        memory_system: TaskMemorySystem | None = None,
        hardware_profile: HardwareProfile | None = None,
    ):
        """
        Initialize agent learner.

        Args:
            capability_registry: Capability registry
            expert_registry: Expert registry for best practices consultation (required)
            memory_system: Optional task memory system
            hardware_profile: Hardware profile (auto-detected if None)
        """
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.capability_registry = capability_registry
        self.memory_system = memory_system
        self.hardware_profile = hardware_profile
        self.learning_intensity = self._get_learning_intensity()

        # Initialize security scanner
        security_scanner = SecurityScanner()

        self.pattern_extractor = PatternExtractor(security_scanner=security_scanner)
        self.anti_pattern_extractor = AntiPatternExtractor(
            security_scanner=security_scanner
        )
        self.negative_feedback_handler = NegativeFeedbackHandler(
            anti_pattern_extractor=self.anti_pattern_extractor
        )
        self.failure_mode_analyzer = FailureModeAnalyzer()
        self.prompt_optimizer = PromptOptimizer(hardware_profile)
        self.feedback_analyzer = FeedbackAnalyzer()

        # Initialize explainability components
        self.decision_logger = DecisionReasoningLogger()
        self.pattern_explainer = PatternSelectionExplainer()
        self.impact_reporter = LearningImpactReporter()

        # Initialize meta-learning components
        self.effectiveness_tracker = LearningEffectivenessTracker()
        self.self_assessor = LearningSelfAssessor()
        self.adaptive_rate = AdaptiveLearningRate()
        self.strategy_selector = LearningStrategySelector()
        self.current_strategy = LearningStrategy.BALANCED

        # Initialize decision engine (always required) with explainability
        best_practice_consultant = BestPracticeConsultant(expert_registry)
        confidence_calculator = LearningConfidenceCalculator()
        self.decision_engine = LearningDecisionEngine(
            capability_registry=self.capability_registry,
            best_practice_consultant=best_practice_consultant,
            confidence_calculator=confidence_calculator,
            decision_logger=self.decision_logger,
        )

        # Initialize dashboard
        self.dashboard = LearningDashboard(
            capability_registry=self.capability_registry,
            pattern_extractor=self.pattern_extractor,
            anti_pattern_extractor=self.anti_pattern_extractor,
            decision_logger=self.decision_logger,
            impact_reporter=self.impact_reporter,
        )

    def _get_learning_intensity(self) -> LearningIntensity:
        """Get learning intensity based on hardware."""
        return self.capability_registry.get_learning_intensity()

    async def learn_from_task(
        self,
        capability_id: str,
        task_id: str,
        code: str | None = None,
        quality_scores: dict[str, float] | None = None,
        success: bool = True,
        duration: float = 0.0,
    ) -> dict[str, Any]:
        """
        Learn from a completed task.

        Args:
            capability_id: Capability identifier
            task_id: Task identifier
            code: Optional source code
            quality_scores: Optional code scoring results
            success: Whether task succeeded
            duration: Task duration

        Returns:
            Learning results
        """
        results: dict[str, Any] = {
            "patterns_extracted": 0,
            "anti_patterns_extracted": 0,
            "prompt_optimized": False,
            "feedback_analyzed": False,
            "security_checked": False,
            "security_score": 0.0,
            "security_vulnerabilities": [],
            "failure_analyzed": False,
        }
        patterns: list[CodePattern] = []
        anti_patterns: list[CodePattern] = []

        # Get before metrics for tracking
        metric = self.capability_registry.get_capability(capability_id)
        before_metrics = {
            "quality_score": metric.quality_score if metric else 0.0,
            "success_rate": metric.success_rate if metric else 0.0,
            "usage_count": metric.usage_count if metric else 0,
        }

        # Extract quality score
        quality_score = 0.5
        if quality_scores:
            quality_score = (
                quality_scores.get("overall_score", 50.0) / 100.0
            )  # Normalize to 0-1 (assumes 0-100 scale)

        # Security check before learning
        security_scanner = SecurityScanner()
        security_result = None
        if code:
            security_result = security_scanner.scan_code(code=code)
            results["security_checked"] = True
            results["security_score"] = security_result["security_score"]
            results["security_vulnerabilities"] = security_result["vulnerabilities"]

            # Skip pattern extraction if security score is too low
            # But continue to extract anti-patterns from vulnerable code
            if not security_scanner.is_safe_for_learning(
                code=code, threshold=self.pattern_extractor.security_threshold
            ):
                logger.debug(
                    f"Skipping pattern extraction for task {task_id}: "
                    f"security score {security_result['security_score']:.2f} "
                    f"below threshold {self.pattern_extractor.security_threshold:.2f}"
                )
                # Still update capability metrics even if we skip pattern extraction
                self.capability_registry.update_capability_metrics(
                    capability_id=capability_id,
                    success=success,
                    duration=duration,
                    quality_score=quality_score,
                )
                # Don't return early - continue to extract anti-patterns from vulnerable code
                # The anti-pattern extraction code below will handle low-quality/vulnerable code

        # Update capability metrics
        self.capability_registry.update_capability_metrics(
            capability_id=capability_id,
            success=success,
            duration=duration,
            quality_score=quality_score,
        )

        # Extract patterns if code provided and quality is good
        # Use decision engine for adaptive threshold, but ensure high-quality code is always extracted
        should_extract_patterns = False
        if code and self.learning_intensity != LearningIntensity.LOW:
            # Base threshold: extract if quality >= 0.7 (normalized 0-1 scale)
            base_threshold = 0.7
            
            # Use decision engine to get adaptive threshold (if available)
            metric = self.capability_registry.get_capability(capability_id)
            learned_data = {
                "usage_count": metric.usage_count if metric else 0,
                "success_rate": metric.success_rate if metric else 0.0,
                "quality_score": quality_score,
                "value": quality_score,  # The threshold value we're considering
                "context_relevance": 1.0,
            }
            context = {
                "hardware_profile": (
                    self.hardware_profile.profile_type.value
                    if hasattr(self.hardware_profile, "profile_type")
                    else "unknown"
                ),
                "learning_intensity": self.learning_intensity.value,
                "task_id": task_id,
                "capability_id": capability_id,
            }

            # Use decision engine (always available)
            decision = await self.decision_engine.make_decision(
                decision_type="pattern_extraction_threshold",
                learned_data=learned_data,
                context=context,
                default_value=base_threshold,
            )

            # Determine threshold value from decision result
            threshold_value = base_threshold  # Default
            if decision.result.value is not None:
                if isinstance(decision.result.value, (int, float)):
                    threshold_value = float(decision.result.value)
                elif isinstance(decision.result.value, str):
                    # Try to extract numeric value from string
                    import re
                    match = re.search(r'(\d+\.?\d*)', str(decision.result.value))
                    if match:
                        threshold_value = float(match.group(1))
            
            # Extract patterns if quality_score meets threshold
            # For new capabilities (low learned_confidence), still extract if quality is high
            should_extract_patterns = quality_score >= threshold_value
            
            # Fallback: if quality is very high (>= 0.8), always extract regardless of decision
            if quality_score >= 0.8:
                should_extract_patterns = True
            
            logger.debug(
                f"Pattern extraction decision: quality_score={quality_score:.3f}, "
                f"threshold={threshold_value:.3f}, should_extract={should_extract_patterns}"
            )

        if should_extract_patterns and code is not None:
            logger.debug(f"Attempting to extract patterns from code (length={len(code)})")
            patterns = self.pattern_extractor.extract_patterns(
                code=code, quality_score=quality_score, task_id=task_id
            )
            logger.debug(f"Extracted {len(patterns)} patterns from code")

            # Store patterns
            for pattern in patterns:
                if pattern.pattern_id not in self.pattern_extractor.patterns:
                    self.pattern_extractor.patterns[pattern.pattern_id] = pattern
                else:
                    # Update existing pattern
                    existing = self.pattern_extractor.patterns[pattern.pattern_id]
                    existing.usage_count += 1
                    existing.learned_from.append(task_id)

            results["patterns_extracted"] = len(patterns)

        # Handle failures: extract anti-patterns
        if not success and code:
            failure_reasons = [f"Task {task_id} failed"]
            if quality_scores:
                # Add quality-based failure reasons
                if quality_scores.get("security_score", 10.0) < 5.0:
                    failure_reasons.append("Low security score")
                if quality_scores.get("overall_score", 100.0) < 50.0:
                    failure_reasons.append("Low overall quality score")

            # Extract anti-patterns from failed code
            anti_patterns = self.anti_pattern_extractor.extract_from_failure(
                code=code,
                task_id=task_id,
                failure_reasons=failure_reasons,
                quality_score=quality_score,
            )

            # Store anti-patterns
            for anti_pattern in anti_patterns:
                if anti_pattern.pattern_id not in self.anti_pattern_extractor.anti_patterns:
                    self.anti_pattern_extractor.anti_patterns[
                        anti_pattern.pattern_id
                    ] = anti_pattern
                else:
                    # Update existing anti-pattern
                    existing = self.anti_pattern_extractor.anti_patterns[
                        anti_pattern.pattern_id
                    ]
                    existing.usage_count += 1
                    existing.learned_from.append(task_id)

            results["anti_patterns_extracted"] = len(anti_patterns)

            # Analyze failure mode
            failure_analysis = self.failure_mode_analyzer.analyze_failure(
                code=code,
                task_id=task_id,
                failure_reasons=failure_reasons,
                quality_scores=quality_scores,
            )
            results["failure_analyzed"] = True
            results["failure_analysis"] = failure_analysis

        # Also extract anti-patterns from low-quality code (even if success=True)
        logger.debug(f"Anti-pattern extraction check: code={code is not None}, quality_score={quality_score}, threshold={self.anti_pattern_extractor.max_quality_threshold}, success={success}")
        if code and quality_score < self.anti_pattern_extractor.max_quality_threshold:
            failure_reasons = [f"Low quality score: {quality_score:.2f}"]
            anti_patterns = self.anti_pattern_extractor.extract_anti_patterns(
                code=code,
                quality_score=quality_score,
                task_id=task_id,
                failure_reasons=failure_reasons,
            )

            # Store anti-patterns
            for anti_pattern in anti_patterns:
                if anti_pattern.pattern_id not in self.anti_pattern_extractor.anti_patterns:
                    self.anti_pattern_extractor.anti_patterns[
                        anti_pattern.pattern_id
                    ] = anti_pattern

            results["anti_patterns_extracted"] = len(anti_patterns)

        # Analyze feedback if scores provided
        if quality_scores:
            analysis = self.feedback_analyzer.analyze_code_scores(quality_scores)
            results["feedback_analyzed"] = True
            results["feedback_analysis"] = analysis

            # Check if improvement is needed
            if not analysis.get("meets_threshold", False):
                suggestions = self.feedback_analyzer.get_improvement_suggestions(
                    analysis
                )
                results["improvement_suggestions"] = suggestions

        # Store in memory system if available
        if self.memory_system and success:
            outcome = TaskOutcome.SUCCESS if success else TaskOutcome.FAILURE
            self.memory_system.store_memory(
                task_id=task_id,
                agent_id="unknown",  # Would be provided by agent
                command=capability_id,
                outcome=outcome,
                quality_score=quality_score,
                patterns_used=[p.pattern_id for p in patterns] if code else [],
            )

        # Track learning effectiveness
        metric_after = self.capability_registry.get_capability(capability_id)
        after_metrics = {
            "quality_score": metric_after.quality_score if metric_after else 0.0,
            "success_rate": metric_after.success_rate if metric_after else 0.0,
            "usage_count": metric_after.usage_count if metric_after else 0,
        }

        # Track effectiveness
        session = self.effectiveness_tracker.track_effectiveness(
            capability_id=capability_id,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            strategies_used=[self.current_strategy.value],
        )

        # Adjust learning rate based on effectiveness
        rate_adjustment = self.adaptive_rate.adjust_learning_intensity(
            session.effectiveness_score
        )
        results["learning_rate_adjustment"] = rate_adjustment

        # Generate impact report
        impact_report = self.impact_reporter.generate_impact_report(
            capability_id=capability_id,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            learning_session_id=session.session_id,
        )
        results["learning_impact"] = impact_report

        return results

    async def learn_from_rejection(
        self,
        capability_id: str,
        task_id: str,
        code: str,
        rejection_reason: str,
        quality_score: float = 0.5,
    ) -> dict[str, Any]:
        """
        Learn from user rejection.

        Args:
            capability_id: Capability identifier
            task_id: Task identifier
            code: Rejected code
            rejection_reason: Reason for rejection
            quality_score: Quality score

        Returns:
            Learning results
        """
        results: dict[str, Any] = {
            "anti_patterns_extracted": 0,
            "rejection_recorded": False,
        }

        # Record rejection and extract anti-patterns
        anti_patterns = self.negative_feedback_handler.record_rejection(
            code=code,
            task_id=task_id,
            reason=rejection_reason,
            quality_score=quality_score,
        )

        results["anti_patterns_extracted"] = len(anti_patterns)
        results["rejection_recorded"] = True

        # Update capability metrics (rejection counts as failure)
        self.capability_registry.update_capability_metrics(
            capability_id=capability_id,
            success=False,
            duration=0.0,
            quality_score=quality_score,
        )

        return results

    def get_learned_patterns(
        self,
        context: str,
        pattern_type: str | None = None,
        limit: int = 5,
        exclude_anti_patterns: bool = True,
    ) -> list[CodePattern]:
        """
        Get learned patterns for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results
            exclude_anti_patterns: If True, exclude anti-patterns (default: True)

        Returns:
            List of relevant patterns
        """
        return self.pattern_extractor.get_patterns_for_context(
            context=context,
            pattern_type=pattern_type,
            limit=limit,
            exclude_anti_patterns=exclude_anti_patterns,
        )

    def optimize_prompt(self, base_prompt: str, context: str | None = None) -> str:
        """
        Get optimized prompt.

        Args:
            base_prompt: Base prompt
            context: Optional context

        Returns:
            Optimized prompt
        """
        # Get best variant if available
        best_variant = self.prompt_optimizer.get_best_variant()
        if best_variant and best_variant.average_quality > 0.7:
            return best_variant.prompt_template

        # Otherwise, optimize for hardware
        return self.prompt_optimizer.optimize_for_hardware(base_prompt)

    def explain_learning(
        self,
        capability_id: str,
        task_id: str | None = None,
        decision_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate explanation for learning process.

        Args:
            capability_id: Capability identifier
            task_id: Optional task identifier
            decision_id: Optional decision identifier

        Returns:
            Explanation dictionary
        """
        explanation: dict[str, Any] = {
            "capability_id": capability_id,
            "task_id": task_id,
        }

        # Get decision explanation if decision_id provided
        if decision_id:
            decision_explanation = self.decision_logger.explain_decision(decision_id)
            if decision_explanation:
                explanation["decision"] = decision_explanation

        # Get pattern selection explanation
        patterns = self.get_learned_patterns(
            context=capability_id, exclude_anti_patterns=True
        )
        if patterns:
            pattern_explanation = self.pattern_explainer.explain_pattern_selection(
                selected_patterns=patterns, context=capability_id
            )
            explanation["pattern_selection"] = pattern_explanation

        # Get decision statistics
        explanation["decision_statistics"] = self.decision_logger.get_decision_statistics()

        return explanation

    async def optimize_learning(
        self, capability_id: str | None = None
    ) -> dict[str, Any]:
        """
        Run meta-learning optimization.

        Args:
            capability_id: Optional filter by capability

        Returns:
            Optimization report
        """
        optimization: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "capability_id": capability_id,
        }

        # Assess learning quality
        pattern_count = len(self.pattern_extractor.patterns)
        anti_pattern_count = len(self.anti_pattern_extractor.anti_patterns)

        # Calculate average quality and security
        avg_quality = 0.0
        avg_security = 0.0
        if self.pattern_extractor.patterns:
            total_quality = sum(p.quality_score for p in self.pattern_extractor.patterns.values())
            total_security = sum(
                getattr(p, "security_score", 0.0)
                for p in self.pattern_extractor.patterns.values()
            )
            avg_quality = total_quality / len(self.pattern_extractor.patterns)
            avg_security = total_security / len(self.pattern_extractor.patterns)

        quality_assessment = self.self_assessor.assess_learning_quality(
            pattern_count=pattern_count,
            anti_pattern_count=anti_pattern_count,
            average_quality=avg_quality,
            average_security=avg_security,
        )
        optimization["quality_assessment"] = quality_assessment

        # Identify learning gaps
        capability_metrics = {}
        if capability_id:
            metric = self.capability_registry.get_capability(capability_id)
            if metric:
                capability_metrics = {
                    "success_rate": metric.success_rate,
                    "quality_score": metric.quality_score,
                    "usage_count": metric.usage_count,
                }
        pattern_stats = {
            "total_patterns": pattern_count,
            "average_quality": avg_quality,
            "average_security": avg_security,
        }
        gaps = self.self_assessor.identify_learning_gaps(
            capability_metrics=capability_metrics,
            pattern_statistics=pattern_stats,
        )
        optimization["learning_gaps"] = gaps

        # Get improvement suggestions
        suggestions = self.self_assessor.suggest_improvements(quality_assessment)
        optimization["improvement_suggestions"] = suggestions

        # Select optimal strategy
        if capability_id:
            metric = self.capability_registry.get_capability(capability_id)
            current_effectiveness = metric.success_rate if metric else 0.5
        else:
            # Use average effectiveness
            roi = self.effectiveness_tracker.get_learning_roi(capability_id=capability_id)
            current_effectiveness = roi.get("average_effectiveness", 0.5)

        hardware_profile_str = (
            self.hardware_profile.profile_type.value
            if hasattr(self.hardware_profile, "profile_type")
            else None
        )
        optimal_strategy = self.strategy_selector.select_strategy(
            capability_id=capability_id or "global",
            current_effectiveness=current_effectiveness,
            hardware_profile=hardware_profile_str,
        )
        optimization["optimal_strategy"] = optimal_strategy.value
        optimization["current_strategy"] = self.current_strategy.value

        # Optimize thresholds
        current_threshold = self.pattern_extractor.min_quality_threshold
        metric = self.capability_registry.get_capability(capability_id) if capability_id else None
        success_rate = metric.success_rate if metric else 0.5
        optimized_threshold = self.adaptive_rate.optimize_thresholds(
            current_threshold=current_threshold,
            success_rate=success_rate,
            quality_score=avg_quality,
        )
        optimization["optimized_threshold"] = optimized_threshold
        optimization["current_threshold"] = current_threshold

        # Update strategy if better one found
        if optimal_strategy != self.current_strategy:
            switch_result = self.strategy_selector.switch_strategy(
                current_strategy=self.current_strategy,
                new_strategy=optimal_strategy,
            )
            if switch_result["switched"]:
                self.current_strategy = optimal_strategy
                optimization["strategy_switched"] = True
                optimization["switch_result"] = switch_result
            else:
                optimization["strategy_switched"] = False

        # Get effectiveness metrics
        effectiveness_metrics = self.effectiveness_tracker.get_learning_roi(
            capability_id=capability_id
        )
        optimization["effectiveness_metrics"] = effectiveness_metrics

        return optimization

    def should_refine_capability(self, capability_id: str) -> bool:
        """
        Determine if a capability should be refined.

        Args:
            capability_id: Capability identifier

        Returns:
            True if refinement is recommended
        """
        metric = self.capability_registry.get_capability(capability_id)
        if not metric:
            return False

        # Refine if quality is below threshold and has enough usage
        return metric.quality_score < 0.7 and metric.usage_count >= 10
