# Enhancer Agent Skill

## Overview

The Enhancer Agent transforms simple prompts into comprehensive, context-aware prompts by running them through all TappsCodingAgents capabilities. It acts as a prompt amplification utility that enriches user input with requirements analysis, architecture guidance, domain expertise, quality standards, and implementation strategies.

## Capabilities

### Full Enhancement Pipeline
- **Analysis**: Detects intent, scope, domains, and workflow type
- **Requirements**: Gathers functional/non-functional requirements with expert consultation
- **Architecture**: Provides system design guidance and patterns
- **Codebase Context**: Injects relevant codebase context and patterns
- **Quality Standards**: Defines security, testing, and quality thresholds
- **Implementation Strategy**: Creates task breakdown and implementation order
- **Synthesis**: Combines all stages into final enhanced prompt

### Quick Enhancement
- Fast path through stages 1-3 (analysis, requirements, architecture)
- Suitable for initial exploration and quick iterations

### Stage-by-Stage Execution
- Run specific stages independently
- Resume interrupted sessions
- Debug and customize individual stages

## Commands

### *enhance
Full enhancement pipeline through all stages.

**Usage:**
```
*enhance "Create a login system"
*enhance "Create a login system" --format json --output enhanced.md
```

**Options:**
- `--format`: Output format (markdown, json, yaml)
- `--output`: Output file path
- `--config`: Custom enhancement config file

### *enhance-quick
Quick enhancement (stages 1-3 only).

**Usage:**
```
*enhance-quick "Add user authentication"
```

### *enhance-stage
Run a specific enhancement stage.

**Usage:**
```
*enhance-stage analysis "Create payment system"
*enhance-stage requirements --session-id abc123
```

**Available Stages:**
- `analysis`: Prompt intent and scope analysis
- `requirements`: Requirements gathering with expert consultation
- `architecture`: Architecture guidance
- `codebase_context`: Codebase context injection
- `quality`: Quality standards definition
- `implementation`: Implementation strategy
- `synthesis`: Final prompt synthesis

### *enhance-resume
Resume an interrupted enhancement session.

**Usage:**
```
*enhance-resume abc123
```

## Integration with Other Agents

The Enhancer Agent coordinates with:
- **Analyst**: Requirements gathering and analysis
- **Architect**: System design guidance
- **Designer**: API and data model patterns
- **Planner**: Task breakdown and implementation order
- **Reviewer**: Quality standards and thresholds
- **Ops**: Security and compliance requirements
- **Industry Experts**: Domain-specific knowledge and business rules

## Expert Consultation

When domains are detected, the Enhancer automatically:
1. Identifies relevant Industry Experts
2. Consults all experts with weighted decision-making
3. Aggregates responses (Primary 51%, Others 49%)
4. Includes domain context in enhanced prompt
5. Provides agreement metrics and confidence levels

## Output Formats

### Markdown (Default)
Human-readable enhanced prompt with sections for:
- Metadata
- Requirements
- Domain Context (from experts)
- Architecture Guidance
- Quality Standards
- Implementation Strategy

### JSON
Structured output with all stage results and metadata.

### YAML
Configuration-friendly format for further processing.

## Configuration

Create `.tapps-agents/enhancement-config.yaml` to customize:

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
  
  codebase_context:
    tier: TIER2
    max_related_files: 10
```

## Session Management

Enhancement sessions are saved to `.tapps-agents/sessions/` for:
- Resuming interrupted enhancements
- Reviewing stage results
- Debugging enhancement pipeline
- Reusing analysis results

## Examples

### Example 1: Full Enhancement
```
*enhance "Create a payment processing system"
```

**Output**: Comprehensive enhanced prompt with:
- Payment domain requirements (from expert-payments)
- Security requirements (from expert-security)
- Architecture patterns (from architect)
- Quality gates (from reviewer)
- Implementation tasks (from planner)

### Example 2: Quick Enhancement
```
*enhance-quick "Add user authentication"
```

**Output**: Fast enhancement with analysis, requirements, and architecture only.

### Example 3: Stage-by-Stage
```
*enhance-stage analysis "Create login system"
*enhance-stage requirements --session-id abc123
*enhance-stage architecture --session-id abc123
```

**Output**: Individual stage results for manual review and customization.

## Best Practices

1. **Start with Quick Enhancement**: Use `*enhance-quick` for initial exploration
2. **Use Full Enhancement for Production**: Use `*enhance` for comprehensive prompts
3. **Customize Configuration**: Adjust stages and settings per project needs
4. **Leverage Expert Knowledge**: Ensure `domains.md` is configured for expert consultation
5. **Review Stage Results**: Use `*enhance-stage` to review and customize individual stages
6. **Save Sessions**: Use session IDs to resume and iterate on enhancements

## Integration with Workflows

The Enhancer can be used within YAML workflows:

```yaml
- id: enhance-prompt
  agent: enhancer
  action: enhance
  creates: ["enhanced_prompt"]
```

See `workflows/prompt-enhancement.yaml` for complete workflow definition.

