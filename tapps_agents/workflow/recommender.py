"""
Workflow Recommender - Recommend appropriate workflows based on project characteristics.

Phase 5.2: Enhanced with preset alias support, YAML validation, and caching
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

from .detector import ProjectCharacteristics, ProjectDetector, WorkflowTrack
from .models import Workflow
from .parser import WorkflowParser

logger = logging.getLogger(__name__)


@dataclass
class WorkflowRecommendation:
    """Workflow recommendation result."""

    workflow_file: str | None
    workflow: Workflow | None
    track: WorkflowTrack
    confidence: float
    characteristics: ProjectCharacteristics
    alternative_workflows: list[str]
    message: str


class WorkflowRecommender:
    """
    Recommend workflows based on project detection.

    Phase 5.2: Enhanced with preset alias support, YAML validation, and caching
    """

    def __init__(
        self, project_root: Path | None = None, workflows_dir: Path | None = None
    ):
        """
        Initialize workflow recommender.

        Args:
            project_root: Root directory of the project
            workflows_dir: Directory containing workflow YAML files
        """
        self.project_root = project_root or Path.cwd()
        self.workflows_dir = workflows_dir or (self.project_root / "workflows")
        self.detector = ProjectDetector(project_root)
        
        # Phase 5.2: Cache for workflow file parsing
        self._workflow_cache: dict[str, tuple[Workflow | None, str | None]] = {}
        # Cache format: {workflow_name: (parsed_workflow, error_message)}

    def recommend(
        self,
        user_query: str | None = None,
        file_count: int | None = None,
        scope_description: str | None = None,
        auto_load: bool = True,
    ) -> WorkflowRecommendation:
        """
        Recommend a workflow based on project characteristics.

        Args:
            user_query: User's query or request (for fix-workflow detection)
            file_count: Estimated number of files to change
            scope_description: Description of the change scope
            auto_load: Whether to automatically load the recommended workflow

        Returns:
            WorkflowRecommendation with recommendation details
        """
        # Detect project characteristics
        if user_query or file_count or scope_description:
            characteristics = self.detector.detect_from_context(
                user_query=user_query,
                file_count=file_count,
                scope_description=scope_description,
            )
        else:
            characteristics = self.detector.detect()

        # Get recommended workflow file
        workflow_file = self.detector.get_recommended_workflow(characteristics)

        # Find available workflows
        available_workflows = self._find_available_workflows()

        # Check if workflow file exists (separate from loading)
        workflow_exists = False
        workflow_path = None
        if workflow_file:
            # Check main workflows directory
            workflow_path = self.workflows_dir / f"{workflow_file}.yaml"
            workflow_exists = workflow_path.exists()
            
            # Also check presets directory
            if not workflow_exists:
                presets_path = self.workflows_dir / "presets" / f"{workflow_file}.yaml"
                workflow_exists = presets_path.exists()
                if workflow_exists:
                    workflow_path = presets_path

        # Load workflow if requested and found (Phase 5.2: Use cached workflow if available)
        workflow = None
        if auto_load and workflow_file and workflow_exists and workflow_path:
            # Check cache first
            workflow_name = workflow_path.stem
            if workflow_name in self._workflow_cache:
                cached_workflow, cached_error = self._workflow_cache[workflow_name]
                if cached_error is None and cached_workflow is not None:
                    workflow = cached_workflow
                else:
                    # Cached error, skip this workflow
                    logger.warning(f"Using cached validation result: {workflow_name} is invalid: {cached_error}")
            else:
                # Not in cache, parse and validate
                try:
                    workflow = WorkflowParser.parse_file(workflow_path)
                    # Cache successful parse
                    self._workflow_cache[workflow_name] = (workflow, None)
                except Exception as e:
                    error_msg = f"Failed to parse workflow {workflow_path}: {e}"
                    logger.warning(error_msg)
                    # Cache error
                    self._workflow_cache[workflow_name] = (None, error_msg)
                    # If recommended workflow doesn't exist or fails, try to find a similar one
                    workflow_file = self._find_best_match(
                        workflow_file, available_workflows
                    )
                    if workflow_file:
                        # Check both directories for best match
                        workflow_path = self.workflows_dir / f"{workflow_file}.yaml"
                        if not workflow_path.exists():
                            workflow_path = self.workflows_dir / "presets" / f"{workflow_file}.yaml"
                        if workflow_path.exists():
                            best_match_name = workflow_path.stem
                            # Check cache for best match
                            if best_match_name in self._workflow_cache:
                                cached_workflow, cached_error = self._workflow_cache[best_match_name]
                                if cached_error is None and cached_workflow is not None:
                                    workflow = cached_workflow
                            else:
                                try:
                                    workflow = WorkflowParser.parse_file(workflow_path)
                                    # Cache successful parse
                                    self._workflow_cache[best_match_name] = (workflow, None)
                                except Exception as e:
                                    error_msg = f"Failed to parse best match workflow {workflow_path}: {e}"
                                    logger.warning(error_msg)
                                    self._workflow_cache[best_match_name] = (None, error_msg)

        # Get alternative workflows
        alternative_workflows = [w for w in available_workflows if w != workflow_file]

        # Generate recommendation message
        message = self._generate_message(
            characteristics, workflow_file, workflow_exists
        )

        return WorkflowRecommendation(
            workflow_file=workflow_file,
            workflow=workflow,
            track=characteristics.workflow_track,
            confidence=characteristics.confidence,
            characteristics=characteristics,
            alternative_workflows=alternative_workflows,
            message=message,
        )

    def _find_available_workflows(self) -> list[str]:
        """
        Find all available workflow files in workflows/ and workflows/presets/.
        
        Phase 5.2: Enhanced with YAML validation
        """
        workflows = []
        
        # Check main workflows directory
        if self.workflows_dir.exists():
            for workflow_file in self.workflows_dir.glob("*.yaml"):
                if self._validate_workflow_file(workflow_file):
                    workflows.append(workflow_file.stem)
        
        # Check presets subdirectory
        presets_dir = self.workflows_dir / "presets"
        if presets_dir.exists():
            for workflow_file in presets_dir.glob("*.yaml"):
                if workflow_file.stem not in workflows:  # Avoid duplicates
                    if self._validate_workflow_file(workflow_file):
                        workflows.append(workflow_file.stem)
        
        return workflows
    
    def _validate_workflow_file(self, workflow_file: Path) -> bool:
        """
        Validate a workflow YAML file.
        
        Phase 5.2: YAML Validation
        
        Args:
            workflow_file: Path to workflow YAML file
            
        Returns:
            True if file is valid, False otherwise
        """
        # Check cache first
        workflow_name = workflow_file.stem
        if workflow_name in self._workflow_cache:
            cached_workflow, cached_error = self._workflow_cache[workflow_name]
            if cached_error is None:
                return True  # Valid and cached
            return False  # Invalid and cached
        
        try:
            # Basic YAML validation (check if file can be parsed as YAML)
            with open(workflow_file, encoding="utf-8") as f:
                content = yaml.safe_load(f)
            
            if not isinstance(content, dict):
                error_msg = f"Workflow file must parse to a mapping/object: {workflow_file}"
                logger.warning(error_msg)
                self._workflow_cache[workflow_name] = (None, error_msg)
                return False
            
            # Try to parse workflow (this also validates schema via WorkflowParser)
            try:
                workflow = WorkflowParser.parse_file(workflow_file)
                # Cache successful parse
                self._workflow_cache[workflow_name] = (workflow, None)
                return True
            except Exception as parse_error:
                error_msg = f"Workflow parsing failed for {workflow_file}: {parse_error}"
                logger.warning(error_msg)
                self._workflow_cache[workflow_name] = (None, error_msg)
                return False
                
        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML in {workflow_file}: {e}"
            logger.warning(error_msg)
            self._workflow_cache[workflow_name] = (None, error_msg)
            return False
        except Exception as e:
            error_msg = f"Error validating workflow file {workflow_file}: {e}"
            logger.warning(error_msg)
            self._workflow_cache[workflow_name] = (None, error_msg)
            return False

    def _find_best_match(self, preferred: str, available: list[str]) -> str | None:
        """
        Find best matching workflow from available workflows, including preset aliases.
        
        Phase 5.2: Enhanced preset alias support
        """
        if not available:
            return None

        # Try exact match first
        if preferred in available:
            return preferred

        # Check preset aliases if no match found (Phase 5.2: Better alias support)
        try:
            from .preset_loader import PRESET_ALIASES
            
            # Normalize preferred to lowercase for case-insensitive matching
            preferred_lower = preferred.lower()
            
            # Check if preferred is an alias (case-insensitive)
            for alias, preset_name in PRESET_ALIASES.items():
                if alias.lower() == preferred_lower:
                    if preset_name in available:
                        return preset_name
            
            # Reverse lookup: check if any available workflow has preferred as alias
            for workflow in available:
                if workflow in PRESET_ALIASES.values():
                    # Find aliases for this workflow
                    aliases = [k for k, v in PRESET_ALIASES.items() if v == workflow]
                    if any(alias.lower() == preferred_lower for alias in aliases):
                        return workflow
        except ImportError:
            # If preset_loader not available, continue with normal matching
            logger.warning("preset_loader not available, alias matching disabled")
            pass

        # Try partial match
        preferred_lower = preferred.lower()
        for workflow in available:
            if (
                preferred_lower in workflow.lower()
                or workflow.lower() in preferred_lower
            ):
                return workflow

        # Return first available as fallback
        return available[0] if available else None

    def _generate_message(
        self,
        characteristics: ProjectCharacteristics,
        workflow_file: str | None,
        workflow_exists: bool,
    ) -> str:
        """Generate human-readable recommendation message."""
        track_emojis = {
            WorkflowTrack.QUICK_FLOW: "⚡",
            WorkflowTrack.BMAD_METHOD: "📋",
            WorkflowTrack.ENTERPRISE: "🏢",
        }

        track_names = {
            WorkflowTrack.QUICK_FLOW: "Quick Flow",
            WorkflowTrack.BMAD_METHOD: "BMad Method",
            WorkflowTrack.ENTERPRISE: "Enterprise",
        }

        emoji = track_emojis.get(characteristics.workflow_track, "📋")
        track_name = track_names.get(characteristics.workflow_track, "BMad Method")

        parts = [
            f"{emoji} **{track_name}** workflow recommended",
            f"Confidence: {characteristics.confidence:.0%}",
            f"Project Type: {characteristics.project_type.value}",
        ]

        if workflow_file:
            if workflow_exists:
                parts.append(f"✅ Recommended: `{workflow_file}.yaml` (found)")
            else:
                parts.append(f"⚠️ Recommended: `{workflow_file}.yaml` (not found)")

        if characteristics.recommendations:
            parts.append("\nRecommendations:")
            for rec in characteristics.recommendations:
                parts.append(f"  • {rec}")

        return "\n".join(parts)

    def _check_workflow_validity(self, workflow_path: Path) -> tuple[bool, str | None]:
        """
        Check if workflow file is valid.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not workflow_path.exists():
            return False, "File does not exist"
        
        try:
            WorkflowParser.parse_file(workflow_path)
            return True, None
        except Exception as e:
            return False, f"Invalid workflow file: {str(e)}"

    def list_available_workflows(self) -> list[dict[str, str]]:
        """
        List all available workflows with metadata.

        Returns:
            List of workflow information dictionaries
        """
        workflows = []
        for workflow_file in self.workflows_dir.glob("*.yaml"):
            try:
                workflow = WorkflowParser.parse_file(workflow_file)
                workflows.append(
                    {
                        "file": workflow_file.name,
                        "id": workflow.id,
                        "name": workflow.name,
                        "type": workflow.type.value,
                        "description": workflow.description,
                    }
                )
            except Exception:
                # Skip invalid workflows
                logger.debug(
                    "Skipping invalid workflow file %s", workflow_file, exc_info=True
                )
                continue  # nosec B112 - best-effort listing
        return workflows
