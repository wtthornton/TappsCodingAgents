"""
Unified Output Format System for TappsCodingAgents.

Provides consistent output formatting across all agents with support for:
- JSON, text, markdown, YAML formats
- File saving
- Template-based formatting
- Structured output base class
"""

import json
from abc import ABC
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class OutputFormat(StrEnum):
    """Supported output formats."""

    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    YAML = "yaml"
    HTML = "html"  # Future support


@dataclass
class AgentOutput(ABC):
    """
    Base class for structured agent outputs.
    
    All agent outputs should inherit from this class to ensure
    consistent formatting and file saving capabilities.
    """

    success: bool
    agent_name: str
    command: str
    data: dict[str, Any]
    metadata: dict[str, Any] | None = None

    def to_json(self) -> str:
        """Convert to JSON format."""
        return json.dumps(
            {
                "success": self.success,
                "agent": self.agent_name,
                "command": self.command,
                "data": self.data,
                "metadata": self.metadata or {},
            },
            indent=2,
            ensure_ascii=False,
        )

    def to_text(self) -> str:
        """Convert to human-readable text format."""
        lines = [
            f"Agent: {self.agent_name}",
            f"Command: {self.command}",
            f"Status: {'Success' if self.success else 'Failed'}",
            "",
        ]

        # Format data section
        if self.data:
            lines.append("Results:")
            lines.extend(self._format_dict(self.data, indent=2))

        # Format metadata if present
        if self.metadata:
            lines.append("")
            lines.append("Metadata:")
            lines.extend(self._format_dict(self.metadata, indent=2))

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Convert to Markdown format."""
        lines = [
            f"# {self.agent_name} - {self.command}",
            "",
            f"**Status:** {'✅ Success' if self.success else '❌ Failed'}",
            "",
        ]

        # Format data section
        if self.data:
            lines.append("## Results")
            lines.append("")
            lines.extend(self._format_dict_markdown(self.data))

        # Format metadata if present
        if self.metadata:
            lines.append("")
            lines.append("## Metadata")
            lines.append("")
            lines.extend(self._format_dict_markdown(self.metadata))

        return "\n".join(lines)

    def to_yaml(self) -> str:
        """Convert to YAML format."""
        output = {
            "success": self.success,
            "agent": self.agent_name,
            "command": self.command,
            "data": self.data,
            "metadata": self.metadata or {},
        }
        return yaml.dump(output, default_flow_style=False, allow_unicode=True)

    def format(self, output_format: str | OutputFormat) -> str:
        """Format output in specified format."""
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format.lower())

        if output_format == OutputFormat.JSON:
            return self.to_json()
        elif output_format == OutputFormat.TEXT:
            return self.to_text()
        elif output_format == OutputFormat.MARKDOWN:
            return self.to_markdown()
        elif output_format == OutputFormat.YAML:
            return self.to_yaml()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save(self, output_file: str | Path, output_format: str | OutputFormat | None = None) -> Path:
        """
        Save output to file.
        
        Args:
            output_file: Path to output file
            output_format: Format to use (auto-detected from extension if None)
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_file)

        # Auto-detect format from extension if not specified
        if output_format is None:
            ext = output_path.suffix.lower()
            format_map = {
                ".json": OutputFormat.JSON,
                ".txt": OutputFormat.TEXT,
                ".md": OutputFormat.MARKDOWN,
                ".yaml": OutputFormat.YAML,
                ".yml": OutputFormat.YAML,
                ".html": OutputFormat.HTML,
            }
            output_format = format_map.get(ext, OutputFormat.TEXT)
        else:
            if isinstance(output_format, str):
                output_format = OutputFormat(output_format.lower())

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Format and save
        formatted = self.format(output_format)
        output_path.write_text(formatted, encoding="utf-8")

        return output_path

    def _format_dict(self, data: dict[str, Any], indent: int = 0) -> list[str]:
        """Format dictionary as text with indentation."""
        lines = []
        prefix = " " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(self._format_dict(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  -")
                        lines.extend(self._format_dict(item, indent + 4))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")
        return lines

    def _format_dict_markdown(self, data: dict[str, Any]) -> list[str]:
        """Format dictionary as Markdown."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"### {key}")
                lines.append("")
                lines.extend(self._format_dict_markdown(value))
                lines.append("")
            elif isinstance(value, list):
                lines.append(f"**{key}:**")
                lines.append("")
                for item in value:
                    if isinstance(item, dict):
                        lines.append("-")
                        for k, v in item.items():
                            lines.append(f"  - **{k}:** {v}")
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"- **{key}:** {value}")
        return lines

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "agent": self.agent_name,
            "command": self.command,
            "data": self.data,
            "metadata": self.metadata or {},
        }


class OutputFormatter:
    """
    Utility class for formatting agent outputs.
    
    Provides helper methods for converting agent results to various formats
    and saving to files.
    """

    @staticmethod
    def format_output(
        result: dict[str, Any],
        agent_name: str,
        command: str,
        output_format: str | OutputFormat = OutputFormat.TEXT,
    ) -> str:
        """
        Format agent result in specified format.
        
        Args:
            result: Agent result dictionary
            agent_name: Name of the agent
            command: Command that was executed
            output_format: Desired output format
            
        Returns:
            Formatted output string
        """
        success = result.get("success", not result.get("error"))
        data = {k: v for k, v in result.items() if k not in ("success", "error")}
        metadata = {"error": result.get("error")} if result.get("error") else None

        output = AgentOutput(
            success=success,
            agent_name=agent_name,
            command=command,
            data=data,
            metadata=metadata,
        )

        return output.format(output_format)

    @staticmethod
    def save_output(
        result: dict[str, Any],
        agent_name: str,
        command: str,
        output_file: str | Path,
        output_format: str | OutputFormat | None = None,
    ) -> Path:
        """
        Save agent result to file.
        
        Args:
            result: Agent result dictionary
            agent_name: Name of the agent
            command: Command that was executed
            output_file: Path to output file
            output_format: Format to use (auto-detected if None)
            
        Returns:
            Path to saved file
        """
        success = result.get("success", not result.get("error"))
        data = {k: v for k, v in result.items() if k not in ("success", "error")}
        metadata = {"error": result.get("error")} if result.get("error") else None

        output = AgentOutput(
            success=success,
            agent_name=agent_name,
            command=command,
            data=data,
            metadata=metadata,
        )

        return output.save(output_file, output_format)
