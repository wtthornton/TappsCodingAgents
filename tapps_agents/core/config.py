"""
Configuration management for TappsCodingAgents.

Provides Pydantic models for type-safe configuration and YAML loading.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class ScoringWeightsConfig(BaseModel):
    """Configuration for code scoring weights (must sum to 1.0). 7-category: Structure, DevEx added (MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.2)."""

    complexity: float = Field(
        default=0.18, ge=0.0, le=1.0, description="Weight for complexity score"
    )
    security: float = Field(
        default=0.27, ge=0.0, le=1.0, description="Weight for security score"
    )
    maintainability: float = Field(
        default=0.24, ge=0.0, le=1.0, description="Weight for maintainability score"
    )
    test_coverage: float = Field(
        default=0.13, ge=0.0, le=1.0, description="Weight for test coverage score"
    )
    performance: float = Field(
        default=0.08, ge=0.0, le=1.0, description="Weight for performance score"
    )
    structure: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Weight for structure score (project layout, key files)"
    )
    devex: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Weight for developer experience score (docs, config, tooling)"
    )

    @model_validator(mode="after")
    def validate_weights_sum(self):
        """Ensure weights sum to approximately 1.0"""
        total = (
            self.complexity
            + self.security
            + self.maintainability
            + self.test_coverage
            + self.performance
            + self.structure
            + self.devex
        )
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
        return self


class TestCoverageConfig(BaseModel):
    """Test coverage configuration for quality gates."""

    enabled: bool = Field(default=True, description="Enable test coverage checks")
    threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum coverage threshold (0.0-1.0)"
    )
    critical_services_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum coverage for critical services (0.0-1.0)",
    )
    warning_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Coverage threshold for warnings (0.0-1.0)",
    )


class QualityGatesConfig(BaseModel):
    """Quality gates configuration."""

    enabled: bool = Field(default=True, description="Enable quality gates")
    test_coverage: TestCoverageConfig = Field(
        default_factory=TestCoverageConfig, description="Test coverage configuration"
    )


class ScoringConfig(BaseModel):
    """Configuration for code scoring system"""

    weights: ScoringWeightsConfig = Field(default_factory=ScoringWeightsConfig)
    quality_threshold: float = Field(
        default=70.0, ge=0.0, le=100.0, description="Minimum overall score to pass"
    )
    quality_gates: QualityGatesConfig = Field(
        default_factory=QualityGatesConfig, description="Quality gates configuration"
    )


class ReviewerAgentContext7Config(BaseModel):
    """Context7 configuration for Reviewer Agent"""
    
    auto_detect: bool = Field(
        default=True, description="Enable automatic library detection"
    )
    topics: list[str] = Field(
        default_factory=lambda: ["best-practices", "routing", "api-design"],
        description="Default topics to fetch for detected libraries"
    )


class ReviewerAgentConfig(BaseModel):
    """Configuration specific to Reviewer Agent"""

    quality_threshold: float = Field(
        default=70.0, ge=0.0, le=100.0, description="Minimum score to pass review"
    )
    include_scoring: bool = Field(
        default=True, description="Include code scoring in review"
    )
    include_llm_feedback: bool = Field(
        default=True, description="Include LLM-generated feedback"
    )
    max_file_size: int = Field(
        default=1024 * 1024,
        ge=1024,
        description="Maximum file size in bytes (1MB default)",
    )
    min_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )
    operation_timeout: float = Field(
        default=300.0,
        ge=10.0,
        description="Timeout in seconds for reviewer operations (default: 5 minutes)",
    )
    tool_timeout: float = Field(
        default=30.0,
        ge=5.0,
        description="Timeout in seconds for individual quality tools (default: 30 seconds)",
    )
    enable_parallel_tools: bool = Field(
        default=True,
        description="Enable parallel execution of quality tools (Ruff, mypy, bandit)",
    )
    context7: ReviewerAgentContext7Config = Field(
        default_factory=ReviewerAgentContext7Config,
        description="Context7 integration settings for Reviewer Agent"
    )
    # NEW: Library detection config
    auto_library_detection: bool = Field(
        default=True,
        description="Automatically detect libraries from code and dependency files"
    )
    library_detection_depth: str = Field(
        default="both",
        description="What to detect: 'code' (imports only), 'dependencies' (requirements.txt/pyproject.toml), or 'both'"
    )
    # NEW: Context7 integration config
    auto_context7_lookups: bool = Field(
        default=True,
        description="Automatically lookup library documentation from Context7"
    )
    context7_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for Context7 lookups in seconds"
    )
    context7_cache_enabled: bool = Field(
        default=True,
        description="Cache Context7 responses to avoid duplicate lookups"
    )
    # NEW: Pattern detection config
    pattern_detection_enabled: bool = Field(
        default=True,
        description="Enable domain-specific pattern detection"
    )
    pattern_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to report detected patterns (0.0-1.0)"
    )


class PlannerAgentConfig(BaseModel):
    """Configuration specific to Planner Agent"""

    stories_dir: str | None = Field(
        default=None, description="Directory for storing stories (default: stories/)"
    )
    default_priority: str = Field(
        default="medium",
        description="Default priority for new stories (high/medium/low)",
    )
    min_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class ImplementerAgentContext7Config(BaseModel):
    """Context7 configuration for Implementer Agent"""
    
    auto_detect: bool = Field(
        default=True, description="Enable automatic library detection"
    )
    detect_from_prompt: bool = Field(
        default=True, description="Detect libraries from prompt/specification text"
    )


class ImplementerAgentConfig(BaseModel):
    """Configuration specific to Implementer Agent"""

    require_review: bool = Field(
        default=True, description="Require code review before writing files"
    )
    auto_approve_threshold: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Auto-approve if score >= threshold"
    )
    backup_files: bool = Field(
        default=True, description="Create backup before overwriting existing files"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        description="Maximum file size in bytes (10MB default)",
    )
    min_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )
    context7: ImplementerAgentContext7Config = Field(
        default_factory=ImplementerAgentContext7Config,
        description="Context7 integration settings for Implementer Agent"
    )


class TesterAgentConfig(BaseModel):
    """Configuration specific to Tester Agent"""

    test_framework: str = Field(
        default="pytest", description="Test framework to use (pytest/unittest)"
    )
    tests_dir: str | None = Field(
        default=None, description="Directory for tests (default: tests/)"
    )
    coverage_threshold: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Target test coverage percentage"
    )
    auto_write_tests: bool = Field(
        default=True, description="Automatically write generated tests to files"
    )
    min_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class DebuggerAgentContext7Config(BaseModel):
    """Context7 configuration for Debugger Agent"""
    
    auto_detect: bool = Field(
        default=True, description="Enable automatic library detection"
    )
    detect_from_errors: bool = Field(
        default=True, description="Detect libraries from error messages and stack traces"
    )


class DebuggerAgentConfig(BaseModel):
    """Configuration specific to Debugger Agent"""

    include_code_examples: bool = Field(
        default=True, description="Include code examples in fix suggestions"
    )
    max_context_lines: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum lines of code context to include in analysis",
    )
    min_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )
    context7: DebuggerAgentContext7Config = Field(
        default_factory=DebuggerAgentContext7Config,
        description="Context7 integration settings for Debugger Agent"
    )


class DocumenterAgentConfig(BaseModel):
    """Configuration specific to Documenter Agent"""

    docs_dir: str | None = Field(
        default=None, description="Directory for generated docs (default: docs/)"
    )
    include_examples: bool = Field(
        default=True, description="Include code examples in documentation"
    )
    docstring_format: str = Field(
        default="google", description="Docstring format (google/numpy/sphinx)"
    )
    min_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class Context7KnowledgeBaseConfig(BaseModel):
    """Configuration for Context7 knowledge base caching"""

    enabled: bool = Field(default=True, description="Enable KB caching")
    location: str = Field(
        default=".tapps-agents/kb/context7-cache", description="KB cache directory"
    )
    sharding: bool = Field(default=True, description="Enable library-based sharding")
    indexing: bool = Field(default=True, description="Enable indexing")
    max_cache_size: str = Field(default="100MB", description="Maximum cache size")
    hit_rate_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Target hit rate threshold"
    )
    fuzzy_match_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Fuzzy match confidence threshold"
    )


class Context7RefreshConfig(BaseModel):
    """Configuration for Context7 auto-refresh system"""

    enabled: bool = Field(default=True, description="Enable auto-refresh")
    default_max_age_days: int = Field(
        default=30, ge=1, description="Default max age for cache entries (days)"
    )
    check_on_access: bool = Field(default=True, description="Check staleness on access")
    auto_queue: bool = Field(
        default=True, description="Automatically queue stale entries"
    )
    auto_process_on_startup: bool = Field(
        default=False, description="Process queue on agent startup"
    )


class Context7Config(BaseModel):
    """Configuration for Context7 integration"""

    enabled: bool = Field(default=True, description="Enable Context7 integration")
    default_token_limit: int = Field(
        default=3000, ge=100, description="Default token limit for Context7 docs"
    )
    cache_duration: int = Field(
        default=3600, ge=0, description="Cache duration in seconds"
    )
    integration_level: str = Field(
        default="optional", description="Integration level (mandatory/optional)"
    )
    usage_requirement: str | None = Field(
        default=None, description="Usage requirement description"
    )
    bypass_forbidden: bool = Field(
        default=True, description="Allow bypassing if Context7 unavailable"
    )
    # Enhancement: Automatic Context7 detection and fetching
    auto_detect: bool = Field(
        default=True, description="Enable automatic library detection from code, prompts, and errors"
    )
    auto_fetch: bool = Field(
        default=True, description="Automatically fetch docs for detected libraries"
    )
    proactive_suggestions: bool = Field(
        default=True, description="Proactively suggest Context7 lookups when library patterns detected"
    )

    knowledge_base: Context7KnowledgeBaseConfig = Field(
        default_factory=Context7KnowledgeBaseConfig
    )
    refresh: Context7RefreshConfig = Field(default_factory=Context7RefreshConfig)


class QualityToolsConfig(BaseModel):
    """Configuration for quality analysis tools (Phase 6 - 2025 Standards)"""

    # Ruff configuration
    ruff_enabled: bool = Field(default=True, description="Enable Ruff linting")
    ruff_config_path: str | None = Field(
        default=None,
        description="Path to ruff.toml or pyproject.toml (auto-detected if None)",
    )

    # mypy configuration
    mypy_enabled: bool = Field(default=True, description="Enable mypy type checking")
    mypy_strict: bool = Field(default=False, description="Enable strict mode for mypy")
    mypy_config_path: str | None = Field(
        default=None,
        description="Path to mypy.ini or pyproject.toml (auto-detected if None)",
    )

    # jscpd configuration
    jscpd_enabled: bool = Field(
        default=True, description="Enable jscpd duplication detection"
    )
    duplication_threshold: float = Field(
        default=3.0,
        ge=0.0,
        le=100.0,
        description="Maximum duplication percentage threshold",
    )
    min_duplication_lines: int = Field(
        default=5, ge=3, description="Minimum lines for duplication detection"
    )

    # TypeScript/JavaScript configuration
    typescript_enabled: bool = Field(
        default=True, description="Enable TypeScript/JavaScript support"
    )
    eslint_config: str | None = Field(
        default=None, description="Path to ESLint config file"
    )
    tsconfig_path: str | None = Field(default=None, description="Path to tsconfig.json")

    # Dependency security auditing
    pip_audit_enabled: bool = Field(
        default=True, description="Enable pip-audit security scanning"
    )
    dependency_audit_threshold: str = Field(
        default="high",
        description="Minimum severity threshold (low/medium/high/critical)",
    )


class ToolingTargetsConfig(BaseModel):
    """Pin runtime/tool targets so agents and CI behave deterministically."""

    python: str = Field(
        default="3.13.3",
        description="Target Python version for this project (pin exact patch where possible)",
    )
    python_requires: str = Field(
        default=">=3.13",
        description="PEP 440 requires-python constraint enforced by packaging/CI",
    )
    os_targets: list[str] = Field(
        default_factory=lambda: ["windows", "linux"],
        description="Primary OS targets (used for setup/doctor guidance)",
    )
    node: str | None = Field(
        default=None,
        description="Optional Node.js version (only needed if TypeScript/jscpd tooling is enabled)",
    )


class ToolingPolicyConfig(BaseModel):
    """Policy for how missing/optional tools are handled."""

    external_tools_mode: str = Field(
        default="soft",
        description="How to handle missing external tools: soft=warn/skip, hard=fail",
    )
    mypy_staged: bool = Field(
        default=True, description="Stage mypy enforcement module-by-module"
    )
    mypy_stage_paths: list[str] = Field(
        default_factory=lambda: [
            "tapps_agents/core",
            "tapps_agents/workflow",
            "tapps_agents/context7",
        ],
        description="Paths enforced by mypy during the staged rollout",
    )


class ToolingConfig(BaseModel):
    """Canonical tooling/targets configuration (single source of truth)."""

    targets: ToolingTargetsConfig = Field(default_factory=ToolingTargetsConfig)
    policy: ToolingPolicyConfig = Field(default_factory=ToolingPolicyConfig)


class ArchitectAgentConfig(BaseModel):
    """Configuration specific to Architect Agent"""

    min_confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class DesignerAgentConfig(BaseModel):
    """Configuration specific to Designer Agent"""

    min_confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class OpsAgentConfig(BaseModel):
    """Configuration specific to Ops Agent"""

    min_confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class EnhancerAgentConfig(BaseModel):
    """Configuration specific to Enhancer Agent"""

    min_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class AnalystAgentConfig(BaseModel):
    """Configuration specific to Analyst Agent"""

    min_confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class OrchestratorAgentConfig(BaseModel):
    """Configuration specific to Orchestrator Agent"""

    min_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class EvaluatorAgentConfig(BaseModel):
    """Configuration specific to Evaluator Agent"""

    auto_run: bool = Field(
        default=False,
        description="Run evaluator automatically at end of workflows (build, full, etc.)"
    )
    output_dir: str = Field(
        default=".tapps-agents/evaluations",
        description="Directory for evaluation reports"
    )
    thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "quality_score": 70.0,
            "workflow_completion": 0.8,
        },
        description="Thresholds for evaluation metrics"
    )


class ExpertConfig(BaseModel):
    """Configuration for expert consultation system"""

    # Agent-specific confidence thresholds
    agent_confidence_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "reviewer": 0.8,
            "architect": 0.75,
            "implementer": 0.7,
            "designer": 0.65,
            "tester": 0.7,
            "ops": 0.75,
            "enhancer": 0.6,
            "analyst": 0.65,
            "planner": 0.6,
            "debugger": 0.7,
            "documenter": 0.5,
            "orchestrator": 0.6,
            "default": 0.7,
        },
        description="Agent-specific confidence thresholds (0.0-1.0)",
    )

    # Confidence calculation weights
    weight_max_confidence: float = Field(
        default=0.35, ge=0.0, le=1.0, description="Weight for maximum expert confidence"
    )
    weight_agreement: float = Field(
        default=0.25, ge=0.0, le=1.0, description="Weight for expert agreement level"
    )
    weight_rag_quality: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Weight for RAG knowledge base quality"
    )
    weight_domain_relevance: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Weight for domain relevance"
    )
    weight_project_context: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Weight for project context relevance"
    )

    # Agreement and similarity thresholds
    high_agreement_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="High agreement threshold for expert consensus (0.0-1.0)",
    )
    similarity_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for expert response comparison (0.0-1.0)",
    )

    # RAG (Retrieval-Augmented Generation) parameters
    rag_max_length: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Maximum length for RAG context retrieval (characters)",
    )
    rag_max_results: int = Field(
        default=8, ge=1, le=20, description="Maximum number of RAG results to retrieve"
    )
    rag_default_quality: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Default RAG quality score when not provided (0.0-1.0)",
    )

    # Profile confidence threshold
    profile_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for including profile values (0.0-1.0)",
    )

    # Supporting expert weight
    supporting_expert_weight: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Approximate weight for supporting experts in agreement calculation",
    )

    @model_validator(mode="after")
    def validate_weights_sum(self):
        """Ensure confidence weights sum to approximately 1.0"""
        total = (
            self.weight_max_confidence
            + self.weight_agreement
            + self.weight_rag_quality
            + self.weight_domain_relevance
            + self.weight_project_context
        )
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Expert confidence weights must sum to 1.0, got {total}")
        return self


class AgentsConfig(BaseModel):
    """Configuration for all agents"""

    reviewer: ReviewerAgentConfig = Field(default_factory=ReviewerAgentConfig)
    planner: PlannerAgentConfig = Field(default_factory=PlannerAgentConfig)
    implementer: ImplementerAgentConfig = Field(default_factory=ImplementerAgentConfig)
    tester: TesterAgentConfig = Field(default_factory=TesterAgentConfig)
    debugger: DebuggerAgentConfig = Field(default_factory=DebuggerAgentConfig)
    documenter: DocumenterAgentConfig = Field(default_factory=DocumenterAgentConfig)
    architect: ArchitectAgentConfig = Field(default_factory=ArchitectAgentConfig)
    designer: DesignerAgentConfig = Field(default_factory=DesignerAgentConfig)
    ops: OpsAgentConfig = Field(default_factory=OpsAgentConfig)
    enhancer: EnhancerAgentConfig = Field(default_factory=EnhancerAgentConfig)
    analyst: AnalystAgentConfig = Field(default_factory=AnalystAgentConfig)
    orchestrator: OrchestratorAgentConfig = Field(
        default_factory=OrchestratorAgentConfig
    )
    evaluator: EvaluatorAgentConfig = Field(default_factory=EvaluatorAgentConfig)


class CheckpointFrequencyConfig(BaseModel):
    """Configuration for checkpoint frequency"""

    mode: str = Field(
        default="every_step",
        description="Checkpoint frequency mode: every_step, every_n_steps, on_gates, time_based, manual",
    )
    interval: int = Field(
        default=1,
        ge=1,
        description="Interval for every_n_steps (step count) or time_based (seconds)",
    )
    enabled: bool = Field(
        default=True,
        description="Enable checkpointing",
    )


class StateCleanupPolicyConfig(BaseModel):
    """Configuration for state cleanup policies"""

    enabled: bool = Field(
        default=True,
        description="Enable automatic state cleanup",
    )
    retention_days: int | None = Field(
        default=None,
        ge=1,
        description="Delete states older than N days (None = no retention limit)",
    )
    max_size_mb: int | None = Field(
        default=None,
        ge=1,
        description="Maximum total state size in MB (None = no size limit)",
    )
    cleanup_schedule: str = Field(
        default="daily",
        description="Cleanup schedule: daily, weekly, monthly, on_startup, manual",
    )
    keep_latest: int = Field(
        default=10,
        ge=1,
        description="Always keep the N most recent states",
    )


class StatePersistenceConfig(BaseModel):
    """Configuration for state persistence and checkpointing"""

    enabled: bool = Field(
        default=True,
        description="Enable state persistence",
    )
    storage_location: str = Field(
        default=".tapps-agents/workflow-state",
        description="Directory for storing workflow state",
    )
    format: str = Field(
        default="json",
        description="State storage format: json, json_gzip",
    )
    compression: bool = Field(
        default=False,
        description="Enable compression for state files",
    )
    checkpoint: CheckpointFrequencyConfig = Field(
        default_factory=CheckpointFrequencyConfig,
        description="Checkpoint frequency configuration",
    )
    cleanup: StateCleanupPolicyConfig = Field(
        default_factory=StateCleanupPolicyConfig,
        description="State cleanup policy configuration",
    )


class BranchCleanupConfig(BaseModel):
    """Configuration for Git branch cleanup after workflow execution"""

    enabled: bool = Field(
        default=True,
        description="Enable automatic branch cleanup",
    )
    delete_branches_on_cleanup: bool = Field(
        default=True,
        description="Delete associated Git branches when worktrees are removed",
    )
    retention_days: int = Field(
        default=7,
        ge=0,
        description="Number of days to retain branches before cleanup (0 = immediate cleanup)",
    )
    auto_cleanup_on_completion: bool = Field(
        default=True,
        description="Automatically cleanup branches when workflow step completes",
    )
    patterns: dict[str, str] = Field(
        default_factory=lambda: {
            "workflow": "workflow/*",
            "agent": "agent/*",
        },
        description="Branch patterns to match for cleanup (wildcards supported)",
    )


class WorkflowDocsCleanupConfig(BaseModel):
    """Configuration for workflow documentation cleanup"""

    enabled: bool = Field(
        default=True,
        description="Enable workflow documentation cleanup",
    )
    keep_latest: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Keep N most recent workflows visible",
    )
    retention_days: int = Field(
        default=30,
        ge=1,
        description="Archive workflows older than N days",
    )
    archive_enabled: bool = Field(
        default=True,
        description="Enable archival of old workflows",
    )
    archive_dir: Path = Field(
        default=Path(".tapps-agents/archives/workflows/"),
        description="Directory for archived workflows (relative to project root)",
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Workflow IDs or patterns to never archive",
    )


class SessionsCleanupConfig(BaseModel):
    """Configuration for .tapps-agents/sessions cleanup (enhancer + SessionManager)."""

    keep_latest: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Keep N most recent enhancer session files",
    )
    max_age_days: int = Field(
        default=30,
        ge=1,
        description="Remove enhancer sessions older than N days; also used for SessionManager cleanup (hours = max_age_days * 24)",
    )
    auto_cleanup_on_enhance: bool = Field(
        default=False,
        description="When True, run sessions cleanup after each enhancer save so the folder does not grow unbounded",
    )


class CleanupConfig(BaseModel):
    """Configuration for cleanup operations"""

    workflow_docs: WorkflowDocsCleanupConfig = Field(
        default_factory=WorkflowDocsCleanupConfig,
        description="Workflow documentation cleanup configuration",
    )
    sessions: SessionsCleanupConfig = Field(
        default_factory=SessionsCleanupConfig,
        description="Sessions cleanup (enhancer + long-running agent sessions)",
    )


class WorkflowArtifactConfig(BaseModel):
    """Configuration for workflow artifact paths and naming."""
    
    base_dir: str = Field(
        default="docs/workflows",
        description="Base directory for workflow artifacts (relative to project root)",
    )
    simple_mode_subdir: str = Field(
        default="simple-mode",
        description="Subdirectory for Simple Mode workflow artifacts",
    )
    auto_detect_existing: bool = Field(
        default=True,
        description="Auto-detect existing artifacts and adjust paths to avoid conflicts",
    )
    naming_pattern: str = Field(
        default="{workflow_id}/{step_name}.md",
        description="Pattern for artifact file naming. Supports: {workflow_id}, {step_name}, {timestamp}, {agent}",
    )
    print_paths_on_completion: bool = Field(
        default=True,
        description="Print artifact file paths after each step completes",
    )
    
    def get_artifact_dir(self, project_root: str | None = None) -> str:
        """Get the full artifact directory path."""
        from pathlib import Path
        base = Path(project_root) if project_root else Path.cwd()
        return str(base / self.base_dir / self.simple_mode_subdir)


class WorkflowFailureConfig(BaseModel):
    """On-step-failure behavior: retry, skip, escalate, or fail (plan 3.1)."""

    on_step_fail: str = Field(
        default="fail",
        description="Behavior on step failure: 'fail' | 'retry' | 'skip' | 'escalate'.",
    )
    retry_count: int = Field(
        default=1,
        ge=0,
        le=10,
        description="Max retries when on_step_fail=='retry'.",
    )
    escalate_to_pause: bool = Field(
        default=True,
        description="When on_step_fail is 'escalate' or 'fail', set status to 'paused' (True) or 'failed' (False).",
    )


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution"""

    failure: WorkflowFailureConfig = Field(
        default_factory=WorkflowFailureConfig,
        description="On-step-failure behavior: retry, skip, escalate (plan 3.1).",
    )
    polling_interval: float = Field(
        default=5.0,
        ge=1.0,
        description="Seconds between status checks when polling for completion",
    )
    timeout_seconds: float = Field(
        default=3600.0,
        ge=1.0,
        description="Maximum time to wait for step completion (seconds)",
    )
    state_persistence: StatePersistenceConfig = Field(
        default_factory=StatePersistenceConfig,
        description="State persistence and checkpointing configuration",
    )
    branch_cleanup: BranchCleanupConfig = Field(
        default_factory=BranchCleanupConfig,
        description="Git branch cleanup configuration for workflow worktrees",
    )
    artifacts: WorkflowArtifactConfig = Field(
        default_factory=WorkflowArtifactConfig,
        description="Artifact paths and naming configuration",
    )
    graceful_partial_completion: bool = Field(
        default=True,
        description="Save partial results on failure instead of losing all progress",
    )
    pre_flight_validation: bool = Field(
        default=True,
        description="Run pre-flight validation before workflow execution",
    )


class ContextBudgetConfig(BaseModel):
    """Context budget when assembling Context7 and expert chunks (plan 3.2)."""

    max_tokens_per_step: int = Field(
        default=0,
        ge=0,
        description="Max tokens per step (0=no hard limit).",
    )
    max_chunks_per_step: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Max chunks when injecting Context7 or expert docs.",
    )
    priority: list[str] = Field(
        default_factory=lambda: ["current_task", "open_files", "recent_changes", "context7", "experts"],
        description="Priority order when assembling context (for future use).",
    )


class BugFixAgentConfig(BaseModel):
    """Configuration for Bug Fix Agent."""

    max_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum iterations for fix loopback (1-10)",
    )
    auto_commit: bool = Field(
        default=True,
        description="Automatically commit changes to main branch when quality passes",
    )
    quality_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "overall_min": 7.0,
            "security_min": 6.5,
            "maintainability_min": 7.0,
        },
        description="Quality thresholds for bug fixes (lower than full SDLC)",
    )
    escalation_threshold: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Escalate to human after N failed iterations (1-5)",
    )
    escalation_enabled: bool = Field(
        default=True,
        description="Enable human escalation after failed iterations",
    )
    pre_commit_security_scan: bool = Field(
        default=True,
        description="Run security scan before committing changes",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection for observability",
    )
    commit_strategy: str = Field(
        default="direct_main",
        description="Commit strategy: 'direct_main' (commit directly) or 'pull_request' (create PR)",
    )
    auto_merge_pr: bool = Field(
        default=False,
        description="Auto-merge PR if quality gates pass (requires PR workflow)",
    )
    require_pr_review: bool = Field(
        default=False,
        description="Require human review before merging PR",
    )


class ContinuousBugFixConfig(BaseModel):
    """Configuration for Continuous Bug Fix feature."""

    max_iterations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum loop iterations (1-100)",
    )
    commit_strategy: str = Field(
        default="one-per-bug",
        description="Commit strategy: 'one-per-bug' (default) or 'batch'",
    )
    auto_commit: bool = Field(
        default=True,
        description="Automatically commit fixes after bug-fix-agent succeeds",
    )
    test_path: str = Field(
        default="tests/",
        description="Default test directory or file to run",
    )
    skip_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns for bugs to skip (not yet implemented)",
    )


class BeadsConfig(BaseModel):
    """Configuration for Beads (bd) task-tracking integration."""

    enabled: bool = Field(
        default=True,
        description="Enable Beads (bd) integration. When false, all beads features are no-ops.",
    )
    sync_epic: bool = Field(
        default=True,
        description="When beads.enabled is true, sync epic to bd (create issues + deps) before *epic run.",
    )
    hooks_simple_mode: bool = Field(
        default=True,
        description="When beads.enabled is true, create/close bd issues at start/end of *build and *fix.",
    )
    hooks_workflow: bool = Field(
        default=True,
        description="When beads.enabled is true, create/close a bd issue at start/end of CLI workflow runs.",
    )
    hooks_review: bool = Field(
        default=False,
        description="When beads.enabled is true, create/close for *review.",
    )
    hooks_test: bool = Field(
        default=False,
        description="When beads.enabled is true, create/close for *test.",
    )
    hooks_refactor: bool = Field(
        default=False,
        description="When beads.enabled is true, create/close for *refactor.",
    )


class SimpleModeConfig(BaseModel):
    """Configuration for Simple Mode."""

    enabled: bool = Field(
        default=True, description="Enable Simple Mode (intent-based agent orchestration)"
    )
    auto_detect: bool = Field(
        default=True,
        description="Auto-enable Simple Mode for first-time users",
    )
    show_advanced: bool = Field(
        default=False, description="Show advanced agent-specific options"
    )
    natural_language: bool = Field(
        default=True, description="Enable natural language command parsing"
    )
    fast_mode_default: bool = Field(
        default=False,
        description="Default to fast mode for Simple Mode workflows (skip documentation steps)",
    )
    state_persistence_enabled: bool = Field(
        default=True,
        description="Enable workflow state persistence for resume capability",
    )
    checkpoint_retention_days: int = Field(
        default=30,
        ge=1,
        description="Days to retain workflow checkpoints",
    )
    documentation_organized: bool = Field(
        default=True,
        description="Organize documentation by workflow ID",
    )
    create_latest_symlink: bool = Field(
        default=False,
        description="Create 'latest' symlink to most recent workflow",
    )


class AutoEnhancementConfig(BaseModel):
    """Configuration for automatic prompt enhancement"""

    enabled: bool = Field(
        default=True, description="Enable auto-enhancement globally"
    )
    mode: str = Field(
        default="cursor-skills",
        description="Enhancement mode: cursor-skills, structured, or smart",
    )
    min_prompt_length: int = Field(
        default=20, description="Minimum prompt length to trigger enhancement"
    )
    quality_threshold: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Quality score below which to enhance",
    )

    commands: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {
            "implementer": {"enabled": True, "synthesis_mode": "full"},
            "planner": {"enabled": True, "synthesis_mode": "quick"},
            "analyst": {"enabled": True, "synthesis_mode": "quick"},
            "architect": {"enabled": False},  # Off by default to avoid over-use
            "designer": {"enabled": False},  # Off by default to avoid over-use
        },
        description="Per-command enhancement settings",
    )


class EvaluationConfig(BaseModel):
    """Configuration for Evaluation & Quality Assurance Engine (Tier 1)"""

    enabled: bool = Field(
        default=True, description="Enable comprehensive evaluation engine"
    )
    include_behavioral_validation: bool = Field(
        default=True, description="Include behavioral correctness validation"
    )
    include_spec_compliance: bool = Field(
        default=True, description="Include specification compliance checking"
    )
    include_architectural_checks: bool = Field(
        default=True, description="Include architectural pattern adherence checking"
    )
    issue_severity_thresholds: dict[str, int] = Field(
        default_factory=lambda: {
            "critical": 0,  # Hard fail
            "high": 5,  # Soft fail/loopback
            "medium": 10,
            "low": 20,
        },
        description="Maximum allowed issues by severity for gate passing",
    )
    enable_remediation_loop: bool = Field(
        default=True, description="Enable automatic remediation loops"
    )
    max_remediation_retries: int = Field(
        default=3, ge=1, le=10, description="Maximum remediation retry attempts"
    )


class PromptLearningConfig(BaseModel):
    """Configuration for Continual System Prompt Learning (Tier 1)"""

    enabled: bool = Field(
        default=True, description="Enable prompt learning system"
    )
    feedback_collection_enabled: bool = Field(
        default=True, description="Enable feedback collection from Cursor IDE"
    )
    ab_testing_enabled: bool = Field(
        default=True, description="Enable A/B testing for prompt variations"
    )
    auto_optimize_enabled: bool = Field(
        default=True, description="Enable automatic prompt optimization"
    )
    min_samples_for_optimization: int = Field(
        default=10, ge=5, description="Minimum feedback samples before optimization"
    )
    optimization_interval_hours: int = Field(
        default=24, ge=1, description="Hours between optimization runs"
    )
    prompt_version_retention_days: int = Field(
        default=90, ge=7, description="Days to retain prompt version history"
    )
    auto_update_skills: bool = Field(
        default=False, description="Automatically update Skills with learned prompts"
    )
    require_approval_for_updates: bool = Field(
        default=True, description="Require approval before updating prompts"
    )


class KnowledgeEngineConfig(BaseModel):
    """Configuration for Knowledge Ecosystem Enhancement (Tier 1)"""

    enabled: bool = Field(
        default=True, description="Enable always-on knowledge orchestration engine"
    )
    auto_detect_domains: bool = Field(
        default=True, description="Automatically detect project domains"
    )
    auto_create_experts: bool = Field(
        default=True, description="Automatically create project experts"
    )
    knowledge_ingestion_enabled: bool = Field(
        default=True, description="Enable automatic knowledge ingestion"
    )
    proactive_consultation: bool = Field(
        default=True, description="Proactively consult experts before needed"
    )
    metrics_tracking_enabled: bool = Field(
        default=True, description="Enable metrics tracking for knowledge quality"
    )
    kb_maintenance_schedule: str = Field(
        default="weekly", description="KB maintenance schedule: daily, weekly, monthly"
    )
    governance_enabled: bool = Field(
        default=True, description="Enable governance and safety layer"
    )
    require_approval_for_writes: bool = Field(
        default=False, description="Require approval before writing to knowledge base"
    )


class ContextIntelligenceConfig(BaseModel):
    """Configuration for Context Intelligence Engine (Tier 1)"""

    enabled: bool = Field(
        default=True, description="Enable context intelligence engine"
    )
    dynamic_gathering_enabled: bool = Field(
        default=True, description="Enable dynamic context gathering"
    )
    repository_exploration_enabled: bool = Field(
        default=True, description="Enable autonomous repository exploration"
    )
    pattern_recognition_enabled: bool = Field(
        default=True, description="Enable pattern recognition and cataloging"
    )
    similarity_detection_enabled: bool = Field(
        default=True, description="Enable similarity detection for code reuse"
    )
    historical_analysis_enabled: bool = Field(
        default=True, description="Enable historical context analysis"
    )
    relevance_ranking_enabled: bool = Field(
        default=True, description="Enable relevance-based context ranking"
    )
    token_budget_management_enabled: bool = Field(
        default=True, description="Enable token budget management"
    )
    default_token_budget: int = Field(
        default=4000, ge=1000, le=16000, description="Default token budget for context"
    )
    progressive_loading_enabled: bool = Field(
        default=True, description="Enable progressive context loading"
    )


class GuardrailConfig(BaseModel):
    """Security guardrails for subprocess and file writes (plan 2.2)."""

    sandbox_subprocess: bool = Field(
        default=True,
        description="When True, never use shell for subprocess; use cwd=project_root.",
    )
    allowed_paths_write: list[str] = Field(
        default_factory=list,
        description="When non-empty, writes must be under project_root and under one of these prefixes (e.g. src, tests, docs, .tapps-agents). When empty, only under project_root.",
    )


class HumanOversightConfig(BaseModel):
    """Human-in-the-loop oversight for *build and *full (plan 2.3)."""

    checkpoints_before_steps: list[str] = Field(
        default_factory=list,
        description="Step/agent names before which to prompt: e.g. implementer, designer. If --auto, skipped.",
    )
    require_diff_review_implementer: bool = Field(
        default=False,
        description="Reserved: when implementer supports preview/diff, require review before apply. Not implemented.",
    )
    branch_for_agent_changes: bool = Field(
        default=True,
        description="For *build and *full: create branch tapps-agents/build-{workflow_id}; merge to main only after human review.",
    )


class ProjectConfig(BaseModel):
    """Root configuration model for TappsCodingAgents project"""

    # Project metadata
    project_name: str | None = Field(default=None, description="Project name")
    version: str | None = Field(default=None, description="Project version")

    # CLI / runtime
    offline_mode: bool = Field(
        default=False,
        description="Use offline mode (no network) when possible for CLI and agents",
    )

    # Core configuration
    tooling: ToolingConfig = Field(
        default_factory=ToolingConfig,
        description="Canonical runtime/tool targets and policy (used by doctor/CI/agents)",
    )
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    expert: ExpertConfig = Field(
        default_factory=ExpertConfig,
        description="Expert consultation system configuration",
    )
    context7: Context7Config | None = Field(
        default_factory=Context7Config, description="Context7 integration configuration"
    )
    context_budget: ContextBudgetConfig = Field(
        default_factory=ContextBudgetConfig,
        description="Context budget: max_chunks for Context7/expert injection; surface cached_at (plan 3.2).",
    )
    quality_tools: QualityToolsConfig | None = Field(
        default_factory=QualityToolsConfig,
        description="Quality analysis tools configuration (Phase 6)",
    )
    workflow: WorkflowConfig = Field(
        default_factory=WorkflowConfig,
        description="Workflow execution configuration",
    )
    guardrails: GuardrailConfig = Field(
        default_factory=GuardrailConfig,
        description="Security guardrails: subprocess sandbox, path allowlist for writes (plan 2.2).",
    )
    human_oversight: HumanOversightConfig = Field(
        default_factory=HumanOversightConfig,
        description="Human oversight: step checkpoints, branch-for-agent-changes (plan 2.3). require_diff_review_implementer reserved.",
    )
    simple_mode: SimpleModeConfig = Field(
        default_factory=SimpleModeConfig,
        description="Simple Mode configuration (intent-based orchestration)",
    )
    beads: BeadsConfig = Field(
        default_factory=BeadsConfig,
        description="Beads (bd) task-tracking integration. See docs/BEADS_INTEGRATION.md.",
    )
    bug_fix_agent: BugFixAgentConfig = Field(
        default_factory=BugFixAgentConfig,
        description="Bug Fix Agent configuration (automated bug fixing with auto-commit)",
    )
    continuous_bug_fix: ContinuousBugFixConfig = Field(
        default_factory=ContinuousBugFixConfig,
        description="Continuous Bug Fix configuration (automated bug finding and fixing loop)",
    )
    auto_enhancement: AutoEnhancementConfig = Field(
        default_factory=AutoEnhancementConfig,
        description="Automatic prompt enhancement configuration",
    )

    # Tier 1 Enhancement Configurations
    evaluation: EvaluationConfig = Field(
        default_factory=EvaluationConfig,
        description="Evaluation & Quality Assurance Engine configuration (Tier 1)",
    )
    prompt_learning: PromptLearningConfig = Field(
        default_factory=PromptLearningConfig,
        description="Continual System Prompt Learning configuration (Tier 1)",
    )
    knowledge_engine: KnowledgeEngineConfig = Field(
        default_factory=KnowledgeEngineConfig,
        description="Knowledge Ecosystem Enhancement configuration (Tier 1)",
    )
    context_intelligence: ContextIntelligenceConfig = Field(
        default_factory=ContextIntelligenceConfig,
        description="Context Intelligence Engine configuration (Tier 1)",
    )
    cleanup: CleanupConfig = Field(
        default_factory=CleanupConfig,
        description="Cleanup operations configuration",
    )

    model_config = {
        "extra": "ignore",  # Ignore unknown fields
        "validate_assignment": True,
    }


def load_config(config_path: Path | None = None) -> ProjectConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml file. If None, looks for `.tapps-agents/config.yaml`
                    in current directory or parent directories.

    Returns:
        ProjectConfig instance with loaded values

    Raises:
        FileNotFoundError: If config file doesn't exist and no defaults available
        ValueError: If config file is invalid
    """
    if config_path is None:
        # Look for .tapps-agents/config.yaml in current and parent directories
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            candidate = parent / ".tapps-agents" / "config.yaml"
            if candidate.exists():
                config_path = candidate
                break

        if config_path is None:
            # Return defaults if no config file found
            return ProjectConfig()

    if not config_path.exists():
        # Return defaults if file doesn't exist
        return ProjectConfig()

    try:
        # Use utf-8-sig to automatically handle UTF-8 BOM (common on Windows)
        # This prevents YAML parsing failures when files have BOM prefix (\xef\xbb\xbf)
        with open(config_path, encoding="utf-8-sig") as f:
            data = yaml.safe_load(f)

        if data is None:
            # Empty file, return defaults
            return ProjectConfig()

        # Validate and load config
        return ProjectConfig(**data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file {config_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading config from {config_path}: {e}") from e


def save_config(config_path: Path, config: ProjectConfig) -> None:
    """
    Save configuration to a YAML file.

    Args:
        config_path: Path to the config file
        config: ProjectConfig instance to save

    Raises:
        OSError: If the file cannot be written
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config to preserve other settings
    existing_data: dict[str, Any] = {}
    if config_path.exists():
        try:
            # Use utf-8-sig to handle UTF-8 BOM (common on Windows)
            with open(config_path, encoding="utf-8-sig") as f:
                existing_data = yaml.safe_load(f) or {}
        except Exception:
            # If we can't read existing config, start fresh
            existing_data = {}

    # Merge with new config (convert to dict, preserving existing values)
    new_data = config.model_dump(exclude_none=True, mode="json")
    
    def deep_merge(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge new dict into existing dict."""
        result = existing.copy()
        for key, value in new.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Overwrite with new value
                result[key] = value
        return result
    
    # Deep merge: preserve existing nested values
    existing_data = deep_merge(existing_data, new_data)

    # Save
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def get_default_config() -> dict[str, Any]:
    """
    Get default configuration as a dictionary (for template generation).

    Returns:
        Dictionary representation of default config with Path objects as strings
    """
    config = ProjectConfig()
    # Use model_dump with mode="json" to serialize Path objects as strings
    # This is required for YAML serialization (yaml.safe_dump can't handle Path objects)
    return config.model_dump(exclude_none=True, mode="json")


def get_expert_config(config: ProjectConfig | None = None) -> ExpertConfig:
    """
    Get expert configuration, loading from file if needed.

    Args:
        config: Optional ProjectConfig instance. If None, loads from file.

    Returns:
        ExpertConfig instance
    """
    if config is None:
        config = load_config()
    return config.expert
