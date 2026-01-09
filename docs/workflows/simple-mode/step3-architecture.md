# Step 3: Architecture Design - TypeScript Enhancement Suite

**Workflow**: Simple Mode *full  
**Date**: 2025-01-16

---

## 1. System Architecture Overview

### 1.1 Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TappsCodingAgents Framework                 │
├─────────────────────────────────────────────────────────────────┤
│  CLI Layer                                                       │
│  ├── tapps-agents reviewer review <file>                        │
│  ├── tapps-agents reviewer score <file>                         │
│  └── tapps-agents improver improve-quality <file>               │
├─────────────────────────────────────────────────────────────────┤
│  Agent Layer                                                     │
│  ├── ReviewerAgent (reviewer/agent.py)                          │
│  │   ├── review_file()                                          │
│  │   ├── score_file()                                           │
│  │   └── _extract_detailed_findings() [ENHANCEMENT POINT]       │
│  ├── ImproverAgent (improver/agent.py)                          │
│  │   └── _handle_improve_quality() [ENHANCEMENT POINT]          │
│  └── Other Agents...                                            │
├─────────────────────────────────────────────────────────────────┤
│  Scorer Layer                                                    │
│  ├── ScorerRegistry - Routes files to appropriate scorer        │
│  ├── CodeScorer - Python scoring (ruff, mypy, bandit)           │
│  └── TypeScriptScorer - TS/JS scoring [ENHANCEMENT POINT]       │
│      ├── _calculate_linting_score() - ESLint                    │
│      ├── _calculate_type_checking_score() - tsc                 │
│      ├── _calculate_security_score() [NEW]                      │
│      ├── get_eslint_issues() - Detailed ESLint output           │
│      └── get_type_errors() - Detailed TypeScript output         │
├─────────────────────────────────────────────────────────────────┤
│  External Tools                                                  │
│  ├── ESLint (via npx)                                           │
│  ├── TypeScript Compiler (via npx tsc)                          │
│  └── npm audit (via npx) [NEW]                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Enhanced Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Enhanced Components                          │
├─────────────────────────────────────────────────────────────────┤
│  ReviewerAgent Enhancements                                      │
│  ├── _extract_detailed_findings()                               │
│  │   ├── _extract_eslint_findings() [NEW]                       │
│  │   ├── _extract_typescript_findings() [NEW]                   │
│  │   └── _extract_security_findings() [ENHANCED]                │
│  └── Output Format                                              │
│      ├── scores (existing)                                      │
│      ├── findings (enhanced with TypeScript)                    │
│      ├── explanations [NEW]                                     │
│      └── tool_status [NEW]                                      │
├─────────────────────────────────────────────────────────────────┤
│  ImproverAgent Enhancements                                      │
│  ├── _handle_improve_quality()                                  │
│  │   ├── Preview mode (existing)                                │
│  │   ├── Auto-apply mode [NEW]                                  │
│  │   └── Diff generation [NEW]                                  │
│  └── Support Methods                                            │
│      ├── _create_backup() [NEW]                                 │
│      ├── _apply_improvements() [NEW]                            │
│      ├── _generate_diff() [NEW]                                 │
│      └── _verify_changes() [NEW]                                │
├─────────────────────────────────────────────────────────────────┤
│  TypeScriptScorer Enhancements                                   │
│  ├── _calculate_security_score() [NEW]                          │
│  │   ├── _detect_dangerous_patterns() [NEW]                     │
│  │   ├── _check_react_security() [NEW]                          │
│  │   └── _run_npm_audit() [NEW - optional]                      │
│  └── _generate_score_explanations() [NEW]                       │
├─────────────────────────────────────────────────────────────────┤
│  New Components                                                  │
│  ├── SecurityPatternDetector [NEW]                              │
│  │   └── Dangerous pattern matching for TS/JS                   │
│  ├── DiffGenerator [NEW]                                        │
│  │   └── Unified diff generation                                │
│  └── ScoreExplainer [NEW]                                       │
│      └── Generate score explanations                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Design

### 2.1 TypeScriptScorer Enhancements

**File**: `tapps_agents/agents/reviewer/typescript_scorer.py`

```python
class TypeScriptScorer(BaseScorer):
    """Enhanced TypeScript scorer with security analysis."""
    
    # Existing methods
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]: ...
    def _calculate_complexity(self, code: str) -> float: ...
    def _calculate_linting_score(self, file_path: Path) -> float: ...
    def _calculate_type_checking_score(self, file_path: Path) -> float: ...
    def get_eslint_issues(self, file_path: Path) -> dict[str, Any]: ...
    def get_type_errors(self, file_path: Path) -> dict[str, Any]: ...
    
    # NEW methods
    def _calculate_security_score(self, code: str, file_path: Path) -> float:
        """Calculate security score based on dangerous patterns."""
        
    def _detect_dangerous_patterns(self, code: str) -> list[SecurityIssue]:
        """Detect dangerous patterns like eval(), innerHTML, etc."""
        
    def _check_react_security(self, code: str) -> list[SecurityIssue]:
        """Check React-specific security patterns."""
        
    def get_security_issues(self, code: str, file_path: Path) -> dict[str, Any]:
        """Get detailed security issues for external access."""
        
    def _generate_explanations(self, scores: dict) -> dict[str, Explanation]:
        """Generate explanations for each score."""
```

### 2.2 ReviewerAgent Enhancements

**File**: `tapps_agents/agents/reviewer/agent.py`

```python
class ReviewerAgent(BaseAgent, ExpertSupportMixin):
    
    # Enhanced methods
    async def _extract_detailed_findings(
        self,
        file_path: Path,
        scores: dict[str, Any],
        task_number: int,
    ) -> list[ReviewFinding]:
        """Extract detailed findings including TypeScript issues."""
        findings = []
        
        # Existing: Python findings (ruff, mypy, bandit)
        findings.extend(self._extract_python_findings(...))
        
        # NEW: TypeScript findings
        if file_ext in [".ts", ".tsx", ".js", ".jsx"]:
            findings.extend(self._extract_eslint_findings(file_path, task_number))
            findings.extend(self._extract_typescript_findings(file_path, task_number))
            findings.extend(self._extract_security_findings(file_path, code, task_number))
        
        return findings
    
    # NEW helper methods
    def _extract_eslint_findings(
        self, file_path: Path, task_number: int
    ) -> list[ReviewFinding]:
        """Extract ESLint issues as ReviewFindings."""
        
    def _extract_typescript_findings(
        self, file_path: Path, task_number: int
    ) -> list[ReviewFinding]:
        """Extract TypeScript compiler errors as ReviewFindings."""
        
    def _extract_security_findings(
        self, file_path: Path, code: str, task_number: int
    ) -> list[ReviewFinding]:
        """Extract security issues as ReviewFindings."""
```

### 2.3 ImproverAgent Enhancements

**File**: `tapps_agents/agents/improver/agent.py`

```python
class ImproverAgent(BaseAgent):
    
    async def _handle_improve_quality(
        self,
        file_path: str,
        instruction: str,
        auto_apply: bool = False,  # NEW parameter
        preview: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Improve code quality with optional auto-apply."""
        
        # Generate improvements
        improved_code = await self._generate_improvements(file_path, instruction)
        
        # Generate diff
        diff = self._generate_diff(original_code, improved_code)
        
        if auto_apply:
            # Create backup
            backup_path = self._create_backup(file_path)
            
            # Apply changes
            self._apply_improvements(file_path, improved_code)
            
            # Verify
            verification = await self._verify_changes(file_path)
            
            return {
                "applied": True,
                "backup": str(backup_path),
                "diff": diff,
                "verification": verification,
            }
        else:
            return {
                "applied": False,
                "preview_diff": diff,
                "instruction": instruction.to_dict(),
                "note": "Use --auto-apply to apply changes",
            }
    
    # NEW helper methods
    def _create_backup(self, file_path: str) -> Path:
        """Create backup of file before modifications."""
        
    def _apply_improvements(self, file_path: str, improved_code: str) -> None:
        """Apply improved code to file."""
        
    def _generate_diff(self, original: str, improved: str) -> str:
        """Generate unified diff between original and improved code."""
        
    async def _verify_changes(self, file_path: str) -> dict[str, Any]:
        """Run verification review after applying changes."""
```

---

## 3. Data Models

### 3.1 SecurityIssue Model

```python
@dataclass
class SecurityIssue:
    """Represents a security issue found in code."""
    pattern: str           # e.g., "eval", "innerHTML"
    severity: Severity     # HIGH, MEDIUM, LOW
    line: int
    column: int | None
    message: str
    recommendation: str
    cwe_id: str | None    # Common Weakness Enumeration ID
```

### 3.2 ScoreExplanation Model

```python
@dataclass
class ScoreExplanation:
    """Explanation for a code quality score."""
    score: float
    reason: str
    issues: list[str]
    recommendations: list[str]
    tool_status: str      # available, unavailable, error
    tool_name: str | None
```

### 3.3 DiffResult Model

```python
@dataclass
class DiffResult:
    """Result of code diff generation."""
    unified_diff: str
    lines_added: int
    lines_removed: int
    files_changed: int
    has_changes: bool
```

---

## 4. Security Patterns

### 4.1 JavaScript/TypeScript Dangerous Patterns

```python
DANGEROUS_PATTERNS = {
    "eval": {
        "pattern": r"\beval\s*\(",
        "severity": "HIGH",
        "message": "eval() can execute arbitrary code",
        "recommendation": "Use JSON.parse() for JSON, or safer alternatives",
        "cwe_id": "CWE-95"
    },
    "innerHTML": {
        "pattern": r"\.innerHTML\s*=",
        "severity": "MEDIUM",
        "message": "innerHTML can lead to XSS vulnerabilities",
        "recommendation": "Use textContent or sanitize input",
        "cwe_id": "CWE-79"
    },
    "document.write": {
        "pattern": r"\bdocument\.write\s*\(",
        "severity": "MEDIUM",
        "message": "document.write can be exploited for XSS",
        "recommendation": "Use DOM manipulation methods instead",
        "cwe_id": "CWE-79"
    },
    "Function constructor": {
        "pattern": r"\bnew\s+Function\s*\(",
        "severity": "HIGH",
        "message": "Function constructor can execute arbitrary code",
        "recommendation": "Use arrow functions or regular function declarations",
        "cwe_id": "CWE-95"
    },
    "setTimeout string": {
        "pattern": r"\bsetTimeout\s*\(\s*['\"]",
        "severity": "MEDIUM",
        "message": "setTimeout with string can execute arbitrary code",
        "recommendation": "Use function reference instead of string",
        "cwe_id": "CWE-95"
    },
}

# React-specific patterns
REACT_SECURITY_PATTERNS = {
    "dangerouslySetInnerHTML": {
        "pattern": r"dangerouslySetInnerHTML",
        "severity": "HIGH",
        "message": "dangerouslySetInnerHTML can lead to XSS",
        "recommendation": "Sanitize content or use safe rendering",
        "cwe_id": "CWE-79"
    },
    "javascript: URL": {
        "pattern": r"href\s*=\s*['\"]javascript:",
        "severity": "HIGH",
        "message": "javascript: URLs can execute arbitrary code",
        "recommendation": "Use onClick handlers instead",
        "cwe_id": "CWE-79"
    },
}
```

---

## 5. Integration Points

### 5.1 CLI Integration

**File**: `tapps_agents/cli/commands/reviewer.py`

```python
@reviewer.command()
@click.option("--explain", is_flag=True, help="Include score explanations")
async def score(file_path: str, explain: bool = False):
    """Score a file with optional explanations."""
```

**File**: `tapps_agents/cli/commands/improver.py`

```python
@improver.command()
@click.option("--auto-apply", is_flag=True, help="Auto-apply improvements")
@click.option("--preview", is_flag=True, help="Preview changes without applying")
async def improve_quality(file_path: str, instruction: str, auto_apply: bool, preview: bool):
    """Improve code quality with optional auto-apply."""
```

### 5.2 Output Format Integration

Review output with enhancements:

```json
{
  "file": "src/app.tsx",
  "file_type": "typescript",
  "scoring": {
    "complexity_score": 7.5,
    "security_score": 6.0,
    "maintainability_score": 8.0,
    "test_coverage_score": 5.0,
    "performance_score": 7.0,
    "linting_score": 8.5,
    "type_checking_score": 9.0,
    "overall_score": 72.5
  },
  "explanations": {
    "security_score": {
      "score": 6.0,
      "reason": "2 security issues detected",
      "issues": ["innerHTML assignment at line 42", "eval() usage at line 55"],
      "recommendations": ["Use textContent instead of innerHTML", "Use JSON.parse() instead of eval()"],
      "tool_status": "available"
    }
  },
  "tool_status": {
    "eslint": "available",
    "tsc": "available",
    "security_scanner": "pattern_based"
  },
  "findings": [
    {
      "id": "TASK-001-ESLINT-001",
      "severity": "MEDIUM",
      "category": "standards",
      "file": "src/app.tsx",
      "line": 42,
      "column": 15,
      "finding": "[@typescript-eslint/no-unused-vars] 'foo' is declared but never used",
      "impact": "Unused code increases maintenance burden",
      "suggested_fix": "Remove unused variable or use it"
    },
    {
      "id": "TASK-001-SEC-001",
      "severity": "HIGH",
      "category": "security",
      "file": "src/app.tsx",
      "line": 55,
      "finding": "eval() can execute arbitrary code (CWE-95)",
      "impact": "Potential code injection vulnerability",
      "suggested_fix": "Use JSON.parse() for JSON parsing"
    }
  ]
}
```

---

## 6. Error Handling

### 6.1 Graceful Degradation

```python
class TypeScriptScorer:
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        scores = {}
        
        # Linting - graceful degradation
        if self.has_eslint:
            scores["linting_score"] = self._calculate_linting_score(file_path)
        else:
            scores["linting_score"] = 5.0
            scores["_linting_note"] = "ESLint not available"
        
        # Type checking - graceful degradation
        if self.has_tsc and file_path.suffix in [".ts", ".tsx"]:
            scores["type_checking_score"] = self._calculate_type_checking_score(file_path)
        else:
            scores["type_checking_score"] = 5.0
            scores["_type_checking_note"] = "TypeScript compiler not available"
        
        # Security - always available (pattern-based)
        scores["security_score"] = self._calculate_security_score(code, file_path)
        
        return scores
```

### 6.2 Error Messages

| Scenario | Error Message | User Action |
|----------|--------------|-------------|
| ESLint not installed | "ESLint not available. Install via: npm install -g eslint" | Install ESLint |
| TypeScript not installed | "TypeScript compiler not available. Install via: npm install -g typescript" | Install TypeScript |
| File too large | "File exceeds maximum size (1MB). Consider splitting into smaller files." | Split file |
| Timeout | "Analysis timed out after 30s. File may be too complex." | Simplify file |

---

## 7. Configuration

### 7.1 Config Schema Updates

**File**: `.tapps-agents/config.yaml`

```yaml
quality_tools:
  # Existing
  ruff_enabled: true
  mypy_enabled: true
  
  # NEW: TypeScript settings
  eslint_enabled: true
  tsc_enabled: true
  typescript_security_enabled: true
  npm_audit_enabled: false  # Optional, requires npm
  
  # NEW: Auto-apply settings
  auto_apply_backup_dir: ".tapps-agents/backups"
  auto_apply_verify: true
  
  # NEW: Explanation settings
  explain_low_scores: true
  low_score_threshold: 7.0
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

| Component | Test File | Coverage Target |
|-----------|-----------|-----------------|
| TypeScriptScorer._calculate_security_score | test_typescript_scorer.py | 90% |
| TypeScriptScorer._detect_dangerous_patterns | test_typescript_scorer.py | 95% |
| ReviewerAgent._extract_eslint_findings | test_reviewer_typescript.py | 90% |
| ImproverAgent._create_backup | test_improver_auto_apply.py | 95% |
| ImproverAgent._generate_diff | test_improver_auto_apply.py | 90% |

### 8.2 Integration Tests

| Scenario | Test File |
|----------|-----------|
| Full TypeScript review with ESLint | test_typescript_integration.py |
| Auto-apply with verification | test_improver_integration.py |
| Score explanations end-to-end | test_explanations_integration.py |

---

**Architecture Status**: APPROVED  
**Next Step**: Step 4 - API Design