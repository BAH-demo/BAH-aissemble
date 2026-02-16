"""
Tests for Audit Logging Module (STIG V-220635, NIST AU-2/AU-3).
Validates structured JSON log format compliance and event coverage.
"""

import json
import tempfile
import os
import pytest
from aissemble_security.audit_logging.audit_logger import AuditLogger, AuditEventType


class TestAuditLogEntry:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = AuditLogger(app_name="test-app", log_dir=self.tmpdir)

    def test_log_entry_has_required_fields(self):
        entry = self.logger.log_auth_success(
            user_identity="testuser", source_ip="192.168.1.1", session_id="sess123"
        )
        required_fields = [
            "timestamp", "event_type", "user_identity", "source_ip",
            "action", "resource", "outcome", "correlation_id",
        ]
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"

    def test_timestamp_iso8601_format(self):
        entry = self.logger.log_auth_success(
            user_identity="testuser", source_ip="192.168.1.1"
        )
        timestamp = entry["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp

    def test_integrity_hash_present(self):
        entry = self.logger.log_auth_success(
            user_identity="testuser", source_ip="192.168.1.1"
        )
        assert "integrity_hash" in entry
        assert len(entry["integrity_hash"]) == 16

    def test_correlation_id_present(self):
        entry = self.logger.log_auth_success(
            user_identity="testuser", source_ip="192.168.1.1"
        )
        assert "correlation_id" in entry
        assert len(entry["correlation_id"]) > 0

    def test_custom_correlation_id(self):
        entry = self.logger.log_auth_success(
            user_identity="testuser", source_ip="192.168.1.1",
            correlation_id="custom-corr-id",
        )
        assert entry["correlation_id"] == "custom-corr-id"

    def test_app_name_in_entry(self):
        entry = self.logger.log_auth_success(
            user_identity="testuser", source_ip="192.168.1.1"
        )
        assert entry["app_name"] == "test-app"


class TestAuthenticationEvents:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = AuditLogger(app_name="test-app", log_dir=self.tmpdir)

    def test_auth_success_event(self):
        entry = self.logger.log_auth_success(
            user_identity="admin", source_ip="10.0.0.1", session_id="s1"
        )
        assert entry["event_type"] == "authentication_success"
        assert entry["outcome"] == "success"
        assert entry["user_identity"] == "admin"

    def test_auth_failure_event(self):
        entry = self.logger.log_auth_failure(
            user_identity="attacker", source_ip="10.0.0.99",
            reason="invalid_password", attempt_number=3,
        )
        assert entry["event_type"] == "authentication_failure"
        assert entry["outcome"] == "failure"
        assert entry["details"]["reason"] == "invalid_password"
        assert entry["details"]["attempt_number"] == 3

    def test_auth_lockout_event(self):
        entry = self.logger.log_auth_lockout(
            user_identity="user1", source_ip="10.0.0.1",
            failed_attempts=5, lockout_minutes=15,
        )
        assert entry["event_type"] == "account_lockout"
        assert entry["outcome"] == "locked"


class TestAuthorizationEvents:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = AuditLogger(app_name="test-app", log_dir=self.tmpdir)

    def test_authorization_granted(self):
        entry = self.logger.log_authz_decision(
            user_identity="user1", source_ip="10.0.0.1",
            resource="/api/data", action="read", granted=True,
        )
        assert entry["event_type"] == "authorization_granted"
        assert entry["outcome"] == "granted"

    def test_authorization_denied(self):
        entry = self.logger.log_authz_decision(
            user_identity="user1", source_ip="10.0.0.1",
            resource="/admin/config", action="write", granted=False,
        )
        assert entry["event_type"] == "authorization_denied"
        assert entry["outcome"] == "denied"


class TestDataAccessEvents:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = AuditLogger(app_name="test-app", log_dir=self.tmpdir)

    def test_data_access(self):
        entry = self.logger.log_data_access(
            user_identity="analyst", source_ip="10.0.0.2",
            resource="customer_records", action="read",
        )
        assert entry["event_type"] == "data_access"
        assert entry["resource"] == "customer_records"

    def test_data_modification(self):
        entry = self.logger.log_data_modification(
            user_identity="admin", source_ip="10.0.0.1",
            resource="user_profile", action="update",
            changes={"field": "email", "old": "old@test.com", "new": "new@test.com"},
        )
        assert entry["event_type"] == "data_modification"
        assert entry["details"]["field"] == "email"


class TestConfigAndPipelineEvents:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = AuditLogger(app_name="test-app", log_dir=self.tmpdir)

    def test_config_change(self):
        entry = self.logger.log_config_change(
            user_identity="ops", source_ip="10.0.0.1",
            resource="application.properties",
            changes={"key": "timeout", "old": "30", "new": "60"},
        )
        assert entry["event_type"] == "configuration_change"

    def test_pipeline_start(self):
        entry = self.logger.log_pipeline_event(
            AuditEventType.PIPELINE_START, user_identity="scheduler",
            source_ip="10.0.0.1", pipeline_name="etl-pipeline",
        )
        assert entry["event_type"] == "pipeline_start"
        assert entry["outcome"] == "started"

    def test_pipeline_complete(self):
        entry = self.logger.log_pipeline_event(
            AuditEventType.PIPELINE_COMPLETE, user_identity="scheduler",
            source_ip="10.0.0.1", pipeline_name="etl-pipeline",
        )
        assert entry["event_type"] == "pipeline_complete"
        assert entry["outcome"] == "completed"

    def test_pipeline_fail(self):
        entry = self.logger.log_pipeline_event(
            AuditEventType.PIPELINE_FAIL, user_identity="scheduler",
            source_ip="10.0.0.1", pipeline_name="etl-pipeline",
            details={"error": "OutOfMemoryError"},
        )
        assert entry["event_type"] == "pipeline_fail"
        assert entry["outcome"] == "failed"


class TestSecurityEvents:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = AuditLogger(app_name="test-app", log_dir=self.tmpdir)

    def test_input_validation_failure(self):
        entry = self.logger.log_input_validation_failure(
            source_ip="10.0.0.99", endpoint="/api/submit",
            validation_error="SQL injection detected",
        )
        assert entry["event_type"] == "input_validation_failure"
        assert entry["outcome"] == "failure"

    def test_security_violation(self):
        entry = self.logger.log_security_violation(
            source_ip="10.0.0.99", violation_type="path_traversal",
            details={"path": "../../../etc/passwd"},
        )
        assert entry["event_type"] == "security_violation"
        assert entry["outcome"] == "violation"


class TestAlertIntegration:
    def test_alert_callback_triggered_on_security_events(self):
        alerts = []

        def alert_callback(entry):
            alerts.append(entry)

        tmpdir = tempfile.mkdtemp()
        logger = AuditLogger(app_name="test", log_dir=tmpdir, alert_callback=alert_callback)

        logger.log_auth_failure(
            user_identity="test", source_ip="10.0.0.1", reason="bad_pass"
        )
        assert len(alerts) == 1
        assert alerts[0]["event_type"] == "authentication_failure"

    def test_alert_not_triggered_on_normal_events(self):
        alerts = []

        def alert_callback(entry):
            alerts.append(entry)

        tmpdir = tempfile.mkdtemp()
        logger = AuditLogger(app_name="test", log_dir=tmpdir, alert_callback=alert_callback)

        logger.log_data_access(
            user_identity="test", source_ip="10.0.0.1", resource="data"
        )
        assert len(alerts) == 0

    def test_alert_callback_failure_does_not_crash(self):
        def bad_callback(entry):
            raise RuntimeError("Callback error")

        tmpdir = tempfile.mkdtemp()
        logger = AuditLogger(app_name="test", log_dir=tmpdir, alert_callback=bad_callback)
        entry = logger.log_auth_failure(
            user_identity="test", source_ip="10.0.0.1", reason="error"
        )
        assert entry is not None


class TestLogFileOutput:
    def test_audit_log_written_to_file(self):
        tmpdir = tempfile.mkdtemp()
        logger = AuditLogger(app_name="filetest", log_dir=tmpdir)
        logger.log_auth_success(user_identity="user1", source_ip="10.0.0.1")

        audit_file = os.path.join(tmpdir, "filetest_audit.log")
        assert os.path.exists(audit_file)
        with open(audit_file) as f:
            content = f.read()
        entry = json.loads(content.strip())
        assert entry["event_type"] == "authentication_success"

    def test_security_log_written_to_file(self):
        tmpdir = tempfile.mkdtemp()
        logger = AuditLogger(app_name="filetest", log_dir=tmpdir)
        logger.log_auth_failure(
            user_identity="attacker", source_ip="10.0.0.99", reason="bad"
        )

        security_file = os.path.join(tmpdir, "filetest_security.log")
        assert os.path.exists(security_file)
        with open(security_file) as f:
            content = f.read()
        entry = json.loads(content.strip())
        assert entry["event_type"] == "authentication_failure"


class TestAllEventTypes:
    def test_all_event_types_have_values(self):
        for event_type in AuditEventType:
            assert event_type.value is not None
            assert len(event_type.value) > 0

    def test_event_type_count(self):
        assert len(AuditEventType) >= 19
