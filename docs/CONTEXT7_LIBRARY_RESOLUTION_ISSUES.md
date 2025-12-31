# Context7 Library Resolution Issues

## Problem Description

When using TappsCodingAgents in other projects, you may see warnings like:

```
Context7 lookup failed for library 'pydantic' (topic: overview): Could not resolve library ID for 'pydantic'. This is required to fetch documentation from Context7 API. Library resolution may have failed or returned no matches.. Continuing without Context7 documentation.
```

## Why This Happens

The reviewer agent automatically detects libraries from your code (using import statements) and tries to fetch Context7 documentation to provide better code quality feedback. However, this lookup can fail for several reasons:

### 1. Context7 Not Configured

**Symptoms:**
- All library lookups fail
- Error mentions "Context7 not available" or "MCP tools not found"

**Solution:**
- **Option A (Recommended)**: Configure Context7 MCP server in Cursor:
  1. Run `tapps-agents init` - this automatically sets up `.cursor/mcp.json`
  2. Or manually create `.cursor/mcp.json`:
  ```json
  {
    "mcpServers": {
      "Context7": {
        "command": "npx",
        "args": ["-y", "@context7/mcp-server"],
        "env": {
          "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
        }
      }
    }
  }
  ```
  3. Set `CONTEXT7_API_KEY` environment variable with your Context7 API key

- **Option B**: Use direct HTTP fallback (requires API key):
  1. Set `CONTEXT7_API_KEY` environment variable
  2. The system will automatically use HTTP fallback if MCP is not available

### 2. Library Not Found in Context7

**Symptoms:**
- Specific library lookups fail (e.g., 'schema', 'pydantic')
- Library name might not match Context7's database

**Common Issues:**
- **'schema' library**: This is often a false positive. The library detector might detect `from schema import ...` but:
  - 'schema' might not be a real Python package
  - Or it might be part of another package (e.g., `marshmallow` or `pydantic`)
  - Context7 might not have documentation for it

- **'pydantic' library**: Pydantic is a real library, but:
  - Context7 might use a different name (e.g., `/pydantic/pydantic`)
  - The library might not be in Context7's database yet
  - Library resolution might need more specific matching

**Solution:**
- These warnings are **non-fatal** - the review continues without Context7 documentation
- The reviewer agent will still work and provide code quality scores
- Context7 documentation is an **enhancement**, not a requirement

### 3. False Positive Library Detection

**Symptoms:**
- Libraries like 'schema' are detected but don't exist in Context7
- These might be local modules or false positives from import parsing

**Solution:**
- This is expected behavior - the library detector errs on the side of detecting more libraries
- False positives are handled gracefully - lookup fails silently and review continues
- No action needed - these warnings can be ignored

## Impact on Review Quality

**Important:** These Context7 lookup failures do NOT affect the core review functionality:

✅ **Still Works:**
- Code quality scoring (5 metrics: complexity, security, maintainability, test coverage, performance)
- Static analysis (Ruff linting, mypy type checking)
- Security scanning
- Code review feedback

❌ **What's Missing:**
- Library-specific best practices from Context7
- API correctness suggestions based on Context7 documentation
- Proactive suggestions for library-specific patterns

## How to Verify Context7 Setup

### Check if Context7 is Configured

```bash
# Check if MCP config exists
cat .cursor/mcp.json

# Check if API key is set (for HTTP fallback)
echo $CONTEXT7_API_KEY  # Linux/Mac
echo %CONTEXT7_API_KEY%  # Windows
```

### Test Context7 Resolution

```bash
# Try resolving a well-known library
tapps-agents reviewer docs fastapi

# Or use Context7 commands directly
tapps-agents context7-resolve fastapi
tapps-agents context7-docs fastapi overview
```

### Expected Results

**If Context7 is configured correctly:**
```
✅ Library resolved: /vercel/next.js
✅ Documentation retrieved (source: api/cache)
```

**If Context7 is not configured:**
```
⚠️ Context7 not available: MCP tools not found and CONTEXT7_API_KEY not set
ℹ️ Continuing without Context7 documentation
```

## Configuration Options

### Disable Context7 (If Not Needed)

If you don't want Context7 documentation lookups, you can disable it:

**Option 1: Disable in config**
Edit `.tapps-agents/config.yaml`:
```yaml
context7:
  enabled: false
```

**Option 2: Don't configure Context7**
Simply don't set up the MCP server or API key. The system will automatically skip Context7 lookups if not available.

### Suppress Warnings (Keep Functionality)

If you want Context7 enabled but want to suppress warning messages, set log level to ERROR:

```bash
export TAPPS_LOG_LEVEL=ERROR  # Linux/Mac
set TAPPS_LOG_LEVEL=ERROR      # Windows
```

## Troubleshooting Steps

### Step 1: Verify Context7 Setup

```bash
# Run doctor command to check environment
tapps-agents doctor

# Should show Context7 status
```

### Step 2: Test Single Library Lookup

```bash
# Try to resolve a well-known library
tapps-agents context7-resolve react

# If this fails, Context7 is not configured correctly
```

### Step 3: Check Library Names

If specific libraries fail:
- Verify the library name is correct
- Check if the library exists in Context7 database
- Try alternative names (e.g., 'pydantic' vs '/pydantic/pydantic')

### Step 4: Review Logs

Check detailed logs for resolution errors:
```bash
# Enable verbose logging
export TAPPS_LOG_LEVEL=DEBUG

# Run review again
tapps-agents reviewer review your_file.py

# Check logs for detailed error messages
```

## Common Library Detection Issues

### 'schema' Library

**Why detected:**
- Code contains `from schema import ...` or `import schema`
- Library detector assumes it's a third-party library

**Why fails:**
- 'schema' might be a local module, not a package
- Or it's part of another package (marshmallow, pydantic)
- Context7 might not have documentation for it

**Action:**
- **No action needed** - this is a false positive, warnings can be ignored
- Or improve library detection to filter out local modules (future enhancement)

### 'pydantic' Library

**Why detected:**
- Code imports `from pydantic import BaseModel` or similar
- This is a real third-party library

**Why fails:**
- Context7 might not have pydantic in its database
- Or library resolution needs exact name matching

**Action:**
- Check if Context7 has pydantic: `tapps-agents context7-resolve pydantic`
- If not found, this is expected - Context7 doesn't have all libraries
- Review will still work without Context7 documentation

## Best Practices

1. **Always configure Context7 if available** - It provides valuable library-specific guidance
2. **Ignore false positive warnings** - Libraries like 'schema' that fail lookup are often false positives
3. **Check Context7 coverage** - Not all libraries are in Context7's database (this is normal)
4. **Use verbose logging** - If you need to debug issues, enable DEBUG logging

## Summary

**These warnings are normal and expected:**
- ✅ Reviewer agent continues to work
- ✅ Code quality scoring still functions
- ✅ Review feedback is still provided
- ❌ Only missing: Library-specific best practices from Context7

**When to take action:**
- If ALL libraries fail → Configure Context7 MCP server or API key
- If specific libraries fail → Check if library exists in Context7 (may not)
- If warnings are too noisy → Adjust log level or disable Context7

**When to ignore:**
- False positives like 'schema' (local modules, part of other packages)
- Libraries not in Context7 database (normal - Context7 doesn't have everything)
- Non-critical lookups (review still works without Context7)

## Related Documentation

- [Context7 Integration Guide](TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Context7 KB-First Lookup](.bmad-core/tasks/context7-kb-lookup.md)

