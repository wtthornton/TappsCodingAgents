"""
Agent Learning System

Enables agents to learn from past tasks and improve over time.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .best_practice_consultant import BestPracticeConsultant
from .capability_registry import CapabilityRegistry, LearningIntensity
from .hardware_profiler import HardwareProfile, HardwareProfiler
from .learning_confidence import LearningConfidenceCalculator
from .learning_decision import LearningDecisionEngine
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

    def __init__(self, min_quality_threshold: float = 0.7):
        """
        Initialize pattern extractor.

        Args:
            min_quality_threshold: Minimum quality score to extract patterns
        """
        self.min_quality_threshold = min_quality_threshold
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

        # Match function definitions
        func_pattern = r"def\s+(\w+)\s*\([^)]*\):\s*\n((?:\s{4}.*\n?)*)"
        matches = re.finditer(func_pattern, code, re.MULTILINE)

        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2)

            pattern = CodePattern(
                pattern_id=f"func_{func_name}_{hash(func_body) % 10000}",
                pattern_type="function",
                code_snippet=f"def {func_name}(...):\n{func_body[:200]}",  # Truncate
                context=f"Function: {func_name}",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
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

            pattern = CodePattern(
                pattern_id=f"class_{class_name}_{hash(class_body) % 10000}",
                pattern_type="class",
                code_snippet=f"class {class_name}:\n{class_body[:200]}",
                context=f"Class: {class_name}",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
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
            pattern = CodePattern(
                pattern_id=f"imports_{hash(''.join(imports)) % 10000}",
                pattern_type="import",
                code_snippet="\n".join(imports[:10]),  # Limit to 10 imports
                context="Import statements",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
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
            pattern = CodePattern(
                pattern_id=f"decorators_{hash(''.join(decorators)) % 10000}",
                pattern_type="structure",
                code_snippet="\n".join(decorators[:5]),
                context="Decorators",
                quality_score=quality_score,
                usage_count=1,
                success_rate=1.0,
                learned_from=[task_id],
            )
            patterns.append(pattern)

        return patterns

    def get_patterns_for_context(
        self, context: str, pattern_type: str | None = None, limit: int = 5
    ) -> list[CodePattern]:
        """
        Get relevant patterns for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results

        Returns:
            List of relevant patterns
        """
        candidates = list(self.patterns.values())

        if pattern_type:
            candidates = [p for p in candidates if p.pattern_type == pattern_type]

        # Sort by quality and usage
        candidates.sort(key=lambda p: (p.quality_score, p.usage_count), reverse=True)

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
            created_at=datetime.utcnow(),
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
        variant.last_tested = datetime.utcnow()

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
            "timestamp": datetime.utcnow().isoformat(),
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

        self.pattern_extractor = PatternExtractor()
        self.prompt_optimizer = PromptOptimizer(hardware_profile)
        self.feedback_analyzer = FeedbackAnalyzer()

        # Initialize decision engine (always required)
        best_practice_consultant = BestPracticeConsultant(expert_registry)
        confidence_calculator = LearningConfidenceCalculator()
        self.decision_engine = LearningDecisionEngine(
            capability_registry=self.capability_registry,
            best_practice_consultant=best_practice_consultant,
            confidence_calculator=confidence_calculator,
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
            "prompt_optimized": False,
            "feedback_analyzed": False,
        }
        patterns: list[CodePattern] = []

        # Extract quality score
        quality_score = 0.5
        if quality_scores:
            quality_score = (
                quality_scores.get("overall_score", 0.5) / 10.0
            )  # Normalize to 0-1

        # Update capability metrics
        self.capability_registry.update_capability_metrics(
            capability_id=capability_id,
            success=success,
            duration=duration,
            quality_score=quality_score,
        )

        # Extract patterns if code provided and quality is good
        # Always use decision engine to determine if we should extract patterns
        should_extract_patterns = False
        if code and self.learning_intensity != LearningIntensity.LOW:
            # Use decision engine to determine if we should extract patterns
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
                default_value=0.7,
            )

            # Determine if we should extract based on decision
            should_extract_patterns = decision.result.should_proceed
            # If decision provides a threshold value, use it
            if decision.result.value is not None and isinstance(
                decision.result.value, (int, float)
            ):
                should_extract_patterns = quality_score >= decision.result.value

        if should_extract_patterns and code is not None:
            patterns = self.pattern_extractor.extract_patterns(
                code=code, quality_score=quality_score, task_id=task_id
            )

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

        return results

    def get_learned_patterns(
        self, context: str, pattern_type: str | None = None, limit: int = 5
    ) -> list[CodePattern]:
        """
        Get learned patterns for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results

        Returns:
            List of relevant patterns
        """
        return self.pattern_extractor.get_patterns_for_context(
            context=context, pattern_type=pattern_type, limit=limit
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
