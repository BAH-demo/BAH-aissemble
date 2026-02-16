"""
STIG V-220632 / NIST SI-10: Input Sanitization
Removes dangerous characters and prevents injection attacks.
"""

import re
import html
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_DANGEROUS_CHARS = re.compile(r'[<>"\';&|`$()\x00]')
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTIPLE_SPACES = re.compile(r"\s{2,}")


class InputSanitizer:
    """Input sanitization per STIG V-220632 / NIST SI-10."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None
        sanitized = value.strip()
        sanitized = _CONTROL_CHARS.sub("", sanitized)
        sanitized = _DANGEROUS_CHARS.sub("", sanitized)
        sanitized = _MULTIPLE_SPACES.sub(" ", sanitized)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized if sanitized else None

    @staticmethod
    def sanitize_html(value: str, max_length: int = 255) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None
        sanitized = html.escape(value.strip(), quote=True)
        sanitized = _CONTROL_CHARS.sub("", sanitized)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized if sanitized else None

    @staticmethod
    def sanitize_path(value: str) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None
        sanitized = value.strip()
        while ".." in sanitized:
            sanitized = sanitized.replace("..", "")
        sanitized = sanitized.replace("\\", "/")
        while "//" in sanitized:
            sanitized = sanitized.replace("//", "/")
        sanitized = re.sub(r"[^a-zA-Z0-9._/\-]", "", sanitized)
        return sanitized if sanitized else None

    @staticmethod
    def sanitize_sql_value(value: str) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None
        sanitized = value.strip()
        sanitized = sanitized.replace("'", "''")
        sanitized = sanitized.replace("\\", "\\\\")
        sanitized = sanitized.replace(";", "")
        sanitized = sanitized.replace("--", "")
        sanitized = sanitized.replace("/*", "")
        sanitized = sanitized.replace("*/", "")
        return sanitized if sanitized else None

    @staticmethod
    def sanitize_numeric(value) -> Optional[float]:
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("Failed to sanitize numeric value")
            return None

    @staticmethod
    def sanitize_integer(value) -> Optional[int]:
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning("Failed to sanitize integer value")
            return None

    @staticmethod
    def strip_null_bytes(value: str) -> str:
        if not isinstance(value, str):
            return ""
        return value.replace("\x00", "")
