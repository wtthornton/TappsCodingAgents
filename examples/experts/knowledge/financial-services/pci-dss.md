# PCI DSS Compliance Guide

## Payment Card Industry Data Security Standard

### Scope

#### What's Included
- Cardholder data (PAN, cardholder name, expiration date)
- Sensitive authentication data (CVV, PIN, track data)
- Systems that store, process, or transmit cardholder data

#### What's Excluded
- Systems that only display masked card numbers
- Systems with no cardholder data access

## 12 PCI DSS Requirements

### Build and Maintain Secure Systems

**1. Install and maintain firewall configuration**
- Default deny firewall rules
- Document firewall rules with business justification
- Review firewall rules quarterly

**2. Do not use vendor-supplied defaults**
- Change all default passwords
- Remove unnecessary default accounts
- Use unique credentials for each system

**3. Protect stored cardholder data**
- Encrypt cardholder data (AES-256)
- Mask PAN when displaying (first 6, last 4 digits only)
- Never store CVV or track data after authorization
- Implement key management procedures

**4. Encrypt transmission of cardholder data**
- Use TLS 1.2+ for all transmissions
- Never send cardholder data via end-user messaging (email, chat)
- Use strong encryption protocols

### Maintain Vulnerability Management

**5. Use and regularly update anti-virus**
- Deploy anti-virus on all systems commonly affected by malware
- Keep signatures updated
- Generate audit logs

**6. Develop and maintain secure systems**
- Establish secure development lifecycle
- Patch systems within 30 days for critical vulnerabilities
- Separate development/test/production environments

### Implement Strong Access Control

**7. Restrict access to cardholder data**
- Principle of least privilege
- Role-based access control
- Document access needs by role

**8. Identify and authenticate access**
- Unique user IDs for each person
- Strong passwords (8+ chars, complexity requirements)
- MFA for remote access
- Lockout after failed attempts

**9. Restrict physical access**
- Secure data center facilities
- Visitor logs and badges
- Video surveillance for sensitive areas

### Monitor and Test Networks

**10. Track and monitor access**
- Log all access to cardholder data
- Time-synchronized clocks
- Log reviews daily
- Retain logs for at least one year

**11. Regularly test security systems**
- Quarterly vulnerability scans
- Annual penetration testing
- Use intrusion detection/prevention systems

### Maintain Information Security Policy

**12. Maintain information security policy**
- Written security policy
- Annual security awareness training
- Incident response plan
- Business continuity plan

## Implementation Best Practices

### Data Minimization
- Collect only necessary cardholder data
- Delete data when no longer needed
- Mask PAN everywhere except where required

### Tokenization
- Replace cardholder data with tokens
- Tokens are not in scope of PCI DSS
- Original cardholder data stored securely

### Segmentation
- Isolate cardholder data environment (CDE) from rest of network
- Network segmentation reduces scope of PCI DSS assessment
- Use firewalls to restrict access to CDE

### Key Management
- Generate strong cryptographic keys
- Secure key storage (HSM preferred)
- Key rotation procedures
- Key access limited to authorized personnel

## Compliance Levels

### Level 1
- 6M+ transactions/year
- Annual on-site assessment by QSA
- Quarterly network scans

### Level 2
- 1M-6M transactions/year
- Annual self-assessment questionnaire (SAQ)
- Quarterly network scans

### Level 3
- 20K-1M e-commerce transactions/year
- Annual SAQ
- Quarterly network scans

### Level 4
- <20K e-commerce transactions/year
- Annual SAQ
- Quarterly network scans (recommended)

## Common Mistakes

### ❌ Avoid
- Storing CVV after authorization
- Sending cardholder data via email
- Weak encryption (using outdated protocols)
- Shared accounts
- Insufficient logging
- Skipping quarterly scans

### ✅ Do Instead
- Delete CVV immediately after authorization
- Use secure payment APIs
- Use strong encryption (TLS 1.2+, AES-256)
- Individual user accounts with MFA
- Comprehensive audit logging
- Regular vulnerability assessments

