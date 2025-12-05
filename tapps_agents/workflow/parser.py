"""
Workflow Parser - Parse YAML workflow definitions.
"""

from typing import Dict, Any, List
from pathlib import Path
import yaml

from .models import (
    Workflow,
    WorkflowStep,
    WorkflowSettings,
    WorkflowType,
)


class WorkflowParser:
    """Parser for YAML workflow definitions."""
    
    @staticmethod
    def parse_file(file_path: Path) -> Workflow:
        """
        Parse a workflow YAML file.
        
        Args:
            file_path: Path to workflow YAML file
        
        Returns:
            Parsed Workflow object
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        
        return WorkflowParser.parse(content)
    
    @staticmethod
    def parse(content: Dict[str, Any]) -> Workflow:
        """
        Parse workflow content from dictionary.
        
        Args:
            content: Workflow YAML content as dictionary
        
        Returns:
            Parsed Workflow object
        """
        workflow_data = content.get("workflow", {})
        
        # Parse workflow metadata
        workflow_id = workflow_data.get("id")
        name = workflow_data.get("name", "")
        description = workflow_data.get("description", "")
        version = workflow_data.get("version", "1.0.0")
        
        # Parse workflow type
        workflow_type_str = workflow_data.get("type", "greenfield")
        try:
            workflow_type = WorkflowType(workflow_type_str.lower())
        except ValueError:
            workflow_type = WorkflowType.GREENFIELD
        
        # Parse settings
        settings_data = workflow_data.get("settings", {})
        settings = WorkflowSettings(
            quality_gates=settings_data.get("quality_gates", True),
            code_scoring=settings_data.get("code_scoring", True),
            context_tier_default=settings_data.get("context_tier_default", 2),
            auto_detect=settings_data.get("auto_detect", True)
        )
        
        # Parse steps
        steps_data = workflow_data.get("steps", [])
        steps = []
        for step_data in steps_data:
            step = WorkflowParser._parse_step(step_data)
            steps.append(step)
        
        # Parse metadata
        metadata = workflow_data.get("metadata", {})
        
        return Workflow(
            id=workflow_id,
            name=name,
            description=description,
            version=version,
            type=workflow_type,
            settings=settings,
            steps=steps,
            metadata=metadata
        )
    
    @staticmethod
    def _parse_step(step_data: Dict[str, Any]) -> WorkflowStep:
        """Parse a workflow step."""
        step_id = step_data.get("id")
        agent = step_data.get("agent")
        action = step_data.get("action")
        
        if not step_id or not agent or not action:
            raise ValueError("Step must have id, agent, and action")
        
        return WorkflowStep(
            id=step_id,
            agent=agent,
            action=action,
            context_tier=step_data.get("context_tier", 2),
            creates=step_data.get("creates", []),
            requires=step_data.get("requires", []),
            condition=step_data.get("condition", "required"),
            next=step_data.get("next"),
            gate=step_data.get("gate"),
            consults=step_data.get("consults", []),
            optional_steps=step_data.get("optional_steps", []),
            notes=step_data.get("notes"),
            repeats=step_data.get("repeats", False),
            scoring=step_data.get("scoring"),
            metadata=step_data.get("metadata", {})
        )

