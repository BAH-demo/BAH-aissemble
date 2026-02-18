# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |

## Reporting a Vulnerability

Please submit a Draft Security Advisory to the administrators of the aissemble project.

1. Navigate to the **Security** tab in GitHub.
2. Click **"Report a vulnerability"**.
3. Fill out the advisory form with details of the vulnerability.
4. Click **"Submit report"**.

We will acknowledge receipt within 48 hours and provide an initial assessment within 5 business days.

## Federal Security Compliance

This project follows federal security standards including NIST SP 800-53 Rev 5 and DISA STIG requirements.

### NIST SP 800-53 Control Families

| Control Family | ID | Description |
|---|---|---|
| Access Control | AC-2, AC-3, AC-6, AC-7, AC-12 | Account management, access enforcement, least privilege, session controls |
| Audit and Accountability | AU-2, AU-3 | Audit events, content of audit records |
| Identification and Authentication | IA-2, IA-5 | Multi-factor authentication, authenticator management |
| System and Communications Protection | SC-7, SC-8, SC-28 | Boundary protection, transmission confidentiality, data-at-rest protection |
| System and Information Integrity | SI-2, SI-10, SI-11 | Flaw remediation, input validation, error handling |

### STIG Compliance

| STIG ID | Control | Status |
|---|---|---|
| V-220629 | Authentication and password policy | Documented |
| V-220630 | Session management (15-min timeout, IP binding) | Documented |
| V-220631 | Input validation (whitelist approach) | Documented |
| V-220632 | Input sanitization (parameterized queries) | Documented |
| V-220633 | Encryption at rest (AES-256) | Documented |
| V-220634 | Encryption in transit (TLS 1.2+) | Documented |
| V-220635 | Audit logging (structured JSON) | Documented |
| V-220641 | Security headers and error handling | Documented |

### Zero Trust Architecture (NIST SP 800-207)

This project aligns with Zero Trust principles:

- **Never trust, always verify** - All requests must carry verified identity
- **Least privilege access** - Default deny, explicit grants only
- **Continuous verification** - Session validation on every request
- **Full audit trail** - All security events logged

## Secure Development Practices

- All dependencies are scanned for known vulnerabilities via Dependabot
- Static application security testing (SAST) is performed via CodeQL
- Secrets must never be hardcoded; use environment variables or secret managers
- All user inputs must be validated and sanitized
- Database queries must use parameterized statements
- Error messages must be generic to users; detailed logs kept internally

## References

- [NIST SP 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [NIST SP 800-207 Zero Trust Architecture](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- [DISA STIGs](https://public.cyber.mil/stigs/)
- [Federal Security Compliance Framework](https://github.com/COG-GTM/fedreral_security_comliance)
