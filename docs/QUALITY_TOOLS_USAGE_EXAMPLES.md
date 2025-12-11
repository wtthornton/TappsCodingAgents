# Quality Tools Usage Examples

**TappsCodingAgents + Cursor AI Skills**

This document provides practical examples of using quality tools via the Reviewer Skill in Cursor AI.

---

## Overview

The Reviewer Skill provides access to 5 quality tools:

1. **Ruff** - Python linting (10-100x faster)
2. **mypy** - Static type checking
3. **bandit** - Security vulnerability scanning
4. **jscpd** - Code duplication detection
5. **pip-audit** - Dependency security auditing

---

## Example 1: Ruff Linting

### Command
```
@reviewer *lint src/api/auth.py
```

### Expected Output
```
🔍 Ruff Linting: src/api/auth.py

Score: 8.5/10 ✅
Issues Found: 3

Issues:
1. [E501] Line 42: Line too long (120 > 100 characters)
   Fix: Break line into multiple lines
   Code:
   ```python
   # Before
   result = some_function_with_very_long_parameter_list(param1, param2, param3, param4, param5)
   
   # After
   result = some_function_with_very_long_parameter_list(
       param1, param2, param3, param4, param5
   )
   ```
   
2. [F401] Line 5: 'os' imported but unused
   Fix: Remove unused import
   Code:
   ```python
   # Before
   import os
   import json
   
   # After
   import json
   ```
   
3. [W503] Line 15: Line break before binary operator
   Fix: Move operator to end of line
   Code:
   ```python
   # Before
   if (condition1
       and condition2):
   
   # After
   if (condition1 and
       condition2):
   ```

Quality Gate: ✅ PASS (score >= 8.0)
```

---

## Example 2: mypy Type Checking

### Command
```
@reviewer *type-check src/api/auth.py
```

### Expected Output
```
🔍 mypy Type Checking: src/api/auth.py

Score: 7.0/10 ⚠️
Errors Found: 3

Errors:
1. Line 25: Argument 1 to "process_user" has incompatible type "str"; expected "User"
   Error Code: [arg-type]
   Fix: Pass User object instead of string
   Code:
   ```python
   # Before
   user_id = "123"
   process_user(user_id)  # Error: expects User object
   
   # After
   user = User(id="123")
   process_user(user)  # Correct
   ```
   
2. Line 42: "None" has no attribute "name"
   Error Code: [union-attr]
   Fix: Add None check before accessing attribute
   Code:
   ```python
   # Before
   user = get_user(id)
   print(user.name)  # Error: user might be None
   
   # After
   user = get_user(id)
   if user:
       print(user.name)  # Safe
   ```
   
3. Line 58: Function is missing a return type annotation
   Error Code: [missing-return-type]
   Fix: Add return type annotation
   Code:
   ```python
   # Before
   def process_data(data):
       return data.upper()
   
   # After
   def process_data(data: str) -> str:
       return data.upper()
   ```

Quality Gate: ⚠️ WARNING (score < 8.0, not blocking)
```

---

## Example 3: Bandit Security Scan

### Command
```
@reviewer *security-scan src/api/auth.py
```

### Expected Output
```
🔍 Bandit Security Scan: src/api/auth.py

Score: 6.0/10 ⚠️
Issues Found: 2 (1 HIGH, 1 MEDIUM)

Security Issues:
1. [HIGH] Line 42: Use of insecure function 'eval()'
   Severity: HIGH
   CWE: CWE-95
   Fix: Use ast.literal_eval() or JSON parsing instead
   Code:
   ```python
   # Before (INSECURE)
   user_input = request.get("data")
   result = eval(user_input)  # DANGEROUS!
   
   # After (SECURE)
   import json
   user_input = request.get("data")
   result = json.loads(user_input)  # Safe
   ```
   
2. [MEDIUM] Line 58: Hardcoded password in source code
   Severity: MEDIUM
   CWE: CWE-798
   Fix: Move password to environment variable or secure config
   Code:
   ```python
   # Before (INSECURE)
   PASSWORD = "secret123"  # Hardcoded password
   
   # After (SECURE)
   import os
   PASSWORD = os.getenv("API_PASSWORD")  # From environment
   ```

Quality Gate: ❌ FAIL (security score < 7.0, blocking)
Action Required: Fix security issues before proceeding.
```

---

## Example 4: jscpd Duplication Detection

### Command
```
@reviewer *duplication src/api/auth.py
```

### Expected Output
```
🔍 Code Duplication: src/api/auth.py

Score: 8.5/10 ✅
Duplication: 1.5% (below 3% threshold)

Duplicated Blocks:
1. Lines 25-35 duplicated in lines 58-68 (11 lines)
   Similarity: 95%
   Fix: Extract to shared function
   Code:
   ```python
   # Duplicated code (lines 25-35 and 58-68)
   def validate_user(user_data):
       if not user_data.get("email"):
           raise ValueError("Email required")
       if not user_data.get("name"):
           raise ValueError("Name required")
       return True
   
   # Extract to shared function
   def validate_user_data(user_data):
       """Validate user data with common checks."""
       if not user_data.get("email"):
           raise ValueError("Email required")
       if not user_data.get("name"):
           raise ValueError("Name required")
       return True
   
   # Use in both places
   validate_user_data(user_data)
   ```

Quality Gate: ✅ PASS (duplication < 3%)
```

---

## Example 5: pip-audit Dependency Audit

### Command
```
@reviewer *audit-deps
```

### Expected Output
```
🔍 Dependency Security Audit

Score: 7.5/10 ✅
Vulnerabilities Found: 2 (0 CRITICAL, 1 HIGH, 1 MEDIUM)

Vulnerabilities:
1. [HIGH] requests==2.28.0: CVE-2023-32681
   Severity: HIGH
   Description: SSRF vulnerability in requests library
   Fix: Upgrade to requests>=2.31.0
   Command:
   ```bash
   pip install --upgrade "requests>=2.31.0"
   ```
   
2. [MEDIUM] urllib3==1.26.0: CVE-2023-45803
   Severity: MEDIUM
   Description: Certificate validation bypass
   Fix: Upgrade to urllib3>=2.0.0
   Command:
   ```bash
   pip install --upgrade "urllib3>=2.0.0"
   ```

Quality Gate: ⚠️ WARNING (HIGH vulnerability found, should fix)
Recommendation: Upgrade vulnerable dependencies before deployment.
```

---

## Example 6: Full Review with All Tools

### Command
```
@reviewer *review src/api/auth.py
```

### Expected Output
```
📊 Code Review: src/api/auth.py

Scores:
- Complexity: 7.2/10 ✅
- Security: 8.5/10 ✅
- Maintainability: 7.8/10 ✅
- Test Coverage: 85% ✅
- Performance: 7.0/10 ✅
- Overall: 76.5/100 ✅ PASS

Quality Tools Results:
- Ruff: 8.5/10 ✅ (3 issues, all fixable)
- mypy: 7.0/10 ⚠️ (3 type errors)
- bandit: 8.5/10 ✅ (0 high-severity issues)
- jscpd: 8.5/10 ✅ (1.5% duplication)
- pip-audit: 7.5/10 ✅ (2 vulnerabilities, 0 CRITICAL)

Quality Gates: ✅ PASS
- Overall score 76.5 >= 70.0 ✅
- Security score 8.5 >= 7.0 ✅
- Complexity score 7.2 <= 8.0 ✅

LLM Feedback:
1. **Code Quality**: Well-structured code with good separation of concerns
2. **Security**: No critical security issues found
3. **Improvements**:
   - Add type hints for better maintainability (mypy warnings)
   - Consider extracting helper function for complex logic (line 42)
   - Fix linting issues (E501, F401, W503)

Context7 References:
- FastAPI usage verified against official documentation ✅
- Security best practices checked ✅

Recommendations:
1. Fix type checking errors (3 issues)
2. Address linting warnings (3 issues)
3. Upgrade dependencies (2 vulnerabilities)
```

---

## Example 7: Parallel Tool Execution

When running `*review`, tools are executed in parallel when possible:

```
📊 Running Quality Tools (Parallel Execution)...

[Parallel Group 1]
✅ Ruff linting: 0.5s
✅ mypy type checking: 1.2s
✅ bandit security scan: 0.8s

[Sequential Group 2]
✅ jscpd duplication: 2.1s

[Sequential Group 3]
✅ pip-audit dependencies: 3.5s

Total Time: 3.5s (vs 8.1s sequential) ⚡ 57% faster
```

---

## Best Practices

1. **Run tools before committing**: Use `*review` to check code quality
2. **Fix blocking issues first**: Security and critical errors must be fixed
3. **Address warnings**: Non-blocking warnings should be fixed when possible
4. **Use parallel execution**: `*review` runs tools in parallel automatically
5. **Check dependencies regularly**: Run `*audit-deps` before deployment
6. **Monitor duplication**: Keep duplication below 3% threshold

---

## Troubleshooting

### Tool Not Found

If a tool is not found, install it:

```bash
# Ruff
pip install ruff

# mypy
pip install mypy

# bandit
pip install bandit

# jscpd (via npm)
npm install -g jscpd

# pip-audit
pip install pip-audit
```

### Tool Timeout

If a tool times out (>30 seconds):
- Check file size (large files may timeout)
- Check tool configuration
- Try running tool directly to debug

### False Positives

If a tool reports false positives:
- Check tool configuration (`.ruff.toml`, `mypy.ini`, etc.)
- Adjust quality gates in `.tapps-agents/quality-gates.yaml`
- Report issues for tool-specific configuration

---

## Configuration

### Quality Gates

Configure thresholds in `.tapps-agents/quality-gates.yaml`:

```yaml
quality_gates:
  overall_min: 70.0
  security_min: 7.0
  complexity_max: 8.0
  maintainability_min: 7.0
  test_coverage_min: 80.0
  linting_min: 8.0
  type_checking_min: 8.0
  duplication_max: 3.0
```

### Tool Configuration

Each tool can be configured:

- **Ruff**: `ruff.toml` or `pyproject.toml`
- **mypy**: `mypy.ini` or `pyproject.toml`
- **bandit**: `bandit.yaml`
- **jscpd**: `.jscpdrc.json`
- **pip-audit**: Uses `requirements.txt` or `pyproject.toml`

---

## Next Steps

1. **Try the examples**: Run each command in Cursor AI
2. **Customize thresholds**: Adjust quality gates for your project
3. **Integrate into workflow**: Use `*review` before commits
4. **Monitor trends**: Track quality scores over time

