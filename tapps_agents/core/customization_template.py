"""
Customization template generator.

Generates customization file templates for agents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Built-in agent IDs
BUILTIN_AGENTS = [
    "analyst",
    "architect",
    "debugger",
    "designer",
    "documenter",
    "enhancer",
    "implementer",
    "improver",
    "ops",
    "orchestrator",
    "planner",
    "reviewer",
    "tester",
]


def get_customization_template(agent_id: str) -> str:
    """
    Get customization template for an agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Template YAML content
    """
    # Agent-specific examples based on common use cases
    agent_examples: dict[str, dict[str, Any]] = {
        "implementer": {
            "principles": [
                "Always use type hints in Python",
                "Follow PEP 8 strictly",
                "Use async/await for I/O operations",
            ],
            "expertise": ["Python", "FastAPI", "Async programming"],
            "instructions": "This project uses Python 3.11+ with FastAPI.\nAlways use async/await for database operations.",
        },
        "reviewer": {
            "principles": [
                "Focus on security vulnerabilities",
                "Check for performance issues",
                "Ensure test coverage",
            ],
            "expertise": ["Code review", "Security", "Performance"],
            "instructions": "This team prioritizes security and performance.\nAlways check for common vulnerabilities.",
        },
        "tester": {
            "principles": [
                "Aim for 90%+ test coverage",
                "Write integration tests for critical paths",
                "Use pytest fixtures for test data",
            ],
            "expertise": ["Testing", "Pytest", "Test automation"],
            "instructions": "This project uses pytest for testing.\nAlways include both unit and integration tests.",
        },
        "architect": {
            "principles": [
                "Design for scalability",
                "Consider microservices architecture",
                "Plan for future growth",
            ],
            "expertise": ["System design", "Architecture patterns", "Scalability"],
            "instructions": "This project follows microservices architecture.\nAlways consider scalability and maintainability.",
        },
    }

    # Get agent-specific examples or use defaults
    examples = agent_examples.get(agent_id, {
        "principles": [
            "Your custom principle here",
            "Another custom principle",
        ],
        "expertise": ["Your domain expertise", "Another area"],
        "instructions": "Additional instructions specific to your needs.\nThese are appended to the agent's base instructions.",
    })

    template = f"""# Agent Customization File
# File: .tapps-agents/customizations/{agent_id}-custom.yaml
#
# This file allows you to customize agent behaviors without modifying
# the base agent definitions. Customizations persist through framework updates.
#
# To use this file:
#   1. Customize the sections below to match your project needs
#   2. Remove or comment out sections you don't need
#   3. Save the file - customizations will be applied automatically

agent_id: {agent_id}  # Must match filename

# Override agent persona
persona_overrides:
  # Add additional core principles (appended to base principles)
  additional_principles:
"""
    
    for principle in examples["principles"]:
        template += f'    - "{principle}"\n'
    
    template += """  
  # Modify communication style (overrides base values)
  communication_style:
    tone: "technical"  # Options: "professional" | "casual" | "friendly" | "technical"
    formality: "balanced"  # Options: "formal" | "informal"
    verbosity: "detailed"  # Options: "concise" | "detailed" | "balanced"
  
  # Custom expertise areas
  expertise_areas:
    # Add new expertise areas (appended to base)
    add:
"""
    
    for area in examples["expertise"]:
        template += f'      - "{area}"\n'
    
    template += """    # Emphasize existing areas (prioritized in responses)
    emphasize:
      - "Focus more on this area"
  
  # Custom instructions (appended to base instructions)
  custom_instructions: |
"""
    
    for line in examples["instructions"].split("\n"):
        template += f"    {line}\n"

    template += """
# Override commands
command_overrides:
  # Add custom commands
  add:
    - name: "custom-command"
      description: "Description of custom command"
      handler: "task-name"  # References a task file in .tapps-agents/tasks/
  
  # Modify existing commands
  modify:
    - name: "help"
      description: "Custom help description"

# Override dependencies
dependency_overrides:
  # Add custom tasks
  tasks:
    add:
      - "custom-task.md"
  
  # Add custom templates
  templates:
    add:
      - "custom-template.yaml"
  
  # Add custom data files
  data:
    add:
      - "custom-data.md"

# Project-specific context
project_context:
  # Always load these files for this agent
  always_load:
    - "docs/architecture/performance-patterns.md"
    - "docs/team-guidelines.md"
  
  # Project-specific preferences
  preferences:
    coding_style: "Your team's style"
    architecture_patterns: ["Pattern 1", "Pattern 2"]
    technology_preferences: ["Tech 1", "Tech 2"]
"""

    return template


def generate_customization_template(
    agent_id: str, project_root: Path, overwrite: bool = False
) -> dict[str, Any]:
    """
    Generate a customization file template for an agent.

    Args:
        agent_id: Agent identifier
        project_root: Project root directory
        overwrite: Whether to overwrite existing file

    Returns:
        Result dictionary with success status and file path
    """
    # Validate agent_id
    if agent_id not in BUILTIN_AGENTS:
        # Warn but allow - might be a custom agent
        pass

    # Create customizations directory if it doesn't exist
    customizations_dir = project_root / ".tapps-agents" / "customizations"
    customizations_dir.mkdir(parents=True, exist_ok=True)

    # Generate file path
    file_path = customizations_dir / f"{agent_id}-custom.yaml"

    # Check if file exists
    if file_path.exists() and not overwrite:
        return {
            "success": False,
            "error": f"Customization file already exists: {file_path}\nUse --overwrite to replace it",
            "file_path": str(file_path),
        }

    # Generate template
    template = get_customization_template(agent_id)

    # Write file
    try:
        file_path.write_text(template, encoding="utf-8")
        return {
            "success": True,
            "file_path": str(file_path),
            "agent_id": agent_id,
        }
    except OSError as e:
        return {
            "success": False,
            "error": f"Error writing file: {e}",
            "file_path": str(file_path),
        }

