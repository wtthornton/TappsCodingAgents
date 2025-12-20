"""
YAML Workflow Schema Validator

Validates workflow YAML against versioned schemas with cross-reference validation.
Epic 5 / Story 5.1: YAML Workflow Parser & Validator
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class SchemaVersion(str, Enum):
    """Supported workflow schema versions."""

    V1_0 = "1.0"
    V2_0 = "2.0"
    LATEST = V2_0


@dataclass
class ValidationError:
    """A validation error with context."""

    field: str
    message: str
    file_path: Path | None = None
    step_id: str | None = None

    def __str__(self) -> str:
        """Format error message with context."""
        parts = []
        if self.file_path:
            parts.append(str(self.file_path))
        if self.step_id:
            parts.append(f"step:{self.step_id}")
        prefix = ": ".join(parts) + (": " if parts else "")
        return f"{prefix}{self.field}: {self.message}"


class WorkflowSchemaValidator:
    """Validates workflow YAML against versioned schemas with strict enforcement."""

    SUPPORTED_VERSIONS = {SchemaVersion.V1_0.value, SchemaVersion.V2_0.value}

    # Allowed workflow-level fields (v2.0 schema)
    ALLOWED_WORKFLOW_FIELDS = {
        "id",
        "name",
        "description",
        "version",
        "type",
        "schema_version",
        "settings",
        "steps",
        "metadata",
        "auto_detect",  # Legacy: allowed at workflow level for backward compatibility
    }

    # Allowed settings fields
    ALLOWED_SETTINGS_FIELDS = {
        "quality_gates",
        "code_scoring",
        "context_tier_default",
        "auto_detect",
    }

    # Allowed step-level fields
    ALLOWED_STEP_FIELDS = {
        "id",
        "agent",
        "action",
        "context_tier",
        "creates",
        "requires",
        "consults",
        "condition",
        "next",
        "gate",
        "optional_steps",
        "notes",
        "repeats",
        "scoring",
        "metadata",
    }

    # Allowed gate fields
    ALLOWED_GATE_FIELDS = {
        "condition",
        "on_pass",
        "on_fail",
    }

    def __init__(self, schema_version: str | None = None, strict: bool = True):
        """
        Initialize schema validator.

        Args:
            schema_version: Schema version to validate against (defaults to latest)
            strict: If True, reject unknown fields (default: True)
        """
        if schema_version is None:
            schema_version = SchemaVersion.LATEST.value
        if schema_version not in self.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported schema version: {schema_version}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_VERSIONS))}"
            )
        self.schema_version = schema_version
        self.strict = strict

    def validate_workflow(
        self, workflow_data: dict[str, Any], file_path: Path | None = None
    ) -> list[ValidationError]:
        """
        Validate workflow structure against schema.

        Args:
            workflow_data: Parsed workflow YAML data
            file_path: Optional file path for error context

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[ValidationError] = []

        # Extract workflow data (handle wrapped format)
        is_wrapped = isinstance(workflow_data.get("workflow"), dict)
        workflow_content = (
            workflow_data.get("workflow") if is_wrapped else workflow_data
        )

        if not isinstance(workflow_content, dict):
            errors.append(
                ValidationError(
                    field="workflow",
                    message="Workflow must be an object/mapping",
                    file_path=file_path,
                )
            )
            return errors

        # Validate schema version if specified
        declared_version = workflow_content.get("schema_version")
        if declared_version is not None:
            if not isinstance(declared_version, str):
                errors.append(
                    ValidationError(
                        field="schema_version",
                        message="schema_version must be a string",
                        file_path=file_path,
                    )
                )
            elif declared_version not in self.SUPPORTED_VERSIONS:
                errors.append(
                    ValidationError(
                        field="schema_version",
                        message=(
                            f"Unsupported schema version: {declared_version}. "
                            f"Supported: {', '.join(sorted(self.SUPPORTED_VERSIONS))}"
                        ),
                        file_path=file_path,
                    )
                )

        # Validate required workflow fields
        if not isinstance(workflow_content.get("id"), str) or not workflow_content.get(
            "id"
        ).strip():
            errors.append(
                ValidationError(
                    field="id",
                    message="Workflow must have a non-empty string 'id'",
                    file_path=file_path,
                )
            )

        # Validate steps
        steps_data = workflow_content.get("steps", [])
        if not isinstance(steps_data, list):
            errors.append(
                ValidationError(
                    field="steps",
                    message="Workflow 'steps' must be a list",
                    file_path=file_path,
                )
            )
        else:
            step_ids: set[str] = set()
            for i, step_data in enumerate(steps_data):
                if not isinstance(step_data, dict):
                    errors.append(
                        ValidationError(
                            field=f"steps[{i}]",
                            message="Each step must be an object/mapping",
                            file_path=file_path,
                        )
                    )
                    continue

                step_id = step_data.get("id")
                step_errors = self._validate_step(step_data, file_path=file_path)
                errors.extend(step_errors)

                # Track step IDs for duplicate detection
                if isinstance(step_id, str):
                    if step_id in step_ids:
                        errors.append(
                            ValidationError(
                                field=f"steps[{i}].id",
                                message=f"Duplicate step id: {step_id}",
                                file_path=file_path,
                                step_id=step_id,
                            )
                        )
                    step_ids.add(step_id)

            # Validate cross-references
            if step_ids:
                ref_errors = self._validate_cross_references(
                    workflow_content, step_ids, file_path=file_path
                )
                errors.extend(ref_errors)

        # Strict schema enforcement: check for unknown workflow-level fields
        if self.strict:
            unknown_fields = self._check_unknown_fields(
                workflow_content,
                self.ALLOWED_WORKFLOW_FIELDS,
                "workflow",
                file_path=file_path,
            )
            errors.extend(unknown_fields)

            # Check settings fields
            settings_data = workflow_content.get("settings")
            if isinstance(settings_data, dict):
                settings_errors = self._check_unknown_fields(
                    settings_data,
                    self.ALLOWED_SETTINGS_FIELDS,
                    "settings",
                    file_path=file_path,
                )
                errors.extend(settings_errors)

        return errors

    def _validate_step(
        self, step_data: dict[str, Any], file_path: Path | None = None
    ) -> list[ValidationError]:
        """Validate a single workflow step."""
        errors: list[ValidationError] = []
        step_id = step_data.get("id", "<unknown>")

        # Required fields
        if not isinstance(step_data.get("id"), str) or not step_data.get("id").strip():
            errors.append(
                ValidationError(
                    field="id",
                    message="Step must have a non-empty string 'id'",
                    file_path=file_path,
                    step_id=step_id,
                )
            )
        if not isinstance(step_data.get("agent"), str) or not step_data.get(
            "agent"
        ).strip():
            errors.append(
                ValidationError(
                    field="agent",
                    message="Step must have a non-empty string 'agent'",
                    file_path=file_path,
                    step_id=step_id,
                )
            )
        if not isinstance(step_data.get("action"), str) or not step_data.get(
            "action"
        ).strip():
            errors.append(
                ValidationError(
                    field="action",
                    message="Step must have a non-empty string 'action'",
                    file_path=file_path,
                    step_id=step_id,
                )
            )

        # Validate list fields
        list_fields = ["creates", "requires", "consults", "optional_steps"]
        for field in list_fields:
            value = step_data.get(field)
            if value is not None:
                if not isinstance(value, list) or any(
                    not isinstance(v, str) for v in value
                ):
                    errors.append(
                        ValidationError(
                            field=field,
                            message=f"Step '{field}' must be a list of strings",
                            file_path=file_path,
                            step_id=step_id,
                        )
                    )

        # Validate context_tier
        context_tier = step_data.get("context_tier", 2)
        if not isinstance(context_tier, int):
            # Allow string format like "TIER2" or "2"
            if isinstance(context_tier, str):
                import re

                txt = context_tier.strip()
                m = re.match(r"(?i)^tier(\d+)$", txt)
                if not m and not txt.isdigit():
                    errors.append(
                        ValidationError(
                            field="context_tier",
                            message=(
                                "Step 'context_tier' must be an int or string "
                                "like 'TIER2' or '2'"
                            ),
                            file_path=file_path,
                            step_id=step_id,
                        )
                    )
            else:
                errors.append(
                    ValidationError(
                        field="context_tier",
                        message="Step 'context_tier' must be an int",
                        file_path=file_path,
                        step_id=step_id,
                    )
                )

        # Validate condition
        condition = step_data.get("condition", "required")
        valid_conditions = ["required", "optional", "conditional"]
        if condition not in valid_conditions:
            errors.append(
                ValidationError(
                    field="condition",
                    message=(
                        f"Step 'condition' must be one of: {', '.join(valid_conditions)}"
                    ),
                    file_path=file_path,
                    step_id=step_id,
                )
            )

        # Validate next
        next_step = step_data.get("next")
        if next_step is not None and not isinstance(next_step, str):
            errors.append(
                ValidationError(
                    field="next",
                    message="Step 'next' must be a string",
                    file_path=file_path,
                    step_id=step_id,
                )
            )

        # Validate gate
        gate = step_data.get("gate")
        if gate is not None:
            if not isinstance(gate, dict):
                errors.append(
                    ValidationError(
                        field="gate",
                        message="Step 'gate' must be an object/mapping",
                        file_path=file_path,
                        step_id=step_id,
                    )
                )
            else:
                # Validate gate routing targets (on_pass, on_fail)
                for routing_key in ["on_pass", "on_fail"]:
                    routing_value = gate.get(routing_key)
                    if routing_value is not None and not isinstance(
                        routing_value, str
                    ):
                        errors.append(
                            ValidationError(
                                field=f"gate.{routing_key}",
                                message=f"Gate '{routing_key}' must be a string (step id)",
                                file_path=file_path,
                                step_id=step_id,
                            )
                        )

        # Validate repeats
        repeats = step_data.get("repeats", False)
        if not isinstance(repeats, bool):
            errors.append(
                ValidationError(
                    field="repeats",
                    message="Step 'repeats' must be a boolean",
                    file_path=file_path,
                    step_id=step_id,
                )
            )

        # Strict schema enforcement: check for unknown step fields
        if self.strict:
            unknown_fields = self._check_unknown_fields(
                step_data,
                self.ALLOWED_STEP_FIELDS,
                "step",
                file_path=file_path,
                step_id=step_id,
            )
            errors.extend(unknown_fields)

            # Check gate fields
            gate = step_data.get("gate")
            if isinstance(gate, dict):
                gate_errors = self._check_unknown_fields(
                    gate,
                    self.ALLOWED_GATE_FIELDS,
                    "gate",
                    file_path=file_path,
                    step_id=step_id,
                )
                errors.extend(gate_errors)

        return errors

    def _validate_cross_references(
        self,
        workflow_data: dict[str, Any],
        step_ids: set[str],
        file_path: Path | None = None,
    ) -> list[ValidationError]:
        """Validate cross-references between steps."""
        errors: list[ValidationError] = []
        steps_data = workflow_data.get("steps", [])

        for step_data in steps_data:
            if not isinstance(step_data, dict):
                continue

            step_id = step_data.get("id")
            if not isinstance(step_id, str):
                continue

            # Validate 'next' reference
            next_step = step_data.get("next")
            if next_step and next_step not in step_ids:
                errors.append(
                    ValidationError(
                        field="next",
                        message=f"Step 'next' references unknown step id: {next_step}",
                        file_path=file_path,
                        step_id=step_id,
                    )
                )

            # Validate 'optional_steps' references
            optional_steps = step_data.get("optional_steps", [])
            if isinstance(optional_steps, list):
                for opt_step in optional_steps:
                    if isinstance(opt_step, str) and opt_step not in step_ids:
                        errors.append(
                            ValidationError(
                                field="optional_steps",
                                message=(
                                    f"Step 'optional_steps' references unknown step id: {opt_step}"
                                ),
                                file_path=file_path,
                                step_id=step_id,
                            )
                        )

            # Validate gate routing references
            # Allow special keywords: "next" (use step's next field), "retry" (retry current step)
            gate = step_data.get("gate")
            if isinstance(gate, dict):
                special_keywords = {"next", "retry"}
                for routing_key in ["on_pass", "on_fail"]:
                    routing_value = gate.get(routing_key)
                    if isinstance(routing_value, str) and routing_value not in step_ids and routing_value not in special_keywords:
                        errors.append(
                            ValidationError(
                                field=f"gate.{routing_key}",
                                message=(
                                    f"Gate '{routing_key}' references unknown step id: {routing_value}"
                                ),
                                file_path=file_path,
                                step_id=step_id,
                            )
                        )

        return errors

    def _check_unknown_fields(
        self,
        data: dict[str, Any],
        allowed_fields: set[str],
        context: str,
        file_path: Path | None = None,
        step_id: str | None = None,
    ) -> list[ValidationError]:
        """Check for unknown/unsupported fields in strict mode."""
        errors: list[ValidationError] = []
        if not self.strict:
            return errors

        for field_name in data.keys():
            if field_name not in allowed_fields:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=(
                            f"Unknown {context} field '{field_name}'. "
                            f"Allowed fields: {', '.join(sorted(allowed_fields))}"
                        ),
                        file_path=file_path,
                        step_id=step_id,
                    )
                )
        return errors
