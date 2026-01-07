"""
Simple Mode - Simplified interface for TappsCodingAgents.

Provides intent-based agent orchestration that hides complexity while
showcasing the power of the framework.

2025 Enhancements:
- StreamingWorkflowExecutor: Progressive streaming with checkpoints
- StreamEvent: Typed events for workflow progress
- Cursor-native response formatting
- Structured step results with Pydantic v2
- Decorator-based formatter registry
- Agent contract validation
- Step dependency management
"""

from .intent_parser import Intent, IntentParser, IntentType
from .nl_handler import SimpleModeHandler
from .streaming import (
    StreamEvent,
    StreamEventType,
    StreamingWorkflowExecutor,
    create_streaming_response,
    format_streaming_response,
)

# 2025: Workflow documentation quality modules
from .agent_contracts import AgentContractValidator, AGENT_CONTRACTS
from .file_inference import TargetFileInferencer
from .result_formatters import FormatterRegistry, format_step_result
from .step_dependencies import (
    StepDependencyManager,
    StepExecutionState,
    WorkflowStep,
)
from .step_results import (
    BaseStepResult,
    StepResultParser,
    StepStatus,
)

__all__ = [
    "Intent",
    "IntentParser",
    "IntentType",
    "SimpleModeHandler",
    # 2025: Streaming responses
    "StreamingWorkflowExecutor",
    "StreamEvent",
    "StreamEventType",
    "create_streaming_response",
    "format_streaming_response",
    # 2025: Workflow documentation quality
    "AgentContractValidator",
    "AGENT_CONTRACTS",
    "TargetFileInferencer",
    "FormatterRegistry",
    "format_step_result",
    "StepDependencyManager",
    "StepExecutionState",
    "WorkflowStep",
    "BaseStepResult",
    "StepResultParser",
    "StepStatus",
]

