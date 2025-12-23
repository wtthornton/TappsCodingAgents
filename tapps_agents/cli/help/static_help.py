"""
Static help text for all agent commands - no network required.

This module provides offline help text for all agent commands.
Help commands should never require network connections or agent activation.
"""

ENHANCER_HELP = """
Enhancer Agent Commands:

  enhance <prompt>                    - Full prompt enhancement (7-stage pipeline)
  enhance-quick <prompt>               - Quick enhancement (stages 1-3)
  enhance-stage <stage> <prompt>      - Run specific enhancement stage
  enhance-resume <session-id>          - Resume interrupted enhancement session
  help                                 - Show this help message

Options:
  --format <json|markdown|yaml>       - Output format (default: markdown)
  --output <file>                     - Save output to file
  --config <path>                     - Custom configuration file

Stages (for enhance-stage):
  analysis, requirements, architecture, implementation, testing, documentation

Examples:
  python -m tapps_agents.cli enhancer enhance "Add user authentication"
  python -m tapps_agents.cli enhancer enhance-quick "Create login page" --format json
  python -m tapps_agents.cli enhancer enhance-stage analysis "Build payment system"

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

ANALYST_HELP = """
Analyst Agent Commands:

  gather-requirements <description>   - Gather and document requirements
  stakeholder-analysis <description>   - Analyze stakeholders and their needs
  tech-research <requirement>         - Research technology options
  estimate-effort <feature>           - Estimate effort and complexity
  assess-risk <feature>               - Assess risks for a feature
  competitive-analysis <product>      - Perform competitive analysis
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --context <context>                  - Additional context
  --output <file>                      - Save output to file
  --stakeholders <s...>                - List of stakeholders (for stakeholder-analysis)
  --criteria <c...>                     - Evaluation criteria (for tech-research)
  --competitors <c...>                 - List of competitors (for competitive-analysis)

Examples:
  python -m tapps_agents.cli analyst gather-requirements "Build payment system"
  python -m tapps_agents.cli analyst tech-research "Authentication" --context "Python backend"
  python -m tapps_agents.cli analyst estimate-effort "User authentication feature"

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

ARCHITECT_HELP = """
Architect Agent Commands:

  design-system <requirements>         - System architecture design
  architecture-diagram <description>   - Generate architecture diagrams
  tech-selection <component>           - Technology decision-making
  design-security <system>             - Security architecture design
  define-boundaries <system>            - System boundary definition
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --context <context>                  - Additional context
  --output <file>                      - Save output to file
  --diagram-type <type>                - Diagram type: component, sequence, deployment
  --requirements <reqs>                 - Requirements (for tech-selection)
  --constraints <c...>                 - Constraints (for tech-selection)
  --threat-model <model>               - Threat model (for design-security)

Examples:
  python -m tapps_agents.cli architect design-system "Microservices e-commerce platform"
  python -m tapps_agents.cli architect architecture-diagram "User authentication flow" --diagram-type sequence
  python -m tapps_agents.cli architect tech-selection "Message queue" --requirements "horizontal scaling"

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

DEBUGGER_HELP = """
Debugger Agent Commands:

  debug <error_message>                 - Debug error and find root cause
  analyze-error <error_message>        - Analyze error with stack trace
  trace <file>                          - Code execution tracing
  help                                  - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --file <path>                        - Source file where error occurred
  --line <n>                           - Line number where error occurred
  --stack-trace <file|text>            - Stack trace file or text
  --code-context <context>             - Code context (for analyze-error)
  --function <name>                    - Function name (for trace)
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli debugger debug "KeyError: 'user_id'" --file src/api.py --line 42
  python -m tapps_agents.cli debugger analyze-error "ValueError: invalid literal" --stack-trace traceback.txt
  python -m tapps_agents.cli debugger trace src/api.py --function authenticate_user

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

DESIGNER_HELP = """
Designer Agent Commands:

  api-design <requirements>            - API specification design
  data-model-design <requirements>    - Database schema and data model design
  ui-ux-design <feature>               - UI/UX design specifications
  wireframes <screen>                  - Wireframe generation
  design-system <project>              - Design system creation
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --api-type <REST|GraphQL|gRPC>      - API type (default: REST)
  --data-source <source>              - Data source (for data-model-design)
  --user-stories <stories>...          - User stories (for ui-ux-design)
  --wireframe-type <type>              - Wireframe type: page, component, flow
  --brand-guidelines <guidelines>      - Brand guidelines (for design-system)
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli designer api-design "User management API with CRUD operations"
  python -m tapps_agents.cli designer data-model-design "User, Post, Comment entities" --data-source PostgreSQL
  python -m tapps_agents.cli designer wireframes "Login page" --wireframe-type page

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

DOCUMENTER_HELP = """
Documenter Agent Commands:

  document <file>                      - Generate documentation for a file
  generate-docs <file>                  - Generate API documentation
  update-readme                         - Generate or update README.md
  document-api <file>                   - Document API endpoints
  help                                 - Show this help message

Options:
  --output-format <format>             - Output format: markdown, rst, html, openapi
  --output <file>                      - Save output to file
  --project-root <path>                - Project root directory
  --context <context>                  - Additional context
  --docstring-format <format>         - Docstring format: google, numpy, sphinx
  --write-file                          - Write docstrings to file

Examples:
  python -m tapps_agents.cli documenter document src/utils.py
  python -m tapps_agents.cli documenter generate-docs src/api/routes.py --output-format openapi
  python -m tapps_agents.cli documenter update-readme

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

IMPLEMENTER_HELP = """
Implementer Agent Commands:

  implement <specification> <file>     - Generate code from specification
  refactor <file> <instruction>        - Refactor existing code
  generate-code <specification>        - Generate code without writing to file
  help                                 - Show this help message

Options:
  --format <json|text|markdown|diff>  - Output format (default: json)
  --context <context>                  - Additional context
  --language <lang>                    - Programming language (default: python)
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli implementer implement "Create a User model" src/models/user.py
  python -m tapps_agents.cli implementer refactor src/utils.py "Extract common logic"
  python -m tapps_agents.cli implementer generate-code "Create email validation function"

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

IMPROVER_HELP = """
Improver Agent Commands:

  refactor <file> <instruction>       - Code refactoring
  optimize <file>                      - Performance optimization
  improve-quality <file>               - Code quality improvement
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --instruction <text>                 - Refactoring instruction
  --type <type>                        - Optimization type: performance, memory, both
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli improver refactor src/utils.py --instruction "Extract helper functions"
  python -m tapps_agents.cli improver optimize src/api.py --type performance
  python -m tapps_agents.cli improver improve-quality src/legacy.py

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

OPS_HELP = """
Ops Agent Commands:

  security-scan [target]               - Security vulnerability scanning
  compliance-check [type]              - Compliance checking (GDPR, HIPAA, PCI-DSS)
  audit-dependencies                   - Dependency vulnerability scanning
  plan-deployment <description>        - Deployment planning
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --target <path>                      - Target path (for security-scan)
  --type <type>                        - Scan type or compliance standard
  --severity-threshold <level>        - Severity threshold: low, medium, high, critical
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli ops security-scan
  python -m tapps_agents.cli ops compliance-check --type GDPR
  python -m tapps_agents.cli ops audit-dependencies --severity-threshold high

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

ORCHESTRATOR_HELP = """
Orchestrator Agent Commands:

  workflow-list                        - List available workflows
  workflow-start <workflow_id>         - Start a workflow
  workflow-status                      - Get workflow status
  workflow-next                        - Execute next workflow step
  workflow-skip <step_id>              - Skip a workflow step
  workflow-resume                      - Resume interrupted workflow
  gate                                 - Evaluate workflow gate condition
  help                                 - Show this help message

Options:
  --condition <expr>                   - Gate condition expression
  --scoring-data <json>                - Scoring data for gate evaluation

Examples:
  python -m tapps_agents.cli orchestrator workflow-list
  python -m tapps_agents.cli orchestrator workflow-start workflow_123
  python -m tapps_agents.cli orchestrator workflow-status

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

PLANNER_HELP = """
Planner Agent Commands:

  plan <description>                   - Create development plan
  create-story <description>          - Create user story
  list-stories                         - List user stories
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --epic <name>                        - Epic name (for create-story)
  --priority <level>                   - Priority: high, medium, low
  --status <status>                     - Story status (for list-stories)
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli planner plan "Add user authentication with OAuth"
  python -m tapps_agents.cli planner create-story "User login functionality" --epic "Authentication" --priority high
  python -m tapps_agents.cli planner list-stories --epic "Authentication"

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

REVIEWER_HELP = """
Reviewer Agent Commands:

  review [files...]                    - Comprehensive code review
  score [files...]                     - Fast objective quality metrics
  lint [files...]                      - Code style checking (Ruff)
  type-check [files...]                - Type annotation validation (mypy)
  report <target> <formats>...         - Comprehensive project-wide quality reports
  duplication <target>                 - Code duplication detection
  security-scan [files...]             - Security vulnerability scanning
  analyze-project                      - Comprehensive project analysis
  analyze-services [services...]      - Service/module analysis
  docs <library> [topic]               - Get library documentation from Context7
  help                                 - Show this help message

Options:
  --format <json|text|markdown|html>  - Output format (default: json)
  --pattern <glob>                     - Glob pattern for batch processing
  --max-workers <n>                    - Concurrent operations (default: 4)
  --output <file>                      - Save output to file
  --output-dir <dir>                   - Output directory (for report)

Examples:
  python -m tapps_agents.cli reviewer review src/main.py
  python -m tapps_agents.cli reviewer score src/utils.py --format text
  python -m tapps_agents.cli reviewer lint src/ --pattern "**/*.py"
  python -m tapps_agents.cli reviewer report src/ json markdown html

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

TESTER_HELP = """
Tester Agent Commands:

  test <file>                          - Generate and run tests
  generate-tests <file>                 - Generate tests without running
  run-tests [test_path]                - Run existing test suite
  help                                 - Show this help message

Options:
  --format <json|text|markdown>       - Output format (default: json)
  --test-file <path>                   - Path for generated test file
  --integration                        - Generate integration tests too
  --no-coverage                        - Skip coverage analysis
  --output <file>                      - Save output to file

Examples:
  python -m tapps_agents.cli tester test src/utils.py
  python -m tapps_agents.cli tester generate-tests src/api.py --test-file tests/test_api.py
  python -m tapps_agents.cli tester run-tests tests/unit/

For more information, see: docs/TAPPS_AGENTS_COMMAND_REFERENCE.md
"""

# Map agent names to their help text
AGENT_HELP_MAP = {
    "enhancer": ENHANCER_HELP,
    "analyst": ANALYST_HELP,
    "architect": ARCHITECT_HELP,
    "debugger": DEBUGGER_HELP,
    "designer": DESIGNER_HELP,
    "documenter": DOCUMENTER_HELP,
    "implementer": IMPLEMENTER_HELP,
    "improver": IMPROVER_HELP,
    "ops": OPS_HELP,
    "orchestrator": ORCHESTRATOR_HELP,
    "planner": PLANNER_HELP,
    "reviewer": REVIEWER_HELP,
    "tester": TESTER_HELP,
}


def get_static_help(agent_name: str) -> str:
    """
    Get static help text for an agent - no network required.
    
    Args:
        agent_name: Name of the agent (e.g., "enhancer", "reviewer")
        
    Returns:
        Help text string for the agent, or a message if agent not found
    """
    return AGENT_HELP_MAP.get(agent_name, f"Help not available for agent: {agent_name}")

