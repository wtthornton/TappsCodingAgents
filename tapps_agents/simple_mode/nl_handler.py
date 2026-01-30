"""
Natural Language Handler - Process natural language commands for Simple Mode.

Intercepts natural language commands, parses them, and routes to appropriate orchestrators.
Works both in CLI mode and Cursor Skills mode. Includes workflow mismatch detection to prevent
users from running inappropriate workflows.
"""

# @ai-prime-directive: This file implements the Simple Mode natural language handler.
# Simple Mode is the primary user interface for TappsCodingAgents, providing natural language
# orchestration of multiple specialized skills. Do not modify the intent parsing or orchestrator
# routing without updating Simple Mode documentation and tests.

# @ai-constraints:
# - Must maintain backward compatibility with existing Simple Mode commands
# - Intent detection must support both explicit commands (*build) and natural language
# - Workflow enforcement is mandatory - do not bypass workflow steps
# - Performance: Intent parsing must complete in <50ms, validation <500ms

# @note[2026-01-30]: Added workflow mismatch detection to warn users when workflow choice
# doesn't match task characteristics. See docs/archive/feedback/WORKFLOW_AUTO_DETECTION_FAILURE_INIT_VALIDATION.md

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from tapps_agents.core.config import ProjectConfig, load_config

from .intent_parser import Intent, IntentParser, IntentType
from .orchestrators import (
    BreakdownOrchestrator,
    BrownfieldOrchestrator,
    BuildOrchestrator,
    EnhanceOrchestrator,
    EpicOrchestrator,
    ExploreOrchestrator,
    FixOrchestrator,
    PlanAnalysisOrchestrator,
    PROrchestrator,
    RefactorOrchestrator,
    ReviewOrchestrator,
    TestOrchestrator,
    TodoOrchestrator,
    ValidateOrchestrator,
)
from .prompt_analyzer import PromptAnalysis, PromptAnalyzer
from .variations import normalize_command
from .workflow_suggester import (
    COMPLEXITY_ORDER,
    SCOPE_ORDER,
    WORKFLOW_REQUIREMENTS,
    WorkflowSuggester,
    detect_primary_intent,
)

# Initialize logger
logger = logging.getLogger(__name__)


# ============================================================================
# Workflow Mismatch Warning Data Model
# ============================================================================

@dataclass(frozen=True)
class WorkflowMismatchWarning:
    """
    Warning data for workflow mismatch detection.

    Represents a detected mismatch between user-specified workflow and task
    characteristics, providing actionable recommendations and impact estimates.

    Attributes:
        detected_intent: Primary intent detected from prompt
            Values: "bug_fix" | "feature" | "enhancement" | "architectural" | "framework_dev"
        detected_scope: Task scope (files affected)
            Values: "low" (1-3 files) | "medium" (4-6 files) | "high" (7+ files)
        detected_complexity: Task complexity (architectural impact)
            Values: "low" | "medium" | "high"
        recommended_workflow: Suggested workflow for this task
            Values: "*fix" | "*build" | "*full" | "*refactor"
        confidence: Confidence in recommendation (0.7-1.0)
        reason: Human-readable explanation for recommendation
        token_savings: Estimated tokens saved by switching workflows
        time_savings: Estimated minutes saved by switching workflows

    Immutability:
        frozen=True ensures warning data cannot be modified after creation
    """

    detected_intent: str
    detected_scope: str
    detected_complexity: str
    recommended_workflow: str
    confidence: float
    reason: str
    token_savings: int
    time_savings: int

    def format_warning(self) -> str:
        """
        Format warning for terminal display.

        Returns:
            Formatted warning message with visual hierarchy (emoji, structure)
        """
        return f"""⚠️ Workflow Mismatch Warning

Task Analysis:
- Primary Intent: {self.detected_intent} (confidence: {self.confidence:.0%})
- Scope: {self.detected_scope}
- Complexity: {self.detected_complexity}

{self.reason}

Recommended: {self.recommended_workflow}
Token Savings: ~{self.token_savings // 1000}K tokens, ~{self.time_savings} minutes"""


# ============================================================================
# Simple Mode Handler
# ============================================================================

class SimpleModeHandler:
    """Handler for natural language commands in Simple Mode."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ):
        """
        Initialize Simple Mode handler.

        Args:
            project_root: Project root directory
            config: Optional project configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()
        self.intent_parser = IntentParser()
        self.workflow_suggester = WorkflowSuggester()
        self.prompt_analyzer = PromptAnalyzer()

        # Initialize orchestrators
        self.orchestrators = {
            IntentType.BUILD: BuildOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.VALIDATE: ValidateOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.REVIEW: ReviewOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.FIX: FixOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.TEST: TestOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.EPIC: EpicOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.EXPLORE: ExploreOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.REFACTOR: RefactorOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.PLAN_ANALYSIS: PlanAnalysisOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.PR: PROrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.BROWNFIELD: BrownfieldOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.ENHANCE: EnhanceOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.BREAKDOWN: BreakdownOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.TODO: TodoOrchestrator(
                project_root=self.project_root, config=self.config
            ),
        }

    async def handle(self, command: str, suggest_workflow: bool = True) -> dict[str, Any]:
        """
        Handle a natural language command.

        Enhanced to detect and force Simple Mode when requested.
        Includes workflow mismatch detection to warn users before execution.

        Args:
            command: User's natural language command
            suggest_workflow: Whether to suggest workflow if not already using Simple Mode

        Returns:
            Dictionary with execution results
        """
        # Check for Simple Mode intent first
        if self.intent_parser.detect_simple_mode_intent(command):
            # Force Simple Mode workflow
            if not self.config.simple_mode.enabled:
                return {
                    "success": False,
                    "error": "Simple Mode requested but not available. Install with: `tapps-agents init`",
                    "suggestion": "Run: tapps-agents simple-mode on",
                }

        # Normalize command (expand synonyms)
        normalized = normalize_command(command)

        # Parse intent
        intent = self.intent_parser.parse(normalized)

        # Analyze prompt for intelligent workflow selection
        analysis = self._analyze_prompt(command, intent)

        # Suggest workflow if enabled and not already using Simple Mode
        if suggest_workflow and not self.intent_parser.detect_simple_mode_intent(command):
            suggestion = self.workflow_suggester.suggest_workflow(command)
            if suggestion and self.workflow_suggester.should_suggest(command):
                return {
                    "success": False,
                    "suggestion": True,
                    "workflow_suggestion": {
                        "command": suggestion.workflow_command,
                        "type": suggestion.workflow_type,
                        "benefits": suggestion.benefits,
                        "reason": suggestion.reason,
                        "confidence": suggestion.confidence,
                        "formatted": self.workflow_suggester.format_suggestion(suggestion),
                    },
                    "message": "Workflow suggestion available",
                }

        # Check if Simple Mode is enabled (or forced)
        force_simple_mode = intent.parameters.get("force_simple_mode", False)
        if force_simple_mode and not self.config.simple_mode.enabled:
            return {
                "success": False,
                "error": "Simple Mode requested but not available. Install with: `tapps-agents init`",
                "suggestion": "Run: tapps-agents simple-mode on",
            }

        if not self.config.simple_mode.enabled and not force_simple_mode:
            return {
                "success": False,
                "error": "Simple Mode is disabled. Enable it in .tapps-agents/config.yaml",
            }

        # Route to appropriate orchestrator
        orchestrator = self.orchestrators.get(intent.type)
        if not orchestrator:
            return {
                "success": False,
                "error": f"Unknown intent type: {intent.type}. Try: build, review, fix, or test",
                "intent": intent.type.value,
                "confidence": intent.confidence,
            }

        # [NEW] Workflow mismatch detection
        # Extract workflow name and check for --force flag
        workflow = f"*{intent.type.value}" if intent.type else None
        force_validation = intent.parameters.get("force", False)

        if workflow:
            warning = self.validate_workflow_match(workflow, command, force_validation)

            if warning:
                # Display warning to user
                self._display_mismatch_warning(warning, workflow)

                # Prompt for user choice (unless auto mode)
                auto_mode = intent.parameters.get("auto", False)

                if auto_mode:
                    choice = "N"  # Default to cancel in auto mode
                    logger.info(f"Auto mode: defaulting to 'N' for workflow mismatch")
                else:
                    choice = self._prompt_user_choice(warning, workflow)

                # Handle user choice
                if choice == "N":
                    logger.info(f"User declined workflow: {workflow}")
                    return {
                        "success": False,
                        "status": "cancelled",
                        "reason": "User declined due to workflow mismatch",
                        "warning": {
                            "detected_intent": warning.detected_intent,
                            "recommended_workflow": warning.recommended_workflow,
                            "confidence": warning.confidence,
                        },
                    }
                elif choice == "switch":
                    # Switch to recommended workflow
                    logger.info(f"User switched from {workflow} to {warning.recommended_workflow}")
                    # Update intent type to match recommended workflow
                    recommended_intent_type = self._workflow_to_intent_type(warning.recommended_workflow)
                    if recommended_intent_type:
                        intent.type = recommended_intent_type
                        orchestrator = self.orchestrators.get(intent.type)
                elif choice == "y":
                    logger.info(f"User proceeded with {workflow} despite mismatch warning")

        # Check for workflow mismatch and suggest better approach (legacy)
        if intent.type.value == "build" and analysis.recommended_workflow == "validate":
            if analysis.intent_confidence >= 0.80:
                # High confidence - show suggestion
                suggestion = self._generate_workflow_suggestion(analysis, f"*{intent.type.value}")
                print(suggestion)
                print(f"\n✅ Auto-switching to *{analysis.recommended_workflow} workflow (confidence: {analysis.intent_confidence:.0%})\n")

        # Pass analysis to orchestrator via parameters
        intent.parameters["prompt_analysis"] = analysis

        # Execute orchestrator
        try:
            result = await orchestrator.execute(intent, intent.parameters)
            result["intent"] = intent.type.value
            result["confidence"] = intent.confidence
            result["prompt_analysis"] = {
                "intent": analysis.primary_intent.value,
                "complexity": analysis.complexity.value,
                "word_count": analysis.word_count,
                "has_existing_code": analysis.has_existing_code,
                "recommended_workflow": analysis.recommended_workflow,
                "recommended_enhancement": analysis.recommended_enhancement,
                "recommended_preset": analysis.recommended_preset,
            }
            if force_simple_mode:
                result["simple_mode_forced"] = True
            return result
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "intent": intent.type.value,
            }

    def validate_workflow_match(
        self,
        workflow: str,
        prompt: str,
        force: bool = False
    ) -> WorkflowMismatchWarning | None:
        """
        Validate that user-specified workflow matches task characteristics.

        Analyzes task characteristics (intent, scope, complexity) and compares against
        workflow requirements. Returns a warning if mismatch is detected with high
        confidence (≥70%).

        Args:
            workflow: Workflow name specified by user ("*full", "*build", "*fix", etc.)
            prompt: Natural language task description
            force: Skip validation if True (default: False)

        Returns:
            WorkflowMismatchWarning if mismatch detected, None otherwise

        Performance:
            Target: <500ms (P99 latency)

        Examples:
            >>> handler.validate_workflow_match("*full", "Fix validation bug", False)
            WorkflowMismatchWarning(...)  # Mismatch detected

            >>> handler.validate_workflow_match("*fix", "Fix validation bug", False)
            None  # No mismatch

            >>> handler.validate_workflow_match("*full", "Fix bug", True)
            None  # Validation bypassed via force=True

        See Also:
            - detect_primary_intent(): Intent detection
            - _analyze_task_characteristics(): Task analysis
            - _compare_to_workflow_requirements(): Requirement comparison
        """
        # Skip validation if force flag is set
        if force:
            logger.info(f"Validation bypassed via --force flag")
            return None

        # Validate workflow name
        if workflow not in WORKFLOW_REQUIREMENTS:
            logger.warning(f"Unknown workflow: {workflow}. Skipping validation.")
            return None

        # Handle empty prompt
        if not prompt or len(prompt.strip()) == 0:
            logger.debug("Empty prompt, skipping validation")
            return None

        # Step 1: Detect primary intent
        intent, confidence = detect_primary_intent(prompt)

        if intent is None or confidence < 0.6:
            # Low confidence, skip validation
            logger.debug(f"Low intent confidence ({confidence:.2f}), skipping validation")
            return None

        # Step 2: Analyze task characteristics
        characteristics = self._analyze_task_characteristics(prompt, intent)

        # Step 3: Compare to workflow requirements
        mismatch = self._compare_to_workflow_requirements(workflow, characteristics)

        # Step 4: Return warning if mismatch detected with high confidence
        if mismatch and confidence >= 0.7:
            warning = self._create_mismatch_warning(workflow, characteristics, confidence)
            logger.info(
                f"Workflow mismatch detected: {workflow} for {characteristics['intent']} "
                f"(confidence: {confidence:.2f}, recommended: {warning.recommended_workflow})"
            )
            return warning

        return None

    def _analyze_task_characteristics(self, prompt: str, intent: str) -> dict[str, str]:
        """
        Analyze task characteristics from prompt and detected intent.

        Uses heuristics to determine task scope (files affected) and complexity
        (architectural impact) based on prompt language and intent type.

        Args:
            prompt: Natural language task description
            intent: Detected primary intent ("bug_fix" | "enhancement" | "architectural")

        Returns:
            Dict with intent, scope, and complexity

        Heuristics:
            Scope (files affected):
            - "low" (1-3 files): Single component, focused change
            - "medium" (4-6 files): Multiple components, moderate reach
            - "high" (7+ files): System-wide, cross-cutting concern

            Complexity (architectural impact):
            - "low": Simple fix, no architectural changes
            - "medium": Feature addition, some design needed
            - "high": Architectural changes, framework development
        """
        # Scope heuristics (simple for MVP)
        scope = "low"  # Default

        if "tapps_agents/" in prompt.lower():
            scope = "high"  # Framework changes
        elif len(prompt.split()) > 30:
            scope = "medium"  # Longer prompts suggest bigger scope

        # Complexity heuristics
        complexity = "medium"  # Default

        if intent == "architectural" or "architecture" in prompt.lower():
            complexity = "high"
        elif intent == "bug_fix" and scope == "low":
            complexity = "low"

        return {
            "intent": intent,
            "scope": scope,
            "complexity": complexity,
        }

    def _compare_to_workflow_requirements(
        self, workflow: str, characteristics: dict[str, str]
    ) -> bool:
        """
        Compare task characteristics to workflow requirements.

        Args:
            workflow: Workflow name ("*full", "*build", "*fix")
            characteristics: Detected task characteristics

        Returns:
            True if mismatch detected, False if workflow matches
        """
        requirements = WORKFLOW_REQUIREMENTS.get(workflow)
        if not requirements:
            return False  # Unknown workflow, skip validation

        # Check intent match
        if characteristics["intent"] not in requirements.get("required_intents", []):
            return True  # Intent mismatch

        # Check complexity bounds
        if "min_complexity" in requirements:
            if COMPLEXITY_ORDER[characteristics["complexity"]] < \
               COMPLEXITY_ORDER[requirements["min_complexity"]]:
                return True  # Complexity too low

        if "max_complexity" in requirements:
            if COMPLEXITY_ORDER[characteristics["complexity"]] > \
               COMPLEXITY_ORDER[requirements["max_complexity"]]:
                return True  # Complexity too high

        # Check scope bounds
        if "min_scope" in requirements:
            if SCOPE_ORDER[characteristics["scope"]] < \
               SCOPE_ORDER[requirements["min_scope"]]:
                return True  # Scope too low

        if "max_scope" in requirements:
            if SCOPE_ORDER[characteristics["scope"]] > \
               SCOPE_ORDER[requirements["max_scope"]]:
                return True  # Scope too high

        return False  # No mismatch

    def _create_mismatch_warning(
        self, workflow: str, characteristics: dict[str, str], confidence: float
    ) -> WorkflowMismatchWarning:
        """
        Create mismatch warning with recommendations.

        Args:
            workflow: Current workflow specified by user
            characteristics: Detected task characteristics
            confidence: Confidence score

        Returns:
            WorkflowMismatchWarning with recommendations
        """
        # Recommend workflow based on intent
        recommended = {
            "bug_fix": "*fix",
            "feature": "*build",
            "enhancement": "*build",
            "architectural": "*full",
            "framework_dev": "*full",
        }.get(characteristics["intent"], "*build")

        # Estimate token savings
        current_steps = WORKFLOW_REQUIREMENTS[workflow]["steps"]
        recommended_steps = WORKFLOW_REQUIREMENTS.get(recommended, {}).get("steps", 4)
        step_difference = current_steps - recommended_steps
        token_savings = max(0, step_difference * 10000)  # ~10K tokens per step
        time_savings = max(0, step_difference * 5)  # ~5 minutes per step

        reason = (
            f"*{workflow.lstrip('*')} workflow is designed for: "
            f"{WORKFLOW_REQUIREMENTS[workflow]['description']}"
        )

        return WorkflowMismatchWarning(
            detected_intent=characteristics["intent"],
            detected_scope=characteristics["scope"],
            detected_complexity=characteristics["complexity"],
            recommended_workflow=recommended,
            confidence=confidence,
            reason=reason,
            token_savings=token_savings,
            time_savings=time_savings,
        )

    def _display_mismatch_warning(
        self, warning: WorkflowMismatchWarning, current_workflow: str
    ) -> None:
        """
        Display formatted warning to user.

        Args:
            warning: Workflow mismatch warning
            current_workflow: Current workflow specified by user
        """
        print("\n" + "=" * 70)
        print(warning.format_warning())
        print("=" * 70)
        print(f"\nProceed with {current_workflow}? [y/N/switch]")

    def _prompt_user_choice(
        self, warning: WorkflowMismatchWarning, current_workflow: str
    ) -> str:
        """
        Prompt user for choice.

        Args:
            warning: Workflow mismatch warning
            current_workflow: Current workflow specified by user

        Returns:
            "y" (proceed), "N" (cancel), or "switch" (use recommended)
        """
        while True:
            try:
                choice = input("> ").strip().lower()

                if choice in ("y", "yes"):
                    return "y"
                elif choice in ("n", "no", ""):
                    return "N"
                elif choice in ("s", "switch"):
                    return "switch"
                else:
                    print("Invalid choice. Enter y (proceed), N (cancel), or switch.")
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled by user")
                return "N"

    def _workflow_to_intent_type(self, workflow: str) -> IntentType | None:
        """
        Convert workflow name to IntentType.

        Args:
            workflow: Workflow name ("*fix", "*build", etc.)

        Returns:
            IntentType or None if unknown
        """
        mapping = {
            "*fix": IntentType.FIX,
            "*build": IntentType.BUILD,
            "*full": IntentType.BUILD,  # Full SDLC maps to build
            "*review": IntentType.REVIEW,
            "*test": IntentType.TEST,
            "*refactor": IntentType.REFACTOR,
        }
        return mapping.get(workflow)

    def is_simple_mode_enabled(self) -> bool:
        """Check if Simple Mode is enabled."""
        return self.config.simple_mode.enabled

    def is_simple_mode_available(self) -> bool:
        """
        Check if Simple Mode is available and enabled.

        Returns:
            True if Simple Mode is available, False otherwise
        """
        return self.config.simple_mode.enabled

    def _analyze_prompt(self, command: str, intent: Intent) -> PromptAnalysis:
        """
        Analyze prompt for intelligent workflow selection.

        Args:
            command: User's command
            intent: Parsed intent

        Returns:
            PromptAnalysis with recommendations
        """
        # Extract command type from intent
        command_type = f"*{intent.type.value}" if intent.type else None

        # Analyze prompt
        analysis = self.prompt_analyzer.analyze(command, command_type)

        # Log analysis for visibility
        if analysis.intent_confidence >= 0.7:
            print("\n📊 Prompt Analysis:")
            print(f"  Intent: {analysis.primary_intent.value} ({analysis.intent_confidence:.0%} confidence)")
            print(f"  Complexity: {analysis.complexity.value} ({analysis.word_count} words)")
            if analysis.has_existing_code:
                print(f"  Existing Code: Yes ({len(analysis.existing_code_refs)} references)")
            print(f"  Recommended Workflow: {analysis.recommended_workflow}")
            print(f"  Recommended Enhancement: {analysis.recommended_enhancement}")
            print(f"  Recommended Preset: {analysis.recommended_preset}")
            print(f"  Rationale: {analysis.analysis_rationale}\n")

        return analysis

    def _generate_workflow_suggestion(self, analysis: PromptAnalysis, current_command: str) -> str:
        """
        Generate workflow suggestion message based on analysis.

        Args:
            analysis: Prompt analysis result
            current_command: Current command being executed

        Returns:
            Formatted suggestion message
        """
        return f"""
🤖 Workflow Suggestion:

Detected existing code reference in your prompt.

**Suggested Workflow:** @simple-mode *{analysis.recommended_workflow} "{analysis.primary_intent.value}"

**Benefits:**
✅ Validates existing implementation
✅ Identifies optimizations
✅ 50% faster (skips duplicate code generation)
✅ Focused recommendations

**Current Command:** {current_command}

**Recommendation:** Use *{analysis.recommended_workflow} for comparison tasks.
""".strip()
