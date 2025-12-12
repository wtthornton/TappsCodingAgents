# Contributing to TappsCodingAgents

Thank you for your interest in contributing to TappsCodingAgents! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Issues

**Before creating an issue:**
- Check existing issues to avoid duplicates
- Use clear, descriptive titles
- Provide reproduction steps
- Include relevant code examples
- Specify your environment (OS, Python version, etc.)

**Issue Types:**
- 🐛 **Bug Report**: Something isn't working
- 💡 **Feature Request**: New functionality
- 📚 **Documentation**: Documentation improvements
- ❓ **Question**: Need help understanding something

### Suggesting Enhancements

**For feature requests:**
1. Open an issue with the `enhancement` label
2. Describe the use case and expected behavior
3. Explain why this would be valuable
4. Consider implementation approach (if possible)

### Pull Requests

**Before submitting a PR:**

1. **Fork the repository** and create a branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Follow coding standards:**
   - Use type hints for all functions
   - Follow PEP 8 style guide
   - Write docstrings for all public functions/classes
   - Keep functions focused and single-purpose

3. **Write tests:**
   - Add unit tests for new functionality
   - Ensure all tests pass: `python -m pytest`
   - Aim for 80%+ code coverage

4. **Update documentation:**
   - Update relevant documentation files
   - Add examples for new features
   - Update CHANGELOG.md

5. **Run quality checks:**
   ```bash
   # Lint code
   ruff check .
   
   # Type checking
   mypy tapps_agents/
   
   # Run tests
   python -m pytest
   ```

6. **Commit messages:**
   - Use clear, descriptive commit messages
   - Reference issues: `Fix #123: Description`
   - Follow conventional commits format when possible

**PR Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No linting errors
- [ ] Type checking passes
- [ ] PR description explains changes

## Development Setup

### Prerequisites

- Python 3.13+ (recommended: latest stable Python)
- Git
- (Optional) Ollama for local LLM testing

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wtthornton/TappsCodingAgents.git
   cd TappsCodingAgents
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Install development tools:**
   ```bash
   pip install ruff mypy pytest pytest-cov
   ```

5. **Run tests:**
   ```bash
   python -m pytest
   ```

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Maximum line length: **100 characters**
- Use **black** or **ruff format** for formatting

### Code Organization

- **One class per file** (when possible)
- **Single responsibility** principle
- **DRY** (Don't Repeat Yourself)
- **Clear naming** conventions

### Type Hints

Always use type hints:

```python
from typing import Dict, List, Optional, Any
from pathlib import Path

def process_file(file_path: Path, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process a file and return results."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_score(code: str, weights: Dict[str, float]) -> float:
    """
    Calculate code quality score.
    
    Args:
        code: Source code to analyze
        weights: Scoring weights for different metrics
    
    Returns:
        Overall quality score (0-100)
    
    Raises:
        ValueError: If weights don't sum to 1.0
    """
    pass
```

### Error Handling

- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately

```python
from tapps_agents.core.exceptions import AgentActivationError

try:
    agent.activate()
except AgentActivationError as e:
    logger.error(f"Failed to activate agent: {e}")
    raise
```

## Testing Guidelines

### Writing Tests

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **Test naming**: `test_<functionality>_<scenario>`

```python
import pytest
from pathlib import Path

def test_calculate_score_returns_valid_range():
    """Test that score is always between 0 and 100."""
    scorer = CodeScorer()
    score = scorer.score_file(Path("test.py"), "def test(): pass")
    assert 0 <= score["overall_score"] <= 100

def test_calculate_score_raises_error_for_invalid_file():
    """Test that non-existent files raise FileNotFoundError."""
    scorer = CodeScorer()
    with pytest.raises(FileNotFoundError):
        scorer.score_file(Path("nonexistent.py"), "")
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_scoring.py

# Run with coverage
pytest --cov=tapps_agents --cov-report=html

# Run with verbose output
pytest -v
```

## Documentation Standards

### Code Documentation

- **Docstrings** for all public APIs
- **Comments** for complex logic
- **Type hints** as documentation

### User Documentation

- **Clear examples** for all features
- **Getting started** guides
- **API reference** documentation
- **Troubleshooting** guides

### Documentation Format

- Use **Markdown** for documentation
- Include **code examples**
- Add **diagrams** where helpful
- Keep **up-to-date** with code changes

## Agent Development

### Creating New Agents

1. Inherit from `BaseAgent`
2. Implement required methods:
   - `activate()`: Setup and validation
   - `get_commands()`: Return available commands
   - `run()`: Execute commands
3. Add configuration in `config.py`
4. Write comprehensive tests
5. Add documentation

### Adding Commands

Commands use star-prefixed format:

```python
def get_commands(self) -> List[Dict[str, str]]:
    return [
        {"*mycommand": "Description of command"},
        {"*another-command": "Another description"}
    ]
```

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
type: Short description (50 chars max)

Longer explanation if needed. Wrap at 72 characters.
Reference issues: Fix #123

- Bullet point for changes
- Another bullet point
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

## Review Process

1. **Automated checks** run on PR creation
2. **Code review** by maintainers
3. **Feedback** and requested changes
4. **Approval** and merge

## Getting Help

- **Documentation**: Check [docs/](docs/) directory
- **Issues**: Search existing issues
- **Discussions**: Use GitHub Discussions (if available)
- **Email**: Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to TappsCodingAgents!** 🎉

