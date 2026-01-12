"""
Common Enums for Workflow Artifacts.

Type-safe enums for status, priority, and other common fields across all artifacts.
"""

from enum import Enum


class Priority(str, Enum):
    """Priority level for stories, tasks, and artifacts."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ArtifactStatus(str, Enum):
    """Status of an artifact during workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    NOT_RUN = "not_run"


class RiskLevel(str, Enum):
    """Risk level for stories, tasks, and features."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StoryStatus(str, Enum):
    """Story execution status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"


class OperationType(str, Enum):
    """Type of operation performed by an agent."""

    # Planning operations
    PLAN = "plan"
    CREATE_STORY = "create-story"
    LIST_STORIES = "list-stories"

    # Design operations
    DESIGN_SYSTEM = "design-system"
    CREATE_DIAGRAM = "create-diagram"
    SELECT_TECHNOLOGY = "select-technology"
    DESIGN_SECURITY = "design-security"
    DEFINE_BOUNDARIES = "define-boundaries"

    # Code operations
    WRITE_CODE = "write-code"
    REFACTOR = "refactor"
    GENERATE_CODE = "generate-code"

    # Review operations
    REVIEW_CODE = "review-code"
    SCORE_CODE = "score-code"
    LINT_CODE = "lint-code"
    TYPE_CHECK = "type-check"
    SECURITY_SCAN = "security-scan"

    # Testing operations
    WRITE_TESTS = "write-tests"
    RUN_TESTS = "run-tests"
    GENERATE_TESTS = "generate-tests"

    # Documentation operations
    DOCUMENT = "document"
    GENERATE_DOCS = "generate-docs"
    UPDATE_README = "update-readme"
    DOCUMENT_API = "document-api"

    # Enhancement operations
    ENHANCE_PROMPT = "enhance-prompt"
    ENHANCE_QUICK = "enhance-quick"
    ENHANCE_STAGE = "enhance-stage"

    # Operations
    SECURITY_AUDIT = "security-audit"
    COMPLIANCE_CHECK = "compliance-check"
    DEPLOY = "deploy"
    INFRASTRUCTURE_SETUP = "infrastructure-setup"
    DEPENDENCY_AUDIT = "dependency-audit"
