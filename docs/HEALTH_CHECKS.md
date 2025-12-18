# Health Checks Guide

Comprehensive guide to TappsCodingAgents health check system for ensuring your installation is working at 100% capacity.

## Overview

The health check system provides actionable health measurements across multiple dimensions:

- **Environment Readiness**: Python, tools, configuration
- **Automation**: Background agent configuration and file system access
- **Execution Reliability**: Workflow success rates and performance
- **Context7 Cache**: Cache effectiveness and performance
- **Knowledge Base**: RAG/KB population and query performance
- **Governance**: Safety and approval queue status
- **Outcomes**: Quality trends and improvement metrics

## Quick Start

### Run All Health Checks

```bash
tapps-agents health check
```

### View Health Dashboard

```bash
tapps-agents health dashboard
```

### Check Specific Area

```bash
tapps-agents health check --check environment
tapps-agents health check --check execution
tapps-agents health check --check context7_cache
```

## Health Check Categories

### 1. Environment Health Check

**What it checks:**
- Python version compatibility
- Required tools (ruff, mypy, pytest, etc.)
- Configuration file presence and validity
- Feature toggles (Context7, TypeScript support)

**Status Thresholds:**
- **Green (≥85)**: All critical tools available, config valid
- **Yellow (70-84)**: Some optional tools missing, config issues
- **Red (<70)**: Critical tools missing, config invalid

**Common Issues:**
- Missing development tools → Run `tapps-agents install-dev`
- Python version mismatch → Update Python or adjust config
- Config file missing → Run `tapps-agents init`

### 2. Automation Health Check

**What it checks:**
- Background agent configuration validity
- File system write access (.tapps-agents/, .cursor/)
- Status file read access
- Command file write access

**Status Thresholds:**
- **Green**: All checks passing, automation ready
- **Yellow**: Some checks degraded, manual usage OK
- **Red**: Critical failures, automation won't work

**Common Issues:**
- Missing background-agents.yaml → Run `tapps-agents background-agent-config generate`
- Permission errors → Check directory permissions
- Invalid config → Run `tapps-agents background-agent-config validate`

### 3. Execution Health Check

**What it checks:**
- Workflow success rate (target: ≥95%)
- Median and p95 duration trends
- Retry rate
- Error categorization (tool missing, config invalid, model unavailable, timeout, permission)

**Status Thresholds:**
- **Green (≥95%)**: Success rate ≥95%, stable performance
- **Yellow (85-95%)**: Success rate 85-95%, some issues
- **Red (<85%)**: Success rate <85%, frequent failures

**Common Issues:**
- Low success rate → Check error categories for patterns
- High retry rate → Check system stability and model availability
- Timeout errors → Check model provider or increase timeout

### 4. Context7 Cache Health Check

**What it checks:**
- Cache hit rate (target: ≥95%)
- Average response time (target: <150ms)
- Cache size and growth
- Stale entry ratio
- Cache directory permissions

**Status Thresholds:**
- **Green**: Hit rate ≥95%, response time <150ms
- **Yellow**: Hit rate 70-95%, response time 150-1000ms
- **Red**: Hit rate <70%, response time >1000ms, or cache empty

**Common Issues:**
- Low hit rate → Run cache pre-population: `python scripts/prepopulate_context7_cache.py`
- Empty cache → Cache will populate automatically, or run pre-population
- Slow response time → Check disk I/O, consider SSD storage

### 5. Knowledge Base Health Check

**What it checks:**
- KB file count and domains
- Recent activity (last 7 days)
- RAG backend type (vector vs simple)
- Vector index existence and validity
- Query performance (target: <2s for vector)

**Status Thresholds:**
- **Green**: KB populated, vector RAG available, recent activity
- **Yellow**: KB exists but using simple search, or no recent activity
- **Red**: KB empty, no activity, or index issues

**Common Issues:**
- Empty KB → Run knowledge ingestion or wait for automatic population
- Simple backend → Install FAISS: `pip install faiss-cpu`
- Missing index → Index will be built automatically on first query

### 6. Governance Health Check

**What it checks:**
- Approval queue size
- Approval lead time
- Filtered content events (secrets/tokens/PII)

**Status Thresholds:**
- **Green**: Queue near 0, occasional filtering
- **Yellow**: Growing queue (<20), frequent filtering
- **Red**: Large queue (≥20), blocked ingestion, stale approvals

**Common Issues:**
- Growing approval queue → Review and process approvals: `tapps-agents governance list`
- Stale approvals → Process oldest approvals first
- Frequent filtering → Review governance policy settings

### 7. Outcome Health Check

**What it checks:**
- Quality score trends (improving/stable/degrading)
- Average quality scores
- Improvement cycle frequency
- Regression rate

**Status Thresholds:**
- **Green**: Scores improving or stable, active improvement cycles
- **Yellow**: Scores stable but low, or no improvement activity
- **Red**: Scores degrading, high regression rate

**Common Issues:**
- No metrics → Run reviewer agent or quality workflows
- Declining scores → Investigate recent code changes
- No improvement cycles → Run quality workflows: `tapps-agents workflow quality`

## Health Status Definitions

### Overall Health Score

The overall health score is a weighted average of all check scores:
- Critical checks (environment, execution) have 2x weight
- Other checks have 1x weight

**Status Levels:**
- **Healthy (≥85)**: All critical checks passing, system operating normally
- **Degraded (70-84)**: Some checks degraded but system functional
- **Unhealthy (<70)**: Critical checks failing, system may not function properly

## Health Check Routine

### Daily (1 minute)
```bash
# Quick health check
tapps-agents health check --format text
```

Check for:
- Any red status checks
- Execution success rate
- Recent failures

### Weekly (10 minutes)
```bash
# Full dashboard
tapps-agents health dashboard

# Check trends
tapps-agents health trends --check-name execution --days 7
```

Review:
- Overall health trends
- Cache effectiveness
- KB growth
- Approval queue status

### Monthly (30 minutes)
```bash
# Comprehensive review
tapps-agents health metrics --days 30

# All trend analysis
for check in environment execution context7_cache knowledge_base governance outcomes; do
  tapps-agents health trends --check-name $check --days 30
done
```

Review:
- Long-term trends
- Quality score improvements
- System stability
- Governance effectiveness

## Troubleshooting Guide

### Red Flags and Solutions

#### "No execution metrics available"
**Cause**: Workflows haven't run yet or metrics disabled
**Solution**: Run a workflow to generate metrics, or check analytics configuration

#### "Context7 cache is empty"
**Cause**: Cache not populated, Context7 disabled, or permissions issue
**Solution**: 
- Run `python scripts/prepopulate_context7_cache.py`
- Check Context7 is enabled in config
- Verify cache directory permissions

#### "High failure rate with 'tool missing'"
**Cause**: Required tools not installed
**Solution**: Run `tapps-agents doctor` to identify missing tools, then `tapps-agents install-dev`

#### "RAG returns 'no relevant knowledge'"
**Cause**: KB not populated or ingestion not running
**Solution**: 
- Check KB directory exists: `.tapps-agents/knowledge/`
- Run knowledge ingestion if available
- Verify KB directory permissions

#### "Approval queue growing forever"
**Cause**: Governance requires approval but no process to review
**Solution**: 
- Review approvals: `tapps-agents governance list`
- Process approvals: `tapps-agents governance approve <id>`
- Or adjust governance policy to reduce approval requirements

#### "Vector index rebuilds constantly"
**Cause**: Index directory path wrong or not writable
**Solution**: 
- Check `.tapps-agents/rag_index/` permissions
- Verify index directory is writable
- Check disk space

## Health Metrics Storage

Health metrics are stored persistently in `.tapps-agents/health/metrics/` as JSONL files (daily rotation).

### Viewing Stored Metrics

```bash
# All metrics (last 30 days)
tapps-agents health metrics

# Specific check
tapps-agents health metrics --check-name execution

# Filter by status
tapps-agents health metrics --status unhealthy

# Custom time range
tapps-agents health metrics --days 7
```

### Trend Analysis

```bash
# Execution health trends
tapps-agents health trends --check-name execution --days 7

# Context7 cache trends
tapps-agents health trends --check-name context7_cache --days 30
```

## Integration with Analytics

Health check summary is automatically included in the analytics dashboard:

```bash
tapps-agents analytics dashboard
```

The dashboard shows:
- Overall health status
- Health score
- Top remediation actions
- Link to detailed health report

## Best Practices

1. **Run health checks regularly**: Daily quick check, weekly full review
2. **Address red status immediately**: Red status indicates critical issues
3. **Monitor trends**: Use trends to catch degrading health early
4. **Pre-populate cache**: Run cache pre-population after project setup
5. **Process approvals**: Keep approval queue small for healthy KB growth
6. **Track outcomes**: Monitor quality scores to ensure improvements

## Command Reference

### Health Check Commands

```bash
# Run all health checks
tapps-agents health check

# Run specific check
tapps-agents health check --check environment

# Save results (default)
tapps-agents health check --save

# Don't save results
tapps-agents health check --no-save

# JSON output
tapps-agents health check --format json
```

### Dashboard Commands

```bash
# Text dashboard
tapps-agents health dashboard

# JSON dashboard
tapps-agents health dashboard --format json
```

### Metrics Commands

```bash
# View stored metrics
tapps-agents health metrics

# Filter by check
tapps-agents health metrics --check-name execution

# Filter by status
tapps-agents health metrics --status unhealthy

# Custom time range
tapps-agents health metrics --days 7
```

### Trends Commands

```bash
# Execution trends (7 days)
tapps-agents health trends --check-name execution

# Context7 cache trends (30 days)
tapps-agents health trends --check-name context7_cache --days 30

# JSON output
tapps-agents health trends --check-name execution --format json
```

## See Also

- [Configuration Guide](CONFIGURATION.md) - Project configuration
- [Context7 Cache Optimization](CONTEXT7_CACHE_OPTIMIZATION.md) - Cache tuning
- [Analytics Dashboard](DEVELOPER_GUIDE.md#analytics) - Performance metrics
- [Background Agents](DEVELOPER_GUIDE.md#background-agents) - Automation setup

