"""
Workflow Parser - Parse YAML workflow definitions.
"""

# @ai-prime-directive: This file implements the YAML workflow parser with strict schema validation.
# The parser supports both wrapped ({workflow: {...}}) and legacy ({id: ..., steps: [...]}) formats
# and enforces schema compliance per ADR-004. This is critical infrastructure for the YAML-first workflow architecture.

# @ai-constraints:
# - Must support both wrapped and legacy workflow formats for backward compatibility
# - Schema validation must occur before workflow object construction
# - Step validation must check required fields (id, agent, instruction) before schema validation
# - Error messages must include file path and step ID for debugging
# - Performance: Parsing should complete in <100ms for typical workflows

# @note[2025-03-15]: YAML-first workflow architecture per ADR-004.
# The parser enforces strict schema compliance while maintaining backward compatibility.
# See docs/architecture/decisions/ADR-004-yaml-first-workflows.md

import re
from pathlib import Path
from typing import Any

import yaml

from .models import (
    Workflow,
    WorkflowSettings,
    WorkflowStep,
    WorkflowType,
)
from .schema_validator import SchemaVersion, WorkflowSchemaValidator


class WorkflowParser:
    """Parser for YAML workflow definitions."""

    @staticmethod
    def _err_prefix(file_path: Path | None = None, step_id: str | None = None) -> str:
        parts: list[str] = []
        if file_path:
            parts.append(str(file_path))
        if step_id:
            parts.append(f"step:{step_id}")
        return ": ".join(parts) + (": " if parts else "")

    @staticmethod
    def parse_file(file_path: Path) -> Workflow:
        """
        Parse a workflow YAML file.

        Args:
            file_path: Path to workflow YAML file

        Returns:
            Parsed Workflow object
        """
        with open(file_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)

        return WorkflowParser.parse(content, file_path=file_path)

    @staticmethod
    def parse(content: Any, file_path: Path | None = None) -> Workflow:
        """
        Parse workflow content from dictionary.

        Args:
            content: Workflow YAML content as dictionary

        Returns:
            Parsed Workflow object
        """
        if not isinstance(content, dict):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow file must parse to a mapping/object"
            )

        # Support both:
        # 1) New schema: {"workflow": {...}}
        # 2) Legacy/utility schema: {"id": "...", "steps": [...], ...}
        is_wrapped = isinstance(content.get("workflow"), dict)
        workflow_data: dict[str, Any] | None = content.get("workflow") if is_wrapped else None
        if not workflow_data:
            if isinstance(content.get("id"), str) and isinstance(content.get("steps"), list):
                workflow_data = content  # legacy/utility format
                is_wrapped = False
            else:
                raise ValueError(
                    f"{WorkflowParser._err_prefix(file_path)}Missing required top-level key 'workflow'"
                )

        # Quick validation of required step fields before schema validation
        # This ensures we get the expected error message format for missing required fields
        steps_data = workflow_data.get("steps", [])
        if isinstance(steps_data, list):
            for step_data in steps_data:
                if isinstance(step_data, dict):
                    step_id = step_data.get("id", "<unknown>")
                    agent = step_data.get("agent")
                    action = step_data.get("action")
                    
                    # Check required fields and raise with expected message format
                    if not isinstance(step_data.get("id"), str) or not step_data.get("id", "").strip():
                        raise ValueError(
                            f"{WorkflowParser._err_prefix(file_path)}Step must have id, agent, and action"
                        )
                    if not isinstance(agent, str) or not agent.strip():
                        raise ValueError(
                            f"{WorkflowParser._err_prefix(file_path, step_id)}Step must have id, agent, and action"
                        )
                    if not isinstance(action, str) or not action.strip():
                        raise ValueError(
                            f"{WorkflowParser._err_prefix(file_path, step_id)}Step must have id, agent, and action"
                        )

        # Determine schema version for validation
        schema_version = workflow_data.get("schema_version")
        if schema_version is None:
            schema_version = SchemaVersion.LATEST.value
        elif not isinstance(schema_version, str):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}schema_version must be a string"
            )

        # Validate against schema (strict mode enabled by default)
        validator = WorkflowSchemaValidator(schema_version=schema_version, strict=True)
        validation_errors = validator.validate_workflow(content, file_path=file_path)
        if validation_errors:
            error_messages = [str(err) for err in validation_errors]
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Schema validation failed:\n"
                + "\n".join(f"  - {msg}" for msg in error_messages)
            )

        # Parse workflow metadata
        workflow_id = workflow_data.get("id")
        if not isinstance(workflow_id, str) or not workflow_id.strip():
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow must have a non-empty string 'id'"
            )

        name = workflow_data.get("name", "")
        if name is None:
            name = ""
        if not isinstance(name, str):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow 'name' must be a string"
            )

        description = workflow_data.get("description", "")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow 'description' must be a string"
            )

        version = workflow_data.get("version", "1.0.0")
        if not isinstance(version, str) or not version.strip():
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow 'version' must be a non-empty string"
            )

        # Parse workflow type
        workflow_type_raw = workflow_data.get("type", None)
        if workflow_type_raw is None:
            workflow_type = WorkflowType.GREENFIELD
        else:
            if not isinstance(workflow_type_raw, str):
                raise ValueError(
                    f"{WorkflowParser._err_prefix(file_path)}Workflow 'type' must be a string"
                )
            try:
                workflow_type = WorkflowType(workflow_type_raw.lower())
            except ValueError as e:
                if is_wrapped:
                    allowed = ", ".join([t.value for t in WorkflowType])
                    raise ValueError(
                        f"{WorkflowParser._err_prefix(file_path)}Invalid workflow type '{workflow_type_raw}'. "
                        f"Allowed: {allowed}"
                    ) from e
                # Legacy/utility workflows may use non-standard types (e.g., "utility").
                workflow_type = WorkflowType.GREENFIELD

        # Parse settings
        settings_data = workflow_data.get("settings", {})
        if settings_data is None:
            settings_data = {}
        if not isinstance(settings_data, dict):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow 'settings' must be an object/mapping"
            )
        # Support auto_detect at workflow level (legacy) or in settings
        auto_detect = workflow_data.get("auto_detect")
        if auto_detect is None:
            auto_detect = settings_data.get("auto_detect", True)
        settings = WorkflowSettings(
            quality_gates=settings_data.get("quality_gates", True),
            code_scoring=settings_data.get("code_scoring", True),
            context_tier_default=settings_data.get("context_tier_default", 2),
            auto_detect=auto_detect if isinstance(auto_detect, bool) else True,
        )

        # Parse steps
        steps_data = workflow_data.get("steps", [])
        if steps_data is None:
            steps_data = []
        if not isinstance(steps_data, list):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow 'steps' must be a list"
            )

        steps: list[WorkflowStep] = []
        for step_data in steps_data:
            step = WorkflowParser._parse_step(step_data, file_path=file_path)
            steps.append(step)

        # Parse metadata
        metadata = workflow_data.get("metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Workflow 'metadata' must be an object/mapping"
            )
        if (not is_wrapped) and isinstance(workflow_type_raw, str):
            metadata.setdefault("raw_type", workflow_type_raw)

        WorkflowParser._validate_references(steps=steps, file_path=file_path)

        return Workflow(
            id=workflow_id,
            name=name,
            description=description,
            version=version,
            type=workflow_type,
            settings=settings,
            steps=steps,
            metadata=metadata,
        )

    @staticmethod
    def _validate_str_list(
        value: Any, *, field: str, file_path: Path | None, step_id: str
    ) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path, step_id)}Step '{field}' must be a list of strings"
            )
        return value

    @staticmethod
    def _parse_step(step_data: Any, file_path: Path | None = None) -> WorkflowStep:
        """Parse a workflow step."""
        if not isinstance(step_data, dict):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Each step must be an object/mapping"
            )

        step_id = step_data.get("id")
        agent = step_data.get("agent")
        action = step_data.get("action")

        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Step must have id, agent, and action"
            )
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path, step_id)}Step must have id, agent, and action"
            )
        if not isinstance(action, str) or not action.strip():
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path, step_id)}Step must have id, agent, and action"
            )

        context_tier = step_data.get("context_tier", 2)
        if isinstance(context_tier, str):
            txt = context_tier.strip()
            m = re.match(r"(?i)^tier(\d+)$", txt)
            if m:
                context_tier = int(m.group(1))
            elif txt.isdigit():
                context_tier = int(txt)
        if not isinstance(context_tier, int):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path, step_id)}Step 'context_tier' must be an int (or 'TIER<n>')"
            )

        creates = WorkflowParser._validate_str_list(
            step_data.get("creates", []), field="creates", file_path=file_path, step_id=step_id
        )
        requires = WorkflowParser._validate_str_list(
            step_data.get("requires", []), field="requires", file_path=file_path, step_id=step_id
        )
        consults = WorkflowParser._validate_str_list(
            step_data.get("consults", []), field="consults", file_path=file_path, step_id=step_id
        )
        optional_steps = WorkflowParser._validate_str_list(
            step_data.get("optional_steps", []),
            field="optional_steps",
            file_path=file_path,
            step_id=step_id,
        )

        next_step = step_data.get("next")
        if next_step is not None and not isinstance(next_step, str):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path, step_id)}Step 'next' must be a string"
            )

        gate = step_data.get("gate")
        if gate is not None and not isinstance(gate, dict):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path, step_id)}Step 'gate' must be an object/mapping"
            )

        return WorkflowStep(
            id=step_id,
            agent=agent,
            action=action,
            context_tier=context_tier,
            creates=creates,
            requires=requires,
            condition=step_data.get("condition", "required"),
            next=next_step,
            gate=gate,
            consults=consults,
            optional_steps=optional_steps,
            notes=step_data.get("notes"),
            repeats=step_data.get("repeats", False),
            scoring=step_data.get("scoring"),
            metadata=step_data.get("metadata", {}),
        )

    @staticmethod
    def _validate_references(steps: list[WorkflowStep], file_path: Path | None) -> None:
        step_ids = [s.id for s in steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                f"{WorkflowParser._err_prefix(file_path)}Duplicate step ids are not allowed"
            )

        step_id_set = set(step_ids)
        for s in steps:
            if s.next and s.next not in step_id_set:
                raise ValueError(
                    f"{WorkflowParser._err_prefix(file_path, s.id)}Step 'next' references unknown step id: {s.next}"
                )
            for opt in (s.optional_steps or []):
                if opt not in step_id_set:
                    raise ValueError(
                        f"{WorkflowParser._err_prefix(file_path, s.id)}Step 'optional_steps' references unknown step id: {opt}"
                    )
