# Deployment Guide

**Version**: 1.6.0  
**Last Updated**: December 2025

## Overview

This guide covers deploying TappsCodingAgents in various environments, from local development to production.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Ollama for local LLM execution
- (Optional) Docker for containerized deployment

## Local Deployment

### Installation

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
   ```

4. **Install in development mode:**
   ```bash
   pip install -e .
   ```

5. **Verify installation:**
   ```bash
   python -m tapps_agents.cli --help
   ```

### Configuration

1. **Create configuration file:**
   ```bash
   cp templates/default_config.yaml project_config.yaml
   ```

2. **Edit `project_config.yaml`:**
   ```yaml
   project:
     name: "my-project"
     root_path: "."
   
   model:
     provider: "local"  # or "anthropic", "openai"
     profiles:
       default:
         model_name: "qwen2.5-coder:7b"
   
   agents:
     reviewer:
       quality_threshold: 70.0
   ```

3. **Set environment variables (if using cloud providers):**
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   export OPENAI_API_KEY="your-key"
   ```

## Docker Deployment

### Building Docker Image

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   RUN pip install -e .
   
   CMD ["python", "-m", "tapps_agents.cli", "--help"]
   ```

2. **Build image:**
   ```bash
   docker build -t tapps-agents:latest .
   ```

3. **Run container:**
   ```bash
   docker run -v $(pwd):/workspace tapps-agents:latest \
     reviewer review /workspace/src/main.py
   ```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tapps-agents:
    build: .
    volumes:
      - ./src:/workspace/src
      - ./config:/workspace/config
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: python -m tapps_agents.cli reviewer review /workspace/src/main.py
```

Run with:
```bash
docker-compose up
```

## Production Deployment

### Requirements

- Python 3.10+
- Persistent storage for KB cache (Context7)
- Network access (if using cloud LLM providers)
- Sufficient resources for agent execution

### Steps

1. **Install on server:**
   ```bash
   pip install tapps-agents
   ```

2. **Create production config:**
   ```yaml
   project:
     name: "production-project"
     root_path: "/var/lib/tapps-agents"
   
   model:
     provider: "anthropic"  # or "openai"
     profiles:
       default:
         model_name: "claude-3-5-sonnet-20241022"
   
   context7:
     cache_dir: "/var/lib/tapps-agents/context7-cache"
     enable_auto_refresh: true
   ```

3. **Set up systemd service** (optional):
   ```ini
   [Unit]
   Description=TappsCodingAgents Service
   After=network.target
   
   [Service]
   Type=oneshot
   User=tapps-agents
   WorkingDirectory=/var/lib/tapps-agents
   Environment="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
   ExecStart=/usr/local/bin/python -m tapps_agents.cli orchestrator execute-workflow /var/lib/tapps-agents/workflows/production.yaml
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable and start service:**
   ```bash
   sudo systemctl enable tapps-agents
   sudo systemctl start tapps-agents
   ```

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e .
      
      - name: Run quality analysis
        run: |
          python -m tapps_agents.cli reviewer analyze-project .
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: quality-reports
          path: reports/quality/
```

### GitLab CI

```yaml
stages:
  - quality

quality:
  stage: quality
  image: python:3.10
  script:
    - pip install -r requirements.txt
    - pip install -e .
    - python -m tapps_agents.cli reviewer analyze-project .
  artifacts:
    paths:
      - reports/quality/
    expire_in: 1 week
```

## Cloud Deployment

### AWS

**Using EC2:**
1. Launch EC2 instance (Amazon Linux 2)
2. Install Python 3.10+
3. Follow production deployment steps
4. Use IAM roles for credential management

**Using Lambda:**
1. Package as Lambda function
2. Use environment variables for config
3. Set timeout appropriately
4. Consider container images for larger deployments

### Google Cloud Platform

**Using Compute Engine:**
1. Create VM instance
2. Install Python and dependencies
3. Follow production deployment steps
4. Use Secret Manager for API keys

**Using Cloud Functions:**
1. Package as Cloud Function
2. Configure environment variables
3. Set appropriate memory/timeout
4. Use Cloud Storage for KB cache

### Azure

**Using App Service:**
1. Create Python web app
2. Configure app settings
3. Deploy code
4. Use Key Vault for secrets

**Using Functions:**
1. Create Python function app
2. Deploy function code
3. Configure application settings
4. Use managed identity for auth

## Environment Variables

### Required (for cloud providers)

```bash
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
```

### Optional

```bash
TAPPS_CONFIG_PATH=/path/to/config.yaml
TAPPS_LOG_LEVEL=INFO
TAPPS_CACHE_DIR=/path/to/cache
CONTEXT7_CACHE_DIR=/path/to/context7-cache
```

## Monitoring

### Logging

Configure logging in `project_config.yaml`:

```yaml
logging:
  level: "INFO"
  format: "json"  # or "text"
  file: "/var/log/tapps-agents.log"
```

### Metrics

- Agent execution times
- Quality scores over time
- Error rates
- Cache hit rates (Context7)

### Health Checks

Create health check endpoint:

```python
# health.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Scaling

### Horizontal Scaling

- Run multiple agent instances
- Use message queue (Redis, RabbitMQ)
- Load balance requests
- Share KB cache (Redis or shared storage)

### Vertical Scaling

- Increase memory for large codebases
- Use faster CPU for analysis tasks
- Allocate more disk for KB cache

## Backup and Recovery

### Backup Strategy

1. **Configuration files:**
   - Version control (Git)
   - Regular backups

2. **KB Cache (Context7):**
   - Regular backups of cache directory
   - Consider using Redis persistence

3. **Quality Reports:**
   - Archive historical reports
   - Use object storage (S3, GCS)

### Recovery

1. Restore from backups
2. Rebuild KB cache (if needed)
3. Verify configuration
4. Test agent functionality

## Security

See [SECURITY.md](../SECURITY.md) for security guidelines.

Key points:
- Use environment variables for secrets
- Restrict file system access
- Validate all inputs
- Keep dependencies updated
- Use HTTPS for remote access

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Performance Tuning

1. **KB Cache:**
   - Increase cache size
   - Enable auto-refresh
   - Use Redis for distributed cache

2. **Agent Execution:**
   - Use local LLM when possible
   - Parallel analysis for multi-service
   - Incremental quality checks

3. **Report Generation:**
   - Generate reports asynchronously
   - Cache report templates
   - Use efficient JSON serialization

---

**Related Documentation:**
- [Configuration Guide](CONFIGURATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Security Policy](../SECURITY.md)

