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


class TestPolicyConfiguration:
    @pytest.fixture(autouse=True)
    def mock_property_manager(self):
        mock_props = MagicMock()
        mock_pm = MagicMock()
        mock_pm.get_properties.return_value = mock_props
        with patch(
            "policy_manager.configuration.policy_configuration.PropertyManager"
        ) as mock_class:
            mock_class.get_instance.return_value = mock_pm
            yield mock_props

    def test_policies_location_returns_value(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="/path/to/policies"
        )
        from policy_manager.configuration.policy_configuration import (
            PolicyConfiguration,
        )

        config = PolicyConfiguration()
        result = config.policiesLocation()
        assert result == "/path/to/policies"

    def test_policies_location_returns_none_on_type_error(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(
            side_effect=TypeError("No properties")
        )
        from policy_manager.configuration.policy_configuration import (
            PolicyConfiguration,
        )

        config = PolicyConfiguration()
        result = config.policiesLocation()
        assert result is None
