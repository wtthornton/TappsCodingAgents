# Step 4: API Design - TypeScript Enhancement Suite

**Workflow**: Simple Mode *full  
**Date**: 2025-01-16

---

## 1. API Overview

### 1.1 Enhanced Methods Summary

| Component | Method | Type | Description |
|-----------|--------|------|-------------|
| TypeScriptScorer | `_calculate_security_score()` | New | Calculate security score |
| TypeScriptScorer | `_detect_dangerous_patterns()` | New | Detect dangerous patterns |
| TypeScriptScorer | `get_security_issues()` | New | Get detailed security issues |
| TypeScriptScorer | `_generate_explanations()` | New | Generate score explanations |
| ReviewerAgent | `_extract_eslint_findings()` | New | Extract ESLint findings |
| ReviewerAgent | `_extract_typescript_findings()` | New | Extract TypeScript findings |
| ReviewerAgent | `_extract_ts_security_findings()` | New | Extract security findings |
| ImproverAgent | `_create_backup()` | New | Create file backup |
| ImproverAgent | `_apply_improvements()` | New | Apply code changes |
| ImproverAgent | `_generate_diff()` | New | Generate unified diff |
| ImproverAgent | `_verify_changes()` | New | Verify applied changes |

---

## 2. TypeScriptScorer API

### 2.1 `_calculate_security_score()`

```python
def _calculate_security_score(self, code: str, file_path: Path) -> float:
    """
    Calculate security score based on dangerous patterns.
    
    Args:
        code: Source code content
        file_path: Path to the file (for React detection)
        
    Returns:
        Security score from 0.0 to 10.0 (higher is better)
        
    Score Calculation:
        - Base score: 10.0
        - HIGH severity issues: -2.0 each
        - MEDIUM severity issues: -1.0 each
        - LOW severity issues: -0.5 each
        - Minimum score: 0.0
    """
```

### 2.2 `_detect_dangerous_patterns()`

```python
def _detect_dangerous_patterns(self, code: str) -> list[dict[str, Any]]:
    """
    Detect dangerous JavaScript/TypeScript patterns.
    
    Args:
        code: Source code to analyze
        
    Returns:
        List of detected issues:
        [
            {
                "pattern": "eval",
                "severity": "HIGH",
                "line": 42,
                "column": 10,
                "message": "eval() can execute arbitrary code",
                "recommendation": "Use JSON.parse() for JSON",
                "cwe_id": "CWE-95"
            }
        ]
        
    Detected Patterns:
        - eval()
        - innerHTML assignment
        - document.write()
        - new Function()
        - setTimeout with string
        - dangerouslySetInnerHTML (React)
        - javascript: URLs
    """
```

### 2.3 `get_security_issues()`

```python
def get_security_issues(self, code: str, file_path: Path) -> dict[str, Any]:
    """
    Get detailed security issues for external access.
    
    Args:
        code: Source code content
        file_path: Path to the file
        
    Returns:
        {
            "available": True,
            "issues": [...],
            "issue_count": 5,
            "high_count": 2,
            "medium_count": 2,
            "low_count": 1,
            "score": 6.0
        }
    """
```

### 2.4 `_generate_explanations()`

```python
def _generate_explanations(
    self, 
    scores: dict[str, Any],
    security_issues: list[dict],
    eslint_available: bool,
    tsc_available: bool
) -> dict[str, dict[str, Any]]:
    """
    Generate explanations for each score.
    
    Args:
        scores: Calculated scores dictionary
        security_issues: List of security issues found
        eslint_available: Whether ESLint is available
        tsc_available: Whether TypeScript compiler is available
        
    Returns:
        {
            "security_score": {
                "score": 6.0,
                "reason": "2 security issues detected",
                "issues": ["eval() at line 42", "innerHTML at line 55"],
                "recommendations": ["Use JSON.parse()", "Use textContent"],
                "tool_status": "pattern_based"
            },
            "linting_score": {
                "score": 8.5,
                "reason": "3 warnings found",
                "issues": ["unused variable", "missing semicolon"],
                "recommendations": ["Fix ESLint warnings"],
                "tool_status": "available"
            }
        }
    """
```

---

## 3. ReviewerAgent API

### 3.1 `_extract_eslint_findings()`

```python
def _extract_eslint_findings(
    self,
    file_path: Path,
    task_number: int,
    max_findings: int = 10
) -> list[ReviewFinding]:
    """
    Extract ESLint issues as ReviewFindings.
    
    Args:
        file_path: Path to the TypeScript/JavaScript file
        task_number: Task number for finding IDs
        max_findings: Maximum number of findings to return
        
    Returns:
        List of ReviewFinding objects:
        [
            ReviewFinding(
                id="TASK-001-ESLINT-001",
                severity=Severity.MEDIUM,
                category="standards",
                file="src/app.tsx",
                line=42,
                finding="[@typescript-eslint/no-unused-vars] 'foo' is declared but never used",
                impact="Unused code increases maintenance burden",
                suggested_fix="Remove unused variable or use it"
            )
        ]
    """
```

### 3.2 `_extract_typescript_findings()`

```python
def _extract_typescript_findings(
    self,
    file_path: Path,
    task_number: int,
    max_findings: int = 10
) -> list[ReviewFinding]:
    """
    Extract TypeScript compiler errors as ReviewFindings.
    
    Args:
        file_path: Path to the TypeScript file
        task_number: Task number for finding IDs
        max_findings: Maximum number of findings to return
        
    Returns:
        List of ReviewFinding objects:
        [
            ReviewFinding(
                id="TASK-001-TSC-001",
                severity=Severity.HIGH,
                category="standards",
                file="src/app.tsx",
                line=55,
                finding="[TS2345] Argument of type 'string' is not assignable to type 'number'",
                impact="Type error may cause runtime issues",
                suggested_fix="Fix type mismatch"
            )
        ]
    """
```

### 3.3 `_extract_ts_security_findings()`

```python
def _extract_ts_security_findings(
    self,
    file_path: Path,
    code: str,
    task_number: int,
    max_findings: int = 10
) -> list[ReviewFinding]:
    """
    Extract TypeScript security issues as ReviewFindings.
    
    Args:
        file_path: Path to the file
        code: Source code content
        task_number: Task number for finding IDs
        max_findings: Maximum number of findings to return
        
    Returns:
        List of ReviewFinding objects:
        [
            ReviewFinding(
                id="TASK-001-SEC-001",
                severity=Severity.HIGH,
                category="security",
                file="src/app.tsx",
                line=42,
                finding="eval() can execute arbitrary code (CWE-95)",
                impact="Potential code injection vulnerability",
                suggested_fix="Use JSON.parse() instead of eval()"
            )
        ]
    """
```

---

## 4. ImproverAgent API

### 4.1 `_create_backup()`

```python
def _create_backup(self, file_path: str | Path) -> Path:
    """
    Create backup of file before modifications.
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file
        
    Backup Location:
        .tapps-agents/backups/<filename>.<timestamp>.backup
        
    Example:
        Input: src/app.tsx
        Output: .tapps-agents/backups/app.tsx.20250116-143022.backup
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If cannot write to backup directory
    """
```

### 4.2 `_apply_improvements()`

```python
def _apply_improvements(
    self, 
    file_path: str | Path, 
    improved_code: str
) -> None:
    """
    Apply improved code to file.
    
    Args:
        file_path: Path to file to modify
        improved_code: Improved code content
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If cannot write to file
        ValueError: If improved_code is empty
    """
```

### 4.3 `_generate_diff()`

```python
def _generate_diff(
    self, 
    original: str, 
    improved: str,
    file_path: str = "file"
) -> dict[str, Any]:
    """
    Generate unified diff between original and improved code.
    
    Args:
        original: Original code content
        improved: Improved code content
        file_path: File path for diff header
        
    Returns:
        {
            "unified_diff": "--- original\n+++ improved\n@@ ... @@\n-old\n+new",
            "lines_added": 5,
            "lines_removed": 3,
            "has_changes": True
        }
    """
```

### 4.4 `_verify_changes()`

```python
async def _verify_changes(self, file_path: str) -> dict[str, Any]:
    """
    Run verification review after applying changes.
    
    Args:
        file_path: Path to modified file
        
    Returns:
        {
            "verified": True,
            "new_score": 78.5,
            "score_change": +2.5,
            "issues_resolved": 3,
            "new_issues": 0
        }
    """
```

---

## 5. CLI Parameter Updates

### 5.1 Reviewer CLI

```bash
# Existing
tapps-agents reviewer score <file>

# Enhanced with --explain
tapps-agents reviewer score <file> --explain

# Output with --explain:
{
  "scores": {...},
  "explanations": {
    "security_score": {
      "score": 6.0,
      "reason": "...",
      "recommendations": [...]
    }
  }
}
```

### 5.2 Improver CLI

```bash
# Existing
tapps-agents improver improve-quality <file> "<instruction>"

# Enhanced with --auto-apply
tapps-agents improver improve-quality <file> "<instruction>" --auto-apply

# Enhanced with --preview
tapps-agents improver improve-quality <file> "<instruction>" --preview

# Output with --auto-apply:
{
  "applied": true,
  "backup": ".tapps-agents/backups/...",
  "diff": "--- original\n+++ improved\n...",
  "verification": {
    "verified": true,
    "new_score": 78.5
  }
}
```

---

## 6. Data Transfer Objects

### 6.1 SecurityIssueDTO

```python
@dataclass
class SecurityIssueDTO:
    """Security issue data transfer object."""
    pattern: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    line: int
    column: int | None
    message: str
    recommendation: str
    cwe_id: str | None
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

### 6.2 ScoreExplanationDTO

```python
@dataclass
class ScoreExplanationDTO:
    """Score explanation data transfer object."""
    score: float
    reason: str
    issues: list[str]
    recommendations: list[str]
    tool_status: str
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

### 6.3 DiffResultDTO

```python
@dataclass
class DiffResultDTO:
    """Diff result data transfer object."""
    unified_diff: str
    lines_added: int
    lines_removed: int
    has_changes: bool
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

---

## 7. Error Responses

### 7.1 Standard Error Format

```python
{
    "error": True,
    "error_type": "ToolNotAvailable",
    "message": "ESLint is not available",
    "details": {
        "tool": "eslint",
        "install_command": "npm install -g eslint"
    },
    "fallback_used": True,
    "fallback_score": 5.0
}
```

### 7.2 Error Types

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| ToolNotAvailable | 200 (graceful) | Tool not installed |
| FileNotFound | 404 | File doesn't exist |
| PermissionDenied | 403 | Cannot read/write file |
| Timeout | 408 | Operation timed out |
| InvalidInput | 400 | Invalid input parameters |

---

## 8. Backward Compatibility

### 8.1 Existing API Preservation

All existing APIs remain unchanged:
- `score_file()` returns same structure (with optional new fields)
- `review_file()` returns same structure (with optional new fields)
- `_handle_improve_quality()` returns same structure (with optional new fields)

### 8.2 New Fields Are Optional

New fields are added as optional:
- `explanations` - Only present if `--explain` flag used
- `tool_status` - Always present (new default)
- `preview_diff` - Only present if `--preview` flag used

---

**API Design Status**: APPROVED  
**Next Step**: Step 5 - Implementation