# Agent Customization Guide

This guide explains how to customize agent behaviors using customization files. Customizations allow you to override agent personas, commands, and dependencies without modifying base agent definitions, ensuring your customizations persist through framework updates.

## Overview

Agent customizations are stored in `.tapps-agents/customizations/` directory as YAML files. Each agent can have its own customization file following the naming pattern: `{agent-id}-custom.yaml`.

### Key Benefits

- **Update-safe**: Customizations persist through framework updates
- **Project-specific**: Customizations are per-project, not global
- **Gitignored by default**: Customizations are excluded from version control by default (opt-in to share)
- **Non-breaking**: Base agent definitions remain unchanged

## Quick Start

### 1. Generate a Template

Use the CLI command to generate a customization template:

```bash
python -m tapps_agents.cli customize init implementer
```

This creates `.tapps-agents/customizations/implementer-custom.yaml` with a complete template.

### 2. Customize Your Agent

Edit the generated file to match your project needs:

```yaml
agent_id: implementer

persona_overrides:
  additional_principles:
    - "Always use type hints in Python"
    - "Follow PEP 8 strictly"
  
  communication_style:
    tone: "technical"
    verbosity: "detailed"
  
  expertise_areas:
    add:
      - "FastAPI"
      - "Async programming"
```

### 3. Use Your Customized Agent

Customizations are automatically loaded when agents activate. No additional configuration needed!

## Customization File Format

### Required Fields

- `agent_id`: Must match the filename (e.g., `implementer-custom.yaml` → `agent_id: implementer`)

### Optional Sections

#### Persona Overrides

Customize agent personality and behavior:

```yaml
persona_overrides:
  # Add principles (appended to base)
  additional_principles:
    - "Your custom principle"
  
  # Override communication style
  communication_style:
    tone: "professional" | "casual" | "friendly" | "technical"
    formality: "formal" | "informal"
    verbosity: "concise" | "detailed" | "balanced"
  
  # Add or emphasize expertise areas
  expertise_areas:
    add:
      - "New domain"
    emphasize:
      - "Existing area to focus on"
  
  # Add custom instructions
  custom_instructions: |
    Additional instructions appended to base instructions.
```

#### Command Overrides

Add or modify agent commands:

```yaml
command_overrides:
  # Add new commands
  add:
    - name: "custom-command"
      description: "Description of custom command"
      handler: "task-name"  # References .tapps-agents/tasks/task-name.md
  
  # Modify existing commands
  modify:
    - name: "help"
      description: "Custom help description"
```

#### Dependency Overrides

Add custom tasks, templates, or data files:

```yaml
dependency_overrides:
  tasks:
    add:
      - "custom-task.md"
  templates:
    add:
      - "custom-template.yaml"
  data:
    add:
      - "custom-data.md"
```

#### Project Context

Specify project-specific files and preferences:

```yaml
project_context:
  # Files always loaded for this agent
  always_load:
    - "docs/architecture/performance-patterns.md"
    - "docs/team-guidelines.md"
  
  # Project-specific preferences
  preferences:
    coding_style: "Pythonic with type hints"
    architecture_patterns: ["Microservices", "Event-driven"]
    technology_preferences: ["FastAPI", "SQLAlchemy", "Pydantic"]
```

## Examples

### Example 1: Python-Focused Implementer

```yaml
agent_id: implementer

persona_overrides:
  additional_principles:
    - "Always use type hints in Python"
    - "Follow PEP 8 strictly"
    - "Use async/await for I/O operations"
  
  communication_style:
    tone: "technical"
    verbosity: "detailed"
  
  expertise_areas:
    emphasize:
      - "Python"
      - "FastAPI"
      - "Async programming"
  
  custom_instructions: |
    This project uses Python 3.11+ with FastAPI.
    Always use async/await for database operations.
    Follow the project's performance patterns document.

project_context:
  always_load:
    - "docs/architecture/performance-patterns.md"
  preferences:
    coding_style: "Pythonic with type hints"
    technology_preferences: ["FastAPI", "SQLAlchemy", "Pydantic"]
```

### Example 2: Security-Focused Reviewer

```yaml
agent_id: reviewer

persona_overrides:
  additional_principles:
    - "Focus on security vulnerabilities"
    - "Check for performance issues"
    - "Ensure test coverage"
  
  expertise_areas:
    emphasize:
      - "Security"
      - "Performance"
      - "Code quality"
  
  custom_instructions: |
    This team prioritizes security and performance.
    Always check for common vulnerabilities (SQL injection, XSS, etc.).
    Verify test coverage meets minimum thresholds.

project_context:
  preferences:
    security_standards: "OWASP Top 10"
    min_test_coverage: 80
```

### Example 3: Agile-Focused Planner

```yaml
agent_id: planner

persona_overrides:
  additional_principles:
    - "Always break stories into 1-3 day tasks"
    - "Include acceptance criteria for every story"
    - "Consider technical debt in story estimation"
  
  custom_instructions: |
    This team follows 2-week sprints.
    Stories should be small enough to complete in 1-3 days.
    Always include risk assessment for complex stories.

project_context:
  preferences:
    sprint_length: "2 weeks"
    story_size: "1-3 days"
    estimation_method: "story points"
```

## Merge Rules

Customizations use **additive and overriding** merge logic:

- **Additional principles**: Appended to base principles
- **Communication style**: Overrides base values
- **Expertise areas**: Added to base (emphasize prioritizes existing areas)
- **Custom instructions**: Appended to base instructions
- **Commands**: New commands added, existing commands modified
- **Dependencies**: Added to base dependencies
- **Project context**: Always_load appended, preferences updated

## Validation

Customization files are validated before loading:

- **YAML syntax**: Must be valid YAML
- **Agent ID matching**: `agent_id` must match filename
- **Structure validation**: Required fields and types are checked
- **File references**: Referenced files are checked (warnings only)

Validation errors prevent agent activation with clear error messages.

## Sharing Customizations

### Default Behavior

Customizations are **gitignored by default** to prevent accidentally committing sensitive configurations.

### Opt-in to Version Control

To share customizations with your team:

1. Remove the gitignore pattern (or add an exception):
   ```bash
   # In .gitignore or .cursorignore
   # Remove or comment out:
   # .tapps-agents/customizations/
   ```

2. Commit your customization files:
   ```bash
   git add .tapps-agents/customizations/
   git commit -m "Add team agent customizations"
   ```

### Best Practices

- **Team standards**: Commit customization files that define team-wide standards
- **Personal preferences**: Keep personal customizations gitignored
- **Documentation**: Document why customizations were added
- **Review changes**: Review customization changes like code changes

## Troubleshooting

### Customization Not Loading?

1. **Check filename**: Must match pattern `{agent-id}-custom.yaml`
2. **Verify agent_id**: Must match filename (e.g., `dev-custom.yaml` → `agent_id: dev`)
3. **Check YAML syntax**: Use a YAML validator
4. **Check file location**: Must be in `.tapps-agents/customizations/`

### Validation Errors?

Common validation errors:

- **Missing agent_id**: Add `agent_id: {agent-id}` at the top
- **Invalid YAML**: Check for syntax errors (indentation, quotes, etc.)
- **Unknown keys**: Remove or fix unknown customization keys

### Customizations Not Applied?

1. **Check agent activation**: Customizations load during agent activation
2. **Verify merge logic**: Customizations are merged, not replaced
3. **Check logs**: Look for warnings about customization loading

### Want to Reset?

Simply delete the customization file:

```bash
rm .tapps-agents/customizations/{agent-id}-custom.yaml
```

The agent will return to default behavior.

## Advanced Usage

### Multiple Customizations

You can customize multiple agents:

```
.tapps-agents/customizations/
  ├── implementer-custom.yaml
  ├── reviewer-custom.yaml
  └── tester-custom.yaml
```

Each agent loads its own customization file independently.

### Conditional Customizations

Use project context to conditionally load files:

```yaml
project_context:
  always_load:
    - "docs/architecture/performance-patterns.md"  # Always loaded
    - "docs/team-guidelines.md"  # Always loaded
```

### Custom Commands

Add project-specific commands:

```yaml
command_overrides:
  add:
    - name: "deploy-staging"
      description: "Deploy to staging environment"
      handler: "deploy-staging-task"
```

Then create `.tapps-agents/tasks/deploy-staging-task.md` with your deployment logic.

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System architecture overview
- [Agent Guide](BUILTIN_EXPERTS_GUIDE.md) - Built-in agents documentation
- [Configuration Guide](CONFIGURATION.md) - Project configuration

## Support

For issues or questions:

1. Check this guide first
2. Review validation error messages
3. Check agent activation logs
4. Open an issue on GitHub

