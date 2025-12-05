# TappsCodingAgents - Developer Guide

**How to use this framework in your projects**

---

## Table of Contents

1. [Quick Start (5 minutes)](#1-quick-start-5-minutes)
2. [Understanding the Framework](#2-understanding-the-framework)
3. [Setting Up Your Project](#3-setting-up-your-project)
4. [Defining Your Domains](#4-defining-your-domains)
5. [Using Workflow Agents](#5-using-workflow-agents)
6. [Working with Industry Experts](#6-working-with-industry-experts)
7. [IDE Integration](#7-ide-integration)
8. [Building Your Knowledge Base](#8-building-your-knowledge-base)
9. [Day-to-Day Workflows](#9-day-to-day-workflows)
10. [Advanced Topics](#10-advanced-topics)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Quick Start (5 minutes)

### Prerequisites

- **Ollama** installed ([ollama.com](https://ollama.com))
- **Python 3.12+** installed
- **Cursor** or **VS Code** IDE
- **8GB+ GPU** recommended (CPU works but slower)

### Step 1: Install Ollama and Pull a Model

```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull a coding model (pick based on your GPU)
ollama pull qwen2.5-coder:7b      # 8GB GPU
ollama pull qwen2.5-coder:14b     # 16GB GPU

# Pull an embedding model
ollama pull nomic-embed-text
```

### Step 2: Clone and Set Up

```bash
# Clone the framework
git clone https://github.com/wtthornton/TappsCodingAgents.git
cd TappsCodingAgents

# Create Python environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Test Local LLM

```bash
# Verify Ollama is running
ollama list

# Quick test
ollama run qwen2.5-coder:7b "Write a Python hello world function"
```

**You're ready!** Continue reading to learn how to use the framework.

---

## 2. Understanding the Framework

### What This Framework Does

TappsCodingAgents helps you work with AI coding assistants by providing:

1. **12 Workflow Agents** - Specialized agents for different SDLC tasks
2. **Industry Experts** - Domain knowledge experts you define per project
3. **Model Routing** - Automatically uses local models, falls back to cloud
4. **Knowledge Base** - RAG system for project/domain documentation

### The Two-Layer Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR PROJECT                                  │
├─────────────────────────────────────────────────────────────────┤
│  KNOWLEDGE LAYER (You Define)                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Expert A   │  │  Expert B   │  │  Expert C   │             │
│  │ (Domain 1)  │  │ (Domain 2)  │  │ (Domain 3)  │             │
│  │   51%       │  │   51%       │  │   51%       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  EXECUTION LAYER (Pre-built)                                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │analyst │ │planner │ │architect│ │designer│ │implement│ ...   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### The 12 Workflow Agents

| Agent | What It Does | When to Use |
|-------|--------------|-------------|
| **analyst** | Gathers requirements, estimates effort | Starting new features |
| **planner** | Creates stories, breaks down tasks | Sprint planning |
| **architect** | Designs systems, makes tech decisions | New services, major changes |
| **designer** | Creates APIs, data models, UI specs | Before implementation |
| **implementer** | Writes production code | Coding features |
| **debugger** | Investigates and fixes bugs | Bug hunting |
| **documenter** | Writes documentation | After implementation |
| **reviewer** | Reviews code, provides feedback | Before merging |
| **improver** | Refactors and enhances code | Code quality |
| **tester** | Writes and fixes tests | Test coverage |
| **ops** | Security scanning, deployment | Release prep |
| **orchestrator** | Coordinates workflows | Complex multi-step tasks |

---

## 3. Setting Up Your Project

### Project Structure

Create this structure in your project:

```
your-project/
├── .tapps-agents/                    # Agent configuration
│   ├── domains.md                    # Your business domains
│   ├── config.yaml                   # Agent settings
│   └── expert_weights.yaml           # Auto-generated
│
├── .claude/skills/                   # Claude Code Skills (optional)
│   ├── implementer/SKILL.md
│   ├── reviewer/SKILL.md
│   └── expert-domain-1/SKILL.md
│
├── knowledge/                        # RAG knowledge base
│   ├── domain-1/
│   │   ├── docs/                     # Domain documentation
│   │   └── patterns/                 # Code patterns
│   └── domain-2/
│
└── your-code/                        # Your actual project code
```

### Basic Configuration

Create `.tapps-agents/config.yaml`:

```yaml
# .tapps-agents/config.yaml

project:
  name: "My Project"
  description: "What your project does"

# LLM Configuration
llm:
  primary:
    provider: ollama
    model: qwen2.5-coder:7b        # Match your GPU
  fallback:
    provider: anthropic
    model: claude-3.5-haiku
    api_key: ${ANTHROPIC_API_KEY}  # Set in environment

# RAG Configuration  
rag:
  enabled: true
  vector_db: chromadb
  embedding:
    provider: ollama
    model: nomic-embed-text
  persistence: ./.tapps-agents/vectors

# Domains (reference your domains.md)
domains_file: ./domains.md
```

---

## 4. Defining Your Domains

### What Are Domains?

Domains are the **business areas** your project covers. Each domain gets an Industry Expert.

**Examples:**
- HomeIQ project: Home Automation, Energy Management, Device Intelligence
- E-commerce project: Catalog, Checkout, Inventory, Shipping
- Healthcare project: Patient Records, Billing, Compliance

### Create Your domains.md

Create `.tapps-agents/domains.md`:

```markdown
# domains.md

## Project: My E-Commerce Platform

### Domain 1: Product Catalog
- Product data management
- Categories and taxonomies
- Search and filtering
- Product variants (size, color)
- Inventory integration
- **Primary Expert:** expert-catalog

### Domain 2: Checkout & Payments
- Shopping cart management
- Payment gateway integration (Stripe, PayPal)
- Order processing
- Tax calculation
- Discount/coupon handling
- **Primary Expert:** expert-checkout

### Domain 3: Customer Management
- User authentication
- Customer profiles
- Order history
- Wishlists and saved items
- Customer support integration
- **Primary Expert:** expert-customer
```

### How Experts Work Together

With 3 domains, you get 3 experts with this weight distribution:

```
                    Catalog     Checkout    Customer
                   ──────────────────────────────────
expert-catalog      51.00%      24.50%      24.50%    ← Primary for Catalog
expert-checkout     24.50%      51.00%      24.50%    ← Primary for Checkout  
expert-customer     24.50%      24.50%      51.00%    ← Primary for Customer
```

When making decisions:
- The primary expert has **51% authority** in their domain
- Other experts can **influence** (24.5% each) but not override
- This ensures domain expertise while allowing cross-domain input

---

## 5. Using Workflow Agents

### In Cursor IDE

Activate agents using `@agent-name` in the chat:

```
@implementer Add a function to calculate shipping costs based on weight and destination
```

```
@reviewer Review this PR for security issues and code quality
```

```
@architect Design a caching strategy for our product catalog
```

### Agent Behaviors

Each agent has specific behaviors:

#### @analyst
```
@analyst What are the requirements for implementing a wishlist feature?

The analyst will:
- Ask clarifying questions
- Research existing patterns in your codebase
- Identify dependencies and constraints
- Estimate complexity and effort
```

#### @implementer
```
@implementer Create a WishlistService class that handles adding/removing items

The implementer will:
- Follow your project's code patterns
- Write production-ready code
- Include error handling
- Add inline comments
- Consult domain experts if needed
```

#### @reviewer
```
@reviewer Review the WishlistService implementation

The reviewer will:
- Check code quality
- Identify potential bugs
- Suggest improvements
- Verify security practices
- NOT make changes (read-only)
```

### Chaining Agents

For complex tasks, chain agents together:

```
1. @analyst → Gather requirements for user notifications
2. @architect → Design the notification system
3. @designer → Define the API contracts
4. @implementer → Build the notification service
5. @tester → Write tests for the service
6. @reviewer → Final review before merge
```

---

## 6. Working with Industry Experts

### When to Consult Experts

Workflow agents automatically consult experts when:
- Making domain-specific decisions
- Writing domain-specific code
- Validating domain correctness

You can also explicitly invoke them:

```
@expert-catalog What's the best way to handle product variants?
```

### Expert Knowledge Sources

Experts get their knowledge from:

1. **RAG Knowledge Base** - Documents you provide
2. **Project Context** - Your codebase patterns
3. **Base Training** - The underlying LLM's knowledge
4. **Fine-tuning** (optional) - Custom training on your data

### Building Expert Knowledge

Add documents to your knowledge base:

```
knowledge/
├── catalog/
│   ├── docs/
│   │   ├── product-schema.md        # How products are structured
│   │   ├── variant-handling.md      # How variants work
│   │   └── search-indexing.md       # Search implementation
│   └── patterns/
│       ├── repository-pattern.py    # Code examples
│       └── validation-rules.py      # Domain validation
```

The expert will retrieve relevant documents when answering questions.

---

## 7. IDE Integration

### Cursor IDE (Recommended)

#### Installing Agent Skills

Copy agent skills to your project:

```bash
# From TappsCodingAgents repo
cp -r agents/* your-project/.claude/skills/
```

#### Using Skills in Cursor

1. Open Cursor settings
2. Enable "Agent Skills" 
3. Skills are automatically loaded from `.claude/skills/`
4. Use `@agent-name` in chat to activate

#### MCP Integration

For advanced tool access, configure MCP in Cursor:

```json
// .cursor/mcp.json
{
  "servers": {
    "tapps-agents": {
      "command": "python",
      "args": ["-m", "tapps_agents.mcp_server"],
      "env": {
        "OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

### VS Code

#### Using with Continue Extension

1. Install [Continue](https://continue.dev) extension
2. Configure local model:

```json
// ~/.continue/config.json
{
  "models": [
    {
      "title": "Qwen Coder (Local)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    }
  ]
}
```

3. Use slash commands for agent behaviors:
   - `/implement` - Code implementation
   - `/review` - Code review
   - `/test` - Generate tests

---

## 8. Building Your Knowledge Base

### Adding Documents

1. **Create knowledge directories:**

```bash
mkdir -p knowledge/domain-name/docs
mkdir -p knowledge/domain-name/patterns
```

2. **Add documentation:**

```markdown
<!-- knowledge/checkout/docs/payment-flow.md -->

# Payment Processing Flow

## Overview
Our payment system integrates with Stripe for card payments.

## Flow
1. Customer enters payment details
2. Frontend creates Stripe PaymentIntent
3. Backend validates and confirms payment
4. Order status updated on webhook

## Important Rules
- Never store raw card numbers
- Always use Stripe webhooks for confirmation
- Implement idempotency keys for retries
```

3. **Add code patterns:**

```python
# knowledge/checkout/patterns/payment-service.py
"""
Example payment service implementation.
Use this pattern for payment-related code.
"""

class PaymentService:
    def __init__(self, stripe_client):
        self.stripe = stripe_client
    
    async def create_payment_intent(
        self, 
        amount: int, 
        currency: str = "usd"
    ) -> PaymentIntent:
        """Create a Stripe PaymentIntent."""
        return await self.stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={"enabled": True}
        )
```

### Indexing Your Knowledge Base

```bash
# Index documents for RAG
python -m tapps_agents.index_knowledge \
  --source ./knowledge \
  --output ./.tapps-agents/vectors
```

### Querying the Knowledge Base

```
@expert-checkout How do we handle failed payments?

The expert will:
1. Search the knowledge base for "failed payments"
2. Find relevant docs (payment-flow.md, error-handling.md)
3. Provide an answer grounded in YOUR documentation
```

---

## 9. Day-to-Day Workflows

### Starting a New Feature

```
1. Define the feature
   @analyst What do we need to implement a customer review system?

2. Plan the work
   @planner Break down the review system into stories

3. Design the solution
   @architect How should the review system integrate with our catalog?
   @designer Define the API for submitting and retrieving reviews

4. Implement
   @implementer Create the Review model and ReviewService

5. Test
   @tester Write tests for the review submission flow

6. Review
   @reviewer Check the implementation for issues

7. Document
   @documenter Add API documentation for the review endpoints
```

### Debugging an Issue

```
1. Investigate
   @debugger Users report slow checkout - investigate the payment flow

2. Identify
   @analyst What's causing the latency? Check the payment service logs

3. Fix
   @implementer Optimize the payment intent creation to use caching

4. Verify
   @tester Add a performance test for payment flow
```

### Code Review

```
@reviewer Review this PR focusing on:
- Security (payment data handling)
- Performance (database queries)
- Error handling (edge cases)
- Code style (project conventions)
```

### Refactoring

```
@improver Refactor the OrderService to:
- Split into smaller methods
- Add better error handling
- Improve type hints
- Remove code duplication
```

---

## 10. Advanced Topics

### Custom Agent Behaviors

Customize agent behavior in `.tapps-agents/customizations/`:

```yaml
# .tapps-agents/customizations/implementer-custom.yaml

agent_id: implementer

persona_overrides:
  additional_principles:
    - "Always use type hints"
    - "Prefer composition over inheritance"
    - "Write docstrings for public methods"

code_style:
  formatter: "black"
  max_line_length: 88
  
project_context:
  always_load:
    - "docs/coding-standards.md"
    - "docs/architecture-decisions.md"
```

### Fine-Tuning an Expert (Advanced)

If RAG isn't enough, fine-tune an expert:

```bash
# Prepare training data
python -m tapps_agents.prepare_training \
  --domain checkout \
  --source ./knowledge/checkout \
  --output ./training/checkout.jsonl

# Fine-tune with Unsloth (requires 8GB+ GPU)
python -m tapps_agents.finetune \
  --base-model qwen2.5-coder:7b \
  --training-data ./training/checkout.jsonl \
  --output ./adapters/checkout-expert \
  --method qlora
```

### Multi-Project Setup

Share agents across projects:

```
~/tapps-agents/                     # Global installation
├── agents/                         # Shared agent definitions
├── profiles/                       # Shared model profiles
└── adapters/                       # Shared fine-tuned adapters

~/projects/project-a/
└── .tapps-agents/
    ├── domains.md                  # Project-specific domains
    └── config.yaml                 # Links to global agents

~/projects/project-b/
└── .tapps-agents/
    ├── domains.md                  # Different domains
    └── config.yaml                 # Same agents, different experts
```

---

## 11. Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve

# Or restart
# Windows: Restart from system tray
# macOS: brew services restart ollama
# Linux: systemctl restart ollama
```

### Model Too Slow

```bash
# Check if GPU is being used
ollama ps

# If using CPU, verify GPU drivers:
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# Try a smaller model
ollama pull qwen2.5-coder:7b
```

### Out of VRAM

```bash
# Use a smaller model
ollama pull deepseek-coder-v2:lite  # Only 1.6GB

# Or enable cloud fallback in config
fallback:
  provider: anthropic
  model: claude-3.5-haiku
```

### RAG Not Finding Documents

```bash
# Re-index the knowledge base
python -m tapps_agents.index_knowledge --force

# Check what's indexed
python -m tapps_agents.query_knowledge "test query" --debug
```

### Agent Not Behaving as Expected

1. Check if the right model is loaded:
   ```bash
   ollama ps
   ```

2. Verify config is correct:
   ```bash
   cat .tapps-agents/config.yaml
   ```

3. Try explicit agent invocation:
   ```
   @implementer [explicit instructions here]
   ```

4. Check for customization conflicts:
   ```bash
   cat .tapps-agents/customizations/*.yaml
   ```

---

## Quick Reference

### Agent Commands

| Command | Description |
|---------|-------------|
| `@analyst` | Requirements gathering, estimation |
| `@planner` | Story creation, task breakdown |
| `@architect` | System design, tech decisions |
| `@designer` | API/data model design |
| `@implementer` | Write code |
| `@debugger` | Fix bugs |
| `@documenter` | Write docs |
| `@reviewer` | Code review (read-only) |
| `@improver` | Refactor code |
| `@tester` | Write/fix tests |
| `@ops` | Security, deployment |
| `@orchestrator` | Coordinate workflows |
| `@expert-{domain}` | Domain expert consultation |

### Key Files

| File | Purpose |
|------|---------|
| `.tapps-agents/config.yaml` | Main configuration |
| `.tapps-agents/domains.md` | Business domain definitions |
| `knowledge/{domain}/` | RAG knowledge base |
| `.claude/skills/` | Cursor agent skills |

### Useful Commands

```bash
# Check Ollama status
ollama list
ollama ps

# Index knowledge base
python -m tapps_agents.index_knowledge

# Test local model
ollama run qwen2.5-coder:7b "Hello"

# Check GPU usage
nvidia-smi
```

---

## Next Steps

1. ✅ Complete Quick Start (Section 1)
2. ✅ Set up your project structure (Section 3)
3. ✅ Define your domains (Section 4)
4. ✅ Start using workflow agents (Section 5)
5. 📚 Build your knowledge base over time (Section 8)
6. 🚀 Explore advanced features as needed (Section 10)

---

*Questions? Issues? Open a GitHub issue or check the [PROJECT_REQUIREMENTS.md](../requirements/PROJECT_REQUIREMENTS.md) for detailed specifications.*

