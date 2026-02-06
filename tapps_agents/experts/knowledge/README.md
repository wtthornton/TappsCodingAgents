# Built-in Expert Knowledge Bases

This directory contains knowledge bases for built-in framework experts. These knowledge bases provide technical domain expertise that ships with the TappsCodingAgents framework.

**Last reviewed**: 2026-02. Keep content current with latest practices; remove or replace deprecated material.

## Structure

Each expert has its own subdirectory containing markdown knowledge files:

```
knowledge/
├── security/                      # Security Expert knowledge base
│   ├── owasp-top10.md
│   ├── secure-coding-practices.md
│   ├── threat-modeling.md
│   └── vulnerability-patterns.md
├── performance/                   # Performance Expert (Phase 2)
│   ├── optimization-patterns.md
│   ├── caching.md
│   ├── scalability.md
│   ├── api-performance.md
│   ├── database-performance.md
│   ├── resource-management.md
│   ├── profiling.md
│   └── anti-patterns.md
├── testing/                       # Testing Expert (Phase 2)
│   ├── best-practices.md
│   ├── test-strategies.md
│   ├── test-design-patterns.md
│   ├── test-automation.md
│   ├── mocking.md
│   ├── test-data.md
│   ├── coverage-analysis.md
│   └── test-maintenance.md
├── data-privacy-compliance/       # Data Privacy Expert (Phase 3)
│   ├── gdpr.md
│   ├── ccpa.md
│   ├── hipaa.md
│   ├── privacy-by-design.md
│   ├── consent-management.md
│   ├── data-minimization.md
│   ├── data-retention.md
│   ├── data-subject-rights.md
│   ├── anonymization.md
│   └── encryption-privacy.md
├── accessibility/                 # Accessibility Expert (Phase 4)
│   ├── wcag-2.1.md
│   ├── wcag-2.2.md
│   ├── semantic-html.md
│   ├── aria-patterns.md
│   ├── keyboard-navigation.md
│   ├── screen-readers.md
│   ├── color-contrast.md
│   ├── accessible-forms.md
│   └── testing-accessibility.md
├── user-experience/               # UX Expert (Phase 4)
│   ├── ux-principles.md
│   ├── user-research.md
│   ├── user-journeys.md
│   ├── information-architecture.md
│   ├── interaction-design.md
│   ├── prototyping.md
│   ├── usability-heuristics.md
│   └── usability-testing.md
├── observability-monitoring/      # Observability Expert (Phase 5)
│   ├── distributed-tracing.md
│   ├── metrics-and-monitoring.md
│   ├── logging-strategies.md
│   ├── apm-tools.md
│   ├── slo-sli-sla.md
│   ├── alerting-patterns.md
│   ├── observability-best-practices.md
│   └── open-telemetry.md
├── api-design-integration/        # API Design Expert (Phase 5)
│   ├── restful-api-design.md
│   ├── graphql-patterns.md
│   ├── grpc-best-practices.md
│   ├── api-versioning.md
│   ├── rate-limiting.md
│   ├── api-gateway-patterns.md
│   ├── api-security-patterns.md
│   ├── contract-testing.md
│   ├── fastapi-patterns.md
│   ├── fastapi-testing.md
│   ├── websocket-patterns.md
│   ├── mqtt-patterns.md
│   ├── async-protocol-patterns.md
│   └── external-api-integration.md
├── cloud-infrastructure/          # Cloud Infrastructure Expert (Phase 5)
│   ├── cloud-native-patterns.md
│   ├── containerization.md
│   ├── container-health-checks.md
│   ├── kubernetes-patterns.md
│   ├── infrastructure-as-code.md
│   ├── serverless-architecture.md
│   ├── multi-cloud-strategies.md
│   ├── cost-optimization.md
│   ├── disaster-recovery.md
│   └── dockerfile-patterns.md
├── database-data-management/      # Database Expert (Phase 5)
│   ├── database-design.md
│   ├── sql-optimization.md
│   ├── nosql-patterns.md
│   ├── data-modeling.md
│   ├── migration-strategies.md
│   ├── scalability-patterns.md
│   ├── backup-and-recovery.md
│   ├── acid-vs-cap.md
│   ├── influxdb-patterns.md
│   ├── influxdb-connection-patterns.md
│   ├── flux-query-optimization.md
│   └── time-series-modeling.md
├── software-architecture/         # Software Architecture Expert
│   ├── microservices-patterns.md
│   ├── service-communication.md
│   └── docker-compose-patterns.md
├── code-quality-analysis/         # Code Quality & Analysis Expert
│   ├── static-analysis-patterns.md
│   ├── code-metrics.md
│   ├── complexity-analysis.md
│   ├── technical-debt-patterns.md
│   └── quality-gates.md
├── development-workflow/          # Development Workflow Expert (DevOps)
│   ├── ci-cd-patterns.md
│   ├── git-workflows.md
│   ├── build-strategies.md
│   ├── deployment-patterns.md
│   └── automation-best-practices.md
├── documentation-knowledge-management/ # Documentation & Knowledge Management Expert
│   ├── documentation-standards.md
│   ├── api-documentation-patterns.md
│   ├── knowledge-management.md
│   └── technical-writing-guide.md
├── agent-learning/                # Agent Learning Best Practices
│   ├── best-practices.md
│   ├── pattern-extraction.md
│   └── prompt-optimization.md
└── ai-frameworks/                 # AI Frameworks Expert
    ├── model-optimization.md
    └── openvino-patterns.md
```

## Knowledge Base Format

Knowledge files are written in Markdown format. The RAG system uses:

- **Headers** (`#`, `##`, `###`) to structure knowledge and prioritize search results
- **Code blocks** for examples
- **Lists** for checklists and guidelines
- **Plain text** for explanations

## Usage

Built-in experts automatically load knowledge from this directory when:
1. The expert is activated
2. RAG is enabled for the expert
3. The expert's `primary_domain` matches a subdirectory name

## Adding Knowledge

To add knowledge to a built-in expert:

1. Create or edit markdown files in the expert's subdirectory
2. Use clear headers and structure
3. Include code examples where relevant
4. Keep content focused and actionable
5. Update this README if adding new experts

## Knowledge Base Best Practices

- **Be specific**: Include concrete examples and patterns
- **Be current**: Keep knowledge up to date with latest practices (review annually; 2026 baseline)
- **Be comprehensive**: Cover common scenarios and edge cases
- **Be structured**: Use headers and sections for easy navigation
- **Be actionable**: Provide clear guidance and checklists

## References

- [Knowledge Base Guide](../../../docs/KNOWLEDGE_BASE_GUIDE.md)
- [Expert Configuration Guide](../../../docs/EXPERT_CONFIG_GUIDE.md)

