"""
Configuration management for TappsCodingAgents.

Provides Pydantic models for type-safe configuration and YAML loading.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class ScoringWeightsConfig(BaseModel):
    """Configuration for code scoring weights (must sum to 1.0)"""

    complexity: float = Field(
        default=0.20, ge=0.0, le=1.0, description="Weight for complexity score"
    )
    security: float = Field(
        default=0.30, ge=0.0, le=1.0, description="Weight for security score"
    )
    maintainability: float = Field(
        default=0.25, ge=0.0, le=1.0, description="Weight for maintainability score"
    )
    test_coverage: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Weight for test coverage score"
    )
    performance: float = Field(
        default=0.10, ge=0.0, le=1.0, description="Weight for performance score"
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
        )
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
        return self


class ScoringConfig(BaseModel):
    """Configuration for code scoring system"""

    weights: ScoringWeightsConfig = Field(default_factory=ScoringWeightsConfig)
    quality_threshold: float = Field(
        default=70.0, ge=0.0, le=100.0, description="Minimum overall score to pass"
    )


class CloudProviderConfig(BaseModel):
    """Configuration for cloud LLM providers"""

    api_key: str | None = Field(default=None, description="API key for cloud provider")
    base_url: str | None = Field(default=None, description="Custom base URL (optional)")
    timeout: float = Field(
        default=60.0, ge=1.0, description="Request timeout in seconds"
    )


class MALConfig(BaseModel):
    """Configuration for Model Abstraction Layer"""

    ollama_url: str = Field(
        default="http://localhost:11434", description="Ollama API URL"
    )
    default_model: str = Field(
        default="qwen2.5-coder:7b", description="Default model name for LLM calls"
    )
    default_provider: str = Field(
        default="ollama", description="Default provider (ollama/anthropic/openai)"
    )
    timeout: float = Field(
        default=60.0,
        ge=1.0,
        description="Request timeout in seconds (legacy, use granular timeouts)",
    )

    # Granular timeout configuration (2025 best practice)
    connect_timeout: float = Field(
        default=10.0, ge=1.0, description="Connection timeout in seconds"
    )
    read_timeout: float = Field(
        default=600.0,
        ge=1.0,
        description="Read timeout in seconds (10 min for large files)",
    )
    write_timeout: float = Field(
        default=30.0, ge=1.0, description="Write timeout in seconds"
    )
    pool_timeout: float = Field(
        default=10.0, ge=1.0, description="Pool timeout in seconds"
    )

    # Streaming configuration (2025 best practice)
    use_streaming: bool = Field(
        default=True, description="Use streaming for large prompts"
    )
    streaming_threshold: int = Field(
        default=5000, ge=0, description="Prompt length (chars) to enable streaming"
    )

    # Cloud provider configurations
    anthropic: CloudProviderConfig | None = Field(
        default=None, description="Anthropic Claude configuration"
    )
    openai: CloudProviderConfig | None = Field(
        default=None, description="OpenAI configuration"
    )

    # Fallback settings
    enable_fallback: bool = Field(
        default=True, description="Enable automatic fallback to cloud if local fails"
    )
    fallback_providers: list[str] = Field(
        default_factory=lambda: ["anthropic", "openai"],
        description="Fallback provider order",
    )


class ReviewerAgentConfig(BaseModel):
    """Configuration specific to Reviewer Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for reviews"
    )
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


class PlannerAgentConfig(BaseModel):
    """Configuration specific to Planner Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for planning"
    )
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


class ImplementerAgentConfig(BaseModel):
    """Configuration specific to Implementer Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for code generation"
    )
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


class TesterAgentConfig(BaseModel):
    """Configuration specific to Tester Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for test generation"
    )
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


class DebuggerAgentConfig(BaseModel):
    """Configuration specific to Debugger Agent"""

    model: str = Field(
        default="deepseek-coder:6.7b", description="LLM model to use for error analysis"
    )
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


class DocumenterAgentConfig(BaseModel):
    """Configuration specific to Documenter Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b",
        description="LLM model to use for documentation generation",
    )
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

    model: str = Field(
        default="qwen2.5-coder:7b",
        description="LLM model to use for architecture design",
    )
    min_confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class DesignerAgentConfig(BaseModel):
    """Configuration specific to Designer Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for design"
    )
    min_confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class OpsAgentConfig(BaseModel):
    """Configuration specific to Ops Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for operations"
    )
    min_confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class EnhancerAgentConfig(BaseModel):
    """Configuration specific to Enhancer Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for enhancements"
    )
    min_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class AnalystAgentConfig(BaseModel):
    """Configuration specific to Analyst Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for analysis"
    )
    min_confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
    )


class OrchestratorAgentConfig(BaseModel):
    """Configuration specific to Orchestrator Agent"""

    model: str = Field(
        default="qwen2.5-coder:7b", description="LLM model to use for orchestration"
    )
    min_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum expert confidence threshold (0.0-1.0)",
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
        default=5, ge=1, le=20, description="Maximum number of RAG results to retrieve"
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


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution"""

    auto_execution_enabled: bool = Field(
        default=True,
        description="Enable Background Agent auto-execution for workflow steps. Defaults to True for better user experience.",
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


class ProjectConfig(BaseModel):
    """Root configuration model for TappsCodingAgents project"""

    # Project metadata
    project_name: str | None = Field(default=None, description="Project name")
    version: str | None = Field(default=None, description="Project version")

    # Core configuration
    tooling: ToolingConfig = Field(
        default_factory=ToolingConfig,
        description="Canonical runtime/tool targets and policy (used by doctor/CI/agents)",
    )
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    mal: MALConfig = Field(default_factory=MALConfig)
    expert: ExpertConfig = Field(
        default_factory=ExpertConfig,
        description="Expert consultation system configuration",
    )
    context7: Context7Config | None = Field(
        default_factory=Context7Config, description="Context7 integration configuration"
    )
    quality_tools: QualityToolsConfig | None = Field(
        default_factory=QualityToolsConfig,
        description="Quality analysis tools configuration (Phase 6)",
    )
    workflow: WorkflowConfig = Field(
        default_factory=WorkflowConfig,
        description="Workflow execution configuration",
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
        with open(config_path, encoding="utf-8") as f:
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


def get_default_config() -> dict[str, Any]:
    """
    Get default configuration as a dictionary (for template generation).

    Returns:
        Dictionary representation of default config
    """
    config = ProjectConfig()
    # Use model_dump with defaults, but exclude None values for cleaner output
    return config.model_dump(exclude_none=True)


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
