"""
React Scorer - Code quality scoring for React files (.tsx, .jsx)

Phase 1.2: Language-Specific Scorers
"""

import re
from pathlib import Path
from typing import Any

from ...core.language_detector import Language
from .scoring import BaseScorer
from .typescript_scorer import TypeScriptScorer


class ReactScorer(BaseScorer):
    """
    Calculate code quality scores for React files (.tsx, .jsx).

    Extends TypeScriptScorer with React-specific analysis:
    - React hooks usage (useState, useMemo, useEffect, useCallback)
    - Component prop type safety
    - JSX pattern analysis
    - Performance patterns (memoization, re-renders)
    - React best practices validation
    """

    def __init__(
        self,
        typescript_scorer: TypeScriptScorer | None = None,
        eslint_config: str | None = None,
        tsconfig_path: str | None = None,
    ):
        """
        Initialize React scorer.

        Args:
            typescript_scorer: Optional TypeScriptScorer instance to reuse
            eslint_config: Path to ESLint config file (optional)
            tsconfig_path: Path to tsconfig.json (optional)
        """
        # Use provided TypeScript scorer or create new one
        if typescript_scorer:
            self.typescript_scorer = typescript_scorer
        else:
            self.typescript_scorer = TypeScriptScorer(
                eslint_config=eslint_config, tsconfig_path=tsconfig_path
            )

    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Score a React file (.tsx, .jsx).

        Args:
            file_path: Path to the file
            code: File content

        Returns:
            Dictionary with scores (extends TypeScriptScorer scores with React-specific metrics):
            {
                "complexity_score": float (0-10),
                "security_score": float (0-10),
                "maintainability_score": float (0-10),
                "test_coverage_score": float (0-10),
                "performance_score": float (0-10),
                "linting_score": float (0-10),
                "type_checking_score": float (0-10),
                "react_score": float (0-10),  # React-specific score
                "overall_score": float (0-100),
                "metrics": {...}
            }
        """
        # Get base TypeScript scores
        base_scores = self.typescript_scorer.score_file(file_path, code)

        # Calculate React-specific score
        react_score = self._calculate_react_score(code, file_path)

        # Phase 3.1: Use context-aware maintainability scorer
        from .maintainability_scorer import MaintainabilityScorer

        maintainability_scorer = MaintainabilityScorer()
        maintainability_score = maintainability_scorer.calculate(
            code, Language.REACT, file_path, context=None
        )

        # Enhance performance with React optimizations
        # Phase 3.2: Use context-aware performance scorer
        from ...core.language_detector import Language
        from .performance_scorer import PerformanceScorer

        performance_scorer = PerformanceScorer()
        performance_score = performance_scorer.calculate(
            code, Language.REACT, file_path, context=None
        )

        # Update scores
        base_scores["react_score"] = react_score
        base_scores["maintainability_score"] = maintainability_score
        base_scores["performance_score"] = performance_score

        # Recalculate overall score with React score included
        # Weights: complexity 20%, security 15%, maintainability 25%,
        #          test_coverage 15%, performance 10%, linting 10%, type_checking 5%, react 0%
        # (React score is already factored into maintainability and performance)
        base_scores["overall_score"] = (
            (10 - base_scores.get("complexity_score", 5.0)) * 0.20
            + base_scores.get("security_score", 5.0) * 0.15
            + maintainability_score * 0.25
            + base_scores.get("test_coverage_score", 0.0) * 0.15
            + performance_score * 0.10
            + base_scores.get("linting_score", 0.0) * 0.10
            + base_scores.get("type_checking_score", 0.0) * 0.05
        ) * 10

        # Add React-specific metrics
        metrics = base_scores.get("metrics", {})
        metrics["react_score"] = float(react_score)
        metrics["react_hooks_count"] = self._count_react_hooks(code)
        metrics["react_memoization_count"] = self._count_memoization_patterns(code)
        metrics["react_components_count"] = self._count_react_components(code)
        base_scores["metrics"] = metrics

        # Phase 3.3: Validate all scores before returning
        from ...core.language_detector import Language
        from .score_validator import ScoreValidator

        validator = ScoreValidator()
        validation_results = validator.validate_all_scores(
            base_scores, language=Language.REACT, context=None
        )

        # Update scores with validated/clamped values and add explanations
        validated_scores = {}
        score_explanations = {}
        for category, result in validation_results.items():
            if result.valid and result.calibrated_score is not None:
                validated_scores[category] = result.calibrated_score
                if result.explanation:
                    score_explanations[category] = {
                        "explanation": result.explanation,
                        "suggestions": result.suggestions,
                    }
            else:
                validated_scores[category] = base_scores.get(category, 0.0)

        # Merge validated scores back into base_scores
        for key, value in validated_scores.items():
            if key != "_explanations":
                base_scores[key] = value

        # Add explanations to result if any
        if score_explanations:
            base_scores["_explanations"] = score_explanations

        return base_scores

    def _calculate_react_score(self, code: str, file_path: Path | None = None) -> float:
        """
        Calculate React-specific quality score (0-10).

        Analyzes:
        - React hooks usage patterns
        - Component structure
        - JSX patterns
        - React best practices
        """
        score = 0.0

        # Check for React imports
        if not re.search(r"import.*from\s+['\"]react['\"]", code):
            return 0.0  # Not a React file

        score += 1.0  # Base score for React file

        # Analyze hooks usage
        hooks = self._analyze_hooks_usage(code)
        if hooks["proper_usage"]:
            score += 2.0
        if hooks["has_use_memo"]:
            score += 1.0
        if hooks["has_use_callback"]:
            score += 1.0
        if hooks["has_error_boundary"]:
            score += 1.0

        # Analyze component patterns
        components = self._analyze_component_patterns(code)
        if components["has_prop_types"]:
            score += 1.0
        if components["has_memo"]:
            score += 1.0
        if components["proper_structure"]:
            score += 1.0

        # Check for React best practices
        if self._check_react_best_practices(code):
            score += 1.0

        return min(score, 10.0)

    def _calculate_react_maintainability_boost(self, code: str) -> float:
        """Calculate maintainability boost from React patterns (0-2.0)."""
        boost = 0.0

        # Type safety for props
        if re.search(r"interface\s+\w+Props|type\s+\w+Props", code):
            boost += 0.5

        # Proper component structure
        if re.search(r"(export\s+)?(const|function)\s+\w+\s*[:=]\s*(\([^)]*\)\s*=>|React\.FC)", code):
            boost += 0.5

        # Error handling
        if re.search(r"try\s*\{|ErrorBoundary|componentDidCatch", code):
            boost += 0.5

        # Documentation (JSDoc)
        if re.search(r"/\*\*.*\*/", code, re.DOTALL):
            boost += 0.5

        return min(boost, 2.0)

    def _calculate_react_performance_boost(self, code: str) -> float:
        """Calculate performance boost from React optimizations (0-3.0)."""
        boost = 0.0

        # Memoization patterns
        if re.search(r"React\.memo|memo\(|useMemo\(|useCallback\(", code):
            boost += 1.5

        # Lazy loading
        if re.search(r"lazy\(|React\.lazy", code):
            boost += 1.0

        # Code splitting
        if re.search(r"import\(|dynamic\s+import", code):
            boost += 0.5

        return min(boost, 3.0)

    def _analyze_hooks_usage(self, code: str) -> dict[str, bool]:
        """Analyze React hooks usage patterns."""
        return {
            "has_use_state": bool(re.search(r"useState\(", code)),
            "has_use_effect": bool(re.search(r"useEffect\(", code)),
            "has_use_memo": bool(re.search(r"useMemo\(", code)),
            "has_use_callback": bool(re.search(r"useCallback\(", code)),
            "has_use_ref": bool(re.search(r"useRef\(", code)),
            "proper_usage": self._check_proper_hooks_usage(code),
            "has_error_boundary": bool(
                re.search(r"componentDidCatch|getDerivedStateFromError|ErrorBoundary", code)
            ),
        }

    def _check_proper_hooks_usage(self, code: str) -> bool:
        """Check if hooks are used properly (rules of hooks)."""
        # Check for hooks in conditionals (bad practice)
        if re.search(r"(if|for|while)\s*\([^)]*\)\s*\{[^}]*use(State|Effect|Memo|Callback)", code):
            return False

        # Check for hooks at top level (good practice)
        # This is a simplified check - full analysis would require AST parsing
        return True

    def _analyze_component_patterns(self, code: str) -> dict[str, bool]:
        """Analyze React component patterns."""
        return {
            "has_prop_types": bool(
                re.search(r"interface\s+\w+Props|type\s+\w+Props|PropTypes", code)
            ),
            "has_memo": bool(re.search(r"React\.memo\(|memo\(", code)),
            "proper_structure": bool(
                re.search(r"(export\s+)?(const|function)\s+\w+\s*[:=]\s*", code)
            ),
            "has_default_props": bool(re.search(r"defaultProps\s*=|\.defaultProps", code)),
        }

    def _check_react_best_practices(self, code: str) -> bool:
        """Check for React best practices."""
        # Check for key prop in lists
        has_key_in_jsx = bool(re.search(r"<[^>]+\bkey\s*=", code))

        # Check for proper event handling
        has_event_handlers = bool(re.search(r"on[A-Z]\w+\s*=\s*\{", code))

        # Check for controlled components
        has_controlled_inputs = bool(
            re.search(r"value\s*=\s*\{[^}]+\}\s+onChange", code)
        )

        return has_key_in_jsx or (has_event_handlers and has_controlled_inputs)

    def _count_react_hooks(self, code: str) -> int:
        """Count React hooks in code."""
        hooks = [
            "useState",
            "useEffect",
            "useMemo",
            "useCallback",
            "useRef",
            "useContext",
            "useReducer",
        ]
        count = 0
        for hook in hooks:
            count += len(re.findall(rf"\b{hook}\s*\(", code))
        return count

    def _count_memoization_patterns(self, code: str) -> int:
        """Count memoization patterns."""
        count = 0
        count += len(re.findall(r"React\.memo\(|memo\(", code))
        count += len(re.findall(r"useMemo\(", code))
        count += len(re.findall(r"useCallback\(", code))
        return count

    def _count_react_components(self, code: str) -> int:
        """Count React components defined in code."""
        # Count function components
        function_components = len(
            re.findall(
                r"(export\s+)?(const|function)\s+\w+\s*[:=]\s*(\([^)]*\)\s*=>|React\.FC)",
                code,
            )
        )
        # Count class components
        class_components = len(re.findall(r"class\s+\w+\s+extends\s+React\.Component", code))
        return function_components + class_components

