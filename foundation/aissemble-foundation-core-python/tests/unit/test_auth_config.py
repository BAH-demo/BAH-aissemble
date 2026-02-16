import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)


@pytest.fixture(autouse=True)
def mock_property_manager():
    mock_props = MagicMock()
    mock_pm = MagicMock()
    mock_pm.get_properties.return_value = mock_props
    with patch(
        "aissembleauth.auth_config.PropertyManager"
    ) as mock_class:
        mock_class.get_instance.return_value = mock_pm
        yield mock_props


class TestAuthConfig:
    def test_public_key_path_returns_expanded_path(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="/path/to/public_key.pem"
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.public_key_path()
        assert result == "/path/to/public_key.pem"

    def test_public_key_path_expands_env_vars(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="$HOME/keys/public_key.pem"
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.public_key_path()
        assert "$HOME" not in result
        assert "keys/public_key.pem" in result

    def test_jks_path_returns_expanded_path(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="/path/to/keystore.jks"
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.jks_path()
        assert result == "/path/to/keystore.jks"

    def test_jks_password_returns_value(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="my-password"
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.jks_password()
        assert result == "my-password"

    def test_jks_key_alias_returns_value(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="my-alias"
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.jks_key_alias()
        assert result == "my-alias"

    def test_pdp_host_url_returns_value(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="http://pdp:8080"
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.pdp_host_url()
        assert result == "http://pdp:8080"

    def test_is_authorization_enabled_returns_true_by_default(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(
            side_effect=Exception("Key not found")
        )
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is True

    def test_is_authorization_enabled_returns_true_when_string_true(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value="true")
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is True

    def test_is_authorization_enabled_returns_false_when_string_false(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value="false")
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is False

    def test_is_authorization_enabled_returns_true_when_bool_true(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=True)
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is True

    def test_is_authorization_enabled_returns_false_when_bool_false(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=False)
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is False

    def test_is_authorization_enabled_case_insensitive(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value="TRUE")
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is True

    def test_is_authorization_enabled_mixed_case(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value="False")
        from aissembleauth.auth_config import AuthConfig

        config = AuthConfig()
        result = config.is_authorization_enabled()
        assert result is False
