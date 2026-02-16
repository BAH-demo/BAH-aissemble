"""
Tests for Input Validation Framework (STIG V-220631, NIST SI-10).
Covers SQL injection, XSS, path traversal, command injection patterns.
"""

import pytest
from aissemble_security.input_validation.validator import InputValidator
from aissemble_security.input_validation.sanitizer import InputSanitizer


class TestStringValidation:
    def test_valid_string(self):
        valid, msg = InputValidator.validate_string("hello world", max_length=255)
        assert valid
        assert msg == ""

    def test_empty_string_with_min_length(self):
        valid, msg = InputValidator.validate_string("", min_length=1)
        assert not valid

    def test_exceeds_max_length(self):
        valid, msg = InputValidator.validate_string("a" * 300, max_length=255)
        assert not valid
        assert "maximum length" in msg

    def test_null_bytes_rejected(self):
        valid, msg = InputValidator.validate_string("hello\x00world")
        assert not valid
        assert "null bytes" in msg

    def test_non_string_rejected(self):
        valid, msg = InputValidator.validate_string(12345)
        assert not valid


class TestAlphanumericValidation:
    def test_valid_alphanumeric(self):
        valid, _ = InputValidator.validate_alphanumeric("abc123")
        assert valid

    def test_special_chars_rejected(self):
        valid, _ = InputValidator.validate_alphanumeric("abc!@#")
        assert not valid

    def test_extended_allows_underscore_hyphen(self):
        valid, _ = InputValidator.validate_alphanumeric_extended("hello_world-123")
        assert valid


class TestEmailValidation:
    def test_valid_email(self):
        valid, _ = InputValidator.validate_email("user@example.com")
        assert valid

    def test_invalid_email_no_at(self):
        valid, _ = InputValidator.validate_email("userexample.com")
        assert not valid

    def test_invalid_email_no_domain(self):
        valid, _ = InputValidator.validate_email("user@")
        assert not valid

    def test_email_too_long(self):
        valid, _ = InputValidator.validate_email("a" * 250 + "@example.com")
        assert not valid


class TestURLValidation:
    def test_valid_https_url(self):
        valid, _ = InputValidator.validate_url("https://example.com/path")
        assert valid

    def test_http_rejected_when_https_required(self):
        valid, _ = InputValidator.validate_url("http://example.com", require_https=True)
        assert not valid

    def test_http_allowed_when_not_required(self):
        valid, _ = InputValidator.validate_url("http://example.com", require_https=False)
        assert valid


class TestNumericValidation:
    def test_valid_numeric(self):
        valid, _ = InputValidator.validate_numeric_range(42, min_val=0, max_val=100)
        assert valid

    def test_below_minimum(self):
        valid, _ = InputValidator.validate_numeric_range(-1, min_val=0, max_val=100)
        assert not valid

    def test_above_maximum(self):
        valid, _ = InputValidator.validate_numeric_range(101, min_val=0, max_val=100)
        assert not valid

    def test_non_numeric_rejected(self):
        valid, _ = InputValidator.validate_numeric_range("abc")
        assert not valid

    def test_integer_range(self):
        valid, _ = InputValidator.validate_integer_range(42, min_val=0, max_val=100)
        assert valid

    def test_integer_non_integer(self):
        valid, _ = InputValidator.validate_integer_range("abc")
        assert not valid


class TestSQLInjectionDetection:
    @pytest.mark.parametrize("payload", [
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "1 AND 1=1",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "1; DELETE FROM users",
        "' OR 'a'='a'",
        "1; EXEC xp_cmdshell('dir')",
        "SLEEP(5)",
        "BENCHMARK(1000000,SHA1('test'))",
        "WAITFOR DELAY '0:0:5'",
        "LOAD_FILE('/etc/passwd')",
        "INTO OUTFILE '/tmp/test'",
        "SELECT * FROM users",
    ])
    def test_sql_injection_detected(self, payload):
        valid, msg = InputValidator.check_sql_injection(payload)
        assert not valid, f"Failed to detect SQL injection: {payload}"
        assert "SQL injection" in msg

    def test_normal_text_passes(self):
        valid, _ = InputValidator.check_sql_injection("Hello World 123")
        assert valid


class TestXSSDetection:
    @pytest.mark.parametrize("payload", [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        '<img onerror="alert(1)" src="x">',
        "<iframe src='evil.com'>",
        "<object data='evil.swf'>",
        "<embed src='evil.swf'>",
        "expression(alert(1))",
        "vbscript:msgbox",
        "data:text/html,<script>alert(1)</script>",
        '<div onmouseover="alert(1)">',
    ])
    def test_xss_detected(self, payload):
        valid, msg = InputValidator.check_xss(payload)
        assert not valid, f"Failed to detect XSS: {payload}"
        assert "XSS" in msg

    def test_normal_html_entities_pass(self):
        valid, _ = InputValidator.check_xss("Hello &amp; World")
        assert valid


class TestPathTraversalDetection:
    @pytest.mark.parametrize("payload", [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        "%2e%2e/etc/passwd",
        "%252e%252e/etc/passwd",
    ])
    def test_path_traversal_detected(self, payload):
        valid, msg = InputValidator.check_path_traversal(payload)
        assert not valid, f"Failed to detect path traversal: {payload}"

    def test_normal_path_passes(self):
        valid, _ = InputValidator.check_path_traversal("/usr/local/bin")
        assert valid

    def test_double_slashes_detected(self):
        valid, _ = InputValidator.check_path_traversal("//etc/passwd")
        assert not valid


class TestCommandInjectionDetection:
    @pytest.mark.parametrize("payload", [
        "; rm -rf /",
        "| cat /etc/passwd",
        "& whoami",
        "$(whoami)",
        "${PATH}",
        "`id`",
        "eval('import os')",
        "exec('cmd')",
        "system('ls')",
        "os.system",
        "subprocess.call",
    ])
    def test_command_injection_detected(self, payload):
        valid, msg = InputValidator.check_command_injection(payload)
        assert not valid, f"Failed to detect command injection: {payload}"

    def test_normal_text_passes(self):
        valid, _ = InputValidator.check_command_injection("hello world 123")
        assert valid


class TestFilenameValidation:
    def test_valid_filename(self):
        valid, _ = InputValidator.validate_filename("report.pdf")
        assert valid

    def test_path_traversal_in_filename(self):
        valid, _ = InputValidator.validate_filename("../../../etc/passwd")
        assert not valid

    def test_invalid_chars_in_filename(self):
        valid, _ = InputValidator.validate_filename("file<script>.txt")
        assert not valid


class TestSafeInputValidation:
    def test_clean_input_passes(self):
        valid, _ = InputValidator.validate_safe_input("Hello World 123")
        assert valid

    def test_sql_injection_blocked(self):
        valid, _ = InputValidator.validate_safe_input("'; DROP TABLE users; --")
        assert not valid

    def test_xss_blocked(self):
        valid, _ = InputValidator.validate_safe_input("<script>alert(1)</script>")
        assert not valid

    def test_path_traversal_blocked(self):
        valid, _ = InputValidator.validate_safe_input("../../../etc/passwd")
        assert not valid

    def test_command_injection_blocked(self):
        valid, _ = InputValidator.validate_safe_input("; rm -rf /")
        assert not valid


class TestInputSanitizer:
    def test_sanitize_string_removes_dangerous_chars(self):
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result
        assert "'" not in result

    def test_sanitize_string_none_for_empty(self):
        assert InputSanitizer.sanitize_string("") is None
        assert InputSanitizer.sanitize_string("   ") is None

    def test_sanitize_string_max_length(self):
        result = InputSanitizer.sanitize_string("a" * 300, max_length=100)
        assert len(result) <= 100

    def test_sanitize_string_strips_control_chars(self):
        result = InputSanitizer.sanitize_string("hello\x01\x02world")
        assert "\x01" not in result

    def test_sanitize_html_escapes(self):
        result = InputSanitizer.sanitize_html("<b>bold</b>")
        assert "<b>" not in result
        assert "&lt;" in result

    def test_sanitize_path_removes_traversal(self):
        result = InputSanitizer.sanitize_path("../../../etc/passwd")
        assert ".." not in result

    def test_sanitize_path_normalizes_slashes(self):
        result = InputSanitizer.sanitize_path("path\\to\\file")
        assert "\\" not in result

    def test_sanitize_sql_value(self):
        result = InputSanitizer.sanitize_sql_value("O'Brien; DROP TABLE--")
        assert "'" not in result or result.count("'") % 2 == 0
        assert ";" not in result
        assert "--" not in result

    def test_sanitize_numeric_valid(self):
        assert InputSanitizer.sanitize_numeric("42.5") == 42.5

    def test_sanitize_numeric_invalid(self):
        assert InputSanitizer.sanitize_numeric("abc") is None

    def test_sanitize_integer_valid(self):
        assert InputSanitizer.sanitize_integer("42") == 42

    def test_sanitize_integer_invalid(self):
        assert InputSanitizer.sanitize_integer("abc") is None

    def test_strip_null_bytes(self):
        result = InputSanitizer.strip_null_bytes("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_non_string_returns_none(self):
        assert InputSanitizer.sanitize_string(12345) is None
        assert InputSanitizer.sanitize_html(12345) is None
        assert InputSanitizer.sanitize_path(12345) is None
