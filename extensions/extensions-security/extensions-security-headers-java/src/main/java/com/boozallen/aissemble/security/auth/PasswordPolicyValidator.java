package com.boozallen.aissemble.security.auth;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * STIG V-220629 / NIST IA-5: Password Policy Validation.
 * Enforces minimum 14 characters with complexity requirements.
 */
public class PasswordPolicyValidator {

    private static final Logger LOG = LoggerFactory.getLogger(PasswordPolicyValidator.class);

    private final int minLength;
    private final boolean requireUppercase;
    private final boolean requireLowercase;
    private final boolean requireDigit;
    private final boolean requireSpecial;

    public PasswordPolicyValidator() {
        this(14, true, true, true, true);
    }

    public PasswordPolicyValidator(int minLength, boolean requireUppercase,
            boolean requireLowercase, boolean requireDigit, boolean requireSpecial) {
        this.minLength = minLength;
        this.requireUppercase = requireUppercase;
        this.requireLowercase = requireLowercase;
        this.requireDigit = requireDigit;
        this.requireSpecial = requireSpecial;
    }

    public ValidationResult validate(String password) {
        List<String> violations = new ArrayList<>();

        if (password == null || password.isEmpty()) {
            violations.add("Password must not be empty");
            return new ValidationResult(false, violations);
        }

        if (password.length() < minLength) {
            violations.add("Password must be at least " + minLength + " characters");
        }

        if (requireUppercase && !password.chars().anyMatch(Character::isUpperCase)) {
            violations.add("Password must contain at least one uppercase letter");
        }

        if (requireLowercase && !password.chars().anyMatch(Character::isLowerCase)) {
            violations.add("Password must contain at least one lowercase letter");
        }

        if (requireDigit && !password.chars().anyMatch(Character::isDigit)) {
            violations.add("Password must contain at least one digit");
        }

        if (requireSpecial && password.chars().allMatch(c -> Character.isLetterOrDigit(c))) {
            violations.add("Password must contain at least one special character");
        }

        boolean isValid = violations.isEmpty();
        if (!isValid) {
            LOG.warn("Password policy violation: {}", String.join("; ", violations));
        }
        return new ValidationResult(isValid, violations);
    }

    public int getMinLength() {
        return minLength;
    }

    public static class ValidationResult {
        private final boolean valid;
        private final List<String> violations;

        public ValidationResult(boolean valid, List<String> violations) {
            this.valid = valid;
            this.violations = Collections.unmodifiableList(violations);
        }

        public boolean isValid() {
            return valid;
        }

        public List<String> getViolations() {
            return violations;
        }
    }
}
