# Data Minimization Patterns

## Overview

Data minimization is a privacy principle that requires organizations to collect, process, and retain only the personal data that is necessary for a specific purpose. It is a fundamental principle of privacy by design and is required by GDPR, CCPA, and other privacy regulations.

## Core Principles

### Necessity
- Collect only data necessary for purpose
- Avoid collecting excessive data
- Question every data field
- Regular review of data collection

### Purpose Limitation
- Collect data for specific purposes
- Do not use for incompatible purposes
- Document all purposes
- Limit processing to stated purposes

### Retention Limitation
- Retain data only as long as necessary
- Define retention periods
- Implement automated deletion
- Regular data purging

### Storage Limitation
- Store data only as long as needed
- Delete when no longer needed
- Secure deletion methods
- Verify deletion

## Collection Minimization

### Field-Level Minimization
- Collect only required fields
- Avoid optional fields unless necessary
- Use progressive disclosure
- Collect at point of need

### Category Minimization
- Collect only necessary categories
- Avoid collecting special categories
- Use pseudonymization when possible
- Avoid collecting sensitive data

### Frequency Minimization
- Collect data only when needed
- Avoid continuous collection
- Use sampling when appropriate
- Collect on-demand when possible

### Source Minimization
- Collect from minimum sources
- Avoid redundant collection
- Use existing data when possible
- Consolidate data sources

## Processing Minimization

### Scope Limitation
- Process only necessary data
- Limit processing to stated purposes
- Avoid broad processing
- Use data filtering

### Duration Limization
- Process data only as long as needed
- Stop processing when purpose fulfilled
- Implement processing time limits
- Regular processing reviews

### Access Limitation
- Limit access to necessary personnel
- Role-based access controls
- Principle of least privilege
- Regular access reviews

### Function Limitation
- Limit functions to necessary operations
- Disable unnecessary features
- Use minimal processing
- Avoid over-processing

## Retention Minimization

### Retention Policies
- Define retention periods
- Document retention rationale
- Implement retention schedules
- Regular retention reviews

### Automated Deletion
- Implement automated deletion
- Schedule deletion tasks
- Verify deletion completion
- Document deletion activities

### Data Purging
- Regular data purging cycles
- Identify obsolete data
- Secure deletion methods
- Verify purging completion

### Archival Strategies
- Archive only when necessary
- Use pseudonymization for archives
- Limit archive access
- Define archive retention

## Technical Implementation

### Collection Patterns

#### Progressive Disclosure
- Collect data incrementally
- Request additional data when needed
- Avoid upfront data collection
- Use multi-step forms

#### Conditional Collection
- Collect based on conditions
- Skip unnecessary fields
- Use smart forms
- Dynamic data collection

#### Default Values
- Use defaults when possible
- Avoid collecting defaults
- Allow user to override
- Document default usage

### Processing Patterns

#### Data Filtering
- Filter data before processing
- Process only relevant records
- Use query filters
- Implement data segmentation

#### Lazy Loading
- Load data on demand
- Avoid loading all data
- Use pagination
- Implement lazy evaluation

#### Caching Strategies
- Cache only necessary data
- Limit cache retention
- Implement cache expiration
- Clear cache regularly

### Storage Patterns

#### Tiered Storage
- Use appropriate storage tiers
- Move old data to cheaper storage
- Delete from primary storage
- Archive to cold storage

#### Compression
- Compress stored data
- Reduce storage footprint
- Use efficient formats
- Regular compression reviews

#### Deduplication
- Remove duplicate data
- Identify duplicates
- Consolidate records
- Maintain single source of truth

## Pseudonymization for Minimization

### Tokenization
- Replace identifiers with tokens
- Store tokens separately
- Limit token access
- Use reversible tokens when needed

### Hashing
- Hash identifiers
- Use salted hashes
- Store hashes instead of identifiers
- Use one-way hashing

### Format-Preserving Encryption
- Encrypt while preserving format
- Maintain data utility
- Limit key access
- Use strong encryption

## Anonymization for Minimization

### K-Anonymity
- Generalize data to k-anonymity
- Suppress rare values
- Maintain data utility
- Verify k-anonymity

### Differential Privacy
- Add noise to data
- Protect individual privacy
- Maintain statistical utility
- Use privacy budget

### Aggregation
- Aggregate data
- Remove individual identifiers
- Use summary statistics
- Limit granularity

## Data Minimization Checklist

### Collection
- [ ] Collect only necessary fields
- [ ] Avoid optional fields
- [ ] Use progressive disclosure
- [ ] Collect at point of need
- [ ] Review collection regularly

### Processing
- [ ] Process only necessary data
- [ ] Limit processing scope
- [ ] Use data filtering
- [ ] Implement processing limits
- [ ] Review processing regularly

### Retention
- [ ] Define retention periods
- [ ] Implement automated deletion
- [ ] Regular data purging
- [ ] Secure deletion methods
- [ ] Verify deletion

### Storage
- [ ] Use appropriate storage
- [ ] Implement data compression
- [ ] Remove duplicate data
- [ ] Archive old data
- [ ] Delete obsolete data

### Access
- [ ] Limit access to necessary personnel
- [ ] Implement role-based access
- [ ] Regular access reviews
- [ ] Monitor access patterns
- [ ] Revoke unnecessary access

## Best Practices

1. **Question Everything**: Question every data field
2. **Start Minimal**: Collect minimum from start
3. **Regular Reviews**: Review data collection regularly
4. **Automated Deletion**: Implement automated deletion
5. **Purpose-Driven**: Collect for specific purposes
6. **User Control**: Let users control their data
7. **Documentation**: Document minimization measures
8. **Training**: Train staff on minimization
9. **Monitoring**: Monitor data collection and retention
10. **Continuous Improvement**: Continuously improve minimization

## Common Pitfalls

1. **Over-Collection**: Collecting more than necessary
2. **No Retention Policy**: Not defining retention periods
3. **No Deletion**: Not deleting obsolete data
4. **Broad Access**: Too many people with access
5. **No Reviews**: Not reviewing data collection
6. **Poor Documentation**: Not documenting minimization
7. **Weak Controls**: Insufficient access controls
8. **No Automation**: Manual deletion processes
9. **Insufficient Training**: Staff not trained on minimization
10. **Static Approach**: Not continuously improving

