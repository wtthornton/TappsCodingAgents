"""
Custom exception types for TappsCodingAgents.

Provides specific exception types for better error handling and debugging.
"""


class TappsAgentsError(Exception):
    """Base exception for all TappsCodingAgents errors."""

    pass


class ConfigurationError(TappsAgentsError):
    """Raised when configuration is invalid or missing."""

    pass


class ExpertError(TappsAgentsError):
    """Base exception for expert-related errors."""

    pass


class ExpertNotFoundError(ExpertError):
    """Raised when an expert is not found."""

    pass


class ExpertConsultationError(ExpertError):
    """Raised when expert consultation fails."""

    pass


class WorkflowError(TappsAgentsError):
    """Base exception for workflow-related errors."""

    pass


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow file is not found."""

    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""

    pass


class AgentError(TappsAgentsError):
    """Base exception for agent-related errors."""

    pass


class AgentActivationError(AgentError):
    """Raised when agent activation fails."""

    pass


class FileOperationError(TappsAgentsError):
    """Raised when file operations fail."""

    pass


class AgentFileNotFoundError(FileOperationError):
    """Raised when a required file is not found."""

    pass


class FileReadError(FileOperationError):
    """Raised when file reading fails."""

    pass


class FileWriteError(FileOperationError):
    """Raised when file writing fails."""

    pass


class Context7Error(TappsAgentsError):
    """Base exception for Context7-related errors."""

    pass


class Context7UnavailableError(Context7Error):
    """Raised when Context7 is unavailable."""

    pass


class ProjectProfileError(TappsAgentsError):
    """Raised when project profile operations fail."""

    pass
