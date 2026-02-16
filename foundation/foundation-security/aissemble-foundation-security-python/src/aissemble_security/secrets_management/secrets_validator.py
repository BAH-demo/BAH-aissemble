"""
STIG V-220633/V-220634: Secrets Management
Validates environment variable configuration and detects hardcoded secrets.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

_SECRET_PATTERNS = [
    re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']+', re.IGNORECASE),
    re.compile(r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', re.IGNORECASE),
    re.compile(r'(?:secret|token)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', re.IGNORECASE),
    re.compile(r'(?:access[_-]?key|aws[_-]?key)\s*[=:]\s*["\']?[A-Z0-9]{16,}', re.IGNORECASE),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'(?:private[_-]?key|ssh[_-]?key)\s*[=:]\s*["\']?[^\s"\']+', re.IGNORECASE),
    re.compile(r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'(?:bearer|authorization)\s*[=:]\s*["\']?[A-Za-z0-9_\-\.]{20,}', re.IGNORECASE),
    re.compile(r'jdbc:[a-z]+://[^@]*:[^@]*@', re.IGNORECASE),
    re.compile(r'(?:mysql|postgres|mongodb)://[^:]+:[^@]+@', re.IGNORECASE),
]

_EXCLUDED_EXTENSIONS = {
    ".pyc", ".class", ".jar", ".war", ".ear", ".zip", ".tar", ".gz",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
}

_EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".tox", ".pytest_cache",
    "target", "build", "dist", ".eggs", ".mypy_cache",
}


class SecretsValidator:
    """Validates secrets configuration and scans for hardcoded credentials."""

    def __init__(self, required_vars: Optional[List[str]] = None):
        self._required_vars = required_vars or []

    def validate_environment(self) -> Tuple[bool, List[str]]:
        missing = []
        for var in self._required_vars:
            value = os.environ.get(var)
            if not value:
                missing.append(var)
                logger.warning("Required environment variable not set: %s", var)
            elif value.startswith("CHANGEME") or value == "default":
                missing.append(var)
                logger.warning("Environment variable has placeholder value: %s", var)
        if missing:
            logger.error(
                "Environment validation failed. Missing or invalid vars: %s",
                ", ".join(missing),
            )
            return False, missing
        return True, []

    @staticmethod
    def scan_file_for_secrets(file_path: str) -> List[Dict[str, str]]:
        findings = []
        path = Path(file_path)
        if path.suffix in _EXCLUDED_EXTENSIONS:
            return findings
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            return findings

        _env_ref = re.compile(r'os\.environ|os\.getenv|System\.getenv|\$\{|%[A-Z_]+%', re.IGNORECASE)
        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if _env_ref.search(line):
                continue
            for pattern in _SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append({
                        "file": str(path),
                        "line": str(line_num),
                        "pattern": pattern.pattern[:60],
                        "match": match.group(0)[:80],
                    })
        return findings

    @staticmethod
    def scan_directory_for_secrets(directory: str) -> List[Dict[str, str]]:
        findings = []
        root = Path(directory)
        if not root.is_dir():
            logger.error("Directory does not exist: %s", directory)
            return findings

        for path in root.rglob("*"):
            if any(excluded in path.parts for excluded in _EXCLUDED_DIRS):
                continue
            if not path.is_file():
                continue
            if path.suffix in _EXCLUDED_EXTENSIONS:
                continue
            file_findings = SecretsValidator.scan_file_for_secrets(str(path))
            findings.extend(file_findings)

        return findings
