# SLO, SLI, and SLA

## Overview

Service Level Objectives (SLOs), Service Level Indicators (SLIs), and Service Level Agreements (SLAs) are fundamental concepts for managing service reliability and setting expectations with users.

## Definitions

### SLA (Service Level Agreement)

**Definition:** A contract between service provider and users that defines the level of service expected.

**Components:**
- Service commitments
- Consequences for violations
- Legal/financial implications
- Business agreements

**Example:**
- "99.9% uptime or money back"
- "Response time < 200ms for 95% of requests"
- "Support response within 4 hours"

### SLO (Service Level Objective)

**Definition:** A target value for an SLI over a time window. Internal goals for service reliability.

**Characteristics:**
- Internal metric (not customer-facing)
- Used for error budget management
- Should be tighter than SLA
- Drives engineering decisions

**Example:**
- "99.95% availability over 30 days"
- "95% of requests < 100ms latency"
- "Error rate < 0.1%"

### SLI (Service Level Indicator)

**Definition:** A carefully defined quantitative measure of some aspect of service level.

**Characteristics:**
- Measurable metric
- Reflects user experience
- Defined formula/calculation
- Tracked continuously

**Example:**
- Availability: (Successful requests) / (All requests)
- Latency: Proportion of requests below threshold
- Error rate: (Failed requests) / (All requests)

## Relationship

```
SLA (Business Contract)
  ↓
SLO (Internal Objective) - Should be tighter than SLA
  ↓
SLI (Measured Indicator) - What we actually measure
```

## SLI Implementation

### Availability SLI

**Formula:**
```
SLI = (Successful requests) / (Total requests)
```

**Definition:**
- What counts as "successful"?
- What time window?
- What requests included/excluded?

**Example:**
```python
# Calculate availability SLI
total_requests = successful_requests + failed_requests
availability_sli = successful_requests / total_requests if total_requests > 0 else 1.0

# Exclude certain requests from SLI
def is_counted_for_sli(request):
    # Exclude health checks
    if request.path == '/health':
        return False
    # Exclude admin endpoints
    if request.path.startswith('/admin'):
        return False
    return True
```

**Considerations:**
- Exclude health checks
- Define "successful" clearly (HTTP 200? 2xx? 4xx?)
- Window for calculation (rolling 30 days? calendar month?)

### Latency SLI

**Formula:**
```
SLI = (Requests under threshold) / (Total requests)
```

**Example:**
```python
# Calculate latency SLI
threshold_ms = 200
requests_under_threshold = sum(1 for latency in latencies if latency < threshold_ms)
latency_sli = requests_under_threshold / len(latencies)

# For percentiles
p95_latency = np.percentile(latencies, 95)
latency_sli = 1.0 if p95_latency < threshold_ms else 0.0
```

**Common Thresholds:**
- p50 (median)
- p95
- p99
- p99.9

### Error Rate SLI

**Formula:**
```
SLI = 1 - (Error requests / Total requests)
```

**Example:**
```python
# Calculate error rate SLI
total_requests = successful_requests + failed_requests
error_rate = failed_requests / total_requests if total_requests > 0 else 0.0
error_rate_sli = 1 - error_rate
```

**Error Definitions:**
- HTTP 5xx errors?
- All non-2xx?
- Application-level errors?
- Timeouts?

### Freshness SLI (Data Systems)

**Formula:**
```
SLI = (Data items within freshness threshold) / (Total data items)
```

**Example:**
```python
# Calculate freshness SLI
freshness_threshold = timedelta(minutes=5)
current_time = datetime.utcnow()

fresh_items = sum(1 for item in data_items 
                 if current_time - item.last_updated < freshness_threshold)
freshness_sli = fresh_items / len(data_items)
```

## SLO Definition

### Availability SLO

**Example:**
- "99.9% availability over 30-day rolling window"
- "99.95% uptime per month"

**Calculation:**
```python
# Rolling 30-day availability
def calculate_availability_slo(metrics, target=0.999):
    # Get last 30 days of metrics
    last_30_days = get_last_n_days(metrics, days=30)
    
    total_requests = sum(m.total for m in last_30_days)
    successful_requests = sum(m.successful for m in last_30_days)
    
    availability = successful_requests / total_requests if total_requests > 0 else 1.0
    
    return {
        'availability': availability,
        'target': target,
        'meeting_slo': availability >= target,
        'error_budget': calculate_error_budget(availability, target)
    }
```

### Latency SLO

**Example:**
- "95% of requests < 100ms over 30 days"
- "99% of requests < 500ms"

**Calculation:**
```python
def calculate_latency_slo(latencies, threshold_ms=100, percentile=95, target=0.95):
    p95_latency = np.percentile(latencies, percentile)
    requests_under_threshold = sum(1 for l in latencies if l < threshold_ms)
    latency_sli = requests_under_threshold / len(latencies)
    
    return {
        'p95_latency_ms': p95_latency,
        'threshold_ms': threshold_ms,
        'sli': latency_sli,
        'target': target,
        'meeting_slo': latency_sli >= target
    }
```

## Error Budgets

### Concept

**Error Budget:** The amount of unreliability allowed before SLO is violated.

**Formula:**
```
Error Budget = 1 - SLO Target
```

**Example:**
- SLO: 99.9% availability
- Error Budget: 0.1% (43.2 minutes per month)

### Error Budget Consumption

**Calculation:**
```python
def calculate_error_budget(availability, target, time_window_days=30):
    total_minutes = time_window_days * 24 * 60
    budget_minutes = total_minutes * (1 - target)
    consumed_minutes = total_minutes * (1 - availability)
    remaining_minutes = budget_minutes - consumed_minutes
    remaining_percent = (remaining_minutes / budget_minutes) * 100 if budget_minutes > 0 else 0
    
    return {
        'total_budget_minutes': budget_minutes,
        'consumed_minutes': consumed_minutes,
        'remaining_minutes': remaining_minutes,
        'remaining_percent': remaining_percent,
        'burn_rate': consumed_minutes / budget_minutes if budget_minutes > 0 else 0
    }
```

### Error Budget Policy

**Use Error Budgets to:**
1. **Deploy faster:** If budget available, can take risks
2. **Slow down:** If budget low, focus on reliability
3. **Prioritize work:** Reliability vs features trade-off

**Example Policy:**
```python
def get_deployment_policy(error_budget_percent):
    if error_budget_percent > 50:
        return "NORMAL"  # Deploy normally
    elif error_budget_percent > 25:
        return "CAUTIOUS"  # Extra testing, canary deployments
    elif error_budget_percent > 10:
        return "FROZEN"  # Only critical fixes
    else:
        return "STOP"  # Stop all deployments, focus on reliability
```

## SLO Implementation

### Monitoring SLOs

**Metrics to Track:**
```python
# Prometheus metrics for SLO tracking
from prometheus_client import Counter, Histogram

# SLI metrics
http_requests_total = Counter('http_requests_total', ...)
http_requests_success = Counter('http_requests_success_total', ...)
http_request_duration = Histogram('http_request_duration_seconds', ...)

# SLO compliance
slo_availability = Gauge('slo_availability', 'Current availability SLI')
slo_compliance = Gauge('slo_compliance', 'SLO compliance (1 = meeting, 0 = not)')
error_budget_remaining = Gauge('error_budget_remaining_percent', 'Remaining error budget %')
```

### Alerting on SLOs

**Burn Rate Alerts:**
```yaml
# Alert if burning error budget too fast
- alert: HighErrorBudgetBurnRate
  expr: |
    (rate(http_errors_total[1h]) / rate(http_requests_total[1h])) 
    > on() (0.001 * 14)  # 14x normal burn rate for 99.9% SLO
  for: 5m
  annotations:
    summary: "Error budget burning at {{ $value }}x normal rate"
```

**SLO Violation Alerts:**
```yaml
- alert: SLOViolation
  expr: |
    (1 - (rate(http_errors_total[30d]) / rate(http_requests_total[30d]))) < 0.999
  annotations:
    summary: "Availability SLO violated: {{ $value }}"
```

## Best Practices

### 1. Start with User Experience

**Define SLIs from user perspective:**
- What does the user experience?
- How do users define "good" service?
- What matters to user satisfaction?

### 2. Use Multiple SLIs

**Don't rely on a single SLI:**
- Availability (uptime)
- Latency (responsiveness)
- Freshness (for data systems)
- Correctness (for data systems)

### 3. Make SLOs Achievable

**Avoid perfectionism:**
- 100% is impossible
- Set realistic targets
- Leave room for innovation
- Balance reliability and velocity

### 4. Review and Adjust

**Regular SLO reviews:**
- Are targets too loose/tight?
- Do they reflect user needs?
- Are they driving right behavior?
- Adjust based on data

### 5. Document Decisions

**Clear SLO documentation:**
- Why this SLO?
- How calculated?
- What excluded?
- When to review?

### 6. Communicate Clearly

**Share SLO status:**
- Dashboard visibility
- Regular reports
- Error budget status
- Impact of decisions

## Common SLO Targets

### Web Services

**Availability:**
- Critical: 99.95% (22 minutes/month downtime)
- Standard: 99.9% (43 minutes/month)
- Non-critical: 99.5% (3.6 hours/month)

**Latency:**
- API: 95% < 200ms, 99% < 500ms
- Web pages: 95% < 2s
- Search: 95% < 100ms

**Error Rate:**
- Critical: < 0.01%
- Standard: < 0.1%
- Non-critical: < 1%

### Data Systems

**Freshness:**
- Real-time: 95% < 1 minute
- Near-real-time: 95% < 5 minutes
- Batch: 95% < 1 hour

**Correctness:**
- Critical: > 99.99%
- Standard: > 99.9%

## Tools

### Open Source

**SLI/SLO Libraries:**
- Prometheus SLO exporter
- Grafana SLO dashboards
- Cortex (for SLO tracking)

### Commercial

**Integrated SLO Management:**
- Datadog SLOs
- New Relic Service Levels
- Google Cloud SLO Monitoring

## Summary

Effective SLO management requires:

1. **Define SLIs** that measure user experience
2. **Set SLOs** that balance reliability and velocity
3. **Track error budgets** to guide decisions
4. **Alert on burn rates** to prevent violations
5. **Use error budgets** to make trade-offs explicit
6. **Review regularly** and adjust based on data
7. **Document clearly** for team understanding
8. **Communicate status** transparently

