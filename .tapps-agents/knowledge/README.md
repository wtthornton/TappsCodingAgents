# Knowledge Base

This directory contains domain-specific knowledge files for your business experts.

**Last updated**: 2026-02. Keep content current; remove or replace outdated material.

## Directory Structure

Organize knowledge by domain:

```
knowledge/
  payments/
    payment-gateways.md
    pci-compliance.md
  inventory/
    stock-management.md
    warehouse-operations.md
  analytics/
    reporting-requirements.md
    data-sources.md
```

## Adding Knowledge

1. Create a directory for each domain (e.g., `payments/`, `inventory/`)
2. Add markdown files with domain knowledge
3. Reference these domains in `.tapps-agents/experts.yaml`

## Knowledge File Format

Use standard markdown. Include:
- Domain concepts and terminology
- Business rules and constraints
- Integration patterns
- Common workflows
- Examples and use cases

## Example Knowledge File

```markdown
# Payment Processing Domain

## Overview
Our payment system integrates with Stripe and PayPal.

## Business Rules
- Minimum transaction amount: $0.50
- Maximum transaction amount: $10,000
- Refunds must be processed within 30 days

## Integration Points
- Stripe API for credit cards
- PayPal API for PayPal payments
- Internal accounting system for reconciliation
```

## How It's Used

Knowledge files are automatically indexed and made available to:
- Expert agents during code generation
- RAG (Retrieval-Augmented Generation) queries
- Context-aware code reviews and suggestions

For more information, see `.tapps-agents/domains.md`.
