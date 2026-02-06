"""
Reviewer Agent - Performs code review with scoring
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...core.language_detector import Language
from ...experts.agent_integration import ExpertSupportMixin
from ..ops.dependency_analyzer import DependencyAnalyzer
from .aggregator import QualityAggregator
from .docker_compose_validator import DockerComposeValidator
from .dockerfile_validator import DockerfileValidator
from .influxdb_validator import InfluxDBValidator
from .library_patterns import LibraryPatternRegistry
from .mqtt_validator import MQTTValidator
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
from .validation import validate_boolean, validate_file_path_input, validate_inputs
from .websocket_validator import WebSocketValidator

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
        
        # Initialize library pattern registry for extensible library-specific checks
        self.pattern_registry = LibraryPatternRegistry()
        
        # NEW: Initialize library detection components (Priority 1 & 2)
        reviewer_config = config.agents.reviewer if config and hasattr(config, 'agents') else None
        auto_library_detection = (
            reviewer_config.auto_library_detection 
            if reviewer_config else True
        )
        library_detection_depth = (
            reviewer_config.library_detection_depth 
            if reviewer_config else "both"
        )
        
        if auto_library_detection:
            from .library_detector import LibraryDetector
            self.library_detector = LibraryDetector(
                include_stdlib=False,
                detection_depth=library_detection_depth
            )
        else:
            self.library_detector = None
        
        # NEW: Initialize pattern detector
        pattern_detection_enabled = (
            reviewer_config.pattern_detection_enabled 
            if reviewer_config else True
        )
        pattern_confidence_threshold = (
            reviewer_config.pattern_confidence_threshold 
            if reviewer_config else 0.5
        )
        
        if pattern_detection_enabled:
            from .pattern_detector import PatternDetector
            self.pattern_detector = PatternDetector(
                confidence_threshold=pattern_confidence_threshold
            )
        else:
            self.pattern_detector = None
        
        # NEW: Initialize Context7 enhancer and output enhancer (will be set in activate)
        self.context7_enhancer = None
        from .output_enhancer import ReviewOutputEnhancer
        self.output_enhancer = ReviewOutputEnhancer()

        # Adaptive scoring integration (will be initialized in activate)
        self.adaptive_scorer = None
        self.adaptive_scoring_enabled = True  # Enabled by default

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
        
        # NEW: Initialize Context7 enhancer if Context7 is enabled (Priority 1 & 2)
        reviewer_config = self.config.agents.reviewer if self.config and hasattr(self.config, 'agents') else None
        auto_context7 = (
            reviewer_config.auto_context7_lookups 
            if reviewer_config else True
        )
        context7_timeout = (
            reviewer_config.context7_timeout 
            if reviewer_config else 30
        )
        context7_cache_enabled = (
            reviewer_config.context7_cache_enabled 
            if reviewer_config else True
        )
        
        # Get Context7 helper if available
        context7_helper = None
        try:
            from ...context7.agent_integration import get_context7_helper
            context7_helper = get_context7_helper(self, self.config, project_root)
        except Exception as e:
            logger.debug(f"Context7 helper not available: {e}")
        
        if (auto_context7 and 
            context7_helper and 
            context7_helper.enabled):
            from .context7_enhancer import Context7ReviewEnhancer
            self.context7_enhancer = Context7ReviewEnhancer(
                context7_helper=context7_helper,
                timeout=context7_timeout,
                cache_enabled=context7_cache_enabled
            )
        else:
            self.context7_enhancer = None

        # Initialize adaptive scorer if enabled
        if self.adaptive_scoring_enabled:
            try:
                from .adaptive_scorer import AdaptiveScorerWrapper
                self.adaptive_scorer = AdaptiveScorerWrapper(enabled=True)
                # Pre-load adaptive weights asynchronously
                import asyncio
                asyncio.create_task(self.adaptive_scorer.get_adaptive_weights())
            except Exception as e:
                logger.warning(f"Failed to initialize adaptive scorer: {e}")
                self.adaptive_scorer = None

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
                    "error": f"Review failed: {e!s}",
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
            
            explain = kwargs.get("explain", False)

            try:
                return await self.review_file(
                    Path(file_path), include_scoring=True, include_llm_feedback=False, include_explanations=explain
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
            
            # P1 Improvement: Support isolated mode for target-aware linting
            isolated = kwargs.get("isolated", False)

            return await self.lint_file(Path(file_path), isolated=isolated)

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
                
        except TimeoutError:
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

    def _generate_python_explanations(self, scores: dict[str, Any]) -> dict[str, Any]:
        """
        Generate explanations for Python code scores.
        
        Args:
            scores: Dictionary of score values
            
        Returns:
            Dictionary of explanations for each score
        """
        explanations = {}
        
        # Complexity explanation
        complexity = scores.get("complexity_score", 10.0)
        if complexity < 7.0:
            explanations["complexity_score"] = {
                "score": complexity,
                "reason": "High cyclomatic complexity detected",
                "recommendations": [
                    "Break down large functions into smaller, focused functions",
                    "Reduce nested conditionals using guard clauses",
                    "Consider using polymorphism instead of large switch/if-else chains",
                ]
            }
        
        # Security explanation
        security = scores.get("security_score", 10.0)
        if security < 7.0:
            bandit_issues = scores.get("bandit_issues", [])
            explanations["security_score"] = {
                "score": security,
                "reason": f"{len(bandit_issues)} security issues detected by Bandit",
                "issues": bandit_issues[:5] if bandit_issues else [],
                "recommendations": [
                    "Review Bandit findings and address HIGH severity issues first",
                    "Consider input validation and sanitization",
                    "Review cryptographic practices",
                ]
            }
        
        # Linting explanation
        linting = scores.get("linting_score", 10.0)
        if linting < 8.0:
            linting_issues = scores.get("linting_issues", [])
            explanations["linting_score"] = {
                "score": linting,
                "reason": f"{len(linting_issues)} linting issues found by Ruff",
                "issues": linting_issues[:5] if linting_issues else [],
                "recommendations": [
                    "Run 'ruff check --fix' to auto-fix fixable issues",
                    "Review code style guidelines",
                    "Consider adding ruff to pre-commit hooks",
                ]
            }
        
        # Type checking explanation
        type_score = scores.get("type_checking_score", 10.0)
        if type_score < 8.0:
            type_issues = scores.get("type_issues", [])
            explanations["type_checking_score"] = {
                "score": type_score,
                "reason": f"{len(type_issues)} type errors found by mypy",
                "issues": type_issues[:5] if type_issues else [],
                "recommendations": [
                    "Add type annotations to function signatures",
                    "Use typing module for complex types",
                    "Consider running 'mypy --strict' locally",
                ]
            }
        
        return explanations

    @validate_inputs(
        include_scoring=validate_boolean,
        include_llm_feedback=validate_boolean,
        include_explanations=validate_boolean,
    )
    async def review_file(
        self,
        file_path: Path,
        include_scoring: bool = True,
        include_llm_feedback: bool = True,
        include_explanations: bool = False,
    ) -> dict[str, Any]:
        """
        Review a code file with timeout protection and improved error handling.

        Args:
            file_path: Path to code file
            include_scoring: Include code scores
            include_llm_feedback: Include LLM-generated feedback (via Cursor Skills)
            include_explanations: Include detailed score explanations (useful for TypeScript)

        Returns:
            Review results with scores and feedback

        Raises:
            TimeoutError: If review operation exceeds configured timeout
            ValueError: If file cannot be read or validated
            FileNotFoundError: If file does not exist
            RuntimeError: If scoring fails
        """
        # Validate file_path (manual validation since decorator doesn't handle Path well)
        file_path = validate_file_path_input(file_path, must_exist=True, method_name="review_file")
        
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
                    file_path, include_scoring, include_llm_feedback, max_file_size, include_explanations
                ),
                timeout=operation_timeout,
            )
        except TimeoutError:
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
        include_explanations: bool = False,
    ) -> dict[str, Any]:
        """Internal review implementation without timeout wrapper."""
        # #region agent log
        from ...core.debug_logger import write_debug_log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G",
                "message": "_review_file_internal called",
                "data": {"file": str(file_path), "include_scoring": include_scoring},
            },
            project_root=self._project_root,
            location="reviewer/agent.py:_review_file_internal:entry",
        )
        # #endregion
        # Use centralized path validation from BaseAgent
        # _validate_path handles existence, size, and path traversal checks
        # #region agent log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G",
                "message": "About to validate path",
                "data": {"file": str(file_path)},
            },
            project_root=self._project_root,
            location="reviewer/agent.py:_review_file_internal:before_validate",
        )
        # #endregion
        self._validate_path(file_path, max_file_size=max_file_size)
        # #region agent log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G",
                "message": "Path validation completed",
                "data": {"file": str(file_path)},
            },
            project_root=self._project_root,
            location="reviewer/agent.py:_review_file_internal:after_validate",
        )
        # #endregion

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
        # Reuse helper from context7_enhancer when available (set in activate()); fallback to get_context7_helper.
        context7_helper = (
            getattr(self.context7_enhancer, "context7_helper", None)
            if self.context7_enhancer
            else None
        )
        if not context7_helper:
            try:
                from ...context7.agent_integration import get_context7_helper
                context7_helper = get_context7_helper(
                    self, self.config, self._project_root
                )
            except Exception as e:
                logger.debug("Context7 helper not available: %s", e)
                context7_helper = None

        context7_verification = {}
        libraries_used = []
        if context7_helper and context7_helper.enabled:
            logger.debug(
                "Context7 enabled, library_detector=%s",
                context7_helper.library_detector is not None,
            )
            try:
                # E2: Detect libraries ONLY from code (not project files)
                # This ensures we only verify libraries actually used in the code
                language_str = file_type.lower()  # "python", "typescript", etc.
                if code and context7_helper.library_detector:
                    libraries_used = context7_helper.library_detector.detect_from_code(
                        code=code,
                        language=language_str
                    )
                    logger.debug(
                        "Library detection: %d libraries found: %s",
                        len(libraries_used),
                        libraries_used,
                    )
                else:
                    libraries_used = []
            except Exception as e:
                logger.debug("Library detection failed: %s", e)
                libraries_used = []

            if libraries_used:
                try:
                    # Pre-process code once for efficient string matching
                    code_lower = code.lower() if code else ""
                    
                    # Verify all libraries in parallel for better performance
                    async def verify_library(lib: str) -> tuple[str, dict[str, Any]]:
                        """Verify a single library with parallel doc fetches."""
                        try:
                            lib_docs_task = asyncio.wait_for(
                                context7_helper.get_documentation(
                                    library=lib,
                                    topic=None,
                                    use_fuzzy_match=True
                                ),
                                timeout=15.0,
                            )
                            best_practices_task = asyncio.wait_for(
                                context7_helper.get_documentation(
                                    library=lib,
                                    topic="best-practices",
                                    use_fuzzy_match=True
                                ),
                                timeout=15.0,
                            )
                            lib_docs, best_practices = await asyncio.gather(
                                lib_docs_task, best_practices_task,
                                return_exceptions=True  # Don't fail all if one fails
                            )
                            # Handle exceptions gracefully
                            if isinstance(lib_docs, Exception):
                                logger.debug(f"Failed to fetch docs for {lib}: {lib_docs}")
                                lib_docs = None
                            if isinstance(best_practices, Exception):
                                logger.debug(f"Failed to fetch best practices for {lib}: {best_practices}")
                                best_practices = None
                            
                            # Basic API correctness check (efficient: use pre-processed code)
                            api_mentioned = lib.lower() in code_lower
                            
                            return (lib, {
                                "api_docs_available": lib_docs is not None,
                                "best_practices_available": best_practices is not None,
                                "api_mentioned": api_mentioned,
                                "docs_source": lib_docs.get("source") if lib_docs else None,
                                "best_practices_source": best_practices.get("source") if best_practices else None,
                            })
                        except Exception as e:
                            logger.debug(f"Failed to verify library {lib}: {e}")
                            return (lib, {
                                "api_docs_available": False,
                                "best_practices_available": False,
                                "api_mentioned": False,
                                "error": str(e)
                            })
                    
                    # Verify all libraries in parallel with timeout protection
                    coroutines = [verify_library(lib) for lib in libraries_used]
                    try:
                        results = await asyncio.wait_for(
                            asyncio.gather(*coroutines, return_exceptions=True),
                            timeout=30.0  # 30s total timeout for all libraries
                        )
                    except TimeoutError:
                        # If Context7 hangs, log and continue without it
                        logger.warning(
                            "Context7 library verification timed out after 30s for %d libraries.",
                            len(libraries_used),
                        )
                        # Mark all as failed due to timeout
                        results = []
                        for lib in libraries_used:
                            results.append((lib, {
                                "api_docs_available": False,
                                "best_practices_available": False,
                                "api_mentioned": False,
                                "error": "timeout"
                            }))
                    context7_verification.update(dict(results))
                    logger.debug(f"E2: Verified {len(libraries_used)} libraries with Context7")
                except TimeoutError:
                    logger.warning(f"Library verification timed out for {len(libraries_used)} libraries")
                    # Mark all as failed
                    for lib in libraries_used:
                        if lib not in context7_verification:
                            context7_verification[lib] = {
                                "api_docs_available": False,
                                "best_practices_available": False,
                                "api_mentioned": False,
                                "error": "timeout"
                            }
                except Exception as e:
                    logger.debug(f"E2: Context7 API verification failed: {e}")
        
        # Store Context7 verification results (always store, even if empty)
        result["context7_verification"] = context7_verification
        result["libraries_detected"] = libraries_used
        if context7_helper:
            result["context7_debug"] = {
                "helper_enabled": context7_helper.enabled,
                "has_library_detector": context7_helper.library_detector is not None,
                "mcp_gateway_available": self.mcp_gateway is not None,
            }

        # Enhancement 4: Proactive Context7 suggestions based on library-specific patterns
        # Use extensible pattern registry instead of hard-coded logic
        context7_suggestions = []
        if context7_helper and context7_helper.enabled and libraries_used:
            try:
                # Use pattern registry to generate suggestions from all matching checkers
                context7_suggestions = await self.pattern_registry.generate_suggestions(
                    code=code,
                    libraries_detected=libraries_used,
                    context7_helper=context7_helper
                )
                
                if context7_suggestions:
                    logger.debug(f"Enhancement 4: Generated {len(context7_suggestions)} proactive Context7 suggestions")
            except Exception as e:
                logger.debug(f"Enhancement 4: Proactive Context7 suggestions failed: {e}")
        
        # Add Context7 suggestions to result
        if context7_suggestions:
            if "suggestions" not in result:
                result["suggestions"] = []
            result["suggestions"].extend(context7_suggestions)

        # Calculate scores based on file type with timeout protection
        if include_scoring:
            from ...core.language_detector import Language
            from .scoring import ScorerFactory

            language = detection_result.language
            reviewer_config = self.config.agents.reviewer if self.config else None
            tool_timeout = reviewer_config.tool_timeout if reviewer_config else 30.0
            
            # Apply adaptive weights if available
            if self.adaptive_scorer and self.adaptive_scoring_enabled:
                try:
                    adaptive_weights = await self.adaptive_scorer.get_adaptive_weights()
                    if adaptive_weights:
                        # Update scorer with adaptive weights
                        adaptive_weights_config = self.adaptive_scorer.get_weights_config()
                        # Update scorer weights (if scorer supports it)
                        if hasattr(self.scorer, 'weights'):
                            self.scorer.weights = adaptive_weights_config
                except Exception as e:
                    logger.debug(f"Failed to apply adaptive weights: {e}")
            
            try:
                if language == Language.YAML:
                    scores = await asyncio.wait_for(
                        asyncio.to_thread(self._score_yaml_file, file_path, code),
                        timeout=tool_timeout,
                    )
                else:
                    # Use ScorerFactory to get appropriate scorer for the language
                    scorer = ScorerFactory.get_scorer(language, self.config)
                    # Apply adaptive weights to scorer if available
                    if self.adaptive_scorer and self.adaptive_scoring_enabled and hasattr(scorer, 'weights'):
                        try:
                            adaptive_weights_config = self.adaptive_scorer.get_weights_config()
                            scorer.weights = adaptive_weights_config
                        except Exception as e:
                            logger.debug(f"Failed to apply adaptive weights to scorer: {e}")
                    # Run scoring in thread with timeout
                    scores = await asyncio.wait_for(
                        asyncio.to_thread(scorer.score_file, file_path, code),
                        timeout=tool_timeout,
                    )
            except TimeoutError:
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
                except TimeoutError:
                    logger.debug(f"Dependency security check timed out for {file_path}")
                    # Continue without dependency security penalty
                except Exception as e:
                    logger.debug(f"Dependency security check failed: {e}")
                    # Continue without dependency security penalty

            result["scoring"] = scores
            
            # Track outcome for adaptive learning (if enabled)
            if self.adaptive_scorer and self.adaptive_scoring_enabled and include_scoring:
                try:
                    # Extract expert IDs from consultations
                    expert_consultations = []
                    if expert_guidance:
                        # Extract expert IDs from consultation results
                        # Note: This is a simplified extraction - actual expert IDs would come from consultation results
                        if "security" in expert_guidance:
                            expert_consultations.append("expert-security")
                        if "performance" in expert_guidance:
                            expert_consultations.append("expert-performance-optimization")
                        if "code_quality" in expert_guidance:
                            expert_consultations.append("expert-code-quality-analysis")
                        if "api_design" in expert_guidance:
                            expert_consultations.append("expert-api-design-integration")
                    
                    # Generate workflow ID from file path
                    import hashlib
                    workflow_id = f"review-{hashlib.sha256(str(file_path).encode()).hexdigest()[:16]}"
                    
                    # Track initial scores
                    await self.adaptive_scorer.track_outcome(
                        workflow_id=workflow_id,
                        file_path=file_path,
                        scores=scores,
                        expert_consultations=expert_consultations if expert_consultations else None,
                        agent_id="reviewer",
                    )
                except Exception as e:
                    logger.debug(f"Failed to track outcome: {e}")
            
            # Add score explanations if requested (especially useful for TypeScript)
            if include_explanations:
                explanations = {}
                if file_type in ("typescript", "javascript") and hasattr(self, 'typescript_scorer'):
                    try:
                        # Get security issues for explanation
                        security_issues = self.typescript_scorer.get_security_issues(code, file_path)
                        security_issues_list = [
                            {"pattern": i.pattern, "severity": i.severity, "line": i.line, 
                             "message": i.message, "recommendation": i.recommendation}
                            for i in security_issues
                        ] if security_issues else []
                        
                        # Generate explanations
                        eslint_available = self.typescript_scorer._check_eslint_available()
                        tsc_available = self.typescript_scorer._check_tsc_available()
                        explanations = self.typescript_scorer._generate_explanations(
                            scores, security_issues_list, eslint_available, tsc_available
                        )
                    except Exception as e:
                        logger.debug(f"Failed to generate TypeScript explanations: {e}")
                        explanations = {"error": str(e)}
                else:
                    # Generic explanations for Python
                    explanations = self._generate_python_explanations(scores)
                
                result["score_explanations"] = explanations

            # Phase 2 (P0): Add maintainability issues to output (outside include_explanations block)
            if include_scoring and self.scorer:
                try:
                    maintainability_issues = self.scorer.get_maintainability_issues(code, file_path)
                    # Always include maintainability_issues (even if empty) for consistency
                    result["maintainability_issues"] = maintainability_issues
                    result["maintainability_issues_summary"] = {
                        "total": len(maintainability_issues),
                        "by_severity": {
                            "high": sum(1 for issue in maintainability_issues if issue.get("severity") == "high"),
                            "medium": sum(1 for issue in maintainability_issues if issue.get("severity") == "medium"),
                            "low": sum(1 for issue in maintainability_issues if issue.get("severity") == "low"),
                        },
                        "by_type": {}
                    }
                    # Count by issue type
                    for issue in maintainability_issues:
                        issue_type = issue.get("issue_type", "unknown")
                        result["maintainability_issues_summary"]["by_type"][issue_type] = \
                            result["maintainability_issues_summary"]["by_type"].get(issue_type, 0) + 1
                except Exception as e:
                    logger.warning(f"Failed to get maintainability issues: {e}", exc_info=True)
                    # Include empty list on error for consistency
                    result["maintainability_issues"] = []
                    result["maintainability_issues_summary"] = {
                        "total": 0,
                        "by_severity": {"high": 0, "medium": 0, "low": 0},
                        "by_type": {}
                    }

            # Phase 4 (P1): Add performance issues to output (outside include_explanations block)
            if include_scoring and self.scorer:
                try:
                    performance_issues = self.scorer.get_performance_issues(code, file_path)
                    # Always include performance_issues (even if empty) for consistency
                    result["performance_issues"] = performance_issues
                    result["performance_issues_summary"] = {
                        "total": len(performance_issues),
                        "by_severity": {
                            "high": sum(1 for issue in performance_issues if issue.get("severity") == "high"),
                            "medium": sum(1 for issue in performance_issues if issue.get("severity") == "medium"),
                            "low": sum(1 for issue in performance_issues if issue.get("severity") == "low"),
                        },
                    }
                except Exception as e:
                    logger.warning(f"Failed to get performance issues: {e}", exc_info=True)
                    # Include empty list on error for consistency
                    result["performance_issues"] = []
                    result["performance_issues_summary"] = {
                        "total": 0,
                        "by_severity": {"high": 0, "medium": 0, "low": 0},
                    }
        
        # NEW: Library detection and Context7 integration (Priority 1 & 2)
        library_recommendations = {}
        pattern_guidance = {}
        
        # Detect libraries if enabled
        libraries = []
        if self.library_detector and file_type == "python":
            try:
                libraries = self.library_detector.detect_all(code, file_path)
                if libraries:
                    logger.debug(f"Detected {len(libraries)} libraries: {libraries}")
            except Exception as e:
                logger.warning(f"Library detection failed: {e}")
        
        # Detect patterns if enabled
        patterns = []
        if self.pattern_detector:
            try:
                patterns = self.pattern_detector.detect_patterns(code)
                if patterns:
                    logger.debug(f"Detected {len(patterns)} patterns: {[p.pattern_name for p in patterns]}")
            except Exception as e:
                logger.warning(f"Pattern detection failed: {e}")
        
        # Get Context7 recommendations if enabled
        if self.context7_enhancer:
            try:
                if libraries:
                    library_recommendations = await self.context7_enhancer.get_library_recommendations(
                        libraries
                    )
                    if library_recommendations:
                        logger.debug(f"Got Context7 recommendations for {len(library_recommendations)} libraries")
                
                if patterns:
                    pattern_guidance = await self.context7_enhancer.get_pattern_guidance(
                        patterns
                    )
                    if pattern_guidance:
                        logger.debug(f"Got Context7 guidance for {len(pattern_guidance)} patterns")
            except Exception as e:
                logger.warning(f"Context7 enhancement failed: {e}")
        
        # Enhance output with library recommendations and pattern guidance
        if library_recommendations or pattern_guidance:
            result = self.output_enhancer.enhance_output(
                result,
                library_recommendations,
                pattern_guidance
            )
        
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

            # Consult API Design expert if code appears to be an HTTP/API client
            if await self._detect_api_client_pattern(code_preview):
                try:
                    api_consultation = await expert_registry.consult(
                        query=f"Review this API client code for best practices:\n\n{code_preview}",
                        domain="api-design-integration",
                        include_all=True,
                        prioritize_builtin=True,
                        agent_id="reviewer",
                    )
                    expert_guidance["api_design"] = api_consultation.weighted_answer
                    expert_guidance["api_design_confidence"] = api_consultation.confidence
                except Exception:
                    logger.debug("API design expert consultation failed", exc_info=True)
                
                # Also consult external-api-integration if code mentions external/third-party APIs
                if "external" in code_preview.lower() or "third-party" in code_preview.lower():
                    try:
                        external_consultation = await expert_registry.consult(
                            query=f"Review this external API integration code:\n\n{code_preview}",
                            domain="api-design-integration",  # external-api is a subdomain
                            include_all=True,
                            prioritize_builtin=True,
                            agent_id="reviewer",
                        )
                        expert_guidance["external_api"] = external_consultation.weighted_answer
                    except Exception:
                        logger.debug("External API expert consultation failed", exc_info=True)

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
        # Phase 6 (P1): Context-aware quality gates based on file status
        # Note: Quality gate checks use tool operations (coverage analysis) which are Cursor-first compatible.
        # LLM feedback generation already uses GenericInstruction with to_skill_command() for Cursor Skills.
        quality_gate_result = None
        if include_scoring and self.config:
            from ...quality.quality_gates import QualityGate, QualityThresholds
            from .context_detector import FileContextDetector

            scoring_config = self.config.scoring
            quality_gates_config = scoring_config.quality_gates if scoring_config else None

            # Check if quality gates are enabled
            if quality_gates_config and quality_gates_config.enabled:
                # Phase 6 (P1): Detect file context for context-aware thresholds
                context_detector = FileContextDetector(project_root=self._project_root)
                file_context = context_detector.detect_context(file_path)

                # Phase 6 (P1): Apply context-aware thresholds
                if file_context.is_new():
                    # New files: More lenient thresholds (warnings, not failures)
                    thresholds = QualityThresholds(
                        overall_min=5.0,  # Lower threshold for new files (warnings only)
                        security_min=6.0,  # Lower security threshold (critical issues only)
                        test_coverage_min=0.0,  # No coverage requirement for new files
                    )
                    result["file_context"] = {
                        "status": "new",
                        "age_days": file_context.age_days,
                        "confidence": file_context.confidence,
                        "thresholds_applied": "new_file",
                    }
                elif file_context.is_modified():
                    # Modified files: Standard thresholds
                    thresholds = QualityThresholds(
                        overall_min=8.0,  # Standard threshold
                        security_min=8.5,  # Standard security threshold
                        test_coverage_min=(
                            quality_gates_config.test_coverage.threshold * 100.0
                            if quality_gates_config.test_coverage.enabled
                            else 70.0  # Slightly lower for modified files
                        ),
                    )
                    result["file_context"] = {
                        "status": "modified",
                        "git_status": file_context.git_status,
                        "confidence": file_context.confidence,
                        "thresholds_applied": "modified_file",
                    }
                else:
                    # Existing files: Strict thresholds (enforce all quality gates)
                    thresholds = QualityThresholds(
                        overall_min=8.0,  # Standard threshold
                        security_min=8.5,  # Standard security threshold
                        test_coverage_min=(
                            quality_gates_config.test_coverage.threshold * 100.0
                            if quality_gates_config.test_coverage.enabled
                            else 80.0  # Strict threshold for existing files
                        ),
                    )
                    result["file_context"] = {
                        "status": "existing",
                        "age_days": file_context.age_days,
                        "confidence": file_context.confidence,
                        "thresholds_applied": "existing_file",
                    }

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
        Phase 3 (P0): Enhanced to provide structured feedback fallback when LLM execution unavailable.
        
        Note: Retry logic should be applied at the Cursor Skills execution layer,
        not here (this just prepares the instruction). See retry_handler.py for
        retry decorator usage.
        """
        from ...core.runtime_mode import RuntimeMode, detect_runtime_mode
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

        # Phase 3 (P0): Generate structured feedback fallback based on scores
        # This provides actionable feedback even when LLM execution isn't available
        structured_feedback = self._generate_structured_feedback_fallback(
            code, language, scores, expert_guidance
        )

        result = {
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "structured_feedback": structured_feedback,  # Phase 3: Always include structured feedback
            "execution_mode": detect_runtime_mode().value,
        }

        # Phase 3: In Cursor mode, note that instruction needs execution
        if detect_runtime_mode() == RuntimeMode.CURSOR:
            result["note"] = (
                "LLM feedback instruction prepared for Cursor Skills execution. "
                "Structured feedback is provided as fallback below."
            )
        else:
            result["note"] = (
                "LLM feedback instruction prepared. "
                "Structured feedback provided below (LLM execution requires Cursor Skills)."
            )

        return result

    def _generate_structured_feedback_fallback(
        self,
        code: str,
        language: Language,
        scores: dict[str, Any] | None,
        expert_guidance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured feedback based on scores and issues (Phase 3 - P0).
        
        Provides actionable feedback even when LLM execution isn't available.
        This addresses the feedback issue where prompts exist but aren't executed.
        
        Returns:
            Dictionary with structured feedback sections
        """
        feedback: dict[str, Any] = {
            "summary": "",
            "strengths": [],
            "issues": [],
            "recommendations": [],
            "priority": "medium",  # low, medium, high
        }

        if not scores:
            feedback["summary"] = "No scoring data available. Review code manually."
            return feedback

        # Extract scores
        overall = scores.get("overall_score", 0.0)
        complexity = scores.get("complexity_score", 5.0)
        security = scores.get("security_score", 5.0)
        maintainability = scores.get("maintainability_score", 5.0)
        test_coverage = scores.get("test_coverage_score", 0.0)
        performance = scores.get("performance_score", 5.0)

        # Generate summary
        if overall >= 80:
            feedback["summary"] = f"Code quality is excellent (score: {overall:.1f}/100). Minor improvements possible."
            feedback["priority"] = "low"
        elif overall >= 70:
            feedback["summary"] = f"Code quality is good (score: {overall:.1f}/100). Some areas need attention."
            feedback["priority"] = "medium"
        elif overall >= 60:
            feedback["summary"] = f"Code quality needs improvement (score: {overall:.1f}/100). Several issues to address."
            feedback["priority"] = "high"
        else:
            feedback["summary"] = f"Code quality is poor (score: {overall:.1f}/100). Significant refactoring needed."
            feedback["priority"] = "high"

        # Identify strengths
        if security >= 8.0:
            feedback["strengths"].append(f"Strong security practices (score: {security:.1f}/10)")
        if maintainability >= 7.0:
            feedback["strengths"].append(f"Good maintainability (score: {maintainability:.1f}/10)")
        if complexity <= 5.0:
            feedback["strengths"].append(f"Low complexity (score: {complexity:.1f}/10)")
        if test_coverage >= 7.0:
            feedback["strengths"].append(f"Good test coverage (score: {test_coverage:.1f}/10)")

        # Identify issues and recommendations
        if security < 7.0:
            feedback["issues"].append({
                "category": "security",
                "severity": "high" if security < 6.0 else "medium",
                "message": f"Security score is {security:.1f}/10 (threshold: 7.0)",
                "recommendation": "Review security patterns, validate inputs, check for vulnerabilities"
            })
            feedback["recommendations"].append("Run security scan and address vulnerabilities")

        if maintainability < 7.0:
            feedback["issues"].append({
                "category": "maintainability",
                "severity": "high" if maintainability < 5.0 else "medium",
                "message": f"Maintainability score is {maintainability:.1f}/10 (threshold: 7.0)",
                "recommendation": "Add docstrings, reduce complexity, improve code organization"
            })
            feedback["recommendations"].append("Review maintainability issues for specific improvements")

        if test_coverage < 5.0:
            feedback["issues"].append({
                "category": "test_coverage",
                "severity": "high" if test_coverage == 0.0 else "medium",
                "message": f"Test coverage is {test_coverage:.1f}/10 (threshold: 5.0)",
                "recommendation": "Add unit tests for critical functions and edge cases"
            })
            feedback["recommendations"].append("Generate tests using @tester *test command")

        if complexity > 7.0:
            feedback["issues"].append({
                "category": "complexity",
                "severity": "high" if complexity > 8.0 else "medium",
                "message": f"Complexity score is {complexity:.1f}/10 (threshold: 7.0)",
                "recommendation": "Refactor complex functions, extract helper methods, reduce nesting"
            })
            feedback["recommendations"].append("Break down complex functions into smaller, focused functions")

        if performance < 6.0:
            feedback["issues"].append({
                "category": "performance",
                "severity": "medium",
                "message": f"Performance score is {performance:.1f}/10 (threshold: 6.0)",
                "recommendation": "Review performance bottlenecks, optimize loops, cache expensive operations"
            })
            feedback["recommendations"].append("Review performance issues for specific bottlenecks")

        # Add expert guidance if available
        if expert_guidance:
            if "security" in expert_guidance:
                feedback["expert_guidance"] = {
                    "security": expert_guidance["security"][:500] + "..." if len(expert_guidance["security"]) > 500 else expert_guidance["security"]
                }
            if "performance" in expert_guidance:
                feedback["expert_guidance"] = feedback.get("expert_guidance", {})
                feedback["expert_guidance"]["performance"] = expert_guidance["performance"][:300] + "..." if len(expert_guidance["performance"]) > 300 else expert_guidance["performance"]
            if "api_design" in expert_guidance:
                feedback["expert_guidance"] = feedback.get("expert_guidance", {})
                feedback["expert_guidance"]["api_design"] = expert_guidance["api_design"][:500] + "..." if len(expert_guidance["api_design"]) > 500 else expert_guidance["api_design"]
            if "external_api" in expert_guidance:
                feedback["expert_guidance"] = feedback.get("expert_guidance", {})
                feedback["expert_guidance"]["external_api"] = expert_guidance["external_api"][:300] + "..." if len(expert_guidance["external_api"]) > 300 else expert_guidance["external_api"]

        return feedback

    async def lint_file(self, file_path: Path, isolated: bool = False) -> dict[str, Any]:
        """
        Run Ruff linting on a file and return detailed issues with timeout protection.

        Phase 6: Modern Quality Analysis - Ruff Integration

        Args:
            file_path: Path to code file (Python only)
            isolated: If True, run ruff in isolated mode ignoring project config.
                     P1 Improvement: Makes linting target-aware.

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
        # Use centralized path validation from BaseAgent
        self._validate_path(file_path)
        
        # Get timeout configuration
        reviewer_config = self.config.agents.reviewer if self.config else None
        tool_timeout = reviewer_config.tool_timeout if reviewer_config else 30.0
        
        try:
            return await asyncio.wait_for(
                self._lint_file_internal(file_path, isolated=isolated),
                timeout=tool_timeout,
            )
        except TimeoutError:
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
    
    async def _lint_file_internal(self, file_path: Path, isolated: bool = False) -> dict[str, Any]:
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
            # P1 Improvement: Support isolated mode for target-aware linting
            if isolated:
                # Run ruff directly with --isolated flag to ignore project config
                issues_raw = self._run_ruff_isolated(file_path)
                # Calculate score from isolated results
                linting_score = self._calculate_score_from_issues(issues_raw)
            else:
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

            # ENH-002 Story #18: Group issues by rule code for cleaner output
            grouped = self.scorer._group_ruff_issues_by_code(issues)

            return {
                "file": str(file_path),
                "linting_score": linting_score,
                "issues": issues,
                "issue_count": len(issues),
                "error_count": error_count,
                "warning_count": warning_count,
                "fatal_count": fatal_count,
                "grouped": grouped,  # Add grouped summary
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

    def _run_ruff_isolated(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Run ruff in isolated mode, ignoring project configuration.
        
        P1 Improvement: Target-aware linting that only applies ruff defaults,
        not project-specific rules that might scan unrelated files.
        
        Args:
            file_path: Path to Python file to lint
            
        Returns:
            List of diagnostic dictionaries from ruff
        """
        import json
        import subprocess
        import sys
        
        try:
            result = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "--isolated",  # Ignore pyproject.toml, ruff.toml
                    "--no-cache",  # Don't use cache for isolated runs
                    "--output-format=json",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            
            if result.returncode == 0 and not result.stdout.strip():
                return []
            
            try:
                diagnostics = json.loads(result.stdout) if result.stdout.strip() else []
                return diagnostics
            except json.JSONDecodeError:
                return []
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"Isolated ruff run failed for {file_path}: {e}")
            return []

    def _calculate_score_from_issues(self, issues: list[dict[str, Any]]) -> float:
        """
        Calculate a linting score from a list of ruff issues.
        
        P1 Improvement: Score calculation for isolated mode.
        
        Args:
            issues: List of ruff diagnostic dictionaries
            
        Returns:
            Linting score (0-10, higher is better)
        """
        if not issues:
            return 10.0
        
        # Count issues by severity
        error_count = 0
        warning_count = 0
        fatal_count = 0
        
        for d in issues:
            code_info = d.get("code", {})
            if isinstance(code_info, dict):
                code_name = code_info.get("name", "")
            else:
                code_name = str(code_info)
            
            if code_name.startswith("E"):
                error_count += 1
            elif code_name.startswith("W"):
                warning_count += 1
            elif code_name.startswith("F"):
                fatal_count += 1
        
        # Calculate score: Start at 10, deduct points
        # Errors (E): -2 points each
        # Fatal (F): -3 points each
        # Warnings (W): -0.5 points each
        score = 10.0
        score -= error_count * 2.0
        score -= fatal_count * 3.0
        score -= warning_count * 0.5
        
        return max(0.0, min(10.0, score))

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
        except TimeoutError:
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
                            # Filter out non-numeric values (e.g., dicts, strings)
                            values = [
                                s.get(key, 0.0)
                                for s in all_scores
                                if isinstance(s.get(key), (int, float))
                            ]
                            # Only calculate average if we have numeric values
                            if values:
                                avg_scores[key] = sum(values) / len(values)
                            else:
                                # Default to 0.0 if no numeric values found
                                avg_scores[key] = 0.0

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
                if code.startswith("F") or fatal_count > 0 or code.startswith("E") or error_count > 0:
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

        # 3. Extract type checking errors (mypy for Python, tsc for TypeScript)
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
        
        # Phase 7.1: Extract TypeScript-specific findings
        file_ext = file_path.suffix.lower()
        if file_ext in [".ts", ".tsx", ".js", ".jsx"] and self.typescript_scorer:
            # 3a. Extract ESLint issues for TypeScript/JavaScript
            try:
                eslint_result = self.typescript_scorer.get_eslint_issues(file_path)
                if eslint_result.get("available") and eslint_result.get("issues"):
                    for file_result in eslint_result.get("issues", [])[:3]:  # Limit files
                        messages = file_result.get("messages", [])
                        for msg in messages[:5]:  # Limit messages per file
                            finding_counter["linting"] += 1
                            severity = Severity.HIGH if msg.get("severity") == 2 else Severity.MEDIUM
                            rule_id = msg.get("ruleId", "unknown")
                            message = msg.get("message", "ESLint issue")
                            line = msg.get("line")
                            column = msg.get("column")
                            
                            findings.append(
                                ReviewFinding(
                                    id=f"TASK-{task_number}-ESLINT-{finding_counter['linting']:03d}",
                                    severity=severity,
                                    category="standards",
                                    file=file_str,
                                    line=line,
                                    finding=f"[{rule_id}] {message}" + (f" (column {column})" if column else ""),
                                    impact="Code does not meet ESLint linting standards",
                                    suggested_fix=f"Fix ESLint issue: {rule_id}",
                                )
                            )
            except Exception as e:
                logger.debug(f"Failed to extract ESLint issues: {e}")
            
            # 3b. Extract TypeScript type errors
            if file_ext in [".ts", ".tsx"]:
                try:
                    tsc_result = self.typescript_scorer.get_type_errors(file_path)
                    if tsc_result.get("available") and tsc_result.get("errors"):
                        for error_line in tsc_result.get("errors", [])[:5]:  # Limit to 5
                            finding_counter["type"] += 1
                            # Parse error format: "file.ts(10,5): error TS2345: ..."
                            import re
                            match = re.search(r"\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)", error_line)
                            if match:
                                line = int(match.group(1))
                                column = int(match.group(2))
                                error_code = match.group(3)
                                message = match.group(4)
                            else:
                                line = None
                                column = None
                                error_code = "TS0000"
                                message = error_line
                            
                            findings.append(
                                ReviewFinding(
                                    id=f"TASK-{task_number}-TSC-{finding_counter['type']:03d}",
                                    severity=Severity.HIGH,
                                    category="standards",
                                    file=file_str,
                                    line=line,
                                    finding=f"[{error_code}] {message}",
                                    impact="TypeScript type error may cause runtime issues",
                                    suggested_fix=f"Fix TypeScript error: {error_code}",
                                )
                            )
                except Exception as e:
                    logger.debug(f"Failed to extract TypeScript errors: {e}")
            
            # 3c. Extract TypeScript security issues (Phase 7.1)
            try:
                code = file_path.read_text(encoding="utf-8")
                security_result = self.typescript_scorer.get_security_issues(code, file_path)
                if security_result.get("available") and security_result.get("issues"):
                    for issue in security_result.get("issues", [])[:5]:  # Limit to 5
                        finding_counter["security"] += 1
                        severity_str = issue.get("severity", "MEDIUM")
                        severity = Severity.HIGH if severity_str == "HIGH" else (
                            Severity.LOW if severity_str == "LOW" else Severity.MEDIUM
                        )
                        
                        findings.append(
                            ReviewFinding(
                                id=f"TASK-{task_number}-TSSEC-{finding_counter['security']:03d}",
                                severity=severity,
                                category="security",
                                file=file_str,
                                line=issue.get("line"),
                                finding=f"[{issue.get('pattern')}] {issue.get('message')}" + (
                                    f" ({issue.get('cwe_id')})" if issue.get('cwe_id') else ""
                                ),
                                impact=issue.get("message", "Security vulnerability"),
                                suggested_fix=issue.get("recommendation", "Review security best practices"),
                            )
                        )
            except Exception as e:
                logger.debug(f"Failed to extract TypeScript security issues: {e}")

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

    async def _detect_api_client_pattern(self, code: str) -> bool:
        """
        Detect if code appears to be an HTTP/API client.

        Checks for common patterns that indicate API client code:
        - HTTP client libraries (requests, httpx)
        - Authentication headers (Authorization, Bearer, X-API-Key)
        - Token management (refresh_token, access_token, token_url)
        - API client structure (class Client, get/post methods, api_base_url)

        Args:
            code: Code content to analyze

        Returns:
            True if code appears to be an API client, False otherwise
        """
        if not code:
            return False
        
        code_lower = code.lower()
        
        # HTTP client library indicators
        http_client_indicators = [
            "requests.get",
            "requests.post",
            "requests.put",
            "requests.delete",
            "httpx.client",
            "httpx.asyncclient",
            "httpx.get",
            "httpx.post",
            "urllib.request",
            "urllib3",
            "aiohttp",
            "fetch(",  # JavaScript/TypeScript
            "axios",   # JavaScript/TypeScript
        ]

        # Authentication indicators (including OAuth2)
        auth_indicators = [
            "authorization:",
            "bearer",
            "x-api-key",
            "api_key",
            "api-key",
            "access_token",
            "refresh_token",
            "token_url",
            "client_id",
            "client_secret",
            "oauth2",
            "oauth",
            "grant_type",
            "authorization_code",
            "client_credentials",
            "jwt",
            "id_token",
        ]
        
        # API client structure indicators
        structure_indicators = [
            "api_base_url",
            "base_url",
            "api_url",
            "endpoint",
            "/api/",
            "rest",
            "graphql",
            "class.*client",
            "class.*api",
            "def get(",
            "def post(",
            "def put(",
            "def delete(",
            "def patch(",
            "def _headers",
            "def _get_access_token",
            "def _refresh",
            "@app.get",      # FastAPI
            "@app.post",     # FastAPI
            "@router",       # FastAPI router
            "apiview",       # Django REST
            "viewset",       # Django REST
        ]
        
        # Check for HTTP client usage
        has_http_client = any(indicator in code_lower for indicator in http_client_indicators)
        
        # Check for authentication patterns
        has_auth = any(indicator in code_lower for indicator in auth_indicators)
        
        # Check for API client structure
        has_structure = any(indicator in code_lower for indicator in structure_indicators)
        
        # Server-side REST framework indicators (FastAPI, Django REST, etc.)
        server_api_indicators = [
            "@app.get",
            "@app.post",
            "@router",
            "apiview",
            "viewset",
        ]
        has_server_api = any(indicator in code_lower for indicator in server_api_indicators)

        # Code is likely an API client/server if:
        # 1. Has HTTP client usage AND (auth OR structure), OR
        # 2. Has auth AND structure (e.g., OAuth2 client without explicit http calls yet), OR
        # 3. Has server-side REST framework patterns (FastAPI, Django REST)
        return (has_http_client and (has_auth or has_structure)) or (has_auth and has_structure) or has_server_api

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
                "error": f"Failed to retrieve documentation: {e!s}",
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
