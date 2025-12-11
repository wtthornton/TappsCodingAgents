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

### Current Implementation Status

**Phase 1 (Week 3 Day 2) - Complete:**
- ✅ Reviewer Agent with Code Scoring (99% coverage)
- ✅ Planner Agent with Story Generation (91% coverage)
- ✅ Configuration System
- ✅ BaseAgent Framework
- ✅ Model Abstraction Layer (MAL)
- ✅ Comprehensive test suite (96 tests, 69% coverage)

**Available Now:**
- Code review with scoring (`*review` command)
- Code scoring without LLM feedback (`*score` command)
- Story generation and planning (`*plan`, `*create-story`, `*list-stories` commands)
- Configuration via `.tapps-agents/config.yaml`
- All 5 scoring metrics (complexity, security, maintainability, test_coverage, performance)

**Coming Soon:**
- Additional workflow agents (10 remaining)
- MCP Gateway
- Tiered Context System
- Workflow Engine
- Industry Experts

### Prerequisites

- **Ollama** installed ([ollama.com](https://ollama.com))
- **Python 3.10+** installed (3.13+ recommended)
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

### Reviewer Agent (Available Now)

The Reviewer Agent provides code review with comprehensive scoring. It's the first fully implemented agent.

#### Commands

```bash
# Review a file with scoring and LLM feedback
python -m tapps_agents.cli reviewer *review path/to/file.py

# Score only (no LLM feedback, faster)
python -m tapps_agents.cli reviewer *score path/to/file.py

# Show help
python -m tapps_agents.cli reviewer *help
```

#### Code Scoring Metrics

The Reviewer Agent calculates 5 objective quality metrics:

1. **Complexity Score** (0-10): Cyclomatic complexity (lower is better)
2. **Security Score** (0-10): Vulnerability detection (higher is better)
3. **Maintainability Score** (0-10): Code maintainability index (higher is better)
4. **Test Coverage Score** (0-10): Test coverage analysis (higher is better)
5. **Performance Score** (0-10): Static performance analysis (higher is better)

**Overall Score** (0-100): Weighted combination of all metrics.

#### Example Output

```json
{
  "file": "src/main.py",
  "scoring": {
    "complexity_score": 3.2,
    "security_score": 9.5,
    "maintainability_score": 8.1,
    "test_coverage_score": 7.0,
    "performance_score": 8.5,
    "overall_score": 78.5,
    "metrics": {
      "complexity": 3.2,
      "security": 9.5,
      "maintainability": 8.1,
      "test_coverage": 7.0,
      "performance": 8.5
    }
  },
  "feedback": {
    "summary": "Code quality is good overall...",
    "full_feedback": "..."
  },
  "passed": true,
  "threshold": 70.0
}
```

#### Configuration

Configure the Reviewer Agent in `.tapps-agents/config.yaml`:

```yaml
agents:
  reviewer:
    model: "qwen2.5-coder:7b"      # LLM model for feedback
    quality_threshold: 70.0         # Minimum overall score to pass
    include_scoring: true           # Include static scoring
    include_llm_feedback: true      # Include LLM-generated feedback
    max_file_size: 1048576          # Max file size in bytes (1MB)

scoring:
  weights:
    complexity: 0.20                # Weight for complexity score
    security: 0.30                  # Weight for security score
    maintainability: 0.25           # Weight for maintainability
    test_coverage: 0.15             # Weight for test coverage
    performance: 0.10               # Weight for performance
  quality_threshold: 70.0           # Overall score threshold
```

#### Performance

- **Small files** (< 100 lines): < 1 second
- **Medium files** (100-500 lines): 1-2 seconds
- **Large files** (500-1500 lines): 2-5 seconds
- **Very large files** (> 1500 lines): 5-10 seconds (scoring only recommended)

Performance scales linearly with file size. For very large files, use `*score` command (no LLM feedback) for faster results.

### Planner Agent (Available Now)

The Planner Agent generates user stories and task breakdowns for feature planning. It creates structured story files with acceptance criteria, tasks, and complexity estimates.

#### Commands

```bash
# Create a plan for a feature/requirement
python -m tapps_agents.cli planner plan "Add user authentication with OAuth2 support"

# Generate a user story from description
python -m tapps_agents.cli planner create-story "User should be able to log in with Google"

# Create story with epic and priority
python -m tapps_agents.cli planner create-story "Add shopping cart" --epic checkout --priority high

# List all stories
python -m tapps_agents.cli planner list-stories

# List stories filtered by epic
python -m tapps_agents.cli planner list-stories --epic checkout

# List stories filtered by status
python -m tapps_agents.cli planner list-stories --status draft

# Show help
python -m tapps_agents.cli planner help
```

**Note:** Commands can also be used programmatically:

```python
from tapps_agents.agents.planner import PlannerAgent

planner = PlannerAgent()
await planner.activate()

# Create a plan
result = await planner.run("plan", description="Add user authentication")

# Create a story
result = await planner.run("create-story", description="User login", epic="auth", priority="high")

# List stories
result = await planner.run("list-stories", epic="checkout")
```

#### Story Generation Features

The Planner Agent automatically generates:

### Implementer Agent (Available Now)

The Implementer Agent generates production code from specifications and writes it to files with automatic code review. It includes safety features like file backups, path validation, and integration with the Reviewer Agent for quality assurance.

#### Commands

```bash
# Generate and write code to file (with review)
python -m tapps_agents.cli implementer implement "Create a function to calculate factorial" factorial.py

# Generate code with context
python -m tapps_agents.cli implementer implement "Add user authentication endpoint" api/auth.py --context "Use FastAPI patterns"

# Generate code only (no file write)
python -m tapps_agents.cli implementer generate-code "Create a REST API client class"

# Generate code for specific file with language
python -m tapps_agents.cli implementer generate-code "Add data validation" --file utils/validation.py --language python

# Refactor existing code file
python -m tapps_agents.cli implementer refactor utils/helpers.py "Extract common logic into helper functions"

# Show help
python -m tapps_agents.cli implementer help
```

**Note:** Commands can also be used programmatically:

```python
from tapps_agents.agents.implementer import ImplementerAgent

implementer = ImplementerAgent()
await implementer.activate()

# Implement code
result = await implementer.run("implement", specification="Create a user service", file_path="services/user.py")

# Generate code only
result = await implementer.run("generate-code", specification="Create a utility function")

# Refactor code
result = await implementer.run("refactor", file_path="models.py", instruction="Add type hints")
```

#### Features

The Implementer Agent includes:

1. **Code Generation**: Generate code from natural language specifications
2. **Code Refactoring**: Refactor existing code based on instructions
3. **Automatic Code Review**: All generated code is reviewed using ReviewerAgent before writing
4. **File Safety**: Automatic backups, path validation, and file size limits
5. **Language Detection**: Automatically detects programming language from file extension
6. **Context Support**: Include existing code patterns or requirements via context

#### Safety Features

- ✅ **Code Review**: All generated code is automatically reviewed; code below quality threshold is rejected
- ✅ **File Backups**: Automatic backups created before overwriting existing files (format: `filename.backup_TIMESTAMP.ext`)
- ✅ **Path Validation**: Prevents path traversal attacks and unsafe file operations
- ✅ **File Size Limits**: Prevents processing files that exceed configured limits (default: 10MB)
- ✅ **Automatic Rollback**: Restores backup if file write fails

#### Configuration

Configure the Implementer Agent in `.tapps-agents/config.yaml`:

```yaml
agents:
  implementer:
    model: "qwen2.5-coder:7b"      # LLM model for code generation
    require_review: true            # Require code review before writing files
    auto_approve_threshold: 80.0    # Auto-approve if score >= threshold (0-100)
    backup_files: true              # Create backup before overwriting existing files
    max_file_size: 10485760         # Maximum file size in bytes (10MB)
```

### Tester Agent (Available Now)

The Tester Agent generates unit and integration tests from code analysis and runs test suites with coverage reporting. It uses LLM-powered code analysis to identify test cases and generate comprehensive test suites.

#### Commands

```bash
# Generate and run tests for a file
python -m tapps_agents.cli tester test calculator.py

# Generate integration tests
python -m tapps_agents.cli tester test api.py --integration

# Generate tests only (don't run)
python -m tapps_agents.cli tester generate-tests utils.py

# Generate tests with custom test file path
python -m tapps_agents.cli tester generate-tests calculator.py --test-file tests/test_calculator.py

# Run all tests in tests/ directory
python -m tapps_agents.cli tester run-tests

# Run specific test file
python -m tapps_agents.cli tester run-tests tests/test_calculator.py

# Run tests without coverage report
python -m tapps_agents.cli tester run-tests --no-coverage

# Show help
python -m tapps_agents.cli tester help
```

**Note:** Commands can also be used programmatically:

```python
from tapps_agents.agents.tester import TesterAgent

tester = TesterAgent()
await tester.activate()

# Generate and run tests
result = await tester.run("test", file="calculator.py")

# Generate tests only
result = await tester.run("generate-tests", file="utils.py", integration=True)

# Run tests
result = await tester.run("run-tests", test_path="tests/", coverage=True)
```

#### Features

The Tester Agent includes:

1. **Test Generation**: Generate unit and integration tests from code analysis
2. **Code Analysis**: Analyze code structure to identify functions, classes, and test targets
3. **Test Framework Support**: Supports pytest (default) and unittest
4. **Test Execution**: Run pytest test suites with coverage reporting
5. **Coverage Tracking**: Track and report test coverage percentage
6. **Automatic Test File Naming**: Automatically generates appropriate test file paths

#### Test Generation Process

1. **Code Analysis**: Analyzes source code to extract:
   - Functions and methods
   - Classes and their methods
   - Imports and dependencies
   - Test framework detection

2. **Test Generation**: Uses LLM to generate tests based on:
   - Code structure analysis
   - Function signatures and arguments
   - Class methods
   - Project test patterns

3. **Test Writing**: Automatically writes generated tests to appropriate test files

4. **Test Execution**: Runs pytest with coverage reporting

#### Configuration

Configure the Tester Agent in `.tapps-agents/config.yaml`:

```yaml
agents:
  tester:
    model: "qwen2.5-coder:7b"      # LLM model for test generation
    test_framework: "pytest"         # Test framework to use (pytest/unittest)
    tests_dir: null                  # Directory for tests (default: tests/)
    coverage_threshold: 80.0         # Target test coverage percentage (0-100)
    auto_write_tests: true           # Automatically write generated tests to files
```

#### Example Workflow

1. **Generate Tests**:
   ```bash
   python -m tapps_agents.cli tester test calculator.py
   ```

2. **Generate Integration Tests**:
   ```bash
   python -m tapps_agents.cli tester test api.py --integration
   ```

3. **Run Test Suite**:
   ```bash
   python -m tapps_agents.cli tester run-tests
   ```

#### Example Workflow (Implementer Agent)

1. **Generate Code**:
   ```bash
   python -m tapps_agents.cli implementer implement "Create a user service class with CRUD operations" services/user_service.py
   ```

2. **Code Review** (automatic):
   - Code is generated using LLM
   - ReviewerAgent reviews the generated code
   - If score >= threshold (default: 80.0), code is written to file
   - If score < threshold, operation fails with review feedback

3. **Backup** (if file exists):
   - Original file is backed up to `user_service.backup_20250105_143022.py`
   - New code is written to `services/user_service.py`

4. **Result**:
   - File written with new code
   - Backup created (if applicable)
   - Review results included in response

#### Best Practices

1. **Provide Clear Specifications**: Be specific about what code to generate
2. **Include Context**: Use `--context` to provide existing code patterns or requirements
3. **Specify Language**: Use `--language` for non-Python code
4. **Review Before Commit**: Even with auto-approve, manually review generated code
5. **Use Refactor for Improvements**: Don't rewrite entire files, use refactor for targeted improvements
6. **Test Generated Code**: Always test generated code before committing

1. **Story Metadata**:
   - Unique story ID (auto-generated slug)
   - Title (extracted from description)
   - Domain inference (backend/frontend/testing/documentation/general)
   - Complexity estimate (1-5 scale via LLM)
   - Epic, priority, status

2. **Acceptance Criteria** (LLM-generated):
   - 3-5 testable criteria
   - Formatted as checkboxes

3. **Task Breakdown** (LLM-generated):
   - 3-7 actionable tasks
   - Numbered list format

4. **Story File**: Markdown with YAML frontmatter saved to `stories/` directory

#### Example Story File

Generated stories are saved as `stories/{story-id}.md`:

```markdown
# User Login with Google

```yaml
story_id: authentication-user-login-with-google
title: User Login with Google
description: |
  User should be able to log in with Google OAuth2
epic: authentication
domain: backend
priority: medium
complexity: 3
status: draft
created_at: 2025-12-04T10:30:00
created_by: planner
```

## Description

User should be able to log in with Google OAuth2

## Acceptance Criteria

- [ ] User can initiate Google OAuth login
- [ ] OAuth callback handles authentication
- [ ] User session is created after successful login
- [ ] Error handling for failed authentication

## Tasks

1. Set up Google OAuth2 credentials
2. Implement OAuth callback endpoint
3. Create user session management
4. Add error handling and logging
5. Write integration tests

## Technical Notes

(Technical considerations, dependencies, etc.)

## Dependencies

- Related stories: []
- Blocks: []
- Blocked by: []
```

#### Configuration

Configure the Planner Agent in `.tapps-agents/config.yaml`:

```yaml
agents:
  planner:
    model: "qwen2.5-coder:7b"      # LLM model for planning
    stories_dir: "stories"           # Directory for story files (default: stories/)
    default_priority: "medium"       # Default priority for new stories
```

#### Story Metadata

Each story includes:

- **story_id**: Auto-generated slug (e.g., `authentication-user-login`)
- **title**: Short title extracted from description
- **epic**: Feature area or epic name
- **domain**: Inferred domain (backend/frontend/testing/documentation/general)
- **priority**: high/medium/low
- **complexity**: 1-5 scale estimate (via LLM)
  - 1: Trivial (<1 hour)
  - 2: Easy (1-4 hours)
  - 3: Medium (1-2 days)
  - 4: Complex (3-5 days)
  - 5: Very Complex (1+ weeks)
- **status**: draft/ready/in-progress/done
- **created_at**: ISO timestamp
- **created_by**: "planner"

#### Domain Inference

The Planner Agent automatically infers the domain from keywords:

- **backend**: Contains "api", "endpoint", "service"
- **frontend**: Contains "ui", "interface", "component", "page"
- **testing**: Contains "test", "testing", "spec"
- **documentation**: Contains "documentation", "docs", "guide"
- **general**: Default fallback

#### Story Listing and Filtering

List stories with optional filters:

```bash
# List all stories
*list-stories

# Filter by epic
*list-stories --epic=authentication

# Filter by status
*list-stories --status=draft

# Combined filters (future)
*list-stories --epic=checkout --status=ready
```

#### Integration with Project Workflow

1. **Create Stories**: Use `*create-story` for each user story
2. **Organize by Epic**: Use `--epic` parameter to group related stories
3. **Track Progress**: Update `status` field in story files as work progresses
4. **Review**: Stories are stored in `stories/` directory for easy review

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

### Agent Expert Integration

Six workflow agents have integrated expert consultation to enhance their decision-making:

#### Architect Agent
- **Experts Used**: Security, Performance, UX, Software Architecture
- **Integration Points**:
  - System design (`_design_system`) - Software Architecture expert
  - Technology selection (`_select_technology`) - Software Architecture & Performance experts
  - Security architecture (`_design_security`) - Security expert
  - Boundary definition (`_define_boundaries`) - Software Architecture expert

#### Implementer Agent
- **Experts Used**: Security, Performance
- **Integration Points**:
  - Code generation (`implement`, `generate_code`) - Security & Performance experts
  - Code refactoring (`refactor_code`) - Security & Performance experts

#### Reviewer Agent
- **Experts Used**: Security, Performance, Testing, Accessibility, Code Quality
- **Integration Points**:
  - Code review (`review_file`) - Security, Performance, and Code Quality experts
  - Expert findings included in LLM feedback generation

#### Tester Agent
- **Experts Used**: Testing
- **Integration Points**:
  - Test generation (`test_command`, `generate_tests_command`) - Testing expert
  - Expert guidance included in test generation prompts for better test coverage and patterns

#### Designer Agent
- **Experts Used**: Accessibility, UX, Data Privacy
- **Integration Points**:
  - UI/UX design (`_design_ui`) - UX & Accessibility experts
  - Design system definition (`_define_design_system`) - UX & Accessibility experts
  - API design (`_design_api`) - Data Privacy expert
  - Data model design (`_design_data_model`) - Data Privacy expert

#### Ops Agent
- **Experts Used**: Security, Data Privacy
- **Integration Points**:
  - Security scanning (`_handle_security_scan`) - Security expert
  - Compliance checking (`_handle_compliance_check`) - Security & Data Privacy experts
  - Deployment (`_handle_deploy`) - Security expert
  - Infrastructure setup (`_handle_infrastructure_setup`) - Security expert

### Project Profiling System (v1.0.0+)

The framework automatically detects your project characteristics to provide context-aware expert advice. This system analyzes your codebase to determine:

- **Deployment Type**: local, cloud, or enterprise
- **Tenancy Model**: single-tenant or multi-tenant
- **User Scale**: single-user, small-team, department, or enterprise
- **Compliance Requirements**: GDPR, HIPAA, PCI, SOC2, ISO27001
- **Security Level**: basic, standard, high, or critical

**How It Works:**

1. **Automatic Detection**: When experts are consulted, the framework automatically detects project characteristics
2. **Profile Storage**: Detected profile is saved to `.tapps-agents/project_profile.yaml`
3. **Context-Aware Prompts**: Experts receive project context in their consultation prompts (high-confidence values only, ≥0.7)
4. **Confidence Boost**: Project context relevance contributes 10% to overall confidence calculation

**Example:**

```python
# Profile is automatically detected and used
from tapps_agents.experts.expert_registry import ExpertRegistry

registry = ExpertRegistry(load_builtin=True)
result = await registry.consult(
    query="How should I secure my API?",
    domain="security"
)

# Expert receives context like:
# "Project Context:
#  - Deployment: cloud (confidence: 90%)
#  - Compliance Requirements: GDPR
#  - Security Level: high (confidence: 80%)"
```

**Manual Profile Management:**

```python
from tapps_agents.core.project_profile import (
    ProjectProfileDetector, 
    save_project_profile,
    load_project_profile,
    match_template
)

# Detect profile
detector = ProjectProfileDetector()
profile = detector.detect()
save_project_profile(profile)

# Load profile
profile = load_project_profile()

# Match to template
template = match_template(profile)
# Returns: "local-development", "saas-application", "enterprise-internal", or "startup-mvp"
```

**Profile Templates:**

- **local-development**: local, single-tenant, small-team, basic security
- **saas-application**: cloud, multi-tenant, enterprise, high security
- **enterprise-internal**: enterprise, single-tenant, department, high security
- **startup-mvp**: cloud, single-tenant, small-team, standard security

See [Project Profiling Guide](PROJECT_PROFILING_GUIDE.md) for complete details.

### Expert Confidence System (v2.1.0)

Expert consultations now use an improved confidence calculation system:

**Confidence Algorithm:**
```python
confidence = (
    max_confidence * 0.4 +      # Maximum expert confidence
    agreement_level * 0.3 +      # Expert agreement
    rag_quality * 0.2 +          # Knowledge base match quality
    domain_relevance * 0.1       # Domain relevance score
)
```

**Agent-Specific Thresholds:**
Each agent has a configurable confidence threshold:
- **Reviewer**: 0.8 (High - critical code reviews)
- **Architect**: 0.75 (High - architecture decisions)
- **Implementer**: 0.7 (Medium-High - code generation)
- **Designer**: 0.65 (Medium - design decisions)
- **Tester**: 0.7 (Medium-High - test generation)
- **Ops**: 0.75 (High - operations)

Configure in `.tapps-agents/config.yaml`:
```yaml
agents:
  reviewer:
    min_confidence_threshold: 0.8
```

**Confidence Metrics Tracking:**
All consultations are automatically tracked:
```python
from tapps_agents.experts.confidence_metrics import get_tracker

tracker = get_tracker()
stats = tracker.get_statistics(agent_id="reviewer", domain="security")
```

### How Agents Use Experts

Agents automatically consult experts during their workflows. The consultation process:

1. **Query Construction**: Agent builds a domain-specific query
2. **Expert Consultation**: Registry routes to relevant experts
3. **Confidence Calculation**: Weighted algorithm calculates overall confidence
4. **Threshold Check**: Compares confidence to agent-specific threshold
5. **Guidance Integration**: If confidence meets threshold, expert guidance is included in LLM prompts

**Example Flow (Tester Agent):**
```python
# Agent generates test
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
mkdir -p your-project/.claude/skills
# Copy Skills from source location
cp -r TappsCodingAgents/tapps_agents/agents/*/SKILL.md your-project/.claude/skills/
# Or if Skills are in .claude/skills/:
cp -r TappsCodingAgents/.claude/skills/* your-project/.claude/skills/
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

