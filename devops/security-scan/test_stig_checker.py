"""
Tests for STIG Compliance Checker.
Tests against intentionally vulnerable code samples.
"""

import os
import json
import tempfile
import pytest
from stig_compliance_checker import (
    check_hardcoded_secrets,
    check_input_validation,
    check_audit_logging,
    check_insecure_crypto,
    generate_compliance_report,
    STIGFinding,
)


@pytest.fixture
def vulnerable_dir():
    tmpdir = tempfile.mkdtemp()
    with open(os.path.join(tmpdir, "bad_secrets.py"), "w") as f:
        f.write('''
password = "SuperSecret123!"
api_key = "ABCDEF1234567890GHIJKLMN"
secret_key = "MyTopSecretTokenValue12345"
db_url = "jdbc:postgresql://admin:password123@db:5432/mydb"
''')

    with open(os.path.join(tmpdir, "bad_crypto.py"), "w") as f:
        f.write('''
import hashlib
digest = hashlib.md5(data).hexdigest()
sha1_hash = hashlib.sha1(data).hexdigest()
cipher = DES.new(key, DES.MODE_ECB)
import random
value = random.random()
''')

    with open(os.path.join(tmpdir, "no_validation.py"), "w") as f:
        f.write('''
from fastapi import FastAPI
app = FastAPI()

@app.post("/api/submit")
def submit_data(request):
    data = request.json()
    process(data)
    return {"status": "ok"}
''')

    with open(os.path.join(tmpdir, "no_audit.py"), "w") as f:
        f.write('''
def authenticate(username, password):
    user = db.find_user(username)
    if user and verify(password, user.hash):
        return create_token(user)
    return None

def authorize(token, resource):
    claims = decode_token(token)
    return claims.get("role") == "admin"
''')

    with open(os.path.join(tmpdir, "clean_code.py"), "w") as f:
        f.write('''
import os
from pydantic import BaseModel, Field

class UserInput(BaseModel):
    name: str = Field(max_length=100)
    age: int = Field(ge=0, le=150)

password = os.environ.get("DB_PASSWORD")
''')
    return tmpdir


class TestHardcodedSecretsDetection:
    def test_detects_hardcoded_password(self, vulnerable_dir):
        findings = check_hardcoded_secrets(vulnerable_dir)
        password_findings = [f for f in findings if "password" in f.description.lower() or "secret" in f.description.lower()]
        assert len(password_findings) > 0

    def test_detects_api_key(self, vulnerable_dir):
        findings = check_hardcoded_secrets(vulnerable_dir)
        api_findings = [f for f in findings if "api" in f.description.lower() or "key" in f.description.lower()]
        assert len(api_findings) > 0

    def test_detects_connection_string(self, vulnerable_dir):
        findings = check_hardcoded_secrets(vulnerable_dir)
        conn_findings = [f for f in findings if "db_url" in f.description.lower() or "jdbc" in f.description.lower() or "Connection" in f.description]
        assert len(findings) >= 3, f"Expected at least 3 secret findings, got {len(findings)}: {[f.description for f in findings]}"

    def test_all_findings_have_v220633_control(self, vulnerable_dir):
        findings = check_hardcoded_secrets(vulnerable_dir)
        for f in findings:
            assert f.control == "V-220633"

    def test_all_findings_are_high_severity(self, vulnerable_dir):
        findings = check_hardcoded_secrets(vulnerable_dir)
        for f in findings:
            assert f.severity == "HIGH"


class TestInsecureCryptoDetection:
    def test_detects_md5(self, vulnerable_dir):
        findings = check_insecure_crypto(vulnerable_dir)
        md5_findings = [f for f in findings if "MD5" in f.description]
        assert len(md5_findings) > 0

    def test_detects_sha1(self, vulnerable_dir):
        findings = check_insecure_crypto(vulnerable_dir)
        sha1_findings = [f for f in findings if "SHA" in f.description]
        assert len(sha1_findings) > 0

    def test_detects_des(self, vulnerable_dir):
        findings = check_insecure_crypto(vulnerable_dir)
        des_findings = [f for f in findings if "DES" in f.description]
        assert len(des_findings) > 0

    def test_detects_ecb_mode(self, vulnerable_dir):
        findings = check_insecure_crypto(vulnerable_dir)
        ecb_findings = [f for f in findings if "ECB" in f.description]
        assert len(ecb_findings) > 0

    def test_detects_insecure_random(self, vulnerable_dir):
        findings = check_insecure_crypto(vulnerable_dir)
        random_findings = [f for f in findings if "Random" in f.description or "random" in f.description]
        assert len(random_findings) > 0


class TestInputValidationCheck:
    def test_detects_missing_validation(self, vulnerable_dir):
        findings = check_input_validation(vulnerable_dir)
        assert len(findings) > 0

    def test_clean_code_passes(self, vulnerable_dir):
        clean_dir = tempfile.mkdtemp()
        with open(os.path.join(clean_dir, "validated.py"), "w") as f:
            f.write('''
from pydantic import BaseModel
from fastapi import FastAPI
app = FastAPI()

class Input(BaseModel):
    name: str

@app.post("/api/data")
def handle(data: Input):
    return {"ok": True}
''')
        findings = check_input_validation(clean_dir)
        assert len(findings) == 0


class TestAuditLoggingCheck:
    def test_detects_missing_audit_logging(self, vulnerable_dir):
        findings = check_audit_logging(vulnerable_dir)
        assert len(findings) > 0

    def test_findings_reference_correct_control(self, vulnerable_dir):
        findings = check_audit_logging(vulnerable_dir)
        for f in findings:
            assert f.control == "V-220635"


class TestComplianceReport:
    def test_report_generation(self, vulnerable_dir):
        all_findings = []
        all_findings.extend(check_hardcoded_secrets(vulnerable_dir))
        all_findings.extend(check_input_validation(vulnerable_dir))
        all_findings.extend(check_audit_logging(vulnerable_dir))
        all_findings.extend(check_insecure_crypto(vulnerable_dir))

        output_dir = tempfile.mkdtemp()
        report = generate_compliance_report(all_findings, output_dir)

        assert "scan_timestamp" in report
        assert "total_findings" in report
        assert "controls" in report
        assert "summary" in report
        assert report["total_findings"] > 0

    def test_report_json_file_created(self, vulnerable_dir):
        output_dir = tempfile.mkdtemp()
        generate_compliance_report([], output_dir)
        assert os.path.exists(os.path.join(output_dir, "stig-compliance-report.json"))

    def test_report_markdown_file_created(self, vulnerable_dir):
        output_dir = tempfile.mkdtemp()
        generate_compliance_report([], output_dir)
        assert os.path.exists(os.path.join(output_dir, "stig-compliance-report.md"))

    def test_clean_codebase_all_pass(self):
        clean_dir = tempfile.mkdtemp()
        with open(os.path.join(clean_dir, "safe.py"), "w") as f:
            f.write('import os\nname = "hello"\n')
        all_findings = []
        all_findings.extend(check_hardcoded_secrets(clean_dir))
        all_findings.extend(check_insecure_crypto(clean_dir))
        output_dir = tempfile.mkdtemp()
        report = generate_compliance_report(all_findings, output_dir)
        assert report["total_findings"] == 0

    def test_finding_to_dict(self):
        finding = STIGFinding(
            control="V-220633", severity="HIGH",
            file_path="/test/file.py", line=10,
            description="Hardcoded secret", recommendation="Use env vars",
        )
        d = finding.to_dict()
        assert d["control"] == "V-220633"
        assert d["file"] == "/test/file.py"
        assert d["line"] == 10
