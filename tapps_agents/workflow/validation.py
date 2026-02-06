"""
Workflow Validation Hooks

Provides validation hooks for SDLC phase validation during workflow execution.
Allows registering validators that check artifacts and state at key points.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .models import Artifact, WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    errors: list[str]
    warnings: list[str]
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata or {},
        }


class WorkflowValidator(ABC):
    """Abstract base class for workflow validators."""

    @abstractmethod
    def validate_requirements(
        self, artifacts: dict[str, Artifact], state: WorkflowState
    ) -> ValidationResult:
        """Validate requirements phase artifacts."""
        pass

    @abstractmethod
    def validate_architecture(
        self, artifacts: dict[str, Artifact], state: WorkflowState
    ) -> ValidationResult:
        """Validate architecture phase artifacts."""
        pass

    @abstractmethod
    def validate_implementation(
        self, artifacts: dict[str, Artifact], state: WorkflowState
    ) -> ValidationResult:
        """Validate implementation phase artifacts."""
        pass

    @abstractmethod
    def validate_quality_gate(
        self, step: WorkflowStep, scoring_result: dict[str, Any], state: WorkflowState
    ) -> ValidationResult:
        """Validate quality gate thresholds."""
        pass


class ValidatorRegistry:
    """Registry for managing validators per SDLC phase."""

    def __init__(self):
        """Initialize validator registry."""
        self._validators: dict[str, list[WorkflowValidator]] = {
            "requirements": [],
            "architecture": [],
            "implementation": [],
            "quality_gate": [],
        }

    def register(self, phase: str, validator: WorkflowValidator) -> None:
        """
        Register a validator for a specific phase.

        Args:
            phase: Phase name (requirements, architecture, implementation, quality_gate)
            validator: Validator instance to register
        """
        if phase not in self._validators:
            logger.warning(f"Unknown phase '{phase}', creating new phase registry")
            self._validators[phase] = []

        if validator not in self._validators[phase]:
            self._validators[phase].append(validator)
            logger.debug(f"Registered validator {validator.__class__.__name__} for phase {phase}")

    def unregister(self, phase: str, validator: WorkflowValidator) -> None:
        """
        Unregister a validator.

        Args:
            phase: Phase name
            validator: Validator instance to unregister
        """
        if phase in self._validators:
            self._validators[phase] = [
                v for v in self._validators[phase] if v is not validator
            ]
            logger.debug(f"Unregistered validator {validator.__class__.__name__} for phase {phase}")

    def validate(
        self,
        phase: str,
        artifacts: dict[str, Artifact] | None = None,
        state: WorkflowState | None = None,
        step: WorkflowStep | None = None,
        scoring_result: dict[str, Any] | None = None,
    ) -> list[ValidationResult]:
        """
        Run all validators for a phase.

        Args:
            phase: Phase name
            artifacts: Artifacts to validate (for requirements/architecture/implementation)
            state: Workflow state
            step: Workflow step (for quality_gate)
            scoring_result: Scoring result (for quality_gate)

        Returns:
            List of validation results from all validators
        """
        if phase not in self._validators:
            logger.warning(f"No validators registered for phase '{phase}'")
            return []

        results: list[ValidationResult] = []
        validators = list(self._validators[phase])  # Copy to avoid modification during iteration

        for validator in validators:
            try:
                if phase == "requirements":
                    if artifacts is None or state is None:
                        logger.warning("Missing artifacts or state for requirements validation")
                        continue
                    result = validator.validate_requirements(artifacts, state)
                elif phase == "architecture":
                    if artifacts is None or state is None:
                        logger.warning("Missing artifacts or state for architecture validation")
                        continue
                    result = validator.validate_architecture(artifacts, state)
                elif phase == "implementation":
                    if artifacts is None or state is None:
                        logger.warning("Missing artifacts or state for implementation validation")
                        continue
                    result = validator.validate_implementation(artifacts, state)
                elif phase == "quality_gate":
                    if step is None or scoring_result is None or state is None:
                        logger.warning("Missing step, scoring_result, or state for quality_gate validation")
                        continue
                    result = validator.validate_quality_gate(step, scoring_result, state)
                else:
                    logger.warning(f"Unknown phase '{phase}'")
                    continue

                results.append(result)

                # Log validation result
                if not result.passed:
                    logger.warning(
                        f"Validation failed for {validator.__class__.__name__} in phase {phase}",
                        extra={
                            "errors": result.errors,
                            "warnings": result.warnings,
                        },
                    )
                elif result.warnings:
                    logger.info(
                        f"Validation passed with warnings for {validator.__class__.__name__} in phase {phase}",
                        extra={"warnings": result.warnings},
                    )

            except Exception as e:
                # Don't let validator exceptions break workflow
                logger.error(
                    f"Validator {validator.__class__.__name__} raised exception: {e}",
                    exc_info=True,
                    extra={"phase": phase},
                )
                # Add error result
                results.append(
                    ValidationResult(
                        passed=False,
                        errors=[f"Validator exception: {e!s}"],
                        warnings=[],
                    )
                )

        return results

    def get_validators(self, phase: str) -> list[WorkflowValidator]:
        """Get all validators for a phase."""
        return list(self._validators.get(phase, []))

    def clear(self, phase: str | None = None) -> None:
        """
        Clear validators.

        Args:
            phase: If provided, clear only this phase. Otherwise clear all phases.
        """
        if phase:
            if phase in self._validators:
                self._validators[phase].clear()
        else:
            for phase_validators in self._validators.values():
                phase_validators.clear()

