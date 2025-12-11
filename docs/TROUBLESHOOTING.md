# Troubleshooting Guide

**Version**: 1.6.1  
**Last Updated**: December 2025

## Common Issues and Solutions

### Installation Issues

#### Problem: `pip install` fails

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Check Python version (requires 3.10+)
python --version
```

#### Problem: Missing dependencies

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Install optional dependencies
pip install ruff mypy jscpd pip-audit pipdeptree
```

### Configuration Issues

#### Problem: Configuration file not found

**Error:**
```
FileNotFoundError: project_config.yaml not found
```

**Solution:**
1. Create config file from template:
   ```bash
   cp templates/default_config.yaml project_config.yaml
   ```
2. Or specify custom path:
   ```bash
   export TAPPS_CONFIG_PATH=/path/to/config.yaml
   ```

#### Problem: Invalid YAML configuration

**Error:**
```
yaml.YAMLError: mapping values are not allowed here
```

**Solution:**
- Validate YAML syntax
- Check indentation (use spaces, not tabs)
- Verify required fields are present
- Use a YAML validator online

### Agent Activation Issues

#### Problem: Agent activation fails

**Error:**
```
AgentActivationError: Failed to activate agent
```

**Solution:**
1. Check project root path:
   ```python
   from pathlib import Path
   print(Path(".").absolute())  # Verify correct directory
   ```

2. Verify configuration:
   ```bash
   python -m tapps_agents.cli --help
   ```

3. Check file permissions:
   ```bash
   ls -la project_config.yaml
   ```

#### Problem: Path validation errors

**Error:**
```
ValueError: Path validation failed
```

**Solution:**
- Ensure paths exist
- Check path permissions
- Verify path format (use forward slashes)
- Use absolute paths if relative paths fail

### Model Provider Issues

#### Problem: Ollama not found

**Error:**
```
ConnectionError: Could not connect to Ollama
```

**Solution:**
1. Install Ollama:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Or download from https://ollama.ai
   ```

2. Start Ollama:
   ```bash
   ollama serve
   ```

3. Pull model:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```

#### Problem: Cloud API key errors

**Error:**
```
AuthenticationError: Invalid API key
```

**Solution:**
1. Verify API key:
   ```bash
   echo $ANTHROPIC_API_KEY  # or $OPENAI_API_KEY
   ```

2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   ```

3. Check API key format and permissions

### Quality Analysis Issues

#### Problem: Ruff not found

**Error:**
```
FileNotFoundError: ruff command not found
```

**Solution:**
```bash
# Install Ruff
pip install ruff

# Verify installation
ruff --version

# Or use npx if installed via npm
npx ruff --version
```

#### Problem: mypy type checking errors

**Error:**
```
mypy.errors.ConfigError: Could not find config file
```

**Solution:**
1. Create `mypy.ini`:
   ```ini
   [mypy]
   python_version = 3.10
   warn_return_any = True
   ```

2. Or configure in `pyproject.toml`:
   ```toml
   [tool.mypy]
   python_version = "3.10"
   warn_return_any = true
   ```

#### Problem: ESLint not found (TypeScript)

**Error:**
```
FileNotFoundError: eslint command not found
```

**Solution:**
```bash
# Install ESLint
npm install -g eslint

# Or use npx
npx --yes eslint --version

# Verify installation
eslint --version
```

#### Problem: TypeScript compiler not found

**Error:**
```
FileNotFoundError: tsc command not found
```

**Solution:**
```bash
# Install TypeScript
npm install -g typescript

# Or use npx
npx --yes tsc --version

# Verify installation
tsc --version
```

### Context7 Issues

#### Problem: Context7 cache not working

**Error:**
```
Context7Error: Cache initialization failed
```

**Solution:**
1. Check cache directory permissions:
   ```bash
   ls -la ~/.tapps-agents/context7-cache/
   ```

2. Recreate cache directory:
   ```bash
   rm -rf ~/.tapps-agents/context7-cache/
   mkdir -p ~/.tapps-agents/context7-cache/
   ```

3. Verify configuration:
   ```yaml
   context7:
     cache_dir: "~/.tapps-agents/context7-cache"
     enable_cache: true
   ```

#### Problem: Context7 API rate limits

**Error:**
```
RateLimitError: API rate limit exceeded
```

**Solution:**
- Enable KB cache (reduces API calls)
- Increase cache staleness duration
- Use batch operations
- Contact Context7 for higher limits

### Report Generation Issues

#### Problem: Report generation fails

**Error:**
```
ReportGenerationError: Failed to generate report
```

**Solution:**
1. Check output directory permissions:
   ```bash
   mkdir -p reports/quality
   chmod 755 reports/quality
   ```

2. Verify Jinja2 templates:
   ```bash
   python -c "import jinja2; print(jinja2.__version__)"
   ```

3. Check for required dependencies:
   ```bash
   pip install jinja2 plotly  # Optional but recommended
   ```

### Performance Issues

#### Problem: Slow agent execution

**Solution:**
1. Use local LLM (Ollama) instead of cloud:
   ```yaml
   model:
     provider: "local"
   ```

2. Enable caching:
   ```yaml
   context7:
     enable_cache: true
     cache_ttl: 86400  # 24 hours
   ```

3. Reduce analysis scope:
   - Analyze specific files instead of entire project
   - Use incremental analysis

#### Problem: High memory usage

**Solution:**
1. Limit concurrent operations:
   ```yaml
   agents:
     reviewer:
       max_concurrent_files: 10
   ```

2. Clear cache periodically:
   ```bash
   python -m tapps_agents.cli context7 cleanup
   ```

3. Process files in batches

### Testing Issues

#### Problem: Tests fail

**Error:**
```
pytest failures
```

**Solution:**
1. Run tests with verbose output:
   ```bash
   pytest -v
   ```

2. Run specific test:
   ```bash
   pytest tests/unit/test_scoring.py::TestCodeScorer
   ```

3. Check test dependencies:
   ```bash
   pip install pytest pytest-cov pytest-asyncio
   ```

#### Problem: Async test failures

**Error:**
```
RuntimeError: Event loop is closed
```

**Solution:**
Use `pytest-asyncio`:
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Multi-Language Issues

#### Problem: TypeScript files not analyzed

**Solution:**
1. Verify TypeScript support enabled:
   ```yaml
   quality_tools:
     typescript_enabled: true
   ```

2. Install TypeScript tools:
   ```bash
   npm install -g typescript eslint
   ```

3. Check file extensions (`.ts`, `.tsx`, `.js`, `.jsx`)

### Dependency Issues

#### Problem: pip-audit not found

**Error:**
```
FileNotFoundError: pip-audit command not found
```

**Solution:**
```bash
pip install pip-audit

# Verify
pip-audit --version
```

#### Problem: pipdeptree not found

**Error:**
```
FileNotFoundError: pipdeptree command not found
```

**Solution:**
```bash
pip install pipdeptree

# Verify
pipdeptree --version
```

## Getting Help

### Debug Mode

Enable verbose logging:
```bash
export TAPPS_LOG_LEVEL=DEBUG
python -m tapps_agents.cli reviewer review src/main.py
```

### Check Logs

View log files:
```bash
tail -f /var/log/tapps-agents.log
```

Or if using file logging:
```bash
cat logs/tapps-agents.log
```

### Common Debug Commands

```bash
# Check installation
python -c "import tapps_agents; print(tapps_agents.__version__)"

# List available agents
python -m tapps_agents.cli --help

# Test agent activation
python -c "from tapps_agents.agents.reviewer.agent import ReviewerAgent; import asyncio; asyncio.run(ReviewerAgent().activate())"

# Verify configuration
python -c "from tapps_agents.core.config import ProjectConfig; print(ProjectConfig.from_yaml('project_config.yaml'))"
```

### Reporting Issues

If you encounter an issue not covered here:

1. **Check existing issues**: Search GitHub issues
2. **Collect information**:
   - Python version: `python --version`
   - OS and version
   - Error messages and stack traces
   - Configuration (redact sensitive data)
3. **Open an issue**: Use the issue template
4. **Include logs**: Share relevant log output

## Prevention Tips

1. **Keep dependencies updated:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Regular security scanning:**
   ```bash
   python -m tapps_agents.cli ops check-vulnerabilities
   ```

3. **Validate configuration:**
   ```bash
   python -c "from tapps_agents.core.config import ProjectConfig; ProjectConfig.from_yaml('project_config.yaml')"
   ```

4. **Test before production:**
   - Run in development environment first
   - Test with sample files
   - Verify expected behavior

---

**Related Documentation:**
- [Configuration Guide](CONFIGURATION.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Security Policy](../SECURITY.md)

