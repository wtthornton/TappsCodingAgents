---
title: Expert Priority Guidelines
version: 1.0.0
status: active
last_updated: 2026-01-28
tags: [experts, configuration, priority, guidelines]
---

# Expert Priority Guidelines

**Version**: 1.0.0
**Last Updated**: 2026-01-28
**Status**: Active

---

## Overview

This guide explains the expert priority system in TappsCodingAgents and provides guidelines for configuring expert priorities effectively. Expert priority determines how frequently and automatically experts are consulted during development workflows.

**Why Priority Matters**:
- **Automatic Consultation**: High-priority experts are consulted automatically
- **Passive Notifications**: Experts with priority > 0.9 trigger notifications even during manual coding
- **Weighted Voting**: Priority affects expert influence in multi-expert decisions
- **Performance**: Lower priority experts are consulted less frequently, improving performance

---

## Priority Scale

TappsCodingAgents uses a **0.0 to 1.0 priority scale** for experts. Higher numbers indicate higher priority.

### 0.95+ : Critical Domain Experts

**When to Use**: Always-consult experts for critical domains that directly impact code correctness or security.

**Characteristics**:
- Automatically consulted whenever domain is detected
- Trigger passive notifications during manual coding
- Highest weight in multi-expert voting (51% primary, 49% split among others)
- Cannot be disabled (only opt-out of notifications)

**Examples from Built-in Experts**:
- `expert-security` (Priority: 0.98) - Security vulnerabilities, OWASP Top 10
- `expert-data-privacy` (Priority: 0.96) - GDPR, CCPA, PII handling
- `expert-testing` (Priority: 0.95) - Test coverage, quality gates

**Use Cases**:
- Security-critical domains (authentication, authorization, encryption)
- Compliance-critical domains (GDPR, HIPAA, SOC2)
- Core technical domains that prevent bugs (testing, error handling)

**Example Configuration**:
```yaml
# .tapps-agents/experts.yaml
experts:
  - id: expert-payment-processing
    name: Payment Processing Expert
    domains:
      - payment-processing
      - pci-compliance
      - stripe-integration
    priority: 0.97  # Critical: financial transactions, PCI compliance
    knowledge_base: .tapps-agents/knowledge/payment-processing
```

---

### 0.85 - 0.94 : Important Domain Experts

**When to Use**: High-value experts that should be consulted frequently but aren't always critical.

**Characteristics**:
- Consulted when domain is detected in context
- May trigger passive notifications (configurable threshold)
- High weight in multi-expert voting
- Can be disabled if needed

**Examples from Built-in Experts**:
- `expert-performance` (Priority: 0.90) - Performance optimization, profiling
- `expert-accessibility` (Priority: 0.88) - WCAG compliance, a11y best practices
- `expert-code-quality` (Priority: 0.85) - Clean code, SOLID principles

**Use Cases**:
- Performance-sensitive domains (database queries, caching)
- User experience domains (accessibility, UX patterns)
- Code quality domains (refactoring, maintainability)

**Example Configuration**:
```yaml
# .tapps-agents/experts.yaml
experts:
  - id: expert-site24x7-monitors
    name: Site24x7 Monitor Expert
    domains:
      - site24x7-monitors
      - monitor-configuration
      - alerting
    priority: 0.90  # Important: monitor setup is critical but not always used
    knowledge_base: .tapps-agents/knowledge/site24x7/monitors
```

---

### 0.70 - 0.84 : Supporting Domain Experts

**When to Use**: Valuable experts for specific contexts but not frequently needed.

**Characteristics**:
- Consulted when explicitly relevant (keyword match, file path, etc.)
- No passive notifications
- Medium weight in multi-expert voting
- Easily disabled if not needed

**Examples from Built-in Experts**:
- `expert-observability` (Priority: 0.80) - Logging, monitoring, tracing
- `expert-documentation` (Priority: 0.78) - Documentation best practices
- `expert-cloud-infrastructure` (Priority: 0.75) - AWS, Azure, GCP patterns

**Use Cases**:
- Supporting technical domains (logging, monitoring)
- Documentation and process domains
- Cloud-specific patterns (not always relevant)

**Example Configuration**:
```yaml
# .tapps-agents/experts.yaml
experts:
  - id: expert-site24x7-reports
    name: Site24x7 Reporting Expert
    domains:
      - site24x7-reports
      - report-generation
      - data-export
    priority: 0.80  # Supporting: reports are important but not always needed
    knowledge_base: .tapps-agents/knowledge/site24x7/reports
```

---

### < 0.70 : Background Domain Experts

**When to Use**: Nice-to-have experts for edge cases or optional features.

**Characteristics**:
- Consulted only on explicit request (`@expert consult`)
- No automatic consultation
- Low weight in multi-expert voting
- Often disabled by default

**Examples from Built-in Experts**:
- `expert-ai-frameworks` (Priority: 0.65) - AI/ML frameworks (only for AI projects)
- `expert-agent-learning` (Priority: 0.60) - Agent learning patterns (meta-level)

**Use Cases**:
- Specialized domains used in few projects
- Meta-level or framework-level patterns
- Experimental or emerging technologies

**Example Configuration**:
```yaml
# .tapps-agents/experts.yaml
experts:
  - id: expert-graphql-federation
    name: GraphQL Federation Expert
    domains:
      - graphql-federation
      - apollo-federation
    priority: 0.65  # Background: only relevant for federated GraphQL
    knowledge_base: .tapps-agents/knowledge/graphql-federation
```

---

## Decision Framework

Use this decision tree to determine appropriate priority:

```
Is the domain critical for security or compliance?
├─ YES → Priority: 0.95+ (Critical)
└─ NO ↓

Is the domain frequently needed in this project?
├─ YES → Priority: 0.85-0.94 (Important)
└─ NO ↓

Is the domain moderately useful for code quality?
├─ YES → Priority: 0.70-0.84 (Supporting)
└─ NO → Priority: < 0.70 (Background)
```

### Additional Considerations

**Project Type**:
- **Security-sensitive projects** (FinTech, HealthTech): Higher priorities for security/compliance experts
- **Performance-critical projects** (Real-time, High-traffic): Higher priorities for performance experts
- **Public-facing projects**: Higher priorities for accessibility/UX experts

**Team Experience**:
- **Junior developers**: Higher priorities for code-quality experts
- **Senior developers**: Lower priorities for basic patterns, higher for advanced patterns

**Project Phase**:
- **Early development**: Higher priorities for architecture/design experts
- **Maintenance phase**: Higher priorities for refactoring/testing experts

---

## Configuration Examples

### Example 1: E-Commerce Platform

```yaml
# .tapps-agents/experts.yaml
experts:
  # Critical: Payment and PCI compliance
  - id: expert-payment-processing
    name: Payment Processing Expert
    priority: 0.97
    domains: [payment-processing, pci-compliance]

  # Important: Cart and checkout flows
  - id: expert-shopping-cart
    name: Shopping Cart Expert
    priority: 0.90
    domains: [shopping-cart, checkout-flow]

  # Supporting: Product catalog
  - id: expert-product-catalog
    name: Product Catalog Expert
    priority: 0.80
    domains: [product-catalog, inventory]

  # Background: Gift cards (not always used)
  - id: expert-gift-cards
    name: Gift Card Expert
    priority: 0.65
    domains: [gift-cards, promotions]
```

### Example 2: Healthcare Application

```yaml
# .tapps-agents/experts.yaml
experts:
  # Critical: HIPAA compliance
  - id: expert-hipaa-compliance
    name: HIPAA Compliance Expert
    priority: 0.98
    domains: [hipaa, phi-protection, audit-logging]

  # Critical: Patient data security
  - id: expert-patient-data
    name: Patient Data Security Expert
    priority: 0.97
    domains: [patient-data, medical-records, encryption]

  # Important: EHR integration
  - id: expert-ehr-integration
    name: EHR Integration Expert
    priority: 0.90
    domains: [ehr-integration, fhir, hl7]

  # Supporting: Appointment scheduling
  - id: expert-scheduling
    name: Appointment Scheduling Expert
    priority: 0.75
    domains: [scheduling, calendar-integration]
```

### Example 3: API Integration Project (Site24x7)

```yaml
# .tapps-agents/experts.yaml
experts:
  # Critical: OAuth authentication (must be correct)
  - id: expert-external-api-auth
    name: External API Authentication Expert
    priority: 0.95
    domains: [api-auth, oauth2]
    knowledge_base: .tapps-agents/knowledge/external-api/auth

  # Important: Resource configuration (frequently used)
  - id: expert-external-api-resources
    name: External API Resource Expert
    priority: 0.90
    domains: [api-resources, resource-config]
    knowledge_base: .tapps-agents/knowledge/external-api/resources

  # Supporting: Reporting (used occasionally)
  - id: expert-external-api-reports
    name: External API Reporting Expert
    priority: 0.80
    domains: [site24x7-reports, data-export]
    knowledge_base: .tapps-agents/knowledge/site24x7/reports
```

---

## Passive Notifications

**Passive notifications** are triggered for high-priority experts during manual coding (not in workflow). This helps developers remember to consult relevant experts.

### Notification Threshold

**Default**: Priority > 0.9 triggers passive notifications

**Configuration**:
```yaml
# .tapps-agents/config.yaml
expert:
  passive_notifications_enabled: true  # Enable/disable notifications
  high_priority_threshold: 0.9  # Threshold for passive notifications
```

### Notification Behavior

**When Triggered**:
- Manual CLI commands (not workflow steps)
- Domain detected in prompt or context
- Expert priority > threshold

**Notification Format**:
```
ℹ️  Detected oauth2 domain - Consider consulting expert-site24x7-api-auth
   Use: tapps-agents expert consult expert-site24x7-api-auth "your query"
```

**Opt-Out**:
```yaml
# .tapps-agents/config.yaml
expert:
  passive_notifications_enabled: false  # Disable all notifications
```

---

## Best Practices

### 1. Start Conservative

**Recommendation**: Start with **lower priorities** and increase based on usage.

**Why**: Overly aggressive expert consultation can slow down development and create notification fatigue.

**Example**:
```yaml
# Start with 0.85 instead of 0.95
- id: expert-new-domain
  priority: 0.85  # Start here, not 0.95
```

### 2. Monitor Expert Usage

**Tools**:
```bash
# View expert consultation history
tapps-agents expert history

# See which experts are used most
tapps-agents expert stats
```

**Adjust**: Increase priority for frequently-consulted experts, decrease for rarely-used ones.

### 3. Align with Project Risks

**High-Risk Domains** → **High Priority**:
- Security vulnerabilities
- Compliance violations
- Data loss/corruption
- Financial transactions

**Low-Risk Domains** → **Lower Priority**:
- UI styling
- Optional features
- Internal tools

### 4. Consider Team Expertise

**Junior Team** → **Higher Priorities**:
- More guidance needed
- More expert consultation beneficial

**Senior Team** → **Lower Priorities**:
- Less hand-holding needed
- Selective expert consultation

### 5. Balance Performance

**Too Many High-Priority Experts** → **Performance Impact**:
- Expert consultation takes time
- RAG retrieval adds latency
- Notification fatigue

**Recommendation**: Limit high-priority experts (0.9+) to **5-10 per project**.

---

## Troubleshooting

### Expert Not Being Consulted

**Problem**: Expert should be consulted but isn't.

**Check**:
1. Is priority high enough? (≥ 0.85 for automatic consultation)
2. Are domains correctly configured?
3. Is expert enabled in config?
4. Does context contain domain keywords?

**Solution**:
```yaml
# Increase priority
- id: expert-my-domain
  priority: 0.90  # Increase from 0.75
  domains:
    - my-domain
    - related-keyword  # Add more domain keywords
```

### Too Many Notifications

**Problem**: Getting too many passive notifications.

**Solutions**:
1. **Disable notifications**:
   ```yaml
   expert:
     passive_notifications_enabled: false
   ```

2. **Increase threshold**:
   ```yaml
   expert:
     high_priority_threshold: 0.95  # Only notify for 0.95+
   ```

3. **Lower expert priorities**:
   ```yaml
   - id: expert-noisy-domain
     priority: 0.85  # Lower from 0.95
   ```

### Expert Consultation Too Slow

**Problem**: Expert consultation slows down commands.

**Check**:
1. How many high-priority experts? (should be ≤ 10)
2. Is knowledge base too large? (should be < 100 files)
3. Is RAG quality score low? (optimize knowledge structure)

**Solutions**:
- Reduce number of high-priority experts
- Optimize knowledge base (see [Knowledge Base Guide](knowledge-base-guide.md))
- Disable experts for specific commands: `tapps-agents reviewer review --no-experts`

---

## Related Documentation

- **[Knowledge Base Organization Guide](knowledge-base-guide.md)** - How to structure knowledge for RAG optimization
- **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
- **[Expert System Architecture](ARCHITECTURE.md#2-expert-system-knowledge-layer)** - How the expert system works

---

## FAQ

### Q: Can I have multiple experts with priority 0.95+?

**A**: Yes, but limit to **5-10** to avoid performance issues and notification fatigue.

### Q: What if I'm not sure which priority to use?

**A**: Start with **0.85** (Important) and adjust based on usage. You can always increase or decrease later.

### Q: Do built-in experts have fixed priorities?

**A**: Built-in expert priorities are defaults but can be overridden in your project's `.tapps-agents/experts.yaml`.

### Q: Can I disable passive notifications for specific experts?

**A**: Not currently per-expert, but you can lower their priority below the threshold (default 0.9) or disable all notifications.

### Q: How do I know which priority an expert should have?

**A**: Use the [Decision Framework](#decision-framework) above. Consider: security criticality, usage frequency, and project risk.

---

**Version History**:
- **1.0.0** (2026-01-28): Initial release based on Site24x7 feedback

**Maintainer**: TappsCodingAgents Team
**Feedback**: Create GitHub issue or update this document via PR
