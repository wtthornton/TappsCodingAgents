# Release & Deployment Documentation Index

## 📘 Canonical Documentation

**Primary Guides:**
- **[RELEASE_GUIDE.md](RELEASE_GUIDE.md)** - **Canonical release process guide** (comprehensive)
- **[PYPI_DEPLOYMENT_GUIDE.md](PYPI_DEPLOYMENT_GUIDE.md)** - **PyPI deployment guide** (credentials, upload script, troubleshooting)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - **Canonical deployment guide** (installation & usage)
- **[RELEASE_QUICK_REFERENCE.md](RELEASE_QUICK_REFERENCE.md)** - Quick command reference

**Critical Warnings:**
- **[RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md)** - ⚠️ **CRITICAL:** Version tag requirements

## 📜 Historical Documents

Historical release documentation has been removed. All current release processes are documented in the canonical guides above.

## 🔧 Scripts

**GitHub Actions Workflows:**
- `.github/workflows/release.yml` — **Release**: runs on tag push (or workflow_dispatch); validates, tests, builds, creates GitHub release.
- `.github/workflows/pypi-on-release.yml` — **Publish to PyPI on Release**: runs on `release: published` (or manual `workflow_dispatch` with `tag_name`); builds from tag and uploads to PyPI. Requires `PYPI_API_TOKEN` (repo or pypi environment).

**Release Scripts:**
- `scripts/create_github_release.ps1` - **Canonical release script** (with version validation)
- `scripts/update_version.ps1` - Version update utility
- `scripts/validate_release_readiness.ps1` - Pre-release validation
- `scripts/verify_release_package.ps1` - Package verification
- `scripts/upload_to_pypi.ps1` - PyPI upload utility (local; token from `.env` or `-Token`)

**Note:** There is only **one** release script: `scripts/create_github_release.ps1`. PyPI publishing is handled by the **Publish to PyPI on Release** workflow (automatic on release; manual re-run via Actions UI or `gh workflow run "Publish to PyPI on Release" -f tag_name=vX.Y.Z`).


## Quick Links

- **How to create a release:** [RELEASE_GUIDE.md](RELEASE_GUIDE.md#method-2-manual-release-script-windows)
- **How to deploy to PyPI:** [PYPI_DEPLOYMENT_GUIDE.md](PYPI_DEPLOYMENT_GUIDE.md)
- **Version tag requirements:** [RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md)
- **Quick commands:** [RELEASE_QUICK_REFERENCE.md](RELEASE_QUICK_REFERENCE.md)
- **Troubleshooting:** [RELEASE_GUIDE.md](RELEASE_GUIDE.md#troubleshooting)

