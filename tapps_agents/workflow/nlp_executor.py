"""
Natural Language Workflow Executor

Orchestrates natural language parsing, confirmation, and execution.
Epic 9: Natural Language Workflow Triggers - Integration
"""

import logging
from pathlib import Path
from typing import Any

from .confirmation_handler import ConfirmationHandler
from .context_analyzer import ContextAnalyzer
from .nlp_config import NLPConfig, LearningSystem
from .nlp_error_handler import AmbiguityResolver, ErrorHandler, ParseErrorType
from .nlp_parser import NaturalLanguageParser, WorkflowIntentResult
from .preset_loader import PresetLoader
from .suggestion_engine import SuggestionEngine

from .executor import WorkflowExecutor

logger = logging.getLogger(__name__)


class NLPWorkflowExecutor:
    """Executes workflows from natural language input."""

    def __init__(self, project_root: Path | None = None, auto_mode: bool = False):
        """
        Initialize NLP workflow executor.

        Args:
            project_root: Project root directory
            auto_mode: Auto mode (skip confirmation for high confidence)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.auto_mode = auto_mode

        # Initialize components
        self.config = NLPConfig()
        self.preset_loader = PresetLoader()
        self.parser = NaturalLanguageParser(self.preset_loader)
        self.context_analyzer = ContextAnalyzer(self.project_root)
        self.suggestion_engine = SuggestionEngine(self.preset_loader)
        self.confirmation_handler = ConfirmationHandler(
            auto_mode=auto_mode, confidence_threshold=self.config.get_confidence_threshold()
        )
        self.ambiguity_resolver = AmbiguityResolver(
            confidence_gap_threshold=self.config.get_ambiguity_threshold()
        )
        self.error_handler = ErrorHandler()
        self.learning_system = LearningSystem(self.config)

    def execute_from_natural_language(self, input_text: str, user_confirmation: str | None = None) -> dict[str, Any]:
        """
        Execute workflow from natural language input.

        Args:
            input_text: Natural language input
            user_confirmation: User confirmation response (if already provided)

        Returns:
            Dictionary with execution result
        """
        try:
            # Parse intent
            intent_result = self.parser.detect_intent(input_text)

            # Check for errors
            if not intent_result.workflow_name:
                error = self.error_handler.handle_error(ParseErrorType.NO_MATCH, intent_result=intent_result)
                return {
                    "success": False,
                    "error": self.error_handler.format_error(error),
                    "error_type": "no_match",
                }

            # Check for ambiguity
            if intent_result.ambiguity_flag:
                workflow_intent = self.parser.parse(input_text)
                resolved_workflow, strategy = self.ambiguity_resolver.resolve_ambiguity(intent_result, workflow_intent)

                if strategy == "clarify":
                    prompt = self.ambiguity_resolver.format_ambiguity_prompt(workflow_intent)
                    return {
                        "success": False,
                        "error": prompt,
                        "error_type": "ambiguous",
                        "requires_clarification": True,
                        "options": [workflow_intent.workflow_name] + [w[0] for w in (workflow_intent.alternative_matches or [])[:3]],
                    }

                intent_result.workflow_name = resolved_workflow

            # Load workflow
            workflow = self.preset_loader.load_preset(intent_result.workflow_name or "")
            if not workflow:
                error = self.error_handler.handle_error(ParseErrorType.NO_MATCH, intent_result=intent_result)
                return {
                    "success": False,
                    "error": self.error_handler.format_error(error),
                    "error_type": "workflow_not_found",
                }

            # Check if confirmation needed
            if not self.confirmation_handler.should_skip_confirmation(intent_result):
                if user_confirmation is None:
                    confirmation_message = self.confirmation_handler.format_confirmation(workflow, intent_result)
                    return {
                        "success": False,
                        "error": confirmation_message,
                        "error_type": "requires_confirmation",
                        "workflow_name": intent_result.workflow_name,
                        "parameters": intent_result.parameters,
                    }

                if not self.confirmation_handler.parse_confirmation(user_confirmation):
                    return {
                        "success": False,
                        "error": "Workflow execution cancelled.",
                        "error_type": "cancelled",
                    }

            # Execute workflow
            executor = WorkflowExecutor(auto_detect=False, auto_mode=self.auto_mode)
            target_file = intent_result.parameters.get("target_file")
            if target_file:
                executor.user_prompt = intent_result.parameters.get("prompt")

            import asyncio

            result = asyncio.run(executor.execute(workflow=workflow, target_file=target_file))

            # Record learning if user corrected
            if intent_result.workflow_name != input_text:
                self.learning_system.record_correction(input_text, input_text, intent_result.workflow_name)

            return {
                "success": True,
                "workflow_name": intent_result.workflow_name,
                "status": result.status,
                "result": result,
            }

        except Exception as e:
            logger.exception("Error executing workflow from natural language")
            error = self.error_handler.handle_error(ParseErrorType.PARSING_ERROR)
            return {
                "success": False,
                "error": f"{self.error_handler.format_error(error)}\n\nException: {str(e)}",
                "error_type": "execution_error",
            }

    def get_suggestions(self) -> str:
        """
        Get context-aware workflow suggestions.

        Returns:
            Formatted suggestions text
        """
        context = self.context_analyzer.analyze()
        suggestions = self.suggestion_engine.suggest_workflows(context)
        return self.suggestion_engine.format_suggestions(suggestions)

