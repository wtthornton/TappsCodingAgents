# Release Notes - TappsCodingAgents v1.6.1

**Release Date:** December 10, 2025  
**Version:** 1.6.1

## 🚀 Major Improvements

### Test Suite Performance Optimization
- **15-30x faster test execution** for daily development
- Coverage disabled by default (can be enabled with `--cov` flag)
- Unit tests only by default (run all tests with `-m ""`)
- Progress indicators added to long-running tests
- Comprehensive performance guide added

**Performance Comparison:**
- Before: ~120-240 seconds (all tests with coverage)
- After: ~4-8 seconds (unit tests only, no coverage)

### Dependency Updates
All dependencies updated to latest 2025 stable versions:
- **pytest**: 8.4.2 → 9.0.2 (major version upgrade)
- **pytest-asyncio**: 0.26.0 → 1.3.0 (major version upgrade)
- **pytest-httpx**: 0.35.0 → 0.36.0 (pytest 9.x compatibility)
- **coverage**: 7.10.6 → 7.13.0
- **black**: 25.1.0 → 25.12.0
- **ruff**: 0.14.5 → 0.14.8
- **mypy**: 1.18.1 → 1.19.0
- **pylint**: 4.0.1 → 4.0.4

## 🐛 Bug Fixes

- Resolved dependency conflict with pytest-httpx for pytest 9.x compatibility
- Fixed Unicode encoding issues in test progress indicators for Windows compatibility
- Updated GitHub repository URLs to wtthornton/TappsCodingAgents
- Fixed project context reference in README.md

## 📚 Documentation

- Added comprehensive [Test Performance Guide](docs/TEST_PERFORMANCE_GUIDE.md)
- Updated all documentation to reflect latest dependency versions
- Updated project structure in README.md
- Updated Skills installation instructions across all documentation

## 📦 Installation

### From Wheel (Recommended)
```bash
pip install dist/tapps_agents-1.6.1-py3-none-any.whl
```

### From Source
```bash
pip install dist/tapps_agents-1.6.1.tar.gz
```

### From PyPI (if published)
```bash
pip install tapps-agents==1.6.1
```

## 🧪 Testing

### Fast Development Testing (Default)
```bash
pytest tests/  # Unit tests only, ~4-8 seconds
```

### Full Test Suite
```bash
pytest tests/ -m ""  # All tests (unit + integration)
```

### With Coverage
```bash
pytest tests/ --cov=tapps_agents --cov-report=term
```

### Parallel Execution (Optional)
```bash
pip install pytest-xdist
pytest tests/ -n auto  # Auto-detect CPU cores
```

## 📊 Test Results

- ✅ **305 tests passing** (unit + integration)
- ✅ **0 failures**
- ✅ **pytest 9.x compatibility verified**
- ✅ **All async tests working correctly**

## 🔧 Configuration Changes

### pytest.ini Updates
- Coverage disabled by default
- Unit tests only by default (`-m unit`)
- Added comprehensive documentation comments

### .gitignore Updates
- Added session JSON files pattern
- Added MagicMock test artifacts
- Coverage.xml already ignored

## 🎯 What's Next

- Monitor for any issues with pytest 9.x
- Consider adding pytest-xdist to requirements for parallel execution
- Continue optimizing test suite performance

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## 🔗 Links

- **Repository**: https://github.com/wtthornton/TappsCodingAgents
- **Documentation**: [docs/](docs/)
- **Test Performance Guide**: [docs/TEST_PERFORMANCE_GUIDE.md](docs/TEST_PERFORMANCE_GUIDE.md)

---

**Note**: This release focuses on test suite optimization and dependency updates. All core functionality remains stable and backward compatible.

