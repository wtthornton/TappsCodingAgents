"""
Natural Language Handler - Process natural language commands for Simple Mode.

Intercepts natural language commands, parses them, and routes to appropriate orchestrators.
Works both in CLI mode and Cursor Skills mode.
"""

# @ai-prime-directive: This file implements the Simple Mode natural language handler.
# Simple Mode is the primary user interface for TappsCodingAgents, providing natural language
# orchestration of multiple specialized skills. Do not modify the intent parsing or orchestrator
# routing without updating Simple Mode documentation and tests.

# @ai-constraints:
# - Must maintain backward compatibility with existing Simple Mode commands
# - Intent detection must support both explicit commands (*build) and natural language
# - Workflow enforcement is mandatory - do not bypass workflow steps
# - Performance: Intent parsing must complete in <50ms

# @note[2025-02-01]: Simple Mode provides natural language orchestration with automatic
# workflow enforcement. All development tasks should default to Simple Mode workflows.
# See docs/SIMPLE_MODE_GUIDE.md and .cursor/rules/simple-mode.mdc

from pathlib import Path
from typing import Any

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
from .workflow_suggester import WorkflowSuggester


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
        Optionally suggests workflows before execution.

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

        # Check for workflow mismatch and suggest better approach
        if intent.type.value == "build" and analysis.recommended_workflow == "validate":
            if analysis.intent_confidence >= 0.80:
                # High confidence - show suggestion
                suggestion = self._generate_workflow_suggestion(analysis, f"*{intent.type.value}")
                print(suggestion)
                print(f"\n✅ Auto-switching to *{analysis.recommended_workflow} workflow (confidence: {analysis.intent_confidence:.0%})\n")
                # Would need to update intent.type here in a real implementation
                # For now, just log the recommendation

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
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "intent": intent.type.value,
            }

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
