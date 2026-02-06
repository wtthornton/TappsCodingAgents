# Security Hardening Guide

## Critical Vulnerabilities Identified (2026-02 Audit)

### 1. Directory Traversal via Unvalidated Cache Path
**Location:** `context7/agent_integration.py` — `cache_root` parameter
**Risk:** HIGH — Attacker-controlled path could escape project boundary
**Fix:** Validate `cache_root` with `Path.resolve()` and check it's within project root

```python
def _validate_cache_root(cache_root: Path, project_root: Path) -> Path:
    resolved = cache_root.resolve()
    if not str(resolved).startswith(str(project_root.resolve())):
        raise ValueError(f"Cache root {cache_root} escapes project boundary")
    return resolved
```

### 2. Symlink Escape in Path Validation
**Location:** `core/agent_base.py` — `_validate_path()`
**Risk:** MEDIUM — Symlinks can escape validated directory
**Fix:** Use `Path.resolve()` before boundary checks

### 3. Decentralized Path Validation
**Risk:** HIGH — Each module implements its own path checks with inconsistent rules
**Fix:** Centralize in `utils/path_security.py`:

```python
def validate_path(path: Path, *, root: Path, allow_symlinks: bool = False) -> Path:
    """Validate path is within root boundary. Resolves symlinks by default."""
    resolved = path.resolve() if not allow_symlinks else path
    root_resolved = root.resolve()
    if not str(resolved).startswith(str(root_resolved)):
        raise SecurityError(f"Path {path} escapes boundary {root}")
    return resolved
```

### 4. Hardcoded API Key in MCP Config
**Location:** MCP configuration files
**Fix:** Move to environment variable or `pydantic.SecretStr`

### 5. Silent Cache Write Failures
**Location:** `context7/kb_cache.py`
**Risk:** MEDIUM — Failed writes silently return, leading to stale cache
**Fix:** Raise on write failure or return success/failure status

## Recommendations

1. **Centralize path validation** in `utils/path_security.py`
2. **Use `pydantic.SecretStr`** for all API keys, tokens, passwords
3. **Add input validation** at system boundaries (CLI args, config values, MCP inputs)
4. **Enable Bandit** in CI pipeline (not just manual runs)
5. **Add `detect-secrets`** to pre-commit hooks
6. **File size limits** — validate file sizes before reading into memory
7. **Subprocess hardening** — always use `shell=False`, set timeouts, validate args

## Security Testing

```bash
# Run security scan
tapps-agents simple-mode security-review --file <path>

# Bandit scan
bandit -r tapps_agents/ -c pyproject.toml

# Secret detection
detect-secrets scan --all-files
```
