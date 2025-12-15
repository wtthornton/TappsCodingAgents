# Expert Setup Wizard Guide

**Interactive wizard for setting up, adding, removing, and configuring experts with RAG support.**

## Quick Start

```bash
# Interactive menu
python -m tapps_agents.cli setup-experts

# Or use specific commands
python -m tapps_agents.cli setup-experts list
python -m tapps_agents.cli setup-experts add
python -m tapps_agents.cli setup-experts remove
python -m tapps_agents.cli setup-experts init

# Cursor/CI (non-interactive)
python -m tapps_agents.cli setup-experts init --yes --non-interactive
```

## Commands

### 1. Initialize Project (`init`)

First-time setup for a new project. Creates:
- `.tapps-agents/` directory
- `domains.md` template (if needed)
- Guides you through adding your first expert

```bash
python -m tapps_agents.cli setup-experts init
```

**Non-interactive (Cursor/CI):**

```bash
python -m tapps_agents.cli setup-experts init --yes --non-interactive
```

In non-interactive mode, the wizard will:
- Use defaults and auto-confirm prompts (with `--yes`)
- Initialize Cursor Rules + workflow presets and create a `domains.md` template (if missing)
- **Skip adding experts** (because expert details require interactive input)

**What it does:**
- Creates `.tapps-agents/` directory structure
- Creates `domains.md` template if missing
- Guides you through adding your first expert
- Sets up RAG knowledge base
- Offers to add more experts

### 2. Add Expert (`add`)

Interactive wizard to add a new expert.

```bash
python -m tapps_agents.cli setup-experts add
```

**The wizard will ask:**
1. Expert name (e.g., "Home Automation Expert")
2. Expert ID (auto-generated from name, can customize)
3. Primary domain (from existing domains or create new)
4. Enable RAG? (Yes/No)
5. Create knowledge base template? (if RAG enabled)

**Example:**
```
Expert name: Home Automation Expert
Expert ID: [expert-home-automation]
Primary domain: home-automation
Enable RAG? [Y/n]: y
Create knowledge base template? [Y/n]: y
```

### 3. Remove Expert (`remove`)

Remove an expert from your configuration.

```bash
python -m tapps_agents.cli setup-experts remove
```

**The wizard will:**
- List all current experts
- Ask which one to remove
- Confirm before removing
- Update `experts.yaml`

### 4. List Experts (`list`)

Show all configured experts with their status.

```bash
python -m tapps_agents.cli setup-experts list
```

**Shows:**
- Expert name and ID
- Primary domain
- RAG enabled status
- Number of knowledge base files

**Example output:**
```
Current Experts
============================================================

1. AI Agent Framework Expert
   ID: expert-ai-frameworks
   Domain: ai-agent-framework
   RAG: Yes
   Knowledge Files: 0

2. Code Quality Expert
   ID: expert-code-quality
   Domain: code-quality-analysis
   RAG: Yes
   Knowledge Files: 3
```

## RAG Knowledge Base Setup

When you add an expert with RAG enabled, the wizard helps you:

1. **Create knowledge base directory**: `.tapps-agents/knowledge/{domain}/`
2. **Create template file**: `{domain}-knowledge.md`
3. **Guide you to add content**: Edit the template with your domain knowledge

### Knowledge Base Structure

```
.tapps-agents/
  knowledge/
    {domain-name}/
      {domain-name}-knowledge.md
      additional-files.md
      ...
```

### Knowledge File Format

The wizard creates a template like this:

```markdown
# {Expert Name} Knowledge Base

## Domain: {domain-name}

Add your domain-specific knowledge here. This file will be used for RAG (Retrieval-Augmented Generation).

### Key Concepts

### Best Practices

### Common Patterns

### References
```

## Integration with Domains

The wizard integrates with your `domains.md` file:

- **Lists existing domains** when adding experts
- **Validates expert IDs** match domain primary experts
- **Creates domain template** if missing

### Domain Configuration

Your `domains.md` should look like:

```markdown
### Domain 1: Home Automation

- **Primary Expert**: expert-home-automation
- **Description**: Smart home systems, IoT devices
- **Key Areas**: Device integration, automation patterns
```

The expert's `expert_id` must match the domain's `primary_expert_id`.

## Workflow Examples

### Example 1: First-Time Setup

```bash
# 1. Initialize project
python -m tapps_agents.cli setup-experts init

# Follow prompts:
# - Create domains.md? Yes
# - Add first expert? Yes
#   - Expert name: Healthcare Expert
#   - Domain: healthcare
#   - Enable RAG? Yes
#   - Create template? Yes

# 2. Edit knowledge base
# Edit .tapps-agents/knowledge/healthcare/healthcare-knowledge.md

# 3. Add more experts
python -m tapps_agents.cli setup-experts add
```

### Example 2: Adding Expert to Existing Project

```bash
# 1. List current experts
python -m tapps_agents.cli setup-experts list

# 2. Add new expert
python -m tapps_agents.cli setup-experts add

# Follow prompts to add expert
```

### Example 3: Removing Expert

```bash
# 1. List experts to see what's available
python -m tapps_agents.cli setup-experts list

# 2. Remove expert
python -m tapps_agents.cli setup-experts remove

# Select expert number to remove
# Confirm removal
```

## Tips

1. **Start with domains**: Define your domains in `domains.md` first, then add experts
2. **Use descriptive names**: Expert names should clearly indicate their domain
3. **Enable RAG**: Most experts benefit from RAG for knowledge retrieval
4. **Add knowledge gradually**: Start with template, add knowledge as you learn
5. **Version control**: Commit `experts.yaml` and knowledge files to git

## Troubleshooting

### Expert Not Found Error

**Problem:** `ValueError: Expert 'expert-id' not found in weight matrix`

**Solution:** Ensure `expert_id` in `experts.yaml` matches `primary_expert_id` in `domains.md`

### RAG Not Working

**Problem:** Knowledge base searches return no results

**Solution:**
1. Check `rag_enabled: true` in expert config
2. Verify knowledge files exist: `.tapps-agents/knowledge/{domain}/`
3. Ensure files are `.md` format
4. Check file encoding (should be UTF-8)

### Configuration Not Loading

**Problem:** `FileNotFoundError: Expert configuration file not found`

**Solution:**
1. Run `setup-experts init` to create `.tapps-agents/experts.yaml`
2. Check file path is correct
3. Ensure YAML syntax is valid

## See Also

- [Expert Configuration Guide](EXPERT_CONFIG_GUIDE.md) - Detailed configuration reference
- [Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md) - Setting up knowledge bases
- [Domain Configuration](../requirements/PROJECT_REQUIREMENTS.md#12-domain-configuration) - Domain definitions

