"""
Context-Aware Suggestion Engine

Epic 13: Context-Aware Suggestions
Provides intelligent suggestions for workflows, agents, and actions based on project context.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.project_profile import ProjectProfile, ProjectProfileDetector
from .context_analyzer import ContextAnalyzer, ProjectContext
from .recommender import WorkflowRecommendation, WorkflowRecommender

logger = logging.getLogger(__name__)


# Backward compatibility: Legacy SuggestionEngine for nlp_executor
class SuggestionEngine:
    """
    Legacy suggestion engine wrapper for backward compatibility.
    
    This class provides a simple interface for NLP executor.
    For new code, use ContextAwareSuggestionEngine instead.
    """

    def __init__(self, preset_loader):
        """Initialize legacy suggestion engine."""
        self.preset_loader = preset_loader
        self.engine = ContextAwareSuggestionEngine()

    def suggest_workflows(self, context):
        """Suggest workflows based on context (legacy interface)."""
        suggestions = self.engine.get_suggestions(include_agents=False, include_actions=False)
        return suggestions.workflows

    def format_suggestions(self, suggestions):
        """Format suggestions for display (legacy interface)."""
        if not suggestions:
            return "No workflow suggestions available."
        
        lines = ["## Workflow Suggestions\n"]
        for i, suggestion in enumerate(suggestions[:5], 1):  # Top 5
            lines.append(f"{i}. **{suggestion.value}** ({suggestion.confidence:.0%} confidence)")
            lines.append(f"   {suggestion.explanation}\n")
        
        return "\n".join(lines)


class SuggestionType(Enum):
    """Type of suggestion."""

    WORKFLOW = "workflow"
    AGENT = "agent"
    ACTION = "action"


@dataclass
class Suggestion:
    """A single suggestion with ranking and explanation."""

    type: SuggestionType
    value: str  # Workflow name, agent name, or action description
    confidence: float  # 0.0 to 1.0
    explanation: str  # Why this suggestion
    context_matches: list[str] = field(default_factory=list)  # What context matched
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SuggestionSet:
    """A set of suggestions for a context."""

    workflows: list[Suggestion] = field(default_factory=list)
    agents: list[Suggestion] = field(default_factory=list)
    actions: list[Suggestion] = field(default_factory=list)
    context: ProjectContext | None = None
    project_profile: ProjectProfile | None = None


class ContextAwareSuggestionEngine:
    """
    Context-aware suggestion engine.

    Analyzes project context and provides intelligent suggestions for:
    - Workflows to use
    - Agents to employ
    - Actions to take
    """

    # Agent mapping based on task context
    AGENT_MAPPING = {
        "requirements": ["analyst", "po"],
        "design": ["architect", "ux-expert"],
        "implementation": ["dev"],
        "testing": ["qa"],
        "review": ["reviewer"],
        "documentation": ["documenter"],
        "planning": ["pm", "po"],
        "security": ["security"],
        "deployment": ["ops"],
    }

    # Action suggestions based on context
    ACTION_PATTERNS = {
        "new_feature": [
            "Run requirements analysis workflow",
            "Create feature branch",
            "Set up testing framework",
        ],
        "bug_fix": [
            "Run fix workflow",
            "Create test case for bug",
            "Review related code",
        ],
        "refactoring": [
            "Run full SDLC workflow",
            "Update documentation",
            "Run comprehensive tests",
        ],
        "documentation": [
            "Run documentation workflow",
            "Review existing docs",
            "Update API documentation",
        ],
    }

    def __init__(self, project_root: Path | None = None):
        """
        Initialize suggestion engine.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.context_analyzer = ContextAnalyzer(project_root)
        self.workflow_recommender = WorkflowRecommender(project_root)
        self.profile_detector = ProjectProfileDetector(project_root)
        self.learning_data_path = self.project_root / ".tapps-agents" / "suggestion_learning.json"
        self.learning_data: dict[str, Any] = self._load_learning_data()

    def get_suggestions(
        self,
        user_query: str | None = None,
        include_workflows: bool = True,
        include_agents: bool = True,
        include_actions: bool = True,
    ) -> SuggestionSet:
        """
        Get context-aware suggestions.

        Args:
            user_query: Optional user query for context
            include_workflows: Whether to include workflow suggestions
            include_agents: Whether to include agent suggestions
            include_actions: Whether to include action suggestions

        Returns:
            SuggestionSet with all suggestions
        """
        # Analyze context
        context = self.context_analyzer.analyze()
        
        # Get project profile
        try:
            project_profile = self.profile_detector.detect()
        except Exception as e:
            logger.warning(f"Failed to detect project profile: {e}")
            project_profile = None

        suggestions = SuggestionSet(context=context, project_profile=project_profile)

        # Get workflow suggestions
        if include_workflows:
            suggestions.workflows = self._suggest_workflows(context, user_query)

        # Get agent suggestions
        if include_agents:
            suggestions.agents = self._suggest_agents(context, user_query)

        # Get action suggestions
        if include_actions:
            suggestions.actions = self._suggest_actions(context, user_query)

        return suggestions

    def _suggest_workflows(
        self, context: ProjectContext, user_query: str | None = None
    ) -> list[Suggestion]:
        """Suggest workflows based on context."""
        suggestions = []

        try:
            # Use workflow recommender
            recommendation = self.workflow_recommender.recommend(user_query=user_query)
            
            if recommendation.workflow_file:
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.WORKFLOW,
                        value=recommendation.workflow_file,
                        confidence=recommendation.confidence,
                        explanation=recommendation.message,
                        context_matches=self._extract_context_matches(context, recommendation),
                        metadata={
                            "track": recommendation.track.value,
                            "characteristics": recommendation.characteristics.__dict__ if hasattr(recommendation.characteristics, '__dict__') else {},
                        },
                    )
                )

            # Add alternative workflows
            for alt_workflow in recommendation.alternative_workflows[:3]:  # Top 3 alternatives
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.WORKFLOW,
                        value=alt_workflow,
                        confidence=recommendation.confidence * 0.7,  # Lower confidence for alternatives
                        explanation=f"Alternative workflow: {alt_workflow}",
                        context_matches=[],
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to suggest workflows: {e}")

        # Apply learning-based ranking
        suggestions = self._apply_learning_ranking(suggestions, "workflow")

        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)

    def _suggest_agents(
        self, context: ProjectContext, user_query: str | None = None
    ) -> list[Suggestion]:
        """Suggest agents based on context."""
        suggestions = []

        # Analyze context to determine task type
        task_type = self._infer_task_type(context, user_query)

        # Get agents for task type
        agent_names = self.AGENT_MAPPING.get(task_type, ["dev"])

        for agent_name in agent_names:
            confidence = self._calculate_agent_confidence(agent_name, context, task_type)
            explanation = self._generate_agent_explanation(agent_name, task_type, context)

            suggestions.append(
                Suggestion(
                    type=SuggestionType.AGENT,
                    value=agent_name,
                    confidence=confidence,
                    explanation=explanation,
                    context_matches=[task_type] if task_type else [],
                    metadata={"task_type": task_type},
                )
            )

        # Apply learning-based ranking
        suggestions = self._apply_learning_ranking(suggestions, "agent")

        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)

    def _suggest_actions(
        self, context: ProjectContext, user_query: str | None = None
    ) -> list[Suggestion]:
        """Suggest actions based on context."""
        suggestions = []

        # Infer action context
        action_context = self._infer_action_context(context, user_query)

        # Get action patterns for context
        action_patterns = self.ACTION_PATTERNS.get(action_context, [])

        for action in action_patterns:
            confidence = self._calculate_action_confidence(action, context, action_context)
            explanation = self._generate_action_explanation(action, action_context, context)

            suggestions.append(
                Suggestion(
                    type=SuggestionType.ACTION,
                    value=action,
                    confidence=confidence,
                    explanation=explanation,
                    context_matches=[action_context] if action_context else [],
                    metadata={"action_context": action_context},
                )
            )

        # Apply learning-based ranking
        suggestions = self._apply_learning_ranking(suggestions, "action")

        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)

    def _infer_task_type(self, context: ProjectContext, user_query: str | None = None) -> str:
        """Infer task type from context."""
        if user_query:
            query_lower = user_query.lower()
            if any(word in query_lower for word in ["requirement", "analyze", "spec"]):
                return "requirements"
            if any(word in query_lower for word in ["design", "architecture", "structure"]):
                return "design"
            if any(word in query_lower for word in ["test", "testing", "qa"]):
                return "testing"
            if any(word in query_lower for word in ["review", "code review"]):
                return "review"
            if any(word in query_lower for word in ["document", "docs", "readme"]):
                return "documentation"
            if any(word in query_lower for word in ["plan", "planning", "roadmap"]):
                return "planning"
            if any(word in query_lower for word in ["security", "secure", "vulnerability"]):
                return "security"
            if any(word in query_lower for word in ["deploy", "deployment", "ops"]):
                return "deployment"

        # Infer from branch name
        if context.branch_name:
            branch_lower = context.branch_name.lower()
            if "feature" in branch_lower or "feat" in branch_lower:
                return "implementation"
            if "fix" in branch_lower or "bug" in branch_lower:
                return "testing"
            if "doc" in branch_lower:
                return "documentation"
            if "refactor" in branch_lower:
                return "implementation"

        # Infer from file changes
        if context.recent_changes:
            file_types = self._analyze_file_types(context.recent_changes)
            if file_types.get("test", 0) > 0:
                return "testing"
            if file_types.get("doc", 0) > 0:
                return "documentation"

        return "implementation"  # Default

    def _infer_action_context(self, context: ProjectContext, user_query: str | None = None) -> str:
        """Infer action context from project state."""
        if user_query:
            query_lower = user_query.lower()
            if any(word in query_lower for word in ["new", "feature", "add"]):
                return "new_feature"
            if any(word in query_lower for word in ["fix", "bug", "error"]):
                return "bug_fix"
            if any(word in query_lower for word in ["refactor", "restructure"]):
                return "refactoring"
            if any(word in query_lower for word in ["document", "docs"]):
                return "documentation"

        # Infer from branch name
        if context.branch_name:
            branch_lower = context.branch_name.lower()
            if "feature" in branch_lower:
                return "new_feature"
            if "fix" in branch_lower or "bug" in branch_lower:
                return "bug_fix"
            if "refactor" in branch_lower:
                return "refactoring"

        # Infer from file changes
        if context.modified_files_count > 20:
            return "refactoring"
        elif context.modified_files_count > 5:
            return "new_feature"
        else:
            return "bug_fix"

    def _analyze_file_types(self, files: list[str]) -> dict[str, int]:
        """Analyze file types in changed files."""
        types = {"test": 0, "doc": 0, "code": 0}
        for file in files:
            file_lower = file.lower()
            if "test" in file_lower or "spec" in file_lower:
                types["test"] += 1
            elif any(ext in file_lower for ext in [".md", ".txt", ".rst"]):
                types["doc"] += 1
            else:
                types["code"] += 1
        return types

    def _calculate_agent_confidence(
        self, agent_name: str, context: ProjectContext, task_type: str
    ) -> float:
        """Calculate confidence for agent suggestion."""
        base_confidence = 0.7

        # Boost confidence if agent matches task type
        if task_type in self.AGENT_MAPPING and agent_name in self.AGENT_MAPPING[task_type]:
            base_confidence += 0.2

        # Apply learning-based adjustments
        learning_boost = self._get_learning_boost(agent_name, "agent")
        base_confidence += learning_boost

        return min(1.0, max(0.0, base_confidence))

    def _calculate_action_confidence(
        self, action: str, context: ProjectContext, action_context: str
    ) -> float:
        """Calculate confidence for action suggestion."""
        base_confidence = 0.6

        # Boost confidence if action matches context
        if action_context in self.ACTION_PATTERNS and action in self.ACTION_PATTERNS[action_context]:
            base_confidence += 0.2

        # Apply learning-based adjustments
        learning_boost = self._get_learning_boost(action, "action")
        base_confidence += learning_boost

        return min(1.0, max(0.0, base_confidence))

    def _generate_agent_explanation(
        self, agent_name: str, task_type: str, context: ProjectContext
    ) -> str:
        """Generate explanation for agent suggestion."""
        explanations = {
            "analyst": "Best for requirements analysis and gathering",
            "architect": "Best for system design and architecture",
            "dev": "Best for implementation and coding tasks",
            "qa": "Best for testing and quality assurance",
            "reviewer": "Best for code review and quality gates",
            "documenter": "Best for documentation tasks",
            "pm": "Best for project planning and management",
            "po": "Best for product ownership and requirements",
        }
        base_explanation = explanations.get(agent_name, f"Recommended for {task_type} tasks")
        
        if context.branch_name:
            base_explanation += f" (current branch: {context.branch_name})"
        
        return base_explanation

    def _generate_action_explanation(
        self, action: str, action_context: str, context: ProjectContext
    ) -> str:
        """Generate explanation for action suggestion."""
        explanations = {
            "new_feature": "Starting a new feature - recommended workflow",
            "bug_fix": "Fixing a bug - quick workflow recommended",
            "refactoring": "Refactoring code - comprehensive workflow recommended",
            "documentation": "Documentation work - documentation workflow recommended",
        }
        base_explanation = explanations.get(action_context, "Recommended based on project context")
        
        if context.modified_files_count > 0:
            base_explanation += f" ({context.modified_files_count} files modified)"
        
        return base_explanation

    def _extract_context_matches(
        self, context: ProjectContext, recommendation: WorkflowRecommendation
    ) -> list[str]:
        """Extract context matches for explanation."""
        matches = []
        
        if context.branch_name:
            matches.append(f"Branch: {context.branch_name}")
        
        if context.project_type:
            matches.append(f"Project type: {context.project_type}")
        
        if context.modified_files_count > 0:
            matches.append(f"{context.modified_files_count} files modified")
        
        return matches

    def _apply_learning_ranking(
        self, suggestions: list[Suggestion], suggestion_type: str
    ) -> list[Suggestion]:
        """Apply learning-based ranking adjustments."""
        for suggestion in suggestions:
            learning_boost = self._get_learning_boost(suggestion.value, suggestion_type)
            suggestion.confidence = min(1.0, suggestion.confidence + learning_boost)
        
        return suggestions

    def _get_learning_boost(self, value: str, suggestion_type: str) -> float:
        """Get learning-based confidence boost."""
        if not self.learning_data:
            return 0.0

        key = f"{suggestion_type}:{value}"
        stats = self.learning_data.get(key, {})
        
        accepted = stats.get("accepted", 0)
        rejected = stats.get("rejected", 0)
        total = accepted + rejected

        if total == 0:
            return 0.0

        # Calculate acceptance rate boost (max 0.1 boost)
        acceptance_rate = accepted / total
        boost = (acceptance_rate - 0.5) * 0.2  # -0.1 to +0.1

        return boost

    def record_feedback(
        self, suggestion_type: SuggestionType, value: str, accepted: bool
    ) -> None:
        """
        Record user feedback on a suggestion.

        Args:
            suggestion_type: Type of suggestion
            value: Suggestion value
            accepted: Whether suggestion was accepted
        """
        key = f"{suggestion_type.value}:{value}"
        
        if key not in self.learning_data:
            self.learning_data[key] = {"accepted": 0, "rejected": 0, "last_updated": None}

        if accepted:
            self.learning_data[key]["accepted"] += 1
        else:
            self.learning_data[key]["rejected"] += 1

        self.learning_data[key]["last_updated"] = datetime.now().isoformat()

        self._save_learning_data()

    def _load_learning_data(self) -> dict[str, Any]:
        """Load learning data from disk."""
        if not self.learning_data_path.exists():
            return {}

        try:
            with open(self.learning_data_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load learning data: {e}")
            return {}

    def _save_learning_data(self) -> None:
        """Save learning data to disk."""
        try:
            self.learning_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learning_data_path, "w") as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save learning data: {e}")
