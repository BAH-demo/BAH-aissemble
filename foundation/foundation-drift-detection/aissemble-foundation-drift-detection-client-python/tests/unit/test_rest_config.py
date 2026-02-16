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


class TestRestConfig:
    @pytest.fixture(autouse=True)
    def mock_property_manager(self):
        mock_props = MagicMock()
        mock_pm = MagicMock()
        mock_pm.get_properties.return_value = mock_props
        with patch(
            "config.rest_config.PropertyManager"
        ) as mock_class:
            mock_class.get_instance.return_value = mock_pm
            yield mock_props

    def test_hostname_returns_configured_value(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="http://drift-service:8084"
        )
        from config.rest_config import RestConfig

        config = RestConfig()
        assert config.hostname() == "http://drift-service:8084"

    def test_reload_refreshes_properties(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="http://host-1:8080"
        )
        from config.rest_config import RestConfig

        config = RestConfig()
        assert config.hostname() == "http://host-1:8080"

        mock_property_manager.__getitem__ = MagicMock(
            return_value="http://host-2:8080"
        )
        config.reload()
        assert config.hostname() == "http://host-2:8080"

    def test_init_calls_reload(self, mock_property_manager):
        from config.rest_config import RestConfig

        config = RestConfig()
        assert config.properties is not None
