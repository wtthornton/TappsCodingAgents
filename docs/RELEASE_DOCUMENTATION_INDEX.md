# Release & Deployment Documentation Index

## 📘 Canonical Documentation

**Primary Guides:**
- **[RELEASE_GUIDE.md](RELEASE_GUIDE.md)** - **Canonical release process guide** (comprehensive)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - **Canonical deployment guide** (installation & usage)
- **[RELEASE_QUICK_REFERENCE.md](RELEASE_QUICK_REFERENCE.md)** - Quick command reference

**Critical Warnings:**
- **[RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md)** - ⚠️ **CRITICAL:** Version tag requirements

## 📜 Historical Documents

Historical release documentation has been removed. All current release processes are documented in the canonical guides above.

## 🔧 Scripts

**Release Scripts:**
- `scripts/create_github_release.ps1` - **Canonical release script** (with version validation)
- `scripts/update_version.ps1` - Version update utility
- `scripts/validate_release_readiness.ps1` - Pre-release validation
- `scripts/verify_release_package.ps1` - Package verification
- `scripts/upload_to_pypi.ps1` - PyPI upload utility

**Note:** There is only **one** release script: `scripts/create_github_release.ps1`


## Quick Links

- **How to create a release:** [RELEASE_GUIDE.md](RELEASE_GUIDE.md#method-2-manual-release-script-windows)
- **Version tag requirements:** [RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md)
- **Quick commands:** [RELEASE_QUICK_REFERENCE.md](RELEASE_QUICK_REFERENCE.md)
- **Troubleshooting:** [RELEASE_GUIDE.md](RELEASE_GUIDE.md#troubleshooting)

