# User Role Templates Guide

User role templates customize agent behavior based on your role (senior developer, junior developer, tech lead, product manager, QA engineer, etc.). They provide sensible defaults that can be customized per-project.

## Overview

Role templates allow you to configure agents to match your working style and expertise level. For example:
- **Senior developers** get concise communication and architecture-focused priorities
- **Junior developers** get detailed explanations and learning-focused guidance
- **Product managers** get verbose analysis and business-focused priorities
- **QA engineers** get test-first emphasis and thorough review settings

## Available Role Templates

The following role templates are available in `templates/user_roles/`:

1. **senior-developer.yaml** - For experienced developers
2. **junior-developer.yaml** - For learning-focused developers
3. **tech-lead.yaml** - For technical leaders
4. **product-manager.yaml** - For product managers
5. **qa-engineer.yaml** - For QA engineers

## Selecting a Role Template

### Method 1: Via Configuration File

Add the `user_role` field to your `.tapps-agents/config.yaml`:

```yaml
# User role template selection
user_role: senior-developer
```

### Method 2: During Project Initialization

When initializing a project, you can manually set the role in the config file after running `tapps-agents init`.

## How Role Templates Work

### Application Order

Role templates are applied in this order (later overrides earlier):

1. **Base agent configuration** - Default agent settings
2. **User role template** - Role-specific defaults
3. **Project customizations** - Project-specific overrides

This ensures that:
- Role templates provide sensible defaults
- Customizations can override role templates
- Base configuration is always the foundation

### Configuration Sections

Role templates customize these aspects of agent behavior:

#### Verbosity

Controls communication style:
- `level`: "concise" | "balanced" | "verbose"
- `explanations`: Include detailed explanations
- `examples`: Include code examples
- `learning_focus`: Learning-oriented explanations

#### Workflow Defaults

Sets default workflow preferences:
- `auto_approve`: Auto-approve code changes
- `require_review`: Require code review
- `test_first`: Emphasize test-first approach
- `progressive_review`: Use progressive code review
- `documentation_emphasis`: "minimal" | "standard" | "comprehensive"

#### Expert Priorities

Prioritizes expert consultation by role needs:
- Values range from 0.0 (no priority) to 1.0 (highest priority)
- Higher values mean that expert is consulted more frequently
- Example: `expert-software-architecture: 0.9` prioritizes architecture guidance

#### Documentation Preferences

Controls documentation generation:
- `detail_level`: "minimal" | "standard" | "comprehensive"
- `include_examples`: Include code examples
- `include_diagrams`: Include diagrams
- `docstring_format`: "google" | "numpy" | "sphinx"

#### Review Depth

Sets code review thoroughness:
- `level`: "light" | "standard" | "thorough"
- `security_focus`: Emphasize security reviews
- `performance_focus`: Emphasize performance reviews
- `test_coverage_focus`: Emphasize test coverage

## Role-Specific Behaviors

### Senior Developer

- **Communication**: Concise, assumes expertise
- **Workflow**: Auto-approve enabled, progressive review
- **Priorities**: Architecture, API design, performance
- **Use Case**: Experienced developers working on production code

**Example Behavior**:
```
Agent: "Implemented authentication middleware using JWT. Ready for review."
(Concise, assumes understanding of JWT)
```

### Junior Developer

- **Communication**: Verbose, detailed explanations
- **Workflow**: Requires review, comprehensive documentation
- **Priorities**: Code quality, testing, documentation
- **Use Case**: Learning developers new to codebase/technology

**Example Behavior**:
```
Agent: "I've implemented authentication middleware using JWT (JSON Web Tokens). 
JWT is a stateless authentication mechanism that encodes user information in 
a token. Here's how it works: [detailed explanation]. Would you like me to 
explain any part in more detail?"
(Verbose, educational)
```

### Tech Lead

- **Communication**: Balanced, architecture-focused
- **Workflow**: Requires review, comprehensive documentation
- **Priorities**: Architecture, security, observability, scalability
- **Use Case**: Technical leaders making architectural decisions

**Example Behavior**:
```
Agent: "Implemented authentication middleware. Architecture considerations:
- Security: JWT with refresh tokens
- Scalability: Stateless design supports horizontal scaling
- Observability: Added logging for auth events
Recommend reviewing security patterns before deployment."
(Balanced, strategic)
```

### Product Manager

- **Communication**: Verbose, business-focused
- **Workflow**: Comprehensive documentation, business context emphasis
- **Priorities**: User experience, documentation, accessibility
- **Use Case**: Product managers gathering requirements

**Example Behavior**:
```
Agent: "Implemented authentication feature. Business impact:
- Improves user experience with secure, seamless login
- Supports accessibility standards (WCAG 2.1)
- Privacy-compliant data handling (GDPR considerations)
User flows: [detailed user journey explanation]"
(Verbose, business context)
```

### QA Engineer

- **Communication**: Balanced, test-focused
- **Workflow**: Test-first approach, thorough reviews
- **Priorities**: Testing, code quality, security, accessibility
- **Use Case**: QA engineers writing test cases

**Example Behavior**:
```
Agent: "Implemented authentication middleware. Test coverage:
- Unit tests: JWT validation, token expiration
- Integration tests: Auth flow, error handling
- Edge cases: Invalid tokens, expired tokens, malformed tokens
Security test cases: [detailed test scenarios]"
(Balanced, test-focused)
```

## Customizing Role Templates

You can override role template settings using project customizations (`.tapps-agents/customizations/{agent-id}-custom.yaml`):

```yaml
# Override role template settings
persona_overrides:
  communication_style:
    verbosity: concise  # Override role template verbosity

project_context:
  expert_priorities:
    expert-security: 1.0  # Increase security priority beyond role template
```

## Creating Custom Role Templates

To create a custom role template:

1. Copy an existing template from `templates/user_roles/`:
   ```bash
   cp templates/user_roles/senior-developer.yaml templates/user_roles/my-custom-role.yaml
   ```

2. Modify the configuration sections to match your role's needs

3. Update metadata:
   ```yaml
   role_id: my-custom-role
   description: "Description of your custom role"
   use_cases:
     - "When to use this role template"
   ```

4. Set the role in your config:
   ```yaml
   user_role: my-custom-role
   ```

## Troubleshooting

### Role template not being applied

**Problem**: Role template settings don't seem to affect agent behavior.

**Solution**:
1. Verify `user_role` is set in `.tapps-agents/config.yaml`
2. Check that the role template file exists in `templates/user_roles/{role_id}.yaml`
3. Verify the YAML syntax is valid
4. Check agent logs for role template loading errors

### Conflicting settings

**Problem**: Customizations seem to override role template in unexpected ways.

**Solution**: Remember the precedence order:
1. Base config
2. Role template
3. Customizations (highest priority)

To preserve role template settings, don't override them in customizations, or explicitly merge values.

### Role template not found

**Problem**: Warning message "Role template not found: {role_id}".

**Solution**:
1. Check spelling of role_id in config
2. Verify template file exists in `templates/user_roles/`
3. Check file permissions
4. Verify YAML syntax is valid

### Agent behavior unchanged

**Problem**: Agent behavior doesn't change after setting role template.

**Solution**:
- Role templates provide defaults; agents must use the loaded template
- Some agents may not support all role template settings
- Check agent-specific documentation for role template support

## Integration with Customization Layer

Role templates integrate seamlessly with the customization layer (Epic 1):

- Role templates are loaded before customizations
- Customizations can override role template settings
- Both use the same configuration structure
- Precedence: Base → Role Template → Customizations

## Examples

### Example 1: Switching from Junior to Senior Role

**Before** (junior-developer):
```yaml
user_role: junior-developer
```
Agent provides detailed explanations for all actions.

**After** (senior-developer):
```yaml
user_role: senior-developer
```
Agent provides concise communication, assumes expertise.

### Example 2: PM Working on Technical Project

```yaml
user_role: product-manager
```

Agent emphasizes:
- Business impact of technical decisions
- User experience considerations
- Documentation and accessibility
- Verbose explanations for technical concepts

### Example 3: Custom Role for DevOps Engineer

Create `templates/user_roles/devops-engineer.yaml`:
```yaml
role_id: devops-engineer
description: "Optimized for DevOps engineers"
verbosity:
  level: balanced
workflow_defaults:
  test_first: true
  documentation_emphasis: comprehensive
expert_priorities:
  expert-devops: 1.0
  expert-cloud-infrastructure: 0.9
  expert-observability: 0.8
```

## Related Documentation

- [Customization Guide](CUSTOMIZATION_GUIDE.md) - Project-specific customizations
- [Agent Configuration](CONFIGURATION.md) - Agent configuration reference
- [Expert System Guide](EXPERT_SETUP_WIZARD.md) - Expert consultation system

## See Also

- `templates/user_roles/README.md` - Template format reference
- `templates/user_roles/TEMPLATE_FORMAT.yaml` - Complete template example

