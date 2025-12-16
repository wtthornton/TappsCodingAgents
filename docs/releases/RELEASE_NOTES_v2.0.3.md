# Release Notes - TappsCodingAgents v2.0.3

**Release Date:** December 16, 2025  
**Version:** 2.0.3  
**Tag:** v2.0.3

## 🐛 Bug Fixes

### Fixed RAG Knowledge Base Directory Creation Error

**Issue:** When enabling RAG for an expert, entering a URL as the primary domain name (e.g., `https://www.home-assistant.io/docs/`) caused an `OSError: [WinError 123]` on Windows systems. The error occurred because URLs contain characters that are invalid in Windows filenames (`:`, `/`, etc.).

**Solution:**
- Added `sanitize_domain_for_path()` utility function in `tapps_agents/experts/domain_utils.py`
- Automatically extracts hostname and path from URLs and sanitizes them for use as directory names
- Replaces invalid filename characters with hyphens for cross-platform compatibility
- Updated `setup_wizard.py` and `base_expert.py` to use sanitized domain names when creating knowledge base directories

**Impact:** Users can now enter URLs as domain names when setting up experts, and the system will automatically create valid directory names. For example:
- Input: `https://www.home-assistant.io/docs/`
- Directory created: `home-assistant.io-docs`

## 📦 Installation

```bash
pip install tapps-agents==2.0.3
```

## 📝 Full Changelog

See `CHANGELOG.md` for complete details.

