# Built-in Experts Guide

**Version:** 2.0.4  
**Last Updated:** January 2026

## Overview

TappsCodingAgents ships with a comprehensive set of **built-in experts** that provide technical domain knowledge. These experts are framework-controlled, immutable, and automatically available to all agents. They complement customer-defined business domain experts.

## Built-in Experts

### 1. Security Expert (`expert-security`)

**Domain:** `security`  
**Knowledge Base:** 4 files covering OWASP Top 10, security patterns, vulnerabilities, and best practices

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
    prioritize_builtin=True,
    agent_id="reviewer"  # For agent-specific confidence threshold
)

# Access confidence information
print(f"Confidence: {result.confidence:.2%}")
print(f"Threshold: {result.confidence_threshold:.2%}")
print(f"Meets threshold: {result.confidence >= result.confidence_threshold}")
print(f"Agreement level: {result.agreement_level:.2%}")
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
**Knowledge Base:** 10 files covering GDPR, HIPAA, CCPA, and privacy best practices

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

### 7. Observability & Monitoring Expert (`expert-observability`)

**Domain:** `observability-monitoring`  
**Knowledge Base:** 8 files covering distributed tracing, metrics, logging, APM tools, SLO/SLI/SLA, alerting patterns, and OpenTelemetry

**Use Cases:**
- Observability strategy design
- Distributed tracing implementation
- Metrics and monitoring setup
- Logging strategy recommendations
- SLO/SLI/SLA definition
- Alerting pattern design
- APM tool selection

**Example:**
```python
result = await registry.consult(
    query="How to implement distributed tracing for microservices?",
    domain="observability-monitoring",
    prioritize_builtin=True,
    agent_id="ops"
)
```

### 8. API Design & Integration Expert (`expert-api-design`)

**Domain:** `api-design-integration`  
**Knowledge Base:** 8 files covering RESTful API design, GraphQL patterns, gRPC best practices, API versioning, rate limiting, API gateway patterns, API security, and contract testing

**Use Cases:**
- RESTful API design reviews
- GraphQL schema design
- gRPC service design
- API versioning strategy
- Rate limiting implementation
- API gateway configuration
- API security patterns
- Contract testing setup

**Example:**
```python
result = await registry.consult(
    query="Best practices for RESTful API versioning?",
    domain="api-design-integration",
    prioritize_builtin=True,
    agent_id="designer"
)
```

### 9. Cloud & Infrastructure Expert (`expert-cloud-infrastructure`)

**Domain:** `cloud-infrastructure`  
**Knowledge Base:** 8 files covering cloud-native patterns, containerization, Kubernetes patterns, infrastructure as code, serverless architecture, multi-cloud strategies, cost optimization, and disaster recovery

**Use Cases:**
- Cloud architecture design
- Container orchestration setup
- Kubernetes deployment patterns
- Infrastructure as Code (IaC) recommendations
- Serverless architecture design
- Multi-cloud strategy planning
- Cost optimization strategies
- Disaster recovery planning

**Example:**
```python
result = await registry.consult(
    query="How to design a Kubernetes deployment strategy?",
    domain="cloud-infrastructure",
    prioritize_builtin=True,
    agent_id="architect"
)
```

### 10. Database & Data Management Expert (`expert-database`)

**Domain:** `database-data-management`  
**Knowledge Base:** 8 files covering database design, SQL optimization, NoSQL patterns, data modeling, migration strategies, scalability patterns, backup and recovery, and ACID vs CAP theorem

**Use Cases:**
- Database schema design
- SQL query optimization
- NoSQL database selection
- Data modeling recommendations
- Migration strategy planning
- Scalability pattern design
- Backup and recovery planning
- Database architecture decisions

**Example:**
```python
result = await registry.consult(
    query="When to use SQL vs NoSQL databases?",
    domain="database-data-management",
    prioritize_builtin=True,
    agent_id="architect"
)
```

### 11. Code Quality & Analysis Expert (`expert-code-quality`)

**Domain:** `code-quality-analysis`  
**Knowledge Base:** Framework-controlled expert for code quality analysis, maintainability, and best practices

**Use Cases:**
- Code quality assessments
- Maintainability analysis
- Code review best practices
- Quality metric evaluation

### 12. Software Architecture Expert (`expert-software-architecture`)

**Domain:** `software-architecture`  
**Knowledge Base:** Framework-controlled expert for software architecture patterns, design principles, and architectural decision-making

**Use Cases:**
- Architecture design reviews
- Pattern selection guidance
- Architectural decision records
- System design recommendations

### 13. Development Workflow Expert (`expert-devops`)

**Domain:** `development-workflow`  
**Knowledge Base:** Framework-controlled expert for DevOps practices, CI/CD, deployment strategies, and development workflows

**Use Cases:**
- CI/CD pipeline design
- Deployment strategy recommendations
- Development workflow optimization
- DevOps best practices

### 14. Documentation & Knowledge Management Expert (`expert-documentation`)

**Domain:** `documentation-knowledge-management`  
**Knowledge Base:** Framework-controlled expert for documentation practices, knowledge management, and technical writing

**Use Cases:**
- Documentation strategy
- API documentation best practices
- Knowledge base organization
- Technical writing guidance

### 15. AI Agent Framework Expert (`expert-ai-frameworks`)

**Domain:** `ai-agent-framework`  
**Knowledge Base:** Framework-controlled expert for AI agent frameworks, patterns, and best practices

**Use Cases:**
- Agent framework selection
- Agent architecture design
- Agent pattern recommendations
- AI framework best practices

### 16. Agent Learning Best Practices Expert (`expert-agent-learning`)

**Domain:** `agent-learning`  
**Knowledge Base:** 3 files covering agent learning patterns, prompt optimization, and best practices for improving agent performance

**Use Cases:**
- Agent learning strategy
- Prompt optimization
- Pattern extraction
- Agent performance improvement

**Example:**
```python
result = await registry.consult(
    query="How to improve agent prompt effectiveness?",
    domain="agent-learning",
    prioritize_builtin=True,
    agent_id="enhancer"
)
```

## Knowledge Base Structure

Built-in expert knowledge bases are located in:

```
tapps_agents/experts/knowledge/
├── security/                      # 4 files
├── performance/                   # 8 files
├── testing/                        # 8 files
├── data-privacy-compliance/       # 10 files
├── accessibility/                 # 9 files
├── user-experience/                # 8 files
├── observability-monitoring/       # 8 files (Phase 5)
├── api-design-integration/         # 8 files (Phase 5)
├── cloud-infrastructure/           # 8 files (Phase 5)
├── database-data-management/       # 8 files (Phase 5)
└── agent-learning/                 # 3 files
```

**Total:** 83 knowledge files across 11 knowledge domains

Each knowledge base contains markdown files with:
- Domain overview
- Best practices
- Common patterns
- Anti-patterns
- Specific topic guides
- Testing strategies

## Agent Integration

### Agents with Expert Support

The following agents have integrated expert consultation:

| Agent | Experts Used | Use Cases |
|-------|-------------|-----------|
| **Architect** | Security, Performance, UX, Software Architecture, Cloud Infrastructure, Database, API Design | System design, technology selection, security architecture, boundary definition, cloud architecture, database design |
| **Implementer** | Security, Performance, API Design, Database | Code generation, refactoring, secure coding practices, API implementation, database queries |
| **Reviewer** | Security, Performance, Testing, Accessibility, Code Quality, API Design | Code reviews, security audits, performance analysis, quality checks, API design reviews |
| **Tester** | Testing, API Design | Test generation (unit & integration), test strategy recommendations, contract testing |
| **Designer** | Accessibility, UX, Data Privacy, API Design | UI/UX design, design systems, API design, data model design |
| **Ops** | Security, Data Privacy, Observability, Cloud Infrastructure | Security scanning, compliance checks, deployment, infrastructure setup, monitoring and observability |

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
- `observability-monitoring` (Phase 5)
- `api-design-integration` (Phase 5)
- `cloud-infrastructure` (Phase 5)
- `database-data-management` (Phase 5)

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
Calculate Confidence
    ├─ Max confidence (40%)
    ├─ Agreement level (30%)
    ├─ RAG quality (20%)
    └─ Domain relevance (10%)
        ↓
Check Agent Threshold
    └─ Compare to agent-specific threshold
        ↓
Aggregate Responses
    └─ Weighted Answer (if confidence >= threshold)
```

## Agent-Specific Examples

### Architect Agent

```python
# System design with expert consultation
async def _design_system(self, requirements: str):
    if self.expert_registry:
        # Consult Software Architecture expert
        arch_consultation = await self.expert_registry.consult(
            query=f"Design system architecture for: {requirements}",
            domain="software-architecture",
            agent_id=self.agent_id,  # Uses architect threshold (0.75)
            prioritize_builtin=True
        )
        
        if arch_consultation.confidence >= arch_consultation.confidence_threshold:
            # Use expert guidance in prompt
            expert_guidance = arch_consultation.weighted_answer
```

### Tester Agent

```python
# Test generation with Testing expert
async def test_command(self, file: str):
    if self.expert_registry:
        testing_consultation = await self.expert_registry.consult(
            query=f"Best practices for generating tests for: {file}",
            domain="testing-strategies",
            agent_id=self.agent_id,  # Uses tester threshold (0.7)
            prioritize_builtin=True
        )
        
        if testing_consultation.confidence >= testing_consultation.confidence_threshold:
            expert_guidance = testing_consultation.weighted_answer
            # Pass to test generator
            test_code = await self.test_generator.generate_unit_tests(
                file_path, expert_guidance=expert_guidance
            )
```

### Designer Agent

```python
# UI design with UX and Accessibility experts
async def _design_ui(self, feature_description: str):
    ux_guidance = ""
    accessibility_guidance = ""
    
    if self.expert_registry:
        # Consult UX expert
        ux_consultation = await self.expert_registry.consult(
            query=f"UX best practices for: {feature_description}",
            domain="user-experience",
            agent_id=self.agent_id,  # Uses designer threshold (0.65)
            prioritize_builtin=True
        )
        if ux_consultation.confidence >= ux_consultation.confidence_threshold:
            ux_guidance = ux_consultation.weighted_answer
        
        # Consult Accessibility expert
        accessibility_consultation = await self.expert_registry.consult(
            query=f"Accessibility best practices for: {feature_description}",
            domain="accessibility",
            agent_id=self.agent_id,
            prioritize_builtin=True
        )
        if accessibility_consultation.confidence >= accessibility_consultation.confidence_threshold:
            accessibility_guidance = accessibility_consultation.weighted_answer
    
    # Include both in design prompt
    prompt = f"""Design UI/UX specifications...
    
UX Expert Guidance:
{ux_guidance}

Accessibility Expert Guidance:
{accessibility_guidance}
"""
```

### Ops Agent

```python
# Security scanning with Security expert
async def _handle_security_scan(self, target: str):
    if self.expert_registry:
        security_consultation = await self.expert_registry.consult(
            query=f"Security scanning best practices for: {target}",
            domain="security",
            agent_id=self.agent_id,  # Uses ops threshold (0.75)
            prioritize_builtin=True
        )
        
        if security_consultation.confidence >= security_consultation.confidence_threshold:
            security_guidance = security_consultation.weighted_answer
            # Include in security analysis prompt
```
        ↓
Calculate Confidence
    ├─ Max Expert Confidence (40%)
    ├─ Agreement Level (30%)
    ├─ RAG Quality (20%)
    └─ Domain Relevance (10%)
        ↓
Check Agent Threshold
    └─ Meets Threshold?
```

## Confidence Calculation

### Improved Confidence Algorithm (v2.1.0)

Expert consultations now use a sophisticated weighted confidence calculation:

```python
confidence = (
    max_confidence * 0.4 +      # Maximum expert confidence
    agreement_level * 0.3 +      # Expert agreement
    rag_quality * 0.2 +          # Knowledge base match quality
    domain_relevance * 0.1       # Domain relevance score
)
```

**Factors:**
- **Max Confidence (40%)**: Highest confidence from expert responses
- **Agreement Level (30%)**: How well experts agree on the answer
- **RAG Quality (20%)**: Quality of knowledge base retrieval
- **Domain Relevance (10%)**: How relevant the domain is to the query

### Agent-Specific Thresholds

Each agent type has a configurable confidence threshold:

| Agent | Default Threshold | Rationale |
|-------|------------------|-----------|
| Reviewer | 0.8 | High threshold for code reviews |
| Architect | 0.75 | High for architecture decisions |
| Implementer | 0.7 | Medium-high for code generation |
| Designer | 0.65 | Medium for design decisions |
| Tester | 0.7 | Medium-high for test generation |
| Ops | 0.75 | High for operations |
| Enhancer | 0.6 | Medium for enhancements |
| Analyst | 0.65 | Medium for analysis |
| Planner | 0.6 | Medium for planning |
| Debugger | 0.7 | Medium-high for debugging |
| Documenter | 0.5 | Lower for documentation |
| Orchestrator | 0.6 | Medium for orchestration |

**Configuration:**
```yaml
# .tapps-agents/config.yaml
agents:
  reviewer:
    min_confidence_threshold: 0.8
  architect:
    min_confidence_threshold: 0.75
```

### Confidence Metrics Tracking

All expert consultations are automatically tracked for analysis:

```python
from tapps_agents.experts.confidence_metrics import get_tracker

tracker = get_tracker()

# Get statistics for an agent
stats = tracker.get_statistics(agent_id="reviewer", domain="security")
# Returns: {
#   "count": 150,
#   "avg_confidence": 0.82,
#   "min_confidence": 0.45,
#   "max_confidence": 0.98,
#   "avg_agreement": 0.75,
#   "threshold_meet_rate": 0.87,
#   "low_confidence_count": 12
# }
```

Metrics are persisted to `.tapps-agents/confidence_metrics.json`.

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

### Example 4: Observability Setup

```python
class OpsAgent(BaseAgent, ExpertSupportMixin):
    async def setup_observability(self, service_name: str):
        result = await self._consult_builtin_expert(
            query=f"Best practices for setting up observability for {service_name}",
            domain="observability-monitoring"
        )
        
        if result and result.confidence >= result.confidence_threshold:
            return result.weighted_answer
        return "Standard observability setup recommended"
```

### Example 5: API Design Review

```python
class DesignerAgent(BaseAgent, ExpertSupportMixin):
    async def review_api_design(self, api_spec: str):
        result = await self._consult_builtin_expert(
            query=f"Review this API design:\n{api_spec}",
            domain="api-design-integration"
        )
        
        return {
            "recommendations": result.weighted_answer if result else "No issues found",
            "confidence": result.confidence if result else 0.0
        }
```

### Example 6: Database Design Consultation

```python
class ArchitectAgent(BaseAgent, ExpertSupportMixin):
    async def design_database(self, requirements: str):
        result = await self._consult_builtin_expert(
            query=f"Design database schema for: {requirements}",
            domain="database-data-management"
        )
        
        if result and result.confidence >= result.confidence_threshold:
            return result.weighted_answer
        return "Standard relational database recommended"
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

