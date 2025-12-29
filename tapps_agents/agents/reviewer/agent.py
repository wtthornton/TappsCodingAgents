"""
Reviewer Agent - Performs code review with scoring
"""

import logging
from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...experts.agent_integration import ExpertSupportMixin
from ..ops.dependency_analyzer import DependencyAnalyzer
from ...core.language_detector import Language
from .aggregator import QualityAggregator
from .progressive_review import (
    ProgressiveReview,
    ProgressiveReviewPolicy,
    ProgressiveReviewRollup,
    ProgressiveReviewStorage,
    ReviewFinding,
    ReviewMetrics,
    Severity,
)
from .report_generator import ReportGenerator
from .scoring import CodeScorer
from .service_discovery import ServiceDiscovery
from .typescript_scorer import TypeScriptScorer
from .influxdb_validator import InfluxDBValidator
from .websocket_validator import WebSocketValidator
from .mqtt_validator import MQTTValidator
from .docker_compose_validator import DockerComposeValidator
from .dockerfile_validator import DockerfileValidator

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent, ExpertSupportMixin):
    """
    Reviewer Agent - Code review with Code Scoring.

    Permissions: Read, Grep, Glob (read-only)

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(
        self,
        config: ProjectConfig | None = None,
        expert_registry: Any | None = None,
    ):
        super().__init__(
            agent_id="reviewer", agent_name="Reviewer Agent", config=config
        )
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Expert registry initialization (required due to multiple inheritance MRO issue)
        # BaseAgent.__init__() doesn't call super().__init__(), so ExpertSupportMixin.__init__()
        # is never called via MRO. We must manually initialize to avoid AttributeError.
        # The registry will be properly initialized in activate() via _initialize_expert_support()
        self.expert_registry: Any | None = None
        # Allow manual override if provided (for testing or special cases)
        if expert_registry:
            self.expert_registry = expert_registry
        # Initialize scorer with config weights and quality tools
        scoring_config = config.scoring if config else None
        weights = scoring_config.weights if scoring_config else None
        quality_tools = config.quality_tools if config else None
        ruff_enabled = quality_tools.ruff_enabled if quality_tools else True
        mypy_enabled = quality_tools.mypy_enabled if quality_tools else True
        jscpd_enabled = quality_tools.jscpd_enabled if quality_tools else True
        duplication_threshold = (
            quality_tools.duplication_threshold if quality_tools else 3.0
        )
        min_duplication_lines = (
            quality_tools.min_duplication_lines if quality_tools else 5
        )
        self.scorer = CodeScorer(
            weights=weights,
            ruff_enabled=ruff_enabled,
            mypy_enabled=mypy_enabled,
            jscpd_enabled=jscpd_enabled,
            duplication_threshold=duplication_threshold,
            min_duplication_lines=min_duplication_lines,
        )

        # Initialize dependency analyzer for security scoring (will be set in activate)
        pip_audit_enabled = quality_tools.pip_audit_enabled if quality_tools else True
        self.dependency_analyzer_enabled = pip_audit_enabled
        self.dependency_analyzer: DependencyAnalyzer | None = None

        # Ensure Python scorer is registered in ScorerRegistry (fix for registration issues)
        # This ensures reviewer commands work even if lazy initialization fails
        try:
            from ...core.language_detector import Language
            from .scorer_registry import ScorerRegistry
            
            # Ensure built-in scorers are registered
            ScorerRegistry._ensure_initialized()
            
            # Double-check Python scorer is registered (fallback if initialization failed)
            if not ScorerRegistry.is_registered(Language.PYTHON):
                logger.warning(
                    "Python scorer not registered, attempting explicit registration"
                )
                ScorerRegistry.register(Language.PYTHON, CodeScorer, override=True)
        except Exception as e:
            # Log but don't fail - we have self.scorer as fallback
            logger.warning(
                f"Failed to ensure Python scorer registration: {e}. "
                "Using direct CodeScorer instance as fallback.",
                exc_info=True
            )

        # Initialize TypeScript scorer (Phase 6.4.4)
        typescript_enabled = quality_tools.typescript_enabled if quality_tools else True
        self.typescript_enabled = typescript_enabled
        self.typescript_scorer: TypeScriptScorer | None
        if typescript_enabled:
            eslint_config = quality_tools.eslint_config if quality_tools else None
            tsconfig_path = quality_tools.tsconfig_path if quality_tools else None
            self.typescript_scorer = TypeScriptScorer(
                eslint_config=eslint_config, tsconfig_path=tsconfig_path
            )
        else:
            self.typescript_scorer = None
        
        # Initialize InfluxDB validator (Phase 1.2: HomeIQ Support)
        self.influxdb_validator = InfluxDBValidator()
        
        # Initialize WebSocket and MQTT validators (Phase 2.2: HomeIQ Support)
        self.websocket_validator = WebSocketValidator()
        self.mqtt_validator = MQTTValidator()
        
        # Initialize Docker Compose validator (Phase 3.3: HomeIQ Support)
        self.docker_compose_validator = DockerComposeValidator()
        
        # Initialize Dockerfile validator (Phase 4.2: HomeIQ Support)
        self.dockerfile_validator = DockerfileValidator()

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the reviewer agent with expert support."""
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        await super().activate(project_root, offline_mode=offline_mode)
        # Initialize expert support via mixin
        await self._initialize_expert_support(project_root, offline_mode=offline_mode)
        # Initialize dependency analyzer if enabled
        if self.dependency_analyzer_enabled:
            self.dependency_analyzer = DependencyAnalyzer(
                project_root=project_root or Path.cwd()
            )

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for reviewer agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*review",
                "description": "Review code file with scoring and feedback",
            },
            {
                "command": "*score",
                "description": "Calculate code scores only (no LLM feedback)",
            },
            {
                "command": "*lint",
                "description": "Run Ruff linting on a file and return issues (Phase 6.1)",
            },
            {
                "command": "*type-check",
                "description": "Run mypy type checking on a file and return errors (Phase 6.2)",
            },
            {
                "command": "*report",
                "description": "Generate quality reports in multiple formats (Phase 6.3)",
            },
            {
                "command": "*duplication",
                "description": "Detect code duplication using jscpd (Phase 6.4)",
            },
            {
                "command": "*analyze-project",
                "description": "Analyze entire project with all services (Phase 6.4.2)",
            },
            {
                "command": "*analyze-services",
                "description": "Analyze specific services (Phase 6.4.2)",
            },
            {
                "command": "*docs",
                "description": "Get library documentation from Context7 (R6)",
            },
        ]

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """
        Execute reviewer agent command.

        Commands:
        - help: Show available commands
        - review: Review file with scoring and feedback
        - score: Calculate scores only
        """
        if command == "help":
            return {"type": "help", "content": self.format_help()}

        elif command == "review":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *review <file>"}

            # Model parameter deprecated - all LLM operations handled by Cursor Skills
            try:
                return await self.review_file(
                    Path(file_path),
                    include_scoring=True,
                    include_llm_feedback=True,
                )
            except (FileNotFoundError, ValueError) as e:
                error_msg = str(e)
                if "File path required" in error_msg:
                    return {
                        "error": error_msg,
                        "suggestion": "Provide a file path: @reviewer *review <file_path>",
                    }
                return {
                    "error": error_msg,
                    "suggestion": "Check that the file exists and is readable",
                }
            except RuntimeError as e:
                # Handle scorer errors and other runtime errors
                return {
                    "error": f"Review failed: {str(e)}",
                    "suggestion": "Check that quality tools (Ruff, mypy) are installed and configured correctly",
                }
            except TimeoutError as e:
                return {
                    "error": str(e),
                    "suggestion": "Try reviewing a smaller file or increase 'operation_timeout' in config",
                }

        elif command == "score":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *score <file>"}

            try:
                return await self.review_file(
                    Path(file_path), include_scoring=True, include_llm_feedback=False
                )
            except (FileNotFoundError, ValueError) as e:
                error_msg = str(e)
                if "File path required" in error_msg:
                    return {
                        "error": error_msg,
                        "suggestion": "Provide a file path: @reviewer *score <file_path>",
                    }
                return {
                    "error": error_msg,
                    "suggestion": "Check that the file exists and is readable",
                }
            except TimeoutError as e:
                return {
                    "error": str(e),
                    "suggestion": "Try scoring a smaller file or increase 'tool_timeout' in config",
                }

        elif command == "lint":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *lint <file>"}

            return await self.lint_file(Path(file_path))

        elif command == "type-check":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *type-check <file>"}

            return await self.type_check_file(Path(file_path))

        elif command == "report":
            # Generate quality reports
            format_type = kwargs.get("format", "all")  # json, markdown, html, all
            output_dir = kwargs.get("output_dir")
            files_list = kwargs.get("files")  # Optional list of files to analyze
            target = kwargs.get("target")  # Optional target path (file or directory)

            return await self.generate_reports(
                format_type=format_type, output_dir=output_dir, files=files_list, target=target
            )

        elif command == "duplication":
            file_path = kwargs.get("file")
            if not file_path:
                return {
                    "error": "File or directory path required. Usage: *duplication <file_or_directory>"
                }

            return await self.check_duplication(Path(file_path))

        elif command == "analyze-project":
            project_root = kwargs.get("project_root")
            include_comparison = kwargs.get("include_comparison", True)

            return await self.analyze_project(
                project_root=Path(project_root) if project_root else None,
                include_comparison=include_comparison,
            )

        elif command == "analyze-services":
            services = kwargs.get("services")  # List of service names or patterns
            project_root = kwargs.get("project_root")
            include_comparison = kwargs.get("include_comparison", True)

            return await self.analyze_services(
                services=services if services else None,
                project_root=Path(project_root) if project_root else None,
                include_comparison=include_comparison,
            )

        elif command == "docs":
            library = kwargs.get("library")
            if not library:
                return {"error": "Library name required. Usage: *docs <library> [topic]"}
            
            topic = kwargs.get("topic")
            mode = kwargs.get("mode", "code")
            page = kwargs.get("page", 1)
            no_cache = kwargs.get("no_cache", False)
            
            return await self.get_documentation(
                library=library,
                topic=topic,
                mode=mode,
                page=page,
                no_cache=no_cache,
            )

        else:
            return {
                "error": f"Unknown command: {command}. Use *help to see available commands."
            }

    async def _run_quality_tools_parallel(
        self, file_path: Path, language: Language
    ) -> dict[str, Any]:
        """
        Run quality tools (linting, type checking) in parallel for better performance.
        
        Args:
            file_path: Path to file to analyze
            language: Detected language
            
        Returns:
            Dictionary with tool results
        """
        import asyncio
        
        reviewer_config = self.config.agents.reviewer if self.config else None
        enable_parallel = (
            reviewer_config.enable_parallel_tools if reviewer_config else True
        )
        tool_timeout = reviewer_config.tool_timeout if reviewer_config else 30.0
        
        results = {
            "linting": None,
            "type_checking": None,
            "parallel": enable_parallel,
        }
        
        if not enable_parallel or language not in [Language.PYTHON, Language.TYPESCRIPT]:
            # Run sequentially or skip for unsupported languages
            if language == Language.PYTHON or (
                language == Language.TYPESCRIPT and self.typescript_scorer
            ):
                results["linting"] = await self.lint_file(file_path)
                results["type_checking"] = await self.type_check_file(file_path)
            return results
        
        # Run tools in parallel
        try:
            lint_task = asyncio.create_task(self.lint_file(file_path))
            type_check_task = asyncio.create_task(self.type_check_file(file_path))
            
            # Wait for both with timeout
            lint_result, type_check_result = await asyncio.wait_for(
                asyncio.gather(
                    lint_task,
                    type_check_task,
                    return_exceptions=True,
                ),
                timeout=tool_timeout * 2,  # Allow 2x timeout for parallel execution
            )
            
            # Handle results (may be exceptions)
            if isinstance(lint_result, Exception):
                logger.warning(f"Linting failed: {lint_result}")
                results["linting"] = {
                    "file": str(file_path),
                    "linting_score": 5.0,
                    "error": str(lint_result),
                    "timeout": isinstance(lint_result, TimeoutError),
                }
            else:
                results["linting"] = lint_result
            
            if isinstance(type_check_result, Exception):
                logger.warning(f"Type checking failed: {type_check_result}")
                results["type_checking"] = {
                    "file": str(file_path),
                    "type_checking_score": 5.0,
                    "error": str(type_check_result),
                    "timeout": isinstance(type_check_result, TimeoutError),
                }
            else:
                results["type_checking"] = type_check_result
                
        except asyncio.TimeoutError:
            logger.warning(f"Parallel quality tools timed out for {file_path}")
            results["timeout"] = True
            results["error"] = f"Quality tools exceeded timeout of {tool_timeout * 2}s"
        
        return results
    
    def _get_dependency_security_penalty(self) -> float:
        """
        Get security penalty based on dependency vulnerabilities.

        Phase 6.4.3: Dependency Analysis & Security Auditing

        Returns:
            Penalty score (0-10, where 10 = no vulnerabilities, 0 = critical vulnerabilities)
        """
        if not self.dependency_analyzer_enabled:
            return 10.0  # No penalty if dependency auditing disabled

        # Initialize dependency analyzer if not already initialized
        if self.dependency_analyzer is None:
            project_root = getattr(self, "project_root", Path.cwd())
            self.dependency_analyzer = DependencyAnalyzer(project_root=project_root)

        try:
            # Get security audit
            quality_tools = self.config.quality_tools if self.config else None
            threshold = (
                quality_tools.dependency_audit_threshold if quality_tools else "high"
            )

            audit_result = self.dependency_analyzer.run_security_audit(
                severity_threshold=threshold
            )

            if not audit_result or "error" in audit_result:
                return 10.0  # No penalty if audit fails

            severity_breakdown = audit_result.get("severity_breakdown", {})

            # Calculate penalty based on severity
            # Critical: -3 points each
            # High: -2 points each
            # Medium: -1 point each
            # Low: -0.5 points each
            penalty = (
                severity_breakdown.get("critical", 0) * 3.0
                + severity_breakdown.get("high", 0) * 2.0
                + severity_breakdown.get("medium", 0) * 1.0
                + severity_breakdown.get("low", 0) * 0.5
            )

            # Score: 10 - penalty, minimum 0
            score = max(0.0, 10.0 - penalty)

            return score

        except Exception:
            return 10.0  # No penalty on error

    async def review_file(
        self,
        file_path: Path,
        include_scoring: bool = True,
        include_llm_feedback: bool = True,
    ) -> dict[str, Any]:
        """
        Review a code file with timeout protection and improved error handling.

        Args:
            file_path: Path to code file
            include_scoring: Include code scores
            include_llm_feedback: Include LLM-generated feedback (via Cursor Skills)

        Returns:
            Review results with scores and feedback

        Raises:
            TimeoutError: If review operation exceeds configured timeout
            ValueError: If file cannot be read or validated
            RuntimeError: If scoring fails
        """
        import asyncio
        
        # Get timeout configuration
        reviewer_config = self.config.agents.reviewer if self.config else None
        operation_timeout = (
            reviewer_config.operation_timeout if reviewer_config else 300.0
        )
        max_file_size = (
            reviewer_config.max_file_size if reviewer_config else (10 * 1024 * 1024)
        )
        
        # Wrap entire review in timeout protection with comprehensive error handling
        try:
            return await asyncio.wait_for(
                self._review_file_internal(
                    file_path, include_scoring, include_llm_feedback, max_file_size
                ),
                timeout=operation_timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Review operation timed out after {operation_timeout}s for {file_path}"
            )
            raise TimeoutError(
                f"Review operation exceeded timeout of {operation_timeout}s. "
                f"The file may be too large or quality tools may be slow. "
                f"Consider increasing 'operation_timeout' in config or reviewing smaller files."
            ) from None
        except Exception as e:
            # Catch any unexpected exceptions to prevent crashes
            # Log the error but re-raise it so retry logic can handle it
            logger.warning(
                f"Unexpected error in review_file for {file_path}: {type(e).__name__}: {e}",
                exc_info=True
            )
            # Re-raise to allow retry logic to handle it
            raise
    
    async def _review_file_internal(
        self,
        file_path: Path,
        include_scoring: bool,
        include_llm_feedback: bool,
        max_file_size: int,
    ) -> dict[str, Any]:
        """Internal review implementation without timeout wrapper."""
        # Use centralized path validation from BaseAgent
        # _validate_path handles existence, size, and path traversal checks
        self._validate_path(file_path, max_file_size=max_file_size)

        # Read code
        try:
            code = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file as UTF-8: {e}") from e

        result: dict[str, Any] = {"file": str(file_path), "review": {}}

        # Detect file type using LanguageDetector
        from ...core.language_detector import LanguageDetector

        detector = LanguageDetector(project_root=self._project_root)
        detection_result = detector.detect_language(file_path, code)
        file_type = detection_result.language.value
        result["file_type"] = file_type
        result["language_detection"] = {
            "language": file_type,
            "confidence": detection_result.confidence,
            "method": detection_result.method,
        }

        # E2: Context7 API verification and best practices validation
        context7_verification = {}
        libraries_used = []
        
        # Get Context7 helper if available
        context7_helper = None
        try:
            from ...context7.agent_integration import get_context7_helper
            context7_helper = get_context7_helper(self, self.config, self._project_root)
        except Exception as e:
            logger.debug(f"Context7 helper not available: {e}")
        
        if context7_helper and context7_helper.enabled:
            try:
                # E2: Detect libraries ONLY from code (not project files)
                # This ensures we only verify libraries actually used in the code
                language_str = file_type.lower()  # "python", "typescript", etc.
                if code:
                    libraries_used = context7_helper.library_detector.detect_from_code(
                        code=code,
                        language=language_str
                    )
                else:
                    libraries_used = []
                
                if libraries_used:
                    # Verify each library usage against Context7 docs
                    for lib in libraries_used:
                        # Get full API reference
                        lib_docs = await context7_helper.get_documentation(
                            library=lib,
                            topic=None,  # Get full API reference
                            use_fuzzy_match=True
                        )
                        
                        # Get best practices
                        best_practices = await context7_helper.get_documentation(
                            library=lib,
                            topic="best-practices",
                            use_fuzzy_match=True
                        )
                        
                        # Basic API correctness check (check if library is mentioned in code)
                        api_mentioned = lib.lower() in code.lower()
                        
                        context7_verification[lib] = {
                            "api_docs_available": lib_docs is not None,
                            "best_practices_available": best_practices is not None,
                            "api_mentioned": api_mentioned,
                            "docs_source": lib_docs.get("source") if lib_docs else None,
                            "best_practices_source": best_practices.get("source") if best_practices else None,
                        }
                    
                    logger.debug(f"E2: Verified {len(libraries_used)} libraries with Context7")
            except Exception as e:
                logger.debug(f"E2: Context7 API verification failed: {e}")
        
        # Store Context7 verification results
        if context7_verification:
            result["context7_verification"] = context7_verification
            result["libraries_detected"] = libraries_used

        # Calculate scores based on file type with timeout protection
        if include_scoring:
            import asyncio
            from ...core.language_detector import Language
            from .scoring import ScorerFactory

            language = detection_result.language
            reviewer_config = self.config.agents.reviewer if self.config else None
            tool_timeout = reviewer_config.tool_timeout if reviewer_config else 30.0
            
            try:
                if language == Language.YAML:
                    scores = await asyncio.wait_for(
                        asyncio.to_thread(self._score_yaml_file, file_path, code),
                        timeout=tool_timeout,
                    )
                else:
                    # Use ScorerFactory to get appropriate scorer for the language
                    scorer = ScorerFactory.get_scorer(language, self.config)
                    # Run scoring in thread with timeout
                    scores = await asyncio.wait_for(
                        asyncio.to_thread(scorer.score_file, file_path, code),
                        timeout=tool_timeout,
                    )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Scoring timed out after {tool_timeout}s for {file_path}. "
                    f"Using fallback scores."
                )
                # Provide fallback scores instead of failing completely
                scores = {
                    "complexity_score": 5.0,
                    "security_score": 5.0,
                    "maintainability_score": 5.0,
                    "test_coverage_score": 0.0,
                    "performance_score": 5.0,
                    "overall_score": 50.0,
                    "metrics": {"timeout": True, "error": "Scoring operation timed out"},
                }
            except Exception as e:
                logger.warning(
                    f"Scoring failed for {file_path}: {e}. "
                    f"Using fallback scores."
                )
                # Provide fallback scores instead of failing completely
                scores = {
                    "complexity_score": 5.0,
                    "security_score": 5.0,
                    "maintainability_score": 5.0,
                    "test_coverage_score": 0.0,
                    "performance_score": 5.0,
                    "overall_score": 50.0,
                    "metrics": {"error": True, "error_message": str(e)},
                }

            # Enhance security score with dependency health (Phase 6.4.3)
            # Only apply to Python files
            if language == Language.PYTHON:
                try:
                    dependency_security = await asyncio.wait_for(
                        asyncio.to_thread(self._get_dependency_security_penalty),
                        timeout=tool_timeout,
                    )
                    # Blend dependency security into security score (70% code security, 30% dependency security)
                    original_security = scores.get("security_score", 5.0)
                    scores["security_score"] = (original_security * 0.7) + (
                        dependency_security * 0.3
                    )
                    scores["dependency_security_score"] = dependency_security
                except asyncio.TimeoutError:
                    logger.debug(f"Dependency security check timed out for {file_path}")
                    # Continue without dependency security penalty
                except Exception as e:
                    logger.debug(f"Dependency security check failed: {e}")
                    # Continue without dependency security penalty

            result["scoring"] = scores
        
        # Validate InfluxDB patterns (Phase 1.2: HomeIQ Support)
        influxdb_review = self.influxdb_validator.review_file(file_path, code)
        if influxdb_review.get("has_influxdb"):
            result["influxdb_validation"] = {
                "flux_queries": influxdb_review.get("flux_queries", []),
                "connection_issues": influxdb_review.get("connection_issues", []),
                "data_modeling_issues": influxdb_review.get("data_modeling_issues", []),
                "suggestions": influxdb_review.get("suggestions", [])
            }
        
        # Validate WebSocket patterns (Phase 2.2: HomeIQ Support)
        websocket_review = self.websocket_validator.review_file(file_path, code)
        if websocket_review.get("has_websocket"):
            result["websocket_validation"] = {
                "connection_issues": websocket_review.get("connection_issues", []),
                "suggestions": websocket_review.get("suggestions", [])
            }
        
        # Validate MQTT patterns (Phase 2.2: HomeIQ Support)
        mqtt_review = self.mqtt_validator.review_file(file_path, code)
        if mqtt_review.get("has_mqtt"):
            result["mqtt_validation"] = {
                "connection_issues": mqtt_review.get("connection_issues", []),
                "topic_issues": mqtt_review.get("topic_issues", []),
                "suggestions": mqtt_review.get("suggestions", [])
            }
        
        # Validate Docker Compose patterns (Phase 3.3: HomeIQ Support)
        compose_review = self.docker_compose_validator.review_file(file_path, code)
        if compose_review.get("is_compose_file"):
            result["docker_compose_validation"] = compose_review.get("validation", {})
        
        # Validate Dockerfile patterns (Phase 4.2: HomeIQ Support)
        dockerfile_review = self.dockerfile_validator.review_file(file_path, code)
        if dockerfile_review.get("is_dockerfile"):
            result["dockerfile_validation"] = dockerfile_review.get("validation", {})

        # Consult experts for review guidance
        expert_guidance: dict[str, Any] = {}
        expert_registry = getattr(self, "expert_registry", None)
        if expert_registry and include_llm_feedback:
            code_preview = code[:2000]  # First 2000 chars for expert consultation

            # Consult Security expert
            try:
                security_consultation = await expert_registry.consult(
                    query=f"Review this code for security vulnerabilities:\n\n{code_preview}",
                    domain="security",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="reviewer",
                )
                expert_guidance["security"] = security_consultation.weighted_answer
                expert_guidance["security_confidence"] = (
                    security_consultation.confidence
                )
            except Exception:
                logger.debug("Security expert consultation failed", exc_info=True)

            # Consult Performance expert
            try:
                perf_consultation = await expert_registry.consult(
                    query=f"Review this code for performance issues:\n\n{code_preview}",
                    domain="performance-optimization",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="reviewer",
                )
                expert_guidance["performance"] = perf_consultation.weighted_answer
            except Exception:
                logger.debug("Performance expert consultation failed", exc_info=True)

            # Consult Code Quality expert
            try:
                quality_consultation = await expert_registry.consult(
                    query=f"Review this code for quality issues:\n\n{code_preview}",
                    domain="code-quality-analysis",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="reviewer",
                )
                expert_guidance["code_quality"] = quality_consultation.weighted_answer
            except Exception:
                logger.debug("Code quality expert consultation failed", exc_info=True)

        # Generate LLM feedback
        if include_llm_feedback:
            # Model parameter deprecated - use default for Cursor Skills
            model_name = "reviewer-agent"
            feedback = await self._generate_feedback(
                code,
                language,  # Pass detected language for language-aware prompts
                scores if include_scoring else None,
                model_name,
                expert_guidance=expert_guidance,
            )
            result["feedback"] = feedback

        # Quality gate evaluation (Phase 2.2: Quality Gates Integration)
        # Note: Quality gate checks use tool operations (coverage analysis) which are Cursor-first compatible.
        # LLM feedback generation already uses GenericInstruction with to_skill_command() for Cursor Skills.
        quality_gate_result = None
        if include_scoring and self.config:
            from ...quality.quality_gates import QualityGate, QualityThresholds

            scoring_config = self.config.scoring
            quality_gates_config = scoring_config.quality_gates if scoring_config else None

            # Check if quality gates are enabled
            if quality_gates_config and quality_gates_config.enabled:
                # Create quality gate with thresholds from config
                thresholds = QualityThresholds(
                    overall_min=8.0,  # Default, can be overridden from config
                    security_min=8.5,  # Default, can be overridden from config
                    test_coverage_min=(
                        quality_gates_config.test_coverage.threshold * 100.0
                        if quality_gates_config.test_coverage.enabled
                        else 80.0
                    ),
                )

                quality_gate = QualityGate(thresholds=thresholds)
                quality_gate_result = quality_gate.evaluate(scores)

                # Block review approval if quality gate fails
                if not quality_gate_result.passed:
                    result["quality_gate"] = quality_gate_result.to_dict()
                    result["quality_gate_blocked"] = True

                # Optionally check coverage using CoverageAnalyzer if enabled
                if quality_gates_config.test_coverage.enabled:
                    try:
                        # Determine project root from file path (go up to find project root markers)
                        project_root = None
                        current_dir = file_path.parent
                        # Look for common project root indicators
                        for _ in range(5):  # Limit search depth
                            if any(
                                (current_dir / marker).exists()
                                for marker in [".git", "pyproject.toml", "package.json", "tsconfig.json"]
                            ):
                                project_root = current_dir
                                break
                            if current_dir == current_dir.parent:  # Reached filesystem root
                                break
                            current_dir = current_dir.parent
                        
                        coverage_result = await quality_gate.check_coverage(
                            file_path=file_path,
                            language=language,
                            threshold=quality_gates_config.test_coverage.threshold,
                            project_root=project_root or file_path.parent,
                        )
                        # Merge coverage-specific results
                        if coverage_result:
                            result["coverage_gate"] = {
                                "coverage_percentage": coverage_result.scores.get("coverage_percentage", 0.0),
                                "coverage_passed": coverage_result.test_coverage_passed,
                                "coverage_threshold": quality_gates_config.test_coverage.threshold * 100.0,
                            }
                            # Block if coverage gate fails
                            if not coverage_result.test_coverage_passed:
                                result["quality_gate_blocked"] = True
                    except Exception as e:
                        # Log error but don't block review if coverage check fails
                        logger.debug(f"Coverage check failed: {e}", exc_info=True)

                # Store quality gate result
                if quality_gate_result:
                    result["quality_gate"] = quality_gate_result.to_dict()

        # Determine pass/fail using configured threshold
        if include_scoring:
            reviewer_config = self.config.agents.reviewer if self.config else None
            threshold = reviewer_config.quality_threshold if reviewer_config else 70.0
            result["passed"] = scores["overall_score"] >= threshold
            result["threshold"] = threshold
            
            # Quality gate can override passed status
            if quality_gate_result and not quality_gate_result.passed:
                result["passed"] = False

        return result

    async def _generate_feedback(
        self,
        code: str,
        language: Language,
        scores: dict[str, Any] | None,
        model: str,
        expert_guidance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate LLM feedback on code using language-aware prompts.
        
        Phase 1.3: LLM Feedback Generation Fix
        """
        from .feedback_generator import FeedbackGenerator

        # Generate language-aware prompt using FeedbackGenerator
        prompt = FeedbackGenerator.generate_prompt(
            code=code,
            language=language,
            scores=scores,
            expert_guidance=expert_guidance,
            code_preview_limit=2000,
        )

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="reviewer",
            command="generate-feedback",
            prompt=prompt,
            parameters={"model": model},
        )

        return {
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }

    async def lint_file(self, file_path: Path) -> dict[str, Any]:
        """
        Run Ruff linting on a file and return detailed issues with timeout protection.

        Phase 6: Modern Quality Analysis - Ruff Integration

        Args:
            file_path: Path to code file (Python only)

        Returns:
            Dictionary with linting results:
            {
                "file": str,
                "linting_score": float (0-10),
                "issues": List[Dict],
                "issue_count": int,
                "error_count": int,
                "warning_count": int,
                "fatal_count": int
            }

        Raises:
            TimeoutError: If linting exceeds configured timeout
        """
        import asyncio
        
        # Use centralized path validation from BaseAgent
        self._validate_path(file_path)
        
        # Get timeout configuration
        reviewer_config = self.config.agents.reviewer if self.config else None
        tool_timeout = reviewer_config.tool_timeout if reviewer_config else 30.0
        
        try:
            return await asyncio.wait_for(
                self._lint_file_internal(file_path),
                timeout=tool_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Linting timed out after {tool_timeout}s for {file_path}")
            return {
                "file": str(file_path),
                "linting_score": 5.0,
                "issues": [],
                "issue_count": 0,
                "error_count": 0,
                "warning_count": 0,
                "fatal_count": 0,
                "tool": "none",
                "timeout": True,
                "error": f"Linting operation timed out after {tool_timeout}s",
            }
    
    async def _lint_file_internal(self, file_path: Path) -> dict[str, Any]:
        """Internal linting implementation without timeout wrapper."""

        file_ext = file_path.suffix.lower()

        # Route to appropriate linter (Phase 6.4.4)
        if file_ext in [".ts", ".tsx", ".js", ".jsx"] and self.typescript_scorer:
            # Use ESLint for TypeScript/JavaScript
            linting_score = self.typescript_scorer._calculate_linting_score(file_path)
            issues_result = self.typescript_scorer.get_eslint_issues(file_path)

            issues = issues_result.get("issues", [])
            error_count = 0
            warning_count = 0

            # Count errors and warnings from ESLint output
            for file_result in issues:
                messages = file_result.get("messages", [])
                for message in messages:
                    severity = message.get("severity", 1)
                    if severity == 2:  # Error
                        error_count += 1
                    elif severity == 1:  # Warning
                        warning_count += 1

            return {
                "file": str(file_path),
                "linting_score": linting_score,
                "issues": issues,
                "issue_count": error_count + warning_count,
                "error_count": error_count,
                "warning_count": warning_count,
                "fatal_count": 0,
                "tool": "eslint",
            }
        elif file_ext == ".py":
            # Use Ruff for Python files
            linting_score = self.scorer._calculate_linting_score(file_path)
            issues_raw = self.scorer.get_ruff_issues(file_path)

            # Defensive check: ensure issues is a list and filter out non-dict items
            if not isinstance(issues_raw, list):
                logger.warning(f"get_ruff_issues returned non-list: {type(issues_raw).__name__}")
                issues = []
            else:
                # Filter to only dict items and ensure they have the expected structure
                issues = []
                for item in issues_raw:
                    if isinstance(item, dict):
                        issues.append(item)
                    else:
                        logger.warning(f"Skipping non-dict issue item: {type(item).__name__} - {str(item)[:100]}")

            # Count issues by severity (defensive: handle missing or malformed code structure)
            error_count = 0
            warning_count = 0
            fatal_count = 0
            
            for d in issues:
                if not isinstance(d, dict):
                    continue
                code_info = d.get("code")
                if isinstance(code_info, dict):
                    code_name = code_info.get("name", "")
                elif isinstance(code_info, str):
                    code_name = code_info
                else:
                    code_name = str(d.get("code", ""))
                
                if code_name.startswith("E"):
                    error_count += 1
                elif code_name.startswith("W"):
                    warning_count += 1
                elif code_name.startswith("F"):
                    fatal_count += 1

            return {
                "file": str(file_path),
                "linting_score": linting_score,
                "issues": issues,
                "issue_count": len(issues),
                "error_count": error_count,
                "warning_count": warning_count,
                "fatal_count": fatal_count,
                "tool": "ruff",
            }
        else:
            return {
                "file": str(file_path),
                "linting_score": 10.0,
                "issues": [],
                "issue_count": 0,
                "error_count": 0,
                "warning_count": 0,
                "fatal_count": 0,
                "message": "Linting only supported for Python and TypeScript/JavaScript files",
                "tool": "none",
            }

    async def type_check_file(self, file_path: Path) -> dict[str, Any]:
        """
        Run mypy type checking on a file and return detailed errors with timeout protection.

        Phase 6.2: Modern Quality Analysis - mypy Integration

        Args:
            file_path: Path to code file (Python only)

        Returns:
            Dictionary with type checking results:
            {
                "file": str,
                "type_checking_score": float (0-10),
                "errors": List[Dict],
                "error_count": int,
                "error_codes": List[str] (unique error codes found)
            }

        Raises:
            TimeoutError: If type checking exceeds configured timeout
        """
        import asyncio
        
        # Use centralized path validation from BaseAgent
        self._validate_path(file_path)
        
        # Get timeout configuration
        reviewer_config = self.config.agents.reviewer if self.config else None
        tool_timeout = reviewer_config.tool_timeout if reviewer_config else 30.0
        
        try:
            return await asyncio.wait_for(
                self._type_check_file_internal(file_path),
                timeout=tool_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Type checking timed out after {tool_timeout}s for {file_path}")
            return {
                "file": str(file_path),
                "type_checking_score": 5.0,
                "errors": [],
                "error_count": 0,
                "error_codes": [],
                "tool": "none",
                "timeout": True,
                "error": f"Type checking operation timed out after {tool_timeout}s",
            }
    
    async def _type_check_file_internal(self, file_path: Path) -> dict[str, Any]:
        """Internal type checking implementation without timeout wrapper."""

        file_ext = file_path.suffix.lower()

        # Route to appropriate type checker (Phase 6.4.4)
        if file_ext in [".ts", ".tsx"] and self.typescript_scorer:
            # Use TypeScript compiler for TypeScript files
            type_checking_score = self.typescript_scorer._calculate_type_checking_score(
                file_path
            )
            errors_result = self.typescript_scorer.get_type_errors(file_path)

            errors = errors_result.get("errors", [])
            error_count = errors_result.get("error_count", 0)

            # Extract error codes from TypeScript errors
            error_codes = []
            for error in errors:
                if "TS" in error:
                    # Extract TS error code (e.g., "error TS2345")
                    parts = error.split("TS")
                    if len(parts) > 1:
                        code = "TS" + parts[1].split()[0] if parts[1] else "TS0000"
                        if code not in error_codes:
                            error_codes.append(code)

            return {
                "file": str(file_path),
                "type_checking_score": type_checking_score,
                "errors": errors,
                "error_count": error_count,
                "error_codes": error_codes,
                "tool": "tsc",
                "passed": errors_result.get("passed", error_count == 0),
            }
        elif file_ext == ".py":
            # Use mypy for Python files
            type_checking_score = self.scorer._calculate_type_checking_score(file_path)
            errors = self.scorer.get_mypy_errors(file_path)  # Returns List[Dict]

            # Extract unique error codes
            error_codes = list(
                set([err.get("error_code") for err in errors if err.get("error_code")])
            )

            return {
                "file": str(file_path),
                "type_checking_score": type_checking_score,
                "errors": errors,  # Already a list
                "error_count": len(errors),
                "error_codes": error_codes,
                "tool": "mypy",
            }
        else:
            # Non-Python files can't be type-checked, so they get a perfect score
            return {
                "file": str(file_path),
                "type_checking_score": 10.0,
                "errors": [],
                "error_count": 0,
                "error_codes": [],
                "message": "Type checking only supported for Python and TypeScript files",
                "tool": "none",
            }

    async def generate_reports(
        self,
        format_type: str = "all",
        output_dir: str | None = None,
        files: list[str] | None = None,
        target: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate quality reports in multiple formats.

        Phase 6.3: Comprehensive Reporting Infrastructure

        Args:
            format_type: Report format ('json', 'markdown', 'html', 'all')
            output_dir: Custom output directory (default: reports/quality/)
            files: Optional list of file paths to analyze (if None, uses single file or project)
            target: Optional file or directory path to analyze (if provided and files is None, files are discovered from target)

        Returns:
            Dictionary with report generation results
        """
        from datetime import datetime
        from pathlib import Path

        # Initialize report generator
        report_gen = ReportGenerator(
            output_dir=Path(output_dir) if output_dir else None
        )

        # Collect scores from files
        all_files = []
        aggregated_scores: dict[str, Any] = {
            "complexity_score": 0.0,
            "security_score": 0.0,
            "maintainability_score": 0.0,
            "test_coverage_score": 0.0,
            "performance_score": 0.0,
            "linting_score": 0.0,
            "type_checking_score": 0.0,
            "metrics": {},
        }

        def _discover_code_files(root: Path, max_files: int = 500) -> list[Path]:
            """Discover code files under a directory, excluding common non-source directories.
            
            Optimized to use pattern-based globbing and early directory pruning for performance.
            """
            exclude_dir_names = {
                ".git",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                ".venv",
                "venv",
                "env",
                "node_modules",
                "dist",
                "build",
                "htmlcov",
                "reports",
                ".tapps-agents",
                "tapps_agents.egg-info",
                ".egg-info",
                "MagicMock",
            }
            allowed_suffixes = {".py", ".ts", ".tsx", ".js", ".jsx"}

            discovered: list[Path] = []
            
            # Use pattern-based globbing instead of rglob("*") for better performance
            # This avoids scanning every file, only matching code file patterns
            for pattern in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
                if len(discovered) >= max_files:
                    break
                    
                for path in root.rglob(pattern):
                    if len(discovered) >= max_files:
                        break
                    
                    # Skip if path contains any excluded directory segment (early pruning)
                    if any(part in exclude_dir_names for part in path.parts):
                        continue
                    
                    # Double-check suffix (should already match pattern, but be safe)
                    if path.suffix.lower() not in allowed_suffixes:
                        continue
                    
                    discovered.append(path)
            
            return discovered

        # If no explicit file list is provided, derive it from target (file or directory) if present.
        if not files and target:
            target_path = Path(target)
            if target_path.exists():
                if target_path.is_file():
                    files = [str(target_path)]
                elif target_path.is_dir():
                    files = [str(p) for p in _discover_code_files(target_path)]

        # Support comma-separated multiple formats (e.g., "json,html") in addition to single tokens.
        requested_formats = {f.strip().lower() for f in str(format_type).split(",") if f.strip()}
        if "all" in requested_formats:
            requested_formats = {"all"}

        if files:
            # Analyze multiple files
            file_count = 0
            for file_path_str in files:
                file_path = Path(file_path_str)
                if not file_path.exists():
                    continue

                try:
                    code = file_path.read_text(encoding="utf-8")
                    scores = self.scorer.score_file(file_path, code)

                    all_files.append({"file": str(file_path), "scoring": scores})

                    # Aggregate scores
                    aggregated_scores["complexity_score"] += scores.get(
                        "complexity_score", 0.0
                    )
                    aggregated_scores["security_score"] += scores.get(
                        "security_score", 0.0
                    )
                    aggregated_scores["maintainability_score"] += scores.get(
                        "maintainability_score", 0.0
                    )
                    aggregated_scores["test_coverage_score"] += scores.get(
                        "test_coverage_score", 0.0
                    )
                    aggregated_scores["performance_score"] += scores.get(
                        "performance_score", 0.0
                    )
                    aggregated_scores["linting_score"] += scores.get(
                        "linting_score", 0.0
                    )
                    aggregated_scores["type_checking_score"] += scores.get(
                        "type_checking_score", 0.0
                    )
                    file_count += 1
                except Exception:
                    # Skip files that can't be analyzed
                    logger.debug(
                        "Skipping unreadable/unscorable file %s",
                        file_path,
                        exc_info=True,
                    )
                    continue  # nosec B112 - best-effort report generation

            # Calculate averages
            if file_count > 0:
                aggregated_scores["complexity_score"] /= file_count
                aggregated_scores["security_score"] /= file_count
                aggregated_scores["maintainability_score"] /= file_count
                aggregated_scores["test_coverage_score"] /= file_count
                aggregated_scores["performance_score"] /= file_count
                aggregated_scores["linting_score"] /= file_count
                aggregated_scores["type_checking_score"] /= file_count

                # Calculate overall score (weighted average)
                aggregated_scores["overall_score"] = (
                    (10 - aggregated_scores["complexity_score"]) * 0.20
                    + aggregated_scores["security_score"] * 0.30
                    + aggregated_scores["maintainability_score"] * 0.25
                    + aggregated_scores["test_coverage_score"] * 0.15
                    + aggregated_scores["performance_score"] * 0.10
                ) * 10  # Scale from 0-10 weighted sum to 0-100
            else:
                # Files were provided but none could be analyzed
                logger.warning(
                    "No files could be analyzed. Generated report will have zero scores."
                )
                aggregated_scores["overall_score"] = 0.0
        else:
            # No target/files provided or no files found - keep scores at 0.
            logger.warning(
                "No files to analyze. Provide a target directory or file list. "
                "Generated report will have zero scores."
            )
            aggregated_scores["overall_score"] = 0.0

        # Prepare metadata
        reviewer_config = self.config.agents.reviewer if self.config else None
        threshold = reviewer_config.quality_threshold if reviewer_config else 70.0

        metadata = {
            "timestamp": datetime.now(),
            "project_name": (
                self.config.project_name
                if self.config and self.config.project_name
                else "Unknown"
            ),
            "version": (
                self.config.version
                if self.config and self.config.version
                else "Unknown"
            ),
            "thresholds": {
                "overall": threshold,
                "complexity": 5.0,
                "security": 8.0,
                "maintainability": 7.0,
            },
        }

        # Generate reports based on format_type
        reports = {}

        if "all" in requested_formats or "json" in requested_formats:
            reports["json"] = str(
                report_gen.generate_json_report(aggregated_scores, all_files, metadata)
            )

        if "all" in requested_formats or "markdown" in requested_formats:
            reports["markdown"] = str(
                report_gen.generate_summary_report(
                    aggregated_scores, all_files, metadata
                )
            )

        if "all" in requested_formats or "html" in requested_formats:
            reports["html"] = str(
                report_gen.generate_html_report(aggregated_scores, all_files, metadata)
            )

        if "all" in requested_formats:
            reports["historical"] = str(
                report_gen.save_historical_data(aggregated_scores, metadata)
            )

        return {
            "format": format_type,
            "output_dir": str(report_gen.output_dir),
            "reports": reports,
            "summary": {
                "files_analyzed": len(all_files),
                "overall_score": aggregated_scores.get("overall_score", 0.0),
                "passed": aggregated_scores.get("overall_score", 0.0) >= threshold,
            },
        }

    async def check_duplication(self, file_path: Path) -> dict[str, Any]:
        """
        Check code duplication using jscpd.

        Phase 6.4: Modern Quality Analysis - jscpd Integration

        Args:
            file_path: Path to file or directory to analyze

        Returns:
            Dictionary with duplication analysis results
        """
        # Get duplication report
        report = self.scorer.get_duplication_report(file_path)

        # Get duplication score
        duplication_score = self.scorer._calculate_duplication_score(file_path)

        # Get threshold from config
        quality_tools = self.config.quality_tools if self.config else None
        threshold = quality_tools.duplication_threshold if quality_tools else 3.0

        return {
            "file_or_directory": str(file_path),
            "available": report.get("available", False),
            "duplication_percentage": report.get("percentage", 0.0),
            "duplication_score": duplication_score,
            "threshold": threshold,
            "passed": report.get("percentage", 0.0) < threshold,
            "total_lines": report.get("total_lines", 0),
            "duplicated_lines": report.get("duplicated_lines", 0),
            "duplicates": report.get("duplicates", []),
            "file_stats": report.get("files", []),
            "error": report.get("error") if "error" in report else None,
        }

    async def analyze_project(
        self, project_root: Path | None = None, include_comparison: bool = True
    ) -> dict[str, Any]:
        """
        Analyze entire project with all services.

        Phase 6.4.2: Multi-Service Analysis

        Args:
            project_root: Root directory of project (default: current directory)
            include_comparison: Whether to include cross-service comparison

        Returns:
            Dictionary with project-wide analysis results
        """
        if project_root is None:
            project_root = Path.cwd()

        # Discover all services
        discovery = ServiceDiscovery(project_root=project_root)
        services = discovery.discover_services()

        if not services:
            return {
                "project_root": str(project_root),
                "services_found": 0,
                "error": "No services found in project",
            }

        # Analyze all services in parallel
        service_names = [s["name"] for s in services]
        return await self.analyze_services(
            services=service_names,
            project_root=project_root,
            include_comparison=include_comparison,
        )

    async def analyze_services(
        self,
        services: list[str] | None = None,
        project_root: Path | None = None,
        include_comparison: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze specific services in parallel.

        Phase 6.4.2: Multi-Service Analysis

        Args:
            services: List of service names or patterns (None = all services)
            project_root: Root directory of project (default: current directory)
            include_comparison: Whether to include cross-service comparison

        Returns:
            Dictionary with service analysis results and aggregation
        """
        import asyncio

        if project_root is None:
            project_root = Path.cwd()

        # Discover services
        discovery = ServiceDiscovery(project_root=project_root)

        if services is None:
            # Analyze all services
            discovered_services = discovery.discover_services()
        else:
            # Analyze specific services
            discovered_services = []
            for service_name_or_pattern in services:
                if "*" in service_name_or_pattern or "?" in service_name_or_pattern:
                    # Pattern match
                    matches = discovery.discover_by_pattern(service_name_or_pattern)
                    discovered_services.extend(matches)
                else:
                    # Exact name match
                    service = discovery.discover_service(service_name_or_pattern)
                    if service:
                        discovered_services.append(service)

        if not discovered_services:
            return {
                "project_root": str(project_root),
                "services_found": 0,
                "error": "No matching services found",
            }

        # Analyze services in parallel
        async def analyze_service(service: dict[str, Any]) -> dict[str, Any]:
            """Analyze a single service."""
            service_path = Path(service["path"])
            service_name = service["name"]

            try:
                # Find all code files in service
                code_files: list[Path] = []
                for pattern in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
                    code_files.extend(service_path.rglob(pattern))

                # Filter out excluded directories
                excluded_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv"}
                code_files = [
                    f
                    for f in code_files
                    if not any(excluded in str(f) for excluded in excluded_dirs)
                ]

                # Analyze files
                all_scores = []
                total_lines = 0
                files_analyzed = 0

                for file_path in code_files[
                    :100
                ]:  # Limit to first 100 files per service
                    try:
                        code = file_path.read_text(encoding="utf-8", errors="ignore")
                        scores = self.scorer.score_file(file_path, code)
                        all_scores.append(scores)
                        total_lines += len(code.splitlines())
                        files_analyzed += 1
                    except Exception:
                        # Skip files that can't be analyzed
                        logger.debug(
                            "Skipping unreadable/unscorable file %s",
                            file_path,
                            exc_info=True,
                        )
                        continue  # nosec B112 - best-effort analysis

                # Aggregate scores for this service
                if all_scores:
                    avg_scores = {}
                    for key in all_scores[0].keys():
                        if key != "metrics":
                            values = [s.get(key, 0.0) for s in all_scores]
                            avg_scores[key] = (
                                sum(values) / len(values) if values else 0.0
                            )

                    # Calculate overall score
                    avg_scores["overall_score"] = avg_scores.get("overall_score", 0.0)
                else:
                    avg_scores = {
                        "overall_score": 0.0,
                        "complexity_score": 0.0,
                        "security_score": 0.0,
                        "maintainability_score": 0.0,
                        "test_coverage_score": 0.0,
                        "performance_score": 0.0,
                        "linting_score": 0.0,
                        "type_checking_score": 0.0,
                        "duplication_score": 0.0,
                    }

                return {
                    "service_name": service_name,
                    "service_path": str(service_path),
                    "relative_path": service.get("relative_path", ""),
                    "scores": avg_scores,
                    "files_analyzed": files_analyzed,
                    "total_lines": total_lines,
                    "status": "success",
                }

            except Exception as e:
                return {
                    "service_name": service_name,
                    "service_path": str(service_path),
                    "scores": {},
                    "files_analyzed": 0,
                    "total_lines": 0,
                    "status": "error",
                    "error": str(e),
                }

        # Run all service analyses in parallel
        tasks = [analyze_service(service) for service in discovered_services]
        service_results = await asyncio.gather(*tasks)

        # Aggregate results
        aggregator = QualityAggregator()

        result = {
            "project_root": str(project_root),
            "services_found": len(discovered_services),
            "services_analyzed": len(
                [r for r in service_results if r.get("status") == "success"]
            ),
            "aggregated": aggregator.aggregate_service_scores(service_results),
        }

        if include_comparison:
            result["comparison"] = aggregator.compare_services(service_results)

        result["services"] = service_results

        return result

    async def progressive_review_task(
        self,
        story_id: str,
        task_number: int,
        task_title: str = "",
        changed_files: list[Path] | None = None,
        project_root: Path | None = None,
    ) -> ProgressiveReview:
        """
        Perform progressive task-level review (Epic 5).

        Reviews code changes for a specific task, catching issues early.
        Aligned with BMAD's progressive review automation.

        Args:
            story_id: Story identifier (e.g., "1.3")
            task_number: Task number
            task_title: Optional task title
            changed_files: List of files changed in this task
            project_root: Project root directory

        Returns:
            ProgressiveReview with decision and findings
        """
        if project_root is None:
            project_root = self.project_root or Path.cwd()

        # Initialize storage and policy
        storage = ProgressiveReviewStorage(project_root)
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])

        # If no files provided, try to detect from git
        if not changed_files:
            changed_files = []
            # TODO: Add git diff detection if needed

        # Review each changed file
        findings: list[ReviewFinding] = []
        metrics = ReviewMetrics()

        for file_path in changed_files:
            if not file_path.exists():
                continue

            try:
                # Review file using existing review_file method
                review_result = await self.review_file(
                    file_path,
                    include_scoring=True,
                    include_llm_feedback=False,  # Faster for progressive reviews
                )

                # Extract findings from review - Enhanced version
                extracted_findings = await self._extract_findings_from_review(
                    review_result, file_path, task_number
                )
                findings.extend(extracted_findings)

                metrics.files_reviewed += 1

            except Exception as e:
                logger.warning(f"Failed to review {file_path}: {e}")

        # Determine decision
        decision, reason = policy.determine_decision(findings)

        # Create review
        review = ProgressiveReview(
            story_id=story_id,
            task_number=task_number,
            task_title=task_title,
            reviewer="TappsCodingAgents Progressive Review",
            decision=decision,
            decision_reason=reason,
            findings=findings,
            metrics=metrics,
        )

        # Save review
        storage.save_review(review)

        return review

    async def rollup_story_reviews(
        self, story_id: str, project_root: Path | None = None
    ) -> dict[str, Any]:
        """
        Rollup all progressive reviews for a story (Story 37.4).

        Args:
            story_id: Story identifier
            project_root: Project root directory

        Returns:
            Rollup summary for final QA
        """
        if project_root is None:
            project_root = self.project_root or Path.cwd()

        storage = ProgressiveReviewStorage(project_root)
        rollup = ProgressiveReviewRollup(storage)

        return rollup.rollup_story_reviews(story_id)

    async def _extract_findings_from_review(
        self, review_result: dict[str, Any], file_path: Path, task_number: int
    ) -> list[ReviewFinding]:
        """
        Extract specific findings from review results (Enhanced Findings).

        Parses linting errors, security warnings, type errors, and other
        specific issues from review output instead of just generic score messages.

        Args:
            review_result: Result from review_file()
            file_path: File being reviewed
            task_number: Task number for finding IDs

        Returns:
            List of ReviewFinding objects
        """
        findings: list[ReviewFinding] = []
        file_str = str(file_path)
        finding_counter = {"security": 0, "linting": 0, "type": 0, "quality": 0}

        # Extract scoring data
        scoring = review_result.get("scoring", {})
        security_score = scoring.get("security_score", 10.0)
        maintainability_score = scoring.get("maintainability_score", 10.0)
        complexity_score = scoring.get("complexity_score", 10.0)

        # 1. Extract linting errors (specific issues)
        try:
            lint_result = await self.lint_file(file_path)
            lint_issues = lint_result.get("issues", [])
            error_count = lint_result.get("error_count", 0)
            fatal_count = lint_result.get("fatal_count", 0)

            # Extract specific linting errors
            for issue in lint_issues[:10]:  # Limit to first 10 issues
                finding_counter["linting"] += 1
                code_name = issue.get("code", {})
                if isinstance(code_name, dict):
                    code = code_name.get("name", "UNKNOWN")
                else:
                    code = str(code_name)

                message = issue.get("message", "Linting issue found")
                line = issue.get("location", {}).get("row", None)
                if line is None:
                    line = issue.get("line", None)

                # Determine severity based on error type
                if code.startswith("F") or fatal_count > 0:
                    severity = Severity.HIGH
                elif code.startswith("E") or error_count > 0:
                    severity = Severity.HIGH
                elif code.startswith("W"):
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                findings.append(
                    ReviewFinding(
                        id=f"TASK-{task_number}-LINT-{finding_counter['linting']:03d}",
                        severity=severity,
                        category="standards",
                        file=file_str,
                        line=line,
                        finding=f"[{code}] {message}",
                        impact="Code does not meet linting standards",
                        suggested_fix=f"Fix linting error: {code} - {message}",
                    )
                )
        except Exception as e:
            logger.debug(f"Failed to extract linting issues: {e}")

        # 2. Extract security issues (from bandit if available)
        if security_score < 7.0:
            # Try to get specific security issues from bandit
            try:
                # Check if scorer has bandit issues
                if hasattr(self.scorer, "get_bandit_issues"):
                    bandit_issues = self.scorer.get_bandit_issues(file_path)
                    for issue in bandit_issues[:5]:  # Limit to first 5
                        finding_counter["security"] += 1
                        findings.append(
                            ReviewFinding(
                                id=f"TASK-{task_number}-SEC-{finding_counter['security']:03d}",
                                severity=Severity.HIGH
                                if issue.get("severity") == "HIGH"
                                else Severity.MEDIUM,
                                category="security",
                                file=file_str,
                                line=issue.get("line_number"),
                                finding=issue.get("test_id", "Security issue"),
                                impact=issue.get("issue_text", "Potential security vulnerability"),
                                suggested_fix=issue.get("more_info", "Review security best practices"),
                            )
                        )
                else:
                    # Fallback to score-based finding
                    finding_counter["security"] += 1
                    findings.append(
                        ReviewFinding(
                            id=f"TASK-{task_number}-SEC-{finding_counter['security']:03d}",
                            severity=Severity.HIGH if security_score < 5.0 else Severity.MEDIUM,
                            category="security",
                            file=file_str,
                            finding=f"Security score below threshold: {security_score:.1f}/10.0",
                            impact="Potential security vulnerabilities detected",
                            suggested_fix="Run security scan and review security best practices",
                        )
                    )
            except Exception as e:
                logger.debug(f"Failed to extract security issues: {e}")
                # Fallback to score-based finding
                finding_counter["security"] += 1
                findings.append(
                    ReviewFinding(
                        id=f"TASK-{task_number}-SEC-{finding_counter['security']:03d}",
                        severity=Severity.HIGH if security_score < 5.0 else Severity.MEDIUM,
                        category="security",
                        file=file_str,
                        finding=f"Security score below threshold: {security_score:.1f}/10.0",
                        impact="Potential security vulnerabilities",
                        suggested_fix="Review security best practices and fix identified issues",
                    )
                )

        # 3. Extract type checking errors (mypy)
        try:
            type_result = await self.type_check_file(file_path)
            type_errors = type_result.get("errors", [])
            if type_errors:
                for error in type_errors[:5]:  # Limit to first 5
                    finding_counter["type"] += 1
                    findings.append(
                        ReviewFinding(
                            id=f"TASK-{task_number}-TYPE-{finding_counter['type']:03d}",
                            severity=Severity.MEDIUM,
                            category="standards",
                            file=file_str,
                            line=error.get("line"),
                            finding=error.get("message", "Type checking error"),
                            impact="Type safety issue may cause runtime errors",
                            suggested_fix=error.get("suggestion", "Fix type annotations"),
                        )
                    )
        except Exception as e:
            logger.debug(f"Failed to extract type errors: {e}")

        # 4. Extract maintainability/complexity issues (if significant)
        if maintainability_score < 6.0:
            finding_counter["quality"] += 1
            complexity_note = ""
            if complexity_score > 7.0:
                complexity_note = " High cyclomatic complexity detected."

            findings.append(
                ReviewFinding(
                    id=f"TASK-{task_number}-MAINT-{finding_counter['quality']:03d}",
                    severity=Severity.MEDIUM,
                    category="code_quality",
                    file=file_str,
                    finding=f"Maintainability score below threshold: {maintainability_score:.1f}/10.0.{complexity_note}",
                    impact="Code may be difficult to maintain and refactor",
                    suggested_fix="Refactor to improve maintainability: reduce complexity, improve naming, add documentation",
                )
            )

        return findings

    def _detect_file_type(self, file_path: Path) -> str:
        """
        Detect file type from extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            File type string (python, yaml, typescript, javascript, etc.)
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".sh": "shell",
            ".ps1": "powershell",
            ".dockerfile": "dockerfile",
        }
        return extension_map.get(file_path.suffix.lower(), "unknown")

    def _score_yaml_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Score YAML file with YAML-specific analysis.
        
        Args:
            file_path: Path to YAML file
            code: File content
            
        Returns:
            Scoring dictionary with YAML-specific metrics
        """
        scores: dict[str, Any] = {
            "complexity_score": 5.0,  # Default for YAML
            "security_score": 8.0,  # Default, will be adjusted
            "maintainability_score": 7.0,  # Default
            "test_coverage_score": 0.0,  # Not applicable
            "performance_score": 10.0,  # Not applicable for config files
            "linting_score": 10.0,  # Will check YAML syntax
            "type_checking_score": 10.0,  # Not applicable
            "duplication_score": 10.0,  # Not applicable
            "overall_score": 75.0,  # Default
            "metrics": {},
        }
        
        # Check YAML syntax
        try:
            import yaml
            yaml.safe_load(code)
            scores["linting_score"] = 10.0
            yaml_valid = True
        except yaml.YAMLError as e:
            scores["linting_score"] = 0.0
            yaml_valid = False
            scores["yaml_error"] = str(e)
        except ImportError:
            # yaml library not available, skip validation
            yaml_valid = True
            scores["yaml_warning"] = "YAML library not available for validation"
        
        # Basic structure analysis
        lines = code.split('\n')
        scores["metrics"]["line_count"] = len(lines)
        scores["metrics"]["file_size"] = len(code)
        
        # Check for common YAML issues
        issues = []
        if not yaml_valid:
            issues.append("Invalid YAML syntax")
        
        # Check for Docker Compose specific patterns if applicable
        if "docker-compose" in file_path.name.lower():
            if "version:" not in code and '"version"' not in code:
                issues.append("Docker Compose version not specified")
            scores["file_subtype"] = "docker-compose"
        
        # Adjust security score based on issues
        if issues:
            scores["security_score"] = max(5.0, scores["security_score"] - len(issues) * 1.0)
        
        scores["yaml_issues"] = issues
        scores["yaml_valid"] = yaml_valid
        
        # Calculate overall score
        scores["overall_score"] = (
            scores["complexity_score"] * 0.1 +
            scores["security_score"] * 0.3 +
            scores["maintainability_score"] * 0.2 +
            scores["linting_score"] * 0.4
        ) * 10
        
        return scores

    async def get_documentation(
        self,
        library: str,
        topic: str | None = None,
        mode: str = "code",
        page: int = 1,
        no_cache: bool = False,
    ) -> dict[str, Any]:
        """
        Get library documentation from Context7 using KB-first lookup.
        
        R6: Reviewer docs command implementation.
        
        Args:
            library: Library name (e.g., "react", "fastapi")
            topic: Optional topic name (e.g., "hooks", "routing")
            mode: Documentation mode ("code" or "info")
            page: Page number for pagination
            no_cache: Skip cache and fetch fresh documentation
            
        Returns:
            Dictionary with documentation content and metadata
        """
        from ...context7.agent_integration import get_context7_helper
        
        # Get Context7 helper
        context7_helper = get_context7_helper(self, config=self.config, project_root=self._project_root)
        
        if not context7_helper or not context7_helper.enabled:
            return {
                "error": "Context7 is not enabled or not available. Check your configuration.",
                "library": library,
                "topic": topic,
            }
        
        try:
            # Use KB-first lookup (respects no_cache flag via lookup implementation)
            # Note: no_cache flag would need to be passed through to KBLookup if implemented
            result = await context7_helper.get_documentation(
                library=library,
                topic=topic,
                use_fuzzy_match=True,
            )
            
            if result:
                return {
                    "success": True,
                    "library": result.get("library", library),
                    "topic": result.get("topic", topic or "overview"),
                    "content": result.get("content", ""),
                    "source": result.get("source", "unknown"),  # "cache", "api", "fuzzy_match"
                    "fuzzy_score": result.get("fuzzy_score"),
                    "matched_topic": result.get("matched_topic"),
                    "response_time_ms": result.get("response_time_ms", 0.0),
                    "cached": result.get("source") == "cache",
                }
            else:
                return {
                    "success": False,
                    "error": f"Documentation not found for library '{library}'" + (f" (topic: {topic})" if topic else ""),
                    "library": library,
                    "topic": topic,
                    "suggestion": "Try a different library name or check if the library is available in Context7",
                }
        except Exception as e:
            logger.warning(
                f"Failed to get Context7 documentation for library '{library}' (topic: {topic}): {e}",
                exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to retrieve documentation: {str(e)}",
                "library": library,
                "topic": topic,
            }

    def _score_generic_file(self, file_path: Path, code: str, file_type: str) -> dict[str, Any]:
        """
        Score generic/non-Python file with basic analysis.
        
        Args:
            file_path: Path to file
            code: File content
            file_type: Detected file type
            
        Returns:
            Scoring dictionary with generic metrics
        """
        lines = code.split('\n')
        line_count = len(lines)
        
        scores: dict[str, Any] = {
            "complexity_score": 5.0,  # Default
            "security_score": 7.0,  # Default
            "maintainability_score": 7.0,  # Default
            "test_coverage_score": 0.0,  # Not applicable
            "performance_score": 10.0,  # Not applicable for config files
            "linting_score": 10.0,  # Not applicable
            "type_checking_score": 10.0,  # Not applicable
            "duplication_score": 10.0,  # Not applicable
            "overall_score": 70.0,  # Default
            "metrics": {
                "line_count": line_count,
                "file_size": len(code),
            },
            "file_type": file_type,
            "message": f"Generic analysis for {file_type} file. File-type-specific analysis not available.",
        }
        
        return scores

    async def close(self):
        """Clean up resources"""
        pass
