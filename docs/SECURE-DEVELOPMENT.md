# Secure Development Guidelines

> Security best practices for Java and Python development in the aissemble project, aligned with NIST SP 800-53 and DISA STIG requirements.

## Input Validation (STIG V-220631, NIST SI-10)

All user inputs must be validated using a whitelist approach before processing.

### Java

```java
import java.util.regex.Pattern;

public class InputValidator {
    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$");
    private static final int MAX_INPUT_LENGTH = 255;

    public static boolean validateEmail(String email) {
        if (email == null || email.length() > MAX_INPUT_LENGTH) {
            return false;
        }
        return EMAIL_PATTERN.matcher(email).matches();
    }

    public static boolean validateUsername(String username) {
        if (username == null || username.length() < 3 || username.length() > 32) {
            return false;
        }
        return username.matches("^[a-zA-Z0-9_-]+$");
    }
}
```

### Python

```python
import re

def validate_input(value: str, pattern: str, max_length: int = 255) -> bool:
    if not value or len(value) > max_length:
        return False
    return bool(re.match(pattern, value))

def sanitize_string(user_input: str, max_length: int = 255) -> str | None:
    if not user_input or len(user_input) > max_length:
        return None
    sanitized = re.sub(r'[<>"\';&|`$()]', '', user_input.strip())
    return sanitized if sanitized else None
```

## Input Sanitization (STIG V-220632, NIST SI-10)

Use parameterized queries for all database operations. Never concatenate user input into queries.

### Java (JPA/Hibernate)

```java
// CORRECT - Parameterized query
TypedQuery<User> query = em.createQuery(
    "SELECT u FROM User u WHERE u.id = :userId", User.class);
query.setParameter("userId", userId);

// WRONG - SQL injection vulnerable
String sql = "SELECT * FROM users WHERE id = " + userId;
```

### Python (SQLAlchemy)

```python
# CORRECT - Parameterized query
result = db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})

# WRONG - SQL injection vulnerable
result = db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

## Authentication (STIG V-220629, NIST IA-2, IA-5)

### Password Requirements

- Minimum 14 characters
- Must include: uppercase, lowercase, digit, special character
- Hash with bcrypt (12 rounds minimum)
- Never store plaintext passwords

### Account Lockout

- Lock account after 5 failed login attempts
- 15-minute lockout duration
- Log all failed attempts with IP address

### Java Password Hashing

```java
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);
String hash = encoder.encode(password);
boolean matches = encoder.matches(password, hash);
```

## Session Management (STIG V-220630, NIST AC-12)

- Session timeout: 15 minutes of inactivity
- Bind sessions to originating IP address
- Regenerate session ID after authentication
- Secure cookie flags: `Secure`, `HttpOnly`, `SameSite=Strict`

### Java (Spring Boot)

```yaml
# application.yml
server:
  servlet:
    session:
      timeout: 15m
      cookie:
        secure: true
        http-only: true
        same-site: strict
```

## Encryption (STIG V-220633, V-220634, NIST SC-8, SC-28)

- **At rest**: AES-256 for all sensitive data
- **In transit**: TLS 1.2+ required for all communications
- **Key management**: Store encryption keys securely, never in code
- **Disabled protocols**: SSLv2, SSLv3, TLS 1.0, TLS 1.1

### Java TLS Configuration

```yaml
# application.yml
server:
  ssl:
    protocol: TLS
    enabled-protocols: TLSv1.2,TLSv1.3
```

## Audit Logging (STIG V-220635, NIST AU-2, AU-3)

Log the following events in structured JSON format:

| Event | When to Log |
|-------|------------|
| `authentication_success` | User successfully authenticates |
| `authentication_failure` | Authentication attempt fails |
| `account_lockout` | Account locked due to failed attempts |
| `authorization_failure` | Access denied to resource |
| `data_access` | Sensitive data read |
| `data_modification` | Data created, updated, or deleted |
| `admin_action` | Privileged operation performed |
| `security_violation` | Security rule violated |

### Required Log Fields

```json
{
    "timestamp": "2026-01-11T19:30:00Z",
    "event_type": "authentication_failure",
    "severity": "WARNING",
    "user_id": "anonymous",
    "ip_address": "192.168.1.1",
    "outcome": "failure",
    "details": {
        "username": "john.doe",
        "reason": "invalid_password"
    }
}
```

### Java (SLF4J/Logback)

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

Logger auditLogger = LoggerFactory.getLogger("audit");
auditLogger.info("{\"timestamp\":\"{}\",\"event\":\"{}\",\"user\":\"{}\",\"ip\":\"{}\"}",
    Instant.now(), "authentication_success", userId, ipAddress);
```

## Security Headers (STIG V-220641, NIST SI-11)

All HTTP responses must include:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS filter |
| `Content-Security-Policy` | `default-src 'self'` | Restrict resource loading |

### Java (Spring Boot)

```java
@Configuration
public class SecurityHeadersConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.headers(headers -> headers
            .httpStrictTransportSecurity(hsts -> hsts
                .includeSubDomains(true)
                .maxAgeInSeconds(31536000))
            .frameOptions(frame -> frame.deny())
            .contentTypeOptions(content -> {})
            .xssProtection(xss -> xss.headerValue(
                XXssProtectionHeaderWriter.HeaderValue.ENABLED_MODE_BLOCK))
            .contentSecurityPolicy(csp -> csp
                .policyDirectives("default-src 'self'"))
        );
        return http.build();
    }
}
```

## Error Handling (STIG V-220641, NIST SI-11)

- Return generic error messages to users
- Log detailed errors internally with stack traces
- Never expose internal implementation details

### Java

```java
try {
    processData(data);
} catch (Exception e) {
    logger.error("Processing error: {}", e.getMessage(), e);
    return ResponseEntity.status(500)
        .body(Map.of("error", "An error occurred"));
}
```

## Secrets Management

- Never hardcode secrets, API keys, or credentials in source code
- Use environment variables or a secret manager (e.g., AWS Secrets Manager, HashiCorp Vault)
- Add sensitive files to `.gitignore`
- Rotate secrets regularly

## References

- [NIST SP 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [NIST SP 800-207 Zero Trust Architecture](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- [DISA STIGs](https://public.cyber.mil/stigs/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Federal Security Compliance Framework](https://github.com/COG-GTM/fedreral_security_comliance)
