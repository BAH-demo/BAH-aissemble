"""
STIG V-220631 / NIST SI-10: Input Validation Framework
Provides whitelist-based input validation with structured audit logging.
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_PATH_TRAVERSAL_PATTERNS = [
    re.compile(r"\.\./"),
    re.compile(r"\.\.\\"),
    re.compile(r"%2e%2e[/\\]", re.IGNORECASE),
    re.compile(r"%252e%252e[/\\]", re.IGNORECASE),
    re.compile(r"\.\./", re.IGNORECASE),
]

_SQL_INJECTION_PATTERNS = [
    re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|UNION|DECLARE)\b)", re.IGNORECASE),
    re.compile(r"('|--|;|/\*|\*/|@@|@)", re.IGNORECASE),
    re.compile(r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(\b(OR|AND)\b\s+'[^']*'\s*=\s*'[^']*')", re.IGNORECASE),
    re.compile(r"(\bSLEEP\s*\()", re.IGNORECASE),
    re.compile(r"(\bBENCHMARK\s*\()", re.IGNORECASE),
    re.compile(r"(\bWAITFOR\b)", re.IGNORECASE),
    re.compile(r"(\bLOAD_FILE\s*\()", re.IGNORECASE),
    re.compile(r"(\bINTO\s+OUTFILE\b)", re.IGNORECASE),
]

_XSS_PATTERNS = [
    re.compile(r"<script\b", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe\b", re.IGNORECASE),
    re.compile(r"<object\b", re.IGNORECASE),
    re.compile(r"<embed\b", re.IGNORECASE),
    re.compile(r"<img\b[^>]+\bonerror\b", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"vbscript:", re.IGNORECASE),
    re.compile(r"data:text/html", re.IGNORECASE),
]

_COMMAND_INJECTION_PATTERNS = [
    re.compile(r"[;&|`$]"),
    re.compile(r"\$\("),
    re.compile(r"\$\{"),
    re.compile(r"\beval\b"),
    re.compile(r"\bexec\b"),
    re.compile(r"\bsystem\b"),
    re.compile(r"\bos\."),
    re.compile(r"\bsubprocess\b"),
]

_ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")
_ALPHANUMERIC_EXTENDED_PATTERN = re.compile(r"^[a-zA-Z0-9_\-. ]+$")
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_URL_PATTERN = re.compile(
    r"^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*"
    r"(:\d{1,5})?(/[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=\-%]*)?$"
)
_SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._\-]*$")


class InputValidator:
    """Whitelist-based input validation per STIG V-220631 / NIST SI-10."""

    @staticmethod
    def validate_string(
        value: str,
        max_length: int = 255,
        min_length: int = 0,
        pattern: Optional[re.Pattern] = None,
    ) -> Tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string"
        if len(value) < min_length:
            return False, f"Value must be at least {min_length} characters"
        if len(value) > max_length:
            return False, f"Value exceeds maximum length of {max_length}"
        if "\x00" in value:
            return False, "Value contains null bytes"
        if pattern and not pattern.match(value):
            return False, "Value does not match required pattern"
        return True, ""

    @staticmethod
    def validate_alphanumeric(value: str, max_length: int = 255) -> Tuple[bool, str]:
        valid, msg = InputValidator.validate_string(value, max_length=max_length, min_length=1)
        if not valid:
            return valid, msg
        if not _ALPHANUMERIC_PATTERN.match(value):
            return False, "Value must contain only alphanumeric characters"
        return True, ""

    @staticmethod
    def validate_alphanumeric_extended(value: str, max_length: int = 255) -> Tuple[bool, str]:
        valid, msg = InputValidator.validate_string(value, max_length=max_length, min_length=1)
        if not valid:
            return valid, msg
        if not _ALPHANUMERIC_EXTENDED_PATTERN.match(value):
            return False, "Value contains disallowed characters"
        return True, ""

    @staticmethod
    def validate_email(value: str) -> Tuple[bool, str]:
        valid, msg = InputValidator.validate_string(value, max_length=254, min_length=3)
        if not valid:
            return valid, msg
        if not _EMAIL_PATTERN.match(value):
            return False, "Invalid email format"
        return True, ""

    @staticmethod
    def validate_url(value: str, require_https: bool = True) -> Tuple[bool, str]:
        valid, msg = InputValidator.validate_string(value, max_length=2048, min_length=8)
        if not valid:
            return valid, msg
        if require_https and not value.startswith("https://"):
            return False, "URL must use HTTPS"
        if not _URL_PATTERN.match(value):
            return False, "Invalid URL format"
        return True, ""

    @staticmethod
    def validate_numeric_range(
        value, min_val: float = float("-inf"), max_val: float = float("inf")
    ) -> Tuple[bool, str]:
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, "Value is not a valid number"
        if num_value < min_val:
            return False, f"Value {num_value} is below minimum {min_val}"
        if num_value > max_val:
            return False, f"Value {num_value} exceeds maximum {max_val}"
        return True, ""

    @staticmethod
    def validate_integer_range(
        value, min_val: int = -(2**31), max_val: int = 2**31 - 1
    ) -> Tuple[bool, str]:
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False, "Value is not a valid integer"
        if int_value < min_val:
            return False, f"Value {int_value} is below minimum {min_val}"
        if int_value > max_val:
            return False, f"Value {int_value} exceeds maximum {max_val}"
        return True, ""

    @staticmethod
    def check_path_traversal(value: str) -> Tuple[bool, str]:
        for pattern in _PATH_TRAVERSAL_PATTERNS:
            if pattern.search(value):
                logger.warning("Path traversal attempt detected: %s", value[:100])
                return False, "Path traversal detected"
        normalized = value.replace("\\", "/")
        if "//" in normalized:
            return False, "Double slashes detected in path"
        return True, ""

    @staticmethod
    def check_sql_injection(value: str) -> Tuple[bool, str]:
        for pattern in _SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                logger.warning("SQL injection attempt detected: %s", value[:100])
                return False, "Potential SQL injection detected"
        return True, ""

    @staticmethod
    def check_xss(value: str) -> Tuple[bool, str]:
        for pattern in _XSS_PATTERNS:
            if pattern.search(value):
                logger.warning("XSS attempt detected: %s", value[:100])
                return False, "Potential XSS attack detected"
        return True, ""

    @staticmethod
    def check_command_injection(value: str) -> Tuple[bool, str]:
        for pattern in _COMMAND_INJECTION_PATTERNS:
            if pattern.search(value):
                logger.warning("Command injection attempt detected: %s", value[:100])
                return False, "Potential command injection detected"
        return True, ""

    @staticmethod
    def validate_filename(value: str) -> Tuple[bool, str]:
        valid, msg = InputValidator.validate_string(value, max_length=255, min_length=1)
        if not valid:
            return valid, msg
        traversal_ok, traversal_msg = InputValidator.check_path_traversal(value)
        if not traversal_ok:
            return traversal_ok, traversal_msg
        if not _SAFE_FILENAME_PATTERN.match(value):
            return False, "Filename contains disallowed characters"
        return True, ""

    @staticmethod
    def validate_safe_input(value: str, max_length: int = 255) -> Tuple[bool, str]:
        valid, msg = InputValidator.validate_string(value, max_length=max_length)
        if not valid:
            return valid, msg
        traversal_ok, traversal_msg = InputValidator.check_path_traversal(value)
        if not traversal_ok:
            return traversal_ok, traversal_msg
        sql_ok, sql_msg = InputValidator.check_sql_injection(value)
        if not sql_ok:
            return sql_ok, sql_msg
        xss_ok, xss_msg = InputValidator.check_xss(value)
        if not xss_ok:
            return xss_ok, xss_msg
        cmd_ok, cmd_msg = InputValidator.check_command_injection(value)
        if not cmd_ok:
            return cmd_ok, cmd_msg
        return True, ""
