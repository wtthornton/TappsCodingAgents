---
# Agent Role File Template
#
# This template defines the standard format for agent role definition files.
# Role files define agent identity, principles, communication style, expertise areas,
# and interaction patterns. These files are used during agent initialization to
# customize agent behavior.
#
# File Naming: {agent-id}-role.md (e.g., implementer-role.md)
# Location: templates/agent_roles/

# Required YAML Frontmatter Fields
role_id: agent-id           # Must match agent_id (e.g., "implementer", "architect")
version: 1.0.0              # Semantic version of the role definition
description: "Brief description of the agent role and purpose"

# Optional YAML Frontmatter Fields
author: "Author name"       # Who created/updated this role file
created: "2025-01-XX"       # Creation date (YYYY-MM-DD)
updated: "2025-01-XX"       # Last update date (YYYY-MM-DD)
compatibility:
  min_framework_version: "1.0.0"  # Minimum framework version required
  max_framework_version: null      # Maximum framework version (null = no limit)
tags:
  - tag1                    # Optional tags for categorization
  - tag2
---

# {Agent Name} Role Definition

## Identity

<!--
Define who the agent is, their role, and their primary responsibilities.
This section establishes the agent's core identity and purpose.

Format:
- Role title and description
- Primary responsibilities
- Key characteristics
- What makes this agent unique
-->

**Role**: {Agent Title}

**Description**: {Clear description of the agent's purpose and role in the development process}

**Primary Responsibilities**:
- {Responsibility 1}
- {Responsibility 2}
- {Responsibility 3}

**Key Characteristics**:
- {Characteristic 1}
- {Characteristic 2}

---

## Principles

<!--
Define the core principles and values that guide the agent's behavior.
These are the foundational beliefs and guidelines that influence all decisions.

Format:
- List of principles (bullet points)
- Each principle should be actionable and clear
- Principles should align with the agent's role
-->

**Core Principles**:
- {Principle 1 - what the agent believes and follows}
- {Principle 2}
- {Principle 3}

**Guidelines**:
- {Guideline 1 - specific behavioral guidance}
- {Guideline 2}

---

## Communication Style

<!--
Define how the agent communicates with users.
This affects tone, verbosity, formality, and interaction patterns.

Format:
- Tone: formal/informal, friendly/professional, etc.
- Verbosity: concise/detailed/balanced
- Formality: formal/casual/professional
- Response patterns: direct/exploratory, prescriptive/collaborative
-->

**Tone**: {e.g., professional, friendly, technical, concise}

**Verbosity**: {e.g., concise, detailed, balanced - specify when to be verbose vs concise}

**Formality**: {e.g., professional, casual, formal}

**Response Patterns**:
- {Pattern 1 - how agent responds to questions}
- {Pattern 2 - how agent provides feedback}

**Examples**:
- {Example of communication style}

---

## Expertise Areas

<!--
Define the agent's areas of expertise and specialization.
This helps route tasks to the right agent and sets expectations.

Format:
- List of expertise domains
- Specializations within each domain
- Technologies, frameworks, or tools the agent knows well
-->

**Primary Expertise**:
- {Domain 1}: {Specialization details}
- {Domain 2}: {Specialization details}

**Technologies & Tools**:
- {Technology/Tool 1}: {Level of expertise}
- {Technology/Tool 2}: {Level of expertise}

**Specializations**:
- {Specialization 1}
- {Specialization 2}

---

## Interaction Patterns

<!--
Define how the agent interacts with users, systems, and other agents.
This covers workflows, command patterns, and collaboration styles.

Format:
- How the agent receives and processes requests
- Typical workflows or processes the agent follows
- How the agent collaborates with other agents
- Command and response patterns
-->

**Request Processing**:
- {How agent processes user requests}

**Typical Workflows**:
1. {Step 1}
2. {Step 2}
3. {Step 3}

**Collaboration**:
- {How agent works with other agents}

**Command Patterns**:
- {Pattern for common commands}

---

## Notes

<!--
Optional additional notes, examples, or context-specific information.
-->

{Any additional notes, examples, or context}

