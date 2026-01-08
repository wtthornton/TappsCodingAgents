# Reviewer Agent Improvements Plan

**Based on User Feedback (Score: 5/10)**

> "TappsCodingAgents provided a useful starting point with the scoring command, but I ended up doing most of the actual analysis with direct tools (ruff, mypy, grep). The wrapper added overhead without proportional value."

This document details improvements to make the Reviewer agent more useful and reduce the gap between our wrapper and direct tool usage.

---

## Implementation Status

| # | Improvement | Status | Implementation Date |
|---|---|---|---|
| 1 | Lint target-aware execution | ✅ **COMPLETED** | 2026-01-08 |
| 2 | Include actual errors in score output | ✅ **COMPLETED** | 2026-01-08 |
| 3 | Dead code detection (vulture) | 🔲 Pending | - |
| 4 | Context7 stale cache fallback | ✅ **COMPLETED** | 2026-01-08 |
| 5 | Per-file quality thresholds | 🔲 Pending | - |

---

## Executive Summary

| # | Improvement | Effort | Impact | Priority |
|---|---|---|---|---|
| 1 | Lint target-aware execution | Medium | High | P1 |
| 2 | Include actual errors in score output | Medium | High | P1 |
| 3 | Dead code detection (vulture) | Medium | Medium | P2 |
| 4 | Context7 stale cache fallback | Low | Medium | P2 |
| 5 | Per-file quality thresholds | High | Medium | P3 |

---

## Improvement 1: Target-Aware Lint Execution

### Problem
When users run `tapps-agents reviewer lint src/myfile.py`, ruff may still:
- Use project-wide configuration that pulls in unrelated rules
- Report issues outside the targeted file
- Run slower than necessary

### Current Code
```python
# tapps_agents/agents/reviewer/agent.py:1583
async def _lint_file_internal(self, file_path: Path) -> dict[str, Any]:
    # ... runs ruff without explicit isolation
```

### Solution

**A. Add `--isolated` flag option:**
```python
async def _lint_file_internal(
    self, 
    file_path: Path,
    isolated: bool = False  # New parameter
) -> dict[str, Any]:
    cmd = ["ruff", "check", str(file_path)]
    
    if isolated:
        # Ignore project config, use ruff defaults
        cmd.extend(["--isolated", "--no-cache"])
    
    # ... rest of implementation
```

**B. Update CLI to expose isolation:**
```bash
# New flag
tapps-agents reviewer lint src/file.py --isolated

# Or always isolated for single-file linting
tapps-agents reviewer lint src/file.py  # Default to isolated for single file
tapps-agents reviewer lint src/          # Use project config for directories
```

**C. Ensure output only contains target file:**
```python
# Filter results to only requested files
if resolved_files:
    results = [r for r in results if Path(r["file"]).resolve() in resolved_files]
```

### Files to Modify
- `tapps_agents/agents/reviewer/agent.py` - `_lint_file_internal()`, `lint_file()`
- `tapps_agents/cli/commands/reviewer.py` - `lint_command()`
- `tapps_agents/cli/parsers/reviewer.py` - Add `--isolated` flag

---

## Improvement 2: Include Actual Errors in Score Output

### Problem
The `score` command returns:
```json
{
  "linting_score": 7.5,
  "type_checking_score": 8.0,
  "overall_score": 75.0
}
```

Users can't see WHAT the issues are. They have to run ruff/mypy separately.

### Current Code
```python
# tapps_agents/agents/reviewer/scoring.py:624
def _calculate_linting_score(self, file_path: Path) -> float:
    """Calculate linting score using Ruff (0-10 scale)."""
    # Runs ruff, counts issues, returns score
    # DISCARDS the actual issue details!
```

### Solution

**A. Modify scorer to return errors alongside score:**
```python
def _calculate_linting_score(
    self, file_path: Path
) -> tuple[float, list[dict[str, Any]]]:
    """
    Calculate linting score and return issues.
    
    Returns:
        Tuple of (score, issues) where issues is a list of:
        {
            "code": "F401",
            "message": "Module imported but unused",
            "line": 5,
            "column": 1,
            "severity": "warning"
        }
    """
```

**B. Update score_file to include issues:**
```python
def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
    # ... existing score calculations ...
    
    linting_score, linting_issues = self._calculate_linting_score(file_path)
    type_score, type_issues = self._calculate_type_checking_score(file_path)
    
    return {
        "linting_score": linting_score,
        "linting_issues": linting_issues,  # NEW: Actual ruff errors
        "type_checking_score": type_score,
        "type_issues": type_issues,  # NEW: Actual mypy errors
        "overall_score": overall_score,
        # ...
    }
```

**C. Update CLI output formatting:**
```python
# tapps_agents/cli/commands/reviewer.py
def _format_text_score_result(result: dict) -> str:
    output = []
    output.append(f"Overall Score: {result['overall_score']:.1f}/100")
    
    # Show top issues (if any)
    if result.get("linting_issues"):
        output.append("\nLinting Issues:")
        for issue in result["linting_issues"][:5]:  # Top 5
            output.append(f"  {issue['line']}: [{issue['code']}] {issue['message']}")
    
    if result.get("type_issues"):
        output.append("\nType Issues:")
        for issue in result["type_issues"][:5]:
            output.append(f"  {issue['line']}: {issue['message']}")
    
    return "\n".join(output)
```

### Sample Output (After)
```
$ tapps-agents score src/myfile.py

Overall Score: 72.0/100

Scores:
  Complexity:     8.5/10
  Security:       9.0/10  
  Maintainability: 7.0/10
  Linting:        7.0/10 (3 issues)
  Type Checking:  6.5/10 (2 issues)

Linting Issues:
  15: [F401] 'os' imported but unused
  42: [E501] Line too long (95 > 88)
  67: [W293] Blank line contains whitespace

Type Issues:
  23: Argument 1 to "process" has incompatible type "str"; expected "int"
  45: "Config" has no attribute "timeout"
```

### Files to Modify
- `tapps_agents/agents/reviewer/scoring.py` - `_calculate_linting_score()`, `_calculate_type_checking_score()`, `score_file()`
- `tapps_agents/cli/commands/reviewer.py` - Output formatters
- `tapps_agents/cli/formatters.py` - Add issue formatting

---

## Improvement 3: Dead Code Detection

### Problem
Current detection only finds unreachable code after return/raise statements. Doesn't find:
- Unused functions/classes
- Unused module-level code
- Dead branches

### Current Code
```python
# tapps_agents/core/evaluators/behavioral_evaluator.py:139
def _find_unreachable_code(self, func_node: ast.FunctionDef) -> list[int]:
    """Find unreachable code (after return/raise statements)."""
    # Very limited scope
```

### Solution

**A. Add vulture integration:**
```python
# tapps_agents/agents/reviewer/dead_code_detector.py (NEW FILE)
"""Dead code detection using vulture."""

import subprocess
from pathlib import Path
from typing import Any

HAS_VULTURE = shutil.which("vulture") is not None


def detect_dead_code(file_path: Path) -> list[dict[str, Any]]:
    """
    Detect dead code using vulture.
    
    Returns:
        List of dead code findings:
        {
            "type": "unused_function" | "unused_variable" | "unused_import" | "unreachable_code",
            "name": "my_function",
            "line": 42,
            "confidence": 90  # vulture's confidence percentage
        }
    """
    if not HAS_VULTURE:
        return []
    
    try:
        result = subprocess.run(
            ["vulture", str(file_path), "--min-confidence", "70"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        findings = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Parse vulture output: "file.py:42: unused function 'my_func' (90% confidence)"
            finding = _parse_vulture_line(line)
            if finding:
                findings.append(finding)
        
        return findings
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []
```

**B. Add to scoring:**
```python
# In CodeScorer
def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
    # ... existing ...
    
    # Dead Code Score (0-10, higher is better)
    dead_code_score, dead_code_findings = self._calculate_dead_code_score(file_path)
    scores["dead_code_score"] = dead_code_score
    scores["dead_code_findings"] = dead_code_findings
```

**C. Add CLI command:**
```bash
tapps-agents reviewer dead-code src/myfile.py
tapps-agents reviewer dead-code src/  # Scan directory
```

### Dependencies
Add `vulture` as optional dependency:
```toml
# pyproject.toml
[project.optional-dependencies]
quality = [
    "vulture>=2.7",
    # ... existing ...
]
```

### Files to Create/Modify
- `tapps_agents/agents/reviewer/dead_code_detector.py` - NEW
- `tapps_agents/agents/reviewer/scoring.py` - Add dead code to scorer
- `tapps_agents/cli/commands/reviewer.py` - Add `dead-code` command
- `tapps_agents/cli/parsers/reviewer.py` - Add parser
- `pyproject.toml` - Add vulture dependency

---

## Improvement 4: Context7 Stale Cache Fallback

### Problem
When Context7 API fails (quota, timeout, network), the lookup returns an error even if stale cached data exists.

### Current Code
```python
# tapps_agents/context7/lookup.py:350
# Step 3: Resolve library ID if needed (API call)
# If this fails → error returned
# NO fallback to stale cache
```

### Solution

**A. Add stale cache retrieval on API failure:**
```python
# tapps_agents/context7/lookup.py

async def lookup(
    self,
    library: str,
    topic: str | None = None,
    use_fuzzy_match: bool = True,
    allow_stale: bool = True,  # NEW: Allow stale cache on failure
    max_stale_days: int = 30,  # NEW: Max age for stale data
) -> LookupResult:
    # Step 1: Check fresh cache (existing)
    cached_entry = self.kb_cache.get(library, topic)
    if cached_entry and not self._is_stale(cached_entry, max_stale_days):
        return LookupResult(success=True, content=cached_entry.content, source="cache")
    
    # Step 2: Fuzzy matching (existing)
    # ...
    
    # Step 3: API call
    try:
        # ... existing API call logic ...
        api_result = await call_context7_resolve_with_fallback(...)
    except Exception as api_error:
        # NEW: Fallback to stale cache on API failure
        if allow_stale and cached_entry:
            logger.warning(
                f"Context7 API failed for {library}/{topic}: {api_error}. "
                f"Using stale cache (age: {self._get_cache_age(cached_entry)} days)."
            )
            return LookupResult(
                success=True,
                content=cached_entry.content,
                source="stale_cache",
                warning=f"Data may be outdated (cached {self._get_cache_age(cached_entry)} days ago)",
            )
        
        # If no stale cache, try fuzzy match with broader criteria
        if allow_stale and use_fuzzy_match:
            stale_fuzzy = self._try_stale_fuzzy_match(library, topic)
            if stale_fuzzy:
                return stale_fuzzy
        
        # Nothing available
        return LookupResult(success=False, error=str(api_error))

def _is_stale(self, entry: CacheEntry, max_days: int) -> bool:
    """Check if cache entry is stale."""
    cached_at = datetime.fromisoformat(entry.cached_at.replace("Z", "+00:00"))
    age_days = (datetime.now(UTC) - cached_at).days
    return age_days > max_days

def _get_cache_age(self, entry: CacheEntry) -> int:
    """Get cache entry age in days."""
    cached_at = datetime.fromisoformat(entry.cached_at.replace("Z", "+00:00"))
    return (datetime.now(UTC) - cached_at).days
```

**B. Add configuration:**
```yaml
# .tapps-agents/config.yaml
context7:
  cache:
    allow_stale_fallback: true
    max_stale_days: 30
    warn_on_stale: true
```

### Files to Modify
- `tapps_agents/context7/lookup.py` - Add stale fallback logic
- `tapps_agents/core/config.py` - Add Context7 cache config
- `tapps_agents/context7/backup_client.py` - Ensure errors are catchable

---

## Improvement 5: Per-File Quality Thresholds

### Problem
Project-wide thresholds don't account for:
- Test files (often lower standards acceptable)
- Generated code
- Legacy code being migrated
- Critical paths (need higher standards)

### Current Code
```python
# tapps_agents/core/config.py:105
class ReviewerAgentConfig(BaseModel):
    quality_threshold: float = Field(default=70.0)
    # Project-wide only!
```

### Solution

**A. Add path-based overrides to config:**
```yaml
# .tapps-agents/config.yaml
agents:
  reviewer:
    quality_threshold: 70.0  # Default
    
    # NEW: Per-path overrides
    threshold_overrides:
      - pattern: "tests/**/*.py"
        quality_threshold: 60.0
        complexity_threshold: null  # Ignore complexity in tests
        
      - pattern: "src/generated/**"
        quality_threshold: 50.0
        skip_lint: true
        
      - pattern: "src/core/security/**"
        quality_threshold: 85.0
        security_threshold: 9.0
```

**B. Add config model:**
```python
# tapps_agents/core/config.py

class ThresholdOverride(BaseModel):
    """Per-path threshold override."""
    pattern: str = Field(description="Glob pattern for matching files")
    quality_threshold: float | None = Field(default=None)
    complexity_threshold: float | None = Field(default=None)
    security_threshold: float | None = Field(default=None)
    maintainability_threshold: float | None = Field(default=None)
    skip_lint: bool = Field(default=False)
    skip_type_check: bool = Field(default=False)

class ReviewerAgentConfig(BaseModel):
    quality_threshold: float = Field(default=70.0)
    # ... existing fields ...
    
    # NEW
    threshold_overrides: list[ThresholdOverride] = Field(
        default_factory=list,
        description="Per-path threshold overrides"
    )
```

**C. Add threshold resolution:**
```python
# tapps_agents/agents/reviewer/agent.py

def get_thresholds_for_file(self, file_path: Path) -> dict[str, float | None]:
    """
    Get effective thresholds for a file, considering overrides.
    
    Args:
        file_path: Path to file being reviewed
        
    Returns:
        Dict of threshold name -> value (None = skip)
    """
    defaults = {
        "quality": self.config.quality_threshold,
        "complexity": 7.0,
        "security": 6.5,
        "maintainability": 6.0,
    }
    
    # Check overrides (last match wins)
    from fnmatch import fnmatch
    for override in self.config.threshold_overrides:
        if fnmatch(str(file_path), override.pattern):
            if override.quality_threshold is not None:
                defaults["quality"] = override.quality_threshold
            if override.complexity_threshold is not None:
                defaults["complexity"] = override.complexity_threshold
            # ... etc
    
    return defaults
```

**D. Update review command to use thresholds:**
```python
async def review_file(self, file_path: Path) -> dict:
    thresholds = self.get_thresholds_for_file(file_path)
    
    result = await self._do_review(file_path)
    
    # Check against file-specific thresholds
    result["passed"] = result["overall_score"] >= thresholds["quality"]
    result["threshold_used"] = thresholds["quality"]
    
    return result
```

### Files to Modify
- `tapps_agents/core/config.py` - Add `ThresholdOverride` model
- `tapps_agents/agents/reviewer/agent.py` - Add `get_thresholds_for_file()`
- `tapps_agents/cli/commands/reviewer.py` - Use file-specific thresholds

---

## Implementation Order

### Phase 1 (P1 - High Impact, Quick Wins)
1. **Improvement 2**: Include actual errors in score output
   - Most impactful for user experience
   - Medium effort, high value

2. **Improvement 1**: Target-aware lint execution
   - Reduces confusion and improves speed
   - Mostly configuration changes

### Phase 2 (P2 - Medium Impact)
3. **Improvement 4**: Context7 stale cache fallback
   - Low effort, improves reliability
   - Good resilience pattern

4. **Improvement 3**: Dead code detection (vulture)
   - New capability
   - Optional dependency

### Phase 3 (P3 - Nice to Have)
5. **Improvement 5**: Per-file quality thresholds
   - Most complex change
   - Requires config schema update

---

## Success Metrics

After implementing these improvements, we expect:

| Metric | Before | Target |
|---|---|---|
| User rating | 5/10 | 7/10+ |
| Need to use direct tools | "Most of the time" | "Sometimes" |
| Score output usefulness | Low (scores only) | High (scores + issues) |
| Context7 reliability | Fails on quota | Graceful degradation |

---

## Testing Plan

1. **Unit Tests**
   - Test isolated lint mode
   - Test error extraction from ruff/mypy
   - Test vulture integration
   - Test stale cache fallback
   - Test threshold resolution

2. **Integration Tests**
   - End-to-end score command with error output
   - Lint on single file vs directory
   - Context7 failure scenarios

3. **User Testing**
   - Have original feedback provider try new version
   - Measure time to identify issues
   - Compare to direct tool usage
