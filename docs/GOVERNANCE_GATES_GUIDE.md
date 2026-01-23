# Governance & Safety Gates Guide

Complete guide to pluggable gates system for security, policy, and approval enforcement.

## Overview

TappsCodingAgents provides a pluggable gates system that extends quality gates with:
- **Security Gates**: Detect secrets, PII, and vulnerabilities
- **Policy Gates**: Enforce compliance (GDPR, HIPAA, PCI-DSS) and custom policies
- **Approval Gates**: Human-in-loop approval mechanisms

## Pluggable Gates Architecture

### Base Gate Interface

All gates implement the `BaseGate` interface:

```python
from tapps_agents.quality.gates.base import BaseGate, GateResult, GateSeverity

class CustomGate(BaseGate):
    def evaluate(self, context: dict[str, Any]) -> GateResult:
        # Gate evaluation logic
        return GateResult(
            passed=True,
            severity=GateSeverity.INFO,
            message="Gate passed",
        )
```

### Gate Result

Gate evaluation returns a `GateResult` with:
- **passed**: Boolean indicating if gate passed
- **severity**: INFO, WARNING, ERROR, or CRITICAL
- **message**: Human-readable message
- **details**: Optional detailed information
- **remediation**: Optional remediation steps
- **metadata**: Optional additional metadata

## Built-in Gates

### Security Gate

The security gate checks for:
- **Secrets**: API keys, tokens, passwords
- **PII**: Social security numbers, credit cards, emails
- **Credentials**: Username/password pairs
- **Vulnerabilities**: Dependency vulnerabilities (when configured)

**Configuration:**
```yaml
# .tapps-agents/config.yaml
gates:
  security:
    filter_secrets: true
    filter_tokens: true
    filter_credentials: true
    filter_pii: true
    check_dependencies: false
```

**Usage in Workflow:**
```yaml
steps:
  - id: implement
    agent: implementer
    action: implement
    gates:
      - name: security
        config:
          filter_secrets: true
          filter_pii: true
```

**Python API:**
```python
from tapps_agents.quality.gates.security_gate import SecurityGate

gate = SecurityGate(config={
    "filter_secrets": True,
    "filter_pii": True,
})

result = gate.evaluate({
    "content": "api_key = 'sk-1234567890'",
    "file_path": "src/config.py",
})

if not result.passed:
    print(f"Security gate failed: {result.message}")
```

### Policy Gate

The policy gate enforces:
- **GDPR Compliance**: Data protection and privacy
- **HIPAA Compliance**: Healthcare data protection
- **PCI-DSS Compliance**: Payment card data security
- **Custom Policies**: Project-specific policies

**Configuration:**
```yaml
# .tapps-agents/config.yaml
gates:
  policy:
    policy_dir: ".tapps-agents/policies"
    enabled_policies: ["custom-policy-1", "custom-policy-2"]
    check_gdpr: true
    check_hipaa: false
    check_pci_dss: false
```

**Custom Policy Format:**
```json
// .tapps-agents/policies/custom-policy-1.json
{
  "name": "custom-policy-1",
  "description": "Custom project policy",
  "rules": [
    {
      "type": "file_pattern",
      "pattern": "*.secret",
      "allowed": false,
      "reason": "Secret files not allowed"
    }
  ]
}
```

**Usage in Workflow:**
```yaml
steps:
  - id: review
    agent: reviewer
    action: review
    gates:
      - name: policy
        config:
          check_gdpr: true
          enabled_policies: ["custom-policy-1"]
```

### Approval Gate

The approval gate requires human approval before proceeding:
- **Synchronous**: Blocks workflow until approved
- **Asynchronous**: Allows workflow to continue, approval checked later
- **Auto-approve**: Automatically approves (for testing/CI)

**Configuration:**
```yaml
# .tapps-agents/config.yaml
gates:
  approval:
    approval_dir: ".tapps-agents/approvals"
    auto_approve: false
    async_mode: false
```

**Usage in Workflow:**
```yaml
steps:
  - id: deploy
    agent: ops
    action: deploy
    gates:
      - name: approval
        config:
          auto_approve: false
          async_mode: false
```

**Approving Workflows:**
```bash
# Approve a pending approval (manual process)
# Approval files are stored in .tapps-agents/approvals/
# Format: {request_id}.json
```

## Gate Registry

The gate registry manages all available gates:

```python
from tapps_agents.quality.gates.registry import get_gate_registry

registry = get_gate_registry()

# Get a gate
security_gate = registry.get("security")

# Evaluate multiple gates
results = registry.evaluate_gates(
    ["security", "policy"],
    context={"workflow_id": "test", "content": "code here"}
)

if results["all_passed"]:
    print("All gates passed")
else:
    print(f"Failures: {results['failures']}")
```

## Custom Gates

### Creating Custom Gates

1. **Create gate class:**
```python
# .tapps-agents/gates/custom_gate.py
from tapps_agents.quality.gates.base import BaseGate, GateResult, GateSeverity

class CustomGate(BaseGate):
    def evaluate(self, context: dict[str, Any]) -> GateResult:
        # Your gate logic here
        workflow_id = context.get("workflow_id")
        
        # Example: Check if workflow ID matches pattern
        if workflow_id and "test" in workflow_id:
            return GateResult(
                passed=False,
                severity=GateSeverity.ERROR,
                message="Test workflows not allowed in production",
            )
        
        return GateResult(
            passed=True,
            severity=GateSeverity.INFO,
            message="Custom gate passed",
        )
```

2. **Gate is automatically loaded** from `.tapps-agents/gates/` directory

3. **Use in workflow:**
```yaml
steps:
  - id: step1
    agent: implementer
    gates:
      - name: custom_gate
```

## Workflow Integration

### Using Gates in Workflow YAML

```yaml
workflow:
  steps:
    - id: implement
      agent: implementer
      action: implement
      gates:
        - name: security
          config:
            filter_secrets: true
        - name: policy
          config:
            check_gdpr: true
        - name: approval
          config:
            auto_approve: false
      gate:
        condition: "gates.all_passed == true"
        on_pass: review
        on_fail: implement  # Retry if gates fail
```

### Gate Chaining

Gates are evaluated in order. All gates must pass for the step to proceed:

```yaml
gates:
  - name: security
  - name: policy
  - name: approval
```

If any gate fails with ERROR or CRITICAL severity, the step is blocked.

## Gate Evaluation Flow

1. **Gate Discovery**: Load gates from registry
2. **Gate Evaluation**: Evaluate each gate with context
3. **Result Aggregation**: Combine all gate results
4. **Decision**: Block step if any critical gates failed
5. **Routing**: Use `on_pass`/`on_fail` for workflow routing

## Best Practices

1. **Security First**: Always enable security gate for code changes
2. **Policy Compliance**: Configure policy gates based on industry requirements
3. **Approval Workflow**: Use approval gates for production deployments
4. **Custom Gates**: Create project-specific gates for domain requirements
5. **Gate Testing**: Test gates in development before enabling in production

## Error Handling & Validation

The gates system includes comprehensive error handling and validation:

### Input Validation

All gates validate context inputs:
- **Context Type**: Must be a dictionary
- **Required Fields**: Validated before evaluation
- **Configuration**: Gate configs validated on load

### Exception Types

Custom exceptions provide clear error messages:

```python
from tapps_agents.quality.gates.exceptions import (
    GateEvaluationError,           # Base exception
    GateConfigurationError,         # Invalid gate configuration
    MissingContextError,           # Required context fields missing
    GateTimeoutError,              # Gate evaluation timeout
    GateNotFoundError,             # Gate not in registry
    CircularGateDependencyError,   # Circular dependencies detected
)
```

### Error Handling in Gate Evaluation

Gates handle errors gracefully:

**Security Gate:**
- Invalid file paths: Logged, evaluation continues
- Scanner errors: Logged, evaluation continues with available data
- Missing content: Returns pass (nothing to check)

**Policy Gate:**
- Missing policy files: Logged, policy check skipped
- Invalid JSON: Logged, policy check skipped
- Missing context: Returns error result with clear message

**Approval Gate:**
- Missing `workflow_id`: Returns error result immediately
- Missing `step_id`: Returns error result immediately
- Corrupt approval files: Logged, creates new approval request

**Gate Registry:**
- Invalid gate names: Logged, skipped
- Evaluation exceptions: Caught, included in results
- Missing gates: Logged, included in results with error

### Configuration Validation

Gate configurations are validated:
- **Gate Names**: Must exist in registry
- **Config Structure**: Must be dictionary if provided
- **Invalid Configs**: Logged and skipped, workflow continues

**Example:**
```python
# Invalid gate config is handled gracefully
step.metadata = {
    "gates": [
        "nonexistent_gate",  # Logged, skipped
        {"invalid": "config"},  # Logged, skipped
        "security",  # Valid, evaluated
    ]
}

results = integration.evaluate_step_gates(step, state, context)
# Only valid gates are evaluated
# Invalid gates are logged but don't crash workflow
```

## Troubleshooting

**Gate not found:**
- Check gate name matches registry
- Verify custom gate file is in `.tapps-agents/gates/`
- Check gate class extends `BaseGate`
- **Error**: `GateNotFoundError` - Gate not in registry (logged, workflow continues)

**Gate always fails:**
- Review gate configuration
- Check context data provided to gate
- Enable debug logging for gate evaluation
- **Error**: `MissingContextError` - Required context fields missing
- **Error**: `GateConfigurationError` - Invalid gate configuration

**Gate evaluation errors:**
- Check gate logs for exceptions
- Verify context has required fields
- **Error**: `GateEvaluationError` - Gate evaluation failed (caught, included in results)

**Approval stuck:**
- Check approval file in `.tapps-agents/approvals/`
- Verify approval status is "approved"
- Check async_mode setting
- **Error**: Missing `workflow_id` or `step_id` returns error immediately

## Related Documentation

- [Quality Gates](quality/quality_gates.py)
- [Workflow Auto-Progression](workflow/auto_progression.py)
- [Security Scanning](quality/secret_scanner.py)
