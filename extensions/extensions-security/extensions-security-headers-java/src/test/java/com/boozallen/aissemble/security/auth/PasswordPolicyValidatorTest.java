package com.boozallen.aissemble.security.auth;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PasswordPolicyValidatorTest {

    private PasswordPolicyValidator validator;

    @BeforeEach
    void setUp() {
        validator = new PasswordPolicyValidator();
    }

    @Test
    void testValidPassword() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("SecureP@ss1234!");
        assertTrue(result.isValid());
        assertTrue(result.getViolations().isEmpty());
    }

    @Test
    void testTooShortPassword() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("Short1!");
        assertFalse(result.isValid());
        assertTrue(result.getViolations().stream().anyMatch(v -> v.contains("14 characters")));
    }

    @Test
    void testMissingUppercase() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("securepassword1!");
        assertFalse(result.isValid());
        assertTrue(result.getViolations().stream().anyMatch(v -> v.contains("uppercase")));
    }

    @Test
    void testMissingLowercase() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("SECUREPASSWORD1!");
        assertFalse(result.isValid());
        assertTrue(result.getViolations().stream().anyMatch(v -> v.contains("lowercase")));
    }

    @Test
    void testMissingDigit() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("SecurePassword!!");
        assertFalse(result.isValid());
        assertTrue(result.getViolations().stream().anyMatch(v -> v.contains("digit")));
    }

    @Test
    void testMissingSpecialCharacter() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("SecurePassword12");
        assertFalse(result.isValid());
        assertTrue(result.getViolations().stream().anyMatch(v -> v.contains("special")));
    }

    @Test
    void testNullPassword() {
        PasswordPolicyValidator.ValidationResult result = validator.validate(null);
        assertFalse(result.isValid());
    }

    @Test
    void testEmptyPassword() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("");
        assertFalse(result.isValid());
    }

    @Test
    void testMinLength14ByDefault() {
        assertEquals(14, validator.getMinLength());
    }

    @Test
    void testExactly14CharacterPasswordValid() {
        PasswordPolicyValidator.ValidationResult result = validator.validate("Abcdefg1234!@#");
        assertTrue(result.isValid());
    }

    @Test
    void testCustomMinLength() {
        PasswordPolicyValidator custom = new PasswordPolicyValidator(8, true, true, true, true);
        PasswordPolicyValidator.ValidationResult result = custom.validate("Secure1!");
        assertTrue(result.isValid());
    }
}
