"""Shared utilities for consistent output handling across commands."""
import json
import sys
from pathlib import Path
from typing import Any


def write_output(
    data: Any,
    output_file: str | None = None,
    format_type: str = "json",
    default_format: str = "json"
) -> None:
    """
    Write command output to file or stdout with consistent formatting.
    
    Args:
        data: Data to output (dict, str, etc.)
        output_file: Optional file path to write to
        format_type: Output format (json, text, markdown)
        default_format: Default format if format_type not specified
    """
    format_type = format_type or default_format
    
    # Format data based on type
    if format_type == "json":
        output = json.dumps(data, indent=2)
    elif format_type == "text":
        output = str(data) if not isinstance(data, str) else data
    elif format_type == "markdown":
        output = _format_as_markdown(data)
    else:
        output = str(data)
    
    # Write to file or stdout
    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
    else:
        print(output, file=sys.stdout)
        sys.stdout.flush()


def _format_as_markdown(data: Any) -> str:
    """Convert data to markdown format."""
    # Implementation for markdown formatting
    if isinstance(data, dict):
        # Format dict as markdown
        lines = []
        for key, value in data.items():
            lines.append(f"## {key}")
            if isinstance(value, (dict, list)):
                lines.append(json.dumps(value, indent=2))
            else:
                lines.append(str(value))
        return "\n\n".join(lines)
    return str(data)

