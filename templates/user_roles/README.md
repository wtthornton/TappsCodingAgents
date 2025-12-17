# User Role Templates

User role templates customize agent behavior based on user role (senior developer, junior developer, tech lead, product manager, QA engineer, etc.). These templates provide sensible defaults that can be customized per-project.

## Template Format

User role templates are YAML files that define role-specific agent configurations. The format consists of metadata and configuration sections.

### Metadata Section

The metadata section identifies and describes the role template:

```yaml
# Role metadata
role_id: string              # Unique identifier (e.g., "senior-developer")
description: string          # Human-readable description
use_cases: list[string]      # When to use this role template
```

### Configuration Sections

The configuration sections customize agent behavior:

#### verbosity

Controls communication verbosity and detail level:

```yaml
verbosity:
  level: string              # "concise" | "balanced" | "verbose"
  explanations: boolean      # Include detailed explanations
  examples: boolean          # Include code examples
  learning_focus: boolean    # Learning-oriented explanations (for juniors)
```

#### workflow_defaults

Sets default workflow preferences:

```yaml
workflow_defaults:
  auto_approve: boolean      # Auto-approve code changes
  require_review: boolean    # Require code review
  test_first: boolean        # Emphasize test-first approach
  progressive_review: boolean # Use progressive code review
  documentation_emphasis: string  # "minimal" | "standard" | "comprehensive"
```

#### expert_priorities

Prioritizes expert consultation by role needs:

```yaml
expert_priorities:
  expert-analyst: float      # Priority 0.0-1.0 (higher = more emphasis)
  expert-architect: float
  expert-planner: float
  expert-tester: float
  # ... other experts as needed
```

#### documentation_preferences

Controls documentation generation:

```yaml
documentation_preferences:
  detail_level: string       # "minimal" | "standard" | "comprehensive"
  include_examples: boolean  # Include code examples
  include_diagrams: boolean  # Include diagrams where applicable
  docstring_format: string   # "google" | "numpy" | "sphinx"
```

#### review_depth

Sets code review thoroughness:

```yaml
review_depth:
  level: string              # "light" | "standard" | "thorough"
  security_focus: boolean    # Emphasize security reviews
  performance_focus: boolean # Emphasize performance reviews
  test_coverage_focus: boolean # Emphasize test coverage
```

## Complete Example

```yaml
# Role metadata
role_id: senior-developer
description: "Optimized for experienced developers who prefer concise communication and assume expertise"
use_cases:
  - "Senior engineers writing production code"
  - "Experienced developers working on complex features"
  - "Team leads implementing architectural patterns"

# Communication verbosity
verbosity:
  level: concise
  explanations: false
  examples: true
  learning_focus: false

# Workflow defaults
workflow_defaults:
  auto_approve: true
  require_review: false
  test_first: true
  progressive_review: true
  documentation_emphasis: standard

# Expert priorities (0.0 = no priority, 1.0 = highest priority)
expert_priorities:
  expert-software-architecture: 0.9
  expert-api-design: 0.8
  expert-performance: 0.7
  expert-security: 0.6
  expert-testing: 0.5

# Documentation preferences
documentation_preferences:
  detail_level: standard
  include_examples: true
  include_diagrams: false
  docstring_format: google

# Review depth
review_depth:
  level: standard
  security_focus: true
  performance_focus: true
  test_coverage_focus: true
```

## Template Location

Role templates are stored in `templates/user_roles/` and follow the naming pattern `{role_id}.yaml`.

## Application Order

Role templates are applied in this order (later overrides earlier):

1. Base agent configuration
2. User role template
3. Project customizations (if any)

This ensures that customizations can override role templates, but role templates provide sensible defaults.

## Creating Custom Role Templates

To create a custom role template:

1. Copy an existing template as a starting point
2. Modify the configuration sections to match your role's needs
3. Save as `templates/user_roles/{your-role-id}.yaml`
4. Reference it in your project configuration

