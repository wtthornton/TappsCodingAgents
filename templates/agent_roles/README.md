# Agent Role Files

This directory contains agent role definition files that define agent identity, principles, communication style, expertise areas, and interaction patterns.

## Directory Organization

All role files follow the naming convention: `{agent-id}-role.md`

### Core Agent Role Files

- `analyst-role.md` - Business analyst and technical researcher
- `architect-role.md` - System architect and design specialist
- `implementer-role.md` - Code implementation specialist
- `reviewer-role.md` - Code reviewer and quality assurance specialist
- `tester-role.md` - QA engineer and test specialist

### Template and Documentation

- `ROLE_FILE_TEMPLATE.md` - Template for creating new role files
- `README.md` - This file (directory documentation)

## File Format

Each role file follows a standardized format with:

1. **YAML Frontmatter** - Metadata (role_id, version, description, etc.)
2. **Identity** - Who the agent is and their primary responsibilities
3. **Principles** - Core principles and guidelines
4. **Communication Style** - How the agent communicates
5. **Expertise Areas** - Areas of expertise and specialization
6. **Interaction Patterns** - How the agent interacts with users and other agents
7. **Notes** - Additional context-specific information

See `ROLE_FILE_TEMPLATE.md` for a complete template with detailed explanations.

## Usage

Role files are:

- **Loaded during agent initialization** - Automatically loaded when agents activate
- **Applied to agent persona** - Role definitions override or extend base personas
- **Customizable** - Customization layer can override role file definitions
- **Optional** - Agents work without role files (backward compatible)

## Precedence Order

When multiple sources define agent behavior:

1. **Customization layer** (highest priority)
2. **Role file** (if present)
3. **SKILL.md** (base definition)
4. **Framework defaults** (lowest priority)

## Creating a New Role File

1. Copy `ROLE_FILE_TEMPLATE.md`
2. Rename to `{agent-id}-role.md`
3. Update YAML frontmatter (role_id must match agent ID)
4. Fill in all sections based on agent's SKILL.md file
5. Save to `templates/agent_roles/`

## Documentation

- See `docs/AGENT_ROLE_FILE_FORMAT.md` for complete format documentation
- See `ROLE_FILE_TEMPLATE.md` for template with detailed comments
- See `implementer-role.md` for a complete example

