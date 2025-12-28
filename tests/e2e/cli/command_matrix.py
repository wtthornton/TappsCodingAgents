"""
Command Matrix Generator for TappsCodingAgents CLI

Documents all CLI commands and parameters for test case generation.
This module provides a structured way to reference all available commands.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class Parameter:
    """Represents a CLI parameter/argument."""

    name: str
    param_type: str  # 'positional', 'optional', 'flag'
    required: bool
    default: Any | None
    choices: list[str] | None
    help_text: str | None
    nargs: str | None = None


@dataclass
class Command:
    """Represents a CLI command with its parameters."""

    agent: str
    command_name: str
    aliases: list[str]
    description: str
    parameters: list[Parameter]
    help_text: str | None = None


def get_all_commands() -> dict[str, list[Command]]:
    """
    Get all CLI commands organized by agent.
    
    This is a manual documentation of all commands based on parser definitions.
    For automated extraction, see the parser files in tapps_agents/cli/parsers/
    """
    commands: dict[str, list[Command]] = {}
    
    # Reviewer Agent Commands
    commands["reviewer"] = [
        Command(
            agent="reviewer",
            command_name="review",
            aliases=["*review"],
            description="Review code with AI analysis",
            parameters=[
                Parameter("files", "positional", False, None, None, "File paths", nargs="*"),
                Parameter("pattern", "optional", False, None, None, "Glob pattern"),
                Parameter("max-workers", "optional", False, 4, None, "Concurrent operations"),
                Parameter("format", "optional", False, "json", ["json", "text", "markdown", "html"], "Output format"),
                Parameter("output", "optional", False, None, None, "Output file"),
                Parameter("fail-under", "optional", False, None, None, "Quality threshold"),
            ],
        ),
        Command(
            agent="reviewer",
            command_name="score",
            aliases=["*score"],
            description="Calculate objective code quality scores",
            parameters=[
                Parameter("files", "positional", False, None, None, "File paths", nargs="*"),
                Parameter("pattern", "optional", False, None, None, "Glob pattern"),
                Parameter("max-workers", "optional", False, 4, None, "Concurrent operations"),
                Parameter("format", "optional", False, "json", ["json", "text", "markdown", "html"], "Output format"),
                Parameter("output", "optional", False, None, None, "Output file"),
                Parameter("fail-under", "optional", False, None, None, "Quality threshold"),
            ],
        ),
        Command(
            agent="reviewer",
            command_name="lint",
            aliases=["*lint"],
            description="Run Ruff linting",
            parameters=[
                Parameter("files", "positional", False, None, None, "File paths", nargs="*"),
                Parameter("pattern", "optional", False, None, None, "Glob pattern"),
                Parameter("max-workers", "optional", False, 4, None, "Concurrent operations"),
                Parameter("format", "optional", False, "json", ["json", "text", "markdown", "html"], "Output format"),
                Parameter("output", "optional", False, None, None, "Output file"),
                Parameter("fail-on-issues", "flag", False, False, None, "Fail on issues"),
            ],
        ),
        Command(
            agent="reviewer",
            command_name="type-check",
            aliases=["*type-check"],
            description="Run mypy type checking",
            parameters=[
                Parameter("files", "positional", False, None, None, "File paths", nargs="*"),
                Parameter("pattern", "optional", False, None, None, "Glob pattern"),
                Parameter("max-workers", "optional", False, 4, None, "Concurrent operations"),
                Parameter("format", "optional", False, "json", ["json", "text", "markdown", "html"], "Output format"),
                Parameter("output", "optional", False, None, None, "Output file"),
                Parameter("fail-on-issues", "flag", False, False, None, "Fail on issues"),
            ],
        ),
        Command(
            agent="reviewer",
            command_name="report",
            aliases=["*report"],
            description="Generate comprehensive quality reports",
            parameters=[
                Parameter("target", "positional", True, None, None, "Target file/directory"),
                Parameter("formats", "positional", True, None, ["json", "markdown", "html", "all"], "Output formats", nargs="+"),
                Parameter("output-dir", "optional", False, None, None, "Output directory"),
            ],
        ),
        Command(
            agent="reviewer",
            command_name="duplication",
            aliases=["*duplication"],
            description="Detect code duplication",
            parameters=[
                Parameter("target", "positional", True, None, None, "Target file/directory"),
                Parameter("format", "optional", False, "json", ["json", "text"], "Output format"),
            ],
        ),
        Command(
            agent="reviewer",
            command_name="docs",
            aliases=["*docs"],
            description="Get library documentation from Context7",
            parameters=[
                Parameter("library", "positional", True, None, None, "Library name"),
                Parameter("topic", "positional", False, None, None, "Topic name"),
                Parameter("mode", "optional", False, "code", ["code", "info"], "Documentation mode"),
                Parameter("page", "optional", False, 1, None, "Page number"),
                Parameter("format", "optional", False, "json", ["json", "text", "markdown"], "Output format"),
                Parameter("no-cache", "flag", False, False, None, "Skip cache"),
            ],
        ),
    ]
    
    # Add more agents as needed - this is a representative sample
    # The full matrix would include all 13 agents and top-level commands
    
    return commands


def generate_test_cases(commands: dict[str, list[Command]], max_per_command: int = 3) -> list[dict[str, Any]]:
    """Generate representative test cases from commands."""
    test_cases: list[dict[str, Any]] = []
    
    for agent_name, agent_commands in commands.items():
        for command in agent_commands:
            # Minimal test case
            minimal = {
                "agent": agent_name,
                "command": command.command_name,
                "parameters": {},
                "type": "minimal",
            }
            # Add required positional parameters
            for param in command.parameters:
                if param.required and param.param_type == "positional":
                    minimal["parameters"][param.name] = f"<{param.name}>"
            test_cases.append(minimal)
            
            # Test with format variations
            format_params = [p for p in command.parameters if "format" in p.name.lower() and p.choices]
            if format_params:
                for fmt_param in format_params[:1]:  # Just first format param
                    for choice in fmt_param.choices[:2]:  # First 2 choices
                        test_case = {
                            "agent": agent_name,
                            "command": command.command_name,
                            "parameters": {fmt_param.name: choice},
                            "type": "format_variant",
                        }
                        # Add required params
                        for param in command.parameters:
                            if param.required and param.param_type == "positional":
                                test_case["parameters"][param.name] = f"<{param.name}>"
                        test_cases.append(test_case)
    
    return test_cases


def export_to_json(commands: dict[str, list[Command]], output_path: Path) -> None:
    """Export commands to JSON."""
    commands_dict = {
        agent: [asdict(cmd) for cmd in cmds]
        for agent, cmds in commands.items()
    }
    
    with output_path.open("w") as f:
        json.dump(commands_dict, f, indent=2, default=str)


def main():
    """Generate command matrix and test cases."""
    print("Building command matrix...")
    commands = get_all_commands()
    
    total = sum(len(cmds) for cmds in commands.values())
    print(f"Documented {total} commands across {len(commands)} agents")
    
    # Export commands
    output_path = Path(__file__).parent / "command_matrix.json"
    export_to_json(commands, output_path)
    print(f"Exported to {output_path}")
    
    # Generate test cases
    test_cases = generate_test_cases(commands)
    print(f"Generated {len(test_cases)} test cases")
    
    test_cases_path = Path(__file__).parent / "test_cases.json"
    with test_cases_path.open("w") as f:
        json.dump(test_cases, f, indent=2, default=str)
    print(f"Exported test cases to {test_cases_path}")


if __name__ == "__main__":
    main()

