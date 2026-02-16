"""
STIG V-220635 / NIST AU-2/AU-3: Structured JSON Audit Logging
Captures security-relevant events with correlation IDs and integrity hashes.
"""

import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from enum import Enum
from pathlib import Path


class AuditEventType(Enum):
    AUTH_SUCCESS = "authentication_success"
    AUTH_FAILURE = "authentication_failure"
    AUTH_LOCKOUT = "account_lockout"
    AUTHZ_GRANTED = "authorization_granted"
    AUTHZ_DENIED = "authorization_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modification"
    DATA_DELETE = "data_deletion"
    CONFIG_CHANGE = "configuration_change"
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_FAIL = "pipeline_fail"
    SESSION_CREATE = "session_created"
    SESSION_EXPIRE = "session_expired"
    SESSION_DESTROY = "session_destroyed"
    INPUT_VALIDATION_FAIL = "input_validation_failure"
    SECURITY_VIOLATION = "security_violation"
    SECRET_ACCESS = "secret_access"
    ENCRYPTION_EVENT = "encryption_event"


class AuditLogger:
    """
    STIG V-220635 / NIST AU-2/AU-3: Comprehensive audit logger.
    Produces structured JSON log entries with all required fields.
    """

    def __init__(
        self,
        app_name: str = "aissemble",
        log_dir: Optional[str] = None,
        alert_callback=None,
    ):
        self.app_name = app_name
        self._alert_callback = alert_callback

        self._audit_logger = logging.getLogger(f"{app_name}.audit")
        self._audit_logger.setLevel(logging.INFO)
        self._audit_logger.propagate = False
        if self._audit_logger.handlers:
            self._audit_logger.handlers.clear()

        self._security_logger = logging.getLogger(f"{app_name}.security")
        self._security_logger.setLevel(logging.INFO)
        self._security_logger.propagate = False
        if self._security_logger.handlers:
            self._security_logger.handlers.clear()

        formatter = logging.Formatter("%(message)s")

        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            audit_handler = logging.FileHandler(log_path / f"{app_name}_audit.log")
            audit_handler.setFormatter(formatter)
            self._audit_logger.addHandler(audit_handler)

            security_handler = logging.FileHandler(log_path / f"{app_name}_security.log")
            security_handler.setFormatter(formatter)
            self._security_logger.addHandler(security_handler)
        else:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self._audit_logger.addHandler(stream_handler)
            self._security_logger.addHandler(stream_handler)

        self._security_alert_events = {
            AuditEventType.AUTH_FAILURE,
            AuditEventType.AUTH_LOCKOUT,
            AuditEventType.AUTHZ_DENIED,
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.INPUT_VALIDATION_FAIL,
            AuditEventType.PIPELINE_FAIL,
        }

    def _build_entry(
        self,
        event_type: AuditEventType,
        user_identity: str,
        source_ip: str,
        action: str,
        resource: str,
        outcome: str,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        entry = {
            "timestamp": timestamp,
            "event_type": event_type.value,
            "user_identity": user_identity,
            "source_ip": source_ip,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "app_name": self.app_name,
        }
        if details:
            entry["details"] = details
        entry_json = json.dumps(entry, sort_keys=True)
        entry["integrity_hash"] = hashlib.sha256(entry_json.encode()).hexdigest()[:16]
        return entry

    def _emit(self, entry: Dict[str, Any], event_type: AuditEventType) -> Dict[str, Any]:
        entry_json = json.dumps(entry)
        if event_type in self._security_alert_events:
            self._security_logger.warning(entry_json)
            if self._alert_callback:
                try:
                    self._alert_callback(entry)
                except Exception:
                    self._security_logger.error("Alert callback failed for event: %s", event_type.value)
        else:
            self._audit_logger.info(entry_json)
        return entry

    def log_event(
        self,
        event_type: AuditEventType,
        user_identity: str,
        source_ip: str,
        action: str,
        resource: str,
        outcome: str,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        entry = self._build_entry(
            event_type, user_identity, source_ip, action, resource, outcome,
            correlation_id, details,
        )
        return self._emit(entry, event_type)

    def log_auth_success(
        self, user_identity: str, source_ip: str,
        session_id: str = "", correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.AUTH_SUCCESS, user_identity, source_ip,
            "login", "auth_service", "success", correlation_id,
            {"session_id": session_id},
        )

    def log_auth_failure(
        self, user_identity: str, source_ip: str,
        reason: str = "", attempt_number: int = 0,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.AUTH_FAILURE, user_identity, source_ip,
            "login", "auth_service", "failure", correlation_id,
            {"reason": reason, "attempt_number": attempt_number},
        )

    def log_auth_lockout(
        self, user_identity: str, source_ip: str,
        failed_attempts: int = 0, lockout_minutes: int = 15,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.AUTH_LOCKOUT, user_identity, source_ip,
            "account_lockout", "auth_service", "locked", correlation_id,
            {"failed_attempts": failed_attempts, "lockout_duration_minutes": lockout_minutes},
        )

    def log_authz_decision(
        self, user_identity: str, source_ip: str,
        resource: str, action: str, granted: bool,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        event_type = AuditEventType.AUTHZ_GRANTED if granted else AuditEventType.AUTHZ_DENIED
        outcome = "granted" if granted else "denied"
        return self.log_event(
            event_type, user_identity, source_ip, action, resource, outcome,
            correlation_id,
        )

    def log_data_access(
        self, user_identity: str, source_ip: str,
        resource: str, action: str = "read",
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.DATA_ACCESS, user_identity, source_ip,
            action, resource, "success", correlation_id,
        )

    def log_data_modification(
        self, user_identity: str, source_ip: str,
        resource: str, action: str = "update",
        changes: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.DATA_MODIFY, user_identity, source_ip,
            action, resource, "success", correlation_id, changes,
        )

    def log_config_change(
        self, user_identity: str, source_ip: str,
        resource: str, changes: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.CONFIG_CHANGE, user_identity, source_ip,
            "config_change", resource, "success", correlation_id, changes,
        )

    def log_pipeline_event(
        self, event_type: AuditEventType, user_identity: str, source_ip: str,
        pipeline_name: str, details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        action_map = {
            AuditEventType.PIPELINE_START: ("start", "started"),
            AuditEventType.PIPELINE_COMPLETE: ("complete", "completed"),
            AuditEventType.PIPELINE_FAIL: ("execute", "failed"),
        }
        action, outcome = action_map.get(event_type, ("unknown", "unknown"))
        return self.log_event(
            event_type, user_identity, source_ip,
            action, pipeline_name, outcome, correlation_id, details,
        )

    def log_input_validation_failure(
        self, source_ip: str, endpoint: str,
        validation_error: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.INPUT_VALIDATION_FAIL, "anonymous", source_ip,
            "input_validation", endpoint, "failure", correlation_id,
            {"validation_error": validation_error},
        )

    def log_security_violation(
        self, source_ip: str, violation_type: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            AuditEventType.SECURITY_VIOLATION, "anonymous", source_ip,
            violation_type, "security", "violation", correlation_id, details,
        )
