# Build Strategies

## Overview

Build strategies determine how software is compiled, packaged, and prepared for deployment. Choosing the right strategy improves build speed, reliability, and reproducibility.

## Build Types

### Clean Build
- Fresh build from scratch
- Removes all artifacts
- Ensures reproducibility
- Slower but reliable

### Incremental Build
- Only rebuilds changed components
- Faster execution
- Dependency tracking required
- May miss some changes

### Parallel Build
- Multiple components built simultaneously
- Reduces total build time
- Requires dependency resolution
- Uses more resources

## Build Optimization

### Caching Strategies

**Dependency Caching:**
```yaml
# GitHub Actions example
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

**Artifact Caching:**
- Cache build outputs
- Reuse unchanged artifacts
- Invalidate on dependency changes
- Speed up subsequent builds

### Build Parallelization

**Multi-Threading:**
- Parallel test execution
- Parallel compilation
- Reduce wall-clock time
- Monitor resource usage

**Distributed Builds:**
- Build across multiple machines
- Scale horizontally
- Faster for large projects
- Requires coordination

### Dependency Management

**Lock Files:**
- Pin exact versions
- Reproducible builds
- Security vulnerability tracking
- Version control lock files

**Minimal Dependencies:**
- Only include needed packages
- Faster installation
- Smaller artifacts
- Easier security scanning

## Container Builds

### Multi-Stage Builds
```dockerfile
# Build stage
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["python", "app.py"]
```

### Build Arguments
```dockerfile
ARG BUILD_VERSION
ARG BUILD_DATE
LABEL version=$BUILD_VERSION
LABEL build-date=$BUILD_DATE
```

### Layer Caching
- Order layers by change frequency
- Separate dependency installation
- Copy application code last
- Maximize cache hits

## Build Tools

### Python
- **setuptools**: Standard packaging
- **wheel**: Binary distribution
- **pip**: Package manager
- **poetry**: Modern dependency management

### JavaScript/TypeScript
- **npm/yarn/pnpm**: Package managers
- **webpack**: Module bundler
- **vite**: Fast build tool
- **rollup**: Module bundler

### General Purpose
- **Make**: Build automation
- **CMake**: Cross-platform builds
- **Bazel**: Fast, scalable builds
- **Gradle**: Build automation

## Build Scripts

### Best Practices

1. **Idempotent**: Can run multiple times safely
2. **Fast**: Optimize for speed
3. **Reliable**: Fail fast on errors
4. **Reproducible**: Same inputs = same outputs
5. **Documented**: Clear what each step does

### Example Build Script
```bash
#!/bin/bash
set -e  # Exit on error

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running linting..."
flake8 .

echo "Running type checking..."
mypy .

echo "Running tests..."
pytest --cov

echo "Building artifacts..."
python setup.py sdist bdist_wheel

echo "Build complete!"
```

## Build Artifacts

### Types
- **Source Distributions**: `.tar.gz`, `.zip`
- **Binary Distributions**: `.whl`, `.deb`, `.rpm`
- **Container Images**: Docker images
- **Executables**: Binary files
- **Documentation**: Generated docs

### Storage
- **Artifact Repositories**: Nexus, Artifactory
- **Container Registries**: Docker Hub, ECR, GCR
- **Package Repositories**: PyPI, npm, Maven

## CI/CD Integration

### Build Triggers
- **Push to main**: Build and test
- **Pull requests**: Validate changes
- **Scheduled**: Nightly builds
- **Manual**: On-demand builds

### Build Matrix
```yaml
strategy:
  matrix:
    python-version: [3.9, 3.10, 3.11]
    os: [ubuntu-latest, windows-latest, macos-latest]
```

## Best Practices

1. **Fast Builds**: Optimize for speed
2. **Reproducible**: Consistent results
3. **Reliable**: Fail fast on errors
4. **Cached**: Reuse where possible
5. **Parallel**: Build concurrently
6. **Versioned**: Tag all artifacts
7. **Secure**: Scan dependencies
