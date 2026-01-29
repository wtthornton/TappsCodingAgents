# Bug #14: bd create fails with 'issue_prefix config is missing'

**Status**: Under Investigation
**Issue**: https://github.com/[org]/TappsCodingAgents/issues/14
**Date**: 2026-01-29
**Severity**: Medium (blocks bd create, but GitHub integration works)

---

## Problem Statement

When running `bd create "Title"`, the command fails with:

```
Error: database not initialized: issue_prefix config is missing (run 'bd init --prefix <prefix>' first)
```

**Despite:**
- ✅ Database is initialized (`.beads/beads.db` exists)
- ✅ Configuration is set (`issue_prefix = TappsCodingAgents` in database)
- ✅ Other bd commands work fine (`bd list`, `bd ready`, `bd status`)
- ✅ Existing issues all have correct prefix (`TappsCodingAgents-XXX`)

---

## Investigation Findings

### Configuration Status

**Database Config:**
```sql
SELECT * FROM config WHERE key LIKE '%issue%prefix%';
-- Results:
-- issue-prefix: TappsCodingAgents
-- issue_prefix: TappsCodingAgents
```

Both hyphenated and underscored versions are present in the database.

**Config File (`.beads/config.yaml`):**
```yaml
# issue-prefix: ""  (commented out)
```

**Config Retrieval:**
```bash
$ bd config get issue-prefix
TappsCodingAgents

$ bd config list | grep issue
issue-prefix = TappsCodingAgents
issue_prefix = TappsCodingAgents
```

### Attempted Solutions

1. ✅ **Set config with hyphens**: `bd config set issue-prefix "TappsCodingAgents"`
   - Result: Still fails

2. ✅ **Set config with underscores**: Already set to `TappsCodingAgents`
   - Result: Still fails

3. ✅ **Try with --force flag**: `bd create "Title" --force`
   - Result: Still fails

4. ✅ **Try with --no-daemon**: `bd create "Title" --no-daemon`
   - Result: Still fails

5. ✅ **Restart daemon**: `bd daemon stop/start`
   - Result: Daemon commands require workspace path argument (different issue)

6. ✅ **Check database directly**: SQLite query confirms config exists
   - Result: Config is present and correct

### Environment Details

**bd Version:**
```
bd version 0.48.0 (dev)
```

**Binary Location:**
```
/c/cursor/HomeIQ/tools/bd/bd
```

**Note**: bd binary is located in a different repository (`HomeIQ`), not in `TappsCodingAgents`. This may indicate a version mismatch or shared installation issue.

**Database:**
```
.beads/beads.db (282 KB, 5 issues)
```

**Working Commands:**
- `bd list` ✅
- `bd ready` ✅
- `bd status` ✅
- `bd config get/set` ✅

**Failing Commands:**
- `bd create "Title"` ❌
- `bd init --prefix X` ❌ (says already initialized)

---

## Root Cause Analysis

### Hypothesis 1: Initialization Check Logic

The error message "database not initialized" suggests `bd create` performs a different initialization check than other commands. Possible reasons:

1. **Missing metadata field**: bd create may check for a specific initialization marker beyond just `issue_prefix` config
2. **Version compatibility**: bd 0.48.0 (dev) may have different requirements than the database schema
3. **Daemon communication**: bd create may use daemon RPC that has different config resolution logic

### Hypothesis 2: Binary Version Mismatch

**Evidence:**
- bd binary is in `/c/cursor/HomeIQ/tools/bd/bd` (different repo)
- Version is `0.48.0 (dev)` (development version)
- Database may have been created with a different bd version

**Implication:**
- May need to update bd binary to match database schema
- Or reinitialize database with current bd version

### Hypothesis 3: Prefix Detection from Title

**Evidence:**
- Error shows: `⚠ Creating issue with 'Test' prefix in production database`
- bd seems to extract "Test" from title "Test issue for bug #14"
- This suggests bd is trying to infer prefix from title when database lookup fails

**Implication:**
- Database config lookup is failing internally
- Fallback logic tries to extract prefix from title
- When that also fails, throws "config is missing" error

---

## Workarounds

### ✅ Workaround 1: Use GitHub Integration

Create issues directly on GitHub, then sync with bd:

```bash
# Create issue on GitHub
gh issue create --title "Title" --body "Description" --label "enhancement"

# Sync to beads database
bd sync

# Or use bd GitHub integration
bd create --external-ref "gh-XXX" "Title from GitHub issue gh-XXX"
```

**Pros:**
- Fully functional
- Issues visible on GitHub immediately
- No bd create dependency

**Cons:**
- Requires GitHub access
- Extra step (create then sync)

### ⚠️ Workaround 2: Directly Insert into Database (Not Recommended)

```bash
# NOT RECOMMENDED - may corrupt database
python scripts/insert_issue.py "Title" "Description"
```

**Pros:**
- Bypasses bd create

**Cons:**
- Risky (may corrupt database)
- Doesn't trigger proper ID generation
- No validation

### ⚠️ Workaround 3: Reinitialize Database

```bash
# DANGER: DATA LOSS
# Backup first!
cp .beads/beads.db .beads/beads.db.backup
rm -rf .beads
bd init --prefix TappsCodingAgents
```

**Pros:**
- May fix initialization issue

**Cons:**
- **DESTROYS ALL EXISTING ISSUES**
- Requires re-import from Git history or JSONL
- High risk

---

## Recommended Actions

### Short-Term (Immediate)

1. ✅ **Use GitHub Integration** as primary workflow
   - Create issues with `gh issue create`
   - Use `bd sync` to import to local database
   - Continue using `bd list`, `bd ready` for local workflow

2. ✅ **Document this bug** in GitHub issue #14
   - Include all investigation findings
   - Request bd maintainer input

3. ✅ **Check bd version compatibility**
   - Verify bd version matches database schema version
   - Consider updating bd binary

### Medium-Term

1. **Update bd binary** to latest stable version
   - Check if newer version fixes this issue
   - Test in isolated environment first

2. **Engage bd maintainers**
   - Report to beads repository
   - Provide database schema for debugging
   - Share bd version and error logs

3. **Create test database** to reproduce
   ```bash
   BEADS_DB=/tmp/test.db bd init --prefix test
   BEADS_DB=/tmp/test.db bd create "Test issue"
   # Does this work?
   ```

### Long-Term

1. **Consider alternative task management**
   - If bd continues to have issues
   - Evaluate GitHub Projects, Linear, or Jira integration
   - Maintain bd for local workflow only

---

## Testing Checklist

When a fix is proposed, test:

- [ ] `bd create "Simple title"` works
- [ ] `bd create "Title with 'special' chars"` works
- [ ] Created issues have correct prefix (`TappsCodingAgents-XXX`)
- [ ] `bd list` shows newly created issue
- [ ] `bd ready` includes new issue if not blocked
- [ ] JSONL export includes new issue
- [ ] Daemon mode works (without --no-daemon)
- [ ] Direct mode works (with --no-daemon)

---

## Related Issues

- **Issue #14**: This bug
- **Beads GitHub**: [Report upstream if needed]

---

## ✅ SOLUTION FOUND

### Root Cause

**Using wrong bd binary!**

| Version | Path | Status |
|---------|------|--------|
| 0.48.0 (dev) ❌ | `/c/cursor/HomeIQ/tools/bd/bd` | **BROKEN** - has initialization bug |
| 0.47.1 ✅ | `/c/cursor/TappsCodingAgents/tools/bd/bd` | **WORKS PERFECTLY!** |
| 0.48.0 (dev) ❌ | `/c/Users/tappt/go/bin/bd` | Also broken (same version) |

The system was using bd 0.48.0 (dev) from HomeIQ which has a bug in database initialization detection. The local TappsCodingAgents bd 0.47.1 works correctly.

### The Fix

**Run the existing PATH configuration script:**

```powershell
# Option 1: Current session only
.\scripts\set_bd_path.ps1

# Option 2: Persistent (recommended)
.\scripts\set_bd_path.ps1 -Persist
```

This adds `tools\bd` to the beginning of PATH, ensuring the working bd 0.47.1 takes priority.

### Verification

```bash
# 1. Check version (should show 0.47.1)
bd version
# Expected: bd version 0.47.1 (279192c5: HEAD@279192c5fbf8)

# 2. Test create
bd create "Bug #14 fixed - testing local bd"
# Expected: ✓ Created issue: TappsCodingAgents-XXX

# 3. Verify it's listed
bd list | head -5
```

### Test Result

**SUCCESS!** Local bd 0.47.1 creates issues correctly:

```
$ /c/cursor/TappsCodingAgents/tools/bd/bd create "Test issue for bug #14 - local bd version"
⚠ Creating issue with 'Test' prefix in production database.
  For testing, consider using: BEADS_DB=/tmp/test.db ./bd create "Test issue"
✓ Created issue: TappsCodingAgents-uc1
  Title: Test issue for bug #14 - local bd version
  Priority: P2
  Status: open
```

---

## Status Updates

### 2026-01-29 (RESOLVED)

**Root Cause Identified:**
- System was using bd 0.48.0 (dev) from different repository (HomeIQ)
- bd 0.48.0 has a bug in initialization check logic
- Local TappsCodingAgents bd 0.47.1 works perfectly

**Solution:**
- ✅ Use existing `set_bd_path.ps1` script to prioritize local bd
- ✅ Verified bd create works with local bd 0.47.1
- ✅ Test issue created successfully (TappsCodingAgents-uc1)

**Status**: **RESOLVED** - Working solution available

---

**Investigator**: Claude Sonnet 4.5
**Date**: 2026-01-29
**Time Spent**: ~2 hours
**Resolution**: Use local bd 0.47.1 via set_bd_path.ps1
