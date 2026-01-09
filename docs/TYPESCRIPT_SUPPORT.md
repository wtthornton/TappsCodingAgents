# TypeScript & JavaScript Support Guide

**Phase 7.1 Enhancement**: Comprehensive TypeScript/JavaScript support with security analysis and detailed feedback.

## Overview

TappsCodingAgents provides full code quality analysis for TypeScript and JavaScript files, including:

- **Linting**: ESLint integration for code style and best practices
- **Type Checking**: TypeScript compiler (tsc) for type safety
- **Security Analysis**: Pattern-based security vulnerability detection
- **Complexity Analysis**: Cyclomatic complexity measurement
- **Maintainability Scoring**: Code quality metrics

## Supported File Types

| Extension | Language | Linting | Type Checking | Security |
|-----------|----------|---------|---------------|----------|
| `.ts` | TypeScript | ✅ ESLint | ✅ tsc | ✅ Full |
| `.tsx` | TypeScript React | ✅ ESLint | ✅ tsc | ✅ Full + React |
| `.js` | JavaScript | ✅ ESLint | ⚠️ Neutral | ✅ Full |
| `.jsx` | JavaScript React | ✅ ESLint | ⚠️ Neutral | ✅ Full + React |

## Commands

### Review a File

```bash
# CLI
tapps-agents reviewer review src/app.tsx

# Cursor
@reviewer *review src/app.tsx
```

### Score a File

```bash
# CLI
tapps-agents reviewer score src/app.tsx

# With explanations
tapps-agents reviewer score src/app.tsx --explain

# Cursor
@reviewer *score src/app.tsx
```

### Security Scan

```bash
# CLI
tapps-agents reviewer security-scan src/app.tsx

# Cursor
@reviewer *security-scan src/app.tsx
```

### Lint a File

```bash
# CLI
tapps-agents reviewer lint src/app.tsx

# Cursor
@reviewer *lint src/app.tsx
```

### Type Check a File

```bash
# CLI
tapps-agents reviewer type-check src/app.tsx

# Cursor
@reviewer *type-check src/app.tsx
```

## Score Metrics

### Complexity Score (0-10)
- **Lower is better** (inverted in overall score)
- Measures cyclomatic complexity
- Counts decision points: if, else, for, while, switch, catch, &&, ||, ?:

### Security Score (0-10)
- **Higher is better**
- Base score: 10.0
- Deductions:
  - HIGH severity issue: -2.0 each
  - MEDIUM severity issue: -1.0 each
  - LOW severity issue: -0.5 each

### Linting Score (0-10)
- **Higher is better**
- Based on ESLint results
- Deductions:
  - Error: -2.0 each
  - Warning: -1.0 each
- Returns 5.0 (neutral) if ESLint unavailable

### Type Checking Score (0-10)
- **Higher is better**
- Based on TypeScript compiler (tsc) results
- Deductions: -0.5 per type error
- Returns 5.0 (neutral) for JavaScript files or if tsc unavailable

### Maintainability Score (0-10)
- **Higher is better**
- Based on:
  - Comments and documentation
  - Type annotations (TypeScript)
  - Interfaces and type aliases
  - Code organization (imports/exports)
  - Error handling
- Penalties for:
  - Long lines (>120 chars)
  - Deep nesting (>3 levels)
  - Long functions (>50 lines)

### Performance Score (0-10)
- **Higher is better**
- Context-aware performance analysis

### Test Coverage Score (0-10)
- **Higher is better**
- Checks for test files (.test.ts, .spec.ts)
- Checks for __tests__ directory

### Overall Score (0-100)
Weighted average:
- Complexity: 20% (inverted)
- Security: 15%
- Maintainability: 25%
- Test Coverage: 15%
- Performance: 10%
- Linting: 10%
- Type Checking: 5%

## Security Patterns Detected

### JavaScript/TypeScript Patterns

| Pattern | Severity | Description | CWE |
|---------|----------|-------------|-----|
| `eval()` | HIGH | Arbitrary code execution | CWE-95 |
| `innerHTML =` | MEDIUM | XSS vulnerability | CWE-79 |
| `outerHTML =` | MEDIUM | XSS vulnerability | CWE-79 |
| `document.write()` | MEDIUM | XSS vulnerability | CWE-79 |
| `new Function()` | HIGH | Arbitrary code execution | CWE-95 |
| `setTimeout("...")` | MEDIUM | Arbitrary code execution | CWE-95 |
| `setInterval("...")` | MEDIUM | Arbitrary code execution | CWE-95 |
| `insertAdjacentHTML()` | MEDIUM | XSS vulnerability | CWE-79 |

### React-Specific Patterns

| Pattern | Severity | Description | CWE |
|---------|----------|-------------|-----|
| `dangerouslySetInnerHTML` | HIGH | XSS vulnerability | CWE-79 |
| `javascript:` URLs | HIGH | Arbitrary code execution | CWE-79 |
| `target="_blank"` without `rel` | LOW | Tabnabbing vulnerability | CWE-1022 |

## Tool Requirements

### Required Tools

1. **Node.js** (for npx)
   ```bash
   # Verify installation
   node --version
   npm --version
   npx --version
   ```

2. **ESLint** (via npx or global install)
   ```bash
   # Global install
   npm install -g eslint
   
   # Or use via npx (automatic)
   npx eslint --version
   ```

3. **TypeScript** (via npx or global install)
   ```bash
   # Global install
   npm install -g typescript
   
   # Or use via npx (automatic)
   npx tsc --version
   ```

### Optional Tools

- **ESLint Security Plugins**
  ```bash
  npm install --save-dev eslint-plugin-security
  npm install --save-dev @typescript-eslint/eslint-plugin
  ```

## Configuration

### TypeScript Config

The scorer respects `tsconfig.json` if present in the project root.

### ESLint Config

The scorer uses your project's ESLint configuration if present:
- `eslint.config.js` (flat config)
- `.eslintrc.js`
- `.eslintrc.json`
- `.eslintrc.yaml`

### Custom Configuration

```yaml
# .tapps-agents/config.yaml
quality_tools:
  eslint_enabled: true
  tsc_enabled: true
  typescript_security_enabled: true
```

## Score Explanations

When a score is low, explanations are provided:

```json
{
  "security_score": 6.0,
  "_explanations": {
    "security_score": {
      "score": 6.0,
      "reason": "2 security issue(s) detected: 1 HIGH severity, 1 MEDIUM severity",
      "issues": [
        "eval at line 42: eval() can execute arbitrary code",
        "innerHTML at line 55: innerHTML can lead to XSS vulnerabilities"
      ],
      "recommendations": [
        "Use JSON.parse() for JSON, or safer alternatives",
        "Use textContent for plain text, or sanitize input with DOMPurify"
      ],
      "tool_status": "pattern_based"
    }
  }
}
```

## Tool Status

Review output includes tool availability:

```json
{
  "_tool_status": {
    "eslint": "available",
    "tsc": "available",
    "security_scanner": "pattern_based",
    "npm": "available"
  }
}
```

Status values:
- `available`: Tool is installed and working
- `unavailable`: Tool not found (neutral score used)
- `error`: Tool found but errored
- `pattern_based`: Using built-in pattern detection

## Known Limitations

1. **Security Analysis**
   - Pattern-based detection (not AST-based)
   - May have false positives in comments/strings
   - Does not detect all vulnerability types

2. **Type Checking**
   - Requires TypeScript files to have valid syntax
   - May timeout on very large files (>30s)
   - tsconfig.json must be valid

3. **ESLint**
   - Requires valid ESLint configuration
   - May timeout on very large files (>30s)
   - Some rules may not apply to all projects

4. **Performance**
   - First run may be slow (npx downloads)
   - Large files may take longer to analyze

## Troubleshooting

### ESLint Not Available

```
"linting_score": 5.0,
"_linting_note": "ESLint not available"
```

**Solution**: Install ESLint globally or locally:
```bash
npm install -g eslint
# or
npm install --save-dev eslint
```

### TypeScript Not Available

```
"type_checking_score": 5.0,
"_type_checking_note": "TypeScript compiler not available"
```

**Solution**: Install TypeScript globally or locally:
```bash
npm install -g typescript
# or
npm install --save-dev typescript
```

### Timeout Errors

If analysis times out, the file may be too large or complex.

**Solution**:
- Split large files into smaller modules
- Increase timeout in config (if available)
- Run analysis on specific files rather than directories

## Related Documentation

- [Command Reference](.cursor/rules/command-reference.mdc)
- [Agent Capabilities](.cursor/rules/agent-capabilities.mdc)
- [Evaluation Review Response](EVALUATION_REVIEW_RESPONSE.md)

## Version History

- **Phase 6.4.4**: Initial TypeScript support
- **Phase 7.1**: Security analysis, score explanations, tool status