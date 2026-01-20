#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TappsCodingAgents Prompt Enhancement Demo

This demo showcases the prompt enhancement feature by demonstrating how
a simple prompt is transformed into a comprehensive, context-aware prompt
through the 7-stage enhancement pipeline.

Usage:
    python demo/demo_prompt_enhancement.py
    python demo/demo_prompt_enhancement.py "Create a user authentication system"
"""

import sys
import io
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(text: str, width: int = 80):
    """Print a formatted header."""
    print("\n" + "=" * width)
    print(f"  {text}  ".center(width, "="))
    print("=" * width + "\n")


def print_section(title: str, width: int = 80):
    """Print a formatted section."""
    print("\n" + "-" * width)
    print(f"  {title}")
    print("-" * width + "\n")


def demo_prompt_enhancement(original_prompt: str = None):
    """
    Demonstrate prompt enhancement by showing what the enhanced prompt would look like.
    
    This demo shows the transformation process without actually running the
    enhancement pipeline, making it fast and suitable for demonstrations.
    """
    
    # Default demo prompt if none provided
    if original_prompt is None:
        original_prompt = "Create a user authentication system"
    
    print_header("TappsCodingAgents - Prompt Enhancement Demo")
    
    print("""
This demo showcases how the Enhancer Agent transforms simple prompts into
comprehensive, context-aware prompts through a 7-stage enhancement pipeline.

[PRIMARY] CURSOR IDE INTEGRATION
  Use @enhancer directly in Cursor chat for seamless prompt enhancement!
  Example: @enhancer *enhance "Your prompt" --format yaml

[FEATURE] YAML OUTPUT SUPPORT
  Enhanced prompts can be output in YAML format for easy integration
  with workflows, CI/CD pipelines, and configuration management.

The enhancement process includes:
  1. Analysis - Detects intent, scope, domains, and workflow type
  2. Requirements - Gathers functional/non-functional requirements with expert consultation
  3. Architecture - Provides system design guidance and patterns
  4. Codebase Context - Injects relevant codebase context and related files
  5. Quality Standards - Defines security, testing, and quality thresholds
  6. Implementation Strategy - Creates task breakdown and implementation order
  7. Synthesis - Combines all stages into final enhanced prompt

INTEGRATION:
  - Cursor IDE: Use @enhancer in Cursor chat for prompt enhancement
  - YAML Workflows: Use prompt-enhancement.yaml workflow
  - YAML Output: Get enhanced prompts in YAML format for further processing
""")
    
    # Show original prompt
    print_section("ORIGINAL PROMPT")
    print(f'"{original_prompt}"')
    print("\nThis is a simple, vague prompt that needs enhancement...")
    
    # Skip interactive prompt in non-interactive mode
    try:
        input("\nPress Enter to see how this prompt is enhanced...")
    except (EOFError, KeyboardInterrupt):
        print("\nProceeding with enhancement demo...\n")
    
    # Show enhanced prompt (simulated)
    print_section("ENHANCED PROMPT (7-Stage Pipeline Output)")
    print("(Showing Markdown format - YAML format also available)\n")
    
    enhanced_prompt = generate_enhanced_prompt_demo(original_prompt)
    print(enhanced_prompt)
    
    # Show YAML format option
    print_section("YAML FORMAT OUTPUT")
    print("""
The enhanced prompt can also be output in YAML format for programmatic use:

Command (Cursor IDE):
  @enhancer *enhance "Create a user authentication system" --format yaml

Command (CLI):
  python -m tapps_agents.cli enhancer enhance "Create a user authentication system" --format yaml

YAML format provides structured data that can be:
  - Parsed programmatically
  - Used as input for other tools
  - Integrated into CI/CD pipelines
  - Stored in version control
  - Shared across teams

See the YAML OUTPUT EXAMPLE section below for a sample YAML structure.
""")
    
    # Show the enhancement stages
    print_section("ENHANCEMENT STAGES BREAKDOWN")
    
    stages_info = [
        {
            "stage": "1. Analysis",
            "output": "Intent: Feature (authentication)\nDomain: security, user-management\nScope: Medium (5-8 files)\nWorkflow: greenfield",
        },
        {
            "stage": "2. Requirements",
            "output": "Functional: User login/logout, password reset, session management\nNon-functional: Security compliance, performance, scalability\nExpert Consultation: Security expert (51%), User-management expert (24.5%), Compliance expert (24.5%)",
        },
        {
            "stage": "3. Architecture",
            "output": "Pattern: Service layer + JWT tokens\nTechnology: bcrypt for passwords, Redis for sessions\nDesign: RESTful API with middleware authentication",
        },
        {
            "stage": "4. Codebase Context",
            "output": "Related files: user models, API routes, middleware\nPatterns: Existing authentication patterns in codebase\nDependencies: Current auth libraries and frameworks",
        },
        {
            "stage": "5. Quality Standards",
            "output": "Security Score: Minimum 8.5/10\nTest Coverage: 85% minimum\nCode Quality: Maintainability score > 8.0\nPerformance: Response time < 200ms",
        },
        {
            "stage": "6. Implementation Strategy",
            "output": "Task 1: Create User model with auth fields\nTask 2: Implement AuthService (login/logout)\nTask 3: Create API endpoints\nTask 4: Add password reset flow\nTask 5: Write unit/integration tests\nTask 6: Add security middleware",
        },
        {
            "stage": "7. Synthesis",
            "output": "Combines all stages into comprehensive enhanced prompt\nIncludes metadata, requirements, architecture, quality gates, and implementation plan",
        },
    ]
    
    for stage_info in stages_info:
        print(f"\n{stage_info['stage']}:")
        print(f"  {stage_info['output']}")
    
    # Show comparison
    print_section("BEFORE vs AFTER COMPARISON")
    
    print("""
BEFORE (Original Prompt):
  "Create a user authentication system"
  
  [X] Vague and unclear
  [X] No requirements specified
  [X] No architecture guidance
  [X] No quality standards
  [X] No implementation plan

AFTER (Enhanced Prompt):
  [OK] Comprehensive specification with 7 stages of analysis
  [OK] Detailed functional and non-functional requirements
  [OK] Architecture patterns and technology recommendations
  [OK] Codebase context and related files identified
  [OK] Quality gates and security standards defined
  [OK] Step-by-step implementation strategy
  [OK] Expert consultation from domain specialists
""")
    
    # Show usage
    print_section("HOW TO USE PROMPT ENHANCEMENT")
    
    print("""
=== CURSOR IDE INTEGRATION (PRIMARY METHOD) ===

Use the @enhancer agent directly in Cursor chat - this is the recommended way!

1. Full Enhancement (all 7 stages) with YAML output:
   @enhancer *enhance "Create a user authentication system" --format yaml
   
2. Quick Enhancement (stages 1-3 only):
   @enhancer *enhance-quick "Add user authentication"
   
3. Save Enhanced Prompt to YAML File:
   @enhancer *enhance "Your prompt" --format yaml --output enhanced.yaml
   
4. Run Specific Stage:
   @enhancer *enhance-stage analysis "Your prompt"
   
5. Use in Cursor Workflows:
   The enhanced prompt can be used directly with other Cursor Skills:
   @implementer *implement {enhanced_prompt}
   @planner *plan {enhanced_prompt}
   @architect *design {enhanced_prompt}

=== COMMAND LINE (Alternative) ===

1. Full Enhancement (all 7 stages):
   python -m tapps_agents.cli enhancer enhance "Your prompt here"
   
2. Quick Enhancement (stages 1-3 only):
   python -m tapps_agents.cli enhancer enhance-quick "Your prompt here"
   
3. YAML Format Output:
   python -m tapps_agents.cli enhancer enhance "Your prompt" --format yaml
   
4. Save to YAML file:
   python -m tapps_agents.cli enhancer enhance "Your prompt" --output enhanced.yaml
   
5. Run specific stage:
   python -m tapps_agents.cli enhancer enhance-stage analysis --prompt "Your prompt"

=== YAML WORKFLOW INTEGRATION ===

Use YAML workflows to automate prompt enhancement:

1. Run the built-in prompt-enhancement workflow:
   python -m tapps_agents.cli workflow prompt-enhancement --prompt "Your prompt"
   
2. Use in Cursor with YAML workflows:
   @orchestrator *workflow prompt-enhancement --prompt "Your prompt"
   
3. Create custom workflows in workflows/ directory using YAML format
""")
    
    # Show YAML workflow example
    print_section("YAML WORKFLOW EXAMPLE")
    
    print("""
Example YAML workflow (workflows/prompt-enhancement.yaml):

id: prompt-enhancement
name: Prompt Enhancement Workflow
type: utility
steps:
  - id: analyze
    agent: analyst
    action: analyze-prompt
    creates: ["prompt_metadata"]
    next: enrich-requirements
  
  - id: enrich-requirements
    agent: analyst
    action: gather-requirements
    consults: ["expert-*"]
    requires: ["prompt_metadata"]
    creates: ["requirements"]
    next: architecture-guidance
  
  - id: architecture-guidance
    agent: architect
    action: design-system
    requires: ["requirements"]
    creates: ["architecture"]
    next: synthesize
  
  - id: synthesize
    agent: enhancer
    action: synthesize-prompt
    requires: ["prompt_metadata", "requirements", "architecture"]
    creates: ["enhanced_prompt"]
""")
    
    print_section("KEY FEATURES")
    
    print("""
[PRIMARY] Cursor IDE Integration
   - Use @enhancer directly in Cursor chat (PRIMARY METHOD)
   - Leverages Cursor Skills for execution
   - Works seamlessly with Cursor's AI capabilities
   - Integrates with Cursor's context and codebase awareness
   - Example: @enhancer *enhance "Your prompt" --format yaml

[FEATURE] YAML Support (Full Integration)
   - Output enhanced prompts in YAML format (--format yaml)
   - Use YAML workflows for automation (workflows/*.yaml)
   - Configuration via YAML files (.tapps-agents/enhancement-config.yaml)
   - Easy integration with CI/CD pipelines
   - YAML workflow definitions for complex multi-step processes

[FEATURE] Industry Expert Integration
   - Automatically detects relevant domains
   - Consults multiple experts with weighted consensus
   - Injects domain-specific patterns and best practices

[FEATURE] Codebase Awareness
   - Analyzes existing code patterns
   - Identifies related files and dependencies
   - Maintains consistency with current architecture

[FEATURE] Quality-First Approach
   - Defines security and quality thresholds upfront
   - Includes testing requirements
   - Sets performance benchmarks

[FEATURE] Implementation Ready
   - Provides actionable task breakdown
   - Suggests implementation order
   - Includes technical constraints and considerations
""")
    
    # Show YAML configuration example
    print_section("YAML CONFIGURATION EXAMPLE")
    
    print("""
Configure enhancement via .tapps-agents/enhancement-config.yaml:

```yaml
enhancement:
  stages:
    analysis: true
    requirements: true
    architecture: true
    codebase_context: true
    quality: true
    implementation: true
    synthesis: true
  
  requirements:
    consult_experts: true
    min_expert_confidence: 0.7
    include_nfr: true
  
  architecture:
    context7_enabled: true
    include_patterns: true
  
  codebase_context:
    tier: TIER2
    include_related: true
    max_related_files: 10
  
  quality:
    include_security: true
    include_testing: true
    scoring_threshold: 70.0
  
  synthesis:
    format: yaml  # Output format: markdown, json, or yaml
    include_metadata: true
```
""")
    
    # Show YAML output example
    print_section("YAML OUTPUT EXAMPLE")
    
    print("""
Enhanced prompts can be output in YAML format for easy integration.
Run: @enhancer *enhance "Your prompt" --format yaml

Example YAML output:

```yaml
enhanced_prompt:
  metadata:
    intent: "Feature (authentication)"
    domain: ["security", "user-management", "compliance"]
    scope: "Medium (5-8 files, ~500-800 lines)"
    workflow: "greenfield"
    complexity: "Medium"
    estimated_time: "2-3 days"
  
  requirements:
    functional:
      - "User registration with email/password validation"
      - "User login with email/password authentication"
      - "Session management with JWT tokens"
      - "Password reset functionality via email"
    
    non_functional:
      security: "OWASP Top 10 compliance, rate limiting (5 attempts/15min)"
      performance: "Response time < 200ms, support 1000 concurrent users"
      scalability: "Horizontal scaling support, stateless authentication"
      compliance: "GDPR compliance, data encryption at rest and in transit"
  
  domain_context:
    security_expert:
      primary: true
      weight: 0.51
      recommendations:
        - "Use JWT-based authentication (stateless)"
        - "Rate limiting: 5 attempts per 15 minutes per IP"
        - "Password requirements: Minimum 12 characters, mixed case, numbers, symbols"
        - "Session timeout: 30 minutes with refresh tokens (7-day expiry)"
      agreement: 0.87
      confidence: 0.91
  
  architecture:
    patterns:
      - "Service Layer Pattern: Separate authentication logic into AuthService"
      - "Repository Pattern: User data access abstraction"
      - "Middleware Pattern: Authentication middleware for route protection"
    
    technology_stack:
      authentication: "JWT (jsonwebtoken library)"
      password_hashing: "bcrypt (cost factor 12)"
      session_storage: "Redis (for refresh tokens and session management)"
      email_service: "SMTP or service provider (SendGrid, AWS SES)"
  
  quality_standards:
    security:
      score_minimum: 8.5
      owasp_compliance: true
      input_validation: true
      csrf_protection: true
      rate_limiting: true
    
    testing:
      unit_coverage: 85
      integration_tests: true
      security_tests: true
    
    performance:
      response_time_ms: 200
      database_query_ms: 50
      token_generation_ms: 10
  
  implementation_strategy:
    phases:
      - phase: 1
        name: "Foundation"
        tasks:
          - "Create User Model with auth fields"
          - "Implement AuthService Core (register, login)"
      
      - phase: 2
        name: "Authentication Flow"
        tasks:
          - "Create API Endpoints (register, login, logout, refresh)"
          - "Implement Session Management (JWT tokens)"
      
      - phase: 3
        name: "Security Features"
        tasks:
          - "Add Password Reset Flow"
          - "Implement Security Middleware"
```

This YAML format makes it easy to:
  - Parse programmatically
  - Integrate with CI/CD pipelines
  - Use as input for other tools
  - Store in version control
  - Share with team members
""")
    
    print_header("Demo Complete!")
    
    print("""
=== NEXT STEPS IN CURSOR IDE ===

The enhanced prompt is now ready to be used by other Cursor Skills:

1. Use Enhanced Prompt with Other Agents:
   @implementer *implement {enhanced_prompt}
   @planner *plan {enhanced_prompt}
   @architect *design {enhanced_prompt}
   @tester *test {enhanced_prompt}
   @reviewer *review {enhanced_prompt}

2. Get YAML Output:
   @enhancer *enhance "Your prompt" --format yaml --output enhanced.yaml

3. Use YAML Workflows:
   @orchestrator *workflow prompt-enhancement --prompt "Your prompt"
   
   Available YAML workflows:
   - workflows/prompt-enhancement.yaml - Full enhancement workflow
   - workflows/rapid-dev.yaml - Uses enhancement in rapid development
   - workflows/presets/simple-new-feature.yaml - Simple feature workflow

=== CURSOR SKILLS COMMANDS ===

All commands work in Cursor IDE using @enhancer:
  - @enhancer *enhance "Your prompt" --format yaml
  - @enhancer *enhance-quick "Your prompt"
  - @enhancer *enhance-stage analysis "Your prompt" [--session-id <id>]

=== YAML INTEGRATION ===

1. Configuration: .tapps-agents/enhancement-config.yaml
2. Workflows: workflows/*.yaml files
3. Output: --format yaml for structured data
4. CI/CD: YAML output integrates with automation pipelines

For more information, see:
  - docs/ENHANCER_AGENT.md - Complete enhancer documentation
  - workflows/prompt-enhancement.yaml - YAML workflow definition
  - .claude/skills/enhancer/SKILL.md - Cursor Skills documentation
  - demo/run_demo.py - Interactive demo script
""")


def generate_enhanced_prompt_demo(original_prompt: str) -> str:
    """Generate a demo enhanced prompt (simulated output)."""
    
    enhanced = f"""# Enhanced Prompt: {original_prompt}

## Metadata
- **Intent**: Feature (authentication)
- **Domain**: security, user-management, compliance
- **Scope**: Medium (5-8 files, ~500-800 lines)
- **Workflow**: greenfield
- **Complexity**: Medium
- **Estimated Time**: 2-3 days

## Requirements

### Functional Requirements
- User registration with email/password validation
- User login with email/password authentication
- Session management with JWT tokens
- Password reset functionality via email
- Account verification (email confirmation)
- Logout functionality
- Session refresh mechanism
- User profile management (basic)

### Non-Functional Requirements
- **Security**: OWASP Top 10 compliance, rate limiting (5 attempts/15min)
- **Performance**: Response time < 200ms, support 1000 concurrent users
- **Scalability**: Horizontal scaling support, stateless authentication
- **Reliability**: 99.9% uptime, graceful error handling
- **Compliance**: GDPR compliance, data encryption at rest and in transit

### Domain Context (from Industry Experts)

#### Security Domain
**Primary Expert (expert-security, 51%):**
- Use OAuth2.0 or JWT-based authentication (JWT recommended for stateless)
- Rate limiting: 5 attempts per 15 minutes per IP
- Password requirements: Minimum 12 characters, mixed case, numbers, symbols
- Session timeout: 30 minutes with refresh tokens (7-day expiry)
- MFA recommended for admin accounts
- Password hashing: bcrypt with cost factor 12+
- Token storage: HTTP-only cookies or secure localStorage
- CSRF protection required

**Additional Expert Input:**
- [expert-user-management (24.5%)]: User model should include:
  - last_login timestamp
  - failed_attempts counter
  - account_status (active, locked, suspended)
  - password_changed_at timestamp
  - email_verified boolean
- [expert-compliance (24.5%)]: GDPR compliance requires:
  - Consent tracking for data processing
  - Right to deletion implementation
  - Data portability support
  - Privacy policy acceptance tracking

**Agreement**: 87% (high consensus)
**Confidence**: 0.91

## Architecture Guidance

### Design Patterns
- **Service Layer Pattern**: Separate authentication logic into AuthService
- **Repository Pattern**: User data access abstraction
- **Middleware Pattern**: Authentication middleware for route protection
- **Strategy Pattern**: Multiple auth providers (email/password, OAuth)

### Technology Stack
- **Authentication**: JWT (jsonwebtoken library)
- **Password Hashing**: bcrypt (cost factor 12)
- **Session Storage**: Redis (for refresh tokens and session management)
- **Email Service**: SMTP or service provider (SendGrid, AWS SES)
- **Validation**: Input validation library (Joi, Zod, or similar)

### System Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  API Gateway │────▶│ Auth Service│
│  (Browser)  │     │  (Express)   │     │             │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                           ┌────────▼────────┐    ┌─────────▼────────┐
                           │  User Database  │    │  Redis Cache    │
                           │   (PostgreSQL)   │    │  (Sessions)     │
                           └─────────────────┘    └──────────────────┘
```

### API Design
- **POST /api/auth/register** - User registration
- **POST /api/auth/login** - User authentication
- **POST /api/auth/logout** - Session termination
- **POST /api/auth/refresh** - Token refresh
- **POST /api/auth/reset-password** - Password reset request
- **POST /api/auth/reset-password/:token** - Password reset confirmation
- **POST /api/auth/verify-email/:token** - Email verification

## Codebase Context

### Related Files (if existing)
- `models/User.ts` - User model structure
- `routes/auth.ts` - Existing auth routes (if any)
- `middleware/auth.ts` - Authentication middleware patterns
- `services/email.ts` - Email service integration

### Patterns to Follow
- Follow existing error handling patterns
- Use same validation library as rest of codebase
- Match code style and naming conventions
- Integrate with existing logging system

### Dependencies
- Check existing auth libraries in package.json
- Verify database connection patterns
- Review existing middleware structure

## Quality Standards

### Security Requirements
- **Security Score**: Minimum 8.5/10 (from code scoring)
- **OWASP Compliance**: All Top 10 vulnerabilities addressed
- **Input Validation**: All user inputs validated and sanitized
- **SQL Injection**: Parameterized queries only
- **XSS Protection**: Output encoding required
- **CSRF Protection**: Token-based CSRF protection
- **Rate Limiting**: Implemented at API gateway level

### Testing Requirements
- **Unit Test Coverage**: 85% minimum
- **Integration Tests**: All API endpoints covered
- **Security Tests**: Penetration testing for auth flows
- **Load Tests**: Verify 1000 concurrent users
- **Test Types**: Unit, integration, e2e, security

### Code Quality
- **Maintainability Score**: > 8.0/10
- **Complexity**: Cyclomatic complexity < 10 per function
- **Documentation**: All public APIs documented
- **Type Safety**: Full TypeScript types (if applicable)

### Performance Benchmarks
- **Response Time**: < 200ms for auth endpoints
- **Database Queries**: < 50ms per query
- **Token Generation**: < 10ms
- **Password Hashing**: < 100ms (acceptable for security)

## Implementation Strategy

### Phase 1: Foundation (Day 1)
1. **Create User Model**
   - Define User schema with auth fields
   - Add indexes for email and username
   - Implement password hashing methods
   - Add validation rules

2. **Implement AuthService Core**
   - Create AuthService class
   - Implement register() method
   - Implement login() method with password verification
   - Add JWT token generation

### Phase 2: Authentication Flow (Day 1-2)
3. **Create API Endpoints**
   - POST /api/auth/register
   - POST /api/auth/login
   - POST /api/auth/logout
   - POST /api/auth/refresh
   - Add request validation
   - Add error handling

4. **Implement Session Management**
   - JWT access token (15min expiry)
   - Refresh token (7-day expiry)
   - Token refresh mechanism
   - Token blacklisting (optional)

### Phase 3: Security Features (Day 2)
5. **Add Password Reset Flow**
   - Generate reset tokens
   - Send reset emails
   - Validate reset tokens
   - Update password securely

6. **Implement Security Middleware**
   - Authentication middleware
   - Rate limiting middleware
   - CSRF protection
   - Input validation middleware

### Phase 4: Email & Verification (Day 2-3)
7. **Email Verification**
   - Generate verification tokens
   - Send verification emails
   - Verify email endpoints
   - Update user status

8. **Email Service Integration**
   - Configure email service
   - Create email templates
   - Add email sending logic
   - Handle email errors

### Phase 5: Testing & Quality (Day 3)
9. **Write Unit Tests**
   - AuthService methods
   - Password hashing
   - Token generation
   - Validation logic

10. **Write Integration Tests**
    - All API endpoints
    - Authentication flows
    - Error scenarios
    - Edge cases

11. **Security Testing**
    - Penetration testing
    - OWASP checklist verification
    - Rate limiting verification
    - Token security testing

### Phase 6: Documentation & Polish (Day 3)
12. **Documentation**
    - API documentation
    - Authentication guide
    - Security best practices
    - Deployment guide

13. **Code Review & Refinement**
    - Code quality review
    - Performance optimization
    - Security audit
    - Final testing

## Technical Constraints

### Security Constraints
- Passwords must never be logged or stored in plain text
- Tokens must be transmitted over HTTPS only
- Session data must be encrypted
- Rate limiting must be enforced

### Performance Constraints
- Database queries must be optimized
- Token validation must be fast (< 5ms)
- Password hashing must not block event loop
- Cache frequently accessed data

### Compliance Constraints
- GDPR: User data deletion support
- GDPR: Data portability support
- GDPR: Consent tracking
- Industry standards: OWASP compliance

## Success Criteria

- [OK] All functional requirements implemented
- [OK] Security score >= 8.5/10
- [OK] Test coverage >= 85%
- [OK] All API endpoints functional
- [OK] Performance benchmarks met
- [OK] OWASP Top 10 addressed
- [OK] Documentation complete
- [OK] Code review passed

## Next Steps

After enhancement, this prompt can be used by:
1. **@planner** - Create detailed task breakdown
2. **@implementer** - Generate implementation code
3. **@architect** - Design system architecture
4. **@tester** - Generate test suites
5. **@reviewer** - Review code quality
6. **@documenter** - Generate API documentation

---

**Enhancement Metadata:**
- **Enhancement Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Stages Completed**: 7/7 (Full Enhancement)
- **Expert Consultation**: Yes (3 experts consulted)
- **Codebase Context**: Analyzed
- **Quality Gates**: Defined
- **Implementation Plan**: Complete
"""
    
    return enhanced


def main():
    """Main entry point."""
    # Get prompt from command line or use default
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        demo_prompt_enhancement(prompt)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

