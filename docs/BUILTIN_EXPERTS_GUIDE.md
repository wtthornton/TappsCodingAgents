# Built-in Experts Guide

**Version:** 2.0.0  
**Last Updated:** December 2025

## Overview

TappsCodingAgents ships with a comprehensive set of **built-in experts** that provide technical domain knowledge. These experts are framework-controlled, immutable, and automatically available to all agents. They complement customer-defined business domain experts.

## Built-in Experts

### 1. Security Expert (`expert-security`)

**Domain:** `security`  
**Knowledge Base:** 10 files covering OWASP Top 10, security patterns, vulnerabilities, and best practices

**Use Cases:**
- Code security reviews
- Vulnerability assessment
- Security pattern recommendations
- Compliance checking

**Example:**
```python
result = await registry.consult(
    query="Is this authentication code secure?",
    domain="security",
    prioritize_builtin=True
)
```

### 2. Performance Expert (`expert-performance`)

**Domain:** `performance-optimization`  
**Knowledge Base:** 8 files covering optimization patterns, caching, scalability, and resource management

**Use Cases:**
- Performance bottleneck identification
- Optimization recommendations
- Scalability planning
- Resource usage analysis

### 3. Testing Expert (`expert-testing`)

**Domain:** `testing-strategies`  
**Knowledge Base:** 9 files covering test strategies, patterns, coverage, and best practices

**Use Cases:**
- Test strategy recommendations
- Test pattern suggestions
- Coverage analysis
- Testing best practices

### 4. Data Privacy Expert (`expert-data-privacy`)

**Domain:** `data-privacy-compliance`  
**Knowledge Base:** 8 files covering GDPR, HIPAA, CCPA, and privacy best practices

**Use Cases:**
- Compliance checking
- Privacy impact assessments
- Data handling recommendations
- Regulatory compliance

### 5. Accessibility Expert (`expert-accessibility`)

**Domain:** `accessibility`  
**Knowledge Base:** 9 files covering WCAG 2.1/2.2, ARIA patterns, screen readers, and accessibility testing

**Use Cases:**
- Accessibility audits
- WCAG compliance checking
- ARIA pattern recommendations
- Accessibility testing strategies

### 6. User Experience Expert (`expert-user-experience`)

**Domain:** `user-experience`  
**Knowledge Base:** 8 files covering UX principles, usability heuristics, user research, and interaction design

**Use Cases:**
- UX design reviews
- Usability assessments
- User journey optimization
- Interaction design recommendations

## Knowledge Base Structure

Built-in expert knowledge bases are located in:

```
tapps_agents/experts/knowledge/
├── security/              # 10 files
├── performance/          # 8 files
├── testing/              # 9 files
├── data-privacy/         # 8 files
├── accessibility/        # 9 files
└── user-experience/      # 8 files
```

Each knowledge base contains markdown files with:
- Domain overview
- Best practices
- Common patterns
- Anti-patterns
- Specific topic guides
- Testing strategies

## Agent Integration

### Using ExpertSupportMixin

The easiest way to add expert support to an agent:

```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.experts.agent_integration import ExpertSupportMixin

class MyAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def review_code(self, code: str):
        # Consult security expert
        result = await self._consult_builtin_expert(
            query=f"Review this code for security issues: {code}",
            domain="security"
        )
        
        if result:
            return result.weighted_answer
        return "No expert advice available"
```

### Direct Registry Usage

```python
from tapps_agents.experts import ExpertRegistry

# Create registry (auto-loads built-in experts)
registry = ExpertRegistry(domain_config=None, load_builtin=True)

# Consult technical domain (prioritizes built-in)
result = await registry.consult(
    query="How to optimize this code?",
    domain="performance-optimization",
    prioritize_builtin=True
)
```

## Weighted Consultation Patterns

### Technical Domains (Built-in Priority)

For technical domains, built-in experts have primary authority:

```python
# Security domain - built-in expert prioritized
result = await registry.consult(
    query="How to secure this API?",
    domain="security",
    prioritize_builtin=True  # Built-in expert gets 51% weight
)
```

**Technical Domains:**
- `security`
- `performance-optimization`
- `testing-strategies`
- `code-quality-analysis`
- `software-architecture`
- `development-workflow`
- `data-privacy-compliance`
- `accessibility`
- `user-experience`
- `documentation-knowledge-management`
- `ai-agent-framework`

### Business Domains (Customer Priority)

For business domains, customer experts have primary authority:

```python
# E-commerce domain - customer expert prioritized
result = await registry.consult(
    query="How to handle checkout?",
    domain="e-commerce",
    prioritize_builtin=False  # Customer expert gets 51% weight
)
```

## Expert Consultation Workflow

```
Agent Request
    ↓
Determine Domain Type
    ├─ Technical → Prioritize Built-in Expert
    └─ Business → Prioritize Customer Expert
        ↓
Consult Experts
    ├─ Primary Expert (51% weight)
    └─ Supporting Experts (49% weight)
        ↓
Aggregate Responses
    └─ Weighted Answer
```

## Custom Expert Setup

While built-in experts are immutable, you can add customer experts for business domains:

**`.tapps-agents/experts.yaml`:**
```yaml
experts:
  - expert_id: expert-ecommerce
    expert_name: E-commerce Expert
    primary_domain: e-commerce
    rag_enabled: true
    fine_tuned: false
```

**Knowledge Base:**
```
.tapps-agents/knowledge/e-commerce/
├── checkout-flow.md
├── payment-processing.md
└── inventory-management.md
```

## Best Practices

1. **Use Built-in Experts for Technical Domains**
   - Security, performance, testing, etc.
   - Automatically prioritized
   - Framework-maintained knowledge

2. **Use Customer Experts for Business Domains**
   - Domain-specific business logic
   - Project-specific knowledge
   - Customer-maintained

3. **Combine Both When Needed**
   - Technical + business consultation
   - Weighted aggregation
   - Comprehensive advice

4. **Leverage RAG**
   - Built-in experts have RAG enabled
   - Retrieves relevant knowledge automatically
   - Cites sources in responses

## Examples

### Example 1: Security Review

```python
class ReviewerAgent(BaseAgent, ExpertSupportMixin):
    async def review_security(self, code: str):
        result = await self._consult_builtin_expert(
            query=f"Review this code for security vulnerabilities:\n{code}",
            domain="security"
        )
        
        if result:
            return {
                "security_issues": result.weighted_answer,
                "confidence": result.confidence,
                "sources": result.responses[0].get("sources", [])
            }
```

### Example 2: Performance Optimization

```python
class ImplementerAgent(BaseAgent, ExpertSupportMixin):
    async def optimize_performance(self, code: str):
        result = await self._consult_builtin_expert(
            query=f"Optimize this code for performance:\n{code}",
            domain="performance-optimization"
        )
        
        return result.weighted_answer if result else "No recommendations"
```

### Example 3: Accessibility Audit

```python
class DesignerAgent(BaseAgent, ExpertSupportMixin):
    async def check_accessibility(self, design: str):
        result = await self._consult_builtin_expert(
            query=f"Check this design for accessibility:\n{design}",
            domain="accessibility"
        )
        
        return result.weighted_answer if result else "No issues found"
```

## Troubleshooting

### Expert Not Found

If an expert is not found, check:
1. Built-in experts are auto-loaded (set `load_builtin=True`)
2. Domain name matches exactly
3. Expert is registered in registry

### No Response

If consultation returns None:
1. Check expert registry is initialized
2. Verify domain is correct
3. Ensure expert has knowledge base (for RAG)

### Low Confidence

If confidence is low:
1. Query may be too vague
2. Knowledge base may not have relevant content
3. Consider consulting multiple experts

## API Reference

See [API.md](./API.md) for complete API documentation.

## Related Documentation

- [Expert Knowledge Base Guide](./EXPERT_KNOWLEDGE_BASE_GUIDE.md)
- [Expert Configuration Guide](./EXPERT_CONFIG_GUIDE.md)
- [Agent Integration Patterns](./DEVELOPER_GUIDE.md)

