# TappsCodingAgents - Complete Setup Guide

**Your project is already initialized!** This guide will help you verify everything is working and get started.

---

## ✅ Current Status

Your TappsCodingAgents project is **already set up** with:

- ✅ **Package Installed**: v1.6.1
- ✅ **5 Industry Experts** configured
- ✅ **5 Workflow Presets** available
- ✅ **Project Structure** initialized
- ✅ **CLI Commands** working

---

## 🚀 Quick Start (5 minutes)

### Step 1: Verify Installation

```bash
# Check package version
python -c "import tapps_agents; print(tapps_agents.__version__)"

# Test CLI
python -m tapps_agents.cli --help

# List available workflows
python -m tapps_agents.cli workflow list

# List configured experts
python -m tapps_agents.cli setup-experts list
```

### Step 2: Install Ollama (Required for Local Models)

TappsCodingAgents uses **Ollama** to run local AI models. Install it:

**Windows:**
```powershell
winget install Ollama.Ollama
```

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 3: Pull a Coding Model

After installing Ollama, pull a coding model:

```bash
# For 8GB GPU (recommended minimum)
ollama pull qwen2.5-coder:7b

# For 16GB+ GPU (better quality)
ollama pull qwen2.5-coder:14b

# Verify installation
ollama list
```

### Step 4: Test with a Simple Command

```bash
# Score a code file (fast, no LLM needed)
python -m tapps_agents.cli reviewer score example_bug.py

# Or review a file (requires Ollama)
python -m tapps_agents.cli reviewer review example_bug.py
```

---

## 📋 What's Already Configured

### 1. Industry Experts (5 configured)

Your project has 5 experts set up in `.tapps-agents/experts.yaml`:

1. **AI Agent Framework Expert** - Agent orchestration, workflow management
2. **Code Quality & Analysis Expert** - Static analysis, code scoring
3. **Software Architecture Expert** - System design, architecture decisions
4. **Development Workflow Expert** - CI/CD, testing, deployment
5. **Documentation & Knowledge Management Expert** - Documentation generation

**View experts:**
```bash
python -m tapps_agents.cli setup-experts list
```

### 2. Workflow Presets (5 available)

Ready-to-use workflows in `workflows/presets/`:

- **Rapid Development** (`rapid`, `feature`) - Fast feature development
- **Quick Fix** (`hotfix`, `urgent`) - Fast bug fixes
- **Maintenance & Bug Fixing** (`fix`, `refactor`) - Debug and improve code
- **Quality Improvement** (`quality`, `improve`) - Comprehensive code review
- **Full SDLC Pipeline** (`full`, `enterprise`) - Complete development lifecycle

**List workflows:**
```bash
python -m tapps_agents.cli workflow list
```

### 3. Project Structure

```
TappsCodingAgents/
├── .tapps-agents/          # Project configuration
│   ├── experts.yaml        # Expert definitions ✅
│   ├── domains.md          # Domain definitions ✅
│   ├── config.yaml         # (Optional - create if needed)
│   └── knowledge/          # RAG knowledge base
├── workflows/
│   └── presets/            # Workflow presets ✅
└── .cursor/
    └── rules/              # Cursor Rules (optional)
```

---

## 🔧 Optional: Create Project Configuration

You can create a custom configuration file at `.tapps-agents/config.yaml`:

```yaml
# Project metadata
project_name: "TappsCodingAgents"
version: "1.6.1"

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

---

## 🎯 Common Commands

### Code Review

```bash
# Quick score (fast, no LLM)
python -m tapps_agents.cli reviewer score path/to/file.py

# Full review (requires Ollama)
python -m tapps_agents.cli reviewer review path/to/file.py

# Lint with Ruff (Phase 6 - very fast)
python -m tapps_agents.cli reviewer lint path/to/file.py

# Type check with mypy (Phase 6)
python -m tapps_agents.cli reviewer type-check path/to/file.py
```

### Code Generation

```bash
# Generate and write code
python -m tapps_agents.cli implementer implement \
  "Create a function to calculate factorial" \
  factorial.py

# Generate code only (no file write)
python -m tapps_agents.cli implementer generate-code \
  "Create a REST API client class"
```

### Workflows

```bash
# Run rapid development workflow
python -m tapps_agents.cli workflow rapid

# Run full SDLC pipeline
python -m tapps_agents.cli workflow full

# Quick bug fix
python -m tapps_agents.cli workflow hotfix

# Quality improvement cycle
python -m tapps_agents.cli workflow quality
```

### Expert Management

```bash
# List all experts
python -m tapps_agents.cli setup-experts list

# Add a new expert (interactive wizard)
python -m tapps_agents.cli setup-experts add

# Remove an expert
python -m tapps_agents.cli setup-experts remove
```

---

## 🧪 Testing Your Setup

### Test 1: Score a File (No Ollama Required)

```bash
python -m tapps_agents.cli reviewer score example_bug.py
```

**Expected output:** JSON with complexity, security, maintainability scores.

### Test 2: Review a File (Requires Ollama)

```bash
# Make sure Ollama is running
ollama list

# Run review
python -m tapps_agents.cli reviewer review example_bug.py
```

**Expected output:** Full review with scores and LLM feedback.

### Test 3: Run a Workflow

```bash
python -m tapps_agents.cli workflow rapid
```

---

## 🐛 Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
ollama list

# Start Ollama
# Windows: Check system tray or start from Start Menu
# macOS: brew services start ollama
# Linux: systemctl start ollama
```

### Model Not Found

```bash
# Pull the model
ollama pull qwen2.5-coder:7b

# Verify
ollama list
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .
```

### Configuration Errors

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.tapps-agents/experts.yaml'))"
```

---

## 📚 Next Steps

1. **Read the Quick Start Guide**: `QUICK_START.md` - Get started in 10 minutes
2. **Explore Workflows**: `docs/WORKFLOW_SELECTION_GUIDE.md` - Learn about workflow presets
3. **Configure Experts**: `docs/EXPERT_CONFIG_GUIDE.md` - Customize your experts
4. **Cursor AI Integration**: `docs/CURSOR_AI_INTEGRATION_PLAN_2025.md` - All 7 phases complete!
5. **API Reference**: `docs/API.md` - Complete API documentation

---

## 🎉 You're Ready!

Your TappsCodingAgents project is fully initialized and ready to use. Start with:

```bash
# Test scoring (no Ollama needed)
python -m tapps_agents.cli reviewer score example_bug.py

# Or run a workflow
python -m tapps_agents.cli workflow rapid
```

**Happy coding! 🚀**

