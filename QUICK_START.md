# TappsCodingAgents - Quick Start Guide

**Get up and running in 10 minutes**

---

## What is TappsCodingAgents?

TappsCodingAgents is a framework for building AI coding agents with specialized workflow agents and domain experts. It provides:

- **13 Workflow Agents** - Specialized agents for SDLC tasks (analyst, planner, architect, implementer, tester, reviewer, enhancer, etc.)
- **Industry Experts** - Domain-specific knowledge experts you configure per project
- **Model Abstraction Layer** - Automatic routing between local (Ollama) and cloud (Anthropic/OpenAI) models
- **Code Scoring System** - Objective quality metrics (complexity, security, maintainability, test coverage, performance)
- **Workflow Engine** - YAML-based workflow definitions for complex multi-step tasks
- **MCP Gateway** - Unified tool access for filesystem, Git, and analysis operations
- **Cursor AI Integration** ✅ - Complete integration with Cursor AI (all 7 phases complete)
  - **13 Cursor Skills** - All agents available as Cursor Skills
  - **Background Agents** - Offload heavy tasks to cloud/remote agents
  - **Multi-Agent Orchestration** - Parallel execution with conflict resolution
  - **Context7 Integration** - KB-first caching with 95%+ hit rate
  - **NUC Optimization** - Resource monitoring and fallback strategy

---

## Prerequisites

- **Python 3.12+** installed
- **Ollama** installed and running ([ollama.com](https://ollama.com))
- **8GB+ GPU** recommended (CPU works but slower)
- **Cursor IDE** or **VS Code** (optional, for IDE integration)

---

## Installation (5 minutes)

### Step 1: Install Ollama

```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Pull a Coding Model

```bash
# For 8GB GPU
ollama pull qwen2.5-coder:7b

# For 16GB+ GPU
ollama pull qwen2.5-coder:14b

# Verify installation
ollama list
```

### Step 3: Clone and Install TappsCodingAgents

```bash
# Clone the repository
git clone https://github.com/wtthornton/TappsCodingAgents.git
cd TappsCodingAgents

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Test Ollama connection
ollama run qwen2.5-coder:7b "Write a Python hello world function"

# Test TappsCodingAgents CLI
python -m tapps_agents.cli reviewer help
```

**✅ You're ready!** Continue to the next section to start using agents.

---

## Quick Examples

### Example 1: Review Code

```bash
# Review a Python file with scoring and feedback
python -m tapps_agents.cli reviewer review path/to/file.py

# Score only (faster, no LLM feedback)
python -m tapps_agents.cli reviewer score path/to/file.py

# Lint a file with Ruff (Phase 6 - fast, 10-100x faster than legacy tools)
python -m tapps_agents.cli reviewer lint path/to/file.py

# Type check a file with mypy (Phase 6)
python -m tapps_agents.cli reviewer type-check path/to/file.py

# Generate comprehensive quality reports (Phase 6)
python -m tapps_agents.cli reviewer report path/to/directory json markdown html
```

**Output:**
```json
{
  "file": "example.py",
  "scoring": {
    "complexity_score": 3.2,
    "security_score": 9.5,
    "maintainability_score": 8.1,
    "test_coverage_score": 7.0,
    "performance_score": 8.5,
    "overall_score": 78.5
  },
  "feedback": {
    "summary": "Code quality is good overall...",
    "full_feedback": "..."
  },
  "passed": true,
  "threshold": 70.0
}
```

### Example 2: Generate Code

```bash
# Generate and write code to file (with automatic review)
python -m tapps_agents.cli implementer implement \
  "Create a function to calculate factorial" \
  factorial.py

# Generate code only (no file write)
python -m tapps_agents.cli implementer generate-code \
  "Create a REST API client class"
```

### Example 3: Create User Stories

```bash
# Create a user story
python -m tapps_agents.cli planner create-story \
  "User should be able to log in with Google" \
  --epic authentication \
  --priority high

# List all stories
python -m tapps_agents.cli planner list-stories

# Filter by epic
python -m tapps_agents.cli planner list-stories --epic authentication
```

### Example 4: Generate Tests

```bash
# Generate and run tests for a file
python -m tapps_agents.cli tester test calculator.py

# Generate integration tests
python -m tapps_agents.cli tester test api.py --integration

# Run existing tests
python -m tapps_agents.cli tester run-tests
```

### Example 5: Debug Errors

```bash
# Debug an error with stack trace
python -m tapps_agents.cli debugger debug \
  "ValueError: invalid literal for int()" \
  --file calculator.py \
  --line 42 \
  --stack-trace "Traceback..."

# Analyze error message
python -m tapps_agents.cli debugger analyze-error \
  "KeyError: 'user_id'" \
  --code-context "def get_user(id): return users[id]"
```

### Example 6: Enhance Prompts

```bash
# Full enhancement pipeline (all stages)
python -m tapps_agents.cli enhancer enhance \
  "Create a login system" \
  --output enhanced-prompt.md

# Quick enhancement (stages 1-3 only)
python -m tapps_agents.cli enhancer enhance-quick \
  "Add user authentication"

# Run specific stage
python -m tapps_agents.cli enhancer enhance-stage analysis \
  "Create payment processing system"
```

**Output:** Enhanced prompt with requirements, architecture guidance, expert domain context, quality standards, and implementation strategy.

---

## Project Setup (Optional but Recommended)

For production use, set up a project configuration:

### Step 1: Create Project Structure

```bash
mkdir -p .tapps-agents
cd .tapps-agents
```

### Step 2: Create Configuration File

Create `.tapps-agents/config.yaml`:

```yaml
# Project metadata
project_name: "MyProject"
version: "1.0.0"

# Agent configurations
agents:
  reviewer:
    model: "qwen2.5-coder:7b"
    quality_threshold: 70.0
    include_scoring: true
    include_llm_feedback: true
  
  implementer:
    model: "qwen2.5-coder:7b"
    require_review: true
    auto_approve_threshold: 80.0
    backup_files: true

# Code scoring weights (must sum to 1.0)
scoring:
  weights:
    complexity: 0.20
    security: 0.30
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.10
  quality_threshold: 70.0

# Model Abstraction Layer
mal:
  ollama_url: "http://localhost:11434"
  default_model: "qwen2.5-coder:7b"
  timeout: 60.0
```

### Step 3: Define Domains (Optional)

Create `.tapps-agents/domains.md`:

```markdown
# Project Domains

## Domain 1: Product Catalog
- Product data management
- Categories and taxonomies
- Search and filtering
- **Primary Expert:** expert-catalog

## Domain 2: Checkout & Payments
- Shopping cart management
- Payment gateway integration
- Order processing
- **Primary Expert:** expert-checkout
```

See `examples/experts/` for complete examples.

---

## Available Agents

| Agent | Purpose | Key Commands |
|-------|---------|--------------|
| **analyst** | Requirements gathering, estimation | `gather-requirements`, `estimate-effort` |
| **planner** | Story creation, task breakdown | `create-story`, `list-stories`, `plan` |
| **architect** | System design, tech decisions | `design-system`, `select-technology` |
| **designer** | API/data model design | `design-api`, `design-data-model` |
| **implementer** | Code generation | `implement`, `generate-code`, `refactor` |
| **tester** | Test generation | `test`, `generate-tests`, `run-tests` |
| **debugger** | Error analysis | `debug`, `analyze-error`, `trace` |
| **documenter** | Documentation generation | `document`, `update-readme` |
| **reviewer** | Code review & quality analysis | `review`, `score`, `lint`, `type-check`, `report` |
| **improver** | Code refactoring | `refactor`, `optimize`, `improve-quality` |
| **ops** | Security, deployment, dependencies | `security-scan`, `compliance-check`, `deploy`, `audit-dependencies` |
| **orchestrator** | Workflow coordination | `workflow-start`, `workflow-status`, `gate` |
| **enhancer** | Prompt enhancement | `enhance`, `enhance-quick`, `enhance-stage` |

**Get help for any agent:**
```bash
python -m tapps_agents.cli <agent-name> help
```

---

## Common Workflows

### Starting a New Feature

```bash
# 1. Gather requirements
python -m tapps_agents.cli analyst gather-requirements \
  "Add user authentication with OAuth2"

# 2. Create stories
python -m tapps_agents.cli planner create-story \
  "User login with Google" --epic auth --priority high

# 3. Design system
python -m tapps_agents.cli architect design-system \
  "OAuth2 authentication flow"

# 4. Implement
python -m tapps_agents.cli implementer implement \
  "Create OAuth2 authentication service" \
  services/auth.py

# 5. Test
python -m tapps_agents.cli tester test services/auth.py

# 6. Review
python -m tapps_agents.cli reviewer review services/auth.py
```

### Debugging an Issue

```bash
# 1. Analyze error
python -m tapps_agents.cli debugger analyze-error \
  "KeyError: 'user_id'" \
  --file services/user.py \
  --line 42

# 2. Trace code execution
python -m tapps_agents.cli debugger trace \
  services/user.py \
  --function get_user

# 3. Fix and review
python -m tapps_agents.cli implementer refactor \
  services/user.py \
  "Add null check for user_id"
```

### Code Review Workflow

```bash
# 1. Score code (fast)
python -m tapps_agents.cli reviewer score path/to/file.py

# 2. Full review (with LLM feedback)
python -m tapps_agents.cli reviewer review path/to/file.py

# 3. Fix issues if needed
python -m tapps_agents.cli improver improve-quality path/to/file.py
```

---

## IDE Integration

### Cursor IDE

1. **Copy agent skills** to your project:
   ```bash
   # Copy Skills from TappsCodingAgents source
   mkdir -p your-project/.claude/skills
   cp -r TappsCodingAgents/tapps_agents/agents/*/SKILL.md your-project/.claude/skills/
   
   # Or if Skills are already in .claude/skills/ in TappsCodingAgents:
   cp -r TappsCodingAgents/.claude/skills/* your-project/.claude/skills/
   ```

2. **Use agents in chat:**
   ```
   @implementer Create a user service class with CRUD operations
   @reviewer Review this code for security issues
   @architect Design a caching strategy for our product catalog
   ```

### VS Code

Use the CLI commands directly in the terminal, or configure Continue extension for local models.

---

## Configuration Options

### Model Selection

Choose models based on your GPU:

```yaml
agents:
  reviewer:
    model: "qwen2.5-coder:7b"      # 8GB GPU
    # model: "qwen2.5-coder:14b"    # 16GB+ GPU
    # model: "deepseek-coder:6.7b" # Alternative
```

### Cloud Fallback

Enable cloud fallback for when Ollama is unavailable:

```yaml
mal:
  ollama_url: "http://localhost:11434"
  default_model: "qwen2.5-coder:7b"
  fallback:
    provider: "anthropic"  # or "openai"
    model: "claude-3.5-haiku"
    api_key: "${ANTHROPIC_API_KEY}"  # Set in environment
```

### Scoring Weights

Customize code scoring weights:

```yaml
scoring:
  weights:
    complexity: 0.15        # Lower weight for complexity
    security: 0.40          # Higher weight for security
    maintainability: 0.25
    test_coverage: 0.15
    performance: 0.05
  quality_threshold: 80.0   # Stricter threshold
```

**Important:** Weights must sum to 1.0.

---

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
ollama list

# Start Ollama
# Windows: Check system tray
# macOS: brew services start ollama
# Linux: systemctl start ollama
```

### Model Too Slow

```bash
# Check GPU usage
ollama ps

# Use a smaller model
ollama pull qwen2.5-coder:7b  # Instead of 14b
```

### Out of VRAM

```bash
# Use a smaller model
ollama pull deepseek-coder-v2:lite  # Only 1.6GB

# Or enable cloud fallback in config.yaml
```

### Configuration Errors

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.tapps-agents/config.yaml'))"

# Check weights sum to 1.0
python -c "
import yaml
config = yaml.safe_load(open('.tapps-agents/config.yaml'))
weights = config['scoring']['weights']
total = sum(weights.values())
print(f'Weights sum: {total} (should be 1.0)')
"
```

---

## Next Steps

1. **Cursor AI Integration** ✅: See `docs/CURSOR_AI_INTEGRATION_PLAN_2025.md` - All 7 phases complete!
   - Install Cursor Skills: `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`
   - Configure Background Agents: `docs/BACKGROUND_AGENTS_GUIDE.md`
   - Multi-Agent Orchestration: `docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md`
2. **Read the Developer Guide**: `docs/DEVELOPER_GUIDE.md` - Comprehensive usage guide
3. **Explore Examples**: `examples/experts/` - Example expert configurations
4. **Review Requirements**: `requirements/PROJECT_REQUIREMENTS.md` - Complete specification
5. **Set Up Industry Experts**: `docs/EXPERT_CONFIG_GUIDE.md` - Configure domain experts
6. **Learn Workflows**: `docs/WORKFLOW_SELECTION_GUIDE.md` - YAML workflow definitions
7. **Quality Tools**: `docs/QUALITY_TOOLS_USAGE_EXAMPLES.md` - Ruff, mypy, Bandit, jscpd, pip-audit

---

## Quick Reference

### CLI Commands

```bash
# Reviewer
python -m tapps_agents.cli reviewer review <file>
python -m tapps_agents.cli reviewer score <file>
python -m tapps_agents.cli reviewer lint <file>  # Phase 6: Ruff linting (fast!)

# Planner
python -m tapps_agents.cli planner create-story <description> [--epic <epic>] [--priority <priority>]
python -m tapps_agents.cli planner list-stories [--epic <epic>] [--status <status>]

# Implementer
python -m tapps_agents.cli implementer implement <spec> <file> [--context <context>]
python -m tapps_agents.cli implementer generate-code <spec> [--file <file>]
python -m tapps_agents.cli implementer refactor <file> <instruction>

# Tester
python -m tapps_agents.cli tester test <file> [--integration]
python -m tapps_agents.cli tester run-tests [<test_path>]

# Debugger
python -m tapps_agents.cli debugger debug <error> [--file <file>] [--line <line>]
python -m tapps_agents.cli debugger analyze-error <error> [--stack-trace <trace>]

# Get help for any agent
python -m tapps_agents.cli <agent-name> help
```

### Key Files

| File | Purpose |
|------|---------|
| `.tapps-agents/config.yaml` | Project configuration |
| `.tapps-agents/domains.md` | Business domain definitions |
| `knowledge/{domain}/` | RAG knowledge base |
| `workflows/*.yaml` | Workflow definitions |

---

## Support

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Issues**: Open a GitHub issue
- **Requirements**: See `requirements/PROJECT_REQUIREMENTS.md`

---

**Happy coding! 🚀**

