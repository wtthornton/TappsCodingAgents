# Python Packaging: Building and Publishing

**Source:** [Building and Publishing - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/section-build-and-publish/)

**Canonical URL:** https://packaging.python.org/en/latest/guides/section-build-and-publish/

This document is the authoritative reference for building and publishing Python packages. Keep it in Context7 cache and RAG for packaging, PyPI, and release workflows.

## Section overview

The Building and Publishing section of the Python Packaging User Guide covers:

- **Writing your pyproject.toml** – [writing-pyproject-toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- **Packaging and distributing projects** – [distributing-packages-using-setuptools](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- **Dropping support for older Python versions**
- **Packaging binary extensions**
- **Packaging namespace packages**
- **Creating and packaging command-line tools**
- **Creating and discovering plugins**
- **Using TestPyPI**
- **Making a PyPI-friendly README**
- **Publishing package distribution releases using GitHub Actions CI/CD workflows**
- **How to modernize a setup.py based project?**
- **Licensing examples and user scenarios**

## Key concepts

- Use **pyproject.toml** (PEP 517/518) as the single source of truth for project metadata and build system.
- **Build** with `python -m build` (sdist + wheel).
- **Publish** to PyPI via Twine or GitHub Actions; use TestPyPI for testing first.
- PyPA maintains the [Python Packaging User Guide](https://packaging.python.org/) and specifications.

## For Context7 and RAG

- **Library/topic for Context7:** If Context7 indexes PyPA docs, use library names such as `packaging` or `python-packaging-guide` and topics `building`, `publishing`, `pypi`, `github-actions`.
- **Prepopulate:** Run `python scripts/prepopulate_context7_cache.py --libraries packaging` or `tapps-agents reviewer docs packaging "building and publishing"` to prime the project Context7 cache.
- **This file:** Ensures the canonical URL and section outline are in project knowledge for RAG retrieval.
