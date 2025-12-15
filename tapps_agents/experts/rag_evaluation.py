"""
RAG Evaluation - Quality metrics and evaluation sets for RAG system.

Provides:
- Golden Q/A evaluation sets
- Metrics: latency, hit rate, relevance scoring
- CI regression detection
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvaluationQuestion:
    """A question in the evaluation set."""

    question: str
    expected_snippets: list[str] = field(default_factory=list)  # Expected text snippets in results
    expected_answers: list[str] = field(default_factory=list)  # Expected answer patterns
    domain: str = ""
    min_relevance: float = 0.7  # Minimum relevance score to pass


@dataclass
class EvaluationResult:
    """Result of evaluating a single question."""

    question: str
    retrieved_chunks: list[str]
    relevance_scores: list[float]
    hit_rate: float  # Fraction of expected snippets found
    latency_ms: float
    passed: bool
    error: str | None = None


@dataclass
class EvaluationMetrics:
    """Aggregated metrics from evaluation run."""

    total_questions: int
    passed_questions: int
    average_latency_ms: float
    average_hit_rate: float
    average_relevance: float
    failed_questions: list[str] = field(default_factory=list)
    regression_detected: bool = False


class RAGEvaluator:
    """
    Evaluates RAG system quality using golden Q/A sets.

    Features:
    - Load evaluation sets from JSON
    - Measure latency, hit rate, relevance
    - Detect regressions (fail CI on major regressions)
    """

    def __init__(self, evaluation_file: Path | None = None):
        """
        Initialize evaluator.

        Args:
            evaluation_file: Path to evaluation set JSON file
        """
        self.evaluation_file = evaluation_file
        self.questions: list[EvaluationQuestion] = []

    def load_evaluation_set(self, evaluation_file: Path | None = None) -> None:
        """
        Load evaluation set from JSON file.

        Format:
        {
            "questions": [
                {
                    "question": "What is X?",
                    "expected_snippets": ["X is", "X means"],
                    "expected_answers": ["X is a"],
                    "domain": "security",
                    "min_relevance": 0.7
                }
            ]
        }
        """
        eval_file = evaluation_file or self.evaluation_file
        if not eval_file or not eval_file.exists():
            logger.warning(f"Evaluation file not found: {eval_file}")
            return

        try:
            with open(eval_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.questions = []
            for q_data in data.get("questions", []):
                question = EvaluationQuestion(
                    question=q_data["question"],
                    expected_snippets=q_data.get("expected_snippets", []),
                    expected_answers=q_data.get("expected_answers", []),
                    domain=q_data.get("domain", ""),
                    min_relevance=q_data.get("min_relevance", 0.7),
                )
                self.questions.append(question)

            logger.info(f"Loaded {len(self.questions)} evaluation questions")
        except Exception as e:
            logger.error(f"Failed to load evaluation set: {e}", exc_info=True)
            raise

    def evaluate(
        self,
        search_func: callable,
        max_results: int = 5,
        latency_threshold_ms: float = 2000.0,
        min_hit_rate: float = 0.5,
    ) -> EvaluationMetrics:
        """
        Evaluate RAG system using loaded questions.

        Args:
            search_func: Function that takes (query, max_results) and returns list of (chunk, score) tuples
            max_results: Maximum results to retrieve
            latency_threshold_ms: Maximum acceptable latency in milliseconds
            min_hit_rate: Minimum hit rate to pass (0.0-1.0)

        Returns:
            EvaluationMetrics with aggregated results
        """
        if not self.questions:
            raise ValueError("No evaluation questions loaded. Call load_evaluation_set() first.")

        results: list[EvaluationResult] = []
        total_latency = 0.0
        total_hit_rate = 0.0
        total_relevance = 0.0

        for question in self.questions:
            try:
                # Measure latency
                start_time = time.time()
                retrieved = search_func(question.question, max_results=max_results)
                elapsed_ms = (time.time() - start_time) * 1000.0
                total_latency += elapsed_ms

                # Extract chunks and scores
                chunks = [chunk for chunk, _ in retrieved] if retrieved else []
                scores = [score for _, score in retrieved] if retrieved else []

                # Calculate hit rate (fraction of expected snippets found)
                hit_rate = self._calculate_hit_rate(chunks, question.expected_snippets)
                total_hit_rate += hit_rate

                # Calculate average relevance
                avg_relevance = sum(scores) / len(scores) if scores else 0.0
                total_relevance += avg_relevance

                # Determine if passed
                passed = (
                    elapsed_ms <= latency_threshold_ms
                    and hit_rate >= min_hit_rate
                    and avg_relevance >= question.min_relevance
                )

                result = EvaluationResult(
                    question=question.question,
                    retrieved_chunks=[str(c) for c in chunks[:3]],  # Store first 3 for debugging
                    relevance_scores=scores[:3],
                    hit_rate=hit_rate,
                    latency_ms=elapsed_ms,
                    passed=passed,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Evaluation failed for question: {question.question}: {e}", exc_info=True)
                result = EvaluationResult(
                    question=question.question,
                    retrieved_chunks=[],
                    relevance_scores=[],
                    hit_rate=0.0,
                    latency_ms=0.0,
                    passed=False,
                    error=str(e),
                )
                results.append(result)

        # Aggregate metrics
        num_questions = len(self.questions)
        passed_count = sum(1 for r in results if r.passed)
        avg_latency = total_latency / num_questions if num_questions > 0 else 0.0
        avg_hit_rate = total_hit_rate / num_questions if num_questions > 0 else 0.0
        avg_relevance = total_relevance / num_questions if num_questions > 0 else 0.0

        failed_questions = [r.question for r in results if not r.passed]

        # Detect regression (if >30% failure rate)
        regression_detected = (passed_count / num_questions) < 0.7 if num_questions > 0 else False

        metrics = EvaluationMetrics(
            total_questions=num_questions,
            passed_questions=passed_count,
            average_latency_ms=avg_latency,
            average_hit_rate=avg_hit_rate,
            average_relevance=avg_relevance,
            failed_questions=failed_questions,
            regression_detected=regression_detected,
        )

        return metrics

    def _calculate_hit_rate(self, chunks: list[str], expected_snippets: list[str]) -> float:
        """
        Calculate hit rate: fraction of expected snippets found in chunks.

        Args:
            chunks: Retrieved chunk texts
            expected_snippets: Expected text snippets

        Returns:
            Hit rate (0.0-1.0)
        """
        if not expected_snippets:
            return 1.0  # No expectations = perfect hit rate

        if not chunks:
            return 0.0

        # Check if each expected snippet appears in any chunk
        chunks_text = " ".join(chunks).lower()
        found_count = sum(
            1 for snippet in expected_snippets if snippet.lower() in chunks_text
        )

        return found_count / len(expected_snippets)

    def save_metrics(self, metrics: EvaluationMetrics, output_file: Path) -> None:
        """Save evaluation metrics to JSON file."""
        data = {
            "total_questions": metrics.total_questions,
            "passed_questions": metrics.passed_questions,
            "average_latency_ms": metrics.average_latency_ms,
            "average_hit_rate": metrics.average_hit_rate,
            "average_relevance": metrics.average_relevance,
            "failed_questions": metrics.failed_questions,
            "regression_detected": metrics.regression_detected,
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Evaluation metrics saved to {output_file}")


def create_default_evaluation_set(output_file: Path) -> None:
    """
    Create a default evaluation set for testing.

    Args:
        output_file: Path to save evaluation set JSON
    """
    default_set = {
        "questions": [
            {
                "question": "What are security best practices for API authentication?",
                "expected_snippets": ["authentication", "security", "token"],
                "expected_answers": ["JWT", "OAuth", "API key"],
                "domain": "security",
                "min_relevance": 0.7,
            },
            {
                "question": "How should I handle database connection pooling?",
                "expected_snippets": ["connection", "pool", "database"],
                "expected_answers": ["pooling", "connection pool"],
                "domain": "database",
                "min_relevance": 0.7,
            },
            {
                "question": "What are performance optimization techniques?",
                "expected_snippets": ["performance", "optimization", "cache"],
                "expected_answers": ["caching", "indexing", "query optimization"],
                "domain": "performance-optimization",
                "min_relevance": 0.7,
            },
        ]
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(default_set, f, indent=2)

    logger.info(f"Default evaluation set created at {output_file}")
