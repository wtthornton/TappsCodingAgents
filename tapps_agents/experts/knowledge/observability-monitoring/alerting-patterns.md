# Alerting Patterns

## Overview

Effective alerting helps teams respond quickly to issues while avoiding alert fatigue. Good alerts are actionable, timely, and based on symptoms rather than causes.

## Alerting Philosophy

### Alert on Symptoms, Not Causes

**Why:**
- Symptoms are observable and measurable
- Causes may not be known
- Symptoms are user-facing
- Causes change over time

**Example:**
```yaml
# Good: Alert on symptom (high error rate)
- alert: HighErrorRate
  expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01

# Bad: Alert on cause (assumed)
- alert: DatabaseSlow
  expr: db_query_duration_seconds > 1
  # This assumes database is the problem, but errors might come from elsewhere
```

### Alert on User Impact

**Focus on what affects users:**
- Service availability
- Error rates
- Latency degradation
- Feature unavailability

**Example:**
```yaml
# Good: User-visible symptom
- alert: ServiceUnavailable
  expr: up{job="api"} == 0

# Less useful: Internal metric without user impact
- alert: HighMemoryUsage
  expr: memory_usage_bytes / memory_total_bytes > 0.8
  # Only alert if this actually affects users
```

## Alert Components

### Alert Definition

**Required Fields:**
- `alert`: Alert name
- `expr`: PromQL expression
- `for`: Duration before firing
- `labels`: Additional labels
- `annotations`: Human-readable information

**Example:**
```yaml
- alert: HighErrorRate
  expr: |
    rate(http_errors_total{status=~"5.."}[5m]) 
    / rate(http_requests_total[5m]) > 0.01
  for: 5m
  labels:
    severity: critical
    team: backend
  annotations:
    summary: "Error rate above 1% for 5 minutes"
    description: "Error rate is {{ $value | humanizePercentage }}"
    runbook: "https://wiki/runbooks/high-error-rate"
```

### Severity Levels

**Critical:**
- Service down
- Data loss
- Security breach
- Immediate user impact

**Warning:**
- Degraded performance
- Approaching thresholds
- Potential issues
- Needs attention soon

**Info:**
- Significant events
- State changes
- Operational notices
- Not urgent

**Example:**
```yaml
- alert: ServiceDown
  expr: up{job="api"} == 0
  labels:
    severity: critical

- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  labels:
    severity: warning

- alert: DeploymentComplete
  expr: changes(deployment_version[1h]) > 0
  labels:
    severity: info
```

## Alerting Patterns

### 1. Threshold-Based Alerts

**Pattern:** Alert when metric exceeds threshold

**Use Cases:**
- Error rates
- Latency
- Resource usage
- Queue depths

**Example:**
```yaml
- alert: HighErrorRate
  expr: |
    rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m

- alert: HighLatency
  expr: |
    histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 10m
```

### 2. Rate of Change Alerts

**Pattern:** Alert on sudden changes

**Use Cases:**
- Traffic spikes/drops
- Error rate increases
- Resource usage changes

**Example:**
```yaml
- alert: TrafficSpike
  expr: |
    (rate(http_requests_total[5m]) - rate(http_requests_total[15m] offset 10m))
    / rate(http_requests_total[15m] offset 10m) > 2
  # Alert if current rate is 3x higher than 10 minutes ago

- alert: ErrorRateIncrease
  expr: |
    (rate(http_errors_total[5m]) / rate(http_requests_total[5m]))
    - (rate(http_errors_total[15m] offset 10m) / rate(http_requests_total[15m] offset 10m))
    > 0.005
  # Alert if error rate increased by 0.5%
```

### 3. Anomaly Detection

**Pattern:** Alert when metric deviates from normal

**Use Cases:**
- Unusual patterns
- Seasonal variations
- Baseline comparisons

**Example:**
```yaml
- alert: UnusualTrafficPattern
  expr: |
    (rate(http_requests_total[5m]) - 
     avg_over_time(rate(http_requests_total[5m])[1d:]))
    / stddev_over_time(rate(http_requests_total[5m])[1d:]) > 3
  # Alert if current rate is 3 standard deviations above 24h average
```

### 4. Absence Alerts

**Pattern:** Alert when metric is missing

**Use Cases:**
- Service down
- Exporter failures
- Missing heartbeats

**Example:**
```yaml
- alert: ServiceDown
  expr: up{job="api"} == 0
  for: 1m

- alert: MissingMetrics
  expr: absent(http_requests_total)
  for: 5m
```

### 5. SLO-Based Alerts

**Pattern:** Alert on error budget burn rate

**Use Cases:**
- SLO violation risk
- Error budget consumption
- Reliability targets

**Example:**
```yaml
# Alert if burning error budget too fast
- alert: HighErrorBudgetBurnRate
  expr: |
    (rate(http_errors_total[1h]) / rate(http_requests_total[1h]))
    > on() (0.001 * 14)  # 14x normal burn rate for 99.9% SLO
  for: 5m
  annotations:
    summary: "Error budget burning at {{ $value }}x normal rate"

# Alert on SLO violation
- alert: SLOViolation
  expr: |
    (1 - (rate(http_errors_total[30d]) / rate(http_requests_total[30d]))) < 0.999
  annotations:
    summary: "Availability SLO violated"
```

## Alert Routing

### Routing by Severity

**Critical Alerts:**
- On-call engineer
- Immediate notification
- Multiple channels (PagerDuty, phone, SMS)

**Warning Alerts:**
- Team channel
- Email notification
- Daily digest

**Info Alerts:**
- Dashboard only
- Weekly report
- Optional notification

**Example:**
```yaml
route:
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'oncall'
      continue: false
    - match:
        severity: warning
      receiver: 'team-slack'
    - match:
        severity: info
      receiver: 'email'
```

### Routing by Service

**Team Ownership:**
```yaml
route:
  routes:
    - match:
        team: backend
      receiver: 'backend-team'
    - match:
        team: frontend
      receiver: 'frontend-team'
    - match:
        service: database
      receiver: 'database-team'
```

## On-Call Practices

### On-Call Rotation

**Best Practices:**
- Regular rotation schedule
- Clear handoff procedures
- Backup on-call engineer
- Timezone considerations

**Rotation Types:**
- Weekly rotation
- Daily rotation (for high-traffic)
- Follow-the-sun (global teams)

### Runbooks

**Every alert should have a runbook:**
```yaml
- alert: HighErrorRate
  annotations:
    runbook: "https://wiki/runbooks/high-error-rate"
```

**Runbook Contents:**
1. Alert description
2. How to verify the issue
3. Common causes
4. Investigation steps
5. Resolution steps
6. Escalation path

### Alert Acknowledgment

**Acknowledgment Workflow:**
1. Alert fires
2. On-call acknowledges
3. Investigation begins
4. Status updates
5. Resolution or escalation

**Benefits:**
- Prevents duplicate work
- Tracks response time
- Shows current status

## Reducing Alert Fatigue

### Problem: Too Many Alerts

**Symptoms:**
- Engineers ignore alerts
- Important alerts missed
- Low signal-to-noise ratio
- Burnout

### Solutions

**1. Consolidate Related Alerts:**
```yaml
# Bad: Multiple alerts for same issue
- alert: HighCPU
- alert: HighMemory
- alert: HighDiskIO

# Better: Single alert for resource exhaustion
- alert: ResourceExhaustion
  expr: |
    (cpu_usage > 0.8) OR (memory_usage > 0.8) OR (disk_io_utilization > 0.8)
```

**2. Increase Thresholds:**
- Only alert on significant issues
- Use `for` clause to prevent flapping
- Tune based on false positive rate

**3. Use Alert Grouping:**
```yaml
# Group related alerts
group_by: ['alertname', 'cluster', 'service']
group_wait: 30s
group_interval: 5m
```

**4. Suppress During Maintenance:**
```yaml
# Silence alerts during known maintenance
- alert: MaintenanceMode
  expr: maintenance_mode == 1
  # Use to suppress other alerts
```

**5. Alert on Aggregates:**
```yaml
# Alert on service-level, not instance-level
- alert: ServiceHighErrorRate
  expr: |
    sum(rate(http_errors_total[5m])) 
    / sum(rate(http_requests_total[5m])) > 0.01
  # Instead of alerting per instance
```

## Alert Testing

### Test Alerts

**Verify alerts work:**
- Trigger test alerts
- Verify routing
- Check notifications
- Validate runbooks

**Example:**
```yaml
# Test alert
- alert: TestAlert
  expr: vector(1)
  annotations:
    summary: "This is a test alert"
```

### Alert Review Process

**Regular Reviews:**
- Weekly alert review
- Identify false positives
- Tune thresholds
- Remove unused alerts
- Update runbooks

**Metrics to Track:**
- Alert frequency
- False positive rate
- Mean time to acknowledge (MTTA)
- Mean time to resolve (MTTR)
- Alert-to-incident ratio

## Best Practices Summary

1. **Alert on symptoms**, not causes
2. **Focus on user impact**
3. **Use appropriate severity levels**
4. **Add `for` clause** to prevent flapping
5. **Include runbooks** for every alert
6. **Route alerts** by severity and team
7. **Reduce alert fatigue** through consolidation
8. **Test alerts** regularly
9. **Review and tune** alerts periodically
10. **Document decisions** and thresholds

## Tools

### Alert Managers

**Prometheus Alertmanager:**
- Alert routing
- Grouping and inhibition
- Silence management
- Integration with notification channels

**PagerDuty:**
- On-call management
- Escalation policies
- Incident response
- Integration with monitoring tools

**Opsgenie:**
- Alert management
- On-call scheduling
- Escalation
- Mobile app

**VictorOps (Splunk On-Call):**
- Incident management
- On-call scheduling
- Timeline view
- Integration ecosystem

