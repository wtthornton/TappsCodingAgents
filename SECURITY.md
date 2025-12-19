# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**We take security seriously.** If you discover a security vulnerability, please follow these steps:

### 1. Do NOT create a public issue

**Never** report security vulnerabilities through public GitHub issues or discussions.

### 2. Report via GitHub Security Advisories

**Use GitHub Security Advisories** to report vulnerabilities privately:
1. Go to the repository's Security tab
2. Click "Report a vulnerability"
3. Fill out the security advisory form

**Include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: As quickly as possible based on severity

### 4. Disclosure Policy

- Vulnerabilities will be disclosed after a fix is released
- Credit will be given to reporters (if desired)
- A security advisory will be published

## Security Best Practices

### For Users

1. **Keep dependencies updated:**
   ```bash
   pip install --upgrade tapps-agents
   ```

2. **Use dependency security scanning:**
   ```bash
   python -m tapps_agents.cli ops check-vulnerabilities
   ```

3. **Review configuration files:**
   - Validate YAML configuration files
   - Use environment variables for sensitive data
   - Never commit API keys or credentials

4. **Limit file system access:**
   - Use path validation in agent configuration
   - Restrict write permissions where possible
   - Use read-only agents for analysis tasks

5. **Secure credential storage:**
   - Use environment variables for API keys
   - Use secure credential management tools
   - Never hardcode credentials in code

### For Developers

1. **Input Validation:**
   - Always validate user input
   - Use type hints and Pydantic models
   - Sanitize file paths and command arguments

2. **Error Handling:**
   - Don't expose sensitive information in error messages
   - Log errors appropriately
   - Use specific exception types

3. **Dependencies:**
   - Keep dependencies up-to-date
   - Use `pip-audit` regularly
   - Review dependency changes

4. **Code Review:**
   - Security-focused code reviews
   - Check for common vulnerabilities
   - Verify authentication/authorization

## Security Features

### Built-in Security

1. **Path Validation:**
   - All file operations validate paths against allowed roots (project root and `.tapps-agents/`)
   - Prevents directory traversal attacks through root-based validation
   - Resolved paths are verified to be within allowed boundaries
   - See [Filesystem Access Policy](docs/SECURITY_FILESYSTEM_ACCESS_POLICY.md) for details

2. **Command Validation:**
   - Star-prefixed command system
   - Command whitelisting
   - Input sanitization

3. **Model Provider Security:**
   - Secure API key handling
   - No credential logging
   - Optional local-first execution

4. **Dependency Scanning:**
   - Integrated `pip-audit` support
   - Automatic vulnerability detection
   - Configurable severity thresholds

5. **Code Quality:**
   - Security-focused linting (Ruff, Bandit)
   - Type checking (mypy)
   - Code review tools

## Known Security Considerations

### LLM Provider Access

- API keys are required for cloud providers (Anthropic, OpenAI)
- Keys should be stored securely (environment variables)
- Local-first execution (Ollama) reduces cloud exposure

### File System Access

- Agents have file system access by design, restricted to project root and `.tapps-agents/` directory
- Path validation enforces root-based boundaries (not just string heuristics)
- All file operations are validated against allowed roots
- See [Filesystem Access Policy](docs/SECURITY_FILESYSTEM_ACCESS_POLICY.md) for detailed rules

### External Tool Execution

- Some agents execute external tools (Ruff, mypy, etc.)
- Tools are executed in subprocesses
- Validate tool outputs before processing

### Configuration Files

- YAML configuration files can contain sensitive data
- **Important**: The configuration loader does **not** automatically interpolate environment variables (e.g., `${ANTHROPIC_API_KEY}` is treated as a literal string)
- If you need environment variable substitution, expand env vars before writing `config.yaml` or use environment variables directly in your code
- Validate configuration schemas
- Never commit API keys or credentials to version control

## Security Audit

### Regular Audits

We perform regular security audits:
- Dependency vulnerability scanning (monthly)
- Code security review (quarterly)
- Penetration testing (as needed)

### Audit Tools

- `pip-audit` - Dependency vulnerability scanning
- `bandit` - Python security linter
- `ruff` - General code quality and security
- `mypy` - Type safety checks

### Running Security Checks

```bash
# Check dependencies
python -m tapps_agents.cli ops check-vulnerabilities

# Lint code
ruff check .

# Security linting
bandit -r tapps_agents/

# Type checking
mypy tapps_agents/
```

## Responsible Disclosure

We follow responsible disclosure practices:

1. **Private Reporting**: Vulnerabilities reported privately
2. **Timely Fixes**: Prompt development of fixes
3. **Public Disclosure**: After fix is available
4. **Credit**: Recognition for security researchers

## Security Updates

Security updates are released as:
- **Patch releases** (e.g., 2.0.0 → 2.0.1) for critical issues
- **Minor releases** for significant security improvements
- **Security advisories** published on GitHub

## Compliance

### Data Privacy

- No telemetry or data collection
- Local-first execution model
- Optional cloud provider usage
- No user data stored

### GDPR Considerations

- No personal data processing
- Local execution option
- User-controlled data

### Best Practices

- Follow OWASP guidelines
- Regular security reviews
- Dependency updates
- Secure coding practices

## Contact

**Security Issues**: Use [GitHub Security Advisories](https://github.com/wtthornton/TappsCodingAgents/security/advisories)  
**General Questions**: Open a [discussion](https://github.com/wtthornton/TappsCodingAgents/discussions)

---

**Last Updated**: January 2026  
**Policy Version**: 1.0

