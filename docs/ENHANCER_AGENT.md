# Enhancer Agent - Prompt Enhancement Utility

## Overview

The Enhancer Agent is a prompt amplification utility that transforms simple user prompts into comprehensive, context-aware prompts by running them through all TappsCodingAgents capabilities. It acts as a meta-agent that coordinates multiple agents and systems to enrich prompts with requirements, architecture, domain expertise, quality standards, and implementation strategies.

## Features

### 7-Stage Enhancement Pipeline

1. **Analysis Stage**: Detects prompt intent, scope, domains, and workflow type
2. **Requirements Stage**: Gathers functional/non-functional requirements with Industry Expert consultation
3. **Architecture Stage**: Provides system design guidance and patterns
4. **Codebase Context Stage**: Injects relevant codebase context and related files
5. **Quality Standards Stage**: Defines security, testing, and quality thresholds
6. **Implementation Strategy Stage**: Creates task breakdown and implementation order
7. **Synthesis Stage**: Combines all stages into final enhanced prompt

### Industry Expert Integration

- **Automatic Domain Detection**: Identifies relevant domains from prompt
- **Multi-Expert Consultation**: Consults all relevant experts with weighted decision-making
- **Weighted Consensus**: Primary expert (51%) + Secondary experts (49% split)
- **RAG Enhancement**: Uses knowledge bases for domain-specific patterns
- **Agreement Metrics**: Provides confidence and agreement levels

### Multiple Usage Modes

- **Full Enhancement**: All 7 stages (comprehensive)
- **Quick Enhancement**: Stages 1-3 only (fast iteration)
- **Stage-by-Stage**: Run individual stages for debugging/customization
- **Session Management**: Resume interrupted enhancements

### Output Formats

- **Markdown**: Human-readable enhanced prompt
- **JSON**: Structured data for programmatic use
- **YAML**: Configuration-friendly format

## Installation

The Enhancer Agent is included in TappsCodingAgents. No additional installation required.

## Quick Start

### Basic Usage

```bash
# Full enhancement
python -m tapps_agents.cli enhancer enhance "Create a login system"

# Quick enhancement
python -m tapps_agents.cli enhancer enhance-quick "Add user authentication"

# Save to file
python -m tapps_agents.cli enhancer enhance "Create payment system" --output enhanced.md
```

### CLI Commands

```bash
# Full enhancement pipeline
python -m tapps_agents.cli enhancer enhance <prompt> [--format markdown|json|yaml] [--output <file>] [--config <config.yaml>]

# Quick enhancement (stages 1-3)
python -m tapps_agents.cli enhancer enhance-quick <prompt> [--format markdown|json|yaml] [--output <file>]

# Run specific stage
python -m tapps_agents.cli enhancer enhance-stage <stage> [--prompt <prompt>] [--session-id <id>]

# Resume session
python -m tapps_agents.cli enhancer enhance-resume <session-id>
```

## Configuration

Create `.tapps-agents/enhancement-config.yaml`:

```yaml
enhancement:
  stages:
    analysis: true
    requirements: true
    architecture: true
    codebase_context: true
    quality: true
    implementation: true
    synthesis: true
  
  requirements:
    consult_experts: true
    min_expert_confidence: 0.7
    include_nfr: true
  
  architecture:
    context7_enabled: true
    include_patterns: true
  
  codebase_context:
    tier: TIER2
    include_related: true
    max_related_files: 10
  
  quality:
    include_security: true
    include_testing: true
    scoring_threshold: 70.0
  
  synthesis:
    format: markdown
    include_metadata: true
```

## Example Output

### Input Prompt
```
"Create a login system"
```

### Enhanced Output (Markdown)

```markdown
# Enhanced Prompt: Create a login system

## Metadata
- **Intent**: Feature (authentication)
- **Domain**: security, user-management
- **Scope**: Medium (3-5 files)
- **Workflow**: greenfield

## Requirements

### Functional Requirements
- User authentication with email/password
- Session management
- Password reset functionality
- Account verification

### Domain Context (from Industry Experts)

#### Security Domain
**Primary Expert (expert-security, 51%):**
- OAuth2.0 or JWT-based authentication required
- Rate limiting: 5 attempts per 15 minutes
- Password requirements: 12+ chars, mixed case, numbers, symbols
- Session timeout: 30 minutes with refresh tokens
- MFA recommended for admin accounts

**Additional Expert Input:**
- [expert-user-management (24.5%)]: User model should include last_login, failed_attempts, account_status
- [expert-compliance (24.5%)]: GDPR compliance requires consent tracking

**Agreement**: 85% (high consensus)
**Confidence**: 0.92

## Architecture Guidance
- Service layer pattern for authentication logic
- JWT token management
- Password hashing with bcrypt
- Session storage in Redis

## Quality Standards
- **Security Score**: Minimum 8.0/10
- **Test Coverage**: 80% minimum
- **Overall Score Threshold**: 70.0

## Implementation Strategy
1. Create User model with authentication fields
2. Implement AuthService with login/logout
3. Create API endpoints for authentication
4. Add password reset flow
5. Write unit and integration tests
```

## Integration with Industry Experts

The Enhancer automatically:

1. **Detects Domains**: Analyzes prompt for domain keywords
2. **Loads Expert Registry**: From `.tapps-agents/domains.md`
3. **Consults Experts**: All relevant experts with weighted aggregation
4. **Injects Domain Knowledge**: Business rules, patterns, best practices
5. **Provides Metrics**: Agreement level, confidence, sources

### Expert Consultation Flow

```
Prompt: "Create payment system"
    ↓
Domain Detection: payments, security, compliance
    ↓
Expert Consultation:
  - expert-payments (primary, 51%)
  - expert-security (24.5%)
  - expert-compliance (24.5%)
    ↓
Weighted Aggregation
    ↓
Domain Context in Enhanced Prompt
```

## Session Management

Sessions are saved to `.tapps-agents/sessions/`:

- **Session ID**: 8-character hash
- **Metadata**: Original prompt, timestamps, config
- **Stage Results**: All stage outputs
- **Resume Capability**: Continue interrupted enhancements

```bash
# Start enhancement
python -m tapps_agents.cli enhancer enhance "Create login" 
# Returns: session_id: abc12345

# Resume later
python -m tapps_agents.cli enhancer enhance-resume abc12345
```

## Workflow Integration

Use in YAML workflows:

```yaml
id: prompt-enhancement
steps:
  - id: enhance
    agent: enhancer
    action: enhance
    creates: ["enhanced_prompt"]
```

See `workflows/prompt-enhancement.yaml` for complete workflow.

## Best Practices

1. **Start Quick**: Use `enhance-quick` for initial exploration
2. **Go Full**: Use `enhance` for production-ready prompts
3. **Configure Experts**: Set up `domains.md` for expert consultation
4. **Customize Stages**: Adjust config to skip unnecessary stages
5. **Review Stages**: Use `enhance-stage` to inspect individual stages
6. **Save Sessions**: Use session IDs for iterative refinement

## Architecture

### Component Integration

```
Enhancer Agent
    ├─ Analyst Agent (requirements)
    ├─ Architect Agent (design)
    ├─ Designer Agent (patterns)
    ├─ Planner Agent (tasks)
    ├─ Reviewer Agent (quality)
    ├─ Ops Agent (security)
    ├─ Expert Registry (domain knowledge)
    ├─ Context Manager (codebase context)
    └─ Workflow Executor (orchestration)
```

### Data Flow

```
Simple Prompt
    ↓
[Analysis] → Intent, Domains, Scope
    ↓
[Requirements] → Functional/NFR + Expert Consultation
    ↓
[Architecture] → Design Patterns + Technology
    ↓
[Codebase Context] → Related Files + Patterns
    ↓
[Quality] → Standards + Thresholds
    ↓
[Implementation] → Tasks + Order
    ↓
[Synthesis] → Enhanced Prompt
```

## Troubleshooting

### No Experts Consulted
- Ensure `.tapps-agents/domains.md` exists
- Check domain detection in analysis stage
- Verify expert registry initialization

### Missing Context
- Check codebase context stage configuration
- Verify tiered context settings
- Ensure related files exist

### Stage Failures
- Use `enhance-stage` to debug individual stages
- Check agent dependencies
- Review session logs in `.tapps-agents/sessions/`

## Future Enhancements

- [ ] Context7 KB integration for pattern lookup
- [ ] Advanced codebase analysis with AST
- [ ] Multi-format output templates
- [ ] Prompt versioning and diff
- [ ] Batch enhancement for multiple prompts
- [ ] Integration with IDE extensions

## See Also

- [Agent Skills](../agents/enhancer/SKILL.md)
- [Enhancement Config Template](../templates/enhancement-config.yaml)
- [Prompt Enhancement Workflow](../workflows/prompt-enhancement.yaml)
- [Industry Experts Guide](../docs/EXPERT_CONFIG_GUIDE.md)

