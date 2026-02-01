"""
Workflow Enforcer - Core enforcement logic for ENH-001-S1

Intercepts file write/edit operations and enforces workflow usage based on
configuration. Part of the ENH-001 Workflow Enforcement System.

Performance Targets:
    - Interception latency: <50ms p95
    - Memory overhead: <10MB
    - CPU overhead: <5%

Design Principles:
    - Fail-safe: Errors default to "allow" (never block users due to bugs)
    - Single responsibility: Only decides enforcement actions
    - Dependency injection: Accepts config via constructor for testability
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, TypedDict

from tapps_agents.core.llm_behavior import EnforcementConfig
from tapps_agents.workflow.intent_detector import IntentDetector, WorkflowType
from tapps_agents.workflow.message_formatter import MessageConfig, MessageFormatter

logger = logging.getLogger(__name__)


class EnforcementDecision(TypedDict):
    """
    Enforcement decision returned by WorkflowEnforcer.

    Attributes:
        action: Enforcement action to take:
            - "block": Block the operation (blocking mode)
            - "warn": Show warning but allow operation (warning mode)
            - "allow": Allow operation without message (silent mode or allowed)
        message: User-facing message explaining the decision. Empty string
            for "allow" actions or silent mode.
        should_block: Boolean indicating if operation should be blocked.
            True only when action="block" AND block_direct_edits=True.
        confidence: Confidence score (0.0-1.0) for the enforcement decision.
            Currently 0.0 (Story 1); Story 2 will add intent detection.

    Example:
        >>> decision: EnforcementDecision = {
        ...     "action": "warn",
        ...     "message": "Consider using @simple-mode *build instead",
        ...     "should_block": False,
        ...     "confidence": 0.0
        ... }
    """

    action: Literal["block", "warn", "allow"]
    message: str
    should_block: bool
    confidence: float


class WorkflowEnforcer:
    """
    Workflow enforcer that intercepts file operations and enforces workflow usage.

    This class implements the core enforcement logic for ENH-001-S1. It intercepts
    file write/edit operations before they execute, evaluates the context against
    configuration, and returns an enforcement decision (block/warn/allow).

    Design Pattern: Interceptor Pattern (Decorator Variant)
    - Hooks into file operations transparently
    - Separation of concerns: enforcement separate from file I/O
    - Fail-safe design: Errors default to "allow"

    Attributes:
        config: EnforcementConfig instance controlling enforcement behavior
        _config_path: Path to config file (for config reload in future)
        _config_mtime: File modification time (for config reload in future)

    Example:
        >>> # Use default config
        >>> enforcer = WorkflowEnforcer()
        >>> decision = enforcer.intercept_code_edit(
        ...     file_path=Path("src/api/auth.py"),
        ...     user_intent="Add login endpoint",
        ...     is_new_file=False,
        ...     skip_enforcement=False
        ... )
        >>> if decision["should_block"]:
        ...     print(decision["message"])

        >>> # Use custom config
        >>> config = EnforcementConfig(mode="warning")
        >>> enforcer = WorkflowEnforcer(config=config)

    Performance:
        - Initialization: <10ms (config load cached)
        - intercept_code_edit(): <50ms p95
        - Memory overhead: <1MB per instance
    """

    def __init__(
        self,
        config_path: Path | None = None,
        config: EnforcementConfig | None = None,
    ) -> None:
        """
        Initialize workflow enforcer.

        Args:
            config_path: Path to configuration file. If None, uses default
                (.tapps-agents/config.yaml in current directory).
            config: Pre-loaded EnforcementConfig instance. If provided,
                overrides config_path. Useful for testing and custom configs.

        Behavior:
            - If config provided, use it directly (no file loading)
            - If config_path provided, load config from that path
            - If neither provided, load from default path
            - If config load fails, use default EnforcementConfig() values
            - Logs info message with config mode after initialization

        Example:
            >>> # Use default config from .tapps-agents/config.yaml
            >>> enforcer = WorkflowEnforcer()

            >>> # Use custom config path
            >>> enforcer = WorkflowEnforcer(config_path=Path("custom.yaml"))

            >>> # Use pre-loaded config (for testing)
            >>> config = EnforcementConfig(mode="warning")
            >>> enforcer = WorkflowEnforcer(config=config)
        """
        self._config_path = config_path
        self._config_mtime: float = 0.0

        # Load or use provided config
        if config is not None:
            # Use provided config directly (dependency injection for testing)
            self.config = config
        else:
            # Load config from file
            self.config = self._load_config(config_path)

        # Initialize intent detector and message formatter (ENH-001-S2, S3)
        self._intent_detector = IntentDetector()
        self._message_formatter = MessageFormatter(MessageConfig(
            use_emoji=True,
            show_benefits=self.config.suggest_workflows,
            show_override=True,
        ))

        logger.info(
            f"WorkflowEnforcer initialized with mode={self.config.mode}, "
            f"confidence_threshold={self.config.confidence_threshold}"
        )

    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool,
        skip_enforcement: bool = False,
    ) -> EnforcementDecision:
        """
        Intercept file write/edit operation and make enforcement decision.

        This is the main enforcement method. It evaluates the file operation
        context, checks configuration, and returns a decision indicating whether
        to block, warn, or allow the operation.

        Args:
            file_path: Path to file being written or edited. Can be absolute
                or relative. Used for enforcement decision and logging.
            user_intent: User's intent or description from prompt/conversation
                context. Used for decision logic and message generation.
                Can be empty string if intent unknown.
            is_new_file: True if creating a new file, False if editing existing
                file. Affects enforcement decision (future: may treat new files
                differently).
            skip_enforcement: Override flag to bypass enforcement. Set to True
                to always return "allow" decision. Used by CLI --skip-enforcement.

        Returns:
            EnforcementDecision: Typed dict with enforcement decision fields:
                - action: "block" | "warn" | "allow"
                - message: User-facing message (empty for silent/allow)
                - should_block: Boolean indicating if operation should be blocked
                - confidence: Confidence score (0.0 for Story 1; Story 2 populates)

        Raises:
            Never raises exceptions. Errors are caught, logged, and result in
            "allow" decision (fail-safe design).

        Performance Contract:
            - p95 latency: <50ms
            - p99 latency: <100ms
            - Memory allocation: <1MB per call

        Example:
            >>> enforcer = WorkflowEnforcer()
            >>> decision = enforcer.intercept_code_edit(
            ...     file_path=Path("src/api/auth.py"),
            ...     user_intent="Add login endpoint",
            ...     is_new_file=False
            ... )
            >>> if decision["should_block"]:
            ...     print(f"Blocked: {decision['message']}")
            ... elif decision["action"] == "warn":
            ...     print(f"Warning: {decision['message']}")
        """
        try:
            # Check if enforcement should be applied
            if not self._should_enforce(file_path, is_new_file, skip_enforcement):
                return self._create_decision("allow", file_path, user_intent)

            # Determine action based on config mode
            # Story 1: Simple config-based decision (no intent detection yet)
            # Story 2 will add intent detection logic here
            action: Literal["block", "warn", "allow"]
            if self.config.mode == "blocking":
                action = "block"
            elif self.config.mode == "warning":
                action = "warn"
            else:  # silent
                action = "allow"

            # Create and return decision
            return self._create_decision(action, file_path, user_intent)

        except Exception as e:
            # Fail-safe: Log error and allow operation
            logger.error(
                f"WorkflowEnforcer.intercept_code_edit() failed with error: {e}. "
                f"Defaulting to 'allow' (fail-safe). file_path={file_path}, "
                f"user_intent={user_intent[:100]}"
            )
            return self._create_decision("allow", file_path, user_intent)

    def _load_config(self, config_path: Path | None = None) -> EnforcementConfig:
        """
        Load configuration from file.

        Delegates to EnforcementConfig.from_config_file() for actual loading.
        Implements caching and error handling.

        Args:
            config_path: Path to config file. If None, uses default path.

        Returns:
            EnforcementConfig instance loaded from file or with defaults

        Error Handling:
            - If config file missing: Returns default EnforcementConfig()
            - If config invalid: Logs warning, returns default EnforcementConfig()
            - Never raises exceptions (fail-safe)
        """
        try:
            config = EnforcementConfig.from_config_file(config_path)
            return config
        except Exception as e:
            logger.warning(
                f"Failed to load enforcement config from {config_path}: {e}. "
                f"Using default config (mode=blocking)"
            )
            return EnforcementConfig()

    def _should_enforce(
        self,
        file_path: Path,
        is_new_file: bool,
        skip_enforcement: bool,
    ) -> bool:
        """
        Check if enforcement should be applied for this operation.

        Args:
            file_path: Path to file being written/edited
            is_new_file: True if creating new file
            skip_enforcement: CLI override flag

        Returns:
            True if enforcement should be applied, False otherwise

        Logic:
            - If skip_enforcement=True → return False (CLI override)
            - If config.mode="silent" → return False (logging only)
            - Otherwise → return True

        Future Extensions (Story 5+):
            - Check excluded paths (e.g., .tapps-agents/*, tests/*)
            - Check file types (e.g., only enforce for .py files)
            - Check user roles (e.g., skip for admins)
        """
        # CLI override: Always allow if skip_enforcement=True
        if skip_enforcement:
            logger.debug(
                f"Enforcement skipped via --skip-enforcement flag: {file_path}"
            )
            return False

        # Silent mode: Log but don't enforce
        if self.config.mode == "silent":
            logger.info(
                f"Silent mode: Would enforce for {file_path}, is_new={is_new_file}"
            )
            return False

        # Default: Enforce
        return True

    def _create_decision(
        self,
        action: Literal["block", "warn", "allow"],
        file_path: Path,
        user_intent: str,
    ) -> EnforcementDecision:
        """
        Create enforcement decision with appropriate message.

        Args:
            action: Enforcement action (block/warn/allow)
            file_path: Path to file being written/edited
            user_intent: User's intent description

        Returns:
            EnforcementDecision with formatted message

        Message Format:
            - block: Suggests using workflows with specific command
            - warn: Lighter suggestion to use workflows
            - allow: Empty message

        Note:
            Uses MessageFormatter (ENH-001-S3) for rich, context-aware messages.
            Uses IntentDetector (ENH-001-S2) for workflow detection and confidence.
        """
        # Determine should_block flag
        should_block = action == "block" and self.config.block_direct_edits

        # Detect intent and get confidence (ENH-001-S2 integration)
        detection_result = self._intent_detector.detect_workflow(
            user_intent=user_intent,
            file_path=file_path if file_path.exists() else None,
        )
        workflow = detection_result.workflow_type
        confidence = detection_result.confidence

        # Generate message using MessageFormatter (ENH-001-S3 integration)
        if action == "block":
            if self.config.suggest_workflows:
                message = self._message_formatter.format_blocking_message(
                    workflow=workflow,
                    user_intent=user_intent,
                    file_path=file_path,
                    confidence=confidence,
                )
            else:
                message = (
                    f"Direct file edit blocked: {file_path}\n"
                    f"Use --skip-enforcement flag to bypass."
                )
        elif action == "warn":
            if self.config.suggest_workflows:
                message = self._message_formatter.format_warning_message(
                    workflow=workflow,
                    user_intent=user_intent,
                    confidence=confidence,
                )
            else:
                message = f"Consider using a workflow for: {file_path}"
        else:  # allow
            message = self._message_formatter.format_allow_message()

        # Create decision with actual confidence from intent detection
        decision: EnforcementDecision = {
            "action": action,
            "message": message,
            "should_block": should_block,
            "confidence": confidence,
        }

        # Log decision
        logger.debug(
            f"Enforcement decision: action={action}, should_block={should_block}, "
            f"file_path={file_path}, workflow={workflow.value}, confidence={confidence:.1f}%"
        )

        return decision
