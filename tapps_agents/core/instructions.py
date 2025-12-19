"""
Instruction models for Cursor Skills integration.

These models represent structured instructions that agents prepare for execution
via Cursor Skills.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CodeGenerationInstruction:
    """Instruction for code generation via Cursor Skills."""

    specification: str
    file_path: Path | None
    context: str | None
    language: str
    expert_guidance: dict[str, str] | None

    def to_skill_command(self, agent_name: str = "implementer") -> str:
        """Convert to Cursor Skill command string."""
        parts = [f"@{agent_name}", "implement"]
        if self.file_path:
            parts.append(f'--file "{self.file_path}"')
        parts.append(f'"{self.specification}"')
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "specification": self.specification,
            "file_path": str(self.file_path) if self.file_path else None,
            "context": self.context,
            "language": self.language,
            "expert_guidance": self.expert_guidance,
        }


@dataclass
class TestGenerationInstruction:
    """Instruction for test generation via Cursor Skills."""

    target_file: Path | str
    test_framework: str
    coverage_requirements: dict[str, Any] | None

    def to_skill_command(self, agent_name: str = "tester") -> str:
        """Convert to Cursor Skill command string."""
        parts = [f"@{agent_name}", "test"]
        parts.append(f'--file "{self.target_file}"')
        if self.test_framework:
            parts.append(f'--framework "{self.test_framework}"')
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_file": str(self.target_file),
            "test_framework": self.test_framework,
            "coverage_requirements": self.coverage_requirements,
        }


@dataclass
class DocumentationInstruction:
    """Instruction for documentation generation via Cursor Skills."""

    target_file: Path | str
    output_dir: str | None
    docstring_format: str
    include_examples: bool

    def to_skill_command(self, agent_name: str = "documenter") -> str:
        """Convert to Cursor Skill command string."""
        parts = [f"@{agent_name}", "document"]
        parts.append(f'--target "{self.target_file}"')
        if self.output_dir:
            parts.append(f'--output-dir "{self.output_dir}"')
        if self.docstring_format:
            parts.append(f'--format "{self.docstring_format}"')
        if self.include_examples:
            parts.append("--include-examples")
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_file": str(self.target_file),
            "output_dir": self.output_dir,
            "docstring_format": self.docstring_format,
            "include_examples": self.include_examples,
        }


@dataclass
class ErrorAnalysisInstruction:
    """Instruction for error analysis via Cursor Skills."""

    error_message: str
    stack_trace: str | None
    context_lines: int

    def to_skill_command(self, agent_name: str = "debugger") -> str:
        """Convert to Cursor Skill command string."""
        parts = [f"@{agent_name}", "analyze-error"]
        parts.append(f'--error-message "{self.error_message}"')
        if self.stack_trace:
            parts.append(f'--stack-trace "{self.stack_trace}"')
        if self.context_lines:
            parts.append(f"--context-lines {self.context_lines}")
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "context_lines": self.context_lines,
        }


@dataclass
class GenericInstruction:
    """Generic instruction for agents that prepare prompts for Cursor Skills."""

    agent_name: str
    command: str
    prompt: str
    parameters: dict[str, Any]

    def to_skill_command(self, agent_name: str | None = None) -> str:
        """Convert to Cursor Skill command string."""
        agent = agent_name or self.agent_name
        parts = [f"@{agent}", self.command]
        for key, value in self.parameters.items():
            if value is not None:
                if isinstance(value, str):
                    parts.append(f'--{key} "{value}"')
                else:
                    parts.append(f"--{key} {value}")
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "command": self.command,
            "prompt": self.prompt,
            "parameters": self.parameters,
        }

