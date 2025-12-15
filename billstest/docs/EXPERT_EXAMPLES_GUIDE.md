# Expert Examples and Best Practices Guide

This guide provides real-world examples and best practices for configuring Industry Experts in your projects.

## Quick Start

### 1. Copy Template Files

```bash
# Copy expert configuration template
cp templates/experts.yaml.template .tapps-agents/experts.yaml

# Copy domains template
cp templates/domains.md.template .tapps-agents/domains.md
```

### 2. Customize for Your Project

Edit `.tapps-agents/experts.yaml` and `.tapps-agents/domains.md` with your project's domains.

### 3. Create Knowledge Bases

Create knowledge directories for each domain:
```bash
mkdir -p .tapps-agents/knowledge/{domain-name}
```

Add markdown files with domain knowledge:
```bash
.tapps-agents/knowledge/home-automation/
  ├── protocols.md
  ├── best-practices.md
  └── device-management.md
```

## Example Configurations

### Example 1: Home Automation Project

**experts.yaml:**
```yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
```

**domains.md:**
```markdown
### Domain 1: Home Automation
- **Primary Expert**: expert-home-automation
- **Description**: Smart home systems, IoT devices, automation rules
- **Key Areas**: Device protocols, automation triggers, energy management
```

**Knowledge Base Structure:**
```
.tapps-agents/knowledge/home-automation/
  ├── protocols.md              # Zigbee, Z-Wave, WiFi protocols
  ├── best-practices.md         # UX principles, automation patterns
  └── device-management.md      # Naming, organization, grouping
```

### Example 2: Healthcare Application

**experts.yaml:**
```yaml
experts:
  - expert_id: expert-healthcare
    expert_name: Healthcare Domain Expert
    primary_domain: healthcare
    rag_enabled: true
```

**domains.md:**
```markdown
### Domain 1: Healthcare
- **Primary Expert**: expert-healthcare
- **Description**: Healthcare applications, HIPAA compliance, medical data
- **Key Areas**: PHI protection, audit trails, regulatory compliance
```

**Knowledge Base Structure:**
```
.tapps-agents/knowledge/healthcare/
  ├── hipaa-compliance.md       # HIPAA requirements and safeguards
  ├── phi-handling.md           # Protected Health Information guidelines
  └── regulatory-standards.md   # Industry regulations and standards
```

### Example 3: Multi-Domain Project

**experts.yaml:**
```yaml
experts:
  - expert_id: expert-home-automation
    expert_name: Home Automation Expert
    primary_domain: home-automation
    rag_enabled: true
  
  - expert_id: expert-healthcare
    expert_name: Healthcare Domain Expert
    primary_domain: healthcare
    rag_enabled: true
  
  - expert_id: expert-energy
    expert_name: Energy Management Expert
    primary_domain: energy-management
    rag_enabled: true
```

**domains.md:**
```markdown
### Domain 1: Home Automation
- **Primary Expert**: expert-home-automation
- **Description**: Smart home systems, IoT devices

### Domain 2: Healthcare
- **Primary Expert**: expert-healthcare
- **Description**: Healthcare applications, HIPAA compliance

### Domain 3: Energy Management
- **Primary Expert**: expert-energy
- **Description**: Energy optimization, grid integration
```

## Knowledge Base Best Practices

### 1. Organize by Topic

Group related knowledge into logical files:

```
knowledge/
  ├── protocols.md              # Technical protocols and standards
  ├── best-practices.md         # Best practices and patterns
  ├── compliance.md             # Regulatory requirements
  ├── user-experience.md        # UX guidelines
  └── troubleshooting.md        # Common issues and solutions
```

### 2. Use Clear Headings

Markdown structure helps the RAG system find relevant content:

```markdown
# Main Topic

## Subsection

### Detail Level

- Bullet points for lists
- **Bold** for important terms
- `Code` for technical terms
```

### 3. Include Examples

Examples help the expert provide concrete guidance:

```markdown
## Good Automation Rule

When: Motion sensor detects motion
And: Time is between sunset and 11pm
Then: Turn on lights at 50% brightness
```

### 4. Document Decision Trees

Help the expert guide users through decisions:

```markdown
## Protocol Selection

1. Battery-powered device?
   - Yes → Zigbee or Z-Wave
   - No → Continue to #2

2. Needs high bandwidth?
   - Yes → WiFi
   - No → Zigbee or Matter
```

### 5. Include Checklists

Checklists help ensure completeness:

```markdown
## Implementation Checklist

- [ ] Encrypt all PHI at rest
- [ ] Implement access controls
- [ ] Set up audit logging
- [ ] Require MFA
```

## Expert Configuration Tips

### Enable RAG for All Domain Experts

Most experts should have RAG enabled:

```yaml
rag_enabled: true  # Enable knowledge base retrieval
```

### Use Descriptive Names

Clear names help identify experts:

```yaml
# ✅ Good
expert_name: Home Automation Expert

# ❌ Avoid
expert_name: Expert 1
```

### Match Expert IDs to Domains

Expert IDs must match primary_expert_id in domains.md:

```yaml
# experts.yaml
- expert_id: expert-home-automation

# domains.md
- **Primary Expert**: expert-home-automation  # Must match
```

## Domain Configuration Tips

### One Domain = One Primary Expert

Each domain should have exactly one primary expert:

```markdown
### Domain 1: Home Automation
- **Primary Expert**: expert-home-automation  # Only one primary per domain
```

### Clear Descriptions

Helpful descriptions improve expert consultation:

```markdown
# ✅ Good
- **Description**: Smart home systems, IoT device management, automation rules, user experience for smart homes
- **Key Areas**: Device protocols (Zigbee, Z-Wave), automation triggers, energy management

# ❌ Too vague
- **Description**: Home stuff
```

## Using Experts in Workflows

### Workflow Configuration

Configure workflow steps to consult experts:

```yaml
steps:
  - id: design
    agent: architect
    action: design_system
    consults:
      - expert-home-automation  # Consult expert during design
    context_tier: 2
```

### Agent Consultation

Agents automatically consult experts when configured:

```python
from tapps_agents.workflow import WorkflowExecutor
from tapps_agents.experts import ExpertRegistry

# Load experts
registry = ExpertRegistry.from_config_file(Path(".tapps-agents/experts.yaml"))

# Create executor with expert registry
executor = WorkflowExecutor(expert_registry=registry)

# Consult experts for a query
result = await executor.consult_experts(
    query="What protocol should I use for battery-powered sensors?",
    domain="home-automation"
)
```

## Common Patterns

### Pattern 1: Single Domain Project

One expert, one domain:

```yaml
experts:
  - expert_id: expert-{domain}
    primary_domain: {domain}
    rag_enabled: true
```

### Pattern 2: Multi-Domain Project

Multiple experts, one per domain:

```yaml
experts:
  - expert_id: expert-domain-a
    primary_domain: domain-a
  
  - expert_id: expert-domain-b
    primary_domain: domain-b
```

### Pattern 3: Expert Without RAG

For simple domains or when knowledge base not needed:

```yaml
experts:
  - expert_id: expert-simple
    primary_domain: simple-domain
    rag_enabled: false  # No knowledge base
```

## Troubleshooting

### Expert Not Found

**Problem**: `ValueError: Expert 'expert-id' not found in weight matrix`

**Solution**: 
1. Check `expert_id` matches `primary_expert_id` in `domains.md`
2. Ensure expert is registered before consultation
3. Verify domain config is loaded

### RAG Returns No Results

**Problem**: Knowledge base searches return no results

**Solution**:
1. Check `rag_enabled: true` in config
2. Verify knowledge files exist: `.tapps-agents/knowledge/{domain}/`
3. Check file format (markdown, UTF-8 encoding)
4. Verify file names end with `.md`

### Domain Config Not Loading

**Problem**: `FileNotFoundError` when loading domain config

**Solution**:
1. Create `.tapps-agents/domains.md`
2. Follow the template structure
3. Ensure all required fields are present

## See Also

- [Expert Configuration Guide](EXPERT_CONFIG_GUIDE.md) - Detailed configuration reference
- [Knowledge Base Guide](KNOWLEDGE_BASE_GUIDE.md) - Setting up knowledge bases
- [Examples Directory](../examples/experts/) - Complete example configurations

