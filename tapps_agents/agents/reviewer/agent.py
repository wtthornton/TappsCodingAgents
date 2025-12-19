"""
Reviewer Agent - Performs code review with scoring
"""

import logging
from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL
from ...experts.agent_integration import ExpertSupportMixin
from ..ops.dependency_analyzer import DependencyAnalyzer
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
        mal: MAL | None = None,
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

        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )
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

    async def activate(self, project_root: Path | None = None):
        """Activate the reviewer agent with expert support."""
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        await super().activate(project_root)
        # Initialize expert support via mixin
        await self._initialize_expert_support(project_root)
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

            model = kwargs.get("model", "qwen2.5-coder:7b")
            try:
                return await self.review_file(
                    Path(file_path),
                    model=model
                    or (
                        self.config.agents.reviewer.model
                        if self.config
                        else "qwen2.5-coder:7b"
                    ),
                    include_scoring=True,
                    include_llm_feedback=True,
                )
            except (FileNotFoundError, ValueError) as e:
                return {"error": str(e)}
            except RuntimeError as e:
                # Handle scorer errors and other runtime errors
                return {"error": str(e)}

        elif command == "score":
            file_path = kwargs.get("file")
            if not file_path:
                return {"error": "File path required. Usage: *score <file>"}

            try:
                return await self.review_file(
                    Path(file_path), include_scoring=True, include_llm_feedback=False
                )
            except (FileNotFoundError, ValueError) as e:
                return {"error": str(e)}

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

        else:
            return {
                "error": f"Unknown command: {command}. Use *help to see available commands."
            }

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
        model: str = "qwen2.5-coder:7b",
        include_scoring: bool = True,
        include_llm_feedback: bool = True,
    ) -> dict[str, Any]:
        """
        Review a code file.

        Args:
            file_path: Path to code file
            model: LLM model to use for feedback
            include_scoring: Include code scores
            include_llm_feedback: Include LLM-generated feedback

        Returns:
            Review results with scores and feedback
        """
        # Use centralized path validation from BaseAgent
        reviewer_config = self.config.agents.reviewer if self.config else None
        max_file_size = (
            reviewer_config.max_file_size if reviewer_config else (10 * 1024 * 1024)
        )
        # _validate_path handles existence, size, and path traversal checks
        self._validate_path(file_path, max_file_size=max_file_size)

        # Read code
        try:
            code = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file as UTF-8: {e}") from e

        result: dict[str, Any] = {"file": str(file_path), "review": {}}

        # Calculate scores
        if include_scoring:
            scores = self.scorer.score_file(file_path, code)

            # Enhance security score with dependency health (Phase 6.4.3)
            dependency_security = self._get_dependency_security_penalty()
            # Blend dependency security into security score (70% code security, 30% dependency security)
            original_security = scores.get("security_score", 5.0)
            scores["security_score"] = (original_security * 0.7) + (
                dependency_security * 0.3
            )
            scores["dependency_security_score"] = dependency_security

            result["scoring"] = scores

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
            feedback = await self._generate_feedback(
                code,
                scores if include_scoring else None,
                model,
                expert_guidance=expert_guidance,
            )
            result["feedback"] = feedback

        # Determine pass/fail using configured threshold
        if include_scoring:
            reviewer_config = self.config.agents.reviewer if self.config else None
            threshold = reviewer_config.quality_threshold if reviewer_config else 70.0
            result["passed"] = scores["overall_score"] >= threshold
            result["threshold"] = threshold

        return result

    async def _generate_feedback(
        self,
        code: str,
        scores: dict[str, Any] | None,
        model: str,
        expert_guidance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate LLM feedback on code"""

        # Build prompt
        prompt_parts = [
            "Review this code and provide feedback:",
            "",
            "Code:",
            "```python",
            code[:2000],  # Limit to first 2000 chars
            "```",
        ]

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
                    "Code Scores:",
                    f"- Complexity: {scores['complexity_score']:.1f}/10",
                    f"- Security: {scores['security_score']:.1f}/10",
                    f"- Maintainability: {scores['maintainability_score']:.1f}/10",
                    f"- Overall: {scores['overall_score']:.1f}/100",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "Provide:",
                "1. What the code does",
                "2. Potential issues or improvements",
                "3. Security concerns (if any)",
                "4. Style/best practices",
            ]
        )

        prompt = "\n".join(prompt_parts)

        try:
            response = await self.mal.generate(prompt, model=model)
            return {
                "summary": response[:500],  # First 500 chars
                "full_feedback": response,
            }
        except Exception as e:
            return {"error": str(e), "summary": "Could not generate LLM feedback"}

    async def lint_file(self, file_path: Path) -> dict[str, Any]:
        """
        Run Ruff linting on a file and return detailed issues.

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
        """
        # Use centralized path validation from BaseAgent
        self._validate_path(file_path)

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
            issues = self.scorer.get_ruff_issues(file_path)

            # Count issues by severity
            error_count = sum(
                1 for d in issues if d.get("code", {}).get("name", "").startswith("E")
            )
            warning_count = sum(
                1 for d in issues if d.get("code", {}).get("name", "").startswith("W")
            )
            fatal_count = sum(
                1 for d in issues if d.get("code", {}).get("name", "").startswith("F")
            )

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
        Run mypy type checking on a file and return detailed errors.

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
        """
        # Use centralized path validation from BaseAgent
        self._validate_path(file_path)

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
            model="reviewer-agent",
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

    async def close(self):
        """Clean up resources"""
        await self.mal.close()
