# TappsCodingAgents Project Context

## Understanding This Project's Dual Nature

TappsCodingAgents has a unique characteristic: **it both develops the framework AND uses it for its own development** (self-hosting). This document clarifies the distinction to avoid confusion.

## Two Roles

### 1. Framework Development (Primary)

**What it is:** TappsCodingAgents is a framework/library that other projects can use.

**What we do:**
- Develop the framework code in `tapps_agents/` package
- Write tests in `tests/` directory
- Create documentation in `docs/` directory
- Define specifications in `requirements/` directory
- Add new agents, features, and capabilities

**Key Files:**
- `tapps_agents/` - Framework source code
- `tests/` - Test suite
- `docs/` - User-facing documentation
- `requirements/` - Framework specifications
- `setup.py` - Package configuration

**When working on framework development:**
- You're modifying the framework itself
- You're adding features that users will use
- You're fixing bugs or improving capabilities
- Focus on code quality, architecture, and user experience

### 2. Self-Hosting (Secondary)

**What it is:** TappsCodingAgents uses its own framework for its own development.

**What we do:**
- Configure Industry Experts in `.tapps-agents/experts.yaml`
- Define domains in `.tapps-agents/domains.md`
- Use Enhancer Agent for prompt enhancement
- Use Reviewer Agent for code quality checks
- Use Context7 for library documentation

**Key Files:**
- `.tapps-agents/` - Project configuration (using the framework)
- `workflows/` - Workflow definitions
- `.tapps-agents/sessions/` - Enhancement session history

**When working on self-hosted development:**
- You're using the framework as a tool
- You're configuring it for this specific project
- You're leveraging agents to help develop the framework
- Focus on project-specific tasks and improvements

## Why This Matters

### For Framework Users

When you install TappsCodingAgents in your project:
- You get the framework code (`tapps_agents` package)
- You configure it for YOUR project (`.tapps-agents/` in YOUR project)
- You use agents via CLI or Python API
- You define YOUR experts and domains

**Example:**
```bash
# In your project
cd my-project/
python -m tapps_agents.cli reviewer review src/main.py
```

### For Framework Developers

When working on TappsCodingAgents itself:
- You modify the framework code (`tapps_agents/`)
- You also use the framework (`.tapps-agents/` in THIS project)
- You test new features by using them
- You dogfood your own framework

**Example:**
```bash
# In TappsCodingAgents project
cd TappsCodingAgents/
# Modify framework code
vim tapps_agents/agents/reviewer/agent.py
# Test it by using it
python -m tapps_agents.cli reviewer review tapps_agents/agents/reviewer/agent.py
```

## Current Self-Hosting Configuration

**Version**: 1.6.1

### Industry Experts (5)

Configured in `.tapps-agents/experts.yaml`:

1. **expert-ai-frameworks**
   - Domain: AI agent orchestration, workflow management
   - Used for: Framework architecture decisions

2. **expert-code-quality**
   - Domain: Static analysis, code scoring, quality metrics
   - Used for: Code quality improvements

3. **expert-software-architecture**
   - Domain: System design patterns, architecture decisions
   - Used for: Framework design decisions

4. **expert-devops**
   - Domain: CI/CD integration, testing strategies
   - Used for: Development workflow improvements

5. **expert-documentation**
   - Domain: Technical documentation, knowledge bases
   - Used for: Documentation generation and management

### Active Usage

- **Enhancer Agent**: 23+ enhancement sessions in `.tapps-agents/sessions/`
- **Context7**: KB cache in `.tapps-agents/kb/context7-cache/`
- **Workflows**: `workflows/prompt-enhancement.yaml` for prompt enhancement

## Documentation Structure

### User-Facing Documentation
These documents explain how to **use** the framework:
- `QUICK_START.md` - Getting started guide
- `docs/DEVELOPER_GUIDE.md` - How to use in your projects
- `docs/CONFIGURATION.md` - Configuration reference
- `docs/API.md` - API documentation

### Developer Documentation
These documents explain how to **develop** the framework:
- `docs/ARCHITECTURE.md` - Framework architecture
- `requirements/PROJECT_REQUIREMENTS.md` - Specifications
- `CONTRIBUTING.md` - Contribution guidelines
- `implementation/` - Development notes

### Self-Hosting Documentation
These documents explain how we **use** the framework:
- `implementation/SELF_HOSTING_SETUP_COMPLETE.md` - Self-hosting setup
- `.cursor/rules/project-context.mdc` - AI assistant context
- This document

## Examples

### Example 1: User Perspective

**Question:** "How do I review code with TappsCodingAgents?"

**Answer:** (User-facing)
```bash
# Install the framework
pip install tapps-agents

# In your project, review code
python -m tapps_agents.cli reviewer review src/main.py
```

### Example 2: Developer Perspective

**Question:** "How do I add a new agent to the framework?"

**Answer:** (Developer-facing)
```python
# In tapps_agents/agents/myagent/agent.py
from tapps_agents.core.agent_base import BaseAgent

class MyAgent(BaseAgent):
    async def activate(self):
        # Agent setup
        pass
    
    def get_commands(self):
        return [{"*mycommand": "Description"}]
    
    async def run(self, command, **kwargs):
        # Command execution
        pass
```

### Example 3: Self-Hosting Perspective

**Question:** "What experts are configured in this project?"

**Answer:** (Self-hosting)
```yaml
# .tapps-agents/experts.yaml
experts:
  - expert_id: expert-ai-frameworks
    expert_name: AI Agent Framework Expert
    primary_domain: ai-agent-framework
  # ... 4 more experts
```

## File Organization

```
TappsCodingAgents/
├── tapps_agents/              # Framework code (developing)
│   ├── agents/                # Agent implementations
│   ├── core/                  # Core framework
│   └── ...
│
├── .tapps-agents/             # Self-hosting config (using)
│   ├── experts.yaml           # Our experts
│   ├── domains.md             # Our domains
│   └── sessions/              # Enhancement sessions
│
├── docs/                      # User documentation (using)
├── requirements/              # Specifications (developing)
└── implementation/            # Dev notes (developing)
```

## Guidelines

### For AI Assistants

When working in this project, AI assistants should:

1. **Understand context:**
   - Framework code = developing
   - Project config = using

2. **Clarify intent:**
   - Ask: "Are you using the framework or developing it?"
   - Provide examples for both when relevant

3. **Reference appropriate docs:**
   - User questions → `QUICK_START.md`, `DEVELOPER_GUIDE.md`
   - Developer questions → `ARCHITECTURE.md`, `PROJECT_REQUIREMENTS.md`
   - Self-hosting questions → This document, `.tapps-agents/`

### For Contributors

1. **Framework changes:**
   - Modify `tapps_agents/` code
   - Update tests in `tests/`
   - Update user docs in `docs/`

2. **Self-hosting changes:**
   - Modify `.tapps-agents/` config
   - Update workflows in `workflows/`
   - Document in `implementation/`

3. **Documentation:**
   - User docs = how to use
   - Developer docs = how to develop
   - Self-hosting docs = how we use it

## References

- **Self-Hosting Setup**: `implementation/SELF_HOSTING_SETUP_COMPLETE.md`
- **Cursor Rules**: `.cursor/rules/project-context.mdc`
- **User Guide**: `QUICK_START.md`
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

**Last Updated**: December 2025  
**Version**: 1.6.1

