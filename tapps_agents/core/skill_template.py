"""
Custom Skill template generator.

Generates Skill file templates for Cursor Skills.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Built-in agent types for template customization
AGENT_TYPES = [
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

# Standard tool options
TOOL_OPTIONS = [
    "Read",
    "Write",
    "Edit",
    "Grep",
    "Glob",
    "Bash",
    "CodebaseSearch",
    "Terminal",
]

# Capability categories
CAPABILITY_CATEGORIES = [
    "code_generation",
    "code_review",
    "testing",
    "documentation",
    "debugging",
    "refactoring",
    "analysis",
    "architecture",
    "design",
    "planning",
]


def get_defaults_for_agent_type(agent_type: str | None) -> dict[str, Any]:
    """Get default values based on agent type."""
    defaults: dict[str, dict[str, Any]] = {
        "implementer": {
            "description": "Write production-quality code following project patterns. Use when implementing features, fixing bugs, or creating new files.",
            "allowed_tools": ["Read", "Write", "Edit", "Grep", "Glob", "Bash"],
            "capabilities": ["code_generation", "refactoring"],
            "identity_focus": "Code Generation, Refactoring, Library Integration",
        },
        "reviewer": {
            "description": "Review code for quality, security, and best practices. Use when reviewing code changes or assessing code quality.",
            "allowed_tools": ["Read", "Grep", "Glob", "CodebaseSearch"],
            "capabilities": ["code_review", "analysis"],
            "identity_focus": "Code Review, Quality Assurance, Security Analysis",
        },
        "tester": {
            "description": "Generate and run tests for code. Use when creating unit tests, integration tests, or running test suites.",
            "allowed_tools": ["Read", "Write", "Edit", "Grep", "Terminal"],
            "capabilities": ["testing", "code_generation"],
            "identity_focus": "Test Generation, Test Execution, Test Coverage",
        },
        "architect": {
            "description": "Design system and security architecture. Use for system design, architecture diagrams, technology selection.",
            "allowed_tools": ["Read", "Grep", "Glob", "CodebaseSearch"],
            "capabilities": ["architecture", "design", "analysis"],
            "identity_focus": "System Design, Architecture Patterns, Technology Selection",
        },
        "analyst": {
            "description": "Gather requirements, perform technical research, and estimate effort/risk. Use for requirements analysis and research.",
            "allowed_tools": ["Read", "Grep", "Glob", "CodebaseSearch"],
            "capabilities": ["analysis", "planning"],
            "identity_focus": "Requirements Analysis, Technical Research, Risk Assessment",
        },
    }
    
    return defaults.get(agent_type or "", {
        "description": "Custom agent for specialized tasks. Use when you need domain-specific capabilities.",
        "allowed_tools": ["Read", "Write", "Edit", "Grep", "Glob"],
        "capabilities": ["code_generation"],
        "identity_focus": "Custom Capabilities, Domain Expertise",
    })


def generate_skill_template(
    skill_name: str,
    agent_type: str | None = None,
    description: str | None = None,
    allowed_tools: list[str] | None = None,
    capabilities: list[str] | None = None,
    model_profile: str | None = None,
) -> str:
    """
    Generate a Skill template with all required fields.
    
    Args:
        skill_name: Name of the Skill (used in YAML frontmatter)
        agent_type: Optional agent type for defaults
        description: Optional custom description
        allowed_tools: Optional list of allowed tools
        capabilities: Optional list of capabilities
        model_profile: Optional model profile name
        
    Returns:
        Complete Skill template as string
    """
    # Get defaults based on agent type
    defaults = get_defaults_for_agent_type(agent_type)
    
    # Use provided values or defaults
    final_description = description or defaults.get("description", "Custom agent for specialized tasks.")
    final_tools = allowed_tools or defaults.get("allowed_tools", ["Read", "Write", "Edit", "Grep", "Glob"])
    final_capabilities = capabilities or defaults.get("capabilities", ["code_generation"])
    final_model_profile = model_profile or f"{skill_name}_profile"
    identity_focus = defaults.get("identity_focus", "Custom Capabilities")
    
    # Format tools as comma-separated string
    tools_str = ", ".join(final_tools)
    
    # Generate YAML frontmatter
    yaml_frontmatter = f"""---
name: {skill_name}
description: {final_description}
allowed-tools: {tools_str}
model_profile: {final_model_profile}
---

"""
    
    # Generate markdown content
    markdown_content = f"""# {skill_name.title()} Agent

## Identity

You are a specialized agent focused on {identity_focus}. You specialize in:

"""
    
    # Add capability-specific identity points
    capability_descriptions = {
        "code_generation": "- **Code Generation**: Creating new code from specifications",
        "code_review": "- **Code Review**: Reviewing code for quality, security, and best practices",
        "testing": "- **Test Generation**: Creating comprehensive test suites",
        "documentation": "- **Documentation**: Writing clear, comprehensive documentation",
        "debugging": "- **Debugging**: Identifying and fixing bugs",
        "refactoring": "- **Refactoring**: Improving code structure and quality",
        "analysis": "- **Analysis**: Analyzing requirements and technical research",
        "architecture": "- **Architecture**: Designing system architecture",
        "design": "- **Design**: Creating design specifications",
        "planning": "- **Planning**: Creating plans and estimates",
    }
    
    for cap in final_capabilities:
        if cap in capability_descriptions:
            markdown_content += capability_descriptions[cap] + "\n"
    
    markdown_content += """
## Instructions

1. **Understand the task** - Read and understand what needs to be done
2. **Follow project conventions** - Adhere to existing patterns and standards
3. **Provide quality output** - Ensure your work meets quality standards
4. **Document your work** - Include clear documentation where needed
5. **Consider edge cases** - Think about potential issues and handle them appropriately

## Commands

### Core Commands

- `*command-name <description>` - Brief description of what this command does
  - Example: `*command-name "example usage"`
  - Example: `*command-name "another example" --option=value`

## Capabilities

### Primary Capabilities

"""
    
    # Add capability sections
    for cap in final_capabilities:
        if cap == "code_generation":
            markdown_content += """### Code Generation

- **Generate Code**: Create new code from specifications
- **Follow Patterns**: Use existing code patterns and conventions
- **Quality Assurance**: Ensure generated code meets quality standards

"""
        elif cap == "code_review":
            markdown_content += """### Code Review

- **Quality Analysis**: Review code for quality issues
- **Security Checks**: Identify security vulnerabilities
- **Best Practices**: Ensure code follows best practices

"""
        elif cap == "testing":
            markdown_content += """### Testing

- **Test Generation**: Create comprehensive test suites
- **Test Execution**: Run and validate tests
- **Coverage Analysis**: Ensure adequate test coverage

"""
    
    markdown_content += """## Configuration

**Agent Configuration:**
- `setting_name`: Description of setting (default: value)
- `another_setting`: Another setting description (default: value)

## Constraints

- **Do not make architectural decisions** (consult architect if needed)
- **Do not skip error handling**
- **Do not introduce new dependencies** without discussion
- **Follow project conventions** and style guidelines

## Integration

- **Framework**: Integrates with TappsCodingAgents framework
- **Tools**: Uses specified tools: """ + tools_str + """
- **Config System**: Loads configuration from `.tapps-agents/config.yaml`

## Example Workflow

1. **Receive Task**: User provides task description
2. **Analyze Requirements**: Understand what needs to be done
3. **Execute Task**: Perform the required work
4. **Validate Output**: Ensure quality and correctness
5. **Return Results**: Provide completed work to user

## Best Practices

1. **Understand before acting** - Always understand requirements fully
2. **Follow conventions** - Adhere to project patterns and standards
3. **Quality first** - Ensure output meets quality standards
4. **Document clearly** - Provide clear documentation
5. **Handle errors gracefully** - Include proper error handling

## Usage Examples

**Basic Usage:**
```
*command-name "example task description"
```

**With Options:**
```
*command-name "task" --option=value
```
"""
    
    return yaml_frontmatter + markdown_content


def create_skill_file(
    skill_name: str,
    project_root: Path | None = None,
    agent_type: str | None = None,
    description: str | None = None,
    allowed_tools: list[str] | None = None,
    capabilities: list[str] | None = None,
    model_profile: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Create a Skill file from template.
    
    Args:
        skill_name: Name of the Skill
        project_root: Project root directory (defaults to current directory)
        agent_type: Optional agent type for defaults
        description: Optional custom description
        allowed_tools: Optional list of allowed tools
        capabilities: Optional list of capabilities
        model_profile: Optional model profile name
        overwrite: Whether to overwrite existing file
        
    Returns:
        Dictionary with success status and file path
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Create .claude/skills/{skill_name}/ directory
    skill_dir = project_root / ".claude" / "skills" / skill_name
    skill_file = skill_dir / "SKILL.md"
    
    # Check if file exists
    if skill_file.exists() and not overwrite:
        return {
            "success": False,
            "error": f"Skill file already exists: {skill_file}\nUse --overwrite to replace it.",
            "file_path": str(skill_file),
        }
    
    # Create directory if it doesn't exist
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate template
    template_content = generate_skill_template(
        skill_name=skill_name,
        agent_type=agent_type,
        description=description,
        allowed_tools=allowed_tools,
        capabilities=capabilities,
        model_profile=model_profile,
    )
    
    # Write file
    try:
        skill_file.write_text(template_content, encoding="utf-8")
        return {
            "success": True,
            "file_path": str(skill_file),
            "skill_name": skill_name,
            "skill_dir": str(skill_dir),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write Skill file: {e}",
            "file_path": str(skill_file),
        }

