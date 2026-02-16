"""
Tests for Secrets Management (STIG V-220633/V-220634).
Tests secrets detection accuracy (true positives and false positives).
"""

import os
import tempfile
import pytest
from aissemble_security.secrets_management.secrets_validator import SecretsValidator
from aissemble_security.secrets_management.encryption import EncryptionHelper
from aissemble_security.secrets_management.tls_enforcer import TLSEnforcer


class TestSecretsDetection:
    def _write_temp_file(self, content: str, suffix: str = ".py") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_detect_hardcoded_password(self):
        path = self._write_temp_file('password = "SuperSecret123!"\n')
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) > 0
        os.unlink(path)

    def test_detect_api_key(self):
        path = self._write_temp_file('api_key = "ABCDEF1234567890ABCDEF"\n')
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) > 0
        os.unlink(path)

    def test_detect_aws_access_key(self):
        path = self._write_temp_file('aws_key = "AKIAIOSFODNN7EXAMPLE"\n')
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) > 0
        os.unlink(path)

    def test_detect_private_key(self):
        path = self._write_temp_file('-----BEGIN RSA PRIVATE KEY-----\nMIIEow...\n')
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) > 0
        os.unlink(path)

    def test_detect_connection_string(self):
        path = self._write_temp_file('db_url = "jdbc:postgresql://user:pass@host:5432/db"\n')
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) > 0
        os.unlink(path)

    def test_detect_mongodb_connection(self):
        path = self._write_temp_file('mongo = "mongodb://admin:secret@localhost:27017"\n')
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) > 0
        os.unlink(path)

    def test_no_false_positive_on_clean_code(self):
        path = self._write_temp_file(
            'import os\nusername = os.environ.get("USERNAME")\nprint("Hello")\n'
        )
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) == 0
        os.unlink(path)

    def test_no_false_positive_on_comments(self):
        path = self._write_temp_file(
            '# password = "example"\n# api_key = "test"\n'
        )
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) == 0
        os.unlink(path)

    def test_no_false_positive_on_env_var_usage(self):
        path = self._write_temp_file(
            'password = os.environ.get("DB_PASSWORD")\n'
            'api_key = os.getenv("API_KEY")\n'
        )
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) == 0
        os.unlink(path)

    def test_skip_binary_files(self):
        fd, path = tempfile.mkstemp(suffix=".pyc")
        os.close(fd)
        findings = SecretsValidator.scan_file_for_secrets(path)
        assert len(findings) == 0
        os.unlink(path)


class TestDirectoryScanning:
    def test_scan_directory(self):
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, "config.py"), "w") as f:
            f.write('password = "MySuperSecretPassword123!"\n')
        with open(os.path.join(tmpdir, "clean.py"), "w") as f:
            f.write('import os\nname = "hello"\n')
        findings = SecretsValidator.scan_directory_for_secrets(tmpdir)
        assert len(findings) >= 1

    def test_scan_nonexistent_directory(self):
        findings = SecretsValidator.scan_directory_for_secrets("/nonexistent/path")
        assert len(findings) == 0


class TestEnvironmentValidation:
    def test_valid_environment(self):
        os.environ["TEST_SECRET_A"] = "valid_value"
        os.environ["TEST_SECRET_B"] = "another_value"
        validator = SecretsValidator(required_vars=["TEST_SECRET_A", "TEST_SECRET_B"])
        valid, missing = validator.validate_environment()
        assert valid
        assert len(missing) == 0
        del os.environ["TEST_SECRET_A"]
        del os.environ["TEST_SECRET_B"]

    def test_missing_environment_var(self):
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]
        validator = SecretsValidator(required_vars=["NONEXISTENT_VAR"])
        valid, missing = validator.validate_environment()
        assert not valid
        assert "NONEXISTENT_VAR" in missing

    def test_placeholder_value_rejected(self):
        os.environ["TEST_PLACEHOLDER"] = "CHANGEME"
        validator = SecretsValidator(required_vars=["TEST_PLACEHOLDER"])
        valid, missing = validator.validate_environment()
        assert not valid
        del os.environ["TEST_PLACEHOLDER"]


class TestEncryption:
    def test_generate_key(self):
        key = EncryptionHelper.generate_key()
        assert len(key) == 32

    def test_key_to_base64(self):
        key = EncryptionHelper.generate_key()
        b64 = EncryptionHelper.key_to_base64(key)
        assert len(b64) > 0

    def test_encrypt_decrypt_roundtrip(self):
        key = EncryptionHelper.generate_key()
        helper = EncryptionHelper(key=key)
        plaintext = "Sensitive data to encrypt"
        encrypted = helper.encrypt(plaintext)
        assert encrypted is not None
        assert encrypted != plaintext
        decrypted = helper.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_without_key_returns_none(self):
        if "AISSEMBLE_ENCRYPTION_KEY" in os.environ:
            del os.environ["AISSEMBLE_ENCRYPTION_KEY"]
        helper = EncryptionHelper(key=None, key_env_var="NONEXISTENT_KEY_VAR")
        result = helper.encrypt("test")
        assert result is None

    def test_decrypt_wrong_key_returns_none(self):
        key1 = EncryptionHelper.generate_key()
        key2 = EncryptionHelper.generate_key()
        helper1 = EncryptionHelper(key=key1)
        helper2 = EncryptionHelper(key=key2)
        encrypted = helper1.encrypt("secret")
        result = helper2.decrypt(encrypted)
        assert result is None

    def test_invalid_key_size_raises(self):
        with pytest.raises(ValueError):
            EncryptionHelper(key=b"tooshort")

    def test_key_from_passphrase(self):
        key = EncryptionHelper.key_from_passphrase("my-secure-passphrase")
        assert len(key) == 32

    def test_key_from_env_var(self):
        key = EncryptionHelper.generate_key()
        b64_key = EncryptionHelper.key_to_base64(key)
        os.environ["TEST_ENC_KEY"] = b64_key
        helper = EncryptionHelper(key_env_var="TEST_ENC_KEY")
        encrypted = helper.encrypt("test data")
        assert encrypted is not None
        decrypted = helper.decrypt(encrypted)
        assert decrypted == "test data"
        del os.environ["TEST_ENC_KEY"]


class TestTLSEnforcer:
    def test_url_with_https_passes(self):
        valid, msg = TLSEnforcer.check_url_uses_tls("https://example.com")
        assert valid

    def test_url_without_https_fails(self):
        valid, msg = TLSEnforcer.check_url_uses_tls("http://example.com")
        assert not valid
        assert "HTTPS" in msg

    def test_create_secure_context(self):
        import ssl
        context = TLSEnforcer.create_secure_context()
        assert context.minimum_version == ssl.TLSVersion.TLSv1_2
