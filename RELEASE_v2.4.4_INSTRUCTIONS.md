# Release v2.4.4 - Instructions

## Summary

All version updates and documentation have been completed. To create the GitHub release, follow these steps:

## Files Updated

✅ Version updated in:
- `tapps_agents/__init__.py` → 2.4.4
- `pyproject.toml` → 2.4.4
- `README.md` → Version badge updated
- `CHANGELOG.md` → Release notes added

✅ Release notes prepared:
- `RELEASE_NOTES_v2.4.4.md` → Complete release notes

## Steps to Create GitHub Release

### 1. Commit and Push Changes

```bash
# Stage all changes
git add .

# Commit with release message
git commit -m "Release v2.4.4: Fix CLI Help Connection Errors

- Fixed connection errors when running help commands offline
- Created static help system for all 13 agents
- 40-100x faster help command response time
- All help commands now work without network

See CHANGELOG.md for full details."

# Push to main branch
git push origin main
```

### 2. Create Git Tag

```bash
# Create annotated tag
git tag -a v2.4.4 -m "Release v2.4.4: Fix CLI Help Connection Errors

Fixed critical issue where help commands would fail with connection errors when network was unavailable. All 13 agent help commands now work offline with 40-100x faster response time."

# Push tag to GitHub
git push origin v2.4.4
```

### 3. Create GitHub Release

**Option A: Via GitHub Web Interface**
1. Go to: https://github.com/wtthornton/TappsCodingAgents/releases/new
2. Select tag: `v2.4.4`
3. Title: `v2.4.4 - Fix CLI Help Connection Errors`
4. Description: Copy content from `RELEASE_NOTES_v2.4.4.md`
5. Click "Publish release"

**Option B: Via GitHub CLI (if installed)**
```bash
gh release create v2.4.4 \
  --title "v2.4.4 - Fix CLI Help Connection Errors" \
  --notes-file RELEASE_NOTES_v2.4.4.md
```

## Release Notes Summary

**Title:** v2.4.4 - Fix CLI Help Connection Errors

**Key Points:**
- 🐛 Fixed: CLI help commands now work offline
- ✨ Added: Static help system for all 13 agents
- ⚡ Performance: 40-100x faster help commands (< 50ms)
- 📦 All 13 agents fixed

**Full Release Notes:** See `RELEASE_NOTES_v2.4.4.md`

## Verification

After release is created, verify:
1. Tag exists: https://github.com/wtthornton/TappsCodingAgents/tags
2. Release exists: https://github.com/wtthornton/TappsCodingAgents/releases
3. Version badge in README shows 2.4.4
4. CHANGELOG.md has v2.4.4 entry

## Next Steps

After release:
1. Verify PyPI package can be updated (if applicable)
2. Update any deployment configurations
3. Notify users of the fix

