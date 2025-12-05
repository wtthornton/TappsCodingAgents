# HIPAA Compliance Guidelines

## Protected Health Information (PHI)

### What is PHI?
Any information that can identify a patient:
- Names, addresses, phone numbers
- Medical record numbers
- Dates (birth, admission, discharge, death)
- Social Security numbers
- Email addresses
- Biometric identifiers
- Full-face photos

### PHI Handling Requirements

#### Storage
- **Encryption**: All PHI must be encrypted at rest (AES-256 minimum)
- **Access Control**: Role-based access with audit logs
- **Location**: Store in HIPAA-compliant cloud regions (US-based for US healthcare)

#### Transmission
- **Encryption**: TLS 1.2+ for data in transit
- **Secure Channels**: Never send PHI via unencrypted email
- **API Security**: Use OAuth 2.0, API keys with rotation

#### Access
- **Authentication**: MFA required for all user accounts
- **Authorization**: Principle of least privilege
- **Audit Trails**: Log all PHI access (who, what, when)
- **Session Management**: Auto-logout after inactivity

## Technical Safeguards

### Access Controls
```yaml
# Example access control policy
access_controls:
  - role: physician
    permissions:
      - read: own_patients
      - write: own_patients
      - read: shared_cases
  
  - role: nurse
    permissions:
      - read: assigned_patients
      - write: assigned_patients_notes
  
  - role: receptionist
    permissions:
      - read: appointment_info
      - write: appointment_scheduling
      - no_phi_access: true
```

### Audit Logging Requirements
- Log all PHI access attempts (successful and failed)
- Include: user ID, timestamp, action, resource accessed
- Retain logs for minimum 6 years
- Monitor for suspicious access patterns

### Data Integrity
- Prevent unauthorized alteration of PHI
- Use cryptographic hashing for verification
- Version control for medical records
- Immutable audit logs

## Administrative Safeguards

### Workforce Training
- Annual HIPAA training for all staff
- Incident response procedures
- Privacy policy acknowledgment

### Business Associate Agreements (BAA)
- Required for all third-party vendors handling PHI
- Clearly define responsibilities
- Include breach notification requirements

### Incident Response
1. **Detect**: Identify potential breach within 1 hour
2. **Contain**: Isolate affected systems immediately
3. **Assess**: Determine scope and impact
4. **Notify**: Report to patients and HHS within 60 days if >500 affected
5. **Remediate**: Fix vulnerabilities, prevent recurrence

## Common Pitfalls

### ❌ Don't Do This
- Store PHI in unencrypted databases
- Send PHI via SMS or unencrypted email
- Share credentials between users
- Skip audit logging for "convenience"
- Store PHI in non-US regions without proper agreements

### ✅ Do This Instead
- Encrypt all PHI at rest and in transit
- Use secure messaging platforms for PHI communication
- Implement proper authentication and authorization
- Log all access comprehensively
- Use HIPAA-compliant cloud providers with BAA

## Implementation Checklist

- [ ] Encrypt all PHI at rest (AES-256)
- [ ] Encrypt all PHI in transit (TLS 1.2+)
- [ ] Implement role-based access control
- [ ] Set up comprehensive audit logging
- [ ] Require MFA for all users
- [ ] Execute BAAs with all vendors
- [ ] Establish incident response procedures
- [ ] Conduct regular security assessments
- [ ] Train workforce annually
- [ ] Document all security policies

