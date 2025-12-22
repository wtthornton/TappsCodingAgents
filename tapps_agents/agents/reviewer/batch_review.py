"""
Batch Review Workflow - Review multiple services in parallel

Phase 4.2: Batch Review Workflow

Uses asyncio.TaskGroup for parallel execution following ParallelStepExecutor patterns.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ...core.config import ProjectConfig
from ...core.language_detector import Language
from .agent import ReviewerAgent
from .service_discovery import Service

logger = logging.getLogger(__name__)

# Default timeout for service review (5 minutes)
DEFAULT_REVIEW_TIMEOUT = 300.0


class ServiceReviewResult(BaseModel):
    """Result of reviewing a single service."""

    service_name: str
    service_path: str
    language: str
    passed: bool
    overall_score: float
    scores: dict[str, float] = Field(default_factory=dict)
    error: str | None = None
    review_details: dict[str, Any] = Field(default_factory=dict)


class BatchReviewResult(BaseModel):
    """Result of batch review workflow."""

    services_reviewed: int
    passed: int
    failed: int
    average_score: float
    results: list[ServiceReviewResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class BatchReviewWorkflow:
    """
    Batch review workflow for reviewing multiple services.

    Phase 4.2: Batch Review Workflow
    Uses asyncio.TaskGroup for parallel execution (Python 3.11+).
    """

    def __init__(
        self,
        config: ProjectConfig | None = None,
        project_root: Path | None = None,
        max_parallel: int = 4,
        review_timeout: float = DEFAULT_REVIEW_TIMEOUT,
    ):
        """
        Initialize batch review workflow.

        Args:
            config: Optional project configuration
            project_root: Optional project root directory
            max_parallel: Maximum number of parallel reviews (default: 4)
            review_timeout: Timeout in seconds for single service review (default: 300.0)
        """
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.max_parallel = max_parallel
        self.review_timeout = review_timeout

    async def review_services(
        self,
        services: list[Service],
        parallel: bool = True,
        include_scoring: bool = True,
        include_llm_feedback: bool = True,
    ) -> BatchReviewResult:
        """
        Review multiple services in parallel or sequentially.

        Phase 4.2: Batch Review with Parallel Execution

        Args:
            services: List of Service objects to review
            parallel: Whether to execute reviews in parallel (default: True)
            include_scoring: Whether to include code quality scoring
            include_llm_feedback: Whether to include LLM feedback

        Returns:
            BatchReviewResult with aggregated results
        """
        if not services:
            return BatchReviewResult(
                services_reviewed=0,
                passed=0,
                failed=0,
                average_score=0.0,
            )

        if parallel:
            return await self._review_services_parallel(
                services, include_scoring, include_llm_feedback
            )
        else:
            return await self._review_services_sequential(
                services, include_scoring, include_llm_feedback
            )

    async def _review_services_parallel(
        self,
        services: list[Service],
        include_scoring: bool,
        include_llm_feedback: bool,
    ) -> BatchReviewResult:
        """
        Review services in parallel using asyncio.TaskGroup.

        Phase 4.2: Parallel Execution with TaskGroup
        """
        results: list[ServiceReviewResult] = []
        errors: list[str] = []

        # Use TaskGroup for structured concurrency (Python 3.11+)
        if sys.version_info >= (3, 11):
            tasks_map: dict[asyncio.Task[ServiceReviewResult], Service] = {}
            try:
                async with asyncio.TaskGroup() as tg:
                    # Create tasks for all services
                    for service in services:
                        task = tg.create_task(
                            self._review_single_service(
                                service, include_scoring, include_llm_feedback
                            )
                        )
                        tasks_map[task] = service

                # All tasks completed successfully - collect results
                for task, service in tasks_map.items():
                    result = await task
                    results.append(result)

            except* Exception as eg:  # ExceptionGroup (Python 3.11+)
                # Handle exception group from TaskGroup
                # TaskGroup automatically cancels all tasks if any task raises an exception
                for task, service in tasks_map.items():
                    if task.done():
                        try:
                            result = await task
                            results.append(result)
                        except Exception as e:
                            logger.error(
                                f"Exception in completed task for service {service.name}: {e}",
                                exc_info=True,
                            )
                            errors.append(f"{service.name}: {str(e)}")
                            results.append(
                                ServiceReviewResult(
                                    service_name=service.name,
                                    service_path=str(service.path),
                                    language=service.language.value,
                                    passed=False,
                                    overall_score=0.0,
                                    error=str(e),
                                )
                            )
                    else:
                        # Task was cancelled by TaskGroup
                        errors.append(f"{service.name}: Task cancelled")
                        results.append(
                            ServiceReviewResult(
                                service_name=service.name,
                                service_path=str(service.path),
                                language=service.language.value,
                                passed=False,
                                overall_score=0.0,
                                error="Task cancelled due to another service's failure",
                            )
                        )
                
                # Add exception group errors
                for exc in eg.exceptions:
                    logger.error(f"TaskGroup exception: {exc}", exc_info=True)
                    errors.append(f"TaskGroup error: {str(exc)}")
        else:
            # Fallback for Python < 3.11: use asyncio.gather with semaphore
            semaphore = asyncio.Semaphore(self.max_parallel)

            async def review_with_semaphore(service: Service) -> ServiceReviewResult:
                async with semaphore:
                    return await self._review_single_service(
                        service, include_scoring, include_llm_feedback
                    )

            tasks = [review_with_semaphore(service) for service in services]
            gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(gathered_results):
                if isinstance(result, Exception):
                    service = services[i]
                    logger.error(
                        f"Exception during review for service {service.name}: {result}",
                        exc_info=True,
                    )
                    errors.append(f"{service.name}: {str(result)}")
                    results.append(
                        ServiceReviewResult(
                            service_name=service.name,
                            service_path=str(service.path),
                            language=service.language.value,
                            passed=False,
                            overall_score=0.0,
                            error=str(result),
                        )
                    )
                else:
                    results.append(result)

        return self._aggregate_results(results, errors)

    async def _review_services_sequential(
        self,
        services: list[Service],
        include_scoring: bool,
        include_llm_feedback: bool,
    ) -> BatchReviewResult:
        """Review services sequentially."""
        results: list[ServiceReviewResult] = []
        errors: list[str] = []

        for service in services:
            try:
                result = await self._review_single_service(
                    service, include_scoring, include_llm_feedback
                )
                results.append(result)
            except Exception as e:
                errors.append(f"{service.name}: {str(e)}")
                results.append(
                    ServiceReviewResult(
                        service_name=service.name,
                        service_path=str(service.path),
                        language=service.language.value,
                        passed=False,
                        overall_score=0.0,
                        error=str(e),
                    )
                )

        return self._aggregate_results(results, errors)

    async def _review_single_service(
        self,
        service: Service,
        include_scoring: bool,
        include_llm_feedback: bool,
    ) -> ServiceReviewResult:
        """
        Review a single service.

        Args:
            service: Service to review
            include_scoring: Whether to include scoring
            include_llm_feedback: Whether to include LLM feedback

        Returns:
            ServiceReviewResult
        """
        # Find main files in service directory to review
        service_path = service.path
        main_files = self._find_main_files(service_path, service.language)

        if not main_files:
            # No files to review, return neutral result
            return ServiceReviewResult(
                service_name=service.name,
                service_path=str(service_path),
                language=service.language.value,
                passed=True,
                overall_score=5.0,  # Neutral score
                review_details={"message": "No code files found to review"},
            )

        # Initialize reviewer agent
        reviewer = ReviewerAgent(config=self.config)
        try:
            # Review first/main file as representative
            # TODO: Could review multiple files and aggregate
            main_file = main_files[0]
            
            # Add timeout to prevent hanging
            try:
                review_result = await asyncio.wait_for(
                    reviewer.review_file(
                        main_file,
                        include_scoring=include_scoring,
                        include_llm_feedback=include_llm_feedback,
                    ),
                    timeout=self.review_timeout,
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Review timeout ({self.review_timeout}s) exceeded for service {service.name}"
                )
                return ServiceReviewResult(
                    service_name=service.name,
                    service_path=str(service_path),
                    language=service.language.value,
                    passed=False,
                    overall_score=0.0,
                    error=f"Review timeout after {self.review_timeout} seconds",
                )

            # Extract scores
            scores = review_result.get("scores", {})
            overall_score = scores.get("overall_score", 0.0)

            # Determine pass/fail (threshold: 70.0)
            threshold = 70.0
            if self.config and self.config.scoring:
                threshold = self.config.scoring.quality_threshold

            passed = overall_score >= threshold

            return ServiceReviewResult(
                service_name=service.name,
                service_path=str(service_path),
                language=service.language.value,
                passed=passed,
                overall_score=overall_score,
                scores={
                    "complexity": scores.get("complexity_score", 0.0),
                    "security": scores.get("security_score", 0.0),
                    "maintainability": scores.get("maintainability_score", 0.0),
                    "test_coverage": scores.get("test_coverage_score", 0.0),
                    "performance": scores.get("performance_score", 0.0),
                },
                review_details=review_result,
            )
        except Exception as e:
            logger.error(
                f"Exception during review for service {service.name}: {e}",
                exc_info=True,
            )
            return ServiceReviewResult(
                service_name=service.name,
                service_path=str(service_path),
                language=service.language.value,
                passed=False,
                overall_score=0.0,
                error=str(e),
            )
        finally:
            await reviewer.close()

    def _find_main_files(self, service_path: Path, language: Language) -> list[Path]:
        """
        Find main code files to review in a service directory.

        Args:
            service_path: Path to service directory
            language: Primary language of the service

        Returns:
            List of main file paths to review
        """
        main_files = []

        # Language-specific file patterns
        if language == Language.PYTHON:
            # Look for __init__.py, main.py, app.py, or service entry points
            patterns = ["**/__init__.py", "**/main.py", "**/app.py", "**/*_service.py"]
            for pattern in patterns:
                main_files.extend(list(service_path.glob(pattern))[:5])

        elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
            # Look for index.ts, index.tsx, main.ts, app.tsx
            patterns = [
                "**/index.ts",
                "**/index.tsx",
                "**/main.ts",
                "**/app.tsx",
                "**/App.tsx",
            ]
            for pattern in patterns:
                main_files.extend(list(service_path.glob(pattern))[:5])

        # If no specific main files found, get first code file
        if not main_files:
            code_extensions = {
                Language.PYTHON: ".py",
                Language.TYPESCRIPT: ".ts",
                Language.JAVASCRIPT: ".js",
                Language.REACT: ".tsx",
            }
            ext = code_extensions.get(language, ".py")
            main_files = list(service_path.glob(f"**/*{ext}"))[:1]

        return main_files[:1]  # Return first file for now

    def _aggregate_results(
        self, results: list[ServiceReviewResult], errors: list[str]
    ) -> BatchReviewResult:
        """
        Aggregate individual service review results.

        Args:
            results: List of service review results
            errors: List of error messages

        Returns:
            BatchReviewResult with aggregated statistics
        """
        if not results:
            return BatchReviewResult(
                services_reviewed=0,
                passed=0,
                failed=0,
                average_score=0.0,
                errors=errors,
            )

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        scores = [r.overall_score for r in results if r.overall_score > 0]
        average_score = sum(scores) / len(scores) if scores else 0.0

        return BatchReviewResult(
            services_reviewed=len(results),
            passed=passed,
            failed=failed,
            average_score=average_score,
            results=results,
            errors=errors,
        )

