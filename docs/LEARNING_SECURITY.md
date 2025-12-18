# Learning System Security Integration

## Overview

The agent learning system now includes comprehensive security scanning to prevent learning from vulnerable code patterns. This ensures that agents only learn from secure, production-ready code.

## Features

### Security Scanner

The `SecurityScanner` module provides reusable security scanning functionality:

- **Bandit Integration**: Uses Bandit for comprehensive security analysis
- **Heuristic Fallback**: Falls back to pattern-based scanning when Bandit is unavailable
- **Structured Results**: Returns detailed vulnerability information with severity levels

### Security-Aware Pattern Extraction

Pattern extraction now includes security checks:

- **Pre-extraction Scanning**: All code is scanned before pattern extraction
- **Threshold Filtering**: Patterns must meet security threshold (default: 7.0/10)
- **Security Scoring**: Each pattern includes a security score in its metadata

### Security Metrics

Learning results include security metrics:

- `security_checked`: Whether security scanning was performed
- `security_score`: Security score (0-10, higher is better)
- `security_vulnerabilities`: List of detected vulnerabilities

## Usage

### Basic Security Scanning

```python
from tapps_agents.core.security_scanner import SecurityScanner

scanner = SecurityScanner()

# Scan code string
result = scanner.scan_code(code="def test():\n    return True")
print(f"Security Score: {result['security_score']}")
print(f"Vulnerabilities: {result['vulnerabilities']}")

# Check if safe for learning
is_safe = scanner.is_safe_for_learning(code=code, threshold=7.0)
```

### Security-Aware Learning

The learning system automatically performs security checks:

```python
from tapps_agents.core.agent_learning import AgentLearner

learner = AgentLearner(...)

result = await learner.learn_from_task(
    capability_id="test",
    task_id="task_1",
    code=code,
    quality_scores={"overall_score": 85.0},
    success=True,
)

# Check security results
if result["security_checked"]:
    print(f"Security Score: {result['security_score']}")
    if result["security_score"] < 7.0:
        print("Code was too insecure to learn from")
```

### Custom Security Thresholds

You can customize security thresholds:

```python
from tapps_agents.core.agent_learning import PatternExtractor
from tapps_agents.core.security_scanner import SecurityScanner

scanner = SecurityScanner()
extractor = PatternExtractor(
    min_quality_threshold=0.7,
    security_scanner=scanner,
    security_threshold=8.0,  # Higher threshold for stricter security
)
```

## Security Score Calculation

Security scores are calculated as follows:

- **Bandit Available**: 
  - Score = 10.0 - (high_severity × 3.0 + medium_severity × 1.0 + low_severity × 0.5)
  - Minimum score: 0.0

- **Heuristic Fallback**:
  - Detects common insecure patterns (eval, exec, shell=True, etc.)
  - Score = 10.0 - (issues × 2.0)

## Vulnerability Data Structure

Each vulnerability includes:

```python
{
    "severity": "high" | "medium" | "low",
    "test_id": "B601",  # Bandit test ID
    "test_name": "shell_injection_subprocess",
    "line": 42,
    "text": "Possible shell injection",
    "confidence": "high" | "medium" | "low"
}
```

## Configuration

### Default Thresholds

- **Security Threshold**: 7.0 (patterns must score ≥ 7.0 to be learned)
- **Bandit Required**: No (falls back to heuristics if unavailable)

### Adjusting Thresholds

For stricter security:
- Increase `security_threshold` to 8.0 or 9.0
- This will reject more patterns but ensure higher security

For more permissive learning:
- Decrease `security_threshold` to 6.0 or 5.0
- Note: This may allow learning from less secure code

## Best Practices

1. **Always Review Security Scores**: Check security scores in learning results
2. **Monitor Vulnerabilities**: Review vulnerability lists for patterns
3. **Use Appropriate Thresholds**: Match security thresholds to your security requirements
4. **Regular Security Audits**: Periodically review learned patterns for security issues

## Integration with Code Review

The security scanner integrates with the code review process:

- Security scores are included in code quality metrics
- Vulnerabilities are flagged during review
- Low-security patterns are automatically excluded from learning

## Troubleshooting

### Bandit Not Available

If Bandit is not installed, the system automatically falls back to heuristic scanning. This provides basic security checking but is less comprehensive.

To enable full Bandit scanning:
```bash
pip install bandit>=1.9.2
```

### False Positives

If legitimate code is being rejected:
- Review the specific vulnerabilities
- Consider adjusting the security threshold
- Add `# nosec` comments for known-safe patterns (if using Bandit)

### Performance

Security scanning adds minimal overhead:
- Bandit scanning: ~100-500ms per file
- Heuristic scanning: <10ms per file
- Scanning is performed asynchronously during learning

## See Also

- [Agent Learning Guide](AGENT_LEARNING_GUIDE.md)
- [Security Best Practices](../tapps_agents/experts/knowledge/agent-learning/best-practices.md)

