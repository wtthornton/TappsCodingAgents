"""
Instruction models for Cursor Skills integration.

These models represent structured instructions that agents prepare for execution
via Cursor Skills.

All instruction classes support:
- Converting to Cursor Skill commands (to_skill_command)
- Converting to CLI commands (to_cli_command)
- Creating execution directives (to_execution_directive)
- Human-readable descriptions (get_description)
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
    context7_docs: dict[str, str] | None = None  # R7: Library name -> documentation content

    def to_skill_command(self, agent_name: str = "implementer") -> str:
        """Convert to Cursor Skill command string."""
        parts = [f"@{agent_name}", "implement"]
        if self.file_path:
            parts.append(f'--file "{self.file_path}"')
        parts.append(f'"{self.specification}"')
        return " ".join(parts)

    def to_cli_command(self, agent_name: str = "implementer") -> str:
        """Convert to CLI command string."""
        parts = ["tapps-agents", agent_name, "implement"]
        if self.file_path:
            parts.append(f'--file "{self.file_path}"')
        parts.append(f'"{self.specification}"')
        return " ".join(parts)

    def to_execution_directive(self) -> dict[str, Any]:
        """Create execution directive for Cursor Skills."""
        return {
            "_cursor_execution_directive": {
                "action": "execute_instruction",
                "type": "code_generation",
                "description": f"Generate {self.language} code: {self.specification[:100]}...",
                "skill_command": self.to_skill_command(),
                "cli_command": self.to_cli_command(),
                "ready_to_execute": True,
                "requires_review": False,
            },
            "instruction": self.to_dict(),
        }

    def get_description(self) -> str:
        """Get human-readable description of this instruction."""
        file_info = f" to {self.file_path}" if self.file_path else ""
        return f"Generate {self.language} code{file_info}: {self.specification[:200]}..."

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "specification": self.specification,
            "file_path": str(self.file_path) if self.file_path else None,
            "context": self.context,
            "language": self.language,
            "expert_guidance": self.expert_guidance,
            "context7_docs": self.context7_docs,
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

    def to_cli_command(self, agent_name: str = "tester") -> str:
        """Convert to CLI command string."""
        parts = ["tapps-agents", agent_name, "test"]
        parts.append(f'--file "{self.target_file}"')
        if self.test_framework:
            parts.append(f'--framework "{self.test_framework}"')
        return " ".join(parts)

    def to_execution_directive(self) -> dict[str, Any]:
        """Create execution directive for Cursor Skills."""
        return {
            "_cursor_execution_directive": {
                "action": "execute_instruction",
                "type": "test_generation",
                "description": f"Generate {self.test_framework} tests for {self.target_file}",
                "skill_command": self.to_skill_command(),
                "cli_command": self.to_cli_command(),
                "ready_to_execute": True,
                "requires_review": False,
            },
            "instruction": self.to_dict(),
        }

    def get_description(self) -> str:
        """Get human-readable description of this instruction."""
        return f"Generate {self.test_framework} tests for {self.target_file}"

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

    def to_cli_command(self, agent_name: str = "documenter") -> str:
        """Convert to CLI command string."""
        parts = ["tapps-agents", agent_name, "document"]
        parts.append(f'--target "{self.target_file}"')
        if self.output_dir:
            parts.append(f'--output-dir "{self.output_dir}"')
        if self.docstring_format:
            parts.append(f'--format "{self.docstring_format}"')
        if self.include_examples:
            parts.append("--include-examples")
        return " ".join(parts)

    def to_execution_directive(self) -> dict[str, Any]:
        """Create execution directive for Cursor Skills."""
        return {
            "_cursor_execution_directive": {
                "action": "execute_instruction",
                "type": "documentation",
                "description": f"Generate {self.docstring_format} documentation for {self.target_file}",
                "skill_command": self.to_skill_command(),
                "cli_command": self.to_cli_command(),
                "ready_to_execute": True,
                "requires_review": False,
            },
            "instruction": self.to_dict(),
        }

    def get_description(self) -> str:
        """Get human-readable description of this instruction."""
        format_info = f" ({self.docstring_format})" if self.docstring_format else ""
        return f"Generate documentation{format_info} for {self.target_file}"

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

    def to_cli_command(self, agent_name: str = "debugger") -> str:
        """Convert to CLI command string."""
        parts = ["tapps-agents", agent_name, "analyze-error"]
        parts.append(f'--error-message "{self.error_message}"')
        if self.stack_trace:
            parts.append(f'--stack-trace "{self.stack_trace}"')
        if self.context_lines:
            parts.append(f"--context-lines {self.context_lines}")
        return " ".join(parts)

    def to_execution_directive(self) -> dict[str, Any]:
        """Create execution directive for Cursor Skills."""
        return {
            "_cursor_execution_directive": {
                "action": "execute_instruction",
                "type": "error_analysis",
                "description": f"Analyze error: {self.error_message[:100]}...",
                "skill_command": self.to_skill_command(),
                "cli_command": self.to_cli_command(),
                "ready_to_execute": True,
                "requires_review": False,
            },
            "instruction": self.to_dict(),
        }

    def get_description(self) -> str:
        """Get human-readable description of this instruction."""
        return f"Analyze error: {self.error_message[:200]}..."

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

    def to_cli_command(self, agent_name: str | None = None) -> str:
        """Convert to CLI command string."""
        agent = agent_name or self.agent_name
        parts = ["tapps-agents", agent, self.command]
        for key, value in self.parameters.items():
            if value is not None:
                if isinstance(value, str):
                    parts.append(f'--{key} "{value}"')
                else:
                    parts.append(f"--{key} {value}")
        return " ".join(parts)

    def to_execution_directive(self) -> dict[str, Any]:
        """Create execution directive for Cursor Skills."""
        return {
            "_cursor_execution_directive": {
                "action": "execute_instruction",
                "type": "generic",
                "description": f"Execute {self.agent_name} {self.command}",
                "skill_command": self.to_skill_command(),
                "cli_command": self.to_cli_command(),
                "ready_to_execute": True,
                "requires_review": len(self.prompt) > 1000,  # Review if prompt is very long
            },
            "instruction": self.to_dict(),
        }

    def get_description(self) -> str:
        """Get human-readable description of this instruction."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items() if v is not None)
        params_info = f" with {params_str}" if params_str else ""
        return f"Execute {self.agent_name} {self.command}{params_info}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "command": self.command,
            "prompt": self.prompt,
            "parameters": self.parameters,
        }

