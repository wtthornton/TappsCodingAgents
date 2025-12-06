"""
Configuration management for TappsCodingAgents.

Provides Pydantic models for type-safe configuration and YAML loading.
"""

from pathlib import Path
from typing import Dict, Optional, Any
import yaml
from pydantic import BaseModel, Field, model_validator


class ScoringWeightsConfig(BaseModel):
    """Configuration for code scoring weights (must sum to 1.0)"""
    
    complexity: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for complexity score")
    security: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for security score")
    maintainability: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for maintainability score")
    test_coverage: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for test coverage score")
    performance: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for performance score")
    
    @model_validator(mode='after')
    def validate_weights_sum(self):
        """Ensure weights sum to approximately 1.0"""
        total = (
            self.complexity +
            self.security +
            self.maintainability +
            self.test_coverage +
            self.performance
        )
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
        return self


class ScoringConfig(BaseModel):
    """Configuration for code scoring system"""
    
    weights: ScoringWeightsConfig = Field(default_factory=ScoringWeightsConfig)
    quality_threshold: float = Field(default=70.0, ge=0.0, le=100.0, description="Minimum overall score to pass")


class CloudProviderConfig(BaseModel):
    """Configuration for cloud LLM providers"""
    
    api_key: Optional[str] = Field(default=None, description="API key for cloud provider")
    base_url: Optional[str] = Field(default=None, description="Custom base URL (optional)")
    timeout: float = Field(default=60.0, ge=1.0, description="Request timeout in seconds")


class MALConfig(BaseModel):
    """Configuration for Model Abstraction Layer"""
    
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    default_model: str = Field(default="qwen2.5-coder:7b", description="Default model name for LLM calls")
    default_provider: str = Field(default="ollama", description="Default provider (ollama/anthropic/openai)")
    timeout: float = Field(default=60.0, ge=1.0, description="Request timeout in seconds")
    
    # Cloud provider configurations
    anthropic: Optional[CloudProviderConfig] = Field(default=None, description="Anthropic Claude configuration")
    openai: Optional[CloudProviderConfig] = Field(default=None, description="OpenAI configuration")
    
    # Fallback settings
    enable_fallback: bool = Field(default=True, description="Enable automatic fallback to cloud if local fails")
    fallback_providers: list[str] = Field(default_factory=lambda: ["anthropic", "openai"], description="Fallback provider order")


class ReviewerAgentConfig(BaseModel):
    """Configuration specific to Reviewer Agent"""
    
    model: str = Field(default="qwen2.5-coder:7b", description="LLM model to use for reviews")
    quality_threshold: float = Field(default=70.0, ge=0.0, le=100.0, description="Minimum score to pass review")
    include_scoring: bool = Field(default=True, description="Include code scoring in review")
    include_llm_feedback: bool = Field(default=True, description="Include LLM-generated feedback")
    max_file_size: int = Field(default=1024 * 1024, ge=1024, description="Maximum file size in bytes (1MB default)")


class PlannerAgentConfig(BaseModel):
    """Configuration specific to Planner Agent"""
    
    model: str = Field(default="qwen2.5-coder:7b", description="LLM model to use for planning")
    stories_dir: Optional[str] = Field(default=None, description="Directory for storing stories (default: stories/)")
    default_priority: str = Field(default="medium", description="Default priority for new stories (high/medium/low)")


class ImplementerAgentConfig(BaseModel):
    """Configuration specific to Implementer Agent"""
    
    model: str = Field(default="qwen2.5-coder:7b", description="LLM model to use for code generation")
    require_review: bool = Field(default=True, description="Require code review before writing files")
    auto_approve_threshold: float = Field(default=80.0, ge=0.0, le=100.0, description="Auto-approve if score >= threshold")
    backup_files: bool = Field(default=True, description="Create backup before overwriting existing files")
    max_file_size: int = Field(default=10 * 1024 * 1024, ge=1024, description="Maximum file size in bytes (10MB default)")


class TesterAgentConfig(BaseModel):
    """Configuration specific to Tester Agent"""
    
    model: str = Field(default="qwen2.5-coder:7b", description="LLM model to use for test generation")
    test_framework: str = Field(default="pytest", description="Test framework to use (pytest/unittest)")
    tests_dir: Optional[str] = Field(default=None, description="Directory for tests (default: tests/)")
    coverage_threshold: float = Field(default=80.0, ge=0.0, le=100.0, description="Target test coverage percentage")
    auto_write_tests: bool = Field(default=True, description="Automatically write generated tests to files")


class DebuggerAgentConfig(BaseModel):
    """Configuration specific to Debugger Agent"""
    
    model: str = Field(default="deepseek-coder:6.7b", description="LLM model to use for error analysis")
    include_code_examples: bool = Field(default=True, description="Include code examples in fix suggestions")
    max_context_lines: int = Field(default=50, ge=10, le=200, description="Maximum lines of code context to include in analysis")


class DocumenterAgentConfig(BaseModel):
    """Configuration specific to Documenter Agent"""
    
    model: str = Field(default="qwen2.5-coder:7b", description="LLM model to use for documentation generation")
    docs_dir: Optional[str] = Field(default=None, description="Directory for generated docs (default: docs/)")
    include_examples: bool = Field(default=True, description="Include code examples in documentation")
    docstring_format: str = Field(default="google", description="Docstring format (google/numpy/sphinx)")


class Context7KnowledgeBaseConfig(BaseModel):
    """Configuration for Context7 knowledge base caching"""
    
    enabled: bool = Field(default=True, description="Enable KB caching")
    location: str = Field(default=".tapps-agents/kb/context7-cache", description="KB cache directory")
    sharding: bool = Field(default=True, description="Enable library-based sharding")
    indexing: bool = Field(default=True, description="Enable indexing")
    max_cache_size: str = Field(default="100MB", description="Maximum cache size")
    hit_rate_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Target hit rate threshold")
    fuzzy_match_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Fuzzy match confidence threshold")


class Context7RefreshConfig(BaseModel):
    """Configuration for Context7 auto-refresh system"""
    
    enabled: bool = Field(default=True, description="Enable auto-refresh")
    default_max_age_days: int = Field(default=30, ge=1, description="Default max age for cache entries (days)")
    check_on_access: bool = Field(default=True, description="Check staleness on access")
    auto_queue: bool = Field(default=True, description="Automatically queue stale entries")
    auto_process_on_startup: bool = Field(default=False, description="Process queue on agent startup")


class Context7Config(BaseModel):
    """Configuration for Context7 integration"""
    
    enabled: bool = Field(default=True, description="Enable Context7 integration")
    default_token_limit: int = Field(default=3000, ge=100, description="Default token limit for Context7 docs")
    cache_duration: int = Field(default=3600, ge=0, description="Cache duration in seconds")
    integration_level: str = Field(default="optional", description="Integration level (mandatory/optional)")
    usage_requirement: Optional[str] = Field(default=None, description="Usage requirement description")
    bypass_forbidden: bool = Field(default=True, description="Allow bypassing if Context7 unavailable")
    
    knowledge_base: Context7KnowledgeBaseConfig = Field(default_factory=Context7KnowledgeBaseConfig)
    refresh: Context7RefreshConfig = Field(default_factory=Context7RefreshConfig)


class QualityToolsConfig(BaseModel):
    """Configuration for quality analysis tools (Phase 6 - 2025 Standards)"""
    
    # Ruff configuration
    ruff_enabled: bool = Field(default=True, description="Enable Ruff linting")
    ruff_config_path: Optional[str] = Field(default=None, description="Path to ruff.toml or pyproject.toml (auto-detected if None)")
    
    # mypy configuration
    mypy_enabled: bool = Field(default=True, description="Enable mypy type checking")
    mypy_strict: bool = Field(default=False, description="Enable strict mode for mypy")
    mypy_config_path: Optional[str] = Field(default=None, description="Path to mypy.ini or pyproject.toml (auto-detected if None)")
    
    # jscpd configuration
    jscpd_enabled: bool = Field(default=True, description="Enable jscpd duplication detection")
    duplication_threshold: float = Field(default=3.0, ge=0.0, le=100.0, description="Maximum duplication percentage threshold")
    min_duplication_lines: int = Field(default=5, ge=3, description="Minimum lines for duplication detection")
    
    # TypeScript/JavaScript configuration
    typescript_enabled: bool = Field(default=True, description="Enable TypeScript/JavaScript support")
    eslint_config: Optional[str] = Field(default=None, description="Path to ESLint config file")
    tsconfig_path: Optional[str] = Field(default=None, description="Path to tsconfig.json")
    
    # Dependency security auditing
    pip_audit_enabled: bool = Field(default=True, description="Enable pip-audit security scanning")
    dependency_audit_threshold: str = Field(default="high", description="Minimum severity threshold (low/medium/high/critical)")


class AgentsConfig(BaseModel):
    """Configuration for all agents"""
    
    reviewer: ReviewerAgentConfig = Field(default_factory=ReviewerAgentConfig)
    planner: PlannerAgentConfig = Field(default_factory=PlannerAgentConfig)
    implementer: ImplementerAgentConfig = Field(default_factory=ImplementerAgentConfig)
    tester: TesterAgentConfig = Field(default_factory=TesterAgentConfig)
    debugger: DebuggerAgentConfig = Field(default_factory=DebuggerAgentConfig)
    documenter: DocumenterAgentConfig = Field(default_factory=DocumenterAgentConfig)


class ProjectConfig(BaseModel):
    """Root configuration model for TappsCodingAgents project"""
    
    # Project metadata
    project_name: Optional[str] = Field(default=None, description="Project name")
    version: Optional[str] = Field(default=None, description="Project version")
    
    # Core configuration
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    mal: MALConfig = Field(default_factory=MALConfig)
    context7: Optional[Context7Config] = Field(default_factory=Context7Config, description="Context7 integration configuration")
    quality_tools: Optional[QualityToolsConfig] = Field(default_factory=QualityToolsConfig, description="Quality analysis tools configuration (Phase 6)")
    
    model_config = {
        "extra": "ignore",  # Ignore unknown fields
        "validate_assignment": True,
    }


def load_config(config_path: Optional[Path] = None) -> ProjectConfig:
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
        with open(config_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            # Empty file, return defaults
            return ProjectConfig()
        
        # Validate and load config
        return ProjectConfig(**data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file {config_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading config from {config_path}: {e}")


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration as a dictionary (for template generation).
    
    Returns:
        Dictionary representation of default config
    """
    config = ProjectConfig()
    # Use model_dump with defaults, but exclude None values for cleaner output
    return config.model_dump(exclude_none=True)

