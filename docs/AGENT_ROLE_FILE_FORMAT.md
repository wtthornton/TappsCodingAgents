# Agent Role File Format Guide

## Overview

Agent role files define the identity, principles, communication style, expertise areas, and interaction patterns for agents in the TappsCodingAgents framework. These files enable transparent, customizable agent behaviors and support team-specific customizations.

## File Location

Role files are located in: `templates/agent_roles/`

## File Naming Convention

Role files follow the pattern: `{agent-id}-role.md`

Examples:
- `implementer-role.md`
- `architect-role.md`
- `analyst-role.md`

## File Structure

Each role file consists of:

1. **YAML Frontmatter** (required) - Metadata about the role file
2. **Markdown Content** - Role definition sections

### YAML Frontmatter

The YAML frontmatter appears at the top of the file, delimited by `---`:

```yaml
---
role_id: agent-id           # Required: Must match agent_id
version: 1.0.0              # Required: Semantic version
description: "Brief description"  # Required: Short description

# Optional fields:
author: "Author name"
created: "2025-01-XX"
updated: "2025-01-XX"
compatibility:
  min_framework_version: "1.0.0"
  max_framework_version: null
tags:
  - tag1
  - tag2
---
```

**Required Fields**:
- `role_id`: Must match the agent's ID (e.g., "implementer", "architect")
- `version`: Semantic version of the role definition (e.g., "1.0.0")
- `description`: Brief one-line description of the agent's role

**Optional Fields**:
- `author`: Creator/maintainer name
- `created`: Creation date (YYYY-MM-DD format)
- `updated`: Last update date (YYYY-MM-DD format)
- `compatibility`: Framework version compatibility
  - `min_framework_version`: Minimum required framework version
  - `max_framework_version`: Maximum compatible version (null = no limit)
- `tags`: List of tags for categorization

### Markdown Content Sections

The markdown content defines the agent's role in five main sections:

#### 1. Identity

Defines who the agent is, their role, and primary responsibilities.

**Format**:
```markdown
## Identity

**Role**: {Agent Title}

**Description**: {Clear description of the agent's purpose}

**Primary Responsibilities**:
- {Responsibility 1}
- {Responsibility 2}

**Key Characteristics**:
- {Characteristic 1}
- {Characteristic 2}
```

#### 2. Principles

Defines core principles and values that guide the agent's behavior.

**Format**:
```markdown
## Principles

**Core Principles**:
- {Principle 1}
- {Principle 2}

**Guidelines**:
- {Guideline 1}
- {Guideline 2}
```

#### 3. Communication Style

Defines how the agent communicates with users.

**Format**:
```markdown
## Communication Style

**Tone**: {e.g., professional, friendly, technical, concise}

**Verbosity**: {e.g., concise, detailed, balanced}

**Formality**: {e.g., professional, casual, formal}

**Response Patterns**:
- {Pattern 1}
- {Pattern 2}

**Examples**:
- {Example of communication style}
```

#### 4. Expertise Areas

Defines the agent's areas of expertise and specialization.

**Format**:
```markdown
## Expertise Areas

**Primary Expertise**:
- {Domain 1}: {Specialization details}
- {Domain 2}: {Specialization details}

**Technologies & Tools**:
- {Technology/Tool 1}: {Level of expertise}
- {Technology/Tool 2}: {Level of expertise}

**Specializations**:
- {Specialization 1}
- {Specialization 2}
```

#### 5. Interaction Patterns

Defines how the agent interacts with users, systems, and other agents.

**Format**:
```markdown
## Interaction Patterns

**Request Processing**:
- {How agent processes user requests}

**Typical Workflows**:
1. {Step 1}
2. {Step 2}

**Collaboration**:
- {How agent works with other agents}

**Command Patterns**:
- {Pattern for common commands}
```

#### 6. Notes (Optional)

Optional additional notes, examples, or context-specific information.

**Format**:
```markdown
## Notes

{Any additional notes, examples, or context}
```

## Complete Example

See `templates/agent_roles/implementer-role.md` for a complete example role file.

## Template

See `templates/agent_roles/ROLE_FILE_TEMPLATE.md` for a template with all sections and field descriptions.

## Usage

Role files are:

1. **Loaded during agent initialization** - Role files are automatically loaded when an agent activates
2. **Applied to agent persona** - Role definitions override or extend base agent personas
3. **Customizable** - Customization layer (Epic 1) can override role file definitions
4. **Optional** - Agents work without role files (backward compatible)

## Precedence Order

When multiple sources define agent behavior, precedence is:

1. **Customization layer** (highest priority)
2. **Role file** (if present)
3. **SKILL.md** (base definition)
4. **Framework defaults** (lowest priority)

## Integration with Existing Systems

- **SKILL.md files**: Role files complement existing SKILL.md files. If both exist, role file takes precedence.
- **BMAD pattern**: Role files follow similar markdown/YAML structure as BMAD agent files but with simpler format focused on role definition.
- **Customization layer**: Role files work with the customization layer (Epic 1) - customizations can override role file definitions.

## Creating a New Role File

1. Copy `templates/agent_roles/ROLE_FILE_TEMPLATE.md`
2. Rename to `{agent-id}-role.md`
3. Update YAML frontmatter (role_id, version, description)
4. Fill in all sections (Identity, Principles, Communication Style, Expertise Areas, Interaction Patterns)
5. Add any optional Notes section
6. Save to `templates/agent_roles/`

## Validation

Role files should:

- Have valid YAML frontmatter (required fields present)
- Have `role_id` matching the agent ID
- Include all five main sections (Identity, Principles, Communication Style, Expertise Areas, Interaction Patterns)
- Use clear, actionable language
- Be consistent with other role files in structure and format

## Migration from SKILL.md

To migrate from SKILL.md to role file format:

1. Extract identity information from SKILL.md "Identity" section
2. Extract principles from "Instructions" and "Constraints" sections
3. Infer communication style from SKILL.md tone and examples
4. Extract expertise from "Capabilities" and technology mentions
5. Extract interaction patterns from "Commands" and "Workflow" sections
6. Create role file using template
7. Keep SKILL.md for backward compatibility (role file will take precedence)

## Questions?

- See `templates/agent_roles/implementer-role.md` for a complete example
- See `templates/agent_roles/ROLE_FILE_TEMPLATE.md` for template with detailed comments
- Check agent initialization code in `tapps_agents/core/role_loader.py` (after Story 32.3 implementation)

