# Database Backup and Recovery

## Overview

Backup and recovery strategies protect against data loss and enable point-in-time recovery. This guide covers backup types, recovery objectives, and implementation strategies.

## Backup Types

### Full Backup

**Complete Database:**
- All data and schema
- Foundation for recovery
- Longer backup time
- More storage required

**PostgreSQL:**
```bash
pg_dump -Fc database_name > backup.dump
```

**MySQL:**
```bash
mysqldump --single-transaction database_name > backup.sql
```

### Incremental Backup

**Changes Since Last Backup:**
- Faster backups
- Less storage
- Requires full + incrementals
- More complex recovery

### Differential Backup

**Changes Since Full Backup:**
- Moderate backup time
- Moderate storage
- Full + latest differential
- Simpler than incremental

### Continuous Archiving

**WAL/Transaction Logs:**
- Real-time log archiving
- Point-in-time recovery
- Minimal data loss
- Higher complexity

**PostgreSQL:**
```conf
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

## Recovery Objectives

### RTO (Recovery Time Objective)

**Maximum Downtime:**
- Time to restore service
- Business impact tolerance
- Drives backup frequency
- Affects recovery strategy

### RPO (Recovery Point Objective)

**Maximum Data Loss:**
- Acceptable data loss window
- Frequency of backups
- Drives replication strategy
- Affects backup type

## Backup Strategies

### Cold Backup

**Database Offline:**
- Database stopped
- Consistent snapshot
- Simple process
- Requires downtime

### Hot Backup

**Database Online:**
- No downtime
- Consistent state required
- More complex
- Production-friendly

**PostgreSQL:**
```bash
pg_basebackup -D /backup/base -Ft -z -P
```

### Snapshot Backup

**Storage-Level Snapshot:**
- Instant snapshot
- Storage vendor feature
- Fast backup
- Restore to snapshot point

## Recovery Procedures

### Full Recovery

**Restore from Backup:**
```bash
# PostgreSQL
pg_restore -d database_name backup.dump

# MySQL
mysql database_name < backup.sql
```

### Point-in-Time Recovery

**Recover to Specific Time:**
```bash
# PostgreSQL
# 1. Restore base backup
pg_restore -d database_name base_backup.dump

# 2. Replay WAL logs to target time
pg_recovery -D /data -t "2026-01-15 10:30:00"
```

### Partial Recovery

**Recover Specific Objects:**
```bash
# Restore specific tables
pg_restore -t users -d database_name backup.dump
```

## Backup Automation

### Scheduled Backups

**Cron Jobs:**
```bash
# Daily full backup
0 2 * * * pg_dump -Fc database > /backup/daily/$(date +\%Y\%m\%d).dump

# Hourly incremental
0 * * * * archive_wal_logs.sh
```

### Retention Policies

**Keep Backups:**
- Daily: 7 days
- Weekly: 4 weeks
- Monthly: 12 months
- Yearly: 7 years

### Backup Verification

**Test Restores:**
- Regular restore tests
- Verify backup integrity
- Test recovery procedures
- Document results

## Best Practices

1. **Automate Backups:** Regular, scheduled
2. **Test Restores:** Regular DR drills
3. **Offsite Storage:** Geographic redundancy
4. **Encrypt Backups:** Protect sensitive data
5. **Monitor Backup Success:** Alert on failures
6. **Document Procedures:** Clear recovery steps
7. **Set Retention:** Balance storage and recovery needs
8. **Verify Integrity:** Regular checksums
9. **Multiple Backup Types:** Full + incremental/differential
10. **Regular Reviews:** Update procedures

