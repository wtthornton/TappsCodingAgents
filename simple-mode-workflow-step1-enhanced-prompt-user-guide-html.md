# Step 1: Enhanced Prompt - User Guide HTML Update

## Original Request
"Update the user guide html with all the information, features, help, starting guide and examples"

## Enhanced Prompt with Requirements Analysis

### 1. Intent Analysis
**User Intent**: Create a comprehensive, up-to-date HTML user guide that serves as the primary documentation interface for TappsCodingAgents.

**Scope**: 
- Complete user guide covering all features, capabilities, and usage patterns
- Help documentation with commands and examples
- Getting started guide for new users
- Feature documentation for all 13 agents and Simple Mode
- Examples and use cases

### 2. Functional Requirements

#### Core Content Requirements
1. **Overview Section**
   - What is TappsCodingAgents
   - Key features and capabilities
   - Architecture overview (13 agents, 16 built-in experts, industry experts)
   - Cursor AI Integration status

2. **Getting Started Guide**
   - Installation instructions
   - Initial setup (`tapps-agents init`)
   - Simple Mode setup and onboarding
   - First commands/examples
   - Project initialization

3. **Simple Mode Documentation**
   - What is Simple Mode
   - How to enable/disable
   - Natural language commands (`*build`, `*review`, `*fix`, `*test`, `*full`)
   - Intent detection and workflows
   - Complete workflow steps (7-step build workflow)
   - Configuration options
   - Examples for each command type

4. **Agent Reference (13 Agents)**
   - Planning: analyst, planner
   - Design: architect, designer
   - Development: implementer, debugger, documenter
   - Testing: tester
   - Quality: reviewer, improver
   - Operations: ops
   - Orchestration: orchestrator
   - Enhancement: enhancer
   
   For each agent:
   - Purpose and capabilities
   - When to use
   - Common commands (CLI and Cursor Skills)
   - Example usage
   - Integration with experts

5. **Features & Capabilities**
   - Workflow Agents (13)
   - Expert System (16 built-in + industry experts)
   - Simple Mode
   - Cursor Skills Integration
   - Background Agents
   - Multi-Agent Orchestration
   - YAML Workflow Definitions
   - Project Profiling
   - Code Scoring System
   - Prompt Enhancement

6. **Help & Command Reference**
   - CLI commands
   - Cursor Skills commands (`@agent-name *command`)
   - Simple Mode commands
   - Workflow presets
   - Configuration commands

7. **Examples Section**
   - Simple Mode examples (build, review, fix, test)
   - Agent usage examples
   - Workflow examples
   - Real-world use cases

8. **Navigation & UX**
   - Clear navigation structure
   - Table of contents
   - Quick links
   - Search functionality (if possible)
   - Mobile-responsive design

### 3. Non-Functional Requirements

#### Quality Standards
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Fast loading, optimized assets
- **Browser Compatibility**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Mobile Responsive**: Works on all screen sizes
- **SEO**: Proper meta tags, semantic HTML

#### Design Requirements
- **Consistency**: Match existing `docs/html/styles.css` design system
- **Dark Theme**: Use existing color palette and variables
- **Typography**: Inter font family, readable line heights
- **Code Blocks**: Syntax highlighting, copy-to-clipboard buttons
- **Interactivity**: Smooth scrolling, hover effects, clear CTAs

#### Content Requirements
- **Accuracy**: All information must be current and verified
- **Completeness**: Cover all major features and capabilities
- **Clarity**: Clear, concise, beginner-friendly language
- **Examples**: Practical, real-world examples throughout
- **Links**: Proper internal linking between sections

### 4. Architecture Guidance

#### HTML Structure
- Semantic HTML5 elements (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`)
- Accessible navigation with proper ARIA labels
- Structured content hierarchy (h1 → h2 → h3)
- Proper use of lists, code blocks, and tables

#### Component Design
- Reusable card components for agent descriptions
- Code example blocks with syntax highlighting
- Command reference tables
- Feature showcase sections
- Navigation sidebar or top nav

#### Integration Points
- Link to existing HTML docs (technical-spec.html, api-reference.html, examples.html)
- Use existing styles.css (no new CSS file needed, extend existing)
- Maintain navigation consistency with other HTML docs

### 5. Codebase Context

#### Existing Files to Reference
- `docs/html/user-guide-index.html` - Current user guide structure
- `docs/html/styles.css` - Design system and styles
- `docs/html/index.html` - Home page structure
- `docs/SIMPLE_MODE_GUIDE.md` - Simple Mode documentation source
- `.cursor/rules/simple-mode.mdc` - Simple Mode rules
- `.cursor/rules/agent-capabilities.mdc` - Agent capabilities reference
- `README.md` - Main project documentation
- `docs/README.md` - Documentation index

#### Patterns to Follow
- Match navigation structure from `user-guide-index.html`
- Use existing doc-card pattern for linking to sub-sections
- Follow existing HTML structure patterns
- Maintain footer consistency

### 6. Implementation Strategy

#### Task Breakdown
1. **Content Gathering** - Extract information from all source docs
2. **Structure Design** - Design HTML structure and navigation
3. **Section Implementation** - Build each major section
4. **Styling** - Apply existing styles, ensure consistency
5. **Links & Navigation** - Add internal and external links
6. **Examples** - Add code examples and use cases
7. **Review** - Check completeness, accuracy, accessibility

#### Dependencies
- Existing styles.css must be available
- Source markdown files for content extraction
- Understanding of all 13 agents and their capabilities
- Simple Mode workflow understanding (7-step process)

### 7. Synthesis - Combined Enhanced Prompt

**Create a comprehensive HTML user guide (`docs/html/user-guide.html` or update `user-guide-index.html`) that includes:**

1. **Complete overview** of TappsCodingAgents framework
2. **Getting started guide** with setup instructions and first steps
3. **Simple Mode documentation** with all commands, workflows, and examples
4. **Complete agent reference** for all 13 agents with capabilities and commands
5. **Features showcase** covering all major capabilities
6. **Help & command reference** with examples
7. **Examples section** with practical use cases
8. **Proper navigation** and UX following existing design system

**Technical Requirements:**
- Use existing `docs/html/styles.css` design system
- Semantic HTML5 with accessibility compliance
- Mobile-responsive design
- Proper linking to other HTML docs
- Code examples with syntax highlighting
- Clear, beginner-friendly language
- Comprehensive coverage of all features

**Quality Standards:**
- WCAG 2.1 AA accessibility
- Cross-browser compatibility
- Performance optimized
- Accurate and up-to-date information
- Professional, polished presentation

---

**Target File**: `docs/html/user-guide-index.html` (update existing) or create comprehensive `docs/html/user-guide.html`

