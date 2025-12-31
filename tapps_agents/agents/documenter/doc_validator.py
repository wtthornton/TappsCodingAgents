"""
Documentation Validator - Validates documentation completeness and consistency.

This module validates that all project documentation is updated when new agents
are added to the framework.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Documentation validation result."""

    readme_valid: bool = False
    api_valid: bool = False
    architecture_valid: bool = False
    capabilities_valid: bool = False
    consistency_valid: bool = False
    agent_count: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if all documentation is complete."""
        return (
            self.readme_valid
            and self.api_valid
            and self.architecture_valid
            and self.capabilities_valid
            and self.consistency_valid
        )


@dataclass
class ConsistencyResult:
    """Agent count consistency check result."""

    is_consistent: bool = False
    counts: dict[str, int] = field(default_factory=dict)
    discrepancies: list[str] = field(default_factory=list)


class DocValidator:
    """Validate documentation completeness and consistency."""

    def __init__(self, project_root: Path):
        """
        Initialize documentation validator.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.readme_path = project_root / "README.md"
        self.api_path = project_root / "docs" / "API.md"
        self.arch_path = project_root / "docs" / "ARCHITECTURE.md"
        self.capabilities_path = (
            project_root / ".cursor" / "rules" / "agent-capabilities.mdc"
        )

    def validate_completeness(self, agent_name: str) -> ValidationResult:
        """
        Validate all documentation is complete for an agent.

        Args:
            agent_name: Agent name to validate

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult()

        # Validate each documentation file
        result.readme_valid = self.validate_readme(agent_name)
        result.api_valid = self.validate_api_docs(agent_name)
        result.architecture_valid = self.validate_architecture_docs(agent_name)
        result.capabilities_valid = self.validate_agent_capabilities(agent_name)

        # Check consistency
        consistency = self.check_consistency()
        result.consistency_valid = consistency.is_consistent
        result.agent_count = consistency.counts

        # Collect errors and warnings
        if not result.readme_valid:
            result.errors.append(f"README.md does not mention {agent_name}")
        if not result.api_valid:
            result.errors.append(f"API.md does not document {agent_name}")
        if not result.architecture_valid:
            result.errors.append(f"ARCHITECTURE.md does not include {agent_name}")
        if not result.capabilities_valid:
            result.errors.append(
                f"agent-capabilities.mdc does not have {agent_name} section"
            )
        if not result.consistency_valid:
            result.warnings.append(
                f"Agent count inconsistency: {consistency.discrepancies}"
            )

        return result

    def validate_readme(
        self, agent_name: str, readme_path: Path | None = None
    ) -> bool:
        """
        Check README.md mentions agent.

        Args:
            agent_name: Agent name to check
            readme_path: README.md path (default: self.readme_path)

        Returns:
            True if agent is mentioned in README.md
        """
        if readme_path is None:
            readme_path = self.readme_path

        if not readme_path.exists():
            logger.warning(f"README.md not found: {readme_path}")
            return False

        try:
            content = readme_path.read_text(encoding="utf-8")
            # Check for agent name in various patterns
            patterns = [
                rf"`@{agent_name}`",  # @agent_name
                rf"\b{agent_name}\b",  # Word boundary
            ]
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
        except Exception as e:
            logger.error(f"Failed to validate README.md: {e}")
            return False

    def validate_api_docs(
        self, agent_name: str, api_path: Path | None = None
    ) -> bool:
        """
        Check API.md documents agent.

        Args:
            agent_name: Agent name to check
            api_path: API.md path (default: self.api_path)

        Returns:
            True if agent is documented in API.md
        """
        if api_path is None:
            api_path = self.api_path

        if not api_path.exists():
            logger.warning(f"API.md not found: {api_path}")
            return False

        try:
            content = api_path.read_text(encoding="utf-8")
            # Check for agent name in subcommands and API section
            patterns = [
                rf"- `{agent_name}`",  # Subcommand
                rf"## {agent_name.title()} Agent",  # API section
                rf"\b{agent_name}\b",  # Word boundary
            ]
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
        except Exception as e:
            logger.error(f"Failed to validate API.md: {e}")
            return False

    def validate_architecture_docs(
        self, agent_name: str, arch_path: Path | None = None
    ) -> bool:
        """
        Check ARCHITECTURE.md includes agent.

        Args:
            agent_name: Agent name to check
            arch_path: ARCHITECTURE.md path (default: self.arch_path)

        Returns:
            True if agent is included in ARCHITECTURE.md
        """
        if arch_path is None:
            arch_path = self.arch_path

        if not arch_path.exists():
            logger.warning(f"ARCHITECTURE.md not found: {arch_path}")
            return False

        try:
            content = arch_path.read_text(encoding="utf-8")
            # Check for agent name in agent list
            patterns = [
                rf"\*\*{agent_name.title()} Agent\*\*",  # **AgentName Agent**
                rf"\b{agent_name}\b",  # Word boundary
            ]
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
        except Exception as e:
            logger.error(f"Failed to validate ARCHITECTURE.md: {e}")
            return False

    def validate_agent_capabilities(
        self, agent_name: str, capabilities_path: Path | None = None
    ) -> bool:
        """
        Check agent-capabilities.mdc has agent section.

        Args:
            agent_name: Agent name to check
            capabilities_path: agent-capabilities.mdc path (default: self.capabilities_path)

        Returns:
            True if agent section exists in agent-capabilities.mdc
        """
        if capabilities_path is None:
            capabilities_path = self.capabilities_path

        if not capabilities_path.exists():
            logger.warning(f"agent-capabilities.mdc not found: {capabilities_path}")
            return False

        try:
            content = capabilities_path.read_text(encoding="utf-8")
            # Check for agent section heading
            pattern = rf"### {agent_name.title()} Agent"
            return bool(re.search(pattern, content))
        except Exception as e:
            logger.error(f"Failed to validate agent-capabilities.mdc: {e}")
            return False

    def check_consistency(self) -> ConsistencyResult:
        """
        Check agent count consistency across all documentation.

        Returns:
            ConsistencyResult with consistency status
        """
        result = ConsistencyResult()

        # Extract agent counts from each documentation file
        counts = {}

        # README.md
        if self.readme_path.exists():
            try:
                content = self.readme_path.read_text(encoding="utf-8")
                match = re.search(
                    r"- \*\*Workflow Agents\*\* \((\d+)\):", content
                )
                if match:
                    counts["README.md"] = int(match.group(1))
            except Exception as e:
                logger.debug(f"Failed to extract count from README.md: {e}")

        # Count agents in API.md subcommands
        if self.api_path.exists():
            try:
                content = self.api_path.read_text(encoding="utf-8")
                # Count subcommands
                subcommand_matches = re.findall(
                    r"- `(\w+)` -", content
                )
                # Filter to only agent subcommands (exclude workflow, simple-mode, etc.)
                agent_subcommands = [
                    m
                    for m in subcommand_matches
                    if m
                    not in [
                        "workflow",
                        "simple-mode",
                        "cursor",
                        "doctor",
                        "score",
                        "init",
                        "create",
                    ]
                ]
                counts["API.md"] = len(agent_subcommands)
            except Exception as e:
                logger.debug(f"Failed to extract count from API.md: {e}")

        # Count agents in ARCHITECTURE.md
        if self.arch_path.exists():
            try:
                content = self.arch_path.read_text(encoding="utf-8")
                agent_matches = re.findall(
                    r"- \*\*(\w+) Agent\*\*", content
                )
                counts["ARCHITECTURE.md"] = len(agent_matches)
            except Exception as e:
                logger.debug(f"Failed to extract count from ARCHITECTURE.md: {e}")

        # Count agents in agent-capabilities.mdc
        if self.capabilities_path.exists():
            try:
                content = self.capabilities_path.read_text(encoding="utf-8")
                agent_matches = re.findall(
                    r"### (\w+) Agent", content
                )
                counts["agent-capabilities.mdc"] = len(agent_matches)
            except Exception as e:
                logger.debug(
                    f"Failed to extract count from agent-capabilities.mdc: {e}"
                )

        result.counts = counts

        # Check consistency
        if len(counts) < 2:
            result.is_consistent = False
            result.discrepancies.append("Not enough documentation files to compare")
            return result

        # Get unique counts
        unique_counts = set(counts.values())
        if len(unique_counts) == 1:
            result.is_consistent = True
        else:
            result.is_consistent = False
            for doc_name, count in counts.items():
                for other_doc, other_count in counts.items():
                    if doc_name != other_doc and count != other_count:
                        result.discrepancies.append(
                            f"{doc_name} has {count} agents, but {other_doc} has {other_count}"
                        )

        return result

    def generate_report(self, validation_result: ValidationResult) -> str:
        """
        Generate validation report.

        Args:
            validation_result: Validation result to report

        Returns:
            Formatted validation report string
        """
        report_lines = ["# Documentation Validation Report\n"]

        # Status summary
        status = "✅ PASS" if validation_result.is_complete else "❌ FAIL"
        report_lines.append(f"**Status**: {status}\n")

        # Individual checks
        report_lines.append("## Individual Checks\n")
        report_lines.append(f"- README.md: {'✅' if validation_result.readme_valid else '❌'}")
        report_lines.append(f"- API.md: {'✅' if validation_result.api_valid else '❌'}")
        report_lines.append(
            f"- ARCHITECTURE.md: {'✅' if validation_result.architecture_valid else '❌'}"
        )
        report_lines.append(
            f"- agent-capabilities.mdc: {'✅' if validation_result.capabilities_valid else '❌'}"
        )
        report_lines.append(
            f"- Consistency: {'✅' if validation_result.consistency_valid else '❌'}\n"
        )

        # Agent counts
        if validation_result.agent_count:
            report_lines.append("## Agent Counts\n")
            for doc_name, count in validation_result.agent_count.items():
                report_lines.append(f"- {doc_name}: {count}")
            report_lines.append("")

        # Errors
        if validation_result.errors:
            report_lines.append("## Errors\n")
            for error in validation_result.errors:
                report_lines.append(f"- ❌ {error}")
            report_lines.append("")

        # Warnings
        if validation_result.warnings:
            report_lines.append("## Warnings\n")
            for warning in validation_result.warnings:
                report_lines.append(f"- ⚠️ {warning}")
            report_lines.append("")

        return "\n".join(report_lines)
