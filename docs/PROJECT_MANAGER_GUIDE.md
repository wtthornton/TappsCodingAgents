# TappsCodingAgents - Project Manager Guide

**How to leverage AI agents for project success**

---

## Table of Contents

1. [Introduction: What This Means for PMs](#1-introduction-what-this-means-for-pms)
2. [Understanding the Framework](#2-understanding-the-framework)
3. [Project Setup and Configuration](#3-project-setup-and-configuration)
4. [Defining Business Domains](#4-defining-business-domains)
5. [Managing Requirements](#5-managing-requirements)
6. [Planning and Story Creation](#6-planning-and-story-creation)
7. [Workflow Orchestration](#7-workflow-orchestration)
8. [Quality and Review Processes](#8-quality-and-review-processes)
9. [Domain Knowledge Management](#9-domain-knowledge-management)
10. [Measuring Success](#10-measuring-success)
11. [Common Workflows](#11-common-workflows)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Introduction: What This Means for PMs

### Why PMs Should Care

As a Project Manager, this framework helps you:

- ✅ **Accelerate Delivery** - Agents handle routine SDLC tasks automatically
- ✅ **Improve Quality** - Consistent quality gates and automated reviews
- ✅ **Reduce Technical Debt** - Built-in refactoring and improvement agents
- ✅ **Scale Expertise** - Industry Experts capture and apply domain knowledge
- ✅ **Better Planning** - AI-assisted story breakdown and estimation
- ✅ **Faster Onboarding** - Knowledge base accelerates team ramp-up

### What You Need to Know (PM Edition)

**You don't need to be a developer** to use this framework effectively. Your primary responsibilities are:

1. **Define Business Domains** - What business areas does your project cover?
2. **Manage Requirements** - Guide the analyst agent in gathering requirements
3. **Plan Work** - Use planner agent to create stories and break down work
4. **Curate Knowledge** - Build the knowledge base with domain documentation
5. **Coordinate Workflows** - Orchestrate agents for complex features
6. **Ensure Quality** - Leverage review and testing agents for quality gates

### The PM-Developer Partnership

```
PM Responsibilities                    Developer Responsibilities
───────────────────────────────────────────────────────────────
• Define domains                       • Configure agents
• Write requirements                   • Write code
• Create stories                       • Review code
• Manage knowledge base                • Build features
• Coordinate workflows                 • Debug issues
• Quality oversight                    • Technical implementation
```

**You focus on WHAT and WHY. Developers focus on HOW.**

---

## 2. Understanding the Framework

### Two-Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              YOUR PROJECT (PM-Managed Layer)                  │
├──────────────────────────────────────────────────────────────┤
│  KNOWLEDGE LAYER (You Define)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Expert A     │  │ Expert B     │  │ Expert C     │       │
│  │ (Domain 1)   │  │ (Domain 2)   │  │ (Domain 3)   │       │
│  │ Business     │  │ Business     │  │ Business     │       │
│  │ Knowledge    │  │ Knowledge    │  │ Knowledge    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├──────────────────────────────────────────────────────────────┤
│  EXECUTION LAYER (Pre-built Agents)                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │analyst │ │planner │ │architect│ │implement│ │reviewer│    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                               │
│  These agents execute SDLC tasks automatically               │
└──────────────────────────────────────────────────────────────┘
```

### The 12 Workflow Agents (PM Perspective)

| Agent | PM Use Case | What It Does for You |
|-------|-------------|----------------------|
| **analyst** | Requirements gathering | Asks stakeholders questions, documents requirements, estimates effort |
| **planner** | Sprint planning | Breaks features into stories, creates task breakdowns |
| **architect** | Technical decisions | Designs systems (you review business alignment) |
| **designer** | API/UI specs | Creates specifications before implementation |
| **implementer** | Code writing | Writes production code (developers review) |
| **debugger** | Bug investigation | Identifies and fixes bugs |
| **documenter** | Documentation | Creates user guides, API docs, runbooks |
| **reviewer** | Quality gates | Reviews code before merging (read-only) |
| **improver** | Technical debt | Refactors code, improves quality |
| **tester** | Test coverage | Writes and maintains tests |
| **ops** | Deployment | Handles security scans, deployment checks |
| **orchestrator** | Complex workflows | Coordinates multiple agents for large features |

### Industry Experts: Your Domain Authorities

**Industry Experts are BUSINESS experts, not technical experts.**

They understand:
- ✅ Business rules and constraints
- ✅ Domain-specific terminology
- ✅ Regulatory/compliance requirements
- ✅ User workflows and personas
- ✅ Industry best practices

They don't understand (that's for workflow agents):
- ❌ Technical implementation details
- ❌ Code patterns and frameworks
- ❌ System architecture (unless domain-specific)

**Example:**
- **Expert:** "In healthcare billing, we must validate ICD-10 codes before submission"
- **Architect Agent:** "I'll design a validation service using this pattern..."

---

## 3. Project Setup and Configuration

### Initial Setup (PM Tasks)

#### Step 1: Define Project Structure

Create these files in your project:

```
your-project/
├── .tapps-agents/
│   ├── domains.md              ← YOU CREATE THIS (Section 4)
│   ├── config.yaml             ← Developer creates (you review)
│   └── expert_weights.yaml     ← Auto-generated
│
└── knowledge/                  ← YOU MANAGE THIS (Section 9)
    ├── domain-1/
    │   ├── docs/               ← Business documentation
    │   └── requirements/       ← Requirements, user stories
    └── domain-2/
```

#### Step 2: Review Configuration (Optional)

You may want to review `.tapps-agents/config.yaml` for business alignment:

```yaml
project:
  name: "My Project"
  description: "What your project does"  # ← Ensure this is accurate

# Domains file (you created this)
domains_file: ./domains.md

# LLM Configuration (developers handle this)
llm:
  primary:
    provider: ollama
    model: qwen2.5-coder:7b
```

**PM Focus:** Ensure `project.name` and `project.description` accurately reflect business goals.

---

## 4. Defining Business Domains

### What Are Business Domains?

**Domains are the business areas your project covers.** Each domain represents a distinct area of business knowledge.

**Examples:**

| Project Type | Domains |
|--------------|---------|
| **E-commerce** | Product Catalog, Checkout & Payments, Customer Management |
| **Healthcare** | Patient Records, Billing, Compliance, Clinical Workflows |
| **Home Automation** | Device Management, Energy Management, User Experience |
| **Banking** | Account Management, Transactions, Compliance, Fraud Detection |

### Creating domains.md

This is **YOUR primary responsibility** as PM. Create `.tapps-agents/domains.md`:

```markdown
# Business Domains

## Project: My E-Commerce Platform

### Domain 1: Product Catalog
**Description:** Managing product information, categories, and search.

**Business Rules:**
- Products must have at least one category
- Variants (size, color) share the same SKU base
- Search must support filtering by price, category, rating

**Key Personas:**
- Product Manager (adds/edits products)
- Customer (browses/searches products)

**Regulatory/Compliance:**
- Must display accurate pricing (consumer protection)
- Age restrictions for certain products

**Primary Expert:** expert-catalog

---

### Domain 2: Checkout & Payments
**Description:** Shopping cart, payment processing, and order creation.

**Business Rules:**
- Cart expires after 30 minutes of inactivity
- Multiple payment methods supported (card, PayPal, Apple Pay)
- Tax calculated based on shipping address
- Discount codes apply to cart total before tax

**Key Personas:**
- Customer (checkout flow)
- Payment Processor (Stripe integration)

**Regulatory/Compliance:**
- PCI DSS compliance required
- Store payment data securely (never raw card numbers)

**Primary Expert:** expert-checkout

---

### Domain 3: Customer Management
**Description:** User accounts, profiles, order history, preferences.

**Business Rules:**
- Email verification required for account creation
- Password must meet security requirements
- Customers can save multiple shipping addresses
- Order history visible for 2 years

**Key Personas:**
- Customer (manages account)
- Support Agent (helps customers)

**Regulatory/Compliance:**
- GDPR: Right to data deletion
- Email preferences must be honored

**Primary Expert:** expert-customer
```

### Domain Definition Checklist

For each domain, include:

- ✅ **Description** - What business area does this cover?
- ✅ **Business Rules** - What rules/constraints apply?
- ✅ **Key Personas** - Who are the users?
- ✅ **Regulatory/Compliance** - What requirements must we meet?
- ✅ **Primary Expert** - Auto-assigned name (expert-{domain-name})

### How Experts Work Together

With 3 domains, you get 3 experts with weighted influence:

```
                    Catalog     Checkout    Customer
                   ──────────────────────────────────
expert-catalog      51.00%      24.50%      24.50%    ← Primary for Catalog
expert-checkout     24.50%      51.00%      24.50%    ← Primary for Checkout  
expert-customer     24.50%      24.50%      51.00%    ← Primary for Customer
```

**Decision-Making:**
- Primary expert has **51% authority** in their domain
- Other experts can **influence** (24.5% each) but not override
- This ensures domain expertise while allowing cross-domain input

**Example:**
- **Feature:** "Add wishlist items to cart"
- **Expert-catalog:** "Wishlists are part of catalog domain" (51% weight)
- **Expert-checkout:** "But we should validate cart limits" (24.5% weight)
- **Expert-customer:** "And remember user preferences" (24.5% weight)

---

## 5. Managing Requirements

### Using the Analyst Agent

The **@analyst** agent helps you gather requirements systematically.

#### Starting Requirements Gathering

```
@analyst I need to implement a customer review system. Help me gather requirements.

The analyst will:
1. Ask clarifying questions
2. Identify stakeholders
3. Document functional requirements
4. Identify non-functional requirements (performance, security)
5. Estimate complexity and effort
```

#### Example Analyst Interaction

**You:**
```
@analyst We need to add product reviews. Customers should be able to:
- Write reviews after purchase
- Rate products 1-5 stars
- See all reviews for a product
- Filter reviews by rating
```

**Analyst Response:**
```
I'll help you gather requirements for the product review system.

Questions:
1. Can customers edit their reviews after submission?
2. Should we allow verified purchase badges?
3. What moderation is needed (profanity filter, manual review)?
4. Should reviews be sortable (newest, highest rated, most helpful)?
5. Can customers upload photos with reviews?

Stakeholders to consult:
- Product Manager (you)
- Customer Support (moderation policies)
- Legal (liability, fake reviews)
- UX Team (review display design)

Initial Complexity Estimate:
- Medium (3-5 days)
- Dependencies: Product catalog, Customer management
```

#### Refining Requirements

Continue the conversation:

```
@analyst For the review system:
- Yes, customers can edit reviews (within 30 days)
- Verified purchase badges are required
- Automatic profanity filter + manual review for flagged content
- Sortable by newest, highest rated, most helpful
- Photo uploads: yes, up to 3 photos per review
```

The analyst will document these requirements.

### Storing Requirements

Save analyst outputs to your knowledge base:

```
knowledge/
├── catalog/
│   └── requirements/
│       ├── review-system.md          ← Analyst output
│       └── review-system-estimate.md ← Effort breakdown
```

### Requirements Templates

Create templates for consistency:

```markdown
# Feature Requirements Template

## Feature Name
[Name of feature]

## Business Goal
[Why are we building this?]

## User Stories
- As a [persona], I want to [action] so that [benefit]

## Functional Requirements
1. [Requirement 1]
2. [Requirement 2]

## Non-Functional Requirements
- Performance: [target]
- Security: [requirements]
- Compliance: [regulations]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Dependencies
- [Feature/service dependency]

## Effort Estimate
[Story points or days]
```

Use the analyst agent to fill out these templates:

```
@analyst Use this template to document the review system requirements:
[paste template]

Fill it out based on our discussion.
```

---

## 6. Planning and Story Creation

### Using the Planner Agent

The **@planner** agent breaks down features into stories and tasks.

#### Creating Stories from Requirements

```
@planner Create user stories for the product review system based on:
[paste requirements document]

Break down into:
- User stories (As a... I want... So that...)
- Technical tasks
- Dependencies between stories
- Story point estimates
```

#### Example Planner Output

**Planner Response:**
```
## User Stories

### Story 1: Write Review (3 points)
**As a** customer  
**I want** to write a review after purchase  
**So that** I can share my experience with other customers

**Tasks:**
- Create Review model (database)
- Build review form UI
- Implement submission API
- Add validation (purchase verification)
- Add photo upload

**Dependencies:** Customer management (purchase history)

---

### Story 2: Display Reviews (2 points)
**As a** customer  
**I want** to see product reviews  
**So that** I can make informed purchase decisions

**Tasks:**
- Create review display component
- Implement filtering (rating, sort)
- Add pagination
- Show verified purchase badges

**Dependencies:** Story 1 (reviews must exist)

---

### Story 3: Moderate Reviews (5 points)
**As a** support agent  
**I want** to moderate flagged reviews  
**So that** we maintain quality and compliance

**Tasks:**
- Implement profanity filter
- Create moderation dashboard
- Add flagging mechanism
- Build approval/rejection workflow

**Dependencies:** Story 1
```

### Story Refinement

Review planner output and refine:

```
@planner For Story 1, add these acceptance criteria:
- Review must be submitted within 90 days of purchase
- Photo uploads are optional, max 3 photos, 5MB each
- Stars rating is required, text review is optional
```

### Exporting to Project Management Tools

Planner can format stories for import:

```
@planner Export these stories as:
- Jira JSON format
- Linear markdown format
- GitHub Issues format
```

---

## 7. Workflow Orchestration

### When to Use Orchestrator

For complex features, use **@orchestrator** to coordinate multiple agents:

```
@orchestrator Coordinate implementation of the review system:
1. Analyst - Gather detailed requirements
2. Architect - Design the review system architecture
3. Designer - Create API specifications
4. Planner - Break down into stories
5. Implementer - Build the review service (stories 1-2)
6. Tester - Write tests for review submission
7. Reviewer - Code review before merge

Execute this workflow step by step.
```

### Manual Orchestration (Alternative)

If you prefer step-by-step control:

```
1. @analyst → Gather requirements
2. Review analyst output
3. @architect → Design system
4. Review architecture (ensure business alignment)
5. @planner → Create stories
6. Assign stories to developers
7. @reviewer → Review PRs
8. @documenter → Update user docs
```

### Workflow Templates

Create reusable workflow templates:

```markdown
# Standard Feature Workflow

## Phase 1: Discovery
- @analyst - Gather requirements
- Review and approve requirements

## Phase 2: Design
- @architect - System design
- @designer - API/UI specs
- Review for business alignment

## Phase 3: Planning
- @planner - Create stories
- Prioritize stories
- Assign to sprint

## Phase 4: Implementation
- Developer: @implementer
- Developer: @tester
- @reviewer - Code review

## Phase 5: Delivery
- @ops - Security scan
- @documenter - Update docs
- Release
```

---

## 8. Quality and Review Processes

### Code Review Workflow

Use **@reviewer** for quality gates:

```
@reviewer Review this PR for:
- Security issues (especially payment handling)
- Business logic correctness (checkout rules)
- Code quality and maintainability
- Test coverage

Provide a detailed review with specific recommendations.
```

### Quality Checklist (PM Perspective)

Before merging features, verify:

- ✅ **Business Requirements Met**
  - Does it match the requirements document?
  - Are acceptance criteria satisfied?

- ✅ **Domain Rules Followed**
  - Consult expert-{domain} if unsure
  - Verify compliance with business rules

- ✅ **Documentation Updated**
  - User-facing docs updated?
  - API docs updated?
  - Knowledge base updated?

- ✅ **Tests Pass**
  - @tester has written tests
  - All tests passing

- ✅ **Security Checked**
  - @ops security scan completed
  - No vulnerabilities introduced

### Automated Quality Gates

Configure quality gates in workflows:

```
Workflow: Feature Implementation
─────────────────────────────────
1. @implementer → Write code
2. @tester → Write tests
3. @reviewer → Code review (must pass)
4. @ops → Security scan (must pass)
5. Merge to main
```

**PM Role:** Ensure quality gates are enforced in your project.

---

## 9. Domain Knowledge Management

### Building the Knowledge Base

The knowledge base is **YOUR responsibility** as PM. It powers Industry Experts and RAG.

### Knowledge Base Structure

```
knowledge/
├── domain-1/                    ← Match your domains.md
│   ├── docs/                    ← Business documentation
│   │   ├── business-rules.md
│   │   ├── user-personas.md
│   │   ├── workflows.md
│   │   └── compliance.md
│   └── requirements/            ← Requirements and stories
│       ├── feature-requirements.md
│       └── user-stories.md
│
├── domain-2/
│   ├── docs/
│   └── requirements/
│
└── shared/                      ← Cross-domain knowledge
    ├── glossary.md              ← Terminology
    └── regulations.md           ← Regulatory requirements
```

### What to Include

#### Business Documentation

**business-rules.md:**
```markdown
# Business Rules: Product Catalog

## Product Management
- Products must belong to at least one category
- SKU format: {CATEGORY}-{ID}-{VARIANT}
- Product descriptions must be at least 50 characters

## Pricing Rules
- Price changes require manager approval
- Discounts cannot exceed 50% of original price
- Sale prices must include original price

## Inventory
- Low stock threshold: 10 units
- Out of stock products hidden from search
- Pre-orders allowed for new products
```

**user-personas.md:**
```markdown
# User Personas: Customer Management

## Primary Persona: Customer
- **Goals:** Manage account, view orders, update preferences
- **Pain Points:** Forgotten passwords, order tracking confusion
- **Key Tasks:** Login, update profile, view order history

## Secondary Persona: Support Agent
- **Goals:** Help customers, resolve issues quickly
- **Pain Points:** Lack of customer context, manual processes
- **Key Tasks:** View customer account, update orders, generate refunds
```

**workflows.md:**
```markdown
# User Workflows: Checkout

## Standard Checkout Flow
1. Customer adds items to cart
2. Customer clicks "Checkout"
3. Customer enters shipping address
4. System calculates tax and shipping
5. Customer selects payment method
6. Customer enters payment details
7. System processes payment
8. System creates order
9. Customer sees confirmation

## Edge Cases
- Cart expires after 30 minutes
- Payment fails → Retry option
- Inventory runs out → Notify customer
```

#### Requirements Documentation

Store all feature requirements and user stories:

```
knowledge/
└── catalog/
    └── requirements/
        ├── review-system-requirements.md
        ├── review-system-stories.md
        └── review-system-estimates.md
```

### Maintaining the Knowledge Base

**Regular Updates:**
- ✅ Add new feature requirements
- ✅ Update business rules when they change
- ✅ Document new user workflows
- ✅ Archive outdated information

**Knowledge Base Checklist:**
- [ ] Each domain has complete docs/
- [ ] Requirements are organized by feature
- [ ] Business rules are documented
- [ ] User personas are defined
- [ ] Workflows are documented
- [ ] Compliance requirements are captured

### Knowledge Base Updates

For project-defined experts, the knowledge base is file-based Markdown under `.tapps-agents/knowledge/<domain>/*.md`.

- **When it takes effect**: As soon as the files are updated (there is no separate indexing CLI step in the current implementation).

---

## 10. Measuring Success

### Key Metrics for PMs

| Metric | How to Measure | Target |
|--------|----------------|--------|
| **Feature Delivery Speed** | Stories completed per sprint | +20% faster |
| **Quality** | Bugs found in production | -50% reduction |
| **Requirements Accuracy** | Rework due to requirements issues | <10% of features |
| **Knowledge Base Coverage** | Domains with complete docs | 100% |
| **Agent Effectiveness** | Tasks completed by agents | 60-80% of routine tasks |

### Tracking Agent Usage

Review agent activity:

```
# Developers can provide this report
Agent Usage Report
──────────────────
@analyst: 15 tasks (requirements gathering)
@planner: 12 tasks (story creation)
@implementer: 45 tasks (code writing)
@reviewer: 30 tasks (code reviews)
@tester: 18 tasks (test writing)
```

### ROI Calculation

**Time Savings Example:**

| Task | Manual Time | Agent-Assisted Time | Savings |
|------|-------------|---------------------|---------|
| Requirements Gathering | 4 hours | 1 hour (review only) | 75% |
| Story Creation | 2 hours | 30 minutes | 75% |
| Code Review | 1 hour | 15 minutes | 75% |
| Documentation | 2 hours | 30 minutes | 75% |

**Per Sprint (20 stories):**
- Manual: 180 hours
- Agent-Assisted: 45 hours
- **Savings: 135 hours (75%)**

---

## 11. Common Workflows

### Starting a New Feature

```
1. Define Feature Goal
   → Document in knowledge base

2. Gather Requirements
   @analyst Help me gather requirements for [feature]
   → Save output to knowledge/domain/requirements/

3. Review Requirements
   → Ensure business alignment
   → Consult stakeholders

4. Create Stories
   @planner Create stories from these requirements: [paste]
   → Review and refine stories

5. Plan Sprint
   → Prioritize stories
   → Assign to developers

6. Monitor Progress
   → Review PRs (use @reviewer for quality)
   → Ensure acceptance criteria met

7. Verify Quality
   → @reviewer final review
   → @ops security scan
   → @tester test coverage check

8. Deliver
   → @documenter update user docs
   → Release
```

### Handling Bug Reports

```
1. Triage Bug
   → Determine domain (consult expert-{domain})

2. Investigate
   @debugger Investigate this bug: [description]
   → Review debugger findings

3. Plan Fix
   @planner Create a story to fix: [bug details]
   → Assign to developer

4. Verify Fix
   @reviewer Review the fix PR
   @tester Verify tests cover the bug scenario
```

### Refining Requirements Mid-Development

```
1. Identify Gap
   → Feature doesn't match requirements

2. Consult Expert
   @expert-{domain} What should happen when [scenario]?

3. Update Requirements
   → Update knowledge base document

4. Communicate Change
   → Notify developer
   → Update acceptance criteria

5. Verify Implementation
   @reviewer Ensure implementation matches updated requirements
```

### Onboarding New Team Members

```
1. Provide Knowledge Base Access
   → Share knowledge/ directory

2. Review Domains
   → Walk through domains.md

3. Demo Agent Usage
   → Show @analyst, @planner in action

4. Assign Starter Task
   → Use @analyst to gather requirements for small feature
   → Use @planner to create stories
   → Build feature with @implementer
```

---

## 12. Best Practices

### Domain Definition

✅ **DO:**
- Define domains by business areas, not technical boundaries
- Include business rules, personas, and compliance requirements
- Keep domains focused (3-5 domains per project)
- Update domains.md when business evolves

❌ **DON'T:**
- Create domains based on technical layers (frontend, backend)
- Have too many domains (harder to manage)
- Forget to update when business rules change

### Requirements Management

✅ **DO:**
- Use @analyst systematically for all features
- Store requirements in knowledge base
- Review analyst output before proceeding
- Update requirements when they change

❌ **DON'T:**
- Skip requirements gathering
- Store requirements in random locations
- Forget to communicate requirement changes

### Story Creation

✅ **DO:**
- Use @planner for consistent story format
- Review stories before sprint planning
- Ensure acceptance criteria are clear
- Link stories to requirements documents

❌ **DON'T:**
- Create stories without requirements
- Accept vague acceptance criteria
- Skip story refinement

### Knowledge Base

✅ **DO:**
- Keep knowledge base up-to-date
- Organize by domain
- Include business rules and workflows
- Document decisions and rationale

❌ **DON'T:**
- Let knowledge base get stale
- Store everything in one file
- Forget to archive outdated information

### Quality Gates

✅ **DO:**
- Enforce quality gates consistently
- Use @reviewer for all PRs
- Verify business alignment in reviews
- Ensure documentation is updated

❌ **DON'T:**
- Skip quality gates for "small" changes
- Approve PRs without business verification
- Merge without documentation updates

---

## 13. Troubleshooting

### Agent Not Understanding Requirements

**Problem:** Agent output doesn't match business needs.

**Solution:**
1. Review domains.md - is the domain correctly defined?
2. Check knowledge base - are business rules documented?
3. Consult expert: `@expert-{domain} [question]`
4. Provide more context in your prompt

### Stories Not Detailed Enough

**Problem:** @planner creates vague stories.

**Solution:**
1. Ensure requirements are complete before planning
2. Provide examples: "Create stories similar to: [example]"
3. Request specific format: "Include acceptance criteria for each story"
4. Refine: "Add more detail to story 1: [specific requirements]"

### Knowledge Base Not Being Used

**Problem:** Agents don't reference knowledge base.

**Solution:**
1. Verify knowledge base is indexed (ask developer)
2. Check document organization (should match domains)
3. Use explicit references: "Based on knowledge/catalog/docs/business-rules.md..."
4. Ensure documents are in knowledge/{domain}/docs/

### Quality Issues

**Problem:** Code quality or business logic issues slip through.

**Solution:**
1. Strengthen quality gates - require @reviewer approval
2. Use @reviewer with specific checklist
3. Consult domain expert before approving: `@expert-{domain} Does this align with [rule]?`
4. Review @reviewer output carefully

### Domain Expert Confusion

**Problem:** Expert gives conflicting advice.

**Solution:**
1. Check domains.md - ensure domains are distinct
2. Verify expert weights (should be 51% primary)
3. Use explicit domain: `@expert-catalog [question]` (not just `@expert`)
4. Review knowledge base - are rules documented clearly?

---

## Quick Reference

### PM Responsibilities

| Task | How to Do It | Agent/Resource |
|------|--------------|----------------|
| **Define Domains** | Create domains.md | Manual (you) |
| **Gather Requirements** | Use @analyst | @analyst |
| **Create Stories** | Use @planner | @planner |
| **Build Knowledge Base** | Document in knowledge/ | Manual (you) |
| **Quality Gates** | Use @reviewer | @reviewer |
| **Coordinate Workflows** | Use @orchestrator | @orchestrator |
| **Consult Domain Expert** | Use @expert-{domain} | @expert-{domain} |

### Key Files

| File | Your Role | Location |
|------|-----------|----------|
| **domains.md** | Create & maintain | `.tapps-agents/domains.md` |
| **knowledge/** | Build & curate | `knowledge/` |
| **config.yaml** | Review (optional) | `.tapps-agents/config.yaml` |
| **Requirements docs** | Create & manage | `knowledge/{domain}/requirements/` |

### Agent Commands (PM Use)

```
@analyst Gather requirements for [feature]
@planner Create stories from [requirements]
@orchestrator Coordinate [workflow]
@expert-{domain} [question]
@reviewer Review this for business alignment
@documenter Update user documentation for [feature]
```

### Knowledge Base Checklist

- [ ] Domains defined in domains.md
- [ ] Business rules documented
- [ ] User personas defined
- [ ] Workflows documented
- [ ] Requirements organized by feature
- [ ] Compliance requirements captured
- [ ] Knowledge base indexed (ask developer)

---

## Next Steps

1. ✅ Read this guide
2. ✅ Review [PROJECT_REQUIREMENTS.md](../requirements/PROJECT_REQUIREMENTS.md) for full spec
3. ✅ Create domains.md for your project
4. ✅ Start building knowledge base
5. ✅ Try @analyst for your next feature
6. ✅ Try @planner for story creation
7. 🚀 Integrate into your workflow

---

*Questions? Check the [Developer Guide](DEVELOPER_GUIDE.md) for technical details, or review [PROJECT_REQUIREMENTS.md](../requirements/PROJECT_REQUIREMENTS.md) for complete specifications.*

