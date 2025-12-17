# Custom Skills Guide

**TappsCodingAgents Custom Skills Creation and Management**

This guide explains how to create, manage, and share custom Skills that extend the framework's capabilities.

---

## Overview

Custom Skills allow you to create domain-specific agents that integrate seamlessly with the TappsCodingAgents framework. Custom Skills:

- ✅ **Extend Framework Capabilities**: Add specialized agents for your domain
- ✅ **Integrate with Framework**: Work with existing tools, workflows, and features
- ✅ **Override Built-in Skills**: Custom Skills take priority over built-in Skills with the same name
- ✅ **Follow Standard Format**: Use the same Cursor Skills format as built-in Skills

---

## Quick Start

### Generate a Custom Skill Template

Use the CLI command to generate a Skill template:

```bash
# Interactive mode (recommended)
tapps-agents skill-template

# Non-interactive mode
tapps-agents skill-template --name=my-custom-skill --type=implementer

# With custom options
tapps-agents skill-template \
  --name=data-engineer \
  --type=implementer \
  --tools="Read,Write,Edit,Grep,Glob,Bash" \
  --capabilities="code_generation,analysis"
```

This creates a Skill file at `.claude/skills/{skill_name}/SKILL.md` with all required fields.

### Example: Creating a Data Engineer Skill

```bash
# Generate template
tapps-agents skill-template --name=data-engineer --type=implementer

# Edit the generated file
code .claude/skills/data-engineer/SKILL.md
```

The generated template includes:
- YAML frontmatter (name, description, allowed-tools, model_profile)
- Identity section
- Instructions section
- Commands section
- Capabilities section
- Configuration section
- Constraints section
- Integration section
- Example workflow
- Best practices
- Usage examples

---

## Template Generation Process

### Step 1: Choose Agent Type

The template generator supports these built-in agent types:

- `analyst` - Requirements gathering and research
- `architect` - System design and architecture
- `debugger` - Error analysis and debugging
- `designer` - API and data model design
- `documenter` - Documentation generation
- `enhancer` - Prompt enhancement
- `implementer` - Code generation (default)
- `improver` - Code refactoring
- `ops` - Security and deployment
- `orchestrator` - Workflow coordination
- `planner` - Story creation and planning
- `reviewer` - Code review and quality
- `tester` - Test generation and execution

Each type provides sensible defaults for:
- Description
- Allowed tools
- Capabilities
- Identity focus

### Step 2: Customize Template

After generation, customize the template:

1. **Edit YAML Frontmatter**:
   ```yaml
   ---
   name: data-engineer
   description: Specialized agent for data engineering tasks
   allowed-tools: Read, Write, Edit, Grep, Glob, Bash
   model_profile: data_engineer_profile
   ---
   ```

2. **Customize Identity Section**:
   - Define the agent's persona and role
   - Specify domain expertise
   - Describe specialization areas

3. **Define Commands**:
   - Add custom commands for your domain
   - Include examples and usage patterns
   - Document command options

4. **Specify Capabilities**:
   - List what the agent can do
   - Include domain-specific capabilities
   - Reference framework features

### Step 3: Test Your Skill

1. **Verify Format**:
   ```bash
   # Check if Skill loads correctly
   python -c "from tapps_agents.core.skill_loader import initialize_skill_registry; r = initialize_skill_registry(); print(r.get_custom_skills())"
   ```

2. **Test in Cursor**:
   - Open Cursor AI IDE
   - Type `@{your-skill-name}` in chat
   - Try a command: `*help`

---

## Usage Examples

### Example 1: Data Engineer Skill

**Generate Template**:
```bash
tapps-agents skill-template --name=data-engineer --type=implementer
```

**Customized Skill** (`.claude/skills/data-engineer/SKILL.md`):
```yaml
---
name: data-engineer
description: Specialized agent for data engineering tasks including ETL pipelines, data transformations, and data quality checks.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Terminal
model_profile: data_engineer_profile
---

# Data Engineer Agent

## Identity

You are a senior data engineer focused on building robust, scalable data pipelines. You specialize in:

- **ETL Pipelines**: Creating efficient extract, transform, load processes
- **Data Quality**: Implementing data validation and quality checks
- **Performance Optimization**: Optimizing data processing for scale
- **Framework Integration**: Using TappsCodingAgents tools and workflows

## Commands

### Data Engineering Commands

- `*create-pipeline <specification> <file_path>` - Create a new ETL pipeline
  - Example: `*create-pipeline "Extract from PostgreSQL, transform, load to S3" pipelines/etl_pipeline.py`
- `*validate-data <file_path>` - Validate data quality
  - Example: `*validate-data data/raw/customers.csv`
- `*optimize-pipeline <file_path>` - Optimize pipeline performance
  - Example: `*optimize-pipeline pipelines/slow_pipeline.py`
```

### Example 2: Security Auditor Skill

**Generate Template**:
```bash
tapps-agents skill-template --name=security-auditor --type=reviewer
```

**Customized Skill** (`.claude/skills/security-auditor/SKILL.md`):
```yaml
---
name: security-auditor
description: Security-focused code reviewer for identifying vulnerabilities and security issues.
allowed-tools: Read, Grep, Glob, CodebaseSearch
model_profile: security_auditor_profile
---

# Security Auditor Agent

## Identity

You are a security expert focused on identifying and preventing security vulnerabilities. You specialize in:

- **Vulnerability Detection**: Finding security issues in code
- **Security Best Practices**: Ensuring code follows security guidelines
- **Compliance**: Checking compliance with security standards
- **Threat Modeling**: Analyzing security threats

## Commands

### Security Commands

- `*audit <file_path>` - Perform security audit
  - Example: `*audit api/auth.py`
- `*check-secrets <directory>` - Check for exposed secrets
  - Example: `*check-secrets src/`
- `*validate-oauth <file_path>` - Validate OAuth implementation
  - Example: `*validate-oauth api/oauth.py`
```

---

## Best Practices

### 1. Follow Standard Format

- Use YAML frontmatter with required fields
- Include all standard sections (Identity, Instructions, Commands, Capabilities, etc.)
- Follow the same structure as built-in Skills

### 2. Be Specific in Descriptions

- Clearly describe what the agent does
- Specify when to use the agent
- Include domain-specific context

### 3. Document Commands Thoroughly

- Provide clear command syntax
- Include multiple examples
- Document all options and flags
- Explain expected behavior

### 4. Define Clear Capabilities

- List what the agent can do
- Specify limitations
- Reference framework features when applicable

### 5. Include Constraints

- Specify what the agent should NOT do
- Define boundaries and limitations
- Reference when to use other agents

### 6. Test Before Sharing

- Verify the Skill loads correctly
- Test commands in Cursor
- Ensure integration with framework features
- Check for conflicts with built-in Skills

### 7. Version Control

- Track Skill changes in git
- Document version history
- Tag releases for sharing

---

## Skill Priority System

Custom Skills take priority over built-in Skills with the same name:

1. **Custom Skills** (`.claude/skills/`) - Highest priority
2. **Built-in Skills** (`tapps_agents/resources/claude/skills/`) - Fallback

**Example**:
- If you create `.claude/skills/reviewer/SKILL.md`, it will override the built-in reviewer Skill
- Use this to customize built-in Skills for your project

**Best Practice**: Use unique names for custom Skills to avoid conflicts:
- ✅ `data-engineer` (unique)
- ✅ `security-auditor` (unique)
- ❌ `reviewer` (conflicts with built-in)

---

## Integration with Framework

### Framework Features Available

Custom Skills can use:

- **Tools**: Read, Write, Edit, Grep, Glob, Bash, Terminal, CodebaseSearch
- **Context7 Integration**: Library documentation lookup
- **Workflow Integration**: Work with workflow executor
- **State Management**: Access workflow state
- **Configuration**: Load from `.tapps-agents/config.yaml`

### Accessing Framework Context

Skills can reference framework features in their documentation:

```markdown
## Integration

- **Framework**: Integrates with TappsCodingAgents framework
- **Tools**: Uses specified tools: Read, Write, Edit, Grep, Glob
- **Config System**: Loads configuration from `.tapps-agents/config.yaml`
- **Context7**: Can use `*docs` commands for library documentation
```

---

## Sharing Custom Skills

### Export Skill

To share a Skill, simply copy the Skill directory:

```bash
# Copy Skill directory
cp -r .claude/skills/data-engineer /path/to/share/

# Or create a tarball
tar -czf data-engineer-skill.tar.gz .claude/skills/data-engineer/
```

### Import Skill

To use a shared Skill:

```bash
# Copy Skill directory
cp -r /path/to/shared/data-engineer .claude/skills/

# Or extract tarball
tar -xzf data-engineer-skill.tar.gz -C .claude/skills/
```

### Skill Metadata

Consider adding metadata to your Skill for sharing:

```yaml
---
name: data-engineer
description: Specialized agent for data engineering tasks
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model_profile: data_engineer_profile
version: 1.0.0
author: Your Name
license: MIT
---
```

---

## Troubleshooting

### Skill Not Loading

1. **Check Directory Structure**:
   ```bash
   ls .claude/skills/{skill-name}/SKILL.md
   ```

2. **Verify YAML Format**:
   - Check YAML frontmatter syntax
   - Ensure required fields are present
   - Validate YAML with a parser

3. **Check Skill Registry**:
   ```bash
   python -c "from tapps_agents.core.skill_loader import initialize_skill_registry; r = initialize_skill_registry(); print(r.get_all_skills())"
   ```

### Skill Not Appearing in Cursor

1. **Restart Cursor**: Close and reopen Cursor AI IDE
2. **Check Skill Name**: Ensure Skill name matches directory name
3. **Verify Format**: Check that Skill follows standard format

### Commands Not Working

1. **Check Command Syntax**: Verify command format matches documentation
2. **Test in Cursor**: Try commands directly in Cursor chat
3. **Review Instructions**: Ensure Instructions section is clear

---

## Advanced Topics

### Custom Model Profiles

Define custom model profiles in `.tapps-agents/config.yaml`:

```yaml
model_profiles:
  data_engineer_profile:
    temperature: 0.7
    max_tokens: 4000
    system_prompt: "You are a data engineering expert..."
```

### Skill Dependencies

Skills can reference other Skills in their documentation:

```markdown
## Dependencies

- Uses `@reviewer` for code quality checks
- Integrates with `@tester` for test generation
```

### Skill Composition

Create composite Skills that combine multiple capabilities:

```markdown
## Capabilities

### Primary Capabilities
- Data pipeline creation
- Data quality validation

### Integrated Capabilities
- Code review (via @reviewer)
- Test generation (via @tester)
```

---

## Next Steps

1. **Generate Your First Skill**: Use `tapps-agents skill-template` to create a custom Skill
2. **Customize Template**: Edit the generated template for your domain
3. **Test in Cursor**: Verify the Skill works in Cursor AI IDE
4. **Share with Team**: Export and share your custom Skills
5. **Iterate**: Refine Skills based on usage and feedback

---

## Related Documentation

- [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md) - Installing built-in Skills
- [Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md) - Auto-execution with Background Agents
- [Workflow Selection Guide](WORKFLOW_SELECTION_GUIDE.md) - Using workflows with Skills

---

## Support

- **Documentation**: See [docs/](../docs/) directory
- **Issues**: Report on GitHub
- **Community**: Join discussions

