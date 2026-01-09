## 🚀 New Features

### TypeScript Security Analysis
- Real security pattern detection for TypeScript/JavaScript files
- Detects dangerous patterns: `eval()`, `innerHTML`, `dangerouslySetInnerHTML`, `document.write`, etc.
- CWE IDs included for all security patterns (CWE-94, CWE-79)
- `SecurityIssue` dataclass for structured security reporting
- Security score now reflects actual issues found

### Improver Auto-Apply Option
- New `--auto-apply` flag: Apply improvements with automatic backup
- New `--preview` flag: Show diff without modifying file
- Timestamped backups stored in `.tapps-agents/backups/`
- Verification review runs after auto-apply
- `DiffResult` dataclass with unified diff and line statistics

### Score Explanation Mode
- New `--explain` flag for `reviewer score` command
- Explanations include: reason, identified issues, recommendations
- Tool availability status (ESLint, TypeScript compiler)
- Works for both Python and TypeScript/JavaScript files

## 📚 Documentation
- `docs/TYPESCRIPT_SUPPORT.md` - Complete TypeScript support guide
- `docs/TRACEABILITY_MATRIX.md` - Requirements to implementation mapping
- `docs/STORY_VERIFICATION_CHECKLIST.md` - Acceptance criteria verification

## ✅ Tests
- 56 new tests for TypeScript enhancement features
- `tests/agents/reviewer/test_typescript_security.py` (26 tests)
- `tests/agents/improver/test_auto_apply.py` (18 tests)
- Acceptance criteria tests mapped to Gherkin scenarios

## 📖 Usage

```bash
# Score TypeScript with explanations
tapps-agents reviewer score src/app.tsx --explain

# Auto-apply improvements with backup
tapps-agents improver improve-quality src/app.tsx --auto-apply

# Preview changes without modifying
tapps-agents improver improve-quality src/app.tsx --preview
```

## 📦 Installation

```bash
pip install tapps-agents==3.5.0
```