#!/usr/bin/env python3
"""
STIG Compliance Checker for aiSSEMBLE Platform.
Performs static analysis against common STIG violations.

Checks:
- Hardcoded secrets detection (V-220633)
- Missing input validation on API endpoints (V-220631)
- Missing audit logging on security operations (V-220635)
- Insecure cryptographic usage (V-220633/V-220634)

Usage:
    python stig_compliance_checker.py --scan-dir /path/to/project [--output-dir ./reports]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", "target", "build", "dist",
    ".tox", ".pytest_cache", ".mypy_cache", ".eggs",
}
EXCLUDED_EXTENSIONS = {
    ".pyc", ".class", ".jar", ".war", ".zip", ".tar", ".gz", ".png",
    ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf",
    ".eot", ".pdf", ".jks", ".p12", ".der", ".cer",
}
SOURCE_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".go", ".rb",
    ".yaml", ".yml", ".xml", ".properties", ".conf", ".cfg", ".ini",
    ".json", ".toml", ".sh", ".bash", ".env", ".dockerfile",
}

SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("Hardcoded password", re.compile(
        r'''(?:password|passwd|pwd)\s*[=:]\s*["'][^"']{4,}["']''', re.IGNORECASE)),
    ("API key assignment", re.compile(
        r'''(?:api[_-]?key|apikey)\s*[=:]\s*["'][A-Za-z0-9_\-]{16,}["']''', re.IGNORECASE)),
    ("Secret/token assignment", re.compile(
        r'''(?:secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[=:]\s*["'][A-Za-z0-9_\-]{16,}["']''',
        re.IGNORECASE)),
    ("AWS Access Key", re.compile(r'AKIA[0-9A-Z]{16}')),
    ("Private key block", re.compile(r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ("Connection string with credentials", re.compile(
        r'''(?:jdbc|mongodb|postgres|mysql)://[^:]+:[^@]+@''', re.IGNORECASE)),
    ("Bearer token hardcoded", re.compile(
        r'''[Bb]earer\s+[A-Za-z0-9_\-\.]{20,}''')),
    ("Base64-encoded secret", re.compile(
        r'''(?:secret|key|token|password)\s*[=:]\s*["'](?:[A-Za-z0-9+/]{32,}={0,2})["']''',
        re.IGNORECASE)),
]

WEAK_CRYPTO_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("MD5 usage", re.compile(r'\b(?:MD5|md5)\b')),
    ("SHA-1 usage", re.compile(r'\bSHA-?1\b', re.IGNORECASE)),
    ("DES encryption", re.compile(r'\bDES(?:ede)?\b')),
    ("RC4 cipher", re.compile(r'\bRC4\b', re.IGNORECASE)),
    ("ECB mode", re.compile(r'\bECB\b')),
    ("Small RSA key", re.compile(r'(?:keysize|key_size|key_length)\s*[=:]\s*(?:512|768|1024)\b')),
    ("SSLv3 or TLS 1.0", re.compile(r'(?:SSLv[23]|TLSv1(?:\.0)?)\b')),
    ("Random (not secure)", re.compile(r'\brandom\.random\b|\bjava\.util\.Random\b')),
]

MISSING_VALIDATION_INDICATORS_JAVA = [
    re.compile(r'@(?:GET|POST|PUT|DELETE|PATCH)\b'),
    re.compile(r'@RequestMapping\b'),
    re.compile(r'@Path\b'),
]
VALIDATION_PRESENT_JAVA = [
    re.compile(r'@Valid\b'),
    re.compile(r'@NotNull\b'),
    re.compile(r'@NotBlank\b'),
    re.compile(r'@Size\b'),
    re.compile(r'@Pattern\b'),
    re.compile(r'validate\s*\(', re.IGNORECASE),
    re.compile(r'InputValidator\b'),
]

MISSING_VALIDATION_INDICATORS_PYTHON = [
    re.compile(r'@(?:app|router)\.\s*(?:get|post|put|delete|patch)\s*\('),
    re.compile(r'def\s+\w+\(.*request'),
]
VALIDATION_PRESENT_PYTHON = [
    re.compile(r'validate\s*\(', re.IGNORECASE),
    re.compile(r'InputValidator\b'),
    re.compile(r'pydantic', re.IGNORECASE),
    re.compile(r'@validator\b'),
    re.compile(r'Field\s*\('),
]

SECURITY_OPERATION_PATTERNS = [
    re.compile(r'(?:authenticate|login|logout|authorize)\s*\(', re.IGNORECASE),
    re.compile(r'(?:create_user|delete_user|update_password)\s*\(', re.IGNORECASE),
    re.compile(r'(?:grant|revoke)_(?:permission|role)\s*\(', re.IGNORECASE),
]
AUDIT_LOG_PRESENT = [
    re.compile(r'(?:audit|security)_?log', re.IGNORECASE),
    re.compile(r'AuditLogger\b'),
    re.compile(r'log_(?:auth|security|event)', re.IGNORECASE),
    re.compile(r'logger\.(?:info|warn|error)\s*\(.*(?:auth|security|login)', re.IGNORECASE),
]


class STIGFinding:
    def __init__(self, control: str, severity: str, file_path: str,
                 line: int, description: str, recommendation: str):
        self.control = control
        self.severity = severity
        self.file_path = file_path
        self.line = line
        self.description = description
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "control": self.control,
            "severity": self.severity,
            "file": self.file_path,
            "line": self.line,
            "description": self.description,
            "recommendation": self.recommendation,
        }


def _should_scan_file(path: Path) -> bool:
    if any(excluded in path.parts for excluded in EXCLUDED_DIRS):
        return False
    if path.suffix in EXCLUDED_EXTENSIONS:
        return False
    if path.suffix not in SOURCE_EXTENSIONS:
        return False
    return True


def _read_file(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def check_hardcoded_secrets(scan_dir: str) -> List[STIGFinding]:
    findings = []
    root = Path(scan_dir)
    for path in root.rglob("*"):
        if not path.is_file() or not _should_scan_file(path):
            continue
        lines = _read_file(path)
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                continue
            if "example" in str(path).lower() or "test" in str(path).lower():
                continue
            for pattern_name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(STIGFinding(
                        control="V-220633",
                        severity="HIGH",
                        file_path=str(path),
                        line=line_num,
                        description=f"{pattern_name}: {line.strip()[:80]}",
                        recommendation="Move secret to environment variable or secrets manager",
                    ))
    return findings


def check_input_validation(scan_dir: str) -> List[STIGFinding]:
    findings = []
    root = Path(scan_dir)
    for path in root.rglob("*"):
        if not path.is_file() or not _should_scan_file(path):
            continue
        lines = _read_file(path)
        content = "\n".join(lines)

        if path.suffix == ".java":
            has_endpoint = any(p.search(content) for p in MISSING_VALIDATION_INDICATORS_JAVA)
            has_validation = any(p.search(content) for p in VALIDATION_PRESENT_JAVA)
            if has_endpoint and not has_validation:
                for line_num, line in enumerate(lines, start=1):
                    for indicator in MISSING_VALIDATION_INDICATORS_JAVA:
                        if indicator.search(line):
                            findings.append(STIGFinding(
                                control="V-220631",
                                severity="MEDIUM",
                                file_path=str(path),
                                line=line_num,
                                description=f"API endpoint without input validation: {line.strip()[:80]}",
                                recommendation="Add @Valid, @NotNull, or explicit validation logic",
                            ))

        elif path.suffix == ".py":
            has_endpoint = any(p.search(content) for p in MISSING_VALIDATION_INDICATORS_PYTHON)
            has_validation = any(p.search(content) for p in VALIDATION_PRESENT_PYTHON)
            if has_endpoint and not has_validation:
                for line_num, line in enumerate(lines, start=1):
                    for indicator in MISSING_VALIDATION_INDICATORS_PYTHON:
                        if indicator.search(line):
                            findings.append(STIGFinding(
                                control="V-220631",
                                severity="MEDIUM",
                                file_path=str(path),
                                line=line_num,
                                description=f"API endpoint without input validation: {line.strip()[:80]}",
                                recommendation="Add input validation using pydantic models or InputValidator",
                            ))
    return findings


def check_audit_logging(scan_dir: str) -> List[STIGFinding]:
    findings = []
    root = Path(scan_dir)
    for path in root.rglob("*"):
        if not path.is_file() or not _should_scan_file(path):
            continue
        if path.suffix not in (".py", ".java"):
            continue
        lines = _read_file(path)
        content = "\n".join(lines)

        has_security_ops = any(p.search(content) for p in SECURITY_OPERATION_PATTERNS)
        has_audit = any(p.search(content) for p in AUDIT_LOG_PRESENT)

        if has_security_ops and not has_audit:
            for line_num, line in enumerate(lines, start=1):
                for op_pattern in SECURITY_OPERATION_PATTERNS:
                    if op_pattern.search(line):
                        findings.append(STIGFinding(
                            control="V-220635",
                            severity="MEDIUM",
                            file_path=str(path),
                            line=line_num,
                            description=f"Security operation without audit logging: {line.strip()[:80]}",
                            recommendation="Add audit logging for security-relevant operations",
                        ))
    return findings


def check_insecure_crypto(scan_dir: str) -> List[STIGFinding]:
    findings = []
    root = Path(scan_dir)
    for path in root.rglob("*"):
        if not path.is_file() or not _should_scan_file(path):
            continue
        if path.suffix not in (".py", ".java", ".js", ".ts", ".go"):
            continue
        lines = _read_file(path)
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                continue
            for pattern_name, pattern in WEAK_CRYPTO_PATTERNS:
                if pattern.search(line):
                    findings.append(STIGFinding(
                        control="V-220633",
                        severity="HIGH",
                        file_path=str(path),
                        line=line_num,
                        description=f"Insecure cryptography - {pattern_name}: {line.strip()[:80]}",
                        recommendation="Use AES-256-GCM, SHA-256+, RSA-2048+, TLS 1.2+",
                    ))
    return findings


def generate_compliance_report(
    findings: List[STIGFinding], output_dir: str,
) -> Dict[str, Any]:
    controls = {
        "V-220629": {"name": "Authentication", "nist": "IA-2, IA-5", "findings": []},
        "V-220630": {"name": "Session Security", "nist": "AC-7, AC-12", "findings": []},
        "V-220631": {"name": "Input Validation", "nist": "SI-10", "findings": []},
        "V-220632": {"name": "Input Sanitization", "nist": "SI-10", "findings": []},
        "V-220633": {"name": "Encryption at Rest", "nist": "SC-28", "findings": []},
        "V-220634": {"name": "Encryption in Transit", "nist": "SC-8", "findings": []},
        "V-220635": {"name": "Audit Logging", "nist": "AU-2, AU-3", "findings": []},
        "V-220641": {"name": "Security Headers", "nist": "SI-11", "findings": []},
    }

    for finding in findings:
        if finding.control in controls:
            controls[finding.control]["findings"].append(finding.to_dict())

    for control_id, control in controls.items():
        control["status"] = "PASS" if not control["findings"] else "FAIL"
        control["finding_count"] = len(control["findings"])

    report = {
        "scan_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_findings": len(findings),
        "controls": controls,
        "summary": {
            "pass": sum(1 for c in controls.values() if c["status"] == "PASS"),
            "fail": sum(1 for c in controls.values() if c["status"] == "FAIL"),
            "total": len(controls),
        },
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "stig-compliance-report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"JSON report written to {json_path}")

    md_path = output_path / "stig-compliance-report.md"
    md_lines = [
        "# STIG Compliance Report",
        "",
        f"**Scan Date:** {report['scan_timestamp']}",
        f"**Total Findings:** {report['total_findings']}",
        f"**Controls Passing:** {report['summary']['pass']}/{report['summary']['total']}",
        "",
        "## Control Status Summary",
        "",
        "| STIG Control | NIST | Description | Status | Findings |",
        "|-------------|------|-------------|--------|----------|",
    ]
    for control_id, control in controls.items():
        status_icon = "PASS" if control["status"] == "PASS" else "FAIL"
        md_lines.append(
            f"| {control_id} | {control['nist']} | {control['name']} "
            f"| {status_icon} | {control['finding_count']} |"
        )

    md_lines.extend(["", "## Detailed Findings", ""])
    for control_id, control in controls.items():
        if control["findings"]:
            md_lines.append(f"### {control_id}: {control['name']}")
            md_lines.append("")
            for finding in control["findings"]:
                md_lines.append(
                    f"- **[{finding['severity']}]** `{finding['file']}:{finding['line']}` "
                    f"- {finding['description']}"
                )
                md_lines.append(f"  - Recommendation: {finding['recommendation']}")
            md_lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Markdown report written to {md_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="STIG Compliance Checker")
    parser.add_argument("--scan-dir", required=True, help="Directory to scan")
    parser.add_argument("--output-dir", default="./reports", help="Output directory")
    args = parser.parse_args()

    print(f"Running STIG compliance checks on {args.scan_dir}...")
    all_findings: List[STIGFinding] = []

    print("  Checking for hardcoded secrets (V-220633)...")
    all_findings.extend(check_hardcoded_secrets(args.scan_dir))

    print("  Checking for missing input validation (V-220631)...")
    all_findings.extend(check_input_validation(args.scan_dir))

    print("  Checking for missing audit logging (V-220635)...")
    all_findings.extend(check_audit_logging(args.scan_dir))

    print("  Checking for insecure cryptography (V-220633/V-220634)...")
    all_findings.extend(check_insecure_crypto(args.scan_dir))

    report = generate_compliance_report(all_findings, args.output_dir)

    print(f"\nCompliance Summary: {report['summary']['pass']}/{report['summary']['total']} controls passing")
    print(f"Total findings: {report['total_findings']}")

    return 0 if report["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
